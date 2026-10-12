#!/usr/bin/env python3
"""Authenticate the selected music successor; preserve exact historical proofs.

Only music inputs/generated data, PSG pitches and music-credit spans may change
production bytes. Current gameplay/geometry run on current sources. Historical
proofs run in an authenticated reconstruction of the previous main tree.
"""
from contextlib import contextmanager
from pathlib import Path
import argparse, base64, copy, gzip, hashlib, json, os, subprocess, sys, tempfile
import verify_review_successor as prior

ROOT=Path(__file__).resolve().parents[1]
CONTRACT_PATH='docs/selected-music/contract.json'
INVERSE_PATH='docs/selected-music/parent-inverse.json.gz'
CONTRACT_SHA='623cbcc958f7a0d51951444cbe250d31fe77b955f4323e30c31eca0b27b746a1'
sha=lambda data:hashlib.sha256(data).hexdigest()

def allowed(path):
    return path.startswith(('assets/music/selected/','src/music_data/','src/ending_credits_text_data/')) or path in {
        'src/music_data.c','src/music_data.h','src/music_catalog.h','src/horizons_audio.c',
        'assets/ending_credits.json','assets/ending_credits_text_metrics.json',
        'src/ending_credits_text.c','src/ending_credits_text.h'}

def load():
    raw=(ROOT/CONTRACT_PATH).read_bytes()
    assert sha(raw)==CONTRACT_SHA,'selected music contract changed'
    c=json.loads(raw);p=prior.load()
    assert c['schema']==1 and c['name']=='owner-selected-music-successor'
    assert c['parent_production']==p['current_production']
    assert c['immutable_proofs']==p['immutable_proofs']
    old,new=c['parent_production'],c['current_production']
    changed={k for k in old.keys()&new.keys() if old[k]!=new[k]}
    assert changed==set(c['changed'])
    assert set(c['added'])==new.keys()-old.keys() and set(c['removed'])==old.keys()-new.keys()
    assert all(allowed(k) for k in changed|set(c['added'])|set(c['removed'])),'non-music production delta'
    assert {k:v for k,v in c['parent_files'].items() if prior.production_path(k)}==old
    assert set(c['parent_files'])==set(c['parent_modes'])
    for path in c['parent_files']:prior.safe_path(path)
    return c

def state(c):
    production={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for root in ('src','assets')
                for p in (ROOT/root).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    production.update({k:sha((ROOT/k).read_bytes()) for k in ('linker.ld','Makefile','LICENSE')})
    return {'production':production,'proofs':{k:sha((ROOT/k).read_bytes()) for k in c['immutable_proofs']},
            'helpers':{k:sha((ROOT/k).read_bytes()) for k in c['current_helpers']},
            'inverse':sha((ROOT/INVERSE_PATH).read_bytes()),'prior_inverse':sha((ROOT/prior.INVERSE_PATH).read_bytes())}

def authenticate(c,s):
    assert s['production']==c['current_production'],'unreviewed production bytes or file set'
    assert s['proofs']==c['immutable_proofs'],'historical proof changed'
    assert s['helpers']==c['current_helpers'],'selected music helper changed'
    assert s['inverse']==c['inverse_sha256'],'selected music inverse changed'
    assert s['prior_inverse']==prior.load()['inverse_sha256'],'historical inverse changed'

def negatives(c,s):
    authenticate(c,s);rejected=[]
    probes=[('production',p) for p in ('src/game.c','src/save5.c','LICENSE','src/horizons_audio.c',
        'assets/music/selected/catalog.json',*[p for p in c['added'] if p.endswith('.raw')])]
    probes += [('helpers',p) for p in c['current_helpers']]
    probes += [('proofs',p) for p in c['immutable_proofs']]
    for group,path in probes:
        modified={**s,group:{**s[group],path:'0'*64}}
        try:authenticate(c,modified)
        except AssertionError:rejected.append(group+': '+path)
        else:raise AssertionError('accepted mutation '+path)
    for modified in ({**s,'inverse':'0'*64},{**s,'production':{**s['production'],'src/unreviewed.c':'0'*64}}):
        try:authenticate(c,modified)
        except AssertionError:rejected.append('inverse/extra-file tampering')
        else:raise AssertionError('accepted mutation')
    return rejected

@contextmanager
def parent_view(c):
    packed=(ROOT/INVERSE_PATH).read_bytes();assert sha(packed)==c['inverse_sha256']
    restored={k:base64.b64decode(v,validate=True) for k,v in json.loads(gzip.decompress(packed)).items()}
    assert {k:sha(v) for k,v in restored.items()}==c['inverse_files_sha256']
    files={k:restored[k] if k in restored else (ROOT/k).read_bytes() for k in c['parent_files']}
    assert {k:sha(v) for k,v in files.items()}==c['parent_files'],'parent bytes changed'
    assert prior.git_tree(files,c['parent_modes'])==c['parent_tree'],'not the exact previous main tree'
    with tempfile.TemporaryDirectory(prefix='selected-music-prior-proof-only-') as d:
        view=Path(d)
        for rel,data in files.items():
            path=view/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            path.chmod(int(c['parent_modes'][rel][-3:],8))
        yield view

def verify(chain=True):
    c=load();authenticate(c,state(c))
    if not chain:return c,None
    with parent_view(c) as view:
        saved=prior.ROOT;prior.ROOT=view
        try:_,history=prior.verify()
        finally:prior.ROOT=saved
    return c,history

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--current-geometry',action='store_true')
    mode.add_argument('--historical-ui',action='store_true')
    mode.add_argument('--renderer-negatives',action='store_true')
    mode.add_argument('--parent-tests',action='store_true')
    p.add_argument('--parent',action='store_true');p.add_argument('--output',type=Path)
    args=p.parse_args();assert not args.parent or args.historical_ui
    c,_=verify(chain=False);rejected=negatives(c,state(c))
    if args.current_geometry:
        path=ROOT/'tests/test_gbj_return_geometry.py';raw=path.read_bytes()
        assert sha(raw)==c['immutable_proofs'][path.relative_to(ROOT).as_posix()]
        source=raw.decode();before='from verify_gbj_font_successor import verify'
        assert source.count(before)==1
        source=source.replace(before,'from selected_music_boundary import verify')
        try:exec(compile(source,str(path),'exec'),{'__name__':'__main__','__file__':str(path)})
        except SystemExit as result:
            if result.code:raise
    else:
        with parent_view(c) as view:
            script='test_review_successor.py' if args.parent_tests else 'verify_review_successor.py'
            command=[sys.executable,str(view/'tests'/script)]
            if args.historical_ui:command.append('--historical-ui')
            if args.renderer_negatives:command.append('--renderer-negatives')
            if args.parent:command.append('--parent')
            subprocess.run(command,cwd=view,check=True,env={**os.environ,'PYTHONPATH':str(view/'tests')})
    report={'result':'PASS','scope':__doc__,'production_files':len(c['current_production']),
            'exact_parent_commit':c['parent_commit'],'contract_sha256':CONTRACT_SHA,
            'rejected_mutations':len(rejected),'historical_gameplay_claimed':False}
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':main()
