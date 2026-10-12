#!/usr/bin/env python3
"""Author the finite review->prior-main inverse from immutable Git objects.

Run only after reviewing the named candidate runtime commit. This writes new
review contract artifacts and its verifier pin; no runtime or old proof edits.
"""
from pathlib import Path
import argparse, base64, gzip, hashlib, json, re, subprocess
from verify_review_successor import (PARENT_COMMIT, PARENT_TREE, CONTRACT_PATH,
                                    INVERSE_PATH, production_path, music_license_path,
                                    immutable_paths, git_tree, sha)


def git(repo, *args, data=None):
    return subprocess.check_output(['git', '-C', str(repo), *args], input=data)


def tree(repo, ref):
    rows = {}
    for row in git(repo, 'ls-tree', '-r', '-z', ref).split(b'\0'):
        if not row:
            continue
        meta, path = row.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        assert kind == 'blob' and mode in ('100644', '100755'), ('unsupported input', path)
        rows[path.decode()] = (mode, oid)
    ids = sorted({oid for _, oid in rows.values()})
    packed = git(repo, 'cat-file', '--batch', data=('\n'.join(ids) + '\n').encode())
    blobs = {}
    offset = 0
    for want in ids:
        end = packed.index(b'\n', offset)
        oid, kind, count = packed[offset:end].decode().split()
        assert oid == want and kind == 'blob'
        offset = end + 1
        count = int(count)
        blobs[oid] = packed[offset:offset + count]
        offset += count
        assert packed[offset:offset + 1] == b'\n'
        offset += 1
    assert offset == len(packed)
    return {p: blobs[oid] for p, (_, oid) in rows.items()}, {p: mode for p, (mode, _) in rows.items()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--candidate-ref', required=True)
    p.add_argument('--output-root', type=Path, required=True)
    a = p.parse_args()
    commit = git(a.repo, 'rev-parse', a.candidate_ref + '^{commit}').decode().strip()
    candidate_tree = git(a.repo, 'rev-parse', commit + '^{tree}').decode().strip()
    parent, modes = tree(a.repo, PARENT_COMMIT)
    current, _ = tree(a.repo, commit)
    assert git_tree(parent, modes) == PARENT_TREE
    parent_hashes = {p: sha(b) for p, b in parent.items()}
    production = {p: sha(b) for p, b in current.items() if production_path(p)}
    immutable = immutable_paths(parent)
    for path in immutable | {p for p in parent if music_license_path(p)}:
        assert path in current and parent[path] == current[path], ('immutable proof/music/license changed', path)
    assert {p for p in current if music_license_path(p)} == {p for p in parent if music_license_path(p)}
    restored = {p: b for p, b in parent.items() if current.get(p) != b}
    inverse = gzip.compress((json.dumps({p: base64.b64encode(b).decode() for p, b in sorted(restored.items())},
                                      sort_keys=True, separators=(',', ':')) + '\n').encode(), mtime=0)
    parent_prod = {p: h for p, h in parent_hashes.items() if production_path(p)}
    c = {'schema': 1, 'name': 'adventure-review-to-exact-main', 'parent_commit': PARENT_COMMIT,
         'parent_tree': PARENT_TREE, 'candidate_commit': commit, 'candidate_tree': candidate_tree,
         'scope': 'Exact current production authentication and exact prior-main historical proofs. '
                  'Historical reconstruction is never a release ROM input or current gameplay evidence.',
         'parent_files': parent_hashes, 'parent_modes': modes, 'current_production': production,
         'immutable_proofs': {p: parent_hashes[p] for p in sorted(immutable)},
         'music_license': {p: parent_hashes[p] for p in sorted(parent) if music_license_path(p)},
         'added': sorted(production.keys() - parent_prod.keys()),
         'removed': sorted(parent_prod.keys() - production.keys()),
         'changed': sorted(p for p in production.keys() & parent_prod.keys() if production[p] != parent_prod[p]),
         'inverse_files_sha256': {p: sha(b) for p, b in sorted(restored.items())},
         'inverse_sha256': sha(inverse)}
    contract = (json.dumps(c, indent=2, sort_keys=True) + '\n').encode()
    verifier = a.output_root / 'tests/verify_review_successor.py'
    source = verifier.read_text()
    source, n = re.subn(r"^CONTRACT_SHA = '[^']+'$", "CONTRACT_SHA = '" + sha(contract) + "'", source, flags=re.M)
    assert n == 1
    for path, data in ((CONTRACT_PATH, contract), (INVERSE_PATH, inverse)):
        target = a.output_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    verifier.write_text(source)
    print(json.dumps({'candidate_commit': commit, 'candidate_tree': candidate_tree,
                      'contract_sha256': sha(contract), 'inverse_sha256': sha(inverse),
                      'changed_production_files': len(c['changed']), 'restored_files': len(restored)}))


if __name__ == '__main__':
    main()
