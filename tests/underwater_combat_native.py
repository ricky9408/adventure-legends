#!/usr/bin/env python3
"""Independent exact-ROM controller-earned Underwater combat/control acceptance.

No game RAM writes, acquisitions, enemy injection or cross-ROM machine states.
The input producer must be a successful full native journey, independently
hash-pinned. Every branch loads its paired exact-ROM state and SRAM together.
Failure evidence is retained; missed acceptance gates are never waived.
"""
from __future__ import annotations
import argparse, ctypes as C, hashlib, json, re, shutil, struct, traceback
from pathlib import Path
from underwater_journey import UnderwaterJourney, ROOT, digest, PLAY, PAUSE, DIALOG, SAVING, EVENT_PENDING, elf_locals
from northern_journey import newest_bank
from northern_combat_tests import NorthernCombat
from test_save5 import Save
from test_creatures import Roster, Instance

CYCLES=280896
DIRECTIONS=('DOWN','UP','LEFT','RIGHT')
QUICK=('UP','RIGHT','DOWN','LEFT')
START=(12,14,16,12,14,16,12,16,16,12,14,18,12,16,12,12,16,16,12,16,18,12,18,20)
ACTIVE=(18,12,24,6,32,20,20,18,24,28,36,4,16,24,24,15,16,18,24,14,24,16,24,4)
LIFE=(36,38,48,28,54,48,40,44,48,44,58,34,36,50,56,38,44,46,44,42,52,36,52,38)
PHASE=(4,2,0,3,1,0,3,4)
# Authored-card world offsets, independently transcribed, not sampled predicates.
TARGETS=dict(zip(range(67,91),((24,0),(28,0),(4,-12),(24,0),(38,0),(24,-11),(12,0),(30,0),(12,-10),(8,0),(38,0),(24,0),(8,0),(12,0),(0,0),(16,0),(16,10),(11,0),(6,0),(38,0),(24,0),(12,-11),(32,0),(28,8))))
GAPS={69:(24,0),72:(24,0),74:(20,0),75:(18,0),78:(24,8),80:(0,0),82:(0,0),83:(16,0),84:(0,0),88:(12,-8),89:(24,0),90:(24,0)}
REQUIREMENTS=('all24-native-equipped-cast','all24-native-damage','native-cooldown-no-double-hit','native-alternate-and-diagonal-controls','native-facing','native-safe-apertures','native-selector-freeze-same-family-legacy','native-all50-storage','native-all24-form-pixels','native-walking-camera-cast-cadence','native-wall-clipping')

class Segment(C.LittleEndianStructure):
    _fields_=[(n,C.c_int16) for n in ('x','y','tx','ty')]+[(n,C.c_uint8) for n in ('radius','kind','live','open')]
class Point(C.LittleEndianStructure):
    _fields_=[('x',C.c_int16),('y',C.c_int16)]
class Cast(C.LittleEndianStructure):
    _fields_=[('seg',Segment*12),('marks',Point*24),('previous',Point*6),('trail',Point*4)]+[(n,C.c_uint32) for n in ('caster','lease','token')]+[('serial',C.c_uint16*6),('caught_serial',C.c_uint16)]+[(n,C.c_int16) for n in ('entry_x','entry_y','crawl_x','crawl_y')]+[(n,C.c_uint8) for n in ('count','mark_count','hits','fields','caught','catch_age','spent','choice','aimed','dirty','geometry_key','art_live','boss_hit','stopped','crawl_mode','crawl_steps','trail_count')]+[('side',C.c_int8),('ink',C.c_uint8)]

class CastD(C.LittleEndianStructure):
    _fields_=[('seg',Segment*12),('marks',Point*24),('previous',Point*6),('trail',Point*4)]+[(n,C.c_uint32) for n in ('caster','lease','token')]+[('serial',C.c_uint16*6),('caught_serial',C.c_uint16)]+[(n,C.c_int16) for n in ('entry_x','entry_y','crawl_x','crawl_y','field_x','field_y','box_x0','box_y0','box_x1','box_y1')]+[(n,C.c_uint8) for n in ('count','mark_count','hits','fields','caught','catch_age','spent','choice','aimed','dirty','geometry_key','art_live','boss_hit','stopped','crawl_mode','crawl_steps','trail_count')]+[('side',C.c_int8)]+[(n,C.c_uint8) for n in ('ink','path_checked','field_radius','field_valid','field_result','box_known','box_open')]+[('collision',C.c_uint8*64)]

def tiled(raw):
    return b''.join(raw[(ty+y)*16+tx:(ty+y)*16+tx+8] for ty in (0,8) for tx in (0,8) for y in range(8))
def phase_damage(command,defender):
    matrix=((256,256,320,224,256,256),(256,256,256,320,224,256),(224,256,256,256,320,256),(320,224,256,256,256,256),(256,320,224,256,256,256))
    base=24 if (command-67)%3 else 16
    return (base*matrix[PHASE[(command-67)//3]][defender if defender<5 else 5]+128)//256

class UnderwaterCombat(UnderwaterJourney):
    arrows=NorthernCombat.arrows
    def __init__(self,rom,symbols,output,rom_sha,symbols_sha,source_report,source_sha,source_manifest,snapshot='11-all89-earned-town',diagnostic_partial=False,producer_source_root=None,cold_cross_rom=False):
        self.report_ready=False;self.diagnostic_partial=diagnostic_partial
        p=Path(source_report).resolve();assert digest(p)==source_sha,'Producer report must be explicitly hash-pinned'
        source=json.loads(p.read_text());assert source['suite']=='underwater-native-controller-journey'
        assert source['controller_only'] is True and source['game_ram_writes']==0
        assert source['checks']
        if not diagnostic_partial:
            assert not source['failures'] and all(c['passed'] is True for c in source['checks'])
            assert not source['provenance'].get('debug_matching_state_branch'),'A segmented diagnostic journey is not final acquisition acceptance'
        self.cross_rom=source['rom_sha256']!=rom_sha
        assert not self.cross_rom or (diagnostic_partial and cold_cross_rom),'Cross-ROM import is diagnostic-only explicitly authorized cold SRAM'
        if not self.cross_rom:assert source['symbols_sha256']==symbols_sha
        source_rom_sha=source['rom_sha256'];source_symbols_sha=source['symbols_sha256']
        assert source['provenance']['cross_rom_machine_state_loaded'] is False
        producer_sources={}
        for name,sha in source['test_sources'].items():
            candidates=((Path(producer_source_root)/name,) if producer_source_root else ())+(p.parent/'test-source'/name,p.parent/'test-source'/Path(name).name,ROOT/name)
            found=next((q for q in candidates if q.is_file() and digest(q)==sha),None)
            assert found is not None,('No exact pinned producer test source',name)
            producer_sources[name]=found
        super().__init__(rom,symbols,output,rom_sha,symbols_sha,fixture=Path(source['provenance']['fixture']),source_manifest=source_manifest)
        if not self.cross_rom:assert source['source_manifest_sha256']==self.source_manifest_sha
        assert digest(p.parent/'tested.elf')==source['elf_sha256']
        assert digest(p.parent/'tested.gba')==source_rom_sha
        elf_locals(p.parent/'tested.elf',p.parent/'tested.gba')
        if not self.cross_rom:assert source['elf_sha256']==digest(self.elf)
        self.source_report=source;self.source_path=p;self.source_sha=source_sha
        self.acquisition_reports=[source];self.acquisition_chain=[];child=source
        while child['provenance'].get('debug_matching_state_branch'):
            link=child['provenance']['debug_matching_state_branch'];ancestor_path=Path(link['source_report']);ancestor_path=ancestor_path if ancestor_path.is_absolute() else ROOT/ancestor_path
            assert digest(ancestor_path)==link['report_sha256']
            ancestor=json.loads(ancestor_path.read_text());assert ancestor['rom_sha256']==link['source_rom_sha256']==source_rom_sha and ancestor['symbols_sha256']==source_symbols_sha
            paired=next((r for r in ancestor['snapshots'].values() if r['state_sha256']==link['state_sha256'] and r['sram_sha256']==link['sram_sha256']),None);assert paired is not None
            assert digest(paired['state_path'])==link['state_sha256'] and digest(paired['sram_path'])==link['sram_sha256']
            self.acquisition_chain.append({'path':str(ancestor_path),'sha256':digest(ancestor_path),'retained_failures':ancestor['failures'],'paired_state_sha256':link['state_sha256'],'paired_sram_sha256':link['sram_sha256']})
            self.acquisition_reports.append(ancestor);child=ancestor
        self.source_evidence={'report_path':str(p),'report_sha256':source_sha,'source_rom_sha256':source_rom_sha,'source_symbols_sha256':source_symbols_sha,'source_elf_sha256':source['elf_sha256'],'source_manifest_sha256':source['source_manifest_sha256'],'cross_rom_sram_import':self.cross_rom,'cross_rom_machine_state_loaded':False,'policy':'Exact-ROM hash-paired state and SRAM only','source_sram_ancestor':source['provenance'],'producer_test_sources':source['test_sources'],'verified_matching_ROM_debug_chain':self.acquisition_chain}
        shutil.copyfile(p,self.out/'acquisition-source-report.json')
        for name,q in producer_sources.items():
            dest=self.out/'acquisition-test-source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(q,dest)
        self.source_snapshot=self.import_snapshot(snapshot)
        rec=self.snapshots[self.source_snapshot]
        if not diagnostic_partial:
            assert len(rec['obtained_form_ids'])==89 and len(rec['owned_form_ids'])==50
            assert set(range(49,73))<=set(rec['obtained_form_ids'])
        self.source_evidence.update(producer_failed_overall=bool(source['failures']),diagnostic_only=diagnostic_partial,excluded_from_final_acceptance=diagnostic_partial)
        self.source_evidence.update(source_retained_instance_ids=rec['sram_instance_ids'],snapshot=snapshot,state_sha256=rec['state_sha256'],sram_sha256=rec['sram_sha256'],owned_forms=rec['owned_form_ids'],historical_forms=rec['obtained_form_ids'])
        self.branch_loads=[];self.screenshots=[];self.cast_commands=[];self.damage_commands=[];self.covered=[];self.native_write_attempts=[];self.pixel_checks=[];self.issues=[];self.case_outcomes={}
        self.active=list(ACTIVE);self.life=list(LIFE);self.cooldowns=[120 if (c-67)%3 else 90 for c in range(67,91)]
        spec_addr,spec_size=self.locals['underwater_powers.c:specs'];assert spec_size==144
        gate_contract=tuple(self.e.bytes(spec_addr+10*6,6))
        assert gate_contract in ((14,36,58,120,24,3),(14,132,154,180,24,3)),('Unreviewed command77 contract',gate_contract)
        if gate_contract==(14,132,154,180,24,3):self.active[10]=132;self.life[10]=154;self.cooldowns[10]=180
        self.source_evidence['command77_authored_contract']={'startup':14,'active':self.active[10],'lifetime':self.life[10],'cooldown':self.cooldowns[10],'damage_q4':24,'phase':3}
        self.cast_address,self.cast_size=self.locals['underwater_powers.c:cast'];self.cast_type={336:Cast,416:CastD}.get(self.cast_size);assert self.cast_type is not None and self.cast_size==C.sizeof(self.cast_type),('Unreviewed Cast ABI',self.cast_size)
        self.observer_abi={'elf_sha256':digest(self.elf),'STT_FILE':'underwater_powers.c','object':'cast','address':self.cast_address,'size':self.cast_size,'offsets':{name:getattr(self.cast_type,name).offset for name,_ in self.cast_type._fields_},'read_only':True}
        self.source_checks={p:digest(self.source_root/p)==v for p,v in self.source_hashes.items()}
        self.test_sources['tests/underwater_combat_native.py']=digest(Path(__file__))
        for name in ('tests/northern_combat_tests.py','tests/region_combat_tests.py','tests/test_save5.py','tests/test_save4.py','tests/test_creatures.py'):
            self.test_sources[name]=digest(ROOT/name)
        for name,sha in self.test_sources.items():
            q=self.out/'test-source'/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,q);assert digest(q)==sha
        def deny(*args,**kwargs):
            self.native_write_attempts.append(repr(args));raise AssertionError('Game RAM writes are forbidden')
        self.e.write=deny;self.e.lib.eb_write=deny
        src=(self.source_root/'src/game.c').read_text();self.cache_stride=int(re.search(r'#define\s+CACHE_FIELDS\s+(\d+)',src)[1])
        self.report_ready=True;self.report()
    def import_snapshot(self,name,source=None):
        source=source or self.source_report
        rec=dict(source['snapshots'][name]);assert (rec['rom_sha256'],rec['symbols_sha256'])==(source['rom_sha256'],source['symbols_sha256'])
        assert rec['rom_sha256']==self.target_sha or self.cross_rom
        key='source-'+('ancestor'+str(self.acquisition_reports.index(source))+'-' if source is not self.source_report else '')+name
        for kind,suffix in (('state','.state'),('sram','.sav')):
            q=Path(rec[kind+'_path']);assert digest(q)==rec[kind+'_sha256']
            if kind=='state' and self.cross_rom:rec[kind+'_path']=None;continue
            dest=self.out/(key+suffix);shutil.copyfile(q,dest);rec[kind+'_path']=str(dest)
        bank=newest_bank(Path(rec['sram_path']).read_bytes());assert int.from_bytes(bank[12:14],'little')==6
        retained=[(bank[160+i*24],int.from_bytes(bank[168+i*24:172+i*24],'little')) for i in range(160) if bank[161+i*24]&1]
        history=[i+1 for i in range(128) if bank[112+(i>>3)]&(1<<(i&7))]
        # Some uncommitted intermediate snapshots need not duplicate current RAM in
        # SRAM; final earned source must, and every restored state keeps its own SRAM.
        if name=='11-all89-earned-town':
            assert [f for f,_ in retained]==rec['owned_form_ids'] and history==rec['obtained_form_ids']
            assert len({i for _,i in retained})==len(retained) and all(i for _,i in retained)
        rec['sram_instance_ids']=[i for _,i in retained]
        self.snapshots[key]=rec;return key
    def report(self):
        if not self.report_ready:return
        data={'suite':'underwater-native-combat-controls','diagnostic_only':self.diagnostic_partial,'excluded_from_final_acceptance':self.diagnostic_partial,'controller_only':True,'game_ram_writes':0,'game_ram_write_attempts':self.native_write_attempts,'synthetic_gameplay':False,'player_facing':False,**self.candidate,'source_manifest_sha256':self.source_manifest_sha,'frozen_source_checks':self.source_checks,'provenance':self.source_evidence,'observer_abi':self.observer_abi,'test_sources':self.test_sources,'commands_equipped_and_cast':sorted(set(self.cast_commands)),'commands_native_damage_accepted':sorted(set(self.damage_commands)),'requirements_covered':self.covered,'requirements_not_accepted':[x for x in REQUIREMENTS if x not in self.covered],'checks':self.checks,'failures':self.failures,'issues':self.issues,'case_outcomes':self.case_outcomes,'cases':self.cases,'frame_windows':self.frame_windows,'pixel_checks':self.pixel_checks,'screenshots':self.screenshots,'branch_loads':self.branch_loads,'snapshots':self.snapshots,'inputs':self.inputs,'timing_source':'Actual mGBA hardware frame counter, sampled engine update counter and displayed Mode4 page flips, plus emulated GBA cycle timer; never host FPS','timing_caveat':'render_cycles includes update/save/render but excludes final VBlank wait/OAM commit, so separate hardware update/page flip cadence is mandatory','limits':['No physical GBA test','No orchestral audio claim','Synthetic host suite owns exhaustive serial wrap and all geometry sets; this suite records only controller-reached cases','No full-engine stack high-water measurement']}
        (self.out/'underwater-combat-native.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    def restore(self,name):
        row=self.snapshots[name];super().restore(name)
        self.branch_loads.append({'snapshot':name,'rom_sha256':self.target_sha,'state_sha256':row['state_sha256'],'sram_sha256':row['sram_sha256'],'matched_sram_loaded_before_state':True})
    def boot(self):
        if self.diagnostic_partial:
            self.e.load_save(self.snapshots[self.source_snapshot]['sram_path']);self.e.reset();self.step(150);self.tap('START',2,50);self.settle();self.source_evidence['source_machine_state_loaded']=False;self.source_evidence['source_sram_cold_boot']=True
        else:self.restore(self.source_snapshot)
        self.check([c.form_id for c in self.live()]==self.source_evidence['owned_forms'],'authenticated native source retains exact genuinely earned individuals')
        self.check(self.collection()==self.source_evidence['historical_forms'],'authenticated native source retains exact earned histories')
        self.check([c.instance_id for c in self.live()]==self.source_evidence['source_retained_instance_ids'],'native source retains exact earned individual IDs without replacement or renumbering')
        self.to_town();self.target(80,256);self.ready();self.step(140);self.snapshot('combat-town-source')
        self.forms={c.form_id for c in self.live()}
    def power(self):
        p={n:self.get('underwater_power_'+n) for n in ('kind','time','form','direction','origin_x','origin_y','age','cooldown','cast_time','phase')}
        c=self.cast_type.from_buffer_copy(self.e.bytes(self.cast_address,self.cast_size))
        for n,t in self.cast_type._fields_:
            v=getattr(c,n)
            if n=='seg':p['segments']=[{k:getattr(s,k) for k,_ in Segment._fields_} for s in v[:c.count]]
            elif n in ('marks','previous','trail'):p[n]=[[s.x,s.y] for s in (v[:c.mark_count] if n=='marks' else v[:c.trail_count] if n=='trail' else v)]
            elif n in ('serial','collision'):p[n]=list(v)
            else:p[n]=v
        p['global_cooldown']=self.get('ability_cd');p['tile_owner']=self.local('tile_owner',file='northern_powers.c')
        return p
    def enemies(self):
        rows=super().enemies()
        for i,e in enumerate(rows):
            e.update(index=i,windup=self.e.read(self.sym['enemy_windups']+i*4),clock=self.e.read(self.sym['enemy_clocks']+i*4),slow=self.e.read(self.sym['slowed_enemies']+i,1),root=self.e.read(self.sym['rooted_enemies']+i*4),stagger=self.e.read(self.sym['enemy_stagger_ticks']+i,1))
        return rows
    def display_camera(self):
        page=int(bool(self.e.read(0x04000000,2)&16));a=self.sym['cache_fields']+4*self.cache_stride*page
        return [self.e.read(a+4*17),self.e.read(a+4*18)]
    def native_selection(self):
        base=self.sym['adventure_save']+Save.roster.offset;party=self.e.read(base+Roster.selected_party.offset,1);slot=self.e.read(base+Roster.party.offset+party,1)
        assert party<4 and slot<160
        return party,Instance.from_buffer_copy(self.e.bytes(base+Roster.instances.offset+slot*C.sizeof(Instance),C.sizeof(Instance)))
    def oam_occupancy(self):
        objects=self.oam();counts=[0]*160;widths=[0]*160
        for o in objects:
            for y in range(max(0,o['y']),min(160,o['y']+o['h'])):
                counts[y]+=1;widths[y]+=o['w']
        return dict(active_entries=len(objects),maximum_sprites_per_line=max(counts),maximum_summed_sprite_width_per_line=max(widths),line_of_maximum_width=widths.index(max(widths)),basis='Actual displayed OAM, unscaled OBJ; summed source widths are occupancy evidence, not a physical-hardware render-time claim')
    def row(self):
        party,selected=self.native_selection()
        return dict(hardware_frame=self.e.frame,game_frame=self.get('frame'),hero=[self.get('px'),self.get('py')],camera=self.display_camera(),selected_form=selected.form_id,selected_id=selected.instance_id,selected_party=party,command=selected.equipped[selected.selected_command],power=self.power(),enemies=self.enemies(),shots=self.shots(),arrows=self.arrows(),hp_q4=self.hp_q4(),hitstop=self.get('hitstop'),invuln=self.get('invuln'),state=self.get('game_state'),cycles=self.get('render_cycles'),obj_count=self.get('obj_count'),displayed_page=self.e.read(0x04000000,2)&16,quickparty_open=self.get('quickparty_open'),quickparty_candidate=self.get('quickparty_candidate'),gfx_companion_frame=self.get('gfx_companion_frame'),summoned=self.get('summoned'),face=self.get('face'),oam_occupancy=self.oam_occupancy())
    def photograph(self,label):
        _,selected=self.native_selection()
        p=self.out/(label+'.png');self.e.screenshot(p);row=dict(path=str(p),sha256=digest(p),dimensions=[240,160],hardware_frame=self.e.frame,form=selected.form_id,command=selected.equipped[selected.selected_command],age=self.get('underwater_power_age'),case=getattr(self,'current_case',None));self.screenshots.append(row);return row
    def power_tile_check(self,command,active,label):
        particle=self.sym['underwater_power_particles']+(command-67)*128
        requests=[('hollow',self.e.bytes(particle,64),15616 if active else 16192)]
        if active:requests.append(('solid',self.e.bytes(particle+64,64),16192))
        else:requests.append(('emblem',tiled(self.e.bytes(self.sym['underwater_power_marks']+(command-67)*256,256)),15616))
        checks=[]
        for name,expected,offset in requests:
            actual=self.e.bytes(0x06014000+offset,len(expected));passed=actual==expected
            record=dict(label=label,command=command,phase='active' if active else 'startup',tile=name,expected_sha256=hashlib.sha256(expected).hexdigest(),actual_sha256=hashlib.sha256(actual).hexdigest(),passed=passed)
            checks.append(record);self.pixel_checks.append(record);self.checks.append({'label':label+' native '+name+' tiles match exact ROM source','passed':passed,'frame':self.e.frame})
            if not passed:self.failures.append({'case':getattr(self,'current_case',label),'kind':'native-power-tile-mismatch',**record})
        return checks
    def trace(self,label,count,keys=None,capture=False):
        previous=self.row();rows=[]
        for n in range(count):
            key=keys(n) if keys else 0;self.step(1,key);r=self.row();r.update(keys=key,update_delta=(r['game_frame']-previous['game_frame'])&0xffffffff,page_flip=r['displayed_page']!=previous['displayed_page']);rows.append(r);previous=r
            if capture and r['power']['time'] and r['power']['kind'] in range(67,91) and r['power']['age'] in (0,START[r['power']['kind']-67]):r['native_power_tile_checks']=self.power_tile_check(r['power']['kind'],r['power']['age']>0,label)
            if capture and (n in (0,2,8,12,16,20,26,35,48) or (r['command'] in range(67,91) and r['power']['age'] in (START[r['command']-67],START[r['command']-67]+4,START[r['command']-67]+10))):self.photograph(label+'-'+str(n))
            if capture and r['power']['time'] and r['power']['age'] in (0,START[r['power']['kind']-67],START[r['power']['kind']-67]+4,START[r['power']['kind']-67]+10) and r['selected_form'] in range(49,73):self.pixel_check(label+'-age'+str(r['power']['age']))
        window=dict(name=label,hardware_frames=count,updates=sum(r['update_delta'] for r in rows),page_flips=sum(r['page_flip'] for r in rows),max_cycles=max(r['cycles'] for r in rows),max_oam=max(r['obj_count'] for r in rows),camera_positions=len({tuple(r['camera']) for r in rows}),trace=rows)
        bad=[dict(index=n,hardware_frame=r['hardware_frame'],update_delta=r['update_delta'],page_flip=r['page_flip'],cycles=r['cycles'],age=r['power']['age'],state=r['state'],keys=r['keys']) for n,r in enumerate(rows) if r['update_delta']!=1 or not r['page_flip'] or r['cycles']>=CYCLES or r['obj_count']>128]
        window['cadence_failures']=bad;self.frame_windows.append(window)
        self.checks.append({'label':label+' strict native update/page/cycle/OAM budget','passed':not bad,'frame':self.e.frame})
        if bad:
            issue={'case':getattr(self,'current_case',label),'kind':'native-cadence','window':label,'max_cycles':window['max_cycles'],'bad_hardware_frames':bad};self.failures.append(issue);print('CADENCE FAILURE',label,json.dumps(bad[:5]),flush=True)
        self.report();return rows
    def owner(self,cmd):
        f=cmd-18
        return f if f in self.forms else f+1 if f+1 in self.forms else None
    def prepare(self,cmd,field=True):
        self.restore('combat-town-source');form=self.owner(cmd);self.check(form is not None,'command'+str(cmd)+' has a genuinely earned native owner')
        self.owned_select(form);self.set_command(cmd);self.ready()
        if field:self.entry(47)
        self.check(self.command()==cmd,'actual Growth menu equips command'+str(cmd));self.ready()
    def align(self,x,y,direction):
        dx,dy=((0,1),(0,-1),(-1,0),(1,0))[direction];self.goto(x-dx*2,y-dy*2,radius=2)
        for _ in range(20):
            ex,ey=x-dx*2-self.get('px'),y-dy*2-self.get('py')
            if abs(ex)+abs(ey)<=1:break
            self.step(1,('RIGHT' if ex>0 else 'LEFT') if abs(ex)>=abs(ey) else ('DOWN' if ey>0 else 'UP'))
        self.step(1,DIRECTIONS[direction]);self.step(1)
        self.check(self.get('face')==direction,'ordinary D-pad movement establishes actual cast facing')
    def pixel_check(self,label):
        _,selected=self.native_selection();form=selected.form_id;code=self.get('gfx_companion_frame');direction=code%16//4;ids=list(self.e.bytes(self.sym['underwater_creature_form_ids'],24));index=ids.index(form)
        casting=bool(code&524288);pose=(code//1048576) if casting else None
        pointer=self.sym['underwater_creature_ability_frames']+((index*4+direction)*3+pose)*256 if casting else self.sym['underwater_creature_direction_frames']+((index*4+direction)*4+code%4)*256
        expected=tiled(self.e.bytes(pointer,256));actual=self.e.bytes(0x06014000+6400,256)
        row=dict(label=label,form=form,instance_id=selected.instance_id,code=code,casting=casting,pose=pose,direction=direction,expected_sha256=hashlib.sha256(expected).hexdigest(),actual_sha256=hashlib.sha256(actual).hexdigest(),passed=expected==actual)
        self.pixel_checks.append(row);self.check(expected==actual,label+' selected individual OBJ tiles match exact authored native ROM pose');return row
    def cast(self,cmd,count=None,keys=None,label=None):
        before=self.row();rows=self.trace(label or 'cast-'+str(cmd),count or self.life[cmd-67]+5,lambda n:'R' if n==0 else keys(n) if keys else 0,True)
        if count is None and rows[-1]['power']['time']:
            # Hardware misses are already failures, but keep observing the same
            # admitted cast until its real simulation lifetime expires.
            for tail in range(3):
                if not rows[-1]['power']['time']:break
                offset=len(rows);rows += self.trace((label or 'cast-'+str(cmd))+'-tail'+str(tail),rows[-1]['power']['time']+3,lambda n:keys(n+offset) if keys else 0,True)
        start=next((r for r in rows if r['power']['kind']==cmd and r['power']['time']>0),None)
        self.check(start is not None,'one-frame R starts actual command'+str(cmd))
        self.check(start['power']['caster']==before['selected_id'] and start['power']['form']==before['selected_form'],'cast binds actual selected individual and form')
        self.check(start['power']['time']==self.life[cmd-67] and start['power']['age']==0,'cast begins with authored lifetime without pre-aged state')
        self.check(start['power']['phase']==PHASE[(cmd-67)//3] and start['power']['tile_owner']==5,'cast uses authored phase and Underwater shared lease')
        cd=self.cooldowns[cmd-67]
        self.check(cd-8<=start['power']['global_cooldown']<=cd,'native cast applies bounded authored cooldown')
        self.check(all(r['power']['count']<=12 and r['power']['mark_count']<=24 for r in rows),'native cast geometry and render lists remain bounded')
        self.cast_commands.append(cmd)
        return before,rows
    def direct(self,cmd,direction=1,gap=False):
        self.prepare(cmd);f,s=(GAPS if gap else TARGETS)[cmd];target=2
        if cmd in (71,77) and not gap:target=3
        enemy=self.enemies()[target];dx,dy=((0,1),(0,-1),(-1,0),(1,0))[direction]
        self.align(enemy['x']-f*dx+s*dy,enemy['y']-f*dy-s*dx,direction);self.ready()
        if cmd==71 and not gap:
            for _ in range(3):
                enemy=self.enemies()[target];self.align(enemy['x']-f*dx+s*dy,enemy['y']-f*dy-s*dx,direction)
        before,rows=self.cast(cmd,keys=(lambda n:'LEFT' if 1<=n<=12 else 0) if cmd==81 and not gap else None,label=('gap-' if gap else 'direct-')+str(cmd)+'-facing'+str(direction))
        hp=before['enemies'][target]['hp_q4'];damage=hp-rows[-1]['enemies'][target]['hp_q4'];expected=0 if gap else phase_damage(cmd,before['enemies'][target]['phase']);changes=[r for a,r in zip([before]+rows,rows) if a['enemies'][target]['hp_q4']!=r['enemies'][target]['hp_q4']]
        result={'case':getattr(self,'current_case','direct'),'command':cmd,'target':target,'expected_q4':expected,'actual_q4':damage,'direction':direction,'before':before,'trace':rows,'damage_changes':len(changes),'gap':gap};self.cases.append(result);self.report()
        self.check(damage==expected,('safe aperture preserves' if gap else 'real pre-existing enemy receives exact once-only damage from')+' command'+str(cmd))
        self.check(len(changes)==(0 if gap else 1),'native per-target damage budget cannot be paid twice')
        if changes:self.check(START[cmd-67]<=changes[0]['power']['age']<START[cmd-67]+self.active[cmd-67],'real damage occurs only inside active window')
        self.check(not rows[-1]['power']['time'] and rows[-1]['power']['tile_owner']==0,'expiry releases native shared OBJ lease')
        self.check(rows[-1]['power']['global_cooldown']>0,'effect expiry cannot refund remaining cooldown')
        self.pixel_check('recovered-'+str(cmd));result['passed']=True
        if not gap:self.damage_commands.append(cmd)
    def alternate(self,cmd):
        self.prepare(cmd,False);self.goto(240,200);self.face(1);self.ready();self.snapshot('alternate-ready-'+str(cmd),False)
        acceptable='UP' if cmd in (69,83,90) else 'RIGHT'
        for variant,key,accept in (('single',acceptable,cmd not in (67,71,77,81)),('diagonal','UP+RIGHT',False),('opposed','LEFT+RIGHT',False)):
            self.restore('alternate-ready-'+str(cmd));before,rows=self.cast(cmd,keys=lambda n:key if n==2 else 'LEFT' if n==4 else 0,label='alternate-'+str(cmd)+'-'+variant)
            if cmd in (67,71,77,81):self.check(not any(r['power']['aimed'] for r in rows),'fixed command ignores alternate direction edges')
            else:
                self.check(bool(rows[2]['power']['aimed'])==accept,'only one valid cardinal direction edge changes the startup alternate')
                if accept:
                    expected=0 if cmd==69 else 1
                    self.check(rows[2]['power']['choice' if cmd==69 else 'side']==expected,'native valid edge changes authored corner or side')
                    self.check(rows[4]['power']['side']==rows[2]['power']['side'] and rows[4]['power']['choice']==rows[2]['power']['choice'],'second direction cannot replace the one startup choice')
            origin=[rows[0]['power']['origin_x'],rows[0]['power']['origin_y']]
            self.check(all([r['power']['origin_x'],r['power']['origin_y']]==origin for r in rows),'moving D-pad input does not move the cast origin')
            self.cases.append(dict(case='alternate-'+str(cmd)+'-'+variant,accepted_first_edge=accept,passed=True))
    def command77(self):
        self.prepare(77);self.goto(304,126,radius=2);self.face(1);self.ready()
        # Place the real ordinary melee target just outside the far entry edge.
        # No actor coordinates are altered by the observer.
        for _ in range(3):
            e=self.enemies()[3];self.align(e['x'],e['y']+38,1)
        before,rows=self.cast(77,count=self.life[10]+7,label='command77-natural-entry-crossing')
        origin=rows[0]['power']['origin_y'];fs=[origin-r['enemies'][3]['y'] for r in rows];caught=[r for r in rows if r['power']['caught']==3]
        damage=before['enemies'][3]['hp_q4']-rows[-1]['enemies'][3]['hp_q4'];record=dict(case='command77-natural-entry-crossing',before=before,trace=rows,forward_range=[min(fs),max(fs)],caught_frames=len(caught),damage_q4=damage,required_damage_q4=phase_damage(77,before['enemies'][3]['phase']),ordinary_ai_speed='One axis moves at most1px every3 active updates; axis alternates, straight-axis motion at most1px per6updates',required_crossing='entry f<=33 to exit f<15, minimum19px',active_updates=self.active[10],max_total_ai_steps=(self.active[10]+2)//3,max_straight_axis_steps=(self.active[10]+5)//6)
        self.cases.append(record);self.report()
        self.check(bool(caught),'native pre-existing ordinary enemy honestly crosses command77 entry edge')
        self.check(damage==record['required_damage_q4'],'command77 real ordinary foe can complete its required crossing before expiry')
        self.damage_commands.append(77)
    def fresh_hostile_shot(self):
        for _ in range(180):
            if any(s['life']>=75 and s['owner'] for s in self.shots()):break
            self.step(1)
        self.check(any(s['life']>=75 and s['owner'] for s in self.shots()),'actual ordinary ranger supplies a live hostile projectile before selector freeze')
    def selector(self):
        self.restore('combat-town-source')
        for slot,form in enumerate((50,51,59,33)):self.assign(slot,form)
        self.select_form(50);self.set_command(68);self.select_form(51);self.set_command(69);self.select_form(33);self.set_command(43);self.select_form(50);self.ready();self.entry(47);self.goto(380,160);self.face(1);self.ready();self.fresh_hostile_shot();self.snapshot('selector-ready',False)
        for cold in (True,False):
            if cold:self.restore('selector-ready')
            else:self.fresh_hostile_shot()
            self.step(1,'R');self.step(1);before=self.row()
            rows=self.trace(('cold' if cold else 'hot')+'-live-L-right-selector',28,lambda n:'L+RIGHT',True);frozen=rows[-1]
            self.check(all(r['quickparty_open'] for r in rows),'L plus direction holds actual quick selector open')
            self.check(all(r['power']==before['power'] and r['enemies']==before['enemies'] and r['shots']==before['shots'] and r['arrows']==before['arrows'] and r['hero']==before['hero'] for r in rows),'selector freezes cast, cooldown, actual ordinary enemies, hostile projectiles and movement')
            release=self.trace('selector-release-to-same-family',2)[-1]
            self.check(release['selected_form']==51 and release['selected_id']!=before['selected_id'],'release commits different same-family branch individual')
            self.check(release['power']['caster']==before['selected_id'],'same-family selection cannot steal active cast')
            self.check(release['power']['fields']==255 and release['power']['aimed']==1,'actual selection change invalidates field rights and alternate aim')
            self.step(1,'R');self.check(self.power()['caster']==before['selected_id'],'new branch cannot recast over previous individual cooldown')
            self.select_form(50);self.check(self.power()['fields']==255,'away-and-back selection does not restore field rights');self.ready()
        for combination in ('UP+RIGHT','LEFT+RIGHT','UP+DOWN'):
            self.restore('selector-ready');before=self.row();rows=self.trace('selector-ambiguous-'+combination,10,lambda n:'L+'+combination if n<8 else 0)
            self.check(rows[-1]['selected_id']==before['selected_id'] and rows[-1]['hero']==before['hero'],'ambiguous selector release never commits or moves')
        for slot,direction in enumerate(QUICK):
            self.restore('selector-ready');self.step(1,'R');self.step(1);before=self.row()
            rows=self.trace('selector-four-cardinals-'+direction,10,lambda n:'L+'+direction if n<8 else 0)
            self.check(all(r['selected_id']==before['selected_id'] and r['hero']==before['hero'] for r in rows[:8]),'held cardinal selector previews without committing or moving')
            self.check(rows[-1]['selected_form']==(50,51,59,33)[slot] and rows[-1]['selected_party']==slot,'cardinal release commits its exact assigned individual')
            self.check(sum(o['tile']==712 for o in self.oam())==int(bool(self.get('summoned'))),'resumed field displays exactly one selected companion body')
        self.restore('selector-ready');self.step(1,'R');self.select_form(33);self.step(1,'R');self.check(self.power()['tile_owner']==5,'old command cannot overwrite live Underwater tiles');self.ready();self.step(1,'R')
        self.check(self.get('magma_power_kind')==43 and self.get('magma_power_time')>0,'returning old retained command works after lease and cooldown release')
        self.covered.append('native-selector-freeze-same-family-legacy')
    def storage(self):
        self.restore('combat-town-source');self.open_tab(2);before=bytes(self.roster());seen=set();trace=[];last=self.row()
        for n in range(240):
            self.step(1,'DOWN' if n%4==0 else 0);r=self.row();candidate=self.get('quickparty_menu_candidate');r.update(candidate=candidate,candidate_id=self.roster().instances[candidate].instance_id if candidate<160 else None,update_delta=(r['game_frame']-last['game_frame'])&0xffffffff,page_flip=r['displayed_page']!=last['displayed_page']);last=r;trace.append(r)
            if candidate<160:seen.add(r['candidate_id'])
        self.cases.append(dict(case='all50-storage',seen_ids=sorted(seen),trace=trace))
        self.check(seen=={c.instance_id for c in self.live()},'ordinary storage scrolling visits all50 genuinely retained individual IDs')
        self.check(bytes(self.roster())==before,'storage browsing preserves all exact individual and party bytes')
        self.check(all(r['update_delta']==1 and r['page_flip'] and r['cycles']<CYCLES for r in trace),'all50 storage frames update and display within exact native budget');self.close_menu();self.covered.append('native-all50-storage')
    def form_pixels(self):
        for form in range(49,73):
            if form in self.forms:self.restore('combat-town-source')
            else:
                candidates=[(n,r,source) for source in self.acquisition_reports for n,r in source['snapshots'].items() if form in r['owned_form_ids'] and n!='failure']
                self.check(bool(candidates),'base form has authenticated actually acquired producer snapshot')
                name,rec,source=candidates[-1];self.restore(self.import_snapshot(name,source))
            self.to_town();self.owned_select(form);self.set_command(67+((form-49)//3)*3);self.ready();self.goto(240,200);self.face(1);self.ready()
            self.step(1,'R');self.pixel_check('form-'+str(form)+'-anticipation');self.photograph('form-'+str(form)+'-anticipation');startup=START[self.command()-67]
            self.step(startup);self.pixel_check('form-'+str(form)+'-release');self.photograph('form-'+str(form)+'-release')
            self.step(4);self.pixel_check('form-'+str(form)+'-settle');self.photograph('form-'+str(form)+'-settle')
            self.step(20);self.pixel_check('form-'+str(form)+'-recover');self.photograph('form-'+str(form)+'-recover')
        self.restore('combat-town-source');self.covered.append('native-all24-form-pixels')
    def workload(self,cmd):
        self.prepare(cmd);self.goto(336,160);self.face(3);self.ready()
        # The camera follows actual movement while the fixed-origin cast runs.
        rows=self.trace('walking-camera-cast-'+str(cmd),self.life[cmd-67]+8,lambda n:'R+RIGHT+DOWN' if n==0 else 'RIGHT+DOWN' if n<18 else 'LEFT+UP' if n<36 else 0,True)
        live=[r for r in rows if r['power']['time']>0]
        self.check(any(r['power']['kind']==cmd and r['power']['time'] for r in rows),'worst-workload probe actually starts requested effect')
        self.check(len({tuple(r['camera']) for r in live})>5 and len({tuple(r['hero']) for r in live})>5,'real cast overlaps moving hero and scrolling camera')
        self.cases.append(dict(case='walking-camera-cast-'+str(cmd),observed_live_enemies=max(sum(e['hp']>0 for e in r['enemies']) for r in rows),observed_hostile_shots=max(sum(bool(s['life'] and s['owner']) for s in r['shots']) for r in rows),observed_simultaneous_effect_walking_camera=True,passed=True))
    def cooldown(self):
        self.prepare(70,False);self.goto(240,200);self.ready();before,rows=self.cast(70,count=130,keys=lambda n:'R' if n%2==0 else 0,label='cooldown-repeated-R')
        starts=[r for a,r in zip([before]+rows,rows) if r['power']['token']!=a['power']['token']]
        self.check(len(starts)==2,'repeated native R starts only initial and post-cooldown casts')
        self.check(starts[1]['game_frame']-starts[0]['game_frame']>=starts[0]['power']['cooldown'],'cooldown cannot be shortened by repeated R edges')
        self.cases.append(dict(case='cooldown-repeated-R',starts=starts,passed=True))
    def wall(self):
        self.prepare(73,False);mask,w,h=self.mask();choices=[]
        for y in range(32,h-32):
            for x in range(32,w-32):
                if mask[y*w+x] or mask[(y+2)*w+x]:continue
                distance=next((d for d in range(1,21) if mask[(y-d)*w+x]),21)
                if 8<=distance<=14:choices.append((abs(x-240)+abs(y-200),x,y,distance))
        self.check(bool(choices),'actual collision map supplies accessible near-wall path probe')
        _,x,y,_=min(choices);self.align(x,y,1);self.ready();px,py=self.get('px'),self.get('py')
        distance=next((d for d in range(1,31) if mask[(py-d)*w+px]),31)
        before,rows=self.cast(73,label='native-wall-73')
        def clear_segment(a,b):
            x,y=a;tx,ty=b;dx=abs(tx-x);dy=-abs(ty-y);sx=1 if x<tx else -1;sy=1 if y<ty else -1;err=dx+dy
            while True:
                if not (0<=x<w and 0<=y<h) or mask[y*w+x]:return False
                if (x,y)==(tx,ty):return True
                twice=err*2;nx,ny=x,y
                if twice>=dy:err+=dy;nx+=sx
                if twice<=dx:err+=dx;ny+=sy
                if nx!=x and ny!=y and (mask[y*w+nx] or mask[ny*w+x]):return False
                x,y=nx,ny
        self.cases.append(dict(case='native-wall-73',wall_distance=distance,origin=before['hero'],trace=rows))
        self.check(any(r['power']['stopped'] for r in rows),'real scenery permanently stops moving tip within same cast')
        self.check(all(clear_segment((seg['x'],seg['y']),(seg['tx'],seg['ty'])) for r in rows for seg in r['power']['segments']),'all observed native path geometry respects inclusive diagonal-safe scenery traversal')
        self.covered.append('native-wall-clipping')
    def modal_freeze(self):
        self.prepare(68,False);self.goto(240,200);self.ready();self.step(1,'R');self.step(1);self.step(1,'START');before=self.power()
        rows=self.trace('native-pause-live-cast',35,lambda n:'RIGHT' if n%2==0 else 0,True)
        self.check(all(r['state']==PAUSE and r['power']==before for r in rows),'real pause freezes age, cooldown, target ledger and geometry despite directional edges')
        self.close_menu();self.ready();self.goto(80,269,radius=2);self.face(1);self.ready();self.step(1,'R');self.step(1)
        rows=self.trace('native-rest-event-save-live-cast',160,lambda n:'A' if n==0 else 0,True)
        modes={r['state'] for r in rows};self.check(SAVING in modes and EVENT_PENDING in modes,'real rest produces observed EVENT_PENDING and SAVING modes')
        frozen=[(a,b) for a,b in zip(rows,rows[1:]) if a['state']==b['state'] and a['state'] in (SAVING,EVENT_PENDING)]
        self.check(bool(frozen) and all(a['power']==b['power'] for a,b in frozen),'real event and save processing freeze live cast and cooldown')
        self.cases.append(dict(case='native-modal-effect-freeze',observed_modes=sorted(modes),frozen_samples=len(frozen),passed=True))
    def run_case(self,name,fn):
        print('BEGIN',name,flush=True);self.current_case=name;before_failures=len(self.failures)
        try:fn()
        except Exception as exc:
            traceback.print_exc();self.failures.append({'case':name,'error':str(exc),'status':self.status()});self.snapshot(name+'-failure',settle=False)
        self.case_outcomes[name]=len(self.failures)==before_failures
        print('END',name,'PASS' if self.case_outcomes[name] else 'FAIL',flush=True);self.report()
    def run(self,only=None):
        self.boot();cases=[('command77',self.command77)]+[('direct-'+str(c),lambda c=c:self.direct(c)) for c in range(67,91) if c!=77]
        cases += [('alternate-'+str(c),lambda c=c:self.alternate(c)) for c in (67,68,69,71,77,81,83,90)]
        cases += [('facing-'+str(d),lambda d=d:self.direct(70,d)) for d in (0,2,3)]
        cases += [('gap-'+str(c),lambda c=c:self.direct(c,gap=True)) for c in GAPS]
        cases += [('selector',self.selector),('storage',self.storage),('form-pixels',self.form_pixels),('cooldown',self.cooldown),('wall',self.wall),('modal-freeze',self.modal_freeze)]
        cases += [('workload-'+str(c),lambda c=c:self.workload(c)) for c in range(67,91)]
        names={n for n,_ in cases};chosen=(names if only=='all' else set(only.split(','))) if only else ({'direct-'+str(c) for c in range(67,91,3)}|{'workload-'+str(c) for c in range(67,91,3)} if self.diagnostic_partial else names);assert chosen<=names,chosen-names
        for name,fn in cases:
            if name in chosen:self.run_case(name,fn)
        if set(self.cast_commands)==set(range(67,91)):self.covered.append('all24-native-equipped-cast')
        if set(self.damage_commands)==set(range(67,91)):self.covered.extend(('all24-native-damage','native-cooldown-no-double-hit'))
        for requirement,subset in (('native-alternate-and-diagonal-controls',['alternate-'+str(c) for c in (67,68,69,71,77,81,83,90)]),('native-facing',['direct-70']+['facing-'+str(d) for d in (0,2,3)]),('native-safe-apertures',['gap-'+str(c) for c in GAPS]),('native-walking-camera-cast-cadence',['workload-'+str(c) for c in range(67,91)])):
            if all(self.case_outcomes.get(n) for n in subset):self.covered.append(requirement)
        self.restore('combat-town-source');self.check([c.form_id for c in self.live()]==self.source_evidence['owned_forms'] and self.collection()==self.source_evidence['historical_forms'],'combat test returns to exact earned source roster and history')
        self.report()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('rom','symbols','output','source-report','source-manifest'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('expected-rom-sha','expected-symbols-sha','source-report-sha'):p.add_argument('--'+n,required=True)
    p.add_argument('--source-snapshot',default='11-all89-earned-town');p.add_argument('--case');p.add_argument('--diagnostic-partial',action='store_true');p.add_argument('--producer-source-root',type=Path);p.add_argument('--cold-cross-rom',action='store_true');a=p.parse_args()
    r=UnderwaterCombat(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.source_report_sha,a.source_manifest,a.source_snapshot,a.diagnostic_partial,a.producer_source_root,a.cold_cross_rom)
    try:r.run(a.case)
    finally:r.report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
