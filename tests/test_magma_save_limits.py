#!/usr/bin/env python3
"""Magma atomic full48, full160, sanitizer and isolated native save timings."""
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_save5 import ROOT,Save,Equipment,A,B,SIZE,BUSY,DONE,FAILED,compare_state
import test_southern_save_limits as old
SOURCES=(*old.SOURCES,'magma_quests')
FIXTURE=ROOT/'tests/fixtures/v5-revision4/southern-all41-town.sav'
FIXTURE_SHA='0bd83c19eb0dee81b3cd9e2b48462f6362b559786e38fa119312fe05787b0bd3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare(folder,synthetic=False,codec=False):
 sources=old.prepare(folder,synthetic,codec)
 sources['magma_quests']=folder/'magma_quests.c';sources['magma_quests'].write_bytes((ROOT/'src/magma_quests.c').read_bytes())
 data=FIXTURE.read_bytes();assert hashlib.sha256(data).hexdigest()==FIXTURE_SHA
 (folder/'magma_s3_fixture.h').write_text('static const unsigned char magma_s3_fixture[32768]={\n'+',\n'.join(','.join(str(x) for x in data[i:i+64]) for i in range(0,len(data),64))+'\n};\n')
 return sources
def build(folder,synthetic=False,codec=False,sanitize=False):
 folder.mkdir(parents=True,exist_ok=True);sources=prepare(folder,synthetic,codec);out=folder/('sanitizer' if sanitize else 'magma.so')
 flags=['-std=c99','-O1' if sanitize else '-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-I'+str(ROOT/'src'),'-I'+str(folder)]
 if sanitize:flags+=['-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']
 else:flags+=['-DMAGMA_SETUP_ONLY','-shared','-fPIC']
 subprocess.run(['cc',*flags,str(ROOT/'tests/magma_save_sanitizer.c'),*map(str,sources.values()),'-o',str(out)],check=True)
 if sanitize:return out
 lib=C.CDLL(str(out));lib.sram=(C.c_ubyte*32768).in_dll(lib,'save5_test_sram')
 for fn in ('magma_test_southern','magma_test_full48','save5_validate','save5_store','save5_load','save5_begin'):
  getattr(lib,fn).argtypes=[C.POINTER(Save)]
 for fn in ('magma_test_completed','magma_test_ready','magma_visit','magma_quest_claim','magma_field_recruit','magma_discover','magma_source_status'):
  getattr(lib,fn).argtypes=[C.POINTER(Save),C.c_uint]
 lib.equipment_validate.argtypes=[C.POINTER(Equipment)];lib.save5_step.argtypes=[C.c_uint]
 return lib
class MagmaLimitsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='magma-save-limits-');cls.addClassCleanup(cls.tmp.cleanup);cls.root=Path(cls.tmp.name)
  cls.normal=build(cls.root/'normal');cls.augmented=build(cls.root/'augmented',True);cls.synthetic=build(cls.root/'synthetic',True,True)
 def test_mixed_Q30_full48_preflight_no_partial_roster_or_gear(self):
  lib=self.augmented;s=Save();self.assertEqual(lib.magma_test_southern(C.byref(s)),0);self.assertEqual(lib.magma_visit(C.byref(s),38),1)
  self.assertEqual(lib.magma_test_ready(C.byref(s),30),0);self.assertEqual(lib.magma_test_full48(C.byref(s)),0)
  before=bytes(s)
  for _ in range(8):
   self.assertEqual(lib.magma_source_status(C.byref(s),1),5);self.assertEqual(bytes(s),before)
   self.assertEqual(lib.magma_quest_claim(C.byref(s),30),5);self.assertEqual(bytes(s),before)
  C.memset(C.byref(s.equipment.bag[47]),0,C.sizeof(s.equipment.bag[47]))
  self.assertEqual(lib.magma_quest_claim(C.byref(s),30),3)
  self.assertEqual(sum(c.form_id==31 for c in s.roster.instances),1);self.assertEqual(sum(e.item_id==20 for e in s.equipment.bag),1)
  self.assertEqual(lib.save5_validate(C.byref(s)),1)
 def test_discovery_READY_with_full_gear_has_no_gear_gate(self):
  lib=self.augmented;s=Save();self.assertEqual(lib.magma_test_southern(C.byref(s)),0)
  for room in (38,41):self.assertEqual(lib.magma_visit(C.byref(s),room),1)
  self.assertEqual(lib.magma_test_full48(C.byref(s)),0)
  for bit in (1,2,4):self.assertIn(lib.magma_discover(C.byref(s),bit),(1,2))
  self.assertEqual(lib.magma_field_recruit(C.byref(s),22),3)
  self.assertEqual(sum(e.item_id!=0 for e in s.equipment.bag),48);self.assertEqual(sum(c.form_id==99 for c in s.roster.instances),1)
 def test_full160_65_31_and_synthetic48_roundtrip_bounded_steps(self):
  for lib,full48 in ((self.normal,False),(self.synthetic,True)):
   s=Save();self.assertEqual(lib.magma_test_completed(C.byref(s),1),0)
   if full48:self.assertEqual(lib.magma_test_full48(C.byref(s)),0)
   for budget in (1,64,1024,3072,4096):
    self.assertEqual(lib.save5_begin(C.byref(s)),1)
    while lib.save5_status()==BUSY:lib.save5_step(budget);self.assertLessEqual(lib.save5_test_step_work(),min(budget,3072))
    self.assertEqual(lib.save5_status(),DONE);out=Save();self.assertEqual(lib.save5_load(C.byref(out)),1);self.assertEqual(compare_state(s),compare_state(out))
 def test_full48_temporary_policy_never_enables_production_or_old_revisions(self):
  s=Save();lib=self.synthetic;self.assertEqual(lib.magma_test_completed(C.byref(s),1),0);self.assertEqual(lib.magma_test_full48(C.byref(s)),0)
  self.assertEqual(lib.save5_store(C.byref(s)),1)
  real=self.augmented;before=bytes(real.sram);self.assertEqual(real.save5_begin(C.byref(s)),1)
  while real.save5_status()==BUSY:real.save5_step(3072)
  self.assertEqual(real.save5_status(),FAILED);self.assertEqual(bytes(real.sram),before)
  latest=max((A,B),key=lambda off:int.from_bytes(bytes(lib.sram[off+8:off+12]),'little'))
  real.sram[:]=bytes([255])*32768;real.sram[A:A+SIZE]=bytes(lib.sram[latest:latest+SIZE]);out=Save()
  self.assertEqual(real.save5_load(C.byref(out)),0)
 def test_asan_ubsan_1200_snapshot_mutations_and_trial_queries(self):
  exe=build(self.root/'sanitized',sanitize=True)
  run=subprocess.run([str(exe)],capture_output=True,text=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'))
  self.assertEqual(run.returncode,0,run.stdout+'\n'+run.stderr)
  result=json.loads(run.stdout);self.assertEqual(result['result'],'PASS')
  p=ROOT/'docs/evidence/magma-save-sanitizers.json';p.parent.mkdir(exist_ok=True)
  p.write_text(json.dumps(dict(result,source_sha256={n:sha(ROOT/'src'/f'{n}.c') for n in SOURCES},fixture_sha256=FIXTURE_SHA,scope='Host ledger/codec only; not controller acquisition'),indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
