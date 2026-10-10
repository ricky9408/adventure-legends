#!/usr/bin/env python3
"""Snapshot and replay retained host gates without rebuilding a native ROM.

Every failed command is retained. This runner is current-host evidence only,
never exact-cartridge native acceptance or controller acquisition evidence.
"""
import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def closure(root):
    paths=[]
    for name in ('src','tests','assets','tools'):
        paths += [p for p in (root/name).rglob('*') if p.is_file() and
                  'sysroot' not in p.parts and '__pycache__' not in p.parts and
                  p.suffix in ('.c','.h','.inc','.s','.py','.json','.sav','.txt')]
    paths += [root/'Makefile',root/'linker.ld']
    return {str(p.relative_to(root)):sha(p) for p in sorted(paths)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--runtime-source',type=Path,help='Frozen candidate root supplying src and linker.ld')
    p.add_argument('--snapshot-existing',type=Path,help='Reuse a closed, passing snapshot after checking its complete input manifest; keep its original receipt')
    p.add_argument('--input-reference',type=Path,help='Hardlink only byte/mode-identical immutable files from a closed passing host snapshot while creating a new snapshot')
    p.add_argument('--scope',choices=('underwater','legacy-host','magma','return-host','southern-entry','magma-save-scheduler','all'),default='all')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    reused=None
    reference=None;linked=[]
    if a.input_reference:
        assert not a.snapshot_existing,'A reused snapshot does not copy inputs'
        reference_receipt=json.loads((a.input_reference/'run-status.json').read_text())
        assert reference_receipt['result']=='PASS','Input reference must be a closed passing snapshot'
        reference=Path(reference_receipt['snapshot_root'])
        reference_inputs=json.loads((a.input_reference/'input-sha256.json').read_text())
        assert sha(a.input_reference/'input-sha256.json')==reference_receipt['input_manifest_sha256']
        assert closure(reference)==reference_inputs,'Reference inputs changed'
    def copy_input(source,target,source_root):
        source=Path(source);target=Path(target)
        rel=source.relative_to(source_root)
        prior=reference/rel if reference else None
        if prior and prior.is_file() and not prior.is_symlink():
            old=prior.stat();new=source.stat()
            if old.st_dev==target.parent.stat().st_dev and old.st_size==new.st_size and stat.S_IMODE(old.st_mode)==stat.S_IMODE(new.st_mode) and prior.read_bytes()==source.read_bytes():
                os.link(prior,target)
                linked.append({'path':str(rel),'sha256':sha(target),'bytes':new.st_size,'mode':oct(stat.S_IMODE(new.st_mode))})
                return str(target)
        return shutil.copy2(source,target)
    if a.snapshot_existing:
        assert not a.runtime_source,'Existing snapshot already fixes its runtime source'
        existing=a.snapshot_existing.resolve()
        prior=json.loads((existing/'run-status.json').read_text())
        assert prior['result']=='PASS','Only a closed passing snapshot can be reused'
        before=json.loads((existing/'input-sha256.json').read_text())
        assert sha(existing/'input-sha256.json')==prior['input_manifest_sha256']
        frozen=Path(prior['snapshot_root'])
        runtime_root=Path(prior['runtime_source'])
        runtime_manifest_sha256=prior['runtime_manifest_sha256']
        reused={'snapshot':str(existing),'prior_status_sha256':sha(existing/'run-status.json'),
                'scope':'Same closed host input snapshot only; this new aggregate earns a separate result'}
    else:
        frozen=out/'source';frozen.mkdir()
        (frozen/'build').mkdir()
        before=closure(ROOT)
        runtime_root=a.runtime_source.resolve() if a.runtime_source else ROOT
        runtime_manifest_sha256=None
        if a.runtime_source:
            runtime_manifest=json.loads((runtime_root/'build/source-hashes.json').read_text())
            assert all(sha(runtime_root/k)==v for k,v in runtime_manifest.items()),'frozen runtime changed'
            before={k:v for k,v in before.items() if not k.startswith('src/') and k!='linker.ld'}
            before.update(runtime_manifest)
            runtime_manifest_sha256=sha(runtime_root/'build/source-hashes.json')
        for name in ('src','tests','assets','tools','docs'):
            source=runtime_root if name=='src' else ROOT
            shutil.copytree(source/name,frozen/name,symlinks=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'),copy_function=lambda s,t,base=source:copy_input(s,t,base))
        for name in ('Makefile','linker.ld'):
            base=runtime_root if name=='linker.ld' else ROOT
            copy_input(base/name,frozen/name,base)
    assert closure(frozen)==before,'input changed during snapshot; preserve and retry into new output'
    (out/'input-sha256.json').write_text(json.dumps(before,indent=2)+'\n')
    if reference:
        assert closure(reference)==reference_inputs,'Reference inputs changed during copy'
        (out/'immutable-input-hardlinks.json').write_text(json.dumps({'reference':str(reference),'reference_receipt_sha256':sha(a.input_reference/'run-status.json'),'scope':'Only byte/mode-identical immutable inputs are linked; different candidate files are copied separately','files':linked},indent=2)+'\n')
    commands=[]
    if a.scope=='return-host':commands.append(['make','test-return-host'])
    if a.scope=='magma-save-scheduler':
        commands.append([sys.executable,'tools/run_bounded_magma_save_probe.py','--output',str(out/'scheduler-attempts')])
    if a.scope=='southern-entry':
        commands += [[sys.executable,'tests/test_southern_enter_job.py','--output',str(out/'southern-entry-strict.json')],
                     [sys.executable,'tests/test_southern_enter_job.py','--sanitize','--output',str(out/'southern-entry-sanitized.json')]]
    if a.scope=='magma':commands.append(['make','test-magma-host'])
    if a.scope in ('underwater','all'):
        commands.append(['make','test-underwater-host'])
    if a.scope in ('legacy-host','all'):
        commands += [['make',target] for target in ('test-tools','test-equipment','test-northern-host','test-southern-host','test-magma-host')]
        commands += [[sys.executable,'tests/'+name+'.py'] for name in
            ('test_save4','test_save5','test_progression_events','test_creatures','test_trials','test_save_feedback')]
    report={'scope':'current-host retained regression replay; no final native ROM or acquisition claim',
            'input_manifest_sha256':sha(out/'input-sha256.json'),'snapshot_root':str(frozen),'runtime_source':str(runtime_root),'runtime_manifest_sha256':runtime_manifest_sha256,'runs':[]}
    if reused:report['reused_snapshot']=reused
    for index,command in enumerate(commands):
        name=f'{index:02d}-'+Path(command[-1]).stem
        log=out/(name+'.log');start=time.monotonic()
        with log.open('w') as f:
            code=subprocess.run(command,cwd=frozen,stdout=f,stderr=subprocess.STDOUT).returncode
        unchanged=closure(frozen)==before
        row={'command':command,'exit_code':code,'seconds':round(time.monotonic()-start,3),
             'log':log.name,'log_sha256':sha(log),'input_snapshot_unchanged':unchanged}
        report['runs'].append(row)
        report['result']='PASS' if all(not r['exit_code'] and r['input_snapshot_unchanged'] for r in report['runs']) else 'FAIL'
        (out/'run-status.json').write_text(json.dumps(report,indent=2)+'\n')
        print(name,code,'snapshot unchanged' if unchanged else 'INPUT CHANGED',flush=True)
        if not unchanged:raise SystemExit('snapshot inputs changed; stop without relabeling prior results')
    return 0 if report['result']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
