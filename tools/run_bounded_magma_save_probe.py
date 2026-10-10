#!/usr/bin/env python3
"""Preserve all bounded Magma scheduler attempts; retry only proved map collisions."""
import argparse,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
from run_deferred_anchor_probe import run_attempts
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output',type=Path,default=ROOT/'build/current-host-evidence/bounded-magma-save')
 p.add_argument('--case',choices=('all','power-cuts'),default='all');a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=True);out=Path(tempfile.mkdtemp(prefix='run-',dir=a.output));attempts=[]
 expected=51 if a.case=='all' else 17
 command=[sys.executable,str(ROOT/'tests/underwater_engine_review/test_bounded_magma_save_current.py'),'--case',a.case]
 def run(n):
  env=dict(os.environ,PROBE_RESULT_NAME=str((out/f'attempt-{n:02}.json').resolve()))
  return subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True)
 def record(n,result,collision):
  for key,value in [('stdout',result.stdout),('stderr',result.stderr)]:
   (out/f'attempt-{n:02}-{key}.txt').write_text(value)
  row={'attempt':n,'returncode':result.returncode,'classified_heap_collision':collision}
  if result.returncode==0:
   report=out/f'attempt-{n:02}.json';data=json.loads(report.read_text())
   assert data['passed'] is True and data['sources_still_frozen'] is True
   assert data['selected_case']==a.case and len(data['checks'])==expected
   assert all(c['passed'] is True for c in data['checks'])
   row.update(passed_checks=expected,report_sha256=hashlib.sha256(report.read_bytes()).hexdigest())
  attempts.append(row);print('bounded Magma scheduler attempt',n,'exit',result.returncode,flush=True)
  if result.returncode and collision is None:print(result.stderr,file=sys.stderr)
 status=run_attempts(run,record)
 report={'scope':'Synthetic full-engine host scheduler integration; no controller, timing or pixel claim','case':a.case,'command':command,'returncode':status,'attempts':attempts,'maximum_attempts':3,'game_assertion_failure_retries':0,'forced_mappings':False}
 (out/'launcher-result.json').write_text(json.dumps(report,indent=2)+'\n');print('Evidence:',out/'launcher-result.json')
 return status
if __name__=='__main__':raise SystemExit(main())
