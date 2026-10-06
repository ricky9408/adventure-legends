#!/usr/bin/env python3
"""Public-summary rejection tests; these are host metadata tests, not gameplay."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from package_underwater_evidence import summarize
class Evidence(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.p=Path(self.d.name)/'r.json'
  self.r={'suite':'underwater-native-combat-controls','rom_sha256':'rom','symbols_sha256':'sym','controller_only':True,'game_ram_writes':0,'failures':[],'checks':[{'passed':True}],'frame_windows':[{'name':'active','hardware_frames':1,'updates':1,'page_flips':1,'trace':[{'update_delta':1,'page_flip':True,'cycles':279000,'obj_count':128}]}]}
 def tearDown(self):self.d.cleanup()
 def run_report(self):self.p.write_text(json.dumps(self.r));return summarize(self.p,'rom','sym')
 def test_active(self):self.assertEqual(self.run_report()['passed_checks'],1)
 def test_failed_check(self):
  self.r['checks'][0]['passed']=False
  with self.assertRaises(AssertionError):self.run_report()
 def test_diagnostic(self):
  self.r['diagnostic_only']=True
  with self.assertRaises(AssertionError):self.run_report()
 def test_dropped_frame(self):
  self.r['frame_windows'][0]['trace'][0]['page_flip']=False
  with self.assertRaises(AssertionError):self.run_report()
 def test_cycles(self):
  self.r['frame_windows'][0]['trace'][0]['cycles']=280896
  with self.assertRaises(AssertionError):self.run_report()
 def test_false_loading_exemption(self):
  self.r['frame_windows'][0]['gameplay_cadence_exemption']=True
  with self.assertRaises(AssertionError):self.run_report()
 def test_explicit_cold_continue(self):
  self.r['suite']='underwater-independent-minimal-native-review';w=self.r['frame_windows'][0];w.update(name='fresh-whole-continue',scope='cold Continue decode and initial checkpoint before active play',gameplay_cadence_exemption=True);w['trace'][0].update(update_delta=0,page_flip=False,cycles=2224758)
  x=self.run_report()['frame_windows'][0];self.assertEqual(x['missed_update_or_flip_rows'],[0]);self.assertIn('raw stalls retained',x['scope'])
 def test_overlong_loading(self):
  self.r['suite']='underwater-independent-minimal-native-review';w=self.r['frame_windows'][0];w.update(name='fresh-whole-continue',scope='cold Continue decode and initial checkpoint before active play',gameplay_cadence_exemption=True);w['trace']*=121
  with self.assertRaises(AssertionError):self.run_report()
if __name__=='__main__':unittest.main(verbosity=2)
