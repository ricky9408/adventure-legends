#!/usr/bin/env python3
"""Reproduce the pinned G5-to-G6 pure renderer comparisons with a host C compiler.

Run from any directory: python tests/verify_late_renderer.py
Equipment rewards requires explicit --equipment-rewards-successor opt-in.
No ARM toolchain, emulator, network, or files outside the source checkout needed.
Compiled programs and generated source are created in an automatically removed
temporary directory. An optional --output writes a JSON result, never binaries.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shlex, subprocess, tempfile, time
from pathlib import Path
from renderer_equipment_successor import FLAG,select_manifest,query_function

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def function(text: str, name: str) -> str:
    match=re.search(r'(?:COLD\s+)?(?:int|void)\s+'+re.escape(name)+r'\([^)]*\)\s*\{',text)
    if not match: raise AssertionError('Missing function: '+name)
    end=match.end(); depth=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}'); end+=1
    return text[match.start():end]

def authenticate(root:Path,fixture:Path,manifest:dict):
    for name,want in manifest['fixture_files'].items():
        assert sha((fixture/name).read_bytes())==want,('Reference fixture changed',name)
    raw=(root/'src/game.c').read_bytes(); current=raw.decode(); reference=(fixture/'reference-game.c').read_text()
    assert sha(raw)==manifest['reviewed_candidate']['game_source_sha256'], 'The game source differs from the reviewed renderer snapshot; review and refresh the pinned verification before claiming reproduction'
    for relative,want in manifest['context_source_pins'].items():
        assert sha((root/relative).read_bytes())==want,('Reviewed query/palette context changed',relative)
    for name,want in manifest['reference_function_sha256'].items():
        assert sha(function(reference,name).encode())==want,('G5 reference function changed',name)
    for name,want in manifest['candidate_function_sha256'].items():
        assert sha(function(current,name).encode())==want,('Candidate differs from the reviewed renderer; update this verification only after reviewing the change',name)
    for relative,names in manifest.get('unchanged_query_function_sha256',{}).items():
        for name,want in names.items():
            assert sha(query_function((root/relative).read_text(),name).encode())==want,('Pinned renderer query changed',relative,name)
    if 'source_change' in manifest:
        change=manifest['source_change'];before=change['before_statement'].encode();after=change['after_statement'].encode()
        assert raw.count(after)==1 and before not in raw,'Exact ordinary save slice change missing or ambiguous'
        assert sha(raw.replace(after,before,1))==change['before_sha256'],'Changes beyond the reviewed ordinary save slice'
    return current,reference

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument(FLAG,action='count',default=0,help='Use only the pinned equipment-rewards renderer context successor')
    parser.add_argument('--source-root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path)
    parser.add_argument('--cc',default=os.environ.get('CC','cc'))
    parser.add_argument('--skip-ubsan',action='store_true',help='Run only the optimized build; report sanitizer coverage as not run')
    args=parser.parse_args(); root=args.source_root.resolve()
    if args.equipment_rewards_successor>1:parser.error(FLAG+' must be supplied once')
    fixture=Path(__file__).resolve().parent/'fixtures/render-g5'
    manifest,manifest_path=select_manifest(fixture,bool(args.equipment_rewards_successor))
    current,reference=authenticate(root,fixture,manifest)
    compiler=shlex.split(args.cc); results={}
    flavors=[('optimized',['-O2'])]
    if not args.skip_ubsan: flavors.append(('ubsan',['-O1','-fsanitize=undefined','-fno-sanitize-recover=all']))
    with tempfile.TemporaryDirectory(prefix='emberbond-render-') as temporary:
        temp=Path(temporary)
        for suite in manifest['suites']:
            original=(fixture/suite['fixture']).read_text()
            before,after=original.split(suite['candidate_marker'],1)
            for name in suite['functions']:
                assert function(before,name)==function(reference,name),('Harness G5 control differs',name)
                old=function(after,name); new=function(current,name)
                assert after.count(old)==1,('Ambiguous candidate replacement',name)
                after=after.replace(old,new,1)
            generated=before+suite['candidate_marker']+after
            # The checked-out candidate is exactly the reviewed body. This also
            # authenticates the unchanged test matrix and its query stubs.
            assert sha(generated.encode())==manifest['fixture_files'][suite['fixture']]
            source=temp/suite['fixture']; source.write_text(generated)
            for flavor,flags in flavors:
                exe=temp/(suite['name']+'-'+flavor)
                command=compiler+['-std=c99','-Wall','-Wextra','-Wno-misleading-indentation',*flags,str(source),'-o',str(exe)]
                compiled=subprocess.run(command,capture_output=True,text=True)
                if compiled.returncode:
                    raise RuntimeError('Compilation failed:\n'+compiled.stdout+compiled.stderr)
                began=time.monotonic(); run=subprocess.run([str(exe)],capture_output=True,text=True)
                if run.returncode: raise RuntimeError('Differential failed:\n'+run.stdout+run.stderr)
                summary=json.loads(run.stdout.splitlines()[-1]); assert summary['all_equal']
                for name,want in suite['expected_counts'].items(): assert summary[name]==want,(name,summary[name],want)
                key=suite['name']+'-'+flavor
                results[key]={'summary':summary,'elapsed_seconds':time.monotonic()-began,'generated_source_sha256':sha(generated.encode()),'stderr':run.stderr}
                print(key+': '+json.dumps(summary),flush=True)
    report={'status':'PASS','scope':manifest['scope'],'baseline':manifest['baseline'],'reviewed_candidate':manifest['reviewed_candidate'],'current_game_source_sha256':sha((root/'src/game.c').read_bytes()),'reference_manifest_sha256':sha((fixture/'reference.json').read_bytes()),'selected_manifest_sha256':sha(manifest_path.read_bytes()),'equipment_rewards_successor':bool(args.equipment_rewards_successor),'runner_sha256':sha(Path(__file__).read_bytes()),'ubsan_run':not args.skip_ubsan,'native_dma_or_gameplay_acceptance_claim':False,'results':results}
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: pinned pure renderer comparison; no native DMA or gameplay claim',flush=True)

if __name__=='__main__': main()
