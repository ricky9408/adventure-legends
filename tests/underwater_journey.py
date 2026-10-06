#!/usr/bin/env python3
"""Underwater controller bringup; authenticated delivered Magma SRAM only.
No old-ROM machine states and no game RAM writes. Developer progression spoilers.
Development routes are not release acceptance until the final ROM is frozen.
"""
from __future__ import annotations
import argparse,ctypes as C,json,shutil,struct
from pathlib import Path
from collections import Counter
from magma_journey import MagmaJourney,elf_locals,ROOT,digest,PLAY,DIALOG,PAUSE,DEAD,SAVING
from region_journey import RegionJourney,Emulator
from northern_journey import newest_bank
from southern_journey import SouthernJourney
from underwater_collection_route import UnderwaterCollectionRoute
MAGMA_SHA='a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858'
MINIMAL_SHA='f584de3b29cb77731148b31b99dc40e0c7e4ec05f1aac42e0d38dd5b44612eeb'
MAGMA_ROM='90ba47f30a0c94c28f073d26cc31ac5f5c736eb4d6e704d090892d2776f1ffb2'
EVENT_PENDING=10
class ReadOnlyGameEmulator(Emulator):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  self.lib.eb_write=self.write
 def write(self,*args,**kwargs):raise AssertionError('Game RAM writes are forbidden')
class UnderwaterJourney(UnderwaterCollectionRoute,MagmaJourney):
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
        self.fixture=Path(fixture or ROOT/'tests/fixtures/v5-revision5/magma-all65-town.sav').resolve();sha=digest(self.fixture);assert sha in (MAGMA_SHA,MINIMAL_SHA)
        self.minimal=sha==MINIMAL_SHA;self.prior_count=10 if self.minimal else 34;self.prior_history=10 if self.minimal else 65;self.source_bytes=self.fixture.read_bytes();self.source_bank=newest_bank(self.source_bytes);assert int.from_bytes(self.source_bank[12:14],'little')==5
        self.provenance={'fixture':str(self.fixture),'sram_sha256':sha,'source_rom_sha256':MAGMA_ROM,'cross_rom_machine_state_loaded':False,'minimal_prior_route':self.minimal}
        manifest=Path(source_manifest or self.source_rom.parent/'source-hashes.json').resolve();self.source_hashes=json.loads(manifest.read_text());self.source_manifest_sha=digest(manifest)
        roots=list(dict.fromkeys([manifest.parent/'runtime-source',manifest.parent/'source',manifest.parent.parent,*manifest.parents,ROOT]));self.source_root=next(root for root in roots if all((root/p).is_file() for p in self.source_hashes))
        assert all(digest(self.source_root/p)==v for p,v in self.source_hashes.items()),'Candidate source changed before suite'
        shutil.copyfile(manifest,self.out/'candidate-source-hashes.json')
        self.test_sources={str(p.relative_to(ROOT)):digest(p) for p in (Path(__file__).resolve(),ROOT/'tests/region_journey.py',ROOT/'tests/northern_journey.py',ROOT/'tests/southern_journey.py',ROOT/'tests/magma_journey.py',ROOT/'tools/mgba_runner.py',ROOT/'tests/underwater_collection_route.py')}
        self.inputs=[];self.checks=[];self.snapshots={};self.failures=[];self.timings={};self.cases=[];self.coverage=[];self.acquisitions=[];self.transitions=[];self.frame_windows=[];self.pixel_cases=[];self.main_selections=[];self.main_only=False
        self.layout=json.loads((ROOT/'assets/underwater_region/layout.json').read_text());self.scene=self.layout
        self.e=ReadOnlyGameEmulator(self.rom);self.e.load_save(self.fixture);self.e.reset();self.mask_cache={};self.descriptors={}
        for name,start,count in (('south',30,8),('magma',38,8),('underwater',46,8)):
            table=self.sym[name+'_art_rooms'];candidates=[]
            for stride in (20,28,32):
                found=[]
                for i in range(count):
                    a=table+i*stride;w,h=struct.unpack('<HH',self.e.bytes(a,4));bitmap=self.e.read(a+4)
                    if (w,h)!=(((self.layout['rooms'][i]['width'],self.layout['rooms'][i]['height']) if name=='underwater' else ((480,320) if i<2 else (240,160)))) or bitmap not in [v for k,v in self.sym.items() if k.startswith(name+'_background_')]:break
                    found.append(dict(address=a,width=w,height=h,bitmap=bitmap,stride=stride))
                if len(found)==count:candidates.append(found)
            assert len(candidates)==1
            self.descriptors.update({start+i:r for i,r in enumerate(candidates[0])})
        self.report()
    def report(self):
        data={'suite':'underwater-native-controller-journey','development_bringup':True,'controller_only':True,'game_ram_writes':0,'player_facing':False,**self.candidate,'provenance':self.provenance,'source_manifest_sha256':self.source_manifest_sha,'test_sources':self.test_sources,'checks':self.checks,'failures':self.failures,'snapshots':self.snapshots,'inputs':self.inputs,'transitions':self.transitions,'cases':self.cases,'frame_windows':self.frame_windows}
        (self.out/'underwater-journey.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    def snapshot(self,name,settle=True):
        if settle:
            self.settle();self.step(3);self.settle()
        state=self.out/(name+'.state');save=self.out/(name+'.sav');shot=self.out/(name+'.png')
        self.e.state(state);save.write_bytes(self.e.bytes(0x0e000000,32768));self.e.screenshot(shot)
        self.snapshots[name]={'rom_sha256':self.target_sha,'symbols_sha256':self.symbol_sha,'state_path':str(state),'state_sha256':digest(state),'sram_path':str(save),'sram_sha256':digest(save),'screenshot':str(shot),'status':self.status(),'quests':[self.quest(q) for q in range(46)],'obtained_form_ids':self.collection(),'owned_form_ids':[c.form_id for c in self.live()],'objectives':list(self.state().quests.objectives)[38:46]}
        self.report();print(name,self.status(),flush=True);return name
    def settle(self):
        for _ in range(700):
            mode=self.get('game_state')
            if mode in (SAVING,EVENT_PENDING,8):self.step(2)
            elif mode==DIALOG:self.tap('A',2,3)
            else:return
        raise AssertionError(('modal failed to settle',self.status()))
    def mask(self):
        if self.get('room')<46:return MagmaJourney.mask(self)
        base,w,h=SouthernJourney.mask(self);b=bytearray(base);a=self.get('room')
        p=list(self.e.bytes(self.sym['underwater_game_puzzle'],8))
        projection=self.local('projection',1,file='underwater_game.c')
        blocks=[]
        if not projection:
            if a==50:blocks=[(100,48,32,12) if p[2] else (132,80,40,12)]
            elif a==51:blocks=[(272,128,24,16) if p[2] else (208,128,64,16)]
            elif a==52:blocks=[(66+p[3]*16,60,12,24),(162-p[4]*16,60,12,24)]
            elif a==53 and not p[2]:blocks=[(48,56,32,12),(160,56,32,12)]
        for x,y,rw,rh in blocks:
            for yy in range(max(0,y-5),min(h,y+rh+5)):
                b[yy*w+max(0,x-5):yy*w+min(w,x+rw+5)]=b'\1'*(min(w,x+rw+5)-max(0,x-5))
        return b,w,h
    def boot_magma(self):
        self.step(150);self.tap('START',2,50);self.settle()
        self.check(self.get('game_state')==PLAY and self.get('room')==38,'authenticated Magma checkpoint resumes normally')
        bank=newest_bank(self.e.bytes(0x0e000000,32768))
        self.check(int.from_bytes(bank[12:14],'little')==6,'ordinary Continue autosave migrates to content revision6')
        self.check(bank[32:]==self.source_bank[32:],'revision5-to6 arrival preserves exact durable payload before new interactions')
        self.check(len(self.live())==self.prior_count and len(self.collection())==self.prior_history,'import retains exact prior individual and history counts, not new acquisitions')
        self.snapshot('00-magma-forward-migration')
    def enter_underwater(self):
        self.goto(416,240,radius=4);self.face(1);self.tap('A');self.settle()
        self.check(self.get('room')==46 and self.get('game_state')==PLAY,'real shell-lift input reaches Nacreway after bounded visit')
        self.check(self.state().quests.region_flags[4]==1,'only the new town visit is granted')
        self.check(len(self.live())==self.prior_count and len(self.collection())==self.prior_history,'travel grants no new companion history')
        self.snapshot('01-nacreway-first-arrival')
        self.step(130);self.snapshot('02-nacreway-clean-native')
        self.cadence('nacreway-idle',120)

    def entry(self,target):
        here=self.get('room')
        edges={(46,47):(464,160,'RIGHT'),(46,48):(240,16,'UP'),(46,38):(240,304,'DOWN'),
               (47,46):(240,304,'DOWN'),(47,50):(400,16,'UP'),(48,46):(240,304,'DOWN'),
               (48,49):(240,16,'UP'),(48,51):(464,160,'RIGHT'),(49,48):(120,144,'DOWN'),
               (49,52):(224,112,'RIGHT'),(50,47):(120,144,'DOWN'),(50,51):(224,112,'RIGHT'),
               (51,50):(240,304,'DOWN'),(51,52):(464,112,'RIGHT'),(51,48):(16,160,'LEFT'),
               (52,51):(120,144,'DOWN'),(52,53):(224,112,'RIGHT'),(52,49):(16,112,'LEFT'),
               (53,52):(120,144,'DOWN'),(53,46):(224,112,'RIGHT')}
        if here==38 and target==46:self.enter_underwater();return
        if (here,target) not in edges:return MagmaJourney.entry(self,target)
        x,y,key=edges[here,target];self.goto(x,y,radius=4)
        for _ in range(30):
            if self.get('room')!=here:break
            self.step(2,key);self.settle()
        self.check(self.get('room')==target,f'actual exit reaches area{target}')
    def cast_position(self,form,x,y,direction,command=None,label=None):
        self.owned_select(form)
        if command is not None:self.set_command(command)
        self.ready();self.goto(x,y,radius=4);self.face(direction);self.ready()
        identity=self.selected().instance_id
        self.cadence(label or f'cast-form{form}-area{self.get("room")}',120,lambda n:'R' if n==0 else 0)
        self.settle();self.check(self.selected().instance_id==identity,'actual field cast retains selected individual')
    def main_route(self):
        self.equip_item(0,1)
        self.target(144,104);self.check(self.state().quests.objectives[38]&1,'dotted plaque advances first teaching clue')
        self.target(120,72);self.check(self.quest(38)==3 and any(c.form_id==49 for c in self.live()),'keeper introduction earns real Inkbud')
        self.target(340,108);self.target(340,108)
        self.check(self.state().quests.objectives[39]&1,'manual lever can rise and return before companion gate')
        self.entry(47);self.goto(176,164);self.goto(304,164);self.goto(240,192);self.settle()
        self.check(self.state().quests.objectives[39]==3,'ordinary walking proves the safe return circuit')
        self.entry(46);self.target(340,72)
        self.check(self.quest(39)==3 and any(c.form_id==52 for c in self.live()),'shellwright earns real Bobclam without optional evolution')
        self.snapshot('03-two-teaching-companions')
        self.entry(47);self.entry(50)
        self.cast_position(49,88,96,1,67,'vestibule-real-echo')
        self.cast_position(52,128,72,3,70,'vestibule-real-ballast')
        self.target(120,104)
        self.check(self.state().quests.objectives[40]==1,'actual echo, ballast and map rotation solve first archive room')
        self.snapshot('04-vestibule-solved')
        self.entry(51)
        self.cast_position(52,176,168,1,70,'stacks-real-wide-handle')
        self.goto(312,112);self.step(4)
        self.cast_position(52,304,168,1,70,'stacks-real-return-handle')
        self.target(240,80)
        self.check(self.state().quests.objectives[40]==3,'walked side loop and second cast complete countercurrent sketch')
        self.snapshot('05-stacks-solved')
        self.entry(52);self.goto(80,96);self.face(1);self.tap('A');self.settle()
        self.cast_position(49,120,72,1,67,'listening-real-echo')
        self.target(120,112)
        self.check(self.state().quests.objectives[40]==7,'physical baffle and echo preserve the quiet motif')
        self.snapshot('06-listening-solved')
        self.entry(53)
        self.cast_position(49,120,72,1,67,'court-real-echo')
        self.cast_position(52,64,104,1,70,'court-real-ballast')
        self.target(176,80);self.target(120,112)
        self.snapshot('07-guardian-warning')
        for hit in range(3):
            for _ in range(100):
                if self.get('underwater_game_guardian_stage',1)==3:break
                self.step(2)
            self.check(self.get('underwater_game_guardian_stage',1)==3,'guardian joint opens only after actual warning/sweep')
            self.goto(120,72);self.face(1);self.tap('A',2,28);self.settle()
            self.check(self.get('underwater_game_guardian_hits',1)==hit+1,'starter sword records one new opening')
        self.check(self.state().quests.objectives[40]==15,'three actual weapon openings settle the guardian')
        self.snapshot('08-guardian-settled')
        self.entry(46);self.target(120,72)
        self.check(self.quest(40)==3,'return conversation claims the archive story')
        self.target(80,256);self.snapshot('09-main-cleared-town')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('rom','symbols','output'):p.add_argument('--'+k,type=Path,required=True)
 for k in ('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+k,required=True)
 p.add_argument('--source-manifest',type=Path)
 p.add_argument('--scope',choices=('entry','main','full'),default='entry')
 p.add_argument('--source-sram',type=Path)
 a=p.parse_args();r=UnderwaterJourney(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,fixture=a.source_sram,source_manifest=a.source_manifest)
 try:
  r.boot_magma();r.enter_underwater()
  if a.scope in ('main','full'):r.main_route()
  if a.scope=='full':r.collection_route()
 except Exception as exc:r.failures.append({'error':str(exc),'status':r.status()});r.snapshot('failure',settle=False);raise
 finally:r.report();r.e.close()
 return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
