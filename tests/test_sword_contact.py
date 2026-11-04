#!/usr/bin/env python3
"""Exercise the production melee and damage paths for sword contact."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def function(source, name):
    match = re.search(r'^(?:static )?(?:COLD )?(?:void|int) ' + name + r'\([^;{}]*\)\s*\{',
                      source, re.MULTILINE)
    assert match, f'Missing production function {name}'
    start = match.start()
    depth = 0
    for end in range(source.index('{', start), len(source)):
        if source[end] == '{':
            depth += 1
        elif source[end] == '}':
            depth -= 1
            if depth == 0:
                return source[start:end + 1]
    raise AssertionError(f'Unterminated production function {name}')


game = (ROOT / 'src/game.c').read_text(encoding='utf-8')
gear = (ROOT / 'src/gear_runtime.c').read_text(encoding='utf-8')
parts = [function(gear, name) for name in
         ('game_health_hurt', 'game_enemy_stagger', 'game_enemy_hurt',
          'clear_path', 'game_melee_hit')]
parts += [function(game, name) for name in
          ('damage_amount', 'damage_phase', 'damage', 'update_charger_contact',
           'sword_blocks_contact',
           'update_enemies', 'update_boss', 'shot_segment_clear', 'update_shots')]

with tempfile.TemporaryDirectory(prefix='sword-contact-') as temporary:
    out = Path(temporary)
    (out / 'production.inc').write_text('\n'.join(parts) + '\n', encoding='utf-8')
    common = ['cc', '-std=c99', '-O1', '-Wall', '-Wextra', '-Werror',
              '-Wno-misleading-indentation', '-pedantic', '-Isrc', '-I' + str(out),
              'tests/sword_contact_host.c', 'src/weapon_actions.c',
              'src/equipment_data.c', 'src/combat_rules.c']
    for name, flags in (('strict', []),
                        ('sanitized', ['-fsanitize=address,undefined',
                                       '-fno-omit-frame-pointer'])):
        executable = out / name
        subprocess.run([*common, *flags, '-o', str(executable)], cwd=ROOT, check=True)
        subprocess.run([str(executable)], cwd=ROOT, check=True)
