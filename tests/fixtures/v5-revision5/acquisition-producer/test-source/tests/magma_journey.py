#!/usr/bin/env python3
"""Magma controller journey. Only authenticated delivered S3 SRAM is imported.
No game RAM writes; exact candidate copies and file-scoped ELF observation.
Screenshots and full route are developer evidence, not player-facing teasers.
"""
from __future__ import annotations
import argparse,ctypes as C,hashlib,inspect,json,shutil,struct
from pathlib import Path
from collections import Counter
from region_journey import RegionJourney,ROOT,Emulator,PLAY,DIALOG,PAUSE,DEAD,SAVING,digest
from northern_journey import NorthernJourney,newest_bank
from southern_journey import SouthernJourney,ALL_FORMS as SOUTH_FORMS

FIXTURE_SHA='0bd83c19eb0dee81b3cd9e2b48462f6362b559786e38fa119312fe05787b0bd3'
MINIMAL_SHA='968066ed983bd48fc2af0d7ffeb79f635624037ef2099809fd00c97aaa04cc0c'
S3_ROM='87d16a0fc513d7e8a491e0b5ac5929f7951e1e44e18b7f534f1e5e0cc794d4de'

def elf_locals(elf,rom):
    raw=Path(elf).read_bytes();target=Path(rom).read_bytes();assert raw[:6]==b'\x7fELF\x01\x01'
    h=struct.unpack_from('<16sHHIIIIIHHHHHH',raw);assert h[2]==40
    image=bytearray(len(target));covered=bytearray(len(target))
    for i in range(h[10]):
        kind,off,virt,physical,size,memsize,flags,align=struct.unpack_from('<IIIIIIII',raw,h[5]+i*h[9])
        if kind!=1 or not size:continue
        start=physical-0x08000000;assert 0<=start<start+size<=len(target)
        image[start:start+size]=raw[off:off+size];covered[start:start+size]=b'\1'*size
    assert all(covered) and image[192:]==target[192:],'ELF does not pair with candidate ROM'
    sections=[struct.unpack_from('<IIIIIIIIII',raw,h[6]+i*h[11]) for i in range(h[12])];out={}
    for sec in sections:
        if sec[1]!=2:continue
        st=sections[sec[6]];strings=raw[st[4]:st[4]+st[5]];file=None
        for pos in range(sec[4],sec[4]+sec[5],sec[9]):
            ni,value,size,info,other,index=struct.unpack_from('<IIIBBH',raw,pos);name=strings[ni:].split(b'\0',1)[0].decode()
            if info&15==4:file=name
            if info>>4==0 and info&15==1 and file:
                key=file+':'+name;assert key not in out;out[key]=(value,size)
    return out

class MagmaJourney(SouthernJourney):
    def __init__(self,rom,symbols,output,rom_sha,symbols_sha,fixture=None,source_manifest=None):
        assert digest(rom)==rom_sha and digest(symbols)==symbols_sha
        self.source_rom=Path(rom).resolve();self.source_symbols=Path(symbols).resolve();self.target_sha=rom_sha;self.symbol_sha=symbols_sha
        self.out=Path(output).resolve();self.out.mkdir(parents=True,exist_ok=True)
        self.rom=self.out/'tested.gba';self.symbol_path=self.out/'tested.sym';self.elf=self.out/'tested.elf'
        for src,dst in ((self.source_rom,self.rom),(self.source_symbols,self.symbol_path),(self.source_rom.with_suffix('.elf'),self.elf)):
            if src!=dst:shutil.copyfile(src,dst)
        self.locals=elf_locals(self.elf,self.rom)
        rows=[p for line in self.symbol_path.read_text().splitlines() if len(p:=line.split())==3];counts=Counter(p[2] for p in rows)
        self.sym={p[2]:int(p[0],16) for p in rows if counts[p[2]]==1}
        self.candidate={'rom_sha256':rom_sha,'symbols_sha256':symbols_sha,'elf_sha256':digest(self.elf),'rom_bytes':self.rom.stat().st_size,'bridge_sha256':digest(ROOT/'tools/mgba_bridge.so')}
        self.fixture=Path(fixture or ROOT/'tests/fixtures/v5-revision4/southern-all41-town.sav').resolve();sha=digest(self.fixture);assert sha in (FIXTURE_SHA,MINIMAL_SHA)
        self.minimal=sha==MINIMAL_SHA;self.source_bytes=self.fixture.read_bytes();self.source_bank=newest_bank(self.source_bytes);assert int.from_bytes(self.source_bank[12:14],'little')==4
        self.provenance={'fixture':str(self.fixture),'sram_sha256':sha,'source_rom_sha256':S3_ROM,'cross_rom_machine_state_loaded':False,'minimal_prior_route':self.minimal}
        manifest=Path(source_manifest or self.source_rom.parent/'source-hashes.json').resolve();self.source_hashes=json.loads(manifest.read_text());self.source_manifest_sha=digest(manifest)
        roots=list(dict.fromkeys([manifest.parent.parent,*manifest.parents,ROOT]));self.source_root=next(root for root in roots if all((root/p).is_file() for p in self.source_hashes))
        assert all(digest(self.source_root/p)==v for p,v in self.source_hashes.items()),'Candidate source changed before suite'
        shutil.copyfile(manifest,self.out/'candidate-source-hashes.json')
        self.test_sources={str(p.relative_to(ROOT)):digest(p) for p in (Path(__file__).resolve(),ROOT/'tests/region_journey.py',ROOT/'tests/northern_journey.py',ROOT/'tests/southern_journey.py',ROOT/'tools/mgba_runner.py')}
        self.inputs=[];self.checks=[];self.snapshots={};self.failures=[];self.timings={};self.cases=[];self.coverage=[];self.acquisitions=[];self.transitions=[];self.frame_windows=[];self.pixel_cases=[];self.main_selections=[];self.main_only=False
        self.layout=json.loads((ROOT/'assets/magma_region/layout.json').read_text());self.scene=self.layout
        self.e=Emulator(self.rom);self.e.load_save(self.fixture);self.e.reset();self.mask_cache={};self.descriptors={}
        for name,start,count in (('south',30,8),('magma',38,8)):
            table=self.sym[name+'_art_rooms'];candidates=[]
            for stride in (20,28,32):
                found=[]
                for i in range(count):
                    a=table+i*stride;w,h=struct.unpack('<HH',self.e.bytes(a,4));bitmap=self.e.read(a+4)
                    if (w,h)!=((480,320) if i<2 else (240,160)) or bitmap not in [v for k,v in self.sym.items() if k.startswith(name+'_background_')]:break
                    found.append(dict(address=a,width=w,height=h,bitmap=bitmap,stride=stride))
                if len(found)==count:candidates.append(found)
            assert len(candidates)==1
            self.descriptors.update({start+i:r for i,r in enumerate(candidates[0])})
        self.report()
    def local(self,name,width=None,file='magma_game.c'):
        address,size=self.locals[file+':'+name];assert width is None or width==size
        assert size in (1,2,4),(name,size)
        return self.e.read(address,size)
    def step(self,n,keys=0):
        before=self.get('room')
        if self.main_only and self.get('game_state')==PLAY:self.main_selections.append(self.selected().form_id)
        RegionJourney.step(self,n,keys)
        after=self.get('room')
        if before!=after:self.transitions.append({'frame':self.e.frame,'from':before,'to':after,'keys':keys})
    def report(self):
        data={'suite':'magma-native-controller-journey','controller_only':True,'game_ram_writes':0,'player_facing':False,**self.candidate,'provenance':self.provenance,'source_manifest_sha256':self.source_manifest_sha,'test_sources':self.test_sources,'checks':self.checks,'failures':self.failures,'snapshots':self.snapshots,'inputs':self.inputs,'transitions':self.transitions,'cases':self.cases,'frame_windows':self.frame_windows,'main_route_selected_forms':sorted(set(self.main_selections))}
        (self.out/'magma-journey.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    def snapshot(self,name,settle=True):
        if settle:self.settle()
        state=self.out/(name+'.state');save=self.out/(name+'.sav');shot=self.out/(name+'.png');self.e.state(state);save.write_bytes(self.e.bytes(0x0e000000,32768));self.e.screenshot(shot)
        self.snapshots[name]={'rom_sha256':self.target_sha,'symbols_sha256':self.symbol_sha,'state_path':str(state),'state_sha256':digest(state),'sram_path':str(save),'sram_sha256':digest(save),'screenshot':str(shot),'status':self.status(),'quests':[self.quest(q) for q in range(38)],'obtained_form_ids':self.collection(),'owned_form_ids':[c.form_id for c in self.live()],'objectives':list(self.state().quests.objectives)[30:38],'puzzle':self.puzzle()}
        self.report();print(name,self.status(),'quests',[self.quest(q) for q in range(30,38)],flush=True);return name
    def mask(self):
        raw,w,h=SouthernJourney.mask(self);b=bytearray(raw);room=self.get('room');points=[]
        if room in (42,43,44) or (room==40 and self.local('trial_index') in (0,1)):
            p=self.puzzle()
            for cell in p[:1 if room in (40,42) else 2]:points.append((48+cell%7*24,32+cell//7*18))
        elif room==38:points.append((self.local('lesson_x'),232))
        elif room==39:points.append((self.local('screen_x'),264))
        for x,y in points:
            for yy in range(max(0,y-11),min(h,y+11)):b[yy*w+max(0,x-11):yy*w+min(w,x+11)]=b'\1'*(min(w,x+11)-max(0,x-11))
        return b,w,h
    def puzzle(self):return list(self.e.bytes(self.sym['magma_game_puzzle'],4))
    def object(self,key):return next(o for o in self.layout['rooms'][self.get('room')-38]['objects'] if o['key']==key)
    def open_tab(self,tab):
        self.settle();self.tap('START',2,4)
        for _ in range(10):
            if self.get('journal_tab')==tab:break
            self.tap('A',2,4)
        self.check(self.get('game_state')==PAUSE and self.get('journal_tab')==tab,f'journal tab{tab} opens')
    def target(self,x,y,face=1):
        dx,dy={0:(0,-16),1:(0,16),2:(16,0),3:(-16,0)}[face]
        self.act(x+dx,y+dy,face)
    def field(self,form,x,y,face=1):
        self.owned_select(form);dx,dy={0:(0,-16),1:(0,16),2:(16,0),3:(-16,0)}[face]
        self.goto(x+dx,y+dy,radius=4);self.face(face)
        self.check(abs(self.get('px')-x)+abs(self.get('py')-y)<23,'field approach is inside actual interaction range')
        self.ready();self.tap('R');self.settle()
    def slide(self,index,dirs,side=1):
        cell=self.puzzle()[index];x,y=48+cell%7*24,32+cell//7*18;self.target(x,y,side)
        self.check(self.local('grab')==index,'A grabs the actual movable object')
        for d in dirs:
            before=self.puzzle();self.tap(d);self.settle();self.check(self.puzzle()!=before,'pressed direction slides actual object without RAM mutation')
        self.tap('A');self.settle();self.check(self.local('grab')==255,'A releases object')
    def entry(self,target):
        here=self.get('room')
        if here==30 and target==38:self.target(288,248)
        elif here==38 and target==30:self.target(240,268)
        elif here==38 and target==39:self.goto(304,16);self.step(8,'UP');self.settle()
        elif here==39 and target==38:self.goto(240,300);self.step(8,'DOWN');self.settle()
        elif here==38 and target==40:self.target(80,136)
        elif here==39 and target==41:self.target(80,88)
        elif here==39 and target==42:self.target(400,56)
        elif here in (42,43,44) and target==here+1:self.target(216,56)
        else:raise AssertionError(('unsupported Magma entry',here,target))
        self.check(self.get('room')==target,'actual exit/interaction reaches intended area')
    def boot(self):
        self.step(150);self.tap('START',2,35);self.settle();s=self.state();b=self.source_bank
        self.check(self.get('room')==30,'delivered Southern SRAM resumes in original town')
        self.check(bytes(s.roster.instances)==b[160:4000],'revision4 to5 preserves160 exact individual records')
        self.check(bytes(s.roster.party)==b[4000:4004] and s.roster.selected_party==b[4004],'party assignments and selected identity preserved')
        self.check(bytes(s.roster.seen)+bytes(s.roster.obtained)+bytes(s.roster.rewards)==b[96:144],'historical collections and generic reward receipts preserved')
        self.check(bytes(s.quests)==b[4032:4296] and bytes(s.equipment)==b[4544:5056],'historical quest and equipment bytes preserved')
        self.check(all(self.quest(q)==0 and not s.quests.objectives[q] for q in range(30,38)) and not s.quests.region_flags[3],'migration invents no Magma state')
        saved=self.e.bytes(0x0e000000,32768);migrated=newest_bank(saved)
        self.check(int.from_bytes(migrated[12:14],'little')==5 and migrated[32:]==b[32:],'migration commits exact unchanged payload at content revision5')
        self.old_ids={c.instance_id for c in self.live()};self.snapshot('00-s3-forward-migration');self.entry(38);self.snapshot('01-lift-entry')
        self.cadence('magma-town-idle',120)
    def recruits_main(self):
        self.target(160,176);self.target(144,232);self.check(self.local('grab')==2,'town lesson has physical grab')
        self.tap('RIGHT');self.settle();self.tap('RIGHT');self.settle();self.tap('A');self.settle();self.check(self.local('grab')==255,'town grab releases after save completes')
        self.check(self.state().quests.objectives[30]&1,'two spatial slides reach public shelf')
        self.target(224,208);self.target(160,176);self.check(self.quest(30)==3 and any(c.form_id==31 for c in self.live()),'teaching quest earns first real companion')
        self.assign(0,31);self.select_form(31);self.entry(39)
        for x in (192,240,288):self.target(x,192)
        self.check(self.quest(31)==3 and any(c.form_id==34 for c in self.live()),'guided footpath earns second real companion')
        self.assign(1,34);self.select_form(31);self.target(80,264);self.snapshot('02-teaching-companions');self.main_only=True
    def clear_enemies(self):
        self.step(60);weapon=1 if self.main_only or self.minimal else 2;self.equip_item(0,weapon);trace=[]
        # Leave the public-rest interaction radius before using A as a weapon.
        # Otherwise an enemy following onto the anchor correctly makes A rest,
        # rather than attacking; all repositioning is ordinary walking input.
        if self.get('room')==39 and abs(self.get('px')-80)+abs(self.get('py')-264)<32:
            self.goto(112,288)
        for _ in range(160):
            live=[(i,e) for i,e in enumerate(self.enemies()) if e['hp']>0]
            if not live:break
            self.check(self.get('game_state')==PLAY,'ordinary combat remains alive without injected health')
            index,e=min(live,key=lambda row:abs(row[1]['x']-self.get('px'))+abs(row[1]['y']-self.get('py')))
            dx=e['x']-self.get('px');dy=e['y']-self.get('py')
            if abs(dx)+abs(dy)>24:
                b,w,h=self.mask();candidates=[(abs(x-self.get('px'))+abs(y-self.get('py')),x,y) for x,y in ((e['x']-20,e['y']),(e['x']+20,e['y']),(e['x'],e['y']+20),(e['x'],e['y']-20)) if 5<=x<w-5 and 5<=y<h-5 and not b[y*w+x]]
                self.check(bool(candidates),'enemy has clear ordinary attack approach');_,x,y=min(candidates);self.goto(x,y)
                e=self.enemies()[index];dx=e['x']-self.get('px');dy=e['y']-self.get('py')
            self.face((3 if dx>0 else 2) if abs(dx)>abs(dy) else (0 if dy>0 else 1))
            if self.get('room')==39 and abs(self.get('px')-80)+abs(self.get('py')-264)<26:
                self.goto(112,288)
                continue
            before=e['hp_q4'];self.tap('A',2,22);self.settle();trace.append({'frame':self.e.frame,'enemy':index,'before':before,'after':self.enemies()[index]['hp_q4']})
        self.check(not any(e['hp']>0 for e in self.enemies()),'all ordinary enemies defeated through actual weapon collision')
        self.cases.append({'name':'ordinary-combat','room':self.get('room'),'weapon_item':weapon,'trace':trace})
    def main_route(self):
        self.entry(42);self.clear_enemies();self.snapshot('03-intake-unsolved')
        self.field(31,48,68,3);self.check(self.puzzle()[2]==1,'teaching heat ability charges actual brick at input')
        self.slide(0,['DOWN','DOWN']+['RIGHT']*6+['UP','UP'])
        self.check(self.state().quests.objectives[32]&1,'heated physical brick reaches output across shaped room')
        self.snapshot('04-intake-solved');self.entry(43);self.clear_enemies()
        self.slide(0,['DOWN','RIGHT','RIGHT'],side=2);self.slide(0,['UP']*4);self.slide(1,['LEFT','UP'])
        self.field(34,168,104);self.check(self.state().quests.objectives[32]&2,'brace requires both actual baffle and shoe rests')
        self.snapshot('05-vault-solved');self.entry(44);self.clear_enemies()
        self.field(31,48,68,3);self.slide(0,['DOWN','DOWN']+['RIGHT']*6+['UP','UP']);self.slide(1,['LEFT']+['UP']*3,side=2)
        self.field(34,168,104);self.goto(208,104);self.face(2)
        for _ in range(4):
            if self.state().quests.objectives[32]&4:break
            self.tap('A',2,24);self.settle()
        self.check(self.state().quests.objectives[32]&4,'ordinary starter sword releases prepared physical pin')
        self.snapshot('06-gallery-solved');self.entry(45);self.machine();self.main_only=False
        self.target(208,136,0);self.check(self.get('room')==38,'cleared regulator opens ordinary return route')
        self.target(160,176);self.check(self.quest(32)==3,'chapter reward is claimed once from town NPC')
        self.target(112,248);self.snapshot('07-magma-main-cleared')
    def machine(self):
        self.equip_item(0,1);self.target(120,112);self.snapshot('regulator-telegraph');trace=[]
        for cycle in range(24):
            if self.get('magma_game_machine_stage',1)==5:break
            self.goto(32,108);self.face(1)
            for _ in range(300):
                stage=self.get('magma_game_machine_stage',1)
                if stage==1:break
                self.step(1)
            self.target(32,80);self.goto(120,48);self.face(0)
            for _ in range(260):
                stage=self.get('magma_game_machine_stage',1)
                if stage in (3,5):break
                self.step(1)
            for _ in range(4):
                if self.get('magma_game_machine_stage',1)!=3:break
                before=self.get('magma_game_machine_hp',1);self.tap('A',2,22);self.settle();after=self.get('magma_game_machine_hp',1)
                trace.append({'frame':self.e.frame,'before':before,'after':after,'stage':self.get('magma_game_machine_stage',1)})
            self.check(self.get('game_state')==PLAY,'regulator attempts retain real player health')
        self.check(self.get('magma_game_machine_stage',1)==5 and self.get('magma_game_machine_hp',1)==0,'manual diversion and starter sword defeat regulator')
        self.check(any(row['after']<row['before'] for row in trace),'actual weapon contacts reduce regulator HP')
        self.cases.append({'name':'regulator-starter-sword','trace':trace});self.snapshot('regulator-cleared')
    def to_town(self):
        while self.get('room')>=40:
            r=self.get('room');self.leave_interior(38 if r==40 else 39 if r in (41,42) else r-1)
        if self.get('room')==39:self.entry(38)
        self.check(self.get('room')==38,'ordinary walk returns to Magma town')
    def optional_recruits(self):
        self.entry(40);self.target(48,64)
        for x,y in ((168,64),(88,64),(168,64),(88,64),(128,64),(168,64),(208,80)):
            self.target(x,y)
        self.check(self.quest(33)==3,'three distinct workbench configurations plus personal return earn pots quest')
        for x,y in ((144,96),(176,96),(192,112),(56,112),(88,112),(120,112)):self.target(x,y)
        self.check(all(any(c.form_id==f for c in self.live()) for f in (43,97)),'two workshop discoveries retain two new individuals')
        self.to_town();self.target(384,208);self.entry(40)
        for x in (48,80,112):self.target(x,96)
        self.to_town();self.target(384,176);self.check(self.quest(36)==3,'returned chime is claimed through actual town conversation');self.target(112,248)
        self.entry(39);self.clear_enemies()
        for x,y in ((72,208),(104,208),(392,208),(424,208),(272,96),(304,96),(304,96)):self.target(x,y)
        self.check(all(any(c.form_id==f for c in self.live()) for f in (37,46,95)),'three field invitations are earned from distinct interactions')
        self.target(128,264);self.check(self.local('grab')==3,'fallen screen is a movable obstacle')
        self.tap('RIGHT');self.settle();self.tap('RIGHT');self.settle();self.tap('A');self.settle()
        self.target(104,112);self.target(136,216);self.check(self.quest(35)==3,'screen and outside return restore one personal route')
        self.target(104,112);self.check(self.get('room')==40,'repaired outside path truly connects to workshop')
        self.target(208,136,0);self.check(self.get('room')==39,'workshop return control reaches field using authorized spawn')
        self.target(80,264);self.clear_enemies();self.target(368,264);self.entry(42);self.entry(43);self.entry(44);self.target(72,112)
        self.target(216,136,0);self.check(self.get('room')==39,'gallery shortcut physically returns to field')
        self.target(336,240);self.target(304,232);self.check(self.quest(37)==3,'carried tray reaches proper field recipient before reward')
        self.target(80,264);self.entry(41);self.clear_enemies()
        for x,y in ((48,64),(80,64),(112,64),(144,64),(208,80),(48,96),(80,96),(144,96),(176,96),(192,112)):self.target(x,y)
        self.check(all(any(c.form_id==f for c in self.live()) for f in (40,99)),'bowl and listening discovery earn distinct grotto companions')
        self.check(self.state().quests.region_flags[9]==127,'all seven field source receipts are actually earned')
        self.check(self.state().quests.region_flags[19]==7,'three-step discovery completes without duplicate reward')
        self.check(all(self.quest(q)==3 for q in range(30,38)),'all eight global Magma quests are claimed')
        self.check(len(self.live())==(17 if self.minimal else 30),'all nine new families retain their own immutable IDs')
        self.to_town();self.target(112,248);self.snapshot('08-all-nine-families-and-stories')
    def travel(self,target,clear=False):
        if self.get('room')==target:return
        while self.get('room')>=40:
            r=self.get('room')
            if r==44 and self.state().quests.objectives[32]&4:self.target(216,136,0)
            elif r==45 and self.get('magma_game_machine_stage',1)==5:self.target(208,136,0)
            else:self.leave_interior(38 if r==40 else 39 if r in (41,42) else r-1)
        if target==38:
            if self.get('room')==39:self.entry(38)
        elif target==40:
            if self.get('room')==39:self.entry(38)
            self.entry(40)
        else:
            if self.get('room')==38:self.entry(39)
            if target>=41:
                self.entry(41 if target==41 else 42)
                while self.get('room')<target:self.entry(self.get('room')+1)
        self.check(self.get('room')==target,'ordinary connected route reaches trial area')
        if clear:
            if target==39:self.target(80,264)
            if any(e['hp']>0 for e in self.enemies()):self.clear_enemies()
    def start_trial(self,form,area,key=1):
        self.to_town();self.target(112,248);self.travel(area,clear=True);self.owned_select(form);self.ready()
        self.target(*( (432 if key==1 else 400,280) if area==38 else (208 if key==1 else 272,248) if area==39 else (24 if key==1 else 216,112)))
        identity=self.selected().instance_id
        self.check(self.local('trial_id')==identity and self.local('trial_slot')==self.roster().party[self.roster().selected_party],'trial pins actual selected individual by slot and immutable ID')
        self.check(self.local('trial_index')<15,'explicit trial sign begins valid authored trial')
        return identity
    def proof(self,form,key,identity):
        c=self.selected();self.check(c.form_id==form and c.instance_id==identity and c.trial_flags&key,'correct physical trial completes for the same actual individual')
        self.check(c.level>=(32 if form in (32,35) else 26) and c.bond>=(60 if form in (32,35) else 45),'personal proof supplies non-grind evolution training floor')
        self.snapshot(f'trial-{form}-key{key}-complete')
    def evolve(self,source,target):
        self.to_town();self.target(112,248);self.owned_select(source);identity=self.selected().instance_id;slot=self.roster().party[self.roster().selected_party]
        self.open_tab(3);self.tap('SELECT');self.check(self.get('game_state')==7,'eligible evolution opens explicit confirmation')
        before=bytes(self.roster());self.tap('B');self.check(self.get('game_state')==PAUSE and bytes(self.roster())==before,'decline keeps actual collection byte-identical')
        self.tap('SELECT')
        if self.get('progression_evolution_target')!=target:self.tap('RIGHT')
        self.check(self.get('progression_evolution_target')==target,'explicit displayed evolution target selected')
        self.e.screenshot(self.out/f'evolve-{source}-{target}-choice.png');self.tap('A');self.settle();self.close_menu()
        c=self.roster().instances[slot];self.check(c.instance_id==identity and c.form_id==target,'evolution keeps actual individual and applies exact chosen target')
        self.snapshot(f'evolved-{target}')
    def repeat_base(self,form):
        area,x,y={37:(39,80,232),40:(41,176,64),43:(40,160,112),46:(39,424,240)}[form]
        self.travel(area,clear=True);before={c.instance_id for c in self.live()};old={c.instance_id:bytes(c) for c in self.live()}
        self.target(x,y);self.target(x,y);fresh=[c for c in self.live() if c.instance_id not in before]
        self.check(len(fresh)==1 and fresh[0].form_id==form,'two explicit invitation interactions retain one new branch individual')
        self.check(all(bytes(c)==old[c.instance_id] for c in self.live() if c.instance_id in old),'repeat source grants no XP/bond or replacement to old individuals')
        self.owned_select(form);return fresh[0].instance_id
    def trials_and_evolutions(self):
        # Optional collection tour uses genuinely earned protective equipment;
        # the independent main/minimal route above stays starter-only.
        for slot,item in ((0,2),(1,36),(2,53),(3,67),(4,82)):self.equip_item(slot,item)
        self.target(112,248)
        i=self.start_trial(31,38);self.field(31,144,232);self.target(144,232)
        for d in ('RIGHT','RIGHT'):self.tap(d);self.settle()
        self.tap('A');self.settle();self.travel(40);self.field(31,48,86,3);self.slide(0,['RIGHT']*2)
        self.travel(42,clear=True);self.field(31,48,68,3);self.slide(0,['DOWN']*2+['RIGHT']*6+['UP']*2);self.proof(31,1,i);self.evolve(31,32)
        i=self.start_trial(32,40,2);self.field(32,48,86,3);self.slide(0,['RIGHT']*2);self.slide(0,['RIGHT']*2);self.target(144,112)
        self.slide(0,['LEFT']*4);self.field(32,48,86,3);self.slide(0,['RIGHT']*5);self.slide(0,['LEFT']);self.target(144,112)
        self.slide(0,['LEFT']*4);self.field(32,48,86,3);self.slide(0,['RIGHT']*6);self.travel(44,clear=True);self.target(72,112);self.proof(32,2,i);self.evolve(32,33)
        i=self.start_trial(34,39);self.field(34,176,128);self.field(34,272,128);self.travel(43,clear=True)
        self.slide(0,['DOWN','RIGHT','RIGHT'],2);self.slide(0,['UP']*4);self.slide(1,['LEFT','UP']);self.field(34,168,104);self.proof(34,1,i);self.evolve(34,35)
        i=self.start_trial(35,39,2);self.field(35,320,112);self.field(35,320,264,0);self.travel(44,clear=True)
        self.slide(0,['DOWN']*2+['RIGHT']*6+['UP']*2);self.slide(1,['LEFT']+['UP']*3,2);self.field(35,48,104,3);self.proof(35,2,i);self.evolve(35,36)
        i=self.start_trial(37,39);self.field(37,72,176,0);self.field(37,104,176,0);self.proof(37,1,i);self.evolve(37,38);self.repeat_base(37)
        i=self.start_trial(37,39,2);self.target(392,208);self.field(37,328,128);self.field(37,360,128);self.target(336,240);self.travel(40);self.target(168,64);self.proof(37,2,i);self.evolve(37,39)
        i=self.start_trial(40,41);self.field(40,48,64);self.field(40,112,64)
        for x in (80,144,176):self.target(x,96)
        self.proof(40,1,i);self.evolve(40,41);self.repeat_base(40)
        i=self.start_trial(40,39,2);self.field(40,272,128);self.travel(41,clear=True);self.field(40,48,64);self.travel(39,clear=True);self.field(40,304,128);self.travel(41,clear=True);self.field(40,112,64);self.proof(40,2,i);self.evolve(40,42)
        i=self.start_trial(43,40);self.target(128,64);self.field(43,144,96,2);self.field(43,176,96,2);self.travel(41,clear=True);self.field(43,176,96,2);self.proof(43,1,i);self.evolve(43,44);self.repeat_base(43)
        i=self.start_trial(43,40,2);self.field(43,80,96,2);self.field(43,112,96,3);self.target(48,96);self.proof(43,2,i);self.evolve(43,45)
        i=self.start_trial(46,39);self.field(46,392,208);self.field(46,424,240);self.travel(44,clear=True);self.field(46,72,112);self.proof(46,1,i);self.evolve(46,47);self.repeat_base(46)
        i=self.start_trial(46,39,2);self.field(46,392,208);self.target(424,240);self.travel(40);self.field(46,128,64);self.proof(46,2,i);self.evolve(46,48)
        i=self.start_trial(95,39);self.target(272,96);self.field(95,304,96);self.target(128,112);self.field(95,160,112);self.travel(41,clear=True);self.target(48,64);self.field(95,80,64);self.proof(95,1,i);self.evolve(95,96)
        i=self.start_trial(97,40);self.target(128,64);self.field(97,56,112);self.field(97,88,112);self.travel(44,clear=True);self.field(97,48,104,3);self.proof(97,1,i);self.evolve(97,98)
        i=self.start_trial(99,41);self.target(80,96);self.target(144,96);self.travel(38);self.field(99,288,248);self.travel(41,clear=True);self.field(99,112,64);self.field(99,176,96);self.proof(99,1,i);self.evolve(99,100)
        expected=sorted(SOUTH_FORMS+list(range(31,49))+list(range(95,101)))
        self.check(self.collection()==expected and len(self.live())==34,'all65 histories earned while retaining34 actual individuals')
        self.check(self.old_ids<={c.instance_id for c in self.live()},'all21 Southern individuals remain retained after every branch')
        self.target(112,248);self.snapshot('09-all65-earned-town')
    def cadence(self,name,count=120,keys=None):
        self.settle();self.step(10);last=self.get('frame');page=self.e.read(0x04000000,2)&16;trace=[]
        for i in range(count):
            self.step(1,keys(i) if keys else 0);now=self.get('frame');newpage=self.e.read(0x04000000,2)&16
            trace.append({'delta':(now-last)&0xffffffff,'flip':newpage!=page,'cycles':self.get('render_cycles'),'state':self.get('game_state'),'obj_count':self.get('obj_count')});last,page=now,newpage
        result={'name':name,'hardware_frames':count,'updates':sum(r['delta'] for r in trace),'flips':sum(r['flip'] for r in trace),'max_cycles':max(r['cycles'] for r in trace),'trace':trace};self.frame_windows.append(result);self.report()
        self.check(all(r['delta']==1 and r['flip'] and r['cycles']<280896 for r in trace),name+' updates and presents once every native frame')
    def run(self,scope):
        self.boot()
        if scope=='migration':return
        self.recruits_main()
        if scope=='teaching':return
        self.main_route()
        if scope=='main':return
        self.optional_recruits()
        self.trials_and_evolutions()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',required=True,type=Path);p.add_argument('--symbols',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True);p.add_argument('--source-sram',type=Path);p.add_argument('--scope',choices=('migration','teaching','main','full'),default='teaching');a=p.parse_args()
    run=MagmaJourney(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_sram)
    try:run.run(a.scope)
    except Exception as exc:run.failures.append({'error':str(exc),'status':run.status()});run.snapshot('failure',settle=False);raise
    finally:run.report();run.e.close()
if __name__=='__main__':main()
