#!/usr/bin/env python3
"""Read-only native canary observation on the separate diagnostic ROM.
Cold SRAM imports only; no machine-state load, no game RAM writes.
This stack diagnostic does not assert candidate-A timing acceptance.
"""
from pathlib import Path
import argparse,hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from underwater_journey import UnderwaterJourney,PLAY,PAUSE
from northern_journey import newest_bank
CANARY=0xA55AC33C;BOTTOM=0x03007000;TOP=0x03007F00
DIAG=ROOT/'build/underwater-memory-diagnostic/build'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class ObservedJourney(UnderwaterJourney):
 def observe(self,label):
  values=[self.e.read(a,4) for a in range(BOTTOM,TOP,4)]
  changed=[i for i,v in enumerate(values) if v!=CANARY]
  lowest=BOTTOM+4*min(changed) if changed else TOP
  record={'label':label,'hardware_frame':self.e.frame,'status':self.status(),
   'retained_individuals':len(self.live()),'obtained_history':len(self.collection()),
   'lowest_overwritten_word_address':hex(lowest),'observed_overwritten_extent_bytes':TOP-lowest,
   'changed_word_bytes':4*len(changed),'unmodified_prefix_bytes':lowest-BOTTOM,
   'bottom_64_bytes_intact':all(v==CANARY for v in values[:16]),
   'true_minimum_sp':'not measured'}
  self.stack_observations.append(record);self.stack_report();print(json.dumps(record),flush=True)
  assert record['bottom_64_bytes_intact'],'Canary reached the reserved stack floor'
  return record
 def stack_report(self):
  report={'suite':'diagnostic-native-stack-canary','controller_only':True,'game_ram_writes':0,
   'startup_reserved_stack_fill_only':True,'cross_rom_machine_states_loaded':False,
   'source_pairing':self.stack_pairing,'observer_script_sha256':sha(Path(__file__)),'diagnostic_rom_sha256':sha(DIAG/'emberbond.gba'),
   'diagnostic_symbols_sha256':sha(DIAG/'emberbond.sym'),'diagnostic_elf_sha256':sha(DIAG/'emberbond.elf'),
   'diagnostic_source_manifest_sha256':sha(DIAG/'source-hashes.json'),
   'system_stack_range':[hex(BOTTOM),hex(TOP)],'reserved_bytes':TOP-BOTTOM,
   'canary_word':hex(CANARY),'observations':self.stack_observations,
   'timing_is_acceptance_evidence':False,'limitations':[
    'Overwritten extent is not true minimum SP: unused allocated slots can retain canary words, and matching writes can be invisible.',
    'Sampled path coverage and native emulator only, not an exhaustive call-graph or physical-hardware proof.',
    'Relocated diagnostic startup changes ROM addresses and boot timing; timing is not candidate-A evidence.',
    'No native 160-individual roster is fabricated; 160-capacity reasoning is static only.']}
  (self.out/'stack-observations.json').write_text(json.dumps(report,indent=2)+'\n')
 def snapshot(self,name,settle=True):
  if settle:self.settle()
  result=super().snapshot(name,settle=False)
  if hasattr(self,'stack_observations'):self.observe(name)
  return result
 def cadence(self,name,count=120,keys=None):
  self.settle();self.step(10);last=self.get('frame');page=self.e.read(0x04000000,2)&16;trace=[]
  for i in range(count):
   self.step(1,keys(i) if keys else 0);now=self.get('frame');newpage=self.e.read(0x04000000,2)&16
   trace.append({'delta':(now-last)&0xffffffff,'flip':newpage!=page,'cycles':self.get('render_cycles'),'state':self.get('game_state'),'obj_count':self.get('obj_count')});last,page=now,newpage
  result={'name':name,'hardware_frames':count,'updates':sum(t['delta'] for t in trace),'flips':sum(t['flip'] for t in trace),'max_cycles':max(t['cycles'] for t in trace),'trace':trace,'original_cadence_predicate_pass':all(t['delta']==1 and t['flip'] and t['cycles']<280896 for t in trace),'timing_is_candidate_acceptance_evidence':False}
  self.frame_windows.append(result);self.report()
  (self.out/'diagnostic-cadence-traces.json').write_text(json.dumps(self.frame_windows,indent=2)+'\n')
 def wait_evolution(self,target_state=7,require_ready=True,max_frames=180):
  # Keep exact functional state/phase boundary checks. Timing is deliberately
  # not gated for this relocated ROM, and no timing pass is reported.
  pairing=self.evolution_observer();trace=[];previous=(self.get('frame'),self.e.read(0x04000000,2)&16)
  for _ in range(max_frames+1):
   state=self.get('game_state');phase=self.e.read(pairing['address']+8)
   if state==target_state and phase==0:break
   self.check(state==7 and 1<=phase<=5,'stack diagnostic observes live evolution job')
   self.step(1);frame=self.get('frame');page=self.e.read(0x04000000,2)&16
   trace.append({'hardware_frame':self.e.frame,'update_delta':(frame-previous[0])&0xffffffff,'page_flip':page!=previous[1],'cycles':self.get('render_cycles'),'phase':self.e.read(pairing['address']+8),'state':self.get('game_state')});previous=(frame,page)
  if not hasattr(self,'diagnostic_evolution_traces'):self.diagnostic_evolution_traces=[]
  self.diagnostic_evolution_traces.append({'target_state':target_state,'trace':trace,'all_frames_meet_original_cadence_predicate':all(t['update_delta']==1 and t['page_flip'] and t['cycles']<280896 for t in trace)})
  (self.out/'diagnostic-evolution-traces.json').write_text(json.dumps({'timing_is_candidate_acceptance_evidence':False,'waits':self.diagnostic_evolution_traces},indent=2)+'\n')
  self.check(self.get('game_state')==target_state and self.e.read(pairing['address']+8)==0,'stack diagnostic reaches requested evolution boundary')
  if require_ready and target_state==7:self.check(self.get('progression_evolution_reason')==0,'earned evolution is ready')
  self.observe('evolution-boundary-'+str(target_state))
def main():
 global DIAG
 ap=argparse.ArgumentParser();ap.add_argument('--diagnostic-build',type=Path,default=DIAG);ap.add_argument('--source-rom-sha',default='0d7fd78733405a6fc8ec6eeca68ad207dfb11b91dcfe44a8d67f312552b46675');ap.add_argument('--source-report',type=Path);ap.add_argument('--snapshot');ap.add_argument('--scope',choices=['boot','tour','evolve-first','evolve-earned','full-collection'],default='tour');ap.add_argument('--evolve-source',type=int);ap.add_argument('--evolve-target',type=int);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();DIAG=a.diagnostic_build.resolve()
 receipt_path=DIAG.parent/'build-receipt.json'
 receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else json.loads((ROOT/'docs/underwater-memory/diagnostic-pairing.json').read_text())
 assert receipt['candidate_rom_sha256']==a.source_rom_sha,'Diagnostic is not paired with requested SRAM producer candidate'
 assert receipt['diagnostic_rom_sha256']==sha(DIAG/'emberbond.gba'),'Diagnostic ROM differs from build receipt'
 r=ObservedJourney(DIAG/'emberbond.gba',DIAG/'emberbond.sym',a.output,sha(DIAG/'emberbond.gba'),sha(DIAG/'emberbond.sym'),source_manifest=DIAG/'source-hashes.json')
 r.stack_observations=[];r.stack_pairing={'source':'authenticated delivered Magma revision5 SRAM','sram_sha256':sha(r.fixture),'expected_individuals':34,'expected_history':65}
 try:
  if a.source_report:
   report=json.loads(a.source_report.read_text());assert report['rom_sha256']==a.source_rom_sha
   assert report['controller_only'] and report['game_ram_writes']==0
   snap=report['snapshots'][a.snapshot];save=Path(snap['sram_path']);assert sha(save)==snap['sram_sha256']
   assert snap['rom_sha256']==report['rom_sha256']
   bank=newest_bank(save.read_bytes());assert int.from_bytes(bank[12:14],'little')==6
   r.stack_pairing={'source_report':str(a.source_report.resolve()),'source_report_sha256_at_import':sha(a.source_report),'source_rom_sha256':report['rom_sha256'],'snapshot':a.snapshot,'sram_sha256':sha(save),'content_revision':6,'save_wire_version':5,'expected_individuals':len(snap['owned_form_ids']),'expected_history':len(snap['obtained_form_ids'])}
   r.provenance={**r.stack_pairing,'cross_rom_machine_state_loaded':False,'import_method':'cold SRAM only, byte-identical persisted schema'}
   r.e.load_save(save);r.e.reset();r.step(150);r.tap('START',2,50);r.settle()
   r.check(r.get('game_state')==PLAY,'controller Continue reaches live gameplay from cold imported SRAM')
   r.check(len(r.live())==r.stack_pairing['expected_individuals'] and len(r.collection())==r.stack_pairing['expected_history'],'cold import retains exact earned roster and histories')
  else:r.boot_magma()
  r.observe('cold-continue')
  if a.scope!='boot':
   if r.get('room')==38:r.enter_underwater()
   for tab in range(5):
    r.open_tab(tab);r.step(90);r.observe('journal-tab-'+str(tab));r.close_menu()
   r.target(80,256);r.observe('checkpoint-save-transaction')
   cast_form=next(c.form_id for c in r.live() if 49<=c.form_id<=72)
   r.cast_position(cast_form,176,184,1,67+cast_form-49,'diagnostic-real-cast');r.observe('real-field-cast')
   if a.scope=='evolve-earned':
    assert a.evolve_source and a.evolve_target,'Specify an already earned source and target'
    r.evolve_underwater(a.evolve_source,a.evolve_target)
   if a.scope in ('evolve-first','full-collection'):
    if a.scope=='full-collection':r.collection_route()
    else:
     identity,idx=r.start_underwater_trial(49,1);r.solve_underwater_trial(idx)
     r.check(r.selected().instance_id==identity and r.selected().trial_flags&1,'real first trial proof earned by controller')
     r.observe('earned-trial-transaction');r.evolve_underwater(49,50)
   r.snapshot('diagnostic-finished')
  r.stack_report()
 except Exception as exc:
  r.failures.append({'error':str(exc),'status':r.status()});r.observe('failure');raise
 finally:r.report();r.stack_report();r.e.close()
if __name__=='__main__':main()
