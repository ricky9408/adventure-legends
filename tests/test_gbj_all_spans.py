#!/usr/bin/env python3
"""All six GBJ text families against the frozen G4 span loop, with canaries."""
from pathlib import Path
import os,subprocess,tempfile
from test_covenants_engine import function
ROOT=Path(__file__).resolve().parents[1]
game=(ROOT/'src/game.c').read_text();core=function(game,'text_spans')
head=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "ui.h"
#include "companion_guide_text.h"
#include "journey_map_text.h"
#include "gear_preview_text.h"
#include "treasure_text_text.h"
#include "opening_scene_data.h"
typedef uint16_t u16;u16*screen;
static u16 storage[19264],reference[19264],original[19264];
/* Exact frozen G4 text loop, with the immutable UiText pointer supplied rather
 * than indexing its global table. Reference instruction logic is unchanged. */
static void legacy(const UiText*t,int x,int y,int col){const UiRun*r=t->runs[x&1];int n=t->count[x&1];u16*base=screen+y*120+(x>>1),color=col|(col<<8);
 while(n--){u16*dst=base+r->offset;int count=r->count;u16 mask=r->mask;r++;
 if(mask==3)while(count--)*dst++=color;
 else if(mask==1)while(count--){*dst=(*dst&0xFF00)|col;dst++;}
 else while(count--){*dst=(*dst&255)|(col<<8);dst++;}}
}
'''
tail=r'''
static unsigned checks;
static void test(const UiText*t){
 int xs[4]={0,1,240-t->width,239-t->width};unsigned colors[4]={0,22,59,255};
 for(unsigned x=0;x<4;x++)for(unsigned bottom=0;bottom<2;bottom++)for(unsigned color=0;color<4;color++){
  if(xs[x]<0||xs[x]+t->width>240)continue;
  for(unsigned i=0;i<19264;i++)original[i]=(u16)(i*977u+checks*31u);
  memcpy(storage,original,sizeof storage);memcpy(reference,original,sizeof reference);
  screen=reference+32;legacy(t,xs[x],bottom?160-t->height:0,colors[color]);
  screen=storage+32;text_spans(t,xs[x],bottom?160-t->height:0,colors[color]);
  assert(!memcmp(storage,reference,sizeof storage));
  assert(!memcmp(storage,original,64));assert(!memcmp(storage+19232,original+19232,64));checks++;
 }
}
int main(void){
 for(unsigned i=0;i<TX_COUNT;i++)test(&ui_texts[i]);
 for(unsigned i=0;i<CG_COUNT;i++)test(&companion_guide_texts[i]);
 for(unsigned i=0;i<JM_TEXT_COUNT;i++)test(&journey_map_texts[i]);
 for(unsigned i=0;i<GP_COUNT;i++)test(&gear_preview_texts[i]);
 for(unsigned i=0;i<TT_COUNT;i++)test(&treasure_text_texts[i]);
 for(unsigned i=0;i<OS_TEXT_COUNT;i++)test(&opening_scene_texts[i]);
 printf("PASS %u full-frame/canary comparisons across %u actual text masks and both alignments\n",checks,TX_COUNT+CG_COUNT+JM_TEXT_COUNT+GP_COUNT+TT_COUNT+OS_TEXT_COUNT);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='shared-text-spans-')as temp:
 path=Path(temp);source=path/'test.c';source.write_text(head+core+tail)
 for label,flags in [('normal',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
  exe=path/label;subprocess.run(['cc','-std=c99','-O1','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Isrc',*flags,str(source),'src/ui.c','src/companion_guide_text.c','src/journey_map_text.c','src/gear_preview_text.c','src/treasure_text_text.c','src/opening_scene_data.c','-o',str(exe)],cwd=ROOT,check=True)
  subprocess.run([str(exe)],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'})
