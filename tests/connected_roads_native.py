#!/usr/bin/env python3
"""Native mGBA connected-road and legacy-checkpoint regression.

Checkpoint cases import validated synthetic ordinary SRAM and hard-disable RAM
writes and machine states. They are compatibility tests, never fresh acquisition.
Seam cases first cold-Continue the actual source room, then explicitly prepare
only actor positions and enemy suppression/placement. Every write is recorded.
The collision, gates, deferred admission, and renderer run unmodified on the ROM.
"""
from __future__ import annotations
import argparse
import ctypes as C
import gzip
import hashlib
import json
import shutil
import struct
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tools')]
from player_feedback_native import Native, sha
from player_feedback_campaign import ControllerNative
from test_save5 import Save, Save5Tests
from mgba_runner import keymask
from generate_connected_roads import compile_rows

ROAD = struct.Struct('<6B2H6h2B')
DOOR = struct.Struct('<6B6h')
NAMES = ('room', 'target', 'spawn', 'edge', 'gate', 'entry_safe', 'width',
         'height', 'low', 'high', 'center', 'target_center', 'arrival_x',
         'arrival_y', 'barrier_inset', 'reserved')
KEYS = ('UP', 'RIGHT', 'DOWN', 'LEFT')
SCROLLING = {1,16,17,22,23,30,31,38,39,46,47,48,51,54,56,57,58}
LIMIT = 280896

# Superseded P2 walking/A coordinates. Building-door footprints are tested
# separately, because the Bellfoundry stair remains a real building entrance.
OLD_MARKERS = ((0,4,196,128),(0,9,80,128),(1,16,168,248),
               (16,22,400,280),(22,16,240,264),(0,54,176,112),
               (0,60,104,112),(17,56,264,284),(22,57,416,144),
               (30,58,432,256),(58,59,432,256),(60,61,208,112),
               (61,62,120,56),(53,46,208,112),(45,38,208,136))
STAIRS = ((27,26,208),(28,27,208),(29,28,208),
          (35,34,208),(36,35,208),(37,36,208),
          (43,42,216),(44,43,216),(45,44,216))


def progress(s):
    result={name: hashlib.sha256(bytes(getattr(s, name))).hexdigest()
            for name in ('roster', 'quests', 'equipment', 'economy')}
    fields={name:getattr(s.campaign,name) for name,_ in type(s.campaign)._fields_
            if name not in ('room','spawn','sequence','loaded_version')}
    result['campaign_progress']=hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest()
    return result


class RoadSuite:
    def __init__(self, args):
        self.a = args
        self.out = args.output.resolve()
        self.out.mkdir(parents=True, exist_ok=False)
        self.sym = {p[2]: int(p[0],16) for line in args.symbols.read_text().splitlines()
                    if len(p := line.split()) == 3}
        self.candidate = {}
        for field, source in (('rom',args.rom),('symbols',args.symbols),('elf',args.rom.with_suffix('.elf'))):
            target = self.out / ('tested' + source.suffix)
            shutil.copyfile(source, target)
            self.candidate[field+'_sha256'] = sha(target)
            if field == 'rom': self.rom = target
        for field in ('rom','symbols'):
            expected = getattr(args, 'expected_'+field+'_sha')
            if expected: assert self.candidate[field+'_sha256'] == expected, (field, expected, self.candidate)
        self.candidate['acceptance_pins_supplied'] = bool(args.expected_rom_sha and args.expected_symbols_sha)
        self.bridge = self.out / 'bridge.so'
        shutil.copyfile(args.bridge, self.bridge)
        self.candidate['bridge_sha256'] = sha(self.bridge)
        receipt = args.bridge.parent / 'bridge-build.json'
        if receipt.exists():
            build = json.loads(receipt.read_text())
            assert build['bridge_sha256'] == sha(self.bridge)
            shutil.copyfile(receipt, self.out/'bridge-build.json')
            if (receipt.parent/'bridge-source').exists():
                shutil.copytree(receipt.parent/'bridge-source', self.out/'bridge-source')
        if args.source_manifest:
            source_map = json.loads(args.source_manifest.read_text())
            assert all(sha(ROOT/name)==value for name,value in source_map.items()), 'Production changed after build receipt'
            shutil.copyfile(args.source_manifest,self.out/'candidate-source-hashes.json')
            self.candidate['source_manifest_sha256'] = sha(args.source_manifest)
        sources = ('tests/connected_roads_native.py','tests/connected_roads_fixtures.py',
                   'tests/player_feedback_native.py','tests/player_feedback_campaign.py',
                   'tools/mgba_runner.py','tools/generate_connected_roads.py',
                   'tests/test_save5.py','tests/test_save4.py','assets/connected_roads.json',
                   'src/connected_roads.h','src/connected_roads_data.inc')
        self.candidate['test_sources'] = {}
        for rel in sources:
            target=self.out/'test-source'/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/rel,target)
            self.candidate['test_sources'][rel] = sha(target)
        self.manifest=json.loads((self.out/'test-source/assets/connected_roads.json').read_text())
        self.expected_rows=compile_rows(self.manifest)
        self.fixtures = json.loads((args.fixtures/'provenance.json').read_text())
        assert len(self.fixtures['fixtures'])==170,'Canonical checkpoint matrix must contain all170 legal fixtures'
        assert sha(ROOT/self.fixtures['source'])==self.fixtures['source_sha256'],'Historical ordinary-SRAM input changed'
        shutil.copyfile(args.fixtures/'provenance.json',self.out/'fixture-provenance.json')
        self.candidate['fixture_provenance_sha256']=sha(args.fixtures/'provenance.json')
        self.fixture_by_room={}
        for row in self.fixtures['fixtures']:
            assert sha(args.fixtures/row['path'])==row['sha256'], row
            self.fixture_by_room.setdefault(row['room'],row)
        Save5Tests.setUpClass()
        self.codec=Save5Tests()
        self.codec.reset()
        self.codec.put((ROOT/self.fixtures['source']).read_bytes())
        self.expected_progress=progress(self.codec.load())
        self.case='initialization';self.e=None;self.session=0;self.phase='boot'
        self.checks=[];self.cases=[];self.writes=[];self.inputs=[];self.images=[];self.loads=[];self.skips=[]
        self.trace=gzip.open(self.out/'native-frames.jsonl.gz','wt')
        self.measured=[];self.rows=[];self.doors=[]

    def g(self,name,width=4,signed=False):
        value=self.e.read(self.sym[name],width)
        return value-(1<<(width*8)) if signed and value&(1<<(width*8-1)) else value

    def state(self):
        names=('room','game_state','px','py','cx','cy','camera_x','camera_y','frame',
               'transition_lock','transition','presented_transition','scene_present_phase','checkpoint_spawn','summoned',
               'connected_road_pending','connected_road_current','connected_road_arrivals',
               'connected_road_refusals','connected_road_revision','quickparty_open',
               'save_feedback_background','save_requested','save_failed')
        return {n:self.g(n,signed=True) for n in names if n in self.sym}

    def check(self,name,passed,detail=None):
        row={'case':self.case,'check':name,'passed':bool(passed)}
        if detail is not None:row['detail']=detail
        self.checks.append(row)
        if not passed:print('FAIL',self.case,name,detail if detail is not None else self.state(),flush=True)
        return passed

    def step(self,n=1,keys=0):
        mask=keymask(keys)
        self.inputs.append({'case':self.case,'session':self.session,'hw':self.e.frame,'frames':n,'keys':mask,'phase':self.phase})
        for _ in range(n):
            before=self.g('frame');page=self.e.read(0x04000000,2)&16
            self.e.frames(1,mask)
            row={'case':self.case,'session':self.session,'hw':self.e.frame,'phase':self.phase,
                 'delta':(self.g('frame')-before)&0xffffffff,'flip':int(page!=(self.e.read(0x04000000,2)&16)),
                 'cycles':self.g('render_cycles'),'faults':self.e.lib.eb_faults(self.e.ptr),**self.state()}
            if 'render_profile_serial' in self.sym:
                serial=self.g('render_profile_serial')
                if not serial&1:
                    profile={name:self.g('render_profile_'+name) for name in
                             ('world','card','actors','save_begin','save_step','frame','state','room','cycles','total','update','save','render','music','deferred_actors','vblank_cycles','vblank_start','vblank_end','commit')
                             if 'render_profile_'+name in self.sym}
                    if self.g('render_profile_serial')==serial:row['completed_profile']={'serial':serial,**profile}
            self.trace.write(json.dumps(row,separators=(',',':'))+'\n')
            if self.phase=='measured':self.measured.append(row)
            assert not row['faults'],('native core fault',row)
            assert not row['save_failed'],('save failed',row)

    def tap(self,keys):self.step(2,keys);self.step(3)

    def wait(self,predicate,limit=1200,keys=0):
        for _ in range(limit):
            if predicate():return True
            self.step(1,keys)
        return False

    def load(self,fixture=None,controller=False):
        if self.e:self.e.close()
        self.session+=1
        self.e=(ControllerNative if controller else Native)(self.rom,self.bridge)
        self.phase='boot'
        if fixture:
            path=self.a.fixtures/fixture['path']
            assert sha(path)==fixture['sha256']
            self.e.load_save(path);self.e.reset()
        self.loads.append({'case':self.case,'session':self.session,'fixture':fixture,
                           'controller_apis_enforced':controller,'source':'validated synthetic cold ordinary SRAM' if fixture else 'fresh New Adventure'})
        self.step(160)
        assert self.g('game_state')==0, self.state()
        self.phase='cold_continue' if fixture else 'new_game'
        self.tap('A')
        for _ in range(1200):
            if self.g('game_state')==2:self.tap('A')
            elif self.g('game_state')==1 and not self.g('scene_present_phase'):break
            else:self.step()
        assert self.g('game_state')==1,self.state()
        # start_game briefly publishes PLAY before the loader has completed.
        # Require actual post-load updates, not just a transient state value.
        assert self.wait(lambda:self.g('game_state')==1 and self.g('frame')>=30 and not self.g('scene_present_phase') and not self.g('transition_lock') and not self.g('save_feedback_background') and not self.g('save_requested')),self.state()
        if fixture:assert self.g('room')==fixture['room'],(fixture,self.state())
        self.step(3)
        if not self.rows:
            self.rows=[dict(zip(NAMES,ROAD.unpack(self.e.bytes(self.sym['connected_roads']+i*ROAD.size,ROAD.size))),index=i)
                       for i in range(self.g('connected_road_count'))]
            assert [tuple(r[n] for n in NAMES) for r in self.rows]==self.expected_rows,'Native road table differs from pinned source manifest'
            self.doors=[dict(zip(('room','target','spawn','edge','gate','reserved','x','y','w','h','arrival_x','arrival_y'),
                                DOOR.unpack(self.e.bytes(self.sym['connected_doors']+i*DOOR.size,DOOR.size))),index=i)
                        for i in range(self.g('connected_door_count'))]
        self.phase='setup'

    def put(self,name,value,offset=0,width=4,reason='explicit seam actor preparation'):
        old=self.e.read(self.sym[name]+offset,width)
        self.writes.append({'case':self.case,'session':self.session,'hw':self.e.frame,'symbol':name,
                            'offset':offset,'width':width,'old':old,'value':value,'reason':reason})
        self.e.write(self.sym[name]+offset,value&((1<<(width*8))-1),width)

    def suppress(self):
        for i in range(6):
            if self.e.read(self.sym['enemies']+20*i+8):
                self.put('enemies',0,20*i+8,reason='suppress existing source enemy to isolate seam collision and admission')

    def prepare(self,x,y,edge=0,suppress=True):
        if suppress:self.suppress()
        width,height=self.dimensions(self.g('room'))
        cx=max(8,min(width-9,x+(18 if edge==3 else -18)))
        cy=max(8,min(height-9,y+(18 if edge==0 else -18)))
        for n,v in (('px',x),('py',y),('px_q8',x*256),('py_q8',y*256),
                    ('cx',cx),('cy',cy),('cx_q8',cx*256),('cy_q8',cy*256)):
            self.put(n,v)
        self.step(4)
        # Let the real easing code catch up before source screenshots. No
        # camera, cache or collision state is injected by this preparation.
        tx=max(0,min(width-240,x-120));ty=max(0,min(height-160,y-80))
        assert self.wait(lambda:abs(self.g('camera_x')-tx)<=1 and abs(self.g('camera_y')-ty)<=1,80),self.state()

    def dimensions(self,room):
        if room>=62:
            first,name=(70,'covenants') if room>=70 else (62,'horizons')
            return struct.unpack('<HH',self.e.bytes(self.sym[name+'_art_rooms']+(room-first)*28,4))
        return (480,320) if room in SCROLLING else (240,160)

    def bound_check(self,label):
        state=self.state();w,h=self.dimensions(state['room'])
        okay=(0<=state['px']<w and 0<=state['py']<h and 0<=state['cx']<w and 0<=state['cy']<h
              and 0<=state['camera_x']<=w-240 and 0<=state['camera_y']<=h-160)
        self.check(label,okay,{'state':state,'world':[w,h]})

    def shot(self,name,moving_key=None):
        # Scene publication completes before the ten-update hardware fade.
        # BLDY is write-only on GBA/mGBA; never use a bus read as its value.
        # Inspect the engine's latched brightness and then both display pages.
        assert self.wait(lambda:self.g('game_state')==1 and not self.g('scene_present_phase')
                         and not self.g('transition') and not self.g('presented_transition')),self.state()
        before=(self.g('px'),self.g('py'))
        if moving_key:self.step(1,moving_key)
        self.step(2)
        assert not self.g('transition') and not self.g('presented_transition') and not self.g('scene_present_phase'),self.state()
        path=self.out/'images'/(name+'.png');path.parent.mkdir(exist_ok=True)
        self.e.screenshot(path)
        row={'case':self.case,'path':str(path.relative_to(self.out)),'sha256':sha(path),
             'native_size':[240,160],'session':self.session,'hw':self.e.frame,'state':self.state(),
             'brightness_observation':'latched software brightness zero, then two displayed pages; write-only BLDY is never read','fade_clear':True,
             'settling_movement':{'key':moving_key,'before':before,'after':[self.g('px'),self.g('py')]},
             'ordinary_save_in_progress':bool(self.g('save_feedback_background') or self.g('save_requested')),
             'saved_success_badge_ticks':self.g('saved_ticks')if 'saved_ticks'in self.sym else None}
        self.images.append(row)
        path.with_suffix('.json').write_text(json.dumps(row,indent=2)+'\n')

    def section(self,name,fn):
        self.case=name;start=len(self.checks);writes=len(self.writes);frames=len(self.measured)
        try:fn()
        except Exception as exc:
            self.check('harness case completed',False,repr(exc));traceback.print_exc()
        observed=self.measured[frames:]
        self.cases.append({'case':name,'checks':len(self.checks)-start,'writes':len(self.writes)-writes,
                           'measured_frames':len(observed),'cadence':self.cadence(observed)})
        self.report()

    @staticmethod
    def cadence(rows):
        unique={}
        for row in rows:
            p=row.get('completed_profile',{})
            if p:unique[(row['session'],p['serial'])]=p
        spills=[p for p in unique.values() if p.get('deferred_actors') and
                not(160<=p.get('vblank_start',0)<=p.get('vblank_end',0)<228 and p.get('vblank_cycles',0)<=83776)]
        return {'frames':len(rows),'update_misses':sum(r['delta']!=1 for r in rows),
                'flip_misses':sum(not r['flip'] for r in rows),'cycle_overruns':sum(r['cycles']>=LIMIT for r in rows),
                'max_cycles':max((r['cycles'] for r in rows),default=0),'publication_spills':len(spills)}

    def checkpoint(self,fixture):
        self.load(fixture,controller=True)
        saved=Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)))
        self.check('Continue preserves campaign, roster, quest, equipment and economy progress',progress(saved)==self.expected_progress,
                   {'expected':self.expected_progress,'actual':progress(saved)})
        self.check('Continue retains legal room and canonical checkpoint',
                   self.g('room')==fixture['room'] and self.g('checkpoint_spawn')==fixture['spawn'],self.state())
        self.check('Continue applies no transient road arrival',self.g('connected_road_arrivals')==0,self.state())
        start=(self.g('px'),self.g('py'));escaped=False
        self.phase='checkpoint_escape'
        for key in ('UP','RIGHT','DOWN','LEFT'):
            self.step(6,key)
            if abs(self.g('px')-start[0])+abs(self.g('py')-start[1])>=4:
                escaped=True;break
        self.check('legacy checkpoint permits controller escape movement',escaped,{'from':start,'to':self.state()})
        self.bound_check('checkpoint actor and camera remain inside world')
        if fixture['spawn']==0 or not escaped:self.shot('checkpoint-'+str(fixture['room'])+'-'+str(fixture['spawn']))

    @staticmethod
    def point(r,lateral,distance):
        return ((lateral,distance) if r['edge']==0 else
                (r['width']-1-distance,lateral) if r['edge']==1 else
                (lateral,r['height']-1-distance) if r['edge']==2 else (distance,lateral))

    def mouth_start(self,r,lateral):
        entries=[struct.unpack('<4B2h2B',self.e.bytes(self.sym['travel_entries']+10*i,10))
                 for i in range(self.g('travel_entry_count'))]
        boxes=[(e[4],e[5],e[6],e[7])for e in entries if e[0]==r['room']]
        boxes +=[(d['x'],d['y'],d['w'],d['h'])for d in self.doors if d['room']==r['room']]
        # The Stone Trial is a genuine separate doorway near room9's east
        # mouth. Preserve the failed acceptance-c1 setup and begin beyond real
        # interior entrances, rather than disabling their valid collision/input.
        for distance in (28,20,12):
            x,y=self.point(r,lateral,distance);ex,ey=self.point(r,lateral,5)
            if not any(max(x,ex)>=bx and min(x,ex)<bx+bw and max(y,ey)>=by and min(y,ey)<by+bh
                       for bx,by,bw,bh in boxes):return x,y
        raise AssertionError(('No isolated road-mouth approach outside retained physical entrances',r,lateral))

    def seam(self,r,lateral,label):
        self.load(self.fixture_by_room[r['room']])
        if not self.g('summoned'):self.tap('B')
        self.prepare(*self.mouth_start(r,lateral),edge=r['edge'])
        self.phase='measured'
        if label=='center':
            self.shot('road-%02d-source'%r['index'])
            selected=self.e.read(self.sym['adventure_save']+Save.roster.offset+type(Save().roster).selected_party.offset,1)
            position=(self.g('px'),self.g('py'));self.step(12,'L+'+KEYS[r['edge']])
            self.check('L picker holds position near seam',self.g('quickparty_open') and position==(self.g('px'),self.g('py')) and self.g('room')==r['room'],self.state())
            self.step(2,'L+B');self.step(3)
            self.check('canceling L picker preserves source and selection',self.g('room')==r['room'] and not self.g('quickparty_open') and self.e.read(self.sym['adventure_save']+Save.roster.offset+type(Save().roster).selected_party.offset,1)==selected,self.state())
        arrivals=self.g('connected_road_arrivals');refusals=self.g('connected_road_refusals')
        crossed=self.wait(lambda:self.g('room')!=r['room'],limit=240,keys=KEYS[r['edge']])
        arrival=self.state()
        self.check('outward walk crosses exactly the requested seam',crossed and arrival['room']==r['target'],arrival)
        if not crossed:return
        expected=[r['arrival_x'],r['arrival_y']]
        expected[0 if r['edge']in(0,2)else 1]+=lateral-r['center']
        self.check('committed landing preserves exact aperture offset',[arrival['px'],arrival['py']]==expected,{'expected':expected,'actual':arrival})
        self.check('one arrival, matching road index, no collision fallback',arrival['connected_road_arrivals']==arrivals+1 and arrival['connected_road_current']==r['index'] and arrival['connected_road_refusals']==refusals,arrival)
        self.bound_check('arrival actors and camera inside destination world')
        if label!='center':
            # Preserve the same held key across both sides of the handoff,
            # including all deferred scene-publication frames.
            self.step(24,KEYS[r['edge']])
            self.check('unreleased outward direction across handoff never bounces',self.g('room')==r['target'] and self.g('connected_road_arrivals')==arrivals+1,self.state())
        assert self.wait(lambda:not self.g('scene_present_phase')),self.state()
        self.step(3)
        if label=='center':self.shot('road-%02d-arrival'%r['index'],KEYS[r['edge']])
        self.step(24)
        self.check('neutral arrival never bounces',self.g('room')==r['target'] and self.g('connected_road_arrivals')==arrivals+1,self.state())
        self.step(12,KEYS[r['edge']])
        self.check('continued outward hold never bounces',self.g('room')==r['target'] and self.g('connected_road_arrivals')==arrivals+1,self.state())
        self.bound_check('held-direction companion and camera inside world')

    def camera_boundary(self,r):
        self.load(self.fixture_by_room[r['room']])
        # Center crossing of an internal 240x160 viewport boundary. The true
        # edge remains at least 60 pixels away throughout this input sample.
        entries=[struct.unpack('<4B2h2B',self.e.bytes(self.sym['travel_entries']+10*i,10))
                 for i in range(self.g('travel_entry_count'))]
        boxes=[(e[4],e[5],e[6],e[7])for e in entries if e[0]==r['room']]
        boxes +=[(d['x'],d['y'],d['w'],d['h'])for d in self.doors if d['room']==r['room']]
        for lateral in (r['center'],r['center']-48,r['center']+48,64,96,192):
            if r['edge']in(0,2):x,y=lateral,160
            else:x,y=240,lateral
            if not(32<=x<r['width']-32 and 32<=y<r['height']-32):continue
            if not any(x+24>=bx and x-24<bx+bw and y+24>=by and y-24<by+bh for bx,by,bw,bh in boxes):break
        else:raise AssertionError('No camera boundary sample clear of retained physical entrances')
        self.prepare(x,y,edge=r['edge'])
        self.phase='measured';before=self.g('connected_road_arrivals')
        self.step(12,KEYS[r['edge']])
        self.check('scrolling viewport boundary is never a room portal',self.g('room')==r['room'] and self.g('connected_road_arrivals')==before,self.state())
        self.bound_check('camera scrolling stays bounded')

    def boundary_inputs(self,r):
        self.load(self.fixture_by_room[r['room']])
        self.prepare(*self.point(r,r['center'],7),edge=r['edge'])
        self.phase='measured'
        start=len(self.measured)
        self.step(1,'B');self.step(3);self.step(1,'B');self.step(3)
        self.step(1,'B');self.step(3)
        self.step(3,'L+RIGHT');self.step(3)
        samples=self.measured[start:]
        w,h=r['width'],r['height']
        violations=[row for row in samples if not(0<=row['cx']<w and 0<=row['cy']<h)]
        self.check('B summon/recall and L replacement never place companion outside source',not violations,violations)
        self.check('B and L actions at mouth never cross the seam',self.g('room')==r['room'],self.state())
        self.phase='setup';self.prepare(*self.point(r,r['center'],5),edge=r['edge'])
        self.phase='measured';self.step(3,KEYS[r['edge']]+'+'+KEYS[(r['edge']+2)%4])
        self.check('opposing held directions cannot request seam travel',self.g('room')==r['room'],self.state())
        for lateral in (r['low']-1,r['high']):
            self.phase='setup';self.prepare(*self.point(r,lateral,5),edge=r['edge'])
            self.phase='measured';self.step(3,KEYS[r['edge']])
            self.check('point outside aperture never requests seam travel at '+str(lateral),self.g('room')==r['room'],self.state())
        self.phase='setup';self.prepare(*self.point(r,r['center'],5),edge=r['edge'])
        self.phase='measured'
        crossed=self.wait(lambda:self.g('room')!=r['room'],240,KEYS[r['edge']]+'+'+KEYS[(r['edge']+1)%4])
        state=self.state();axis='px' if r['edge']in(0,2)else'py'
        self.check('unopposed outward diagonal crosses correct seam within aperture',crossed and state['room']==r['target'] and abs(state[axis]-r['target_center'])<=3,state)

    def closed(self,r):
        self.load()
        assert r['room']==0
        self.prepare(*self.point(r,r['center'],32),edge=r['edge'])
        self.phase='measured';self.step(45,KEYS[r['edge']])
        state=self.state();distance=(state['py'] if r['edge']==0 else r['width']-1-state['px'] if r['edge']==1 else r['height']-1-state['py'] if r['edge']==2 else state['px'])
        self.check('closed gate keeps play in source and blocks at physical fence',state['room']==0 and state['game_state']==1 and distance>=r['barrier_inset']+5 and self.g('connected_road_arrivals')==0,state)
        self.shot('closed-road-%02d'%r['index'])

    def hostile(self,r):
        self.load(self.fixture_by_room[r['room']])
        live=[i for i in range(6) if self.e.read(self.sym['enemies']+20*i+8)]
        if not live:
            self.skips.append({'case':self.case,'source':r['room'],'limit':'No existing live enemy on cold-load source; no hostile fabricated'})
            return
        x,y=self.point(r,r['center'],5)
        self.prepare(x,y,edge=r['edge'],suppress=False)
        i=live[0];ex,ey=self.point(r,r['center']+8,8)
        self.put('enemies',ex,20*i,reason='relocate existing live hostile beside mouth to exercise entry_safe guard')
        self.put('enemies',ey,20*i+4,reason='relocate existing live hostile beside mouth to exercise entry_safe guard')
        self.phase='measured';before=self.g('connected_road_arrivals');self.step(2,KEYS[r['edge']])
        self.check('live nearby hostile prevents guarded seam admission',self.g('room')==r['room'] and self.g('connected_road_arrivals')==before,self.state())

    def marker(self,marker):
        room,target,x,y=marker
        self.load(self.fixture_by_room[room]);self.prepare(x,y)
        self.phase='measured';self.tap('A');self.step(10)
        self.check('old interior A marker does not invoke replaced road',self.g('room')==room,{'retired_target':target,'state':self.state()})
        if self.g('room')!=room:return
        for _ in range(12):
            if self.g('game_state')!=2:break
            self.tap('A')
        assert self.wait(lambda:self.g('game_state')==1 and not self.g('scene_present_phase')),self.state()
        for key in KEYS:
            self.phase='setup';self.prepare(x,y)
            self.phase='measured';self.step(3,key)
            self.check('walking '+key+' over retired marker never invokes old link',self.g('room')==room,{'retired_target':target,'state':self.state()})
            if self.g('room')!=room:return

    def door(self,d):
        self.load(self.fixture_by_room[d['room']])
        x=d['x']+d['w']//2;y=d['y']+d['h']-1 if d['edge']==0 else d['y']
        self.prepare(x,y,edge=d['edge'])
        self.phase='measured';crossed=self.wait(lambda:self.g('room')!=d['room'],240,KEYS[d['edge']])
        self.check('real building doorway enters requested room on foot',crossed and self.g('room')==d['target'],self.state())
        if crossed:
            self.check('building doorway uses authored physical landing',(self.g('px'),self.g('py'))==(d['arrival_x'],d['arrival_y']),self.state())
            self.bound_check('doorway arrival and camera remain bounded')
            assert self.wait(lambda:not self.g('scene_present_phase')),self.state()
            self.step(3);self.shot('door-%d-arrival'%d['index'],KEYS[d['edge']]);self.step(28)
            self.check('neutral building arrival never bounces',self.g('room')==d['target'],self.state())

    def stair(self,source,target,x):
        self.load(self.fixture_by_room[source],controller=True)
        old_y=136 if source>=38 else 132
        self.check('stair source Continue retains original canonical position',(self.g('px'),self.g('py'))==(120,old_y),self.state())
        self.tap('B')
        self.phase='measured'
        crossed=self.wait(lambda:self.g('room')!=source,240,'DOWN')
        self.check('controller descends to immediately preceding stair room',crossed and self.g('room')==target,self.state())
        if not crossed:return
        self.step(3)
        assert self.wait(lambda:self.g('game_state')==1 and not self.g('scene_present_phase')),self.state()
        self.check('descending stair uses matching upstairs landing and checkpoint0',(self.g('px'),self.g('py'),self.g('checkpoint_spawn'))==(x,80,0),self.state())
        self.bound_check('descending stair actors and camera remain bounded')
        self.shot('stair-%02d-%02d'%(source,target),'DOWN');self.step(24)
        self.check('neutral stair landing cannot bounce',self.g('room')==target,self.state())
        held_start=len(self.measured);self.step(24,'DOWN')
        assert self.wait(lambda:self.g('game_state')==1 and not self.g('scene_present_phase')),self.state()
        if source==37:
            # A separate, retained service stair starts25px below this landing.
            # Development run dev-stairs-r6 preserved the original over-broad
            # stay-in-room assertion. Require actual walking into its footprint.
            entries=[struct.unpack('<4B2h2B',self.e.bytes(self.sym['travel_entries']+10*i,10))
                     for i in range(self.g('travel_entry_count'))]
            entry=next(e for e in entries if e[0]==36 and e[2]==31)
            bx,by,bw,bh=entry[4:]
            rows=self.measured[held_start:]
            admission=next((i for i,row in enumerate(rows) if row['room']==36 and row['game_state']==10 and
                            bx<=row['px']<bx+bw and by<=row['py']<by+bh),None)
            departure=next((i for i,row in enumerate(rows) if row['room']!=36),None)
            okay=(self.g('room')==31 and admission is not None and departure is not None and admission<departure
                  and all(row['room']in(36,31) for row in rows))
            self.check('37 to36 continued walk uses distinct service stair only after reaching its footprint',okay,
                       {'native_footprint':[bx,by,bw,bh],'admission_frame':rows[admission]if admission is not None else None,'state':self.state()})
            self.step(24)
            self.check('separate service-stair arrival remains stable on neutral input',self.g('room')==31,self.state())
        else:
            self.check('holding Down after stair arrival cannot bounce or skip another stair',self.g('room')==target,self.state())
        self.bound_check('held stair travel leaves actors and camera bounded')
        self.load(self.fixture_by_room[target],controller=True)
        self.check('cold checkpoint remains original instead of transient stair landing',(self.g('px'),self.g('py'),self.g('checkpoint_spawn'))==(120,old_y,0),self.state())

    def report(self):
        self.trace.flush()
        data={'suite':__doc__,'candidate':self.candidate,'fixture_scope':'170 validated synthetic room/spawn variants; no user saves, no fresh acquisition claim',
              'controller_checkpoint_cases':'RAM-write and machine-state APIs disabled; ordinary SRAM import only',
              'prepared_seam_cases':'Cold-load actual source room, then logged actor and enemy preparation only; no gate/collision override',
              'cases':self.cases,'checks':self.checks,'skips':self.skips,'failures':sum(not r['passed'] for r in self.checks),
              'passes':sum(r['passed'] for r in self.checks),'preparation_writes':self.writes,'loads':self.loads,
              'images':self.images,'roads':self.rows,'doors':self.doors,'native_cadence':self.cadence(self.measured),
              'frame_trace':'native-frames.jsonl.gz','machine_state_imports':0,'input_log':'controller-inputs.json',
              'limits':['Cold Continue/bootstrap/setup timings are labeled separately from measured seam handoffs',
                        'All128/72-member checkpoint fixtures have synthetic room/spawn edits and do not prove progression acquisition',
                        'Full campaign/global49 route acquisition and typed Q45 guardian departure are separate suites']}
        (self.out/'report.json').write_text(json.dumps(data,indent=2)+'\n')
        (self.out/'controller-inputs.json').write_text(json.dumps(self.inputs,separators=(',',':'))+'\n')

    def run(self):
        mode=self.a.mode
        if mode in ('all','checkpoints'):
            fixtures=[r for r in self.fixtures['fixtures'] if self.a.room is None or r['room']==self.a.room]
            for f in fixtures[:self.a.limit or None]:
                self.section('checkpoint-%02d-%d'%(f['room'],f['spawn']),lambda f=f:self.checkpoint(f))
        if mode!='checkpoints':
            self.case='table-validation';self.load(self.fixture_by_room[0])
            roads=[r for r in self.rows if not r['reserved'] and (self.a.room is None or r['room']==self.a.room)]
            if self.a.road is not None:roads=[r for r in roads if r['index']==self.a.road]
            roads=roads[:self.a.limit or None]
            if mode in ('all','seams'):
                for r in roads:
                    points=[('low',r['low']),('low-inner',r['low']+5),('center',r['center']),('high-inner',r['high']-6),('high',r['high']-1)]
                    if self.a.center_only:points=[points[2]]
                    for name,value in points:self.section('road-%02d-%s'%(r['index'],name),lambda r=r,value=value,name=name:self.seam(r,value,name))
                    if (r['edge']in(0,2)and r['height']>160)or(r['edge']in(1,3)and r['width']>240):
                        self.section('viewport-%02d'%r['index'],lambda r=r:self.camera_boundary(r))
                    self.section('boundary-inputs-%02d'%r['index'],lambda r=r:self.boundary_inputs(r))
            if mode in ('all','guards'):
                for r in roads:
                    if r['room']==0 and r['gate']:
                        self.section('closed-%02d'%r['index'],lambda r=r:self.closed(r))
                    if r['entry_safe']:
                        self.section('hostile-%02d'%r['index'],lambda r=r:self.hostile(r))
            if mode in ('all','markers'):
                for marker in OLD_MARKERS:
                    if self.a.room is None or marker[0]==self.a.room:self.section('retired-%02d-%02d'%marker[:2],lambda marker=marker:self.marker(marker))
            if mode in ('all','doors'):
                for d in self.doors:
                    if self.a.room is None or d['room']==self.a.room:self.section('door-%d'%d['index'],lambda d=d:self.door(d))
            if mode in ('all','stairs'):
                for source,target,x in STAIRS:
                    if self.a.room is None or source==self.a.room:self.section('stair-%02d-%02d'%(source,target),lambda source=source,target=target,x=x:self.stair(source,target,x))
        self.case='suite-verification'
        self.check('all fixture input bytes remain unchanged',all(sha(self.a.fixtures/r['path'])==r['sha256'] for r in self.fixtures['fixtures']))
        cadence=self.cadence(self.measured)
        self.check('measured native updates, flips, cycle budget and publication windows all pass',not any(cadence[k] for k in ('update_misses','flip_misses','cycle_overruns','publication_spills')),cadence)
        self.report();self.trace.close()
        if self.e:self.e.close()
        Save5Tests.doClassCleanups()
        print(json.dumps({'output':str(self.out),'cases':len(self.cases),'failures':sum(not r['passed']for r in self.checks),'cadence':self.cadence(self.measured)}),flush=True)
        return int(any(not r['passed']for r in self.checks))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,default=ROOT/'build/emberbond.gba')
    p.add_argument('--symbols',type=Path,default=ROOT/'build/emberbond.sym')
    p.add_argument('--bridge',type=Path,default=ROOT/'build/connected-roads-native-bridge/bridge.so')
    p.add_argument('--fixtures',type=Path,default=ROOT/'build/connected-road-checkpoints-r0')
    p.add_argument('--source-manifest',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--expected-rom-sha');p.add_argument('--expected-symbols-sha')
    p.add_argument('--mode',choices=('all','checkpoints','seams','guards','markers','doors','stairs'),default='all')
    p.add_argument('--room',type=int);p.add_argument('--road',type=int);p.add_argument('--limit',type=int)
    p.add_argument('--center-only',action='store_true')
    args=p.parse_args()
    sys.exit(RoadSuite(args).run())


if __name__=='__main__':main()
