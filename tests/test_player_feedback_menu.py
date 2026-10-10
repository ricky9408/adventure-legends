#!/usr/bin/env python3
"""Actual menu/core/codec behavior and generated-text layout; host, not native QA."""
from pathlib import Path
import os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
MODULES=['gear_preview','gear_preview_text','companion_guide','companion_guide_text','journal_nav','gear_menu','quickparty','progression','creatures','creature_data','equipment','equipment_data','economy','save5','save4','regional_quests','northern_quests','southern_quests','magma_quests','underwater_quests','return_quests','horizons_quests','covenants_quests','campaign_rules','progression_events','ui','assets']
def main():
 with tempfile.TemporaryDirectory(prefix='player-menu-host-') as tmp:
  for label,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
   exe=Path(tmp)/label
   subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-Isrc',*flags,'tests/player_feedback_menu_host.c','tests/player_feedback_menu_draw.c',*[f'src/{m}.c' for m in MODULES],'-o',str(exe)],cwd=ROOT,check=True)
   subprocess.run([str(exe)],cwd=ROOT,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'),check=True)
if __name__=='__main__':main()
