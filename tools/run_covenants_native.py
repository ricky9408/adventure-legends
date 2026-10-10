#!/usr/bin/env python3
"""Freeze and reproduce controller-only Covenants routes; retain every failed run.

No publication. No game-memory writes or machine-state imports. Pass a fresh
output root. Runtime closure is copied once; immutable candidate files are
hardlinked into child evidence. Ordinary accepted C SRAM is hash-authenticated.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import stat
import time
import tempfile
import errno
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
import covenants_journey
from return_native_dependencies import resolve_mgba

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def frozen_copy(source,destination):
 """Share only immutable content-addressed copies, never mutable source inodes."""
 source=Path(source);destination=Path(destination);digest=sha(source);mode=stat.S_IMODE(source.stat().st_mode)
 store=Path(os.environ.get('COVENANTS_NATIVE_OBJECT_STORE',str(ROOT/'build/covenants-native-objects'))).resolve();store.mkdir(parents=True,exist_ok=True)
 obj=store/(digest+'.mode'+oct(mode)[2:])
 legacy=store/digest
 if not obj.exists() and legacy.is_file() and sha(legacy)==digest and stat.S_IMODE(legacy.stat().st_mode)==mode:
  try:os.link(legacy,obj)
  except FileExistsError:pass
 if not obj.exists():
  fd,name=tempfile.mkstemp(prefix=digest+'.mode'+oct(mode)[2:]+'.tmp-',dir=store);os.close(fd);temp=Path(name)
  shutil.copyfile(source,temp);os.chmod(temp,mode);assert sha(temp)==digest and stat.S_IMODE(temp.stat().st_mode)==mode
  try:os.link(temp,obj)
  except FileExistsError:pass
  finally:temp.unlink()
 assert sha(obj)==digest and stat.S_IMODE(obj.stat().st_mode)==mode
 destination.parent.mkdir(parents=True,exist_ok=True)
 if destination.exists():
  assert sha(destination)==digest and stat.S_IMODE(destination.stat().st_mode)==mode
 else:
  try:os.link(obj,destination)
  except OSError as exc:
   if exc.errno!=errno.EXDEV:raise
   shutil.copyfile(obj,destination);os.chmod(destination,mode)
  assert sha(destination)==digest and stat.S_IMODE(destination.stat().st_mode)==mode

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--candidate',type=Path,required=True,help='Directory with emberbond.gba/.elf/.sym and source-hashes.json')
 p.add_argument('--source-root',type=Path,default=ROOT)
 p.add_argument('--mgba-library',type=Path,help='Explicit installed library when the bridge uses an unresolved loader path')
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--prior-root',type=Path,default=ROOT,help='Authenticated current-C fixtures and producer evidence root')
 p.add_argument('--stages',default='migration,first-two',help='Comma-separated migration, first-two, full, full-reverse, minimal, minimal-reverse, controls, minimal-controls')
 p.add_argument('--minimal-fixture',choices=('minimal-stage','minimal-water'),default='minimal-stage')
 p.add_argument('--prelude-report',type=Path)
 p.add_argument('--prelude-snapshot',default='original-ending-cold-after')
 p.add_argument('--earned-report',type=Path,help='Exact completed producer for controls-only reproduction')
 p.add_argument('--earned-snapshot',default='12-final-cold-after')
 p.add_argument('--timing-mode',choices=('strict','collect-diagnostic'),default='strict')
 a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 c=a.candidate.resolve();source=a.source_root.resolve();manifest=json.loads((c/'source-hashes.json').read_text())
 assert all((source/f).is_file() and sha(source/f)==h for f,h in manifest.items()),'Current runtime source does not match build receipt'
 candidate=out/'candidate';candidate.mkdir();pins={}
 for name in ('emberbond.gba','emberbond.sym','emberbond.elf','source-hashes.json'):
  frozen_copy(c/name,candidate/name);pins[name]=sha(candidate/name)
 covenants_journey.elf_locals(candidate/'emberbond.elf',candidate/'emberbond.gba')
 runtime=out/'runtime-source'
 for name,h in manifest.items():
  dst=runtime/name;dst.parent.mkdir(parents=True,exist_ok=True);frozen_copy(source/name,dst);assert sha(dst)==h
 build=json.loads((ROOT/'tools/horizons_mgba_bridge.build.json').read_text());assert build['bridge_sha256']==sha(ROOT/'tools/horizons_mgba_bridge.so') and build['source_sha256']==sha(ROOT/'tools/horizons_mgba_bridge.c')
 helpers=out/'helpers';files={Path(__file__).resolve(),ROOT/'tools/horizons_mgba_bridge.c',ROOT/'tools/horizons_mgba_bridge.so',ROOT/'tools/build_horizons_mgba_bridge.sh',ROOT/'tools/horizons_mgba_bridge.build.json'}
 files.update(ROOT/f for f in ('tests/covenants_core_prelude.py','tools/run_covenants_acceptance.py','assets/region/layout.json','assets/world_manifest.json','assets/campaign_layouts.json','assets/return_region/geometry.json','assets/horizons_region/geometry.json','assets/covenants_world/geometry.json'))
 for m in tuple(sys.modules.values()):
  name=getattr(m,'__file__',None)
  if name and Path(name).is_file() and Path(name).resolve().is_relative_to(ROOT):files.add(Path(name).resolve())
 hashes={}
 for f in sorted(files):
  name=f.relative_to(ROOT);dst=helpers/name;dst.parent.mkdir(parents=True,exist_ok=True);frozen_copy(f,dst);hashes[str(name)]=sha(dst)
 library,soname,discovery=resolve_mgba(ROOT/'tools/horizons_mgba_bridge.so',a.mgba_library)
 libdir=helpers/'tools/emulator-libs';libdir.mkdir();frozen_copy(library,libdir/Path(soname).name)
 hashes[str((libdir/Path(soname).name).relative_to(helpers))]=sha(libdir/Path(soname).name)
 (helpers/'helper-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
 (out/'emulator-dependencies.txt').write_text(discovery)
 status={'suite':'covenants-native-reproduction','release_acceptance':False,'controller_only':True,'game_ram_writes':0,'machine_state_loads':0,'candidate':pins,'runtime_manifest_sha256':pins['source-hashes.json'],'helper_manifest_sha256':sha(helpers/'helper-hashes.json'),'stages':[],'finished':False}
 def record():(out/'run-status.json').write_text(json.dumps(status,indent=2)+'\n')
 common=['--rom',str(candidate/'emberbond.gba'),'--symbols',str(candidate/'emberbond.sym'),'--source-manifest',str(candidate/'source-hashes.json'),'--source-root',str(runtime),'--expected-rom-sha',pins['emberbond.gba'],'--expected-symbols-sha',pins['emberbond.sym'],'--expected-elf-sha',pins['emberbond.elf'],'--expected-manifest-sha',pins['source-hashes.json'],'--timing-mode',a.timing_mode]
 prior=out/'prior-current-c'
 for kind in covenants_journey.C_INPUTS:
  _,contract=covenants_journey.authenticate_current_c(a.prior_root,kind)
  for name in (contract['fixture_path'],contract['producer_path'],'tests/fixtures/v5-revision8/provenance.json'):
   dest=prior/name;dest.parent.mkdir(parents=True,exist_ok=True);frozen_copy(a.prior_root/name,dest)
 for stage in a.stages.split(','):
  minimal=stage.startswith('minimal')
  kind=a.minimal_fixture if minimal else 'full'
  scope={'minimal-first-two':'first-two','minimal':'full','minimal-reverse':'full','full-reverse':'full','minimal-controls':'controls','minimal-lifecycle':'lifecycle','minimal-late':'late-invitations'}.get(stage,stage)
  command=[sys.executable,str(helpers/'tests/covenants_journey.py'),*common,'--prior-root',str(prior),'--fixture-kind',kind,'--output',str(out/stage),'--scope',scope,'--arm-order','reverse' if stage.endswith('-reverse') else 'forward']
  if minimal and a.prelude_report and scope not in ('controls','late-invitations'):command += ['--prelude-report',str(a.prelude_report.resolve()),'--prelude-sha',sha(a.prelude_report),'--prelude-snapshot',a.prelude_snapshot]
  if scope in ('controls','late-invitations'):
   report=a.earned_report.resolve() if a.earned_report else out/('minimal' if minimal else 'full')/'covenants-journey.json'
   producer=json.loads(report.read_text()) if report.is_file() else None
   ready=producer is not None and producer.get('finished_scope')=='full' and producer.get('timing_mode')=='strict' and producer.get('controller_only') is True and producer.get('game_ram_writes')==0 and producer.get('machine_state_loads')==0 and not producer.get('failures') and all(c['passed'] for c in producer.get('checks',[])) and producer.get('global_native',{}).get('closed') is True and not producer.get('global_native',{}).get('exceptions') and producer.get('rom_sha256')==pins['emberbond.gba'] and producer.get('elf_sha256')==pins['emberbond.elf'] and producer.get('source_manifest_sha256')==pins['source-hashes.json']
   if not ready:
    status['stages'].append({'name':stage,'state':'skipped-dependency','reason':'No successful strict controller-only full producer on this exact candidate','producer_report':str(report)});record();print(stage+': skipped-dependency',flush=True);continue
   command += ['--earned-report',str(report),'--earned-sha',sha(report),'--earned-snapshot',a.earned_snapshot]
  row={'name':stage,'state':'running','argv':command,'started':time.time()};status['stages'].append(row);record()
  ld='DYLD_LIBRARY_PATH' if sys.platform=='darwin' else 'LD_LIBRARY_PATH'
  with (out/(stage+'.log')).open('w') as stream:
   result=subprocess.run(command,cwd=helpers,env={**os.environ,ld:str(libdir)+(os.pathsep+os.environ[ld] if os.environ.get(ld) else ''),'PYTHONDONTWRITEBYTECODE':'1','HORIZONS_MGBA_LIBRARY':str(libdir/Path(soname).name)},stdout=stream,stderr=subprocess.STDOUT)
  row.update(state='passed' if result.returncode==0 else 'failed',exit_code=result.returncode,elapsed_seconds=round(time.time()-row['started'],3))
  r=out/stage/'covenants-journey.json'
  if r.is_file():row.update(report=str(r),report_sha256=sha(r))
  print(stage+': '+row['state'],flush=True);record()
 status['finished']=True;status['runtime_closure_still_exact']=all(sha(runtime/f)==h for f,h in manifest.items());status['helper_closure_still_exact']=all(sha(helpers/f)==h for f,h in hashes.items());status['all_requested_stages_passed']=all(s['state']=='passed' for s in status['stages']) and status['runtime_closure_still_exact'] and status['helper_closure_still_exact'];record()
 return not status['all_requested_stages_passed']
if __name__=='__main__':raise SystemExit(main())
