#!/usr/bin/env python3
"""Every interrupted bank write offset for revision6 transactions.

Synthetic typed route starts from the exact native Magma34 fixture. Each target
was produced by a real typed core transaction, never edited into wire bytes.
All6146 cut positions run with final current policy; A/B destinations alternate.
"""
import ctypes as C,json,tempfile,time,unittest
from pathlib import Path
from test_underwater_save import ROOT,build,sha,FIXTURE_SHA,SOURCES,runtime_hashes
from test_save5 import Save,A,B,SIZE,compare_state
class UnderwaterPowerLoss(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='underwater-powerloss-');cls.addClassCleanup(cls.tmp.cleanup);cls.lib=build(Path(cls.tmp.name)/'normal')
 def test_every_byte_of_every_transaction_type_both_bank_destinations(self):
  lib=self.lib;s=Save();self.assertEqual(lib.underwater_test_earned34(C.byref(s)),0);changes=[]
  def change(name,call):
   nonlocal s
   new=Save.from_buffer_copy(bytes(s));result=call(new);self.assertIn(result,(0,1,2,3),(name,result));self.assertEqual(lib.save5_validate(C.byref(new)),1,name);changes.append((name,s,new));s=new
  change('arrival',lambda x:lib.underwater_visit(C.byref(x),46))
  for room in (47,48,49):self.assertEqual(lib.underwater_visit(C.byref(s),room),1)
  for q in (38,39,40):
   self.assertEqual(lib.underwater_test_ready(C.byref(s),q),0);change(f'quest{q}',lambda x,q=q:lib.underwater_quest_claim(C.byref(x),q))
  for room in range(50,54):self.assertEqual(lib.underwater_visit(C.byref(s),room),1)
  for family,bits in ((23,(1,2)),(24,(1,2,4))):
   for bit in bits:change(f'discovery{family}:{bit}',lambda x,family=family,bit=bit:lib.underwater_discover(C.byref(x),family,bit))
  for token in range(3,9):change(f'first-source{token}',lambda x,token=token:lib.underwater_field_recruit(C.byref(x),token))
  for family in range(17,25):
   token=family-16;base=49+3*(family-17)
   for key in (1,2):
    if key==2:change(f'first-extra{family}',lambda x,token=token:lib.underwater_branch_recruit(C.byref(x),token))
    slot=lib.underwater_test_slot(C.byref(s),base);identity=s.roster.instances[slot].instance_id
    change(f'trial{family}:{key}',lambda x,slot=slot,identity=identity,family=family,key=key,token=token:lib.underwater_trial_complete(C.byref(x),slot,identity,family,key,token))
    change(f'evolution{family}:{key}',lambda x,slot=slot,target=base+key:lib.creatures_evolve_to(C.byref(x.roster),slot,target,lib.underwater_context(C.byref(x)),1,1))
   # A further real copy proves the first-extra receipt never exhausts a source.
   change(f'later-extra{family}',lambda x,token=token:lib.underwater_branch_recruit(C.byref(x),token))
  for q in range(41,46):
   self.assertEqual(lib.underwater_test_ready(C.byref(s),q),0);change(f'gear-quest{q}',lambda x,q=q:lib.underwater_quest_claim(C.byref(x),q))
  for room in (46,47):change(f'anchor{room}',lambda x,room=room:lib.underwater_anchor(C.byref(x),room))
  checks=0;start=time.monotonic();rows=[]
  for index,(name,old,new) in enumerate(changes):
   lib.save5_test_reset_writer();lib.save5_test_fail_after(-1);lib.sram[:]=bytes([255])*32768
   self.assertEqual(lib.save5_store(C.byref(old)),1)
   if index&1:self.assertEqual(lib.save5_store(C.byref(old)),1)
   initial=bytes(lib.sram);preserved=B if index&1 else A;oldkey=compare_state(old);newkey=compare_state(new)
   for cut in range(SIZE+2):
    lib.save5_test_reset_writer();lib.save5_test_fail_after(cut);lib.sram[:]=initial
    ok=lib.save5_store(C.byref(new));self.assertEqual(ok,int(cut>=SIZE+1),(name,cut))
    out=Save();self.assertEqual(lib.save5_load(C.byref(out)),1,(name,cut));self.assertEqual(compare_state(out),newkey if ok else oldkey,(name,cut))
    self.assertEqual(bytes(lib.sram[:A]),initial[:A]);self.assertEqual(bytes(lib.sram[preserved:preserved+SIZE]),initial[preserved:preserved+SIZE]);checks+=1
   lib.save5_test_fail_after(-1);rows.append({'transaction':name,'cut_positions':SIZE+2,'destination':'A' if index&1 else 'B'})
   print(name,'all cuts pass',flush=True)
  report={'scope':'Synthetic typed transaction every-cut interruption test, not native acquisition','result':'PASS','transactions':rows,'checks':checks,'seconds':time.monotonic()-start,'fixture_sha256':FIXTURE_SHA,'source_sha256':lib._source_hashes,'source_unchanged_during_measurement':lib._source_hashes==runtime_hashes()}
  (ROOT/'docs/evidence/underwater-save-powerloss.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
