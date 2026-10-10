#!/usr/bin/env python3
"""Exact source portrait-matte and follower-displacement presentation checks.
Host pixels/motion only; whole-ROM cadence and actual four-way travel are separate.
"""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
from test_covenants_engine import function
ROOT=Path(__file__).resolve().parents[1]
HEAD=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "assets.h"
#include "covenants_creature_art.h"
#include "connected_roads.h"
#define COLD
#define GAME_HOST_TEST
#define WHITE PAL_WHITE
typedef unsigned char u8;typedef unsigned short u16;typedef unsigned int u32;
u16 pixels[19200];u16*screen=pixels;u8 old_portrait[1024];
int px,py,cx,cy,cx_q8,cy_q8,face,summoned;
int world_w=480,world_h=320,blocked,x0,y0,x1,y1;
int world_width(void){return world_w;}
int world_height(void){return world_h;}
int solid(int x,int y){return blocked&&x>=x0&&x<x1&&y>=y0&&y<y1;}
/* Portrait test draws without an opaque world overlay. Mask geometry has its independent camera oracle. */
int world_mask_active;
int game_world_rect_hidden(int x,int y,int w,int h){(void)x;(void)y;(void)w;(void)h;return 0;}
unsigned char covenants_walk_direction;
int ab(int x){return x<0?-x:x;}
static const u8*portrait(unsigned form){return form>=121&&form<=128?covenants_creature_art_portrait(form):old_portrait;}
const u8*companion_form_pixels(unsigned f,unsigned d,unsigned a){(void)f;(void)d;(void)a;return 0;}
'''
CHECKS=r'''
static unsigned portrait_pixels(void){
 unsigned form,n=0;int x,y;
 for(form=1;form<=128;form++){
  const u8*p=portrait(form);u8*actual=(u8*)pixels;
  memset(pixels,1,sizeof pixels);draw_form(form,18,56);
  for(y=0;y<160;y++)for(x=0;x<240;x++){
   unsigned expected=1;
   if(x>=18&&x<50&&y>=56&&y<88){unsigned v=p[(y-56)*32+x-18];expected=v?v:(form>=121?PAL_GOLD4:1);}
   assert(actual[y*240+x]==expected);n++;
  }
 }
 return n;
}
static unsigned motion(void){
 unsigned seed=17,n,head;int original_x,original_y,dx,dy;
 world_w=480;world_h=320;blocked=0;
 for(n=0;n<100000;n++){
  /* Keep the old exact smoothing oracle for100000 genuinely open positions.
   * Outside-world positions now have the explicit safety contract below. */
  seed=seed*1664525u+1013904223u;px=32+(int)(seed%416);
  seed=seed*1664525u+1013904223u;py=32+(int)(seed%256);
  seed=seed*1664525u+1013904223u;cx_q8=32*256+(int)(seed%(416*256));
  seed=seed*1664525u+1013904223u;cy_q8=32*256+(int)(seed%(256*256));
  face=(int)(n%4);summoned=(int)(n%5!=0);cx=cx_q8>>8;cy=cy_q8>>8;covenants_walk_direction=(unsigned char)(n%4);head=covenants_walk_direction;
  original_x=cx_q8;original_y=cy_q8;dx=((px+(face==2?17:-17))*256-cx_q8)/6;dy=((py+8)*256-cy_q8)/6;
  if(summoned){original_x+=dx;original_y+=dy;if(dx||dy)head=ab(dx)>ab(dy)?(dx<0?2:3):(dy<0?1:0);}
  game_companion_follow();assert(cx_q8==original_x&&cy_q8==original_y&&cx==(cx_q8>>8)&&cy==(cy_q8>>8));assert(covenants_walk_direction==head);
 }
 for(head=0;head<4;head++){
  face=3;summoned=1;cx_q8=cy_q8=100*256;px=117;py=92;
  if(head==0)py+=24;else if(head==1)py-=24;else if(head==2)px-=24;else px+=24;
  game_companion_follow();assert(covenants_walk_direction==head);
  px=(cx_q8>>8)+17;py=(cy_q8>>8)-8;cx_q8=px*256-17*256;cy_q8=(py+8)*256;cx=cx_q8>>8;cy=cy_q8>>8;
  game_companion_follow();assert(covenants_walk_direction==head);
 }
 return n;
}
static unsigned boundaries(void){
 static const int sizes[4][2]={{240,160},{480,160},{240,320},{480,320}};
 unsigned size,corner,f,n=0;int expected;
 summoned=1;blocked=0;
 for(size=0;size<4;size++){
  world_w=sizes[size][0];world_h=sizes[size][1];
  for(corner=0;corner<4;corner++)for(f=0;f<4;f++){
   px=corner&1?world_w-6:5;py=corner&2?world_h-6:5;face=(int)f;
   cx=cx_q8=-40;cy=cy_q8=-40;cx_q8*=256;cy_q8*=256;
   game_companion_follow();assert(game_companion_position_open(cx,cy));
   assert(cx>=5&&cy>=5&&cx<world_w-5&&cy<world_h-5&&!solid(cx,cy));
   assert(cx==(cx_q8>>8)&&cy==(cy_q8>>8));n++;
  }
 }
 /* Desired follow position outside the world: smoothly follow the safe hero. */
 world_w=240;world_h=160;px=5;py=80;face=3;cx=40;cy=80;cx_q8=cx*256;cy_q8=cy*256;
 expected=cx_q8+(px*256-cx_q8)/6;game_companion_follow();
 assert(cx_q8==expected&&cy_q8==80*256&&game_companion_position_open(cx,cy));n++;
 /* A solid desired position falls back to the hero without crossing the wall. */
 blocked=1;x0=80;y0=104;x1=89;y1=113;px=100;py=100;face=3;cx=60;cy=100;cx_q8=cx*256;cy_q8=cy*256;
 expected=cx_q8+(px*256-cx_q8)/6;game_companion_follow();
 assert(cx_q8==expected&&cy_q8==100*256&&game_companion_position_open(cx,cy));n++;
 /* An already obstructed interpolated point must reseat with exact Q8 sync. */
 x0=72;y0=104;x1=81;y1=113;cx=72;cy=108;cx_q8=cx*256;cy_q8=cy*256;
 game_companion_follow();assert(cx==px&&cy==py&&cx_q8==px*256&&cy_q8==py*256);n++;
 blocked=0;return n;
}
int main(void){unsigned i,p,m,b;for(i=0;i<1024;i++)old_portrait[i]=i%5?0:(unsigned char)(i%96+1);p=portrait_pixels();m=motion();b=boundaries();printf("PASS: %u full-screen portrait pixels; %u identical free-space follower-motion cases; all four motion headings/idle retention; %u actual boundary/solid safety cases\n",p,m,b);return 0;}
'''
def main():
 game=(ROOT/'src/game.c').read_text();engine=(ROOT/'src/covenants_engine.inc').read_text();progression=(ROOT/'src/progression.c').read_text()
 position=function(game,'game_companion_position_open')
 code=HEAD+''.join(function(game,n)for n in ('pix','rect','sprite'))+function(progression,'draw_form')+position+function(game,'game_companion_reanchor')+function(engine,'game_companion_follow')+CHECKS
 results={}
 with tempfile.TemporaryDirectory(prefix='covenants-presentation-')as td:
  root=Path(td)
  for mode,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
   c=root/(mode+'.c');c.write_text(code);exe=root/mode
   subprocess.run(['cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*flags,'-Isrc',str(c),'src/covenants_creature_art.c','-o',str(exe)],cwd=ROOT,check=True)
   run=subprocess.run([str(exe)],capture_output=True,text=True,check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'});results[mode]=run.stdout.strip();print(run.stdout.strip())
  mutant=code.replace(position,'int game_companion_position_open(int x,int y){(void)x;(void)y;return 1;}\n');assert mutant!=code
  c=root/'negative-unbounded-follow.c';c.write_text(mutant);exe=root/'negative-unbounded-follow'
  subprocess.run(['cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Isrc',str(c),'src/covenants_creature_art.c','-o',str(exe)],cwd=ROOT,check=True)
  failure=subprocess.run([str(exe)],capture_output=True,text=True);assert failure.returncode!=0 and 'Assertion' in failure.stderr
  results['unbounded_follower_mutation_rejected']={'exit_code':failure.returncode,'stderr':failure.stderr.strip()};print('PASS: unbounded follower mutation rejected')
 sources=['src/game.c','src/covenants_engine.inc','src/connected_roads.h','src/progression.c','src/covenants_creature_art.c']
 (ROOT/'build/covenants-presentation-host.json').write_text(json.dumps({'scope':__doc__,'results':results,'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}},indent=2)+'\n')
if __name__=='__main__':main()
