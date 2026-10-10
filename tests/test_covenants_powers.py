#!/usr/bin/env python3
"""Strict/sanitized real-catalog tests and ARM object resource accounting."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/covenants-powers-host'
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = ['tests/covenants_powers_host.c', 'src/covenants_powers.c',
           'src/covenants_power_art.c', 'src/creatures.c', 'src/creature_data.c',
           'src/gear_runtime.c', 'src/combat_rules.c', 'src/north_art.c', 'src/south_art.c']
def run(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, **kwargs)

outputs = [ROOT / p for p in ('src/covenants_power_art.c', 'src/covenants_power_art.h',
           'assets/covenants_powers/manifest.json', 'assets/covenants_powers/glyphs_3x.png')]
before = {p: p.read_bytes() for p in outputs}
run(['python3', 'assets/generate_covenants_powers.py'])
assert all(p.read_bytes() == value for p, value in before.items()), 'non-deterministic power art'
common = ['-std=c99', '-Wall', '-Wextra', '-Werror', '-pedantic', '-ffunction-sections', '-fdata-sections', '-Isrc']
run(['cc', *common, '-O2', '-c', 'src/covenants_powers.c', '-o', str(OUT / 'warning-check.o')])
logs = {}
for name, flags in [('strict', []), ('sanitized', ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
    exe = OUT / name
    run(['cc', *common, '-Wno-misleading-indentation', '-O1', '-g', '-Wl,--gc-sections',
         *flags, *SOURCES, '-o', str(exe)])
    result = run([str(exe)], text=True, capture_output=True,
                 env=dict(os.environ, ASAN_OPTIONS='detect_leaks=0'))
    logs[name] = result.stdout
    (OUT / (name + '.log')).write_text(result.stdout + result.stderr)
    print(result.stdout)
arm = ROOT / 'tools/sysroot/usr/bin/arm-none-eabi-gcc'
assert arm.exists(), 'ARM resource gate requires a toolchain'
objects = []
for source in ('src/covenants_powers.c', 'src/covenants_power_art.c', 'src/covenants_creature_art.c'):
    obj = OUT / (Path(source).stem + '.o')
    run([str(arm), '-mcpu=arm7tdmi', '-mthumb-interwork', '-mthumb', '-std=c99', '-O2',
         '-ffreestanding', '-fno-builtin', '-fno-strict-aliasing', '-fomit-frame-pointer',
         '-Wall', '-Wextra', '-Werror', '-fstack-usage', '-Isrc', '-c', source, '-o', str(obj)])
    objects.append(str(obj))
prefix = str(arm).removesuffix('gcc')
sizes = subprocess.check_output([prefix + 'size', *objects], text=True)
sections = subprocess.check_output([prefix + 'objdump', '-h', *objects], text=True)
stack = '\n'.join(p.read_text() for p in OUT.glob('*.su'))
rows = [line.split() for line in sizes.splitlines()[1:]]
ram = sum(int(row[1]) + int(row[2]) for row in rows)
max_stack = max(int(line.split('\t')[1]) for line in stack.splitlines() if line)
assert ram <= 768 and max_stack <= 128 and '.iwram' not in sections
report = {'scope': 'synthetic-host-and-ARM-object-only; not-controller-gameplay-or-frame-budget-acceptance',
          'ram_bytes': ram, 'module_ram_limit_bytes': 768,
          'ram_budget_reason': 'approved bounded48-rectangle cache; whole chapter+2048B remains hard',
          'rom_bytes': sum(int(row[0]) for row in rows),
          'IWRAM_growth': 0, 'resident_OBJ_growth': 0, 'maximum_moving_parts': 3,
          'maximum_stamp_draws_including_startup_glyph': 25,
          'maximum_function_stack_bytes': max_stack,
          'stack_excludes_external_callbacks_and_IRQ': True,
          'source_sha256': {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in SOURCES},
          'sizes': sizes, 'stack': stack, 'host_logs': logs}
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(sizes)
