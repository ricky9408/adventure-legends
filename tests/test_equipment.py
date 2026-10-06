#!/usr/bin/env python3
"""Native equipment/damage contract tests; execute shipped C, not a Python model.

Synthetic immutable catalogs exercise the otherwise unreachable 48-slot limit
and future aggregate stat caps. Those fixtures do not enable content in the ROM.
"""
import ctypes as C
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
U8, U16, U32, S16 = C.c_ubyte, C.c_ushort, C.c_uint, C.c_short
LEGACY_IDS = [1, 2, 9, 10, 17, 18, 33, 34, 49, 50, 65, 81, 82, 3, 11, 19, 35, 51, 83]
SOUTHERN_IDS = [4, 12, 36, 52, 66, 84]
MAGMA_IDS = [20, 37, 53, 67, 85, 5]
IDS = LEGACY_IDS + SOUTHERN_IDS + MAGMA_IDS
OK, INVALID, BUSY, INCOMPATIBLE, FULL, DUPLICATE, ALREADY, PROTECTED, CONFIRM = range(9)


class Record(C.Structure):
    _fields_ = [('item_id', U16), ('rank', U8), ('flags', U8), ('quantity', U8), ('reserved', U8 * 3)]


class State(C.Structure):
    _fields_ = [('bag', Record * 48), ('equipped', U8 * 5), ('settings_reserved', U8 * 11),
                ('seen', U8 * 64), ('wallet_key_reserved', U8 * 16),
                ('reward_claims', U8 * 8), ('reserved', U8 * 24)]


class Bonuses(C.Structure):
    _fields_ = [(k, S16) for k in ['attack_q4', 'defense_q4', 'hp_q4', 'speed_q8_delta',
                                  'roll_reduction', 'power_reduction', 'reach_px', 'stagger']]


class Definition(C.Structure):
    _fields_ = [('id', U16), ('slot', U8), ('weapon_class', U8), ('flags', U8),
                ('phase', U8), ('reserved', U8 * 2), ('stats', Bonuses)]


class Move(C.Structure):
    _fields_ = [(k, U8) for k in ['windup', 'active', 'recovery', 'damage_q4', 'reach_px', 'half_width_px']]


class Weapon(C.Structure):
    _fields_ = [('id', U8), ('move_count', U8), ('combo_window', U8), ('buffer', U8),
                ('lunge_q8', U16), ('projectile_speed_q8', U16), ('charge_min_updates', U8),
                ('charge_max_updates', U8), ('max_live_arrows', U8), ('reserved', U8), ('moves', Move * 3)]


class Stats(C.Structure):
    _fields_ = [('max_hp_q4', U16), ('speed_q8', U16), ('diagonal_q8', U16)] + [
        (k, U8) for k in ['attack_q4', 'defense_q4', 'roll_cooldown', 'power_cooldown',
                          'reach_px', 'stagger', 'weapon_class', 'phase']]


class Comparison(C.Structure):
    _fields_ = [('before', Stats), ('after', Stats), ('hp_before_q4', U16), ('hp_after_q4', U16),
                ('slot', U8), ('old_ref', U8), ('new_ref', U8), ('reserved', U8)]


def build(directory, tag='normal', data=None):
    source = ROOT / 'src/equipment_data.c'
    if data is not None:
        source = Path(directory) / (tag + '.c')
        source.write_text(data)
    output = Path(directory) / (tag + '.so')
    subprocess.run([os.environ.get('CC', 'cc'), '-std=c99', '-O2', '-Wall', '-Wextra',
                    '-Werror', '-pedantic', '-fPIC', '-shared', '-I' + str(ROOT / 'src'),
                    str(ROOT / 'src/equipment.c'), str(source), str(ROOT / 'src/combat_rules.c'),
                    str(ROOT / 'src/creatures.c'), str(ROOT / 'src/creature_data.c'),
                    '-o', str(output)], check=True)
    lib = C.CDLL(str(output))
    P, UINT = C.POINTER, C.c_uint
    signatures = {
        'equipment_init': (None, [P(State)]),
        'equipment_definition': (P(Definition), [UINT]),
        'equipment_weapon': (P(Weapon), [UINT]),
        'equipment_name': (C.c_char_p, [UINT]),
        'equipment_description': (C.c_char_p, [UINT, UINT]),
        'equipment_catalog_validate': (C.c_int, []),
        'equipment_record_validate': (C.c_int, [P(Record)]),
        'equipment_refs_validate': (C.c_int, [P(State)]),
        'equipment_reserved_validate': (C.c_int, [P(State)]),
        'equipment_validate': (C.c_int, [P(State)]),
        'equipment_count': (UINT, [P(State)]),
        'equipment_find': (UINT, [P(State), UINT]),
        'equipment_seen': (C.c_int, [P(State), UINT]),
        'equipment_reward_item': (UINT, [UINT]),
        'equipment_reward_source': (UINT, [UINT]),
        'equipment_reward_claimed': (C.c_int, [P(State), UINT]),
        'equipment_claim': (UINT, [P(State), UINT, UINT, P(UINT)]),
        'equipment_claim_many': (UINT, [P(State), P(U8), UINT]),
        'equipment_derive': (C.c_int, [P(State), UINT, P(Stats)]),
        'equipment_preview': (UINT, [P(State), UINT, UINT, UINT, UINT, UINT, P(Comparison)]),
        'equipment_equip': (UINT, [P(State), UINT, UINT, UINT, P(U16), UINT, P(Comparison)]),
        'equipment_unequip': (UINT, [P(State), UINT, UINT, P(U16), UINT, P(Comparison)]),
        'equipment_discard': (UINT, [P(State), UINT, UINT, P(U16), UINT, C.c_int]),
        'combat_phase_multiplier_q8': (UINT, [UINT, UINT]),
        'combat_damage_q4': (UINT, [UINT, UINT, UINT, UINT, UINT, C.c_int]),
        'combat_field_allows': (C.c_int, [U32, U32]),
        'creatures_phase_multiplier_q8': (UINT, [UINT, UINT]),
    }
    for name, (result, args) in signatures.items():
        getattr(lib, name).restype, getattr(lib, name).argtypes = result, args
    return lib


def variant_data(mode):
    text = (ROOT / 'src/equipment_data.c').read_text()
    if mode == 'capacity':
        extra = ''.join('    [%d] = {%d, 1, 0, 0, 255, {0, 0}, {0, 0, 0, 0, 0, 0, 0, 0}},\n' %
                        (i, i) for i in range(100, 147))
        return text.replace('    [1] = {1, 0,', extra + '    [1] = {1, 0,', 1)
    def patch(match):
        item_id, prefix, body = int(match[1]), match[2], match[3]
        if item_id not in [1, 33, 49, 65, 81]:
            return match[0]
        reach = 4 if item_id == 1 else 0
        values = {'caps': [24, 8, 32, 16, 6, 8, reach, 3],
                  'minimum': [0, 0, 0, -16, 0, 0, 0, 0],
                  'overflow': [32767] * 8,
                  'negative': [-32768] * 8}[mode]
        return '    [%d] = %s{%s}},' % (item_id, prefix, ', '.join(map(str, values)))
    return re.sub(r'    \[(\d+)\] = (\{\d+, \d+, \d+, \d+, 255, \{0, 0\}, )\{([^}]+)\}\},', patch, text)


class EquipmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='equipment-tests-')
        cls.lib = build(cls.tmp.name)
        cls.variants = {m: build(cls.tmp.name, m, variant_data(m))
                        for m in ['capacity', 'caps', 'minimum', 'overflow', 'negative']}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.s, self.hp = State(), U16(96)
        self.lib.equipment_init(C.byref(self.s))

    def claim(self, item, lib=None):
        lib = lib or self.lib
        ref = C.c_uint(999)
        result = lib.equipment_claim(C.byref(self.s), item, lib.equipment_reward_source(item), C.byref(ref))
        self.assertEqual(result, OK)
        return ref.value

    def equip(self, slot, ref, lib=None, base=96):
        lib = lib or self.lib
        self.assertEqual(lib.equipment_equip(C.byref(self.s), slot, ref, base, C.byref(self.hp), 0, None), OK)

    def derive(self, base=96, lib=None):
        out = Stats()
        self.assertEqual((lib or self.lib).equipment_derive(C.byref(self.s), base, C.byref(out)), 1)
        return out

    def valid(self):
        self.assertEqual(self.lib.equipment_validate(C.byref(self.s)), 1)

    def test_layout_and_wire_offsets(self):
        self.assertEqual(C.sizeof(Record), 8)
        self.assertEqual(C.sizeof(State), 512)
        self.assertEqual(C.sizeof(Definition), 24)
        self.assertEqual(C.sizeof(Stats), 14)
        self.assertEqual(C.sizeof(Comparison), 36)
        for field, offset in [('bag', 0), ('equipped', 384), ('settings_reserved', 389),
                              ('seen', 400), ('wallet_key_reserved', 464), ('reward_claims', 480), ('reserved', 488)]:
            self.assertEqual(getattr(State, field).offset, offset)
        self.assertEqual(self.s.bag[0].item_id, 1)
        self.assertEqual(list(self.s.equipped), [0, 255, 255, 255, 255])
        self.assertEqual(self.lib.equipment_count(C.byref(self.s)), 1)
        self.assertEqual(self.lib.equipment_reward_claimed(C.byref(self.s), 0), 1)
        self.valid()

    def test_catalog_matches_fixed_source_and_bounds(self):
        self.assertEqual(self.lib.equipment_catalog_validate(), 1)
        subprocess.run(['python3', str(ROOT / 'assets/equipment/generate_data.py'), '--check'], check=True)
        catalog = json.loads((ROOT / 'assets/equipment/catalog.json').read_text())
        for item in catalog['items']:
            d = self.lib.equipment_definition(item['id']).contents
            for name, value in item['stats'].items():
                self.assertEqual(getattr(d.stats, name), value)
            self.assertEqual(self.lib.equipment_name(item['id']).decode(), item['name'])
            self.assertEqual(d.phase, 255)
        for item_id in list(range(1024)) + [65535, 0xffffffff]:
            self.assertEqual(bool(self.lib.equipment_definition(item_id)), item_id in IDS)
        for source in range(256):
            self.assertEqual(self.lib.equipment_reward_item(source), IDS[source] if source < len(IDS) else 0)
        self.assertEqual(self.lib.equipment_description(1, 2), b'')
        self.assertEqual(self.lib.equipment_name(65535), b'Empty')

    def test_original_nineteen_catalog_rows_and_starter_wire_are_frozen(self):
        catalog = json.loads((ROOT / 'assets/equipment/catalog.json').read_text())
        catalog['items'] = catalog['items'][:19]
        catalog['reward_sources'] = catalog['reward_sources'][:19]
        # Canonical snapshot taken before the Southern append. Covers every old
        # name, description, stat, weapon parameter, bound, and source pairing.
        digest = hashlib.sha256(json.dumps(catalog, sort_keys=True,
                                           separators=(',', ':')).encode()).hexdigest()
        self.assertEqual(digest, '710d174fe8126c9a581641a0f590895ba9b5826b783f2193ca2a88910ed3aa66')
        expected = bytearray(512)
        expected[:8] = bytes([1, 0, 0, 1, 1, 0, 0, 0])
        expected[384:389] = bytes([0, 255, 255, 255, 255])
        expected[400], expected[480] = 2, 1
        self.assertEqual(bytes(self.s), bytes(expected))
        self.assertEqual([self.lib.equipment_reward_item(i) for i in range(19)], LEGACY_IDS)

    def test_southern_definitions_match_exact_sidegrade_contract(self):
        # All eight bonuses are explicit; an omitted design bonus must be zero.
        expected = [
            (4, 'Shadecutter Sword', 0, 1, (0, 0, 0, 0, 0, 0, 1, 1)),
            (12, 'Sunlace Lance', 0, 2, (0, 0, 0, 0, 0, 0, 4, 0)),
            (36, 'Breezewall Mail', 1, 0, (0, 3, 0, -2, 0, 0, 0, 0)),
            (52, 'Softsand Boots', 2, 0, (0, 0, 0, -4, 4, 0, 0, 0)),
            (66, 'Raincatch Belt', 3, 0, (0, 0, 4, 0, 0, 1, 0, 0)),
            (84, 'Springpin Ring', 4, 0, (0, 0, 0, -4, 0, 0, 0, 2)),
        ]
        authored = (U16 * len(IDS)).in_dll(self.lib, 'equipment_authored_ids')
        self.assertEqual(list(authored), IDS)
        for source, (item, name, slot, weapon, stats) in enumerate(expected, 19):
            with self.subTest(item=item, source=source):
                d = self.lib.equipment_definition(item).contents
                self.assertEqual((d.id, d.slot, d.weapon_class, d.flags, d.phase),
                                 (item, slot, weapon, 0, 255))
                self.assertEqual(tuple(getattr(d.stats, k) for k, _ in Bonuses._fields_), stats)
                self.assertEqual(bytes(d.reserved), bytes(2))
                self.assertEqual(self.lib.equipment_name(item).decode(), name)
                self.assertEqual(self.lib.equipment_reward_item(source), item)
                self.assertEqual(self.lib.equipment_reward_source(item), source)
        self.assertEqual(self.lib.equipment_reward_item(31), 0)

    def test_magma_six_exact_vectors_sources_and_derived_comparisons(self):
        allocation=json.loads((ROOT/'docs/magma-design/magma_allocation.json').read_text())
        slots=['weapon','body','boots','belt','ring']
        for row in allocation['equipment']:
            d=self.lib.equipment_definition(row['id']).contents
            self.assertEqual(self.lib.equipment_name(row['id']).decode(),row['name'])
            self.assertEqual(d.slot,slots.index(row['slot']))
            self.assertEqual(d.weapon_class,{'sword':1,'bow':3,None:0}[row['weapon_class']])
            self.assertEqual({key:getattr(d.stats,key) for key,_ in Bonuses._fields_},row['stats'])
            self.assertEqual(self.lib.equipment_reward_item(row['source_id']),row['id'])
            self.assertEqual(self.lib.equipment_reward_source(row['id']),row['source_id'])
            self.claim(row['id'])
            ref=self.lib.equipment_find(C.byref(self.s),row['id'])
            before=bytes(self.s);preview=Comparison()
            self.assertEqual(self.lib.equipment_preview(C.byref(self.s),d.slot,ref,192,192,0,C.byref(preview)),OK)
            self.assertEqual(bytes(self.s),before)
            hp=U16(192)
            self.assertEqual(self.lib.equipment_equip(C.byref(self.s),d.slot,ref,192,C.byref(hp),0,None),OK)
            actual=Stats();self.assertEqual(self.lib.equipment_derive(C.byref(self.s),192,C.byref(actual)),1)
            self.assertEqual(bytes(actual),bytes(preview.after))
            self.assertEqual(actual.max_hp_q4,192)
            self.assertEqual(hp.value,preview.hp_after_q4)

    def test_southern_choices_have_explicit_benefits_and_costs(self):
        for new, old, benefit, cost in [
                (4, 2, 'stagger', 'attack_q4'), (4, 3, 'stagger', 'reach_px'),
                (12, 10, 'reach_px', 'attack_q4'), (12, 11, 'reach_px', 'defense_q4'),
                (36, 34, 'speed_q8_delta', 'hp_q4'),
                (36, 35, 'defense_q4', 'speed_q8_delta'),
                (52, 50, 'roll_reduction', 'speed_q8_delta'),
                (66, 65, 'power_reduction', 'hp_q4'),
                (84, 82, 'stagger', 'defense_q4'),
                (84, 81, 'stagger', 'power_reduction')]:
            with self.subTest(new=new, old=old):
                a = self.lib.equipment_definition(new).contents.stats
                b = self.lib.equipment_definition(old).contents.stats
                self.assertGreater(getattr(a, benefit), getattr(b, benefit))
                self.assertLess(getattr(a, cost), getattr(b, cost))

    def test_southern_derived_previews_clamps_and_no_free_healing(self):
        refs = {item: self.claim(item) for item in SOUTHERN_IDS}
        self.hp.value = 70
        for item in [4, 36, 52, 66, 84]:
            slot = self.lib.equipment_definition(item).contents.slot
            before, comparison = bytes(self.s), Comparison()
            self.assertEqual(self.lib.equipment_preview(C.byref(self.s), slot, refs[item],
                             96, self.hp.value, 0, C.byref(comparison)), OK)
            self.assertEqual(bytes(self.s), before)
            self.equip(slot, refs[item])
            self.assertEqual(bytes(self.derive()), bytes(comparison.after))
            self.assertEqual((self.hp.value, comparison.hp_after_q4), (70, 70))
        s = self.derive()
        self.assertEqual((s.max_hp_q4, s.speed_q8, s.diagonal_q8), (100, 310, 219))
        self.assertEqual((s.attack_q4, s.defense_q4, s.roll_cooldown, s.power_cooldown),
                         (0, 3, 38, 74))
        self.assertEqual((s.reach_px, s.stagger, s.weapon_class, s.phase), (1, 3, 1, 255))
        self.equip(0, refs[12])
        s = self.derive()
        self.assertEqual((s.reach_px, s.stagger, s.weapon_class), (4, 2, 2))
        self.assertEqual(self.derive(192).max_hp_q4, 192)
        self.hp.value = 100
        self.assertEqual(self.lib.equipment_unequip(C.byref(self.s), 3, 96,
                         C.byref(self.hp), 0, None), OK)
        self.assertEqual((self.derive().max_hp_q4, self.hp.value), (96, 96))
        self.equip(3, refs[66])
        self.assertEqual((self.derive().max_hp_q4, self.hp.value), (100, 96))
        self.valid()

    def test_southern_claims_append_preserve_old_records_and_discard_history(self):
        for item in LEGACY_IDS[1:]:
            self.claim(item)
        before = bytes(self.s)
        self.assertEqual(list(self.s.reward_claims), [255, 255, 7, 0, 0, 0, 0, 0])
        for sources in [(19, 20, 21, 22), (23, 24)]:
            bundle = (U8 * len(sources))(*sources)
            self.assertEqual(self.lib.equipment_claim_many(C.byref(self.s), bundle, len(sources)), OK)
        self.assertEqual(bytes(self.s)[:19 * 8], before[:19 * 8])
        self.assertEqual(bytes(self.s)[384:400], before[384:400])
        self.assertEqual(self.lib.equipment_count(C.byref(self.s)), 25)
        self.assertEqual(list(self.s.reward_claims), [255, 255, 255, 1, 0, 0, 0, 0])
        for source, item in enumerate(SOUTHERN_IDS, 19):
            ref = self.lib.equipment_find(C.byref(self.s), item)
            slot = self.lib.equipment_definition(item).contents.slot
            self.equip(slot, ref)
            snapshot = bytes(self.s)
            for busy in [1, 2, 4, 8, 16]:
                self.assertEqual(self.lib.equipment_discard(C.byref(self.s), ref, 96,
                                 C.byref(self.hp), busy, 1), BUSY)
                self.assertEqual(bytes(self.s), snapshot)
            self.assertEqual(self.lib.equipment_discard(C.byref(self.s), ref, 96,
                             C.byref(self.hp), 0, 0), CONFIRM)
            self.assertEqual(bytes(self.s), snapshot)
            self.assertEqual(self.lib.equipment_discard(C.byref(self.s), ref, 96,
                             C.byref(self.hp), 0, 1), OK)
            self.assertEqual(self.s.equipped[slot], 0 if slot == 0 else 255)
            self.assertEqual(self.lib.equipment_seen(C.byref(self.s), item), 1)
            self.assertEqual(self.lib.equipment_reward_claimed(C.byref(self.s), source), 1)
            snapshot = bytes(self.s)
            self.assertEqual(self.lib.equipment_claim(C.byref(self.s), item, source, None), ALREADY)
            self.assertEqual(bytes(self.s), snapshot)
        self.assertEqual(self.lib.equipment_count(C.byref(self.s)), 19)
        self.valid()
        for source in range(25, 64):
            bad = State.from_buffer_copy(bytes(self.s))
            bad.reward_claims[source >> 3] |= 1 << (source & 7)
            self.assertEqual(self.lib.equipment_reserved_validate(C.byref(bad)), 0)

    def test_southern_full_bag_claims_and_cross_byte_bundle_are_atomic(self):
        lib = self.variants['capacity']
        for ref, item in enumerate(range(100, 147), 1):
            self.s.bag[ref].item_id, self.s.bag[ref].quantity = item, 1
            self.s.seen[item >> 3] |= 1 << (item & 7)
        before, out = bytes(self.s), C.c_uint(999)
        for source, item in enumerate(SOUTHERN_IDS, 19):
            self.assertEqual(lib.equipment_claim(C.byref(self.s), item, source, C.byref(out)), FULL)
            self.assertEqual(bytes(self.s), before)
            self.assertEqual(out.value, 999)
        self.assertEqual(lib.equipment_discard(C.byref(self.s), 47, 96,
                         C.byref(self.hp), 0, 1), OK)
        before = bytes(self.s)
        sources = (U8 * 2)(23, 24)
        self.assertEqual(lib.equipment_claim_many(C.byref(self.s), sources, 2), FULL)
        self.assertEqual(bytes(self.s), before)
        self.assertEqual(lib.equipment_discard(C.byref(self.s), 46, 96,
                         C.byref(self.hp), 0, 1), OK)
        self.assertEqual(lib.equipment_claim_many(C.byref(self.s), sources, 2), OK)
        self.assertEqual((lib.equipment_find(C.byref(self.s), 66),
                          lib.equipment_find(C.byref(self.s), 84)), (46, 47))
        self.assertEqual(list(self.s.reward_claims), [1, 0, 128, 1, 0, 0, 0, 0])
        self.assertEqual(lib.equipment_validate(C.byref(self.s)), 1)

    def test_generator_rejects_remapping_and_unauthorized_append(self):
        spec = importlib.util.spec_from_file_location('equipment_generator',
                                     ROOT / 'assets/equipment/generate_data.py')
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        source = json.loads((ROOT / 'assets/equipment/catalog.json').read_text())
        generator.SOURCE = Path(self.tmp.name) / 'test-catalog.json'
        generator.SOURCE.write_text(json.dumps(source))
        self.assertEqual(generator.generate(), (ROOT / 'src/equipment_data.c').read_text())
        for case in ['old_order', 'southern_order', 'source_remap', 'missing', 'extra', 'stat_overflow']:
            data = json.loads(json.dumps(source))
            if case == 'old_order':
                data['items'][1], data['items'][13] = data['items'][13], data['items'][1]
            elif case == 'southern_order':
                data['items'][19], data['items'][20] = data['items'][20], data['items'][19]
            elif case == 'source_remap':
                data['reward_sources'][19]['item_id'] = 12
            elif case == 'missing':
                data['items'].pop()
            elif case == 'extra':
                data['items'].append(dict(data['items'][-1], id=85))
            else:
                data['items'][19]['stats']['hp_q4'] = 33
            generator.SOURCE.write_text(json.dumps(data))
            with self.subTest(case=case), self.assertRaises(AssertionError):
                generator.generate()

    def test_northern_sidegrades_preserve_source_ids_and_no_heal(self):
        original=[1,2,9,10,17,18,33,34,49,50,65,81,82]
        added=[3,11,19,35,51,83]
        self.assertEqual([self.lib.equipment_reward_item(i) for i in range(13)],original)
        self.assertEqual([self.lib.equipment_reward_item(i) for i in range(13,19)],added)
        for source,item in enumerate(added,13):
            ref=self.claim(item);slot=self.lib.equipment_definition(item).contents.slot
            hp=self.hp.value;self.equip(slot,ref);self.assertLessEqual(self.hp.value,hp)
            self.assertEqual(self.lib.equipment_reward_source(item),source)
        self.assertEqual(self.lib.equipment_definition(19).contents.stats.reach_px,12)
        # Compare each new item's role against an older alternative. There is
        # a benefit and a cost, not a universal strictly-better replacement.
        for new,old,benefit,cost in [(3,2,'reach_px','attack_q4'),(11,10,'defense_q4','attack_q4'),
                                    (19,18,'reach_px','attack_q4'),(35,33,'speed_q8_delta','defense_q4'),
                                    (51,49,'roll_reduction','speed_q8_delta'),(83,81,'defense_q4','power_reduction')]:
            a=self.lib.equipment_definition(new).contents.stats;b=self.lib.equipment_definition(old).contents.stats
            self.assertGreater(getattr(a,benefit),getattr(b,benefit));self.assertLess(getattr(a,cost),getattr(b,cost))
        self.valid()

    def test_weapon_parameters_exact_and_no_action_runtime(self):
        for expected in json.loads((ROOT / 'assets/equipment/catalog.json').read_text())['weapon_classes']:
            w = self.lib.equipment_weapon(expected['id']).contents
            for name in ['combo_window', 'buffer', 'lunge_q8', 'charge_min_updates',
                         'charge_max_updates', 'projectile_speed_q8', 'max_live_arrows']:
                self.assertEqual(getattr(w, name), expected.get(name, 0))
            self.assertEqual(w.move_count, len(expected['moves']))
            for got, want in zip(w.moves, expected['moves']):
                for name, _ in Move._fields_:
                    self.assertEqual(getattr(got, name), want[name])
        for invalid in [0, 4, 255, 0xffffffff]:
            self.assertFalse(self.lib.equipment_weapon(invalid))

    def test_all_items_all_slots_and_stable_instance_references(self):
        for item in IDS[1:]:
            self.claim(item)
        self.assertEqual(self.lib.equipment_count(C.byref(self.s)), len(IDS))
        for ref in range(len(IDS)):
            item = self.s.bag[ref].item_id
            target = self.lib.equipment_definition(item).contents.slot
            for slot in range(5):
                before = bytes(self.s)
                result = self.lib.equipment_equip(C.byref(self.s), slot, ref, 96, C.byref(self.hp), 0, None)
                self.assertEqual(result, OK if slot == target else INCOMPATIBLE)
                if slot != target:
                    self.assertEqual(bytes(self.s), before)
            self.assertEqual(self.lib.equipment_find(C.byref(self.s), item), ref)
        self.valid()
        for slot in range(5):
            self.assertEqual(self.lib.equipment_unequip(C.byref(self.s), slot, 96, C.byref(self.hp), 0, None), OK)
        self.assertEqual(list(self.s.equipped), [0, 255, 255, 255, 255])

    def test_ref_slot_and_current_input_bounds_are_atomic(self):
        before = bytes(self.s)
        for slot in [5, 6, 255, 65535, 0xffffffff]:
            self.assertEqual(self.lib.equipment_equip(C.byref(self.s), slot, 0, 96, C.byref(self.hp), 0, None), INVALID)
        for ref in list(range(1, 255)) + [256, 65535, 0xffffffff]:
            self.assertEqual(self.lib.equipment_equip(C.byref(self.s), 0, ref, 96, C.byref(self.hp), 0, None), INVALID)
        self.assertEqual(self.lib.equipment_equip(C.byref(self.s), 0, 0, 65536, C.byref(self.hp), 0, None), INVALID)
        self.assertEqual(self.lib.equipment_equip(C.byref(self.s), 0, 0, 96, None, 0, None), INVALID)
        self.assertEqual(bytes(self.s), before)
        c = Comparison()
        self.assertEqual(self.lib.equipment_preview(C.byref(self.s), 0, 0, 96, 65536, 0, C.byref(c)), INVALID)
        self.assertEqual(self.lib.equipment_preview(C.byref(self.s), 0, 0, 96, 96, 0, None), INVALID)

    def test_every_busy_combination_blocks_preview_equip_unequip_discard(self):
        ref = self.claim(2)
        c = Comparison()
        for busy in range(1, 256):
            expected = BUSY if busy <= 31 else INVALID
            before = bytes(self.s)
            self.assertEqual(self.lib.equipment_equip(C.byref(self.s), 0, ref, 96, C.byref(self.hp), busy, None), expected)
            self.assertEqual(self.lib.equipment_preview(C.byref(self.s), 0, ref, 96, 96, busy, C.byref(c)), expected)
            self.assertEqual(self.lib.equipment_unequip(C.byref(self.s), 0, 96, C.byref(self.hp), busy, None), expected)
            self.assertEqual(self.lib.equipment_discard(C.byref(self.s), ref, 96, C.byref(self.hp), busy, 1), expected)
            self.assertEqual(bytes(self.s), before)
            self.assertEqual(self.hp.value, 96)

    def test_preview_numbers_and_no_hover_mutation(self):
        ref = self.claim(33)
        c = Comparison()
        before = bytes(self.s)
        self.assertEqual(self.lib.equipment_preview(C.byref(self.s), 1, ref, 96, 70, 0, C.byref(c)), OK)
        self.assertEqual(bytes(self.s), before)
        self.assertEqual((c.before.max_hp_q4, c.after.max_hp_q4), (96, 104))
        self.assertEqual((c.before.defense_q4, c.after.defense_q4), (0, 2))
        self.assertEqual((c.before.speed_q8, c.after.speed_q8), (320, 316))
        self.assertEqual((c.hp_before_q4, c.hp_after_q4), (70, 70))
        self.assertEqual((c.old_ref, c.new_ref), (255, ref))

    def test_no_free_heal_and_repeated_stats_do_not_accumulate(self):
        mail, belt, ring = self.claim(34), self.claim(65), self.claim(81)
        self.hp.value = 70
        for _ in range(1000):
            self.equip(1, mail)
            self.equip(3, belt)
            self.equip(4, ring)
            stats = self.derive()
            self.assertEqual((stats.max_hp_q4, stats.defense_q4, stats.power_cooldown), (120, 4, 71))
            self.assertEqual(self.hp.value, 70)
            for slot in [1, 3, 4]:
                self.assertEqual(self.lib.equipment_unequip(C.byref(self.s), slot, 96, C.byref(self.hp), 0, None), OK)
            self.assertEqual((self.derive().max_hp_q4, self.hp.value), (96, 70))
        self.equip(1, mail)
        self.equip(3, belt)
        self.hp.value = 120
        self.assertEqual(self.lib.equipment_unequip(C.byref(self.s), 1, 96, C.byref(self.hp), 0, None), OK)
        self.assertEqual(self.hp.value, 104)
        self.equip(1, mail)
        self.assertEqual(self.hp.value, 104)
        self.hp.value = 0
        self.equip(1, mail)
        self.assertEqual(self.hp.value, 0)

    def test_discard_confirmation_starter_protection_and_no_regrant(self):
        before = bytes(self.s)
        self.assertEqual(self.lib.equipment_discard(C.byref(self.s), 0, 96, C.byref(self.hp), 0, 1), PROTECTED)
        self.assertEqual(bytes(self.s), before)
        sword, belt = self.claim(2), self.claim(65)
        self.equip(0, sword)
        self.equip(3, belt)
        self.hp.value = 104
        before = bytes(self.s)
        self.assertEqual(self.lib.equipment_discard(C.byref(self.s), belt, 96, C.byref(self.hp), 0, 0), CONFIRM)
        self.assertEqual(bytes(self.s), before)
        self.assertEqual(self.lib.equipment_discard(C.byref(self.s), belt, 96, C.byref(self.hp), 0, 1), OK)
        self.assertEqual((self.hp.value, self.s.equipped[3]), (96, 255))
        self.assertEqual(bytes(self.s.bag[belt]), bytes(8))
        self.assertEqual(self.lib.equipment_find(C.byref(self.s), 65), 255)
        self.assertEqual(self.lib.equipment_seen(C.byref(self.s), 65), 1)
        self.assertEqual(self.lib.equipment_claim(C.byref(self.s), 65, 10, None), ALREADY)
        self.assertEqual(self.lib.equipment_discard(C.byref(self.s), sword, 96, C.byref(self.hp), 0, 1), OK)
        self.assertEqual(self.s.equipped[0], 0)
        self.valid()

    def test_prior_source_history_completes_without_second_instance(self):
        ref = self.claim(49)
        self.s.reward_claims[1] &= ~1
        self.valid()
        out = C.c_uint(999)
        self.assertEqual(self.lib.equipment_claim(C.byref(self.s), 49, 8, C.byref(out)), DUPLICATE)
        self.assertEqual(out.value, ref)
        self.assertEqual(self.lib.equipment_count(C.byref(self.s)), 2)
        self.assertEqual(self.lib.equipment_discard(C.byref(self.s), ref, 96, C.byref(self.hp), 0, 1), OK)
        self.s.reward_claims[1] &= ~1
        self.assertEqual(self.lib.equipment_claim(C.byref(self.s), 49, 8, C.byref(out)), DUPLICATE)
        self.assertEqual(out.value, 255)
        self.assertEqual(self.lib.equipment_count(C.byref(self.s)), 1)
        self.assertEqual(self.lib.equipment_claim(C.byref(self.s), 49, 8, None), ALREADY)

    def test_capacity_ready_claim_unchanged_and_retry_after_discard(self):
        lib = self.variants['capacity']
        for ref, item in enumerate(range(100, 147), 1):
            self.s.bag[ref].item_id, self.s.bag[ref].quantity = item, 1
            self.s.seen[item >> 3] |= 1 << (item & 7)
        self.assertEqual(lib.equipment_validate(C.byref(self.s)), 1)
        self.assertEqual(lib.equipment_count(C.byref(self.s)), 48)
        before, out = bytes(self.s), C.c_uint(999)
        for _ in range(100):
            self.assertEqual(lib.equipment_claim(C.byref(self.s), 49, 8, C.byref(out)), FULL)
            self.assertEqual(bytes(self.s), before)
            self.assertEqual(out.value, 999)
        self.assertEqual(lib.equipment_reward_claimed(C.byref(self.s), 8), 0)
        self.assertEqual(lib.equipment_discard(C.byref(self.s), 47, 96, C.byref(self.hp), 0, 1), OK)
        self.assertEqual(lib.equipment_claim(C.byref(self.s), 49, 8, C.byref(out)), OK)
        self.assertEqual(out.value, 47)
        self.assertEqual(self.s.bag[46].item_id, 145)
        self.assertEqual(lib.equipment_claim(C.byref(self.s), 49, 8, None), ALREADY)
        self.assertEqual(lib.equipment_validate(C.byref(self.s)), 1)

    def test_atomic_claim_many_success_repeat_and_input_validation(self):
        sources = (U8 * 2)(3, 12)
        self.assertEqual(self.lib.equipment_claim_many(C.byref(self.s), sources, 2), OK)
        self.assertEqual(self.lib.equipment_count(C.byref(self.s)), 3)
        self.assertNotEqual(self.lib.equipment_find(C.byref(self.s), 10), 255)
        self.assertNotEqual(self.lib.equipment_find(C.byref(self.s), 82), 255)
        before = bytes(self.s)
        self.assertEqual(self.lib.equipment_claim_many(C.byref(self.s), sources, 2), ALREADY)
        self.assertEqual(bytes(self.s), before)
        for values, count in [([1, 1], 2), ([1, len(IDS)], 2), ([1, 255], 2), ([1], 0), ([1] * 5, 5)]:
            array = (U8 * len(values))(*values)
            self.assertEqual(self.lib.equipment_claim_many(C.byref(self.s), array, count), INVALID)
            self.assertEqual(bytes(self.s), before)
        self.assertEqual(self.lib.equipment_claim_many(C.byref(self.s), None, 1), INVALID)
        self.assertEqual(self.lib.equipment_claim_many(None, sources, 2), INVALID)
        self.assertEqual(bytes(self.s), before)
        sources = (U8 * 4)(1, 2, 4, 6)
        self.assertEqual(self.lib.equipment_claim_many(C.byref(self.s), sources, 4), OK)
        self.assertEqual(self.lib.equipment_count(C.byref(self.s)), 7)
        self.valid()

    def test_atomic_claim_many_full_rolls_back_all_inventory_and_claim_changes(self):
        lib = self.variants['capacity']
        for ref, item in enumerate(range(100, 146), 1):
            self.s.bag[ref].item_id, self.s.bag[ref].quantity = item, 1
            self.s.seen[item >> 3] |= 1 << (item & 7)
        self.assertEqual(lib.equipment_count(C.byref(self.s)), 47)
        before = bytes(self.s)
        sources = (U8 * 2)(3, 12)
        self.assertEqual(lib.equipment_claim_many(C.byref(self.s), sources, 2), FULL)
        self.assertEqual(bytes(self.s), before)
        self.assertEqual(lib.equipment_reward_claimed(C.byref(self.s), 3), 0)
        self.assertEqual(lib.equipment_reward_claimed(C.byref(self.s), 12), 0)
        self.assertEqual(lib.equipment_discard(C.byref(self.s), 46, 96, C.byref(self.hp), 0, 1), OK)
        self.assertEqual(lib.equipment_claim_many(C.byref(self.s), sources, 2), OK)
        self.assertEqual(lib.equipment_count(C.byref(self.s)), 48)
        self.assertEqual(lib.equipment_reward_claimed(C.byref(self.s), 3), 1)
        self.assertEqual(lib.equipment_reward_claimed(C.byref(self.s), 12), 1)
        # A historical duplicate claim must also roll back when a later grant is full.
        self.s.seen[2 >> 3] |= 1 << (2 & 7)
        before = bytes(self.s)
        sources = (U8 * 2)(1, 8)
        self.assertEqual(lib.equipment_claim_many(C.byref(self.s), sources, 2), FULL)
        self.assertEqual(bytes(self.s), before)
        self.assertEqual(lib.equipment_reward_claimed(C.byref(self.s), 1), 0)

    def test_atomic_claim_many_history_and_mixed_status(self):
        for item in [10, 82]:
            self.s.seen[item >> 3] |= 1 << (item & 7)
        sources = (U8 * 2)(3, 12)
        self.assertEqual(self.lib.equipment_claim_many(C.byref(self.s), sources, 2), DUPLICATE)
        self.assertEqual(self.lib.equipment_count(C.byref(self.s)), 1)
        sources = (U8 * 3)(0, 3, 2)
        self.assertEqual(self.lib.equipment_claim_many(C.byref(self.s), sources, 3), OK)
        self.assertEqual(self.lib.equipment_count(C.byref(self.s)), 2)
        self.valid()

    def test_invalid_and_mismatched_reward_sources_atomic(self):
        before = bytes(self.s)
        for source in list(range(len(IDS), 256)) + [65535, 0xffffffff]:
            self.assertEqual(self.lib.equipment_claim(C.byref(self.s), 49, source, None), INVALID)
        for source in range(len(IDS)):
            if source != 8:
                self.assertEqual(self.lib.equipment_claim(C.byref(self.s), 49, source, None), INVALID)
        for item in [0, 3, 511, 512, 65535, 0xffffffff]:
            self.assertEqual(self.lib.equipment_claim(C.byref(self.s), item, 8, None), INVALID)
        self.assertEqual(bytes(self.s), before)

    def test_aggregate_caps_and_signed_overflow_inputs(self):
        for mode in ['caps', 'minimum', 'overflow', 'negative']:
            lib = self.variants[mode]
            lib.equipment_init(C.byref(self.s))
            for slot, item in enumerate([1, 33, 49, 65, 81]):
                ref = 0 if item == 1 else self.claim(item, lib)
                self.equip(slot, ref, lib)
            stats = self.derive(65535 if mode == 'overflow' else 96, lib)
            if mode in ['caps', 'overflow']:
                self.assertEqual((stats.max_hp_q4, stats.attack_q4, stats.defense_q4), (192, 24, 8))
                self.assertEqual((stats.speed_q8, stats.diagonal_q8), (352, 249))
                self.assertEqual((stats.roll_cooldown, stats.power_cooldown, stats.reach_px, stats.stagger), (36, 67, 12 if mode == 'overflow' else 4, 3))
            else:
                self.assertEqual((stats.max_hp_q4, stats.attack_q4, stats.defense_q4), (96, 0, 0))
                self.assertEqual((stats.speed_q8, stats.diagonal_q8), (288, 204))
                self.assertEqual((stats.roll_cooldown, stats.power_cooldown, stats.reach_px, stats.stagger), (42, 75, 0, 0))
            self.assertEqual(lib.equipment_catalog_validate(), 0 if mode in ['overflow', 'negative'] else 1)

    def test_base_hp_and_diagonal_exact_rounding(self):
        for base in [0, 1, 95, 96, 97, 127, 128, 191, 192, 193, 65535]:
            stats = self.derive(base)
            self.assertEqual(stats.max_hp_q4, min(192, max(96, base)))
            self.assertEqual(stats.diagonal_q8, 226)
        boots = self.claim(49)
        self.equip(2, boots)
        self.assertEqual((self.derive().speed_q8, self.derive().diagonal_q8), (328, 232))
        out = Stats()
        C.memset(C.byref(out), 0xa5, C.sizeof(out))
        before = bytes(out)
        self.assertEqual(self.lib.equipment_derive(C.byref(self.s), 0xffffffff, C.byref(out)), 0)
        self.assertEqual(bytes(out), before)

    def test_malformed_records_and_reserved_facing_state(self):
        initial = bytes(self.s)
        cases = []
        for offset in [2, 3, 4, 5, 6, 7]:
            for value in [1, 2, 255]:
                if (offset, value) not in [(3, 1), (4, 1)]:
                    cases.append((offset, value))
        cases += [(offset, 1) for offset in range(8, 384)]
        cases += [(offset, 1) for offset in list(range(389, 400)) + list(range(464, 480)) + list(range(488, 512))]
        cases += [(400, 1), (401, 1), (481, 32), (487, 128)]
        for offset, value in cases:
            state = State.from_buffer_copy(initial)
            C.cast(C.byref(state), C.POINTER(U8))[offset] = value
            self.assertEqual(self.lib.equipment_validate(C.byref(state)), 0, (offset, value))
        for invalid_id in [0, 2, 3, 128, 511, 512, 65535]:
            state = State.from_buffer_copy(initial)
            state.bag[0].item_id = invalid_id
            self.assertEqual(self.lib.equipment_validate(C.byref(state)), 0)
        for slot in range(5):
            for ref in range(256):
                state = State.from_buffer_copy(initial)
                state.equipped[slot] = ref
                expected = (slot == 0 and ref == 0) or (slot > 0 and ref == 255)
                self.assertEqual(self.lib.equipment_validate(C.byref(state)), int(expected), (slot, ref))
        self.claim(2)
        self.s.bag[2] = self.s.bag[1]
        self.assertEqual(self.lib.equipment_validate(C.byref(self.s)), 0)

    def test_seen_claim_consistency_and_corruption_atomic(self):
        ref = self.claim(49)
        self.s.seen[49 >> 3] &= ~(1 << (49 & 7))
        self.assertEqual(self.lib.equipment_validate(C.byref(self.s)), 0)
        before = bytes(self.s)
        out = Stats()
        self.assertEqual(self.lib.equipment_derive(C.byref(self.s), 96, C.byref(out)), 0)
        self.assertEqual(self.lib.equipment_equip(C.byref(self.s), 2, ref, 96, C.byref(self.hp), 0, None), INVALID)
        self.assertEqual(self.lib.equipment_claim(C.byref(self.s), 2, 1, None), INVALID)
        self.assertEqual(self.lib.equipment_discard(C.byref(self.s), ref, 96, C.byref(self.hp), 0, 1), INVALID)
        self.assertEqual(bytes(self.s), before)

    def test_null_state_and_records_reject_safely(self):
        self.lib.equipment_init(None)
        for name in ['equipment_validate', 'equipment_refs_validate', 'equipment_reserved_validate', 'equipment_record_validate']:
            self.assertEqual(getattr(self.lib, name)(None), 0)
        self.assertEqual(self.lib.equipment_count(None), 0)
        self.assertEqual(self.lib.equipment_find(None, 1), 255)
        self.assertEqual(self.lib.equipment_claim(None, 2, 1, None), INVALID)
        self.assertEqual(self.lib.equipment_derive(None, 96, None), 0)

    def test_phase_25_pairs_delegate_to_existing_resolver(self):
        controls = [2, 3, 4, 0, 1]
        for a in range(5):
            for d in range(5):
                expected = 320 if controls[a] == d else 224 if controls[d] == a else 256
                self.assertEqual(self.lib.combat_phase_multiplier_q8(a, d), expected)
                self.assertEqual(self.lib.combat_phase_multiplier_q8(a, d), self.lib.creatures_phase_multiplier_q8(a, d))
        for phase in range(5):
            self.assertEqual(self.lib.combat_phase_multiplier_q8(255, phase), 256)
            self.assertEqual(self.lib.combat_phase_multiplier_q8(phase, 255), 256)
        self.assertEqual(self.lib.combat_phase_multiplier_q8(255, 255), 256)
        for bad in [5, 6, 254, 256, 65535, 0xffffffff]:
            self.assertEqual(self.lib.combat_phase_multiplier_q8(bad, 255), 0)
            self.assertEqual(self.lib.combat_phase_multiplier_q8(255, bad), 0)

    def test_damage_rounding_min_max_immunity_and_integer_safety(self):
        for a, d, multiplier in [(0, 2, 320), (2, 0, 224), (255, 255, 256)]:
            for base in range(1, 256):
                for attack in [0, 1, 4, 24]:
                    for defense in [0, 1, 8, 255]:
                        want = min(255, max(4, ((base + attack) * multiplier + 128) // 256 - defense))
                        self.assertEqual(self.lib.combat_damage_q4(base, attack, defense, a, d, 0), want)
                        self.assertEqual(self.lib.combat_damage_q4(base, attack, defense, a, d, 1), 0)
        for values in [(0, 0, 0, 255, 255), (256, 0, 0, 255, 255), (1, 25, 0, 255, 255),
                       (1, 0, 256, 255, 255), (1, 0, 0, 5, 255), (1, 0, 0, 255, 5),
                       (0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff)]:
            self.assertEqual(self.lib.combat_damage_q4(*values, 0), 0)
        self.assertEqual(self.lib.combat_damage_q4(255, 24, 0, 0, 2, 0), 255)
        self.assertEqual(self.lib.combat_damage_q4(4, 0, 0, 0, 2, 0), 5)
        self.assertEqual(self.lib.combat_damage_q4(12, 0, 0, 2, 0, 0), 11)
        self.assertEqual(self.lib.combat_damage_q4(16, 0, 8, 255, 255, 0), 8)

    def test_legacy_neutral_damage_has_no_new_encounter_bonus(self):
        for hearts in [1, 2, 3, 4, 6, 8]:
            for defender in list(range(5)) + [255]:
                self.assertEqual(self.lib.combat_damage_q4(hearts * 16, 0, 0, 255, defender, 0), hearts * 16)
        self.assertEqual([self.lib.combat_damage_q4(n, 0, 0, 255, 255, 0) for n in [16, 16, 32]], [16, 16, 32])

    def test_cooldowns_and_action_snapshot_bytes_untouched(self):
        class Runtime(C.Structure):
            _fields_ = [(k, U16) for k in ['hp', 'attack', 'power', 'roll', 'heal', 'snapshot']]
        runtime = Runtime(80, 12, 59, 23, 319, 0xabc)
        hp = C.cast(C.byref(runtime), C.POINTER(U16))
        ref = self.claim(81)
        before = bytes(runtime)[2:]
        self.assertEqual(self.lib.equipment_equip(C.byref(self.s), 4, ref, 96, hp, 0, None), OK)
        self.assertEqual(bytes(runtime)[2:], before)
        self.assertEqual(runtime.hp, 80)
        self.assertEqual(self.lib.equipment_unequip(C.byref(self.s), 4, 96, hp, 0, None), OK)
        self.assertEqual(bytes(runtime)[2:], before)
        self.assertEqual(self.lib.equipment_equip(C.byref(self.s), 4, ref, 96, hp, 4, None), BUSY)
        self.assertEqual(bytes(runtime)[2:], before)

    def test_address_undefined_sanitizers_malformed_state_fuzz(self):
        source = Path(self.tmp.name) / 'sanitizer.c'
        source.write_text(r'''#include "equipment.h"
#include "combat_rules.h"
#include <assert.h>
#include <string.h>
static unsigned random_state = 0x76c1259du;
static unsigned next_random(void) {
    random_state ^= random_state << 13;
    random_state ^= random_state >> 17;
    random_state ^= random_state << 5;
    return random_state;
}
int main(void) {
    EquipmentState state, old;
    EquipmentStats stats;
    EquipmentComparison comparison;
    EquipmentU16 hp;
    unsigned iteration, i;
    assert(equipment_catalog_validate());
    for (iteration = 0; iteration < 20000; ++iteration) {
        equipment_init(&state);
        for (i = 0; i < 1u + (iteration & 7u); ++i) {
            unsigned at = next_random() % sizeof(state);
            ((unsigned char *)&state)[at] ^= (unsigned char)(1u << (next_random() & 7u));
        }
        memcpy(&old, &state, sizeof(state));
        hp = 71;
        if (!equipment_validate(&state)) {
            assert(!equipment_derive(&state, 96, &stats));
            assert(equipment_equip(&state, 0, 0, 96, &hp, 0, &comparison) == EQUIPMENT_INVALID);
            assert(equipment_discard(&state, 1, 96, &hp, 0, 1) == EQUIPMENT_INVALID);
            assert(equipment_claim(&state, 49, 8, 0) == EQUIPMENT_INVALID);
            assert(!memcmp(&old, &state, sizeof(state)));
            assert(hp == 71);
        } else {
            assert(equipment_derive(&state, next_random() & 65535u, &stats));
            assert(stats.max_hp_q4 >= 96 && stats.max_hp_q4 <= 192);
        }
        { EquipmentU8 sources[4] = {3, 12, 2, 4};
          if (!equipment_validate(&state)) assert(equipment_claim_many(&state, sources, 4) == EQUIPMENT_INVALID); }
        equipment_preview(&state, next_random(), next_random(), next_random(),
                          next_random(), next_random(), &comparison);
        equipment_definition(next_random());
        equipment_record_validate(&state.bag[next_random() % 48]);
        equipment_weapon(next_random());
        combat_damage_q4(next_random(), next_random(), next_random(),
                         next_random(), next_random(), (int)(iteration & 1));
        combat_field_allows(next_random(), next_random());
    }
    return 0;
}
''')
        binary = Path(self.tmp.name) / 'sanitizer'
        subprocess.run([os.environ.get('CC', 'cc'), '-std=c99', '-O1', '-g', '-Wall', '-Wextra',
                        '-Werror', '-pedantic', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                        '-fno-pie', '-no-pie', '-I' + str(ROOT / 'src'), str(source),
                        *[str(ROOT / 'src' / name) for name in ['equipment.c', 'equipment_data.c',
                          'combat_rules.c', 'creatures.c', 'creature_data.c']], '-o', str(binary)], check=True)
        # This execution environment uses ptrace; LSan cannot inspect its threads.
        # The target modules allocate nothing. Address/UB checks stay enabled.
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
        subprocess.run([str(binary)], check=True, env=env)

    def test_field_capability_is_explicit_not_ownership_or_phase(self):
        ignite = 1 << 12
        for required in [1 << n for n in range(21)]:
            self.assertEqual(self.lib.combat_field_allows(0, required), 0)
            self.assertEqual(self.lib.combat_field_allows(required, required), 1)
        self.assertEqual(self.lib.combat_field_allows(ignite, ignite), 1)
        self.assertEqual(self.lib.combat_field_allows(1 << 1, ignite), 0)
        self.assertEqual(self.lib.combat_field_allows(ignite, ignite | 1), 0)
        self.assertEqual(self.lib.combat_field_allows(ignite | 1, ignite | 1), 1)
        self.assertEqual(self.lib.combat_field_allows(0xffffffff, ignite), 0)
        self.assertEqual(self.lib.combat_field_allows(ignite, 0), 0)
        self.assertEqual(self.lib.combat_field_allows(0, 0), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
