#!/usr/bin/env python3
"""Synthetic host Return transactions; distinct from controller/native QA."""
import ctypes as C,random,tempfile,unittest,subprocess,os,json
from pathlib import Path
from return_host_support import *
from test_save5 import repair_crc
class ReturnTransactions(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='return-transactions-');cls.addClassCleanup(cls.tmp.cleanup);cls.lib=build(cls.tmp.name)
 def setUp(self):self.lib.return_job_cancel();self.lib.save5_test_reset_writer();self.lib.save5_test_fail_after(-1)
 def test_104_history_52_retained_all_thirteen_trials_and_evolutions(self):
  l=self.lib;s,changes=initial_chapter(l);changes+=trials(l,s)
  self.assertEqual(sum(bool(c.form_id) for c in s.roster.instances),52)
  self.assertEqual(sum(x.bit_count() for x in s.roster.obtained),104)
  self.assertEqual(l.save5_store(C.byref(s)),1);out=Save();self.assertEqual(l.save5_load(C.byref(out)),1)
  self.assertEqual(compare_state(s),compare_state(out));self.assertEqual(bytes(s.roster.rewards[2:]),bytes(14))
  self.assertEqual(s.quests.region_flags[11],0)
 def test_party_full_first_invitation_stores_without_selecting(self):
  l=self.lib;s=source(l)
  for bit in (1,2):runjob(l,s,Request(operation=5,quest=46,bit=bit))
  runjob(l,s,Request(operation=6,quest=46),3)
  for room in (54,55):runjob(l,s,Request(operation=1,room=room),1)
  for bit in (1,2,4):runjob(l,s,Request(operation=5,quest=47,bit=bit))
  party=bytes(s.roster.party);selected=s.roster.selected_party;next_id=s.roster.next_instance_id
  runjob(l,s,Request(operation=6,quest=47,source=1),3)
  self.assertEqual(bytes(s.roster.party),party);self.assertEqual(s.roster.selected_party,selected)
  c=next(c for c in s.roster.instances if c.form_id==101)
  self.assertEqual((c.instance_id,c.level,c.bond,c.trial_flags,c.flags),(next_id,28,25,0,1))
 def test_repeats_are_exact_participant_new_attempt_and_no_credit(self):
  l=self.lib;s,_=initial_chapter(l)
  for token,form,command,room,family in ((17,101,102,55,39),(18,103,104,58,40)):
   slot,id=select(l,s,form,command);r=Request(operation=7,room=room,source=token,slot=slot,instance_id=id,family=family,form=form,command=command)
   scene=generation();party=bytes(s.roster.party);selected=s.roster.selected_party;quests=bytes(s.quests);gear=bytes(s.equipment);credits=bytes(s.roster.expedition_events)+bytes(s.roster.lifetime_field_aid)
   runjob(l,s,r,3,scene,3);self.assertEqual(s.roster.party[0],party[0]);self.assertEqual(s.roster.selected_party,selected)
   self.assertEqual(bytes(s.equipment),gear);self.assertEqual(bytes(s.roster.expedition_events)+bytes(s.roster.lifetime_field_aid),credits)
   expected=bytearray(quests);expected[216+11]|=1<<(family-39);self.assertEqual(bytes(s.quests),expected)
   before=bytes(s);self.assertEqual(l.return_job_begin(C.byref(s),C.byref(r),scene,3),0);self.assertEqual(bytes(s),before)
   runjob(l,s,r,3,scene,4)
   for old in (1,2,3,4):self.assertEqual(l.return_job_begin(C.byref(s),C.byref(r),scene,old),0)
   for field,value in (('source',token+256),('source',1 if token==17 else 2),('family',family+256),('room',room+256),('command',command+256),('form',form+256),('key',1)):
    bad=Request.from_buffer_copy(bytes(r));setattr(bad,field,value);self.assertEqual(l.return_job_begin(C.byref(s),C.byref(bad),generation(),1),0,(field,value))
   wrong=Request.from_buffer_copy(bytes(r));wrong.instance_id+=999;runjob(l,s,wrong,-1)
 def test_denial_replay_training_and_credits_never_authorize(self):
  l=self.lib;s,_=initial_chapter(l);slot,id=select(l,s,16,11)
  s.roster.expedition_events[473//8]|=1<<(473%8);s.roster.lifetime_field_aid[89//8]|=1<<(89%8)
  request=Request(operation=9,room=55,slot=slot,instance_id=id,family=6,key=1,form=16,command=11)
  other=next(i for i,c in enumerate(s.roster.instances) if c.form_id and i!=slot);before=bytes(s.roster.instances[other])
  runjob(l,s,request,3);self.assertEqual(bytes(s.roster.instances[other]),before)
  self.assertEqual((s.roster.instances[slot].level,s.roster.instances[slot].bond,s.roster.instances[slot].trial_flags),(28,45,1024))
  same=bytes(s);runjob(l,s,request,0);self.assertEqual(bytes(s),same)
 def test_stale_every_byte_cancels_before_single_commit(self):
  l=self.lib;base=source(l);r=Request(operation=5,quest=46,bit=1)
  for offset in range(C.sizeof(Save)):
   s=Save.from_buffer_copy(bytes(base));token=l.return_job_begin(C.byref(s),C.byref(r),generation(),1);self.assertTrue(token)
   l.return_job_phase(token) # phase query itself must be read-only
   # Obtain our generation from module rather than accessing private cursor.
   import return_host_support as helpers
   scene=helpers._generation
   while l.return_job_phase(token)!=6:
    self.assertEqual(l.return_job_step(token,1024,scene,1),BUSY)
   data=(C.c_ubyte*C.sizeof(Save)).from_buffer(s);data[offset]^=1;before=bytes(s)
   self.assertEqual(l.return_job_step(token,1024,scene,1),FAILED,offset);self.assertEqual(bytes(s),before,offset)
 def test_cancel_scene_attempt_request_copy_and_scratch_exclusion(self):
  l=self.lib;base=source(l);r=Request(operation=5,quest=46,bit=1)
  for mode in ('cancel','scene','attempt','load','selection'):
   for phase in (0,1,6):
    s=Save.from_buffer_copy(bytes(base));scene=generation();request=Request.from_buffer_copy(bytes(r));token=l.return_job_begin(C.byref(s),C.byref(request),scene,1);self.assertTrue(token)
    while l.return_job_phase(token)<phase:self.assertEqual(l.return_job_step(token,1024,scene,1),BUSY)
    self.assertEqual(l.save5_begin(C.byref(s)),0);self.assertEqual(l.save5_preflight_begin(C.byref(s)),0)
    before=bytes(s)
    if mode=='cancel':l.return_job_cancel()
    elif mode=='load':out=Save();self.assertEqual(l.save5_load(C.byref(out)),1)
    elif mode=='selection':s.roster.selected_party=(s.roster.selected_party+1)%4;before=bytes(s)
    status=BUSY
    while status==BUSY:status=l.return_job_step(token,1024,scene+(mode=='scene'),1+(mode=='attempt'))
    self.assertNotEqual(status,DONE,(mode,phase));self.assertEqual(bytes(s),before)
  s=Save.from_buffer_copy(bytes(base));scene=generation();token=l.return_job_begin(C.byref(s),C.byref(r),scene,1);r.quest=47
  while l.return_job_step(token,1024,scene,1)==BUSY:pass
  self.assertEqual(l.return_job_result(token),1);self.assertEqual(s.quests.objectives[46],1);self.assertEqual(s.quests.objectives[47],0)
 def test_preflight_blocking_streaming_and_malformed_parity(self):
  l=self.lib;base,_=initial_chapter(l);trials(l,base);rng=random.Random(0x52455437)
  for case in range(4000):
   s=Save.from_buffer_copy(bytes(base));data=(C.c_ubyte*C.sizeof(Save)).from_buffer(s)
   if case:
    for _ in range(1+case%3):data[rng.randrange(len(data))]=rng.randrange(256)
   expected=l.save5_validate(C.byref(s));before=bytes(s);token=l.save5_preflight_begin(C.byref(s));self.assertTrue(token)
   for step in range(500):
    status=l.save5_preflight_step(token,(1,64,1024,0xffffffff)[step%4])
    if status!=BUSY:break
   self.assertEqual(status,DONE if expected else FAILED,case);self.assertEqual(bytes(s),before);l.save5_preflight_cancel()
   l.save5_test_reset_writer();l.save5_test_fail_after(-1);l.sram[:]=bytes([255])*32768
   accepted=l.save5_store(C.byref(s));self.assertEqual(accepted,expected,case);self.assertEqual(bytes(s),before)
   if accepted:
    out=Save();self.assertEqual(l.save5_load(C.byref(out)),1)
    # C alignment bytes are not wire fields. The codec preserves typed bytes
    # and independently emits canonical zero wire padding.
    raw=(C.c_ubyte*C.sizeof(Roster)).from_buffer(s.roster)
    for i in range(Roster.selected_party.offset+1,Roster.next_instance_id.offset):raw[i]=0
    self.assertEqual(compare_state(out),compare_state(s))
 def test_current_room_visits_anchors_credits_and_source_gates(self):
  l=self.lib;s,_=initial_chapter(l)
  for room,count in ((54,3),(55,3),(56,2),(57,2),(58,2),(59,2),(60,2),(61,2)):
   for spawn in range(6):
    candidate=Save.from_buffer_copy(bytes(s));candidate.campaign.room=room;candidate.campaign.spawn=spawn
    self.assertEqual(l.save5_validate(C.byref(candidate)),int(spawn<count),(room,spawn))
  rows={54:(296,2),56:(298,2),57:(300,3),58:(303,2),61:(305,3)}
  for room in range(62):
   for slot in range(8):
    got=l.progression_encounter_event(room,slot)
    if room<=29:self.assertEqual(got,room*6+slot if slot<6 else 512)
    if room>=54:self.assertEqual(got,rows[room][0]+slot if room in rows and slot<rows[room][1] else 512)
 def test_repeat_provenance_is_exactly_two_real_members_crc_and_atomic(self):
  l=self.lib;s,_=initial_chapter(l);trials(l,s)
  for source,form,command,room,family in ((17,102,102,55,39),(18,104,104,58,40)):
   slot,id=select(l,s,form,command);request=Request(operation=7,source=source,room=room,slot=slot,instance_id=id,family=family,form=form,command=command)
   runjob(l,s,request,3);self.assertEqual(l.save5_store(C.byref(s)),1)
   bank_offset=max((A,B),key=lambda p:int.from_bytes(bytes(l.sram[p+8:p+12]),'little'))
   bank=bytearray(l.sram[bank_offset:bank_offset+SIZE]);bank[4248+11]&=~(1<<(family-39));bank=repair_crc(bank)
   image=bytearray([255])*32768;image[A:A+SIZE]=bank;l.sram[:]=image
   out=Save.from_buffer_copy(bytes([90])*C.sizeof(Save));before=bytes(out)
   self.assertEqual(l.save5_load(C.byref(out)),0);self.assertEqual(bytes(out),before)
   malformed=Save.from_buffer_copy(bytes(s));malformed.quests.region_flags[11]&=~(1<<(family-39));before=bytes(malformed)
   self.assertEqual(l.save5_validate(C.byref(malformed)),0)
   token=l.return_job_begin(C.byref(malformed),C.byref(request),generation(),1);self.assertTrue(token)
   import return_host_support as helpers
   while l.return_job_status(token)==BUSY:l.return_job_step(token,1024,helpers._generation,1)
   self.assertEqual(l.return_job_status(token),FAILED);self.assertEqual(bytes(malformed),before)
   self.assertEqual(l.save5_store(C.byref(malformed)),0);self.assertEqual(bytes(malformed),before)
 def test_new_gear_seen_requires_exact_source_crc_and_atomic(self):
  l=self.lib;legal,_=initial_chapter(l);self.assertEqual(l.save5_store(C.byref(legal)),1)
  offset=max((A,B),key=lambda p:int.from_bytes(bytes(l.sram[p+8:p+12]),'little'));seed=bytes(l.sram[offset:offset+SIZE])
  # Remove only the side quest52 claim and its source37 receipt. Its bow
  # history/record still exists, and no other quest depends on52.
  bank=bytearray(seed);bank[4032+52//4]&=~(3<<(2*(52%4)));bank[4032+52//4]|=2<<(2*(52%4))
  bank[4176+52//8]&=~(1<<(52%8));bank[5024+37//8]&=~(1<<(37%8));bank=repair_crc(bank)
  image=bytearray([255])*32768;image[A:A+SIZE]=bank;l.sram[:]=image;out=Save.from_buffer_copy(bytes([90])*C.sizeof(Save));before=bytes(out)
  self.assertEqual(l.save5_load(C.byref(out)),0);self.assertEqual(bytes(out),before)
  for receipt,item in enumerate((21,39,55,69,87),37):
   s=source(l)
   free=next(i for i,r in enumerate(s.equipment.bag) if not r.item_id)
   s.equipment.bag[free].item_id=item;s.equipment.bag[free].quantity=1;s.equipment.seen[item//8]|=1<<(item%8)
   self.assertEqual(l.save5_validate(C.byref(s)),0,(receipt,item));before=bytes(s)
   token=l.save5_preflight_begin(C.byref(s));self.assertTrue(token)
   while True:
    status=l.save5_preflight_step(token,1024)
    if status!=BUSY:break
   self.assertEqual(status,FAILED);l.save5_preflight_cancel();self.assertEqual(bytes(s),before)
   self.assertEqual(l.save5_store(C.byref(s)),0);self.assertEqual(bytes(s),before)
 def test_old_future_credit_bits_preserve_without_authorizing_or_blocking(self):
  l=self.lib;s=source(l)
  for event in (288,289,468):s.roster.expedition_events[event//8]|=1<<(event%8)
  s.roster.lifetime_field_aid[84//8]|=1<<(84%8)
  self.assertEqual(l.save5_validate_revision(C.byref(s),6),1)
  self.assertEqual(s.quests.objectives[46],0);self.assertFalse(any(c.form_id==101 for c in s.roster.instances))
  credits=bytes(s.roster.expedition_events)+bytes(s.roster.lifetime_field_aid)
  for bit in (1,2):runjob(l,s,Request(operation=5,quest=46,bit=bit))
  runjob(l,s,Request(operation=6,quest=46),3)
  for room in (54,55):runjob(l,s,Request(operation=1,room=room),1)
  for bit in (1,2,4):runjob(l,s,Request(operation=5,quest=47,bit=bit))
  runjob(l,s,Request(operation=6,quest=47,source=1),3)
  slot,id=select(l,s,2,5)
  runjob(l,s,Request(operation=9,room=54,slot=slot,instance_id=id,family=1,key=2,form=2,command=5),3)
  self.assertEqual(s.roster.instances[slot].trial_flags&1024,1024)
  self.assertEqual(bytes(s.roster.expedition_events)+bytes(s.roster.lifetime_field_aid),credits)
 def test_full_reserved_and_id_exhausted_no_consumption(self):
  l=self.lib;base,_=initial_chapter(l);slot,id=select(l,base,101,102)
  request=Request(operation=7,room=55,source=17,slot=slot,instance_id=id,family=39,form=101,command=102)
  for kind in ('full','reserved','id'):
   s=Save.from_buffer_copy(bytes(base))
   if kind=='id':s.roster.next_instance_id=0xffffffff
   else:
    count=160 if kind=='full' else 143
    while sum(bool(c.form_id) for c in s.roster.instances)<count:self.assertLess(l.creatures_grant(C.byref(s.roster),1,1,0,0,0),160)
   self.assertEqual(l.save5_validate(C.byref(s)),1)
   before=bytes(s);runjob(l,s,request,{'full':5,'reserved':6,'id':7}[kind]);self.assertEqual(bytes(s),before)
if __name__=='__main__':unittest.main(verbosity=2)
