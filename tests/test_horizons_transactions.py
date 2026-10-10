#!/usr/bin/env python3
"""Content8 source/quest/identity transaction adversaries; host-only evidence."""
import ctypes as C,random,tempfile,unittest
from horizons_host_support import *
class HorizonsTransactions(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='horizons-jobs-');cls.addClassCleanup(cls.tmp.cleanup);cls.lib=build(cls.tmp.name)
 def test_full120_64_real_60_quests_46_gear_cold_reload(self):
  l=self.lib;s=complete(l)
  self.assertEqual(sum(v.bit_count() for v in s.roster.obtained),120);self.assertEqual(sum(bool(c.form_id) for c in s.roster.instances),64)
  self.assertEqual(sum(l.save5_quest_state(C.byref(s.quests),i)==3 for i in range(64)),60);self.assertEqual(sum(bool(v.item_id) for v in s.equipment.bag),46)
  self.assertEqual(len({l.creatures_family_revision(c.form_id,8) for c in s.roster.instances if c.form_id}),52)
  self.assertEqual(l.save5_validate_revision(C.byref(s),7),0);before=compare_state(s);self.assertEqual(l.save5_store(C.byref(s)),1);out=Save();self.assertEqual(l.save5_load(C.byref(out)),1);self.assertEqual(compare_state(out),before)
 def test_main_both_orders_no_optional_or_evolution(self):
  a=main(self.lib);b=main(self.lib,True)
  for s in (a,b):
   self.assertEqual(sum(bool(c.form_id) for c in s.roster.instances),56);self.assertEqual(sum(v.bit_count() for v in s.roster.obtained),108)
   self.assertEqual(s.quests.region_flags[12],15);self.assertEqual(s.quests.region_flags[13],0)
   for c in s.roster.instances:
    if c.form_id>=105:self.assertEqual((c.level,c.bond,c.trial_flags),(32,30,0))
  self.assertEqual(bytes(a.quests),bytes(b.quests));self.assertEqual(sorted(v.item_id for v in a.equipment.bag),sorted(v.item_id for v in b.equipment.bag));self.assertEqual(bytes(a.equipment.reward_claims),bytes(b.equipment.reward_claims))
 def test_all_repeats_exact_owner_stale_attempt_and_storage(self):
  l=self.lib;s=complete(l)
  for i,base in enumerate(BASES):
   move(l,s,ROOMS[i]);form=base+1 if i<4 else base;slot,id=select(l,s,form,base+1);s.roster.party[:]=[slot,0,1,2];before=Save.from_buffer_copy(bytes(s));scene=generation();r=Request(operation=8,source=33+i,family=41+i,room=ROOMS[i],slot=slot,instance_id=id,form=form,command=base+1)
   runjob(l,s,r,3,scene=scene);new=[c for c in s.roster.instances if c.instance_id==before.roster.next_instance_id];self.assertEqual(len(new),1);self.assertEqual(new[0].form_id,base);self.assertEqual(new[0].trial_flags,0)
   self.assertEqual(bytes(s.quests.states),bytes(before.quests.states));self.assertEqual(bytes(s.equipment),bytes(before.equipment));self.assertEqual(bytes(s.roster.party),bytes(before.roster.party));self.assertEqual(s.roster.selected_party,before.roster.selected_party)
   self.assertEqual(l.horizons_job_begin(C.byref(s),C.byref(r),scene,1),0);self.assertEqual(s.quests.region_flags[14+(i>>3)]&(1<<(i&7)),1<<(i&7))
  self.assertEqual(sum(bool(c.form_id) for c in s.roster.instances),76)
 def test_invitation_bits_and_aliases_fail_before_preflight(self):
  l=self.lib;s=main(l)
  for q in range(54,58):
   r=Request(operation=5,quest=q,bit=4 if q==54 else 8,room=62 if q==54 else ROOMS[q-54]);before=bytes(s)
   self.assertEqual(l.horizons_job_begin(C.byref(s),C.byref(r),generation(),1),0);self.assertEqual(bytes(s),before)
  for source in (0,13,32,45,257,289,0xffffffff):
   r=Request(operation=7,source=source,family=41,room=62);self.assertEqual(l.horizons_job_begin(C.byref(s),C.byref(r),generation(),1),0)
  for fn in ('horizons_source_family','horizons_source_form','horizons_source_room'):
   for source in (0,13,32,45,257,289,0xffffffff):self.assertEqual(getattr(l,fn)(source),0)
 def test_cancel_every_phase_stale_every_byte_and_zero_budget(self):
  l=self.lib;base=main(l);move(l,base,64);r=Request(operation=7,source=6,family=46,room=64)
  for phase in (0,1,2,3,6):
   for mode in ('cancel','scene','attempt','byte'):
    s=Save.from_buffer_copy(bytes(base));scene=generation();token=l.horizons_job_begin(C.byref(s),C.byref(r),scene,1);self.assertTrue(token)
    while l.horizons_job_phase(token)!=phase:self.assertEqual(l.horizons_job_step(token,1024,scene,1),BUSY)
    before=bytes(s);self.assertEqual(l.horizons_job_step(token,0,scene,1),BUSY);self.assertEqual(l.horizons_job_phase(token),phase)
    self.assertEqual(l.save5_begin(C.byref(s)),0);self.assertEqual(l.save5_preflight_begin(C.byref(s)),0)
    if mode=='cancel':l.horizons_job_cancel()
    elif mode=='byte':s.roster.instances[0].cosmetic_seed^=1;before=bytes(s)
    status=BUSY
    while status==BUSY:status=l.horizons_job_step(token,1024,scene+(mode=='scene'),1+(mode=='attempt'))
    self.assertNotEqual(status,DONE,(phase,mode));self.assertEqual(bytes(s),before)
  for pos in range(C.sizeof(Save)):
   s=Save.from_buffer_copy(bytes(base));scene=generation();token=l.horizons_job_begin(C.byref(s),C.byref(r),scene,1)
   while l.horizons_job_phase(token)!=6:self.assertEqual(l.horizons_job_step(token,0xffffffff,scene,1),BUSY)
   raw=(C.c_ubyte*C.sizeof(s)).from_buffer(s);raw[pos]^=1;before=bytes(s)
   self.assertEqual(l.horizons_job_step(token,1024,scene,1),FAILED,pos);self.assertEqual(bytes(s),before,pos)
 def test_sources_history_quest_gear_and_preflight_stream_parity(self):
  l=self.lib;base=complete(l);rng=random.Random(8012)
  cases=[]
  for index in range(12):
   for region in (12,14):
    s=Save.from_buffer_copy(bytes(base));s.quests.region_flags[region+(index>>3)]^=1<<(index&7);cases.append(s)
  for form in range(105,121):
   s=source(l);s.roster.seen[(form-1)//8]|=1<<((form-1)%8);s.roster.obtained[(form-1)//8]|=1<<((form-1)%8);cases.append(s)
  for n in range(1000):
   s=Save.from_buffer_copy(bytes(base));raw=(C.c_ubyte*C.sizeof(s)).from_buffer(s)
   for _ in range(1+n%3):raw[rng.randrange(len(raw))]=rng.randrange(256)
   cases.append(s)
  cases.append(base)
  for n,s in enumerate(cases):
   expected=l.save5_validate(C.byref(s));before=bytes(s);token=l.save5_preflight_begin(C.byref(s));self.assertTrue(token)
   for k in range(2000):
    status=l.save5_preflight_step(token,(1,64,1024,0xffffffff)[k%4])
    if status!=BUSY:break
   self.assertEqual(status,DONE if expected else FAILED,n);self.assertEqual(bytes(s),before);l.save5_preflight_cancel()
   l.save5_test_reset_writer();l.save5_test_fail_after(-1);l.sram[:]=bytes([255])*32768
   self.assertEqual(l.save5_store(C.byref(s)),expected,n)
 def test_trial_owner_floors_and_other_copy_isolation(self):
  l=self.lib;s=main(l)
  for i in range(4):
   move(l,s,TRIAL_ROOMS[i]);slot,id=select(l,s,BASES[i]);r=Request(operation=10,room=TRIAL_ROOMS[i],slot=slot,instance_id=id,family=41+i,key=1,form=BASES[i],command=BASES[i]+1)
   for field in ('slot','instance_id','family','key','form','command'):
    bad=Request.from_buffer_copy(bytes(r));setattr(bad,field,getattr(bad,field)+256);before=bytes(s);token=l.horizons_job_begin(C.byref(s),C.byref(bad),generation(),1)
    if token:
     while l.horizons_job_step(token,1024,generation(),1)==BUSY:pass
    self.assertEqual(bytes(s),before)
   runjob(l,s,r,3);c=s.roster.instances[slot];self.assertEqual((c.level,c.bond,c.trial_flags),(34,60,1024));before=bytes(s);runjob(l,s,r,0);self.assertEqual(bytes(s),before)
   c.bond=59;self.assertEqual(l.save5_validate(C.byref(s)),0);c.bond=60
 def test_quest_state_masks_and_exact_spawn_anchor_mapping(self):
  from test_save5 import Quests
  l=self.lib
  for q in range(54,60):
   masks=(7,15,15,15,7,15);full=masks[q-54]
   partial={0,1,3} if q==54 else {0,1,3,7} if q<=57 else set(range(4)) if q==58 else set(range(8))
   for state in range(4):
    for bits in range(32):
     v=Quests();l.save5_quest_set_state(C.byref(v),q,state);v.objectives[q]=bits
     if state==3:v.rewards[q//8]|=1<<(q%8)
     expected=bits==0 if state==0 else bits in partial if state==1 else bits==full
     self.assertEqual(l.save5_quests_validate(C.byref(v)),expected,(q,state,bits))
  base=complete(l);base.quests.anchors[6]=3
  for room,count in zip(range(62,70),(5,4,2,4,3,4,1,2)):
   for spawn in range(256):
    s=Save.from_buffer_copy(bytes(base));s.campaign.room=room;s.campaign.spawn=spawn
    self.assertEqual(l.save5_validate(C.byref(s)),spawn<count,(room,spawn))
  for room,spawn,bit in ((62,4,1),(65,3,2)):
   s=Save.from_buffer_copy(bytes(base));s.campaign.room=room;s.campaign.spawn=spawn;s.quests.anchors[6]^=bit
   self.assertEqual(l.save5_validate(C.byref(s)),0,(room,spawn))
 def test_old_future_credit_bits_never_block_sources_or_personal_floor(self):
  l=self.lib;s=main(l)
  s.roster.expedition_events[38]|=0xf0;s.roster.expedition_events[39]=255;s.roster.expedition_events[40]|=63;s.roster.lifetime_field_aid[12]|=127
  credits=bytes(s.roster.expedition_events),bytes(s.roster.lifetime_field_aid)
  invite(l,s,5);move(l,s,64);slot,id=select(l,s,105)
  runjob(l,s,Request(operation=10,room=64,slot=slot,instance_id=id,family=41,key=1,form=105,command=106),3)
  self.assertEqual((s.roster.instances[slot].level,s.roster.instances[slot].bond),(34,60));self.assertEqual((bytes(s.roster.expedition_events),bytes(s.roster.lifetime_field_aid)),credits)
 def test_full_reserved_exhausted_and_malformed_receipt_no_mutation(self):
  l=self.lib;base=main(l);move(l,base,64);r=Request(operation=7,source=6,family=46,room=64)
  for count,code in ((160,5),):
   s=Save.from_buffer_copy(bytes(base));template=Instance.from_buffer_copy(bytes(s.roster.instances[0]));template.flags=1
   for i in range(56,count):
    s.roster.instances[i]=template;s.roster.instances[i].instance_id=s.roster.next_instance_id;s.roster.next_instance_id+=1
   before=bytes(s);runjob(l,s,r,code);self.assertEqual(bytes(s),before)
  # A first missing family improves even a grandfathered over-budget roster;
  # an extra copy must not consume the remaining protected opportunities.
  s=Save.from_buffer_copy(bytes(base));move(l,s,62);slot,id=select(l,s,105);repeat=Request(operation=8,source=33,family=41,room=62,slot=slot,instance_id=id,form=105,command=106)
  template=Instance.from_buffer_copy(bytes(s.roster.instances[0]));template.flags=1
  for i in range(56,144):
   s.roster.instances[i]=template;s.roster.instances[i].instance_id=s.roster.next_instance_id;s.roster.next_instance_id+=1
  before=bytes(s);runjob(l,s,repeat,6);self.assertEqual(bytes(s),before)
  s=Save.from_buffer_copy(bytes(base));s.roster.next_instance_id=0xffffffff;before=bytes(s);runjob(l,s,r,7);self.assertEqual(bytes(s),before)
  s=Save.from_buffer_copy(bytes(base));s.quests.region_flags[12]|=32;before=bytes(s);scene=generation();token=l.horizons_job_begin(C.byref(s),C.byref(r),scene,1);self.assertTrue(token)
  while l.horizons_job_step(token,1024,scene,1)==BUSY:pass
  self.assertEqual(l.horizons_job_status(token),FAILED);self.assertEqual(bytes(s),before)
if __name__=='__main__':unittest.main(verbosity=2)
