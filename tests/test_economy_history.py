#!/usr/bin/env python3
"""Independent frozen E versus recovered current10 and poisoned live catalogs."""
import ctypes as C,hashlib,json,os,re,subprocess,sys,tempfile,unittest
from pathlib import Path
from test_save5 import ROOT,Save,Instance,Roster,A,B,SIZE,repair_crc,compare_state
from test_save5_history_differential import HARNESS
from test_return_history_core import TABLE_HARNESS
from test_return_history_differential import source_closure,SOURCES,FIXTURES
from test_covenants_history import poison_current
sys.path.insert(0,str(ROOT/'tools'))
from check_economy_history import ORACLE,verify_oracle
class OldSave(C.Structure):_fields_=Save._fields_[:4]
def poison(name,data):
 data=poison_current(name,data)
 if name=='save5_covenants_policy.inc':
  s=data.decode();s,n=re.subn(r'save5_quest_state\(q,quest\)==3','save5_quest_state(q,quest)==0',s);assert n==1
  s,n=re.subn(r'(static const Save4U8 counts\[8\]=)\{[^}]+\}',r'\1{0}',s);assert n==1;data=s.encode()
 return data
def build(root,folder,old=False,transform=None):
 folder.mkdir()
 for name,data in source_closure(root).items():
  base=Path(name).name;(folder/base).write_bytes(transform(base,data)if transform else data)
 (folder/'probe.c').write_text(HARNESS+TABLE_HARNESS);so=folder/'probe.so'
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-shared','-fPIC','-I'+str(folder),*[str(folder/(n+'.c'))for n in SOURCES],str(folder/'probe.c'),'-o',str(so)],check=True)
 l=C.CDLL(str(so));l.State=OldSave if old else Save;assert l.history_state_size()==C.sizeof(l.State)
 for fn,args in [('history_probe_bank',[C.c_void_p,C.c_uint,C.c_void_p]),('history_probe_image',[C.c_void_p,C.c_void_p]),('history_encode',[C.c_void_p,C.c_void_p]),('save5_validate_revision',[C.c_void_p,C.c_uint]),('creatures_roster_validate_revision',[C.POINTER(Roster),C.c_uint]),('history_mask_table',[C.POINTER(Instance),C.c_uint,C.c_void_p]),('history_command_table',[C.c_uint,C.c_uint,C.c_void_p]),('history_instance_byte_table',[C.POINTER(Instance),C.c_uint,C.c_void_p])]:getattr(l,fn).argtypes=args
 return l
class EconomyHistory(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  verify_oracle();cls.tmp=tempfile.TemporaryDirectory(prefix='economy-history-recovered-');cls.addClassCleanup(cls.tmp.cleanup);p=Path(cls.tmp.name)
  cls.old=build(ORACLE,p/'old',True);cls.new=build(ROOT,p/'new');cls.poisoned=build(ROOT,p/'poison',transform=poison);cls.images=[]
  provenance=json.loads((ROOT/'tests/fixtures/v5-revision9/provenance.json').read_text());assert provenance['candidate']['emberbond.gba']=='27793b4b6b5cd0049539da777013d6ed5587dcca6baa8843c36697ef1c8ef55f'
  for row in provenance['fixtures']:
   image=(ROOT/row['path']).read_bytes();assert len(image)==32768 and hashlib.sha256(image).hexdigest()==row['sha256'];cls.images.append((row['path'],image))
  cls.base=OldSave();assert cls.old.history_probe_image(cls.images[0][1],C.byref(cls.base))==1
  cls.seed=max((cls.images[0][1][x:x+SIZE]for x in (A,B)),key=lambda b:int.from_bytes(b[8:12],'little'))
 def bank(self,b,label,expected=None):
  b=bytes(repair_crc(b));old=OldSave();verdict=self.old.history_probe_bank(b,A,C.byref(old));self.assertIn(verdict,(0,1))
  if expected is not None:self.assertEqual(verdict,expected,label)
  for l in (self.new,self.poisoned):
   out=Save();self.assertEqual(l.history_probe_bank(b,B,C.byref(out)),verdict,label);self.assertEqual(bytes(out),bytes(old)+(bytes(32)if verdict else bytes([204])*32),(label,'exact decoded bytes'))
 def test_genuine9_full48_explicit10_no_gains(self):
  self.assertEqual(sum(bool(x.item_id)for x in self.base.equipment.bag),48)
  for name,image in self.images:
   old=OldSave();self.assertEqual(self.old.history_probe_image(image,C.byref(old)),1)
   for l in (self.new,self.poisoned):
    out=Save();self.assertEqual(l.history_probe_image(image,C.byref(out)),1);self.assertEqual(bytes(out),bytes(old)+bytes(32));self.assertEqual(l.save5_validate_revision(C.byref(out),9),1)
   s=Save.from_buffer_copy(bytes(old)+bytes(32));b=(C.c_ubyte*SIZE)();self.assertEqual(self.new.history_encode(C.byref(s),b),1);self.assertEqual(bytes(b)[12:14],b'\x0b\0');self.assertEqual(bytes(b)[6:8],(5088).to_bytes(2,'little'));self.assertEqual(self.old.history_probe_bank(b,A,C.byref(OldSave())),0)
   out=Save();self.assertEqual(self.new.history_probe_bank(b,B,C.byref(out)),1);self.assertEqual(compare_state(out),compare_state(s))
 def test_genuine_revisions1_to8_unchanged(self):
  images=[(r,n,(ROOT/f'tests/fixtures/v5-revision{r}'/n).read_bytes())for r,n,_ in FIXTURES]
  for revision in (7,8):
   for row in json.loads((ROOT/f'tests/fixtures/v5-revision{revision}/provenance.json').read_text())['fixtures']:
    name=row.get('path')or f"tests/fixtures/v5-revision{revision}/{row['file']}";images.append((revision,name,(ROOT/name).read_bytes()))
  for r,name,image in images:
   old=OldSave();self.assertEqual(self.old.history_probe_image(image,C.byref(old)),1,name)
   for l in (self.new,self.poisoned):
    out=Save();self.assertEqual(l.history_probe_image(image,C.byref(out)),1,name);self.assertEqual(bytes(out),bytes(old)+bytes(32),name);self.assertEqual(l.save5_validate_revision(C.byref(out),r),1,name)
 def test_all128_forms_exhaustive_masks_commands_record_bytes(self):
  rows=json.loads((ROOT/'assets/history/creatures-v9.json').read_text())['forms'];self.assertEqual(len(rows),128)
  for row in rows:
   c=Instance();c.form_id=row['id'];c.flags=1;c.instance_id=1;c.level=50;c.xp=470596;c.bond=100;c.polarity=row['polarity'];c.equipped[0]=row['learn'][0][1];c.trial_flags=row['trial_mask']
   for method,args,count in [('history_mask_table',(C.byref(c),9),65536),('history_command_table',(9,row['id']),52*256),('history_instance_byte_table',(C.byref(c),9),24*256)]:
    expected=(C.c_ubyte*count)();getattr(self.old,method)(*args,expected)
    for l in (self.new,self.poisoned):
     out=(C.c_ubyte*count)();getattr(l,method)(*args,out);self.assertEqual(bytes(out),bytes(expected),(row['id'],method))
  for form in range(257):
   for method in ('creatures_trial_allowed_mask','creatures_family_revision','creatures_legacy_spirit_revision','creatures_form_allowed_revision'):
    want=getattr(self.old,method)(form,9)
    for l in (self.new,self.poisoned):self.assertEqual(getattr(l,method)(form,9),want,(form,method))
 def test_each_decoded_state_byte_and_zero_new_extension(self):
  seed=bytes(self.base)
  for pos in range(len(seed)):
   raw=bytearray(seed);raw[pos]^=(1,2,4,8,16,32,64,128,255)[pos%9];old=OldSave.from_buffer_copy(raw);want=self.old.save5_validate_revision(C.byref(old),9);new=Save.from_buffer_copy(raw+bytes(32))
   for l in (self.new,self.poisoned):self.assertEqual(l.save5_validate_revision(C.byref(new),9),want,pos)
  for pos in range(32):
   s=Save.from_buffer_copy(seed+bytes(32));raw=(C.c_ubyte*32).from_buffer(s.economy);raw[pos]=1
   for l in (self.new,self.poisoned):self.assertEqual(l.save5_validate_revision(C.byref(s),9),0,pos)
 def test_crc_valid_bank_mutations_and_unknown_revisions(self):
  for pos in (*range(32,47),*range(4032,4296),*range(4544,5056),96+15,112+15,160+16):
   for value in (0,1,3,7,15,31,63,127,128,254,255):
    b=bytearray(self.seed);b[pos]=value;self.bank(b,(pos,value))
  for revision in (0,12,255,256,65535):
   b=bytearray(self.seed);b[12:14]=revision.to_bytes(2,'little');self.bank(b,revision,0)
  for pos in range(5056,6144):
   b=bytearray(self.seed);b[pos]=1;self.bank(b,('reserved',pos),0)
 def test_legendary_party_exact_limit(self):
  s=OldSave.from_buffer_copy(bytes(self.base));legends=[i for i,c in enumerate(s.roster.instances)if c.form_id>=121];self.assertEqual(len(legends),8)
  s.roster.party[:]=(legends[0],legends[1],255,255);s.roster.selected_party=0;self.assertEqual(self.old.save5_validate_revision(C.byref(s),9),0)
  for l in (self.new,self.poisoned):
   new=Save.from_buffer_copy(bytes(s)+bytes(32));self.assertEqual(l.save5_validate_revision(C.byref(new),9),0)
  b=bytearray(self.seed);b[4000:4005]=bytes((*s.roster.party,0));self.bank(b,'two legends',0)
 def test_full160_roster_non_authoritative_credit(self):
  s=OldSave.from_buffer_copy(bytes(self.base));template=Instance.from_buffer_copy(bytes(s.roster.instances[0]));template.flags=1
  for i in range(160):
   if not s.roster.instances[i].form_id:s.roster.instances[i]=template;s.roster.instances[i].instance_id=s.roster.next_instance_id;s.roster.next_instance_id+=1
  s.roster.expedition_events[:]=bytes([255])*64;s.roster.lifetime_field_aid[:]=bytes([255])*16;self.assertEqual(self.old.save5_validate_revision(C.byref(s),9),1)
  for l in (self.new,self.poisoned):self.assertEqual(l.save5_validate_revision(C.byref(Save.from_buffer_copy(bytes(s)+bytes(32))),9),1)
  b=(C.c_ubyte*SIZE)();self.assertEqual(self.old.history_encode(C.byref(s),b),1);self.bank(bytes(b),'full160',1)
if __name__=='__main__':unittest.main(verbosity=2)
