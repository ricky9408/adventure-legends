#!/usr/bin/env python3
"""Frozen-E Southern entry algorithm vs current byte-differential, strict and sanitizers.
No gameplay, emulator RAM injection, or native performance claims are made.
"""
import argparse,hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
from retained_boundary_core import verify_core
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'tests/fixtures/southern-entry-e'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
FIXTURES=['v5-revision3/northern-all21-town.sav','v5-revision4/southern-minimal8-town.sav','v5-revision6/underwater-all89-town.sav','v5-revision6/underwater-minimal12-town.sav','v5-revision7/return-all104-town.sav']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sanitize',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 manifest=json.loads((E/'source-hashes.json').read_text());assert sha(E/'source-hashes.json')=='d6a2a1898cdf782dcae2a3001646ee612168b9841662254ae5a3b4033a9db615'
 assert sha(E/'south_game.c')==manifest['src/south_game.c']
 # The relocated oracle resolves these quoted fragments through -I src.
 # Preserve their exact frozen implementation rather than deriving an oracle
 # from a potentially changed current fragment.
 for name in ('south_rest_job.inc','south_game_draw.inc'):
  assert sha(ROOT/'src'/name)==manifest['src/'+name],name
 modules=['southern_quests','northern_quests','save5','save4','equipment','equipment_data','creatures','creature_data']
 # Preserve historical pins; content8 requires its separate exact shared-core contract.
 core_contract=verify_core(ROOT,'southern',modules,manifest)
 fixtures=[ROOT/'tests/fixtures'/f for f in FIXTURES];report={'scope':__doc__,'sanitize':a.sanitize,'frozen_manifest_sha256':sha(E/'source-hashes.json'),'shared_core_contract':core_contract,'fixtures':{str(p.relative_to(ROOT)):sha(p) for p in fixtures},'sources':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'src/south_game.c',ROOT/'src/south_game.h',ROOT/'src/south_enter_job.inc',ROOT/'tests/southern_enter_differential.c',Path(__file__)]},'comparisons':[]}
 with tempfile.TemporaryDirectory(prefix='south-enter-diff-') as temp:
  out=Path(temp);binaries=[]
  for current in (False,True):
   dest=out/('current' if current else 'frozen-e');source=ROOT/'src/south_game.c' if current else E/'south_game.c'
   cmd=['cc','-std=c99','-O1' if a.sanitize else '-O2','-g','-Wall','-Wextra','-Werror','-pedantic','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-I'+str(ROOT/'src'),'-DSOUTH_SOURCE="'+str(source)+'"']
   if current:cmd+=['-DNEW_ADAPTER']
   if a.sanitize:cmd+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-sanitize-recover=all','-no-pie']
   subprocess.run(cmd+[str(ROOT/'tests/southern_enter_differential.c'),*[str(ROOT/'src'/f'{n}.c') for n in modules],'-o',str(dest)],check=True);binaries.append(dest)
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1')
  for mode in (0,1):
   commands=[[str(binaries[0]),'0',*map(str,fixtures)],[str(binaries[1]),str(mode),*map(str,fixtures)]]
   processes=[subprocess.Popen(c,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env) for c in commands]
   h=hashlib.sha256();total=0
   while True:
    old,new=[p.stdout.read(65536) for p in processes]
    assert old==new,('byte mismatch',mode,total,len(old),len(new))
    if not old:break
    total+=len(old);h.update(old)
   diagnostics=[p.stderr.read().decode() for p in processes]
   assert all(p.wait()==0 for p in processes),diagnostics
   item={'mode':'direct' if not mode else 'queued','exact_bytes_equal':True,'bytes_compared':total,'snapshot_stream_sha256':h.hexdigest(),'diagnostics':diagnostics};report['comparisons'].append(item);print(json.dumps(item),flush=True)
  stale=subprocess.run([str(binaries[1]),'2',*map(str,fixtures)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,env=env);report['stale_proof_checks']=stale.stderr.decode();print(report['stale_proof_checks'],flush=True)
 assert verify_core(ROOT,'southern',modules,manifest)==core_contract,'Core changed during differential'
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
