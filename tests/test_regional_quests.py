#!/usr/bin/env python3
"""Actual C quest/reward/save integration; host-only, no in-game route claim."""
from pathlib import Path
import os, subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build'/'regional-quests-host';OUT.mkdir(parents=True,exist_ok=True)
sources=['tests/regional_quests_native.c','src/regional_quests.c','src/save5.c','src/save4.c','src/equipment.c','src/equipment_data.c','src/creatures.c','src/creature_data.c']
for name,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
    exe=OUT/name
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST','-Isrc',*flags,*sources,'-o',str(exe)],cwd=ROOT,check=True)
    subprocess.run([str(exe)],cwd=ROOT,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'),check=True)
