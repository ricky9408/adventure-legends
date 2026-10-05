#!/usr/bin/env python3
"""Host-native deterministic transient weapon actions. Not in-game route evidence."""
from pathlib import Path
import os, subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build'/'weapon-actions-host'
OUT.mkdir(parents=True,exist_ok=True)
sources=['tests/weapon_actions_native.c','src/weapon_actions.c','src/equipment_data.c']
for suffix,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
    exe=OUT/suffix
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-Isrc',*flags,*sources,'-o',str(exe)],cwd=ROOT,check=True)
    env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0')
    subprocess.run([str(exe)],cwd=ROOT,env=env,check=True)
