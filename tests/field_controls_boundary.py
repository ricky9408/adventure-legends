#!/usr/bin/env python3
"""Authenticate current field controls/audio and preserve exact 4005 proofs.

Historical views supply source-only inherited proofs. Every current gameplay,
geometry, controller input and native ROM gate stays on the actual current tree.
"""
from contextlib import contextmanager
from pathlib import Path
import argparse,base64,copy,gzip,hashlib,json,os,subprocess,sys,tempfile
from verify_review_successor import git_tree,production_path,safe_path

ROOT=Path(__file__).resolve().parents[1]
PARENT_COMMIT='4005fa2c9e7cf7bcc92576b16753dc4022b8a5a8'
PARENT_TREE='b56a6e59968c2ed873dfa2c14fadb6cc8c1d3f91'
CONTRACT_PATH='docs/field-controls/contract.json'
INVERSE_PATH='docs/field-controls/parent-inverse.json.gz'
CONTRACT_SHA='e79574142f25ff8299d9af97f02112400cc29ec52ff192cda77507a1f41f1b15'
SELECTED_CONTRACT_SHA='e5d70fa79ab143cbef6ac20fa2449659318233b2bfb303d700baeb5b9421720e'
sha=lambda data:hashlib.sha256(data).hexdigest()


def allowed(path):
    return path.startswith(('src/ui_data/','src/companion_guide_text_data/')) or path in {
        'src/game.c','src/game_shop.c','src/modal_blit.inc','src/ui.c',
        'src/field_controls.h','src/quickparty.c','src/quickparty.h',
        'src/power_aim_hold.h','src/music.c','src/magma_powers.c','src/magma_powers.h',
        'src/return_interact.inc','src/underwater_game.c',
        'assets/campaign_dialogue.json','assets/companion_guide_commands.json',
        'assets/companion_guide_commands/commands_065_096.json',
        'assets/companion_guide_commands/commands_097_128.json',
        'assets/companion_guide_text_metrics.json','assets/covenants_power_ui.json',
        'assets/covenants_ui_texts.json','assets/generate_ui.py','assets/generate_companion_guide.py',
        'assets/horizons_region/dialogue_ja.json','assets/horizons_ui.json','assets/magma_ui.json',
        'assets/player_feedback_ui.json','assets/return_region/dialogue.json',
        'assets/return_region/dialogue_ja.json','assets/ui_texts.json',
        'assets/ui_texts_covenants.json','assets/ui_texts_horizons.json',
        'assets/ui_texts_player_feedback.json','assets/ui_texts_return.json','assets/underwater_ui.json'}


def protected_input(path):
    return path.startswith(('assets/music/','assets/fonts/','src/music_data/',
                             'src/ending_credits_text_data/')) or path in {
        'src/music_data.c','src/music_data.h','src/music_catalog.h','src/horizons_audio.c',
        'src/ending_credits_text.c','src/ending_credits_text.h','assets/ending_credits.json',
        'assets/ending_credits_text_metrics.json','tools/generate_music.py','LICENSE','Makefile','linker.ld'} or path.endswith('-LICENSE.txt')


def immutable_paths(parent,selected):
    fixed=set(selected['immutable_proofs'])|{
        'docs/selected-music/contract.json','docs/selected-music/parent-inverse.json.gz',
        'tests/selected_music_boundary.py','tests/test_selected_music_snapshot.py',
        'tests/verify_review_successor.py','tests/test_review_successor.py'}
    fixed.update(p for p in parent if p.startswith('docs/') and ('contract' in p or p.endswith('.json.gz')))
    fixed.update(p for p in parent if p.startswith('tests/fixtures/'))
    return fixed


def helper_inventory(root=None):
    root=ROOT if root is None else root
    return {p.relative_to(root).as_posix():sha(p.read_bytes())
            for folder in ('tests','tools') for p in (root/folder).iterdir()
            if p.is_file() and p.suffix in ('.py','.c','.h','.sh','.json')
            and p.relative_to(root).as_posix()!='tests/field_controls_boundary.py'}


def load(contract_bytes=None):
    raw=(ROOT/CONTRACT_PATH).read_bytes() if contract_bytes is None else contract_bytes
    assert sha(raw)==CONTRACT_SHA,'field controls contract changed or not authored'
    c=json.loads(raw)
    assert c['schema']==1 and c['name']=='field-controls-audio-successor'
    assert c['parent_commit']==PARENT_COMMIT and c['parent_tree']==PARENT_TREE
    selected_raw=(ROOT/'docs/selected-music/contract.json').read_bytes()
    assert sha(selected_raw)==SELECTED_CONTRACT_SHA,'inherited selected-music contract changed'
    selected=json.loads(selected_raw)
    assert c['parent_production']==selected['current_production']
    assert set(c['parent_files'])==set(c['parent_modes'])
    assert {p:v for p,v in c['parent_files'].items() if production_path(p)}==c['parent_production']
    assert set(c['immutable_proofs'])==immutable_paths(c['parent_files'],selected)
    assert all(c['parent_files'][p]==v for p,v in c['immutable_proofs'].items())
    old,new=c['parent_production'],c['current_production']
    changed={p for p in old.keys()&new.keys() if old[p]!=new[p]}
    assert changed==set(c['changed']) and set(c['added'])==new.keys()-old.keys() and set(c['removed'])==old.keys()-new.keys()
    assert all(allowed(p) for p in changed|set(c['added'])|set(c['removed'])),'unapproved production delta'
    assert set(c['protected_inputs'])=={p for p in c['parent_files'] if protected_input(p)}
    assert all(c['parent_files'][p]==v and (not production_path(p) or new.get(p)==v)
               for p,v in c['protected_inputs'].items()),'approved music/font/license/build boundary changed'
    assert c['historical_helpers']==selected['current_helpers']
    assert all(c['parent_files'][p]==v for p,v in c['historical_helpers'].items())
    assert set(c['inverse_files_sha256'])<=set(c['parent_files'])
    assert '.gitignore' in c['inverse_files_sha256'],'historical housekeeping must be self-contained'
    for path in c['parent_files']:safe_path(path)
    return c


def state(c):
    production={p.relative_to(ROOT).as_posix():sha(p.read_bytes())
        for folder in ('src','assets') for p in (ROOT/folder).rglob('*')
        if p.is_file() and '__pycache__' not in p.parts}
    production.update({p:sha((ROOT/p).read_bytes()) for p in ('linker.ld','Makefile','LICENSE')})
    return {'production':production,'helpers':helper_inventory(),
        'proofs':{p:sha((ROOT/p).read_bytes()) for p in c['immutable_proofs']},
        'protected':{p:sha((ROOT/p).read_bytes()) for p in c['protected_inputs']},
        'inverse':sha((ROOT/INVERSE_PATH).read_bytes())}


def authenticate(c,s):
    for actual,expected,message in (
        ('production','current_production','unreviewed production bytes or file set'),
        ('helpers','current_helpers','unreviewed helper bytes or file set'),
        ('proofs','immutable_proofs','inherited proof changed'),
        ('protected','protected_inputs','approved music/font/license/build input changed')):
        assert s[actual]==c[expected],message
    assert s['inverse']==c['inverse_sha256'],'field controls inverse changed'


def negatives(c,s):
    authenticate(c,s);rejected=[]
    for group,paths in (('production',set(c['changed'])|set(c['added'])|{'src/save5.c','LICENSE'}),
                        ('helpers',c['current_helpers']),('proofs',c['immutable_proofs']),
                        ('protected',c['protected_inputs'])):
        for path in sorted(paths):
            modified={**s,group:{**s[group],path:'0'*64}}
            try:authenticate(c,modified)
            except AssertionError:rejected.append(group+': '+path)
            else:raise AssertionError('accepted mutation '+path)
    for group,path in (('production','src/unreviewed.c'),('helpers','tests/unreviewed.py')):
        modified={**s,group:{**s[group],path:'0'*64}}
        try:authenticate(c,modified)
        except AssertionError:rejected.append('unexpected '+path)
        else:raise AssertionError('accepted extra '+path)
    for group,path in (('production','src/game.c'),('helpers','tests/current_field_controls.py')):
        modified=copy.deepcopy(s);del modified[group][path]
        try:authenticate(c,modified)
        except AssertionError:rejected.append('deleted '+path)
        else:raise AssertionError('accepted deletion '+path)
    try:authenticate(c,{**s,'inverse':'0'*64})
    except AssertionError:rejected.append('inverse tampering')
    else:raise AssertionError('accepted inverse tampering')
    try:load((ROOT/CONTRACT_PATH).read_bytes()+b' ')
    except AssertionError:rejected.append('contract tampering')
    else:raise AssertionError('accepted contract tampering')
    return rejected


@contextmanager
def parent_view(c):
    packed=(ROOT/INVERSE_PATH).read_bytes()
    assert sha(packed)==c['inverse_sha256'],'field controls inverse changed'
    restored={p:base64.b64decode(value,validate=True) for p,value in json.loads(gzip.decompress(packed)).items()}
    assert {p:sha(data) for p,data in restored.items()}==c['inverse_files_sha256'],'inverse byte set changed'
    files={p:restored[p] if p in restored else (ROOT/p).read_bytes() for p in c['parent_files']}
    assert {p:sha(data) for p,data in files.items()}==c['parent_files'],'parent bytes changed'
    assert git_tree(files,c['parent_modes'])==PARENT_TREE,'not the exact 4005 tree'
    with tempfile.TemporaryDirectory(prefix='field-controls-exact-4005-proof-only-') as temp:
        view=Path(temp)
        for path,data in files.items():
            target=view/path;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data);target.chmod(int(c['parent_modes'][path][-3:],8))
        yield view


def historical(c,args=None,chain_only=False):
    with parent_view(c) as view:
        command=[sys.executable,'-c','import selected_music_boundary as b; b.verify()'] if chain_only else [sys.executable,str(view/'tests/selected_music_boundary.py'),*(args or [])]
        subprocess.run(command,cwd=view,check=True,env={**os.environ,'PYTHONPATH':str(view/'tests')})


def verify(chain=True):
    c=load();authenticate(c,state(c))
    if chain:historical(c,chain_only=True)
    return c,None


def main():
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group()
    for flag in ('current-geometry','historical-ui','renderer-negatives','parent-tests'):
        mode.add_argument('--'+flag,action='store_true')
    parser.add_argument('--parent',action='store_true');parser.add_argument('--output',type=Path)
    args=parser.parse_args();assert not args.parent or args.historical_ui
    c,_=verify(chain=False);rejected=negatives(c,state(c))
    if args.current_geometry:
        path=ROOT/'tests/test_gbj_return_geometry.py';raw=path.read_bytes()
        assert sha(raw)==c['immutable_proofs'][path.relative_to(ROOT).as_posix()]
        source=raw.decode();before='from verify_gbj_font_successor import verify';assert source.count(before)==1
        source=source.replace(before,'from field_controls_boundary import verify')
        try:exec(compile(source,str(path),'exec'),{'__name__':'__main__','__file__':str(path)})
        except SystemExit as result:
            if result.code:raise
    else:
        flags=[]
        for flag in ('historical_ui','renderer_negatives','parent_tests','parent'):
            if getattr(args,flag):flags.append('--'+flag.replace('_','-'))
        historical(c,flags)
        if args.parent_tests:
            subprocess.run([sys.executable,str(ROOT/'tests/test_field_controls_boundary.py')],cwd=ROOT,check=True)
    report={'result':'PASS','scope':__doc__,'production_files':len(c['current_production']),
        'contract_sha256':CONTRACT_SHA,'exact_parent_commit':PARENT_COMMIT,'exact_parent_tree':PARENT_TREE,
        'rejected_mutations':len(rejected),'historical_gameplay_claimed':False}
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
