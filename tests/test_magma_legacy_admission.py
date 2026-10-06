#!/usr/bin/env python3
"""Real legacy quest/field wrappers preserve Magma's global terminal reserve."""
import hashlib,json,os,subprocess,tempfile,unittest
from pathlib import Path
from test_southern_save_limits import ROOT,prepare

class LegacyAdmissionTests(unittest.TestCase):
    def run_native(self,sanitized=False):
        with tempfile.TemporaryDirectory(prefix='magma-legacy-admission-') as temp:
            folder=Path(temp);sources=prepare(folder)
            for name in ('regional_quests','northern_quests'):
                path=folder/(name+'.c');path.write_bytes((ROOT/'src'/(name+'.c')).read_bytes());sources[name]=path
            exe=folder/'test';flags=['-std=c99','-O1' if sanitized else '-O2','-g','-Wall','-Wextra','-Werror','-pedantic','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-DSOUTHERN_SETUP_ONLY','-I'+str(ROOT/'src'),'-I'+str(folder)]
            if sanitized:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie']
            subprocess.run(['cc',*flags,*map(str,sources.values()),str(ROOT/'tests/southern_save_sanitizer.c'),str(ROOT/'tests/magma_legacy_admission_native.c'),'-o',str(exe)],check=True)
            env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
            result=subprocess.run([str(exe)],capture_output=True,text=True,env=env);self.assertEqual(result.returncode,0,result.stdout+result.stderr);print(result.stdout.strip())
    def test_strict_actual_legacy_wrappers(self):self.run_native()
    def test_address_undefined_sanitizers(self):self.run_native(True)
    def test_no_raw_gameplay_grants_in_legacy_wrappers(self):
        for name in ('regional_quests','northern_quests','southern_quests'):
            text=(ROOT/'src'/f'{name}.c').read_text();self.assertNotIn('creatures_grant(',text);self.assertIn('creatures_grant_admitted(',text)
        # Historical migration stays an explicit fresh-roster inner operation.
        core=(ROOT/'src/creatures.c').read_text();self.assertIn('int creatures_migrate_legacy(',core)

if __name__=='__main__':unittest.main(verbosity=2)
