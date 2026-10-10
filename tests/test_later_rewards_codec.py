#!/usr/bin/env python3
"""Revision11 receipt codec and exact frozen10 differential tests (host only)."""
import ctypes as C
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
import unittest

from test_save5 import A, B, SIZE, Save, Economy, Quests, Instance, Roster, compare_state, repair_crc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from check_later_rewards_history import ORACLE, creature_data, verify_oracle, outputs

SOURCES = ('save4', 'save5', 'creatures', 'creature_data', 'equipment', 'equipment_data')


def build(directory, name, source=ROOT, mutations=None):
    target = directory / name
    target.mkdir()
    todo = [stem + '.c' for stem in SOURCES]
    copied = set()
    while todo:
        path = todo.pop()
        if path in copied:
            continue
        copied.add(path)
        text = (source / 'src' / path).read_text()
        for before, after in (mutations or {}).get(path, ()):
            assert before in text, (path, before)
            text = text.replace(before, after, 1)
        (target / path).write_text(text)
        todo += re.findall(r'^#include "([^"]+)"', text, re.M)
    bridge = '#include "save5.c"\n'
    if source == ROOT:
        bridge += 'int frozen_instance(const CreatureInstance*c){return history10_instance_validate(c);}\n'
    (target / 'codec.c').write_text(bridge)
    library = target / 'codec.so'
    subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-ffreestanding', '-fno-builtin', '-DSAVE4_HOST_TEST', '-DSAVE5_HOST_TEST',
                    '-shared', '-fPIC', '-I' + str(target),
                    str(target / 'codec.c'), *[str(target / (s + '.c')) for s in SOURCES if s != 'save5'],
                    '-o', str(library)], check=True)
    lib = C.CDLL(str(library))
    lib.ram = (C.c_ubyte * 32768).in_dll(lib, 'save5_test_sram')
    for fn in ('save5_load', 'save5_store', 'save5_validate', 'save5_begin'):
        getattr(lib, fn).argtypes = [C.POINTER(Save)]
    lib.save5_validate_revision.argtypes = [C.POINTER(Save), C.c_uint]
    lib.creatures_instance_validate.argtypes = [C.POINTER(Instance)]
    if source == ROOT:
        lib.frozen_instance.argtypes = [C.POINTER(Instance)]
        lib.save5_later_claims_validate.argtypes = [C.POINTER(Quests), C.POINTER(Economy)]
    return lib


def install(lib, bank=None, other=None):
    lib.save5_test_reset_writer()
    lib.save5_test_fail_after(-1)
    lib.save5_test_corrupt_write(-1, 0)
    lib.ram[:] = bytes([255]) * 32768
    if bank is not None:
        lib.ram[A:A + SIZE] = bank
    if other is not None:
        lib.ram[B:B + SIZE] = other


class LaterRewardsCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        verify_oracle()
        cls.tmp = tempfile.TemporaryDirectory(prefix='later-reward-codec-')
        cls.addClassCleanup(cls.tmp.cleanup)
        directory = Path(cls.tmp.name)
        cls.current = build(directory, 'current')
        cls.old = build(directory, 'accepted10', ORACLE)
        cls.changed = build(directory, 'changed-current', mutations={
            'save5.c': [('quest_masks[64] = {7,3,7,7', 'quest_masks[64] = {15,3,7,7'),
                        ('equipment_source_quest[48] = {-1,7,', 'equipment_source_quest[48] = {-1,0,')],
            'creature_data.c': [('    {1, 1},', '    {1, 23},')],
            'economy_types.h': [('e->gold>9999', 'e->gold>20000')],
        })
        fixture = ROOT / 'tests/fixtures/v5-revision9/covenants-all128-72-cold.sav'
        assert hashlib.sha256(fixture.read_bytes()).hexdigest() == 'eec8efbfeaf83a51b66faa0c8e9d6a3061af36b88fb6d7b3aa77fbc47107122a'
        cls.old.ram[:] = fixture.read_bytes()
        cls.complete = Save()
        assert cls.old.save5_load(C.byref(cls.complete)) == 1
        e = cls.complete.economy
        e.relics = e.boss_claims = 7
        e.bought[0], e.used[0], e.supplies[0] = 2, 1, 1
        e.earned, e.spent, e.gold = 357, 36, 321
        assert cls.old.save5_validate(C.byref(cls.complete)) == 1
        install(cls.old)
        assert cls.old.save5_store(C.byref(cls.complete)) == 1
        cls.bank = bytes(cls.old.ram[A:A + SIZE])
        assert cls.bank[12:14] == bytes((10, 0))

    def read(self, lib, bank, accepted=True, other=None):
        install(lib, bank, other)
        before = bytes(lib.ram)
        out = Save.from_buffer_copy(bytes([0x5a]) * C.sizeof(Save))
        untouched = bytes(out)
        self.assertEqual(lib.save5_load(C.byref(out)), int(accepted))
        self.assertEqual(lib.save5_has_valid(), int(accepted))
        self.assertEqual(bytes(lib.ram), before)
        if not accepted:
            self.assertEqual(bytes(out), untouched)
        return out

    def test_frozen_policy_is_reproducible_and_layout_unchanged(self):
        for path, content in outputs().items():
            self.assertEqual((ROOT / path).read_text(), content, path)
        self.assertEqual(C.sizeof(Economy), 32)
        self.assertEqual(Economy.later_claims.offset, 23)
        self.assertEqual(Economy.reserved.offset, 24)
        self.assertEqual(C.sizeof(self.complete.equipment), 512)
        self.assertEqual(len(self.complete.equipment.bag), 48)
        self.assertEqual(len(self.complete.roster.instances), 160)

    def test_revision10_load_grants_nothing_and_first_write_preserves_payload(self):
        s = self.read(self.current, self.bank)
        self.assertEqual(compare_state(s), compare_state(self.complete))
        self.assertEqual(s.economy.later_claims, 0)
        original = bytes(self.current.ram)
        self.assertEqual(self.current.save5_store(C.byref(s)), 1)
        newer = bytes(self.current.ram[B:B + SIZE])
        self.assertEqual(bytes(self.current.ram[A:A + SIZE]), self.bank)
        self.assertEqual(bytes(self.current.ram[:A]), original[:A])
        self.assertEqual(newer[12:14], bytes((11, 0)))
        self.assertEqual(newer[6:8], (5088).to_bytes(2, 'little'))
        self.assertEqual(newer[32:], self.bank[32:])
        self.assertEqual(compare_state(self.read(self.current, newer)), compare_state(s))

    def test_all_original_nine_reserved_bytes_reject_under_revision10(self):
        for offset in range(5079, 5088):
            for value in (1, 15, 128, 255):
                with self.subTest(offset=offset, value=value):
                    bad = bytearray(self.bank)
                    bad[offset] = value
                    bad = repair_crc(bad)
                    self.read(self.old, bad, False)
                    self.read(self.current, bad, False)
                    self.read(self.changed, bad, False)

    def test_revision11_receipts_roundtrip_and_future_versions_reject(self):
        for receipt in (0, 1, 2, 4, 8, 15):
            s = Save.from_buffer_copy(bytes(self.complete))
            s.economy.later_claims = receipt
            award = sum(gold for bit, gold in enumerate((80, 100, 120, 160)) if receipt & (1 << bit))
            s.economy.earned += award
            s.economy.gold += award
            self.assertEqual(self.current.save5_validate(C.byref(s)), 1)
            self.assertEqual(self.current.save5_validate_revision(C.byref(s), 11), 1)
            self.assertEqual(self.current.save5_validate_revision(C.byref(s), 10), int(not receipt))
            install(self.current)
            self.assertEqual(self.current.save5_store(C.byref(s)), 1)
            bank = bytes(self.current.ram[A:A + SIZE])
            self.assertEqual(bank[5079], receipt)
            self.assertEqual(bank[5080:5088], bytes(8))
            self.assertEqual(compare_state(self.read(self.current, bank)), compare_state(s))
        for revision in (0, 12, 255, 256, 65535):
            bad = bytearray(bank)
            bad[12:14] = revision.to_bytes(2, 'little')
            self.read(self.current, repair_crc(bad), False)
            self.assertEqual(self.current.save5_validate_revision(C.byref(s), revision), 0)
        for offset in range(5079, 5088):
            bad = bytearray(bank)
            bad[offset] = 128 if offset == 5079 else 1
            self.read(self.current, repair_crc(bad), False)

    def test_later_receipt_earned_floors_and_zero_earned_forgery(self):
        for receipt in range(1, 16):
            later_floor = sum(gold for bit, gold in enumerate((80, 100, 120, 160)) if receipt & (1 << bit))
            for original in range(8):
                original_floor = sum(gold for bit, gold in enumerate((60, 100, 160)) if original & (1 << bit))
                minimum = original_floor + later_floor
                with self.subTest(later=receipt, original=original, minimum=minimum):
                    s = Save.from_buffer_copy(bytes(self.complete))
                    s.economy = Economy()
                    s.economy.relics = s.economy.boss_claims = original
                    s.economy.later_claims = receipt
                    s.economy.earned = s.economy.gold = minimum
                    self.assertEqual(self.current.save5_validate(C.byref(s)), 1)
                    self.assertEqual(self.current.save5_validate_revision(C.byref(s), 11), 1)
                    self.assertEqual(self.current.save5_validate_revision(C.byref(s), 10), 0)
                    install(self.current)
                    self.assertEqual(self.current.save5_store(C.byref(s)), 1)
                    bank = bytes(self.current.ram[A:A + SIZE])
                    self.assertEqual(compare_state(self.read(self.current, bank)), compare_state(s))
                    for earned in (0, minimum - 1):
                        # Keep earned-spent==gold lawful: only the ownership
                        # floor is forged, and every required quest is CLAIMED.
                        s.economy.earned = s.economy.gold = earned
                        self.assertEqual(self.current.save5_validate(C.byref(s)), 0)
                        self.assertEqual(self.current.save5_begin(C.byref(s)), 0)
                        bad = bytearray(bank)
                        bad[5056:5060] = earned.to_bytes(4, 'little')
                        bad[5064:5066] = earned.to_bytes(2, 'little')
                        self.read(self.current, repair_crc(bad), False)
                        self.read(self.old, repair_crc(bad), False)
                        # Re-labeling cannot smuggle the new receipt through
                        # either the original or frozen revision10 decoder.
                        bad[12:14] = bytes((10, 0))
                        self.read(self.current, repair_crc(bad), False)
                        self.read(self.old, repair_crc(bad), False)
                    # Clipping does not invalidate the floor: reaching the
                    # cap already implies earned >= 9999 > all awards (780).
                    s.economy.earned = s.economy.gold = 9999
                    self.assertEqual(self.current.save5_validate(C.byref(s)), 1)

    def test_receipts_require_matching_claimed_quest_only(self):
        for index, quest in enumerate((21, 24, 32, 40)):
            q, e = Quests(), Economy()
            e.earned = e.gold = 1000
            e.later_claims = 1 << index
            for status in range(4):
                q.states[quest >> 2] = status << ((quest & 3) * 2)
                self.assertEqual(self.current.save5_later_claims_validate(C.byref(q), C.byref(e)), int(status == 3))
            e.later_claims = 0
            self.assertEqual(self.current.save5_later_claims_validate(C.byref(q), C.byref(e)), 1)
        s = Save()
        self.current.creatures_roster_init(C.byref(s.roster))
        self.current.equipment_init(C.byref(s.equipment))
        s.economy.earned = s.economy.gold = 1000
        install(self.current)
        self.assertEqual(self.current.save5_store(C.byref(s)), 1)
        bank = bytearray(self.current.ram[A:A + SIZE])
        for receipt in (1, 2, 4, 8, 15, 16, 255):
            s.economy.later_claims = receipt
            self.assertEqual(self.current.save5_validate(C.byref(s)), 0)
            self.assertEqual(self.current.save5_begin(C.byref(s)), 0)
            bad = bytearray(bank)
            bad[5079] = receipt
            self.read(self.current, repair_crc(bad), False)

    def test_invalid_newer_bank_falls_back_without_writes(self):
        for revision, receipt in ((10, 1), (11, 16), (12, 0)):
            bad = bytearray(self.bank)
            bad[12:14] = revision.to_bytes(2, 'little')
            bad[8:12] = (99).to_bytes(4, 'little')
            bad[5079] = receipt
            s = self.read(self.current, repair_crc(bad), other=self.bank)
            self.assertEqual(compare_state(s), compare_state(self.complete))

    def test_revision10_is_independent_of_live_policy_mutations(self):
        for lib in (self.current, self.changed):
            self.assertEqual(compare_state(self.read(lib, self.bank)), compare_state(self.complete))
            self.assertEqual(lib.save5_validate_revision(C.byref(self.complete), 10), 1)
        self.assertEqual(self.changed.save5_validate(C.byref(self.complete)), 0)
        s = Save()
        self.old.creatures_roster_init(C.byref(s.roster))
        self.old.equipment_init(C.byref(s.equipment))
        s.economy.gold = s.economy.earned = 10000
        self.assertEqual(self.changed.save5_validate(C.byref(s)), 1)
        self.assertEqual(self.changed.save5_validate_revision(C.byref(s), 10), 0)
        s.economy.gold = s.economy.earned = 0
        s.campaign.chapter_flags = 1
        s.quests.region_flags[0] = 1
        s.quests.states[0], s.quests.objectives[0] = 1, 8
        self.assertEqual(self.changed.save5_validate(C.byref(s)), 1)
        self.assertEqual(self.changed.save5_validate_revision(C.byref(s), 10), 0)

    def test_revision10_exact_original_bank_mutation_differential(self):
        rng = random.Random(1105079)
        positions = list(range(32, 47)) + list(range(4032, 4296)) + list(range(4544, 5088))
        positions += [160 + i * 24 + j for i in (0, 1, 12, 64, 71, 72, 159) for j in range(24)]
        for case in range(1500):
            bad = bytearray(self.bank)
            offset = rng.choice(positions)
            bad[offset] = rng.choice((0, 1, 2, 3, 7, 15, 31, 63, 127, 128, 254, 255))
            bad = repair_crc(bad)
            install(self.old, bad)
            expected = Save()
            accepted = bool(self.old.save5_load(C.byref(expected)))
            for lib in (self.current, self.changed):
                actual = self.read(lib, bad, accepted)
                if accepted:
                    self.assertEqual(compare_state(actual), compare_state(expected), (case, offset))

    def test_frozen_creature_acceptance_matches_original_all128_forms(self):
        for f in creature_data()['forms']:
            c = Instance()
            c.form_id, c.flags, c.level, c.bond = f['id'], 1, 50, 100
            c.xp, c.instance_id, c.trial_flags = 470596, 1, f['trial_mask']
            c.polarity, c.equipped[0] = f['polarity'], f['learn'][0][1]
            self.assertEqual(self.old.creatures_instance_validate(C.byref(c)), 1, f['id'])
            for field, values in (
                ('flags', (0, 1, 2, 3, 7, 8, 255)), ('level', (0, 1, 25, 34, 49, 50, 51, 255)),
                ('bond', (0, 39, 40, 44, 45, 59, 60, 100, 101, 255)),
                ('trial_flags', (0, 1, 2, 3, 1024, 2048, 3072, f['required_trial'], 65535)),
                ('nickname_id', (0, 1, 65535)), ('polarity', (0, 1, 2, 255)),
                ('selected_command', (0, 1, 2, 255)), ('xp', (0, 4, 470595, 470596, 470597, 0xffffffff)),
                ('instance_id', (0, 1, 0xfffffffe, 0xffffffff)),
            ):
                for value in values:
                    mutated = Instance.from_buffer_copy(bytes(c))
                    setattr(mutated, field, value)
                    expected = self.old.creatures_instance_validate(C.byref(mutated))
                    self.assertEqual(self.current.frozen_instance(C.byref(mutated)), expected, (f['id'], field, value))
            for ability in range(256):
                c.equipped[0] = ability
                self.assertEqual(self.current.frozen_instance(C.byref(c)), self.old.creatures_instance_validate(C.byref(c)), (f['id'], ability))


if __name__ == '__main__':
    unittest.main(verbosity=2)
