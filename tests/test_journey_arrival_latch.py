#!/usr/bin/env python3
"""Real transport logic, including the controller-observed Southern bounce."""
import ctypes as C
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class Entry(C.Structure):
 _fields_=[(n,C.c_ubyte)for n in ('room','action','target','spawn')]+[(n,C.c_short)for n in ('x','y')]+[(n,C.c_ubyte)for n in ('w','h')]
class Arrival(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup);p=Path(cls.tmp.name)/'travel.so'
  subprocess.run(['cc','-shared','-fPIC','-std=c99','-O2','-Wall','-Wextra','-Werror',str(ROOT/'src/travel_feedback.c'),'-o',str(p)],check=True)
  cls.lib=C.CDLL(str(p));cls.lib.travel_feedback_step.restype=C.c_int;n=C.c_uint.in_dll(cls.lib,'travel_entry_count').value;cls.entries=(Entry*n).in_dll(cls.lib,'travel_entries')
 def test_southern_normal_walk_from_exact_saved_spawn(self):
  # All are real positions on the narrow arrival corridor, ending outside the
  # dock. Former ten-pixel band released on y284, then triggered at y272.
  self.lib.travel_feedback_arrive(30,240,284)
  for y in range(284,238,-1):self.assertEqual(self.lib.travel_feedback_step(30,240,y,64,0),-1,('bounce',y))
  returned=[]
  for y in range(238,274):
   n=self.lib.travel_feedback_step(30,240,y,128,0)
   if n>=0:returned.append(n)
  self.assertEqual(len(returned),1);self.assertEqual(self.entries[returned[0]].target,22)
 def test_same_guard_all_authored_transports(self):
  for i,e in enumerate(self.entries):
   x=e.x+e.w//2;y=e.y+e.h//2
   for edge in ((x,e.y+e.h+11),(x,e.y-12),(e.x-12,y),(e.x+e.w+11,y)):
    self.lib.travel_feedback_arrive(e.room,*edge)
    # Destination's central rectangle remains quiet after approach from each
    # canonical-sized outer margin, under every held cardinal direction.
    for key in (16,32,64,128):
     self.assertNotEqual(self.lib.travel_feedback_step(e.room,x,y,key,0),i)
    self.lib.travel_feedback_step(e.room,-200,-200,64,0)
    self.assertEqual(self.lib.travel_feedback_step(e.room,x,y,64,0),i)
 def test_interaction_buttons_and_lock_never_travel(self):
  for i,e in enumerate(self.entries):
   for held,lock in ((1,0),(2,0),(4,0),(256,0),(512,0),(64,1)):
    self.lib.travel_feedback_reset();self.assertEqual(self.lib.travel_feedback_step(e.room,e.x+e.w//2,e.y+e.h//2,held,lock),-1)
if __name__=='__main__':unittest.main()
