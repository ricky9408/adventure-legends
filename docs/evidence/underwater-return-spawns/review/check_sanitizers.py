#!/usr/bin/env python3
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tests'));from test_underwater_save import prepare,runtime_hashes
before=runtime_hashes()
with tempfile.TemporaryDirectory(prefix='independent-return-sanitizers-') as td:
 td=Path(td);sources=prepare(td);flags=['-std=c99','-O2','-Wall','-Wextra','-Werror','-Wstrict-aliasing=2','-fstrict-aliasing','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(ROOT/'src'),'-I'+str(td)]
 subprocess.run(['cc',*flags,*map(str,sources.values()),str(ROOT/'tests/underwater_save_setup.c'),str(OUT/'bounds.c'),'-o',str(td/'bounds')],check=True)
 env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0');result=subprocess.run([str(td/'bounds')],capture_output=True,text=True,env=env);assert before==runtime_hashes()
 (OUT/'sanitizers.log').write_text(result.stdout+result.stderr)
 (OUT/'sanitizers.json').write_text(json.dumps({'exit_code':result.returncode,'source_hashes':before,'test_sha256':hashlib.sha256((OUT/'bounds.c').read_bytes()).hexdigest(),'flags':flags,'environment':{'ASAN_OPTIONS':'detect_leaks=0'},'scope':'host return-spawn bound checks; leak detection unavailable under ptrace'},indent=2)+'\n')
 print(result.stdout,result.stderr);assert result.returncode==0
