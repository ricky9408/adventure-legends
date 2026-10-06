#!/usr/bin/env python3
"""Run the synthetic probe, retaining narrowly classified host-heap collisions.

Only EEXIST with a proved overlapping Python heap, before any game assertion,
permits at most two fresh-process retries. Game failures, permission errors,
unknown setup failures and malformed diagnostics are never retried or hidden.
No mapping is overwritten, no protection or ASLR setting is changed.
"""
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
PREFIX='DEFERRED_PROBE_SETUP_FAILURE_JSON='
ADDRESSES={0x04000000,0x05000000,0x06000000,0x07000000}

def collision_detail(result):
 if result.returncode!=78:return None
 lines=[line[len(PREFIX):] for line in result.stderr.splitlines() if line.startswith(PREFIX)]
 if len(lines)!=1:return None
 try:d=json.loads(lines[0])
 except (TypeError,ValueError):return None
 if not isinstance(d,dict):return None
 if d.get('kind')!='synthetic-address-reservation' or d.get('errno')!=errno.EEXIST:return None
 if d.get('game_assertions_started') is not False or d.get('overwritten_mappings') is not False:return None
 address=d.get('address');length=d.get('length');count=d.get('mapped_before_failure')
 if type(address) is not int or address not in ADDRESSES or length!=0x20000:return None
 if type(count) is not int or count!=sorted(ADDRESSES).index(address):return None
 overlaps=d.get('overlaps')
 if not isinstance(overlaps,list):return None
 if not any(isinstance(row,dict) and row.get('tag')=='[heap]' and
            type(row.get('start')) is int and type(row.get('end')) is int and
            row['start']<address+length and row['end']>address for row in overlaps):return None
 return d

def run_attempts(run,record,max_attempts=3):
 assert 1<=max_attempts<=3
 for n in range(1,max_attempts+1):
  result=run(n);collision=collision_detail(result)
  record(n,result,collision)
  if result.returncode==0:return 0
  if collision is None or n==max_attempts:return result.returncode
 raise AssertionError('unreachable')

def main():
 build=ROOT/'build';build.mkdir(exist_ok=True)
 output=Path(tempfile.mkdtemp(prefix='deferred-anchor-probe-',dir=build))
 attempts=[]
 def run(n):
  env=dict(os.environ);env['PROBE_RESULT_NAME']=str(output/f'attempt-{n:02}.json')
  return subprocess.run([sys.executable,str(ROOT/'docs/evidence/deferred-anchor/test_engine_probe.py')],
                        cwd=ROOT,env=env,text=True,capture_output=True)
 def record(n,result,collision):
  for name,data in (('stdout',result.stdout),('stderr',result.stderr)):
   (output/f'attempt-{n:02}-{name}.txt').write_text(data)
  row={'attempt':n,'returncode':result.returncode,'classified_heap_collision':collision,
       'stdout_sha256':hashlib.sha256(result.stdout.encode()).hexdigest(),
       'stderr_sha256':hashlib.sha256(result.stderr.encode()).hexdigest()}
  report=output/f'attempt-{n:02}.json'
  if result.returncode==0:
   data=json.loads(report.read_text());assert data['passed'] is True and len(data['checks'])==27
   assert all(c['passed'] is True for c in data['checks'])
   row.update(report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),passed_game_checks=27)
  attempts.append(row)
  print(f'Synthetic deferred-anchor attempt {n}: exit {result.returncode}'+(' (proved host heap overlap; fresh-process retry allowed)' if collision else ''),flush=True)
  if result.returncode and collision is None:print(result.stderr,file=sys.stderr)
 status=run_attempts(run,record)
 receipt={'scope':'Synthetic host integration, not native GBA timing or acquisition',
          'returncode':status,'attempts':attempts,'maximum_attempts':3,
          'game_assertion_failure_retries':0,'forced_mappings':False}
 (output/'launcher-result.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print('Evidence:',output/'launcher-result.json')
 return status
if __name__=='__main__':raise SystemExit(main())
