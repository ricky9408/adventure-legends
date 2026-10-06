#!/usr/bin/env python3
"""Host-only evidence-export guard checks; never gameplay/acquisition evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('magma_evidence',ROOT/'tools/package_magma_evidence.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class EvidenceGuard(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'report.json'
  self.report=dict(suite='synthetic exporter input',rom_sha256='r',symbols_sha256='s',controller_only=True,game_ram_writes=0,failures=[],checks=[dict(passed=True)],frame_windows=[dict(name='x',hardware_frames=1,updates=1,flips=1,trace=[dict(delta=1,flip=True)])])
 def tearDown(self):self.tmp.cleanup()
 def run_report(self):
  self.path.write_text(json.dumps(self.report));return module.summarize(self.path,'r','s')
 def test_short_keys(self):self.assertEqual(self.run_report()['frame_windows'][0]['trace_count'],1)
 def test_long_keys(self):
  self.report['frame_windows'][0]['trace']=[dict(update_delta=1,page_flip=True)];self.assertEqual(self.run_report()['passed_checks'],1)
 def test_missing_cadence_rejected(self):
  self.report['frame_windows'][0]['trace']=[dict(cycles=1)]
  with self.assertRaises(AssertionError):self.run_report()
 def test_missed_update_rejected(self):
  self.report['frame_windows'][0]['trace'][0]['delta']=0
  with self.assertRaises(AssertionError):self.run_report()
 def test_missed_flip_rejected(self):
  self.report['frame_windows'][0]['trace'][0]['flip']=False
  with self.assertRaises(AssertionError):self.run_report()
 def test_count_mismatch_rejected(self):
  self.report['frame_windows'][0]['hardware_frames']=2
  with self.assertRaises(AssertionError):self.run_report()
 def test_wrong_rom_rejected(self):
  self.report['rom_sha256']='wrong'
  with self.assertRaises(AssertionError):self.run_report()
 def test_failure_rejected(self):
  self.report['failures']=['failed']
  with self.assertRaises(AssertionError):self.run_report()
 def test_game_ram_write_rejected(self):
  self.report['game_ram_writes']=1
  with self.assertRaises(AssertionError):self.run_report()
if __name__=='__main__':unittest.main()
