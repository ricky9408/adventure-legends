#!/usr/bin/env python3
"""Pure source registry test, not gameplay acquisition evidence."""
from pathlib import Path
import ctypes,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class Events(unittest.TestCase):
 def test_registry(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'events.so'
   subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC','-Isrc','src/progression_events.c','-o',str(out)],cwd=ROOT,check=True)
   lib=ctypes.CDLL(str(out));f=lib.progression_encounter_event;f.argtypes=[ctypes.c_uint,ctypes.c_uint];f.restype=ctypes.c_uint
   old=[f(a,s) for a in range(30) for s in range(6)];self.assertEqual(old,list(range(180)))
   new=[f(a,s) for a in (31,33) for s in range(6)];self.assertEqual(new,list(range(180,192)))
   self.assertEqual(len(set(old+new)),192)
   rows={39:(220,5),41:(225,2),42:(227,1),43:(228,1),44:(229,2),45:(231,1)}
   magma=[f(a,slot) for a,(_,count) in rows.items() for slot in range(count)]
   self.assertEqual(magma,list(range(220,232)))
   self.assertEqual(len(set(old+new+magma)),204)
   return_rows={54:(296,2),56:(298,2),57:(300,3),58:(303,2),61:(305,3)}
   current=[f(a,slot) for a,(_,count) in return_rows.items() for slot in range(count)]
   self.assertEqual(current,list(range(296,308)))
   self.assertEqual(len(set(old+new+magma+current)),216)
   horizons_rows={63:(314,3),65:(317,3),66:(320,2),67:(322,3),69:(325,1)}
   horizons=[f(a,slot) for a,(_,count) in horizons_rows.items() for slot in range(count)]
   self.assertEqual(horizons,list(range(314,326)))
   self.assertEqual(len(set(old+new+magma+current+horizons)),228)
   rows.update(return_rows);rows.update(horizons_rows)
   for a in (*range(30,31),32,*range(34,256),65536,0xffffffff):
    if a in rows:
     for slot in range(rows[a][1],6):self.assertEqual(f(a,slot),512)
     continue
    for s in (0,1,5,6,255,0xffffffff):self.assertEqual(f(a,s),512)
   for a in range(34):
    for s in (6,255,65536,0xffffffff):self.assertEqual(f(a,s),512)
if __name__=='__main__':unittest.main(verbosity=2)
