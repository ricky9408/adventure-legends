#!/usr/bin/env python3
"""Synthetic full-party reserve inspector/bitmap/codec regression.

Builds the real selected checkout's menu/core/Save5 implementation. The host
fixture is deliberately prepared with public creature grants, not presented as
controller-earned gameplay; native acquisition proof is fresh_reserve_notice.py.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

MODULES=['gear_preview','gear_preview_text','companion_guide','companion_guide_text',
 'journal_nav','gear_menu','quickparty','recruit_notice','progression','creatures',
 'creature_data','equipment','equipment_data','economy','save5','save4',
 'regional_quests','northern_quests','southern_quests','magma_quests',
 'underwater_quests','return_quests','horizons_quests','covenants_quests',
 'campaign_rules','progression_events','ui','assets','growth_goals',
 'growth_journal_text','collection_journal']

TEST=r'''
#define main existing_menu_main
#include "player_feedback_menu_host.c"
#undef main
#include "player_feedback_menu_draw.c"
#include "recruit_notice.h"
static unsigned ordinary_saves,companion_reseats;
void save_game_ordinary(void){ordinary_saves++;}
void game_companion_reseat(void){companion_reseats++;}
void journey_map_open(void){assert(!"reserve test cannot open map");}
int journey_map_input(int pressed){(void)pressed;assert(!"reserve test cannot input map");return 0;}
static int badge(void){
 static const unsigned char glyphs[3][5]={{5,7,7,7,5},{7,4,6,4,7},{5,5,7,7,5}};
 unsigned x,y;
 for(y=0;y<7;y++)for(x=0;x<13;x++){
  unsigned lit=0;
  if(y>0&&y<6&&x>0&&x<12){unsigned letter=(x-1)/4,column=(x-1)%4;
   lit=column<3&&(glyphs[letter][y-1]&(4u>>column));}
  if(fb.pixels[(86+y)*240+18+x]!=(lit?PAL_GOLD3:PAL_INK))return 0;
 }
 return 1;
}
int main(void){
 Save5State before,expected,recovered;unsigned stone,water,wind,i;
 fresh(1);ordinary_saves=0;
 assert(creatures_migrate_legacy(&adventure_save.roster,0,0));
 wind=creatures_grant_story(&adventure_save.roster,2,1);assert(wind<160);
 water=creatures_grant(&adventure_save.roster,13,1,0,0,0);assert(water<160);
 adventure_save.campaign.chapter_flags=chapter_flags=3;
 stone=creatures_grant_story(&adventure_save.roster,3,3);assert(stone<160);
 adventure_save.campaign.spawn=3;creatures_apply_story_floors(&adventure_save.roster,3);
 adventure_save.economy.reserved[1]=1; /* Wind explicitly acknowledged fixture. */
 assert(save5_validate(&adventure_save));
 assert(adventure_save.roster.party[0]==0&&adventure_save.roster.party[1]==1&&adventure_save.roster.party[2]==wind&&adventure_save.roster.party[3]==water);
 for(i=0;i<4;i++)assert(adventure_save.roster.party[i]!=stone);
 assert(recruit_notice_pending(&adventure_save.roster.instances[stone]));
 journal_tab=2;progression_refresh();quickparty_menu_reset();before=adventure_save;
 for(i=0;i<161&&quickparty_menu_candidate!=(int)stone;i++)quickparty_menu_input(128);
 assert(quickparty_menu_candidate==(int)stone&&!quickparty_menu_detail);
 assert(!memcmp(&before,&adventure_save,sizeof before)&&!ordinary_saves&&!saves);
 clear();quickparty_draw_journal();assert(badge());capture("reserved-stone-NEW");
 /* Browsing and B cancellation cannot clear a reserve recruit's notice. */
 journal_nav_input(2);assert(journal_tab==13);
 assert(!memcmp(&before,&adventure_save,sizeof before)&&recruit_notice_pending(&adventure_save.roster.instances[stone]));
 journal_tab=2;quickparty_menu_reset();
 for(i=0;i<161&&quickparty_menu_candidate!=(int)stone;i++)quickparty_menu_input(128);
 expected=before;expected.economy.reserved[1]|=2;
 assert(quickparty_menu_input(1)&&quickparty_menu_detail);
 assert(!memcmp(&expected,&adventure_save,sizeof expected)&&ordinary_saves==1&&!saves&&!companion_reseats);
 assert(!recruit_notice_pending(&adventure_save.roster.instances[stone]));
 clear();quickparty_draw_journal();capture("reserved-stone-inspected");
 journal_nav_input(2);assert(!quickparty_menu_detail);
 clear();quickparty_draw_journal();assert(!badge());capture("reserved-stone-acknowledged");
 assert(quickparty_menu_input(1)&&quickparty_menu_detail&&ordinary_saves==1);
 assert(!memcmp(&expected,&adventure_save,sizeof expected));
 journal_nav_input(2);
 memset(save5_test_sram,255,32768);assert(save5_store(&adventure_save));
 memset(&recovered,0,sizeof recovered);assert(save5_load(&recovered));
 /* Codec output metadata is intentionally produced on load, not persisted
  * from the caller. All actual campaign/party/individual bytes stay exact. */
 assert(recovered.campaign.sequence==1&&recovered.campaign.loaded_version==5);
 expected.campaign.sequence=1;expected.campaign.loaded_version=5;
 assert(!memcmp(&expected,&recovered,sizeof expected)&&save5_validate(&recovered));
 adventure_save=recovered;quickparty_menu_reset();
 for(i=0;i<161&&quickparty_menu_candidate!=(int)stone;i++)quickparty_menu_input(128);
 clear();quickparty_draw_journal();assert(!badge());capture("reserved-stone-codec-continued");
 /* An immutable writer lease defers acknowledgement without assigning Stone. */
 adventure_save.economy.reserved[1]=1;before=adventure_save;
 assert(save5_preflight_begin(&adventure_save));
 quickparty_menu_input(1);assert(!memcmp(&before,&adventure_save,sizeof before)&&ordinary_saves==1);
 save5_preflight_cancel();journal_nav_input(2);quickparty_menu_input(1);
 assert(!memcmp(&expected,&adventure_save,sizeof expected)&&ordinary_saves==2&&!saves);
 puts("PASS synthetic reserve Stone: real menu NEW bitmap, browse/B preserve notice, first A acknowledges only, repeated A idempotent, codec retains reserve and party, immutable lease defers acknowledgement");
 return 0;
}
'''

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--source-root',type=Path,default=Path(__file__).resolve().parents[1])
 p.add_argument('--capture-dir',type=Path)
 opts=p.parse_args();root=opts.source_root.resolve()
 if opts.capture_dir:opts.capture_dir.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='reserve-notice-host-') as tmp:
  source=Path(tmp)/'reserve.c';source.write_text(TEST)
  for label,flags in (('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer'])):
   exe=Path(tmp)/label
   subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror',
    '-Wno-misleading-indentation','-ffunction-sections','-fdata-sections',
    '-Wl,-dead_strip' if sys.platform=='darwin' else '-Wl,--gc-sections',
    '-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-I'+str(root/'src'),'-I'+str(root/'tests'),*flags,
    str(source),*[str(root/'src'/(m+'.c')) for m in MODULES],'-o',str(exe)],cwd=root,check=True)
   env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0')
   if opts.capture_dir:env['PLAYER_MENU_CAPTURE_DIR']=str(opts.capture_dir.resolve())
   subprocess.run([str(exe)],cwd=root,env=env,check=True)

if __name__=='__main__':main()
