#!/usr/bin/env python3
"""Production field stages with controlled external outcomes and real weapon actions.

These host fixtures test event ownership and execution order. They do not prove
controller-earned progress, rendering, collision geometry or GBA frame timing.
"""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='field-update-') as temporary:
        for label, flags in [('strict', []), ('sanitized', [
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
            target = Path(temporary) / label
            subprocess.run([
                os.environ.get('HOST_CC', 'cc'), '-std=c99', '-O2', '-Wall',
                '-Wextra', '-Werror', '-pedantic', '-Isrc', *flags,
                'tests/field_update_host.c', 'src/weapon_actions.c',
                'src/equipment_data.c', '-o', str(target)], cwd=ROOT, check=True)
            subprocess.run([str(target)], cwd=ROOT, check=True, env={**os.environ,
                'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1',
                'UBSAN_OPTIONS': 'halt_on_error=1'})


if __name__ == '__main__':
    main()
