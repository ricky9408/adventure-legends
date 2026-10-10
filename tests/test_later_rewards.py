#!/usr/bin/env python3
"""Real core transactions on authenticated G7 saves; positions, READY rewinds,
wallet extremes/full roster and faults are explicitly synthetic host probes.
No emulator acquisition or real hardware performance claim is made here.
"""
import ctypes as C,hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from test_save5 import Save,Economy,Instance,ROOT,A,B,SIZE,compare_state
BUSY,DONE,FAILED=1,2,3
FULL='--full-cuts' in sys.argv
if FULL:sys.argv.remove('--full-cuts')
QUEST=(21,24,32,40);GOLD=(80,100,120,160)
SOURCES=((0,1),(2,3),(4,),(5,))
FIXTURE=('north-machine-1-cleared','south-boss-1-cleared','magma-regulator-cleared','underwater-08-guardian-settled')
CLAIMED=('north-north-main-before-continue','south-south-main-before-continue','magma-magma-main-before-continue','underwater-underwater-main-before-continue')
class Context(C.Structure):
 _fields_=[('scene',C.c_uint),('room',C.c_int),('x',C.c_int),('y',C.c_int),('facing',C.c_int),('source_state',C.c_uint)]
def context(source):
 return Context(17,*( [(29,120,122,1,5),(22,312,206,1,0),(37,120,126,1,5),(30,400,206,1,0),(38,160,190,1,0),(46,120,86,1,0),(0,56,114,1,0)][source]))
class LaterRewardTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='later-rewards-');cls.addClassCleanup(cls.tmp.cleanup);out=Path(cls.tmp.name)/'core.so'
  flags=['-fsanitize=undefined','-fno-sanitize-recover=all']if os.environ.get('LATER_SANITIZE')else[]
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-shared','-fPIC',*flags,*[str(ROOT/'src'/n)for n in ('save4.c','save5.c','creatures.c','creature_data.c','equipment.c','equipment_data.c','economy.c')],'-o',str(out)],check=True)
  cls.l=C.CDLL(str(out));cls.ram=(C.c_ubyte*32768).in_dll(cls.l,'save5_test_sram')
  for n in ('save5_validate','save5_begin','save5_store','save5_load','save5_preflight_begin','later_rewards_claimable'):getattr(cls.l,n).argtypes=[C.POINTER(Save)]
  cls.l.later_rewards_begin.argtypes=[C.POINTER(Save),C.c_uint,C.c_uint,C.POINTER(Context)]
  cls.l.later_rewards_check.argtypes=cls.l.later_rewards_begin.argtypes
  cls.l.save5_preflight_store_economy.argtypes=[C.c_uint,C.POINTER(Save),C.POINTER(Economy)]
  cls.l.later_rewards_step.argtypes=[C.POINTER(Context)]
  cls.l.save5_test_fail_after.argtypes=[C.c_int]
  cls.provenance=json.loads((ROOT/'tests/fixtures/v5-revision10-later/provenance.json').read_text())
 def setUp(self):
  self.l.save5_test_reset_writer()
  if self.l.later_rewards_pending():self.l.later_rewards_step(None);self.l.later_rewards_cancel()
  self.l.save5_preflight_cancel();self.l.save5_test_fail_after(-1);self.l.save5_test_corrupt_write(-1,0);self.ram[:]=bytes([255])*32768
 def fixture(self,name):
  row=next(r for r in self.provenance['fixtures']if r['path'].endswith(name+'.sav'));b=(ROOT/row['path']).read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),row['sha256']);return b
 def load(self):
  s=Save();self.assertEqual(self.l.save5_load(C.byref(s)),1);return s
 def state(self,t,fresh=True,source=None,gold=0):
  self.l.save5_test_reset_writer();self.ram[:]=self.fixture(FIXTURE[t]if fresh else CLAIMED[t]);s=self.load()
  if fresh:
   q=QUEST[t];s.quests.states[q>>2]=(s.quests.states[q>>2]&~(3<<((q&3)*2)))|(2<<((q&3)*2));s.quests.rewards[q>>3]&=~(1<<(q&7))
  s.economy=Economy();s.economy.gold=gold;s.economy.earned=gold
  source=SOURCES[t][0]if source is None else source;c=context(source);s.campaign.room=c.room;s.campaign.spawn=0
  self.assertEqual(self.l.save5_validate(C.byref(s)),1,(t,fresh,source));return s,c
 def finish(self,s,c):
  before=bytes(s)
  for steps in range(400):
   status=self.l.later_rewards_step(C.byref(c)if c else None)
   if status!=BUSY:return status,steps+1
   self.assertEqual(bytes(s),before)
  self.fail('unbounded transaction')
 def job(self,s,t,source,c):
  self.assertEqual(self.l.later_rewards_begin(C.byref(s),t,source,C.byref(c)),1,(t,source,self.l.later_rewards_last_error()))
  self.assertEqual(self.finish(s,c)[0],DONE,(t,source,self.l.later_rewards_last_error()));self.assertEqual(self.l.save5_validate(C.byref(s)),1)
 def test_each_source_fresh_recovery_repeat_actual_clipped_cash(self):
  for t in range(4):
   for fresh in (True,False):
    for source in SOURCES[t]+(()if fresh else(6,)):
     for gold in (0,9990,9999):
      s,c=self.state(t,fresh,source,gold);old=Save.from_buffer_copy(bytes(s));self.job(s,t,source,c)
      self.assertEqual(s.economy.later_claims,1<<t);self.assertEqual(s.economy.gold,min(gold+GOLD[t],9999));self.assertEqual(self.l.later_rewards_last_gold(),min(GOLD[t],9999-gold));self.assertEqual(self.l.later_rewards_last_fresh(),fresh)
      self.assertEqual(bytes(s.equipment),bytes(old.equipment));self.assertEqual(bytes(s.campaign),bytes(old.campaign))
      if not fresh or t<2:self.assertEqual(bytes(s.roster),bytes(old.roster));self.assertEqual(self.l.later_rewards_last_xp(),0)
      else:
       expected=type(s.roster).from_buffer_copy(bytes(old.roster));event=242 if t==2 else 282
       self.assertGreaterEqual(self.l.creatures_credit_event(C.byref(expected),event,160,2),0)
       self.assertEqual(bytes(s.roster),bytes(expected))
       self.assertEqual(self.l.later_rewards_last_xp(),sum(s.roster.instances[k].xp-old.roster.instances[k].xp for k in s.roster.party if k<160))
      self.assertEqual(compare_state(self.load()),compare_state(s));before=bytes(s);ram=bytes(self.ram)
      self.assertEqual(self.l.later_rewards_begin(C.byref(s),t,source,C.byref(c)),0);self.assertEqual(self.l.later_rewards_last_error(),4);self.assertEqual(bytes(s),before);self.assertEqual(bytes(self.ram),ram)
 def test_no_implicit_load_claim_and_village_cannot_finish_ready_quest(self):
  for t in range(4):
   b=self.fixture(CLAIMED[t]);self.ram[:]=b;s=self.load();self.assertEqual(bytes(self.ram),b);self.assertEqual(s.economy.later_claims,0);self.assertTrue(self.l.later_rewards_claimable(C.byref(s))&(1<<t))
   s,c=self.state(t,True,6);before=bytes(s);self.assertEqual(self.l.later_rewards_begin(C.byref(s),t,6,C.byref(c)),0);self.assertEqual(self.l.later_rewards_last_error(),3);self.assertEqual(bytes(s),before)
 def test_exp_event_bond_cap_and_xp_cap_preserved(self):
  for t in (2,3):
   for credited in (False,True):
    s,c=self.state(t);event=242 if t==2 else 282
    for slot in s.roster.party:
     if slot<160:
      s.roster.instances[slot].bond=99;s.roster.expedition_bond[slot]=9
      self.l.creatures_add_xp(C.byref(s.roster.instances[slot]),0xffffffff)
    if credited:s.roster.expedition_events[event>>3]|=1<<(event&7)
    old=Save.from_buffer_copy(bytes(s));self.job(s,t,SOURCES[t][0],c);self.assertEqual(self.l.later_rewards_last_xp(),0)
    for slot in s.roster.party:
     if slot<160:self.assertEqual(s.roster.instances[slot].bond,99 if credited else 100);self.assertEqual(s.roster.expedition_bond[slot],9 if credited else 10)
    self.assertEqual(bytes(s.roster.lifetime_field_aid),bytes(old.roster.lifetime_field_aid))
 def test_full48_gear160_roster_recovery_has_no_loss(self):
  rows=json.loads((ROOT/'tests/fixtures/v5-revision9/provenance.json').read_text())['fixtures'];row=rows[0];b=(ROOT/row['path']).read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),row['sha256']);self.ram[:]=b;s=self.load()
  template=Instance.from_buffer_copy(bytes(s.roster.instances[0]));template.flags=1
  for i in range(160):
   if not s.roster.instances[i].form_id:s.roster.instances[i]=template;s.roster.instances[i].instance_id=s.roster.next_instance_id;s.roster.next_instance_id+=1
  self.assertEqual(sum(bool(r.item_id)for r in s.equipment.bag),48);self.assertEqual(self.l.save5_validate(C.byref(s)),1)
  s.campaign.room=0;s.campaign.spawn=0;c=context(6);roster,gear,quests=bytes(s.roster),bytes(s.equipment),bytes(s.quests)
  for t in range(4):self.job(s,t,6,c);self.assertEqual((bytes(s.roster),bytes(s.equipment),bytes(s.quests)),(roster,gear,quests))
  self.assertEqual(s.economy.gold,sum(GOLD));self.assertEqual(s.economy.later_claims,15);self.assertEqual(compare_state(self.load()),compare_state(s))
 def test_stale_context_state_and_invalid_sources_fail_before_write(self):
  for t in range(4):
   for field in ('scene','room','x','y','facing','source_state'):
    s,c=self.state(t);self.assertEqual(self.l.save5_store(C.byref(s)),1);ram=bytes(self.ram);before=bytes(s)
    self.assertEqual(self.l.later_rewards_begin(C.byref(s),t,SOURCES[t][0],C.byref(c)),1);setattr(c,field,getattr(c,field)+1)
    self.assertEqual(self.finish(s,c)[0],FAILED);self.assertEqual(self.l.later_rewards_last_error(),6);self.assertEqual(bytes(s),before);self.assertEqual(bytes(self.ram),ram)
   for change in ('cosmetic','wallet','room','quest','gear','identity','party'):
    s,c=self.state(t);self.assertEqual(self.l.save5_store(C.byref(s)),1);ram=bytes(self.ram)
    self.assertEqual(self.l.later_rewards_begin(C.byref(s),t,SOURCES[t][0],C.byref(c)),1)
    if change=='cosmetic':s.roster.instances[0].cosmetic_seed+=1
    if change=='wallet':s.economy.gold+=1;s.economy.earned+=1
    if change=='room':s.campaign.room=0
    if change=='quest':s.quests.objectives[QUEST[t]]^=1
    if change=='gear':s.equipment.equipped[4]=255 if s.equipment.equipped[4]!=255 else 0
    if change=='identity':s.roster.instances[0].instance_id+=1
    if change=='party':s.roster.selected_party=(s.roster.selected_party+1)%4
    before=bytes(s);self.assertEqual(self.finish(s,c)[0],FAILED);self.assertEqual(bytes(s),before);self.assertEqual(bytes(self.ram),ram)
   for treasure,source in ((4,SOURCES[t][0]),(0xffffffff,SOURCES[t][0]),(t,7),(t,0xffffffff),((t+1)%4,SOURCES[t][0])):
    s,c=self.state(t);ram=bytes(self.ram);before=bytes(s);self.assertEqual(self.l.later_rewards_begin(C.byref(s),treasure,source,C.byref(c)),0);self.assertEqual(bytes(s),before);self.assertEqual(bytes(self.ram),ram)
 def test_cancel_before_admission_repeat_requests_and_revoked_ownership(self):
  for phase in (1,2):
   s,c=self.state(2);before=bytes(s);ram=bytes(self.ram);self.assertEqual(self.l.later_rewards_begin(C.byref(s),2,4,C.byref(c)),1)
   while self.l.later_rewards_phase()!=phase:self.assertEqual(self.l.later_rewards_step(C.byref(c)),BUSY)
   self.assertEqual(self.l.later_rewards_cancel(),1);self.assertEqual(bytes(s),before);self.assertEqual(bytes(self.ram),ram)
   self.job(s,2,4,c)
  s,c=self.state(2);self.assertEqual(self.l.later_rewards_begin(C.byref(s),2,4,C.byref(c)),1)
  while self.l.later_rewards_phase()!=3:
   self.assertEqual(self.l.later_rewards_begin(C.byref(s),3,5,C.byref(context(5))),0)
   self.assertEqual(self.l.later_rewards_step(C.byref(c)),BUSY)
  self.assertEqual(self.l.later_rewards_cancel(),0);self.l.save5_set_preemptible(1);self.assertEqual(self.l.save5_cancel_background(),0);self.assertEqual(self.l.save5_preflight_begin(C.byref(s)),0)
  c.scene+=1;self.assertEqual(self.finish(s,c)[0],DONE);self.assertEqual(s.economy.later_claims,4)
  s,c=self.state(2);self.assertEqual(self.l.later_rewards_begin(C.byref(s),2,4,C.byref(c)),1);other=self.load();token=self.l.save5_preflight_begin(C.byref(other));self.assertTrue(token)
  self.assertEqual(self.finish(s,c)[0],FAILED);self.assertEqual(self.l.save5_preflight_status(token),BUSY);self.l.save5_preflight_cancel()
 def test_first_revision10_recovery_powercuts_and_both_destinations(self):
  for t,source in enumerate((1,3,4,5)):
   self.l.save5_test_reset_writer();genuine=self.fixture(CLAIMED[t]);self.ram[:]=genuine;old=self.load();c=context(source)
   self.assertEqual(old.campaign.room,c.room)
   for swap in (False,True):
    initial=bytearray(genuine)
    if swap:initial[A:A+SIZE],initial[B:B+SIZE]=genuine[B:B+SIZE],genuine[A:A+SIZE]
    self.l.save5_test_reset_writer();self.l.save5_test_fail_after(-1);self.ram[:]=initial;original=self.load();expected=Save.from_buffer_copy(bytes(original));self.job(expected,t,source,c)
    for cut in (0,1,32,4032,4296,4456,4544,*range(5055,5089),6144,6145):
     self.l.save5_test_reset_writer();self.l.save5_test_fail_after(cut);self.ram[:]=initial;live=Save.from_buffer_copy(bytes(original))
     self.assertEqual(self.l.later_rewards_begin(C.byref(live),t,source,C.byref(c)),1);status,_=self.finish(live,c)
     self.assertEqual(status,DONE if cut>=6145 else FAILED);wanted=expected if status==DONE else original
     self.assertEqual(compare_state(live),compare_state(wanted));self.assertEqual(compare_state(self.load()),compare_state(wanted))
     self.assertEqual(bytes(live.roster),bytes(original.roster));self.assertEqual(bytes(live.quests),bytes(original.quests));self.assertEqual(bytes(live.equipment),bytes(original.equipment))
    self.l.save5_test_fail_after(-1)
 def test_readonly_routing_and_generic_economy_cannot_forge_receipt(self):
  for t in range(4):
   s,c=self.state(t,False);before=bytes(s);ram=bytes(self.ram)
   self.assertEqual(self.l.later_rewards_check(C.byref(s),t,SOURCES[t][0],C.byref(c)),0)
   self.assertEqual(bytes(s),before);self.assertEqual(bytes(self.ram),ram);self.assertEqual(self.l.save5_preflight_active(),0)
   token=self.l.save5_preflight_begin(C.byref(s));self.assertTrue(token)
   while self.l.save5_preflight_step(token,480)==BUSY:pass
   e=Economy.from_buffer_copy(bytes(s.economy));e.later_claims=1<<t;e.earned=e.gold=GOLD[t]
   self.assertEqual(self.l.save5_preflight_store_economy(token,C.byref(s),C.byref(e)),0)
   self.assertEqual(bytes(s),before);self.assertEqual(bytes(self.ram),ram);self.l.save5_preflight_cancel()
 def test_power_loss_at_every_update_boundary_including_after_commit(self):
  for t in range(4):
   for fresh in (True,False):
    for destination in (A,B):
     original,c=self.state(t,fresh);source=SOURCES[t][0];self.ram[:]=bytes([255])*32768
     self.assertEqual(self.l.save5_store(C.byref(original)),1)
     if destination==A:self.assertEqual(self.l.save5_store(C.byref(original)),1)
     initial=bytes(self.ram);expected=Save.from_buffer_copy(bytes(original));self.job(expected,t,source,c);counts=[0,0]
     for boundary in range(400):
      self.l.save5_test_reset_writer();self.l.save5_test_fail_after(-1);self.ram[:]=initial;live=Save.from_buffer_copy(bytes(original))
      self.assertEqual(self.l.later_rewards_begin(C.byref(live),t,source,C.byref(c)),1);status=BUSY
      for _ in range(boundary):
       status=self.l.later_rewards_step(C.byref(c))
       if status!=BUSY:break
      if status==DONE:break
      self.assertEqual(bytes(live),bytes(original));self.l.save5_test_reset_writer()
      # Simulate loss of the transient job after a CPU reset; this release is
      # no write and never publishes an incomplete transaction into live RAM.
      self.l.later_rewards_step(None);self.l.later_rewards_cancel()
      loaded=self.load();state=compare_state(loaded);self.assertIn(state,(compare_state(original),compare_state(expected)))
      counts[int(state==compare_state(expected))]+=1
      prior=A if destination==B else B;self.assertEqual(bytes(self.ram[prior:prior+SIZE]),initial[prior:prior+SIZE])
     else:self.fail('transaction never completed')
     self.assertTrue(all(counts),(t,fresh,destination,counts))
 def test_faults_both_banks_fresh_recovery_no_duplicate_grants(self):
  for t in range(4):
   for fresh in (True,False):
    for destination in (A,B):
     original,c=self.state(t,fresh);source=SOURCES[t][0]
     self.assertEqual(self.l.save5_store(C.byref(original)),1)
     # Erase authenticated input banks; establish the exact original twice/once.
     self.ram[:]=bytes([255])*32768;self.assertEqual(self.l.save5_store(C.byref(original)),1)
     if destination==A:self.assertEqual(self.l.save5_store(C.byref(original)),1)
     initial=bytes(self.ram);preserved=B if destination==A else A;expected=Save.from_buffer_copy(bytes(original));self.job(expected,t,source,c)
     cuts=range(SIZE+2)if FULL else(0,1,2,31,32,160,4000,4032,4296,4456,4544,4928,5024,*range(5055,5090),6143,6144,6145)
     for cut in cuts:
      self.l.save5_test_reset_writer();self.l.save5_test_fail_after(cut);self.ram[:]=initial;live=Save.from_buffer_copy(bytes(original));self.assertEqual(self.l.later_rewards_begin(C.byref(live),t,source,C.byref(c)),1)
      status,_=self.finish(live,c);self.assertEqual(status,DONE if cut>=6145 else FAILED,(t,fresh,destination,cut));out=self.load();want=expected if status==DONE else original
      self.assertEqual(compare_state(live),compare_state(want));self.assertEqual(compare_state(out),compare_state(want));self.assertEqual(bytes(self.ram[:A]),initial[:A]);self.assertEqual(bytes(self.ram[preserved:preserved+SIZE]),initial[preserved:preserved+SIZE])
      if status==FAILED:
       self.assertEqual(self.l.later_rewards_last_gold(),0);self.assertEqual(self.l.later_rewards_last_xp(),0)
     for corrupt in (0,1,32,160,4032,4296,4456,4544,5079,5080,5087,6144):
      self.l.save5_test_reset_writer();self.l.save5_test_fail_after(-1);self.l.save5_test_corrupt_write(corrupt,1);self.ram[:]=initial;live=Save.from_buffer_copy(bytes(original));self.assertEqual(self.l.later_rewards_begin(C.byref(live),t,source,C.byref(c)),1)
      self.assertEqual(self.finish(live,c)[0],FAILED);self.l.save5_test_corrupt_write(-1,0);self.assertEqual(compare_state(self.load()),compare_state(original));self.assertEqual(compare_state(live),compare_state(original))
      self.job(live,t,source,c);self.assertEqual(compare_state(live),compare_state(expected));self.assertEqual(compare_state(self.load()),compare_state(expected))
     self.l.save5_test_fail_after(-1)
if __name__=='__main__':unittest.main(verbosity=2)
