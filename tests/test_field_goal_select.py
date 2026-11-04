#!/usr/bin/env python3
"""Exercise the production field Select handler with the real journey-goal reader."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'src/game.c').read_text(encoding='utf-8')


def function(name):
    match = re.search(r'^(?:COLD |static inline )?(?:void|u32) ' + name + r'\([^;{}]*\)\s*\{',
                      SOURCE, re.MULTILINE)
    assert match, f'Missing production function {name}'
    start = match.start()
    depth = 0
    for end in range(SOURCE.index('{', start), len(SOURCE)):
        depth += (SOURCE[end] == '{') - (SOURCE[end] == '}')
        if depth == 0:
            return SOURCE[start:end + 1]
    raise AssertionError(f'Unterminated production function {name}')


update = SOURCE[SOURCE.index('void update(void)'):SOURCE.index('COLD void draw_sword(void)')]
assert update.index('quickparty_update(keys,pressed)') < update.index('field_goal_input((unsigned)pressed)')
assert update.index('if(pressed&KEY_START)') < update.index('field_goal_input((unsigned)pressed)')
assert update.index('if(event_frame()||game_state!=PLAY)return;') < update.index('field_goal_input((unsigned)pressed)')
assert update.index('field_goal_input((unsigned)pressed)') < update.index('field_controls_read(')

with tempfile.TemporaryDirectory(prefix='field-goal-select-') as temporary:
    out = Path(temporary)
    (out / 'field_goal_select.inc').write_text(
        '\n'.join(function(name) for name in ('toast', 'field_goal_input', 'play_toast_cache_key', 'obj_add')) + '\n',
        encoding='utf-8')
    common = ['cc', '-std=c99', '-O1', '-Wall', '-Wextra', '-Werror', '-pedantic',
              '-Isrc', '-I' + str(out), 'tests/field_goal_select_host.c',
              'src/journey_goal.c']
    for mode, flags in (('strict', []),
                        ('sanitized', ['-fsanitize=address,undefined',
                                       '-fno-omit-frame-pointer'])):
        target = out / mode
        subprocess.run([*common, *flags, '-o', str(target)], cwd=ROOT, check=True)
        subprocess.run([str(target)], cwd=ROOT, check=True)
