#!/usr/bin/env python3
"""Exact accepted Magma oracle vs r6: all historical bank semantics stay frozen.

All mutant banks have independent recomputed CRC. Temporary independent source
closures include private .inc dependencies. No live sibling checkout required.
No generated SRAM here is evidence of Underwater controller acquisitions.
"""
import collections,ctypes as C,hashlib,json,os,random,shlex,subprocess,tempfile,unittest
from pathlib import Path
from test_save5 import ROOT,Save,A,B,SIZE,repair_crc,compare_state
from test_save5_history_differential import HARNESS,FIXTURES as OLD_FIXTURES
ORACLE=ROOT/'tests/fixtures/magma-policy-oracle'
MANIFEST_SHA='9ba6c261b8a45525ecbe5d75a2a9ee858f11709074875105a9560dc855689d54'
FIXTURES=(*OLD_FIXTURES,(5,'magma-all65-town.sav','a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858'))
SOURCES=('save4','save5','creatures','creature_data','equipment','equipment_data','southern_quests','magma_quests')
def digest(data):return hashlib.sha256(data).hexdigest()
def build(root,folder):
 folder.mkdir();hashes={}
 for p in (root/'src').iterdir():
  if p.is_file() and p.suffix in ('.c','.h','.inc'):
   data=p.read_bytes();(folder/p.name).write_bytes(data);hashes[p.name]=digest(data)
 (folder/'probe.c').write_text(HARNESS)
 so=folder/'history.so';subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+['-std=c99','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-shared','-fPIC','-I'+str(folder),*[str(folder/(n+'.c')) for n in SOURCES],str(folder/'probe.c'),'-o',str(so)],check=True)
 lib=C.CDLL(str(so));lib.history_probe_bank.argtypes=[C.c_void_p,C.c_uint,C.POINTER(Save)];lib.history_probe_image.argtypes=[C.c_void_p,C.POINTER(Save)];lib.history_encode.argtypes=[C.POINTER(Save),C.c_void_p];lib.save5_validate_revision.argtypes=[C.POINTER(Save),C.c_uint]
 lib._hashes=hashes;assert lib.history_state_size()==C.sizeof(Save);return lib
class UnderwaterHistoricalDifferential(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  data=(ORACLE/'provenance.json').read_bytes();assert digest(data)==MANIFEST_SHA
  for row in json.loads(data)['files']:
   data=(ORACLE/row['path']).read_bytes();assert len(data)==row['bytes'] and digest(data)==row['sha256'],row['path']
  assert (ROOT/'src/save5_history_policy.h').read_bytes()==(ORACLE/'src/save5_history_policy.h').read_bytes()
  cls.tmp=tempfile.TemporaryDirectory(prefix='underwater-history-');cls.addClassCleanup(cls.tmp.cleanup);root=Path(cls.tmp.name)
  cls.old=build(ORACLE,root/'old');cls.new=build(ROOT,root/'new');cls.oldout=Save();cls.newout=Save();cls.counts=collections.Counter();cls.images=[];cls.seeds={}
  for revision,name,sha in FIXTURES:
   data=(ROOT/f'tests/fixtures/v5-revision{revision}'/name).read_bytes();assert len(data)==32768 and digest(data)==sha
   cls.images.append((revision,name,data));offset=max((A,B),key=lambda p:int.from_bytes(data[p+8:p+12],'little'));cls.seeds[revision]=data[offset:offset+SIZE]
 @classmethod
 def tearDownClass(cls):
  for name,sha in cls.old._hashes.items():assert digest((ORACLE/'src'/name).read_bytes())==sha
  print(json.dumps({'suite':'underwater-history-differential','checks':dict(cls.counts),'oracle_manifest_sha256':MANIFEST_SHA,'candidate_save5_sha256':cls.new._hashes['save5.c']},sort_keys=True))
 def compare(self,bank,expected=None,label='mutant',offset=A):
  bank=bytes(repair_crc(bank));a=self.old.history_probe_bank(bank,offset,C.byref(self.oldout));b=self.new.history_probe_bank(bank,offset,C.byref(self.newout))
  self.assertIn(a,(0,1),label);self.assertIn(b,(0,1),label);self.assertEqual(a,b,(label,digest(bank)))
  self.assertEqual(bytes(self.oldout),bytes(self.newout),(label,'decoded/failure bytes'))
  if expected is not None:self.assertEqual(a,expected,label)
  self.counts[label if label in ('original','weakened','cross-revision') else 'mutants']+=1;self.counts['accepted' if a else 'rejected']+=1
  return a
 def test_original_images_every_historical_fixture_resaves_revision6(self):
  for revision,name,data in self.images:
   self.assertEqual(self.old.history_probe_image(data,C.byref(self.oldout)),1,name);self.assertEqual(self.new.history_probe_image(data,C.byref(self.newout)),1,name);self.assertEqual(bytes(self.oldout),bytes(self.newout))
   previous=compare_state(self.newout);out=(C.c_ubyte*SIZE)();self.assertEqual(self.new.history_encode(C.byref(self.newout),out),1,name)
   self.assertEqual(bytes(out[12:14]),b'\x06\x00');self.assertEqual(self.new.history_probe_bank(out,A,C.byref(self.newout)),1,name);self.assertEqual(compare_state(self.newout),previous)
   for src in (A,B):
    bank=data[src:src+SIZE];self.assertEqual(bytes(repair_crc(bank)),bank,name)
    for dst in (A,B):self.compare(bank,1,'original',dst)
 def test_all_campaign_quest_equipment_bytes_crc_valid(self):
  edges=(0,1,2,3,7,15,31,63,127,128,254,255)
  for revision,seed in self.seeds.items():
   for offset in (*range(32,47),*range(4032,4296),*range(4544,5056)):
    for value in edges:
     if seed[offset]==value:continue
     bank=bytearray(seed);bank[offset]=value;self.compare(bank,label=f'r{revision}:{offset}:{value}')
 def test_old_legal_weakened_trials_and_bond_remain_loadable_and_resavable(self):
  accepted=0
  for rev,seed in self.seeds.items():
   for slot in range(160):
    p=160+slot*24
    if seed[p] not in (2,5,8,11,14,20,23,74,76,78):continue
    for flags in (0,1,3,31,255,65535):
     for bond in (0,1,39,100):
      bank=bytearray(seed);bank[p+3]=bond;bank[p+14:p+16]=flags.to_bytes(2,'little')
      if self.compare(bank,label='weakened'):
       encoded=(C.c_ubyte*SIZE)();before=compare_state(self.newout);self.assertEqual(self.new.history_encode(C.byref(self.newout),encoded),1,(rev,slot,flags,bond));self.assertEqual(self.new.history_probe_bank(encoded,A,C.byref(self.newout)),1);self.assertEqual(compare_state(self.newout),before);accepted+=1
  self.assertGreater(accepted,20)
 def test_new_content_rejected_in_every_old_revision(self):
  for rev,seed in self.seeds.items():
   for form in range(49,73):
    for start in (96,112):
     bank=bytearray(seed);bank[start+(form-1)//8]|=1<<((form-1)%8);self.compare(bank,0,'cross-revision')
   for byte,bit in ((4,1),(10,1),(17,1),(20,1),(21,1)):
    bank=bytearray(seed);bank[4248+byte]|=bit;self.compare(bank,0,'cross-revision')
   for q in range(38,46):
    bank=bytearray(seed);bank[4032+q//4]|=1<<(2*(q%4));self.compare(bank,0,'cross-revision')
   for item in (6,13,38,54,68,86):
    bank=bytearray(seed);bank[4944+item//8]|=1<<(item%8);self.compare(bank,0,'cross-revision')
   for source in range(31,37):
    bank=bytearray(seed);bank[5024+source//8]|=1<<(source%8);self.compare(bank,0,'cross-revision')
   for command in range(67,91):
    bank=bytearray(seed);bank[176]=command;self.compare(bank,0,'cross-revision')
 def test_every_form_command_byte_and_random_masks(self):
  rng=random.Random(0x554e4436)
  for rev,seed in self.seeds.items():
   for p in (160,176,177,178,179):
    for value in range(256):
     bank=bytearray(seed);bank[p]=value;self.compare(bank,label=f'r{rev}:identity{p}:{value}')
   for _ in range(2000):
    bank=bytearray(seed);slot=rng.randrange(160);p=160+slot*24;bank[p+14:p+16]=rng.randrange(65536).to_bytes(2,'little');self.compare(bank)
 def test_unknown_revision_and_bad_newer_bank_fallback(self):
  seed=self.seeds[5]
  for rev in (0,7,255,256,65535):
   bank=bytearray(seed);bank[12:14]=rev.to_bytes(2,'little');self.compare(bank,0)
   image=bytearray([255])*32768;image[A:A+SIZE]=seed;bank[8:12]=(0x7fffffff).to_bytes(4,'little');image[B:B+SIZE]=repair_crc(bank)
   self.assertEqual(self.old.history_probe_image(bytes(image),C.byref(self.oldout)),1);self.assertEqual(self.new.history_probe_image(bytes(image),C.byref(self.newout)),1);self.assertEqual(bytes(self.oldout),bytes(self.newout))
if __name__=='__main__':unittest.main(verbosity=2)
