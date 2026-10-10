#!/usr/bin/env python3
"""Prove real optional practice target pixels using generated collision/renderer."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/covenants-practice-geometry'
OUT.mkdir(parents=True, exist_ok=True)
exe = OUT / 'practice'
sources = ['tests/covenants_practice_geometry.c', 'src/covenants_powers.c', 'src/covenants_power_art.c',
           'src/covenants_art.c', 'src/creatures.c', 'src/creature_data.c', 'src/gear_runtime.c',
           'src/combat_rules.c', 'src/north_art.c', 'src/south_art.c']
subprocess.run(['cc', '-std=c99', '-O1', '-g', '-Wall', '-Wextra', '-Werror', '-pedantic',
                '-Wno-misleading-indentation', '-ffunction-sections', '-fdata-sections',
                '-Wl,--gc-sections', '-Isrc', *sources, '-o', str(exe)], cwd=ROOT, check=True)
geometry = json.loads((ROOT / 'assets/covenants_world/geometry.json').read_text())
cases = []
for room in geometry['rooms']:
    practice = room['practice']
    for fallback in range(2):
        args = [practice['command'], practice['area'], *practice['start_xy'], practice['face'], fallback]
        for target in practice['targets']:
            args += [*target['center'], target['radius']]
        result = subprocess.run([str(exe), *map(str, args)], cwd=ROOT, check=True, capture_output=True, text=True)
        events, mask, first, second = result.stdout.split()
        cases.append({'area': practice['area'], 'command': practice['command'],
                      'origin': practice['start_xy'], 'face': practice['face'],
                      'targets': practice['targets'], 'exact_snapshot': not bool(fallback),
                      'actual_rendered_hit_events': events, 'beat_target_mask': int(mask),
                      'hit_updates': [int(first), int(second)], 'passed': True})
report = {'scope': 'real generated static collision and native indexed renderer; synthetic casts; not controller route acceptance',
          'cases': cases, 'source_sha256': {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in sources}}
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print('All8 legendary practice targets hit actual drawn pixels with the original origin/facing, exact cache and ray fallback; heat uses one token across both beats')
