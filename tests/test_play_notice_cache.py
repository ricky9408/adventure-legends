#!/usr/bin/env python3
"""Full-frame oracle: production notice cache versus unchanged toast/hint raster.

Exercises real generated text masks, cold and warm cache keys, changing world
pixels, absent/present/overlapping notices, width/alignment changes and disable.
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
#define TEAL PAL_TEAL2
#define UI_BG 1
#define UI_BORDER PAL_GOLD2
#define MAGMA_HINT_LANDING 1
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
u16 *screen;int world_mask_active,world_mask_left,world_mask_right,world_mask_top,world_mask_bottom;
int game_state=PLAY,toast_ticks,toast_id,fixture_hint;
int covenants_hint_text(void){return fixture_hint;}
int horizons_hint_text(void){return 0;} int return_hint_text(void){return 0;}
int underwater_hint_text(void){return 0;} int magma_powers_hint(void){return 0;}
int southern_hint_text(void){return 0;}
static u32 before[9600],reference[9600],actual[9600];
'''
body=''.join(function(game,name)for name in ('game_world_rect_hidden','pix','rect','box','text_spans','text','centered','draw_play_toast','draw_play_hint'))
body+=game[game.index('u16 play_notice_pixels['):game.index('COLD void draw_play_notices(')]
body+=function(game,'draw_play_notices')
tail=r'''
static unsigned rng=74619;static unsigned next(void){rng=rng*1664525u+1013904223u;return rng;}
static unsigned comparisons;
static void compare(int toast,int hint,int mode,int disabled){
 toast_ticks=toast>=0?110:0;toast_id=toast>=0?toast:0;fixture_hint=hint;
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
int main(void){
 unsigned eligible=0;
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
 printf("PASS: %u full-frame comparisons, %u real text IDs, cold/warm/disabled and overlap/expiry\n",comparisons,eligible);
}
'''
with tempfile.TemporaryDirectory(prefix='notice-cache-')as folder:
 folder=Path(folder);source=folder/'oracle.c';source.write_text(head+body+tail)
 for sanitizer in (False,True):
  target=folder/('sanitized'if sanitizer else'normal')
  flags=['-fsanitize=address,undefined','-fno-omit-frame-pointer']if sanitizer else[]
  subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*flags,'-I'+str(ROOT/'src'),str(source),str(ROOT/'src/ui.c'),'-o',str(target)],check=True)
  subprocess.run([str(target)],check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
