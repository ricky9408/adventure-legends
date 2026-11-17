#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
CATALOG = 'tools/trust/check-catalog.json'
SOURCE_SUFFIXES = {'.c', '.h', '.s', '.inc'}
CHECK_SUFFIXES = {'.py', '.c', '.h', '.sh'}
HOST_HEADERS = {
    'region_game_test_ui.h': 'REGION_GAME_HOST_TEST',
    'north_game_test_ui.h': 'NORTH_GAME_HOST_TEST',
    'south_game_test_ui.h': 'SOUTH_GAME_HOST_TEST',
    'magma_game_test_ui.h': 'MAGMA_GAME_HOST_TEST',
    'underwater_game_test_ui.h': 'UNDERWATER_GAME_HOST_TEST',
}


class ContractError(ValueError):
    pass


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def visible_paths(root):
    result = subprocess.run(
        ['git', '-c', 'safe.directory=' + str(root), 'ls-files', '-z',
         '--cached', '--others', '--exclude-standard'],
        cwd=root, check=True, stdout=subprocess.PIPE,
    )
    return sorted(set(result.stdout.decode().rstrip('\0').split('\0')) - {''})


def runtime_snapshot(root):
    paths = sorted((root / 'src').rglob('*')) + [root / 'linker.ld']
    result = {}
    for path in paths:
        if path.is_symlink():
            raise ContractError(f'Runtime inputs cannot be symlinks: {path}')
        if path.is_dir():
            continue
        if not path.is_file():
            raise ContractError(f'Missing runtime input: {path}')
        if path.name != 'linker.ld' and path.suffix not in SOURCE_SUFFIXES:
            raise ContractError(f'Uncompiled input under src/: {path}')
        result[path.relative_to(root).as_posix()] = sha(path)
    if len(result) < 2:
        raise ContractError('Runtime inventory is empty')
    return result


def input_snapshot(root):
    paths = set(runtime_snapshot(root))
    for name in visible_paths(root):
        if not name.startswith(('build/', 'dist/', '.trust/runs/')):
            paths.add(name)
    result = {}
    for name in sorted(paths):
        path = root / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root and root in p.parents):
            raise ContractError(f'Inputs cannot contain symlinks: {name}')
        if not path.is_file():
            raise ContractError(f'Missing input: {name}')
        result[name] = sha(path)
    return result


def snapshot_delta(before, after):
    return {
        'added': sorted(after.keys() - before.keys()),
        'removed': sorted(before.keys() - after.keys()),
        'changed': sorted(name for name in before.keys() & after.keys() if before[name] != after[name]),
    }


def require_unchanged(before, after):
    delta = snapshot_delta(before, after)
    if any(delta.values()):
        raise ContractError('Inputs changed: ' + json.dumps(delta, sort_keys=True))


def build_units(root):
    source = (root / 'Makefile').read_text().replace('\\\n', ' ')
    matches = re.findall(r'^OBJECTS\s*:?=\s*(.+)$', source, re.MULTILINE)
    if len(matches) != 1:
        raise ContractError('Expected one explicit OBJECTS assignment')
    tokens = matches[0].split()
    units = []
    for token in tokens:
        match = re.fullmatch(r'\$\(BUILD\)/([a-zA-Z0-9_/.-]+)\.o', token)
        if not match:
            raise ContractError(f'Unaccounted build object expression: {token}')
        candidates = [f'src/{match[1]}{suffix}' for suffix in ('.c', '.s')
                      if (root / f'src/{match[1]}{suffix}').is_file()]
        if len(candidates) != 1:
            raise ContractError(f'Object needs exactly one translation unit: {token}')
        units.extend(candidates)
    if len(units) != len(set(units)):
        raise ContractError('Duplicate build objects')
    actual = {p.relative_to(root).as_posix() for p in (root / 'src').rglob('*')
              if p.is_file() and p.suffix in {'.c', '.s'}}
    if set(units) != actual:
        raise ContractError(f'Translation units missing from build: {sorted(actual - set(units))}')
    return sorted(units)


def include_edges(root, name):
    edges = []
    guards = []
    for line in (root / name).read_text().splitlines():
        directive = re.match(r'\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)', line)
        if directive:
            op, condition = directive.groups()
            if op in ('if', 'ifdef', 'ifndef'):
                guards.append((op, condition.strip()))
            elif op in ('else', 'elif') and guards:
                guards[-1] = (op, condition.strip())
            elif op == 'endif' and guards:
                guards.pop()
        match = re.match(r'\s*#\s*include\s*"([^"]+)"', line)
        if not match:
            continue
        include = match[1]
        for candidate in ((root / name).parent / include, root / 'src' / include):
            if candidate.is_file():
                if not candidate.resolve().is_relative_to((root / 'src').resolve()):
                    raise ContractError(f'Production include escapes src/: {name}: {include}')
                edges.append(candidate.relative_to(root).as_posix())
                break
        else:
            macro = HOST_HEADERS.get(include)
            producer = root / 'tests' / ('test_' + include.removesuffix('_test_ui.h') + '.py')
            if macro and ('ifdef', macro) in guards and producer.is_file():
                continue
            raise ContractError(f'Unresolved or unguarded include: {name}: {include}')
    return edges


def source_graph(root):
    units = build_units(root)
    graph = {}
    pending = units.copy()
    while pending:
        name = pending.pop()
        if name in graph:
            continue
        graph[name] = include_edges(root, name)
        pending.extend(graph[name])
    actual = set(runtime_snapshot(root)) - {'linker.ld'}
    if actual != graph.keys():
        raise ContractError(f'Source files unreachable from build: {sorted(actual - graph.keys())}')
    return {'translation_units': units, 'includes': dict(sorted(graph.items()))}


def check_paths(root):
    return sorted(name for name in visible_paths(root)
                  if name.startswith(('tests/', 'tools/', 'assets/'))
                  and not name.startswith(('tests/fixtures/', 'tools/sysroot/'))
                  and '__pycache__' not in Path(name).parts
                  and Path(name).suffix in CHECK_SUFFIXES)


def check_references(root, paths):
    by_stem = defaultdict(list)
    for name in paths:
        by_stem[Path(name).stem].append(name)
    graph = {}
    for name in paths:
        references = set()
        if name.endswith('.py'):
            tree = ast.parse((root / name).read_text(), filename=name)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if node.value in paths:
                        references.add(node.value)
                    if node.value in by_stem:
                        references.update(by_stem[node.value])
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        references.update(by_stem.get(alias.name.split('.')[-1], []))
                if isinstance(node, ast.ImportFrom) and node.module:
                    references.update(by_stem.get(node.module.split('.')[-1], []))
        graph[name] = sorted(references - {name})
    return graph


def reference_routes(root, graph):
    policy = root / '.trust/policy.json'
    declared = json.loads(policy.read_text()).get('checks', []) if policy.is_file() else []
    policy_roots = sorted({argument for check in declared for argument in check['command']
                           if argument in graph})
    roots = {'supplemental_host_references': ['tools/run_equipment_rewards_host.py'],
             'gameplay_ci_references': ['tools/run_gameplay_ci.py'],
             'policy_command_references': policy_roots}
    reached = {}
    for suite, pending in roots.items():
        found = set()
        while pending:
            name = pending.pop()
            if name in found:
                continue
            found.add(name)
            pending.extend(graph.get(name, []))
        reached[suite] = found
    return {name: [suite for suite, found in reached.items() if name in found] or ['not_referenced_by_current_roots']
            for name in graph}


def write_catalog(root):
    paths = check_paths(root)
    result = {'schema': 1, 'files': paths,
              'meaning': 'Reviewed file membership only. References do not prove execution or behavior.'}
    target = root / CATALOG
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + '\n')


def validate_catalog(root):
    document = json.loads((root / CATALOG).read_text())
    if document.get('schema') != 1 or not isinstance(document.get('files'), list):
        raise ContractError('Invalid check catalog')
    recorded = document['files']
    if recorded != sorted(set(recorded)):
        raise ContractError('Check catalog must contain unique sorted paths')
    actual = check_paths(root)
    if actual != recorded:
        raise ContractError('Check catalog drift: ' + json.dumps({
            'unreviewed': sorted(set(actual) - set(recorded)),
            'missing': sorted(set(recorded) - set(actual)),
        }))
    return actual


def inventory(root):
    graph = source_graph(root)
    checks = validate_catalog(root)
    references = check_references(root, checks)
    routes = reference_routes(root, references)
    files = []
    for name in sorted(set(visible_paths(root)) | set(runtime_snapshot(root))):
        path = root / name
        if not path.is_file():
            raise ContractError(f'Missing inventoried file: {name}')
        if name.startswith('src/'):
            role = 'generated-production-data' if any(part.endswith('_data') for part in path.parts) else 'production-source'
        elif name.startswith('tests/fixtures/'):
            role = 'historical-fixture'
        elif name in checks:
            role = 'verification-or-generator-code'
        elif name.startswith('assets/'):
            role = 'asset-input-or-authored-output'
        elif name.startswith('docs/'):
            role = 'documentation-or-historical-evidence'
        elif name.startswith(('tests/', 'tools/')):
            role = 'verification-support-data'
        elif name in ('Makefile', 'linker.ld') or name.startswith(('.github/', '.trust/')):
            role = 'build-or-verification-configuration'
        else:
            role = 'repository-metadata-or-delivery'
        row = {'path': name, 'role': role, 'sha256': sha(path)}
        if name in routes:
            row['reference_routes'] = routes[name]
        files.append(row)
    return {
        'schema': 1, 'files': files, 'counts': dict(Counter(row['role'] for row in files)),
        'build': graph, 'check_references': references,
        'limitations': [
            'Static reference reachability is conservative; it is not execution coverage.',
            'Include closure considers every quoted branch; only five named host-test UI headers are excluded under their matching ifdef.',
            'Generated data is classified by its dedicated directory. Other asset files remain inputs-or-outputs until regeneration is demonstrated.',
            'Inventory does not prove tests have meaningful assertions or native gameplay coverage.',
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--refresh-catalog', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.refresh_catalog:
            write_catalog(root)
            print('Updated reviewed file membership; review the catalog diff before accepting it.')
            return 0
        result = inventory(root)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({'result': 'PASS', 'counts': result['counts'],
                          'translation_units': len(result['build']['translation_units'])}))
        return 0
    except (ContractError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
