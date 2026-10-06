#!/usr/bin/env python3
"""Fresh sequential exact-ROM Underwater controller acceptance.

Reports and snapshots are never reused from a different cartridge. An immutable
observer closure is copied before any producer, and verified after every suite.
Output must be new; Make archives its previous directory rather than deleting it.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','symbols','source-manifest','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 rom,sym,manifest=a.rom.resolve(),a.symbols.resolve(),a.source_manifest.resolve()
 hashes=json.loads(manifest.read_text());assert all(sha(ROOT/k)==v for k,v in hashes.items())
 observers=set(json.loads((ROOT/'tools/underwater_observer_paths.json').read_text()))
 observers.update(('tests/underwater_minimal_review.py','tests/underwater_combat_native.py','tests/underwater_geometry_stress_native.py','tests/underwater_precision_native.py','tests/underwater_dynamic_stress_native.py','tests/underwater_phase_stress_native.py','tools/run_underwater_native.py'))
 closure={name:sha(ROOT/name) for name in sorted(observers)}
 snap=out/'test-source'
 for name in closure:
  target=snap/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
 (snap/'source-snapshot-hashes.json').write_text(json.dumps(closure,indent=2)+'\n')
 base=['--rom',str(rom),'--symbols',str(sym),'--source-manifest',str(manifest),'--expected-rom-sha',sha(rom),'--expected-symbols-sha',sha(sym)]
 results=[]
 def run(label,script,args):
  command=[sys.executable,str(ROOT/script),*args]
  with (out/(label+'.log')).open('w') as log:
   code=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT).returncode
  results.append({'suite':label,'command':command,'exit_code':code,'log_sha256':sha(out/(label+'.log'))})
  (out/'run-status.json').write_text(json.dumps({'rom_sha256':sha(rom),'symbols_sha256':sha(sym),'runtime_manifest_sha256':sha(manifest),'observer_manifest_sha256':sha(snap/'source-snapshot-hashes.json'),'runs':results},indent=2)+'\n')
  assert all(sha(ROOT/k)==v and sha(snap/k)==v for k,v in closure.items()),'Observer changed during acceptance'
  assert all(sha(ROOT/k)==v for k,v in hashes.items()),'Runtime input changed during acceptance'
  if code:raise SystemExit(f'{label} failed ({code}); preserved {out/(label+".log")}')
  print(label,'PASS',flush=True)
 full=out/'full';minimal=out/'minimal';fixture=ROOT/'tests/fixtures/v5-revision5-minimal/magma-minimal10-town.sav'
 run('full','tests/underwater_journey.py',base+['--scope','full','--output',str(full)])
 run('minimal','tests/underwater_journey.py',base+['--scope','main','--source-sram',str(fixture),'--output',str(minimal)])
 run('minimal-lifecycle','tests/underwater_minimal_review.py',base+['--helper-snapshot',str(snap),'--source-sram',str(fixture),'--source-report',str(minimal/'underwater-journey.json'),'--output',str(out/'minimal-lifecycle'),'--expected-manifest-sha',sha(manifest),'--expected-helper-sha',closure['tests/underwater_journey.py'],'--loading-policy','bounded-cold'])
 producer=full/'underwater-journey.json';args=base+['--source-report',str(producer),'--source-report-sha',sha(producer),'--producer-source-root',str(snap)]
 run('combat','tests/underwater_precision_native.py',args+['--acceptance','--case','all','--output',str(out/'combat')])
 run('scenery','tests/underwater_geometry_stress_native.py',args+['--acceptance','--output',str(out/'scenery')])
 run('dynamic','tests/underwater_dynamic_stress_native.py',args+['--acceptance','--output',str(out/'dynamic')])
 run('phase','tests/underwater_phase_stress_native.py',args+['--acceptance','--output',str(out/'phase')])
 run('scenery-aim','tests/underwater_geometry_stress_native.py',args+['--acceptance','--only','87:5','--aim-right','--output',str(out/'scenery-aim')])
 print('All sequenced native suites passed; see verification guide for independent host, legacy, stack and clean-export gates.')
if __name__=='__main__':main()
