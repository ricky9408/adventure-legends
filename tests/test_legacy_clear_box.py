#!/usr/bin/env python3
"""Pinned production-predicate box proof. Host evidence, never native pacing."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/legacy-clear-box'
PIN = ROOT / 'tests/fixtures/legacy-clear-box/source-pins.json'
FUNCTIONS = {
    'src/game.c': ('progress_bits', 'ab', 'solid'),
    'src/region_game.c': ('region_game_is_room', 'foot_in', 'region_game_solid'),
    'src/north_game.c': ('north_game_solid',),
    'src/south_game.c': ('south_game_is_room', 'south_game_solid'),
    'src/trials.c': ('trials_is_room', 'trials_solid'),
}
DATA = ('src/asset_collisions.h', 'src/campaign_rules.c', 'src/world.c',
        'src/region_art.c', 'src/north_art.c', 'src/south_art.c')
HEADERS = ('src/world.h', 'src/campaign_rules.h', 'src/region_art.h',
           'src/north_art.h', 'src/south_art.h', 'src/region_game.h',
           'src/trials.h', 'src/regional_quests.h')
UNCHANGED = ('src/region_game.c', 'src/north_game.c', 'src/south_game.c',
             'src/trials.c')


def function_text(path, name):
    text = (ROOT / path).read_text()
    # These pinned predicates have no strings/comments containing braces.
    match = re.search(r'(?:static )?(?:unsigned|int) ' + re.escape(name)
                      + r'\([^;{}]*\)\{', text)
    if not match:
        raise AssertionError((path, name, 'predicate missing'))
    depth = 0
    for end in range(match.end() - 1, len(text)):
        if text[end] == '{':
            depth += 1
        elif text[end] == '}':
            depth -= 1
            if depth == 0:
                return text[match.start():end + 1]
    raise AssertionError((path, name, 'unterminated predicate'))


def closure(path):
    data = (ROOT / path).read_bytes()
    result = {path: data}
    for child in re.findall(rb'^#include "([^"]+\.inc)"', data, re.M):
        child_path = str(Path(path).parent / child.decode())
        result.update(closure(child_path))
    return result


def digest(data):
    return hashlib.sha256(data).hexdigest()


def current_pins():
    result = {'predicates': {}, 'headers': {}, 'data_closures': {},
              'unchanged_modules': {}}
    for path, names in FUNCTIONS.items():
        for name in names:
            result['predicates'][path + ':' + name] = digest(
                function_text(path, name).encode())
    for path in HEADERS:
        result['headers'][path] = digest((ROOT / path).read_bytes())
    for path in UNCHANGED:
        result['unchanged_modules'][path] = digest((ROOT / path).read_bytes())
    for path in DATA:
        files = closure(path)
        h = hashlib.sha256()
        for name, data in sorted(files.items()):
            h.update(name.encode() + b'\0' + digest(data).encode() + b'\n')
        result['data_closures'][path] = {'sha256': h.hexdigest(),
                                      'files': len(files)}
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    current = current_pins()
    expected = json.loads(PIN.read_text())
    if current != expected:
        raise AssertionError('Pinned original collision source changed; review required')
    parts = []
    # Production dependencies precede production solid(), exactly as extracted.
    order = [p for p in FUNCTIONS if p != 'src/game.c'] + ['src/game.c']
    for path in order:
        for name in FUNCTIONS[path]:
            parts.append('/* Unmodified production: ' + path + ':' + name + ' */\n'
                         + function_text(path, name))
    (OUT / 'production_predicates.inc').write_text('\n\n'.join(parts) + '\n')
    sanitize = bool(os.environ.get('LEGACY_BOX_SANITIZE'))
    binary = OUT / ('proof-sanitized' if sanitize else 'proof-strict')
    args = ['cc', '-std=c99', '-O2', '-g', '-Wall', '-Wextra', '-Werror',
            '-pedantic', '-ffunction-sections', '-fdata-sections',
            '-Isrc', '-I' + str(OUT), 'tests/legacy_clear_box_host.c',
            *DATA[1:], '-Wl,--gc-sections', '-o', str(binary)]
    if sanitize:
        args += ['-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                 '-fno-omit-frame-pointer', '-no-pie']
    subprocess.run(args, cwd=ROOT, check=True)
    start = time.monotonic()
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    output = subprocess.run([str(binary)], cwd=ROOT, check=True, env=env,
                            text=True, capture_output=True)
    print(output.stdout, end='')
    if output.stderr:
        print(output.stderr, end='')
    report = json.loads(output.stdout)
    report.update({'scope': 'host equality against unchanged production solid()',
                   'not_native_pacing_acceptance': True,
                   'sanitizers': ['address', 'undefined'] if sanitize else [],
                   'elapsed_seconds': round(time.monotonic() - start, 3),
                   'compiler': subprocess.check_output(['cc', '--version'],
                               text=True).splitlines()[0],
                   'source_pins': current,
                   'certificate_sha256': digest((ROOT / 'src/legacy_clear_box.inc').read_bytes()),
                   'harness_sha256': digest((ROOT / 'tests/legacy_clear_box_host.c').read_bytes())})
    # Confirm the proof never rewrote any original collision source.
    assert current_pins() == expected
    destination = OUT / ('sanitized-report.json' if sanitize else 'strict-report.json')
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print('Report:', destination.relative_to(ROOT))


if __name__ == '__main__':
    main()
