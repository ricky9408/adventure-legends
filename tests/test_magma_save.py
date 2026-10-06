#!/usr/bin/env python3
"""Revision5 typed transactions/codec tests. Synthetic progression is not gameplay proof."""
import ctypes as C
import json
import tempfile
import unittest
import test_save5 as base
from test_save5 import ROOT,A,B,SIZE,Save,Instance,Roster,compare_state,repair_crc,BUSY,DONE,FAILED
FORMS=(31,34,37,40,43,46,95,97,99)
FAMILIES=(11,12,13,14,15,16,36,37,38)
TOKENS=(1,2,16,17,18,19,20,21,22)
MASKS=(3,3,15,7,3,3,3,7)
class MagmaSaveTests(base.Save5Tests):
 @classmethod
 def setUpClass(cls):
  super().setUpClass()
  for name in ('magma_can_enter','magma_visit','magma_anchor','magma_quest_available','magma_quest_offer','magma_quest_claim','magma_field_recruit','magma_discover','magma_source_claimed','magma_source_status','magma_branch_status','magma_branch_recruit'):
   getattr(cls.lib,name).argtypes=[C.POINTER(Save),C.c_uint];getattr(cls.lib,name).restype=C.c_int
  cls.lib.magma_quest_objective.argtypes=[C.POINTER(Save),C.c_uint,C.c_uint]
  cls.lib.magma_trial_complete.argtypes=[C.POINTER(Save)]+[C.c_uint]*5
  cls.lib.magma_trial_status.argtypes=[C.POINTER(Save)]+[C.c_uint]*5
  cls.lib.magma_discovery_state.argtypes=[C.POINTER(Save)]
  cls.lib.magma_context.argtypes=[C.POINTER(Save)]
  cls.lib.save5_validate_revision.argtypes=[C.POINTER(Save),C.c_uint]
  cls.lib.creatures_evolve_to.argtypes=[C.POINTER(Roster)]+[C.c_uint]*5
 def magma(self):
  self.reset();self.put((ROOT/'tests/fixtures/v5-revision4/southern-all41-town.sav').read_bytes());s=self.load()
  self.assertEqual(self.lib.magma_visit(C.byref(s),38),1)
  return s
 def unchanged(self,s,call,result):
  before=bytes(s);self.assertEqual(call(),result);self.assertEqual(bytes(s),before)
 def ready(self,s,q):
  self.assertIn(self.lib.magma_quest_offer(C.byref(s),q),(0,1))
  for bit in (1,2,4,8):
   if MASKS[q-30]&bit:self.assertIn(self.lib.magma_quest_objective(C.byref(s),q,bit),(0,1,2))
  self.assertEqual(self.lib.save5_quest_state(C.byref(s.quests),q),2)
 def claim(self,s,q):
  self.ready(s,q);self.assertEqual(self.lib.magma_quest_claim(C.byref(s),q),3)
  self.assertEqual(self.lib.save5_validate(C.byref(s)),1)
 def recruits(self):
  s=self.magma()
  for room in (39,40,41):self.assertEqual(self.lib.magma_visit(C.byref(s),room),1)
  self.claim(s,30);self.claim(s,31)
  for bit in (1,2,4):self.assertIn(self.lib.magma_discover(C.byref(s),bit),(1,2))
  for token in TOKENS[2:]:self.assertEqual(self.lib.magma_field_recruit(C.byref(s),token),3)
  return s
 def slot(self,s,form):return next(i for i,c in enumerate(s.roster.instances) if c.form_id==form)
 def trial(self,s,index,key=1,slot=None):
  if slot is None:slot=self.slot(s,FORMS[index]+int(index<2 and key==2))
  c=s.roster.instances[slot]
  self.assertEqual(self.lib.magma_trial_complete(C.byref(s),slot,c.instance_id,FAMILIES[index],key,TOKENS[index]),3)
  return slot
 def evolve(self,s,slot,target):
  self.assertEqual(self.lib.creatures_evolve_to(C.byref(s.roster),slot,target,self.lib.magma_context(C.byref(s)),1,1),0)
  self.assertEqual(self.lib.save5_validate(C.byref(s)),1)
 def completed(self):
  s=self.recruits();self.claim(s,32)
  for i in range(9):
   slot=self.trial(s,i);self.evolve(s,slot,FORMS[i]+1)
   if i<2:self.trial(s,i,2,slot);self.evolve(s,slot,FORMS[i]+2)
   elif i<6:
    self.assertEqual(self.lib.magma_branch_recruit(C.byref(s),TOKENS[i]),3)
    slot=self.trial(s,i,2);self.evolve(s,slot,FORMS[i]+2)
  for q in range(33,38):self.claim(s,q)
  for room in range(42,46):self.assertEqual(self.lib.magma_visit(C.byref(s),room),1)
  return s
 def reject(self,s):
  before=bytes(self.sram);writes=self.lib.save5_test_write_count()
  self.assertEqual(self.lib.save5_validate(C.byref(s)),0)
  if self.lib.save5_begin(C.byref(s)):
   while self.lib.save5_status()==BUSY:self.lib.save5_step(3072)
  self.assertEqual(self.lib.save5_status(),FAILED);self.assertEqual(bytes(self.sram),before)
  self.assertEqual(self.lib.save5_test_write_count(),writes)
 def test_magma_all65_34_individuals_31_gear_38_quests(self):
  s=self.completed()
  self.assertEqual(sum(c.form_id!=0 for c in s.roster.instances),34)
  self.assertEqual(sum(x.bit_count() for x in s.roster.obtained),65)
  self.assertEqual(sum(e.item_id!=0 for e in s.equipment.bag),31)
  self.assertTrue(all(self.lib.save5_quest_state(C.byref(s.quests),q)==3 for q in range(38)))
  self.assertEqual(self.lib.magma_context(C.byref(s)),0x300)
  self.assertEqual(self.lib.magma_discovery_state(C.byref(s)),3)
  self.store(s);self.assertEqual(compare_state(self.load()),compare_state(s))
  self.assertEqual(self.lib.save5_validate_revision(C.byref(s),5),1)
  for rev in range(1,5):self.assertEqual(self.lib.save5_validate_revision(C.byref(s),rev),0)
 def test_magma_exact_quest_gates_prefixes_discovery_and_no_automatic_credit(self):
  s=self.magma();events=bytes(s.roster.expedition_events);aid=bytes(s.roster.lifetime_field_aid)
  self.unchanged(s,lambda:self.lib.magma_visit(C.byref(s),42),4)
  for q in (32,33,37):self.unchanged(s,lambda:self.lib.magma_quest_offer(C.byref(s),q),4)
  self.assertEqual(self.lib.magma_visit(C.byref(s),41),1)
  for bit in (2,4):self.unchanged(s,lambda:self.lib.magma_discover(C.byref(s),bit),4)
  self.assertEqual(self.lib.magma_discover(C.byref(s),1),1)
  self.unchanged(s,lambda:self.lib.magma_field_recruit(C.byref(s),22),4)
  self.assertEqual(self.lib.magma_discover(C.byref(s),2),1);self.assertEqual(self.lib.magma_discover(C.byref(s),4),2)
  self.assertEqual(self.lib.magma_field_recruit(C.byref(s),22),3)
  self.unchanged(s,lambda:self.lib.magma_field_recruit(C.byref(s),22),0)
  self.claim(s,30);self.claim(s,31);self.lib.magma_quest_offer(C.byref(s),32)
  self.unchanged(s,lambda:self.lib.magma_quest_objective(C.byref(s),32,2),4)
  self.assertEqual(self.lib.magma_quest_objective(C.byref(s),32,1),1)
  self.assertEqual(self.lib.magma_can_enter(C.byref(s),43),1);self.assertEqual(self.lib.magma_can_enter(C.byref(s),44),0)
  self.assertEqual(self.lib.magma_quest_objective(C.byref(s),32,2),1)
  self.assertEqual(self.lib.magma_quest_offer(C.byref(s),37),1)
  self.assertEqual(bytes(s.roster.expedition_events),events);self.assertEqual(bytes(s.roster.lifetime_field_aid),aid)
 def test_magma_trial_identity_source_from_form_prerequisite_and_same_copy_floors(self):
  s=self.recruits();slot=self.slot(s,31);c=s.roster.instances[slot]
  for args,result in [((slot,c.instance_id+1,11,1,1),-1),((slot,c.instance_id,12,1,2),-1),((slot,c.instance_id,11,1,16),-1),((slot,c.instance_id,11,2,1),4)]:
   self.unchanged(s,lambda:self.lib.magma_trial_complete(C.byref(s),*args),result)
  self.trial(s,0);self.assertEqual(s.roster.instances[slot].trial_flags,1)
  self.assertGreaterEqual(s.roster.instances[slot].level,26);self.assertGreaterEqual(s.roster.instances[slot].bond,45)
  self.evolve(s,slot,32);self.unchanged(s,lambda:self.lib.magma_trial_complete(C.byref(s),slot,c.instance_id,11,2,1),4)
  self.claim(s,32);self.trial(s,0,2,slot);self.assertEqual(s.roster.instances[slot].trial_flags,3)
  self.assertGreaterEqual(s.roster.instances[slot].level,32);self.assertGreaterEqual(s.roster.instances[slot].bond,60)
  bad=Save.from_buffer_copy(bytes(s));bad.roster.instances[slot].bond=59;self.reject(bad)
  bad=Save.from_buffer_copy(bytes(s));bad.roster.instances[slot].trial_flags=2;self.reject(bad)
  # Existing generic aid history is never source/trial provenance or suppression.
  s.roster.lifetime_field_aid[:]=bytes([255])*16
  slot=self.trial(s,2,2);self.assertEqual(s.roster.instances[slot].trial_flags,2)
  bad=Save.from_buffer_copy(bytes(s));bad.quests.region_flags[9]&=~1;self.reject(bad)
 def test_magma_linear_key2_cannot_exist_on_unevolved_base_current_or_wire(self):
  self.lib.creatures_instance_validate.argtypes=[C.POINTER(Instance)]
  self.lib.creatures_instance_validate_revision.argtypes=[C.POINTER(Instance),C.c_uint]
  self.lib.creatures_mark_trial_qualified.argtypes=[C.POINTER(Instance),C.c_uint,C.c_uint]
  self.lib.creatures_has_trial_qualified.argtypes=[C.POINTER(Instance),C.c_uint,C.c_uint]
  for index,form in enumerate((31,34)):
   s=self.recruits();self.claim(s,32);slot=self.trial(s,index);c=s.roster.instances[slot]
   c.level=32;c.xp=self.lib.creatures_xp_threshold(32);c.bond=60
   before=bytes(c)
   self.assertEqual(self.lib.creatures_mark_trial_qualified(C.byref(c),FAMILIES[index],2),0)
   self.assertEqual(bytes(c),before)
   self.assertEqual(self.lib.save5_validate(C.byref(s)),1)
   self.reset();self.store(s);original=bytes(self.sram[A:A+SIZE])
   for flags in (2,3):
    bad=Save.from_buffer_copy(bytes(s));wrong=bad.roster.instances[slot];wrong.trial_flags=flags
    self.assertEqual(self.lib.creatures_instance_validate(C.byref(wrong)),0,(form,flags))
    self.assertEqual(self.lib.creatures_instance_validate_revision(C.byref(wrong),5),0)
    self.assertEqual(self.lib.creatures_has_trial_qualified(C.byref(wrong),FAMILIES[index],2),0)
    self.assertEqual(self.lib.save5_validate_revision(C.byref(bad),5),0)
    self.unchanged(bad,lambda:self.lib.magma_trial_complete(C.byref(bad),slot,wrong.instance_id,FAMILIES[index],2,TOKENS[index]),-1)
    self.reject(bad)
    forged=bytearray(original);forged[160+slot*24+14:160+slot*24+16]=flags.to_bytes(2,'little')
    self.reset();self.put(bytes([255])*32768);self.sram[A:A+SIZE]=repair_crc(forged)
    out=Save.from_buffer_copy(bytes([90])*C.sizeof(Save));before=bytes(out)
    self.assertEqual(self.lib.save5_load(C.byref(out)),0)
    self.assertEqual(self.lib.save5_has_valid(),0);self.assertEqual(bytes(out),before)

 def test_magma_branches_same_twice_real_third_and_receipt_minimums(self):
  s=self.recruits();token=16;slot=self.trial(s,2);self.evolve(s,slot,38)
  self.assertEqual(self.lib.magma_branch_recruit(C.byref(s),token),3)
  slot=self.trial(s,2);self.evolve(s,slot,38)
  before_ids={c.instance_id for c in s.roster.instances if c.form_id};events=bytes(s.roster.expedition_events);aid=bytes(s.roster.lifetime_field_aid)
  self.assertEqual(self.lib.magma_branch_recruit(C.byref(s),token),3)
  slot=self.slot(s,37);self.assertNotIn(s.roster.instances[slot].instance_id,before_ids)
  self.assertEqual(s.roster.instances[slot].trial_flags,0)
  self.trial(s,2,2,slot);self.evolve(s,slot,39)
  self.assertEqual(bytes(s.roster.expedition_events),events);self.assertEqual(bytes(s.roster.lifetime_field_aid),aid)
  self.store(s);self.assertEqual(compare_state(self.load()),compare_state(s))
  bad=Save.from_buffer_copy(bytes(s))
  for n,c in enumerate(bad.roster.instances):
   if c.form_id in (38,39) and n!=slot:C.memset(C.byref(bad.roster.instances[n]),0,C.sizeof(Instance))
  self.reject(bad)
 def test_magma_admission_boundary_atomic_refusal_missing_sources_still_allowed(self):
  s=self.magma()
  # Duplicate raw grants are fixture-only: preserve historical over-budget legality.
  for _ in range(88):self.assertNotEqual(self.lib.creatures_grant(C.byref(s.roster),1,30,20,0,0),255)
  self.claim(s,30);self.claim(s,31)
  self.lib.magma_visit(C.byref(s),39);self.assertEqual(self.lib.magma_field_recruit(C.byref(s),16),3)
  slot=self.trial(s,2);self.evolve(s,slot,38)
  self.assertEqual(self.lib.magma_branch_recruit(C.byref(s),16),3)
  slot=self.trial(s,2)
  before=bytes(s);self.assertNotEqual(self.lib.creatures_evolve_to(C.byref(s.roster),slot,38,0x100,1,1),0);self.assertEqual(bytes(s),before)
  self.unchanged(s,lambda:self.lib.magma_branch_recruit(C.byref(s),16),6)
  self.trial(s,2,2,slot);self.evolve(s,slot,39)
  self.unchanged(s,lambda:self.lib.magma_field_recruit(C.byref(s),16),0)
  self.store(s);self.assertEqual(compare_state(self.load()),compare_state(s))
 def test_magma_overbudget_old_roster_and_full160_preserved(self):
  s=self.magma()
  while sum(c.form_id!=0 for c in s.roster.instances)<159:self.assertNotEqual(self.lib.creatures_grant(C.byref(s.roster),1,30,20,0,0),255)
  self.assertEqual(self.lib.save5_validate(C.byref(s)),1)
  self.claim(s,30);self.ready(s,31)
  self.unchanged(s,lambda:self.lib.magma_quest_claim(C.byref(s),31),5)
  self.store(s);self.assertEqual(compare_state(self.load()),compare_state(s))
 def test_magma_status_and_claim_identity_exhaustion_agree_and_remain_atomic(self):
  s=self.magma();self.lib.magma_visit(C.byref(s),39);s.roster.next_instance_id=0xffffffff
  self.assertEqual(self.lib.save5_validate(C.byref(s)),1)
  for token in (16,19,20):
   self.unchanged(s,lambda:self.lib.magma_source_status(C.byref(s),token),7)
   self.unchanged(s,lambda:self.lib.magma_field_recruit(C.byref(s),token),7)
  self.ready(s,30);self.unchanged(s,lambda:self.lib.magma_quest_claim(C.byref(s),30),7)
  s=self.recruits();slot=self.trial(s,2);self.evolve(s,slot,38);s.roster.next_instance_id=0xffffffff
  self.unchanged(s,lambda:self.lib.magma_branch_status(C.byref(s),16),7)
  self.unchanged(s,lambda:self.lib.magma_branch_recruit(C.byref(s),16),7)
  self.unchanged(s,lambda:self.lib.magma_source_status(C.byref(s),16),0)
  self.unchanged(s,lambda:self.lib.magma_field_recruit(C.byref(s),16),0)
  self.unchanged(s,lambda:self.lib.magma_quest_claim(C.byref(s),30),0)

 def test_magma_revision4_fixtures_exact_payload_migration(self):
  for filename in ('southern-all41-town.sav','southern-minimal8-town.sav'):
   data=(ROOT/'tests/fixtures/v5-revision4'/filename).read_bytes();self.reset();self.put(data);s=self.load()
   self.assertEqual(self.lib.save5_validate_revision(C.byref(s),4),1)
   self.store(s);self.assertEqual(compare_state(self.load()),compare_state(s))
   latest=max((A,B),key=lambda o:int.from_bytes(bytes(self.sram[o+8:o+12]),'little'))
   self.assertEqual(bytes(self.sram[latest+12:latest+14]),b'\x05\x00')
 def test_magma_crc_valid_bad_sources_trials_history_and_reserved_bits(self):
  s=self.completed();self.reset();self.store(s);bank=bytearray(self.sram[A:A+SIZE])
  cases=[]
  # All newly assigned content must stay rejected under every old revision.
  for revision in (1,2,3,4):
   b=bytearray(bank);b[12:14]=revision.to_bytes(2,'little');cases.append(b)
  for offset,value in [(4248+9,255),(4248+16,31),(4248+19,2),(4248+19,5),(4248+20,1),(4280+3,4),(4248+9,0),(4248+19,3)]:
   b=bytearray(bank);b[offset]=value;cases.append(b)
  for b in cases:
   self.reset();self.put(bytes([255])*32768);self.sram[A:A+SIZE]=repair_crc(b);out=Save.from_buffer_copy(bytes([90])*C.sizeof(Save));before=bytes(out)
   self.assertEqual(self.lib.save5_load(C.byref(out)),0);self.assertEqual(self.lib.save5_has_valid(),0);self.assertEqual(bytes(out),before)
 def test_magma_exact_room_anchor_prefix_policy_and_all_unassigned_bytes(self):
  s=self.completed()
  for room in range(38,46):
   for spawn in range(6):
    t=Save.from_buffer_copy(bytes(s));t.campaign.room=room;t.campaign.spawn=spawn
    expected=spawn<3 if room<40 else spawn==0
    self.assertEqual(self.lib.save5_validate(C.byref(t)),expected,(room,spawn))
    self.assertEqual(self.lib.save5_validate_revision(C.byref(t),5),expected,(room,spawn))
   if room<40:
    self.assertEqual(self.lib.magma_anchor(C.byref(s),room),1)
    t=Save.from_buffer_copy(bytes(s));t.campaign.room=room;t.campaign.spawn=3
    self.assertEqual(self.lib.save5_validate(C.byref(t)),1);self.store(t);self.assertEqual(compare_state(self.load()),compare_state(t))
  for index in (4,5,6,7,10,11,12,13,14,15,17,20,21,22,23,24,25,26,27,28,29,30,31):
   for bit in range(8):
    t=Save.from_buffer_copy(bytes(s));t.quests.region_flags[index]=1<<bit;self.reject(t)
  for bit in (4,8,16,32,64,128):
   t=Save.from_buffer_copy(bytes(s));t.quests.anchors[3]|=bit;self.reject(t)
 def test_magma_FULL_discovery_stays_READY_and_trial_can_finish(self):
  s=self.recruits();slot=self.slot(s,37)
  while sum(c.form_id!=0 for c in s.roster.instances)<160:self.lib.creatures_grant(C.byref(s.roster),1,30,20,0,0)
  self.trial(s,2,2,slot)
  self.unchanged(s,lambda:self.lib.magma_field_recruit(C.byref(s),22),0)
  # A separate still-unclaimed discovery gets no receipt/ID on FULL.
  s=self.magma();self.lib.magma_visit(C.byref(s),41)
  while sum(c.form_id!=0 for c in s.roster.instances)<160:self.lib.creatures_grant(C.byref(s.roster),1,30,20,0,0)
  for bit in (1,2,4):self.assertIn(self.lib.magma_discover(C.byref(s),bit),(1,2))
  self.assertEqual(self.lib.magma_discovery_state(C.byref(s)),2)
  self.unchanged(s,lambda:self.lib.magma_field_recruit(C.byref(s),22),5)
 def test_magma_every_cut_mixed_reward_branch_trial_discovery_and_evolution(self):
  transitions=[];s=self.magma()
  def change(name,fn):
   nonlocal s
   t=Save.from_buffer_copy(bytes(s));fn(t);transitions.append((name,s,t));s=t
  for room in (39,40,41):self.lib.magma_visit(C.byref(s),room)
  for q in (30,31):
   self.ready(s,q);change('Q'+str(q),lambda t:self.lib.magma_quest_claim(C.byref(t),q))
  for bit in (1,2,4):change('discovery'+str(bit),lambda t:self.lib.magma_discover(C.byref(t),bit))
  for token in TOKENS[2:]:change('source'+str(token),lambda t:self.lib.magma_field_recruit(C.byref(t),token))
  self.ready(s,32);change('main-Q32',lambda t:self.lib.magma_quest_claim(C.byref(t),32))
  for i in range(9):
   slot=self.slot(s,FORMS[i]);change('trial'+str(FORMS[i])+'-1',lambda t:self.trial(t,i,1,slot))
   change('evolve'+str(FORMS[i]+1),lambda t:self.evolve(t,slot,FORMS[i]+1))
   if i<2:
    change('trial'+str(FORMS[i])+'-2',lambda t:self.trial(t,i,2,slot))
    change('evolve'+str(FORMS[i]+2),lambda t:self.evolve(t,slot,FORMS[i]+2))
   elif i<6:
    change('first-extra'+str(TOKENS[i]),lambda t:self.lib.magma_branch_recruit(C.byref(t),TOKENS[i]))
    slot=self.slot(s,FORMS[i]);change('trial'+str(FORMS[i])+'-2',lambda t:self.trial(t,i,2,slot))
    change('evolve'+str(FORMS[i]+2),lambda t:self.evolve(t,slot,FORMS[i]+2))
    change('later-extra'+str(TOKENS[i]),lambda t:self.lib.magma_branch_recruit(C.byref(t),TOKENS[i]))
  for q in range(33,38):
   self.ready(s,q);change('gear-Q'+str(q),lambda t:self.lib.magma_quest_claim(C.byref(t),q))
  for name,old,target in transitions:
   self.reset();self.store(old);initial=bytes(self.sram)
   for cut in range(SIZE+2):
    self.put(initial);self.lib.save5_test_reset_writer();self.lib.save5_test_fail_after(cut);ok=self.lib.save5_store(C.byref(target))
    self.assertEqual(ok,int(cut>=SIZE+1),(name,cut));self.assertEqual(compare_state(self.load()),compare_state(target if ok else old),(name,cut))
    self.assertEqual(bytes(self.sram[:A]),initial[:A]);self.assertEqual(bytes(self.sram[A:A+SIZE]),initial[A:A+SIZE])
   self.lib.save5_test_fail_after(-1)
def load_tests(loader,tests,pattern):
 return unittest.TestSuite(MagmaSaveTests(name) for name in loader.getTestCaseNames(MagmaSaveTests) if name.startswith('test_magma_'))
if __name__=='__main__':unittest.main(verbosity=2)
