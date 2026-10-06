#!/usr/bin/env python3
"""Preserve every attempt; only proved pre-assertion heap collisions retry."""
from pathlib import Path
import sys, os, json, hashlib, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from run_deferred_anchor_probe import run_attempts
name=sys.argv[1] if len(sys.argv)>1 else 'test_legacy_deferred_anchor_linked.py'
expected_checks={'test_legacy_deferred_anchor_linked.py':27,'test_legacy_deferred_anchor_current.py':27,'test_engine_lifecycle.py':30,'test_bounded_magma_return.py':39,'test_bounded_southern_rest.py':51}
assert name in expected_checks, 'Unknown reviewed probe'
path=Path(__file__).resolve().parent/name
(ROOT/'build/underwater-engine-review').mkdir(parents=True,exist_ok=True)
output=Path(tempfile.mkdtemp(prefix=path.stem+'-',dir=ROOT/'build/underwater-engine-review'))
attempts=[]
def run(n):
 env=dict(os.environ);env['PROBE_RESULT_NAME']=str(output/f'attempt-{n:02}.json')
 return subprocess.run([sys.executable,str(path)],cwd=ROOT,env=env,text=True,capture_output=True)
def record(n,result,collision):
 for key,value in [('stdout',result.stdout),('stderr',result.stderr)]:
  (output/f'attempt-{n:02}-{key}.txt').write_text(value)
 row={'attempt':n,'returncode':result.returncode,'classified_heap_collision':collision}
 if result.returncode==0:
  report=output/f'attempt-{n:02}.json';data=json.loads(report.read_text())
  assert data['passed'] is True and len(data['checks'])==expected_checks[name]
  assert all(c['passed'] is True for c in data['checks'])
  row.update(passed_game_checks=len(data['checks']),report_sha256=hashlib.sha256(report.read_bytes()).hexdigest())
 attempts.append(row)
 print(f'{path.name} attempt {n}: exit {result.returncode}',flush=True)
 if result.returncode and collision is None:print(result.stderr,file=sys.stderr)
status=run_attempts(run,record)
(output/'launcher-result.json').write_text(json.dumps({'scope':'synthetic full-engine host integration, not GBA timing or native acquisition','returncode':status,'attempts':attempts,'maximum_attempts':3,'game_assertion_failure_retries':0,'forced_mappings':False},indent=2)+'\n')
print('Evidence:',output/'launcher-result.json')
raise SystemExit(status)
