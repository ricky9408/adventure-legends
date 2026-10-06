#!/usr/bin/env python3
"""Byte-exact validation fast paths; synthetic adversarial inputs, no gameplay proof."""
import ctypes as C
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_save5 import ROOT,Instance
sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools

FORMS=(79,85,25,28,81,83,87,89,91,93)
LEVELS=(20,20,20,22,22,22,24,22,24,22)
BONDS=(40,40,40,45,45,45,45,45,45,45)
class ValidationFastPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='southern-validation-fastpath-')
        cls.addClassCleanup(cls.tmp.cleanup)
        folder=Path(cls.tmp.name)
        cls.libs=[]
        for portable in (False,True):
            dest=folder/('portable.so' if portable else 'alias-safe.so')
            command=['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-fstrict-aliasing',
                     '-fPIC','-shared','-I'+str(ROOT/'src')]
            if portable:command+=['-U__GNUC__','-U__clang__']
            subprocess.run([*command,str(ROOT/'src/creatures.c'),str(ROOT/'src/creature_data.c'),'-o',str(dest)],check=True)
            lib=C.CDLL(str(dest));lib.creatures_instance_validate.argtypes=[C.POINTER(Instance)]
            lib.creatures_instance_validate_revision.argtypes=[C.POINTER(Instance),C.c_uint]
            cls.libs.append(lib)
        exported=folder/'export-save5.c'
        exported.write_text((ROOT/'src/save5.c').read_text()+'\nunsigned southern_evidence_test(const CreatureInstance*c){return southern_instance_evidence(c);}\n')
        sources=[ROOT/'src'/f'{name}.c' for name in ('save4','creatures','creature_data','equipment','equipment_data')]
        dest=folder/'source-evidence.so'
        subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-fstrict-aliasing',
                        '-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-fPIC','-shared','-I'+str(ROOT/'src'),
                        str(exported),*map(str,sources),'-o',str(dest)],check=True)
        cls.evidence=C.CDLL(str(dest));cls.evidence.southern_evidence_test.argtypes=[C.POINTER(Instance)]
        cls.evidence.southern_evidence_test.restype=C.c_uint

    def test_all24_empty_record_bytes_all255_nonzero_values_and_revisions(self):
        # Both implementations check every byte, even when form_id is zero.
        for lib in self.libs:
            c=Instance()
            self.assertEqual(lib.creatures_instance_validate(C.byref(c)),1)
            for offset in range(24):
                for value in range(1,256):
                    raw=bytearray(24);raw[offset]=value;c=Instance.from_buffer_copy(raw)
                    self.assertEqual(lib.creatures_instance_validate(C.byref(c)),0,(offset,value))
                    for revision in (1,2,3,4):
                        self.assertEqual(lib.creatures_instance_validate_revision(C.byref(c),revision),0,(offset,value,revision))
                    self.assertEqual(bytes(c),bytes(raw))

    def test_keyed_source_evidence_preserves_all256_forms_and_floor_edges(self):
        count=0
        for form in range(256):
            for level in (0,19,20,21,22,23,24,50,255):
                for bond in (0,39,40,44,45,100,255):
                    for trial in (0,1,2,3,32768,65535):
                        c=Instance();c.form_id=form;c.level=level;c.bond=bond;c.trial_flags=trial
                        expected=0
                        for i,base in enumerate(FORMS):
                            if form in (base,base+1):
                                expected=1<<i
                                if trial or form==base+1:
                                    expected=(expected|(1<<(i+10))) if trial==1 and level>=LEVELS[i] and bond>=BONDS[i] else 0x80000000
                                break
                        before=bytes(c)
                        self.assertEqual(self.evidence.southern_evidence_test(C.byref(c)),expected,(form,level,bond,trial))
                        self.assertEqual(bytes(c),before);count+=1
        self.assertEqual(count,96768)

    def test_second_pass_exhaustive_xp_party_collection_differential(self):
        exe=Path(self.tmp.name)/'second-pass-differential'
        subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic',
            '-I'+str(ROOT/'src'),str(ROOT/'tests/southern_validation_differential.c'),
            str(ROOT/'src/creature_data.c'),'-o',str(exe)],check=True)
        result=json.loads(subprocess.check_output([str(exe)],text=True))
        self.assertEqual(result,{'xp_level_pairs':23531642,'party_reference_pairs':301510,
            'collection_byte_pairs':1048576,'instance_corruptions':36720})

    def test_arm_empty_checks_introduce_no_libc_symbols(self):
        arm=resolve_arm_tools('gcc','nm',root=ROOT)
        for portable in (False,True):
            out=Path(self.tmp.name)/('portable.o' if portable else 'alias-safe.o')
            command=[arm['gcc'],'-std=c99','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin',
                     '-fstrict-aliasing','-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-I'+str(ROOT/'src')]
            if portable:command+=['-U__GNUC__','-U__clang__']
            subprocess.run([*command,'-c',str(ROOT/'src/creatures.c'),'-o',str(out)],check=True)
            unresolved=subprocess.check_output([arm['nm'],'-u',str(out)],text=True)
            for forbidden in ('memcpy','memset','memcmp','memmove','malloc','calloc','free'):
                self.assertNotIn(forbidden,unresolved)

if __name__=='__main__':unittest.main(verbosity=2)
