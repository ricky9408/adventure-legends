#!/usr/bin/env python3
"""Eight-owner host lease compatibility: no native timing/gameplay claim."""
import os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHIM=r'''
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include "northern_powers.h"
int regional_power_time,southern_power_time,magma_power_time,underwater_power_time;
#ifndef OMIT_RETURN
int return_power_time;
#endif
#ifndef OMIT_HORIZONS
int horizons_power_time;
#endif
#ifndef OMIT_COVENANTS
int covenants_power_time;
#endif
int main(void){unsigned owner,other,before,cases=0;
 int *live[9]={0,&regional_power_time,&northern_power_time,&southern_power_time,&magma_power_time,&underwater_power_time,0,0,0};
#ifndef OMIT_RETURN
 live[6]=&return_power_time;
#endif
#ifndef OMIT_HORIZONS
 live[7]=&horizons_power_time;
#endif
#ifndef OMIT_COVENANTS
 live[8]=&covenants_power_time;
#endif
 assert(NORTHERN_TILES_RETURN==6&&NORTHERN_TILES_HORIZONS==7&&NORTHERN_TILES_COVENANTS==8);
 assert(!northern_powers_tiles_claim(0)&&!northern_powers_tiles_claim(9)&&!northern_powers_tiles_claim(UINT_MAX));
 for(owner=1;owner<=8;owner++){
  before=northern_powers_tiles_generation();assert(northern_powers_tiles_claim(owner));
  assert(northern_powers_tiles_owner()==owner&&northern_powers_tiles_generation()==before+1);
  for(other=1;other<=8;other++){
   assert(!northern_powers_tiles_claim(other));
   if(other!=owner)assert(!northern_powers_tiles_release(other));
   assert(northern_powers_tiles_owner()==owner&&northern_powers_tiles_generation()==before+1);cases++;
  }
  if(live[owner]){*live[owner]=20;assert(!northern_powers_tiles_release(owner));assert(northern_powers_tiles_generation()==before+1);*live[owner]=0;}
  assert(northern_powers_tiles_release(owner));
  assert(!northern_powers_tiles_owner()&&northern_powers_tiles_generation()==before+2);
 }
 for(owner=1;owner<=8;owner++)if(live[owner]){
  before=northern_powers_tiles_generation();*live[owner]=20;
  for(other=1;other<=8;other++){assert(!northern_powers_tiles_claim(other));assert(!northern_powers_tiles_owner()&&northern_powers_tiles_generation()==before);cases++;}
  *live[owner]=0;
 }
 printf("PASS: %u lease cases; eight legal owners, active effects protected, generations stable on refusal\n",cases);
 return 0;
}
'''
class Lease(unittest.TestCase):
 def run_variant(self,omit_return,omit_horizons=False,omit_covenants=False):
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);p=d/'lease.c';p.write_text(SHIM);exe=d/'lease'
   cmd=['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-ffunction-sections','-fdata-sections','-I',str(ROOT/'src'),str(p),str(ROOT/'src/northern_powers.c'),'-Wl,--gc-sections','-o',str(exe)]
   if omit_covenants:cmd.insert(1,'-DOMIT_COVENANTS=1')
   if omit_return:cmd.insert(1,'-DOMIT_RETURN=1')
   if omit_horizons:cmd.insert(1,'-DOMIT_HORIZONS=1')
   p=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr)
   p=subprocess.run([str(exe)],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr)
 def test_return_owner_and_all_historical_live_claimants(self):self.run_variant(False)
 def test_old_focused_link_without_optional_return_module(self):self.run_variant(True)
 def test_old_focused_link_without_optional_horizons_module(self):self.run_variant(False,True)
 def test_old_focused_link_without_both_optional_modules(self):self.run_variant(True,True)
 def test_focused_links_without_covenants_module(self):
  for r,h in ((False,False),(True,False),(False,True),(True,True)):
   with self.subTest(omit_return=r,omit_horizons=h):self.run_variant(r,h,True)
if __name__=='__main__':unittest.main(verbosity=2)
