#!/usr/bin/env python3
"""Revision6 exact typed transactions and fixed-wire save tests.

Setup begins with authenticated native Magma34. Underwater actions here are
synthetic calls, not controller-earned world proof.
"""
import ctypes as C
import hashlib
import json
import os
import re
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest
from test_save5 import ROOT,Save,Instance,Roster,Equipment,compare_state,repair_crc,A,B,SIZE,BUSY,DONE,FAILED
SOURCES=('save4','save5','creatures','creature_data','equipment','equipment_data','southern_quests','magma_quests','underwater_quests')
FIXTURE=ROOT/'tests/fixtures/v5-revision5/magma-all65-town.sav'
FIXTURE_SHA='a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def runtime_hashes():
 """Hash the complete quoted-include closure, including immutable policy .inc."""
 pending=[ROOT/'src'/f'{n}.c' for n in SOURCES];result={}
 while pending:
  path=pending.pop().resolve();key=str(path.relative_to(ROOT))
  if key in result:continue
  result[key]=sha(path)
  for include in re.findall(r'#include\s+"([^"]+)"',path.read_text()):
   child=path.parent/include
   if not child.exists():child=ROOT/'src'/include
   if child.exists():pending.append(child)
 return dict(sorted(result.items()))
def prepare(folder,synthetic=False,codec=False):
 folder.mkdir(parents=True,exist_ok=True);data=FIXTURE.read_bytes();assert sha(FIXTURE)==FIXTURE_SHA
 # Binary-to-C fixture is private temporary test input, not a public text asset.
 (folder/'underwater_magma_fixture.h').write_text('static const unsigned char underwater_magma_fixture[32768]={'+','.join(map(str,data))+'};\n')
 sources={n:ROOT/'src'/f'{n}.c' for n in SOURCES}
 if synthetic:
  p=folder/'synthetic-equipment.c';text=sources['equipment_data'].read_text();mark='const EquipmentDefinition equipment_definitions[EQUIPMENT_DEFINITION_CAPACITY] = {\n';assert text.count(mark)==1
  rows=''.join(f' [{i}]={{{i},1,0,0,255,{{0,0}},{{0,0,0,0,0,0,0,0}}}},\n' for i in range(100,147));p.write_text(text.replace(mark,mark+rows));sources['equipment_data']=p
 if codec:
  assert synthetic;p=folder/'synthetic-save5.c';text=sources['save5'].read_text();mark='static const Save5HistoryItem *history_item(unsigned id, unsigned revision) {\n';assert text.count(mark)==1
  rows=','.join('{%d,1,0,0,-1}'%i for i in range(100,147));text=text.replace(mark,mark+' static const Save5HistoryItem synthetic_items[47]={'+rows+'};\n if(revision==6&&id>=100&&id<=146)return &synthetic_items[id-100];\n');p.write_text(text);sources['save5']=p
 return sources

def build(folder,synthetic=False,codec=False,sanitize=False):
 sources=prepare(folder,synthetic,codec);out=folder/('sanitizer' if sanitize else 'underwater.so')
 flags=['-std=c99','-O1' if sanitize else '-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-I'+str(ROOT/'src'),'-I'+str(folder)]
 if sanitize:flags+=['-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'];extra=[ROOT/'tests/underwater_save_sanitizer.c']
 else:flags+=['-shared','-fPIC'];extra=[]
 subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+flags+[*map(str,sources.values()),str(ROOT/'tests/underwater_save_setup.c'),*map(str,extra),'-o',str(out)],check=True)
 if sanitize:return out
 lib=C.CDLL(str(out));lib._source_hashes=runtime_hashes();lib.sram=(C.c_ubyte*32768).in_dll(lib,'save5_test_sram')
 for n in ('save5_load','save5_store','save5_begin','save5_validate','underwater_test_earned34','underwater_test_recruits'):
  getattr(lib,n).argtypes=[C.POINTER(Save)]
 for n in ('underwater_visit','underwater_anchor','underwater_quest_available','underwater_quest_offer','underwater_quest_claim','underwater_source_claimed','underwater_source_status','underwater_field_recruit','underwater_branch_status','underwater_branch_recruit','underwater_test_ready','underwater_test_completed','underwater_test_slot','underwater_can_enter','underwater_discovery_state','save5_validate_revision'):
  getattr(lib,n).argtypes=[C.POINTER(Save),C.c_uint]
 for n in ('underwater_quest_objective','underwater_discover'):getattr(lib,n).argtypes=[C.POINTER(Save),C.c_uint,C.c_uint]
 for n in ('underwater_trial_status','underwater_trial_complete'):getattr(lib,n).argtypes=[C.POINTER(Save)]+[C.c_uint]*5
 lib.underwater_context.argtypes=[C.POINTER(Save)];lib.underwater_recruit_level.argtypes=[C.POINTER(Roster)]
 lib.creatures_evolve_to.argtypes=[C.POINTER(Roster)]+[C.c_uint]*5
 lib.creatures_grant.argtypes=[C.POINTER(Roster)]+[C.c_uint]*5
 lib.creatures_admission_query_grant.argtypes=[C.POINTER(Roster),C.c_uint,C.c_void_p]
 lib.equipment_validate.argtypes=[C.POINTER(Equipment)];lib.equipment_claim.argtypes=[C.POINTER(Equipment),C.c_uint,C.c_uint,C.c_void_p]
 lib.save5_quest_state.argtypes=[C.c_void_p,C.c_uint];lib.save5_step.argtypes=[C.c_uint]
 lib.save5_test_fail_after.argtypes=[C.c_int];lib.save5_test_corrupt_write.argtypes=[C.c_int,C.c_ubyte]
 return lib

class UnderwaterSaveTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='underwater-save-');cls.addClassCleanup(cls.tmp.cleanup);cls.folder=Path(cls.tmp.name)
  cls.lib=build(cls.folder/'normal');cls.augmented=build(cls.folder/'augmented',True);cls.synthetic=build(cls.folder/'synthetic',True,True)
 def state(self,mode='earned34',lib=None):
  lib=lib or self.lib;s=Save();fn=getattr(lib,'underwater_test_'+mode)
  self.assertEqual(fn(C.byref(s),0) if mode=='completed' else fn(C.byref(s)),0);return s
 def unchanged(self,s,call,result):
  before=bytes(s);self.assertEqual(call(),result);self.assertEqual(bytes(s),before)
 def ready(self,s,q,lib=None):self.assertEqual((lib or self.lib).underwater_test_ready(C.byref(s),q),0)
 def reject(self,s):
  lib=self.lib;before=bytes(lib.sram);writes=lib.save5_test_write_count();self.assertEqual(lib.save5_validate(C.byref(s)),0)
  if lib.save5_begin(C.byref(s)):
   while lib.save5_status()==BUSY:lib.save5_step(3072)
  self.assertEqual(lib.save5_status(),FAILED);self.assertEqual(bytes(lib.sram),before);self.assertEqual(lib.save5_test_write_count(),writes)
 def test_exact89_history_50_real_identities_37_items_roundtrip(self):
  s=self.state('completed');self.assertEqual(sum(bool(c.form_id) for c in s.roster.instances),50)
  self.assertEqual(sum(b.bit_count() for b in s.roster.obtained),89);self.assertEqual(sum(bool(x.item_id) for x in s.equipment.bag),37)
  self.assertEqual(s.quests.region_flags[17],255);self.assertEqual(len({c.instance_id for c in s.roster.instances if c.form_id}),50)
  self.assertEqual(self.lib.save5_validate_revision(C.byref(s),6),1)
  for rev in range(1,6):self.assertEqual(self.lib.save5_validate_revision(C.byref(s),rev),0)
  for budget in (1,64,1024,3072,0xffffffff):
   self.assertEqual(self.lib.save5_begin(C.byref(s)),1)
   while self.lib.save5_status()==BUSY:self.lib.save5_step(budget);self.assertLessEqual(self.lib.save5_test_step_work(),min(budget,3072))
   self.assertEqual(self.lib.save5_status(),DONE);out=Save();self.assertEqual(self.lib.save5_load(C.byref(out)),1);self.assertEqual(compare_state(out),compare_state(s))
 def test_native34_migrates_unchanged_without_new_receipts(self):
  s=self.state();before=compare_state(s);self.assertEqual(self.lib.save5_validate_revision(C.byref(s),5),1)
  self.assertEqual(self.lib.save5_store(C.byref(s)),1);out=Save();self.assertEqual(self.lib.save5_load(C.byref(out)),1);self.assertEqual(compare_state(out),before)
  for i in (4,10,17,20,21):self.assertEqual(out.quests.region_flags[i],0)
  self.assertEqual(out.quests.anchors[4],0)
  self.assertFalse(any(self.lib.save5_quest_state(C.byref(out.quests),q) for q in range(38,46)))
 def test_exact_source_discovery_trial_namespaces_and_32bit_inputs(self):
  lib=self.lib;s=self.state('recruits');slot=lib.underwater_test_slot(C.byref(s),49);c=s.roster.instances[slot]
  for token in (0,9,16,17,24,256,0x10001,0xffffffff):
   for name in ('underwater_source_status','underwater_field_recruit','underwater_branch_recruit'):
    self.unchanged(s,lambda:getattr(lib,name)(C.byref(s),token),-1)
  for args,result in [((slot,c.instance_id+1,17,1,1),-1),((slot,c.instance_id,18,1,2),-1),((slot,c.instance_id,17,1,3),-1),((slot,c.instance_id,17,0,1),-1),((slot,c.instance_id,17,3,1),-1),((0x10000+slot,c.instance_id,17,1,1),-1)]:
   self.unchanged(s,lambda:lib.underwater_trial_complete(C.byref(s),*args),result)
  self.assertEqual(lib.underwater_trial_complete(C.byref(s),slot,c.instance_id,17,2,1),3)
  self.assertEqual(c.trial_flags,2);self.assertGreaterEqual(c.level,28);self.assertGreaterEqual(c.bond,45)
  self.assertEqual(lib.underwater_trial_complete(C.byref(s),slot,c.instance_id,17,1,1),3);self.assertEqual(c.trial_flags,3)
  self.unchanged(s,lambda:lib.underwater_trial_complete(C.byref(s),slot,c.instance_id,17,2,1),0)
  self.assertEqual(lib.creatures_evolve_to(C.byref(s.roster),slot,51,lib.underwater_context(C.byref(s)),1,1),0)
  for token in range(3,9):self.unchanged(s,lambda:lib.underwater_field_recruit(C.byref(s),token),0)
  for family in (17,22,25,65559):self.unchanged(s,lambda:lib.underwater_discover(C.byref(s),family,1),-1)
 def test_main_route_and_return_spawns_require_permanent_prefixes(self):
  lib=self.lib;s=self.state();self.assertEqual(lib.underwater_visit(C.byref(s),46),1)
  for room in (50,51,52,53):self.unchanged(s,lambda:lib.underwater_visit(C.byref(s),room),4)
  self.unchanged(s,lambda:lib.underwater_quest_offer(C.byref(s),45),4)
  for q in (38,39):self.ready(s,q);self.assertEqual(lib.underwater_quest_claim(C.byref(s),q),3)
  self.assertEqual(lib.underwater_quest_offer(C.byref(s),40),1)
  for bit in (2,4,8):self.unchanged(s,lambda:lib.underwater_quest_objective(C.byref(s),40,bit),4)
  self.assertEqual(lib.underwater_visit(C.byref(s),50),1)
  for room,bit in ((51,1),(52,2),(53,4)):
   self.assertEqual(lib.underwater_quest_objective(C.byref(s),40,bit),1);self.assertEqual(lib.underwater_visit(C.byref(s),room),1)
  for room in range(46,54):
   for spawn in range(6):
    trial=Save.from_buffer_copy(bytes(s));trial.campaign.room=38;trial.campaign.spawn=0
    if not (trial.quests.region_flags[4]&(1<<(room-46))):lib.underwater_visit(C.byref(trial),room)
    trial.campaign.room=room;trial.campaign.spawn=spawn
    expected=spawn<2 or (room==46 and spawn==3) or (room in (48,51,52) and spawn==2)
    self.assertEqual(lib.save5_validate(C.byref(trial)),expected,(room,spawn))
  for room in (46,47):
   self.assertIn(lib.underwater_visit(C.byref(s),room),(0,1));self.assertEqual(lib.underwater_anchor(C.byref(s),room),1)
   s.campaign.room=room;s.campaign.spawn=2;self.assertEqual(lib.save5_validate(C.byref(s)),1)
 def test_extra_receipt_requires_two_retained_and_terminal_without_replay(self):
  lib=self.lib;s=self.state('completed');events=bytes(s.roster.expedition_events);aids=bytes(s.roster.lifetime_field_aid);gear=bytes(s.equipment);q=bytes(s.quests)
  for token in range(1,9):
   ids={c.instance_id for c in s.roster.instances if c.form_id};self.assertEqual(lib.underwater_branch_recruit(C.byref(s),token),3)
   slot=lib.underwater_test_slot(C.byref(s),49+3*(token-1));c=s.roster.instances[slot]
   self.assertNotIn(c.instance_id,ids);self.assertEqual(c.trial_flags,0);self.assertEqual(c.bond,20)
  self.assertEqual(bytes(s.roster.expedition_events),events);self.assertEqual(bytes(s.roster.lifetime_field_aid),aids);self.assertEqual(bytes(s.equipment),gear);self.assertEqual(bytes(s.quests),q)
  bad=Save.from_buffer_copy(bytes(s));bad.quests.region_flags[10]&=~1;self.reject(bad)
  bad=Save.from_buffer_copy(bytes(s));slot=lib.underwater_test_slot(C.byref(bad),50);bad.roster.instances[slot].bond=44;self.reject(bad)
  bad=Save.from_buffer_copy(bytes(s))
  for c in bad.roster.instances:
   if c.form_id in (50,51):C.memset(C.byref(c),0,C.sizeof(Instance))
  self.reject(bad)
 def test_invalid_typed_bytes_never_write(self):
  s=self.state('completed')
  mutations=[('region_flags',4,0),('region_flags',10,127),('region_flags',20,2),('region_flags',21,6),('region_flags',22,1),('anchors',4,4),('anchors',5,1),('variables',38,1)]
  for field,index,value in mutations:
   bad=Save.from_buffer_copy(bytes(s));getattr(bad.quests,field)[index]=value;self.reject(bad)
  for quest in range(46,64):
   bad=Save.from_buffer_copy(bytes(s));bad.quests.objectives[quest]=1;self.reject(bad)
 def test_id_exhaustion_and_full_roster_are_atomic(self):
  lib=self.lib;s=self.state('completed');s.roster.next_instance_id=0xffffffff
  self.unchanged(s,lambda:lib.underwater_branch_recruit(C.byref(s),1),7)
  self.assertEqual(lib.underwater_test_completed(C.byref(s),1),0)
  self.unchanged(s,lambda:lib.underwater_branch_recruit(C.byref(s),1),5)
  self.assertEqual(lib.save5_store(C.byref(s)),1);out=Save();self.assertEqual(lib.save5_load(C.byref(out)),1);self.assertEqual(compare_state(s),compare_state(out))
 def test_bundle_second_item_full_rolls_back_and_seen_discard_settles(self):
  lib=self.augmented;s=self.state('recruits',lib);self.ready(s,45,lib)
  # Runtime-only synthetic unique equipment fills capacity without legalizing
  # any production wire IDs. Keep authentic quest claims and seen history.
  for i in range(1,48):
   r=s.equipment.bag[i];r.item_id=100+i-1;r.rank=r.flags=0;r.quantity=1;r.reserved[:]=bytes(3);s.equipment.seen[r.item_id>>3]|=1<<(r.item_id&7)
  s.equipment.equipped[0]=0
  for i in range(1,5):s.equipment.equipped[i]=255
  self.assertEqual(lib.save5_validate(C.byref(s)),1)
  self.unchanged(s,lambda:lib.underwater_quest_claim(C.byref(s),45),5)
  C.memset(C.byref(s.equipment.bag[47]),0,8)
  self.unchanged(s,lambda:lib.underwater_quest_claim(C.byref(s),45),5)
  # First unique item was owned before and discarded: settle its ledger, use
  # the one free slot only for second item. Neither reward duplicates history.
  s.equipment.seen[68>>3]|=1<<(68&7)
  self.assertEqual(lib.underwater_quest_claim(C.byref(s),45),3)
  self.assertFalse(any(x.item_id==68 for x in s.equipment.bag));self.assertEqual(sum(x.item_id==86 for x in s.equipment.bag),1)
  self.unchanged(s,lambda:lib.underwater_quest_claim(C.byref(s),45),0)
 def test_synthetic_full160_full48_roundtrip_and_production_rejection(self):
  lib=self.synthetic;s=Save();self.assertEqual(lib.underwater_test_completed(C.byref(s),1),0)
  for i in range(1,48):
   record=s.equipment.bag[i];record.item_id=99+i;record.rank=record.flags=0;record.quantity=1;record.reserved[:]=bytes(3)
   s.equipment.seen[record.item_id>>3]|=1<<(record.item_id&7)
  s.equipment.equipped[0]=0
  for i in range(1,5):s.equipment.equipped[i]=255
  self.assertEqual(lib.save5_validate(C.byref(s)),1)
  for budget in (1,768,1024,3072):
   self.assertEqual(lib.save5_begin(C.byref(s)),1)
   while lib.save5_status()==BUSY:lib.save5_step(budget);self.assertLessEqual(lib.save5_test_step_work(),budget)
   self.assertEqual(lib.save5_status(),DONE);out=Save();self.assertEqual(lib.save5_load(C.byref(out)),1);self.assertEqual(compare_state(out),compare_state(s))
  # Production cannot decode temporary stress identities, even with valid CRC.
  latest=max((A,B),key=lambda offset:int.from_bytes(bytes(lib.sram[offset+8:offset+12]),'little'))
  self.lib.save5_test_reset_writer();self.lib.save5_test_fail_after(-1);self.lib.sram[:]=bytes([255])*32768
  self.lib.sram[A:A+SIZE]=bytes(lib.sram[latest:latest+SIZE]);before=bytes(self.lib.sram);out=Save()
  self.assertEqual(self.lib.save5_load(C.byref(out)),0);self.assertEqual(bytes(self.lib.sram),before)
 def test_asan_ubsan_snapshot_mutations_and_staged_jobs(self):
  exe=build(self.folder/'sanitized',sanitize=True)
  run=subprocess.run([str(exe)],capture_output=True,text=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'))
  self.assertEqual(run.returncode,0,run.stdout+'\n'+run.stderr);result=json.loads(run.stdout);self.assertEqual(result['result'],'PASS')
  report=dict(result,scope='Host ASan/UBSan; synthetic Underwater state atop authentic Magma34',fixture_sha256=FIXTURE_SHA,source_sha256=self.lib._source_hashes,source_unchanged_during_measurement=self.lib._source_hashes==runtime_hashes())
  (ROOT/'docs/evidence/underwater-save-sanitizers.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
