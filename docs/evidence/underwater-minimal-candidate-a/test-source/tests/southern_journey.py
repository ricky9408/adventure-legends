#!/usr/bin/env python3
"""Hash-pinned, controller-only Southern chapter journey.

Only authenticated N5 SRAM is imported and cold-booted. No RAM writes, synthetic
ownership, or cross-ROM machine states. Same-ROM branches always pair state and
SRAM hashes. Scene-only runs explicitly do not accept combat commands23–42.
All screenshots are spoiler-rich developer evidence, never player media.
"""
from __future__ import annotations
import argparse, ctypes as C, hashlib, inspect, itertools, json, shutil, struct
from collections import Counter
from pathlib import Path
from southern_symbols import paired_southern_symbols
from northern_journey import NorthernJourney, newest_bank
from region_journey import RegionJourney, Emulator, ROOT, PLAY, PAUSE, DEAD, DIALOG, SAVING, CONFIRM, digest

N5_SHA='f4e853c85445b8567263a1a875eba967e552e0dcae30958ca42f39bfec4e4479'
N5_ROM='302316c53d6fb9dafa0ecbf9f679c9c39af3a150af3aa78398c368312e50399e'
OLD_FORMS=[1,2,4,5,7,8,10,11,13,14,16,19,20,22,23,73,74,75,76,77,78]
BASES=[25,28,79,81,83,85,87,89,91,93]
ALL_FORMS=sorted(OLD_FORMS+[f for base in BASES for f in (base,base+1)])
NEW_ITEMS={4,12,36,52,66,84}

class SouthernJourney(NorthernJourney):
    def __init__(self,rom,symbols,output,expected_rom_sha,expected_symbols_sha,fixture=None,scene_only=False,source_manifest=None,elf=None):
        assert digest(rom)==expected_rom_sha,'Candidate ROM differs from explicit frozen SHA'
        assert digest(symbols)==expected_symbols_sha,'Candidate symbols differ from explicit frozen SHA'
        self.target_sha=expected_rom_sha;self.symbol_sha=expected_symbols_sha;self.scene_only=scene_only
        self.source_rom=Path(rom).resolve();self.source_symbols=Path(symbols).resolve();self.out=Path(output).resolve();self.out.mkdir(parents=True,exist_ok=True)
        self.rom=self.out/'tested.gba';self.symbol_path=self.out/'tested.sym'
        for src,dst in ((self.source_rom,self.rom),(self.source_symbols,self.symbol_path)):
            if src!=dst:shutil.copyfile(src,dst)
        self.sym,self.south_elf_pairing=paired_southern_symbols(self.rom,self.symbol_path,elf or self.source_rom.with_suffix('.elf'),self.out/'tested.elf')
        self.candidate={'rom_path':str(self.source_rom),'symbols_path':str(self.source_symbols),'rom_sha256':digest(self.rom),'symbols_sha256':digest(self.symbol_path),'rom_bytes':self.rom.stat().st_size,'emulator_bridge_sha256':digest(ROOT/'tools/mgba_bridge.so'),'emulator_bridge_source_sha256':digest(ROOT/'tools/mgba_bridge.c')}
        self.candidate['southern_elf_pairing']=self.south_elf_pairing
        self.inputs=[];self.checks=[];self.snapshots={};self.failures=[];self.timings={};self.coverage=[];self.cases=[];self.frame_windows=[];self.pixel_cases=[];self.acquisitions=[];self.transitions=[];self.main_selections=[];self.main_only=False
        self.fixture=Path(fixture or ROOT/'tests/fixtures/v5-revision3/northern-all21-town.sav').resolve()
        assert digest(self.fixture)==N5_SHA,'Only the authenticated N5 SRAM is accepted'
        self.source_bytes=self.fixture.read_bytes();self.source_bank=newest_bank(self.source_bytes)
        assert int.from_bytes(self.source_bank[12:14],'little')==3
        self.provenance={'fixture_path':str(self.fixture),'sram_sha256':N5_SHA,'source_rom_sha256':N5_ROM,'source_machine_state_loaded':False,'scope':'Prior eleven owned individuals and21 histories only; no Southern progress exists'}
        manifest=Path(source_manifest or self.source_rom.parent/'source-hashes.json').resolve()
        assert manifest.is_file(),'Require frozen candidate source-hashes.json provenance'
        self.source_hashes=json.loads(manifest.read_text());self.source_manifest_sha=digest(manifest)
        shutil.copyfile(manifest,self.out/'candidate-source-hashes.json')
        roots=list(dict.fromkeys([manifest.parent.parent,*manifest.parents,ROOT]))
        self.source_root=next((root for root in roots if all((root/p).is_file() for p in self.source_hashes)),None)
        assert self.source_root is not None,'Cannot locate all files in frozen source manifest'
        self.source_checks={p:digest(self.source_root/p)==sha for p,sha in self.source_hashes.items()}
        assert all(self.source_checks.values()),'Frozen source provenance differs from manifest'
        shutil.copyfile(self.source_root/'src/game.c',self.out/'candidate-source-game.c')
        self.test_sources={str(p.relative_to(ROOT)):digest(p) for p in (Path(__file__).resolve(),ROOT/'tests/southern_symbols.py',ROOT/'tests/northern_journey.py',ROOT/'tests/region_journey.py',ROOT/'tests/region_combat_tests.py',ROOT/'tests/test_save5.py',ROOT/'tests/test_save4.py',ROOT/'tools/mgba_runner.py',Path(inspect.getfile(type(self))).resolve())}
        (self.out/'test-source').mkdir(exist_ok=True)
        for p in self.test_sources:shutil.copyfile(ROOT/p,self.out/'test-source'/Path(p).name)
        self.contract=json.loads((ROOT/'assets/southern_region/contract.json').read_text());self.scene=json.loads((ROOT/'assets/southern_region/scene.json').read_text())
        self.contract_sha=digest(ROOT/'assets/southern_region/contract.json');self.scene_sha=digest(ROOT/'assets/southern_region/scene.json')
        self.e=Emulator(self.rom);self.e.load_save(self.fixture);self.e.reset();self.mask_cache={};self.descriptors={}
        # Discover the descriptor stride from actual tested ARM tables, never a
        # mutable layout.json. Verify every bitmap pointer names the right ROM art.
        for name,start,count in (('south',30,8),('north',22,8)):
            table=self.sym[name+'_art_rooms'];candidates=[]
            for stride in (20,28,32):
                rows=[]
                for i in range(count):
                    addr=table+i*stride;w,h=struct.unpack('<HH',self.e.bytes(addr,4));bitmap=self.e.read(addr+4)
                    if (w,h)!=((480,320) if i<2 else (240,160)) or bitmap not in [v for k,v in self.sym.items() if k.startswith(name+'_background_')]:break
                    rows.append({'address':addr,'width':w,'height':h,'bitmap':bitmap,'stride':stride})
                if len(rows)==count:candidates.append(rows)
            assert len(candidates)==1,('Ambiguous ARM room descriptor',name)
            self.descriptors.update({start+i:r for i,r in enumerate(candidates[0])})
        self.report()

    def report(self):
        if not hasattr(self,'provenance'):return
        data={'suite':'southern-native-controller-journey','controller_only':True,'game_ram_writes':0,'player_facing':False,'scene_only_bringup':self.scene_only,'native_commands23_42_accepted':False,
            'provenance':self.provenance,**self.candidate,'test_sources':self.test_sources,'source_manifest_sha256':self.source_manifest_sha,'verified_source_root':str(self.source_root),'frozen_source_checks':self.source_checks,'content_contract_sha256':self.contract_sha,'scene_sha256':self.scene_sha,
            'compiled_room_descriptors':self.descriptors,'branch_policy':'Only exact tested ROM/symbols hash-checked state/SRAM pairs; no imported machine states','enabled_rows_are_not_acquisition_evidence':True,
            'checks':self.checks,'failures':self.failures,'coverage':self.coverage,'cases':self.cases,'acquisitions':self.acquisitions,'snapshots':self.snapshots,'transitions':self.transitions,'main_route_selected_forms':sorted(set(self.main_selections)),
            'frame_windows':self.frame_windows,'pixel_cases':self.pixel_cases,'inputs':self.inputs}
        (self.out/'southern-journey.json').write_text(json.dumps(data,indent=2)+'\n')

    def step(self,n,keys=0):
        before=self.get('room')
        if self.main_only and self.get('game_state')==PLAY:self.main_selections.append(self.selected().form_id)
        RegionJourney.step(self,n,keys)
        after=self.get('room')
        if before!=after:self.transitions.append({'frame':self.e.frame,'from':before,'to':after,'keys':keys})
    def snapshot(self,name,settle=True):
        if settle:self.settle()
        state=self.out/(name+'.state');save=self.out/(name+'.sav');shot=self.out/(name+'.png')
        self.e.screenshot(shot);self.e.state(state);save.write_bytes(self.e.bytes(0x0e000000,32768))
        self.snapshots[name]={'rom_sha256':self.target_sha,'symbols_sha256':self.symbol_sha,'state_path':str(state),'state_sha256':digest(state),'sram_path':str(save),'sram_sha256':digest(save),'screenshot':str(shot),'status':self.status(),'quests':[self.quest(q) for q in range(30)],'obtained_form_ids':self.collection(),'owned_form_ids':[c.form_id for c in self.live()],'southern_objectives':[self.state().quests.objectives[q] for q in range(22,30)],'puzzle':self.puzzle(),'trial':{'index':self.get('trial_index',1),'slot':self.get('trial_slot',1),'instance_id':self.get('trial_id'),'bits':self.get('trial_bits',1)}}
        self.report();print(name,self.status(),'South quests',[self.quest(q) for q in range(22,30)],flush=True);return name
    def mask(self):
        room=self.get('room')
        assert room in self.descriptors,('No authenticated ARM navigation descriptor',room)
        if room in self.mask_cache:return self.mask_cache[room]
        d=self.descriptors[room];a=d['address'];w,h=d['width'],d['height'];b=bytearray(w*h)
        if d['stride']>=28:
            rows=self.e.read(a+20);bands=self.e.read(a+24)
            for y in range(h):
                ptr=bands+2*self.e.read(rows+2*y,2);count=self.e.read(ptr,2);assert count<=64
                for k in range(count):
                    lo=self.e.read(ptr+2+4*k,2);hi=self.e.read(ptr+4+4*k,2);assert 0<=lo<=hi<=w
                    b[y*w+lo:y*w+hi]=b'\1'*(hi-lo)
        else:
            ptr=self.e.read(a+12);count=self.e.read(a+16,2)
            for y in range(h):
                for x in range(w):
                    if x<5 or y<5 or x>w-6 or y>h-6:b[y*w+x]=1
            for i in range(count):
                x,y,rw,rh=struct.unpack('<4h',self.e.bytes(ptr+i*8,8));lo,hi=max(0,x-5),min(w,x+rw+5)
                for yy in range(max(0,y-5),min(h,y+rh+5)):b[yy*w+lo:yy*w+hi]=b'\1'*(hi-lo)
        self.mask_cache[room]=(b,w,h);return b,w,h
    def puzzle(self):return list(self.e.bytes(self.sym['south_game_puzzle'],3))
    def object(self,key):return next(o for o in self.scene['objects'][self.get('room')-30] if o['key']==key)
    def approach(self,key):
        o=self.object(key);x,y=o['approach'];cx,cy=o['center']
        # Move closer along the marked approach when the compiled collision
        # permits it, disambiguating nearby controls without teleportation.
        nx=cx+(6 if x>cx else -6 if x<cx else 0);ny=cy+(6 if y>cy else -6 if y<cy else 0)
        blocked,w,h=self.mask()
        if not blocked[ny*w+nx]:self.goto(nx,ny,radius=4)
        else:self.goto(x,y,radius=4)
        self.face(1 if y>cy else 0 if y<cy else 2 if x>cx else 3)
        self.check(abs(self.get('px')-cx)+abs(self.get('py')-cy)<18,f'{key} controller reaches exact marked interaction range')
    def use(self,key):self.approach(key);self.tap('A');self.settle()
    def field_object(self,key,form):
        self.owned_select(form);self.approach(key);self.ready();before=self.get('ability_cd');identity=self.selected().instance_id;self.tap('R');self.settle()
        self.check(self.selected().instance_id==identity,'field action keeps individual identity')
    def field_point(self,form,x,y):
        self.owned_select(form);self.goto(x,y+10,radius=4);self.face(1);self.ready();self.tap('R');self.settle()
    def entry(self,target):
        here=self.get('room')
        if here==22 and target==30:self.act(208,224,1)
        elif here==30 and target==22:self.use('ferry')
        elif here==30 and target==31:self.goto(304,16);self.step(8,'UP');self.settle()
        elif here==31 and target==30:self.goto(240,300);self.step(8,'DOWN');self.settle()
        elif here==30 and target==32:self.act(80,148,1)
        elif here==31 and target in (33,34):self.act(80 if target==33 else 400,104 if target==33 else 72,1)
        elif here in (34,35,36) and target==here+1:self.use('exit_gate')
        else:raise AssertionError(('Unsupported Southern transition',here,target))
        self.check(self.get('room')==target,f'ordinary controller transition {here} to{target}')
    def to_town(self):
        while self.get('room')>=32:
            r=self.get('room');self.leave_interior(30 if r==32 else 31 if r in (33,34) else r-1)
        if self.get('room')==31:self.entry(30)
        self.check(self.get('room')==30,'reachable return to Southern town')
    def boot(self):
        self.step(150);self.tap('START',2,35);self.settle();s=self.state();b=self.source_bank
        self.check(self.get('room')==22,'authentic Northern N5 SRAM resumes in Northern town')
        self.check(bytes(s.roster.instances)==b[160:4000],'revision3 to current6 preserves all160 exact instance records')
        self.check(bytes(s.roster.party)==b[4000:4004] and s.roster.selected_party==b[4004],'migration retains exact active party and selected identity')
        self.check(bytes(s.roster.seen)+bytes(s.roster.obtained)+bytes(s.roster.rewards)==b[96:144],'exact historical collection and generic reward ledgers preserved')
        self.check(bytes(s.quests)==b[4032:4296] and bytes(s.equipment)==b[4544:5056],'all old quest and gear bytes preserved')
        self.check(bytes(s.roster.expedition_bond)+bytes(s.roster.expedition_events)+bytes(s.roster.lifetime_field_aid)==b[4296:4536],'expedition and lifetime aid bytes preserved')
        self.check(self.collection()==OLD_FORMS and len(self.live())==11,'fixture genuinely retains11 individuals and21 histories')
        self.check(not any(s.quests.region_flags[2:]) and all(self.quest(q)==0 and not s.quests.objectives[q] for q in range(22,30)),'migration fabricates no Southern content')
        self.old_ids={c.instance_id for c in self.live()}
        saved=self.e.bytes(0x0e000000,32768);migrated=newest_bank(saved)
        self.check(int.from_bytes(migrated[12:14],'little')==6 and migrated[32:]==b[32:],'cold boot commits current revision6 with exact byte-for-byte revision3 payload preservation')
        old_offset=self.source_bytes.index(b);self.check(saved[old_offset:old_offset+6144]==b,'forward migration leaves prior committed revision3 bank intact')
        self.snapshot('00-n5-forward-migration')
        self.entry(30);self.snapshot('01-ferry-entry');self.cadence('town-early-idle',60)
    def recruits_main(self):
        self.use('guide');self.use('demo_handle');self.use('lens_hood');self.use('hood_bench');self.use('guide');self.reward(22,79)
        self.entry(31);self.use('second_hinge');self.check(not self.state().quests.objectives[23],'second hinge cannot skip public latch')
        self.use('public_latch');self.use('second_hinge');self.use('hinge_npc');self.reward(23,85)
        self.assign(0,79);self.assign(1,85);self.select_form(79);self.main_only=True
        self.check(self.old_ids<={c.instance_id for c in self.live()},'guaranteed recruit assignment preserves every previous individual')
        self.snapshot('02-guaranteed-bases');self.entry(34)
    def solve_optics(self,room):
        if room in (34,35):
            self.use('mirror0')
            if room==35:self.use('mirror1');self.use('shade')
        else:self.use('mirror0');self.use('mirror1');self.use('shade')
    def puzzle_room(self,room):
        bit=1<<(room-34);before_obj=self.state().quests.objectives[24];self.snapshot(f'{room}-unsolved-entry')
        if room in (34,35):
            key='receiver'
            # Incorrect selected capability is rejected without objective/cooldown.
            self.field_object(key,85 if room==34 else 79)
            self.check(self.state().quests.objectives[24]==before_obj and not self.get('ability_cd'),'wrong capability cannot advance mandatory target or consume cooldown')
        self.use('mirror0');self.use('reset');self.check(self.puzzle()==[int(room==36),int(room==36),1],'manual reset restores incomplete optics')
        self.use('mirror0');self.leave_interior(31 if room==34 else room-1);self.entry(room)
        self.check(self.puzzle()==[int(room==36),int(room==36),1] and self.state().quests.objectives[24]==before_obj,'escape and reentry reset transient optics without awarding objective')
        self.solve_optics(room)
        if room in (34,35):
            self.check(self.state().quests.objectives[24]==before_obj,'manual optical solution does not bypass mandatory companion target')
            self.field_object(key,79 if room==34 else 85)
        self.check(self.state().quests.objectives[24]&bit,'actual tagged solution earns stage objective')
        self.use('reset');self.check(self.state().quests.objectives[24]&bit,'reset retains completed objective')
        self.snapshot(f'{room}-solved');self.entry(room+1)
    def machine(self,cls):
        self.step(90);self.equip_item(0,{1:1,2:9,3:17}[cls]);self.use('shade');self.use('start');self.check(self.get('south_game_machine_stage',1)==1,'machine begins with a visible warning phase');self.snapshot(f'machine-{cls}-telegraph',settle=False)
        self.open_tab(7);paused=(self.get('south_game_machine_stage',1),self.get('south_game_machine_ticks',1),self.get('south_game_machine_hp',1));self.step(45,'R')
        self.check((self.get('south_game_machine_stage',1),self.get('south_game_machine_ticks',1),self.get('south_game_machine_hp',1))==paused,'journal freezes boss warning, HP and phase timer');self.close_menu()
        trace=[];shown=set()
        for cycle in range(16):
            if self.get('south_game_machine_stage',1)==5:break
            self.goto(152,112)
            for _ in range(300):
                stage=self.get('south_game_machine_stage',1)
                if stage in (2,3) and stage not in shown:
                    self.e.screenshot(self.out/f'machine-{cls}-phase-{stage}.png');shown.add(stage)
                if stage in (3,5):break
                self.step(1)
            if stage==5:break
            self.goto(152,82 if cls<3 else 108);self.face(1)
            for _ in range(3):
                before=self.get('south_game_machine_hp',1);self.tap('A',2,22);self.settle();after=self.get('south_game_machine_hp',1)
                trace.append({'frame':self.e.frame,'stage':self.get('south_game_machine_stage',1),'damage_q4':before-after,'hp_q4':after,'weapon_class':cls})
                if self.get('south_game_machine_stage',1)!=3:break
        self.check(self.get('south_game_machine_stage',1)==5 and self.get('south_game_machine_hp',1)==0,f'actual native weapon class{cls} defeats moving coupling')
        self.check(any(r['damage_q4']>0 for r in trace),'boss HP only drops through actual attacks');self.cases.append({'case':f'boss-weapon-{cls}','trace':trace,'passed':True})
        self.use('start');self.reward(24);self.snapshot(f'boss-{cls}-cleared')
    def main_route(self):
        self.recruits_main()
        for room in (34,35,36):self.puzzle_room(room)
        self.snapshot('03-machine-ready')
        for cls in (2,3,1):self.restore('03-machine-ready');self.machine(cls)
        self.check(set(self.main_selections)<={79,85},'mandatory route uses only guaranteed base companions')
        self.main_only=False;self.use('start');self.check(self.get('room')==30,'completed Crown returns to town');self.use('rest');self.snapshot('04-main-complete')
        self.coverage.append('guaranteed-base79-base85-controller-main-route')
    def recruit_field(self,key,form):
        before={c.instance_id for c in self.live()};self.use(key)
        rows=[c for c in self.live() if c.form_id==form];self.check(len(rows)==1,f'field encounter earns one actual form{form} individual')
        c=rows[0];self.check(c.instance_id not in before,'field recruit receives a new unique instance identity')
        self.acquisitions.append({'form_id':form,'instance_id':c.instance_id,'frame':self.e.frame,'source':'field'})
        saved=(bytes(self.roster()),bytes(self.state().quests));self.use(key)
        self.check((bytes(self.roster()),bytes(self.state().quests))==saved,'repeated field encounter cannot clone reward')
    def optional_recruits(self):
        self.step(90)
        for slot,item in ((0,2),(1,34),(3,65)):self.equip_item(slot,item)
        self.use('rest')
        for key in ('market_npc','rain_npc','porter','tailor','loft_npc'):self.use(key)
        for key in ('stall0','stall1','stall2','rain0','rain1','delivery0','delivery1'):self.use(key)
        for key,q in (('market_npc',25),('rain_npc',26),('porter',27)):self.use(key);self.reward(q)
        self.entry(32);self.use('encounter6');self.check(not any(c.form_id==91 for c in self.live()),'hinted bat is not awarded before environmental reveal')
        self.use('torn_clue');self.use('replacement_panel');self.use('sightline0');self.use('sightline1')
        self.check(self.quest(28)==2 and self.quest(29)==2,'both optional clue quests ready before accepting gear')
        self.check(self.state().quests.region_flags[18]&1,'simultaneous sightlines reveal hinted companion before reward claim')
        self.use('market_shortcut');self.check(self.get('room')==30,'explicit loft shortcut reaches town')
        self.use('shade_clock');self.check(self.state().quests.region_flags[18]&2,'quiet clock completes second deterministic reveal before gear claim')
        self.entry(32);self.recruit_field('encounter6',91);self.leave_interior(30)
        self.use('tailor');self.reward(28);self.use('loft_npc');self.reward(29);self.use('rest')
        self.entry(31);self.use('rest')
        for key in ('root_tie0','root_tie1'):self.use(key)
        self.recruit_field('encounter0',25);self.use('drain_cover');self.recruit_field('encounter1',28)
        self.use('ripple_clue');self.use('runnel_gate');self.recruit_field('encounter5',89)
        self.recruit_field('encounter4',87)
        self.use('shade_panel0');self.use('shade_panel1');self.recruit_field('encounter3',83)
        self.use('rest');self.entry(33);self.use('sun_shutter');self.recruit_field('encounter2',81)
        for key in ('pin0','pin1','pin2'):self.use(key)
        self.recruit_field('encounter7',93);self.leave_interior(31);self.use('rest');self.to_town();self.use('rest')
        self.check(self.state().quests.region_flags[8]==255,'all eight typed field sources are actually claimed')
        self.check(all(self.quest(q)==3 for q in range(22,30)),'all eight Southern quests are earned and claimed')
        self.check(NEW_ITEMS<={r.item_id for r in self.state().equipment.bag},'all six Southern gear rewards earned')
        self.check(len(self.live())==21 and len({c.instance_id for c in self.live()})==21,'eight field and two guaranteed sources retain21 distinct individuals')
        self.snapshot('05-all-ten-recruits-eight-quests')
    def clear_enemies(self):
        # Ordinary sword attacks clear trial workspaces. The test never grants
        # damage, health, invulnerability or killed flags through observations.
        self.step(60);self.equip_item(0,2);trace=[]
        for _ in range(100):
            live=[(i,e) for i,e in enumerate(self.enemies()) if e['hp']>0]
            if not live:break
            self.check(self.get('game_state')==PLAY,'native enemy clearing stays alive')
            index,e=min(live,key=lambda row:abs(row[1]['x']-self.get('px'))+abs(row[1]['y']-self.get('py')))
            dx=e['x']-self.get('px');dy=e['y']-self.get('py')
            if abs(dx)+abs(dy)>24:
                b,w,h=self.mask();candidates=[(abs(x-self.get('px'))+abs(y-self.get('py')),x,y) for x,y in ((e['x']-20,e['y']),(e['x']+20,e['y']),(e['x'],e['y']+20),(e['x'],e['y']-20)) if 5<=x<w-5 and 5<=y<h-5 and not b[y*w+x]]
                self.check(bool(candidates),'enemy has a reachable ordinary attack approach');_,x,y=min(candidates);self.goto(x,y)
                e=self.enemies()[index];dx=e['x']-self.get('px');dy=e['y']-self.get('py')
            self.face((3 if dx>0 else 2) if abs(dx)>abs(dy) else (0 if dy>0 else 1))
            hp=e['hp_q4'];self.tap('A',2,22);self.settle();after=self.enemies()[index]['hp_q4'];trace.append({'frame':self.e.frame,'enemy':index,'before_hp_q4':hp,'after_hp_q4':after})
        self.check(not any(e['hp']>0 for e in self.enemies()),'all spawned trial-area enemies defeated by actual native sword attacks')
        self.cases.append({'case':'native-trial-workspace-combat','room':self.get('room'),'trace':trace,'passed':True})
    def ensure_setting(self,key,symbol,value):
        for _ in range(4):
            if self.get(symbol,1)==value:return
            self.use(key)
        self.check(False,f'{symbol} can reach visible setting{value}')
    def start_trial(self,form):
        self.owned_select(form);self.ready();self.use('trial_sign')
        self.check(self.get('trial_id')==self.selected().instance_id and self.get('trial_slot',1)==self.roster().party[self.roster().selected_party],'trial pins selected actual slot and instance_id')
        self.check(self.get('trial_bits',1)==0,'explicit trial sign starts clean proof')
        return self.selected().instance_id
    def trial_target(self,form,x,y,bit,mark=False):
        self.field_point(form,x,y)
        if mark:self.tap('A');self.settle()
        if bit<7:self.check(self.get('trial_bits',1)==bit,'only distinct environmental target advances proof')
        if bit==1:
            identity=self.selected().instance_id;proof=self.get('trial_bits',1)
            self.field_point(form,x,y);self.check(self.get('trial_bits',1)==proof,'duplicate target cannot advance this individual personal trial')
            self.field_point(85 if form==79 else 79,x,y)
            self.check(self.get('trial_id')==identity and self.get('trial_bits',1)==proof,'another selected individual cannot add or steal this trial proof')
            self.owned_select(form)
    def trial_done(self,form,identity):
        c=next(c for c in self.live() if c.instance_id==identity)
        self.check(c.form_id==form and c.trial_flags==1,f'form{form} exact individual earns family-local personal trial')
        self.check(c.level>=20 and c.bond>=40,'environmental training reaches non-grinding evolution floors')
        self.cases.append({'case':f'personal-trial-{form}','instance_id':identity,'level':c.level,'bond':c.bond,'passed':True});self.snapshot(f'trial-{form}-earned')
    def trial_death_branch(self):
        self.snapshot('trial79-partial-before-death');proof=self.get('trial_bits',1);identity=self.get('trial_id');forms=self.collection();owned={c.instance_id for c in self.live()}
        self.check(proof==1,'death branch begins with one genuinely earned transient proof')
        self.entry(31);self.use('rest');self.goto(208,264)
        for _ in range(800):
            if self.get('game_state')==DEAD:break
            self.step(10)
        self.check(self.get('game_state')==DEAD,'ordinary enemy damage interrupts an incomplete personal trial')
        self.check(self.get('trial_index',1)==255 and self.get('trial_bits',1)==0 and not self.get('trial_id'),'death clears transient trial participant and proof')
        self.tap('A',2,30);self.settle();self.check(self.get('room')==31 and self.hp_q4()>0,'incomplete-trial death retry returns to safe manual checkpoint')
        self.check(self.collection()==forms and {c.instance_id for c in self.live()}==owned and not next(c for c in self.live() if c.instance_id==identity).trial_flags,'trial death fabricates no trial completion and loses no retained source')
        self.snapshot('trial79-death-retry');self.restore('trial79-partial-before-death')
    def trials(self):
        # Water uses alternating visible configurations, with duplicate/wrong
        # active individual checks before the remaining two distinct receivers.
        ident=self.start_trial(79);self.ensure_setting('demo_handle','demo',1);self.trial_target(79,160,192,1);self.trial_death_branch()
        before=self.get('trial_bits',1);self.field_point(79,160,192);self.check(self.get('trial_bits',1)==before,'repeated fixture cannot advance personal trial')
        self.field_point(85,208,192);self.check(self.get('trial_bits',1)==before,'different selected individual cannot contribute pinned trial proof')
        self.ensure_setting('demo_handle','demo',0);self.trial_target(79,208,192,3);self.ensure_setting('demo_handle','demo',1);self.trial_target(79,256,192,7);self.trial_done(79,ident)
        self.entry(31);self.use('rest');ident=self.start_trial(25)
        self.trial_target(25,128,192,1);self.trial_target(25,176,144,3);self.entry(30);self.entry(32);self.trial_target(25,56,104,7);self.trial_done(25,ident)
        self.leave_interior(30);self.entry(31);self.use('rest');self.entry(33);self.clear_enemies()
        ident=self.start_trial(28);self.ensure_setting('overflow','overflow',0)
        for i,x in enumerate((56,112,168)):self.trial_target(28,x,80,(1<<(i+1))-1)
        self.trial_done(28,ident)
        ident=self.start_trial(81);self.ensure_setting('moisture','moisture',1)
        for i,x in enumerate((56,112,168)):self.trial_target(81,x,112,(1<<(i+1))-1)
        self.trial_done(81,ident)
        ident=self.start_trial(93)
        for i,x in enumerate((56,112,168)):
            self.ensure_setting('alignment','alignment',i);self.trial_target(93,x,48,(1<<(i+1))-1)
        self.trial_done(93,ident);self.leave_interior(31);self.use('rest');self.clear_enemies();self.use('rest')
        ident=self.start_trial(83)
        for i,(x,setting) in enumerate(((368,1),(400,3),(432,2))):
            current=self.get('panels',1)
            for key,mask in (('shade_panel0',1),('shade_panel1',2)):
                if (current^setting)&mask:self.use(key)
            self.trial_target(83,x,176,(1<<(i+1))-1)
        self.trial_done(83,ident);self.use('rest');ident=self.start_trial(89)
        for i,(x,y) in enumerate(((224,112),(272,176),(320,112))):self.trial_target(89,x,y,(1<<(i+1))-1,True)
        self.trial_done(89,ident);self.use('rest');self.entry(34);self.entry(35)
        ident=self.start_trial(85)
        if self.puzzle()[2]:self.use('shade')
        for i,(x,y) in enumerate(((48,112),(112,128),(176,128))):self.trial_target(85,x,y,(1<<(i+1))-1)
        self.trial_done(85,ident);self.to_town();self.use('rest');self.entry(32)
        for form,positions,settings in ((87,((48,80),(120,80),(192,80)),(1,2,3)),(91,((48,32),(120,32),(192,32)),(1,3,2))):
            ident=self.start_trial(form)
            for i,((x,y),setting) in enumerate(zip(positions,settings)):
                current=self.get('loft',1)
                for key,mask in (('sightline0',1),('sightline1',2)):
                    if (current^setting)&mask:self.use(key)
                self.trial_target(form,x,y,(1<<(i+1))-1)
            self.trial_done(form,ident)
        self.leave_interior(30);self.use('rest');self.snapshot('06-all-ten-personal-trials')
    def evolutions(self):
        changes=[]
        for base in BASES:
            self.owned_select(base);self.use('rest');self.open_tab(3);before=bytes(self.selected());roster=bytes(self.roster());quests=bytes(self.state().quests)
            self.tap('SELECT',2,4);self.check(self.get('game_state')==CONFIRM,f'form{base} evolution asks for explicit confirmation')
            self.e.screenshot(self.out/f'evolution-{base}-confirmation.png');self.tap('B',2,4)
            self.check(bytes(self.roster())==roster and bytes(self.state().quests)==quests,'declined evolution leaves roster/history/quest bytes identical')
            self.tap('SELECT',2,4);self.wait_evolution();self.tap('A',2,3);self.wait_evolution(8);self.settle();expected=bytearray(before);expected[0]=base+1
            self.check(bytes(self.selected())==bytes(expected),f'confirmed evolution{base} preserves identity, learned loadout and all non-form bytes')
            self.close_menu();changes.append({'base':base,'evolved':base+1,'instance_id':self.selected().instance_id})
            self.snapshot(f'evolved-{base+1}')
        self.check(self.collection()==ALL_FORMS and len(self.live())==21,'one real controller save earns all41 histories in21 retained individuals')
        self.cases.append({'case':'ten-confirmed-and-declined-evolutions','changes':changes,'passed':True})
    def field_command_variants(self):
        self.entry(31);self.use('rest');self.entry(34)
        for room,form,commands in ((34,80,(27,28)),(35,86,(33,34))):
            if self.get('room')!=room:self.entry(room)
            for command in commands:
                self.owned_select(form);self.set_command(command);before=self.state().quests.objectives[24]
                self.field_object('receiver',form)
                self.check(self.command()==command and self.get('ability_cd')>0,'tagged field success works with either valid equipped combat command')
                self.check(self.state().quests.objectives[24]==before,'repeated tagged field success never duplicates durable rewards')
                self.cases.append({'case':'field-independent-of-combat-command','room':room,'form':form,'equipped_command':command,'passed':True})
        self.to_town();self.use('rest')
    def lifecycle(self):
        self.field_command_variants();self.use('rest');before=(bytes(self.roster()),bytes(self.state().quests),bytes(self.state().equipment))
        for key in ('guide','market_npc','rain_npc','porter','tailor','loft_npc','curator'):self.use(key)
        self.check((bytes(self.roster()),bytes(self.state().quests),bytes(self.state().equipment))==before,'all repeated Southern turn-ins are byte-identical no-ops')
        self.check(self.state().quests.region_flags[2]==255,'all eight Southern areas truly visited')
        self.check(sum(bool(g.item_id) for g in self.state().equipment.bag)==25,'complete save contains25 real gear items')
        self.snapshot('07-complete41-saved');saved=self.snapshots['07-complete41-saved'];self.e.close();self.e=Emulator(self.rom);self.e.load_save(saved['sram_path']);self.e.reset();self.step(150);self.tap('START',2,35);self.settle()
        self.check((bytes(self.roster()),bytes(self.state().quests),bytes(self.state().equipment))==before,'independent cold boot retains exact roster, quest and equipment bytes')
        self.check(self.collection()==ALL_FORMS and len(self.live())==21,'independent SRAM boot retains41 histories and21 actual individuals')
        self.snapshot('08-complete41-independent-reboot');self.entry(22)
        self.check(all(self.quest(q)==3 for q in range(30)) and self.old_ids<={c.instance_id for c in self.live()},'old Northern return preserves old and new quests and original identities')
        self.owned_select(2);self.check(self.selected().form_id==2,'old evolved companion can be reassigned safely');self.snapshot('09-old-region-return')
        self.entry(30);self.entry(31);self.use('rest');self.goto(208,264)
        for _ in range(800):
            if self.get('game_state')==DEAD:break
            self.step(10)
        self.check(self.get('game_state')==DEAD,'real Southern enemy damage reaches death without injected health')
        self.e.screenshot(self.out/'ordinary-death.png');self.tap('A',2,30);self.settle()
        self.check(self.get('room')==31 and self.hp_q4()>0,'ordinary death retry restores safe field checkpoint')
        self.check(self.collection()==ALL_FORMS and len(self.live())==21 and all(self.quest(q)==3 for q in range(30)),'death/retry loses and duplicates no earned content')
        self.snapshot('10-southern-death-retry');self.coverage.append('all41-native-controller-acquisition-retention-and-reboot')
    def cadence(self,name,count=120,keys=None):
        self.settle();self.step(10);old=self.get('frame');page=self.e.read(0x04000000,2)&16;trace=[]
        for i in range(count):
            self.step(1,keys(i) if keys else 0);new=self.get('frame');np=self.e.read(0x04000000,2)&16
            trace.append({'hardware_frame':self.e.frame,'update_delta':(new-old)&0xffffffff,'page_flip':np!=page,'render_cycles':self.get('render_cycles'),'game_state':self.get('game_state'),'camera':[self.get('camera_x'),self.get('camera_y')],'obj_count':self.get('obj_count')});old,page=new,np
        row={'name':name,'hardware_frames':count,'game_updates':sum(t['update_delta'] for t in trace),'page_flips':sum(t['page_flip'] for t in trace),'max_cycles':max(t['render_cycles'] for t in trace),'update_histogram':dict(Counter(t['update_delta'] for t in trace)),'frame_budget':280896,'trace':trace}
        self.frame_windows.append(row);self.report();self.check(all(t['update_delta']==1 and t['page_flip'] for t in trace),name+' has one update and page flip per hardware frame');self.check(row['max_cycles']<280896 and max(t['obj_count'] for t in trace)<=128,name+' remains inside native cycle and OBJ budgets');return row
    def run(self,scope='full'):
        self.boot()
        if scope=='migration':return
        self.main_route()
        if scope=='main':return
        self.optional_recruits();self.trials();self.evolutions();self.lifecycle()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('rom','symbols','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True)
    p.add_argument('--source-sram',type=Path);p.add_argument('--source-manifest',type=Path);p.add_argument('--scene-only',action='store_true');p.add_argument('--scope',choices=('migration','main','full'),default='full')
    a=p.parse_args();run=SouthernJourney(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_sram,a.scene_only,a.source_manifest)
    try:run.run(a.scope)
    except Exception as exc:
        run.failures.append({'error':str(exc),'status':run.status()});run.snapshot('failure',settle=False);raise
    finally:run.report();run.e.close()
if __name__=='__main__':main()
