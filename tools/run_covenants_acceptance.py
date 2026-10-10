#!/usr/bin/env python3
"""Reproduce the complete genuine native Covenants acceptance matrix.

One immutable candidate; both original Core preludes are earned through buttons.
No synthetic engine fixture, game RAM write, or machine-state API counts here.
A fresh output is mandatory, and failed stages remain immutable evidence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verified_report(path,pins,suite,scope):
    path=Path(path)
    if not path.is_file():return False,'report missing'
    r=json.loads(path.read_text())
    requirements={
      'expected suite/scope':r.get('suite')==suite and r.get('finished_scope')==scope,
      'exact ROM':r.get('rom_sha256')==pins['emberbond.gba'],
      'exact ELF':r.get('elf_sha256')==pins['emberbond.elf'],
      'exact symbols':r.get('symbols_sha256')==pins['emberbond.sym'],
      'exact runtime closure':r.get('source_manifest_sha256')==pins['source-hashes.json'],
      'controller only':r.get('controller_only') is True and r.get('game_ram_writes')==0 and r.get('machine_state_loads')==0,
      'strict pass':r.get('timing_mode')=='strict' and not r.get('failures') and all(c['passed'] for c in r.get('checks',[])),
      'closed all-frame trace':r.get('global_native',{}).get('closed') is True and not r.get('global_native',{}).get('exceptions'),
    }
    trace=r.get('global_native',{})
    if trace.get('closed'):
        source=path.parent/Path(trace['trace_path']).name
        requirements['exact native trace']=source.is_file() and sha(source)==trace['trace_sha256']
    return all(requirements.values()),[k for k,v in requirements.items() if not v]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--source-root',type=Path,default=ROOT)
    p.add_argument('--prior-root',type=Path,default=ROOT)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mgba-library',type=Path)
    p.add_argument('--object-store',type=Path,default=ROOT/'build/covenants-native-objects')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    state={'suite':'covenants-complete-native-matrix','release_acceptance':False,
      'controller_only':True,'game_ram_writes':0,'machine_state_loads':0,
      'synthetic_engine_fixtures_counted':False,'finished':False,'stages':[],'required_reports':[]}
    def record():(out/'acceptance-status.json').write_text(json.dumps(state,indent=2)+'\n')
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','COVENANTS_NATIVE_OBJECT_STORE':str(a.object_store.resolve())}
    def run(name,args,run_env=None):
        row={'name':name,'state':'running','argv':list(map(str,args)),'started':time.time()};state['stages'].append(row);record()
        with (out/(name+'.log')).open('w') as stream:
            result=subprocess.run(row['argv'],cwd=ROOT,env=run_env or env,stdout=stream,stderr=subprocess.STDOUT)
        row.update(state='passed' if result.returncode==0 else 'failed',exit_code=result.returncode,elapsed_seconds=round(time.time()-row['started'],3));record()
        print(name+': '+row['state'],flush=True)
        return result.returncode==0
    def require(name,path,suite,scope):
        ok,why=verified_report(path,pins,suite,scope)
        row={'name':name,'path':str(path),'passed':ok,'unmet':why}
        if Path(path).is_file():row['sha256']=sha(path)
        state['required_reports'].append(row);record();return ok
    native=out/'native'
    command=[sys.executable,ROOT/'tools/run_covenants_native.py','--candidate',a.candidate.resolve(),
      '--source-root',a.source_root.resolve(),'--prior-root',a.prior_root.resolve(),'--output',native,
      '--stages','full,controls,lifecycle,full-reverse','--timing-mode','strict']
    if a.mgba_library:command+=['--mgba-library',a.mgba_library.resolve()]
    run('full-controls-lifecycle-reverse',command)
    receipt=native/'run-status.json'
    if not receipt.is_file():
        state.update(finished=True,all_native_gates_passed=False,blocker='Candidate/helper freeze failed; original log retained');record();return 1
    base=json.loads(receipt.read_text());pins=base['candidate'];state['candidate']=pins
    for name,scope in (('full','full'),('controls','controls'),('lifecycle','lifecycle'),('full-reverse','full')):
        require(name,native/name/'covenants-journey.json','covenants-native-controller-journey',scope)
    # From here every executable helper and input is taken from the frozen
    # first-stage closure, never from evolving working-tree code.
    helpers=native/'helpers';libdir=helpers/'tools/emulator-libs'
    libs=list(libdir.glob('*'));assert len(libs)==1 and libs[0].is_file()
    ld='DYLD_LIBRARY_PATH' if sys.platform=='darwin' else 'LD_LIBRARY_PATH'
    frozen_env={**env,ld:str(libdir)+(os.pathsep+env[ld] if env.get(ld) else ''),'HORIZONS_MGBA_LIBRARY':str(libs[0])}
    for label,fixture,stage in (('stage','minimal-stage','minimal'),('water','minimal-water','minimal-reverse')):
        prelude=out/('core-'+label)
        run('core-'+label,[sys.executable,helpers/'tests/covenants_core_prelude.py','--frozen-root',native,
          '--prior-root',native/'prior-current-c','--fixture-kind',fixture,'--output',prelude],frozen_env)
        producer=prelude/'covenants-core-prelude.json'
        if not require('core-'+label,producer,'covenants-core-prelude','core-ending'):
            state['stages'].append({'name':'minimal-'+label,'state':'skipped-dependency','reason':'No passing same-candidate genuine Core producer'});record();continue
        minimal=out/('minimal-'+label)
        command=[sys.executable,helpers/'tools/run_covenants_native.py','--candidate',native/'candidate',
          '--source-root',native/'runtime-source','--prior-root',native/'prior-current-c','--output',minimal,
          '--stages',stage+',minimal-late','--minimal-fixture',fixture,'--prelude-report',producer,
          '--prelude-snapshot','original-ending-cold-after','--earned-report',minimal/stage/'covenants-journey.json',
          '--earned-snapshot','12-final-cold-after','--timing-mode','strict','--mgba-library',libs[0]]
        run('minimal-'+label+'-and-late-invitations',command,frozen_env)
        require('minimal-'+label,minimal/stage/'covenants-journey.json','covenants-native-controller-journey','full')
        require('late-invitations-'+label,minimal/'minimal-late/covenants-journey.json','covenants-native-controller-journey','late-invitations')
    manifest=json.loads((native/'candidate/source-hashes.json').read_text())
    helper_manifest=json.loads((helpers/'helper-hashes.json').read_text())
    state['candidate_closure_exact']=all(sha(native/'candidate'/f)==h for f,h in pins.items())
    state['runtime_closure_exact']=all(sha(native/'runtime-source'/f)==h for f,h in manifest.items())
    state['helper_closure_exact']=all(sha(helpers/f)==h for f,h in helper_manifest.items())
    state['finished']=True
    state['all_native_gates_passed']=len(state['required_reports'])==10 and all(r['passed'] for r in state['required_reports']) and all(r['state']=='passed' for r in state['stages']) and state['candidate_closure_exact'] and state['runtime_closure_exact'] and state['helper_closure_exact']
    record();return not state['all_native_gates_passed']

if __name__=='__main__':raise SystemExit(main())
