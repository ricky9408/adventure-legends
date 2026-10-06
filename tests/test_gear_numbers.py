#!/usr/bin/env python3
"""Exact cold-menu decimal pixel/rounding equivalence, strict and sanitizer host."""
from pathlib import Path
import subprocess,os
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/gear-number-host';OUT.mkdir(exist_ok=True,parents=True)
for label,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
 exe=OUT/label
 subprocess.run(['cc','-std=c99','-O2','-g','-Wall','-Wextra','-Werror','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Isrc',*flags,'tests/gear_number_native.c','-o',str(exe)],cwd=ROOT,check=True)
 subprocess.run([str(exe)],cwd=ROOT,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'),check=True)
