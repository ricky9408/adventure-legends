#!/usr/bin/env python3
"""Every physical write cutoff in both banks, synthetic Return core changes."""
import ctypes as C,json,tempfile,time,unittest,hashlib
from pathlib import Path
from return_host_support import *
class ReturnPowerloss(unittest.TestCase):
 def test_each_write_all_new_transaction_classes_both_destinations(self):
  with tempfile.TemporaryDirectory(prefix='return-powerloss-') as tmp:
   lib=build(tmp);state,initial=initial_chapter(lib)
   # Every quest claim, every trial/evolution, both anchors, arrival and one
   # representative offered/objective state; all changes are typed jobs.
   changes=[row for row in initial if row[0].startswith(('claim','anchor')) or row[0] in ('arrival54','objective46:1')]
   changes+=trials(lib,state)
   for source,form,command,room,family in ((17,102,102,55,39),(18,104,104,58,40)):
    slot,id=select(lib,state,form,command);old=Save.from_buffer_copy(bytes(state))
    runjob(lib,state,Request(operation=7,source=source,room=room,slot=slot,instance_id=id,family=family,form=form,command=command),3)
    changes.append((f'repeat{family}',old,Save.from_buffer_copy(bytes(state))))
   start=time.monotonic();checks=0;rows=[]
   for name,old,new in changes:
    for destination in ('A','B'):
     lib.return_job_cancel();lib.save5_test_reset_writer();lib.save5_test_fail_after(-1);lib.sram[:]=bytes([255])*32768
     self.assertEqual(lib.save5_store(C.byref(old)),1)
     if destination=='A':self.assertEqual(lib.save5_store(C.byref(old)),1)
     initial=bytes(lib.sram);preserved=B if destination=='A' else A;oldkey=compare_state(old);newkey=compare_state(new)
     for cut in range(SIZE+2):
      lib.save5_test_reset_writer();lib.save5_test_fail_after(cut);lib.sram[:]=initial
      ok=lib.save5_store(C.byref(new));self.assertEqual(ok,int(cut>=SIZE+1),(name,destination,cut))
      out=Save();self.assertEqual(lib.save5_load(C.byref(out)),1,(name,destination,cut));self.assertEqual(compare_state(out),newkey if ok else oldkey,(name,destination,cut))
      self.assertEqual(bytes(lib.sram[:A]),initial[:A]);self.assertEqual(bytes(lib.sram[preserved:preserved+SIZE]),initial[preserved:preserved+SIZE]);checks+=1
     lib.save5_test_fail_after(-1);rows.append({'transaction':name,'destination':destination,'cut_positions':SIZE+2})
    print(name,'both banks every cutoff pass',flush=True)
   out=ROOT/'docs/evidence/return-save-powerloss.json';out.parent.mkdir(parents=True,exist_ok=True)
   out.write_text(json.dumps({'scope':'Synthetic host Return transactions; not native acquisition','result':'PASS','source_sha256':lib.source_hashes,'source_unchanged':runtime_hashes()==lib.source_hashes,'checks':checks,'transactions':rows,'seconds':round(time.monotonic()-start,3),'source_fixture_sha256':FIXTURE_SHA},indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
