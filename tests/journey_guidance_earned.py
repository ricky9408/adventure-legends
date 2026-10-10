#!/usr/bin/env python3
"""Same-ROM, empty-SRAM main adventure proof; all gameplay uses real buttons.

Historical journey helpers supply authored actions, never constructors, pinned
fixtures, state imports, or previous progress. Baseline/partial runs are explicitly
route-development diagnostics. Only a complete fresh run can be acceptance.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import ctypes as C
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tools')]
import campaign_tests
from campaign_tests import CampaignRun
from evolution_tests import EvolutionRun
from player_feedback_campaign import FeedbackCampaign, ControllerNative
from player_feedback_native import sha
from mgba_runner import keymask
from test_save5 import Save
from region_journey import RegionJourney
from northern_journey import NorthernJourney
from southern_journey import SouthernJourney
from magma_journey import MagmaJourney, elf_locals
from underwater_journey import UnderwaterJourney
from return_journey import ReturnJourney
from horizons_journey import HorizonsJourney
from covenants_journey import CovenantsJourney
from connected_roads_journey import ConnectedRoadJourneyMixin
from journey_guidance_opening import OpeningJourneyMixin

CHAPTERS = ('original', 'river', 'north', 'south', 'magma', 'underwater', 'return', 'horizons', 'covenants')
GUARANTEED_FORMS = {1,4,7,10,13,16,19,77,79,85,31,34,49,52,101,103,105,107,109,111}

class StrictNative(ControllerNative):
    """Block Python and direct-library mutation/state-import escape hatches."""
    def __init__(self, rom, bridge):
        super().__init__(rom, bridge)
        self.lib.eb_write = self.write
        self.lib.eb_state = self.state

class Evidence:
    def init_evidence(self, args, chapter, *, original=False):
        self.args = args
        self.chapter = chapter
        self.session = 0
        self.mode = 'boot'
        self.route_complete = False
        self.checks = []
        self.failures = []
        self.inputs = []
        self.snapshots = {}
        self.transitions = []
        self.visits = []
        self.edges = []
        self.receipts = []
        self.checkpoints = []
        self.metrics = {'hardware_frames':0, 'faults':0, 'max_cycles':0,
                        'active_update_misses':0, 'active_flip_misses':0, 'active_overruns':0}
        self.checkpoint_serial = 0
        self._stream = gzip.open(self.out/'controller-inputs.jsonl.gz', 'wt')
        self._frames = gzip.open(self.out/'native-frames.jsonl.gz', 'wt')
        self.candidate = dict(args.candidate)
        self.source_root = args.source_root
        self.bridge = args.bridge
        self.history = []
        self.main_only = False
        self.main_selections = []
        self.cases = []
        self.coverage = []
        self.acquisitions = []
        self.frame_windows = []
        self.timings = {}
        self.pixel_cases = []
        self.provenance = {'initial_sram':'controller-earned cross-ROM chapter boundary' if args.cross_rom_diagnostic else 'empty cartridge', 'candidate_sha256':args.expected_rom_sha,
                           'historical_progress_imports':0, 'machine_state_imports':0, 'game_ram_writes':0}
    def check(self, condition, label, fatal=True):
        row = {'label':label, 'passed':bool(condition), 'chapter':self.chapter,
               'session':self.session, 'frame':self.e.frame}
        self.checks.append(row)
        if not condition and fatal: raise AssertionError((label, self.status()))
    def raw_step(self, count, keys=0):
        mask = keymask(keys) & ~4  # No removed Select dodge, or hidden shortcut.
        row = {'chapter':self.chapter, 'session':self.session, 'emulator_frame':self.e.frame,
               'frames':int(count), 'keys':mask, 'phase':self.mode}
        self.inputs.append(row)
        self._stream.write(json.dumps(row, separators=(',',':'))+'\n')
        for _ in range(count):
            previous_room = self.get('room')
            previous_state = self.get('game_state')
            previous_frame = self.get('frame')
            page = self.e.read(0x04000000,2)&16
            self.e.frames(1,mask)
            room = self.get('room')
            state = self.get('game_state')
            delta = (self.get('frame')-previous_frame)&0xffffffff
            flip = (self.e.read(0x04000000,2)&16)!=page
            cycles = self.get('render_cycles')
            faults = self.e.lib.eb_faults(self.e.ptr)
            obs = {'chapter':self.chapter,'session':self.session,'hardware_frame':self.e.frame,
                   'phase':self.mode,'room':room,'state':state,'x':self.get('px'),'y':self.get('py'),
                   'delta':delta,'flip':flip,'cycles':cycles,'faults':faults,
                   'game_frame':self.get('frame'),'before_state':previous_state,
                   'counter_reset':self.mode=='opening_activation' and previous_state==0 and state==14 and self.get('frame')==0}
            if self.mode in ('journey','opening_activation') and (delta!=1 or not flip or cycles>=250000):
                obs['before_room']=previous_room;obs['before_state']=previous_state
                obs['runtime']={n:self.get(n) for n in ('scene_present_phase','save_feedback_background','save_requested','save_begin_cycles','save_step_cycles','toast_id','toast_ticks','return_power_kind','return_power_time','horizons_power_kind','horizons_power_time','covenants_power_kind','covenants_power_time') if n in self.sym}
                if 'render_profile_serial' in self.sym:
                    serial=self.get('render_profile_serial')
                    if not serial&1:
                        profile={n:self.get('render_profile_'+n) for n in ('world','card','actors','save_begin','save_step','frame','state','room','update','save','render','music','deferred_actors','vblank_cycles','vblank_start','vblank_end','commit') if 'render_profile_'+n in self.sym}
                        if serial==self.get('render_profile_serial'):obs['completed_profile']={'serial':serial,**profile}
            self._frames.write(json.dumps(obs,separators=(',',':'))+'\n')
            self.metrics['hardware_frames'] += 1
            self.metrics['faults'] = max(self.metrics['faults'],faults)
            self.metrics['max_cycles'] = max(self.metrics['max_cycles'],cycles)
            if self.mode == 'journey' and previous_state == state == 1:
                self.metrics['active_update_misses'] += delta != 1
                self.metrics['active_flip_misses'] += not flip
                self.metrics['active_overruns'] += cycles >= 280896
            assert not faults, ('Native core fault',obs)
            assert not self.get('save_failed'), ('Ordinary SRAM save failed',obs)
            if room != previous_room:
                self.transitions.append({'from':previous_room,'to':room,'frame':self.e.frame,'session':self.session,'keys':mask})
                self.edges.append([previous_room,room])
            if room not in self.visits: self.visits.append(room)
            if self.main_only and state == 1: self.main_selections.append(self.selected().form_id)
    def step(self, n, keys=0):
        self.raw_step(n, keys)
        self.settle_save()
    def settle_save(self, intrusive=False):
        for _ in range(1500):
            state = self.get('game_state')
            if state in (6,8,10,12): self.raw_step(1); continue
            if state == 13:
                self.receipts.append({'chapter':self.chapter,'frame':self.e.frame})
                self.raw_step(3); self.raw_step(2,'A'); self.raw_step(3); continue
            return
        raise AssertionError(('transaction failed to settle',self.status()))
    def drain_background(self):
        self.settle_save()
        for _ in range(1500):
            if not self.get('save_feedback_background') and not self.get('save_requested'): return
            self.step(1)
        raise AssertionError('ordinary background save did not finish')
    def state(self): return Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)))
    save_state = state
    def equipped_items(self):
        s = self.state()
        return [s.equipment.bag[i].item_id if i<48 else 0 for i in s.equipment.equipped]
    def proof_state(self):
        s = self.state()
        return {'status':self.status(),'quests':[(s.quests.states[q>>2]>>((q&3)*2))&3 for q in range(64)],
                'objectives':list(s.quests.objectives),'region_flags':list(s.quests.region_flags),
                'owned_forms':[c.form_id for c in s.roster.instances if c.flags&1],
                'individuals':[{'id':c.instance_id,'form':c.form_id,'level':c.level,'bond':c.bond} for c in s.roster.instances if c.flags&1],
                'equipped_items':self.equipped_items()}
    def snapshot(self, name, settle=True):
        if settle: self.drain_background()
        self.raw_step(3)
        key=f'{self.chapter}-{name}'
        if key in self.snapshots:
            key += f'-{self.checkpoint_serial}'
        self.checkpoint_serial += 1
        p=self.out/(key+'.sav')
        method=self.e.save(p)
        self.e.screenshot(self.out/(key+'.png'))
        row={'sram_path':str(p),'sram_sha256':sha(p),'sram_export':method,
             'candidate_sha256':self.candidate['rom_sha256'],'chapter':self.chapter,
             'session':self.session,'frame':self.e.frame,**self.proof_state()}
        self.snapshots[key]=row
        self.report()
        print(key,row['status'],'forms',row['owned_forms'],flush=True)
        return p
    def restore(self,*args,**kwargs): raise AssertionError('Machine state restoration is forbidden')
    def cold_reboot(self,name):
        self.drain_background()
        before=self.state()
        path=self.snapshot(name+'-before-continue')
        self.e.close(); self.session+=1
        self.e=StrictNative(self.rom,self.bridge)
        self.e.load_save(path); self.e.reset(); self.mode='cold_continue'
        self.raw_step(160); self.tap('A',4,4)
        for _ in range(1500):
            if self.get('game_state')==1 and self.get('frame')>0: break
            self.step(1)
        self.settle(); self.drain_background()
        after=self.state()
        self.check(bytes(before.quests)==bytes(after.quests),'ordinary Continue preserves all earned quest bytes')
        self.check(bytes(before.roster.instances)==bytes(after.roster.instances),'ordinary Continue preserves every individual')
        stable_campaign=('chapter_flags','room_flags','optional_flags','story_seen','bridge','torches','relic','camp')
        self.check(all(getattr(before.campaign,n)==getattr(after.campaign,n) for n in stable_campaign),'ordinary Continue preserves all original chapter and discovery flags')
        self.check(all(bytes(getattr(before.roster,n))==bytes(getattr(after.roster,n)) for n in ('seen','obtained','rewards')),'ordinary Continue preserves complete collection and reward ledgers')
        self.check(bytes(before.equipment)==bytes(after.equipment),'ordinary Continue preserves exact equipment')
        self.check(self.get('game_state')==1,'ordinary Continue returns to active play')
        self.mode='journey'; self.snapshot(name+'-after-continue')
        self.coverage.append('cold-continue-'+name)
    def open_tab(self,tab):
        self.settle(); self.tap('START',2,4)
        self.check(self.get('game_state')==3 and self.get('journal_tab')==13,'Start opens the named journal hub')
        category={15:0,4:1,2:2,3:3,1:4,14:5,0:5,16:6}.get(tab,5)
        if category&1: self.tap('RIGHT',2,3)
        for _ in range(category//2): self.tap('DOWN',2,3)
        self.tap('A',2,3)
        if tab==0: self.tap('A',2,3)
        elif 5<=tab<=12:
            for _ in range(tab-4):self.tap('DOWN',2,3)
            self.tap('A',2,3)
        self.check(self.get('game_state')==3 and self.get('journal_tab')==tab,f'controller opens requested journal page {tab}')
    def close_menu(self): self.tap('START',2,4); self.settle()
    def guidance(self,name):
        self.settle()
        for tab,label in ((0,'objective'),(1,'map')):
            self.open_tab(tab); self.raw_step(3)
            self.e.screenshot(self.out/f'{self.chapter}-{name}-{label}.png')
            self.close_menu()
    def chapter_checkpoint(self,name):
        self.check(self.equipped_items()==[1,0,0,0,0],'main journey uses starter sword with all other gear slots empty')
        self.check(set(self.proof_state()['owned_forms']) <= GUARANTEED_FORMS,'main journey has no evolution or optional recruitment')
        self.guidance(name)
        self.cold_reboot(name)
    def report(self):
        if not hasattr(self,'e') or not self.e.ptr:return
        if not self._stream.closed:self._stream.flush()
        if not self._frames.closed:self._frames.flush()
        data={'suite':'journey-guidance-earned-main','candidate':self.candidate,'provenance':self.provenance,
              'baseline_diagnostic':self.args.baseline,'cross_rom_earned_sram_diagnostic':self.args.cross_rom_diagnostic,'controller_only':True,'game_ram_writes':0,
              'machine_state_imports':0,'historical_progress_imports':int(self.args.cross_rom_diagnostic),'chapter':self.chapter,
              'route_complete':self.route_complete,'checks':self.checks,'failures':self.failures,
              'snapshots':self.snapshots,'visited_rooms':self.visits,'transitions':self.transitions,
              'coverage':self.coverage,'acquisitions':self.acquisitions,'cases':self.cases,'metrics':self.metrics,
              'completed_chapters':self.history,'last_chapter_selected_forms':sorted(set(self.main_selections)),
              'final':self.proof_state(),'inputs_sha256':sha(self.out/'controller-inputs.jsonl.gz'),
              'native_frames_sha256':sha(self.out/'native-frames.jsonl.gz'),
              'scope':'Explicit cross-ROM earned-SRAM chapter diagnostic; no acceptance claim' if self.args.cross_rom_diagnostic else 'One same-candidate controller-earned main route; no full-collection claim',
              'timing_scope':'Observations retained; whole-build timing acceptance is a separate gate'}
        (self.out/'report.json').write_text(json.dumps(data,indent=2)+'\n')
    def close(self):
        self.report();self._stream.close();self._frames.close();self.report();self.e.close()

class OriginalJourney(OpeningJourneyMixin,Evidence,FeedbackCampaign):
    def __init__(self,args):
        self.out=args.output/'original';self.out.mkdir()
        self.source_rom=args.rom;self.source_symbols=args.symbols
        self.init_evidence(args,'original',original=True)
        old=campaign_tests.Emulator
        campaign_tests.Emulator=lambda rom:StrictNative(rom,args.bridge)
        try: EvolutionRun.__init__(self,args.rom,args.symbols,self.out,optional=False,exhaustive=False)
        finally:campaign_tests.Emulator=old
        # CampaignRun creates these arrays during its ordinary initialization.
        self.checks=[];self.transitions=[];self.candidate=dict(args.candidate)
        self.death_done=False;self.unsolved_return_done=False
        blank=self.e.bytes(0x0e000000,32768)
        self.check(len(set(blank))==1 and blank[0] in (0,255),'new cartridge has genuinely blank SRAM')
        self.provenance.update(initial_sram_sha256=hashlib.sha256(blank).hexdigest(),initial_sram_fill=blank[0])
    def settle(self):
        self.settle_save(); self.dialogs(); self.settle_save()
    def shot(self,name):
        self.raw_step(3);self.e.screenshot(self.out/(name+'.png'))
    def reload_case(self,name,expected_state=None):
        if self.get('game_state')==5:self.snapshot(name);return
        self.chapter_checkpoint(name)
    def nextroom(self,target,key='UP'):
        CampaignRun.nextroom(self,target,key)
        if target==5 and not self.unsolved_return_done:
            before=self.get('room_flags')
            CampaignRun.nextroom(self,4,'DOWN');CampaignRun.nextroom(self,5,'UP')
            self.check(self.get('room_flags')==before,'leaving unsolved sky mechanism and returning grants no puzzle progress')
            self.unsolved_return_done=True;self.coverage.append('unsolved-sky-puzzle-return')
    def chapter_two(self):
        # Natural death/retry is tested on the ridge before any mechanism work.
        CampaignRun.chapter_two(self)
    def hub(self,target):
        if target==9:
            self.check(self.get('room')==0,'core road starts at home')
            self.goto(y=109);self.goto(x=24);self.goto(y=116)
            for _ in range(120):
                if self.get('room')==9:break
                self.step(1,'LEFT')
            self.check(self.get('room')==9,'core entrance follows its current west road around village shop')
            self.step(24);self.dialogs()
        else:FeedbackCampaign.hub(self,target)
        if target==4 and not self.death_done:
            self.snapshot('ridge-before-natural-death')
            self.navigate(176,128)
            if self.get('summoned'):self.tap('B')
            for _ in range(4000):
                if self.get('game_state')==4:break
                self.step(2)
            self.check(self.get('game_state')==4,'ordinary ridge enemies defeat an idle player without health writes')
            flags=self.get('room_flags');self.shot('ridge-natural-death');self.tap('A',4,4);self.settle()
            self.check(self.get('room')==4 and self.get('game_state')==1 and self.e.read(self.sym['hero_hp_q4'])==self.e.read(self.sym['gear_stats'],2),'A performs ordinary death retry')
            self.check(self.get('room_flags')==flags,'retry preserves earned progress')
            self.death_done=True;self.coverage.append('natural-death-and-A-retry')
    def run(self):
        self.first_chapter();self.chapter_two();self.chapter_three();self.ending()
        self.check(self.get('chapter_flags')&15==15,'all three lights and original chapter celebration are earned')
        self.chapter_checkpoint('original-ending');self.route_complete=True;self.history=['original']
        return self.snapshot('handoff')

# Dynamic dispatch before the historical Covenants mask keeps each authored
# region's collision estimate scoped to that region.
def regional_base_mask(self):
    area=self.get('room')
    if area<22:
        key=(area,self.get('bridge_open'),self.get('room_flags'),self.state().quests.objectives[1],self.e.bytes(self.sym['region_game_crates'],8) if area==20 else b'')
        cache=getattr(self,'_early_masks',{})
        if key not in cache:cache[key]=RegionJourney.mask(self);self._early_masks=cache
        return cache[key]
    if area<38:return SouthernJourney.mask(self)
    if area<54:return UnderwaterJourney.mask(self)
    if area<62:return ReturnJourney.mask(self)
    if area<70:return HorizonsJourney.mask(self)
    return CovenantsJourney.mask(self)
# The mixin's super().mask resolves to this explicit region selector.
class RegionMaskDispatch(CovenantsJourney):
    mask=regional_base_mask

class RegionalJourney(Evidence,ConnectedRoadJourneyMixin,RegionMaskDispatch):
    def __init__(self,args,source_save,source_report):
        self.out=args.output/'regions';self.out.mkdir()
        self.source_rom=args.rom;self.source_symbols=args.symbols
        self.rom=self.out/'tested.gba';self.symbol_path=self.out/'tested.sym';self.elf=self.out/'tested.elf'
        for src,dst in ((args.rom,self.rom),(args.symbols,self.symbol_path),(args.rom.with_suffix('.elf'),self.elf)):shutil.copyfile(src,dst)
        self.init_evidence(args,'river')
        self.locals=elf_locals(self.elf,self.rom)
        rows=[p for line in self.symbol_path.read_text().splitlines() if len(p:=line.split())==3]
        counts=Counter(p[2] for p in rows)
        self.sym={p[2]:int(p[0],16) for p in rows if counts[p[2]]==1}
        self.target_sha=args.expected_rom_sha;self.symbol_sha=args.expected_symbols_sha
        self.source_manifest_sha=args.candidate['source_manifest_sha256']
        p=json.loads(source_report.read_text())
        assert p['controller_only'] and not p['game_ram_writes'] and not p['machine_state_imports']
        if not args.diagnostic_boundary_report:
            assert p['route_complete'] and not p['failures'] and all(c['passed'] for c in p['checks'])
        else:assert args.baseline or args.cross_rom_diagnostic,'A prior diagnostic boundary cannot count as candidate acceptance'
        if not args.cross_rom_diagnostic:assert p['candidate']==args.candidate
        else:self.provenance.update(source_candidate=p['candidate'],cross_rom_earned_sram_imports=1,historical_progress_imports=1)
        records=[r for r in p['snapshots'].values() if Path(r['sram_path'])==source_save]
        assert len(records)==1 and sha(source_save)==records[0]['sram_sha256']
        self.provenance.update(source_report=str(source_report),source_report_sha256=sha(source_report),
                               source_sram_sha256=sha(source_save),source_scope='explicit cross-ROM diagnostic from an earned chapter boundary' if args.cross_rom_diagnostic else 'same-candidate empty-SRAM earned original chapter' if not args.diagnostic_boundary_report else 'baseline diagnostic branch from a prior earned chapter boundary',
                               diagnostic_boundary_resume=bool(args.diagnostic_boundary_report))
        self.fixture=source_save
        self.minimal=True
        self.main_only=True
        self.layout=json.loads((args.source_root/'assets/region/layout.json').read_text())
        self.world=json.loads((args.source_root/'assets/world_manifest.json').read_text())
        self.campaign=json.loads((args.source_root/'assets/campaign_layouts.json').read_text())
        self.campaign_rooms={r['id']:r for r in self.campaign['rooms']}
        self.north=json.loads((args.source_root/'assets/northern_region/layout.json').read_text())
        self.scene=json.loads((args.source_root/'assets/southern_region/scene.json').read_text())
        self.magma_layout=json.loads((args.source_root/'assets/magma_region/layout.json').read_text())
        self.return_geometry=json.loads((args.source_root/'assets/return_region/geometry.json').read_text())
        self.covenants_geometry=json.loads((args.source_root/'assets/covenants_world/geometry.json').read_text())
        self.cv_rooms={r['id']:r for r in self.covenants_geometry['rooms']}
        self.e=StrictNative(self.rom,self.bridge);self.e.load_save(source_save);self.e.reset()
        self.descriptors={};self.mask_cache={}
        for prefix,start in (('north',22),('south',30),('magma',38),('underwater',46),('return',54),('horizons',62)):
            table=self.sym[prefix+'_art_rooms'];found=[]
            for stride in (20,28,32):
                candidate=[]
                for i in range(8):
                    address=table+i*stride;w,h=struct.unpack('<HH',self.e.bytes(address,4));bitmap=self.e.read(address+4)
                    if (w,h) not in ((240,160),(480,320),(480,160),(240,320)) or bitmap not in [v for k,v in self.sym.items() if k.startswith(prefix+'_background_')]:break
                    candidate.append(dict(address=address,width=w,height=h,bitmap=bitmap,stride=stride))
                if len(candidate)==8:found.append(candidate)
            assert len(found)==1,('ambiguous ROM room descriptor',prefix)
            self.descriptors.update({start+i:d for i,d in enumerate(found[0])})
        self.mode='cold_continue';self.step(160);self.tap('A',4,4)
        for _ in range(1500):
            if self.get('game_state')==1 and self.get('frame')>0:break
            self.step(1)
        self.settle();self.drain_background();self.mode='journey'
        expected_room=records[0]['status']['room'] if args.diagnostic_boundary_report else 0
        self.check(self.get('room')==expected_room and self.get('chapter_flags')&15==15,'same-candidate earned SRAM continues at its real chapter boundary')
        self.remember_prior()
    def settle(self):
        for _ in range(750):
            state=self.get('game_state')
            if state in (6,8,10,12,13):self.settle_save()
            elif state==2:self.tap('A',2,4)
            elif state==1 and ('scene_present_phase' in self.sym and self.get('scene_present_phase')):self.step(1)
            else:return
        raise AssertionError(('modal failed to finish',self.status()))
    def act(self,x,y,f=None):
        here=self.get('room');self.goto(x,y)
        if self.get('room')!=here:return
        if f is not None:self.face(f);self.settle()
        if self.get('room')!=here:return
        self.tap('A');self.settle()
    def ready(self):
        self.settle()
        for _ in range(1000):
            if not self.get('ability_cd'):break
            self.step(1)
        self.check(not self.get('ability_cd'),'companion cooldown completes without injected timing')
        if not self.get('summoned'):self.tap('B');self.settle()
    def assign(self,slot,form):
        r=self.roster();index=next(i for i,c in enumerate(r.instances) if c.flags&1 and c.form_id==form)
        self.open_tab(2)
        for _ in range(4):
            if self.get('quickparty_menu_slot')==slot:break
            self.tap('RIGHT',2,3)
        for _ in range(161):
            if self.get('quickparty_menu_candidate')==index:break
            self.tap('DOWN',2,3)
        self.tap('A',2,25);self.settle()
        if 'quickparty_menu_detail' in self.sym and self.get('quickparty_menu_detail'):self.tap('A',2,25);self.settle()
        self.close_menu()
        self.check(self.roster().party[slot]==index,f'controller assigns guaranteed form {form} to slot {slot}')
    def equip_item(self,slot,item):
        self.check((slot,item)==(0,1),'main route never requests upgraded equipment')
        if self.equipped_items()[slot]==item:return
        self.open_tab(4)
        for _ in range(5):
            if self.get('gear_menu_slot')==slot:break
            self.tap('RIGHT',2,3)
        for _ in range(50):
            ref=self.get('gear_menu_candidate');chosen=self.state().equipment.bag[ref].item_id if ref<48 else (1 if slot==0 else 0)
            if chosen==item:break
            self.tap('DOWN',2,3)
        self.tap('A',2,25);self.settle();self.close_menu()
        self.check(self.equipped_items()[slot]==item,'real menu equips starter sword')
    def set_command(self,command):
        if self.command()==command:return
        self.open_tab(3)
        for _ in range(12):
            c=self.selected()
            candidate=self.get('progression_menu_command')
            if candidate==command:break
            self.tap('RIGHT',2,4)
        self.tap('A',2,25);self.settle()
        if 'progression_menu_detail' in self.sym and self.get('progression_menu_detail'):self.tap('A',2,25);self.settle()
        self.close_menu()
        self.check(self.command()==command,f'real growth menu selects earned command {command}')
    def approach(self,key):
        here=self.get('room');o=self.object(key);x,y=o['approach'];cx,cy=o['center']
        nx=cx+(6 if x>cx else -6 if x<cx else 0);ny=cy+(6 if y>cy else -6 if y<cy else 0)
        blocked,w,h=self.mask()
        self.goto(nx,ny,radius=4) if not blocked[ny*w+nx] else self.goto(x,y,radius=4)
        if self.get('room')!=here:return False
        self.face(1 if y>cy else 0 if y<cy else 2 if x>cx else 3);self.settle()
        if self.get('room')!=here:return False
        self.check(abs(self.get('px')-cx)+abs(self.get('py')-cy)<18,f'{key} reaches authored interaction range')
        return True
    def use(self,key):
        if self.approach(key):self.tap('A');self.settle()
    def puzzle(self):
        area=self.get('room')
        prefix,size=('north',4) if area<30 else ('south',3) if area<38 else ('magma',4) if area<46 else ('underwater',8)
        return list(self.e.bytes(self.sym[prefix+'_game_puzzle'],size))
    def object(self,key):
        if 30<=self.get('room')<38:return SouthernJourney.object(self,key)
        if 38<=self.get('room')<46:return next(o for o in self.magma_layout['rooms'][self.get('room')-38]['objects'] if o['key']==key)
        raise AssertionError(('no current object dispatcher',self.get('room'),key))
    def path(self,tx,ty):
        blocked,w,h=self.mask();start=self.get('py')*w+self.get('px');goal=ty*w+tx
        if blocked[goal]:
            candidates=[(abs(x-tx)+abs(y-ty),x,y) for y in range(max(0,ty-3),min(h,ty+4)) for x in range(max(0,tx-3),min(w,tx+4)) if not blocked[y*w+x]]
            assert candidates,('blocked controller goal',self.status(),tx,ty)
            _,gx,gy=min(candidates);goal=gy*w+gx
        signature=(self.get('room'),w,h,goal,hash(bytes(blocked)))
        if getattr(self,'_path_signature',None)!=signature:
            parent=[-2]*(w*h);parent[goal]=-1;queue=deque([goal])
            while queue:
                p=queue.popleft();x=p%w
                for n in (p-1,p+1,p-w,p+w):
                    if 0<=n<w*h and abs(n%w-x)+abs(n//w-p//w)==1 and not blocked[n] and parent[n]==-2:
                        parent[n]=p;queue.append(n)
            self._path_signature=signature;self._path_parent=parent
        parent=self._path_parent
        assert 0<=start<len(parent) and parent[start]!=-2,('no controller walk route',self.status(),tx,ty)
        route=[];p=start
        while parent[p]!=-1:p=parent[p];route.append(p)
        return route,blocked,w
    def goto(self,tx,ty,radius=4):
        previous=getattr(self,'_navigation_goal',None);self._navigation_goal=(tx,ty)
        here=self.get('room')
        try:
            for _ in range(1600):
                self.settle()
                if self.get('room')!=here:return
                self.check(self.get('game_state')==1,'pathfinding moves only during active gameplay')
                x,y=self.get('px'),self.get('py');distance=abs(x-tx)+abs(y-ty)
                if distance<=radius:return
                path,blocked,w=self.path(tx,ty)
                if not path:return
                direction=path[0]-(y*w+x);length=1
                for j in range(1,len(path)):
                    if path[j]-path[j-1]!=direction:break
                    length+=1
                if length==1 and len(path)>length:
                    turn=path[length]-path[length-1];point=y*w+x
                    if 0<=point+turn*2<len(blocked) and not blocked[point+turn] and not blocked[point+turn*2]:
                        direction=turn;length=2
                if distance<=8:
                    point=y*w+x
                    axes=sorted(((abs(tx-x),1 if tx>x else -1),(abs(ty-y),w if ty>y else -w)),reverse=True)
                    for amount,near_direction in axes:
                        if amount and 0<=point+near_direction*2<len(blocked) and not blocked[point+near_direction] and not blocked[point+near_direction*2]:
                            direction=near_direction;break
                frames=1 if distance<=12 or length<=4 else max(1,min(12,int(length/1.25)))
                self.step(frames,{1:'RIGHT',-1:'LEFT',w:'DOWN',-w:'UP'}[direction])
            raise AssertionError(('controller pathfinding stalled',self.status(),tx,ty))
        finally:self._navigation_goal=previous
    def mask(self):
        # Edge apertures wrap compiled floor masks and live puzzle props. Avoid
        # walking over an unrelated ferry/stair while routing to an NPC.
        raw,w,h=ConnectedRoadJourneyMixin.mask(self);b=bytearray(raw)
        goal=getattr(self,'_navigation_goal',None)
        if goal and 'travel_entries' in self.sym:
            count=self.get('travel_entry_count');assert count<=64
            for i in range(count):
                area,action,target,spawn,x,y,rw,rh=struct.unpack('<4Bhh2B',self.e.bytes(self.sym['travel_entries']+10*i,10))
                if area!=self.get('room'):continue
                if target==getattr(self,'_entry_target',None):continue
                latch=self.locals.get('travel_feedback.c:latched')
                if latch and self.e.read(latch[0]+4*(i//32))&(1<<(i%32)):continue
                if x-4<=goal[0]<x+rw+4 and y-4<=goal[1]<y+rh+4:continue
                lo,hi=max(0,x),min(w,x+rw)
                for yy in range(max(0,y),min(h,y+rh)):b[yy*w+lo:yy*w+hi]=b'\1'*(hi-lo)
        return b,w,h
    def machine(self,*args):
        a=self.get('room')
        if a==29:return NorthernJourney.machine(self,*args)
        if a==37:return SouthernJourney.machine(self,*args)
        if a==45:return MagmaJourney.machine(self)
        raise AssertionError(('unknown machine',a))
    def entry(self,target):
        previous=getattr(self,'_entry_target',None);self._entry_target=target
        try:return self._entry(target)
        finally:self._entry_target=previous
    def _entry(self,target):
        here=self.get('room')
        if (here,target) in ((53,46),(45,38)):
            return ConnectedRoadJourneyMixin.entry(self,target)
        pair=self.road_pair(here,target)
        if pair:
            source,destination=pair;self.goto(*source['arrival'],radius=2);self.settle()
            self.check(self.get('room')==here,'road approach remains on its source map')
            key={'N':'UP','E':'RIGHT','S':'DOWN','W':'LEFT'}[source['edge']]
            for _ in range(600):
                if self.get('room')!=here:break
                self.step(1,key)
            self.settle();self.check(self.get('room')==target,f'ordinary {key} road crossing reaches {target}')
            requested=destination['saved_spawn']
            expected=0 if target==0 and requested in (1,2) else requested
            self.check(self.get('checkpoint_spawn')==expected,'road retains its canonical saved checkpoint (original village north arrival normalizes to0)')
            self.transitions[-1].update(verified_destination=target,travel_kind='physical_world_edge',source_edge=source['edge'],destination_edge=destination['edge'],requested_spawn=requested,canonical_spawn=expected,manifest_sha256=self.connected_road_manifest_sha256)
            return
        if (here,target)==(22,30):
            self.act(208,224,1);self.settle()
            self.check(self.get('room')==30,'ordinary Northern ferry reaches Southern arrival')
            if self.args.baseline:
                # Explicit diagnostic workaround for C4's unlatched y284
                # arrival. Candidate acceptance must not depend on this squeeze.
                start=[self.get('px'),self.get('py')]
                for _ in range(30):
                    if self.get('px')<=230:break
                    self.step(1,'LEFT')
                self.check(self.get('px') in (229,230),'diagnostic ferry squeeze reaches two-pixel outside lane')
                for _ in range(60):
                    if self.get('py')<=244:break
                    self.step(1,'UP')
                self.check(self.get('room')==30,'diagnostic ferry squeeze escapes old arrival bounce')
                self.cases.append({'known_baseline_defect':'South ferry spawn outside return-marker arrival latch','controller_workaround':True,'start':start,'end':[self.get('px'),self.get('py')]})
                self.coverage.append('baseline-only-ferry-arrival-workaround')
            elif not getattr(self,'_south_arrival_verified',False):
                self._south_arrival_verified=True
                self.check(self.get('checkpoint_spawn')==0,'ferry uses existing Southern checkpoint0')
                self.snapshot('southern-ferry-arrival')
                self.step(44,'UP');self.settle()
                self.check(self.get('room')==30 and self.get('py')<240,'held UP leaves ordinary Southern ferry arrival without bouncing')
                self.step(44,'DOWN');self.settle()
                self.check(self.get('room')==22,'after leaving the dock clearance, walking back returns once to North')
                self.act(208,224,1);self.settle()
                self.check(self.get('room')==30 and self.get('checkpoint_spawn')==0,'ordinary ferry can be re-entered without duplicate travel')
                self.cold_reboot('southern-ferry-spawn0')
                self.check(self.get('room')==30 and self.get('px')==240 and self.get('py')==284,'cold Continue preserves the existing Southern dock spawn')
                self.step(44,'UP');self.settle()
                self.check(self.get('room')==30 and self.get('py')<240,'held UP also leaves cold Southern dock Continue without bouncing')
                self.coverage.append('southern-ferry-live-and-cold-arrival-return-and-reentry')
            return
        if self.connected_door(target):return
        if here==16 and target==18:return self.foundry()
        if here==18 and target==16:return self.leave_interior(target)
        if 22<=here<30 and 22<=target<30:
            if target<here:return self.leave_interior(target)
            return NorthernJourney.entry(self,target)
        if 30<=here<38 and 30<=target<38:
            if target<here:return self.leave_interior(target)
            return SouthernJourney.entry(self,target)
        if 38<=here<46 and 38<=target<46:
            if target<here:return self.leave_interior(target)
            return MagmaJourney.entry(self,target)
        return CovenantsJourney.entry(self,target)
    def exit_north(self,target):return self.entry(target)
    def to_town(self):
        a=self.get('room')
        if 22<=a<30:
            while self.get('room')>=24:
                a=self.get('room');self.entry(22 if a in (24,25) else 23 if a==26 else a-1)
            if self.get('room')==23:self.entry(22)
        elif 30<=a<38:
            while self.get('room')>=32:
                a=self.get('room');self.entry(30 if a==32 else 31 if a in (33,34) else a-1)
            if self.get('room')==31:self.entry(30)
        elif 38<=a<46:
            if a==45:self.entry(38)
            else:MagmaJourney.to_town(self)
        elif 46<=a<54:self.travel(46)
    def measured(self,name,callback,**kwargs):
        start=self.e.frame;result=callback()
        self.cases.append({'name':name,'session':self.session,'start':start,'end':self.e.frame})
        return result
    def cadence(self,name,count=120,keys=None):
        return self.measured(name,lambda:[self.step(1,keys(n) if callable(keys) else keys or 0) for n in range(count)])
    cast_position=UnderwaterJourney.cast_position
    def remember_prior(self):
        self.old_ids={c.instance_id for c in self.live()};self.old_history=self.collection()
        self.old_equipped=bytes(self.state().equipment.equipped)
        self.prior_count=len(self.live());self.prior_history=len(self.collection())
        self.main_selections=[];self.main_only=True
    def river_route(self):
        self.travel(16);self.guidance('first-arrival');self.entry(17)
        self.assign(0,1);self.assign(1,4);self.assign(2,7);self.assign(3,10)
        self.act(264,216);self.cast(4,240,199)
        self.act(120,232);self.cast(4,98,44);self.cast(7,184,88);self.act(184,88)
        self.check(self.quest(2)==3 and 13 in self.collection(),'basin care earns base Water without evolution')
        self.assign(3,13);self.entry(16)
        self.entry(18)
        self.cast(1,48,72);self.cast(13,80,120);self.cast(7,96,80);self.act(96,80)
        self.check(self.quest(3)==3 and 16 in self.collection(),'three base powers earn Metal without training')
        self.entry(16);self.act(104,232)
        self.chapter_checkpoint('river-main');self.entry(22)
    def north_route(self):
        self.guidance('first-arrival');self.act(168,208)
        for x in (304,160):self.act(x,224)
        self.act(168,208);self.reward(11,19)
        self.assign(0,19);self.select_form(19);self.entry(23)
        self.act(240,208);self.act(320,208);self.act(352,176);self.reward(13,77)
        self.assign(1,77);self.select_form(19);self.entry(26)
        for room in (26,27,28):NorthernJourney.puzzle_room(self,room)
        NorthernJourney.machine(self,1);self.to_town();self.act(104,208)
        self.chapter_checkpoint('north-main');self.entry(30)
    def south_route(self):
        self.guidance('first-arrival');SouthernJourney.recruits_main(self)
        for room in (34,35,36):SouthernJourney.puzzle_room(self,room)
        SouthernJourney.machine(self,1);self.to_town();self.use('rest')
        self.check(self.quest(24)==3,'Southern main dungeon claimed without optional companions')
        self.chapter_checkpoint('south-main');self.entry(38)
    def magma_route(self):
        self.guidance('first-arrival');MagmaJourney.recruits_main(self)
        self.entry(42);self.clear_enemies();self.field(31,48,68,3)
        self.slide(0,['DOWN','DOWN']+['RIGHT']*6+['UP','UP'])
        self.check(self.state().quests.objectives[32]&1,'base heat and physical brick solve intake')
        self.entry(43);self.clear_enemies()
        self.slide(0,['DOWN','RIGHT','RIGHT'],side=2);self.slide(0,['UP']*4);self.slide(1,['LEFT','UP'])
        self.field(34,168,104)
        self.check(self.state().quests.objectives[32]&2,'base brace solves vault')
        self.entry(44);self.clear_enemies();self.field(31,48,68,3)
        self.slide(0,['DOWN','DOWN']+['RIGHT']*6+['UP','UP']);self.slide(1,['LEFT']+['UP']*3,side=2)
        self.field(34,168,104);self.goto(208,104);self.face(2)
        for _ in range(4):
            if self.state().quests.objectives[32]&4:break
            self.tap('A',2,24);self.settle()
        self.check(self.state().quests.objectives[32]&4,'starter sword opens prepared gallery pin')
        self.entry(45);MagmaJourney.machine(self);self.entry(38)
        self.target(160,176);self.target(112,248)
        self.check(self.quest(32)==3,'Magma dungeon reward is earned after walking home')
        self.chapter_checkpoint('magma-main');self.entry(46)
    def underwater_route(self):
        self.guidance('first-arrival');UnderwaterJourney.main_route(self)
        self.chapter_checkpoint('underwater-main')
    def return_route(self):
        ReturnJourney.main_route(self);self.chapter_checkpoint('return-main')
    def horizons_route(self):
        HorizonsJourney.main_route(self);self.chapter_checkpoint('horizons-main')
    def complete_story(self):
        self.travel(74);self.target(136,264,1);self.check(self.quest(62)==3,'upper circuit report claims q62')
        self.travel(70);self.target(128,272,1);self.check(self.quest(63)==1,'steward offers the shared porch homecoming')
        self.target(128,272,1);self.check(self.cv_local('porch_confirm')==1,'porch commitment asks for a deliberate second A')
        before=self.state_signature();self.tap('B');self.settle()
        self.check(self.state_signature()==before and not self.cv_local('porch_confirm'),'B defers the porch decision without losing earned work')
        self.snapshot('porch-decision-deferred');self.target(128,272,1)
        self.check(self.cv_local('porch_confirm')==1,'deferred porch decision can be reopened normally')
        self.tap('A');self.settle();self.check(self.state().quests.objectives[63]&1,'shared porch commitment is explicitly recorded')
        self.snapshot('porch-commitment-earned');self.travel(62)
        if self.get('summoned'):self.tap('B');self.settle()
        self.target(self.cv_local('npc_x'),self.cv_local('npc_y'),0)
        self.follow_resident(lambda:bool(self.state().quests.objectives[63]&2),'return companion walks the ordinary fairground path home',limit=1200)
        self.travel(0);self.target(120,94,1);self.target(120,94,1)
        self.check(self.quest(63)==3,'final homecoming is claimed through the elder conversation')
        self.step(8);self.settle();self.snapshot('final-ending')
        self.coverage.append('porch-decision-defer-reopen-commit-and-escorted-homecoming')
    def covenants_route(self):
        self.initialize_covenants()
        for i in range(4):
            getattr(self,'solve'+str(70+i))();self.invitation(i,accept=False)
        self.travel(70);self.target(128,272,1);self.check(self.quest(61)==3,'four lower works earn lower circuit report')
        self.chapter_checkpoint('lower-circuit')
        self.travel(74);self.target(136,264,1)
        for i in range(4,8):
            getattr(self,'solve'+str(70+i))();self.invitation(i,accept=False)
        self.complete_story()
        self.check(self.quest(63)==3 and self.state().quests.region_flags[22]==255,'all eight works and final homecoming are earned')
        self.check(self.state().quests.region_flags[23]==0,'all optional invitations stay deferred without preventing homecoming')
        self.check(self.collection()==sorted(GUARANTEED_FORMS),'main journey uses only twenty genuinely earned guaranteed base forms')
        self.chapter_checkpoint('homecoming')
        self.travel(16);self.guidance('final-reedhaven-revisit');self.travel(0);self.guidance('final-home-revisit')
    def run(self,start='river'):
        if self.args.diagnostic_boundary_report:
            start=self.args.diagnostic_start_chapter
            self.travel({'river':16,'north':22,'south':30,'magma':38,'underwater':46,'return':46,'horizons':0,'covenants':62}[start])
        for chapter in CHAPTERS[CHAPTERS.index(start):]:
            self.chapter=chapter;self.remember_prior()
            getattr(self,chapter+'_route')();self.history.append(chapter)
            self.report()
            if chapter==self.args.stop_after:
                self.route_complete=chapter=='covenants';self.report();return
        self.route_complete=True;self.report()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','symbols','bridge','source-root','source-manifest','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True)
    p.add_argument('--expected-elf-sha',required=True)
    p.add_argument('--expected-manifest-sha')
    p.add_argument('--cross-rom-diagnostic',action='store_true',help='explicit prepared chapter diagnostic from authenticated earned SRAM; never acceptance')
    p.add_argument('--diagnostic-boundary-report',type=Path)
    p.add_argument('--diagnostic-boundary-snapshot')
    p.add_argument('--diagnostic-start-chapter',choices=CHAPTERS[1:])
    p.add_argument('--diagnostic-original-report',type=Path,help='baseline-only resume of this harness completed original prefix')
    p.add_argument('--baseline',action='store_true',help='explicit pre-candidate route-development diagnostic')
    p.add_argument('--stop-after',choices=CHAPTERS,default='covenants')
    a=p.parse_args()
    for field in ('rom','symbols','bridge','source_root','source_manifest','output'):setattr(a,field,getattr(a,field).resolve())
    assert not a.output.exists() or not any(a.output.iterdir()),'Use fresh output; never overwrite evidence'
    assert sha(a.rom)==a.expected_rom_sha and sha(a.symbols)==a.expected_symbols_sha
    assert sha(a.rom.with_suffix('.elf'))==a.expected_elf_sha
    if a.expected_manifest_sha:assert sha(a.source_manifest)==a.expected_manifest_sha,'Source receipt differs from explicit manifest hash'
    manifest=json.loads(a.source_manifest.read_text())
    assert all(sha(a.source_root/name)==value for name,value in manifest.items()),'Candidate source manifest differs'
    a.output.mkdir(parents=True,exist_ok=True)
    a.candidate={'rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),'elf_sha256':a.expected_elf_sha,
                 'source_manifest_sha256':sha(a.source_manifest),'bridge_sha256':sha(a.bridge)}
    (a.output/'candidate.json').write_text(json.dumps(a.candidate,indent=2)+'\n')
    shutil.copyfile(a.source_manifest,a.output/'source-hashes.json')
    helpers={}
    for directory,pattern in (('tests','*.py'),('tools','mgba_runner.py')):
        for source in (ROOT/directory).glob(pattern):
            target=a.output/'helper-source'/directory/source.name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target);helpers[str(source.relative_to(ROOT))]=sha(target)
    (a.output/'helper-source-hashes.json').write_text(json.dumps(helpers,indent=2)+'\n')
    assert not a.cross_rom_diagnostic or a.diagnostic_boundary_report,'Cross-ROM mode requires an explicit authenticated chapter boundary'
    r=None
    try:
        if a.diagnostic_boundary_report:
            assert (a.baseline or a.cross_rom_diagnostic) and a.diagnostic_boundary_snapshot and a.diagnostic_start_chapter
            original=a.diagnostic_boundary_report.resolve();prior=json.loads(original.read_text())
            sram=Path(prior['snapshots'][a.diagnostic_boundary_snapshot]['sram_path'])
        elif a.diagnostic_original_report:
            assert a.baseline,'Prefix resume is diagnostic only; candidate acceptance must start empty'
            original=a.diagnostic_original_report.resolve();prior=json.loads(original.read_text())
            sram=Path(next(r for k,r in prior['snapshots'].items() if k=='original-handoff')['sram_path'])
        else:
            r=OriginalJourney(a);sram=r.run();r.report();original=r.out/'report.json';r.close();r=None
        if a.stop_after!='original':
            r=RegionalJourney(a,sram,original);r.run();r.report();r.close();r=None
        reports=[json.loads(path.read_text()) for path in (a.output/'original/report.json',a.output/'regions/report.json') if path.exists()]
        full=a.stop_after=='covenants' and len(reports)==2 and all(x['route_complete'] for x in reports)
        summary={'suite':'journey-guidance-empty-SRAM-through-homecoming','candidate':a.candidate,
                 'complete_fresh_main_journey':full,'accepted':False,
                 'requested_scope_completed':bool(reports and reports[-1].get('completed_chapters') and reports[-1]['completed_chapters'][-1]==a.stop_after and not any(r['failures'] for r in reports)),
                 'baseline_diagnostic':a.baseline,'cross_rom_earned_sram_diagnostic':a.cross_rom_diagnostic,'stop_after':a.stop_after,'controller_only':True,
                 'game_ram_writes':0,'machine_state_imports':0,'historical_progress_imports':int(a.cross_rom_diagnostic),
                 'passed_checks':sum(sum(c['passed'] for c in x['checks']) for x in reports),
                 'visited_rooms':sorted({v for x in reports for v in x['visited_rooms']}),
                 'reports':{str(path.relative_to(a.output)):sha(path) for path in (a.output/'original/report.json',a.output/'regions/report.json') if path.exists()}}
        (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        from journey_guidance_timing import summarize
        timing=summarize(a.output)
        summary=json.loads((a.output/'summary.json').read_text())
        print(json.dumps(summary,indent=2))
        return int(full and not a.baseline and not timing['pacing_passed'])
    except Exception as exc:
        if r:
            r.failures.append({'error':repr(exc),'status':r.status()});r.e.screenshot(r.out/'failure.png');r.close()
        traceback.print_exc();return 1

if __name__=='__main__':raise SystemExit(main())
