#!/usr/bin/env python3
"""Synthetic actual-C tap, bounded preparation and field carousel contracts.

These fixtures make no full-acquisition claim.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODULES = ('creatures', 'creature_data', 'progression', 'recruit_notice',
           'companion_guide', 'companion_guide_text', 'ui')


def main():
    link = ['-Wl,-dead_strip'] if sys.platform == 'darwin' else ['-Wl,--gc-sections']
    with tempfile.TemporaryDirectory(prefix='field-carousel-') as temp:
        for name, extra in [('strict', []), ('sanitized', [
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
            target = Path(temp) / name
            subprocess.run([os.environ.get('HOST_CC', 'cc'), '-std=c99', '-O2',
                            '-Wall', '-Wextra', '-Werror', '-Wno-misleading-indentation',
                            '-ffunction-sections', '-fdata-sections', *link, '-Isrc',
                            *extra, 'tests/field_carousel_native.c',
                            *(f'src/{module}.c' for module in MODULES),
                            '-o', str(target)], cwd=ROOT, check=True)
            result = subprocess.run([str(target)], cwd=ROOT, check=True, text=True,
                                    capture_output=True, env={**os.environ,
                                        'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1',
                                        'UBSAN_OPTIONS': 'halt_on_error=1'})
            print(f'{name}: {result.stdout.strip()}')


if __name__ == '__main__':
    main()
