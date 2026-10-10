#!/usr/bin/env python3
"""Actual native map logic/pixels on host; this does not claim GBA execution."""
from pathlib import Path
import argparse,os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
MODULES=['journey_map','journey_map_text','journal_nav','connected_roads','travel_feedback',
         'regional_quests','northern_quests','southern_quests','magma_quests','underwater_quests',
         'return_quests','horizons_quests','covenants_quests','horizons_game','covenants_game',
         'campaign_rules','save5','ui','assets']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--captures',type=Path);a=p.parse_args()
 env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0')
 if a.captures:a.captures.mkdir(parents=True,exist_ok=True);env['JOURNEY_MAP_CAPTURE_DIR']=str(a.captures.resolve())
 with tempfile.TemporaryDirectory(prefix='journey-map-host-') as tmp:
  for label,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
   exe=Path(tmp)/label
   subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-Isrc',*flags,'tests/journey_map_host.c',*[f'src/{m}.c' for m in MODULES],'-o',str(exe)],cwd=ROOT,check=True)
   subprocess.run([str(exe)],cwd=ROOT,env=env,check=True)
if __name__=='__main__':main()
