#!/usr/bin/env python3
"""Content8 interrupted SRAM writes. Synthetic host actions, genuine H input."""
import ctypes as C,json,tempfile,time,unittest
from pathlib import Path
import horizons_host_support as h
from horizons_host_support import *
class HorizonsPowerloss(unittest.TestCase):
 def test_all_source_boundaries_and_every_write_atomic_footprints(self):
  with tempfile.TemporaryDirectory(prefix='horizons-powerloss-') as tmp:
   l=build(tmp);changes=[];original=h.runjob
   def capture(lib,s,r,*args,**kwargs):
    old=Save.from_buffer_copy(bytes(s));result=original(lib,s,r,*args,**kwargs)
    if result==3 and r.operation in (6,7,10):changes.append((f'op{r.operation}:source{r.source}:q{r.quest}:family{r.family}',r.operation,r.source,r.quest,old,Save.from_buffer_copy(bytes(s))))
    return result
   h.runjob=capture
   try:s=h.complete(l)
   finally:h.runjob=original
   for i in range(12):
    move(l,s,ROOMS[i]);form=BASES[i]+1 if i<4 else BASES[i];slot,id=select(l,s,form,BASES[i]+1);old=Save.from_buffer_copy(bytes(s))
    runjob(l,s,Request(operation=8,source=33+i,family=41+i,room=ROOMS[i],slot=slot,instance_id=id,form=form,command=BASES[i]+1),3)
    changes.append((f'repeat{41+i}',8,33+i,0,old,Save.from_buffer_copy(bytes(s))))
   started=time.monotonic();checks=0;rows=[]
   cuts=(0,1,2,31,32,33,159,160,161,3999,4000,4032,4048,4176,4248,4280,4296,4456,4520,4544,4928,4944,5024,5056,6143,6144,6145)
   # Six distinct atomic footprints exhaust every physical write cutoff:
   # story invitation, both receipt bytes, both repeat receipt bytes, trial,
   # and latest gear claim. All other sources/claims use every wire boundary.
   for name,op,source,q,old,new in changes:
    exhaustive=(op==7 and source in (1,12)) or (op==8 and source in (33,44)) or (op==10 and ':family44' in name) or (op==6 and q==59)
    bounds=range(SIZE+2) if exhaustive else cuts
    for destination in ('A','B'):
     l.horizons_job_cancel();l.save5_test_reset_writer();l.save5_test_fail_after(-1);l.save5_test_corrupt_write(-1,0);l.sram[:]=bytes([255])*32768
     self.assertEqual(l.save5_store(C.byref(old)),1)
     if destination=='A':self.assertEqual(l.save5_store(C.byref(old)),1)
     initial=bytes(l.sram);preserved=B if destination=='A' else A;oldkey=compare_state(old);newkey=compare_state(new)
     for cut in bounds:
      l.save5_test_reset_writer();l.save5_test_fail_after(cut);l.sram[:]=initial
      ok=l.save5_store(C.byref(new));self.assertEqual(ok,int(cut>=SIZE+1),(name,destination,cut))
      out=Save();self.assertEqual(l.save5_load(C.byref(out)),1);self.assertEqual(compare_state(out),newkey if ok else oldkey,(name,destination,cut))
      self.assertEqual(bytes(l.sram[:A]),initial[:A]);self.assertEqual(bytes(l.sram[preserved:preserved+SIZE]),initial[preserved:preserved+SIZE]);checks+=1
     for corrupt in (1,32,160,4032,4248,4544,5024,6144):
      l.save5_test_reset_writer();l.save5_test_fail_after(-1);l.save5_test_corrupt_write(corrupt,1);l.sram[:]=initial
      self.assertEqual(l.save5_store(C.byref(new)),0,(name,destination,corrupt));l.save5_test_corrupt_write(-1,0)
      out=Save();self.assertEqual(l.save5_load(C.byref(out)),1);self.assertEqual(compare_state(out),oldkey)
      self.assertEqual(bytes(l.sram[preserved:preserved+SIZE]),initial[preserved:preserved+SIZE]);checks+=1
    rows.append(dict(transaction=name,every_write=exhaustive,cutoffs_per_bank=len(bounds),corrupt_readbacks_per_bank=8));print(name,'passed',flush=True)
   (ROOT/'docs/evidence/horizons-save-powerloss.json').write_text(json.dumps(dict(scope='Host-only content8 interrupted writers; no native acquisition assertion',result='PASS',checks=checks,transactions=rows,seconds=round(time.monotonic()-started,3),fixture_sha256=FIXTURE_SHA,source_sha256=l.source_hashes,source_unchanged=runtime_hashes()==l.source_hashes),indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
