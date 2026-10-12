#!/usr/bin/env python3
"""Authenticate the review candidate and exact prior-main historical proof view.

The reconstructed tree is used only for unchanged historical source/UI/renderer
proofs. Current gameplay, geometry, save and native checks use current sources.
"""
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
import argparse, base64, copy, gzip, hashlib, json, os, subprocess, sys, tempfile

ROOT = Path(__file__).resolve().parents[1]
PARENT_COMMIT = 'cc5e88edcd27722d4e48c449fcc8d7d94f87f733'
PARENT_TREE = '362d43f452b2826bd42fa1761e27109f2a818b0c'
CONTRACT_SHA = '547d4eab8635557b34b07a59a348e4b4d9030b525d04fe7752392aad22f4f0db'
CONTRACT_PATH = 'docs/review-successor/contract.json'
INVERSE_PATH = 'docs/review-successor/main-inverse.json.gz'
sha = lambda b: hashlib.sha256(b).hexdigest()


def production_path(path):
    return path.startswith(('src/', 'assets/')) or path in ('linker.ld', 'Makefile', 'LICENSE')


def music_license_path(path):
    return path.startswith(('src/music', 'assets/music/')) or path == 'LICENSE' or path.endswith('-LICENSE.txt')


def immutable_paths(paths):
    """Existing proof code and all existing contract/inverse artifacts stay exact."""
    proof_names = {
        'verify_soundtrack_successor.py', 'test_soundtrack_historical_ui.py',
        'test_soundtrack_geometry.py', 'verify_companion_browsing_successor.py',
        'verify_endroll_successor.py', 'verify_gbj_font_successor.py',
        'verify_late_renderer.py', 'renderer_equipment_successor.py',
        'test_renderer_equipment_successor.py', 'retained_ui_successor.py',
        'retained_ui_story_successor.py', 'test_retained_ui_successor.py',
        'test_retained_ui_story_successor.py', 'test_gbj_return_geometry.py',
        'test_return_geometry.py', 'test_connected_route_copy.py',
    }
    return {p for p in paths if
            (p.startswith('docs/') and ('contract' in p or p.endswith('.json.gz')))
            or p.startswith('docs/soundtrack-successor/')
            or (p.startswith('tests/') and PurePosixPath(p).name in proof_names)
            or p == 'tests/fixtures/render-equipment-i4/reference.json'}


def safe_path(path):
    p = PurePosixPath(path)
    assert not p.is_absolute() and path == str(p) and '..' not in p.parts, ('unsafe inverse path', path)


def git_tree(files, modes):
    """Compute Git's tree object identity without relying on a checkout or Git."""
    nodes = {}
    for path, data in files.items():
        safe_path(path)
        assert modes[path] in ('100644', '100755'), ('unsupported parent mode', path)
        node = nodes
        parts = path.split('/')
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        assert parts[-1] not in node
        node[parts[-1]] = (modes[path], hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).digest())

    def digest(node):
        body = bytearray()
        for name, value in sorted(node.items(), key=lambda pair: pair[0].encode() + (b'/' if isinstance(pair[1], dict) else b'')):
            mode, oid = ('40000', digest(value)) if isinstance(value, dict) else value
            body.extend(mode.encode() + b' ' + name.encode() + b'\0' + oid)
        return hashlib.sha1(b'tree ' + str(len(body)).encode() + b'\0' + body).digest()
    return digest(nodes).hex()


def load(contract_bytes=None):
    raw = (ROOT / CONTRACT_PATH).read_bytes() if contract_bytes is None else contract_bytes
    assert sha(raw) == CONTRACT_SHA, 'review contract changed or not authored'
    c = json.loads(raw)
    assert c['schema'] == 1 and c['name'] == 'adventure-review-to-exact-main'
    assert c['parent_commit'] == PARENT_COMMIT and c['parent_tree'] == PARENT_TREE
    parent, current = c['parent_files'], c['current_production']
    assert set(parent) == set(c['parent_modes'])
    assert all(production_path(p) for p in current)
    assert set(c['immutable_proofs']) == immutable_paths(parent)
    assert all(c['immutable_proofs'][p] == parent[p] for p in c['immutable_proofs'])
    parent_prod = {p: h for p, h in parent.items() if production_path(p)}
    assert set(c['added']) == set(current) - set(parent_prod)
    assert set(c['removed']) == set(parent_prod) - set(current)
    assert set(c['changed']) == {p for p in current.keys() & parent_prod.keys() if current[p] != parent_prod[p]}
    protected = {p for p in parent if music_license_path(p)}
    assert set(c['music_license']) == protected
    assert {p for p in current if music_license_path(p)} == protected
    assert all(c['music_license'][p] == parent[p] == current[p] for p in protected), 'music/license boundary changed'
    assert set(c['inverse_files_sha256']) <= set(parent)
    for p in parent:
        safe_path(p)
        if production_path(p) and current.get(p) != parent[p]:
            assert p in c['inverse_files_sha256'], ('missing inverse byte', p)
    return c


def state(c):
    files = {str(p.relative_to(ROOT)): sha(p.read_bytes())
             for folder in ('src', 'assets') for p in (ROOT / folder).rglob('*')
             if p.is_file() and '__pycache__' not in p.parts}
    for p in ('linker.ld', 'Makefile', 'LICENSE'):
        files[p] = sha((ROOT / p).read_bytes())
    return {'production': files,
            'proofs': {p: sha((ROOT / p).read_bytes()) for p in c['immutable_proofs']},
            'inverse': sha((ROOT / INVERSE_PATH).read_bytes())}


def authenticate(c, s):
    actual, expected = s['production'], c['current_production']
    if actual != expected:
        added = sorted(actual.keys() - expected.keys())
        removed = sorted(expected.keys() - actual.keys())
        changed = sorted(p for p in actual.keys() & expected.keys() if actual[p] != expected[p])
        raise AssertionError({'error': 'unreviewed production bytes or file set',
                              'added': added, 'removed': removed, 'changed': changed})
    assert s['proofs'] == c['immutable_proofs'], 'historical proof input changed'
    assert s['inverse'] == c['inverse_sha256'], 'main inverse archive changed'


def negatives(c, s):
    authenticate(c, s)  # Clean positive first: rejection controls cannot pass vacuously.
    rejected = []

    def reject(label, group, path=None, remove=False):
        changed = copy.deepcopy(s)
        if group == 'inverse':
            changed[group] = '0' * 64
        elif remove:
            del changed[group][path]
        else:
            changed[group][path] = '0' * 64
        assert changed != s, label
        try:
            authenticate(c, changed)
        except AssertionError:
            rejected.append(label)
        else:
            raise AssertionError('accepted negative ' + label)

    for p in sorted(set(c['changed']) | set(c['added']) | set(c['music_license']) | {'src/game.c', 'src/save5.c', 'linker.ld', 'Makefile'}):
        reject('changed ' + p, 'production', p)
    for p in ('src/unreviewed.c', 'assets/unreviewed.json'):
        reject('unexpected ' + p, 'production', p)
    reject('deleted runtime file', 'production', 'src/game.c', remove=True)
    reject('deleted authoring file', 'production', 'assets/ui_texts.json', remove=True)
    for p in sorted(c['immutable_proofs']):
        reject('changed historical proof ' + p, 'proofs', p)
    reject('inverse payload tampering', 'inverse')
    try:
        load((ROOT / CONTRACT_PATH).read_bytes() + b' ')
    except AssertionError:
        rejected.append('review contract tampering')
    else:
        raise AssertionError('accepted contract tampering')
    return rejected


@contextmanager
def parent_view(c):
    packed = (ROOT / INVERSE_PATH).read_bytes()
    assert sha(packed) == c['inverse_sha256']
    restored = {p: base64.b64decode(b, validate=True) for p, b in json.loads(gzip.decompress(packed)).items()}
    assert {p: sha(b) for p, b in restored.items()} == c['inverse_files_sha256'], 'inverse byte set changed'
    files = {}
    for p, want in c['parent_files'].items():
        data = restored[p] if p in restored else (ROOT / p).read_bytes()
        assert sha(data) == want, ('parent byte mismatch', p)
        files[p] = data
    assert git_tree(files, c['parent_modes']) == PARENT_TREE, 'reconstructed tree is not exact prior main'
    with tempfile.TemporaryDirectory(prefix='review-exact-main-proof-only-') as d:
        view = Path(d)
        for p, data in files.items():
            target = view / p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(int(c['parent_modes'][p][-3:], 8))
        assert {str(p.relative_to(view)) for p in view.rglob('*') if p.is_file()} == set(c['parent_files'])
        yield view


def verify(chain=True):
    c = load()
    authenticate(c, state(c))
    if not chain:
        return c, None
    # Import the unchanged checker, then point it only at the authenticated main.
    import verify_soundtrack_successor as prior
    with parent_view(c) as view:
        saved = prior.ROOT
        prior.ROOT = view
        try:
            _, i4 = prior.verify()
            prior.negatives(prior.load(), prior.state(prior.load()))
        finally:
            prior.ROOT = saved
    return c, i4


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--historical-ui', action='store_true')
    mode.add_argument('--renderer-negatives', action='store_true')
    mode.add_argument('--current-geometry', action='store_true')
    p.add_argument('--parent', action='store_true', help='Historical UI parent negatives; requires --historical-ui')
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    assert not a.parent or a.historical_ui
    c, _ = verify(chain=False)
    rejected = negatives(c, state(c))
    if a.current_geometry:
        # Preserve the original geometry adapter byte-for-byte, changing only
        # which exact boundary authenticates its *current* source inputs.
        path = ROOT / 'tests/test_gbj_return_geometry.py'
        raw = path.read_bytes()
        assert sha(raw) == c['immutable_proofs'][str(path.relative_to(ROOT))]
        source = raw.decode()
        before = 'from verify_gbj_font_successor import verify'
        assert source.count(before) == 1
        source = source.replace(before, 'from verify_review_successor import verify')
        try:
            exec(compile(source, str(path), 'exec'), {'__name__': '__main__', '__file__': str(path)})
        except SystemExit as result:
            if result.code:
                raise
    else:
        with parent_view(c) as view:
            script = 'test_soundtrack_historical_ui.py' if a.historical_ui else 'verify_soundtrack_successor.py'
            cmd = [sys.executable, str(view / 'tests' / script)]
            if a.parent:
                cmd.append('--parent')
            if a.renderer_negatives:
                cmd.append('--renderer-negatives')
            subprocess.run(cmd, cwd=view, check=True, env={**os.environ, 'PYTHONPATH': str(view / 'tests')})
    report = {'result': 'PASS', 'scope': __doc__, 'contract_sha256': CONTRACT_SHA,
              'candidate_runtime_commit': c['candidate_commit'], 'exact_parent_commit': PARENT_COMMIT,
              'exact_parent_tree': PARENT_TREE, 'current_production_files': len(c['current_production']),
              'historical_tree_files': len(c['parent_files']), 'mutation_negatives': rejected,
              'current_gameplay_claimed_from_inverse': False}
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'mutation_negatives'}
                     | {'mutation_negatives_rejected': len(rejected)}))


if __name__ == '__main__':
    main()
