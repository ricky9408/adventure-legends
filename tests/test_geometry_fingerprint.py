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
 int room,bridge_open,torches;unsigned room_flags,chapter_flags,calls;
 short trial_parcels[2][2],region_game_crates[2][2];
 unsigned progress_bits(void){return room_flags|(chapter_flags<<16);}
 void southern_powers_geometry_changed(void){calls++;}
 void set_dry(unsigned n){adventure_save.quests.objectives[1]=(Save4U16)n;}
 void set_point(unsigned mode,unsigned index,int n){if(mode)region_game_crates[index/2][index%2]=(short)n;else trial_parcels[index/2][index%2]=(short)n;}
 '''
  with tempfile.TemporaryDirectory() as td:
   c=Path(td)/'case.c';c.write_text(prefix+body);lib=Path(td)/'case.so'
   subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC','-Isrc',str(c),'-o',str(lib)],cwd=ROOT,check=True)
   l=ctypes.CDLL(str(lib))
   def var(n):return ctypes.c_uint.in_dll(l,n)
   def expect(delta):
    before=var('calls').value;l.game_geometry_sync();self.assertEqual(var('calls').value-before,delta)
   expect(0)
   for area in (1,2,4,8,13,15,17,20,22,30,37):
    var('room').value=area;expect(1);expect(0)
    if area==1:var('bridge_open').value^=1;expect(1)
    elif area==2:var('torches').value^=3;expect(1)
    elif 4<=area<14:var('room_flags').value^=1;expect(1);var('chapter_flags').value^=1;expect(1)
    elif area in (15,20):
     for i in range(4):l.set_point(area==20,i,16+i);expect(1);expect(0)
    elif area==17:l.set_dry(2);expect(1);l.set_dry(3);expect(0)
    else:
     var('bridge_open').value^=1;var('torches').value^=3;var('room_flags').value^=1;l.set_point(0,0,99);l.set_point(1,0,99);expect(0)
if __name__=='__main__':unittest.main(verbosity=2)
