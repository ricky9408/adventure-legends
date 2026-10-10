#!/usr/bin/env python3
"""Independent Magma C catalog/admission tests; host grants are not route proof.

Reads the reviewed allocation and frozen released policy as independent oracles.
The native executable exercises the actual production C, including ASan/UBSan.
No existing historical fixture, production table or saved record is rewritten.
"""
import ctypes as C
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import re
import shlex
import subprocess
import tempfile
import unittest

from test_creatures import build, Instance, Roster, Form, U8, U16, ROOT
from test_creature_sparse import edit_array
from test_southern_creature_core import historical_prefix_bytes
from test_southern_catalog import RETURN_FORMS

ALLOCATION = json.loads((ROOT / 'docs/magma-design/magma_allocation.json').read_text())
NEW = list(range(31, 49)) + list(range(95, 101))
OLD = [1,2,4,5,7,8,10,11,13,14,16,19,20,22,23,73,74,75,76,77,78,25,26,28,29] + list(range(79,95))
ENABLED = OLD + NEW
HISTORY = json.loads((ROOT / 'assets/history/creatures-v1-v4.json').read_text())['forms']
CAPABILITIES = ['break_crack','burn_thorns','draw_ore','drive_sail','earth_socket',
                'expose_fire','expose_stone','expose_wind','fill_basin','fire_socket',
                'grow_bridge','grow_roots','ignite','link_pools','press_weight',
                'reveal_current','tune_latch','turn_vane','uncap_well','wind_socket',
                'wood_socket','reel_load','store_heat','float_load','align_rail','refract_beam']


class Evolution(C.Structure):
    _fields_ = [('from_id',U8),('to_id',U8),('min_level',U8),('min_bond',U8),
                ('trial_flag',U16),('chapter_flags',U16)]


class Learn(C.Structure):
    _fields_ = [('level',U8),('ability_id',U8)]


class Ability(C.Structure):
    _fields_ = [('id',U8),('phase',U8),('cooldown_updates',U16),('field_caps',C.c_uint)]


def configure(lib):
    signatures = {
        'creatures_form_allowed_revision':(C.c_int,[C.c_uint]*2),
        'creatures_family_revision':(C.c_uint,[C.c_uint]*2),
        'creatures_command_learned_revision':(C.c_int,[C.c_uint]*4),
        'creatures_trial_allowed_mask':(C.c_uint,[C.c_uint]*2),
        'creatures_instance_validate_revision':(C.c_int,[C.POINTER(Instance),C.c_uint]),
        'creatures_roster_validate_revision':(C.c_int,[C.POINTER(Roster),C.c_uint]),
        'creatures_trial_mask_for_key':(C.c_uint,[C.c_uint]*2),
        'creatures_mark_trial_qualified':(C.c_int,[C.POINTER(Instance),C.c_uint,C.c_uint]),
        'creatures_has_trial_qualified':(C.c_int,[C.POINTER(Instance),C.c_uint,C.c_uint]),
        'creatures_evolution_count':(C.c_uint,[C.c_uint]),
        'creatures_evolution_at':(C.POINTER(Evolution),[C.c_uint,C.c_uint]),
        'creatures_evolution_to':(C.POINTER(Evolution),[C.c_uint,C.c_uint]),
        'creatures_can_evolve_to':(C.c_uint,[C.POINTER(Instance),C.c_uint,C.c_uint,C.c_int]),
        'creatures_evolve_to':(C.c_uint,[C.POINTER(Roster),C.c_uint,C.c_uint,C.c_uint,C.c_int,C.c_int]),
        'creatures_supports_capability':(C.c_int,[C.c_uint]*2),
        'creatures_name':(C.c_char_p,[C.c_uint]),
        'creatures_ability_name':(C.c_char_p,[C.c_uint]),
    }
    for name,(result,args) in signatures.items():
        function=getattr(lib,name);function.restype=result;function.argtypes=args
    return lib


def compile_native(*, sanitized=False, data=None):
    with tempfile.TemporaryDirectory(prefix='magma-native-') as directory:
        directory=Path(directory)
        source=ROOT/'src/creature_data.c'
        if data is not None:
            source=directory/'creature_data.c';source.write_text(data)
        command=shlex.split(os.environ.get('HOST_CC','cc')) + [
            '-std=c99','-O1' if sanitized else '-O2','-Wall','-Wextra','-Werror','-pedantic',
            '-I'+str(ROOT/'src')]
        if sanitized:command += ['-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie']
        if data is not None:command += ['-DEXPECT_INVALID_CATALOG']
        command += [str(ROOT/'src/creatures.c'),str(source),str(ROOT/'tests/magma_creature_native.c'),'-o',str(directory/'test')]
        subprocess.run(command,check=True)
        subprocess.run([str(directory/'test')],check=True,
                       env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'))


class MagmaCreatureCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='magma-creature-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.lib=configure(build(cls.temp.name))

    def test_entire_released_revision4_prefix_is_byte_exact(self):
        expected=[('creature_forms',1312,'8ff46756f002331002cef3622f89790361527f63f2fd6a95baac36ae6bb98260'),
                  ('creature_learnsets',122,'42f86b6e1e8c47088fda179261880fe0dab31facc4c1f7b666e588d01d9e53cd'),
                  ('creature_evolutions',160,'b34d98b7c74beaf2c03ded7f7b90ca3c7765da622709102972d77572d4094182'),
                  ('creature_abilities',328,'332f28e80476149567bf9d63f5bf23c722aaa803d8a895a4d6b3ac1ccf003268')]
        for name,count,digest in expected:
            self.assertEqual(hashlib.sha256(historical_prefix_bytes(self.lib,name,count)).hexdigest(),digest,name)

    def test_exact_allocation_every_form_command_capability_and_polarity(self):
        self.assertTrue(self.lib.creatures_catalog_validate())
        self.assertEqual(ALLOCATION['exact_new_form_ids'],NEW)
        forms=(Form*65).in_dll(self.lib,'creature_forms')
        learns=(Learn*102).in_dll(self.lib,'creature_learnsets')
        abilities=(Ability*65).in_dll(self.lib,'creature_abilities')
        self.assertEqual([f.id for f in forms],ENABLED)
        self.assertEqual([a.id for a in abilities],list(range(1,12))+list(range(13,67)))
        self.assertFalse(self.lib.creatures_ability(12))
        phases=['wood','fire','earth','metal','water'];polarities=['yin','yang']
        for authored in ALLOCATION['forms']:
            f=self.lib.creatures_form(authored['id']).contents
            cap=sum(1<<CAPABILITIES.index(c) for c in authored['field_caps'])
            self.assertEqual((f.family,f.tier,f.rarity,f.phase,f.polarity),
                             (int(authored['family_id'][1:]),authored['tier'],0,phases.index(authored['phase']),polarities.index(authored['polarity'])))
            self.assertEqual(list(f.stats),[authored['stats'][key] for key in ['vitality','power','guard','focus','haste']])
            self.assertEqual(sum(f.stats),285 if f.tier==3 else 180 if f.tier==1 else 240)
            self.assertEqual(f.signature_ability,authored['signature_ability'])
            self.assertEqual(f.field_caps,cap)
            self.assertEqual(self.lib.creatures_name(f.id).decode(),authored['name'])
            pairs=[(learns[i].level,learns[i].ability_id) for i in range(f.learnset_offset,f.learnset_offset+f.learnset_count)]
            self.assertEqual(pairs,[(item['min_level'],item['ability_id']) for item in authored['learnset']])
            for level in [0,1,25,26,31,32,50,51]:
                for ability in range(68):
                    self.assertEqual(bool(self.lib.creatures_command_learned(f.id,level,ability)),1<=level<=50 and any(a==ability and l<=level for l,a in pairs),(f.id,level,ability))
            a=next(a for a in abilities if a.id==f.signature_ability)
            self.assertEqual((a.phase,a.cooldown_updates,a.field_caps),(f.phase,authored['command']['timing_updates']['cooldown'],cap))
            self.assertEqual(self.lib.creatures_ability_name(a.id).decode(),authored['command']['name'])
            for key in range(1,27):
                self.assertEqual(bool(self.lib.creatures_supports_capability(f.id,key)),bool(cap&(1<<(key-1))))
        flipped=[]
        for e in ALLOCATION['evolutions']:
            before=self.lib.creatures_form(e['from']).contents
            after=self.lib.creatures_form(e['to']).contents
            if before.polarity!=after.polarity:flipped.append(after.id)
        self.assertEqual(flipped,[39,48])

    def test_exact_revision_whitelists_and_historical_command_trial_differential(self):
        lookup={p['id']:p for p in HISTORY}
        for revision in [0,1,2,3,4,5,6,7,255,256,0xffffffff]:
            for form in list(range(130))+[256,65537,0xffffffff]:
                expected=form in ENABLED+list(range(49,73))+RETURN_FORMS if revision==7 else form in ENABLED+list(range(49,73)) if revision==6 else form in ENABLED if revision==5 else form in lookup and revision in range(1,5) and bool(lookup[form]['revision_bits']&(1<<(revision-1)))
                self.assertEqual(bool(self.lib.creatures_form_allowed_revision(form,revision)),expected,(form,revision))
                if revision in (1,2,3,4):
                    p=lookup.get(form)
                    self.assertEqual(self.lib.creatures_trial_allowed_mask(form,revision),p['trial_mask'] if expected else 0)
                    self.assertEqual(self.lib.creatures_family_revision(form,revision),p['family'] if expected else 0)
                    for level,ability in itertools.product([0,1,12,16,20,26,32,50,51],[0,1,12,23,43,49,66,67,255,256,65537]):
                        learned=bool(expected and 1<=level<=50 and any(a==ability and l<=level for l,a in p['learn']))
                        self.assertEqual(bool(self.lib.creatures_command_learned_revision(form,level,ability,revision)),learned)

    def test_current_and_old_malformed_instances_match_independent_reference(self):
        old={p['id']:p for p in HISTORY}
        new={f['id']:f for f in ALLOCATION['forms']}
        def reference(c,revision):
            if revision not in range(1,6):return False
            if not c.form_id:return not any(bytes(c))
            p=old.get(c.form_id)
            if revision<5 and (not p or not p['revision_bits']&(1<<(revision-1))):return False
            if p:
                family,polarity,minimum,mask,learn=p['family'],p['polarity'],p['min_level'],p['trial_mask'],p['learn']
            elif c.form_id in new and revision==5:
                p=new[c.form_id];family=int(p['family_id'][1:]);polarity=['yin','yang'].index(p['polarity'])
                minimum=p['evolution']['min_level'] if p['evolution'] else 1
                mask=1 if c.form_id in (31,34) else 3 if 11<=family<=16 else 1
                learn=[(l['min_level'],l['ability_id']) for l in p['learnset']]
            else:return False
            if not(c.flags&1) or c.flags&~7 or not 1<=c.level<=50 or c.bond>100 or c.xp>470596 or not 0<c.instance_id<0xffffffff or c.nickname_id:return False
            if c.flags&2 and not 1<=family<=4:return False
            if c.polarity!=polarity or c.level<minimum or c.trial_flags&~mask:return False
            if revision==5 and family in (11,12) and c.trial_flags==2:return False
            if c.xp<4*(c.level-1)**3 or c.level<50 and c.xp>=4*c.level**3:return False
            if c.selected_command>1 or not c.equipped[c.selected_command] or c.equipped[0] and c.equipped[0]==c.equipped[1]:return False
            return all(not a or any(command==a and l<=c.level for l,command in learn) for a in c.equipped)
        randomizer=random.Random(0x4d41474d)
        for form in ENABLED:
            roster=Roster();self.lib.creatures_roster_init(C.byref(roster))
            self.assertEqual(self.lib.creatures_grant(C.byref(roster),form,50,100,0,0),0)
            valid=roster.instances[0]
            cases=[bytes(valid)]
            for _ in range(160):
                case=bytearray(bytes(valid));case[randomizer.randrange(24)]=randomizer.randrange(256);cases.append(case)
            for case in cases:
                c=Instance.from_buffer_copy(case)
                for revision in range(1,6):
                    expected=reference(c,revision)
                    self.assertEqual(bool(self.lib.creatures_instance_validate_revision(C.byref(c),revision)),expected,(form,revision,bytes(c).hex()))
                    if revision==5:self.assertEqual(bool(self.lib.creatures_instance_validate(C.byref(c))),expected)

    def test_disabled_forms_and_wide_ids_reject_without_mutation(self):
        roster=Roster();self.lib.creatures_roster_init(C.byref(roster));before=bytes(roster)
        for form in list(range(130))+[256,65537,0xffffffff]:
            if form in ENABLED+list(range(49,73))+RETURN_FORMS+list(range(105,121)):continue
            self.assertFalse(self.lib.creatures_form(form))
            self.assertEqual(self.lib.creatures_grant(C.byref(roster),form,50,100,0,0),255)
            self.assertEqual(bytes(roster),before)
        for form in NEW:
            self.assertEqual(self.lib.creatures_family_trial(form),0)

    def test_native_strict(self):compile_native()
    def test_native_address_and_undefined_sanitizers(self):compile_native(sanitized=True)

    def test_corrupt_new_rom_rows_fail_closed(self):
        original=(ROOT/'src/creature_data.c').read_text()
        def replace_form(source,form,transform):
            pattern=rf'(?m)^    \{{{form},[^\n]+$'
            def replace(body):
                result,count=re.subn(pattern,lambda match:transform(match[0]),body)
                self.assertEqual(count,1);return result
            return edit_array(source,'creature_forms',replace)
        mutations=[]
        for form in [33,36]:
            mutations.append((f'tier3-total-{form}',replace_form(original,form,lambda row:re.sub(r', \{(\d+),',lambda m:', {'+str(int(m[1])+1)+',',row,count=1))))
        for form in [38,39,47,48]:
            # Change only this form's polarity, not its family or other rows.
            def flip(row):
                parts=row.split(',');parts[3]=' '+str(1-int(parts[3]));return ','.join(parts)
            mutations.append((f'polarity-{form}',replace_form(original,form,flip)))
        for form in [33,36,39,48,100]:
            mutations.append((f'lost-capability-{form}',replace_form(original,form,lambda row:re.sub(r'0x[0-9a-fA-F]+u','0x00000000u',row,count=1))))
        for index,key in [('creature_form_index',33),('creature_ability_index',66),('creature_incoming_evolution_index',36)]:
            for bad in [0,255]:
                def corrupt(body,key=key,bad=bad):
                    values=[int(v) for v in re.findall(r'\d+',body)];values[key]=bad
                    return '    '+', '.join(map(str,values))+','
                mutations.append((f'{index}-{bad}',edit_array(original,index,corrupt)))
        for form in [1,37,49,121,128]:
            def corrupt_topology(body,form=form):
                rows=body.splitlines()
                # Explicit zero row followed by one row per immutable form ID.
                self.assertEqual(len(rows),129)
                rows[form]=re.sub(r'\{(\d+),\s*\d+\}',r'{\1, 0}',rows[form])
                return '\n'.join(rows)
            mutations.append((f'terminal-topology-{form}',edit_array(original,'creature_terminal_policy',corrupt_topology)))
        for name,data in mutations:
            with self.subTest(name=name):
                self.assertNotEqual(original,data)
                lib=build(self.temp.name,data,'magma-bad-'+name)
                self.assertFalse(lib.creatures_catalog_validate(),name)
                if name=='terminal-topology-37':
                    roster=Roster();lib.creatures_roster_init(C.byref(roster))
                    self.assertEqual(lib.creatures_grant(C.byref(roster),1,50,100,0,0),0)
                    self.assertEqual(lib.creatures_grant(C.byref(roster),37,50,100,0,0),1)
                    output=(U16*6)(*[0x7777]*6)
                    lib.creatures_collection_coverage.argtypes=[C.POINTER(Roster),C.c_void_p]
                    self.assertEqual(lib.creatures_collection_coverage(C.byref(roster),output),0)
                    self.assertEqual(bytes(output),bytes(12),'late metadata failure must clear partial coverage')


if __name__=='__main__':unittest.main(verbosity=2)
