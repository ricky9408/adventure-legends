#!/usr/bin/env python3
"""Run explicit content9 retained linked-engine and small old-native gates serially."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time,shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--adapter',type=Path,required=True);p.add_argument('--native-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();adapter=a.adapter.resolve();src=adapter/'source';out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 receipt=json.loads((adapter/'adapter-receipt.json').read_text());inputs=json.loads((adapter/'adapter-inputs.json').read_text());assert receipt['content_revision']==9
 def verify():
  assert all(sha(src/n)==h for n,h in inputs.items()),'Adapter input changed'
  assert all(sha(src/'build'/n)==h for n,h in receipt['candidate'].items()),'Paired candidate changed'
  assert all(sha(ROOT/n)==r['original_sha256']for n,r in receipt['changes'].items()),'Original helper changed'
 verify();report={'scope':__doc__,'candidate':receipt['candidate'],'adapter_receipt_sha256':sha(adapter/'adapter-receipt.json'),'runs':[],'finished':False,'host_scope':'Synthetic state plus real linked engine; no host audio/timing claim','native_scope':'Only explicitly listed controller/native scripts carry their own observed checks'}
 commands=[('migration9',[sys.executable,str(ROOT/'tools/check_retained_current9_migration.py'),'--adapter',str(adapter),'--native-report',str(a.native_report.resolve()),'--output',str(out/'migration9.json')])]
 names=['test_save_feedback.py','underwater_engine_review/test_legacy_deferred_anchor_current.py','underwater_engine_review/test_engine_lifecycle.py','underwater_engine_review/test_bounded_southern_rest.py','underwater_engine_review/test_bounded_magma_return.py','underwater_engine_review/test_bounded_magma_save_current.py','test_return_transactions.py','test_horizons_preflight_ownership.py']
 commands += [(Path(n).stem,[sys.executable,'tests/'+n])for n in names]
 for name in ('test_southern_enter_job','test_magma_boundaries'):
  for mode in ('strict','sanitized'):commands.append((name+'-'+mode,[sys.executable,'tests/'+name+'.py',*(['--sanitize']if mode=='sanitized'else[]),'--output',str(out/(name+'-'+mode+'.json'))]))
 commands += [(name,[sys.executable,'tests/'+name+'.py'])for name in ('playthrough','review_tests','exploration_tests')]
 for name,command in commands:
  verify();free=shutil.disk_usage(out).free
  if free<100*1024*1024:report['blocked_resource']={'next_command':command,'free_bytes':free};break
  env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','UNDERWATER_REVIEW_SOURCE':str(src),'UNDERWATER_REVIEW_MANIFEST':str(src/'build/source-hashes.json'),'PROBE_RESULT_NAME':str(out/(name+'.json')),'EMBERBOND_TEST_OUTPUT':str(out/'native-qa'),'EMBERBOND_REVIEW_OUTPUT':str(out/'native-review'),'EMBERBOND_PRIMARY_OUTPUT':str(out/'native-qa')}
  log=out/(name+'.log');row={'name':name,'command':command,'status':'RUNNING','log':log.name};report['runs'].append(row);(out/'run-status.json').write_text(json.dumps(report,indent=2)+'\n');start=time.monotonic()
  with log.open('w')as stream:r=subprocess.run(command,cwd=src,env=env,stdout=stream,stderr=subprocess.STDOUT)
  row.update(status='PASS'if r.returncode==0 else'FAIL',exit_code=r.returncode,seconds=round(time.monotonic()-start,3),log_sha256=sha(log));verify();row['inputs_and_candidate_unchanged']=True
  (out/'run-status.json').write_text(json.dumps(report,indent=2)+'\n');print(name,row['status'],flush=True)
 report['finished']='blocked_resource'not in report;report['all_passed']=report['finished']and all(r['status']=='PASS'for r in report['runs']);(out/'run-status.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['all_passed']else 1
if __name__=='__main__':raise SystemExit(main())
