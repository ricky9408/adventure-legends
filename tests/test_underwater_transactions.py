#!/usr/bin/env python3
"""Budgeted Save5 preflight / immutable-snapshot Underwater job parity tests."""
import ctypes as C,random,tempfile,unittest
from pathlib import Path
from test_underwater_save import build
from test_save5 import Save,Instance,BUSY,DONE,FAILED
class Request(C.Structure):
 _fields_=[(n,C.c_uint) for n in ('operation','room','quest','bit','source','slot','family','key','instance_id')]
def configure(lib):
 lib.save5_preflight_begin.argtypes=[C.POINTER(Save)];lib.save5_preflight_begin.restype=C.c_uint
 for n in ('save5_preflight_step','save5_preflight_status','save5_preflight_phase','save5_preflight_snapshot'):
  getattr(lib,n).argtypes=[C.c_uint,C.c_uint] if n.endswith('step') else [C.c_uint]
 lib.save5_preflight_snapshot.restype=C.c_void_p;lib.save5_preflight_matches.argtypes=[C.c_uint,C.POINTER(Save)]
 lib.underwater_job_begin.argtypes=[C.POINTER(Save),C.POINTER(Request),C.c_uint];lib.underwater_job_begin.restype=C.c_uint
 lib.underwater_job_step.argtypes=[C.c_uint,C.c_uint,C.c_uint]
 for n in ('underwater_job_status','underwater_job_phase','underwater_job_result'):getattr(lib,n).argtypes=[C.c_uint]
 return lib
class UnderwaterTransactionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='underwater-transactions-');cls.addClassCleanup(cls.tmp.cleanup);cls.lib=configure(build(Path(cls.tmp.name)/'normal'));cls.augmented=configure(build(Path(cls.tmp.name)/'augmented',True))
 def setUp(self):self.lib.underwater_job_cancel();self.lib.save5_test_reset_writer();self.lib.save5_test_fail_after(-1)
 def state(self,full=False):
  s=Save();self.assertEqual(self.lib.underwater_test_completed(C.byref(s),int(full)),0);return s
 def runjob(self,s,r,expected=None):
  before=bytes(s);sram=bytes(self.lib.sram);token=self.lib.underwater_job_begin(C.byref(s),C.byref(r),17);self.assertTrue(token)
  steps=0
  while self.lib.underwater_job_status(token)==BUSY:
   phase=self.lib.underwater_job_phase(token);result=self.lib.underwater_job_step(token,1024,17);steps+=1
   if phase!=6:self.assertEqual(bytes(s),before)
   self.assertEqual(bytes(self.lib.sram),sram);self.assertLess(steps,300)
  self.assertEqual(result,DONE);out=self.lib.underwater_job_result(token)
  if expected is not None:self.assertEqual(out,expected)
  after=bytes(s);self.assertEqual(self.lib.underwater_job_step(token,1024,17),DONE);self.assertEqual(bytes(s),after)
  self.assertFalse(self.lib.save5_preflight_active());return out
 def test_preflight_matches_full_validator_on_real_and_random_malformed_states(self):
  lib=self.lib;base=self.state();rng=random.Random(0x554e4436)
  for i in range(3000):
   s=Save.from_buffer_copy(bytes(base));data=(C.c_ubyte*C.sizeof(Save)).from_buffer(s)
   if i:
    for _ in range(1+i%3):data[rng.randrange(len(data))]=rng.randrange(256)
   expected=lib.save5_validate(C.byref(s));before=bytes(s);sr=bytes(lib.sram);token=lib.save5_preflight_begin(C.byref(s));self.assertTrue(token)
   for step in range(300):
    result=lib.save5_preflight_step(token,(1,64,1024,0xffffffff)[step%4])
    self.assertEqual(bytes(s),before)
    if result!=BUSY:break
   self.assertEqual(result,DONE if expected else FAILED,i)
   self.assertEqual(bool(lib.save5_preflight_snapshot(token)),bool(expected));self.assertEqual(bytes(lib.sram),sr)
   if expected:self.assertEqual(lib.save5_preflight_matches(token,C.byref(s)),1)
   lib.save5_preflight_cancel()
 def test_all_request_kinds_match_synchronous_transaction(self):
  lib=self.lib;base=self.state()
  cases=[(Request(operation=1,room=46),lambda s:lib.underwater_visit(C.byref(s),46)),
   (Request(operation=2,room=46),lambda s:lib.underwater_anchor(C.byref(s),46)),
   (Request(operation=3,quest=41),lambda s:lib.underwater_quest_offer(C.byref(s),41)),
   (Request(operation=4,quest=41,bit=1),lambda s:lib.underwater_quest_objective(C.byref(s),41,1)),
   (Request(operation=6,quest=45),lambda s:lib.underwater_quest_claim(C.byref(s),45)),
   (Request(operation=7,source=3),lambda s:lib.underwater_field_recruit(C.byref(s),3)),
   (Request(operation=8,source=1),lambda s:lib.underwater_branch_recruit(C.byref(s),1)),
   (Request(operation=9,family=24,bit=4),lambda s:lib.underwater_discover(C.byref(s),24,4))]
  slot=lib.underwater_test_slot(C.byref(base),50);identity=base.roster.instances[slot].instance_id
  for op,fn in ((10,lib.underwater_trial_status),(11,lib.underwater_trial_complete)):
   cases.append((Request(operation=op,slot=slot,instance_id=identity,family=17,key=1,source=1),lambda s,fn=fn:fn(C.byref(s),slot,identity,17,1,1)))
  for request,fn in cases:
   a=Save.from_buffer_copy(bytes(base));b=Save.from_buffer_copy(bytes(base));expected=fn(a);self.runjob(b,request,expected);self.assertEqual(bytes(a),bytes(b),request.operation)
 def test_successful_teaching_field_repeat_trial_gear_and_implicit_objective(self):
  lib=self.lib;s=Save();self.assertEqual(lib.underwater_test_earned34(C.byref(s)),0);self.runjob(s,Request(operation=1,room=46),1)
  for q in (38,39):
   self.runjob(s,Request(operation=5,quest=q,bit=1),1);self.runjob(s,Request(operation=5,quest=q,bit=2),2);self.runjob(s,Request(operation=6,quest=q),3)
  self.runjob(s,Request(operation=1,room=48),1);self.runjob(s,Request(operation=7,source=3),3)
  slot=lib.underwater_test_slot(C.byref(s),49);identity=s.roster.instances[slot].instance_id
  self.runjob(s,Request(operation=10,slot=slot,instance_id=identity,family=17,key=2,source=1),1)
  self.runjob(s,Request(operation=11,slot=slot,instance_id=identity,family=17,key=2,source=1),3)
  self.assertEqual(lib.creatures_evolve_to(C.byref(s.roster),slot,51,lib.underwater_context(C.byref(s)),1,1),0)
  self.runjob(s,Request(operation=8,source=1),3)
  for q in (40,41,42,43,44,45):
   self.assertEqual(lib.underwater_test_ready(C.byref(s),q),0);self.runjob(s,Request(operation=6,quest=q),3)
  self.assertEqual(lib.save5_validate(C.byref(s)),1)
 def test_full_and_exhausted_denials_match_without_consuming_receipts(self):
  s=self.state(full=True);self.runjob(s,Request(operation=8,source=1),5)
  s=self.state();s.roster.next_instance_id=0xffffffff;self.runjob(s,Request(operation=8,source=1),7)
 def test_cancel_state_mutation_scene_change_and_load_invalidate_before_commit(self):
  lib=self.lib;base=self.state();request=Request(operation=8,source=1)
  for mode in ('cancel','scene','load','state'):
   for target_phase in range(7):
    s=Save.from_buffer_copy(bytes(base));original=bytes(s);token=lib.underwater_job_begin(C.byref(s),C.byref(request),17);self.assertTrue(token)
    while lib.underwater_job_phase(token)<target_phase and lib.underwater_job_status(token)==BUSY:lib.underwater_job_step(token,1024,17)
    if lib.underwater_job_phase(token)!=target_phase:lib.underwater_job_cancel();continue
    if mode=='cancel':lib.underwater_job_cancel();self.assertNotEqual(lib.underwater_job_step(token,1024,17),DONE)
    elif mode=='scene':self.assertEqual(lib.underwater_job_step(token,1024,18),FAILED)
    elif mode=='load':out=Save();self.assertEqual(lib.save5_load(C.byref(out)),1);self.assertEqual(lib.underwater_job_step(token,1024,17),FAILED)
    else:
     s.roster.instances[0].cosmetic_seed^=1;original=bytes(s)
     while lib.underwater_job_status(token)==BUSY:lib.underwater_job_step(token,1024,17)
     self.assertEqual(lib.underwater_job_status(token),FAILED)
    self.assertEqual(bytes(s),original)
 def test_copied_request_and_writer_ownership(self):
  lib=self.lib;s=self.state();request=Request(operation=8,source=1);token=lib.underwater_job_begin(C.byref(s),C.byref(request),17);self.assertTrue(token)
  request.source=8;self.assertEqual(lib.save5_begin(C.byref(s)),0);self.assertEqual(lib.save5_preflight_begin(C.byref(s)),0)
  count=sum(c.form_id==49 for c in s.roster.instances)
  while lib.underwater_job_step(token,1024,17)==BUSY:pass
  self.assertEqual(lib.underwater_job_result(token),3);self.assertEqual(sum(c.form_id==49 for c in s.roster.instances),count+1)
  self.assertEqual(lib.save5_begin(C.byref(s)),1);self.assertEqual(lib.underwater_job_begin(C.byref(s),C.byref(request),17),0)
  while lib.save5_status()==BUSY:lib.save5_step(1024)
  self.assertEqual(lib.save5_status(),DONE)
 def test_unused_fields_and_wrapped_ids_fail_closed(self):
  s=self.state()
  for r in (Request(operation=1,room=46,key=1),Request(operation=8,source=65537),Request(operation=11,source=1,family=17,key=1,slot=65536,instance_id=1),Request(operation=65537,room=46)):
   before=bytes(s);self.assertEqual(self.lib.underwater_job_begin(C.byref(s),C.byref(r),17),0);self.assertEqual(bytes(s),before)
 def test_bounded_full48_mixed_bundle_has_no_partial_first_item(self):
  lib=self.augmented;s=Save();self.assertEqual(lib.underwater_test_recruits(C.byref(s)),0)
  self.assertEqual(lib.underwater_test_ready(C.byref(s),45),0)
  for i in range(1,48):
   record=s.equipment.bag[i];record.item_id=99+i;record.rank=record.flags=0;record.quantity=1;record.reserved[:]=bytes(3)
   s.equipment.seen[record.item_id>>3]|=1<<(record.item_id&7)
  s.equipment.equipped[0]=0
  for i in range(1,5):s.equipment.equipped[i]=255
  self.assertEqual(lib.save5_validate(C.byref(s)),1)
  C.memset(C.byref(s.equipment.bag[47]),0,8)
  request=Request(operation=6,quest=45);before=bytes(s);token=lib.underwater_job_begin(C.byref(s),C.byref(request),17);self.assertTrue(token)
  while lib.underwater_job_status(token)==BUSY:
   lib.underwater_job_step(token,1024,17);self.assertEqual(bytes(s),before)
  self.assertEqual(lib.underwater_job_result(token),5);self.assertEqual(lib.save5_quest_state(C.byref(s.quests),45),2)
  s.equipment.seen[68>>3]|=1<<(68&7);token=lib.underwater_job_begin(C.byref(s),C.byref(request),17);self.assertTrue(token)
  while lib.underwater_job_step(token,1024,17)==BUSY:pass
  self.assertEqual(lib.underwater_job_result(token),3);self.assertEqual(sum(e.item_id==86 for e in s.equipment.bag),1)
  self.assertFalse(any(e.item_id==68 for e in s.equipment.bag));self.assertEqual(lib.save5_validate(C.byref(s)),1)
if __name__=='__main__':unittest.main(verbosity=2)
