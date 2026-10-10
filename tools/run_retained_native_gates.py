#!/usr/bin/env python3
"""Execute retained recipes on an explicit frozen Return adapter and ROM.

Disables rebuilding the paired cartridge in all nested Make invocations.
Every attempt gets a new evidence directory; nonzero results stay failures.
"""
import argparse,datetime,hashlib,json,os,shutil,signal,stat,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--adapter',type=Path,required=True)
    p.add_argument('--scope',choices=('legacy','magma','underwater','affected-host','continuation'),required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--commands',type=Path,help='Explicit remaining recipe argv lists for continuation scope')
    a=p.parse_args();adapter=a.adapter.resolve();src=adapter/'source';out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    receipt=json.loads((adapter/'adapter-receipt.json').read_text());inputs=json.loads((adapter/'adapter-inputs.json').read_text())
    def verify():
        assert all(sha(src/k)==v for k,v in inputs.items()),'Adapter source input changed'
        assert all(sha(src/'build'/k)==v for k,v in receipt['candidate'].items()),'Paired candidate artifact changed'
        for k,v in receipt['changes'].items():
            if 'original_sha256' in v:assert sha(ROOT/k)==v['original_sha256'],('Historical original changed',k)
    verify()
    base=['make','-o','build/emberbond.gba','MAKE=make -o build/emberbond.gba']
    commands={'legacy':[base+['test-tools','test']],
              'magma':[base+['test-magma-native']],
              'underwater':[base+['test-underwater-native']],
              'affected-host':[[ 'python3','tests/test_magma_game.py'],['python3','tests/test_magma_evolution_ui.py'],['python3','tests/test_save_feedback.py'],['python3','tests/profile_evolution_ui.py','--output',str(out/'evolution-arm.json')]]}.get(a.scope)
    if a.scope=='continuation':
        assert a.commands,'Continuation requires explicit commands'
        commands=json.loads(a.commands.read_text())
        assert commands and all(isinstance(c,list) and all(isinstance(x,str) for x in c) for c in commands)
    report={'scope':a.scope,'adapter_receipt_sha256':sha(adapter/'adapter-receipt.json'),'candidate':receipt['candidate'],'runs':[],'result':'RUNNING','runner_sha256':sha(Path(__file__))}
    # Helper snapshots copy the bridge, but not the installed toolchain tree.
    # Supply the already-installed matching library path explicitly to children.
    library=src/'tools/sysroot/usr/lib/x86_64-linux-gnu'
    env=dict(os.environ)
    if (library/'libmgba.so.0.10').exists():
        env['LD_LIBRARY_PATH']=str(library.resolve())+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
        report['mgba_runtime_library']={'path':str((library/'libmgba.so.0.10').resolve()),'sha256':sha(library/'libmgba.so.0.10')}
    dedup_records=[]
    immutable={}
    for suffix in ('.gba','.elf'):
        path=src/'build'/('emberbond'+suffix)
        immutable[suffix]=(path,sha(path),path.stat().st_size,stat.S_IMODE(path.stat().st_mode))
    def deduplicate_candidate_copies():
        # Hardlinks retain each pathname (and therefore each emulator save path).
        # Only fixed candidate-identical ROM/ELF copies are eligible, never SRAM,
        # machine states, reports, sources or different isolated benchmark ROMs.
        for suffix,(canonical,expected,size,mode) in immutable.items():
            for path in (src/'build').rglob('*'+suffix):
                if path==canonical or path.is_symlink() or not path.is_file():continue
                info=path.stat();owner=canonical.stat()
                if (info.st_dev,info.st_ino)==(owner.st_dev,owner.st_ino):continue
                if info.st_size!=size or stat.S_IMODE(info.st_mode)!=mode or sha(path)!=expected:continue
                temporary=path.with_name(path.name+'.verified-'+uuid.uuid4().hex)
                os.link(canonical,temporary)
                assert sha(temporary)==expected and stat.S_IMODE(temporary.stat().st_mode)==mode
                os.replace(temporary,path)
                dedup_records.append({'path':str(path.relative_to(src)),'sha256':expected,'bytes':size,'mode':oct(mode)})
        if dedup_records:
            (out/'immutable-copy-hardlinks.json').write_text(json.dumps({'scope':'Candidate-identical immutable binaries only; every path, byte and mode preserved','files':dedup_records},indent=2)+'\n')
    status=out/'run-status.json'
    def save():status.write_text(json.dumps(report,indent=2)+'\n')
    for n,command in enumerate(commands):
        verify();log=out/f'{n:02d}.log';row={'command':command,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'log':log.name,'status':'RUNNING'};report['runs'].append(row);report['result']='RUNNING';save();start=time.monotonic();low_space=False;cancelled=False
        with log.open('w') as f:
            process=subprocess.Popen(command,cwd=src,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=env)
            def stop():
                try:os.killpg(process.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                try:process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL);process.wait()
            try:
                last_dedup=0
                while process.poll() is None:
                    if time.monotonic()-last_dedup>20:
                        deduplicate_candidate_copies();last_dedup=time.monotonic()
                    free=shutil.disk_usage(src).free
                    if free<128*1024*1024:
                        low_space=True;stop();break
                    request=out/'stop-request.json'
                    if request.exists():
                        cancelled=True;row['cancellation_request']=json.loads(request.read_text());stop();break
                    time.sleep(2)
            except KeyboardInterrupt:
                cancelled=True;row['cancellation_request']='Interrupted by operator';stop()
        row.update(exit_code=process.returncode,seconds=round(time.monotonic()-start,3),log_sha256=sha(log),status='CANCELLED' if cancelled else 'BLOCKED_RESOURCE' if low_space else 'PASS' if process.returncode==0 else 'FAIL')
        try:verify();row['source_and_candidate_unchanged']=True
        except AssertionError as error:row['source_and_candidate_unchanged']=False;row['integrity_error']=str(error)
        report['result']='PASS' if all(r['status']=='PASS' and r.get('source_and_candidate_unchanged') for r in report['runs']) else row['status'] if low_space or cancelled else 'FAIL';save()
        print(a.scope,row['status'],'exit',process.returncode,'seconds',row['seconds'],flush=True)
        if process.returncode or low_space or cancelled or not row['source_and_candidate_unchanged']:return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
