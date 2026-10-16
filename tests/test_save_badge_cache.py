#!/usr/bin/env python3
"""Real generated save-badge pixels, cold/cache-hit/masked; host raster evidence.

This does not establish native DMA timing, SRAM completion or earned play.
"""
from pathlib import Path
import sys,subprocess,os,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_player_feedback_box_native import extract_function
s=(ROOT/'src/game.c').read_text()
head='''#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include "assets.h"
#include "ui.h"
#define COLD
#define GAME_HOST_TEST
#define TEAL PAL_TEAL2
#define UI_BG 1
#define UI_BORDER PAL_GOLD2
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
u16 *screen;int world_mask_active,world_mask_left,world_mask_right,world_mask_top,world_mask_bottom;
static u32 reference_pixels[9600],actual_pixels[9600];
int badge_id;int game_save_badge_id(void){return badge_id;}
'''
body=''.join(extract_function(s,n)for n in ['game_world_rect_hidden','pix','rect','box','text_spans','text','centered'])
body+=s[s.index('u16 save_badge_pixels['):s.index('COLD void game_draw_save_badge(')]
body+=extract_function(s,'game_draw_save_badge')
tail='''void reference_badge(void){int id=game_save_badge_id();if(id){int w=ui_texts[id].width+8;box(200-w,3,w,17);text(id,204-w,3,TEAL);}}
static unsigned rng=8123;static unsigned next(void){rng=rng*1664525u+1013904223u;return rng;}
int main(void){int ids[]={0,TX_FB_SAVING,TX_FB_SAVED,TX_FB_WORKING,TX_FB_SAVE_ERROR};unsigned count=0;
world_mask_left=8;world_mask_right=232;world_mask_top=31;world_mask_bottom=153;
for(unsigned i=0;i<10000;i++){
 badge_id=ids[(i/3)%5];world_mask_active=i%7==0;
 for(unsigned n=0;n<9600;n++)reference_pixels[n]=actual_pixels[n]=next();
 screen=(u16*)reference_pixels;reference_badge();screen=(u16*)actual_pixels;game_draw_save_badge();
 assert(!memcmp(reference_pixels,actual_pixels,sizeof actual_pixels));assert(screen==(u16*)actual_pixels);count++;
}printf("PASS %u complete framebuffer badge comparisons\\n",count);}
'''
with tempfile.TemporaryDirectory(prefix='badge-cache-')as d:
 p=Path(d);(p/'test.c').write_text(head+body+tail)
 for sanitize in [False,True]:
  flags=['-fsanitize=address,undefined','-fno-omit-frame-pointer']if sanitize else[]
  subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*flags,'-I'+str(ROOT/'src'),str(p/'test.c'),str(ROOT/'src/ui.c'),'-o',str(p/'test')],check=True)
  subprocess.run([str(p/'test')],check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
