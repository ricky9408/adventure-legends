#!/usr/bin/env python3
"""Authenticated wire5/r6 -> wire5/r7 explicit writer interruption tests."""
import ctypes as C,hashlib,json,tempfile,unittest,time
from pathlib import Path
from return_host_support import *
FIXTURES=(('underwater-all89-town.sav',FIXTURE_SHA),('underwater-minimal12-town.sav','3f5bbccab022f86b38f4d180e8cf66b04c055791fe4804ddbebbdefb5406aeda'))
class ReturnMigrationPowerloss(unittest.TestCase):
 def test_every_r6_to_r7_write_cut_both_banks(self):
  with tempfile.TemporaryDirectory(prefix='return-migration-cuts-') as tmp:
   lib=build(tmp);checks=0;rows=[];start=time.monotonic()
   for name,sha in FIXTURES:
    data=(FIXTURE.parent/name).read_bytes();self.assertEqual(hashlib.sha256(data).hexdigest(),sha)
    newest=max((A,B),key=lambda offset:int.from_bytes(data[offset+8:offset+12],'little'));bank=data[newest:newest+SIZE]
    self.assertEqual(bank[12:14],b'\x06\x00')
    for destination,preserved in (('A',B),('B',A)):
     image=bytearray(data);image[A:A+SIZE]=bytes([255])*SIZE;image[B:B+SIZE]=bytes([255])*SIZE;image[preserved:preserved+SIZE]=bank
     lib.return_job_cancel();lib.save5_test_reset_writer();lib.save5_test_fail_after(-1);lib.sram[:]=image
     source=Save();self.assertEqual(lib.save5_load(C.byref(source)),1);self.assertEqual(bytes(lib.sram),image,'load must not write')
     baseline=compare_state(source)
     for cut in range(SIZE+2):
      lib.save5_test_reset_writer();lib.save5_test_fail_after(cut);lib.sram[:]=image
      committed=lib.save5_store(C.byref(source));self.assertEqual(committed,int(cut>=SIZE+1),(name,destination,cut))
      out=Save();self.assertEqual(lib.save5_load(C.byref(out)),1);self.assertEqual(compare_state(out),baseline)
      self.assertEqual(bytes(lib.sram[:A]),image[:A]);self.assertEqual(bytes(lib.sram[preserved:preserved+SIZE]),bank)
      self.assertEqual(out.quests.region_flags[5],0);self.assertEqual(out.quests.region_flags[11],0);self.assertEqual(out.quests.anchors[5],0)
      self.assertTrue(all(not out.quests.objectives[q] for q in range(46,54)))
      if committed:
       target=A if destination=='A' else B;self.assertEqual(bytes(lib.sram[target+12:target+14]),b'\x08\x00')
      checks+=1
     rows.append({'fixture':name,'sha256':sha,'destination':destination,'cuts':SIZE+2});print(name,destination,'every cutoff passed',flush=True)
   path=ROOT/'docs/evidence/return-migration-powerloss.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps({'scope':'Authenticated native-earned input, synthetic host interruption test. No machine states imported.','result':'PASS','source_sha256':lib.source_hashes,'source_unchanged':runtime_hashes()==lib.source_hashes,'checks':checks,'seconds':round(time.monotonic()-start,3),'cases':rows},indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
