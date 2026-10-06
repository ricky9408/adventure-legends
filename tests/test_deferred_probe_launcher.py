#!/usr/bin/env python3
"""Synthetic launcher control-flow tests, not game/native acceptance."""
import errno,importlib.util,json,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('launcher',ROOT/'tools/run_deferred_anchor_probe.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def result(code=78,**changes):
 d=dict(kind='synthetic-address-reservation',errno=errno.EEXIST,address=0x05000000,length=0x20000,mapped_before_failure=1,overlaps=[dict(start=0x04d48000,end=0x051a2000,tag='[heap]')],game_assertions_started=False,overwritten_mappings=False)
 d.update(changes)
 return subprocess.CompletedProcess([],code,'',m.PREFIX+json.dumps(d)+'\n')
class LauncherTests(unittest.TestCase):
 def run_case(self,results):
  calls=[];records=[]
  def run(n):calls.append(n);return results[n-1]
  status=m.run_attempts(run,lambda n,r,d:records.append((n,r.returncode,d)))
  return status,calls,records
 def test_success_once(self):self.assertEqual(self.run_case([result(0)])[:2],(0,[1]))
 def test_proved_collision_then_success(self):
  status,calls,rows=self.run_case([result(),result(0)]);self.assertEqual((status,calls),(0,[1,2]));self.assertIsNotNone(rows[0][2])
 def test_maximum_three_attempts_retains_all_failures(self):
  status,calls,rows=self.run_case([result(),result(),result()]);self.assertEqual((status,calls),(78,[1,2,3]));self.assertEqual(len(rows),3)
 def test_game_assertion_never_retried(self):self.assertEqual(self.run_case([result(1)])[:2],(1,[1]))
 def test_permission_denial_never_retried(self):self.assertEqual(self.run_case([result(errno=errno.EACCES)])[:2],(78,[1]))
 def test_allocation_failure_never_retried(self):self.assertIsNone(m.collision_detail(result(errno=errno.ENOMEM)))
 def test_unknown_overlap_never_retried(self):self.assertIsNone(m.collision_detail(result(overlaps=[dict(start=0x04d48000,end=0x051a2000,tag='other')])))
 def test_nonoverlapping_heap_never_retried(self):self.assertIsNone(m.collision_detail(result(overlaps=[dict(start=1,end=9,tag='[heap]')])))
 def test_game_started_never_retried(self):self.assertIsNone(m.collision_detail(result(game_assertions_started=True)))
 def test_forced_mapping_never_retried(self):self.assertIsNone(m.collision_detail(result(overwritten_mappings=True)))
 def test_wrong_stage_never_retried(self):self.assertIsNone(m.collision_detail(result(mapped_before_failure=0)))
 def test_unexpected_address_never_retried(self):self.assertIsNone(m.collision_detail(result(address=0x08000000)))
 def test_malformed_diagnostic_never_retried(self):self.assertIsNone(m.collision_detail(subprocess.CompletedProcess([],78,'',m.PREFIX+'{bad}')))
 def test_multiple_diagnostics_never_retried(self):
  r=result();r.stderr+=r.stderr;self.assertIsNone(m.collision_detail(r))
 def test_two_collisions_then_actual_game_failure_is_not_hidden(self):self.assertEqual(self.run_case([result(),result(),result(1)])[:2],(1,[1,2,3]))
if __name__=='__main__':unittest.main(verbosity=2)
