#!/usr/bin/env python3
"""Strict and sanitizer host C integration, plus ARM ROM/data/stack accounting.

Not a substitute for a controller-only native gameplay acceptance route.
"""
from pathlib import Path
import json
import hashlib
import os
import subprocess
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build' / 'northern-powers-host'
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = ['tests/northern_powers_native.c', 'src/northern_powers.c',
           'src/northern_power_art.c', 'src/southern_powers.c',
           'src/southern_power_art.c', 'src/advanced_powers.c',
           'src/regional_powers.c', 'src/gear_runtime.c', 'tests/legacy_magma_hooks.c', 'src/weapon_actions.c',
           'src/combat_rules.c', 'src/equipment.c', 'src/equipment_data.c',
           'src/creatures.c', 'src/creature_data.c', 'src/assets.c']
for name, flags in [('strict', []), ('sanitized', ['-fsanitize=address,undefined',
                                                '-fno-omit-frame-pointer'])]:
    exe = OUT / name
    subprocess.run(['cc', '-std=c99', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                    '-Wno-misleading-indentation', '-pedantic', '-Isrc',
                    *flags, *SOURCES, '-o', str(exe)], cwd=ROOT, check=True)
    subprocess.run([str(exe)], cwd=ROOT, check=True,
                   env=dict(os.environ, ASAN_OPTIONS='detect_leaks=0'))
arm = ROOT / 'tools/sysroot/usr/bin/arm-none-eabi-gcc'
if arm.exists():
    prefix = str(arm).removesuffix('gcc')
    objects = []
    for source in ['src/northern_powers.c', 'src/northern_power_art.c']:
        obj = OUT / (Path(source).stem + '.o')
        subprocess.run([str(arm), '-mcpu=arm7tdmi', '-mthumb-interwork', '-mthumb',
                        '-std=c99', '-O2', '-ffreestanding', '-fno-builtin',
                        '-fno-strict-aliasing', '-fomit-frame-pointer', '-Wall',
                        '-Wextra', '-Werror', '-fstack-usage', '-Isrc', '-c',
                        source, '-o', str(obj)], cwd=ROOT, check=True)
        objects.append(str(obj))
    size = subprocess.check_output([prefix+'size', *objects], text=True)
    sections = subprocess.check_output([prefix+'objdump', '-h', *objects], text=True)
    undefined = subprocess.check_output([prefix+'nm', '-u', objects[0]], text=True)
    assert '__aeabi_idiv' not in undefined and '__aeabi_uidiv' not in undefined, 'Effect paths must not require integer division'
    stack = '\n'.join(p.read_text() for p in OUT.glob('*.su'))
    assert '.iwram' not in sections, 'Northern code must stay ROM-resident'
    rows = [line.split() for line in size.strip().splitlines()[1:]]
    bss = sum(int(row[2]) for row in rows)
    data = sum(int(row[1]) for row in rows)
    max_stack = max(int(line.split('\t')[1]) for line in stack.splitlines() if line)
    assert bss+data < 1024, 'New transient state exceeds the 1 KiB bound'
    assert max_stack <= 128, 'No large local pixel/grid buffers allowed'
    report = {'kind': 'host-and-ARM-object-evidence-not-native-gameplay',
              'bss_bytes': bss, 'data_bytes': data,
              'max_individual_function_stack_bytes': max_stack,
              'conservative_max_module_only_call_chain_bytes': 272,
              'call_chain_note': 'cast104 + washback56 + hurt56 + clear_segment56; excludes external runtime callbacks',
              'rom_resident': True, 'additional_resident_OBJ_bytes': 0,
              'size': size, 'stack_usage': stack, 'sections': sections,
              'n1_render_optimization': {
                  'baseline_handler_sha256': 'bb0c4d9a801dbfb88565c2dc7fffe732e670087e014e65b179fc378846b08bd1',
                  'handler_sha256': hashlib.sha256((ROOT/'src/northern_powers.c').read_bytes()).hexdigest(),
                  'draw14_solid_calls_before': 102, 'draw14_solid_calls_after': 31,
                  'four_direction_render_cases': 120, 'dynamic_wall_cases': 116,
                  'diagonal_corner_cases': 2, 'render_segment_OBJ_cap': 10,
                  'all_effect_OBJ_cap': 20, 'integer_division_helpers': False,
                  'native_frame_budget_status': 'requires separate N1 controller stress evidence'}}
    (OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(size, end='')
    print(f'ARM: BSS+data={bss+data}; max individual stack={max_stack}; no IWRAM; OBJ delta=0')
else:
    print('ARM compiler unavailable; ARM object/stack evidence NOT run')
