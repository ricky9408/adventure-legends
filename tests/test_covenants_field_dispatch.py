#!/usr/bin/env python3
"""Exact chapter backend and missing-link rejection; host routing evidence only."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
SHIM=r'''
#include <assert.h>
#include <limits.h>
#include "field_world.h"
volatile int room;
unsigned calls[3][6];
#define WORLD(prefix,n) \
 int prefix##_game_is_room(unsigned a){return a==54u+8u*n;} \
 int prefix##_game_clear_box(int a,int b,int c,int d){assert(a==11&&b==12&&c==13&&d==14);calls[n][0]++;return 1;} \
 int prefix##_game_supercover(int a,int b,int c,int d){assert(a==11&&b==12&&c==13&&d==14);calls[n][1]++;return 1;} \
 unsigned prefix##_game_action_begin(unsigned c){assert(c==3);calls[n][2]++;return n+100;} \
 int prefix##_game_field_target(unsigned i,int*x,int*y,int*r){assert(i==7);*x=11;*y=12;*r=13;calls[n][3]++;return 1;} \
 int prefix##_game_field_hit(unsigned i,unsigned c,unsigned id,unsigned f,unsigned t){assert(i==7&&c==106&&id==1007&&f==105&&t==n+100);calls[n][4]++;return 1;} \
 void prefix##_game_revoke_cast(unsigned t){assert(t==n+100);calls[n][5]++;}
WORLD(return,0)
#ifndef OMIT_HORIZONS
WORLD(horizons,1)
#endif
#ifndef OMIT_COVENANTS
WORLD(covenants,2)
#endif
int main(void){unsigned a,n,i;int x=0,y=0,r=0;
 for(a=54;a<78;a++){
  int present=1;n=(a-54)/8;room=(int)a;
#ifdef OMIT_HORIZONS
  if(n==1)present=0;
#endif
#ifdef OMIT_COVENANTS
  if(n==2)present=0;
#endif
  assert(field_world_clear_box(11,12,13,14)==present);
  assert(field_world_supercover(11,12,13,14)==present);
  assert(field_world_action_begin(3)==(present?n+100:0));
  assert(field_world_target(7,&x,&y,&r)==present);
  assert(field_world_hit(7,106,1007,105,n+100)==present);
  field_world_revoke_cast(n+100);
 }
 for(n=0;n<3;n++)for(i=0;i<6;i++){
  unsigned expected=n==0&&i==5?0:8;
#ifdef OMIT_HORIZONS
  if(n==1)expected=0;
#endif
#ifdef OMIT_COVENANTS
  if(n==2)expected=0;
#endif
  assert(calls[n][i]==expected);
 }
 for(a=0;a<4;a++){
  static const unsigned invalid[4]={0,53,78,UINT_MAX};room=(int)invalid[a];
  assert(!field_world_is_room(invalid[a]));assert(!field_world_clear_box(11,12,13,14));
  assert(field_world_supercover(11,12,13,14)==-1);assert(!field_world_action_begin(3));
  assert(!field_world_target(7,&x,&y,&r));assert(!field_world_hit(7,106,1007,105,102));field_world_revoke_cast(102);
 }
 return 0;
}
'''
class Dispatch(unittest.TestCase):
 def test_backends_and_absence(self):
  with tempfile.TemporaryDirectory(prefix='covenants-field-')as td:
   root=Path(td);c=root/'dispatch.c';c.write_text(SHIM)
   for defines in ([],['OMIT_HORIZONS'],['OMIT_COVENANTS'],['OMIT_HORIZONS','OMIT_COVENANTS']):
    with self.subTest(omitted=defines):
     exe=root/('dispatch-'+str(len(defines))+'-'+str('OMIT_HORIZONS'in defines))
     subprocess.run(['cc','-std=c99','-O1','-Wall','-Wextra','-Werror','-pedantic','-Isrc',*['-D'+d for d in defines],str(c),'-o',str(exe)],cwd=ROOT,check=True)
     subprocess.run([str(exe)],check=True)
if __name__=='__main__':unittest.main(verbosity=2)
