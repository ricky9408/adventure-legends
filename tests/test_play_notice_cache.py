#!/usr/bin/env python3
"""Full-frame oracle: production notice cache versus unchanged toast/hint raster.

Exercises real generated text masks, cold and warm cache keys, changing world
pixels, absent/present/overlapping notices, two-line journey goals,
width/alignment changes and disable.
Host pixels are evidence for exact composition, never native timing.
"""
from pathlib import Path
import os,re,subprocess,tempfile
from test_covenants_engine import function
ROOT=Path(__file__).resolve().parents[1]
game=(ROOT/'src/game.c').read_text()
head=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "assets.h"
#include "ui.h"
#define COLD
#define GAME_HOST_TEST
#define PLAY 1
#define CREAM PAL_GOLD4
#define GOLD PAL_GOLD3
#define TEAL PAL_TEAL2
#define UI_BG 1
#define UI_BORDER PAL_GOLD2
#define MAGMA_HINT_LANDING 1
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
u16 *screen;int world_mask_active,world_mask_left,world_mask_right,world_mask_top,world_mask_bottom;
int game_state=PLAY,toast_ticks,toast_id,field_goal_detail,fixture_hint,fixture_reward,quickparty_visible,scene_present_phase;
int game_shop_reward_visible(void){return fixture_reward;}
int covenants_hint_text(void){return fixture_hint;}
int horizons_hint_text(void){return 0;} int return_hint_text(void){return 0;}
int underwater_hint_text(void){return 0;} int magma_powers_hint(void){return 0;}
int southern_hint_text(void){return 0;}
static u32 before[9600],reference[9600],actual[9600];
'''
body=''.join(function(game,name)for name in ('game_world_rect_hidden','pix','rect','box','text_spans','text','centered','play_hint_text','tick_play_toast','draw_play_toast','draw_play_hint'))
body+=game[game.index('u16 play_notice_pixels['):game.index('COLD void draw_play_notices(')]
body+=function(game,'draw_play_notices')
goal_ids=sorted(set(re.findall(r'\bTX_[A-Z0-9_]+\b',(ROOT/'src/journey_goal.c').read_text(encoding='utf-8'))))
body+='\nstatic const int goal_ids[] = {'+','.join(goal_ids)+'};\n'
tail=r'''
static unsigned rng=74619;static unsigned next(void){rng=rng*1664525u+1013904223u;return rng;}
static unsigned comparisons;
static void compare(int toast,int hint,int mode,int disabled){
 toast_ticks=toast>=0?110:0;toast_id=toast>=0?toast:0;field_goal_detail=0;fixture_hint=hint;fixture_reward=0;
 game_state=mode;play_notice_cache_disabled=disabled;
 for(unsigned i=0;i<9600;i++)before[i]=reference[i]=actual[i]=next();
 screen=(u16*)reference;draw_play_toast();draw_play_hint();
 screen=(u16*)actual;draw_play_notices(comparisons%3!=0);
 if(memcmp(reference,actual,sizeof reference)){
  for(unsigned i=0;i<38400;i++)if(((u8*)reference)[i]!=((u8*)actual)[i]){
   fprintf(stderr,"toast=%d hint=%d mode=%d disabled=%d at(%u,%u) before=%u expected=%u actual=%u\n",toast,hint,mode,disabled,i%240,i/240,((u8*)before)[i],((u8*)reference)[i],((u8*)actual)[i]);break;
  }assert(0);
 }
 assert(screen==(u16*)actual);comparisons++;
}
static void compare_goal(int title,int detail,int hint,int reward,int disabled,int build_cache){
 int w=ui_texts[title].width>ui_texts[detail].width?ui_texts[title].width:ui_texts[detail].width;
 int x=(240-w-12)/2;
 game_state=PLAY;toast_ticks=110;toast_id=title;field_goal_detail=detail;
 fixture_hint=hint;fixture_reward=reward;play_notice_cache_disabled=disabled;
 for(unsigned i=0;i<9600;i++)before[i]=reference[i]=actual[i]=next();
 screen=(u16*)reference;
 if(hint)draw_play_hint();else if(!reward){box(x,122,w+12,32);centered(title,123,GOLD);centered(detail,138,CREAM);}
 screen=(u16*)actual;draw_play_notices(build_cache);
 if(memcmp(reference,actual,sizeof reference)){
  for(unsigned i=0;i<38400;i++)if(((u8*)reference)[i]!=((u8*)actual)[i]){
   fprintf(stderr,"goal=%d/%d hint=%d reward=%d disabled=%d cache=%d at(%u,%u) before=%u expected=%u actual=%u\n",title,detail,hint,reward,disabled,build_cache,i%240,i/240,((u8*)before)[i],((u8*)reference)[i],((u8*)actual)[i]);break;
  }assert(0);
 }
 assert(screen==(u16*)actual);comparisons++;
}
int main(void){
 unsigned eligible=0;
 for(unsigned i=0;i<sizeof goal_ids/sizeof goal_ids[0];i++)assert(ui_texts[goal_ids[i]].width<=228);
 /* Required hints own the whole slot, even if a wider toast is queued.
  * This checks readable composition rather than cache/oracle equivalence alone. */
 game_state=PLAY;toast_ticks=110;toast_id=TX_SUMMONED;fixture_hint=TX_UW_AIM_SIDE;
 for(unsigned i=0;i<9600;i++)reference[i]=actual[i]=next();
 screen=(u16*)reference;draw_play_hint();
 screen=(u16*)actual;draw_play_toast();draw_play_hint();
 assert(!memcmp(reference,actual,sizeof actual));
 for(unsigned i=0;i<90;i++)tick_play_toast();assert(toast_ticks==110);
 fixture_hint=0;tick_play_toast();assert(toast_ticks==109);
 game_state=3;tick_play_toast();assert(toast_ticks==109);
 game_state=PLAY;toast_ticks=0;tick_play_toast();assert(!toast_ticks);
 field_goal_detail=TX_JG_BEGIN_DETAIL;toast_ticks=110;fixture_reward=1;
 for(unsigned i=0;i<90;i++)tick_play_toast();assert(toast_ticks==110);
 fixture_reward=0;tick_play_toast();assert(toast_ticks==109);field_goal_detail=0;
 {
  static const int goals[][2]={{TX_JG_BEGIN,TX_JG_BEGIN_DETAIL},
   {TX_C_QUEST_ACT2,TX_JG_SKY_DETAIL},{TX_JG_HOME,TX_JG_HOME_FREE}};
  for(unsigned i=0;i<sizeof goals/sizeof goals[0];i++){
   int title=goals[i][0],detail=goals[i][1];
   assert(ui_texts[title].width<=228&&ui_texts[detail].width<=228);
   compare_goal(title,detail,0,0,0,0);compare_goal(title,detail,0,0,0,1);
   compare_goal(title,detail,0,0,0,1);compare_goal(title,detail,0,0,1,1);
   compare_goal(title,detail,TX_UW_AIM_SIDE,0,0,1);
   compare_goal(title,detail,0,1,0,1);
  }
 }
 for(int id=0;id<TX_COUNT;id++){
  const UiText*t=&ui_texts[id];
  /* Production toasts/hints have one line; unrelated oversized menu lines
   * are not valid bottom-card inputs for either historical renderer. */
  if(t->width>228||t->height>17)continue;
  eligible++;
  int other=(id*631+17)%TX_COUNT;
  while(ui_texts[other].width>228||ui_texts[other].height>17)other=(other+1)%TX_COUNT;
  for(unsigned repeat=0;repeat<3;repeat++){
   compare(id,0,PLAY,0);compare(id,0,PLAY,0);
   compare(-1,id,PLAY,0);compare(-1,id,PLAY,0);
   compare(id,other,PLAY,0);compare(id,other,PLAY,0);
   compare(other,id,PLAY,0);compare(other,id,PLAY,0);
   compare(id,other,PLAY,1);compare(-1,0,PLAY,0);
   compare(id,other,3,0);
  }
 }
 printf("PASS: hint ownership/deferred toast timing and two-line goals, %u full-frame comparisons, %u real text IDs, cold/warm/disabled and overlap/expiry\n",comparisons,eligible);
}
'''
with tempfile.TemporaryDirectory(prefix='notice-cache-')as folder:
 folder=Path(folder);source=folder/'oracle.c';source.write_text(head+body+tail)
 for sanitizer in (False,True):
  target=folder/('sanitized'if sanitizer else'normal')
  flags=['-fsanitize=address,undefined','-fno-omit-frame-pointer']if sanitizer else[]
  subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*flags,'-I'+str(ROOT/'src'),str(source),str(ROOT/'src/ui.c'),'-o',str(target)],check=True)
  subprocess.run([str(target)],check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
