#!/usr/bin/env python3
"""Freeze reviewed current controls/audio bytes and an exact 4005 source inverse.

Reads immutable parent Git blobs and the reviewed working tree. The inverse is
proof-only: it is never used to build a release ROM or as current gameplay data.
"""
import argparse,base64,gzip,json,re
from pathlib import Path
from author_review_successor import tree
import field_controls_boundary as boundary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    a=p.parse_args();root=a.repo.resolve()
    parent,modes=tree(root,boundary.PARENT_COMMIT)
    assert boundary.git_tree(parent,modes)==boundary.PARENT_TREE
    hashes={p:boundary.sha(data) for p,data in parent.items()}
    selected=json.loads(parent['docs/selected-music/contract.json'])
    assert boundary.sha(parent['docs/selected-music/contract.json'])==boundary.SELECTED_CONTRACT_SHA
    production={p.relative_to(root).as_posix():boundary.sha(p.read_bytes())
        for folder in ('src','assets') for p in (root/folder).rglob('*')
        if p.is_file() and '__pycache__' not in p.parts}
    production.update({p:boundary.sha((root/p).read_bytes()) for p in ('Makefile','LICENSE','linker.ld')})
    old={p:h for p,h in hashes.items() if boundary.production_path(p)}
    assert old==selected['current_production']
    changed={p for p in old.keys()&production.keys() if old[p]!=production[p]}
    added=production.keys()-old.keys();removed=old.keys()-production.keys()
    assert all(boundary.allowed(p) for p in changed|added|removed),('unapproved runtime delta',sorted(changed|added|removed))
    protected={p:h for p,h in hashes.items() if boundary.protected_input(p)}
    assert {p for p in production if boundary.protected_input(p)}=={p for p in old if boundary.protected_input(p)}
    immutable=boundary.immutable_paths(hashes,selected)
    for path in immutable|set(protected):
        assert boundary.sha((root/path).read_bytes())==hashes[path],('immutable input changed',path)
    before=b'    R16(0x04000200)=16;start_output();'
    after=b'    R16(0x04000004)=8; /* VBlank IRQ for BIOS wait; Timer1 retains PCM IRQ. */\n    R16(0x04000200)=17;start_output();'
    assert parent['src/music.c'].count(before)==1
    assert (root/'src/music.c').read_bytes()==parent['src/music.c'].replace(before,after),'music.c exceeds the reviewed VBlank IRQ-only delta'
    restored={p:data for p,data in parent.items() if p=='.gitignore' or not (root/p).is_file() or (root/p).read_bytes()!=data}
    packed=gzip.compress((json.dumps({p:base64.b64encode(data).decode() for p,data in sorted(restored.items())},sort_keys=True,separators=(',',':'))+'\n').encode(),mtime=0)
    c={'schema':1,'name':'field-controls-audio-successor',
       'parent_commit':boundary.PARENT_COMMIT,'parent_tree':boundary.PARENT_TREE,
       'scope':'Exact current production/helper bytes; historical source-only proofs restore every 4005 byte and mode. Historical fixtures never establish current controls or feed a release build.',
       'parent_files':hashes,'parent_modes':modes,'parent_production':old,
       'current_production':production,'current_helpers':boundary.helper_inventory(root),
       'historical_helpers':selected['current_helpers'],
       'immutable_proofs':{p:hashes[p] for p in sorted(immutable)},'protected_inputs':protected,
       'changed':sorted(changed),'added':sorted(added),'removed':sorted(removed),
       'inverse_files_sha256':{p:boundary.sha(data) for p,data in restored.items()},
       'inverse_sha256':boundary.sha(packed)}
    raw=(json.dumps(c,indent=2,sort_keys=True)+'\n').encode()
    verifier=root/'tests/field_controls_boundary.py';source=verifier.read_text()
    source,n=re.subn(r"^CONTRACT_SHA='[^']+'$","CONTRACT_SHA='"+boundary.sha(raw)+"'",source,flags=re.M);assert n==1
    for name,data in ((boundary.CONTRACT_PATH,raw),(boundary.INVERSE_PATH,packed)):
        target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    verifier.write_text(source)
    print(json.dumps({'contract_sha256':boundary.sha(raw),'inverse_sha256':boundary.sha(packed),
        'parent_tree':boundary.PARENT_TREE,'parent_files':len(parent),'changed_production':len(changed),
        'added_production':len(added),'current_helpers':len(c['current_helpers']),
        'protected_inputs':len(protected),'immutable_proofs':len(immutable),'inverse_files':len(restored)}))


if __name__=='__main__':main()
