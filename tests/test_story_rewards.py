#!/usr/bin/env python3
"""Differential original story rewards versus bounded atomic commits; no native claim."""
from pathlib import Path
import ctypes as C,hashlib,json,subprocess,tempfile,unittest
import covenants_host_support as h
ROOT=Path(__file__).resolve().parents[1]
class Story(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='story-rewards-host-');cls.addClassCleanup(cls.tmp.cleanup);out=Path(cls.tmp.name)/'story.so'
  src=[ROOT/'src'/f'{n}.c'for n in [*h.SOURCES,'story_rewards']]
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST','-shared','-fPIC',*map(str,src),'-o',str(out)],check=True)
  cls.l=C.CDLL(str(out));l=cls.l
  l.creatures_grant.argtypes=[C.POINTER(h.Roster)]+[C.c_uint]*5
  l.creatures_story_job_begin.argtypes=[C.POINTER(h.Roster),C.c_uint]
  l.creatures_story_job_commit.argtypes=[C.c_uint,C.POINTER(h.Roster)]
  l.creatures_admission_job_begin.argtypes=[C.POINTER(h.Roster),C.c_uint,C.c_uint]
  l.story_rewards_begin.argtypes=[C.POINTER(h.Save),C.c_uint]
  l.save5_validate.argtypes=[C.POINTER(h.Save)];l.save5_load.argtypes=[C.POINTER(h.Save)]
  l.sram=(C.c_ubyte*32768).in_dll(l,'save5_test_sram');cls.cases=0
 def tearDown(self):self.l.story_rewards_cancel();self.l.creatures_admission_job_cancel();self.l.save5_preflight_cancel()
 def sync(self,r,chapter):
  for i in range(4):self.l.creatures_grant_story(C.byref(r),i,chapter)
  self.l.creatures_apply_story_floors(C.byref(r),chapter)
 def bounded(self,r,chapter):
  before=bytes(r);snap=h.Roster.from_buffer_copy(before);token=self.l.creatures_story_job_begin(C.byref(snap),chapter);self.assertTrue(token)
  for step in range(100):
   status=self.l.creatures_admission_job_step(token,4);self.assertEqual(bytes(r),before);self.assertEqual(bytes(snap),before)
   if status:break
  self.assertEqual(status,1);self.assertEqual(self.l.creatures_admission_job_result(token,None),0)
  self.assertEqual(self.l.creatures_story_job_commit(token,C.byref(r)),1);after=bytes(r)
  self.assertEqual(self.l.creatures_story_job_commit(token,C.byref(r)),0);self.assertEqual(bytes(r),after)
  self.assertEqual(self.l.creatures_roster_validate(C.byref(r)),1)
 def compare(self,base,chapter):
  r=h.Roster.from_buffer_copy(bytes(base));expected=h.Roster.from_buffer_copy(bytes(base));self.sync(expected,chapter);self.bounded(r,chapter);self.assertEqual(bytes(r),bytes(expected),(sum(bool(c.form_id)for c in base.instances),chapter));type(self).cases+=1
  self.bounded(r,chapter);self.assertEqual(bytes(r),bytes(expected),'retry changed an already fulfilled reward')
 def test_every_legal_cardinality_and_admission_boundary(self):
  r=h.Roster();self.l.creatures_roster_init(C.byref(r))
  for n in range(161):
   self.assertEqual(self.l.creatures_roster_validate(C.byref(r)),1)
   if n:r.selected_party=n%min(n,4)
   for chapter in (0,1,2,3,7,15,0xffffffff):self.compare(r,chapter)
   if n<160:self.assertLess(self.l.creatures_grant(C.byref(r),(1,4,7,10,19,22,73,75,77,121)[n%10],1+n%50,n%101,0,0),160)
 def test_story_identities_floors_trials_levels_party_and_exhaustion(self):
  for chapter in (0,1,3,7):
   r=h.Roster();self.assertEqual(self.l.creatures_migrate_legacy(C.byref(r),chapter,0),1)
   for i,c in enumerate(r.instances):
    if not c.form_id:continue
    c.trial_flags|=1<<i;c.bond=80 if i&1 else 20
   self.assertEqual(self.l.creatures_roster_validate(C.byref(r)),1)
   for n in (4,18,72,156,157,158,159,160):
    while sum(bool(c.form_id)for c in r.instances)<n:self.assertLess(self.l.creatures_grant(C.byref(r),1,37,66,0,0),160)
    for target in (0,1,3,7,15):self.compare(r,target)
  for nxt in (0xfffffffe,0xffffffff):
   r=h.Roster();self.l.creatures_roster_init(C.byref(r));r.next_instance_id=nxt;self.compare(r,7)
 def test_cancel_stale_alias_mutation_and_wrong_purpose(self):
  r=h.Roster();self.l.creatures_migrate_legacy(C.byref(r),0,0);snap=h.Roster.from_buffer_copy(bytes(r));before=bytes(r)
  for at in (0,1,20,39,40):
   token=self.l.creatures_story_job_begin(C.byref(snap),7)
   for _ in range(at):self.l.creatures_admission_job_step(token,4)
   self.l.creatures_story_job_cancel(token);self.assertEqual(self.l.creatures_story_job_commit(token,C.byref(r)),0);self.assertEqual(bytes(r),before)
  for offset in (0,16,h.Roster.party.offset,h.Roster.next_instance_id.offset,h.Roster.seen.offset,h.Roster.expedition_events.offset):
   token=self.l.creatures_story_job_begin(C.byref(snap),7)
   for _ in range(40):self.l.creatures_admission_job_step(token,4)
   raw=(C.c_ubyte*C.sizeof(r)).from_buffer(r);raw[offset]^=1;changed=bytes(r)
   self.assertEqual(self.l.creatures_story_job_commit(token,C.byref(r)),0);self.assertEqual(bytes(r),changed);raw[offset]^=1
  token=self.l.creatures_story_job_begin(C.byref(snap),7)
  self.assertEqual(self.l.creatures_admission_job_step(token,0),-1);self.assertEqual(self.l.creatures_admission_job_step(token,5),-1)
  for _ in range(40):self.l.creatures_admission_job_step(token,4)
  self.assertEqual(self.l.creatures_story_job_commit(token,C.byref(snap)),0);self.assertEqual(bytes(snap),before)
  token=self.l.creatures_admission_job_begin(C.byref(snap),7,255)
  for _ in range(40):self.l.creatures_admission_job_step(token,4)
  self.assertEqual(self.l.creatures_story_job_commit(token,C.byref(r)),0);self.assertEqual(bytes(r),before)
  token=self.l.creatures_story_job_begin(C.byref(snap),7)
  for _ in range(40):self.l.creatures_admission_job_step(token,4)
  slot=C.c_uint();self.assertEqual(self.l.creatures_admission_job_commit_grant(token,C.byref(r),8,20,2,3,C.byref(slot)),2);self.assertEqual(bytes(r),before)
 def test_full_save_transaction_atomic_cancel_mutation_and_sram(self):
  l=self.l;s=h.source(l);before=bytes(s);sram=bytes(l.sram);expected=h.Save.from_buffer_copy(before);self.sync(expected.roster,7)
  self.assertEqual(l.story_rewards_begin(C.byref(s),7),1)
  for n in range(200):
   result=l.story_rewards_step();self.assertEqual(bytes(l.sram),sram)
   if result!=h.BUSY:break
   self.assertEqual(bytes(s),before)
  self.assertEqual(result,h.DONE);self.assertEqual(bytes(s),bytes(expected));self.assertEqual(l.save5_validate(C.byref(s)),1)
  for at in (0,1,10,55,95):
   s=h.Save.from_buffer_copy(before);self.assertEqual(l.story_rewards_begin(C.byref(s),7),1)
   for _ in range(at):self.assertEqual(l.story_rewards_step(),h.BUSY)
   l.story_rewards_cancel();self.assertEqual(bytes(s),before);self.assertEqual(bytes(l.sram),sram)
  for offset in (h.Save.roster.offset+16,h.Save.campaign.offset,h.Save.quests.offset,h.Save.equipment.offset):
   s=h.Save.from_buffer_copy(before);self.assertEqual(l.story_rewards_begin(C.byref(s),7),1)
   self.assertEqual(l.story_rewards_step(),h.BUSY)
   raw=(C.c_ubyte*C.sizeof(s)).from_buffer(s);raw[offset]^=1;changed=bytes(s)
   for _ in range(200):
    result=l.story_rewards_step()
    if result!=h.BUSY:break
   self.assertEqual(result,h.FAILED);self.assertEqual(bytes(s),changed);self.assertEqual(bytes(l.sram),sram)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Story))
 if result.wasSuccessful():
  paths=['src/creatures.c','src/creature_admission_job.inc','src/story_rewards.c','src/story_rewards.h']
  (ROOT/'build/story-rewards-host.json').write_text(json.dumps({'scope':__doc__,'differential_cases':Story.cases,'tests':result.testsRun,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in paths}},indent=2)+'\n')
 raise SystemExit(not result.wasSuccessful())
