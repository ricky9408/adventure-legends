#!/usr/bin/env python3
"""All companion text coverage, read-only preview and unchanged evolution commit."""
from pathlib import Path
import json,os,subprocess,tempfile,sys
from test_player_feedback_menu import MODULES
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets'))
from companion_guide_source import load_commands
def main():
 commands=load_commands(ROOT)
 assert sorted(c['id'] for c in commands)==list(range(1,129))
 for c in commands:
  assert len(c['combat'])==2 and all(c['combat']) and c['field'] and c['recovery']
  for source in c['source']:
   path=source.split(':')[0]
   assert (ROOT/path).is_file(),source
 for path in (ROOT/'src/companion_guide_text_data').glob('*.inc'):assert path.stat().st_size<75000
 with tempfile.TemporaryDirectory(prefix='companion-guide-host-') as tmp:
  for label,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
   exe=Path(tmp)/label
   subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-Isrc',*flags,'tests/companion_guide_host.c','tests/player_feedback_menu_draw.c',*[f'src/{m}.c' for m in MODULES],'-o',str(exe)],cwd=ROOT,check=True)
   subprocess.run([str(exe)],cwd=ROOT,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1'),check=True)
   recovery=Path(tmp)/(label+'-recovery')
   subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Isrc',*flags,'tests/companion_guide_recovery_host.c',*[f'src/{m}.c' for m in ['companion_guide','creatures','creature_data','gear_runtime','equipment','equipment_data','economy']],'-o',str(recovery)],cwd=ROOT,check=True)
   subprocess.run([str(recovery)],cwd=ROOT,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1'),check=True)
if __name__=='__main__':main()
