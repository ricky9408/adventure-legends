#!/usr/bin/env python3
"""Native C host tests. No emulator RAM injection and no Python rule surrogate."""
import ctypes as C
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
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
            self.assertEqual(bool(self.lib.creatures_form(i)),i in [1,2,4,5,7,8,10,11])
        for i in [0,3,13,14,16,121,128,255,256]:
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
        for form in [2,5,8,11]:self.assertEqual(self.grant(form,1),255)
    def test_catalog_c_mutation_rejection(self):
        source=(ROOT/'src/creature_data.c').read_text()
        mutations=[('wrong_phase','{1, 1, 1, 1, 1, 0,','{1, 1, 4, 1, 1, 0,'),
                   ('wrong_polarity','{1, 1, 1, 1, 1, 0,','{1, 1, 1, 0, 1, 0,'),
                   ('lost_capability','0x00001222u','0x00000222u'),
                   ('evolution_cycle','{1, 2, 12, 40, 1, 1}','{1, 1, 12, 40, 1, 1}'),
                   ('disabled_target','{1, 2, 12, 40, 1, 1}','{1, 3, 12, 40, 1, 1}'),
                   ('wrong_family','{1, 2, 12, 40, 1, 1}','{1, 5, 12, 40, 1, 1}'),
                   ('missing_learned','{12, 5}','{12, 2}'),
                   ('bad_bond','{1, 2, 12, 40, 1, 1}','{1, 2, 12, 101, 1, 1}')]
        for tag,old,new in mutations:
            self.assertIn(old,source,tag)
            lib=build(self.tmp.name,source.replace(old,new,1),tag)
            self.assertEqual(lib.creatures_catalog_validate(),0,tag)

if __name__ == '__main__': unittest.main(verbosity=2)
