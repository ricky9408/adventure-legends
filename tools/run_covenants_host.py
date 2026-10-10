#!/usr/bin/env python3
"""Run current content9 host gates against a fixed runtime build receipt.

Synthetic host, geometry, sanitizer and isolated ARM object evidence only.
Native controller acquisition, frame pacing and audio need separate gates.
Previous output directories/files are preserved before this aggregate.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 manifest=ROOT/'build/source-hashes.json';runtime=json.loads(manifest.read_text())
 # These concurrent native-only observers are never loaded by this host suite.
 native_only={'tests/covenants_core_prelude.py','tests/covenants_journey.py','tests/covenants_engine_diagnostic.py','tests/covenants_visual_review.py','tools/run_covenants_native.py','tools/run_covenants_acceptance.py','tests/observe_covenants_stack.py','tools/prepare_covenants_retained_adapter.py'}
 helpers={str(p.relative_to(ROOT)):sha(p)for base in ('tests','assets','tools')for p in (ROOT/base).rglob('*.py')if 'sysroot' not in p.parts and str(p.relative_to(ROOT)) not in native_only}
 def unchanged():return all(sha(ROOT/k)==v for k,v in {**runtime,**helpers}.items())
 assert unchanged(),'Runtime does not match the candidate receipt'
 prior=out/'prior-evidence';prior.mkdir();moved=[]
 for name in ('covenants-art-host','covenants-powers-host','covenants-practice-geometry','covenants-world-review','covenants-geometry-review'):
  source=ROOT/'build'/name
  if source.exists():assert source.is_dir() and not source.is_symlink();source.rename(prior/name);moved.append(str(source.relative_to(ROOT)))
 for name in ('build/covenants-engine-host.json','build/covenants-camera-host.json','build/covenants-presentation-host.json','build/story-rewards-host.json','docs/evidence/covenants-save-powerloss.json'):
  source=ROOT/name
  if source.is_file():dest=prior/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
 (ROOT/'docs/evidence').mkdir(parents=True,exist_ok=True)
 names=['test_covenants_catalog','test_covenants_history','test_covenants_transactions','test_covenants_powerloss','test_covenants_sanitizers','test_covenants_art','test_covenants_creature_art','test_covenants_camera','test_covenants_engine','test_covenants_field_dispatch','test_covenants_presentation','test_covenants_party_notice','test_covenants_world','test_covenants_powers','test_covenants_practice_geometry','check_covenants_geometry','check_covenants_world_arm','check_covenants_field_feasibility','test_story_rewards','test_story_reward_finish']
 commands=[([sys.executable,'tests/'+name+'.py'],{})for name in names]
 asan=subprocess.check_output(['cc','-print-file-name=libasan.so'],text=True).strip();assert Path(asan).is_file()
 commands += [([sys.executable,'tests/test_covenants_world.py'],{'COVENANTS_WORLD_SANITIZE':'1','LD_PRELOAD':asan}),([sys.executable,'tests/check_covenants_geometry.py','--sanitize'],{})]
 report={'scope':__doc__,'result':'RUNNING','runtime_manifest_sha256':sha(manifest),'candidate':{n:sha(ROOT/'build'/n)for n in ('emberbond.gba','emberbond.elf','emberbond.sym')},'helpers_sha256':helpers,'excluded_unexecuted_native_observers':sorted(native_only),'preserved_prior_directories':moved,'runs':[]}
 def save():(out/'run-status.json').write_text(json.dumps(report,indent=2)+'\n')
 save()
 for i,(cmd,extra)in enumerate(commands):
  assert unchanged(),'Runtime/helper changed between commands'
  log=out/(f'{i:02d}-'+Path(cmd[1]).stem+'.log');start=time.monotonic();row={'command':cmd,'environment_overrides':extra,'log':log.name,'status':'RUNNING'};report['runs'].append(row);save()
  with log.open('w')as f:result=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1',**extra})
  row.update(exit_code=result.returncode,seconds=round(time.monotonic()-start,3),log_sha256=sha(log),runtime_and_helpers_unchanged=unchanged());row['status']='PASS'if not result.returncode and row['runtime_and_helpers_unchanged']else'FAIL'
  print(log.name,row['status'],flush=True);save()
  if not row['runtime_and_helpers_unchanged']:report['result']='FAIL';save();return 1
 report['result']='PASS'if all(r['status']=='PASS'for r in report['runs'])else'FAIL';save();return report['result']!='PASS'
if __name__=='__main__':raise SystemExit(main())
