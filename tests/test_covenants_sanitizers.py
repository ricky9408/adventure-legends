#!/usr/bin/env python3
"""Address/UB sanitizer verification with explicitly synthetic host seeds."""
import os,subprocess,tempfile,unittest
from pathlib import Path
from covenants_host_support import *
class CovenantsSanitizers(unittest.TestCase):
 def test_state_and_request_fuzz_asan_ubsan(self):
  with tempfile.TemporaryDirectory(prefix='covenants-sanitizers-') as td:
   td=Path(td);l=build(td/'seed');old=source(l);full=story(l,True)
   (td/'covenants-seeds.h').write_text('\n'.join('static const unsigned char '+name+'[]={' + ','.join(map(str,bytes(value)))+'};' for name,value in [('covenants_old',old),('covenants_full',full)]))
   sources=['save4','save5','creatures','creature_data','equipment','equipment_data','covenants_quests']
   out=td/'sanitize';subprocess.run(['cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST','-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie','-Isrc','-I'+str(td),*[str(ROOT/'src'/f'{n}.c') for n in sources],str(ROOT/'tests/covenants_persistence_sanitizer.c'),'-o',str(out)],cwd=ROOT,check=True)
   subprocess.run([str(out)],env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'),check=True)
if __name__=='__main__':unittest.main(verbosity=2)
