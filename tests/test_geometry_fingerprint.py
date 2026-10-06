#!/usr/bin/env python3
"""Synthetic exact-source collision-cache invalidation contract, no native claim."""
from pathlib import Path
import ctypes,re,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class Fingerprint(unittest.TestCase):
 def test_collision_inputs_only(self):
  source=(ROOT/'src/game.c').read_text();a=source.index('static u32 collision_fingerprint[4]');b=source.index('COLD unsigned journal_page_count',a);body=source[a:b].replace('COLD ','')
  prefix='''#include "save5.h"
 typedef unsigned int u32;typedef unsigned short u16;
 enum { REGION_QUEST_DRY_ROAD=1 };Save5State adventure_save;
 int room,bridge_open,torches;unsigned room_flags,chapter_flags,calls,magma_calls,underwater_calls,props[3],underwater_props[3];
 short trial_parcels[2][2],region_game_crates[2][2];
 unsigned progress_bits(void){return room_flags|(chapter_flags<<16);}
 void southern_powers_geometry_changed(void){calls++;}
 void magma_powers_geometry_changed(void){magma_calls++;}
 void underwater_powers_geometry_changed(void){underwater_calls++;}
 int magma_game_is_room(unsigned a){return a>=38&&a<=45;}
 void magma_game_collision_inputs(unsigned out[3]){unsigned i;for(i=0;i<3;i++)out[i]=props[i];}
 void set_prop(unsigned i,unsigned value){if(i<3)props[i]=value;}
 /* Explicit synthetic regional collision inputs; the extracted engine
  * invalidation logic is the real current production implementation. */
 void underwater_game_collision_inputs(unsigned out[3]){unsigned i;for(i=0;i<3;i++)out[i]=underwater_props[i];}
 void set_underwater_prop(unsigned i,unsigned value){if(i<3)underwater_props[i]=value;}
 void set_dry(unsigned n){adventure_save.quests.objectives[1]=(Save4U16)n;}
 void set_point(unsigned mode,unsigned index,int n){if(mode)region_game_crates[index/2][index%2]=(short)n;else trial_parcels[index/2][index%2]=(short)n;}
 '''
  with tempfile.TemporaryDirectory() as td:
   c=Path(td)/'case.c';c.write_text(prefix+body);lib=Path(td)/'case.so'
   subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC','-Isrc',str(c),'-o',str(lib)],cwd=ROOT,check=True)
   l=ctypes.CDLL(str(lib))
   def var(n):return ctypes.c_uint.in_dll(l,n)
   def expect(delta):
    before=var('calls').value;l.game_geometry_sync();self.assertEqual(var('calls').value-before,delta);self.assertEqual(var('magma_calls').value,var('calls').value);self.assertEqual(var('underwater_calls').value,var('calls').value)
   expect(0)
   for area in (1,2,4,8,13,15,17,20,22,30,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53):
    var('room').value=area;expect(1);expect(0)
    if area==1:var('bridge_open').value^=1;expect(1)
    elif area==2:var('torches').value^=3;expect(1)
    elif 4<=area<14:var('room_flags').value^=1;expect(1);var('chapter_flags').value^=1;expect(1)
    elif area in (15,20):
     for i in range(4):l.set_point(area==20,i,16+i);expect(1);expect(0)
    elif area==17:l.set_dry(2);expect(1);l.set_dry(3);expect(0)
    elif 38<=area<=45:
     for i in range(3):l.set_prop(i,area+i);expect(1);expect(0)
     for i in range(3):l.set_underwater_prop(i,area+i);expect(0)
    elif 46<=area<=53:
     for i in range(3):l.set_underwater_prop(i,area+i);expect(1);expect(0)
     for i in range(3):l.set_prop(i,area+i);expect(0)
    else:
     var('bridge_open').value^=1;var('torches').value^=3;var('room_flags').value^=1;l.set_point(0,0,99);l.set_point(1,0,99);expect(0)
if __name__=='__main__':unittest.main(verbosity=2)
