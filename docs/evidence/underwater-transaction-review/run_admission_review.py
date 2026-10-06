#!/usr/bin/env python3
import hashlib,json,os,subprocess,sys,tempfile,time
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from test_underwater_save import runtime_hashes
before=runtime_hashes();sanitize='--sanitize' in sys.argv
with tempfile.TemporaryDirectory(prefix='independent-core-review-') as d:
 flags=['-std=c99','-O2','-Wall','-Wextra','-Werror','-Wstrict-aliasing=2','-fstrict-aliasing','-ffreestanding','-fno-builtin','-I'+str(ROOT/'src')]
 if sanitize:flags+=['-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']
 subprocess.run(['cc',*flags,str(ROOT/'src/creatures.c'),str(ROOT/'src/creature_data.c'),str(OUT/'admission_review.c'),'-o',d+'/review'],check=True)
 t=time.monotonic();r=subprocess.run([d+'/review'],capture_output=True,text=True);elapsed=time.monotonic()-t
 assert before==runtime_hashes()
 name='admission-sanitizers' if sanitize else 'admission-strict'
 (OUT/(name+'.log')).write_text(r.stdout+r.stderr)
 result={'kind':'independent host synthetic bounded core review','source_hashes':before,'test_source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'review.c',OUT/'admission_review.c',OUT/'run_review.py',OUT/'run_admission_review.py',ROOT/'tests/underwater_save_setup.c',ROOT/'tests/test_underwater_save.py']},'review_sha256':hashlib.sha256((OUT/'admission_review.c').read_bytes()).hexdigest(),'flags':flags,'exit_code':r.returncode,'sanitizer_environment':{'ASAN_OPTIONS':os.environ.get('ASAN_OPTIONS','')},'duration_seconds':elapsed,'result':json.loads(r.stdout) if not r.returncode else None}
 (OUT/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(r.stdout,r.stderr);assert not r.returncode
