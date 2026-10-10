#!/usr/bin/env python3
"""Independent accepted C oracle against current9. No controller claims."""
import ctypes as C,hashlib,json,random,re,tempfile,unittest
from pathlib import Path
from test_save5 import ROOT,Save,Instance,A,B,SIZE,repair_crc,compare_state
from test_return_history_differential import build,erase_live_tables,FIXTURES as EARLY_FIXTURES
from test_return_history_core import TABLE_HARNESS
ORACLE=ROOT/'tests/fixtures/horizons-c-policy-oracle'
MANIFEST_SHA='de5129176b917cc7c3869089a7fd1b12bda6dce5fc2d1ab214867165b68bdeaf'
def poison_current(name,data):
 data=erase_live_tables(name,data)
 if name=='creatures.c':
  text=data.decode()
  for table in ('form_policy','family_policy','ability_policy','form_policy_index','family_policy_index','ability_policy_index'):
   text,n=re.subn(r'(static const \w+ '+table+r'\[[^=]*= )\{.*?\};',r'\1{0};',text,flags=re.S);assert n==1,(table,n)
  data=text.encode()
 if name=='save5.c':
  text=data.decode();text,n=re.subn(r'(static const Save4U8 quest_masks\[64\] = )\{[^}]+\}',r'\1{0}',text);assert n==1
  text,n=re.subn(r'(static const signed char equipment_source_quest\[48\] = )\{[^}]+\}',r'\1{0}',text);assert n==1;data=text.encode()
 if name=='save5_horizons_policy.inc':
  text=data.decode();text,n=re.subn(r'(static const Save4U8 horizons_\w+\[[^=]+?=)\{.*?\};',r'\1{0};',text,flags=re.S);assert n>=5,(name,n);data=text.encode()
 return data
class CovenantsHistory(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='covenants-history-');cls.addClassCleanup(cls.tmp.cleanup);root=Path(cls.tmp.name)
  raw=(ORACLE/'manifest.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==MANIFEST_SHA
  manifest=json.loads(raw);assert manifest['source_rom_sha256']=='4166bdafdba0bf689a8230d6d8d407ae7faf0271925df480b4e3b0aa917f1a91'
  for name,sha in manifest['files'].items():assert hashlib.sha256((ORACLE/name).read_bytes()).hexdigest()==sha,name
  cls.old=build(ORACLE,root/'old',extra_harness=TABLE_HARNESS);cls.new=build(ROOT,root/'new',extra_harness=TABLE_HARNESS);cls.erased=build(ROOT,root/'erased',poison_current,TABLE_HARNESS)
  cls.images=[]
  provenance=json.loads((ROOT/'tests/fixtures/v5-revision8/provenance.json').read_text())
  for row in provenance['fixtures']:
   data=(ROOT/row['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'];cls.images.append((row['path'],data))
  for lib in (cls.old,cls.new,cls.erased):
   lib.creatures_instance_validate_revision.argtypes=[C.POINTER(Instance),C.c_uint]
   lib.history_mask_table.argtypes=[C.POINTER(Instance),C.c_uint,C.c_void_p]
   lib.history_command_table.argtypes=[C.c_uint,C.c_uint,C.c_void_p]
   lib.history_instance_byte_table.argtypes=[C.POINTER(Instance),C.c_uint,C.c_void_p]
  cls.base=Save();assert cls.old.history_probe_image(cls.images[0][1],C.byref(cls.base))==1
 def test_all_genuine8_import_and_explicit9_save_without_gain(self):
  for name,data in self.images:
   outputs=[]
   for lib in (self.old,self.new,self.erased):
    out=Save();self.assertEqual(lib.history_probe_image(data,C.byref(out)),1,name);outputs.append(bytes(out))
   self.assertEqual(outputs[0],outputs[1]);self.assertEqual(outputs[0],outputs[2])
   s=Save.from_buffer_copy(outputs[1]);before=compare_state(s);encoded=(C.c_ubyte*SIZE)();self.assertEqual(self.new.history_encode(C.byref(s),encoded),1)
   self.assertEqual(bytes(encoded)[2],5);self.assertEqual(bytes(encoded)[12:14],b'\x0b\0');self.assertEqual(self.old.history_probe_bank(encoded,A,C.byref(Save())),0)
   out=Save();self.assertEqual(self.new.history_probe_bank(encoded,B,C.byref(out)),1);self.assertEqual(compare_state(out),before)
   self.assertEqual((out.quests.region_flags[7],out.quests.region_flags[22],out.quests.region_flags[23],out.quests.anchors[7]),(0,0,0,0))
   self.assertEqual(list(out.quests.objectives[60:]),[0]*4);self.assertEqual(out.roster.obtained[15],0)
 def test_old1_to7_decode_exactly_unchanged(self):
  images=[(r,n,(ROOT/f'tests/fixtures/v5-revision{r}'/n).read_bytes()) for r,n,_ in EARLY_FIXTURES]
  for row in json.loads((ROOT/'tests/fixtures/v5-revision7/provenance.json').read_text())['fixtures']:images.append((7,row['file'],(ROOT/'tests/fixtures/v5-revision7'/row['file']).read_bytes()))
  for revision,name,data in images:
   outputs=[]
   for l in (self.old,self.new,self.erased):
    out=Save();self.assertEqual(l.history_probe_image(data,C.byref(out)),1,(revision,name));outputs.append(bytes(out));self.assertEqual(l.save5_validate_revision(C.byref(out),revision),1)
   self.assertEqual(outputs[0],outputs[1]);self.assertEqual(outputs[0],outputs[2])
 def test_every120_form_full_trial_mask_commands_levels_and_instance_bytes(self):
  rows=json.loads((ROOT/'assets/history/creatures-v8.json').read_text())['forms'];self.assertEqual(len(rows),120)
  for row in rows:
   c=Instance();c.form_id=row['id'];c.flags=1;c.instance_id=1;c.level=50;c.xp=470596;c.bond=100;c.polarity=row['polarity'];c.equipped[0]=row['learn'][0][1];c.trial_flags=row['trial_mask']
   for method,args,n in [('history_mask_table',(C.byref(c),8),65536),('history_command_table',(8,row['id']),52*256),('history_instance_byte_table',(C.byref(c),8),24*256)]:
    old=(C.c_ubyte*n)();new=(C.c_ubyte*n)();erased=(C.c_ubyte*n)();getattr(self.old,method)(*args,old);getattr(self.new,method)(*args,new);getattr(self.erased,method)(*args,erased)
    self.assertEqual(bytes(old),bytes(new),(row['id'],method));self.assertEqual(bytes(old),bytes(erased),(row['id'],method,'poisoned'))
  for form in range(257):
   for fn in ('creatures_trial_allowed_mask','creatures_family_revision','creatures_legacy_spirit_revision','creatures_form_allowed_revision'):
    expected=getattr(self.old,fn)(form,8)
    for l in (self.new,self.erased):self.assertEqual(getattr(l,fn)(form,8),expected,(fn,form))
 def test_all_state_bytes_differential(self):
  seed=bytes(self.base)
  for pos in range(len(seed)):
   s=Save.from_buffer_copy(seed);raw=(C.c_ubyte*len(seed)).from_buffer(s);raw[pos]^=(1,2,4,8,16,32,64,128,255)[pos%9]
   expected=self.old.save5_validate_revision(C.byref(s),8)
   for l in (self.new,self.erased):self.assertEqual(l.save5_validate_revision(C.byref(s),8),expected,pos)
 def test_crc_valid_future_fields_and_malformed_banks(self):
  data=self.images[0][1];seed=max((data[x:x+SIZE] for x in (A,B)),key=lambda b:int.from_bytes(b[8:12],'little'))
  # Exhaust every byte in campaign, quests, gear; historical revision remains8.
  for pos in (*range(32,47),*range(4032,4296),*range(4544,5056),96+15,112+15,160+16):
   for value in (0,1,3,7,15,31,63,127,128,254,255):
    b=bytearray(seed);b[pos]=value;b=bytes(repair_crc(b));a=Save();expected=self.old.history_probe_bank(b,A,C.byref(a))
    for l in (self.new,self.erased):
     out=Save();self.assertEqual(l.history_probe_bank(b,B,C.byref(out)),expected,(pos,value));self.assertEqual(bytes(out),bytes(a),(pos,value,'decoded'))
  for form in range(121,129):
   b=bytearray(seed);b[96+(form-1)//8]|=1<<((form-1)%8);b=bytes(repair_crc(b))
   for l in (self.old,self.new,self.erased):self.assertEqual(l.history_probe_bank(b,A,C.byref(Save())),0)
  for revision in (0,12,255,256,65535):
   b=bytearray(seed);b[12:14]=revision.to_bytes(2,'little');b=bytes(repair_crc(b))
   for l in (self.old,self.new,self.erased):self.assertEqual(l.history_probe_bank(b,A,C.byref(Save())),0)
 def test_legal_full_overbudget_revision8_and_non_authoritative_credit(self):
  s=Save.from_buffer_copy(bytes(self.base));template=Instance.from_buffer_copy(bytes(s.roster.instances[0]));template.flags=1
  for slot in range(64,160):s.roster.instances[slot]=template;s.roster.instances[slot].instance_id=s.roster.next_instance_id;s.roster.next_instance_id+=1
  s.roster.expedition_events[:]=bytes([255])*64;s.roster.lifetime_field_aid[:]=bytes([255])*16
  for l in (self.old,self.new,self.erased):self.assertEqual(l.save5_validate_revision(C.byref(s),8),1)
  bank=(C.c_ubyte*SIZE)();self.assertEqual(self.old.history_encode(C.byref(s),bank),1)
  for l in (self.new,self.erased):
   out=Save();self.assertEqual(l.history_probe_bank(bank,A,C.byref(out)),1);self.assertEqual(compare_state(out),compare_state(s))
if __name__=='__main__':unittest.main(verbosity=2)
