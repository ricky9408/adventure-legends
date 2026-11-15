#!/usr/bin/env python3
"""Pin an explicit reviewed redesign path list for the current field boundary.

Candidate listing is read-only. Authoring requires the exact reviewed JSON list;
it cannot approve a prefix, wildcard, protected input, or unrelated extra path.
This command never rewrites an inherited proof, current contract or inverse.
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
import field_controls_boundary as boundary


def candidates(root):
    raw=(root/boundary.CONTRACT_PATH).read_bytes()
    assert boundary.sha(raw)==boundary.CONTRACT_SHA,'current field contract was not authenticated'
    contract=json.loads(raw)
    old=contract['parent_production']
    current={p.relative_to(root).as_posix():boundary.sha(p.read_bytes())
             for folder in ('src','assets') for p in (root/folder).rglob('*')
             if p.is_file() and '__pycache__' not in p.parts}
    current.update({p:boundary.sha((root/p).read_bytes()) for p in ('Makefile','LICENSE','linker.ld')})
    delta={p for p in old.keys()|current.keys() if old.get(p)!=current.get(p)}
    protected={p for p in delta if boundary.protected_input(p)}
    assert not protected,('protected input changed',sorted(protected))
    return sorted(p for p in delta if not boundary.legacy_allowed(p))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=ROOT)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--list-candidates',action='store_true')
    mode.add_argument('--reviewed-paths',type=Path,
                      help='JSON array of individually reviewed exact additional production paths')
    args=parser.parse_args()
    root=args.repo.resolve()
    expected=candidates(root)
    if args.list_candidates:
        print(json.dumps(expected,indent=2))
        return
    reviewed=json.loads(args.reviewed_paths.read_text())
    assert isinstance(reviewed,list) and all(isinstance(path,str) for path in reviewed)
    assert reviewed==sorted(set(reviewed)),'reviewed paths must be sorted and unique'
    assert reviewed==expected,{'error':'reviewed path list and candidate delta differ',
                               'missing':sorted(set(expected)-set(reviewed)),
                               'extra':sorted(set(reviewed)-set(expected))}
    for path in reviewed:
        boundary.safe_path(path)
        assert boundary.production_path(path) and not boundary.protected_input(path)
        assert not any(mark in path for mark in ('*','?','[',']'))
    scope={'schema':1,'name':'lantern-trails-redesign-production-scope',
           'parent_commit':boundary.PARENT_COMMIT,'parent_tree':boundary.PARENT_TREE,
           'scope':'Additional individually reviewed redesign production paths. Exact current hashes remain in the field contract; this list makes no gameplay or visual-quality claim.',
           'additional_paths':reviewed}
    raw=(json.dumps(scope,indent=2,sort_keys=True)+'\n').encode()
    target=root/boundary.REDESIGN_SCOPE_PATH
    verifier=root/'tests/field_controls_boundary.py'
    source,count=re.subn(r"^REDESIGN_SCOPE_SHA='[^']+'$",
                        "REDESIGN_SCOPE_SHA='"+boundary.sha(raw)+"'",verifier.read_text(),flags=re.M)
    assert count==1,'scope pin is missing or ambiguous'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(raw)
    verifier.write_text(source)
    print(json.dumps({'scope_sha256':boundary.sha(raw),'additional_paths':len(reviewed),
                      'scope_path':str(target)}))


if __name__=='__main__':main()
