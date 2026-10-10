#!/usr/bin/env python3
"""Frozen-F Magma boundary algorithm vs current: exact entry/anchor differential.
Streams comparisons; no large duplicate trace outputs are written.
"""
import argparse,hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
from retained_boundary_core import verify_core
ROOT=Path(__file__).resolve().parents[1];ORACLE=ROOT/'tests/oracles/magma-f';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
FIXTURES=['v5-revision4/southern-minimal8-town.sav','v5-revision5/magma-all65-town.sav','v5-revision6/underwater-all89-town.sav','v5-revision6/underwater-minimal12-town.sav','v5-revision7/return-all104-town.sav']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sanitize',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args();manifest=json.loads((ORACLE/'manifest.json').read_text());assert sha(ORACLE/'manifest.json')=='4d215f978424aad243911b0768201d962c113d3fa6693b5b99f1aa288023912f';assert all(sha(ORACLE/n)==v for n,v in manifest['files'].items());core=json.loads((ORACLE/'core-hashes.json').read_text());assert sha(ORACLE/'core-hashes.json')==manifest['core_hashes_sha256'];modules=['magma_quests','save5','save4','equipment','equipment_data','creatures','creature_data'];core_contract=verify_core(ROOT,'magma',modules,core);fixtures=[ROOT/'tests/fixtures'/f for f in FIXTURES];report={'scope':__doc__,'sanitize':a.sanitize,'portable_oracle':manifest,'shared_core_contract':core_contract,'fixtures':{str(x.relative_to(ROOT)):sha(x)for x in fixtures},'sources':{str(x.relative_to(ROOT)):sha(x)for x in [ROOT/'src'/n for n in ['magma_game.c','magma_game.h','magma_enter_job.inc','magma_anchor_job.inc']]+[ROOT/'tests/magma_boundary_differential.c',Path(__file__)]},'comparisons':[]}
 with tempfile.TemporaryDirectory(prefix='magma-boundary-host-')as td:
  td=Path(td);bins=[]
  for current in (False,True):
   exe=td/('current'if current else'oracle');source=ROOT/'src/magma_game.c'if current else ORACLE/'magma_game.c';cmd=['cc','-std=c99','-O1'if a.sanitize else'-O2','-g','-Wall','-Wextra','-Werror','-pedantic','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-I'+str(ROOT/'src'),'-DMAGMA_SOURCE="'+str(source)+'"']
   if current:cmd+=['-DNEW_ADAPTER']
   if a.sanitize:cmd+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-sanitize-recover=all','-no-pie']
   subprocess.run(cmd+[str(ROOT/'tests/magma_boundary_differential.c'),*[str(ROOT/'src'/f'{n}.c')for n in modules],'-o',str(exe)],check=True);bins.append(exe)
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1')
  for mode in (0,1):
   ps=[subprocess.Popen([str(b),str(0 if i==0 else mode),*map(str,fixtures)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)for i,b in enumerate(bins)];h=hashlib.sha256();n=0
   while True:
    old,new=[p.stdout.read(65536)for p in ps]
    if old!=new:
     for proc in ps:proc.kill()
     raise AssertionError(('byte mismatch',mode,n,len(old),len(new),next((i for i,(x,y)in enumerate(zip(old,new))if x!=y),None)))
    if not old:break
    h.update(old);n+=len(old)
   diagnostics=[p.stderr.read().decode()for p in ps];assert all(p.wait()==0 for p in ps),diagnostics;row={'mode':'direct'if mode==0 else'queued','exact_bytes_equal':True,'bytes_compared':n,'stream_sha256':h.hexdigest(),'diagnostics':diagnostics};report['comparisons'].append(row);print(json.dumps(row),flush=True)
  done=subprocess.run([str(bins[1]),'2',*map(str,fixtures)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,check=True);report['stale_checks']=done.stderr.decode();print(report['stale_checks'],flush=True)
 assert verify_core(ROOT,'magma',modules,core)==core_contract,'Core changed during differential'
 a.output.parent.mkdir(exist_ok=True,parents=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
