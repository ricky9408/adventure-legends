#!/usr/bin/env python3
"""Pixel oracle for the production one-pass card raster; no native timing claim."""
from pathlib import Path
import os
import subprocess
import tempfile
from test_covenants_engine import function

ROOT = Path(__file__).resolve().parents[1]
game = (ROOT / 'src/game.c').read_text()
head = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define COLD
#define GAME_HOST_TEST
#define UI_BG 1
#define UI_BORDER 45
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
static u32 reference_pixels[9600],actual_pixels[9600];
u16 *screen;int world_mask_active,world_mask_left,world_mask_right,world_mask_top,world_mask_bottom;
'''
body = ''.join(function(game, name) for name in ('game_world_rect_hidden', 'pix', 'rect'))
# This simple composition is the historical box contract, independent of the
# proposal and valid even after production integrates a faster common path.
body += '''void reference_box(int x,int y,int w,int h){rect(x,y,w,h,UI_BG);rect(x,y,w,1,UI_BORDER);rect(x,y+h-1,w,1,UI_BORDER);rect(x,y,1,h,UI_BORDER);rect(x+w-1,y,1,h,UI_BORDER);}\n'''
body += function(game, 'box').replace('void box(', 'void proposal_box(')
tail = r'''
static unsigned rng=84921;static unsigned next(void){rng=rng*1664525u+1013904223u;return rng;}
int main(void){unsigned count=0;
 for(unsigned i=0;i<12000;i++){
  int x=(int)(next()%280)-20,y=(int)(next()%190)-15,w=(int)(next()%270)-8,h=(int)(next()%180)-6;
  if(i<4000){x=(int)(next()%52)*4;y=(int)(next()%120);w=(int)(next()%52+8)*4;h=(int)(next()%130+3);}
  for(unsigned n=0;n<9600;n++)reference_pixels[n]=actual_pixels[n]=next();
  world_mask_active=i%3==0;world_mask_left=8;world_mask_right=232;world_mask_top=31;world_mask_bottom=153;
  screen=(u16*)reference_pixels;reference_box(x,y,w,h);
  screen=(u16*)actual_pixels;proposal_box(x,y,w,h);
  assert(!memcmp(reference_pixels,actual_pixels,sizeof reference_pixels));count++;
 }
 const int cards[][4]={{8,31,224,123},{8,31,224,122},{8,31,224,119},{12,42,216,105},{20,38,200,114},{26,29,188,131},{136,3,64,17},{5,99,230,56}};
 for(unsigned i=0;i<sizeof cards/sizeof cards[0];i++)for(int cover=0;cover<2;cover++){
  for(unsigned n=0;n<9600;n++)reference_pixels[n]=actual_pixels[n]=next();world_mask_active=cover;
  screen=(u16*)reference_pixels;reference_box(cards[i][0],cards[i][1],cards[i][2],cards[i][3]);
  screen=(u16*)actual_pixels;proposal_box(cards[i][0],cards[i][1],cards[i][2],cards[i][3]);
  assert(!memcmp(reference_pixels,actual_pixels,sizeof reference_pixels));count++;
 }
 printf("PASS: %u full-frame arbitrary/clipped/opaque box comparisons\n",count);
}
'''
with tempfile.TemporaryDirectory(prefix='feedback-box-') as folder:
    folder = Path(folder)
    source = folder / 'oracle.c'
    source.write_text(head + body + tail)
    for sanitized in (False, True):
        target = folder / ('sanitized' if sanitized else 'strict')
        flags = ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if sanitized else []
        subprocess.run([os.environ.get('HOST_CC', 'cc'), '-std=c99', '-O1', '-g', '-Wall', '-Wextra', '-Werror', '-Wno-misleading-indentation', *flags, str(source), '-o', str(target)], check=True)
        environment = dict(os.environ, ASAN_OPTIONS='detect_leaks=0')
        subprocess.run([str(target)], check=True, env=environment)
