#!/usr/bin/env python3
"""Physical input contracts plus actual extracted engine helpers; no play claim."""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def extract(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


def main():
    source = (ROOT / 'src/game.c').read_text()
    helpers = '\n'.join(extract(source, 'COLD ' + signature) for signature in (
        'void game_field_ability(void)', 'void game_field_companion_toggle(void)',
        'int game_field_context_input(void)'))
    with tempfile.TemporaryDirectory(prefix='field-controls-') as temporary:
        temporary = Path(temporary)
        (temporary / 'field_controls_engine.inc').write_text(helpers)
        for label, flags in [('strict', []), ('sanitized', [
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
            target = temporary / label
            subprocess.run([os.environ.get('HOST_CC', 'cc'), '-std=c99', '-O2',
                            '-Wall', '-Wextra', '-Werror', '-pedantic', '-Isrc',
                            '-I' + str(temporary), *flags,
                            'tests/field_controls_host.c', '-o', str(target)],
                           cwd=ROOT, check=True)
            result = subprocess.run([str(target)], cwd=ROOT, check=True,
                                    capture_output=True, text=True, env={**os.environ,
                                        'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1',
                                        'UBSAN_OPTIONS': 'halt_on_error=1'})
            print(label + ': ' + result.stdout.strip())


if __name__ == '__main__':
    main()
