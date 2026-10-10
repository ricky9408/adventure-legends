#!/usr/bin/env python3
"""Exact H source oracle against content8; all mutations are host-only evidence."""
import ctypes as C,hashlib,json,random,tempfile,unittest
from pathlib import Path
from test_save5 import ROOT,Save,Instance,A,B,SIZE,repair_crc,compare_state
from test_return_history_differential import build,erase_live_tables
from test_return_history_core import TABLE_HARNESS
ORACLE=ROOT/'tests/fixtures/return-h-policy-oracle'
FIXTURES=ROOT/'tests/fixtures/v5-revision7'
class HorizonsHistory(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='horizons-history-');cls.addClassCleanup(cls.tmp.cleanup);root=Path(cls.tmp.name)
  raw=(ORACLE/'manifest.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='1a5a74ad82a2856224118b0aaebe1e63bed9ec0e9c83f9b90772fa0cad80a3d9'
  manifest=json.loads(raw)
  assert manifest['source_rom_sha256']=='f2330562b2c370d094164e7a5bf1e307da24412c88280cc880744eba072edaec'
  for name,sha in manifest['files'].items():assert hashlib.sha256((ORACLE/name).read_bytes()).hexdigest()==sha,name
  cls.old=build(ORACLE,root/'old',extra_harness=TABLE_HARNESS);cls.new=build(ROOT,root/'new',extra_harness=TABLE_HARNESS);cls.erased=build(ROOT,root/'erased',erase_live_tables,TABLE_HARNESS)
  cls.images=[]
  for row in json.loads((FIXTURES/'provenance.json').read_text())['fixtures']:
   data=(FIXTURES/row['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'];assert row['controller_only'] and row['game_ram_writes']==0 and row['machine_state_loads']==0
   cls.images.append((row['file'],data))
  for lib in (cls.old,cls.new,cls.erased):
   lib.creatures_instance_validate_revision.argtypes=[C.POINTER(Instance),C.c_uint]
   lib.creatures_trial_allowed_mask.argtypes=[C.c_uint,C.c_uint]
   lib.creatures_family_revision.argtypes=[C.c_uint,C.c_uint]
   lib.history_mask_table.argtypes=[C.POINTER(Instance),C.c_uint,C.c_void_p]
   lib.history_command_table.argtypes=[C.c_uint,C.c_uint,C.c_void_p]
   lib.history_instance_byte_table.argtypes=[C.POINTER(Instance),C.c_uint,C.c_void_p]
  cls.base=Save();assert cls.old.history_probe_image(cls.images[0][1],C.byref(cls.base))==1
 def test_exact_h_import_and_explicit_content8_save_no_gain(self):
  for name,data in self.images:
   outputs=[]
   for lib in (self.old,self.new,self.erased):
    out=Save();self.assertEqual(lib.history_probe_image(data,C.byref(out)),1,name);outputs.append(bytes(out))
   self.assertEqual(outputs[0],outputs[1]);self.assertEqual(outputs[0],outputs[2])
   s=Save.from_buffer_copy(outputs[1]);before=compare_state(s);encoded=(C.c_ubyte*SIZE)()
   self.assertEqual(self.new.history_encode(C.byref(s),encoded),1);self.assertEqual(bytes(encoded)[12:14],b'\x0b\0')
   self.assertEqual(self.old.history_probe_bank(encoded,A,C.byref(Save())),0)
   out=Save();self.assertEqual(self.new.history_probe_bank(encoded,B,C.byref(out)),1);self.assertEqual(compare_state(out),before)
   self.assertEqual(bytes(out.quests.region_flags[6:8]),bytes(2));self.assertEqual(bytes(out.quests.region_flags[12:16]),bytes(4));self.assertEqual(bytes(out.quests.anchors[6:]),bytes(10))
 def test_recorded7_lookups_and_individuals_independent_of_live8(self):
  for form in range(257):
   for lib in (self.new,self.erased):
    self.assertEqual(lib.creatures_trial_allowed_mask(form,7),self.old.creatures_trial_allowed_mask(form,7),form)
    self.assertEqual(lib.creatures_family_revision(form,7),self.old.creatures_family_revision(form,7),form)
  rng=random.Random(7048)
  for original in self.base.roster.instances:
   if not original.form_id:continue
   for k in range(160):
    c=Instance.from_buffer_copy(bytes(original));raw=(C.c_ubyte*C.sizeof(c)).from_buffer(c)
    if k<16:c.trial_flags=1<<k
    elif k<66:c.level=k-15;c.xp=self.new.creatures_xp_threshold(c.level)
    else:raw[rng.randrange(len(raw))]=rng.randrange(256)
    expected=self.old.creatures_instance_validate_revision(C.byref(c),7)
    for lib in (self.new,self.erased):self.assertEqual(lib.creatures_instance_validate_revision(C.byref(c),7),expected,(original.form_id,k))
 def test_every104_form_trial_mask_and_command_level_table(self):
  rows=json.loads((ROOT/'assets/history/creatures-v7.json').read_text())['forms']
  for row in rows:
   c=Instance();c.form_id=row['id'];c.flags=1;c.instance_id=1;c.level=50;c.xp=470596;c.bond=100;c.polarity=row['polarity'];c.equipped[0]=row['learn'][0][1];c.trial_flags=row['trial_mask']
   for method,args,n in [('history_mask_table',(C.byref(c),7),65536),('history_command_table',(7,row['id']),52*256),('history_instance_byte_table',(C.byref(c),7),24*256)]:
    old=(C.c_ubyte*n)();new=(C.c_ubyte*n)();erased=(C.c_ubyte*n)()
    getattr(self.old,method)(*args,old);getattr(self.new,method)(*args,new);getattr(self.erased,method)(*args,erased)
    self.assertEqual(bytes(old),bytes(new),(row['id'],method));self.assertEqual(bytes(old),bytes(erased),(row['id'],method,'erased'))
 def test_revision7_state_differential_all_authoritative_bytes(self):
  seed=bytes(self.base);rng=random.Random(0x4837)
  offsets=list(range(Save.quests.offset,Save.quests.offset+264))+list(range(Save.equipment.offset,Save.equipment.offset+512))
  offsets+=rng.sample(range(len(seed)),2000)
  for index,pos in enumerate(offsets):
   s=Save.from_buffer_copy(seed);raw=(C.c_ubyte*len(seed)).from_buffer(s);raw[pos]^=(1,2,4,8,16,32,64,128,255)[index%9]
   old=self.old.save5_validate_revision(C.byref(s),7);new=self.new.save5_validate_revision(C.byref(s),7)
   self.assertEqual(new,old,(pos,index));self.assertEqual(bytes(s)[pos],seed[pos]^((1,2,4,8,16,32,64,128,255)[index%9]))
 def test_crc_valid_future_content_rejected_by_both_bank_scanners(self):
  data=self.images[0][1];seed=max((data[x:x+SIZE] for x in (A,B)),key=lambda b:int.from_bytes(b[8:12],'little'))
  # Reserved quests54..63, new visits/receipts/anchors, future form history,
  # future gear seen/claims/records and command identity aliases.
  positions=[4032+q//4 for q in range(54,64)]+list(range(4048+54*2,4048+64*2))+list(range(4176+6,4176+8))+list(range(4184+54,4184+64))+[4248+6,4248+7,*range(4248+12,4248+16),*range(4280+6,4296),96+13,112+13,160+16,4544+52*0,4944+88//8,5024+5]
  for pos in positions:
   for value in (1,15,127,128,255):
    b=bytearray(seed);b[pos]=value;b=bytes(repair_crc(b))
    a=Save();c=Save();x=self.old.history_probe_bank(b,A,C.byref(a));y=self.new.history_probe_bank(b,B,C.byref(c));self.assertEqual(y,x,(pos,value))
    if x:self.assertEqual(bytes(a),bytes(c))
  for form in range(105,129):
   b=bytearray(seed);b[96+(form-1)//8]|=1<<((form-1)%8);b=bytes(repair_crc(b))
   self.assertEqual(self.old.history_probe_bank(b,A,C.byref(Save())),0);self.assertEqual(self.new.history_probe_bank(b,B,C.byref(Save())),0)
 def test_future_credit_bits_remain_nonauthoritative(self):
  s=Save.from_buffer_copy(bytes(self.base));s.roster.expedition_events[38]|=0xf0;s.roster.expedition_events[39]=255;s.roster.expedition_events[40]|=63
  s.roster.lifetime_field_aid[12]|=127
  for lib in (self.old,self.new,self.erased):self.assertEqual(lib.save5_validate_revision(C.byref(s),7),1)
  encoded=(C.c_ubyte*SIZE)();self.assertEqual(self.old.history_encode(C.byref(s),encoded),1);out=Save();self.assertEqual(self.new.history_probe_bank(encoded,A,C.byref(out)),1);self.assertEqual(compare_state(out),compare_state(s))
if __name__=='__main__':unittest.main(verbosity=2)
