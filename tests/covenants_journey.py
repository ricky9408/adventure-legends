#!/usr/bin/env python3
"""Genuine current-C SRAM -> Covenants controller-only native acceptance.

The original Horizons/H verifier remains unchanged. This explicit next-chapter
import contract authenticates exact accepted C producers rather than pretending
that C fixtures are H inputs or same-candidate saves. No game-memory writes,
machine state imports, injected completion, or synthetic collection credit.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import ctypes as C
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import struct
import traceback
from horizons_journey import HorizonsJourney, HorizonsEmulator, H_PRODUCERS, H_ROM, DOORS as H_DOORS
from return_journey import ReturnJourney, ReturnTrial, preserve_pinned_file
from magma_journey import MagmaJourney, elf_locals
from region_journey import ROOT, digest, PLAY, DIALOG, PAUSE, DEAD, SAVING
from northern_journey import newest_bank
from test_save5 import Save, Roster

C_ROM = '4166bdafdba0bf689a8230d6d8d407ae7faf0271925df480b4e3b0aa917f1a91'
C_ELF = 'c5648eb363bdcfaf2e9f553d003dd4ca2150f23bb8607d042470ae85ee19dc28'
C_SYM = 'e0cd163b6233c850c8c86711aeff39ce2c7f62de3cffab0e9fcf76ebea693d71'
C_MANIFEST = 'e4f99d30802a5e6a97f1d5c639ff3f3d8d59ddb2ad4a91d6c61b212b0ed91a54'
C_INPUTS = {
 'full': ('full','07-all120-cold-reboot-after','1d4e000918e7b77bd5f6e2585abff3e7e13c3c703eb4b50a14546e647d6cc45a','d0786e3db82cd23c5f9ba948900f3d73340de8df004738d26ad1c2956055994e',64,120),
 'minimal-stage': ('minimal-stage-lifecycle','main-cold-save-after','99d471bdbcfde387a6eba41a766daec3831b5af45dc086bc20d71b9c685a9adf','12e6177222cb8d319ca69cd37c2950934491618141c282f1e133d466a274ce77',18,18),
 'minimal-water': ('minimal-water','04-main-horizons-complete','f78d5b7cab0bace554106b0931a6da9debb3b739b373b82a0651747f38cd467d','04de7bfb3077f086bb9b05a26a7a1e68a5bab005cc4909e5b15a5760028975b6',18,18),
}

def authenticate_current_c(root, kind):
    root=Path(root);stage,snapshot,producer_sha,sram_sha,individuals,history=C_INPUTS[kind]
    provenance_path=root/'tests/fixtures/v5-revision8/provenance.json'
    provenance=json.loads(provenance_path.read_text())
    rows=[r for r in provenance['fixtures'] if r['stage']==stage and r['source_snapshot']==snapshot]
    assert len(rows)==1, 'Current C provenance row must resolve uniquely'
    row=rows[0];raw=gzip.decompress((root/row['producer_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==producer_sha==row['producer_raw_sha256']
    assert digest(root/row['path'])==sram_sha==row['sha256']
    assert (root/row['path']).stat().st_size==32768
    p=json.loads(raw)
    assert p['suite']=='horizons-native-controller-journey'
    assert p['rom_sha256']==C_ROM and p['elf_sha256']==C_ELF and p['symbols_sha256']==C_SYM
    assert p['source_manifest_sha256']==C_MANIFEST
    assert p['controller_only'] and not p['game_ram_writes'] and not p['machine_state_loads']
    assert not p['failures'] and all(c['passed'] for c in p['checks'])
    assert p['timing_mode']=='strict' and p['global_native']['closed'] and not p['global_native']['exceptions']
    ancestry=p['provenance']
    assert ancestry['source_rom_sha256']==H_ROM and not ancestry['same_candidate_source']
    assert ancestry['sram_sha256']==H_PRODUCERS[ancestry['producer_sha256']][ancestry['source_snapshot']]
    prior=p['snapshots'][snapshot]
    assert prior==row['snapshot'] and prior['sram_sha256']==sram_sha
    assert prior['sram_export']=='mCore.savedataClone'
    assert len(prior['individuals'])==individuals and len(prior['obtained_form_ids'])==history
    assert int.from_bytes(newest_bank((root/row['path']).read_bytes())[12:14],'little')==8
    return prior, {'contract':'accepted-C-native-to-current9-v1','fixture_kind':kind,'fixture_path':row['path'],
      'sram_sha256':sram_sha,'source_rom_sha256':C_ROM,'source_snapshot':snapshot,
      'producer_path':row['producer_path'],'producer_sha256':producer_sha,
      'minimal_prior_route':kind!='full','source_individuals':individuals,'source_history':history,
      'ordinary_cold_reload_observed_by_producer':row['ordinary_cold_reload_observed'],
      'cross_rom_machine_state_loaded':False,'provenance_sha256':digest(provenance_path),
      'verified_H_ancestry':ancestry}

class CovenantsJourney(HorizonsJourney):
    def __init__(self, rom, symbols, output, rom_sha, symbols_sha, elf_sha,
                 source_manifest, manifest_sha, fixture=None, source_root=None, timing_mode='strict', prior_root=None, fixture_kind="full", prelude_report=None, prelude_sha=None, prelude_snapshot=None, earned_report=None, earned_sha=None, earned_snapshot=None):
        self.source_rom, self.source_symbols = Path(rom).resolve(), Path(symbols).resolve()
        self.out = Path(output).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        assert not (self.out / 'covenants-journey.json').exists(), 'Use a fresh evidence directory; earlier reports are immutable'
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
        self.prior_root = Path(prior_root or ROOT).resolve()
        prior, contract = authenticate_current_c(self.prior_root, fixture_kind)
        self.fixture = self.prior_root / contract['fixture_path']
        self.source_revision=8
        self.completed_source=False
        if prelude_report is not None:
            prelude_report=Path(prelude_report).resolve()
            assert digest(prelude_report)==prelude_sha, 'Prelude report must be explicitly pinned'
            p=json.loads(prelude_report.read_text())
            assert p['suite']=='covenants-core-prelude' and p['finished_scope']=='core-ending'
            assert p['rom_sha256']==rom_sha and p['elf_sha256']==elf_sha and p['symbols_sha256']==symbols_sha
            assert p['source_manifest_sha256']==manifest_sha
            assert p['controller_only'] and not p['game_ram_writes'] and not p['machine_state_loads']
            assert p['timing_mode']=='strict' and not p['failures'] and all(c['passed'] for c in p['checks'])
            assert p['global_native']['closed'] and not p['global_native']['exceptions']
            assert p['provenance']==contract, 'Prelude must originate in this exact accepted C fixture'
            prior=p['snapshots'][prelude_snapshot]
            self.fixture=prelude_report.parent/Path(prior['sram_path']).name
            assert prior['sram_export']=='mCore.savedataClone' and digest(self.fixture)==prior['sram_sha256']
            assert len(prior['individuals'])==18 and len(prior['obtained_form_ids'])==18
            assert prior['status']['chapter_flags']&8 and prior['quests'][60:64]==[0]*4
            assert not prior['fulfilled'] and not prior['invitations']
            contract={**contract,'contract':'same-candidate-core-prelude-to-final-v1','accepted_C_ancestry':contract,
              'source_rom_sha256':rom_sha,'fixture_path':str(self.fixture),'sram_sha256':prior['sram_sha256'],
              'source_snapshot':prelude_snapshot,'source_individuals':len(prior['individuals']),'source_history':len(prior['obtained_form_ids']),
              'prelude_report':str(prelude_report),'prelude_sha256':prelude_sha,'prelude_snapshot':prelude_snapshot}
            self.source_revision=9
            shutil.copyfile(prelude_report,self.out/'source-core-prelude.json')
        if earned_report is not None:
            assert prelude_report is None, 'Choose one explicit native source contract'
            earned_report=Path(earned_report).resolve()
            assert digest(earned_report)==earned_sha, 'Earned report must be explicitly pinned'
            p=json.loads(earned_report.read_text())
            assert p['suite']=='covenants-native-controller-journey' and p['finished_scope']=='full'
            assert p['rom_sha256']==rom_sha and p['elf_sha256']==elf_sha and p['symbols_sha256']==symbols_sha
            assert p['source_manifest_sha256']==manifest_sha
            assert p['controller_only'] and not p['game_ram_writes'] and not p['machine_state_loads']
            assert p['timing_mode']=='strict' and not p['failures'] and all(c['passed'] for c in p['checks'])
            assert p['global_native']['closed'] and not p['global_native']['exceptions']
            ancestry=p['provenance'].get('accepted_C_ancestry',p['provenance'])
            assert ancestry==contract, 'Earned source must retain exact accepted C ancestry'
            prior=p['snapshots'][earned_snapshot]
            self.fixture=earned_report.parent/Path(prior['sram_path']).name
            assert prior['sram_export']=='mCore.savedataClone' and digest(self.fixture)==prior['sram_sha256']
            assert prior['quests'][60:64]==[3]*4 and prior['fulfilled']==255
            assert (len(prior['individuals']),len(prior['obtained_form_ids']),prior['invitations'])==((18,18,0) if contract['minimal_prior_route'] else (72,128,255))
            contract={**contract,'contract':'same-candidate-completed-final-followup-v1','accepted_C_ancestry':contract,
              'source_rom_sha256':rom_sha,'fixture_path':str(self.fixture),'sram_sha256':prior['sram_sha256'],
              'source_snapshot':earned_snapshot,'source_individuals':len(prior['individuals']),'source_history':len(prior['obtained_form_ids']),
              'earned_report':str(earned_report),'earned_sha256':earned_sha,'earned_snapshot':earned_snapshot}
            self.source_revision=9;self.completed_source=True
            shutil.copyfile(earned_report,self.out/'source-final-producer.json')
        if fixture is not None:
            assert digest(fixture) == contract['sram_sha256']
            self.fixture = Path(fixture).resolve()
        self.minimal = contract['minimal_prior_route']
        self.prior_count, self.prior_history = len(prior['individuals']), len(prior['obtained_form_ids'])
        self.source_bytes = self.fixture.read_bytes()
        self.source_bank = newest_bank(self.source_bytes)
        assert int.from_bytes(self.source_bank[12:14], 'little') == self.source_revision
        shutil.copyfile(self.fixture, self.out / 'source-earned.sav')
        self.provenance = contract
        report_raw = gzip.decompress((self.prior_root / contract['producer_path']).read_bytes())
        (self.out / 'source-producer.json').write_bytes(report_raw)
        (self.out / 'current-c-import-contract.json').write_text(json.dumps(contract, indent=2)+'\n')
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
        self.covenants_geometry = json.loads((self.out / 'helper-source/assets/covenants_world/geometry.json').read_text())
        self.cv_rooms = {r['id']: r for r in self.covenants_geometry['rooms']}
        assert C.sizeof(ReturnTrial) == 28
        self.report()

    def freeze_helpers(self):
        hashes=HorizonsJourney.freeze_helpers(self)
        for name in ('assets/covenants_world/geometry.json',):
            src=ROOT/name;dst=self.out/'helper-source'/name
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);hashes[name]=digest(dst)
        (self.out/'helper-source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
        return hashes

    def report(self):
        data={'suite':'covenants-native-controller-journey','development_diagnostic':True,'release_acceptance':False,
            'finished_scope':self.finished_scope,'timing_mode':self.timing_mode,'controller_only':True,
            'game_ram_writes':0,'machine_state_loads':0,'physical_handheld_tested':False,'player_facing':False,
            **self.candidate,'provenance':self.provenance,'source_manifest_sha256':self.source_manifest_sha,
            'source_root':str(self.source_root),'helper_sources':getattr(self,'test_sources',{}),
            'checks':self.checks,'failures':self.failures,'snapshots':self.snapshots,'inputs':self.inputs,
            'transitions':self.transitions,'cases':self.cases,'acquisitions':self.acquisitions,
            'coverage':self.coverage,'frame_windows':self.frame_windows,'global_native':self.global_native,
            'main_route_selected_forms':sorted(set(self.main_selections)),
            'scope_limits':['No physical GBA test','Failed candidates remain immutable','Imported collection is prior earned history, never new acquisition']}
        (self.out/'covenants-journey.json').write_text(json.dumps(data,indent=2)+'\n')

    def cv_local(self,name,width=None):return self.local(name,width,file='covenants_game.c')
    def cv_setting(self):
        address,size=self.locals['covenants_game.c:setting'];assert size==24
        return list(self.e.bytes(address,size))
    def fulfilled(self,i):return bool(self.state().quests.region_flags[22]&(1<<i))
    def invited(self,i):return bool(self.state().quests.region_flags[23]&(1<<i))
    def snapshot(self,name,settle=True):
        assert name not in self.snapshots,'Snapshot names are immutable'
        if settle:self.settle();self.step(3);self.settle()
        save,shot=self.out/(name+'.sav'),self.out/(name+'.png')
        self.e.save(save);self.e.screenshot(shot)
        self.check(digest(self.fixture)==self.provenance['sram_sha256'],'source C SRAM remains exact after native export')
        self.check(save.stat().st_size==32768,'normal savedataClone exports32768 bytes')
        self.check(save.read_bytes()==self.e.bytes(0x0e000000,32768),'normal savedataClone matches cartridge SRAM')
        s=self.state()
        self.snapshots[name]={'rom_sha256':self.target_sha,'symbols_sha256':self.symbol_sha,'elf_sha256':self.candidate['elf_sha256'],
          'sram_path':str(save),'sram_sha256':digest(save),'sram_export':'mCore.savedataClone','screenshot':str(shot),
          'status':self.status(),'quests':[self.quest(q) for q in range(64)],'obtained_form_ids':self.collection(),
          'individuals':[{'slot':i,'form':c.form_id,'instance_id':c.instance_id,'trial_flags':c.trial_flags,'level':c.level,'bond':c.bond} for i,c in enumerate(s.roster.instances) if c.flags&1],
          'gear_items':[g.item_id for g in s.equipment.bag if g.item_id],'party':list(s.roster.party),
          'equipped':list(s.equipment.equipped),'objectives':list(s.quests.objectives)[60:64],
          'fulfilled':s.quests.region_flags[22],'invitations':s.quests.region_flags[23],
          'setting':self.cv_setting(),'moving_x':self.cv_local('moving_x'),'npc_xy':[self.cv_local('npc_x'),self.cv_local('npc_y')],
          'npc_stage':self.cv_local('npc_stage'),'attempt':self.cv_local('attempt'),'scene':self.cv_local('scene')}
        self.snapshots[name]['legendary_power']={n:self.get('covenants_power_'+n) for n in ('kind','time','form','age','direction','origin_x','origin_y','cast_time','cooldown')}
        if self.get('covenants_power_time'):
            address,size=self.locals['covenants_powers.c:cast']
            self.snapshots[name]['legendary_power_cast_bytes_hex']=self.e.bytes(address,size).hex()
        self.report();print(name,self.status(),'quests',[self.quest(q) for q in range(60,64)],'fulfilled',s.quests.region_flags[22],flush=True)
        return name

    def boot(self):
        self.step(150)
        self.measured('bounded-cold-currentC-continue',lambda:(self.tap('START',2,90),self.settle()),cold_continue=True)
        bank=newest_bank(self.e.bytes(0x0e000000,32768))
        self.check(self.get('game_state')==PLAY,'accepted C SRAM resumes by ordinary Continue')
        self.check(int.from_bytes(bank[12:14],'little')==9,'ordinary Continue commits current content9')
        self.check(bank[32:]==self.source_bank[32:],'C import preserves every durable payload byte before new actions')
        offset=self.source_bytes.index(self.source_bank)
        self.check(self.e.bytes(0x0e000000+offset,len(self.source_bank))==self.source_bank,'import preserves prior committed C bank exactly')
        self.check(len(self.live())==self.prior_count and len(self.collection())==self.prior_history,'migration creates no individual or history')
        if not self.completed_source:
            self.check(all(not self.quest(q) and not self.state().quests.objectives[q] for q in range(60,64)),'migration creates no final quest or objective')
            self.check(not any(self.state().quests.region_flags[x] for x in (7,22,23)) and not self.state().quests.anchors[7],'migration creates no visit, fulfilled right, invite or anchor')
        else:self.check([self.quest(q) for q in range(60,64)]==[3]*4 and self.state().quests.region_flags[22]==255,'same-candidate followup retains completed final story')
        self.old_ids={c.instance_id for c in self.live()};self.old_history=self.collection();self.old_equipped=bytes(self.state().equipment.equipped)
        self.old_party=bytes(self.roster().party);self.old_roster=bytes(self.roster());self.old_gear=bytes(self.state().equipment)
        if self.minimal:self.check([self.state().equipment.bag[i].item_id if i<48 else 0 for i in self.state().equipment.equipped]==[1,0,0,0,0],'minimal starts with starter weapon and empty remaining slots')
        self.snapshot('00-currentC-exact-import')

    def mask(self):
        room=self.get('room')
        if room<70:return HorizonsJourney.mask(self)
        desc=self.cv_rooms[room];w,h=desc['width'],desc['height']
        b=bytearray(int(x<5 or y<5 or x>w-6 or y>h-6) for y in range(h) for x in range(w))
        rects=[r['rect'] for r in desc['solids']]
        x=self.cv_local('moving_x')
        if room in (71,73,76):rects.append((x,{71:104,73:96,76:48}[room],16 if room==73 else 24,16 if room==71 else 12))
        for x,y,rw,rh in rects:
            lo,hi=max(0,x-5),min(w,x+rw+5)
            for yy in range(max(0,y-5),min(h,y+rh+5)):b[yy*w+lo:yy*w+hi]=b'\1'*(hi-lo)
        if self.cv_local('practice_ticks'):
            x,y,rw,rh=desc['practice']['shortcut_center_strip']
            for yy in range(y,y+rh):b[yy*w+x:yy*w+x+rw]=b'\0'*rw
        return b,w,h

    def entry(self,target):
        here=self.get('room')
        if (here,target)==(62,70):self.target(416,16,1)
        elif here>=70:
            portal=next(p for p in self.cv_rooms[here]['portals'] if p['to']==target)
            x,y=portal['center'];w,h=self.cv_rooms[here]['width'],self.cv_rooms[here]['height']
            face=2 if x<=16 else 3 if x>=w-16 else 1 if y<=16 else 0
            self.target(x,y,face)
        else:return HorizonsJourney.entry(self,target)
        self.check(self.get('room')==target,f'ordinary final chapter door {here} reaches{target}')

    def travel(self,target,clear=False):
        here=self.get('room')
        if here<70 and target<70:return HorizonsJourney.travel(self,target,clear)
        if here<70:self.travel(62);self.entry(70)
        if target<70:self.travel(70);self.entry(62);return self.travel(target)
        graph={r:[p['to'] for p in row['portals'] if p['to']>=70] for r,row in self.cv_rooms.items()}
        queue,seen=deque([(self.get('room'),[])]),{self.get('room')}
        while queue:
            here,path=queue.popleft()
            if here==target:
                for to in path:self.entry(to)
                return
            for to in graph[here]:
                if to not in seen:seen.add(to);queue.append((to,path+[to]))
        raise AssertionError(('no final chapter route',target))

    def wait_for(self,predicate,label,limit=1200,settle=True):
        for _ in range(limit):
            if predicate():
                if settle:self.settle()
                self.check(True,label);return
            self.step(1)
        self.check(False,label)

    def station_origin(self,x,y,direction):
        # One-frame final approach avoids the legacy helper's two-frame Q8
        # oscillation and the extra face-step overshooting a small target.
        dx,dy={0:(0,1),1:(0,-1),2:(-1,0),3:(1,0)}[direction]
        self.goto(x-dx*8,y-dy*8,radius=4)
        axes=(('px',x,'LEFT','RIGHT'),('py',y,'UP','DOWN')) if dy else (('py',y,'UP','DOWN'),('px',x,'LEFT','RIGHT'))
        for name,target,low,high in axes:
            for _ in range(60):
                if abs(self.get(name)-target)<=1:break
                self.step(1,low if self.get(name)>target else high)
            else:self.check(False,'authored station origin is reachable through one-frame controller steps')
        self.step(1)
        self.check(abs(self.get('px')-x)+abs(self.get('py')-y)<=2 and self.get('face')==direction,'cast begins at authored station with its ordinary facing')

    def station(self,index):
        room=self.get('room');station=self.cv_rooms[room]['stations'][index];command=station['command']
        form=self.base_form({102:101,104:103,106:105,108:107,110:109,112:111}[command])
        self.owned_select(form);self.set_command(command);self.ready()
        x,y=station['approach'];direction=station['face']
        self.station_origin(x,y,direction);self.ready()
        before={'room':room,'station':station['key'],'command':command,'form':self.selected().form_id,
                'id':self.selected().instance_id,'origin':[self.get('px'),self.get('py')],'setting':self.cv_setting()}
        self.step(1,'R')
        self.step(station['release_age'] or 100)
        if station['release_age']:self.step(1,'R');self.step(100)
        self.settle()
        self.cases.append({'station_cast':before,'setting_after':self.cv_setting(),'frame':self.e.frame})
        self.check(bool(self.cv_setting()[0]&(1<<index)),f'actual cast settles {station["key"]}')

    def invitation(self,i,accept=True):
        self.check(self.fulfilled(i),f'covenant{i+1} fulfilled before invitation')
        self.travel(70+i);x,y=self.cv_rooms[70+i]['invitation'];before=len(self.live());history=self.collection()
        self.target(x,y,1)
        self.check(self.cv_local('invite_confirm')==i+1,'first invitation dialogue asks; it grants nothing')
        self.check(len(self.live())==before and self.collection()==history,'invitation preview creates no entity or history')
        if not accept:
            self.tap('B');self.settle();self.check(not self.cv_local('invite_confirm') and not self.invited(i),'B deliberately declines invitation while fulfilled right remains')
        else:
            self.tap('A')
            if getattr(self,'lifecycle_mode',False):
                self.wait_for(lambda:self.get('game_state')==SAVING,'unique invitation reaches real incremental SRAM save',limit=900,settle=False)
                self.snapshot(f'lifecycle-invitation-{i+1}-interrupted',settle=False)
                self.snapshots[f'lifecycle-invitation-{i+1}-interrupted']['interrupted_save']=True
                self.snapshots[f'lifecycle-invitation-{i+1}-interrupted']['live_state_may_differ_from_committed_SRAM']=True
                self.report()
                save=self.snapshots[f'lifecycle-invitation-{i+1}-interrupted']['sram_path']
                self.e.close();self.e=HorizonsEmulator(self.rom);self.e.load_save(save);self.e.reset();self.step(150)
                self.measured(f'invitation-{i+1}-power-loss-bounded-continue',lambda:(self.tap('START',2,90),self.settle()),cold_continue=True)
                self.check(len(self.live())==before and self.collection()==history and not self.invited(i) and self.fulfilled(i),'early interrupted invitation restores prior committed bank and retains fulfilled retry right')
                self.target(x,y,1);self.check(self.cv_local('invite_confirm')==i+1,'power-loss invitation reopens for deliberate retry')
                self.tap('A')
            self.settle()
            self.check(self.invited(i) and len(self.live())==before+1,f'unique invitation{i+1} acquires exactly one individual')
            rows=[c for c in self.live() if c.form_id==121+i]
            self.check(len(rows)==1 and rows[0].instance_id not in self.old_ids,'unique legendary receives a fresh real identity')
            self.acquisitions.append({'form':121+i,'instance_id':rows[0].instance_id,'frame':self.e.frame})
            signature=self.state_signature();self.target(x,y,1);self.tap('A');self.settle()
            self.check(self.state_signature()==signature,'repeated claimed invitation cannot grant duplicate or change durable state')

    def initialize_covenants(self):
        self.travel(0);self.target(120,94,1)
        self.check(self.quest(60)==1 and self.state().quests.objectives[60]==1,'home conversation begins final journey')
        self.travel(62);self.target(120,208,1)
        self.check(self.state().quests.objectives[60]==3,'completed fair conversation delivers invitation letter')
        self.travel(70);self.target(128,272,1);self.target(64,136,1);self.target(144,264,1)
        self.check(self.quest(60)==2,'hearing neighbors and inspecting work readies welcome quest')
        self.target(128,272,1);self.check(self.quest(60)==3,'welcome report claims q60 without a legendary')
        self.target(128,272,1);self.check(self.quest(61)==1,'steward offers lower circuit')
        self.snapshot('01-final-chapter-welcome')

    def solve70(self):
        self.travel(70)
        for i in range(5):self.station(i)
        self.target(144,264,1);self.target(144,264,1);self.target(352,176,1)
        self.target(144,240,1);self.target(336,272,1)
        self.wait_for(lambda:self.fulfilled(0),'five settled tools and both observations fulfill Siltwake')
        self.snapshot('02-siltwake-fulfilled')

    def solve71(self):
        self.travel(71);self.station(0);self.target(120,232,1)
        self.wait_for(lambda:self.cv_local('moving_state')==0,'orchard arbor reaches stationary position')
        self.check(self.cv_local('moving_x')==120,'manual arbor moves to middle position')
        self.station(1);self.target(96,192,1);self.target(160,192,1);self.target(160,232,1)
        self.goto(190,250,radius=2)
        self.wait_for(lambda:self.fulfilled(1),'grower walks through inspected orchard with player nearby')
        self.snapshot('03-orchard-fulfilled')

    def commit_current_selection(self):
        # Quick selection is transient until an ordinary save action. Reapply
        # the unchanged weapon through the real menu, after live effects expire.
        self.wait_for(lambda:not any(self.get(n) for n in ('horizons_power_time','return_power_time','covenants_power_time')),'live effects expire before ordinary equipment save',limit=400)
        ref=self.state().equipment.equipped[0]
        self.check(ref<48,'normal saved party has a valid owned weapon reference')
        before=bytes(self.state().equipment);self.equip_item(0,self.state().equipment.bag[ref].item_id)
        self.check(bytes(self.state().equipment)==before,'ordinary unchanged-equipment save preserves all gear bytes')

    def cold_reboot(self,name):
        self.settle();before=self.state_signature();self.snapshot(name+'-before');saved=self.snapshots[name+'-before']
        self.e.close();self.e=HorizonsEmulator(self.rom);self.e.load_save(saved['sram_path']);self.e.reset();self.step(150)
        self.measured(name+'-bounded-cold-continue',lambda:(self.tap('START',2,90),self.settle()),cold_continue=True)
        self.check(self.state_signature()==before,'ordinary SRAM cold reload preserves exact roster quests and equipment')
        self.check(not self.cv_local('invite_confirm') and not self.cv_local('practice_mode'),'cold load clears invitation and practice transients')
        self.snapshot(name+'-after')

    def follow_resident(self,predicate,label,limit=400):
        trace=[];previous=None;stalled=0
        for _ in range(limit):
            if predicate():self.settle();self.check(True,label);self.cases.append({'resident_walk':label,'trace':trace});return
            nx,ny=self.cv_local('npc_x'),self.cv_local('npc_y')
            x,y=self.get('px'),self.get('py');b,w,h=self.mask()
            candidates=[(abs(px-x)+abs(py-y),px,py) for px,py in ((nx,ny+22),(nx,ny-22),(nx-22,ny),(nx+22,ny)) if 5<=px<w-5 and 5<=py<h-5 and not b[py*w+px]]
            self.check(bool(candidates),'resident route has a clear nearby following position')
            stalled=stalled+1 if previous==(nx,ny) else 0;previous=(nx,ny)
            candidates.sort();_,px,py=candidates[(stalled//5)%len(candidates)] if stalled>=5 else candidates[0]
            if abs(x-nx)+abs(y-ny)>30 or stalled>=5:self.goto(px,py,radius=5)
            self.step(12);self.settle()
            trace.append({'frame':self.e.frame,'npc':[nx,ny],'hero':[self.get('px'),self.get('py')],'stage':self.cv_local('npc_stage'),'escort_stage':self.cv_local('escort_stage')})
        self.cases.append({'resident_walk':label,'trace':trace});self.check(False,label)

    def solve72(self):
        self.travel(72);self.target(336,104,1);self.station(0);self.station(1)
        self.wait_for(lambda:self.cv_local('movement_ticks')>=72,'open kiln visibly cools for72 active frames')
        for x in (144,272,384):self.target(x,104,1)
        self.wait_for(lambda:self.fulfilled(2),'three cooled bowls fulfill Open Kiln')
        self.snapshot('04-kiln-fulfilled')

    def solve73(self):
        self.travel(73);self.station(0);self.station(1);self.target(64,128,1)
        self.follow_resident(lambda:self.fulfilled(3),'walking beside resident with still pauses fulfills Two-Foot Span')
        self.snapshot('05-span-fulfilled')

    def solve74(self):
        self.travel(74);self.station(0)
        self.target(120,240,1);self.target(240,136,1);self.station(1)
        for x,y,f in ((120,216,1),(360,240,1),(240,168,0)):self.target(x,y,f)
        self.wait_for(lambda:self.fulfilled(4),'two acoustic screens protect alcoves while center stays open')
        self.snapshot('07-hollowbell-fulfilled')

    def solve75(self):
        self.travel(75);self.station(0);self.target(192,232,1);self.station(1)
        self.target(160,208,1)
        self.follow_resident(lambda:self.fulfilled(5),'seed keeper crosses both shaded beds with walking gap intact')
        self.snapshot('08-shade-fulfilled')

    def solve76(self):
        self.travel(76);self.station(0);self.target(112,128,1)
        self.follow_resident(lambda:self.cv_local('npc_stage')==3,'passenger walks to stationary ferry and explicitly boards')
        self.station(1)
        self.wait_for(lambda:self.cv_local('moving_x')==272 and not self.cv_local('moving_state'),'ferry moves without carrying the player')
        self.station(2);self.target(384,120,1)
        self.step(700)
        self.check(self.cv_local('npc_stage')==5 and not self.fulfilled(6),'passenger safely waits for player occupying destination')
        self.goto(424,144)
        self.wait_for(lambda:self.fulfilled(6),'passenger disembarks at cleared far signal',limit=2200)
        self.snapshot('09-ferry-fulfilled')

    def clear_enemies(self):
        MagmaJourney.clear_enemies(self)
        self.check(self.get('game_state')==PLAY and self.hp_q4()>0,'wave victory requires a living hero; death cleanup is never counted as clearing enemies')

    def recover_between_waves(self):
        self.check(self.get('game_state')==PLAY and not any(e['hp']>0 for e in self.enemies()),'ordinary recovery begins alive between consented waves')
        self.check(self.selected().form_id==4 and self.command()==2,'minimal recovery uses guaranteed base Midori healing')
        before=self.hp_q4();casts=0
        # Move out of the old firing lane under an ordinary downward roll.
        shots=lambda:any(self.e.read(self.sym['shots']+i*24+16)>0 and self.e.read(self.sym['shots']+i*24+20)>0 for i in range(12))
        if shots():
            self.tap('SELECT+DOWN',1,12);self.goto(208,144)
            for _ in range(180):
                self.check(self.get('game_state')==PLAY,'retreat from remaining ordinary projectiles stays alive')
                if not shots():break
                self.step(1)
            self.check(not shots(),'remaining finite wave projectiles expire before next consent')
        for _ in range(2200):
            self.check(self.get('game_state')==PLAY,'ordinary between-wave healing stays alive')
            if self.hp_q4()>=self.stats()['max_hp']:break
            if not self.get('heal_cd') and not self.get('ability_cd'):
                old=self.hp_q4();self.tap('R',1,2);casts+=1
                self.check(self.hp_q4()>old,'actual Midori cast restores ordinary health')
            else:self.step(1)
        self.check(self.hp_q4()==self.stats()['max_hp'],'ordinary Midori healing restores full health before the next wave')
        self.cases.append({'name':'ordinary-between-wave-recovery','before_hp_q4':before,'after_hp_q4':self.hp_q4(),'healing_casts':casts,'companion_form':4,'weapon_item':1,'frame':self.e.frame})

    def solve77(self):
        self.travel(77);self.target(120,120,0)
        for i in range(3):self.station(i)
        if self.minimal:self.owned_select(4);self.set_command(2);self.ready()
        for wave in range(1,4):
            if self.minimal:self.recover_between_waves()
            self.target(120,120,0)
            self.check(self.cv_setting()[4]==wave,f'deliberate consent starts finite defense wave{wave}')
            self.clear_enemies()
        if self.minimal:self.recover_between_waves()
        self.target(120,120,0);self.wait_for(lambda:self.fulfilled(7),'three ordinary defense waves fulfill Last Watch')
        self.snapshot('10-lastwatch-fulfilled')

    def complete_story(self):
        self.travel(74);self.target(136,264,1);self.check(self.quest(62)==3,'upper circuit report claims q62')
        self.travel(70);self.target(128,272,1);self.check(self.quest(63)==1,'steward offers shared porch homecoming')
        self.target(128,272,1);self.check(self.cv_local('porch_confirm')==1,'porch commitment requires second deliberate A')
        self.tap('A');self.settle();self.check(self.state().quests.objectives[63]&1,'porch commitment recorded explicitly')
        self.travel(62)
        if self.get('summoned'):self.tap('B');self.settle()
        self.target(self.cv_local('npc_x'),self.cv_local('npc_y'),0)
        self.follow_resident(lambda:bool(self.state().quests.objectives[63]&2),'return companion walks ordinary fairground path home',limit=1200)
        self.travel(0);self.target(120,94,1);self.target(120,94,1)
        self.check(self.quest(63)==3,'homecoming report claims final quest and ending')
        self.step(8);self.settle();self.snapshot('11-final-ending')

    def local_reset(self,label):
        room=self.get('room');before=self.state_signature();point=self.cv_rooms[room]['reset']
        self.target(*point,face=0)
        self.check(self.cv_local('reset_confirm')==1,label+' reset sign requires second A')
        self.tap('B');self.settle();self.check(self.state_signature()==before,label+' canceled reset preserves durable state')
        self.target(*point,face=0);self.tap('A');self.settle()
        self.check(self.state_signature()==before,label+' confirmed reset preserves durable state')
        self.check(not any(self.cv_setting()[:5]),label+' confirmed reset clears incomplete ordinary work')

    def interrupt_local_work(self,i):
        self.travel(70+i)
        def partial():
            if i==2:self.target(336,104,1)
            if i==7:self.target(120,120,0)
            self.station(0)
        partial();self.local_reset(f'room{70+i}')
        partial();before=([self.quest(q) for q in range(60,64)],list(self.state().quests.objectives)[60:64],list(self.state().quests.region_flags)[22:24])
        other=next(p['to'] for p in self.cv_rooms[70+i]['portals'] if p['to']>=70 and (p['to']<74 or self.quest(61)==3))
        self.entry(other);self.entry(70+i)
        self.check(not any(self.cv_setting()[:5]),f'room{70+i} exit clears incomplete physical arrangement')
        self.check(([self.quest(q) for q in range(60,64)],list(self.state().quests.objectives)[60:64],list(self.state().quests.region_flags)[22:24])==before,f'room{70+i} exit preserves final progress while recording only its legitimate visit')
        partial();self.commit_current_selection();self.cold_reboot(f'lifecycle-room{70+i}-partial')
        self.check(not any(self.cv_setting()[:5]) and not self.fulfilled(i),f'room{70+i} ordinary cold load discards partial work and no right appears')
        self.coverage.append(f'room{70+i}-partial-reset-exit-cold')

    def death_recovery77(self):
        self.target(120,120,0)
        for i in range(3):self.station(i)
        self.target(120,120,0);self.check(self.cv_setting()[4]==1,'death control explicitly begins first finite wave')
        if self.get('summoned'):self.tap('B');self.settle()
        before=self.state_signature()
        for _ in range(8000):
            if self.get('game_state')==DEAD:break
            self.step(1)
        self.check(self.get('game_state')==DEAD,'ordinary wave contact causes genuine player death without health writes')
        self.tap('A');self.settle()
        self.check(self.get('game_state')==PLAY and self.get('room')==77,'ordinary death acknowledgement restores final-room checkpoint')
        self.check(not any(self.cv_setting()[:5]) and not self.fulfilled(7),'death removes incomplete defense waves and transient work')
        self.check(self.state_signature()==before,'death preserves exact roster quests and gear')
        self.snapshot('lifecycle-final-defense-death-recovery')

    def full_route(self,arm_order):
        self.main_only=self.minimal;self.initialize_covenants()
        lower=(0,1,2,3) if arm_order=='forward' else (3,2,1,0)
        upper=(4,5,6,7) if arm_order=='forward' else (7,6,5,4)
        for i in lower:
            if getattr(self,'lifecycle_mode',False):self.interrupt_local_work(i)
            getattr(self,'solve'+str(70+i))();self.invitation(i,accept=not self.minimal)
        self.travel(70);self.target(128,272,1);self.check(self.quest(61)==3,'lower circuit report claims q61')
        self.travel(74);self.target(136,264,1);self.check(self.quest(62)==1,'repairer offers upper circuit')
        self.snapshot('06-lower-circuit-report')
        for i in upper:
            if getattr(self,'lifecycle_mode',False):self.interrupt_local_work(i)
            if i==7 and getattr(self,'lifecycle_mode',False):self.death_recovery77()
            getattr(self,'solve'+str(70+i))();self.invitation(i,accept=not self.minimal)
        self.complete_story();self.main_only=False
        self.check(self.old_ids<={c.instance_id for c in self.live()},'every imported individual identity survives final story')
        self.check(set(self.old_history)<=set(self.collection()),'every imported obtained form survives final story')
        if self.minimal:
            self.check(len(self.live())==18 and self.collection()==self.old_history,'minimal story and return complete with all8 invitations declined')
            self.check(bytes(self.state().equipment.equipped)==self.old_equipped,'minimal ending retains starter gear equipment')
            self.check(set(self.main_selections)<=set(self.old_history),'minimal route uses guaranteed earned prior forms only')
            self.check(self.state().quests.region_flags[22]==255 and self.state().quests.region_flags[23]==0,'all8 fulfilled rights retained independently of acquisition')
        else:
            self.check(len(self.live())==72 and self.collection()==list(range(1,129)),'all128 recorded forms and72 real individuals earned through unique invitations')
            self.check([self.quest(q) for q in range(64)]==[3]*64 and sum(bool(g.item_id) for g in self.state().equipment.bag)==48,'all64 quests and48 gear items are genuine')
            table=self.sym['creature_forms'];families={self.e.read(table+i*32,1):self.e.read(table+i*32+1,1) for i in range(128)}
            self.check(len(families)==128 and len({families[c.form_id] for c in self.live()})==60,'all60 families remain represented by actual individuals')
        self.cold_reboot('12-final-cold')
        self.coverage.append(('minimal-declined-' if self.minimal else 'full-all128-')+arm_order)

    def cv_cast_bytes(self):
        a,n=self.locals['covenants_game.c:cast'];return self.e.bytes(a,n)

    def prepare_practice(self,i):
        self.travel(70+i);self.owned_select(121+i)
        practice=self.cv_rooms[70+i]['practice'];self.set_command(practice['command']);self.ready()
        self.target(*self.cv_rooms[70+i]['manual'][0],face=0 if i==7 else 1)
        self.check(self.cv_local('practice_mode')==1,'fulfilled local work opens optional owned-signature practice')
        self.goto(*practice['start_xy']);self.face(practice['face']);self.ready()
        return practice

    def practice_route(self):
        for i in range(8):
            practice=self.prepare_practice(i);before=self.state_signature();history=self.collection();ids={c.instance_id for c in self.live()}
            self.step(1,'R');self.check(self.get('covenants_power_kind')==practice['command'] and self.get('covenants_power_time')>0,'owned legendary begins its exact real signature')
            self.cases.append({'legendary_practice':121+i,'frame':self.e.frame,'origin':[self.get('covenants_power_origin_x'),self.get('covenants_power_origin_y')],'face':self.get('covenants_power_direction'),'command':practice['command']})
            if i==0:self.step(36);self.step(1,'R')
            self.wait_for(lambda:self.cv_local('practice_ticks')>0,f'command{practice["command"]} completes its own optional field practice',limit=180)
            self.check(self.state_signature()==before and self.collection()==history and {c.instance_id for c in self.live()}==ids,'optional field benefit changes no durable quest, roster, gear or identity')
            endpoints=practice['shortcut_endpoints']
            if endpoints:
                self.goto(*endpoints[0]);strip=practice['shortcut_center_strip'];x,y,w,h=strip
                self.goto(x+w//2,y+h//2)
                self.step(370)
                self.check(self.cv_local('practice_ticks')==1,'temporary path waits to close while player occupies it')
                self.goto(*endpoints[-1]);self.step(30)
                dx=endpoints[-1][0]-endpoints[0][0];dy=endpoints[-1][1]-endpoints[0][1]
                self.goto(endpoints[-1][0]+(16 if dx>0 else -16 if dx<0 else 0),endpoints[-1][1]+(16 if dy>0 else -16 if dy<0 else 0));self.step(30)
                if self.cv_local('practice_ticks') and self.get('summoned'):
                    self.check(self.cv_local('practice_ticks')==1,'path also waits for trailing companion occupancy')
                    self.tap('B');self.settle();self.step(2)
                self.check(not self.cv_local('practice_ticks'),'temporary path closes after player and companion clear it')
            self.snapshot(f'practice-{121+i}-real-field')
        self.commit_current_selection();self.cold_reboot('practice-all8-cold')

    def late_invitations(self):
        self.check(self.completed_source and self.minimal,'late invitations start from completed genuine all-declined minimal route')
        history=self.collection();count=len(self.live())
        for i in range(8):self.invitation(i,True)
        self.check(len(self.live())==count+8 and self.collection()==sorted(history+list(range(121,129))),'all8 declined invitations acquired later without replaying fulfilled covenants')
        self.cold_reboot('late-all8-invitations-cold')
        self.coverage.append('all8-late-invitations-without-trial-replay')

    def choose_party_candidate(self,slot,instance):
        for _ in range(4):
            if self.get('quickparty_menu_slot')==slot:break
            self.tap('RIGHT',2,3)
        for _ in range(161):
            if self.get('quickparty_menu_candidate')==instance:break
            self.tap('DOWN',2,3)
        self.check(self.get('quickparty_menu_slot')==slot and self.get('quickparty_menu_candidate')==instance,'real party menu selects exact proposed slot and instance')

    def legendary_party_notice(self):
        self.prepare_practice(0);self.step(1,'R');self.step(1)
        selected=self.roster().selected_party;first=self.selected().instance_id
        second=next(i for i,c in enumerate(self.roster().instances) if c.flags&1 and c.form_id==122)
        target=next(i for i in range(4) if i!=selected)
        self.open_tab(2);self.choose_party_candidate(target,second);self.step(3)
        names=('covenants_power_kind','covenants_power_time','covenants_power_age','ability_cd','covenants_cooldown_owned')
        state=bytes(self.state());proof=self.cv_cast_bytes();power={n:self.get(n) for n in names}
        before=self.out/'legendary-party-before.sav';after=self.out/'legendary-party-rejected.sav';self.e.save(before)
        title_before=self.e.screenshot().crop((8,31,232,51)).tobytes()
        self.e.screenshot(self.out/'legendary-party-before.png')
        self.tap('R',2,4);self.step(3)
        self.check(self.local('menu_notice',file='quickparty.c')==2,'second legendary shows the specific one-legendary party notice')
        self.check(self.get('game_state')==PAUSE and bytes(self.state())==state,'rejected second legendary preserves complete save, party and selected identity')
        self.check(self.cv_cast_bytes()==proof and {n:self.get(n) for n in names}==power,'rejected second legendary preserves live power proof and exact cooldown')
        self.e.save(after);self.check(before.read_bytes()==after.read_bytes(),'rejected second legendary causes no cartridge SRAM mutation')
        title_after=self.e.screenshot().crop((8,31,232,51)).tobytes()
        self.check(title_after!=title_before,'specific legendary limit notice is visibly rendered in the native title strip')
        shot=self.out/'legendary-party-specific-notice.png';self.e.screenshot(shot)
        self.cases.append({'name':'specific-second-legendary-party-notice','notice_text_id':self.ui_ids['TX_CV_PARTY_ONE'],
          'screenshot':str(shot),'selected_identity':first,'proposed_instance':self.roster().instances[second].instance_id,
          'party_unchanged':True,'complete_save_unchanged':True,'cartridge_SRAM_unchanged':True,'power_and_cooldown_unchanged':True,'frame':self.e.frame})
        self.tap('UP',2,3);self.step(3)
        self.check(self.local('menu_notice',file='quickparty.c')==0,'ordinary menu navigation dismisses legendary limit notice')
        self.e.screenshot(self.out/'legendary-party-notice-dismissed.png')
        self.choose_party_candidate(selected,second);self.tap('R',2,25);self.settle();self.close_menu()
        self.check(self.roster().party[selected]==second and self.roster().instances[second].form_id==122,'same-slot replacement by another owned legendary succeeds normally')
        self.select_form(122);self.check(self.selected().form_id==122,'normally selecting the replacement makes its owned identity active')
        self.check(sum(121<=self.roster().instances[i].form_id<=128 for i in self.roster().party if i<160)==1,'successful replacement retains exactly one active legendary')
        self.check(0<self.get('ability_cd')<=power['ability_cd'],'successful replacement cannot refund prior legendary cooldown')
        self.step(240);self.coverage.append('specific-second-legendary-notice-and-legal-replacement')

    def full_menu_matrix(self):
        before=self.state_signature()
        for tab in range(13):
            self.open_tab(tab)
            for _ in range(12 if tab==12 else 4):self.tap('DOWN',2,3)
            for _ in range(12 if tab==12 else 4):self.tap('UP',2,3)
            self.step(6);self.snapshot(f'full-roster-journal-tab-{tab:02d}',settle=False);self.close_menu()
        self.check(self.state_signature()==before,'viewing all13 full-roster journal tabs changes no durable roster quests or equipment')
        self.coverage.append('all13-full-roster-journal-tabs')

    def controls_final(self):
        self.check(self.completed_source,'controls start from exact authenticated complete native route')
        if self.minimal:self.late_invitations()
        self.legendary_party_notice()
        self.prepare_practice(0);self.step(1,'R');self.step(1)
        proof=self.cv_cast_bytes();age=self.get('covenants_power_age');cd=self.get('ability_cd')
        self.step(36,'L')
        self.check(self.cv_cast_bytes()==proof and self.get('covenants_power_age')==age and self.get('ability_cd')==cd,'held L freezes exact final field proof age and cooldown')
        self.step(1);self.tap('START',1,1);self.check(self.get('game_state')==PAUSE,'journal opens while legendary cast remains live')
        proof=self.cv_cast_bytes();age=self.get('covenants_power_age');cd=self.get('ability_cd')
        self.step(36)
        self.check(self.cv_cast_bytes()==proof and self.get('covenants_power_age')==age and self.get('ability_cd')==cd,'viewing journal preserves exact final field proof and cooldown')
        self.tap('B',1,1);self.step(36);self.step(1,'R')
        self.wait_for(lambda:self.cv_local('practice_ticks')>0,'viewed immutable cast can still complete its practice')
        self.step(400)
        self.prepare_practice(0);self.step(1,'R');self.step(1)
        cd=self.get('ability_cd');selected=self.roster().selected_party;other=next(i for i,v in enumerate(self.roster().party) if v<160 and i!=selected)
        self.tap('L+'+('UP','RIGHT','DOWN','LEFT')[other],1,1)
        self.check(not self.cv_local('practice_mode') and int.from_bytes(self.cv_cast_bytes()[:4],'little')==0,'actual selector edit revokes final cast field rights')
        self.check(0<self.get('ability_cd')<=cd,'actual selector edit does not refund legendary cooldown')
        self.step(180);self.check(not self.cv_local('practice_ticks'),'revoked cast cannot rebuild final field rights')
        self.prepare_practice(0);self.step(1,'R');self.step(1)
        cd=self.get('ability_cd');selected_id=self.selected().instance_id;selected_slot=self.roster().selected_party
        party=set(self.roster().party);replacement=next(c.form_id for j,c in enumerate(self.roster().instances) if c.flags&1 and j not in party and c.form_id<121)
        other_slot=next(i for i in range(4) if i!=selected_slot)
        self.assign(other_slot,replacement)
        self.check(self.selected().instance_id==selected_id and not self.cv_local('practice_mode') and int.from_bytes(self.cv_cast_bytes()[:4],'little')==0,'editing another party slot revokes exact field proof while selected identity stays unchanged')
        self.check(0<self.get('ability_cd')<=cd,'party assignment cannot refund the live legendary cooldown')
        self.step(220)
        self.owned_select(121);self.set_command(12);self.ready();self.target(48,296,0)
        self.check(self.cv_local('reset_confirm')==1,'reset requires deliberate second A')
        self.step(1,'R');cd=self.get('ability_cd');before=self.state_signature();self.tap('A');self.settle()
        self.check(self.state_signature()==before and not self.cv_local('practice_mode'),'confirmed local reset preserves all durable history and clears transient work')
        self.check(0<self.get('ability_cd')<=cd,'confirmed local reset does not refund legendary cooldown')
        self.step(240);self.practice_route();self.full_menu_matrix()
        self.coverage.append('selector-menu-reset-cooldown-all8-practice')

    def run(self,scope,arm_order='forward'):
        self.boot()
        if scope in ('full','lifecycle'):
            self.lifecycle_mode=scope=='lifecycle';self.full_route(arm_order)
        elif scope=='controls':self.controls_final()
        elif scope=='late-invitations':self.late_invitations()
        elif scope!='migration':
            self.main_only=self.minimal;self.lifecycle_mode=scope=='first-two-lifecycle'
            self.initialize_covenants()
            if self.lifecycle_mode:self.interrupt_local_work(0)
            self.solve70();self.invitation(0,accept=not self.minimal)
            if self.lifecycle_mode:self.interrupt_local_work(1)
            self.solve71();self.invitation(1,accept=not self.minimal)
            self.cold_reboot('first-two-cold')
            self.main_only=False
        self.finished_scope=scope;self.verify_closures();self.report()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','symbols','output','source-manifest','source-root'):p.add_argument('--'+key,type=Path,required=True)
    for key in ('expected-rom-sha','expected-symbols-sha','expected-elf-sha','expected-manifest-sha'):p.add_argument('--'+key,required=True)
    p.add_argument('--prior-root',type=Path,default=ROOT)
    p.add_argument('--prelude-report',type=Path)
    p.add_argument('--prelude-sha')
    p.add_argument('--prelude-snapshot')
    p.add_argument('--earned-report',type=Path)
    p.add_argument('--earned-sha')
    p.add_argument('--earned-snapshot')
    p.add_argument('--fixture-kind',choices=tuple(C_INPUTS),default='full')
    p.add_argument('--scope',choices=('migration','first-two','first-two-lifecycle','full','controls','lifecycle','late-invitations'),default='migration')
    p.add_argument('--arm-order',choices=('forward','reverse'),default='forward')
    p.add_argument('--timing-mode',choices=('strict','collect-diagnostic'),default='strict')
    a=p.parse_args()
    r=CovenantsJourney(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.expected_elf_sha,
        a.source_manifest,a.expected_manifest_sha,source_root=a.source_root,timing_mode=a.timing_mode,prior_root=a.prior_root,fixture_kind=a.fixture_kind,prelude_report=a.prelude_report,prelude_sha=a.prelude_sha,prelude_snapshot=a.prelude_snapshot,earned_report=a.earned_report,earned_sha=a.earned_sha,earned_snapshot=a.earned_snapshot)
    try:r.run(a.scope,a.arm_order)
    except Exception as exc:
        r.failures.append({'error':str(exc),'traceback':traceback.format_exc(),'status':r.status()})
        r.snapshot('failure',settle=False);raise
    finally:r.close_global_trace();r.report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
