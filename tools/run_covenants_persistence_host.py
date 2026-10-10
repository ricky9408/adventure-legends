#!/usr/bin/env python3
"""Reproducible final-chapter host gate, with exact runtime source binding."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from covenants_host_support import runtime_hashes
SUITES=['tools/check_covenants_history.py','tests/test_covenants_transactions.py','tests/test_covenants_history.py','tests/test_covenants_sanitizers.py','tests/test_covenants_powerloss.py']
def main():
 output=ROOT/'docs/evidence/covenants-persistence-host';output.mkdir(parents=True,exist_ok=True)
 sources=runtime_hashes();results=[]
 for name in SUITES:
  log=output/(Path(name).stem+'.log');start=time.monotonic()
  with log.open('w') as f:run=subprocess.run([sys.executable,str(ROOT/name)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
  results.append({'suite':name,'exit_code':run.returncode,'seconds':round(time.monotonic()-start,3),'log':str(log.relative_to(ROOT)),'sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'suite_script_sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()})
  print(name,'PASS' if not run.returncode else 'FAIL',flush=True)
  if run.returncode:break
 unchanged=runtime_hashes()==sources
 report={'scope':'Synthetic host persistence/catalog contracts only; final chapter controller obtainability, world/native performance and physical hardware remain pending','result':'PASS' if len(results)==len(SUITES) and all(x['exit_code']==0 for x in results) and unchanged else 'FAIL','source_sha256':sources,'source_unchanged':unchanged,'suites':results,'oracle_manifest_sha256':hashlib.sha256((ROOT/'tests/fixtures/horizons-c-policy-oracle/manifest.json').read_bytes()).hexdigest(),'generator_inputs_manifest_sha256':hashlib.sha256((ROOT/'tests/fixtures/horizons-c-policy-oracle/generator-inputs-manifest.json').read_bytes()).hexdigest()}
 (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
 if report['result']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
