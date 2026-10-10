#!/usr/bin/env python3
"""Return E startup-only native stack-canary observations, never timing acceptance.

Cold SRAM may cross the paired production/diagnostic ROM boundary. No machine
state is imported or restored and the inherited bridge rejects game RAM writes.
"""
from pathlib import Path
import argparse, json, struct, traceback
from return_journey import ReturnJourney, ROOT, digest, ReadOnlyGameEmulator, PLAY
from return_followup_diagnostics import Followup
from return_collection_route import TRIALS
from northern_journey import newest_bank
from verify_return_memory_e import D_SHA, M_SHA
BOTTOM,TOP,CANARY=0x03007000,0x03007f00,0xa55ac33c
class StackJourney(Followup):
    travel=Followup.travel
    entry=Followup.entry
    mask=Followup.mask
    leave_interior=Followup.leave_interior
    def __init__(self,args):
        d=args.diagnostic.resolve();self.stack_pairing=json.loads((d/'build-receipt.json').read_text())
        assert self.stack_pairing['candidate_rom_sha256']==D_SHA and self.stack_pairing['candidate_source_manifest_sha256']==M_SHA
        assert digest(d/'control/control.gba')==D_SHA
        assert self.stack_pairing['runtime_source_changes']==['src/startup.s']
        assert digest(d/'build/emberbond.gba')==self.stack_pairing['diagnostic_rom_sha256']
        assert digest(d/'build/source-hashes.json')==self.stack_pairing['diagnostic_source_manifest_sha256']
        self.stack_observations=[];self.source_producer=None;self.boot_epoch=0
        super().__init__(d/'build/emberbond.gba',d/'build/emberbond.sym',args.output,
            digest(d/'build/emberbond.gba'),digest(d/'build/emberbond.sym'),digest(d/'build/emberbond.elf'),
            d/'build/source-hashes.json',digest(d/'build/source-hashes.json'),source_root=d,timing_mode='stack-diagnostic-no-release-timing')
        # Only this relocated canary observer excludes the production cadence gate.
        self.close_global_trace()
        self.global_enabled=False
        self.global_native.update(enabled=False,diagnostic_only=True,timing_is_release_acceptance_evidence=False,exclusion='Startup-only canary ROM is not a release timing measurement')
    def observe(self,label):
        values=struct.unpack('<960I',self.e.bytes(BOTTOM,TOP-BOTTOM));changed=[i for i,x in enumerate(values) if x!=CANARY]
        lowest=BOTTOM+4*min(changed) if changed else TOP
        record={'label':label,'boot_epoch':self.boot_epoch,'hardware_frame':self.e.frame,'status':self.status(),
            'retained_individuals':len(self.live()),'obtained_histories':len(self.collection()),
            'lowest_overwritten_word':hex(lowest),'overwritten_extent_bytes':TOP-lowest,'changed_word_bytes':4*len(changed),
            'unmodified_prefix_bytes':lowest-BOTTOM,'bottom_64_bytes_intact':all(v==CANARY for v in values[:16]),'true_minimum_sp':'not measured'}
        self.stack_observations.append(record);self.stack_report();print(json.dumps(record),flush=True)
        self.check(record['bottom_64_bytes_intact'],'sampled startup canary bottom guard remains unchanged')
    def stack_report(self):
        data={'suite':'return-e-native-stack-canary','controller_only':True,'game_ram_writes':0,'machine_state_loads':self.machine_state_loads,
            'startup_only_reserved_stack_fill':True,'system_stack_range':[hex(BOTTOM),hex(TOP)],'reserved_bytes':TOP-BOTTOM,'canary_word':hex(CANARY),
            'production_pairing':self.stack_pairing,'diagnostic':self.candidate,'diagnostic_source_manifest_sha256':self.source_manifest_sha,
            'helper_sources':self.test_sources,'observer_script_sha256':digest(Path(__file__)),'source_sram':self.provenance,'source_producer':self.source_producer,'persisted_source_proof':getattr(self,'persisted_source_proof',None),
            'finished_scope':self.finished_scope,'observations':self.stack_observations,'timing_is_release_acceptance_evidence':False,
            'limitations':['Overwrite extent is not true minimum SP: unused allocated slots can retain canary, and writes equal to the canary are invisible.',
                'Finite controller-path observations in native emulator, not an exhaustive call-chain or physical-hardware proof.',
                'Startup relocation changes code addresses and timing; no diagnostic timing is release evidence.',
                'No fabricated 160-person roster; capacity stack observations are not claimed.',
                'Each observation is cumulative only within its own cold boot epoch; upper 256 bytes, SVC/IRQ/BIOS stack are excluded.']}
        (self.out/'stack-observations.json').write_text(json.dumps(data,indent=2)+'\n')
    def measured(self,name,callback,cold_continue=False,strict=True):
        # The production harness and its acceptance predicate stay untouched.
        # This subclass retains every trace but deliberately has no timing gate.
        result=super().measured(name,callback,cold_continue=False,strict=False)
        self.frame_windows[-1]['diagnostic_only']=True
        self.frame_windows[-1]['timing_is_release_acceptance_evidence']=False
        self.frame_windows[-1]['cold_continue_observation']=cold_continue
        if cold_continue:self.check(self.get('game_state')==PLAY and not self.get('save_failed'),name+' reaches live play with no save failure')
        self.observe(name);return result
    def snapshot(self,name,settle=True):
        result=super().snapshot(name,settle);self.observe(result);return result
    def restore(self,name):raise AssertionError('Machine-state imports/restores are forbidden in the canary observer')
    def wait_evolution(self,target_state=7,require_ready=True,max_frames=180):
        pairing=self.evolution_observer();trace=[]
        for _ in range(max_frames+1):
            state=self.get('game_state');phase=self.e.read(pairing['address']+8)
            if state==target_state and phase==0:break
            self.check(state==7 and 1<=phase<=5,'diagnostic observes actual evolution preparation/commit phase')
            self.step(1);trace.append({'frame':self.e.frame,'state':self.get('game_state'),'phase':self.e.read(pairing['address']+8),'cycles':self.get('render_cycles')})
        self.check(self.get('game_state')==target_state and self.e.read(pairing['address']+8)==0,'actual evolution reaches requested state')
        if require_ready and target_state==7:self.check(self.get('progression_evolution_reason')==0,'earned evolution is genuinely ready')
        self.cases.append({'diagnostic_evolution_target_state':target_state,'trace':trace,'timing_is_release_acceptance_evidence':False})
        self.observe('actual-evolution-boundary-'+str(target_state))
    def import_sram(self,args):
        path=args.producer_report.resolve();assert digest(path)==args.producer_sha
        producer=json.loads(path.read_text())
        prior_d=producer['rom_sha256']=='d9e08d5e45f9df259305503f4f10be0ba56dc5db0e1265613aee630ab7a25cb3'
        if prior_d:
            assert args.allow_prior_d_sram, 'Earlier-candidate source SRAM needs the explicit supplemental scope'
            assert producer['source_manifest_sha256']=='162acf8e09a78b4a201bbd9bc28a1511d1eedb3896c5e536e56f41b20cf6e0c1'
            prior_root=ROOT/'build/return-collision-d1-source';current_root=ROOT/'build/return-boundary-e-source'
            before=json.loads((prior_root/'build/source-hashes.json').read_text());after=json.loads((current_root/'build/source-hashes.json').read_text())
            assert digest(prior_root/'build/source-hashes.json')==producer['source_manifest_sha256']
            assert digest(current_root/'build/source-hashes.json')==M_SHA
            assert all(digest(prior_root/name)==h for name,h in before.items()) and all(digest(current_root/name)==h for name,h in after.items())
            changed=[name for name in before if before[name]!=after.get(name)]
            assert changed==['src/game.c','src/return_engine.inc','src/underwater_engine.inc']
            assert sorted(set(after)-set(before))==['src/modal_blit.inc'] and not set(before)-set(after)
            self.persisted_source_proof={'prior_candidate':'D','current_candidate':'E','D_manifest_sha256':producer['source_manifest_sha256'],'E_manifest_sha256':M_SHA,'changed_existing_files':changed,'added_files':['src/modal_blit.inc'],'unchanged_files':len(before)-len(changed),'save_codecs_catalogs_structures_unchanged':True,'source_scope':'Genuinely controller-earned D SRAM, not a fresh E acquisition producer'}
        else:
            assert producer['rom_sha256']==D_SHA and producer['source_manifest_sha256']==M_SHA
        assert producer['finished_scope']=='full' and not producer['failures'] and producer['controller_only'] and not producer['game_ram_writes'] and not producer['machine_state_loads']
        assert not producer['provenance']['cross_rom_machine_state_loaded']
        saved=producer['snapshots'][args.snapshot];sram=Path(saved['sram_path']);assert digest(sram)==saved['sram_sha256']
        assert saved['rom_sha256']==producer['rom_sha256']
        self.source_producer={'report':str(path),'report_sha256':args.producer_sha,'snapshot':args.snapshot,'sram_sha256':digest(sram),'source_helper_manifest_sha256':digest(path.parent/'helper-source-hashes.json')}
        self.e.close();self.e=ReadOnlyGameEmulator(self.rom);self.e.load_save(sram);self.e.reset();self.boot_epoch+=1
        self.provenance={'fixture_path':str(sram),'sram_sha256':digest(sram),'source_rom_sha256':producer['rom_sha256'],'cross_rom_machine_state_loaded':False}
        self.source_bank=newest_bank(sram.read_bytes());self.step(150);self.observe('cold-current7-title')
        self.measured('cold-current7-continue',lambda:(self.tap('START',2,90),self.settle()),cold_continue=True)
        bank=newest_bank(self.e.bytes(0x0e000000,32768))
        self.check(bank[32:]==self.source_bank[32:],'cold SRAM Continue preserves imported current7 payload')
        self.check(self.collection()==saved['obtained_form_ids'] and len(self.live())==len(saved['individuals']),'import retains authenticated producer counts')
        self.snapshot('cold-current7-import')
    def menus(self):
        for tab in range(10):self.measured('journal-tab-'+str(tab),lambda tab=tab:(self.open_tab(tab),self.tap('DOWN',2,4),self.tap('UP',2,4),self.close_menu()))
        self.coverage.append('all10-old-and-new-journal-tabs')
    def old_magma_repeat(self):
        self.travel(39,clear=True);self.goto(80,248,radius=4);self.face(1);self.step(120)
        previous={c.instance_id:bytes(c) for c in self.live()};history=self.collection()
        self.measured('old-magma-repeat37-real-event-save',lambda:(self.tap('A',2,120),self.settle(),self.tap('A',2,120),self.settle()))
        fresh=[c for c in self.live() if c.instance_id not in previous]
        self.check(len(fresh)==1 and fresh[0].form_id==37,'actual old Magma repeat adds one earned individual')
        self.check(all(bytes(c)==previous[c.instance_id] for c in self.live() if c.instance_id in previous),'old repeat preserves prior individuals')
        self.check(self.collection()==history,'old repeat adds no duplicate history');self.snapshot('old-magma-repeat37-earned')
    def run_stack(self,args):
        if args.producer_report:self.import_sram(args)
        else:self.boot()
        self.menus()
        if args.scope=='tour':
            self.initialize_return();self.travel(54);self.snapshot('return-first-events-and-rest')
            identity,slot=self.begin_return_trial(0);old=self.roster().instances[slot].trial_flags
            self.solve_return_trial(0);self.check(self.roster().instances[slot].trial_flags!=old,'actual Return trial0 earns individual proof')
            self.snapshot('return-trial0-earned');self.evolve_return(2,3,identity,slot)
        elif args.scope=='evolve':
            source,target=int(args.evolve_source),int(args.evolve_target);self.owned_select(source)
            identity=self.selected().instance_id;slot=self.roster().party[self.roster().selected_party]
            self.evolve_return(source,target,identity,slot)
        elif args.scope=='final':
            self.check(len(self.collection())==104 and len(self.live())==52,'final controller fixture genuinely contains104/52')
            self.travel(54);self.target(72,256);self.snapshot('final104-52-return-rest-save')
            for form,command in ((3,1),(102,102),(104,104)):
                self.owned_select(form);self.set_command(command);self.ready();self.measured('final-real-power-'+str(form),lambda:(self.tap('R'),self.settle()))
        self.old_magma_repeat();self.finished_scope=args.scope;self.verify_closures();self.report();self.observe('finished-'+args.scope)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--diagnostic',type=Path,default=Path('/tmp/return-e-memory-diagnostic'));p.add_argument('--output',type=Path,required=True)
    p.add_argument('--scope',choices=('tour','evolve','final'),default='tour');p.add_argument('--producer-report',type=Path);p.add_argument('--producer-sha');p.add_argument('--snapshot');p.add_argument('--evolve-source',type=int);p.add_argument('--evolve-target',type=int)
    p.add_argument('--allow-prior-d-sram',action='store_true',help='Supplemental SRAM only after exact frozen D/E source comparison; never fresh E acceptance')
    args=p.parse_args();r=StackJourney(args)
    try:r.run_stack(args)
    except Exception as e:r.failures.append({'error':str(e),'traceback':traceback.format_exc(),'status':r.status()});r.snapshot('failure',settle=False);raise
    finally:r.report();r.stack_report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
