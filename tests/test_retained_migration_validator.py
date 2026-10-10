#!/usr/bin/env python3
"""Synthetic validator unit cases; no gameplay or native acquisition claim."""
import binascii
from pathlib import Path
import unittest
from retained_migration_validator import validate_bank,validate_migration
ROOT=Path(__file__).resolve().parents[1]

def repair(bank):
    bank=bytearray(bank);bank[16:20]=bytes(4);commit=bank[20];bank[20]=0
    bank[16:20]=binascii.crc32(bank).to_bytes(4,'little');bank[20]=commit
    return bytes(bank)

class MigrationValidator(unittest.TestCase):
    def setup_case(self,revision,path):
        original=(ROOT/'tests/fixtures'/path).read_bytes()
        offset=max((0x200,0x1a00),key=lambda p:int.from_bytes(original[p+8:p+12],'little'))
        prior=original[offset:offset+6144];validate_bank(prior,revision)
        current=bytearray(prior);current[12:14]=(7).to_bytes(2,'little');current[8:12]=((int.from_bytes(prior[8:12],'little')+1)&0xffffffff).to_bytes(4,'little');current=repair(current)
        image=bytearray(original);other=0x1a00 if offset==0x200 else 0x200;image[other:other+6144]=current
        return prior,current,original,image,revision,offset
    def test_accepts_only_exact_same_wire_payload_and_preserved_old_bank(self):
        for revision,path in ((3,'v5-revision3/northern-all21-town.sav'),(4,'v5-revision4/southern-all41-town.sav'),(5,'v5-revision5/magma-all65-town.sav'),(6,'v5-revision6/underwater-all89-town.sav')):
            p,c,before,after,r,offset=self.setup_case(revision,path)
            self.assertTrue(validate_migration(p,c,before,after,r))
            for changed in (32,160,4000,4032,4544,6143):
                bad=bytearray(c);bad[changed]^=1;bad=repair(bad)
                with self.assertRaises(AssertionError):validate_migration(p,bad,before,after,r)
            bad=bytearray(c);bad[16]^=1
            with self.assertRaises(AssertionError):validate_migration(p,bad,before,after,r)
            bad=bytearray(c);bad[12:14]=(6).to_bytes(2,'little');bad=repair(bad)
            with self.assertRaises(AssertionError):validate_migration(p,bad,before,after,r)
            bad=bytearray(after);bad[offset+20]=0
            with self.assertRaises(AssertionError):validate_migration(p,c,before,bad,r)
    def test_rejects_other_wire_formats_and_ambiguous_old_bank(self):
        p,c,before,after,r,offset=self.setup_case(3,'v5-revision3/northern-all21-town.sav')
        for revision in (0,1,2,7,8):
            with self.assertRaises(AssertionError):validate_migration(p,c,before,after,revision)
        for prefix in (b'EB\x04\x20',b'XX\x05\x20'):
            bad=repair(prefix+p[4:])
            with self.assertRaises(AssertionError):validate_migration(bad,c,before,after,3)
        bad=bytearray(before);other=0x1a00 if offset==0x200 else 0x200;bad[other:other+6144]=p
        with self.assertRaises(AssertionError):validate_migration(p,c,bad,after,3)
if __name__=='__main__':unittest.main(verbosity=2)
