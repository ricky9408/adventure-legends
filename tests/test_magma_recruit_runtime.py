#!/usr/bin/env python3
"""Synthetic world-pose tests around the actual async Magma branch wrapper."""
import ctypes as C,hashlib,unittest
from pathlib import Path
from test_magma_game import L,SRAM,v,ROOT
from test_save5 import Save,BUSY,DONE,FAILED
FIXTURE=ROOT/'tests/fixtures/v5-revision7/return-all104-town.sav'
assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()=='d482466d04050c3d7f2e8eb8e1960729c9b9b33aa3e32440d186a4b54b854a69'
def live():return Save.in_dll(L,'adventure_save')
def state():return bytes(live())
class MagmaRecruitRuntime(unittest.TestCase):
 def setUp(self):
  L.magma_game_cancel_event();SRAM[:]=FIXTURE.read_bytes();self.assertEqual(L.fresh(),1);self.assertEqual(L.entry(39,3),1);L.at(80,248);L.facing(1)
 def queue(self):
  self.assertEqual(L.magma_game_interact(),1);self.assertFalse(L.magma_game_event_pending());before=state()
  self.assertEqual(L.magma_game_interact(),1);self.assertTrue(L.magma_game_event_pending());self.assertEqual(state(),before)
  return before
 def advance(self):
  C.c_int.in_dll(L,'game_state').value=10
  for _ in range(150):
   status=L.magma_game_prepare_event()
   if status!=BUSY:return status
  self.fail('transaction did not terminate')
 def test_exact_once_repeat_without_credit_or_party_change(self):
  before=self.queue();old=Save.from_buffer_copy(before);sram=bytes(SRAM)
  self.assertEqual(self.advance(),DONE);self.assertEqual(bytes(SRAM),sram)
  C.c_int.in_dll(L,'game_state').value=1;self.assertEqual(L.magma_game_commit_event(),1);after=state();self.assertFalse(L.magma_game_event_pending());self.assertEqual(L.magma_game_commit_event(),0);self.assertEqual(state(),after)
  new=live();self.assertEqual(sum(bool(c.form_id) for c in new.roster.instances),53);self.assertEqual(bytes(new.roster.party),bytes(old.roster.party));self.assertEqual(new.roster.selected_party,old.roster.selected_party)
  self.assertEqual(bytes(new.roster.obtained),bytes(old.roster.obtained));self.assertEqual(bytes(new.roster.expedition_events),bytes(old.roster.expedition_events));self.assertEqual(bytes(new.roster.lifetime_field_aid),bytes(old.roster.lifetime_field_aid))
  for i,c in enumerate(old.roster.instances):
   if c.form_id:self.assertEqual(bytes(new.roster.instances[i]),bytes(c))
 def test_cancel_and_pose_scene_revision_changes_are_nonmutating(self):
  for change in ('cancel','room','x','y','face','spawn','chapter','revision','reset','load','mode'):
   self.setUp();before=self.queue();sram=bytes(SRAM);C.c_int.in_dll(L,'game_state').value=10
   self.assertEqual(L.magma_game_prepare_event(),BUSY)
   if change=='cancel':L.magma_game_cancel_event()
   elif change=='reset':L.magma_game_reset()
   elif change=='load':self.assertEqual(L.fresh(),1);before=state()
   elif change=='mode':C.c_int.in_dll(L,'game_state').value=1
   else:
    name={'room':'room','x':'px','y':'py','face':'face','spawn':'checkpoint_spawn','chapter':'chapter_flags','revision':'progression_revision'}[change]
    q=C.c_uint.in_dll(L,name);q.value+=1
   self.assertEqual(L.magma_game_prepare_event(),FAILED,change);self.assertFalse(L.magma_game_event_pending());self.assertEqual(state(),before,change);self.assertEqual(bytes(SRAM),sram,change)
 def test_pending_repeat_cannot_be_duplicated_and_new_confirmation_required_after_cancel(self):
  self.queue();self.assertEqual(L.magma_game_interact(),1);self.assertTrue(L.magma_game_event_pending());L.magma_game_cancel_event();self.assertFalse(L.magma_game_event_pending())
  self.assertEqual(L.magma_game_interact(),1);self.assertFalse(L.magma_game_event_pending());self.assertEqual(L.magma_game_interact(),1);self.assertTrue(L.magma_game_event_pending())
if __name__=='__main__':unittest.main(verbosity=2)
