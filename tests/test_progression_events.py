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
   for a in (*range(30,31),32,*range(34,256),65536,0xffffffff):
    for s in (0,1,5,6,255,0xffffffff):self.assertEqual(f(a,s),512)
   for a in range(34):
    for s in (6,255,65536,0xffffffff):self.assertEqual(f(a,s),512)
if __name__=='__main__':unittest.main(verbosity=2)
