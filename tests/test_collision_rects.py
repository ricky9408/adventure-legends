#!/usr/bin/env python3
"""Exact occupied-union proof against pinned, current production predicates.

This suite owns separate pins. It never refreshes historical clear-box evidence.
Host correctness and isolated ARM placement are not native pacing acceptance.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from test_legacy_clear_box import ROOT, FUNCTIONS, DATA, HEADERS, UNCHANGED, function_text, closure, digest

DATA = DATA + ('src/magma_art.c', 'src/return_art.c')
HEADERS = HEADERS + ('src/magma_game.h', 'src/magma_art.h', 'src/return_game.h', 'src/return_art.h')
OUT = ROOT / 'build/collision-rects'
PIN = ROOT / 'tests/fixtures/collision-rects/source-pins.json'


def current_pins():
    result = {'predicates': {}, 'headers': {}, 'data_closures': {}, 'unchanged_modules': {}}
    for path, names in FUNCTIONS.items():
        for name in names:
            result['predicates'][path + ':' + name] = digest(function_text(path, name).encode())
    for path in HEADERS:
        result['headers'][path] = digest((ROOT / path).read_bytes())
    for path in UNCHANGED:
        result['unchanged_modules'][path] = digest((ROOT / path).read_bytes())
    for path in DATA + ('src/magma_game.c', 'src/return_game.c'):
        files = closure(path)
        h = hashlib.sha256()
        for name, data in sorted(files.items()):
            h.update(name.encode() + b'\0' + digest(data).encode() + b'\n')
        result['data_closures'][path] = {'sha256': h.hexdigest(), 'files': len(files)}
    return result


def extract():
    current = current_pins()
    expected = json.loads(PIN.read_text())
    assert current == expected, 'Current production collision authority changed; review the new snapshot pins explicitly'
    OUT.mkdir(parents=True, exist_ok=True)
    parts = []
    for path in [p for p in FUNCTIONS if p != 'src/game.c'] + ['src/game.c']:
        for name in FUNCTIONS[path]:
            parts.append('/* Current production, verbatim: ' + path + ':' + name + ' */\n' + function_text(path, name))
    (OUT / 'production_predicates.inc').write_text('\n\n'.join(parts) + '\n')
    return current


def compile_harness(binary, sanitize=False, mutation=None):
    args = ['cc', '-std=c99', '-O2', '-g', '-Wall', '-Wextra', '-Werror', '-pedantic',
            '-ffunction-sections', '-fdata-sections', '-Isrc', '-I' + str(OUT),
            'tests/collision_rects_host.c', 'tests/collision_rects_magma_host.c', 'tests/collision_rects_return_host.c', *DATA[1:], '-Wl,--gc-sections', '-o', str(binary)]
    if mutation:
        args += ['-DCOLLISION_RECTS_INCLUDE="' + str(mutation) + '"']
    if sanitize:
        args += ['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-no-pie']
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    current = extract()
    snapshot_digest = digest((ROOT / 'src/collision_rects.inc').read_bytes())
    header_digest = digest((ROOT / 'src/collision_rects.h').read_bytes())
    sanitize = bool(os.environ.get('COLLISION_RECTS_SANITIZE'))
    binary = OUT / ('proof-sanitized' if sanitize else 'proof-strict')
    compile_harness(binary, sanitize)
    started = time.monotonic()
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    result = subprocess.run([str(binary)], cwd=ROOT, env=env, check=True, text=True, capture_output=True)
    report = json.loads(result.stdout)
    report.update({'scope': 'exact rectangle unions against current production solid(), region/trials/North/South predicates and the actual Magma/Return modules',
                   'not_native_pacing_acceptance': True, 'sanitizers': ['address', 'undefined'] if sanitize else [],
                   'elapsed_seconds': round(time.monotonic() - started, 3),
                   'compiler': subprocess.check_output(['cc', '--version'], text=True).splitlines()[0],
                   'source_pins': current,
                   'snapshot_sha256': snapshot_digest,
                   'api_header_sha256': header_digest,
                   'harness_sha256': digest((ROOT / 'tests/collision_rects_host.c').read_bytes()),
                   'magma_test_wrapper_sha256': digest((ROOT / 'tests/collision_rects_magma_host.c').read_bytes()),
                   'return_test_wrapper_sha256': digest((ROOT / 'tests/collision_rects_return_host.c').read_bytes())})
    if not sanitize:
        source = (ROOT / 'src/collision_rects.inc').read_text()
        mutations = {
            'extra_foot_dilation': ('s->x-5,s->y-5', 's->x-6,s->y-5'),
            'torch_gate_inverted': ('if(torches!=3)', 'if(torches==3)'),
            'campaign_right_edge_lost': ('s->x+s->w-dx-1', 's->x+s->w-dx-2'),
            'magma_row_right_edge_lost': ('band[1]-1,end', 'band[1]-2,end'),
            'magma_prop_left_edge_lost': ('x-11,y-11,x+10,y+10', 'x-10,y-11,x+10,y+10'),
            'clip_right_edge_lost': ('if(r>b->x1)r=b->x1;', 'if(r>b->x1)r=b->x1-1;'),
            'capacity_off_by_one': ('if(b->count==b->cap)return 0;', 'if(b->count>b->cap)return 0;'),
            'return_dynamic_shapes_omitted': ('count=return_game_collision_rects(dynamic);', 'count=0;'),
            'overflow_claims_success': ('if(b->count==b->cap)return 0;', 'if(b->count==b->cap)return 1;'),
        }
        controls = {}
        for name, (old, new) in mutations.items():
            assert old in source, (name, 'mutation anchor missing; review required')
            include = OUT / ('negative-' + name + '.inc')
            include.write_text(source.replace(old, new))
            mutant = OUT / ('negative-' + name)
            compile_harness(mutant, mutation=include)
            target_room = {'extra_foot_dilation': 16, 'torch_gate_inverted': 2, 'campaign_right_edge_lost': 4, 'magma_row_right_edge_lost': 38, 'magma_prop_left_edge_lost': 38, 'return_dynamic_shapes_omitted': 55}.get(name, 0)
            rejected = subprocess.run([str(mutant), str(target_room)], cwd=ROOT, text=True, capture_output=True)
            assert rejected.returncode != 0, (name, 'negative control was not rejected')
            controls[name] = {'rejected': True, 'exit_code': rejected.returncode,
                              'reason': rejected.stderr.strip().splitlines()[0]}
        report['negative_controls'] = controls
    assert current_pins() == current, 'Collision authority changed during proof'
    assert digest((ROOT / 'src/collision_rects.inc').read_bytes()) == snapshot_digest, 'Snapshot changed during proof'
    assert digest((ROOT / 'src/collision_rects.h').read_bytes()) == header_digest, 'API header changed during proof'
    destination = OUT / ('sanitized-report.json' if sanitize else 'strict-report.json')
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'source_pins'}, indent=2))
    print('Report:', destination.relative_to(ROOT))


if __name__ == '__main__':
    main()
