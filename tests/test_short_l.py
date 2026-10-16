#!/usr/bin/env python3
"""Real-C short-L compatibility and bounded long-picker host contracts.

Synthetic input/roster evidence only. Save/reseat/revocation hooks are counted;
rendering, controller acquisition, hardware timing, and personal SRAM are unused.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/short-l'
MODULES = ('creatures', 'creature_data', 'progression', 'recruit_notice',
           'companion_guide', 'companion_guide_text', 'ui')


def checked(command, log):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            timeout=120, env={**os.environ,
                                'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1',
                                'UBSAN_OPTIONS': 'halt_on_error=1'})
    log.write_text(result.stdout + result.stderr)
    if result.returncode:
        print(result.stdout + result.stderr, end='')
        result.check_returncode()
    return result.stdout.strip()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = OUT / 'report.json'
    report.unlink(missing_ok=True)
    link = ['-Wl,-dead_strip'] if sys.platform == 'darwin' else ['-Wl,--gc-sections']
    runs = []
    with tempfile.TemporaryDirectory(prefix='short-l-') as temporary:
        for label, flags in [('strict', []), ('sanitized', [
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
            target = Path(temporary) / label
            command = [os.environ.get('HOST_CC', 'cc'), '-std=c99', '-O2',
                       '-Wall', '-Wextra', '-Werror', '-Wno-misleading-indentation',
                       '-ffunction-sections', '-fdata-sections', *link, '-Isrc',
                       *flags, 'tests/short_l_host.c',
                       *(f'src/{module}.c' for module in MODULES), '-o', str(target)]
            checked(command, OUT / f'{label}-compile.log')
            output = checked([str(target)], OUT / f'{label}.log')
            print(label + ': ' + output, flush=True)
            runs.append({'mode': label, 'result': output})
    report.write_text(json.dumps({
        'evidence': 'synthetic actual-C short-L and long-picker input contracts',
        'runs': runs,
        'sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                   for path in ('tests/test_short_l.py', 'tests/short_l_host.c',
                                'src/quickparty.c', 'src/quickparty.h',
                                'src/progression.c', 'src/creatures.c',
                                'src/recruit_notice.c')},
        'limits': ['rendering is stubbed', 'save/reseat/revocation hooks are counted',
                   'no controller acquisition or hardware timing tested',
                   'no personal saves read or written'],
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
