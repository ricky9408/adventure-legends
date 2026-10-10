#!/usr/bin/env python3
"""Summarize exact accepted G evidence; this is not a test runner.
Full reports/traces stay under ignored build/. This bounded public index pins
those bytes and retains case detail, rather than copying enormous trace files.
"""
from pathlib import Path
import gzip,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
ROM='6db7ebbbe452b69606addabc6f07a322c00bc5d47df9103875483ad135fe6608'
MANIFEST='588ef3b212730660ea79e1bef183a60767e01b370f913f205837b3e011c540a4'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def main():
 out=ROOT/'docs/evidence/return-g-release';out.mkdir(parents=True,exist_ok=True)
 def emit(name,value):
  data=(json.dumps(value,indent=2)+'\n').encode();assert len(data)<90000,(name,len(data));(out/name).write_bytes(data)
 native=ROOT/'build/return-native-g-global-01';status=read(native/'run-status.json');verified=read(native/'verification-receipt.json')
 assert status['finished'] and status['all_requested_stages_passed'] and status['runtime_closure_still_exact'] and status['helper_closure_still_exact']
 assert verified['run_status_sha256']==sha(native/'run-status.json') and verified['all_stages_passed'] and verified['zero_strict_exceptions']
 assert status['candidate']['rom_sha256']==ROM and verified['source_manifest_sha256']==MANIFEST
 assert len(status['stages'])==len(verified['stages'])==6
 for stage,check in zip(status['stages'],verified['stages']):
  assert stage['state']=='passed' and stage['exit_code']==0 and stage['name']==check['stage']
  path=Path(stage['report']);assert sha(path)==stage['report_sha256']==check['report_sha256']
  emit('native-'+stage['name']+'.json',dict(check,report=str(path.relative_to(ROOT)),scope='Controller route; exact loader exclusions and raw trace hashes retained in the original report'))
 emit('native-recipe.json',dict(verified,run_status_sha256=sha(native/'run-status.json'),scope='Six separately recorded exact-G stages; overlapping gameplay coverage is not a unique-scenario total'))
 p=ROOT/'build/return-companion-g-all/companion-controls.json';d=read(p)
 assert d['stage']=='finished-all' and d['controller_only'] and not d['game_ram_writes'] and not d['machine_state_loads'] and not d['failures'] and not d['cadence']['exceptions']
 assert d['rom_sha256']==ROM and d['source_manifest_sha256']==MANIFEST and len(d['art_cases'])==len(d['combat_cases'])==15 and len(d['control_cases'])==11
 trace=p.parent/d['native_frame_capture'];case_files={}
 for kind in ('art','combat','control'):
  case_files[kind]=[]
  for i,case in enumerate(d[kind+'_cases']):
   name='companion-'+kind+'-'+str(i).zfill(2)+'.json';emit(name,case);case_files[kind].append(name)
 emit('companions.json',dict(scope='Real G-earned cold SRAM; complete case detail is split into bounded files. Full raw reports and trace remain reproducible under build/',report_sha256=sha(p),trace_sha256=sha(trace),cadence=d['cadence'],checks=len(d['checks']),case_files=case_files,game_ram_writes=0,machine_state_loads=0,rom_sha256=ROM,source_manifest_sha256=MANIFEST))
 for image in p.parent.glob('*.png'):
  target=out/'companion-images'/image.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(image,target)
 p=ROOT/'build/return-guard-g/guard-exclusions.json';d=read(p);assert not d['failures'] and d['source_closure_verified_before_and_after'] and d['ROM_sha256']==ROM and len(d['cases'])==6
 cases=[]
 for c in d['cases']:
  assert not c['cadence_exceptions'];cases.append({k:c[k] for k in ('command','source','synthetic_scene_setup','projectiles_written','power_private_state_written','actual_engine_generated_projectiles','guard_used','maximum_cycles')})
 emit('guard-exclusions.json',dict(scope='Synthetic public scene/roster setup; real engine-generated shots. Not earned acquisition, art acceptance or physical hardware.',report_sha256=sha(p),rom_sha256=ROM,source_manifest_sha256=MANIFEST,cases=cases,active_frames=sum(len(c['cadence'])for c in d['cases'])))
 observations=[];checks=frames=0
 for name in ('return-memory-g-tour-02','return-memory-g-final','return-memory-g-evolve'):
  base=ROOT/'build'/name;d=read(base/'stack-observations.json');r=read(base/'return-journey.json')
  assert not r['failures'] and not d['game_ram_writes'] and not d['machine_state_loads'] and d['finished_scope'] in ('tour','final','evolve')
  assert d['production_pairing']['candidate_rom_sha256']==ROM and d['production_pairing']['control_byte_identical_to_candidate'] and d['production_pairing']['runtime_source_changes']==['src/startup.s']
  checks+=len(r['checks']);frames+=d['observations'][-1]['hardware_frame']
  emit('memory-'+d['finished_scope']+'.json',dict(scope='Startup-only canary diagnostic, not release pacing or true minimum SP',original_report_sha256=sha(base/'stack-observations.json'),controller_report_sha256=sha(base/'return-journey.json'),pairing=d['production_pairing'],observations=d['observations'],game_ram_writes=0,machine_state_loads=0,limitations=d['limitations']))
  observations+=d['observations']
 emit('memory-summary.json',dict(rom_sha256=ROM,native_frames=frames,functional_checks=checks,samples=len(observations),maximum_overwritten_extent=max(x['overwritten_extent_bytes']for x in observations),minimum_unmodified_prefix=min(x['unmodified_prefix_bytes']for x in observations),bottom_guards_intact=all(x['bottom_64_bytes_intact']for x in observations),upper_256_bytes_not_measured=True,true_minimum_sp_measured=False,physical_hardware_tested=False,preserved_failed_observer_setup='build/return-memory-g-tour/observer-setup-failure.json'))
 for name in ('memory-budget.json','link-limit-probes.json','diagnostic-build-receipt.json'):
  source=ROOT/'docs/return-memory-candidate-G'/name;shutil.copyfile(source,out/name)
 raw=(ROOT/'docs/return-memory-candidate-G/stack-usage.tsv').read_bytes();(out/'stack-usage.tsv.gz').write_bytes(gzip.compress(raw,9,mtime=0))
 emit('stack-usage-encoding.json',dict(raw_sha256=hashlib.sha256(raw).hexdigest(),gzip_sha256=sha(out/'stack-usage.tsv.gz'),raw_bytes=len(raw),encoding='deterministic gzip; restore exact TSV with standard gzip'))
 pixel=read(ROOT/'build/return-modal-portable-g/comparison.json');assert pixel['after_rom']==ROM and not pixel['failures'] and pixel['cases']==3499;emit('pixel-regression.json',pixel)
 retained=ROOT/'docs/evidence/return-retained-gates-g.json';emit('retained-index-reference.json',dict(path=str(retained.relative_to(ROOT/'docs')),sha256=sha(retained),scope='Separate exact-G retained index; historical and current linked contracts retain distinct scope'))
 generator=ROOT/'build/return-generator-reproduction';before=read(generator/'before-hashes.json');after={str(p.relative_to(generator)):sha(p)for name in ('assets','src')for p in (generator/name).rglob('*')if p.is_file()and '__pycache__'not in p.parts};assert before==after
 emit('asset-regeneration.json',dict(scope='Independent complete make assets with copied editable inputs, design references, tools and generated files',files=len(before),changed_files=0,new_files=0,exit_code=0,original_manifest_sha256=sha(generator/'before-hashes.json'),log_sha256=sha(ROOT/'build/return-generator-reproduction-02.log'),preserved_initial_setup_failure='build/return-generator-reproduction/attempt-01-receipt.json'))
 manifest={str(p.relative_to(out)):dict(bytes=p.stat().st_size,sha256=sha(p))for p in out.rglob('*')if p.is_file()and p.name!='CHECKSUMS.json'};emit('CHECKSUMS.json',dict(scope=__doc__,files=manifest));print('Packaged',len(manifest),'bounded evidence files')
if __name__=='__main__':main()
