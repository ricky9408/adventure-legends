#!/usr/bin/env python3
"""Source-locked independent host semantic review; no production source mutation."""
import hashlib,json,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tests'))
from test_underwater_save import prepare,runtime_hashes,FIXTURE,FIXTURE_SHA

def run(sanitize=False):
 before=runtime_hashes();assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==FIXTURE_SHA
 with tempfile.TemporaryDirectory(prefix='underwater-independent-review-') as d:
  d=Path(d);sources=prepare(d)
  for name,hook in [('save5','void review_preflight_serial(unsigned v){save5_preflight_cancel();preflight.generation=v;}'),('creatures','void review_admission_serial(unsigned v){creatures_admission_job_cancel();admission_job_serial=v;}')]:
   wrapper=d/(name+'-review.c');wrapper.write_text('#include "'+str(sources[name])+'"\n'+hook+'\n');sources[name]=wrapper
  flags=['-std=c99','-O2','-Wall','-Wextra','-Werror','-Wstrict-aliasing=2','-fstrict-aliasing','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-I'+str(ROOT/'src'),'-I'+str(d)]
  if sanitize:flags+=['-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']
  command=[os.environ.get('HOST_CC','cc')]+flags+[str(p) for p in sources.values()]+[str(ROOT/'tests/underwater_save_setup.c'),str(OUT/'review.c'),'-o',str(d/'review')]
  subprocess.run(command,check=True)
  start=time.monotonic();p=subprocess.run([str(d/'review')],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);seconds=time.monotonic()-start
  name='sanitizers' if sanitize else 'strict'
  (OUT/(name+'.log')).write_text(p.stdout+p.stderr)
  after=runtime_hashes();assert before==after,'Production include closure changed during review'
  evidence={'kind':'host synthetic semantic review; not native route or frame pacing','fixture_sha256':FIXTURE_SHA,'source_hashes':before,'test_source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'review.c',OUT/'admission_review.c',OUT/'run_review.py',OUT/'run_admission_review.py',ROOT/'tests/underwater_save_setup.c',ROOT/'tests/test_underwater_save.py']},'review_sha256':hashlib.sha256((OUT/'review.c').read_bytes()).hexdigest(),'compiler':subprocess.check_output([command[0],'--version'],text=True).splitlines()[0],'flags':flags,'sanitizer_environment':{'ASAN_OPTIONS':os.environ.get('ASAN_OPTIONS','')},'duration_seconds':seconds,'exit_code':p.returncode,'results':json.loads(p.stdout) if p.returncode==0 else None}
  (OUT/(name+'.json')).write_text(json.dumps(evidence,indent=2)+'\n');print(p.stdout,p.stderr,flush=True);assert p.returncode==0
if __name__=='__main__':run('--sanitize' in sys.argv)
