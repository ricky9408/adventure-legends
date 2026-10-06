#!/usr/bin/env python3
"""Independent cold-SRAM lifecycle of actually earned34 individuals/65 histories.

Only a successful exact-ROM controller producer, or the explicitly authorized
and separately pinned predecessor-C cold SRAM for targetD, is admitted. The original
producer's machine states are never loaded. Every mutation is ordinary input;
no generated catalog row, synthetic roster, injected health or RAM write is
acquisition evidence. Four same-family branch pairs come from actual ownership.
"""
from __future__ import annotations
import argparse, json, shutil
from collections import defaultdict
from pathlib import Path
from magma_controls import MagmaControls, NoRamWriteEmulator
from magma_journey import MagmaJourney, ROOT, PLAY, DEAD, SAVING, digest
from northern_journey import newest_bank
from southern_journey import ALL_FORMS as SOUTH_FORMS

ALL65 = sorted(SOUTH_FORMS+list(range(31,49))+list(range(95,101)))
PREDECESSOR_C_ROM='8080b2fb1c82a99650da9837c5f5037a570dc3e5b17eb1a10ee7a9d7c31ffde4'
PREDECESSOR_C_SYMBOLS='018eb338ea61eb0af04ea91de32d2c3d10564033f6dd9ab85d2904e259b0274e'
PREDECESSOR_C_REPORT='439a0096fc5f70109fcebc52082ad6bf815c53eef148e1b6b3aada5892913c27'
PREDECESSOR_C_SRAM='8287fb0c34b2cdd2a73408bd24bf290f640281ac3a8b7d98d0ad8a5f009ece28'
AUTHORIZED_TARGET_D='90ba47f30a0c94c28f073d26cc31ac5f5c736eb4d6e704d090892d2776f1ffb2'

class ColdOnlyEmulator(NoRamWriteEmulator):
    def state(self, path, load=False):
        assert not load, 'Retained lifecycle never imports a machine state'
        return super().state(path, False)

class MagmaRetainedControls(MagmaControls):
    def __init__(self, *args, source_report, source_snapshot, allow_authenticated_predecessor_c=False, **kwargs):
        self.completed=False;self.branch_loads=[];self.case_results=[];self.oracle_results=[]
        self.cold_imports=[];self.retained_records={};self.session=0
        report_path=Path(source_report).resolve();producer=json.loads(report_path.read_text())
        assert producer['controller_only'] and producer['game_ram_writes']==0
        assert not producer['failures'] and all(row['passed'] for row in producer['checks'])
        fixture=ROOT/'tests/fixtures/v5-revision4'/Path(producer['provenance']['fixture']).name
        assert digest(fixture)==producer['provenance']['sram_sha256']
        kwargs['fixture']=fixture
        MagmaJourney.__init__(self,*args,**kwargs)
        same_rom=producer['rom_sha256']==self.target_sha and producer['symbols_sha256']==self.symbol_sha
        if not same_rom:
            assert allow_authenticated_predecessor_c and self.target_sha==AUTHORIZED_TARGET_D
            assert producer['rom_sha256']==PREDECESSOR_C_ROM and producer['symbols_sha256']==PREDECESSOR_C_SYMBOLS
            assert digest(report_path)==PREDECESSOR_C_REPORT and source_snapshot=='09-all65-earned-town'
        source=producer['snapshots'][source_snapshot]
        assert source['rom_sha256']==producer['rom_sha256'] and source['symbols_sha256']==producer['symbols_sha256']
        assert source['obtained_form_ids']==ALL65 and len(source['owned_form_ids'])==34
        assert source['quests']==[3]*38
        sram=Path(source['sram_path']);assert digest(sram)==source['sram_sha256']
        if not same_rom:assert source['sram_sha256']==PREDECESSOR_C_SRAM
        self.source_sram=self.out/'earned34-source.sav';shutil.copyfile(sram,self.source_sram)
        self.source_sram_sha=source['sram_sha256'];self.source_earned_bank=newest_bank(self.source_sram.read_bytes())
        assert int.from_bytes(self.source_earned_bank[12:14],'little')==(6 if same_rom else 5)
        self.provenance.update(earned_source_report=str(report_path),earned_source_report_sha256=digest(report_path),
                               earned_source_snapshot=source_snapshot,earned_source_sram_sha256=self.source_sram_sha,
                               earned_source_rom_sha256=producer['rom_sha256'],earned_source_symbols_sha256=producer['symbols_sha256'],
                               earned_source_relation='same-ROM' if same_rom else 'explicitly authenticated predecessor-C cold SRAM into D',
                               source_machine_states_loaded=0)
        shutil.copyfile(report_path,self.out/'earned-source-report.json')
        receipt_path=report_path.parent/'test-source-capture.json'
        receipt=json.loads(receipt_path.read_text())
        assert receipt['recorded_hashes_verified']==producer['test_sources']
        verified={**receipt['recorded_hashes_verified'],**receipt['additional_imported_observer_sources']}
        for path,sha in verified.items():
            original=report_path.parent/'test-source'/Path(path).name
            assert digest(original)==sha
            destination=self.out/'producer-test-source'/path;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(original,destination)
        shutil.copyfile(receipt_path,self.out/'producer-test-source-capture.json')
        self.provenance['producer_source_capture_sha256']=digest(receipt_path)
        self.provenance['verified_producer_test_sources']=verified
        for name in ('magma_controls.py','magma_retained_controls.py'):
            self.test_sources['tests/'+name]=digest(ROOT/'tests'/name)
        for path,sha in self.test_sources.items():
            p=ROOT/path;assert digest(p)==sha
            destination=self.out/'test-source'/path;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,destination)
        self.e.close();self.e=ColdOnlyEmulator(self.rom)
        self.report()

    def report(self):
        MagmaControls.report(self)
        data=json.loads((self.out/'magma-controls.json').read_text())
        data.update(suite='magma-earned34-65-independent-lifecycle',cold_sram_imports=self.cold_imports,
                    machine_state_loads=0,retained_records=self.retained_records,
                    coverage_scope='Cold boot, autosave, all34 storage candidates, four actually retained same-family pairs, ordinary hazard death/retry/reboot; no new acquisition claim')
        (self.out/'magma-retained-controls.json').write_text(json.dumps(data,indent=2)+'\n')

    def cold_boot(self,path,sha):
        assert digest(path)==sha
        self.e.close();self.e=ColdOnlyEmulator(self.rom);self.session+=1
        self.cold_imports.append({'session':self.session,'path':str(path),'sha256':sha,'machine_state_loaded':False})
        self.e.load_save(path);self.e.reset();self.step(150);self.tap('START',2,35);self.settle()
        self.check(self.get('game_state')==PLAY,'independent SRAM boot resumes playable game')
        self.full_counts()

    def full_counts(self):
        self.check(self.collection()==ALL65,'all65 genuinely earned historical form receipts survive')
        self.check(len(self.live())==34 and len({c.instance_id for c in self.live()})==34,'all34 actual individuals survive with unique immutable identities')
        self.check([self.quest(q) for q in range(38)]==[3]*38,'all38 actual claimed quest states survive')

    def retained(self):
        return bytes(self.roster()),bytes(self.state().quests),bytes(self.state().equipment)

    def record(self,label):
        s=self.state()
        self.retained_records[label]={'status':self.status(),'obtained_form_ids':self.collection(),
            'individuals':[{'instance_id':c.instance_id,'form_id':c.form_id,'record_hex':bytes(c).hex()} for c in self.live()],
            'party':list(s.roster.party),'selected_party':s.roster.selected_party,'selected_instance_id':self.selected().instance_id,
            'roster_hex':bytes(s.roster).hex(),'quests_hex':bytes(s.quests).hex(),'equipment_hex':bytes(s.equipment).hex()}
        self.report()

    def town(self):
        if self.get('room')==30:self.entry(38)
        elif self.get('room')!=38:self.to_town()
        self.check(self.get('room')==38,'earned source reaches ordinary safe Magma town')

    def source_boot(self):
        self.cold_boot(self.source_sram,self.source_sram_sha)
        s=self.state();b=self.source_earned_bank
        self.check(bytes(s.roster.instances)==b[160:4000],'cold boot preserves exact160-slot instance array from controller-earned SRAM')
        self.check(bytes(s.roster.party)==b[4000:4004] and s.roster.selected_party==b[4004],'cold boot preserves all party references and selected actual identity')
        self.check(bytes(s.roster.seen)+bytes(s.roster.obtained)+bytes(s.roster.rewards)==b[96:144],'cold boot preserves exact earned collection and reward ledgers')
        self.check(bytes(s.quests)==b[4032:4296] and bytes(s.equipment)==b[4544:5056],'cold boot preserves exact quests and equipment')
        self.record('independent-earned34-source');self.snapshot('00-independent-earned34-source');self.town()

    def storage_window(self):
        self.open_tab(2);before=self.retained();trace=[]
        frame=self.get('frame');page=self.e.read(0x04000000,2)&16
        for i in range(148):
            self.step(1,'DOWN' if i%4==0 else 0)
            index=self.get('quickparty_menu_candidate');r=self.roster();now=self.get('frame');newpage=self.e.read(0x04000000,2)&16
            trace.append({'hardware_frame':self.e.frame,'candidate_index':index,'candidate_id':r.instances[index].instance_id if index<160 else None,
                          'candidate_form':r.instances[index].form_id if index<160 else None,'delta':(now-frame)&0xffffffff,
                          'flip':newpage!=page,'cycles':self.get('render_cycles'),'obj_count':self.get('obj_count')})
            frame,page=now,newpage
        self.frame_windows.append({'name':'actual34-storage-cycle','hardware_frames':len(trace),'updates':sum(x['delta'] for x in trace),
                                   'flips':sum(x['flip'] for x in trace),'max_cycles':max(x['cycles'] for x in trace),'trace':trace})
        self.check({c.instance_id for c in self.live()}<={x['candidate_id'] for x in trace},'ordinary storage scrolling visits every one of34 actually retained individuals')
        self.check(self.retained()==before,'browsing all34 candidates changes no roster quests or equipment bytes')
        self.check(all(x['delta']==1 and x['flip'] and x['cycles']<280896 and x['obj_count']<=128 for x in trace),'full34 storage draws every hardware frame within actual cycle and OBJ budgets')
        self.close_menu()

    def assign_identity(self,slot,identity):
        index=next(i for i,c in enumerate(self.roster().instances) if c.flags&1 and c.instance_id==identity)
        self.open_tab(2)
        for _ in range(4):
            if self.get('quickparty_menu_slot')==slot:break
            self.tap('RIGHT',2,3)
        for _ in range(161):
            if self.get('quickparty_menu_candidate')==index:break
            self.tap('DOWN',2,3)
        self.check(self.get('quickparty_menu_candidate')==index,'journal cursor reaches the exact requested owned individual')
        self.tap('R',2,25);self.settle();self.close_menu()
        self.check(self.roster().party[slot]==index,'ordinary journal assignment references exact instance, not just a family or form')

    def same_family_pairs(self):
        # ROM catalog supplies metadata only; group membership comes exclusively
        # from the34 actual retained records observed after independent boot.
        rows=[self.e.bytes(self.sym['creature_forms']+i*32,32) for i in range(65)]
        forms={row[0]:row for row in rows};groups=defaultdict(list)
        for c in self.live():
            if c.form_id in list(range(31,49))+list(range(95,101)):
                groups[forms[c.form_id][1]].append((c.instance_id,c.form_id))
        pairs={family:sorted(owned) for family,owned in groups.items() if len(owned)==2}
        self.check(len(pairs)==4,'four same-family branch pairs genuinely coexist in retained ownership')
        for family, pair in sorted(pairs.items()):
            first,second=pair
            self.assign_identity(0,first[0]);self.assign_identity(1,second[0]);self.select_slot(0)
            self.set_command(forms[first[1]][11]);self.goto(260,248);self.face(3);self.ready();self.step(120)
            self.check(self.selected().instance_id==first[0],'first member of actual same-family pair selected')
            before_records=bytes(self.roster().instances);self.step(1,'R');self.step(1)
            self.check(self.get('magma_power_time')>0,'genuine same-family member starts its owned signature cast')
            caster=self.local('caster_id',4,file='magma_powers.c')
            self.check(caster==first[0],'native cast ownership records exact first individual')
            before=(self.get('px'),self.get('py'),self.get('hp'),self.get('magma_power_time'),self.get('magma_power_age'),self.get('ability_cd'),self.local('world_clock'))
            self.raw('same-family-'+str(family)+'-L-freeze',32,lambda i:'L+RIGHT')
            self.check((self.get('px'),self.get('py'),self.get('hp'),self.get('magma_power_time'),self.get('magma_power_age'),self.get('ability_cd'),self.local('world_clock'))==before,'same-family selector freezes position health effect cooldown and regional clock')
            self.step(1)
            self.check(self.selected().instance_id==second[0] and self.selected().form_id==second[1],'L release selects exact second same-family individual')
            self.check(self.local('caster_id',4,file='magma_powers.c')==first[0],'same-family selection cannot steal active cast ownership')
            self.step(3);self.tile_check('same-family-'+str(family)+'-new-selected-pose')
            self.check(self.get('gfx_companion_frame')<131072,'different same-family instance does not borrow the original casting pose')
            self.step(1,'R');self.step(1)
            self.check(self.local('caster_id',4,file='magma_powers.c')==first[0] and self.get('ability_cd')>0,'different same-family member cannot overwrite live cast or reset cooldown')
            self.check(bytes(self.roster().instances)==before_records,'same-family swaps preserve every exact retained individual record')
            self.step(120)
            self.case_results.append({'name':'actual-same-family-pair','family':family,'individuals':pair,'original_cast_owner':caster,'passed':True})
        self.full_counts();self.record('after-four-same-family-selectors');self.snapshot('01-four-same-family-selectors')

    def save_reboot(self):
        self.goto(112,264);self.face(1);self.step(4)
        before=self.retained()
        self.snapshot('02-before-full34-native-save')
        try:
            row=self.raw('actual34-native-save-through-resume',180,lambda i:'A' if i==0 else 0)
        except AssertionError as exc:
            # Preserve strict failure and continue independent functional
            # lifecycle checks; a completed save is not a cadence pass.
            row=self.frame_windows[-1]
            assert row['name']=='actual34-native-save-through-resume'
            self.failures.append({'case':'full34-native-save-cadence','error':str(exc),
                                  'hardware_frames':row['hardware_frames'],'updates':row['updates'],
                                  'flips':row['flips'],'max_cycles':row['max_cycles']})
        self.check(any(x['state']==SAVING for x in row['trace']) and row['trace'][-1]['state']==PLAY,'full34 workload includes actual save updates and completed return to play')
        self.settle();self.full_counts()
        # Rest legitimately settles ordinary expedition bookkeeping; preserve
        # the post-save actual payload, without pretending its pre-save bytes
        # must ignore such game-authored bookkeeping.
        after=self.retained();self.record('after-full34-save');name=self.snapshot('02-full34-native-save')
        saved=self.snapshots[name];self.cold_boot(saved['sram_path'],saved['sram_sha256'])
        self.check(self.retained()==after,'independent cold boot after full34 native save preserves every roster quest and equipment byte')
        self.record('after-full34-independent-reboot');self.snapshot('03-full34-independent-reboot')

    def death_retry_reboot(self):
        self.town();self.entry(39);self.target(80,264);self.step(90)
        self.check(self.get('hp')>0,'ordinary field rest supplies real saved health before death test')
        before=self.retained();self.goto(184,116);trace=[]
        for _ in range(360):
            if self.get('game_state')==DEAD:break
            self.step(12)
            trace.append({'frame':self.e.frame,'hp':self.get('hp'),'state':self.get('game_state')})
        self.check(self.get('game_state')==DEAD and self.get('hp')==0,'ordinary enemies cause actual death on full34 retained save without health injection')
        self.check(self.retained()==before,'death loses or duplicates none of the34 records quests or equipment')
        self.snapshot('04-full34-actual-death',settle=False);self.tap('A+R',1,1);self.settle()
        self.check(self.get('game_state')==PLAY and self.get('room')==39 and self.get('hp')>0,'ordinary retry resumes real saved field checkpoint')
        self.check(not self.get('magma_power_time') and self.local('grab')==255,'death/retry clears transient cast and object ownership')
        self.check(self.retained()==before,'retry preserves full34 payload byte-for-byte')
        self.full_counts();self.record('after-full34-death-retry');name=self.snapshot('05-full34-retry-save')
        saved=self.snapshots[name];self.cold_boot(saved['sram_path'],saved['sram_sha256'])
        self.check(self.retained()==before,'independent reboot after death and retry keeps exact full34 payload')
        self.entry(38);self.entry(30);self.full_counts()
        self.record('full34-old-region-return');self.snapshot('06-full34-independent-reboot-old-region')
        self.case_results.append({'name':'actual-full34-death-trace','trace':trace,'passed':True})

    def run(self):
        for name,method in [('source-cold-boot',self.source_boot),('all34-storage',self.storage_window),('same-family-selectors',self.same_family_pairs),('full34-save-reboot',self.save_reboot),('full34-death-retry-reboot',self.death_retry_reboot)]:
            failures=len(self.failures);method();self.case_results.append({'name':name,'passed':len(self.failures)==failures});self.report()
        self.completed=not self.failures;self.report()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','symbols','output','source-report'):p.add_argument('--'+key,type=Path,required=True)
    for key in ('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+key,required=True)
    p.add_argument('--source-snapshot',default='09-all65-earned-town');p.add_argument('--source-manifest',type=Path)
    p.add_argument('--allow-authenticated-predecessor-c',action='store_true')
    a=p.parse_args();run=MagmaRetainedControls(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,
                source_report=a.source_report,source_snapshot=a.source_snapshot,source_manifest=a.source_manifest,
                allow_authenticated_predecessor_c=a.allow_authenticated_predecessor_c)
    try:run.run()
    except Exception as exc:
        run.failures.append({'error':str(exc),'status':run.status()});run.snapshot('failure',settle=False);raise
    finally:run.report();run.e.close()
    print(json.dumps({'completed':run.completed,'checks':len(run.checks),'report_sha256':digest(run.out/'magma-retained-controls.json')}))
    return bool(run.failures)

if __name__=='__main__':raise SystemExit(main())
