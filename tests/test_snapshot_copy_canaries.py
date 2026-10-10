#!/usr/bin/env python3
"""Portable strict-aliasing and ASan/UBSan audit of full-state snapshot copying."""
from pathlib import Path
import os,shlex,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]

def main():
    compiler=shlex.split(os.environ.get('HOST_CC','cc'))
    with tempfile.TemporaryDirectory(prefix='snapshot-copy-canaries-') as temp:
        for label,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
            binary=Path(temp)/label
            subprocess.run([*compiler,'-std=c99','-O3','-Wall','-Wextra','-Werror','-fstrict-aliasing','-fno-builtin',*flags,'-I'+str(ROOT/'src'),str(ROOT/'tests/snapshot_copy_canaries.c'),'-o',str(binary)],check=True)
            print('Snapshot copy canaries: '+label,flush=True)
            subprocess.run([str(binary)],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
if __name__=='__main__':main()
