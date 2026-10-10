#!/usr/bin/env python3
"""Current Return stage constraints in normal and address/undefined builds."""
import os,shlex,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ReturnCurrentMasks(unittest.TestCase):
 def test_all65536_masks_each_form_normal_and_sanitized(self):
  with tempfile.TemporaryDirectory(prefix='return-current-masks-') as tmp:
   for sanitized in (False,True):
    out=Path(tmp)/('sanitized' if sanitized else 'normal')
    flags=['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie'] if sanitized else ['-O2']
    subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+['-std=c99','-Wall','-Wextra','-Werror',*flags,'-I'+str(ROOT/'src'),str(ROOT/'src/creatures.c'),str(ROOT/'src/creature_data.c'),str(ROOT/'tests/return_current_masks_host.c'),'-o',str(out)],check=True)
    subprocess.run([str(out)],check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'))
if __name__=='__main__':unittest.main(verbosity=2)
