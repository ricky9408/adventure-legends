#!/usr/bin/env python3
"""Strict/sanitized actual Gear display cache and fresh validated runtime apply."""
from pathlib import Path
import os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='feedback-gear-cache-') as tmp:
 for label,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
  for name,source in [('cache',['tests/player_feedback_gear_cache_host.c','src/equipment.c','src/equipment_data.c']),('apply',['tests/player_feedback_gear_apply_host.c','src/gear_runtime.c','src/economy.c','src/equipment.c','src/equipment_data.c'])]:
   exe=Path(tmp)/(name+'-'+label)
   subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Isrc',*flags,*source,'-o',str(exe)],cwd=ROOT,check=True)
   subprocess.run([str(exe)],cwd=ROOT,check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1'))
