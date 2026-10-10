#!/usr/bin/env python3
"""Read-only successor validation plus isolated negative guard tests.

Run after make assets. Mutation probes use a temporary copy of guard inputs,
never the working source tree. Optional --baseline checks historical P2 files.
"""
from pathlib import Path
import argparse, hashlib, json, shutil, sys, tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets'))
from legacy_art_successor import SUCCESSOR_FILE,validate_legacy_prefix,sha
CONTRACTS=[f'assets/{name}/legacy_prefix_sha256.json'for name in('underwater_creatures','return_creatures')]

def expect_failure(action,label,results):
    try:action()
    except (AssertionError,KeyError,ValueError) as error:
        results.append({'case':label,'passed':True,'rejection':str(error)});return
    raise AssertionError('Guard accepted '+label)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--baseline',type=Path);parser.add_argument('--output',type=Path);args=parser.parse_args();results=[]
    paths={SUCCESSOR_FILE,'assets/generate_assets.py'}
    for rel in CONTRACTS:
        paths.add(rel);paths.update(json.loads((ROOT/rel).read_text())['sha256'])
    paths.update(str(p.relative_to(ROOT))for p in(ROOT/'src/asset_data').glob('part_*.inc'))
    before={p:sha((ROOT/p).read_bytes())for p in paths}
    for rel in CONTRACTS:
        result=validate_legacy_prefix(ROOT,ROOT/rel,'connected-roads-c4')
        assert result['protected_creature_palette_arrays_unchanged'] and not result['unchanged']
        results.append({'case':'explicit successor '+rel,'passed':True,'result':result})
        expect_failure(lambda rel=rel:validate_legacy_prefix(ROOT,ROOT/rel),'historical rejects successor '+rel,results)
        if args.baseline:
            result=validate_legacy_prefix(args.baseline,args.baseline/rel)
            assert result['unchanged'];results.append({'case':'historical baseline '+rel,'passed':True,'result':result})
    with tempfile.TemporaryDirectory(prefix='connected-art-guard-')as td:
        scratch=Path(td)
        for rel in paths:
            target=scratch/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target)
        saved={p:(scratch/p).read_bytes()for p in paths}
        def restore():
            for rel,data in saved.items():(scratch/rel).write_bytes(data)
            extra=scratch/'src/asset_data/part_999.inc'
            if extra.exists():extra.unlink()
        def check():return validate_legacy_prefix(scratch,scratch/CONTRACTS[1],'connected-roads-c4')
        def refresh_file_exception(rel):
            p=scratch/SUCCESSOR_FILE;d=json.loads(p.read_text())
            for c in d['historical_contracts'].values():
                if rel in c['reviewed_exceptions']:c['reviewed_exceptions'][rel]['successor_sha256']=sha((scratch/rel).read_bytes())
            p.write_text(json.dumps(d))
        # A normal protected creature prefix byte must still be rejected.
        p=scratch/'src/underwater_creature_art_data/part_000.inc';p.write_bytes(p.read_bytes()+b'\n')
        expect_failure(check,'protected creature file changed',results);restore()
        p=scratch/'src/asset_data/part_000.inc';p.write_bytes(p.read_bytes()+b'\n')
        expect_failure(check,'unreviewed background file hash',results);restore()
        # Even an incorrectly refreshed file exception cannot hide actor changes.
        rel='src/asset_data/part_023.inc';p=scratch/rel;text=p.read_text();needle='const unsigned char sprite_data';where=text.index(needle);comma=text.index(',',text.index('{',where));start=text.rfind(' ',0,comma)+1
        # Edit the first decimal initializer token, preserving valid C structure.
        import re
        hit=re.search(r'\d+',text[text.index('{',where):]);offset=text.index('{',where)+hit.start();value=hit.group();text=text[:offset]+str((int(value)+1)%256)+text[offset+len(value):];p.write_text(text)
        refresh_file_exception(rel);expect_failure(check,'creature array changed despite refreshed chunk hash',results);restore()
        rel='assets/generate_assets.py';p=scratch/rel;p.write_text(p.read_text().replace('def hero(direction,frame):','def hero(direction,frame):\n    marker=1',1));refresh_file_exception(rel)
        expect_failure(check,'hero authoring changed despite refreshed source hash',results);restore()
        p=scratch/CONTRACTS[1];p.write_bytes(p.read_bytes()+b'\n')
        expect_failure(check,'historical contract edited',results);restore()
        (scratch/'src/asset_data/part_999.inc').write_text('\n')
        expect_failure(check,'unexpected base asset chunk',results);restore()
        expect_failure(lambda:validate_legacy_prefix(scratch,scratch/CONTRACTS[1],'unreviewed-world'),'unknown successor mode',results)
    assert before=={p:sha((ROOT/p).read_bytes())for p in paths},'Probe changed working inputs'
    report={'passed':True,'cases':results,'root_guard_inputs_unchanged':True}
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':True,'checks':len(results),'root_guard_inputs_unchanged':True}))
if __name__=='__main__':main()
