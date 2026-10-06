#!/usr/bin/env python3
"""Native C host tests. No emulator RAM injection and no Python rule surrogate."""
import ctypes as C
import json
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENABLED = [1,2,4,5,7,8,10,11,13,14,16,19,20,22,23,73,74,75,76,77,78]
U8, U16, U32 = C.c_ubyte, C.c_ushort, C.c_uint

class Instance(C.Structure):
    _fields_ = [('form_id', U8), ('flags', U8), ('level', U8), ('bond', U8),
                ('xp', U32), ('instance_id', U32), ('nickname_id', U16),
                ('trial_flags', U16), ('equipped', U8 * 2), ('polarity', U8),
                ('selected_command', U8), ('cosmetic_seed', U32)]

class Roster(C.Structure):
    _fields_ = [('instances', Instance * 160), ('party', U8 * 4),
                ('selected_party', U8), ('next_instance_id', U32),
                ('seen', U8 * 16), ('obtained', U8 * 16), ('rewards', U8 * 16),
                ('expedition_bond', U8 * 160), ('expedition_events', U8 * 64),
                ('lifetime_field_aid', U8 * 16)]

class Form(C.Structure):
    _fields_ = [('id',U8),('family',U8),('phase',U8),('polarity',U8),('tier',U8),('rarity',U8),
                ('stats',U8*5),('signature_ability',U8),('field_caps',U32),('name_id',U16),
                ('learnset_offset',U16),('learnset_count',U8),('evolution_count',U8),
                ('evolution_offset',U16),('sprite_offset',U32),('portrait_id',U16),('flags',U16)]

def build(directory, data=None, tag='good'):
    source = ROOT / 'src' / 'creature_data.c'
    if data is not None:
        source = Path(directory) / (tag + '.c')
        source.write_text(data)
    output = Path(directory) / (tag + '.so')
    subprocess.run([os.environ.get('CC','cc'), '-std=c99', '-O2', '-Wall', '-Wextra',
                    '-Werror', '-pedantic', '-fPIC', '-shared', '-I' + str(ROOT / 'src'),
                    str(ROOT / 'src' / 'creatures.c'), str(source), '-o', str(output)], check=True)
    lib = C.CDLL(str(output))
    signatures = {
        'creatures_roster_init': (None, [C.POINTER(Roster)]),
        'creatures_roster_validate': (C.c_int, [C.POINTER(Roster)]),
        'creatures_instance_validate': (C.c_int, [C.POINTER(Instance)]),
        'creatures_party_validate': (C.c_int, [C.POINTER(Roster)]),
        'creatures_migrate_legacy': (C.c_int, [C.POINTER(Roster), C.c_uint, C.c_uint]),
        'creatures_apply_story_floors': (C.c_int, [C.POINTER(Roster), C.c_uint]),
        'creatures_grant': (C.c_uint, [C.POINTER(Roster)] + [C.c_uint]*5),
        'creatures_grant_story': (C.c_uint, [C.POINTER(Roster), C.c_uint, C.c_uint]),
        'creatures_roster_count': (C.c_uint, [C.POINTER(Roster)]),
        'creatures_party_set': (C.c_int, [C.POINTER(Roster), C.POINTER(U8), U32]),
        'creatures_party_capabilities': (U32, [C.POINTER(Roster)]),
        'creatures_form': (C.POINTER(Form), [C.c_uint]),
        'creatures_family_trial': (C.c_uint, [C.c_uint]),
        'creatures_ability': (C.c_void_p, [C.c_uint]),
        'creatures_command_learned': (C.c_int, [C.c_uint, C.c_uint, C.c_uint]),
        'creatures_xp_threshold': (U32, [C.c_uint]),
        'creatures_level_for_xp': (C.c_uint, [U32]),
        'creatures_capabilities': (U32, [C.c_uint]),
        'creatures_add_xp': (C.c_int, [C.POINTER(Instance), U32]),
        'creatures_equip': (C.c_int, [C.POINTER(Instance), C.c_uint, C.c_uint]),
        'creatures_select_command': (C.c_int, [C.POINTER(Instance), C.c_uint]),
        'creatures_credit_event': (C.c_int, [C.POINTER(Roster), C.c_uint, U32, C.c_uint]),
        'creatures_begin_expedition': (None, [C.POINTER(Roster)]),
        'creatures_mark_trial': (C.c_int, [C.POINTER(Instance), C.c_uint]),
        'creatures_can_evolve': (C.c_uint, [C.POINTER(Instance), C.c_uint, C.c_int]),
        'creatures_evolve': (C.c_uint, [C.POINTER(Roster), C.c_uint, C.c_uint, C.c_int, C.c_int]),
        'creatures_defer_evolution': (C.c_uint, [C.POINTER(Instance)]),
    }
    for name, (result, args) in signatures.items():
        getattr(lib, name).restype = result
        getattr(lib, name).argtypes = args
    return lib

class CreatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='creature-tests-')
        cls.lib = build(cls.tmp.name)
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def setUp(self):
        self.r = Roster()
        self.lib.creatures_roster_init(C.byref(self.r))
    def migrate(self, chapter=0, selected=0):
        self.assertEqual(self.lib.creatures_migrate_legacy(C.byref(self.r),chapter,selected),1)
        return self.r
    def valid(self): self.assertEqual(self.lib.creatures_roster_validate(C.byref(self.r)),1)
    def grant(self, form=1, level=1, bond=0, flags=0, reward=0):
        return self.lib.creatures_grant(C.byref(self.r),form,level,bond,flags,reward)
    def test_fixed_instance_layout_and_roster_budget(self):
        self.assertEqual(C.sizeof(Instance),24)
        self.assertEqual(C.sizeof(Form),32)
        for field,offset in [('form_id',0),('xp',4),('instance_id',8),('nickname_id',12),
                             ('trial_flags',14),('equipped',16),('polarity',18),
                             ('selected_command',19),('cosmetic_seed',20)]:
            self.assertEqual(getattr(Instance,field).offset,offset)
        self.assertEqual(C.sizeof(Roster),4140)
    def test_catalog_and_generation_match(self):
        self.assertEqual(self.lib.creatures_catalog_validate(),1)
        subprocess.run(['python3', str(ROOT/'assets/creatures/generate_data.py'),'--check'],check=True)
    def test_valid_reserved_is_not_enabled(self):
        for i in range(256):
            self.assertEqual(bool(self.lib.creatures_form_id_valid(i)),1<=i<=128)
            self.assertEqual(bool(self.lib.creatures_form(i)),i in ENABLED)
        for i in [0,3,6,9,12,15,17,121,128,255,256]:
            before=bytes(self.r)
            self.assertEqual(self.grant(i),255)
            self.assertEqual(bytes(self.r),before)
    def test_every_xp_threshold_and_saturation(self):
        for level in range(1,51):
            xp=4*(level-1)**3
            self.assertEqual(self.lib.creatures_xp_threshold(level),xp)
            self.assertEqual(self.lib.creatures_level_for_xp(xp),level)
            if level>1:self.assertEqual(self.lib.creatures_level_for_xp(xp-1),level-1)
        self.assertEqual(self.lib.creatures_xp_threshold(0),0xffffffff)
        self.assertEqual(self.lib.creatures_xp_threshold(51),0xffffffff)
        self.assertEqual(self.lib.creatures_level_for_xp(0xffffffff),50)
        self.grant(); c=self.r.instances[0]
        self.assertEqual(self.lib.creatures_add_xp(C.byref(c),0xffffffff),1)
        self.assertEqual((c.xp,c.level),(470596,50))
        self.lib.creatures_add_xp(C.byref(c),0xffffffff)
        self.assertEqual(c.xp,470596)
    def test_all_phase_pairs_and_separate_polarity(self):
        counts={320:0,224:0,256:0}
        controls={0:2,2:4,4:1,1:3,3:0}
        for a in range(5):
            self.assertEqual(self.lib.creatures_generated_phase(a),(a+1)%5)
            for d in range(5):
                m=self.lib.creatures_phase_multiplier_q8(a,d)
                self.assertEqual(m,320 if controls[a]==d else 224 if controls[d]==a else 256)
                counts[m]+=1
        self.assertEqual(counts,{320:5,224:5,256:15})
        self.assertEqual(self.lib.creatures_phase_multiplier_q8(5,0),0)
        self.assertEqual(self.lib.creatures_generated_phase(5),255)
        self.assertEqual([self.lib.creatures_form(x).contents.phase for x in [1,4,7,10]],[1,0,0,2])
        self.assertEqual([self.lib.creatures_form(x).contents.polarity for x in [1,4,7,10]],[1,0,1,0])
    def test_capabilities_preserved_and_distinct_wood_roles(self):
        masks=[self.lib.creatures_capabilities(x) for x in [1,4,7,10]]
        for base in [1,4,7,10]:
            self.assertEqual(self.lib.creatures_capabilities(base),self.lib.creatures_capabilities(base+1))
            self.assertEqual(self.lib.creatures_legacy_spirit(base),self.lib.creatures_legacy_spirit(base+1))
        self.assertFalse(masks[1]&masks[2])
        self.assertEqual(self.lib.creatures_capabilities(128),0)
    def test_empty_roster(self):
        self.valid()
        self.assertEqual(list(self.r.party),[255]*4)
        self.assertEqual(self.r.selected_party,255)
    def test_migration_chapter_boundaries_and_compensation(self):
        expectations={0:([1,1],[20,20]),1:([12,12,8],[30,30,20]),
                      3:([16,16,16,14],[40,40,45,20]),
                      7:([20]*4,[50,50,55,50]),15:([20]*4,[50,50,55,50])}
        for chapter,(levels,bonds) in expectations.items():
            self.migrate(chapter,len(levels)-1)
            self.assertEqual([c.form_id for c in self.r.instances[:len(levels)]],[1,4,7,10][:len(levels)])
            self.assertEqual([c.level for c in self.r.instances[:len(levels)]],levels)
            self.assertEqual([c.bond for c in self.r.instances[:len(levels)]],bonds)
            self.assertEqual(self.r.selected_party,len(levels)-1)
            for c in self.r.instances[:len(levels)]:self.assertEqual(c.xp,4*(c.level-1)**3)
            self.valid()
    def test_invalid_migration_is_atomic(self):
        self.migrate()
        for chapter,selected in [(2,0),(4,0),(8,0),(16,0),(0,2),(3,4)]:
            before=bytes(self.r)
            self.assertEqual(self.lib.creatures_migrate_legacy(C.byref(self.r),chapter,selected),0)
            self.assertEqual(bytes(self.r),before)
    def test_story_floor_monotonic_and_idempotent(self):
        self.migrate(3)
        self.r.instances[0].bond=90
        self.lib.creatures_add_xp(C.byref(self.r.instances[0]),300000)
        xp=self.r.instances[0].xp
        self.lib.creatures_apply_story_floors(C.byref(self.r),7)
        self.assertEqual((self.r.instances[0].xp,self.r.instances[0].bond),(xp,90))
        before=bytes(self.r)
        self.assertEqual(self.lib.creatures_apply_story_floors(C.byref(self.r),7),0)
        self.assertEqual(bytes(self.r),before)
        self.lib.creatures_apply_story_floors(C.byref(self.r),0)
        self.assertEqual(bytes(self.r),before)
    def test_normal_story_joins_use_median_with_chapter_floor(self):
        self.migrate()
        self.assertEqual(self.lib.creatures_grant_story(C.byref(self.r),2,0),255)
        self.assertEqual(self.lib.creatures_grant_story(C.byref(self.r),2,1),2)
        self.assertEqual(self.r.instances[2].level,8)
        before=bytes(self.r)
        self.assertEqual(self.lib.creatures_grant_story(C.byref(self.r),2,1),2)
        self.assertEqual(bytes(self.r),before)
        for c in self.r.instances[:3]:
            c.level=30;c.xp=4*29**3
        self.assertEqual(self.lib.creatures_grant_story(C.byref(self.r),3,3),3)
        self.assertEqual(self.r.instances[3].level,30)
    def test_full_roster_never_overwrites_or_consumes_reward(self):
        for i in range(160):self.assertEqual(self.grant(),i)
        self.valid()
        self.assertEqual(list(self.r.party),[0,1,2,3])
        before=bytes(self.r)
        self.assertEqual(self.lib.creatures_grant_story(C.byref(self.r),2,1),255)
        self.assertEqual(self.grant(reward=5),255)
        self.assertEqual(bytes(self.r),before)
        self.assertEqual(self.lib.creatures_roster_count(C.byref(self.r)),160)
    def test_duplicate_reward_and_instance_exhaustion(self):
        self.assertEqual(self.grant(reward=5),0)
        before=bytes(self.r)
        self.assertEqual(self.grant(reward=5),255)
        self.assertEqual(self.grant(reward=1),255)
        self.assertEqual(bytes(self.r),before)
        self.r.next_instance_id=0xffffffff
        before=bytes(self.r)
        self.assertEqual(self.grant(),255)
        self.assertEqual(bytes(self.r),before)
    def test_party_references_and_field_guard_are_atomic(self):
        self.migrate(3,2)
        caps=self.lib.creatures_party_capabilities(C.byref(self.r))
        for party in [[0,0,1,2],[160,1,2,3],[254,1,2,3],[4,1,2,3],[0,1,2,255]]:
            before=bytes(self.r)
            self.assertEqual(self.lib.creatures_party_set(C.byref(self.r),(U8*4)(*party),caps),0)
            self.assertEqual(bytes(self.r),before)
        self.assertEqual(self.lib.creatures_party_set(C.byref(self.r),(U8*4)(3,2,1,0),caps),1)
        self.assertEqual(self.r.selected_party,1)
        self.assertEqual(self.lib.creatures_party_set(C.byref(self.r),(U8*4)(255,255,255,255),0),1)
        self.assertEqual(self.r.selected_party,255)
        self.valid()
    def test_duplicate_and_malformed_instance_mutations(self):
        self.migrate(3)
        good=bytes(self.r)
        mutations=[lambda r:setattr(r.instances[1],'instance_id',r.instances[0].instance_id),
                   lambda r:setattr(r.instances[0],'instance_id',0),
                   lambda r:setattr(r.instances[0],'form_id',128),
                   lambda r:setattr(r.instances[0],'flags',9),
                   lambda r:setattr(r.instances[0],'level',49),
                   lambda r:setattr(r.instances[0],'bond',101),
                   lambda r:setattr(r.instances[0],'xp',470597),
                   lambda r:setattr(r.instances[0],'polarity',0),
                   lambda r:setattr(r.instances[0],'trial_flags',2),
                   lambda r:setattr(r.instances[0],'nickname_id',1),
                   lambda r:r.instances[0].equipped.__setitem__(0,2),
                   lambda r:setattr(r.instances[0],'selected_command',1),
                   lambda r:setattr(r.instances[4],'flags',1),
                   lambda r:r.expedition_bond.__setitem__(4,1),
                   lambda r:r.expedition_bond.__setitem__(0,11),
                   lambda r:r.seen.__setitem__(15,128),
                   lambda r:r.obtained.__setitem__(0,0),
                   lambda r:r.rewards.__setitem__(0,0),
                   lambda r:setattr(r,'next_instance_id',1),
                   lambda r:setattr(r,'selected_party',255)]
        for mutate in mutations:
            r=Roster.from_buffer_copy(good);mutate(r)
            self.assertEqual(self.lib.creatures_roster_validate(C.byref(r)),0)
    def test_distinct_events_party_xp_storage_and_exp_cap(self):
        self.migrate(3)
        self.grant()
        stored=bytes(self.r.instances[4])
        beforexp=[c.xp for c in self.r.instances[:4]]
        beforebond=[c.bond for c in self.r.instances[:4]]
        for event in range(12):
            self.assertEqual(self.lib.creatures_credit_event(C.byref(self.r),event,10,0),1)
        self.assertEqual([c.xp for c in self.r.instances[:4]],[x+120 for x in beforexp])
        self.assertEqual([c.bond for c in self.r.instances[:4]],[b+10 for b in beforebond])
        self.assertEqual(bytes(self.r.instances[4]),stored)
        self.assertEqual(list(self.r.expedition_bond[:4]),[10]*4)
        before=bytes(self.r)
        self.assertEqual(self.lib.creatures_credit_event(C.byref(self.r),0,999,0),0)
        self.assertEqual(bytes(self.r),before)
        self.lib.creatures_begin_expedition(C.byref(self.r))
        self.lib.creatures_credit_event(C.byref(self.r),0,10,0)
        self.assertEqual(self.r.instances[0].bond,beforebond[0]+11)
    def test_party_swap_does_not_recredit_event(self):
        self.migrate(3)
        self.grant()
        self.lib.creatures_credit_event(C.byref(self.r),2,100,0)
        self.lib.creatures_party_set(C.byref(self.r),(U8*4)(4,1,2,3),0)
        before=bytes(self.r)
        self.assertEqual(self.lib.creatures_credit_event(C.byref(self.r),2,100,0),0)
        self.assertEqual(bytes(self.r),before)
    def test_lifetime_field_aid_and_bond_cap(self):
        self.migrate()
        self.r.instances[0].bond=99
        self.assertEqual(self.lib.creatures_credit_event(C.byref(self.r),384,0,1),1)
        self.assertEqual((self.r.instances[0].bond,self.r.instances[1].bond),(100,23))
        self.assertEqual(self.r.lifetime_field_aid[0]&1,1)
        self.lib.creatures_begin_expedition(C.byref(self.r))
        self.assertEqual(self.r.lifetime_field_aid[0]&1,1)
        self.lib.creatures_credit_event(C.byref(self.r),384,0,1)
        self.assertEqual(self.r.instances[1].bond,23)
        self.lib.creatures_credit_event(C.byref(self.r),385,0,1)
        self.assertEqual(self.r.instances[1].bond,26)
    def test_invalid_event_ids_do_not_mutate(self):
        self.migrate()
        for event,kind in [(512,0),(384,0),(383,1),(384,2),(1,3)]:
            before=bytes(self.r)
            self.assertEqual(self.lib.creatures_credit_event(C.byref(self.r),event,10,kind),-1)
            self.assertEqual(bytes(self.r),before)
    def test_all_evolutions_require_confirmation_and_preserve_commands(self):
        self.migrate(7)
        for slot,base in enumerate([1,4,7,10]):
            c=self.r.instances[slot]
            self.assertEqual(self.lib.creatures_mark_trial(C.byref(c),1<<slot),1)
            c.bond=100
            before=bytes(self.r)
            self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),7,1),0)
            self.assertEqual(self.lib.creatures_evolve(C.byref(self.r),slot,7,1,0),8)
            self.assertEqual(self.lib.creatures_defer_evolution(C.byref(c)),8)
            self.assertEqual(bytes(self.r),before)
            identity=(c.instance_id,c.xp,c.level,c.bond,c.cosmetic_seed,c.trial_flags,list(c.equipped))
            self.assertEqual(self.lib.creatures_evolve(C.byref(self.r),slot,7,1,1),0)
            self.assertEqual(c.form_id,base+1)
            after_evolution=bytes(self.r)
            self.assertEqual(self.lib.creatures_grant_story(C.byref(self.r),slot,7),slot)
            self.assertEqual(bytes(self.r),after_evolution)
            self.assertEqual((c.instance_id,c.xp,c.level,c.bond,c.cosmetic_seed,c.trial_flags,list(c.equipped)),identity)
            self.assertTrue(self.r.obtained[(base-1)//8] & (1<<((base-1)%8)))
            self.assertTrue(self.r.obtained[base//8] & (1<<(base%8)))
            self.assertEqual(self.lib.creatures_equip(C.byref(c),1,slot+5),1)
            self.assertEqual(self.lib.creatures_select_command(C.byref(c),1),1)
            self.assertEqual(self.lib.creatures_equip(C.byref(c),1,0),0)
            self.assertEqual(self.lib.creatures_evolve(C.byref(self.r),slot,7,1,1),2)
            self.valid()
    def test_visible_evolution_blockers(self):
        self.migrate();c=self.r.instances[0]
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),1,1),3)
        self.lib.creatures_add_xp(C.byref(c),4*11**3)
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),1,1),4)
        c.bond=40
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),0,1),5)
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),1,1),6)
        before=bytes(c)
        self.assertEqual(self.lib.creatures_mark_trial(C.byref(c),2),0)
        self.assertEqual(bytes(c),before)
        self.lib.creatures_mark_trial(C.byref(c),1)
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),1,0),7)
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),1,1),0)
    def test_evolved_forms_cannot_be_granted_below_evolution_level(self):
        for form in [2,5,8,11,14,20,23,74,76,78]:self.assertEqual(self.grant(form,1),255)
    def test_new_enabled_data_has_exact_authored_identity_and_commands(self):
        expected={13:(5,4,0,1,9,0x8100),14:(5,4,0,2,10,0xa100),16:(6,3,1,1,11,0x10004)}
        for form,(family,phase,polarity,tier,signature,caps) in expected.items():
            f=self.lib.creatures_form(form).contents
            self.assertEqual((f.family,f.phase,f.polarity,f.tier,f.signature_ability,f.field_caps),
                             (family,phase,polarity,tier,signature,caps))
            self.assertEqual(self.lib.creatures_legacy_spirit(form),255)
        for command in range(256):
            self.assertEqual(bool(self.lib.creatures_ability(command)),1<=command<=11 or 13<=command<=22)
        self.assertTrue(self.lib.creatures_command_learned(14,15,9))
        self.assertTrue(self.lib.creatures_command_learned(14,15,10))
        self.assertFalse(self.lib.creatures_command_learned(14,14,10))
        self.assertFalse(self.lib.creatures_command_learned(13,50,10))
        self.assertFalse(self.lib.creatures_command_learned(16,50,9))

    def test_northern_exact_policies_evolution_and_disabled_legendary_command(self):
        # Direct host grants exercise core contracts only, never acquisition.
        rows = [(19,7,0,0,13,0x200000,16,40,32),
                (22,8,1,0,15,0x400000,17,40,64),
                (73,25,4,1,17,0x800000,18,45,128),
                (75,26,2,1,19,0x4000,18,45,256),
                (77,27,3,0,21,0x1000000,20,50,512)]
        for base,family,phase,polarity,ability,caps,level,bond,trial in rows:
            with self.subTest(form=base):
                self.lib.creatures_roster_init(C.byref(self.r))
                for form in (base,base+1):
                    f=self.lib.creatures_form(form).contents
                    self.assertEqual((f.family,f.phase,f.polarity,f.tier,f.signature_ability,f.field_caps),
                                     (family,phase,polarity,form-base+1,ability+form-base,caps))
                    self.assertEqual(self.lib.creatures_family_trial(form),trial)
                    self.assertEqual(self.lib.creatures_legacy_spirit(form),255)
                self.assertEqual(self.grant(base+1,level-1,bond),255)
                self.assertEqual(self.grant(base,level-1,bond-1),0)
                c=self.r.instances[0]
                self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),16,1),3)
                self.lib.creatures_add_xp(C.byref(c),4*(level-1)**3-c.xp)
                self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),16,1),4)
                c.bond=bond
                for context in (0,7,8,15,32):
                    self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),context,1),5)
                self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),16,1),6)
                self.assertEqual(self.lib.creatures_mark_trial(C.byref(c),trial),1)
                self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),16,0),7)
                before=bytes(self.r)
                self.assertEqual(self.lib.creatures_evolve(C.byref(self.r),0,16,1,0),8)
                self.assertEqual(bytes(self.r),before)
                identity=bytes(c)
                self.assertEqual(self.lib.creatures_evolve(C.byref(self.r),0,16,1,1),0)
                expected=bytearray(identity);expected[0]=base+1
                self.assertEqual(bytes(c),bytes(expected))
                self.assertTrue(self.lib.creatures_command_learned(base+1,1,ability))
                self.assertFalse(self.lib.creatures_command_learned(base+1,level-1,ability+1))
                self.assertTrue(self.lib.creatures_command_learned(base+1,level,ability+1))
                before=bytes(self.r)
                self.assertEqual(self.lib.creatures_equip(C.byref(c),1,12),0)
                self.assertEqual(bytes(self.r),before)
                self.assertEqual(self.lib.creatures_equip(C.byref(c),1,ability+1),1)
                self.valid()

    def test_data_manifest_is_not_native_obtainability_evidence(self):
        result=json.loads(subprocess.check_output(['python3',str(ROOT/'assets/creatures/validate_catalog.py')]))
        self.assertEqual((result['reserved_identities'],result['authored_designs'],
                          result['enabled_native_core_forms'],result['enabled_evolution_edges'],
                          result['enabled_abilities']),(128,22,21,10,21))
        self.assertEqual(result['disabled_authored_forms'],[121])
        self.assertIn('separate native acquisition',result['native_obtainability'])
        # Host grants test data APIs; they do not navigate any acquisition route.
        manifest=json.loads((ROOT/'assets/creatures/enabled.json').read_text())
        self.assertEqual(manifest['enabled_form_ids'],ENABLED)

    def test_manifest_mutations_rejected_and_generator_is_deterministic(self):
        import sys, copy
        sys.path.insert(0,str(ROOT/'assets/creatures'))
        try:
            import generate_data, validate_catalog
            catalog=validate_catalog.load_json(ROOT/'assets/creatures/catalog.json')
            manifest=validate_catalog.load_json(ROOT/'assets/creatures/enabled.json')
            self.assertEqual(generate_data.generate(),generate_data.generate())
            self.assertEqual(generate_data.generate(),(ROOT/'src/creature_data.c').read_text())
            mutations=[('content_revision',1),('content_revision',2),('content_revision',True),
                       ('enabled_form_ids',ENABLED+[121]),('enabled_form_ids',ENABLED[:-1]),
                       ('enabled_form_ids',[True]+ENABLED[1:]),
                       ('enabled_ability_ids',list(range(1,13))),
                       ('enabled_evolutions',manifest['enabled_evolutions'][:-1])]
            for key,value in mutations:
                changed=copy.deepcopy(manifest);changed[key]=value
                self.assertTrue(validate_catalog.validate_enabled(catalog,changed),(key,value))
            changed=copy.deepcopy(catalog)
            changed['field_capabilities']=sorted(changed['field_capabilities'])
            self.assertTrue(validate_catalog.validate(changed))
            changed=copy.deepcopy(catalog)
            changed['forms']=[f for f in changed['forms'] if f['id']!=13]
            self.assertTrue(validate_catalog.validate_enabled(changed,manifest))
        finally:sys.path.pop(0)

    def test_legacy_migration_and_evolution_bytes_are_pinned(self):
        # SHA256 from the pre-revision-2 native core, captured before this change.
        # All roster bytes, IDs, commands, party, collection and credits are covered.
        expected={0:(1,'f3e7c130fe499e60e41d382cc718fe64eaa880d725b71a9388182b2e364a238b'),
                  1:(2,'66624d79efc9ef81fd8b17f0f399818b2baa125df846cd0f623e5e353e314072'),
                  3:(3,'cdb1a0ab5c30f37c6638f99282ded7185b56a0c315abb076f9cc1963ad40063a'),
                  7:(3,'fdb0cef10161b1fe00f87cdc21bec88a548fbc0473216e22a057eafe518d10e0'),
                  15:(3,'fdb0cef10161b1fe00f87cdc21bec88a548fbc0473216e22a057eafe518d10e0')}
        for chapter,(selected,digest) in expected.items():
            self.migrate(chapter,selected)
            self.assertEqual(hashlib.sha256(bytes(self.r)).hexdigest(),digest)
        self.migrate(7,3)
        for slot in range(4):
            c=self.r.instances[slot]
            self.lib.creatures_mark_trial(C.byref(c),1<<slot);c.bond=100
            self.assertEqual(self.lib.creatures_evolve(C.byref(self.r),slot,7,1,1),0)
            self.lib.creatures_equip(C.byref(c),1,slot+5)
            self.lib.creatures_select_command(C.byref(c),1)
        self.assertEqual(hashlib.sha256(bytes(self.r)).hexdigest(),
                         'e0b9f24e16858b192d54164e852d60e1e79216b6c2674da68cb493ca53b82b46')

    def test_regional_recruits_keep_party_story_instances_and_stay_owned(self):
        self.migrate(7,3)
        stories=bytes(self.r.instances)[:4*24];party=bytes(self.r.party)
        selected=self.r.selected_party
        self.assertEqual(self.grant(13,10,20,0,5),4)
        self.assertEqual(self.grant(16,10,20,0,6),5)
        self.assertEqual(bytes(self.r.instances)[:4*24],stories)
        self.assertEqual((bytes(self.r.party),self.r.selected_party),(party,selected))
        self.assertEqual([c.flags for c in self.r.instances[4:6]],[1,1])
        self.assertEqual([list(c.equipped) for c in self.r.instances[4:6]],[[9,0],[11,0]])
        recruits=bytes(self.r.instances)[4*24:6*24]
        all_story_caps=self.lib.creatures_party_capabilities(C.byref(self.r))
        before=bytes(self.r)
        self.assertEqual(self.lib.creatures_party_set(C.byref(self.r),(U8*4)(4,5,0,1),all_story_caps),0)
        self.assertEqual(bytes(self.r),before)
        self.assertEqual(self.lib.creatures_party_set(C.byref(self.r),(U8*4)(4,5,0,1),0),1)
        self.valid()
        for spirit in range(4):
            self.assertEqual(self.lib.creatures_grant_story(C.byref(self.r),spirit,7),spirit)
        self.assertEqual(bytes(self.r.instances)[:4*24],stories)
        self.assertEqual(self.lib.creatures_party_set(C.byref(self.r),(U8*4)(0,1,2,3),all_story_caps),1)
        self.assertEqual(bytes(self.r.instances)[4*24:6*24],recruits)
        self.assertEqual(self.lib.creatures_roster_count(C.byref(self.r)),6)
        self.valid()

    def test_regional_grant_failures_leave_every_byte_unchanged(self):
        self.migrate(7)
        for form,reward in [(13,5),(16,6)]:
            before=bytes(self.r)
            for flags,bad_reward in [(2,reward),(2,1),(0,1),(0,4)]:
                self.assertEqual(self.grant(form,10,20,flags,bad_reward),255)
                self.assertEqual(bytes(self.r),before)
            self.assertLess(self.grant(form,10,20,0,reward),160)
            before=bytes(self.r)
            self.assertEqual(self.grant(form,10,20,0,reward),255)
            self.assertEqual(bytes(self.r),before)
        while self.lib.creatures_roster_count(C.byref(self.r))<160:self.grant()
        before=bytes(self.r)
        for form in [13,14,16]:self.assertEqual(self.grant(form,50,100,0,7),255)
        self.assertEqual(bytes(self.r),before)
        self.valid()

    def test_trial_flags_are_exactly_family_specific_including_zero(self):
        trials={1:1,2:1,4:2,5:2,7:4,8:4,10:8,11:8,13:16,14:16,16:0,19:32,20:32,22:64,23:64,73:128,74:128,75:256,76:256,77:512,78:512}
        for form,trial in trials.items():
            self.lib.creatures_roster_init(C.byref(self.r))
            self.assertEqual(self.grant(form,50,100),0)
            good=bytes(self.r.instances[0])
            for flag in range(1024):
                c=Instance.from_buffer_copy(good)
                result=self.lib.creatures_mark_trial(C.byref(c),flag)
                self.assertEqual(bool(result),bool(trial and flag==trial),(form,flag))
                if not result:self.assertEqual(bytes(c),good)
                c=Instance.from_buffer_copy(good);c.trial_flags=flag
                self.assertEqual(bool(self.lib.creatures_instance_validate(C.byref(c))),flag in (0,trial),(form,flag))
            c=Instance.from_buffer_copy(good);c.flags|=2
            self.assertEqual(bool(self.lib.creatures_instance_validate(C.byref(c))),form<13)

    def test_water_evolution_requires_separate_context_and_all_conditions(self):
        self.assertEqual(self.grant(13,10,20,0,5),0)
        c=self.r.instances[0]
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),8,1),3)
        self.lib.creatures_add_xp(C.byref(c),4*14**3-c.xp)
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),8,1),4)
        c.bond=45
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),7,1),5)
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),8,1),6)
        self.assertEqual(self.lib.creatures_mark_trial(C.byref(c),16),1)
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),8,0),7)
        # Campaign ENDING_SEEN must be stripped; only quest2 claimed sets bit3.
        campaign_chapters=15
        context=lambda claimed:(campaign_chapters&7)|(8 if claimed else 0)
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),context(False),1),5)
        self.assertEqual(self.lib.creatures_can_evolve(C.byref(c),context(True),1),0)
        before=bytes(self.r)
        for ctx,sanctuary,confirmed,result in [(7,1,1,5),(8,0,1,7),(8,1,0,8),(16,1,1,5),(32,1,1,5),(64,1,1,1),(0x10000,1,1,1)]:
            self.assertEqual(self.lib.creatures_evolve(C.byref(self.r),0,ctx,sanctuary,confirmed),result)
            self.assertEqual(bytes(self.r),before)
        identity=bytes(c);party=bytes(self.r.party)
        self.assertEqual(self.lib.creatures_evolve(C.byref(self.r),0,8,1,1),0)
        expected=bytearray(identity);expected[0]=14
        self.assertEqual(bytes(c),bytes(expected))
        self.assertEqual(bytes(self.r.party),party)
        self.assertEqual(c.flags,1)
        self.assertEqual(self.r.obtained[1]&0x30,0x30)
        self.assertEqual(self.lib.creatures_equip(C.byref(c),1,10),1)
        self.assertEqual(list(c.equipped),[9,10])
        self.assertEqual(self.lib.creatures_select_command(C.byref(c),1),1)
        self.valid()
        before=bytes(self.r)
        self.assertEqual(self.lib.creatures_evolve(C.byref(self.r),0,8,1,1),2)
        self.assertEqual(bytes(self.r),before)

    def test_evolved_water_invalid_level_and_party_members_rejected(self):
        self.assertEqual(self.grant(14,14,45),255)
        self.assertEqual(self.grant(14,15,45),0)
        self.valid()
        good=bytes(self.r)
        for mutate in [lambda r:setattr(r.instances[0],'flags',3),
                       lambda r:setattr(r.instances[0],'trial_flags',1),
                       lambda r:setattr(r.instances[0],'polarity',1),
                       lambda r:r.instances[0].equipped.__setitem__(0,11),
                       lambda r:r.party.__setitem__(1,0),
                       lambda r:r.party.__setitem__(0,159),
                       lambda r:r.obtained.__setitem__(1,0)]:
            r=Roster.from_buffer_copy(good);mutate(r)
            self.assertEqual(self.lib.creatures_roster_validate(C.byref(r)),0)
        r=Roster.from_buffer_copy(good);r.instances[0].level=14;r.instances[0].xp=4*13**3
        self.assertEqual(self.lib.creatures_instance_validate(C.byref(r.instances[0])),0)
        self.assertEqual(self.lib.creatures_party_capabilities(C.byref(r)),0)

    def test_evolution_candidate_rejects_lost_command_without_mutation(self):
        source=(ROOT/'src/creature_data.c').read_text()
        broken=source.replace('{1, 9},\n    {15, 10}', '{1, 11},\n    {15, 10}',1)
        self.assertNotEqual(source,broken)
        lib=build(self.tmp.name,broken,'lost-water-command')
        self.assertEqual(lib.creatures_catalog_validate(),0)
        self.assertEqual(self.grant(13,15,45,0,5),0)
        self.lib.creatures_mark_trial(C.byref(self.r.instances[0]),16)
        before=bytes(self.r)
        self.assertEqual(lib.creatures_evolve(C.byref(self.r),0,8,1,1),1)
        self.assertEqual(bytes(self.r),before)

    def test_catalog_c_mutation_rejection(self):
        source=(ROOT/'src/creature_data.c').read_text()
        mutations=[('wrong_phase','{1, 1, 1, 1, 1, 0,','{1, 1, 4, 1, 1, 0,'),
                   ('wrong_polarity','{1, 1, 1, 1, 1, 0,','{1, 1, 1, 0, 1, 0,'),
                   ('lost_capability','0x00001222u','0x00000222u'),
                   ('evolution_cycle','{1, 2, 12, 40, 1, 1}','{1, 1, 12, 40, 1, 1}'),
                   ('disabled_target','{1, 2, 12, 40, 1, 1}','{1, 3, 12, 40, 1, 1}'),
                   ('wrong_family','{1, 2, 12, 40, 1, 1}','{1, 5, 12, 40, 1, 1}'),
                   ('missing_learned','{12, 5}','{12, 2}'),
                   ('bad_bond','{1, 2, 12, 40, 1, 1}','{1, 2, 12, 101, 1, 1}'),
                   ('weakened_old_level','{1, 2, 12, 40, 1, 1}','{1, 2, 11, 40, 1, 1}'),
                   ('wrong_water_trial','{13, 14, 15, 45, 16, 8}','{13, 14, 15, 45, 1, 8}'),
                   ('wrong_water_gate','{13, 14, 15, 45, 16, 8}','{13, 14, 15, 45, 16, 4}'),
                   ('water_cycle','{13, 14, 15, 45, 16, 8}','{14, 13, 15, 45, 16, 8}'),
                   ('metal_evolution','{13, 14, 15, 45, 16, 8}','{13, 16, 15, 45, 16, 8}'),
                   ('water_inherited_command','{1, 9},\n    {15, 10}', '{1, 10},\n    {15, 10}'),
                   ('water_delayed_signature','{15, 10}', '{16, 10}'),
                   ('water_missing_link','0x0000a100u','0x00008100u'),
                   ('water_polarity','{13, 5, 4, 0, 1, 0,','{13, 5, 4, 1, 1, 0,'),
                   ('metal_phase','{16, 6, 3, 1, 1, 0,','{16, 6, 4, 1, 1, 0,'),
                   ('metal_legendary','{16, 6, 3, 1, 1, 0,','{16, 6, 3, 1, 1, 1,'),
                   ('enabled_placeholder','{16, 6, 3, 1, 1, 0,','{121, 6, 3, 1, 1, 0,'),
                   ('bad_stat_range','{35, 20, 30, 55, 40}','{0, 55, 30, 55, 40}'),
                   ('ability_id_gap','{11, 3, 90,','{12, 3, 90,'),
                   ('ability_cooldown','{9, 4, 90,','{9, 4, 89,'),
                   ('legacy_mapping','{1, 4, 7, 10}', '{1, 4, 7, 13}'),
                   ('bad_learn_range','13, 12, 1, 1, 4, 0, 13, 1','13, 255, 1, 1, 4, 0, 13, 1'),
                   ('orphan_edge_offset','13, 12, 1, 1, 4, 0, 13, 1','13, 12, 1, 1, 0, 0, 13, 1')]
        for tag,old,new in mutations:
            self.assertIn(old,source,tag)
            lib=build(self.tmp.name,source.replace(old,new,1),tag)
            self.assertEqual(lib.creatures_catalog_validate(),0,tag)

if __name__ == '__main__':
    from test_creature_sparse import SparseCreatureTests
    unittest.main(verbosity=2)
