#!/usr/bin/env python3
"""Exhaustive finite optical semantics against the retained pixel-step oracle."""
from pathlib import Path
import hashlib,os,subprocess,tempfile
from test_covenants_engine import function
ROOT=Path(__file__).resolve().parents[1]
REFERENCE_SHA='efaed1a0448a22a6deb115a78917ccba93a590fa93152ae01a18298dcef61756'
assert hashlib.sha256((ROOT/'assets/southern_beam_reference.c').read_bytes()).hexdigest()==REFERENCE_SHA
source=(ROOT/'src/south_game.c').read_text()
head='''#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "south_game.h"
#include "southern_beams.inc"
unsigned reference_south_puzzle_beam(const SouthPuzzle*,unsigned,SouthBeam[4]);
'''
code=head+''.join(function(source,n)for n in ('puzzle_valid','south_puzzle_step','south_puzzle_beam','contains','south_puzzle_receivers','south_puzzle_solved'))
code+=r'''
static unsigned cases;
static void compare(const SouthPuzzle*p,unsigned area){
 struct {unsigned guard0;SouthBeam rays[4];unsigned guard1;}a,b;
 unsigned expected,actual,i,v=0;
 memset(&a,0x5a,sizeof a);memset(&b,0x5a,sizeof b);
 expected=reference_south_puzzle_beam(p,area,a.rays);actual=south_puzzle_beam(p,area,b.rays);
 assert(expected==actual&&!memcmp(&a,&b,sizeof a));
 assert(!south_puzzle_beam(p,area,0));
 for(i=0;i<expected;i++){
  const SouthBeam*r=&a.rays[i];
  if(area==35&&((r->x1==r->x2&&r->x1==80&&56>=(r->y1<r->y2?r->y1:r->y2)&&56<=(r->y1>r->y2?r->y1:r->y2))||(r->y1==r->y2&&r->y1==56&&80>=(r->x1<r->x2?r->x1:r->x2)&&80<=(r->x1>r->x2?r->x1:r->x2))))v|=1;
  if(r->end_kind==SOUTH_BEAM_RECEIVER)v|=area==35?2:1;
 }
 assert(south_puzzle_receivers(p,area)==v);
 assert(south_puzzle_solved(p,area)==(expected&&v==(area==35?3u:1u)));
 cases++;
}
int main(void){unsigned area,bits,field,value,action;
 for(area=0;area<80;area++)for(bits=0;bits<8;bits++){
  SouthPuzzle p={{bits&1,(bits>>1)&1},(bits>>2)&1};compare(&p,area);
  if(area>=34&&area<=36)for(action=0;action<7;action++){
   SouthPuzzle q=p;int changed=south_puzzle_step(&q,area,action);
   if(changed>0)compare(&q,area);
  }
 }
 for(area=34;area<=36;area++)for(field=0;field<3;field++)for(value=2;value<256;value++){
  SouthPuzzle p={{1,1},1};((unsigned char*)&p)[field]=(unsigned char)value;compare(&p,area);
 }
 for(area=0;area<80;area++)compare(0,area);
 printf("PASS: %u complete optical/path/receiver/invalid-input comparisons;24 valid states and all action successors\n",cases);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='southern-beam-oracle-')as td:
 td=Path(td);(td/'oracle.c').write_text(code)
 for mode,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
  exe=td/mode
  subprocess.run(['cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror',*flags,'-Isrc',str(td/'oracle.c'),'assets/southern_beam_reference.c','src/south_art.c','-o',str(exe)],cwd=ROOT,check=True)
  subprocess.run([str(exe)],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
subprocess.run(['python3','tools/generate_southern_beams.py','--check'],cwd=ROOT,check=True)
