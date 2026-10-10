#!/usr/bin/env python3
"""Controller-only Shared Horizons acceptance: exact candidates and earned H SRAM.

No game-memory writes or machine-state imports exist in the actual QA bridge.
Every hardware frame is gated; audio faults and ordinary native SRAM exports are
recorded. Developer evidence contains spoilers and is not a player artifact.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import ctypes as C
import gzip
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import traceback
from return_journey import ReturnJourney, ReturnTrial, preserve_pinned_file
from magma_journey import MagmaJourney, elf_locals
from region_journey import RegionJourney, Emulator, ROOT, digest, PLAY, DIALOG, PAUSE, DEAD, SAVING
from northern_journey import newest_bank, NorthernJourney
from southern_journey import SouthernJourney
from underwater_journey import UnderwaterJourney
from test_save5 import Save, Roster
from return_native_dependencies import resolve_mgba, identity, preload_frozen
from mgba_runner import keymask

H_ROM = 'f2330562b2c370d094164e7a5bf1e307da24412c88280cc880744eba072edaec'
H_PRODUCERS = {
 'a87942fda29e848124f4a7439ea96d59d0abcf66807c2a370ec1cbab68b0ab6c': {
  '05-all104-cold-reboot-after': 'd482466d04050c3d7f2e8eb8e1960729c9b9b33aa3e32440d186a4b54b854a69'},
 '0f40dd7f394909893f676c30b157b95d621bfba95ad5c97bd5196ff9a1af44c3': {
  'main-route-cold-save-after': '0c49f8cee8c601dbc3de35f2f98911b96f483fc32060b4b6817e650151fee970'},
 '73630064abbc0297912451ac61fef5df090828b02b2f3a032c7ed0c319d5c19c': {
  '02-main-return-complete': 'c3da1d2389a7865968c33dfbf5c32f8d40b66c2e2700b8d79ce2b3e9de519468'}}
MUSIC_FIELDS = ('music_faults','music_recoveries','music_stopped','music_irq_count','music_irq_late_max','music_track')
SOURCES = [
 (62,105,106,(352,224),(352,256),(352,176),(384,208)),
 (63,107,108,(416,96),(416,128),(392,96),(440,96)),
 (66,109,110,(64,256),(64,224),(48,240),(80,272)),
 (68,111,112,(192,112),(160,136),(176,112),(216,112)),
 (63,113,114,(64,64),(80,96),(48,64),(112,96)),
 (64,114,115,(200,112),(176,120),(200,104),(160,112)),
 (65,115,116,(416,256),(384,224),(384,256),(416,224)),
 (67,116,117,(64,192),(48,144),(64,144),(96,192)),
 (69,117,118,(208,112),(48,48),(192,64),(176,112)),
 (66,118,119,(48,208),(48,176),(48,160),(80,208)),
 (62,119,120,(304,272),(304,240),(320,240),(336,272)),
 (68,120,121,(48,112),(80,112),(80,88),(48,136))]
DOORS = {
 (62,61):(240,304,0), (62,63):(464,160,3), (62,66):(16,160,2), (62,64):(240,16,1),
 (63,62):(8,128,2), (63,65):(472,128,3), (63,64):(208,16,1), (63,67):(400,16,1),
 (64,63):(120,150,0), (64,62):(8,112,2),
 (65,63):(16,160,2), (65,66):(464,160,3), (65,67):(240,16,1),
 (66,65):(120,304,0), (66,62):(48,8,1), (66,69):(224,272,3),
 (67,63):(80,288,0), (67,65):(400,288,0), (67,68):(240,16,1), (67,69):(16,144,2),
 (68,67):(120,150,0), (69,66):(120,150,0), (69,67):(224,112,3)}

class HorizonsEmulator(Emulator):
    boot_sequence = itertools.count(1)
    def __init__(self, rom):
        bridge = ROOT / 'tools/horizons_mgba_bridge.so'
        self.lib = C.CDLL(str(bridge))
        for name,args,rest in [
            ('eb_open',[C.c_char_p],C.c_void_p),('eb_close',[C.c_void_p],None),
            ('eb_frames',[C.c_void_p,C.c_uint,C.c_uint],None),
            ('eb_read',[C.c_void_p,C.c_uint32,C.c_uint],C.c_uint32),
            ('eb_rgb',[C.c_void_p,C.c_void_p],None),('eb_framecounter',[C.c_void_p],C.c_uint),
            ('eb_reset',[C.c_void_p],None),('eb_load_save',[C.c_void_p,C.c_char_p],C.c_int),
            ('eb_save',[C.c_void_p,C.c_char_p],C.c_int)]:
            f=getattr(self.lib,name); f.argtypes=args; f.restype=rest
        assert not hasattr(self.lib,'eb_write') and not hasattr(self.lib,'eb_state')
        self.ptr=self.lib.eb_open(str(Path(rom).resolve()).encode())
        assert self.ptr, 'mGBA cannot open candidate'
        self.boot_serial=next(self.boot_sequence)
    def reset(self):
        super().reset(); self.boot_serial=next(self.boot_sequence)
    def write(self,*args,**kwargs):
        raise AssertionError('Game RAM writes forbidden')
    def state(self,*args,**kwargs):
        raise AssertionError('Machine-state import/export forbidden')
    def save(self,path):
        assert self.lib.eb_save(self.ptr,str(path).encode()), 'Native SRAM clone export failed'

class HorizonsProof(C.Structure):
    _fields_=[(n,C.c_uint) for n in ('id','party','scene','attempt','cast_token')]+[(n,C.c_ubyte) for n in ('mode','index','slot','selected','form','command','stage','setting','hits','walk','replay')]

class HorizonsJourney(ReturnJourney):
    def __init__(self, rom, symbols, output, rom_sha, symbols_sha, elf_sha,
                 source_manifest, manifest_sha, fixture=None, source_root=None, timing_mode='strict', producer=None, producer_sha=None, source_snapshot=None):
        self.source_rom, self.source_symbols = Path(rom).resolve(), Path(symbols).resolve()
        self.out = Path(output).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        assert not (self.out / 'horizons-journey.json').exists(), 'Use a fresh evidence directory; earlier reports are immutable'
        self.target_sha, self.symbol_sha = rom_sha, symbols_sha
        self.rom, self.symbol_path, self.elf = [self.out / ('tested.' + s) for s in ('gba', 'sym', 'elf')]
        for src, dst, sha in ((self.source_rom, self.rom, rom_sha),
                              (self.source_symbols, self.symbol_path, symbols_sha),
                              (self.source_rom.with_suffix('.elf'), self.elf, elf_sha)):
            preserve_pinned_file(src, dst, sha)
        self.locals = elf_locals(self.elf, self.rom)
        rows = [p for line in self.symbol_path.read_text().splitlines() if len(p := line.split()) == 3]
        counts = Counter(p[2] for p in rows)
        self.sym = {p[2]: int(p[0], 16) for p in rows if counts[p[2]] == 1}
        manifest = Path(source_manifest).resolve()
        assert digest(manifest) == manifest_sha, 'source manifest must be explicitly pinned'
        self.source_hashes = json.loads(manifest.read_text())
        roots = [Path(source_root).resolve()] if source_root else [manifest.parent / 'runtime-source', manifest.parent / 'source', manifest.parent.parent, *manifest.parents, ROOT]
        self.source_root = next((r for r in roots if all((r / p).is_file() and digest(r / p) == h for p, h in self.source_hashes.items())), None)
        assert self.source_root is not None, 'No complete matching frozen source closure'
        self.source_manifest_sha = manifest_sha
        shutil.copyfile(manifest, self.out / 'candidate-source-hashes.json')
        producer = Path(producer).resolve()
        assert digest(producer) == producer_sha
        p = json.loads(producer.read_text())
        self.same_candidate_source = producer_sha not in H_PRODUCERS
        assert p['controller_only'] and not p['game_ram_writes'] and not p['machine_state_loads']
        assert not p['failures'] and all(c['passed'] for c in p['checks'])
        assert p['global_native']['closed'] and not p['global_native']['exceptions']
        prior = p['snapshots'][source_snapshot]
        self.fixture = Path(fixture or prior['sram_path']).resolve()
        if not self.fixture.is_file() and fixture is None:self.fixture=producer.parent/Path(prior['sram_path']).name
        assert digest(self.fixture) == prior['sram_sha256']
        if self.same_candidate_source:
            assert p['suite']=='horizons-native-controller-journey' and p['finished_scope']=='full'
            assert p['rom_sha256']==rom_sha and p['symbols_sha256']==symbols_sha and p['elf_sha256']==elf_sha
            assert p['source_manifest_sha256']==manifest_sha and p['timing_mode']=='strict'
            assert p['provenance']['producer_sha256'] in H_PRODUCERS and p['provenance']['source_rom_sha256']==H_ROM
            assert source_snapshot=='07-all120-cold-reboot-after'
            assert len(prior['individuals'])==64 and len(prior['obtained_form_ids'])==120 and prior['quests']==[3]*60 and len(prior['gear_items'])==46
        else:
            assert p['rom_sha256']==H_ROM and digest(self.fixture)==H_PRODUCERS[producer_sha][source_snapshot]
        self.minimal = len(prior['individuals']) == 14
        self.prior_count, self.prior_history = len(prior['individuals']), len(prior['obtained_form_ids'])
        self.source_bytes = self.fixture.read_bytes()
        self.source_bank = newest_bank(self.source_bytes)
        assert int.from_bytes(self.source_bank[12:14], 'little') == (8 if self.same_candidate_source else 7)
        shutil.copyfile(producer, self.out / 'source-producer.json')
        shutil.copyfile(self.fixture, self.out / 'source-earned.sav')
        self.provenance = {'fixture_path': str(self.fixture), 'sram_sha256': digest(self.fixture),
                           'source_rom_sha256': rom_sha if self.same_candidate_source else H_ROM, 'minimal_prior_route': self.minimal,
                           'same_candidate_source': self.same_candidate_source,
                           'source_snapshot': source_snapshot, 'producer_sha256': producer_sha,
                           'source_individuals': self.prior_count, 'source_history': self.prior_history,
                           'cross_rom_machine_state_loaded': False}
        self.candidate = {'rom_sha256': rom_sha, 'symbols_sha256': symbols_sha, 'elf_sha256': elf_sha,
                          'rom_bytes': self.rom.stat().st_size, 'bridge_sha256': digest(ROOT / 'tools/horizons_mgba_bridge.so')}
        self.inputs, self.checks, self.failures, self.transitions = [], [], [], []
        self.cases, self.coverage, self.acquisitions, self.frame_windows = [], [], [], []
        self.snapshots, self.timings, self.pixel_cases, self.main_selections = {}, {}, [], []
        self.main_only, self.trace, self.machine_state_loads = False, None, 0
        self.finished_scope = None
        self.timing_mode = timing_mode
        self.global_enabled = True
        self.global_native = {'enabled': True, 'hardware_frames': 0, 'strict_frames': 0,
                              'loader_frames': 0, 'maximum_cycles': 0, 'maximum_obj_count': 0,
                              'exceptions': [], 'cold_prefixes': [], 'closed': False,
                              'trace_path': str(self.out / 'native-global.jsonl.gz')}
        self._native_stream = gzip.open(self.global_native['trace_path'], 'wt', encoding='utf-8', compresslevel=6)
        self._observed_boot_serial = None
        self._initial_prefix = None
        self._continue_prefix = None
        self.test_sources = self.freeze_helpers()
        navigation_root = self.out / 'helper-source'
        self.layout = json.loads((navigation_root / 'assets/region/layout.json').read_text())
        self.world = json.loads((navigation_root / 'assets/world_manifest.json').read_text())
        self.campaign = json.loads((navigation_root / 'assets/campaign_layouts.json').read_text())
        self.campaign_rooms = {r['id']: r for r in self.campaign['rooms']}
        self.return_geometry = json.loads((navigation_root / 'assets/return_region/geometry.json').read_text())
        ui_enum = re.search(r'enum\s*\{(.*?)\};', (self.source_root / 'src/ui.h').read_text(), re.S).group(1)
        self.ui_ids = {name.strip(): index for index, name in enumerate(ui_enum.split(',')) if name.strip()}
        self.e = HorizonsEmulator(self.rom)
        self.e.load_save(self.fixture)
        self.e.reset()
        self.mask_cache, self.descriptors = {}, {}
        for name, start in (('north', 22), ('south', 30), ('magma', 38), ('underwater', 46), ('return', 54), ('horizons', 62)):
            table = self.sym[name + '_art_rooms']
            candidates = []
            for stride in (20, 28, 32):
                found = []
                for i in range(8):
                    a = table + i * stride
                    w, h = struct.unpack('<HH', self.e.bytes(a, 4))
                    bitmap = self.e.read(a + 4)
                    if (w, h) not in ((240, 160), (480, 320), (480, 160), (240, 320)) or bitmap not in [v for k, v in self.sym.items() if k.startswith(name + '_background_')]:
                        break
                    found.append({'address': a, 'width': w, 'height': h, 'bitmap': bitmap, 'stride': stride})
                if len(found) == 8:
                    candidates.append(found)
            assert len(candidates) == 1, ('ambiguous compiled room descriptor', name)
            self.descriptors.update({start + i: r for i, r in enumerate(candidates[0])})
        assert C.sizeof(ReturnTrial) == 28
        self.report()

    def freeze_helpers(self):
        build=json.loads((ROOT/'tools/horizons_mgba_bridge.build.json').read_text())
        assert build['bridge_sha256']==digest(ROOT/'tools/horizons_mgba_bridge.so')
        assert build['source_sha256']==digest(ROOT/'tools/horizons_mgba_bridge.c')
        paths = {Path(__file__).resolve(), ROOT/'tools/horizons_mgba_bridge.c', ROOT/'tools/horizons_mgba_bridge.so', ROOT/'tools/build_horizons_mgba_bridge.sh', ROOT/'tools/horizons_mgba_bridge.build.json'}
        paths.update(ROOT/p for p in ('assets/region/layout.json','assets/world_manifest.json','assets/campaign_layouts.json','assets/return_region/geometry.json','assets/horizons_region/geometry.json'))
        for module in tuple(sys.modules.values()):
            name = getattr(module,'__file__',None)
            if name and Path(name).is_file() and Path(name).resolve().is_relative_to(ROOT):paths.add(Path(name).resolve())
        hashes={}
        for p in sorted(paths):
            relative=p.relative_to(ROOT); dest=self.out/'helper-source'/relative
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);hashes[str(relative)]=digest(dest)
        library,soname,discovery=resolve_mgba(ROOT/'tools/horizons_mgba_bridge.so',os.environ.get('HORIZONS_MGBA_LIBRARY'))
        dest=self.out/'helper-source/tools/emulator-libs'/Path(soname).name
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(library,dest)
        hashes[str(dest.relative_to(self.out/'helper-source'))]=digest(dest)
        receipt={'bridge_sha256':digest(ROOT/'tools/horizons_mgba_bridge.so'),'library_sha256':digest(dest),'loader_identity':soname,'actual_library':str(library),'discovery':discovery}
        (self.out/'emulator-library.json').write_text(json.dumps(receipt,indent=2)+'\n')
        (self.out/'helper-source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
        return hashes

    def report(self):
        data={'suite':'horizons-native-controller-journey','development_diagnostic':True,'release_acceptance':False,
              'finished_scope':self.finished_scope,'timing_mode':self.timing_mode,'controller_only':True,
              'game_ram_writes':0,'machine_state_loads':0,'physical_handheld_tested':False,'player_facing':False,
              **self.candidate,'provenance':self.provenance,'source_manifest_sha256':self.source_manifest_sha,
              'source_root':str(self.source_root),'helper_sources':getattr(self,'test_sources',{}),
              'checks':self.checks,'failures':self.failures,'snapshots':self.snapshots,'inputs':self.inputs,
              'transitions':self.transitions,'cases':self.cases,'acquisitions':self.acquisitions,
              'coverage':self.coverage,'frame_windows':self.frame_windows,'global_native':self.global_native,
              'main_route_selected_forms':sorted(set(self.main_selections)),
              'scope_limits':['No physical GBA test','Distinct diagnostics retain original failures','No synthetic records count as native collection']}
        (self.out/'horizons-journey.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

    def open_tab(self,tab):
        self.settle();self.tap('START',2,4)
        for _ in range(12):
            if self.get('journal_tab')==tab:break
            self.tap('A',2,4)
        self.check(self.get('game_state')==PAUSE and self.get('journal_tab')==tab,f'journal tab{tab} opens')

    def hz_local(self,name,width=None):return self.local(name,width,file='horizons_game.c')
    def hz_setting(self):
        address,size=self.locals['horizons_game.c:setting'];assert size==16
        return list(self.e.bytes(address,size))
    def proof(self):
        address,size=self.locals['horizons_game.c:proof'];assert size==C.sizeof(HorizonsProof)
        return HorizonsProof.from_buffer_copy(self.e.bytes(address,size))
    def proof_dict(self):return {n:getattr(self.proof(),n) for n,_ in HorizonsProof._fields_}
    def restore(self,*args):raise AssertionError('All Horizons routes are SRAM-only; no machine-state restores')
    def snapshot(self,name,settle=True):
        assert name not in self.snapshots, 'Snapshot names are immutable'
        if settle:self.settle();self.step(3);self.settle()
        save,shot=self.out/(name+'.sav'),self.out/(name+'.png')
        self.e.save(save);self.e.screenshot(shot)
        self.check(digest(self.fixture)==self.provenance['sram_sha256'],'source earned SRAM remains unchanged after native snapshot export')
        self.check(save.stat().st_size==32768,'normal native savedataClone exports exactly32768 cartridge SRAM bytes')
        self.check(save.read_bytes()==self.e.bytes(0x0e000000,save.stat().st_size),'normal native savedataClone matches visible SRAM')
        self.snapshots[name]={'rom_sha256':self.target_sha,'symbols_sha256':self.symbol_sha,'elf_sha256':self.candidate['elf_sha256'],
            'sram_path':str(save),'sram_sha256':digest(save),'sram_export':'mCore.savedataClone','screenshot':str(shot),
            'status':self.status(),'quests':[self.quest(q) for q in range(60)],'obtained_form_ids':self.collection(),
            'individuals':[{'slot':i,'form':c.form_id,'instance_id':c.instance_id,'trial_flags':c.trial_flags,'level':c.level,'bond':c.bond} for i,c in enumerate(self.roster().instances) if c.flags&1],
            'gear_items':[g.item_id for g in self.state().equipment.bag if g.item_id],
            'objectives':list(self.state().quests.objectives)[54:60],'proof':self.proof_dict(),'setting':self.hz_setting()}
        self.report();print(name,self.status(),'quests',[self.quest(q) for q in range(54,60)],flush=True)
        return name
    def mask(self):
        room=self.get('room')
        if 38<=room<54:return UnderwaterJourney.mask(self)
        if room<62:return ReturnJourney.mask(self)
        raw,w,h=SouthernJourney.mask(self);b=bytearray(raw)
        if room==63:
            x=self.hz_local('carriage_x',2)
            for y in range(60,85):b[y*w+x-12:y*w+x+13]=b'\1'*25
        return b,w,h
    def boot(self):
        self.step(150)
        self.measured('bounded-cold-earned120-continue' if self.same_candidate_source else 'bounded-cold-revision7-continue',lambda:(self.tap('START',2,90),self.settle()),cold_continue=True)
        bank=newest_bank(self.e.bytes(0x0e000000,32768))
        self.check(self.get('game_state')==PLAY,'authentic H SRAM resumes by ordinary Continue')
        self.check(int.from_bytes(bank[12:14],'little')==8,'ordinary Continue commits content revision8')
        self.check(bank[32:]==self.source_bank[32:],'revision7 migration retains all durable payload bytes')
        self.check(len(self.live())==self.prior_count and len(self.collection())==self.prior_history,'migration gives no automatic companion or history')
        if not self.same_candidate_source:self.check(all(not self.quest(q) and not self.state().quests.objectives[q] for q in range(54,60)),'migration grants no Horizons quests')
        else:self.check(all(self.quest(q)==3 for q in range(60)),'same-candidate earned120 cold branch retains all60 genuine quest claims')
        self.old_ids={c.instance_id for c in self.live()};self.old_history=self.collection();self.old_equipped=bytes(self.state().equipment.equipped)
        if self.minimal:self.check([self.state().equipment.bag[i].item_id if i<48 else 0 for i in self.state().equipment.equipped]==[1,0,0,0,0],'minimal route starts with only starter weapon and empty remaining gear slots')
        self.snapshot('00-revision8-exact-migration')
    def entry(self,target):
        here=self.get('room')
        if (here,target) in ((22,23),(23,22)):return NorthernJourney.entry(self,target)
        if (here,target) in ((30,31),(31,30)):return SouthernJourney.entry(self,target)
        if 46<=here<54 and 46<=target<54:return UnderwaterJourney.entry(self,target)
        if (here,target) in ((38,39),(39,38),(38,40),(39,41),(39,42),(42,43),(43,44),(44,45)):return MagmaJourney.entry(self,target)
        if (here,target) in ((40,38),(41,39),(42,39),(43,42),(44,43),(45,44)):return self.leave_interior(target)
        if (here,target)==(44,39):self.target(216,136,0);self.check(self.get('room')==target,'ordinary completed Magma shortcut returns to field');return
        if (here,target)==(45,38):self.target(208,136,0);self.check(self.get('room')==target,'ordinary completed Magma machine exit returns to town');return
        if here==61 and target==62:self.act(120,56,1)
        elif (here,target) in DOORS:
            x,y,f=DOORS[here,target];self.target(x,y,f)
        else:return ReturnJourney.entry(self,target)
        self.check(self.get('room')==target,f'ordinary controller exit {here} reaches {target}')
    def travel(self,target,clear=False):
        graph={0:[1,54,60],1:[0,16],16:[1,17,22,55],17:[16,56],22:[16,23,30,57],23:[22],
            30:[22,31,38,58],31:[30],38:[30,39,40,46],39:[38,41,42],40:[38],41:[39],42:[39,43],43:[42,44],44:[43,45,39],45:[44,38],
            46:[38,47,48],47:[46,50],48:[46,49,51],49:[48,52],50:[47,51],51:[50,52,48],52:[51,53,49],53:[52,46],
            54:[0],55:[16],56:[17],57:[22],58:[30,59],59:[58],60:[0,61],61:[60,62]}
        for a,b in DOORS:
            if b in (67,68) and not (self.quest(55)==self.quest(56)==3):continue
            if (a,b) in ((67,69),(69,67)) and self.quest(57)!=3:continue
            graph.setdefault(a,[]).append(b)
        queue,seen=deque([(self.get('room'),[])]),{self.get('room')}
        while queue:
            area,path=queue.popleft()
            if area==target:
                for destination in path:self.entry(destination)
                return
            for destination in graph.get(area,[]):
                if destination not in seen:seen.add(destination);queue.append((destination,path+[destination]))
        raise AssertionError(('no ordinary controller route',self.get('room'),target))
    def base_form(self,form):return form if any(c.form_id==form for c in self.live()) else form+1
    def cast_at(self,form,command,x,y,direction,wait=110,prepare=True):
        if prepare:self.owned_select(form);self.set_command(command)
        self.ready();self.goto(x,y,radius=4);self.face(direction);self.ready()
        before={'form':self.selected().form_id,'instance_id':self.selected().instance_id,'command':self.command(),'origin':[self.get('px'),self.get('py')],'face':direction,'proof':self.proof_dict(),'setting':self.hz_setting()}
        def actual_cast():
            self.step(1,'R')
            if command>=106:self.check(self.get('horizons_power_kind')==command and self.get('horizons_power_time')>0,'requested learned signature starts as a genuine live native cast')
            self.step(wait);self.settle()
        self.measured(f'cast{command}-room{self.get("room")}',actual_cast)
        self.cases.append({'cast':before,'proof_after':self.proof_dict(),'setting_after':self.hz_setting(),'frame':self.e.frame})
    def warm_at(self,x,y,prepare=True,manual=None):
        if prepare:self.owned_select(self.base_form(107));self.set_command(108)
        self.ready();self.goto(x,y,radius=4);self.face(2);self.ready()
        self.tap('R',1,12)
        if manual:self.target(*manual)
        self.tap('R',1,100);self.settle()
    def invite(self,index):
        area,form,command,point,*_=SOURCES[index]
        before=self.state_signature();r=self.roster();party=bytes(r.party);selected=r.selected_party;ids={c.instance_id for c in self.live()}
        self.target(*point)
        self.check(self.state_signature()==before and self.hz_local('invite_confirm',1)==index+1,'first A previews invitation without durable mutation')
        self.tap('B');self.check(self.state_signature()==before and not self.hz_local('invite_confirm',1),'B cancels invitation without durable mutation')
        self.target(*point);self.step(20,'DOWN');self.settle()
        self.check(self.state_signature()==before and not self.hz_local('invite_confirm',1),'walking away cancels invitation without consuming its solved attempt')
        self.target(*point);self.tap('A');self.settle()
        fresh=[c for c in self.live() if c.instance_id not in ids]
        self.check(len(fresh)==1 and fresh[0].form_id==form,f'source{index+1} genuinely admits exactly form{form}')
        self.check(bytes(self.roster().party)==party and self.roster().selected_party==selected,'full active party stores admission without eviction or selection')
        self.check(self.state().quests.region_flags[12+index//8]&(1<<(index%8)),f'source{index+1} commits one-shot receipt')
        self.acquisitions.append({'source':index+1,'form':form,'instance_id':fresh[0].instance_id,'frame':self.e.frame,'method':'actual solved encounter and explicit second A'})
    def initialize_horizons(self):
        self.travel(60);self.target(64,112);self.travel(62)
        self.target(72,256)
        self.target(208,208);self.target(272,208);self.goto(240,240);self.step(4);self.settle()
        self.check(self.state().quests.objectives[54]==3,'both physical braces and crosswalk earn intro composition')
        self.invite(0);self.target(120,208)
        self.check(self.quest(54)==3,'host claims first shared promise')
        self.snapshot('01-horizons-intro')
    def stage_contribution(self):
        self.travel(63);self.clear_enemies();self.target(136,80)
        before=self.state().quests.objectives[55]
        self.cast_at(105,106,224,90,2)
        self.check(self.hz_setting()[0]==0 and self.state().quests.objectives[55]==before,'closed first junction refuses correctly aimed load cast')
        self.target(80,96)
        self.cast_at(self.base_form(101),102,224,90,2)
        self.check(self.hz_setting()[0]==0 and self.state().quests.objectives[55]==before,'wrong companion command cannot move tagged load')
        self.cast_at(105,106,192,122,1)
        self.check(self.hz_setting()[0]==0,'wrong-side load cast cannot move the carriage')
        self.reset_horizons();self.check(self.hz_setting()[:3]==[0,0,0],'reset restores unfinished junction work')
        self.target(80,96)
        self.cast_at(105,106,224,90,2);self.check(self.hz_setting()[0]==1,'first load pull reaches socket1')
        self.cast_at(105,106,256,90,2);self.goto(256,128);self.step(4);self.settle()
        self.check(self.state().quests.objectives[55]&2,'load reaches safe procession handoff')
        self.travel(64);self.cast_at(105,106,64,88,1);self.cast_at(105,106,176,88,1)
        self.cast_at(self.base_form(101),102,208,120,1)
        self.check(self.state().quests.objectives[55]==7,'two hems and quiet pin earn theater composition')
        self.travel(62);self.target(72,256);self.travel(63);self.clear_enemies();self.invite(1);self.target(416,96)
        self.check(self.quest(55)==3,'stage contribution claimed');self.snapshot('02-stage-contribution')
    def water_contribution(self):
        self.travel(65);self.target(80,256);self.clear_enemies();self.target(80,256);self.target(96,176);self.target(336,208)
        self.cast_at(self.base_form(103),104,336,192,1)
        self.check(self.state().quests.objectives[56]&2,'stencil and flowing cast earn court composition')
        self.travel(66);self.clear_enemies();self.cast_at(105,106,176,248,2)
        self.cast_at(self.base_form(103),104,176,104,1);self.cast_at(self.base_form(103),104,208,104,1)
        self.check(self.state().quests.objectives[56]==7,'print spacing and two wet blocks preserve dry road')
        self.invite(2);self.travel(65);self.target(80,256);self.target(352,272)
        self.check(self.quest(56)==3,'water contribution claimed');self.snapshot('03-water-contribution')
    def main_route(self,arm_order='stage-first'):
        self.main_only=True
        self.equip_item(0,1);self.old_equipped=bytes(self.state().equipment.equipped)
        self.initialize_horizons()
        for route in ((self.stage_contribution,self.water_contribution) if arm_order=='stage-first' else (self.water_contribution,self.stage_contribution)):route()
        self.travel(65);self.target(80,256);self.travel(67);self.clear_enemies();self.cast_at(109,110,48,224,3);self.target(352,224);self.warm_at(300,208)
        self.check(self.state().quests.objectives[57]&3==3,'wagon transfer and same-cast wax press earn assembly access')
        self.travel(68)
        self.cast_at(self.base_form(103),104,192,96,1)
        self.check(self.hz_setting()[0]==0 and self.state().quests.objectives[57]==3,'wrong public demonstration order cannot advance the assembly')
        for form,cmd,x in ((105,106,48),(self.base_form(101),102,120),(self.base_form(103),104,192)):self.cast_at(form,cmd,x,96,1)
        self.check(self.state().quests.objectives[57]==7,'public assembly earns three distinct ordered contributions')
        if self.hz_local('performance_ticks',2):
            def phrase():return (self.hz_local('performance_ticks',2),self.get('horizons_music_note',1),self.get('horizons_music_left',1))
            before=phrase();self.step(30,'L');self.check(phrase()==before,'held L freezes live assembly choreography and short phrase together')
            self.step(1);self.tap('START',1,1);before=phrase();self.step(30)
            self.check(phrase()==before,'journal viewing freezes live assembly choreography and short phrase together')
            self.tap('B',1,1)
        self.coverage.append('native-public-assembly-three-commands-and-phrase-pause')
        self.invite(3);self.travel(62);self.target(120,208)
        self.check(all(self.quest(q)==3 for q in range(54,58)),'all four main Horizons quests are claimed')
        self.check(bytes(self.state().equipment.equipped)==self.old_equipped,'main route retains exactly its incoming equipped gear')
        self.check(len(self.live())==self.prior_count+4 and self.old_ids<={c.instance_id for c in self.live()},'main route retains every prior identity and only four mandatory recruits')
        if self.minimal:
            self.check(set(self.main_selections)<=set(self.old_history+[105,107,109,111]),'minimal main selects only guaranteed base companions and mandatory new recruits')
            self.check(self.collection()==sorted(self.old_history+[105,107,109,111]),'minimal main earns no optional recruit or evolution')
        self.coverage.append('controller-main-route-'+arm_order)
        self.main_only=False;self.snapshot('04-main-horizons-complete')
    def cold_reboot(self,name):
        self.settle();before=self.state_signature();self.snapshot(name+'-before');saved=self.snapshots[name+'-before']
        self.e.close();self.e=HorizonsEmulator(self.rom);self.e.load_save(saved['sram_path']);self.e.reset();self.step(150)
        self.measured(name+'-bounded-cold-continue',lambda:(self.tap('START',2,90),self.settle()),cold_continue=True)
        self.check(self.state_signature()==before,'ordinary SRAM cold reload preserves exact roster quest and equipment')
        self.check(not self.proof().mode,'cold reload discards all transient attempt rights');self.snapshot(name+'-after')
    def run(self,scope,arm_order):
        self.boot()
        if scope not in ('migration','followup-repeats'):self.main_route(arm_order)
        if scope in ('full','repeats'):self.collection_route()
        if scope in ('repeats','followup-repeats'):self.controls();self.repeat_route()
        if scope=='lifecycle':self.lifecycle()
        self.finished_scope=scope;self.verify_closures();self.check(digest(self.fixture)==self.provenance['sram_sha256'],'read-only source SRAM fixture remains byte-identical');self.report()

    def global_step(self, n, keys=0):
        """Observe every real hardware frame, without per-frame roster copies."""
        batch = {'frame': self.e.frame, 'frames': 0, 'requested_frames': int(n), 'keys': keys}
        self.inputs.append(batch)
        if self.e.boot_serial != self._observed_boot_serial:
            self._observed_boot_serial = self.e.boot_serial
            self._initial_prefix = {'kind': 'startup', 'boot_serial': self.e.boot_serial,
                                    'hardware_frames': 0, 'excluded_frames': 0, 'started': True, 'done': False}
            self.global_native['cold_prefixes'].append(self._initial_prefix)
        for _ in range(n):
            old, display_before = self.get('frame'), self.e.read(0x04000000, 2)
            page = display_before & 16
            state, room = self.get('game_state'), self.get('room')
            self.e.frames(1, keys)
            batch['frames'] += 1
            new, after_room = self.get('frame'), self.get('room')
            display_after = self.e.read(0x04000000, 2)
            row = {'hardware_frame': self.e.frame, 'sample_index': self.global_native['hardware_frames'],
                   'boot_serial': self.e.boot_serial, 'frame_before': old, 'frame_after': new,
                   'update_delta': (new - old) & 0xffffffff, 'counter_reset': new < old,
                   'page_flip': (display_after & 16) != page,
                   'display_before': display_before, 'display_after': display_after,
                   'cycles': self.get('render_cycles'), 'state_before': state, 'state_after': self.get('game_state'),
                   'room': after_room, 'journal_tab': self.get('journal_tab'),
                   'toast_id': self.get('toast_id'), 'toast_ticks': self.get('toast_ticks'),
                   'obj_count': self.get('obj_count')}
            prefix = self._continue_prefix if self._continue_prefix is not None else self._initial_prefix
            exempt = False
            if prefix is not None and not prefix['done']:
                prefix['hardware_frames'] += 1
                self.check(prefix['hardware_frames'] <= 160, 'global cold loader prefix stays within160 hardware frames')
                startup_blank = prefix['kind'] == 'startup' and (display_before & 128 or display_after & 128 or row['cycles'] == 0)
                if row['counter_reset'] or new == 0 or startup_blank:
                    prefix['started'] = True
                    prefix['excluded_frames'] += 1
                    exempt = True
                elif prefix['started']:
                    prefix['done'] = True
            row['music']={name:self.get(name) for name in MUSIC_FIELDS}
            row['cold_loader_exempt'] = exempt
            self.global_native['hardware_frames'] += 1
            if exempt:
                self.global_native['loader_frames'] += 1
            else:
                self.global_native['strict_frames'] += 1
                self.global_native['maximum_cycles'] = max(self.global_native['maximum_cycles'], row['cycles'])
                self.global_native['maximum_obj_count'] = max(self.global_native['maximum_obj_count'], row['obj_count'])
            self._native_stream.write(json.dumps(row, separators=(',', ':')) + '\n')
            if self.trace is not None:
                self.trace.append(row)
            if room != after_room:
                self.transitions.append({'frame': self.e.frame, 'from': room, 'to': after_room, 'keys': keys})
            if self.main_only and row['state_after'] == PLAY:
                base = self.sym['adventure_save'] + Save.roster.offset
                selected = self.e.read(base + Roster.selected_party.offset, 1)
                slot = self.e.read(base + Roster.party.offset + selected, 1) if selected < 4 else 255
                if slot < 160:
                    form = self.e.read(base + Roster.instances.offset + slot * 24, 1)
                    self.main_selections.append(form)
            bad = not exempt and (row['update_delta'] != 1 or not row['page_flip'] or row['cycles'] >= 280896 or row['obj_count'] > 128 or any(row['music'][key] for key in ('music_faults','music_recoveries','music_stopped')))
            if bad:
                self.global_native['exceptions'].append(row)
                self._native_stream.flush()
                label = 'global hardware frame has one update/flip within cycle/OAM budget'
                if self.timing_mode == 'collect-diagnostic':
                    self.checks.append({'label': label, 'passed': False, 'frame': self.e.frame})
                    self.failures.append({'kind': 'global-native-cadence', 'row': row, 'continued_only_for_diagnosis': True})
                else:
                    self.check(False, label)


    def reset_horizons(self):
        room=self.get('room');height=self.descriptors[room]['height']
        before=self.state_signature();self.target(24,height-28,0)
        self.check(self.hz_local('reset_confirm',1)==1,'reset requires second deliberate A')
        self.tap('B');self.check(self.state_signature()==before,'cancelled reset preserves durable state')
        self.target(24,height-28,0);self.tap('A');self.settle()
        self.check(not self.proof().mode and not self.hz_local('reset_confirm',1),'confirmed reset revokes transient proof')
        b,w,h=self.mask();self.check(not b[self.get('py')*w+self.get('px')],'reset landing is walkable with normal hero footprint')
    def first_optional(self,index):
        area,form,command,invite,manual,target,walk=SOURCES[index]
        self.travel(area)
        if area==65:self.target(80,256)
        if any(e['hp']>0 for e in self.enemies()):self.clear_enemies()
        if area==65:self.target(80,256)
        if index==6:self.owned_select(self.story_form(1));self.set_command(1)
        elif index==9:self.owned_select(self.base_form(103));self.set_command(104)
        elif index==10:self.owned_select(self.story_form(4));self.set_command(2)
        elif index==11:self.owned_select(self.story_form(7));self.set_command(3)
        else:self.owned_select(105);self.set_command(106)
        self.ready();self.target(*invite)
        self.check(self.proof().mode==1 and self.proof().index==index,'explicit optional invitation begins fresh local initial work')
        if index==4:self.target(*manual);self.target(*manual)
        elif index==5:self.target(*manual)
        elif index==6:self.target(*manual);self.cast_at(self.story_form(1),1,384,280,1,prepare=False)
        elif index==7:self.target(*manual);self.target(80,144)
        elif index==8:self.target(*manual);self.target(192,32)
        elif index==9:self.target(*manual);self.cast_at(self.base_form(103),104,48,192,1,prepare=False)
        elif index==10:self.cast_at(self.story_form(4),2,320,264,1,prepare=False)
        elif index==11:
            self.target(*manual);self.cast_at(self.story_form(7),3,80,120,1,prepare=False)
            self.cast_at(self.base_form(101),102,80,120,1)
        self.goto(*walk,radius=4);self.step(4);self.settle()
        self.check(self.proof().stage==3,f'optional source{index+1} requires genuine completed work and marked walk')
        self.invite(index);self.snapshot(f'source-{index+1:02d}-earned-form{form}')
    def optional_quests(self):
        self.travel(64);self.target(176,120)
        self.travel(69);self.target(48,104);self.target(80,104);self.target(40,80)
        self.travel(66);self.target(176,80)
        self.travel(65);self.target(352,272);self.target(352,272)
        self.travel(60);self.target(64,112);self.target(64,112)
        self.check(all(self.quest(q)==3 for q in range(60)),'all60 quests genuinely claimed through local work and return report')
        self.check(sum(bool(g.item_id) for g in self.state().equipment.bag)==46,'all46 gear entries genuinely retained')
        self.snapshot('05-all60-quests46-gear')
    def begin_horizons_trial(self,index):
        area,form,command,lectern=[(64,105,106,(32,48)),(67,107,108,(368,208)),(66,109,110,(48,72)),(68,111,112,(48,112))][index]
        self.travel(area)
        if any(e['hp']>0 for e in self.enemies()):self.clear_enemies()
        self.owned_select(form);self.set_command(command);self.ready()
        slot=self.roster().party[self.roster().selected_party];identity=self.selected().instance_id
        self.target(*lectern);p=self.proof()
        self.check(p.mode==3 and p.index==index and p.id==identity and p.slot==slot,'trial lectern binds exact genuine base individual')
        return identity,slot
    def solve_horizons_trial(self,index):
        if index==0:
            self.cast_at(105,106,64,88,1,prepare=False);self.cast_at(105,106,176,88,1,prepare=False)
        elif index==1:self.warm_at(300,208,prepare=False,manual=(300,232,0))
        elif index==2:
            self.cast_at(109,110,112,248,3,prepare=False);self.target(80,160)
        elif index==3:
            self.target(80,112);self.cast_at(111,112,48,88,3,prepare=False);self.cast_at(111,112,128,88,3,prepare=False)
        self.check(self.proof().stage==3,f'personal trial{index+41} actual power composition solved')
        walks=[((64,120),(120,112)),((400,240),(368,272)),((80,248),(64,288)),((112,112),(160,136))][index]
        for point in walks:self.goto(*point,radius=4);self.step(4);self.settle()
    def evolve_horizons(self,source,target,identity,slot):
        self.travel(62);self.target(72,256);self.owned_select(source)
        self.check(self.selected().instance_id==identity,'sanctuary selects exact trial-qualified individual')
        self.open_tab(3);self.tap('SELECT');self.wait_evolution(require_ready=False)
        before=self.state_signature();self.tap('B')
        self.check(self.get('game_state')==PAUSE and self.state_signature()==before,'cancel evolution preserves exact durable state')
        self.tap('SELECT');self.wait_evolution();self.check(self.get('progression_evolution_target')==target,'earned optional evolution previews correct form')
        self.tap('A');self.wait_evolution(8);self.settle();self.close_menu()
        c=self.roster().instances[slot]
        self.check(c.instance_id==identity and c.form_id==target,'optional evolution keeps original individual identity')
        self.acquisitions.append({'source':'same-instance optional evolution','from':source,'form':target,'instance_id':identity,'slot':slot,'frame':self.e.frame})
        self.snapshot(f'evolved-{source}-to-{target}')
    def collection_route(self):
        self.check(not self.minimal,'all120 producer starts from genuine H all104 history')
        for i in range(4,12):self.first_optional(i)
        self.optional_quests()
        for index,(source,target) in enumerate(((105,106),(107,108),(109,110),(111,112))):
            identity,slot=self.begin_horizons_trial(index);before=bytes(self.roster().instances[slot])
            if index==0:
                self.cast_at(105,106,64,24,0,prepare=False)
                self.check(self.proof().stage==0 and self.proof().hits==0 and bytes(self.roster().instances[slot])==before,'wrong-side genuine personal cast grants no proof floor or evolution')
                self.reset_horizons();identity,slot=self.begin_horizons_trial(index)
            self.solve_horizons_trial(index);c=self.roster().instances[slot]
            self.check(c.instance_id==identity and c.form_id==source and c.trial_flags&1024 and c.level>=34 and c.bond>=60,'genuine personal trial gives only bound predecessor its34/60 floor')
            self.evolve_horizons(source,target,identity,slot)
        self.check(len(self.collection())==120 and len(self.live())==64,'all120 forms recorded through genuine encounters and four optional evolutions;64 real individuals retained')
        self.check(self.old_ids<={c.instance_id for c in self.live()},'all52 prior exact H individuals retained')
        table=self.sym['creature_forms'];families={self.e.read(table+i*32,1):self.e.read(table+i*32+1,1) for i in range(120)}
        self.check(len(families)==120 and len({families[c.form_id] for c in self.live()})==52,'real retained individuals cover all52 compiled families')
        self.snapshot('06-all120-earned64-saved');self.cold_reboot('07-all120-cold-reboot')
    def repeat_route(self):
        before_count=len(self.live())
        for index,(area,base,command,invite,manual,target,walk) in enumerate(SOURCES):
            self.travel(area)
            if area==65:self.target(80,256)
            if any(e['hp']>0 for e in self.enemies()):self.clear_enemies()
            if area==65:self.target(80,256)
            self.owned_select(self.base_form(base) if index<4 else base);self.set_command(command);self.ready()
            count=len(self.live());before_quests=bytes(self.state().quests);before_gear=bytes(self.state().equipment)
            self.target(*invite);p=self.proof()
            self.check(p.mode==2 and p.index==index and p.stage==0,f'source{index+1} repeat requires freshly started local encounter')
            if index not in (7,10):self.target(*manual)
            x,y=target
            if index==0:self.cast_at(self.base_form(base),command,x+32,y,2,prepare=False)
            elif index==1:self.warm_at(x+12,y,prepare=False)
            elif index==2:self.cast_at(self.base_form(base),command,x-24,y,3,prepare=False)
            elif index==6:self.cast_at(base,command,x,y-24,1,prepare=False)
            elif index==7:
                self.cast_at(base,command,x,y+24,1,wait=10,prepare=False);self.target(*manual)
            elif index in (8,9):self.cast_at(base,command,196 if index==8 else 52,88 if index==8 else 180,1,prepare=False)
            else:self.cast_at(self.base_form(base) if index<4 else base,command,x,y+24,1,prepare=False)
            self.goto(*walk,radius=4);self.step(4);self.settle()
            self.check(self.proof().stage==3,f'repeat{index+1} requires actual signature geometry and fresh marked walk')
            self.target(*invite);self.tap('B');self.check(len(self.live())==count,'repeat invitation cancellation cannot grant')
            self.target(*invite);self.tap('A');self.settle()
            self.check(len(self.live())==count+1,f'genuine repeat encounter{index+1} admits one new individual')
            self.check(bytes(self.state().equipment)==before_gear,'repeat cannot grant gear')
            # Repeat receipt is allowed to change; quest states/objectives/rewards are not.
            self.check(bytes(self.state().quests.states)==before_quests[:16],'repeat does not grant any quest')
            self.target(*invite);self.check(self.proof().mode==2 and self.proof().stage==0 and len(self.live())==count+1,'reused invitation starts unsolved fresh encounter without duplicating reward')
            self.reset_horizons();self.snapshot(f'repeat-{index+1:02d}-earned')
        self.check(len(self.live())==before_count+12,'all twelve distinct repeats retain twelve real extra individuals')
        self.cold_reboot('all12-repeats-cold-reboot')
    def lifecycle(self):
        self.travel(62);self.target(72,256);self.cold_reboot('main-cold-save')
        identities=[(c.instance_id,c.form_id) for c in self.live()];history=self.collection()
        self.travel(69);self.target(208,112)
        self.check(self.proof().mode==1 and self.proof().index==8,'death test starts genuine unfinished optional work without recruiting')
        quests=bytes(self.state().quests)
        self.goto(120,112,radius=4)
        trace=[]
        for _ in range(1800):
            trace.append({'frame':self.e.frame,'hp':self.get('hp'),'state':self.get('game_state')})
            if self.get('game_state')==DEAD:break
            self.step(10)
        self.cases.append({'name':'ordinary-horizons-enemy-death','trace':trace})
        self.check(self.get('game_state')==DEAD,'genuine enemy damage reaches death without injected health')
        self.snapshot('native-horizons-death',settle=False);self.tap('A',2,30);self.settle()
        self.check(self.get('game_state')==PLAY and self.get('hp')>0,'ordinary A retry returns to live safe checkpoint')
        self.check([(c.instance_id,c.form_id) for c in self.live()]==identities and self.collection()==history,'death/retry retains every individual and history')
        self.check(bytes(self.state().quests)==quests and not self.proof().mode,'death/retry retains exact quests and revokes attempt rights')
        self.travel(62);self.target(72,256)
        for area in (61,60,0,16,22,30,38,46,62):self.travel(area)
        self.snapshot('native-old-regions-return')


    def controls(self):
        self.travel(62);self.owned_select(self.base_form(105));self.set_command(106);self.ready()
        self.target(352,224);self.target(352,256);self.goto(384,176,radius=4);self.face(2);self.ready()
        self.tap('R',1,1)
        p=self.proof_dict();age=self.get('horizons_power_age');cd=self.get('ability_cd')
        self.step(36,'L')
        self.check(self.proof_dict()==p and self.get('horizons_power_age')==age and self.get('ability_cd')==cd,'held L freezes exact proof cast age and shared cooldown')
        self.step(1);self.tap('START',1,1)
        self.check(self.get('game_state')==PAUSE,'journal opens during immutable live cast')
        p=self.proof_dict();age=self.get('horizons_power_age');cd=self.get('ability_cd')
        self.step(36)
        self.check(self.proof_dict()==p and self.get('horizons_power_age')==age and self.get('ability_cd')==cd,'journal viewing preserves proof and freezes cast/cooldown')
        self.tap('B',1,1);self.step(100)
        self.check(self.proof().mode==2 and self.proof().stage==2,'unchanged selected identity preserves repeat proof after viewed cast resolves')
        self.goto(384,208,radius=4);self.step(4)
        self.check(self.proof().stage==3,'viewed repeat remains solvable after ordinary walk')
        self.reset_horizons()
        self.target(352,224);self.target(352,256);self.goto(384,176,radius=4);self.face(2);self.ready();self.tap('R',1,1)
        oldid=self.selected().instance_id;cooldown=self.get('ability_cd');oldtime=self.get('horizons_power_time')
        current=self.roster().selected_party;other=next(i for i,v in enumerate(self.roster().party) if v<160 and i!=current)
        self.tap('L+'+('UP','RIGHT','DOWN','LEFT')[other],1,1)
        self.check(self.selected().instance_id!=oldid and not self.proof().mode,'actual party selection change revokes bound repeat proof')
        self.check(0<self.get('ability_cd')<=cooldown and 0<self.get('horizons_power_time')<=oldtime,'selection edit preserves live immutable cast and cooldown rather than refunding them')
        self.step(100);self.check(not self.proof().mode,'revoked cast cannot rebuild proof after resume')
        self.owned_select(106);self.set_command(106);self.ready();self.target(352,224);self.target(352,256)
        self.goto(384,176,radius=4);self.face(2);self.ready();self.tap('R',1,1);cooldown=self.get('ability_cd')
        self.set_command(107)
        self.check(not self.proof().mode and 0<self.get('ability_cd')<=cooldown,'actual command edit revokes source rights without cooldown refund')
        self.step(100)
        self.set_command(106);self.ready();self.target(352,224);self.target(352,256)
        self.goto(384,176,radius=4);self.face(2);self.ready();self.tap('R',1,1)
        identity=self.selected().instance_id;cooldown=self.get('ability_cd');selected_slot=self.roster().selected_party
        other_slot=next(i for i in range(4) if i!=selected_slot)
        self.assign(other_slot,113)
        self.check(self.selected().instance_id==identity and not self.proof().mode,'editing another party slot revokes proof even when selected individual stays identical')
        self.check(0<self.get('ability_cd')<=cooldown,'party assignment cannot refund the live cast cooldown')
        self.step(100);self.target(352,224);self.target(352,256);self.target(24,292,0)
        self.check(self.hz_local('reset_confirm',1)==1,'live-reset test previews the ordinary reset sign')
        self.ready();self.tap('R',1,1);cooldown=self.get('ability_cd');self.tap('A');self.settle()
        self.check(not self.proof().mode and 0<self.get('ability_cd')<=cooldown,'confirmed reset revokes the unfinished attempt without refunding its active cooldown')
        self.step(100);self.snapshot('controls-heldL-journal-and-edit')
        self.travel(68);self.owned_select(120);self.set_command(121);self.ready()
        # Same fan at several distances from the real northern wall. Each call
        # includes every startup, active, settle and cooldown hardware frame.
        for x,y,d in ((24,32,1),(120,48,1),(216,32,3),(80,88,1)):
            self.cast_at(120,121,x,y,d)
        self.travel(67);self.owned_select(self.base_form(107));self.set_command(108);self.ready()
        for x,y,d in ((40,48,0),(240,48,0),(448,160,1),(300,208,2)):
            self.goto(x,y,radius=4);self.face(d);self.ready();self.tap('R',1,12);self.tap('R',1,100);self.settle()
        self.snapshot('controls-wall-adjacent108-121')
        self.travel(63);self.cast_at(106,107,336,54,0)
        self.travel(67);self.owned_select(108);self.set_command(109);self.ready();self.goto(268,208,radius=4);self.face(3);self.ready();self.tap('R',1,12);self.tap('R',1,100);self.settle()
        self.travel(66);self.cast_at(110,111,132,256,3)
        self.travel(68);self.cast_at(112,113,64,94,3)
        self.snapshot('controls-four-evolved-signatures')
        self.old_wall_stress()

    def old_wall_stress(self):
        for area in (23,1,17,31,40,41,42,43,44,45,47,51,55,56):
            if area==40:self.travel(38);self.target(112,248)
            if area==47:self.travel(46);self.target(80,256)
            if area==55:self.travel(54);self.target(72,256)
            self.travel(area)
            if area in (23,31):self.target(80,248)
            if area==17:self.target(120,216)
            if area==47:self.target(64,256)
            if any(e['hp']>0 for e in self.enemies()):self.clear_enemies()
            blocked,w,h=self.mask();start=self.get('py')*w+self.get('px');reachable={start};queue=deque([start])
            while queue:
                cell=queue.popleft();cx,cy=cell%w,cell//w
                for n in (cell-1,cell+1,cell-w,cell+w):
                    if 0<=n<w*h and abs(n%w-cx)+abs(n//w-cy)==1 and not blocked[n] and n not in reachable:reachable.add(n);queue.append(n)
            points=[]
            for y in range(24,h-24,8):
                for x in range(24,w-24,8):
                    if y*w+x not in reachable:continue
                    if area in (42,44):
                        cell=self.puzzle()[0];charge=(48+(cell%7)*24,32+(cell//7)*18)
                        # A legacy heat-glyph interaction consumes R before
                        # signature dispatch. Keep performance probes outside
                        # that actual authored interaction neighborhood.
                        if abs(x-charge[0])+abs(y-charge[1])<48:continue
                    if area in (43,44) and abs(x-168)+abs(y-104)<48:continue
                    for direction,(dx,dy) in enumerate(((0,1),(0,-1),(-1,0),(1,0))):
                        if any(blocked[(y+dy*d)*w+x+dx*d] for d in (8,12,16)):
                            points.append((abs(x-self.get('px'))+abs(y-self.get('py')),x,y,direction));break
            chosen=[]
            for _,x,y,d in sorted(points):
                if all(abs(x-u)+abs(y-v)>40 for u,v,_ in chosen):chosen.append((x,y,d))
                if len(chosen)==3:break
            if area==23:chosen=[(408,192,0),(392,224,3),(440,208,2)]
            self.check(len(chosen)==3 and all(y*w+x in reachable for x,y,_ in chosen),f'old area{area} has three reachable actual narrow-obstruction approaches')
            for command,form in ((108,self.base_form(107)),(121,120)):
                for x,y,d in chosen:
                    self.owned_select(form);self.set_command(command);self.ready();self.goto(x,y,radius=4);self.face(d);self.ready()
                    self.check(self.get('room')==area,'old-wall probe remains in its controller-reached area')
                    self.step(1,'R');self.check(self.get('horizons_power_kind')==command and self.get('horizons_power_time')>0,'new signature genuinely starts beside an old-region obstruction')
                    origin=[self.get('horizons_power_origin_x'),self.get('horizons_power_origin_y')]
                    self.step(12)
                    if command==108:self.tap('R',1,110)
                    else:self.step(110)
                    self.settle()
                    self.cases.append({'old_field_wall_cast':command,'requested_origin':[x,y],'actual_cast_origin':origin,'direction':d,'room':area,'frame':self.e.frame})
            self.snapshot(f'controls-old-area{area:02d}-wall108-121')
        self.travel(62);self.target(72,256)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','symbols','output','source-manifest','source-root','producer-report'):p.add_argument('--'+key,type=Path,required=True)
    for key in ('expected-rom-sha','expected-symbols-sha','expected-elf-sha','expected-manifest-sha','expected-producer-sha','source-snapshot'):p.add_argument('--'+key,required=True)
    p.add_argument('--source-sram',type=Path)
    p.add_argument('--scope',choices=('migration','main','full','repeats','followup-repeats','lifecycle'),default='migration')
    p.add_argument('--arm-order',choices=('stage-first','water-first'),default='stage-first')
    p.add_argument('--timing-mode',choices=('strict','collect-diagnostic'),default='strict')
    a=p.parse_args()
    r=HorizonsJourney(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.expected_elf_sha,
        a.source_manifest,a.expected_manifest_sha,a.source_sram,a.source_root,a.timing_mode,a.producer_report,a.expected_producer_sha,a.source_snapshot)
    try:r.run(a.scope,a.arm_order)
    except Exception as exc:
        r.failures.append({'error':str(exc),'traceback':traceback.format_exc(),'status':r.status()})
        r.snapshot('failure',settle=False);raise
    finally:r.close_global_trace();r.report();r.e.close()
    return bool(r.failures)

if __name__=='__main__':raise SystemExit(main())
