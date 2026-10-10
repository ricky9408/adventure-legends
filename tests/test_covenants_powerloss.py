#!/usr/bin/env python3
"""Current9 torn-write evidence for typed rights, receipts, and quest rewards."""
import ctypes as C,hashlib,json,tempfile,time,unittest
import covenants_host_support as h
from covenants_host_support import *
class CovenantsPowerloss(unittest.TestCase):
 def test_all_boundaries_and_every_atomic_footprint_write(self):
  with tempfile.TemporaryDirectory(prefix='covenants-powerloss-') as tmp:
   l=build(tmp);changes=[];original=h.runjob
   def capture(lib,s,r,*args,**kwargs):
    old=Save.from_buffer_copy(bytes(s));result=original(lib,s,r,*args,**kwargs)
    if result in (1,2,3) and r.operation in (5,6,7):changes.append((f'op{r.operation}:source{r.source}:q{r.quest}',r.operation,r.source,r.quest,old,Save.from_buffer_copy(bytes(s))))
    return result
   h.runjob=capture
   try:h.story(l,True)
   finally:h.runjob=original
   started=time.monotonic();checks=0;rows=[]
   cuts=(0,1,2,31,32,33,159,160,161,3999,4000,4032,4048,4176,4248,4270,4271,4280,4287,4296,4456,4520,4544,4928,4944,5024,5056,6143,6144,6145)
   for name,op,source,q,old,new in changes:
    exhaustive=(op==6 and source in (4,8)) or (op==7 and source in (1,8)) or (op==5 and q==63)
    bounds=range(SIZE+2) if exhaustive else cuts
    for destination in ('A','B'):
     l.covenants_job_cancel();l.save5_test_reset_writer();l.save5_test_fail_after(-1);l.save5_test_corrupt_write(-1,0);l.sram[:]=bytes([255])*32768
     self.assertEqual(l.save5_store(C.byref(old)),1)
     if destination=='A':self.assertEqual(l.save5_store(C.byref(old)),1)
     initial=bytes(l.sram);preserved=B if destination=='A' else A;oldkey=compare_state(old);newkey=compare_state(new)
     for cut in bounds:
      l.save5_test_reset_writer();l.save5_test_fail_after(cut);l.sram[:]=initial
      ok=l.save5_store(C.byref(new));self.assertEqual(ok,int(cut>=SIZE+1),(name,destination,cut))
      out=Save();self.assertEqual(l.save5_load(C.byref(out)),1);self.assertEqual(compare_state(out),newkey if ok else oldkey,(name,destination,cut))
      self.assertEqual(bytes(l.sram[:A]),initial[:A]);self.assertEqual(bytes(l.sram[preserved:preserved+SIZE]),initial[preserved:preserved+SIZE]);checks+=1
     for corrupt in (1,32,160,4032,4248,4270,4271,4544,5024,6144):
      l.save5_test_reset_writer();l.save5_test_fail_after(-1);l.save5_test_corrupt_write(corrupt,1);l.sram[:]=initial
      self.assertEqual(l.save5_store(C.byref(new)),0,(name,destination,corrupt));l.save5_test_corrupt_write(-1,0)
      out=Save();self.assertEqual(l.save5_load(C.byref(out)),1);self.assertEqual(compare_state(out),oldkey);checks+=1
    rows.append(dict(transaction=name,every_write=exhaustive,cutoffs_per_bank=len(bounds),corrupt_readbacks_per_bank=10));print(name,'passed',flush=True)
   report=dict(scope='Host-only content9 interrupted writers; no native acquisition assertion',result='PASS',checks=checks,transactions=rows,seconds=round(time.monotonic()-started,3),fixture_sha256=FIXTURE_SHA,source_sha256=l.source_hashes,source_unchanged=runtime_hashes()==l.source_hashes)
   (ROOT/'docs/evidence/covenants-save-powerloss.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
