#!/usr/bin/env python3
"""Original porch pixels versus the shared paired-pixel sprite blitter."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
from test_covenants_engine import function
ROOT=Path(__file__).resolve().parents[1]
reference=ROOT/'tests/fixtures/player-feedback-proposed/porch_reference.inc'
assert hashlib.sha256(reference.read_bytes()).hexdigest()==json.loads(reference.with_suffix('.json').read_text())['reference_sha256']
game=(ROOT/'src/game.c').read_text();draw=(ROOT/'src/covenants_draw.inc').read_text()
head=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "assets.h"
#include "covenants_art.h"
#define COLD
#define WHITE PAL_WHITE
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
u16 expected[19200],actual[19200],*screen;
int camera_x,camera_y,world_mask_active,world_mask_left=8,world_mask_right=232,world_mask_top=31,world_mask_bottom=153;
'''
code=head+''.join(function(game,n)for n in ('game_world_rect_hidden','pix','sprite'))+(ROOT/'tests/fixtures/player-feedback-proposed/porch_reference.inc').read_text()+function(draw,'floor_stamp')
code+=r'''
int main(void){unsigned images[]={COVENANTS_SPR_PORCH_LEFT,COVENANTS_SPR_PORCH_MARKS,COVENANTS_SPR_PORCH_RIGHT},i,count=0;int x,y,cover;
 for(i=0;i<3;i++)for(x=-15;x<263;x+=7)for(y=-15;y<183;y+=11)for(cover=0;cover<2;cover++){
  for(unsigned k=0;k<19200;k++)expected[k]=actual[k]=(unsigned short)(k*47+count*17);
  camera_x=(int)i*13;camera_y=(int)i*7;world_mask_active=cover;
  screen=expected;reference_floor_stamp(images[i],x,y);screen=actual;floor_stamp(images[i],x,y);
  /* A wholly covered sprite may be skipped; compare the final opaque panel. */
  if(cover)for(int yy=31;yy<153;yy++)for(int xx=8;xx<232;xx++){screen=expected;pix(xx,yy,1);screen=actual;pix(xx,yy,1);}
  assert(!memcmp(expected,actual,sizeof actual));count++;
 }
 printf("PASS: %u full-frame porch/transparent/clipped/camera/opaque-panel comparisons\n",count);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='feedback-porch-')as td:
 td=Path(td);(td/'oracle.c').write_text(code)
 for name,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
  exe=td/name
  subprocess.run(['cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*flags,'-Isrc',str(td/'oracle.c'),'src/covenants_art.c','-o',str(exe)],cwd=ROOT,check=True)
  subprocess.run([str(exe)],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
