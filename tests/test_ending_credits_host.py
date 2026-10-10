#!/usr/bin/env python3
"""Endroll behavior and independent pixel/canary tests, strict and sanitized."""
from pathlib import Path
import os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='ending-credit-host-')as t:
 for kind in ('clip','state'):
  for name,flags in [('normal',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
   exe=Path(t)/(kind+'-'+name)
   subprocess.run(['cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Isrc',*flags,f'tests/ending_credits_{kind}_host.c','src/ending_credits_text.c','-o',str(exe)],cwd=ROOT,check=True)
   subprocess.run([str(exe)],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
