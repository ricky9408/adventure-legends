#!/usr/bin/env python3
"""Strict/ASan direct-API branch transactions on pinned controller SRAM inputs."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'build/return-bounded-magma-host');p.add_argument('--fixture104',type=Path,default=ROOT/'tests/fixtures/v5-revision7/return-all104-town.sav');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 old=ROOT/'tests/fixtures/v5-revision5/magma-all65-town.sav';assert digest(old)=='a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858';assert digest(a.fixture104)=='d482466d04050c3d7f2e8eb8e1960729c9b9b33aa3e32440d186a4b54b854a69'
 (a.output/'magma_recruit_fixtures.h').write_text('\n'.join('static const unsigned char '+n+'[32768]={'+','.join(map(str,f.read_bytes()))+'};' for n,f in [('recruit_65_fixture',old),('recruit_104_fixture',a.fixture104)]))
 modules=['save4','save5','creatures','creature_data','equipment','equipment_data','magma_quests']
 source={str(f.relative_to(ROOT)):digest(f) for f in (ROOT/'src').rglob('*') if f.is_file()};report={'scope':'Real typed code, pinned earned SRAM; direct-API synthetic/malformed/full stress, not controller acquisition or native timing','fixture104_sha256':digest(a.fixture104),'source_sha256':source,'runs':[]}
 for san in (False,True):
  flags=['-std=c99','-O1' if san else '-O2','-g','-Wall','-Wextra','-Werror','-pedantic','-fno-strict-aliasing','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-I'+str(ROOT/'src'),'-I'+str(a.output)]
  if san:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer']
  exe=a.output/('sanitized' if san else 'strict');cmd=[os.environ.get('HOST_CC','cc'),*flags,str(ROOT/'tests/magma_recruit_transaction_native.c'),*[str(ROOT/'src'/f'{n}.c') for n in modules],'-o',str(exe)]
  subprocess.run(cmd,check=True);r=subprocess.run([str(exe)],text=True,capture_output=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'},check=False);(a.output/(exe.name+'.log')).write_text(r.stdout+r.stderr);report['runs'].append({'sanitizer':san,'exit':r.returncode,'stdout':r.stdout,'executable_sha256':digest(exe)});(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');assert r.returncode==0,r.stderr
 print(json.dumps(report['runs'],indent=2))
if __name__=='__main__':main()
