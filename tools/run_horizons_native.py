#!/usr/bin/env python3
"""Freeze and reproduce controller-only Horizons routes; retain every failed run.

No publication. No game-memory writes or machine-state imports. Pass a fresh
output root. Runtime closure is copied once; immutable candidate files are
hardlinked into child evidence. Ordinary H prior SRAM is hash-authenticated.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
import horizons_journey
from return_native_dependencies import resolve_mgba

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--candidate',type=Path,required=True,help='Directory with emberbond.gba/.elf/.sym and source-hashes.json')
 p.add_argument('--source-root',type=Path,default=ROOT)
 p.add_argument('--mgba-library',type=Path,help='Explicit installed library when the bridge uses an unresolved loader path')
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--h-native-root',type=Path,required=True,help='Exact delivered native-h-global-01 evidence root')
 p.add_argument('--stages',default='full,repeats,minimal-stage-lifecycle,minimal-water',help='Comma-separated full, minimal-stage-lifecycle, minimal-water, migration, main, repeats')
 p.add_argument('--timing-mode',choices=('strict','collect-diagnostic'),default='strict')
 a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 c=a.candidate.resolve();source=a.source_root.resolve();manifest=json.loads((c/'source-hashes.json').read_text())
 assert all((source/f).is_file() and sha(source/f)==h for f,h in manifest.items()),'Current runtime source does not match build receipt'
 candidate=out/'candidate';candidate.mkdir();pins={}
 for name in ('emberbond.gba','emberbond.sym','emberbond.elf','source-hashes.json'):
  shutil.copyfile(c/name,candidate/name);pins[name]=sha(candidate/name)
 horizons_journey.elf_locals(candidate/'emberbond.elf',candidate/'emberbond.gba')
 runtime=out/'runtime-source'
 for name,h in manifest.items():
  dst=runtime/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,dst);assert sha(dst)==h
 build=json.loads((ROOT/'tools/horizons_mgba_bridge.build.json').read_text());assert build['bridge_sha256']==sha(ROOT/'tools/horizons_mgba_bridge.so') and build['source_sha256']==sha(ROOT/'tools/horizons_mgba_bridge.c')
 helpers=out/'helpers';files={Path(__file__).resolve(),ROOT/'tools/horizons_mgba_bridge.c',ROOT/'tools/horizons_mgba_bridge.so',ROOT/'tools/build_horizons_mgba_bridge.sh',ROOT/'tools/horizons_mgba_bridge.build.json'}
 files.update(ROOT/f for f in ('assets/region/layout.json','assets/world_manifest.json','assets/campaign_layouts.json','assets/return_region/geometry.json','assets/horizons_region/geometry.json'))
 for m in tuple(sys.modules.values()):
  name=getattr(m,'__file__',None)
  if name and Path(name).is_file() and Path(name).resolve().is_relative_to(ROOT):files.add(Path(name).resolve())
 hashes={}
 for f in sorted(files):
  name=f.relative_to(ROOT);dst=helpers/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dst);hashes[str(name)]=sha(dst)
 library,soname,discovery=resolve_mgba(ROOT/'tools/horizons_mgba_bridge.so',a.mgba_library)
 libdir=helpers/'tools/emulator-libs';libdir.mkdir();shutil.copyfile(library,libdir/Path(soname).name)
 hashes[str((libdir/Path(soname).name).relative_to(helpers))]=sha(libdir/Path(soname).name)
 (helpers/'helper-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
 (out/'emulator-dependencies.txt').write_text(discovery)
 status={'suite':'horizons-native-reproduction','release_acceptance':False,'controller_only':True,'game_ram_writes':0,'machine_state_loads':0,'candidate':pins,'runtime_manifest_sha256':pins['source-hashes.json'],'helper_manifest_sha256':sha(helpers/'helper-hashes.json'),'stages':[],'finished':False}
 def record():(out/'run-status.json').write_text(json.dumps(status,indent=2)+'\n')
 common=['--rom',str(candidate/'emberbond.gba'),'--symbols',str(candidate/'emberbond.sym'),'--source-manifest',str(candidate/'source-hashes.json'),'--source-root',str(runtime),'--expected-rom-sha',pins['emberbond.gba'],'--expected-symbols-sha',pins['emberbond.sym'],'--expected-elf-sha',pins['emberbond.elf'],'--expected-manifest-sha',pins['source-hashes.json'],'--timing-mode',a.timing_mode]
 for stage in a.stages.split(','):
  minimal=stage.startswith('minimal');producer_name='minimal-north-lifecycle' if minimal else 'full'
  report=a.h_native_root.resolve()/producer_name/'return-journey.json'
  snapshot='main-route-cold-save-after' if minimal else '05-all104-cold-reboot-after'
  scope={'minimal-stage-lifecycle':'lifecycle','minimal-water':'main'}.get(stage,stage)
  if stage=='repeats':
   producer=next((s for s in status['stages'] if s['name']=='full' and s['state']=='passed'),None)
   if producer is None:
    status['stages'].append({'name':stage,'state':'skipped-dependency','reason':'No passing uninterrupted full producer on this exact candidate'});record();continue
   report=out/'full/horizons-journey.json';snapshot='07-all120-cold-reboot-after';scope='followup-repeats'
  source_record=json.loads(report.read_text())['snapshots'][snapshot]
  fixture=report.parent/Path(source_record['sram_path']).name
  assert fixture.is_file() and sha(fixture)==source_record['sram_sha256'],'Supplied producer directory must contain its exact native SRAM'
  command=[sys.executable,str(helpers/'tests/horizons_journey.py'),*common,'--producer-report',str(report),'--expected-producer-sha',sha(report),'--source-snapshot',snapshot,'--source-sram',str(fixture),'--output',str(out/stage),'--scope',scope,'--arm-order','water-first' if stage=='minimal-water' else 'stage-first']
  row={'name':stage,'state':'running','argv':command,'started':time.time()};status['stages'].append(row);record()
  ld='DYLD_LIBRARY_PATH' if sys.platform=='darwin' else 'LD_LIBRARY_PATH'
  with (out/(stage+'.log')).open('w') as stream:
   result=subprocess.run(command,cwd=helpers,env={**os.environ,ld:str(libdir)+(os.pathsep+os.environ[ld] if os.environ.get(ld) else ''),'PYTHONDONTWRITEBYTECODE':'1','HORIZONS_MGBA_LIBRARY':str(libdir/Path(soname).name)},stdout=stream,stderr=subprocess.STDOUT)
  row.update(state='passed' if result.returncode==0 else 'failed',exit_code=result.returncode,elapsed_seconds=round(time.time()-row['started'],3))
  r=out/stage/'horizons-journey.json'
  if r.is_file():row.update(report=str(r),report_sha256=sha(r))
  print(stage+': '+row['state'],flush=True);record()
 status['finished']=True;status['runtime_closure_still_exact']=all(sha(runtime/f)==h for f,h in manifest.items());status['helper_closure_still_exact']=all(sha(helpers/f)==h for f,h in hashes.items());status['all_requested_stages_passed']=all(s['state']=='passed' for s in status['stages']) and status['runtime_closure_still_exact'] and status['helper_closure_still_exact'];record()
 return not status['all_requested_stages_passed']
if __name__=='__main__':raise SystemExit(main())
