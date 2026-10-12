#!/usr/bin/env python3
"""Recovered real-core economy tests; --full-cuts checks every bank write."""
import ctypes as C,hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from test_save5 import Save,Economy,ROOT,A,B,SIZE,compare_state,repair_crc
BUSY,DONE,FAILED=1,2,3
FULL='--full-cuts' in sys.argv
if FULL:sys.argv.remove('--full-cuts')
class EconomyTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='economy-recovery-');cls.addClassCleanup(cls.tmp.cleanup);out=Path(cls.tmp.name)/'core.so'
  flags=['-fsanitize=undefined','-fno-sanitize-recover=all']if os.environ.get('ECONOMY_SANITIZE')else[]
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-shared','-fPIC',*flags,*[str(ROOT/'src'/n)for n in ('save4.c','save5.c','creatures.c','creature_data.c','equipment.c','equipment_data.c','economy.c')],'-o',str(out)],check=True)
  cls.l=C.CDLL(str(out));cls.ram=(C.c_ubyte*32768).in_dll(cls.l,'save5_test_sram')
  for n in ('save5_validate','save5_begin','save5_store','save5_load','save5_preflight_begin'):getattr(cls.l,n).argtypes=[C.POINTER(Save)]
  cls.l.save5_validate_revision.argtypes=[C.POINTER(Save),C.c_uint]
  cls.l.equipment_purchase.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
  for n in ('economy_begin_purchase','economy_begin_market_purchase','economy_begin_use','economy_begin_claim','economy_award_combat'):getattr(cls.l,n).argtypes=[C.POINTER(Save),C.c_uint]
  cls.l.save5_test_fail_after.argtypes=[C.c_int]
 def setUp(self):
  self.l.save5_test_reset_writer()
  if self.l.economy_pending():self.l.economy_step();self.l.economy_cancel()
  self.l.save5_preflight_cancel();self.l.save5_test_fail_after(-1);self.l.save5_test_corrupt_write(-1,0);self.ram[:]=bytes([255])*32768
 def fresh(self,chapter=0,gold=0):
  s=Save();s.campaign.chapter_flags=chapter
  if chapter&1:s.campaign.story_seen=2
  if chapter&2:s.campaign.story_seen|=8
  if chapter&4:s.campaign.spawn=3
  self.assertEqual(self.l.creatures_migrate_legacy(C.byref(s.roster),chapter,0),1);self.l.equipment_init(C.byref(s.equipment));self.assertEqual(self.l.save5_validate(C.byref(s)),1)
  self.assertEqual(self.l.economy_award_combat(C.byref(s),gold),min(gold,9999));return s
 def finish(self,s):
  prior=bytes(s)
  for _ in range(400):
   status=self.l.economy_step()
   if status!=BUSY:return status
   self.assertEqual(bytes(s),prior)
  self.fail('Unbounded transaction')
 def job(self,s,fn,item):
  self.assertEqual(getattr(self.l,fn)(C.byref(s),item),1);self.assertEqual(self.finish(s),DONE);self.assertEqual(self.l.save5_validate(C.byref(s)),1)
 def reload(self):
  s=Save();self.assertEqual(self.l.save5_load(C.byref(s)),1);return s
 def fixture(self):
  row=json.loads((ROOT/'tests/fixtures/v5-revision9/provenance.json').read_text())['fixtures'][0];b=(ROOT/row['path']).read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),row['sha256']);return b
 def test_newgame_bounds_no_free_ownership(self):
  s=self.fresh();self.assertEqual(C.sizeof(Economy),32);self.assertEqual(bytes(s.economy),bytes(32));before=bytes(s)
  self.assertEqual(self.l.economy_begin_purchase(C.byref(s),0),0);self.assertEqual(self.l.economy_last_error(),3);self.assertEqual(self.l.economy_begin_claim(C.byref(s),0),0);self.assertEqual(bytes(s),before)
  self.assertEqual(self.l.economy_award_combat(C.byref(s),0xffffffff),9999);self.assertEqual(self.l.economy_award_combat(C.byref(s),0xffffffff),0)
  self.assertEqual(self.l.save5_store(C.byref(s)),1);self.assertEqual(compare_state(self.reload()),compare_state(s))
 def test_purchase_use_upgrade_reload(self):
  s=self.fresh(gold=200);gear=bytes(s.equipment)
  for item in range(3):self.job(s,'economy_begin_purchase',item)
  self.assertEqual((s.economy.gold,s.economy.upgrade),(38,1));self.assertEqual(self.l.economy_attack_bonus(C.byref(s)),1)
  self.assertEqual(self.l.economy_begin_purchase(C.byref(s),2),0);self.assertEqual(self.l.economy_last_error(),5)
  for item in range(2):self.job(s,'economy_begin_use',item)
  self.assertEqual(self.l.economy_begin_use(C.byref(s),0),0);self.assertEqual(self.l.economy_last_error(),7);self.assertEqual(bytes(s.equipment),gear);self.assertEqual(compare_state(self.reload()),compare_state(s))
  bank=bytes(self.ram[A:A+SIZE]);self.assertEqual(bank[6:8],(5088).to_bytes(2,'little'));self.assertEqual(bank[12:14],b'\x0c\0')
 def test_content12_receipts_keep_revision11_wallet_exact(self):
  s=self.fresh(1,gold=200);s.quests.region_flags[0]=1
  self.assertEqual(self.l.save5_validate_revision(C.byref(s),11),1)
  self.assertEqual(self.l.save5_store(C.byref(s)),1);prior=bytearray(self.ram[A:A+SIZE])
  prior[12:14]=(11).to_bytes(2,'little');prior=repair_crc(prior)
  self.ram[A:A+SIZE]=prior
  ref=C.c_uint();self.assertEqual(self.l.equipment_purchase(C.byref(s.equipment),2,C.byref(ref)),0)
  s.economy.reserved[0]=1;s.economy.spent=96;s.economy.gold=104
  self.assertEqual(self.l.save5_validate_revision(C.byref(s),12),1)
  self.assertEqual(self.l.save5_validate_revision(C.byref(s),11),0)
  self.assertEqual(self.l.save5_store(C.byref(s)),1);self.assertEqual(compare_state(self.reload()),compare_state(s))
  purchased=bytearray(self.ram[B:B+SIZE]);self.assertEqual(purchased[5080],1)
  purchased[12:14]=(11).to_bytes(2,'little');purchased=repair_crc(purchased)
  self.ram[B:B+SIZE]=purchased;recovered=self.reload()
  self.assertEqual(recovered.economy.gold,200);self.assertFalse(recovered.economy.reserved[0])
  self.assertEqual(self.l.equipment_find(C.byref(recovered.equipment),2),255)
  self.ram[:]=bytes([255])*32768;self.ram[A:A+SIZE]=purchased
  self.assertEqual(self.l.save5_load(C.byref(Save())),0)
 def test_paid_gear_requires_visited_source_and_unique_seen_history(self):
  s=self.fresh(1,gold=200);s.economy.reserved[0]=1;s.economy.spent=96;s.economy.gold=104
  self.assertEqual(self.l.save5_validate(C.byref(s)),0)
  self.assertEqual(self.l.equipment_purchase(C.byref(s.equipment),2,None),0)
  self.assertEqual(self.l.save5_validate(C.byref(s)),0)
  s.quests.region_flags[0]=1;self.assertEqual(self.l.save5_validate(C.byref(s)),1)
  before=bytes(s.equipment);self.assertEqual(self.l.equipment_purchase(C.byref(s.equipment),2,None),5)
  self.assertEqual(bytes(s.equipment),before)
  self.assertEqual(self.l.equipment_claim(C.byref(s.equipment),2,1,None),5)
  self.assertEqual(sum(x.item_id==2 for x in s.equipment.bag),1)
 def test_inspected_story_mask_is_revision12_and_prerequisite_scoped(self):
  s=self.fresh();s.economy.reserved[1]=1;self.assertEqual(self.l.save5_validate(C.byref(s)),0)
  s=self.fresh(1);s.economy.reserved[1]=1;self.assertEqual(self.l.save5_validate(C.byref(s)),1)
  self.assertEqual(self.l.save5_validate_revision(C.byref(s),11),0)
  s.economy.reserved[1]=2;self.assertEqual(self.l.save5_validate(C.byref(s)),0)
  s=self.fresh(3);s.economy.reserved[1]=3;self.assertEqual(self.l.save5_validate(C.byref(s)),1)
  self.assertEqual(self.l.save5_store(C.byref(s)),1);self.assertEqual(compare_state(self.reload()),compare_state(s))
  s.economy.reserved[1]=4;self.assertEqual(self.l.save5_validate(C.byref(s)),0)
 def test_old_bosses_explicit_one_time_no_reload_gain(self):
  s=self.fresh(7);self.assertEqual(self.l.economy_claimable(C.byref(s)),7)
  for boss,gold in enumerate((60,160,320)):
   self.job(s,'economy_begin_claim',boss);self.assertEqual(s.economy.gold,gold);s=self.reload();before=bytes(s)
   self.assertEqual(self.l.economy_begin_claim(C.byref(s),boss),0);self.assertEqual(bytes(s),before)
  self.assertEqual((self.l.economy_heart_bonus(C.byref(s)),self.l.economy_power_reduction(C.byref(s)),self.l.economy_attack_bonus(C.byref(s))),(1,8,1));self.assertEqual(self.l.economy_claimable(C.byref(s)),0)
 def test_shop_capacity_location_identity_and_changed_source(self):
  s=self.fresh(gold=1000)
  for _ in range(9):self.job(s,'economy_begin_purchase',0)
  self.assertEqual(self.l.economy_begin_purchase(C.byref(s),0),0);self.assertEqual(self.l.economy_last_error(),4)
  for item in (3,255,0xffffffff):self.assertEqual(self.l.economy_begin_purchase(C.byref(s),item),0)
  s.campaign.room=1;self.assertEqual(self.l.economy_begin_purchase(C.byref(s),1),0);self.assertEqual(self.l.economy_last_error(),10);s.campaign.room=0
  self.assertEqual(self.l.economy_begin_purchase(C.byref(s),1),1);self.assertEqual(self.l.economy_begin_purchase(C.byref(s),1),0);self.assertEqual(self.l.economy_award_combat(C.byref(s),10),0)
  s.roster.instances[0].cosmetic_seed+=1;self.assertEqual(self.finish(s),FAILED);self.assertEqual(self.l.economy_last_error(),9)
 def test_cancel_revoked_owner_does_not_cancel_new_owner(self):
  s=self.fresh(gold=50);self.assertEqual(self.l.save5_store(C.byref(s)),1)
  self.assertEqual(self.l.economy_begin_purchase(C.byref(s),0),1);self.assertEqual(self.l.economy_cancel(),1);self.assertEqual(s.economy.gold,50)
  self.assertEqual(self.l.economy_begin_purchase(C.byref(s),0),1);out=self.reload();token=self.l.save5_preflight_begin(C.byref(out));self.assertTrue(token)
  self.assertEqual(self.l.economy_step(),FAILED);self.assertEqual(self.l.save5_preflight_status(token),BUSY)
  while self.l.save5_preflight_step(token,480)==BUSY:pass
  self.assertEqual(self.l.save5_preflight_status(token),DONE);self.l.save5_preflight_cancel()
 def test_invalid_extension_rejected_before_writes(self):
  s=self.fresh();self.assertEqual(self.l.save5_store(C.byref(s)),1);initial=bytes(self.ram)
  for pos in range(32):
   bad=Save.from_buffer_copy(bytes(s));raw=(C.c_ubyte*32).from_buffer(bad.economy);raw[pos]=255
   self.assertEqual(self.l.save5_validate(C.byref(bad)),0,pos);self.l.save5_test_reset_writer();self.l.save5_test_fail_after(-1)
   self.assertEqual(self.l.save5_store(C.byref(bad)),0,pos);self.assertEqual(self.l.save5_test_write_count(),0);self.assertEqual(bytes(self.ram),initial)
  for pos in range(5056,5088):
   b=bytearray(initial[A:A+SIZE]);b[pos]=255;b=repair_crc(b);self.l.save5_test_reset_writer();self.ram[:]=bytes([255])*32768;self.ram[A:A+SIZE]=b
   self.assertEqual(self.l.save5_load(C.byref(Save())),0,pos)
 def test_full48_gear160_creatures_preserved(self):
  self.ram[:]=self.fixture();s=self.reload();self.assertEqual(sum(bool(x.item_id)for x in s.equipment.bag),48)
  template=type(s.roster.instances[0]).from_buffer_copy(bytes(s.roster.instances[0]));template.flags=1
  for i in range(160):
   if not s.roster.instances[i].form_id:s.roster.instances[i]=template;s.roster.instances[i].instance_id=s.roster.next_instance_id;s.roster.next_instance_id+=1
  self.assertEqual(self.l.save5_validate(C.byref(s)),1);s.campaign.room=0;s.campaign.spawn=3;self.l.economy_award_combat(C.byref(s),200);roster,gear=bytes(s.roster),bytes(s.equipment)
  self.job(s,'economy_begin_purchase',0);self.job(s,'economy_begin_purchase',2);self.assertEqual((bytes(s.roster),bytes(s.equipment)),(roster,gear));self.assertEqual(compare_state(self.reload()),compare_state(s))
 def test_purchase_claim_powercuts_and_corruptions_atomic(self):
  for fn,item,original in [('economy_begin_purchase',0,self.fresh(gold=200)),('economy_begin_claim',2,self.fresh(7))]:
   for destination in ('A','B'):
    self.l.save5_test_reset_writer();self.l.save5_test_fail_after(-1);self.ram[:]=bytes([255])*32768;self.assertEqual(self.l.save5_store(C.byref(original)),1)
    if destination=='A':self.assertEqual(self.l.save5_store(C.byref(original)),1)
    initial=bytes(self.ram);preserved=B if destination=='A'else A;expected=Save.from_buffer_copy(bytes(original));self.job(expected,fn,item)
    cuts=range(SIZE+2)if FULL else (0,1,2,31,32,160,4000,4032,4544,4928,5024,*range(5055,5090),6143,6144,6145)
    for cut in cuts:
     self.l.save5_test_reset_writer();self.l.save5_test_fail_after(cut);self.ram[:]=initial;live=Save.from_buffer_copy(bytes(original));self.assertEqual(getattr(self.l,fn)(C.byref(live),item),1)
     status=self.finish(live);self.assertEqual(status,DONE if cut>=6145 else FAILED,(fn,destination,cut));out=self.reload();want=expected if status==DONE else original
     self.assertEqual(compare_state(live),compare_state(want));self.assertEqual(compare_state(out),compare_state(want));self.assertEqual(bytes(self.ram[:A]),initial[:A]);self.assertEqual(bytes(self.ram[preserved:preserved+SIZE]),initial[preserved:preserved+SIZE])
    for corrupt in (0,1,32,160,4032,4544,*range(5056,5088),6144):
     self.l.save5_test_reset_writer();self.l.save5_test_fail_after(-1);self.l.save5_test_corrupt_write(corrupt,1);self.ram[:]=initial;live=Save.from_buffer_copy(bytes(original));self.assertEqual(getattr(self.l,fn)(C.byref(live),item),1)
     self.assertEqual(self.finish(live),FAILED);self.l.save5_test_corrupt_write(-1,0);self.assertEqual(compare_state(self.reload()),compare_state(original));self.assertEqual(compare_state(live),compare_state(original))
    self.l.save5_test_fail_after(-1)
 def test_first_revision9_claim_migrates_at_commit_only(self):
  initial=self.fixture();self.ram[:]=initial;original=self.reload();original.campaign.room=0;original.campaign.spawn=3;self.assertEqual(bytes(original.economy),bytes(32));expected=Save.from_buffer_copy(bytes(original));self.job(expected,'economy_begin_claim',0)
  for cut in (0,1,32,4544,5024,*range(5055,5089),6144,6145):
   self.l.save5_test_reset_writer();self.l.save5_test_fail_after(cut);self.ram[:]=initial;live=Save.from_buffer_copy(bytes(original));self.assertEqual(self.l.economy_begin_claim(C.byref(live),0),1);status=self.finish(live);out=self.reload()
   self.assertEqual(status,DONE if cut>=6145 else FAILED);self.assertEqual(bytes(out.economy),bytes(expected.economy)if status==DONE else bytes(32))
   self.assertEqual((bytes(out.roster),bytes(out.quests),bytes(out.equipment)),(bytes(original.roster),bytes(original.quests),bytes(original.equipment)))
  self.l.save5_test_fail_after(-1)
 def test_background_preemption_every512_step_boundary(self):
  old=self.fresh(gold=20);new=self.fresh(gold=40);self.assertEqual(self.l.save5_store(C.byref(old)),1);initial=bytes(self.ram);counts=[0,0];done=False
  for boundary in range(250):
   self.l.save5_test_reset_writer();self.ram[:]=initial;self.assertEqual(self.l.save5_begin(C.byref(new)),1);self.l.save5_set_preemptible(1)
   for _ in range(boundary):
    if self.l.save5_step(512)!=BUSY:break
   if self.l.save5_status()==DONE:done=True;break
   token=self.l.save5_preflight_begin(C.byref(new));self.assertTrue(token);self.assertEqual(self.l.save5_take_preempted(),1);self.assertEqual(self.l.save5_take_preempted(),0)
   while self.l.save5_preflight_step(token,480)==BUSY:pass
   self.assertEqual(self.l.save5_preflight_status(token),DONE);self.l.save5_preflight_cancel();out=self.reload();self.assertIn(compare_state(out),(compare_state(old),compare_state(new)));counts[int(out.economy.gold==40)]+=1;self.assertEqual(bytes(self.ram[A:A+SIZE]),initial[A:A+SIZE])
  self.assertTrue(done);self.assertTrue(all(counts))
 def test_critical_writer_cannot_be_preempted(self):
  s=self.fresh(gold=50);self.assertEqual(self.l.economy_begin_purchase(C.byref(s),0),1)
  for _ in range(100):
   self.assertEqual(self.l.economy_step(),BUSY)
   if self.l.save5_status()==BUSY:break
  self.assertEqual(self.l.save5_status(),BUSY);self.l.save5_set_preemptible(1);self.assertEqual(self.l.save5_cancel_background(),0);self.assertEqual(self.l.economy_cancel(),0);self.assertEqual(self.l.save5_preflight_begin(C.byref(s)),0);self.assertEqual(self.finish(s),DONE)
 def market_fresh(self,gold=1000):
  s=self.fresh(1,gold);s.quests.region_flags[0]=1;s.campaign.room=16;s.campaign.spawn=0
  self.assertEqual(self.l.save5_validate(C.byref(s)),1);return s
 def test_regional_stock_access_and_existing_supply_history(self):
  s=self.market_fresh();before=bytes(s)
  self.assertEqual(self.l.economy_begin_purchase(C.byref(s),0),0)
  self.assertEqual(self.l.economy_begin_market_purchase(C.byref(s),4),0)
  self.assertEqual(bytes(s),before)
  self.job(s,'economy_begin_market_purchase',0)
  self.assertEqual((s.economy.gold,s.economy.bought[0],s.economy.supplies[0]),(982,1,1))
  self.job(s,'economy_begin_market_purchase',3)
  self.assertEqual((s.economy.gold,s.economy.spent,s.economy.reserved[0]),(886,114,1))
  self.assertEqual(s.equipment.reward_claims[0]&2,0)
  self.assertEqual(sum(x.item_id==2 for x in s.equipment.bag),1)
  self.assertEqual(compare_state(self.reload()),compare_state(s))
  before=bytes(s);self.assertEqual(self.l.economy_begin_market_purchase(C.byref(s),3),0)
  self.assertEqual(self.l.economy_last_error(),5);self.assertEqual(bytes(s),before)
 def test_regional_gear_failure_and_powercuts_keep_old_or_complete_purchase(self):
  original=self.market_fresh();self.assertEqual(self.l.save5_store(C.byref(original)),1);initial=bytes(self.ram)
  expected=Save.from_buffer_copy(bytes(original));self.job(expected,'economy_begin_market_purchase',3)
  for cut in (0,1,32,160,4000,4544,5024,5056,5079,5080,5081,5087,5088,6143,6144,6145):
   self.l.save5_test_reset_writer();self.l.save5_test_fail_after(cut);self.ram[:]=initial
   live=Save.from_buffer_copy(bytes(original));self.assertEqual(self.l.economy_begin_market_purchase(C.byref(live),3),1)
   status=self.finish(live);want=expected if status==DONE else original
   self.assertEqual(status,DONE if cut>=6145 else FAILED)
   self.assertEqual(compare_state(live),compare_state(want));self.assertEqual(compare_state(self.reload()),compare_state(want))
  self.l.save5_test_fail_after(-1)
 def test_regional_gear_rejects_changed_owner_and_quest_duplicate_remains_unique(self):
  s=self.market_fresh();self.assertEqual(self.l.save5_store(C.byref(s)),1);old=bytes(s)
  self.assertEqual(self.l.economy_begin_market_purchase(C.byref(s),3),1)
  s.roster.instances[0].cosmetic_seed+=1;self.assertEqual(self.finish(s),FAILED)
  self.assertEqual(s.economy.gold,1000);self.assertEqual(sum(x.item_id==2 for x in s.equipment.bag),0)
  self.assertEqual(bytes(self.reload().equipment),bytes(Save.from_buffer_copy(old).equipment))
  s=self.market_fresh();self.job(s,'economy_begin_market_purchase',3)
  self.assertEqual(self.l.equipment_claim(C.byref(s.equipment),2,1,None),5)
  self.assertEqual(sum(x.item_id==2 for x in s.equipment.bag),1)
  self.assertEqual(s.economy.reserved[0],1)
 def test_all_eight_paid_receipts_roundtrip_with_existing_completed_history(self):
  self.ram[:]=self.fixture();s=self.reload();self.l.economy_award_combat(C.byref(s),3000)
  s.economy.reserved[0]=255;s.economy.spent=sum((96,144,180,216,252,288,324,360));s.economy.gold=s.economy.earned-s.economy.spent
  self.assertEqual(self.l.save5_validate(C.byref(s)),1)
  self.assertEqual(self.l.save5_store(C.byref(s)),1);self.assertEqual(compare_state(self.reload()),compare_state(s))
  s.economy.spent+=1;s.economy.gold-=1;self.assertEqual(self.l.save5_validate(C.byref(s)),0)
if __name__=='__main__':unittest.main(verbosity=2)
