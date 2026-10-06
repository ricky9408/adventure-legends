#!/usr/bin/env python3
"""Actual C gear/health/OBJ integration with synthetic bounded world/render bridges."""
from pathlib import Path
import os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build'/'gear-runtime-host';OUT.mkdir(parents=True,exist_ok=True)
sources=['tests/gear_runtime_native.c','src/gear_runtime.c', 'tests/legacy_magma_hooks.c', 'tests/legacy_underwater_hooks.c','src/weapon_actions.c','src/regional_powers.c','src/northern_powers.c','src/northern_power_art.c','src/southern_powers.c','src/southern_power_art.c','src/advanced_powers.c','src/combat_rules.c','src/equipment.c','src/equipment_data.c','src/creatures.c','src/creature_data.c','src/assets.c']
for name,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
    exe=OUT/name
    subprocess.run(['cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pedantic','-Isrc',*flags,*sources,'-o',str(exe)],cwd=ROOT,check=True)
    subprocess.run([str(exe)],cwd=ROOT,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'),check=True)
