#!/usr/bin/env python3
"""Southern core APIs only. Direct host grants are not acquisition evidence."""
import ctypes as C
import hashlib
from pathlib import Path
import unittest
import tempfile
from test_creatures import build, Instance, Roster, U8, U16, ROOT, ENABLED as CURRENT_ENABLED

PAIRS = [(25,9,20,40),(28,10,22,45),(79,28,20,40),(81,29,22,45),
         (83,30,22,45),(85,31,20,40),(87,32,24,45),(89,33,22,45),
         (91,34,24,45),(93,35,22,45)]
OLD = [1,2,4,5,7,8,10,11,13,14,16,19,20,22,23,73,74,75,76,77,78]
class SouthernCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='southern-core-')
        cls.lib=build(cls.tmp.name)
        signatures={
            'creatures_form_allowed_revision':(C.c_int,[C.c_uint]*2),
            'creatures_command_learned_revision':(C.c_int,[C.c_uint]*4),
            'creatures_trial_allowed_mask':(C.c_uint,[C.c_uint]*2),
            'creatures_instance_validate_revision':(C.c_int,[C.POINTER(Instance),C.c_uint]),
            'creatures_trial_mask_for_key':(C.c_uint,[C.c_uint]*2),
            'creatures_mark_trial_qualified':(C.c_int,[C.POINTER(Instance),C.c_uint,C.c_uint]),
            'creatures_has_trial_qualified':(C.c_int,[C.POINTER(Instance),C.c_uint,C.c_uint]),
            'creatures_evolution_count':(C.c_uint,[C.c_uint]),
            'creatures_evolution_at':(C.c_void_p,[C.c_uint,C.c_uint]),
            'creatures_evolution_to':(C.c_void_p,[C.c_uint,C.c_uint]),
            'creatures_can_evolve_to':(C.c_uint,[C.POINTER(Instance),C.c_uint,C.c_uint,C.c_int]),
            'creatures_evolve_to':(C.c_uint,[C.POINTER(Roster),C.c_uint,C.c_uint,C.c_uint,C.c_int,C.c_int]),
            'creatures_supports_capability':(C.c_int,[C.c_uint]*2),
            'creatures_party_supports_capability':(C.c_int,[C.POINTER(Roster),C.c_uint]),
            'creatures_party_set_requirements':(C.c_int,[C.POINTER(Roster),C.POINTER(U8),C.POINTER(U16),C.c_uint]),
        }
        for name,(restype,args) in signatures.items():
            f=getattr(cls.lib,name);f.restype=restype;f.argtypes=args
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def setUp(self):
        self.r=Roster();self.lib.creatures_roster_init(C.byref(self.r))
    def grant(self,form,level=50,bond=100):
        return self.lib.creatures_grant(C.byref(self.r),form,level,bond,0,0)
    def test_all_released_binary_rows_stay_byte_exact(self):
        pinned=[('creature_forms',672,'bc65ecc6849c015686b0263ad59928fa4e73d16097afdbc48af5f24c1e091da0'),
                ('creature_learnsets',62,'c5a36f66da524b8aa96daa1257aa5dbba48f2a9b98561d21b35ce051402c9d05'),
                ('creature_evolutions',80,'fb21890584b87cd1c3793917564a3518f2b87be9f86faf4360b911eeb4bf56be'),
                ('creature_abilities',168,'2fbab2735f8dcac6956d9676053f44600d47c2f425de0cad5edc87b82befd15f')]
        for name,n,want in pinned:
            self.assertEqual(hashlib.sha256(bytes((U8*n).in_dll(self.lib,name))).hexdigest(),want)
    def test_qualified_trials_are_full_width_family_bound_and_atomic(self):
        for base,family,level,bond in PAIRS:
            self.lib.creatures_roster_init(C.byref(self.r));self.assertEqual(self.grant(base),0)
            c=self.r.instances[0];initial=bytes(c)
            self.assertEqual(self.lib.creatures_family_trial(base),0)
            self.assertEqual(self.lib.creatures_trial_mask_for_key(family,1),1)
            for bad in [0,2,3,65535,65536,65537,0xffffffff]:
                self.assertFalse(self.lib.creatures_mark_trial_qualified(C.byref(c),family,bad))
                self.assertFalse(self.lib.creatures_has_trial_qualified(C.byref(c),family,bad))
                self.assertEqual(bytes(c),initial)
            for other in [0,1,9,10,28,29,30,31,32,33,34,35,60,61,256+family,65536+family,0xffffffff]:
                if other==family:continue
                self.assertFalse(self.lib.creatures_mark_trial_qualified(C.byref(c),other,1))
                self.assertFalse(self.lib.creatures_has_trial_qualified(C.byref(c),other,1))
                self.assertEqual(bytes(c),initial)
            for flag in [0,1,2,3,65537,0xffffffff]:
                self.assertFalse(self.lib.creatures_mark_trial(C.byref(c),flag));self.assertEqual(bytes(c),initial)
            self.assertFalse(self.lib.creatures_has_trial_qualified(C.byref(c),family,1))
            self.assertTrue(self.lib.creatures_mark_trial_qualified(C.byref(c),family,1))
            self.assertTrue(self.lib.creatures_mark_trial_qualified(C.byref(c),family,1))
            self.assertTrue(self.lib.creatures_has_trial_qualified(C.byref(c),family,1))
            self.assertEqual(c.trial_flags,1)
            c.trial_flags=3;invalid=bytes(c)
            self.assertFalse(self.lib.creatures_mark_trial_qualified(C.byref(c),family,1));self.assertEqual(bytes(c),invalid)
    def test_legacy_qualified_keys_preserve_wire_masks(self):
        families={1:1,4:2,7:4,10:8,13:16,16:0,19:32,22:64,73:128,75:256,77:512}
        for base,mask in families.items():
            self.lib.creatures_roster_init(C.byref(self.r));self.grant(base)
            c=self.r.instances[0];family=self.lib.creatures_form(base).contents.family
            self.assertEqual(self.lib.creatures_trial_mask_for_key(family,1),mask)
            self.assertEqual(bool(self.lib.creatures_mark_trial_qualified(C.byref(c),family,1)),bool(mask))
            self.assertEqual(c.trial_flags,mask)
    def test_revision_whitelists_cover_every_form_command_and_trial(self):
        allowed={1:OLD[:8],2:OLD[:11],3:OLD,4:OLD+[x for b,*_ in PAIRS for x in (b,b+1)]}
        allowed[5]=[id for id in CURRENT_ENABLED if not 49<=id<=72]
        allowed[6]=CURRENT_ENABLED
        for revision in [0,1,2,3,4,5,6,255,256,0xffffffff]:
            for form in list(range(130))+[256,0xffffffff]:
                self.assertEqual(bool(self.lib.creatures_form_allowed_revision(form,revision)),form in allowed.get(revision,[]),(form,revision))
                if form not in allowed.get(revision,[]):self.assertEqual(self.lib.creatures_trial_allowed_mask(form,revision),0)
        for revision in range(1,5):
            for form in allowed[revision]:
                for ability in list(range(256))+[256,65537,0xffffffff]:
                    for level in [0,1,11,12,15,16,19,20,22,24,50,51]:
                        self.assertEqual(bool(self.lib.creatures_command_learned_revision(form,level,ability,revision)),bool(self.lib.creatures_command_learned(form,level,ability)),(revision,form,ability,level))
                self.lib.creatures_roster_init(C.byref(self.r));self.grant(form);c=self.r.instances[0]
                mask=self.lib.creatures_trial_allowed_mask(form,revision)
                for flag in [0,1,2,4,8,16,32,64,128,256,512,1024,32768,65535]:
                    c.trial_flags=flag
                    self.assertEqual(bool(self.lib.creatures_instance_validate_revision(C.byref(c),revision)),flag in (0,mask),(revision,form,flag,mask))
    def test_bad_rom_indexes_reject_lookups_without_mutation(self):
        import re
        from test_creature_sparse import edit_array
        source=(ROOT/'src/creature_data.c').read_text()
        for name,key,value in [('creature_form_index',1,0),('creature_form_index',1,255),
                               ('creature_form_index',1,2),('creature_ability_index',1,255),
                               ('creature_ability_index',1,2),('creature_incoming_evolution_index',2,255),
                               ('creature_incoming_evolution_index',2,2)]:
            def corrupt(body):
                values=[int(v) for v in re.findall(r'\d+',body)];values[key]=value
                return '    '+', '.join(map(str,values))+','
            changed=edit_array(source,name,corrupt)
            lib=build(self.tmp.name,changed,name+str(value))
            self.assertFalse(lib.creatures_catalog_validate())
            r=Roster();lib.creatures_roster_init(C.byref(r));before=bytes(r)
            form=2 if name=='creature_incoming_evolution_index' else 1
            self.assertEqual(lib.creatures_grant(C.byref(r),form,50,100,0,0),255)
            self.assertEqual(bytes(r),before)
            if name=='creature_form_index':self.assertFalse(lib.creatures_form(1))
            if name=='creature_ability_index':self.assertFalse(lib.creatures_ability(1))
    def test_historical_commands_do_not_follow_broadened_current_learnsets(self):
        # Hypothetical future current data may admit command23 on old form1;
        # every immutable historical snapshot still permits only its old pair.
        source=(ROOT/'src/creature_data.c').read_text()
        source=source.replace('    {1, 1},','    {1, 23},',1)
        expanded=build(self.tmp.name,source,'future-current-learnset')
        expanded.creatures_instance_validate_revision.restype=C.c_int
        expanded.creatures_instance_validate_revision.argtypes=[C.POINTER(Instance),C.c_uint]
        r=Roster();expanded.creatures_roster_init(C.byref(r))
        self.assertEqual(expanded.creatures_grant(C.byref(r),1,50,100,0,0),0)
        self.assertEqual(r.instances[0].equipped[0],23)
        self.assertTrue(expanded.creatures_instance_validate(C.byref(r.instances[0])))
        for revision in [1,2,3,4]:
            self.assertFalse(expanded.creatures_instance_validate_revision(C.byref(r.instances[0]),revision))
    def test_new_evolutions_require_exact_target_and_preserve_identity(self):
        for n,(base,family,level,bond) in enumerate(PAIRS):
            self.lib.creatures_roster_init(C.byref(self.r));self.grant(base,level,bond);c=self.r.instances[0]
            self.assertEqual(self.lib.creatures_evolution_count(base),1)
            self.assertTrue(self.lib.creatures_evolution_at(base,0))
            for index in [1,20,255,256,0xffffffff]:self.assertFalse(self.lib.creatures_evolution_at(base,index))
            self.assertTrue(self.lib.creatures_evolution_to(base,base+1))
            self.assertEqual(self.lib.creatures_can_evolve_to(C.byref(c),base+1,64,1),6)
            self.lib.creatures_mark_trial_qualified(C.byref(c),family,1);before=bytes(self.r)
            for target,result in [(0,1),(121,1),(256+base+1,1),(0xffffffff,1),(1,2),(base,2)]:
                self.assertEqual(self.lib.creatures_evolve_to(C.byref(self.r),0,target,64,1,1),result);self.assertEqual(bytes(self.r),before)
            for context,sanctuary,confirm,result in [(0,1,1,5),(1024,1,1,5),(2048,1,1,5),(4096,1,1,1),(64,0,1,7),(64,1,0,8)]:
                self.assertEqual(self.lib.creatures_evolve_to(C.byref(self.r),0,base+1,context,sanctuary,confirm),result);self.assertEqual(bytes(self.r),before)
            identity=bytearray(bytes(c));identity[0]=base+1
            self.assertEqual(self.lib.creatures_evolve_to(C.byref(self.r),0,base+1,64,1,1),0)
            self.assertEqual(bytes(c),identity);self.assertEqual(c.equipped[0],23+2*n)
            self.assertTrue(self.lib.creatures_equip(C.byref(c),1,24+2*n))
            self.assertEqual(self.lib.creatures_evolution_count(base+1),0)
    def test_capability_keys_and_party_requirements_are_bounded_atomic(self):
        for form in OLD+[x for b,*_ in PAIRS for x in (b,b+1)]:
            mask=self.lib.creatures_capabilities(form)
            for key in range(1,27):self.assertEqual(bool(self.lib.creatures_supports_capability(form,key)),bool(mask&(1<<(key-1))))
            for key in [0,27,32,33,256,65536,0xffffffff]:self.assertFalse(self.lib.creatures_supports_capability(form,key))
        for form in [0,3,121,256,0xffffffff]:self.assertFalse(self.lib.creatures_supports_capability(form,1))
        self.grant(79);self.grant(85);self.grant(1);self.grant(4);self.grant(89)
        requires=(U16*2)(26,17)
        self.assertTrue(self.lib.creatures_party_set_requirements(C.byref(self.r),(U8*4)(1,0,3,2),requires,2))
        self.assertEqual(self.r.selected_party,1)
        before=bytes(self.r)
        for party,req,count in [((4,2,3,255),requires,2),((0,0,1,255),requires,2),((0,1,160,255),requires,2),((0,1,2,3),(U16*1)(33),1),((0,1,2,3),requires,9),((0,1,2,3),None,1)]:
            self.assertFalse(self.lib.creatures_party_set_requirements(C.byref(self.r),(U8*4)(*party),req,count));self.assertEqual(bytes(self.r),before)
        self.assertFalse(self.lib.creatures_party_supports_capability(C.byref(self.r),16))
        self.assertTrue(self.lib.creatures_party_set_requirements(C.byref(self.r),(U8*4)(255,255,255,255),None,0))
        self.assertFalse(self.lib.creatures_party_supports_capability(C.byref(self.r),26))

if __name__=='__main__':unittest.main(verbosity=2)
