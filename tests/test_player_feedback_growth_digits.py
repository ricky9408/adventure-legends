#!/usr/bin/env python3
"""Check the proposal, or --applied runtime, against the captured original renderer."""
import argparse,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--applied',action='store_true');a=p.parse_args()
with tempfile.TemporaryDirectory(prefix='growth-digit-equivalence-') as tmp:
 for label,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
  exe=Path(tmp)/label;mode=['-DTEST_APPLIED'] if a.applied else []
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Isrc',*mode,*flags,'tests/player_feedback_growth_digits_host.c','-o',str(exe)],cwd=ROOT,check=True)
  subprocess.run([str(exe)],cwd=ROOT,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'),check=True)
print('Mode:', 'actual runtime' if a.applied else 'unapplied proposal; runtime unchanged')
