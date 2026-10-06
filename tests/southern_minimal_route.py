#!/usr/bin/env python3
"""Bounded S3 prerequisite proof using genuine main-only N5 SRAM.

Only controller inputs mutate gameplay. Cold SRAM imports are hash-checked;
all machine-state loads and RAM writes are forbidden, including same-ROM loads.
Unchanged SouthernJourney helpers provide controller navigation, recruitment,
reset/escape/reentry recovery and actual starter-sword boss combat. The constructor
is explicit because the standard helper intentionally pins a different full-history
fixture. This does not relax that fixture or modify any existing helper.
Reports and screenshots contain developer-only progression details.
"""
from __future__ import annotations
import argparse, hashlib, inspect, json, shutil, struct
from pathlib import Path
from southern_symbols import paired_southern_symbols
from southern_journey import SouthernJourney, N5_ROM
from northern_journey import newest_bank
from region_journey import ROOT, Emulator, digest

MINIMAL_SHA='d34152445836da03a7cd9abbcd11f68e35d70887717bc24624bb2141cb25da5d'
PRODUCER_REPORT_SHA='b1e0eb43aa6a7ec36e0cae8aac41673fd831ae574db63234a2006ce6bb49ecba'
N5_SYMBOLS_SHA='7110402451d7bea92ebd1d83dfddbf2f389468028e8842ef6afa22f043595018'
OLD_FORMS=[1,4,7,10,19,77]
OLD_QUESTS=[3 if q in (11,13,21) else 0 for q in range(22)]


def authenticate_source(fixture):
    provenance=fixture.with_suffix('.provenance.json')
    data=json.loads(provenance.read_text())
    assert data['sha256']==digest(fixture)==MINIMAL_SHA
    assert data['source_rom_sha256']==N5_ROM and data['source_symbols_sha256']==N5_SYMBOLS_SHA
    manifest_path=fixture.parent/data['source_report_manifest']
    assert digest(manifest_path)==data['source_report_manifest_sha256']
    manifest=json.loads(manifest_path.read_text())
    assert manifest['format']=='exact-byte-concatenation-v1'
    assert manifest['original_bytes']==780727 and manifest['max_part_bytes']==30000
    assert manifest['original_sha256']==data['source_report_sha256']==PRODUCER_REPORT_SHA
    fixture_files={str(p.relative_to(ROOT)):digest(p) for p in (fixture,provenance,manifest_path)}
    chunks=[];offset=0
    for index,row in enumerate(manifest['parts']):
        assert row['file']==f'part_{index:03d}.txt' and row['offset']==offset
        part=manifest_path.parent/row['file'];raw=part.read_bytes()
        assert len(raw)==row['bytes'] and 0<len(raw)<=30000
        assert hashlib.sha256(raw).hexdigest()==row['sha256']
        raw.decode('utf-8')
        chunks.append(raw);offset+=len(raw)
        fixture_files[str(part.relative_to(ROOT))]=row['sha256']
    report_bytes=b''.join(chunks)
    assert len(report_bytes)==manifest['original_bytes']
    assert hashlib.sha256(report_bytes).hexdigest()==PRODUCER_REPORT_SHA
    producer=json.loads(report_bytes)
    assert producer['rom_sha256']==N5_ROM and producer['symbols_sha256']==N5_SYMBOLS_SHA
    assert producer['controller_only'] and producer['game_ram_writes']==0
    assert not producer['failures'] and all(c['passed'] for c in producer['checks'])
    assert len(producer['checks'])==data['source_report_checks']
    source_checks={}
    for path,sha in producer['test_sources'].items():
        archived=manifest_path.parent.parent/'test-source'/Path(path).name
        assert digest(archived)==sha,('producer source mismatch',path)
        source_checks[path]=sha
        fixture_files[str(archived.relative_to(ROOT))]=sha
    endpoint=producer['snapshots'][data['source_snapshot']]
    assert endpoint['sram_sha256']==MINIMAL_SHA
    assert endpoint['quests']==OLD_QUESTS
    assert endpoint['owned_form_ids']==endpoint['obtained_form_ids']==OLD_FORMS
    assert endpoint['status']['chapter_flags']==3 and endpoint['status']['room']==22
    original_root=Path(endpoint['sram_path']).parent
    assert data['source_directory']==str(original_root)
    original_artifacts={str(original_root/'test-source'/Path(path).name):sha
                        for path,sha in producer['test_sources'].items()}
    for snapshot in producer['snapshots'].values():
        assert snapshot['rom_sha256']==N5_ROM and snapshot['symbols_sha256']==N5_SYMBOLS_SHA
        for kind in ('state','sram'):
            original_artifacts[snapshot[kind+'_path']]=snapshot[kind+'_sha256']
    assert len(original_artifacts)==37 and data['verified_original_artifacts']==original_artifacts
    return {'provenance_sha256':digest(provenance),'report_sha256':hashlib.sha256(report_bytes).hexdigest(),
            'report_manifest_sha256':digest(manifest_path),'report_part_count':len(chunks),
            'verified_fixture_files':fixture_files,
            'verified_producer_tests':source_checks,'producer_checks':len(producer['checks']),
            'producer_inputs':len(producer['inputs']),'endpoint':endpoint,
            'original_artifacts_verified_at_fixture_capture':data['verified_original_artifacts']}


class ControllerOnlyEmulator(Emulator):
    def write(self,*args,**kwargs):
        raise AssertionError('RAM writes are forbidden in this acceptance run')
    def state(self,path,load=False):
        assert not load,'No machine-state load is permitted in this acceptance run'
        return super().state(path,False)


class SouthernMinimalRoute(SouthernJourney):
    def __init__(self,rom,symbols,output,expected_rom_sha,expected_symbols_sha,fixture=None,source_manifest=None,elf=None):
        assert digest(rom)==expected_rom_sha,'Candidate ROM differs from explicit frozen SHA'
        assert digest(symbols)==expected_symbols_sha,'Candidate symbols differ from explicit frozen SHA'
        self.target_sha=expected_rom_sha;self.symbol_sha=expected_symbols_sha;self.scene_only=False
        self.source_rom=Path(rom).resolve();self.source_symbols=Path(symbols).resolve();self.out=Path(output).resolve();self.out.mkdir(parents=True,exist_ok=True)
        self.rom=self.out/'tested.gba';self.symbol_path=self.out/'tested.sym'
        for src,dst in ((self.source_rom,self.rom),(self.source_symbols,self.symbol_path)):
            if src!=dst:shutil.copyfile(src,dst)
        self.sym,self.south_elf_pairing=paired_southern_symbols(self.rom,self.symbol_path,elf or self.source_rom.with_suffix('.elf'),self.out/'tested.elf')
        self.candidate={'rom_path':str(self.source_rom),'symbols_path':str(self.source_symbols),'rom_sha256':digest(self.rom),'symbols_sha256':digest(self.symbol_path),'rom_bytes':self.rom.stat().st_size,'emulator_bridge_sha256':digest(ROOT/'tools/mgba_bridge.so'),'emulator_bridge_source_sha256':digest(ROOT/'tools/mgba_bridge.c')}
        self.candidate['southern_elf_pairing']=self.south_elf_pairing
        self.inputs=[];self.checks=[];self.snapshots={};self.failures=[];self.timings={};self.coverage=[];self.cases=[];self.frame_windows=[];self.pixel_cases=[];self.acquisitions=[];self.transitions=[];self.main_selections=[];self.main_only=False
        self.fixture=Path(fixture or ROOT/'tests/fixtures/v5-revision3/northern-main-only-sky.sav').resolve()
        assert digest(self.fixture)==MINIMAL_SHA,'Only the exact genuine main-only N5 SRAM is accepted'
        self.source_authentication=authenticate_source(self.fixture)
        self.imported_sram=[];self.session=0;self.completed=False;self.field_commands=[];self.state_records={}
        self.source_bytes=self.fixture.read_bytes();self.source_bank=newest_bank(self.source_bytes)
        assert int.from_bytes(self.source_bank[12:14],'little')==3
        self.provenance={'fixture_path':str(self.fixture),'sram_sha256':MINIMAL_SHA,'source_rom_sha256':N5_ROM,'source_machine_state_loaded':False,'source_report_sha256':PRODUCER_REPORT_SHA,'scope':'Genuine six base individuals and six histories; only Northern main quests11/13/21 complete; no River/optional Northern quests, Core clear, ending, or Southern progress'}
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
        self.test_sources={str(p.relative_to(ROOT)):digest(p) for p in (Path(__file__).resolve(),ROOT/'tests/southern_symbols.py',ROOT/'tests/southern_journey.py',ROOT/'tests/northern_journey.py',ROOT/'tests/region_journey.py',ROOT/'tests/region_combat_tests.py',ROOT/'tests/test_save5.py',ROOT/'tests/test_save4.py',ROOT/'tools/mgba_runner.py',Path(inspect.getfile(type(self))).resolve())}
        (self.out/'test-source').mkdir(exist_ok=True)
        for p in self.test_sources:shutil.copyfile(ROOT/p,self.out/'test-source'/Path(p).name)
        # Preserve fixture hierarchy to avoid colliding with current helper names.
        # Every fragment, integrity manifest, source script and SRAM input is part
        # of the test-source hash provenance, not only the reconstructed report.
        for p,sha in self.source_authentication['verified_fixture_files'].items():
            self.test_sources[p]=sha
            dest=self.out/'test-source'/p;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/p,dest)
        self.contract=json.loads((ROOT/'assets/southern_region/contract.json').read_text());self.scene=json.loads((ROOT/'assets/southern_region/scene.json').read_text())
        self.contract_sha=digest(ROOT/'assets/southern_region/contract.json');self.scene_sha=digest(ROOT/'assets/southern_region/scene.json')
        self.e=ControllerOnlyEmulator(self.rom);self.cold_import(self.fixture,MINIMAL_SHA);self.mask_cache={};self.descriptors={}
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

    def cold_import(self, path, expected_sha):
        assert digest(path)==expected_sha
        self.imported_sram.append({'session':self.session,'path':str(path),'sha256':expected_sha,'machine_state_loaded':False})
        self.e.load_save(path);self.e.reset()

    def report(self):
        if not hasattr(self,'descriptors'):return
        super().report()
        base=self.out/'southern-journey.json'
        data=json.loads(base.read_text())
        data.update({'suite':'southern-minimal-native-controller-route','completed':self.completed,
                     'source_authentication':self.source_authentication,'cold_sram_imports':self.imported_sram,
                     'machine_state_loads':0,'field_commands':self.field_commands,'state_records':self.state_records,
                     'coverage_scope':'Main-route dependency proof only. No optional recruitment, evolution, optional rewards, all41 collection, alternate weapons, exhaustive combat, or performance acceptance claimed.'})
        for path in (base,self.out/'southern-minimal-route.json'):
            path.write_text(json.dumps(data,indent=2)+'\n')

    def step(self,n,keys=0):
        super().step(n,keys)
        self.inputs[-1]['emulator_session']=self.session

    def record_state(self,name):
        s=self.state()
        self.state_records[name]={
            'status':self.status(),'quests':[self.quest(q) for q in range(30)],
            'quest_objectives':list(s.quests.objectives),'quest_rewards':list(s.quests.rewards),
            'region_flags':list(s.quests.region_flags),'obtained_form_ids':self.collection(),
            'individuals':[{'instance_id':c.instance_id,'form_id':c.form_id,'level':c.level,'bond':c.bond,
                            'xp':c.xp,'trial_flags':c.trial_flags,'record_hex':bytes(c).hex()} for c in self.live()],
            'party_slots':list(s.roster.party),'selected_party':s.roster.selected_party,
            'selected_instance_id':self.selected().instance_id,'next_instance_id':s.roster.next_instance_id,
            'gear_item_ids':[g.item_id for g in s.equipment.bag if g.item_id],
            'equipped_items':[s.equipment.bag[i].item_id if i<48 else 0 for i in s.equipment.equipped],
            'chapter_flags':self.get('chapter_flags'),'room_flags':self.get('room_flags'),
            'roster_hex':bytes(s.roster).hex(),'quests_hex':bytes(s.quests).hex(),'equipment_hex':bytes(s.equipment).hex()}
        self.report()

    def absent_optional(self):
        s=self.state()
        self.check([self.quest(q) for q in range(22)]==OLD_QUESTS,'River and optional Northern quests stay absent; prior main quests stay complete')
        self.check(self.get('chapter_flags')==3,'earlier Core clear and ending remain unearned')
        self.check(all(self.quest(q)==0 and s.quests.objectives[q]==0 for q in range(25,30)),
                   'all optional Southern quests remain absent')
        self.check(not s.quests.region_flags[8],'no optional Southern field companion claimed')
        self.check(all(c.trial_flags==0 for c in self.live()),'no personal trial or evolution prerequisite acquired')

    def boot(self):
        self.step(150);self.tap('START',2,35);self.settle();s=self.state();b=self.source_bank
        self.check(self.get('room')==22,'genuine main-only Northern SRAM cold-resumes in Northern town')
        self.check(bytes(s.roster.instances)==b[160:4000],'migration preserves all160 exact prior instance records')
        self.check(bytes(s.roster.party)==b[4000:4004] and s.roster.selected_party==b[4004],
                   'migration preserves active party and selected individual')
        self.check(bytes(s.roster.seen)+bytes(s.roster.obtained)+bytes(s.roster.rewards)==b[96:144],
                   'migration preserves exact six-history collection and reward ledgers')
        self.check(bytes(s.quests)==b[4032:4296] and bytes(s.equipment)==b[4544:5056],
                   'migration preserves exact previous quests and starter-only equipment')
        self.check(bytes(s.roster.expedition_bond)+bytes(s.roster.expedition_events)+bytes(s.roster.lifetime_field_aid)==b[4296:4536],
                   'migration preserves expedition and lifetime field aid bytes')
        self.check(self.collection()==OLD_FORMS and [c.form_id for c in self.live()]==OLD_FORMS,
                   'source genuinely owns only six base individuals and six historical forms')
        self.check([c.instance_id for c in self.live()]==[1,2,3,4,5,6],
                   'all exact original individual IDs survive forward migration')
        self.check(not any(s.quests.region_flags[2:]) and all(self.quest(q)==0 and not s.quests.objectives[q] for q in range(22,30)),
                   'migration invents no Southern content')
        self.check([g.item_id for g in s.equipment.bag if g.item_id]==[1],
                   'source owns only guaranteed starter sword and no optional gear reward')
        self.old_ids={c.instance_id for c in self.live()};self.old_forms={c.instance_id:c.form_id for c in self.live()}
        self.old_records={c.instance_id:bytes(c) for c in self.live()}
        self.old_quests=[self.quest(q) for q in range(22)];self.old_objectives=list(s.quests.objectives[:22])
        saved=self.e.bytes(0x0e000000,32768);migrated=newest_bank(saved)
        self.check(int.from_bytes(migrated[12:14],'little')==5 and migrated[32:]==b[32:],
                   'migration commits current revision5 with byte-identical revision3 payload')
        old_offset=self.source_bytes.index(b)
        self.check(saved[old_offset:old_offset+6144]==b,'forward migration keeps prior committed revision3 bank intact')
        self.absent_optional();self.record_state('before-southern-entry');self.snapshot('00-minimal-n5-forward-migration')
        self.entry(30);self.snapshot('01-minimal-ferry-entry')

    def field_object(self,key,form):
        super().field_object(key,form)
        self.field_commands.append({'frame':self.e.frame,'room':self.get('room'),'target':key,
                                    'form_id':form,'instance_id':self.selected().instance_id})

    def main_route(self):
        self.recruits_main()
        self.check([c.form_id for c in self.live()]==OLD_FORMS+[79,85],
                   'only the two mandatory Southern base companions are recruited')
        self.check([c.instance_id for c in self.live()]==list(range(1,9)),
                   'mandatory recruits receive new IDs7 and8 without changing earlier individuals')
        for room in (34,35,36):self.puzzle_room(room)
        self.snapshot('03-minimal-machine-ready');self.record_state('before-boss')
        self.check([g.item_id for g in self.state().equipment.bag if g.item_id]==[1,4],
                   'only starter sword and mandatory recruit quest gear exist before boss')
        self.check([self.state().equipment.bag[i].item_id if i<48 else 0 for i in self.state().equipment.equipped]==[1,0,0,0,0],
                   'before boss only starter sword is equipped with no armor or accessory prerequisite')
        self.machine(1)
        self.check(set(self.main_selections)<={79,85},'entire Southern mandatory route selects only guaranteed bases79/85')
        self.check(all(r['form_id'] in (79,85) for r in self.field_commands),
                   'all mandatory field commands use the two guaranteed Southern bases')
        self.check(self.state().equipment.bag[self.state().equipment.equipped[0]].item_id==1,
                   'actual boss completion uses guaranteed starter sword item1')
        self.check(all(self.quest(q)==3 for q in (22,23,24)),'only mandatory Southern quests are completed')
        self.main_only=False;self.use('start');self.check(self.get('room')==30,'completed main route returns to Southern town')
        self.use('rest');self.absent_optional()
        self.check({c.instance_id:c.form_id for c in self.live() if c.instance_id in self.old_ids}==self.old_forms,
                   'every prior individual retains exact ID and form after the full route')
        self.check({c.instance_id:bytes(c) for c in self.live() if c.instance_id in self.old_ids}==self.old_records,
                   'all six earlier individual records stay byte-identical through the full route')
        self.check(self.get('room_flags')==int.from_bytes(self.source_bank[40:44],'little'),
                   'all earlier campaign room progression bits remain unchanged')
        self.check(list(self.state().quests.objectives[:22])==self.old_objectives,
                   'all earlier quest objectives stay unchanged')
        self.check(self.collection()==OLD_FORMS+[79,85],'no extra history or evolved form manufactured')
        self.record_state('main-complete');self.snapshot('04-minimal-main-complete')
        before=(bytes(self.roster()),bytes(self.state().quests),bytes(self.state().equipment))
        snap=self.snapshots['04-minimal-main-complete'];self.e.close();self.session+=1
        self.e=ControllerOnlyEmulator(self.rom);self.cold_import(snap['sram_path'],snap['sram_sha256'])
        self.step(150);self.tap('START',2,35);self.settle()
        self.check((bytes(self.roster()),bytes(self.state().quests),bytes(self.state().equipment))==before,
                   'independent cold SRAM boot preserves exact roster, quests and equipment')
        self.check(self.get('room')==30,'independent boot resumes at Southern safe checkpoint')
        self.absent_optional();self.record_state('independent-reboot');self.snapshot('05-minimal-independent-reboot')
        self.entry(22);self.absent_optional();self.record_state('old-region-return');self.snapshot('06-minimal-old-region-return')
        self.coverage.extend(['genuine-main-only-N5-SRAM-forward-migration','ferry-without-optional-prerequisites',
                              'mandatory-bases79-and85-only','all-three-main-puzzles-reset-and-escape-reentry',
                              'native-starter-sword-boss-clear','independent-cold-reboot-and-earlier-region-return'])
        self.completed=True;self.report()

    def run(self):
        self.boot();self.main_route()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','symbols','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True)
    p.add_argument('--source-sram',type=Path);p.add_argument('--source-manifest',type=Path)
    a=p.parse_args();run=SouthernMinimalRoute(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_sram,a.source_manifest)
    try:run.run()
    except Exception as exc:
        run.failures.append({'error':str(exc),'status':run.status()});run.snapshot('failure',settle=False);raise
    finally:run.report();run.e.close()
    print(json.dumps({'completed':run.completed,'report':str(run.out/'southern-minimal-route.json'),
                      'report_sha256':digest(run.out/'southern-minimal-route.json'),'checks':len(run.checks)}),flush=True)


if __name__=='__main__':main()
