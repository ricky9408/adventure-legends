#!/usr/bin/env python3
"""Current-r6 reciprocal landings; exact old-policy rejection remains frozen.

All raw cases have independent CRC repair and an otherwise valid state. These
are host/preflight checks, not native walking or collision evidence.
"""
import ctypes as C,hashlib,json,struct,tempfile,unittest
from pathlib import Path
from test_underwater_save import ROOT,build,runtime_hashes,FIXTURE_SHA
from test_underwater_transactions import configure
from test_save5 import Save,A,B,SIZE,repair_crc,compare_state,BUSY,DONE,FAILED
(ROOT/'build/current-host-evidence/underwater-return-spawns').mkdir(parents=True,exist_ok=True)
from test_underwater_history_differential import build as history_build,ORACLE
TEMPLATE_FIXTURE=ROOT/'tests/fixtures/v5-revision6/underwater-minimal12-town.sav'
TEMPLATE_SHA='3f5bbccab022f86b38f4d180e8cf66b04c055791fe4804ddbebbdefb5406aeda'

def historical_template():
 """Current revision11 used-size5088 is not the historical revision6 size5056."""
 raw=TEMPLATE_FIXTURE.read_bytes();assert hashlib.sha256(raw).hexdigest()==TEMPLATE_SHA
 provenance=json.loads((TEMPLATE_FIXTURE.parent/'provenance.json').read_text())
 row=next(x for x in provenance['fixtures'] if x['fixture']==TEMPLATE_FIXTURE.name)
 assert row['sha256']==TEMPLATE_SHA and row['controller_only'] and row['game_ram_writes']==0
 banks=[raw[offset:offset+SIZE] for offset in (A,B)]
 banks=[b for b in banks if b[:4]==b'EB\x05\x20' and b[20]==0xa5 and bytes(repair_crc(b))==b and int.from_bytes(b[12:14],'little')==6]
 assert banks,'No authenticated committed revision6 bank'
 bank=max(banks,key=lambda b:int.from_bytes(b[8:12],'little'))
 assert not any(bank[5056:]),'Historical economy/padding must remain zero'
 return bank

def encode_state(template,s,revision=6):
 b=bytearray(template);b[12:14]=revision.to_bytes(2,'little')
 c=s.campaign;b[32:47]=struct.pack('<8BIHB',c.room,c.spawn,c.chapter_flags,c.bridge,c.torches,c.relic,c.camp,c.optional_flags,c.room_flags,c.story_seen,c.spirit)
 b[96:144]=bytes(s.roster.seen)+bytes(s.roster.obtained)+bytes(s.roster.rewards)
 for i,c in enumerate(s.roster.instances):b[160+i*24:184+i*24]=struct.pack('<4BIIHH4BI',c.form_id,c.flags,c.level,c.bond,c.xp,c.instance_id,c.nickname_id,c.trial_flags,*c.equipped,c.polarity,c.selected_command,c.cosmetic_seed)
 b[4000:4005]=bytes(s.roster.party)+bytes([s.roster.selected_party]);b[4008:4012]=s.roster.next_instance_id.to_bytes(4,'little')
 q=s.quests;b[4032:4296]=bytes(q.states)+b''.join(x.to_bytes(2,'little') for x in q.objectives)+bytes(q.rewards)+bytes(q.variables)+bytes(q.region_flags)+bytes(q.anchors)
 b[4296:4536]=bytes(s.roster.expedition_bond)+bytes(s.roster.expedition_events)+bytes(s.roster.lifetime_field_aid)
 for i,r in enumerate(s.equipment.bag):b[4544+i*8:4552+i*8]=struct.pack('<H6B',r.item_id,r.rank,r.flags,r.quantity,*r.reserved)
 e=s.equipment;b[4928:5056]=bytes(e.equipped)+bytes(e.settings_reserved)+bytes(e.seen)+bytes(e.wallet_key_reserved)+bytes(e.reward_claims)+bytes(e.reserved)
 if revision==1:b[4032:4296]=bytes(264);b[4544:5056]=bytes(512)
 return bytes(repair_crc(b))

class ReturnSpawnTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='underwater-return-spawns-');cls.addClassCleanup(cls.tmp.cleanup);folder=Path(cls.tmp.name)
  cls.lib=configure(build(folder/'current'));cls.oracle=history_build(ORACLE,folder/'oracle');cls.checks=0;cls.failed=False
  s=Save();assert cls.lib.underwater_test_earned34(C.byref(s))==0;cls.old=bytes(s)
  # Keep testing the current writer, but independently seed raw legacy cases
  # from a real old bank. Relabeling revision11 retains an invalid used-size.
  assert cls.lib.save5_store(C.byref(s))==1;latest=max((A,B),key=lambda p:int.from_bytes(bytes(cls.lib.sram[p+8:p+12]),'little'));cls.current_template=bytes(cls.lib.sram[latest:latest+SIZE])
  cls.template=historical_template()
  assert cls.lib.underwater_test_completed(C.byref(s),0)==0
  for room in (46,47):assert cls.lib.underwater_anchor(C.byref(s),room)==1
  s.quests.anchors[3]=3;cls.complete=bytes(s)
 def tearDown(self):
  result=self._outcome.result
  if any(test is self for test,_ in result.failures+result.errors):self.__class__.failed=True
 @classmethod
 def tearDownClass(cls):
  report={'result':'FAIL' if cls.failed else 'PASS','scope':'Retained r6 landings under current-r7 reciprocal return spawn codec/current/preflight checks only; world collision and native journeys are separate','checks':cls.checks,'source_sha256':cls.lib._source_hashes,'source_unchanged_during_measurement':cls.lib._source_hashes==runtime_hashes(),'fixture_sha256':FIXTURE_SHA,'new_landings':{'38:4':'requires Underwater town visit','46:3':'ordinary return','48:2':'ordinary return','51:2':'ordinary return with main prefix1','52:2':'ordinary return with main prefix3'},'anchor_spawns':['46:2','47:2'],'old_revisions':'unchanged; all1..5 reject38:4'}
  report['raw_template']={'fixture':str(TEMPLATE_FIXTURE.relative_to(ROOT)),'fixture_sha256':TEMPLATE_SHA,'bank_sha256':hashlib.sha256(cls.template).hexdigest(),'content_revision':6,'source':'Authenticated controller-only retained SRAM; current writer is not used as a historical template'}
  (ROOT/'build/current-host-evidence/underwater-return-spawns/host.json').write_text(json.dumps(report,indent=2)+'\n')
 def clone(self,complete=True):return Save.from_buffer_copy(self.complete if complete else self.old)
 def test_current_writer_cannot_be_relabelled_as_historical_template(self):
  self.assertEqual(int.from_bytes(self.current_template[12:14],'little'),11)
  self.assertEqual(int.from_bytes(self.current_template[6:8],'little'),5088)
  self.assertEqual(int.from_bytes(self.template[6:8],'little'),5056)
  bank=encode_state(self.current_template,self.clone(),6)
  self.lib.save5_test_reset_writer();self.lib.sram[:]=bytes([255])*32768;self.lib.sram[A:A+SIZE]=bank
  out=Save();self.assertEqual(self.lib.save5_load(C.byref(out)),0)
 def assert_state(self,s,expected,raw=True):
  lib=self.lib;before=bytes(s);lib.save5_test_reset_writer();lib.save5_test_fail_after(-1)
  self.assertEqual(lib.save5_validate(C.byref(s)),expected,(s.campaign.room,s.campaign.spawn))
  self.assertEqual(lib.save5_validate_revision(C.byref(s),6),expected)
  token=lib.save5_preflight_begin(C.byref(s));self.assertTrue(token)
  for _ in range(180):
   result=lib.save5_preflight_step(token,640)
   if result!=BUSY:break
  self.assertEqual(result,DONE if expected else FAILED);lib.save5_preflight_cancel();self.assertEqual(bytes(s),before)
  if raw:
   bank=encode_state(self.template,s)
   for offset in (A,B):
    lib.save5_test_reset_writer();lib.save5_test_fail_after(-1);lib.sram[:]=bytes([255])*32768;lib.sram[offset:offset+SIZE]=bank
    prior=bytes(lib.sram);out=Save.from_buffer_copy(bytes([0x91])*C.sizeof(Save));out_before=bytes(out)
    self.assertEqual(lib.save5_load(C.byref(out)),expected,(offset,s.campaign.room,s.campaign.spawn))
    if expected:self.assertEqual(compare_state(out),compare_state(s))
    else:self.assertEqual(bytes(out),out_before)
    self.assertEqual(bytes(lib.sram),prior);self.assertEqual(lib.save5_test_write_count(),0)
  self.__class__.checks+=1
 def test_every_spawn_byte_and_unsupported_holes(self):
  masks={38:31,39:15,40:1,41:1,42:1,43:1,44:1,45:1,46:15,47:7,48:7,49:3,50:3,51:7,52:7,53:3,14:0,15:0,54:0,255:0}
  for room,mask in masks.items():
   for spawn in range(256):
    s=self.clone();s.campaign.room=room;s.campaign.spawn=spawn;self.assert_state(s,int(spawn<8 and bool(mask&(1<<spawn))))
 def test_ordinary_return_spawns_do_not_borrow_anchor_permission(self):
  for room,spawn in ((46,3),(48,2),(51,2),(52,2)):
   s=self.clone();s.quests.anchors[4]=0;s.campaign.room=room;s.campaign.spawn=spawn;self.assert_state(s,1)
  for room in (46,47):
   s=self.clone();s.campaign.room=room;s.campaign.spawn=2;s.quests.anchors[4]=0;self.assert_state(s,0)
   s.quests.anchors[4]=1<<(room-46);self.assert_state(s,1)
 def test_magma_return_requires_real_underwater_visit_in_revision6_only(self):
  s=self.clone(False);s.campaign.room=38;s.campaign.spawn=4;self.assert_state(s,0)
  s.campaign.spawn=0;self.assertEqual(self.lib.underwater_visit(C.byref(s),46),1);s.campaign.spawn=4;self.assert_state(s,1)
  # Old Magma anchor cannot substitute for the new room's visit.
  s.quests.region_flags[4]=0;s.quests.anchors[3]=3;self.assert_state(s,0)
  for rev in range(1,6):
   s=self.clone(False);s.campaign.room=38;s.campaign.spawn=4;bank=encode_state(self.template,s,rev)
   out=Save();self.assertEqual(self.oracle.history_probe_bank(bank,A,C.byref(out)),0)
   self.lib.save5_test_reset_writer();self.lib.sram[:]=bytes([255])*32768;self.lib.sram[A:A+SIZE]=bank
   self.assertEqual(self.lib.save5_load(C.byref(out)),0);self.assertEqual(self.lib.save5_validate_revision(C.byref(s),rev),0);self.__class__.checks+=1
 def test_return_routes_keep_teaching_prefix_source_and_visit_gates(self):
  for room,spawn in ((46,3),(48,2),(51,2),(52,2)):
   s=self.clone();s.campaign.room=room;s.campaign.spawn=spawn;s.quests.region_flags[4]&=~(1<<(room-46));self.assert_state(s,0)
  for room in (51,52):
   for quest in (38,39):
    s=self.clone();s.campaign.room=room;s.campaign.spawn=2
    self.lib.save5_quest_set_state(C.byref(s.quests),quest,2);s.quests.rewards[quest>>3]&=~(1<<(quest&7));self.assert_state(s,0)
  # Minimal synthetic route with no late-room visits masks the exact prefix.
  s=self.clone(False);self.assertEqual(self.lib.underwater_visit(C.byref(s),46),1)
  for q in (38,39):self.assertEqual(self.lib.underwater_test_ready(C.byref(s),q),0);self.assertEqual(self.lib.underwater_quest_claim(C.byref(s),q),3)
  self.assertEqual(self.lib.underwater_quest_offer(C.byref(s),40),1)
  s.quests.region_flags[4]|=32;s.campaign.room=51;s.campaign.spawn=2;self.assert_state(s,0)
  s.quests.objectives[40]=1;self.assert_state(s,1)
  s.quests.region_flags[4]|=64;s.campaign.room=52;self.assert_state(s,0)
  s.quests.objectives[40]=3;self.assert_state(s,1)
  # A saved ordinary return grants no first-family/source/history exemption.
  t=self.clone();t.campaign.room=48;t.campaign.spawn=2;t.quests.region_flags[10]&=~1;self.assert_state(t,0)
  t=self.clone();t.campaign.room=51;t.campaign.spawn=2
  for form in (67,68,69):t.roster.obtained[(form-1)>>3]&=~(1<<((form-1)&7))
  self.assert_state(t,0)
 def test_new_return_writer_roundtrips_and_invalid_begin_never_writes(self):
  lib=self.lib
  for room,spawn in ((38,4),(46,3),(48,2),(51,2),(52,2)):
   s=self.clone();s.campaign.room=room;s.campaign.spawn=spawn
   for budget in (1,640,1024):
    lib.save5_test_reset_writer();lib.save5_test_fail_after(-1)
    self.assertEqual(lib.save5_begin(C.byref(s)),1)
    while lib.save5_status()==BUSY:lib.save5_step(budget)
    self.assertEqual(lib.save5_status(),DONE);out=Save();self.assertEqual(lib.save5_load(C.byref(out)),1);self.assertEqual(compare_state(out),compare_state(s));self.__class__.checks+=1
   # Persisted visit is a causal guard, including on otherwise valid room38.
   s.quests.region_flags[4]&=~(1 if room==38 else 1<<(room-46));before=bytes(lib.sram);writes=lib.save5_test_write_count()
   if lib.save5_begin(C.byref(s)):
    while lib.save5_status()==BUSY:lib.save5_step(1024)
   self.assertEqual(lib.save5_status(),FAILED);self.assertEqual(bytes(lib.sram),before);self.assertEqual(lib.save5_test_write_count(),writes)
 def test_focused_return_checkpoints_every_cut_both_destinations(self):
  lib=self.lib
  for index,(room,spawn) in enumerate(((38,4),(51,2))):
   old=self.clone();old.campaign.room=46;old.campaign.spawn=3;new=Save.from_buffer_copy(bytes(old));new.campaign.room=room;new.campaign.spawn=spawn
   lib.save5_test_reset_writer();lib.save5_test_fail_after(-1);lib.sram[:]=bytes([255])*32768;self.assertEqual(lib.save5_store(C.byref(old)),1)
   if index:self.assertEqual(lib.save5_store(C.byref(old)),1)
   before=bytes(lib.sram);kept=B if index else A;oldkey=compare_state(old);newkey=compare_state(new)
   for cut in range(SIZE+2):
    lib.save5_test_reset_writer();lib.save5_test_fail_after(cut);lib.sram[:]=before
    result=lib.save5_store(C.byref(new));self.assertEqual(result,int(cut>=SIZE+1),(room,spawn,cut));out=Save();self.assertEqual(lib.save5_load(C.byref(out)),1)
    self.assertEqual(compare_state(out),newkey if result else oldkey);self.assertEqual(bytes(lib.sram[:A]),before[:A]);self.assertEqual(bytes(lib.sram[kept:kept+SIZE]),before[kept:kept+SIZE]);self.__class__.checks+=1
   lib.save5_test_fail_after(-1)
 def test_unchanged_historical_magma_spawn_matrix(self):
  for room in range(38,46):
   for spawn in range(256):
    s=self.clone(False);s.quests.anchors[3]=3;s.campaign.room=room;s.campaign.spawn=spawn
    bank=encode_state(self.template,s,5);old=Save();current=Save()
    accepted=self.oracle.history_probe_bank(bank,A,C.byref(old))
    self.lib.save5_test_reset_writer();self.lib.sram[:]=bytes([255])*32768;self.lib.sram[A:A+SIZE]=bank
    self.assertEqual(self.lib.save5_load(C.byref(current)),accepted,(room,spawn))
    self.assertEqual(accepted,int(spawn<4 if room<40 else spawn==0))
    if accepted:self.assertEqual(bytes(old),bytes(current))
    self.__class__.checks+=1
if __name__=='__main__':unittest.main(verbosity=2)
