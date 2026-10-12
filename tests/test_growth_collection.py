#!/usr/bin/env python3
"""Current goals/collection contracts; synthetic host boundaries,not acquisition."""
from pathlib import Path
import json,os,subprocess,tempfile,sys
from test_player_feedback_menu import MODULES
ROOT=Path(__file__).resolve().parents[1]
def main():
 metrics=json.loads((ROOT/'assets/growth_journal_metrics.json').read_text())
 assert all(v['width']<=214 and v['height']==15 for v in metrics.values())
 assert all(p.stat().st_size<=32000 for p in (ROOT/'src/growth_journal_text_data').glob('*.inc'))
 link=['-Wl,-dead_strip'] if sys.platform=='darwin' else ['-Wl,--gc-sections']
 with tempfile.TemporaryDirectory(prefix='growth-collection-') as d:
  for name,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
   exe=Path(d)/name
   subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections',*link,'-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-Isrc','-Itests',*flags,'tests/growth_collection_host.c',*[f'src/{m}.c'for m in MODULES],'-o',str(exe)],cwd=ROOT,check=True)
   subprocess.run([str(exe)],cwd=ROOT,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'),check=True)
if __name__=='__main__':main()
