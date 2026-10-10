#!/usr/bin/env python3
"""Current9 typed transaction and scanner evidence, not native acceptance."""
import ctypes as C,random,tempfile,unittest
from covenants_host_support import *
class CovenantsTransactions(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='covenants-jobs-');cls.addClassCleanup(cls.tmp.cleanup);cls.lib=build(cls.tmp.name)
 def test_full128_72_all64_48_gear_and_cold_reload(self):
  l=self.lib;s=story(l,True)
  self.assertEqual(sum(v.bit_count() for v in s.roster.obtained),128);self.assertEqual(sum(bool(c.form_id) for c in s.roster.instances),72)
  self.assertEqual(len({l.creatures_family_revision(c.form_id,9) for c in s.roster.instances if c.form_id}),60)
  self.assertEqual(sum(l.save5_quest_state(C.byref(s.quests),i)==3 for i in range(64)),64)
  self.assertEqual(sum(bool(x.item_id) for x in s.equipment.bag),48)
  self.assertEqual((s.quests.region_flags[22],s.quests.region_flags[23]),(255,255))
  self.assertEqual(l.save5_validate_revision(C.byref(s),8),0)
  before=compare_state(s);self.assertEqual(l.save5_store(C.byref(s)),1);out=Save();self.assertEqual(l.save5_load(C.byref(out)),1);self.assertEqual(compare_state(out),before)
 def test_story_all_declined_then_late_unique_invites(self):
  l=self.lib;s=story(l,False);other=story(l,False,True)
  self.assertEqual(bytes(s.quests),bytes(other.quests));self.assertEqual(bytes(s.equipment),bytes(other.equipment))
  self.assertEqual((s.quests.region_flags[22],s.quests.region_flags[23]),(255,0))
  self.assertEqual(sum(v.bit_count() for v in s.roster.obtained),120)
  self.assertEqual(sum(bool(c.form_id) for c in s.roster.instances),64)
  history=bytes(s.quests.states),bytes(s.quests.objectives),bytes(s.equipment)
  for i in range(1,9):
   invite(l,s,i);before=bytes(s);runjob(l,s,Request(operation=7,room=69+i,source=i),0);self.assertEqual(bytes(s),before)
  self.assertEqual((bytes(s.quests.states),bytes(s.quests.objectives),bytes(s.equipment)),history)
  self.assertEqual(sum(bool(c.form_id) for c in s.roster.instances),72)
 def test_seen_only_legal_and_lifetime_bits_never_authorize_sources(self):
  l=self.lib;s=enter(l);s.roster.seen[15]=255;s.roster.expedition_events[:]=bytes([255])*64;s.roster.lifetime_field_aid[:]=bytes([255])*16
  self.assertEqual(l.save5_validate(C.byref(s)),1)
  before=bytes(s);runjob(l,s,Request(operation=7,room=70,source=1),4);self.assertEqual(bytes(s),before)
  credits=bytes(s.roster.expedition_events),bytes(s.roster.lifetime_field_aid)
  fulfill(l,s,1);invite(l,s,1);self.assertEqual((bytes(s.roster.expedition_events),bytes(s.roster.lifetime_field_aid)),credits)
 def test_second_legend_goes_storage_with_vacant_party_slots(self):
  l=self.lib;s=story(l,False);s.roster.party[:]=[0,255,255,255];s.roster.selected_party=0
  invite(l,s,1);first=next(i for i,c in enumerate(s.roster.instances) if c.form_id==121)
  self.assertEqual(list(s.roster.party),[0,first,255,255]);before=bytes(s.roster.party)
  for i in range(2,9):invite(l,s,i);self.assertEqual(bytes(s.roster.party),before)
  for c in s.roster.instances:
   if c.form_id>=121:self.assertEqual((c.level,c.bond,c.trial_flags,c.flags),(36,60,0,1))
  second=next(i for i,c in enumerate(s.roster.instances) if c.form_id==122);s.roster.party[2]=second
  self.assertEqual(l.save5_validate(C.byref(s)),0);l.save5_test_reset_writer();self.assertEqual(l.save5_store(C.byref(s)),0)
 def test_full_width_unused_fields_namespaces_and_generic_objectives(self):
  l=self.lib;s=enter(l)
  for r in [Request(operation=4,quest=q,bit=b,room=70+(q-61)*4) for q in (61,62) for b in (1,2,4,8,15)]:
   self.assertEqual(l.covenants_job_begin(C.byref(s),C.byref(r),generation(),1),0)
  good=Request(operation=6,room=70,source=1)
  for field in ('operation','room','source','quest','bit'):
   for value in (256,257,65536,0xffffffff):
    bad=Request.from_buffer_copy(bytes(good));setattr(bad,field,getattr(bad,field)+value if getattr(bad,field)+value<=0xffffffff else value)
    before=bytes(s);self.assertEqual(l.covenants_job_begin(C.byref(s),C.byref(bad),generation(),1),0,(field,value));self.assertEqual(bytes(s),before)
  for value in (0,9,33,257,0xffffffff):
   for name in ('covenants_source_form','covenants_source_family','covenants_source_room'):self.assertEqual(getattr(l,name)(value),0)
  runjob(l,s,Request(operation=7,room=70,source=1),4)
  before=bytes(s);runjob(l,s,Request(operation=6,room=71,source=2),-1);self.assertEqual(bytes(s),before)
 def test_cancel_every_phase_every_live_byte_and_scratch_lease(self):
  l=self.lib;base=enter(l);fulfill(l,base,1);r=Request(operation=7,room=70,source=1)
  for phase in (0,1,2,3,5):
   for mode in ('cancel','scene','attempt','byte'):
    s=Save.from_buffer_copy(bytes(base));scene=generation();token=l.covenants_job_begin(C.byref(s),C.byref(r),scene,1);self.assertTrue(token)
    while l.covenants_job_phase(token)!=phase:self.assertEqual(l.covenants_job_step(token,1024,scene,1),BUSY)
    before=bytes(s);self.assertEqual(l.covenants_job_step(token,0,scene,1),BUSY);self.assertEqual(l.covenants_job_phase(token),phase)
    self.assertEqual(l.save5_begin(C.byref(s)),0);self.assertEqual(l.save5_preflight_begin(C.byref(s)),0)
    if mode=='cancel':l.covenants_job_cancel()
    elif mode=='byte':s.roster.instances[0].cosmetic_seed^=1;before=bytes(s)
    status=BUSY
    while status==BUSY:status=l.covenants_job_step(token,1024,scene+(mode=='scene'),1+(mode=='attempt'))
    self.assertNotEqual(status,DONE);self.assertEqual(bytes(s),before)
  for pos in range(C.sizeof(Save)):
   s=Save.from_buffer_copy(bytes(base));scene=generation();token=l.covenants_job_begin(C.byref(s),C.byref(r),scene,1)
   while l.covenants_job_phase(token)!=5:self.assertEqual(l.covenants_job_step(token,0xffffffff,scene,1),BUSY)
   raw=(C.c_ubyte*C.sizeof(s)).from_buffer(s);raw[pos]^=1;before=bytes(s)
   self.assertEqual(l.covenants_job_step(token,1024,scene,1),FAILED,pos);self.assertEqual(bytes(s),before,pos)
  s=Save.from_buffer_copy(bytes(base));scene=generation();token=l.covenants_job_begin(C.byref(s),C.byref(r),scene,1)
  l.save5_preflight_cancel();new=l.save5_preflight_begin(C.byref(s));self.assertTrue(new);l.covenants_job_cancel();self.assertEqual(l.save5_preflight_status(new),BUSY);l.save5_preflight_cancel()
 def test_full_and_exhausted_preserve_right_grandfathered_missing_family_allowed(self):
  l=self.lib;base=enter(l);fulfill(l,base,1);r=Request(operation=7,room=70,source=1)
  for count,code in ((160,5),(159,3)):
   s=Save.from_buffer_copy(bytes(base));template=Instance.from_buffer_copy(bytes(s.roster.instances[0]));template.flags=1
   for i in range(64,count):s.roster.instances[i]=template;s.roster.instances[i].instance_id=s.roster.next_instance_id;s.roster.next_instance_id+=1
   before=bytes(s);runjob(l,s,r,code)
   if code==5:self.assertEqual(bytes(s),before)
   else:self.assertEqual(sum(bool(c.form_id) for c in s.roster.instances),160)
   self.assertTrue(s.quests.region_flags[22]&1)
  s=Save.from_buffer_copy(bytes(base));s.roster.next_instance_id=0xffffffff;before=bytes(s);runjob(l,s,r,7);self.assertEqual(bytes(s),before)
 def test_malformed_sources_and_preflight_writer_validation_parity(self):
  l=self.lib;base=story(l,True);rng=random.Random(9128);cases=[]
  for i in range(8):
   for field in (7,22,23):
    s=Save.from_buffer_copy(bytes(base));s.quests.region_flags[field]^=1<<i;cases.append(s)
   s=story(l,False);s.roster.obtained[15]|=1<<i;s.roster.seen[15]|=1<<i;cases.append(s)
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
   l.save5_test_reset_writer();l.save5_test_fail_after(-1);l.sram[:]=bytes([255])*32768;self.assertEqual(l.save5_store(C.byref(s)),expected,n)
 def test_exact_checkpoint_spawns_inbound_and_anchors(self):
  l=self.lib;base=story(l,False);base.quests.anchors[7]=3
  for room,count in zip(range(70,78),(5,2,2,2,4,2,2,2)):
   for spawn in range(256):
    s=Save.from_buffer_copy(bytes(base));s.campaign.room=room;s.campaign.spawn=spawn;self.assertEqual(l.save5_validate(C.byref(s)),spawn<count,(room,spawn))
  for room,spawn,bit in ((70,4,1),(74,3,2)):
   s=Save.from_buffer_copy(bytes(base));s.campaign.room=room;s.campaign.spawn=spawn;s.quests.anchors[7]^=bit;self.assertEqual(l.save5_validate(C.byref(s)),0)
  base.campaign.room=62;base.campaign.spawn=5;self.assertEqual(l.save5_validate(C.byref(base)),1);self.assertEqual(l.save5_validate_revision(C.byref(base),8),0)
 def test_quest_masks_prefixes_and_reserved_fields(self):
  from test_save5 import Quests
  l=self.lib
  for q,full in ((60,7),(61,15),(62,15),(63,7)):
   for state in range(4):
    for bits in range(32):
     v=Quests();l.save5_quest_set_state(C.byref(v),q,state);v.objectives[q]=bits
     if state==3:v.rewards[q//8]|=1<<(q%8)
     expected=bits==0 if state==0 else bits in ({0,1,3} if q in (60,63) else set(range(15))) if state==1 else bits==full
     self.assertEqual(l.save5_quests_validate(C.byref(v)),expected,(q,state,bits))
  s=story(l,False)
  for field,indices in (('region_flags',range(24,32)),('anchors',range(8,16)),('variables',range(60,64))):
   for index in indices:
    t=Save.from_buffer_copy(bytes(s));getattr(t.quests,field)[index]=1;self.assertEqual(l.save5_validate(C.byref(t)),0,(field,index))
if __name__=='__main__':unittest.main(verbosity=2)
