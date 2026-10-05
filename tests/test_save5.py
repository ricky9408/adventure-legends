#!/usr/bin/env python3
"""Format-5 host SRAM, power-loss, content validation and legacy migration tests.

No game RAM is injected and no emulator is launched by this host suite. v2/v3
fixtures are the pinned controller-produced bytes from test_save4. v4 fixtures
below are exact banks from the frozen controller-only campaign. Full originals
are additionally hash-checked when present. Run python3 tests/test_save5.py.
"""
import binascii
import ctypes as C
import hashlib
import itertools
import json
import sys
import os
from pathlib import Path
import random
import shlex
import subprocess
import tempfile
import unittest

from test_save4 import CampaignSave, AUTHENTIC_FIXTURES, legacy, record, fields, state

ROOT = Path(__file__).resolve().parents[1]
A, B, SIZE, USED = 0x200, 0x1A00, 6144, 5056
IDLE, BUSY, DONE, FAILED = range(4)
LEGACY_ENABLED = (1, 2, 4, 5, 7, 8, 10, 11)
ENABLED = LEGACY_ENABLED + (13, 14, 16)
QUEST_MASKS = (7,3,7,7,3,1,1,1,3,7,1)
SOURCE_QUEST = (None,7,None,6,None,4,0,8,1,9,5,10,6)


def claim_equipment_quests(s):
    s.quests.region_flags[0] |= 1
    for q in set(SOURCE_QUEST) - {None}:
        s.quests.states[q // 4] |= 3 << (2 * (q % 4))
        s.quests.objectives[q] = QUEST_MASKS[q]
        s.quests.rewards[q // 8] |= 1 << (q % 8)



class Instance(C.Structure):
    _fields_ = [('form_id', C.c_ubyte), ('flags', C.c_ubyte),
                ('level', C.c_ubyte), ('bond', C.c_ubyte),
                ('xp', C.c_uint), ('instance_id', C.c_uint),
                ('nickname_id', C.c_ushort), ('trial_flags', C.c_ushort),
                ('equipped', C.c_ubyte * 2), ('polarity', C.c_ubyte),
                ('selected_command', C.c_ubyte), ('cosmetic_seed', C.c_uint)]


class Roster(C.Structure):
    _fields_ = [('instances', Instance * 160), ('party', C.c_ubyte * 4),
                ('selected_party', C.c_ubyte), ('next_instance_id', C.c_uint),
                ('seen', C.c_ubyte * 16), ('obtained', C.c_ubyte * 16),
                ('rewards', C.c_ubyte * 16), ('expedition_bond', C.c_ubyte * 160),
                ('expedition_events', C.c_ubyte * 64), ('lifetime_field_aid', C.c_ubyte * 16)]


class Quests(C.Structure):
    _fields_ = [('states', C.c_ubyte * 16), ('objectives', C.c_ushort * 64),
                ('rewards', C.c_ubyte * 8), ('variables', C.c_ubyte * 64),
                ('region_flags', C.c_ubyte * 32), ('anchors', C.c_ubyte * 16)]


class EquipmentRecord(C.Structure):
    _fields_ = [('item_id', C.c_ushort), ('rank', C.c_ubyte),
                ('flags', C.c_ubyte), ('quantity', C.c_ubyte), ('reserved', C.c_ubyte * 3)]


class Equipment(C.Structure):
    _fields_ = [('bag', EquipmentRecord * 48), ('equipped', C.c_ubyte * 5),
                ('settings_reserved', C.c_ubyte * 11), ('seen', C.c_ubyte * 64),
                ('wallet_key_reserved', C.c_ubyte * 16), ('reward_claims', C.c_ubyte * 8),
                ('reserved', C.c_ubyte * 24)]


class Save(C.Structure):
    _fields_ = [('campaign', CampaignSave), ('roster', Roster),
                ('quests', Quests), ('equipment', Equipment)]


def repair_crc(b):
    b = bytearray(b)
    b[16:20] = bytes(4)
    commit, b[20] = b[20], 0
    b[16:20] = binascii.crc32(b).to_bytes(4, 'little')
    b[20] = commit
    return b


def compare_state(s):
    return fields(s.campaign), bytes(s.roster), bytes(s.quests), bytes(s.equipment)


# (filename, full32KiB SHA256, exact A32bytes, exact B32bytes)
AUTHENTIC_V4 = [
    ('grove-complete.sav', '505c3c89dc61b783ecef644b54afd751953796c1a5c69c69a194b97f889cf7c1',
     '45420420a5090000000003010103000000000000000200000000000000008877',
     '45420420a5080000000003010103000000000000000000000000000000005bf4'),
    ('sky-complete.sav', 'c77f7ac55c0103d4ad454dd642469f50318b5356ba76489c8802a608c896381d',
     '45420420a521000000000303010300003f000000000e00020000000000005bf4',
     '45420420a520000000000303010300003f000000000600020000000000001098'),
    ('core-complete-ending-pending.sav', 'fff8f7fe9eef088f1ecbdc97acb7e8b7d00b44dd8a0a646ff0a34a6ead781bc9',
     '45420420a53d00000000030701030000ffff0000003e00000000000000004d51',
     '45420420a53c00000000030701030000ffff0000001e000000000000000005b3'),
    ('finished-ending.sav', '8f603dff9d9893675b2864a900f77a4608d7de43b85fa1464ad3b5f820607809',
     '45420420a53f00000000030f01030000ffff0000003e00000000000000001b4a',
     '45420420a53e00000000030701030000ffff0000003e0000000000000000919f'),
]


class Save5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='emberbond-save5-host-')
        cls.addClassCleanup(cls.tmp.cleanup)
        so = Path(cls.tmp.name) / 'save5.so'
        compiler = shlex.split(os.environ.get('HOST_CC', 'cc'))
        subprocess.run(compiler + [
            '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-ffreestanding',
            '-fno-builtin', '-DSAVE4_HOST_TEST', '-DSAVE5_HOST_TEST', '-shared', '-fPIC',
            *[str(ROOT / 'src' / name) for name in ('save4.c', 'save5.c', 'creatures.c', 'creature_data.c', 'equipment.c', 'equipment_data.c')],
            '-o', str(so),
        ], check=True)
        cls.lib = C.CDLL(str(so))
        cls.sram = (C.c_ubyte * 32768).in_dll(cls.lib, 'save5_test_sram')
        cls.old_sram = (C.c_ubyte * 256).in_dll(cls.lib, 'save4_test_sram')
        for name in ('save5_load', 'save5_store', 'save5_begin', 'save5_validate'):
            getattr(cls.lib, name).argtypes = [C.POINTER(Save)]
            getattr(cls.lib, name).restype = C.c_int
        for name in ('save5_status', 'save5_progress', 'save5_progress_total', 'save5_test_write_count',
                     'save5_test_step_work'):
            getattr(cls.lib, name).restype = C.c_uint
        cls.lib.save5_step.argtypes = [C.c_uint]
        cls.lib.save5_step.restype = C.c_uint
        cls.lib.save5_test_fail_after.argtypes = [C.c_int]
        cls.lib.save5_test_corrupt_write.argtypes = [C.c_int, C.c_ubyte]
        cls.lib.save5_crc32.argtypes = [C.POINTER(C.c_ubyte), C.c_uint]
        cls.lib.save5_crc32.restype = C.c_uint
        cls.lib.save4_load.argtypes = [C.POINTER(CampaignSave)]
        cls.lib.creatures_migrate_legacy.argtypes = [C.POINTER(Roster), C.c_uint, C.c_uint]
        cls.lib.creatures_grant.argtypes = [C.POINTER(Roster)] + [C.c_uint] * 5
        cls.lib.creatures_grant.restype = C.c_uint
        cls.lib.creatures_grant_story.argtypes = [C.POINTER(Roster), C.c_uint, C.c_uint]
        cls.lib.creatures_grant_story.restype = C.c_uint
        cls.lib.creatures_roster_validate.argtypes = [C.POINTER(Roster)]
        cls.lib.creatures_form.argtypes = [C.c_uint]
        cls.lib.creatures_form.restype = C.c_void_p
        cls.lib.creatures_roster_init.argtypes = [C.POINTER(Roster)]
        cls.lib.creatures_mark_trial.argtypes = [C.POINTER(Instance),C.c_uint]
        cls.lib.creatures_evolve.argtypes = [C.POINTER(Roster),C.c_uint,C.c_uint,C.c_int,C.c_int]
        cls.lib.equipment_init.argtypes = [C.POINTER(Equipment)]
        cls.lib.equipment_claim.argtypes = [C.POINTER(Equipment), C.c_uint, C.c_uint, C.POINTER(C.c_uint)]
        cls.lib.equipment_claim.restype = C.c_uint
        cls.lib.equipment_reward_source.argtypes = [C.c_uint]
        cls.lib.equipment_reward_source.restype = C.c_uint
        cls.lib.save5_quest_state.argtypes = [C.POINTER(Quests), C.c_uint]
        cls.lib.save5_quest_set_state.argtypes = [C.POINTER(Quests), C.c_uint, C.c_uint]
        cls.lib.creatures_credit_event.argtypes = [C.POINTER(Roster), C.c_uint, C.c_uint, C.c_uint]

    def setUp(self):
        self.reset()

    def reset(self, value=255):
        self.sram[:] = bytes([value]) * 32768
        self.lib.save5_test_reset_writer()
        self.lib.save5_test_fail_after(-1)
        self.lib.save5_test_corrupt_write(-1, 0)

    def put(self, b, offset=0):
        self.sram[offset:offset+len(b)] = b

    def fresh(self, chapter=0, spirit=0):
        s = Save()
        s.campaign.chapter_flags = chapter
        s.campaign.spirit = spirit
        if chapter & 1:
            s.campaign.story_seen = 2
        if chapter & 2:
            s.campaign.story_seen |= 8
        self.assertEqual(self.lib.creatures_migrate_legacy(C.byref(s.roster), chapter, spirit), 1)
        self.lib.equipment_init(C.byref(s.equipment))
        self.assertEqual(self.lib.save5_validate(C.byref(s)), 1)
        return s

    def load(self):
        s = Save()
        self.assertEqual(self.lib.save5_load(C.byref(s)), 1)
        return s

    def store(self, s):
        original = bytes(s)
        self.assertEqual(self.lib.save5_store(C.byref(s)), 1)
        self.assertEqual(bytes(s), original)
        self.assertEqual(self.lib.save5_status(), DONE)

    def invalid(self):
        before = bytes(self.sram)
        s = Save.from_buffer_copy(bytes([0xCC]) * C.sizeof(Save))
        original = bytes(s)
        self.assertEqual(self.lib.save5_load(C.byref(s)), 0)
        self.assertEqual(bytes(s), original)
        self.assertEqual(self.lib.save5_has_valid(), 0)
        self.assertEqual(bytes(self.sram), before)

    def test_crc_oracle_and_width(self):
        self.assertEqual(C.sizeof(Instance), 24)
        rng = random.Random(5056)
        for b in [b'', b'123456789', bytes(6144)] + [rng.randbytes(n) for n in range(64)]:
            c = (C.c_ubyte * len(b)).from_buffer_copy(b)
            self.assertEqual(self.lib.save5_crc32(c, len(b)), binascii.crc32(b))
        self.assertEqual(binascii.crc32(b'123456789'), 0xCBF43926)

    def test_empty_null_readonly_and_failure_atomic(self):
        for value in (0, 255, 0xCC):
            self.reset(value)
            self.invalid()
        self.assertEqual(self.lib.save5_load(None), 0)
        self.assertEqual(self.lib.save5_begin(None), 0)
        self.assertEqual(self.lib.save5_store(None), 0)
        self.assertEqual(self.lib.save5_test_write_count(), 0)

    def test_explicit_layout_full_roundtrip_and_reservations(self):
        s = self.fresh(3, 3)
        s.campaign.bridge, s.campaign.torches = 1, 3
        s.campaign.relic, s.campaign.camp = 1, 1
        s.campaign.room_flags = 0xFFFF
        s.campaign.optional_flags, s.campaign.story_seen = 1, 0x5F
        s.roster.expedition_bond[0] = 7
        s.roster.expedition_events[31] = 0xA5
        s.roster.lifetime_field_aid[9] = 0x48
        s.roster.rewards[10] = 0x20
        s.roster.instances[0].cosmetic_seed = 0xDEADBEEF
        self.store(s)
        got = self.load()
        self.assertEqual(compare_state(got), compare_state(s))
        self.assertEqual((got.campaign.sequence, got.campaign.loaded_version), (1, 5))
        b = bytes(self.sram[A:A+SIZE])
        self.assertEqual(b[:8], b'EB\x05\x20\x00\x18\xc0\x13')
        self.assertEqual(b[20], 0xA5)
        self.assertEqual(b, repair_crc(b))
        self.assertEqual(b[160+20:160+24], b'\xef\xbe\xad\xde')
        self.assertEqual(b[4296], 7)
        self.assertEqual(b[4456+31], 0xA5)
        self.assertEqual(b[4520+9], 0x48)
        for lo, hi in ((21,32), (47,96), (144,160), (4005,4008), (4012,4296), (4536,4544), (4552,4928), (4933,4944), (4945,5024), (5025,6144)):
            self.assertEqual(b[lo:hi], bytes(hi-lo))
        self.assertEqual(bytes(self.sram[:A]), b'\xff' * A)
        self.assertEqual(bytes(self.sram[B+SIZE:]), b'\xff' * (32768-B-SIZE))

    def test_incremental_budget_snapshot_and_busy_refusal(self):
        s = self.fresh()
        expected = compare_state(s)
        before = bytes(self.sram)
        self.assertEqual(self.lib.save5_begin(C.byref(s)), 1)
        self.assertEqual(bytes(self.sram), before, 'begin touched SRAM')
        self.assertEqual(self.lib.save5_step(0), BUSY)
        self.assertEqual(self.lib.save5_progress(), 0)
        s.roster.instances[0].bond = 99
        s.campaign.relic = 1
        self.assertEqual(self.lib.save5_begin(C.byref(s)), 0)
        untouched = Save.from_buffer_copy(bytes([0xCE]) * C.sizeof(Save))
        saved = bytes(untouched)
        self.assertEqual(self.lib.save5_load(C.byref(untouched)), 0)
        self.assertEqual(bytes(untouched), saved)
        prior = 0
        for i in range(50000):
            budget = (1, 7, 24, 127, 1024)[i % 5]
            result = self.lib.save5_step(budget)
            self.assertLessEqual(self.lib.save5_test_step_work(), budget)
            progress = self.lib.save5_progress()
            self.assertGreaterEqual(progress, prior)
            self.assertLessEqual(progress, self.lib.save5_progress_total())
            prior = progress
            if result != BUSY:
                break
        else:
            self.fail('incremental save failed to finish')
        self.assertEqual(result, DONE)
        self.assertEqual(compare_state(self.load()), expected)
        self.assertEqual(self.lib.save5_test_write_count(), SIZE + 1)

    def test_invalid_runtime_never_writes_or_mutates(self):
        s = self.fresh()
        broken = Save.from_buffer_copy(bytes(s))
        broken.quests.states[15] = 1
        self.assert_runtime_invalid(broken)
        broken = Save.from_buffer_copy(bytes(s))
        broken.equipment.reserved[0] = 1
        self.assert_runtime_invalid(broken)
        for attr, value in [('form_id', 3), ('flags', 0x81), ('level', 2), ('xp', 470597),
                            ('bond', 101), ('instance_id', 0), ('nickname_id', 1),
                            ('trial_flags', 2), ('polarity', 2), ('selected_command', 2)]:
            broken = Save.from_buffer_copy(bytes(s))
            setattr(broken.roster.instances[0], attr, value)
            self.assert_runtime_invalid(broken)
        broken = Save.from_buffer_copy(bytes(s))
        broken.roster.instances[0].equipped[0] = 255
        self.assert_runtime_invalid(broken)
        broken = Save.from_buffer_copy(bytes(s))
        broken.roster.instances[1].instance_id = broken.roster.instances[0].instance_id
        self.assert_runtime_invalid(broken)

    def assert_runtime_invalid(self, s):
        before, memory = bytes(self.sram), bytes(s)
        writes = self.lib.save5_test_write_count()
        self.assertEqual(self.lib.save5_validate(C.byref(s)), 0)
        if self.lib.save5_begin(C.byref(s)):
            while self.lib.save5_step(1024) == BUSY:
                pass
        self.assertEqual(self.lib.save5_status(), FAILED)
        self.assertEqual(bytes(self.sram), before)
        self.assertEqual(bytes(s), memory)
        self.assertEqual(self.lib.save5_test_write_count(), writes)

    def test_crc_valid_malformed_semantics_and_headers(self):
        s = self.fresh()
        self.store(s)
        good = bytes(self.sram[A:A+SIZE])
        mutations = [(0, 0), (2, 6), (3, 31), (4, 1), (6, 0), (12, 3),
                     (14, 1), (21, 1), (32, 14), (34, 2), (46, 3), (47, 1),
                     (96, 255), (112, 0), (128, 0), (144, 1),
                     (160+1, 0x81), (160+2, 2), (160+3, 101), (160+8, 0),
                     (160+12, 1), (160+14, 2), (160+16, 255), (160+17, 255),
                     (160+18, 2), (160+19, 2),
                     (4000, 160), (4000, 2), (4001, 0), (4004, 4), (4004, 255),
                     (4005, 1), (4008, 0), (4012, 1), (4047, 1), (4296, 11),
                     (4298, 1), (4536, 1), (4544, 0), (5056, 1), (6143, 1)]
        mutations += [(160, form) for form in range(256) if form not in ENABLED]
        for offset, value in mutations:
            with self.subTest(offset=offset, value=value):
                self.reset()
                bad = bytearray(good)
                bad[offset] = value
                self.put(repair_crc(bad), A)
                self.invalid()
        for offset, payload in [(160+4, (470597).to_bytes(4,'little')),
                                (184+8, good[168:172]),
                                (4008, (2).to_bytes(4,'little'))]:
            self.reset()
            bad = bytearray(good)
            bad[offset:offset+len(payload)] = payload
            self.put(repair_crc(bad), A)
            self.invalid()

    def test_every_bank_byte_corruption_falls_back(self):
        s = self.fresh()
        self.store(s)
        first = bytes(self.sram)
        s.campaign.relic = 1
        self.store(s)
        both = bytes(self.sram)
        for bank, expect in ((B, 0), (A, 1)):
            for index in range(SIZE):
                self.put(both)
                self.sram[bank+index] ^= 1
                got = self.load()
                self.assertEqual(got.campaign.relic, expect, (bank, index))
        self.put(first)
        self.sram[A+SIZE-1] ^= 1
        self.invalid()

    def test_each_interruption_position_first_and_replacement_banks(self):
        # All 6145 durable byte writes, including commit, for first migration,
        # replacing B while A is current, then replacing A while B is current.
        self.put(legacy(3, room=1, bridge=1, relic=1, camp=1))
        old = bytes(self.sram)
        migrated = self.load()
        migrated.campaign.relic = 0
        scenarios = [(old, migrated, 3, 0)]
        self.store(migrated)
        first = bytes(self.sram)
        newer = Save.from_buffer_copy(bytes(migrated))
        newer.campaign.bridge = 0
        newer.campaign.room, newer.campaign.spawn = 0, 0
        scenarios.append((first, newer, 5, 1))
        self.store(newer)
        second = bytes(self.sram)
        newest = Save.from_buffer_copy(bytes(newer))
        newest.campaign.torches = 3
        scenarios.append((second, newest, 5, 2))
        for baseline, target, old_version, old_seq in scenarios:
            for count in range(SIZE+2):
                self.put(baseline)
                self.lib.save5_test_reset_writer()
                self.lib.save5_test_fail_after(count)
                original = bytes(target)
                ok = self.lib.save5_store(C.byref(target))
                self.assertEqual(ok, int(count >= SIZE+1), (old_seq, count))
                self.assertEqual(bytes(target), original)
                got = self.load()
                self.assertEqual(got.campaign.loaded_version, 5 if ok else old_version)
                self.assertEqual(got.campaign.sequence, old_seq+1 if ok else old_seq)
                self.assertEqual(bytes(self.sram[:A]), baseline[:A])
                if old_seq:
                    active = A if old_seq == 1 else B
                    self.assertEqual(bytes(self.sram[active:active+SIZE]), baseline[active:active+SIZE])
                if ok:
                    self.assertEqual(compare_state(got), compare_state(target))
        self.lib.save5_test_fail_after(-1)

    def test_each_corrupted_write_never_commits_broken_replacement(self):
        s = self.fresh()
        self.store(s)
        first = bytes(self.sram)
        s.campaign.relic = 1
        for index in range(SIZE+1):
            self.put(first)
            self.lib.save5_test_reset_writer()
            self.lib.save5_test_fail_after(-1)
            self.lib.save5_test_corrupt_write(index, 1)
            self.assertEqual(self.lib.save5_store(C.byref(s)), 0, index)
            got = self.load()
            self.assertEqual((got.campaign.sequence, got.campaign.relic), (1, 0), index)
            self.assertEqual(bytes(self.sram[A:A+SIZE]), first[A:A+SIZE])
        self.lib.save5_test_corrupt_write(-1, 0)

    def test_commit_is_last_and_survives_cut_before_final_readback(self):
        s = self.fresh()
        self.store(s)
        original = bytes(self.sram)
        s.campaign.relic = 1
        self.lib.save5_test_fail_after(-1)
        self.assertEqual(self.lib.save5_begin(C.byref(s)), 1)
        for _ in range(100000):
            self.lib.save5_step(1)
            writes = self.lib.save5_test_write_count()
            self.assertEqual(bytes(self.sram[A:A+SIZE]), original[A:A+SIZE])
            if writes <= SIZE:
                self.assertNotEqual(self.sram[B+20], 0xA5)
            if writes == SIZE+1:
                self.assertEqual(self.sram[B+20], 0xA5)
                self.assertEqual(self.lib.save5_status(), BUSY)
                # Reboot after durable commit, before the asynchronous final
                # readback: the complete new bank is already authoritative.
                self.lib.save5_test_reset_writer()
                got = self.load()
                self.assertEqual((got.campaign.sequence, got.campaign.relic), (2,1))
                break
        else:
            self.fail('commit was never reached')

    def test_large_budget_is_capped_and_zero_budget_is_quiet(self):
        s = self.fresh(3,3)
        self.assertEqual(self.lib.save5_begin(C.byref(s)), 1)
        for _ in range(100):
            before = bytes(self.sram)
            progress = self.lib.save5_progress()
            self.assertEqual(self.lib.save5_step(0), BUSY)
            self.assertEqual(bytes(self.sram), before)
            self.assertEqual(self.lib.save5_progress(), progress)
            status = self.lib.save5_step(0xFFFFFFFF)
            self.assertLessEqual(self.lib.save5_test_step_work(), 3072)
            if status != BUSY:
                self.assertEqual(status, DONE)
                break
        else:
            self.fail('capped budget did not finish')
        self.assertEqual(compare_state(self.load()), compare_state(s))

    def test_unsigned_sequence_wrap_equal_and_half_range(self):
        s = self.fresh()
        self.store(s)
        b = bytearray(self.sram[A:A+SIZE])
        for sa, sb, expected in [(0xFFFFFFFF,0,0), (7,7,7), (0,0x80000000,0),
                                 (0xFFFFFFFF,0xFFFFFFFE,0xFFFFFFFF), (2,3,3)]:
            self.reset()
            a = bytearray(b); a[8:12] = sa.to_bytes(4,'little')
            newer = bytearray(b); newer[8:12] = sb.to_bytes(4,'little'); newer[37] = 1
            self.put(repair_crc(a), A); self.put(repair_crc(newer), B)
            got = self.load()
            self.assertEqual(got.campaign.sequence, expected)
            self.store(got)
            self.assertEqual(self.load().campaign.sequence, (expected+1) & 0xFFFFFFFF)

    def test_writer_rejects_crc_valid_bad_newest_bank_before_replacement(self):
        s = self.fresh()
        self.store(s)
        a = bytes(self.sram[A:A+SIZE])
        bad = bytearray(a); bad[8:12] = (2).to_bytes(4,'little'); bad[160] = 3
        self.put(repair_crc(bad), B)
        self.assertEqual(self.load().campaign.sequence, 1)
        self.lib.save5_test_fail_after(100)
        self.assertEqual(self.lib.save5_store(C.byref(s)), 0)
        self.assertEqual(bytes(self.sram[A:A+SIZE]), a)
        self.assertEqual(self.load().campaign.sequence, 1)

    def assert_migration(self, expected_version):
        before = bytes(self.sram)
        self.old_sram[:] = before[:256]
        campaign = CampaignSave()
        self.assertEqual(self.lib.save4_load(C.byref(campaign)), 1)
        s = self.load()
        self.assertEqual(fields(s.campaign, True), fields(campaign, True))
        self.assertEqual(s.campaign.loaded_version, expected_version)
        expected_forms = [1,4] + ([7] if campaign.chapter_flags & 1 else []) + ([10] if campaign.chapter_flags & 2 else [])
        actual = [i.form_id for i in s.roster.instances if i.flags & 1]
        self.assertEqual(actual, expected_forms)
        self.assertEqual(s.roster.instances[s.roster.party[s.roster.selected_party]].form_id,
                         (1,4,7,10)[campaign.spirit])
        self.assertEqual(bytes(self.sram), before, 'migration load wrote SRAM')
        self.store(s)
        self.assertEqual(bytes(self.sram[:A]), before[:A], 'migration damaged old format')
        got = self.load()
        self.assertEqual(compare_state(got), compare_state(s))
        self.assertEqual((got.campaign.sequence, got.campaign.loaded_version), (1,5))

    def test_authentic_legacy_and_v4_controller_fixtures(self):
        for name, header, digest, valid in AUTHENTIC_FIXTURES:
            with self.subTest(name=name):
                self.reset()
                file = ROOT / 'tests/fixtures/legacy' / name
                if file.exists():
                    data = file.read_bytes()
                    self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
                    self.put(data)
                else:
                    self.put(bytes.fromhex(header))
                if valid: self.assert_migration(bytes.fromhex(header)[2])
                else: self.invalid()
        frozen = ROOT / 'tests/fixtures/v4'
        for name, digest, a, b in AUTHENTIC_V4:
            with self.subTest(name=name):
                self.reset()
                file = frozen / name
                if file.exists():
                    data = file.read_bytes()
                    self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
                    self.put(data)
                else:
                    self.put(bytes.fromhex(a), 64); self.put(bytes.fromhex(b), 128)
                self.assert_migration(4)

    def test_all_legacy_payloads_chapter_boundaries_and_selected_companions(self):
        for version in (2,3):
            options = [(0,0)] if version == 2 else itertools.product(range(2), repeat=2)
            for relic, camp in options:
                for room, bridge, torches, done, quest in itertools.product(range(4), range(2), range(4), range(2), range(2)):
                    self.reset()
                    self.put(legacy(version, room, bridge, torches, done, quest, relic, camp))
                    self.assert_migration(version)
        for chapter, count in ((0,2),(1,3),(3,4),(7,4),(15,4)):
            for spirit in range(count):
                self.reset()
                old = state(chapter_flags=chapter, spirit=spirit)
                self.put(record(old, sequence=0xFFFFFFFF), 64)
                self.assert_migration(4)

    def test_full_roster_roundtrip_and_story_reward_remains_claimable(self):
        s = self.fresh()
        for i in range(2,160):
            form = ENABLED[i % len(ENABLED)]
            # Level50 allows every authored command; slots remain independent.
            self.assertEqual(self.lib.creatures_grant(C.byref(s.roster), form, 50, 100, 0, 0), i)
        before = bytes(s.roster)
        self.assertEqual(self.lib.creatures_grant_story(C.byref(s.roster), 2, 1), 255)
        self.assertEqual(bytes(s.roster), before)
        self.assertEqual(s.roster.rewards[0] & 4, 0)
        self.store(s)
        self.assertEqual(compare_state(self.load()), compare_state(s))
        # Simulate a future authorized storage transfer freeing one nonstory
        # slot; no release UI is enabled in this milestone.
        C.memset(C.byref(s.roster.instances[159]), 0, C.sizeof(Instance))
        self.assertEqual(self.lib.creatures_grant_story(C.byref(s.roster), 2, 1), 159)
        self.assertEqual(s.roster.rewards[0] & 4, 4)
        s.campaign.chapter_flags, s.campaign.story_seen = 1, 2
        self.store(s)
        self.assertEqual(compare_state(self.load()), compare_state(s))
        count = sum(bool(i.flags & 1) for i in s.roster.instances)
        self.assertEqual(self.lib.creatures_grant_story(C.byref(s.roster), 2, 1), 159)
        self.assertEqual(sum(bool(i.flags & 1) for i in s.roster.instances), count)

    def test_revision1_controller_fixture_preserves_complete_roster(self):
        fixture = ROOT / 'tests/fixtures/v5-revision1/all-evolved-village.sav'
        evidence = json.loads(fixture.with_name('provenance.json').read_text())
        old = fixture.read_bytes()
        self.assertEqual(hashlib.sha256(old).hexdigest(), evidence['sram_sha256'])
        self.assertTrue(evidence['controller_only'])
        self.assertEqual(evidence['game_ram_writes'], 0)
        self.put(old)
        migrated = self.load()
        self.assertEqual([x.form_id for x in migrated.roster.instances if x.flags & 1], [2,5,8,11])
        self.assertEqual([list(x.equipped) for x in migrated.roster.instances[:4]], [[5,0],[6,0],[7,0],[8,0]])
        self.assertEqual(bytes(migrated.quests), bytes(264))
        self.assertEqual([r.item_id for r in migrated.equipment.bag if r.item_id], [1])
        self.assertEqual(bytes(self.sram), old)
        banks = [(offset, old[offset:offset+SIZE]) for offset in (A,B)]
        offset, original = max(banks, key=lambda x: int.from_bytes(x[1][8:12], 'little'))
        self.assertEqual(original[12:14], bytes((1,0)))
        self.assertEqual(original[4032:4296], bytes(264))
        self.assertEqual(original[4544:5056], bytes(512))
        self.assertEqual(bytes(migrated.roster.expedition_bond), original[4296:4456])
        self.assertEqual(bytes(migrated.roster.expedition_events), original[4456:4520])
        self.assertEqual(bytes(migrated.roster.lifetime_field_aid), original[4520:4536])
        self.store(migrated)
        newest = bytes(self.sram[B if offset == A else A:(B if offset == A else A)+SIZE])
        self.assertEqual(newest[12:14], bytes((2,0)))
        self.assertEqual(newest[96:4032], original[96:4032])
        self.assertEqual(newest[4296:4544], original[4296:4544])
        self.assertEqual(bytes(self.sram[:A]), old[:A])
        self.assertEqual(bytes(self.sram[offset:offset+SIZE]), original)
        self.assertEqual(compare_state(self.load()), compare_state(migrated))

    def test_revision1_reserved_blocks_and_future_revision_fail_safely(self):
        s = self.fresh()
        self.store(s)
        rev2 = bytearray(self.sram[A:A+SIZE])
        rev1 = bytearray(rev2)
        rev1[12:14] = bytes((1,0)); rev1[4544:5056] = bytes(512)
        self.reset(); self.put(repair_crc(rev1), A)
        migrated = self.load()
        self.assertEqual(compare_state(migrated), compare_state(s))
        for offset in (4032,4176,4280,4544,4928,4944,5024):
            bad = bytearray(rev1); bad[offset] = 1
            self.reset(); self.put(repair_crc(bad), A); self.invalid()
        for revision in (0,3,255,256,65535):
            bad = bytearray(rev2); bad[12:14] = revision.to_bytes(2,'little')
            self.reset(); self.put(repair_crc(bad), A); self.invalid()
            self.put(repair_crc(rev1), B)
            self.assertEqual(compare_state(self.load()), compare_state(s))

    def test_revision2_postgame_resume_and_revision1_conservative_migration(self):
        for chapter, expected_room in ((7,0),(15,4)):
            s = self.fresh(chapter, 3)
            s.campaign.room = 4
            self.reset(); self.store(s)
            got = self.load()
            self.assertEqual(got.campaign.room, expected_room)
            self.assertEqual(got.campaign.spawn, 0 if expected_room else 3)
            old = bytearray(self.sram[A:A+SIZE]); old[12:14] = bytes((1,0))
            old[4544:5056] = bytes(512)
            self.reset(); self.put(repair_crc(old), A)
            got = self.load()
            self.assertEqual((got.campaign.room,got.campaign.spawn),(0,3))
            self.assertEqual(got.campaign.chapter_flags,chapter)

    def test_equipment_roundtrip_duplicate_refs_stats_and_reward_rejection(self):
        s = self.fresh(3)
        for source, item in enumerate((1,2,9,10,17,18,33,34,49,50,65,81,82)):
            if source:
                self.assertEqual(self.lib.equipment_claim(C.byref(s.equipment), item, source, None), 0)
        s.equipment.equipped[:] = (3,7,9,10,12)
        claim_equipment_quests(s)
        self.store(s)
        self.assertEqual(compare_state(self.load()), compare_state(s))
        good = bytes(self.sram[A:A+SIZE])
        self.assertEqual(good[4544:4552], bytes((1,0,0,1,1,0,0,0)))
        self.assertEqual(good[4928:4933], bytes((3,7,9,10,12)))
        self.assertEqual(good[5024:5026], bytes((255,31)))
        mutations = [(4544,0), (4545,2), (4546,1), (4547,0), (4548,2), (4549,1),
                     (4552,1), (4555,1), (4556,0), (4928,48), (4928,255),
                     (4929,3), (4930,3), (4933,1), (4944,255), (5008,1),
                     (5025,63), (5032,1)]
        for offset, value in mutations:
            bad = bytearray(good); bad[offset] = value
            self.reset(); self.put(repair_crc(bad), A); self.invalid()
        broken = Save.from_buffer_copy(bytes(s))
        broken.equipment.bag[47] = broken.equipment.bag[1]
        self.assert_runtime_invalid(broken)
        broken = Save.from_buffer_copy(bytes(s))
        broken.equipment.equipped[1] = broken.equipment.equipped[0]
        self.assert_runtime_invalid(broken)

    def test_equipment_failed_save_retry_preserves_authoritative_bank(self):
        old = self.fresh(1); old.quests.region_flags[0] = 1; self.store(old)
        initial = bytes(self.sram)
        target = Save.from_buffer_copy(bytes(old))
        self.assertEqual(self.lib.equipment_claim(C.byref(target.equipment), 9, 2, None), 0)
        for cut in (0,1,4544,5000,SIZE):
            self.put(initial); self.lib.save5_test_fail_after(cut)
            self.assertEqual(self.lib.save5_store(C.byref(target)), 0)
            self.assertEqual(compare_state(self.load()), compare_state(old))
            self.assertEqual(bytes(self.sram[A:A+SIZE]), initial[A:A+SIZE])
            self.lib.save5_test_fail_after(-1)
            self.store(target)
            self.assertEqual(compare_state(self.load()), compare_state(target))


    def set_quest(self, s, qid, state, objectives, reward=False):
        self.assertEqual(self.lib.save5_quest_set_state(C.byref(s.quests), qid, state), 1)
        s.quests.objectives[qid] = objectives
        bit = 1 << (qid % 8)
        if reward: s.quests.rewards[qid // 8] |= bit
        else: s.quests.rewards[qid // 8] &= ~bit

    def regional(self, chapter=1):
        s = self.fresh(chapter)
        s.quests.region_flags[0] = 1
        return s

    def claim_quest(self, s, qid):
        contract = json.loads((ROOT / 'assets/region/contract.json').read_text())
        entry = contract['quests'][qid]
        for source in entry['equipment_sources']:
            self.assertEqual(self.lib.equipment_claim(C.byref(s.equipment),
                contract['equipment_source_items'][source], source, None), 0)
        if qid in (2,3):
            form = 13 if qid == 2 else 16
            if not self.lib.creatures_form(form): return False
            self.assertLess(self.lib.creatures_grant(C.byref(s.roster), form, 50, 100, 0,
                                                    entry['creature_reward_id']), 160)
        self.set_quest(s, qid, 3, QUEST_MASKS[qid], True)
        return True

    def test_retained_recruit_sanitizer_random_budgets_and_invalid_snapshots(self):
        source=Path(self.tmp.name)/'retained-sanitizer.c'
        exe=Path(self.tmp.name)/'retained-sanitizer'
        source.write_text(RETAINED_SANITIZER_MAIN)
        subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+[
            '-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',
            '-fsanitize=address,undefined','-fno-omit-frame-pointer',
            '-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-I'+str(ROOT/'src'),
            str(source),*[str(ROOT/'src'/name) for name in
                ('save4.c','save5.c','creatures.c','creature_data.c','equipment.c','equipment_data.c')],
            '-o',str(exe)],check=True)
        subprocess.run([str(exe)],env=dict(os.environ,
            ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'),check=True)

    def test_claimed_recruits_require_retained_owned_forms_not_only_history(self):
        s=self.regional(3)
        self.assertTrue(self.claim_quest(s,2));self.assertTrue(self.claim_quest(s,3))
        self.assertEqual(list(s.roster.party),[0,1,2,3])
        self.assertEqual([c.form_id for c in s.roster.instances[4:6]],[13,16])
        self.store(s)
        self.assertEqual(compare_state(self.load()),compare_state(s))
        for slot in (4,5):
            broken=Save.from_buffer_copy(bytes(s))
            C.memset(C.byref(broken.roster.instances[slot]),0,C.sizeof(Instance))
            self.assertEqual(self.lib.creatures_roster_validate(C.byref(broken.roster)),1)
            self.assertEqual(bytes(broken.roster.obtained),bytes(s.roster.obtained))
            self.assertEqual(bytes(broken.roster.rewards),bytes(s.roster.rewards))
            self.assert_runtime_invalid(broken)
        # Evolved Water in storage remains sufficient; neither phase label nor
        # STORY_LOCKED is substituted for its actual enabled form identity.
        self.assertEqual(self.lib.creatures_mark_trial(C.byref(s.roster.instances[4]),16),1)
        self.assertEqual(self.lib.creatures_evolve(C.byref(s.roster),4,8,1,1),0)
        self.assertEqual(s.roster.instances[4].form_id,14)
        self.store(s);self.assertEqual(compare_state(self.load()),compare_state(s))
        # Retention is at least one family member, independent of reward slot.
        water=self.lib.creatures_grant(C.byref(s.roster),13,10,20,0,0)
        metal=self.lib.creatures_grant(C.byref(s.roster),16,10,20,0,0)
        C.memset(C.byref(s.roster.instances[4]),0,C.sizeof(Instance))
        C.memset(C.byref(s.roster.instances[5]),0,C.sizeof(Instance))
        self.store(s);self.assertEqual(compare_state(self.load()),compare_state(s))
        for slot in (water,metal):
            broken=Save.from_buffer_copy(bytes(s))
            C.memset(C.byref(broken.roster.instances[slot]),0,C.sizeof(Instance))
            self.assert_runtime_invalid(broken)

    def test_missing_recruit_incremental_rejection_has_zero_writes_at_all_budgets(self):
        s=self.regional(3)
        self.assertTrue(self.claim_quest(s,2));self.assertTrue(self.claim_quest(s,3))
        self.store(s);baseline=bytes(self.sram)
        for slot,budget in itertools.product((4,5),(1,7,31,1024,3072,0xffffffff)):
            broken=Save.from_buffer_copy(bytes(s))
            C.memset(C.byref(broken.roster.instances[slot]),0,C.sizeof(Instance))
            self.assertEqual(self.lib.save5_validate(C.byref(broken)),0)
            self.put(baseline);self.lib.save5_test_reset_writer();self.lib.save5_test_fail_after(-1)
            before=bytes(broken)
            self.assertEqual(self.lib.save5_begin(C.byref(broken)),1)
            self.assertEqual(self.lib.save5_test_write_count(),0)
            for step in range(30000):
                status=self.lib.save5_step(budget)
                self.assertLessEqual(self.lib.save5_test_step_work(),min(budget,3072))
                self.assertEqual(self.lib.save5_test_write_count(),0)
                if status!=BUSY:break
            self.assertEqual(status,FAILED,(slot,budget,step))
            self.assertEqual(bytes(self.sram),baseline)
            self.assertEqual(bytes(broken),before)

    def test_crc_valid_missing_recruits_reject_or_fall_back_read_only(self):
        old=self.regional(3);self.store(old);old_bank=bytes(self.sram[A:A+SIZE])
        target=Save.from_buffer_copy(bytes(old))
        self.assertTrue(self.claim_quest(target,2));self.assertTrue(self.claim_quest(target,3))
        self.store(target);good=bytes(self.sram[B:B+SIZE])
        for slots in ((4,),(5,),(4,5)):
            malformed=bytearray(good)
            for slot in slots:malformed[160+24*slot:184+24*slot]=bytes(24)
            malformed=repair_crc(malformed)
            self.assertEqual(malformed,repair_crc(malformed))
            self.reset();self.put(malformed,B)
            self.invalid();self.assertEqual(self.lib.save5_test_write_count(),0)
            self.put(old_bank,A);before=bytes(self.sram)
            self.assertEqual(compare_state(self.load()),compare_state(old))
            self.assertEqual(bytes(self.sram),before)
            self.assertEqual(self.lib.save5_test_write_count(),0)
            # Writer must treat the malformed newest bank as invalid and keep
            # the valid predecessor intact while replacing that rejected bank.
            self.store(target)
            self.assertEqual(bytes(self.sram[A:A+SIZE]),old_bank)
            self.assertEqual(compare_state(self.load()),compare_state(target))

    def test_retention_is_claim_scoped_and_finds_final_storage_slot(self):
        s=self.regional(3)
        # Generic rewards retain their original meaning without regional claims.
        self.assertEqual(self.lib.creatures_grant(C.byref(s.roster),1,10,20,0,5),4)
        self.assertEqual(self.lib.creatures_grant(C.byref(s.roster),4,10,20,0,6),5)
        self.store(s);self.assertEqual(compare_state(self.load()),compare_state(s))
        self.reset();s=self.regional(3)
        for slot in range(4,159):
            self.assertEqual(self.lib.creatures_grant(C.byref(s.roster),1,10,20,0,0),slot)
        self.assertTrue(self.claim_quest(s,2))
        self.assertEqual(s.roster.instances[159].form_id,13)
        self.store(s);self.assertEqual(compare_state(self.load()),compare_state(s))
        C.memset(C.byref(s.roster.instances[159]),0,C.sizeof(Instance))
        self.assert_runtime_invalid(s)

    def test_creature_reward_every_interrupted_write_retains_prior_state(self):
        for qid in (2,3):
            self.reset();old=self.regional(3)
            if qid==3:self.assertTrue(self.claim_quest(old,2))
            self.set_quest(old,qid,2,QUEST_MASKS[qid]);self.store(old)
            initial=bytes(self.sram)
            target=Save.from_buffer_copy(bytes(old));self.assertTrue(self.claim_quest(target,qid))
            for cut in range(SIZE+2):
                self.put(initial);self.lib.save5_test_reset_writer();self.lib.save5_test_fail_after(cut)
                ok=self.lib.save5_store(C.byref(target))
                self.assertEqual(ok,int(cut>=SIZE+1),(qid,cut))
                self.assertEqual(compare_state(self.load()),compare_state(target if ok else old),(qid,cut))
                self.assertEqual(bytes(self.sram[:A]),initial[:A])
                self.assertEqual(bytes(self.sram[A:A+SIZE]),initial[A:A+SIZE])
            self.lib.save5_test_fail_after(-1)

    def test_authored_quest_shapes_ledgers_and_little_endian(self):
        contract = json.loads((ROOT/'assets/region/contract.json').read_text())
        self.assertEqual(tuple(q['objective_mask'] for q in contract['quests']), QUEST_MASKS)
        for qid, mask in enumerate(QUEST_MASKS):
            with self.subTest(quest=qid):
                s = self.regional()
                self.set_quest(s, qid, 1, 0)
                self.assertEqual(self.lib.save5_validate(C.byref(s)), 1)
                self.set_quest(s, qid, 1, mask)
                self.assert_runtime_invalid(s)
                self.set_quest(s, qid, 2, mask)
                self.store(s)
                bank = A if self.load().campaign.sequence % 2 else B
                wire = bytes(self.sram[bank:bank+SIZE])
                self.assertEqual(wire[4048+qid*2:4050+qid*2], mask.to_bytes(2,'little'))
                self.assertEqual(compare_state(self.load()), compare_state(s))
                self.set_quest(s, qid, 2, mask | 0x100)
                self.assert_runtime_invalid(s)
                self.set_quest(s, qid, 2, mask)
                claimed = self.claim_quest(s, qid)
                if claimed:
                    self.store(s)
                    self.assertEqual(compare_state(self.load()), compare_state(s))
                    broken = Save.from_buffer_copy(bytes(s))
                    broken.quests.rewards[qid//8] ^= 1 << (qid%8)
                    self.assert_runtime_invalid(broken)
                else:
                    self.set_quest(s, qid, 3, mask, True)
                    s.roster.rewards[0] |= 1 << (qid+2)
                    self.assert_runtime_invalid(s)
                self.reset()
        s = self.regional()
        before = bytes(s.quests)
        for qid, value in ((64,1),(0,4),(0,0xFFFFFFFF)):
            self.assertEqual(self.lib.save5_quest_set_state(C.byref(s.quests),qid,value),0)
            self.assertEqual(bytes(s.quests),before)
        for qid in range(11,64):
            broken = Save.from_buffer_copy(bytes(s)); self.set_quest(broken,qid,1,0)
            self.assert_runtime_invalid(broken)

    def test_quest_variables_anchors_reserved_and_source_consistency(self):
        s = self.regional()
        for qid in (3,9):
            s.quests.variables[qid] = 1
            self.assert_runtime_invalid(s)
            self.set_quest(s,qid,1,0)
            for value in range(4):
                s.quests.variables[qid] = value
                self.assertEqual(self.lib.save5_validate(C.byref(s)),1)
            s.quests.variables[qid] = 4; self.assert_runtime_invalid(s)
            s.quests.variables[qid] = 0
            self.set_quest(s,qid,2,QUEST_MASKS[qid])
            self.assertEqual(self.lib.save5_validate(C.byref(s)),1)
        for member,index,value in [('variables',0,1),('variables',63,1),
            ('region_flags',0,2),('region_flags',0,65),('region_flags',1,1),
            ('anchors',0,2),('anchors',0,4),('anchors',1,1)]:
            bad = Save.from_buffer_copy(bytes(s)); getattr(bad.quests,member)[index]=value
            self.assert_runtime_invalid(bad)
        for source in (1,3,5,6,7,8,9,10,11,12):
            bad = self.regional()
            item = json.loads((ROOT/'assets/region/contract.json').read_text())['equipment_source_items'][source]
            self.assertEqual(self.lib.equipment_claim(C.byref(bad.equipment),item,source,None),0)
            self.assert_runtime_invalid(bad)
        for source,item in ((2,9),(4,17)):
            bad = self.fresh(1)
            self.assertEqual(self.lib.equipment_claim(C.byref(bad.equipment),item,source,None),0)
            self.assert_runtime_invalid(bad)
            bad.quests.region_flags[0]=1
            self.assertEqual(self.lib.save5_validate(C.byref(bad)),1)
        for chapter,visit in ((0,0),(0,1),(1,0)):
            bad=self.fresh(chapter);bad.quests.region_flags[0]=visit
            self.set_quest(bad,0,1,0);self.assert_runtime_invalid(bad)

    def test_regional_checkpoint_room_spawn_visit_anchor_contract(self):
        contract = json.loads((ROOT/'assets/region/contract.json').read_text())
        for entry in contract['rooms']:
            room = entry['id']
            for spawn in range(6):
                s = self.regional(15)
                s.campaign.room=room;s.campaign.spawn=spawn
                s.quests.region_flags[0] |= 1 << (room-16)
                if entry.get('rest_anchor_bit') is not None:
                    s.quests.anchors[0] |= 1 << entry['rest_anchor_bit']
                claimable=True
                if entry['requires_quest_claimed'] is not None:
                    claimable=self.claim_quest(s,entry['requires_quest_claimed'])
                valid = str(spawn) in entry['spawns'] and claimable
                self.assertEqual(bool(self.lib.save5_validate(C.byref(s))),valid,(room,spawn))
                if valid:
                    self.store(s);got=self.load()
                    self.assertEqual((got.campaign.room,got.campaign.spawn),(room,spawn))
                    self.assertEqual(compare_state(got),compare_state(s))
                    bad=Save.from_buffer_copy(bytes(s));bad.quests.region_flags[0]&=~(1<<(room-16))
                    self.assert_runtime_invalid(bad)
                    if spawn==2 and room in (16,17):
                        bad=Save.from_buffer_copy(bytes(s));bad.quests.anchors[0]=0
                        self.assert_runtime_invalid(bad)
                else: self.assert_runtime_invalid(s)
                self.reset()
        for room in (14,15,22,23,24,127,255):
            s=self.regional(15);s.campaign.room=room;self.assert_runtime_invalid(s)
        s=self.regional(7);s.campaign.room=16;s.campaign.spawn=0
        self.store(s);self.assertEqual((self.load().campaign.room,self.load().campaign.spawn),(0,3))

    def test_quest_reward_every_interrupted_write_and_retry(self):
        old=self.regional();self.set_quest(old,1,2,3);self.store(old)
        initial=bytes(self.sram)
        target=Save.from_buffer_copy(bytes(old));self.assertTrue(self.claim_quest(target,1))
        for cut in range(SIZE+2):
            self.put(initial);self.lib.save5_test_reset_writer();self.lib.save5_test_fail_after(cut)
            ok=self.lib.save5_store(C.byref(target))
            self.assertEqual(ok,int(cut>=SIZE+1),cut)
            self.assertEqual(compare_state(self.load()),compare_state(target if ok else old),cut)
            self.assertEqual(bytes(self.sram[:A]),initial[:A])
            self.assertEqual(bytes(self.sram[A:A+SIZE]),initial[A:A+SIZE])
        self.put(initial);self.lib.save5_test_fail_after(SIZE)
        self.assertEqual(self.lib.save5_store(C.byref(target)),0)
        self.lib.save5_test_fail_after(-1);self.store(target)
        self.assertEqual(compare_state(self.load()),compare_state(target))
        self.assertEqual(self.lib.equipment_claim(C.byref(target.equipment),49,8,None),6)



RETAINED_SANITIZER_MAIN = r"""
#include "save5.h"
#include <assert.h>
#include <string.h>
static Save5State state, out, broken;
static unsigned rng=0xC0DE5052u;
static unsigned next(void) { rng^=rng<<13; rng^=rng>>17; rng^=rng<<5; return rng; }
static void finish(unsigned expected) {
    unsigned steps=0;
    while(save5_status()==SAVE5_BUSY) {
        unsigned budget=next()%4097u;
        save5_step(budget);
        assert(save5_test_step_work()<=(budget>3072?3072:budget));
        assert(++steps<1000);
    }
    assert(save5_status()==expected);
}
int main(void) {
    unsigned i,cycle;
    static const unsigned forms[8]={1,2,4,5,7,8,10,11};
    static const unsigned masks[11]={7,3,7,7,3,1,1,1,3,7,1};
    memset(save5_test_sram,255,sizeof save5_test_sram);
    state.campaign.chapter_flags=3;state.campaign.story_seen=10;
    assert(creatures_migrate_legacy(&state.roster,3,0));
    equipment_init(&state.equipment);
    assert(creatures_grant(&state.roster,13,50,100,0,5)==4);
    assert(creatures_grant(&state.roster,16,50,100,0,6)==5);
    for(i=6;i<160;++i)assert(creatures_grant(&state.roster,forms[i&7],50,100,0,0)==i);
    for(i=1;i<EQUIPMENT_AUTHORED_COUNT;++i)
        assert(equipment_claim(&state.equipment,equipment_authored_ids[i],i,0)==EQUIPMENT_OK);
    state.quests.region_flags[0]=1;
    for(i=0;i<11;++i) {
        assert(save5_quest_set_state(&state.quests,i,SAVE5_QUEST_CLAIMED));
        state.quests.objectives[i]=masks[i];state.quests.rewards[i>>3]|=1u<<(i&7);
    }
    for(cycle=0;cycle<1000;++cycle) {
        if(cycle==400) {
            assert(creatures_mark_trial(&state.roster.instances[4],CREATURE_TRIAL_PAIRED_POOLS));
            assert(creatures_evolve(&state.roster,4,CREATURE_REED_RESTORED,1,1)==CREATURE_EVOLVE_READY);
        }
        if(cycle%50==0) {
            const CreatureU8 party[4]={4,5,2,3};
            assert(creatures_party_set(&state.roster,party,0));
        } else if(cycle%50==25) {
            const CreatureU8 party[4]={0,1,2,3};
            assert(creatures_party_set(&state.roster,party,0));
        }
        state.roster.instances[cycle%160].cosmetic_seed=next();
        assert(save5_validate(&state));assert(save5_begin(&state));finish(SAVE5_DONE);
        assert(save5_load(&out));
        assert(!memcmp(&state.roster,&out.roster,sizeof state.roster));
        assert(!memcmp(&state.quests,&out.quests,sizeof state.quests));
        assert(!memcmp(&state.equipment,&out.equipment,sizeof state.equipment));
    }
    for(i=4;i<=5;++i) {
        unsigned writes=save5_test_write_count();
        broken=state;memset(&broken.roster.instances[i],0,sizeof(CreatureInstance));
        assert(creatures_roster_validate(&broken.roster));
        assert(!save5_validate(&broken));assert(save5_begin(&broken));finish(SAVE5_FAILED);
        assert(save5_test_write_count()==writes);
        assert(save5_load(&out));assert(!memcmp(&state.roster,&out.roster,sizeof state.roster));
    }
    return 0;
}
"""

ARM_TIMING_MAIN = r"""
#include "save5.h"
#ifndef BENCH_BUDGET
#define BENCH_BUDGET 1024
#endif
#define REG16(a) (*(volatile unsigned short *)(a))
static Save5State state;
volatile unsigned begin_cycles[18], step_cycles[18][256], step_counts[18], results[18], completed;
const char sram_id[] = "SRAM_V113";
static unsigned now(void) {
    unsigned hi, lo, hi2;
    do { hi=REG16(0x0400010C); lo=REG16(0x04000108); hi2=REG16(0x0400010C); } while(hi!=hi2);
    return (hi<<16)|lo;
}
static void bench(unsigned n) {
    unsigned t=now(), i=0;
    results[n]=(unsigned)save5_begin(&state); begin_cycles[n]=now()-t;
    while(save5_status()==SAVE5_BUSY && i<256) {
        t=now(); save5_step(BENCH_BUDGET); step_cycles[n][i++]=now()-t;
    }
    step_counts[n]=i; results[n]=save5_status();
}
int main(void) {
    unsigned i;
    const unsigned char forms[8]={1,2,4,5,7,8,10,11};
    REG16(0x04000208)=0; REG16(0x04000000)=0x80; REG16(0x04000204)=0x4317;
    REG16(0x0400010C)=0; REG16(0x0400010E)=0x84; REG16(0x04000108)=0; REG16(0x0400010A)=0x80;
    creatures_migrate_legacy(&state.roster,0,0);
    equipment_init(&state.equipment);
    bench(0); bench(1); bench(2);
    state.campaign.chapter_flags=3; state.campaign.story_seen=10;
    creatures_migrate_legacy(&state.roster,3,0);
    bench(3); bench(4); bench(5);
    for(i=4;i<160;++i) creatures_grant(&state.roster,forms[i&7],50,100,0,0);
    bench(6); bench(7); bench(8);
    creatures_migrate_legacy(&state.roster,3,0);
    for(i=4;i<160;++i) creatures_grant(&state.roster,11,50,100,0,0);
    bench(9); bench(10); bench(11);
    for(i=1;i<EQUIPMENT_AUTHORED_COUNT;++i)
        equipment_claim(&state.equipment,equipment_authored_ids[i],i,0);
    state.quests.region_flags[0]=1;
    {
        const unsigned char masks[11]={7,3,7,7,3,1,1,1,3,7,1};
        for(i=0;i<11;++i) if(i!=2&&i!=3) {
            save5_quest_set_state(&state.quests,i,SAVE5_QUEST_CLAIMED);
            state.quests.objectives[i]=masks[i];
            state.quests.rewards[i>>3]|=(unsigned char)(1u<<(i&7u));
        }
    }
    bench(12); bench(13); bench(14);
    creatures_migrate_legacy(&state.roster,3,0);
    creatures_grant(&state.roster,13,50,100,0,5);
    creatures_grant(&state.roster,16,50,100,0,6);
    for(i=6;i<160;++i) creatures_grant(&state.roster,forms[i&7],50,100,0,0);
    for(i=2;i<=3;++i) {
        save5_quest_set_state(&state.quests,i,SAVE5_QUEST_CLAIMED);
        state.quests.objectives[i]=7;state.quests.rewards[0]|=(1u<<i);
    }
    creatures_mark_trial(&state.roster.instances[4],CREATURE_TRIAL_PAIRED_POOLS);
    creatures_evolve(&state.roster,4,CREATURE_REED_RESTORED,1,1);
    bench(15); bench(16); bench(17);
    completed=1;
    while(1) { }
    return 0;
}
"""


def arm_timing():
    """Explicit optional real-ARM microbenchmark; separate from journey proof."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm-timing', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT/'build/save5-timing')
    parser.add_argument('--mgba-tools', type=Path, default=ROOT/'tools')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    tools = args.mgba_tools.resolve()
    if not (tools/'mgba_bridge.so').exists():
        raise SystemExit('Build the repository mGBA bridge or pass --mgba-tools to an existing verified bridge')
    sys.path.insert(0, str(tools))
    from mgba_runner import Emulator
    default = ROOT/'tools/sysroot/usr/bin/arm-none-eabi-'
    prefix = os.environ.get('ARM_PREFIX', str(default) if Path(str(default)+'gcc').exists() else 'arm-none-eabi-')
    cc = prefix+'gcc'
    flags = ['-I', str(ROOT/'src'), '-mcpu=arm7tdmi', '-mthumb-interwork', '-mthumb', '-O2',
             '-std=c99', '-ffreestanding', '-fno-builtin', '-fno-strict-aliasing',
             '-fomit-frame-pointer', '-Wall', '-Wextra', '-Werror', '-fstack-usage']
    main = out/'timing.c'
    main.write_text(ARM_TIMING_MAIN)
    sources = ['save4', 'save5', 'creatures', 'creature_data', 'equipment', 'equipment_data']
    for name in sources:
        subprocess.run([cc, *flags, '-c', str(ROOT/'src'/f'{name}.c'), '-o', str(out/f'{name}.o')], check=True)
    subprocess.run([cc, '-mcpu=arm7tdmi', '-mthumb-interwork', '-marm', '-x', 'assembler-with-cpp',
                    '-c', str(ROOT/'src/startup.s'), '-o', str(out/'startup.o')], check=True)
    report = {'purpose': 'Isolated save5 ARM7TDMI cycle microbenchmark; not controller journey or whole-frame proof',
              'waitcnt': '0x4317', 'timer_clock_hz': 16777216, 'frame_cycles': 280896,
              'source_sha256': {name: hashlib.sha256((ROOT/'src'/f'{name}.c').read_bytes()).hexdigest() for name in sources},
              'budgets': []}
    labels = ['two-creatures-empty', 'two-creatures-one-bank', 'two-creatures-two-banks',
              'four-creatures-after-two', 'four-creatures-mixed-banks', 'four-creatures-two-banks',
              'full-mixed-roster-after-four', 'full-mixed-roster-mixed-banks', 'full-mixed-roster-two-banks',
              'full-evolved-roster-after-mixed', 'full-evolved-roster-mixed-banks', 'full-evolved-roster-two-banks',
              'full-roster-all13-items-after-starter', 'full-roster-all13-items-mixed-banks',
              'full-roster-all13-items-two-banks',
              'full-retained-recruits-all11-quests-after-gear',
              'full-retained-recruits-all11-quests-mixed-banks',
              'full-retained-recruits-all11-quests-two-banks']
    for budget in (1024, 3072, 4096):
        subprocess.run([cc, *flags, f'-DBENCH_BUDGET={budget}', '-c', str(main), '-o', str(out/'main.o')], check=True)
        elf, rom = out/f'timing-{budget}.elf', out/f'timing-{budget}.gba'
        subprocess.run([cc, '-mcpu=arm7tdmi', '-mthumb-interwork', '-mthumb', '-nostdlib',
                        '-Wl,-T,'+str(ROOT/'linker.ld'), *[str(out/f'{name}.o') for name in ['startup','main']+sources],
                        '-lgcc', '-o', str(elf)], check=True)
        subprocess.run([prefix+'objcopy', '-O', 'binary', str(elf), str(rom)], check=True)
        subprocess.run([sys.executable, str(ROOT/'tools/fix_header.py'), str(rom)], check=True)
        nm = subprocess.check_output([prefix+'nm', '-n', str(elf)], text=True)
        (out/f'timing-{budget}.sym').write_text(nm)
        symbols = {x[2]: int(x[0],16) for line in nm.splitlines() if len(x:=line.split()) == 3}
        scenarios=[]
        with Emulator(rom) as e:
            for _ in range(100):
                e.frames(600)
                if e.read(symbols['completed']): break
            assert e.read(symbols['completed']) == 1, 'ARM timing harness did not finish'
            for index, label in enumerate(labels):
                count = e.read(symbols['step_counts']+index*4)
                values = [e.read(symbols['step_cycles']+index*1024+j*4) for j in range(count)]
                begin = e.read(symbols['begin_cycles']+index*4)
                status = e.read(symbols['results']+index*4)
                assert status == DONE and count < 256
                assert begin < 70000, (budget,label,'begin',begin)
                limit = 70000 if budget == 1024 else 230000
                assert max(values) < limit, (budget,label,'step',max(values))
                scenarios.append({'scenario':label, 'begin_cycles':begin, 'steps':count,
                                  'max_step_cycles':max(values), 'step_cycles':values, 'status':status})
        report['budgets'].append({'requested_budget':budget, 'effective_cap':3072,
                                  'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(), 'scenarios':scenarios})
        print('budget',budget,'max begin',max(x['begin_cycles'] for x in scenarios),
              'max step',max(x['max_step_cycles'] for x in scenarios),
              'four-creature steps',scenarios[5]['steps'],'full-roster steps',scenarios[-1]['steps'])
    report['save5_object_size'] = subprocess.check_output([prefix+'size', str(out/'save5.o')],text=True)
    report['save5_stack_usage'] = (out/'save5.su').read_text()
    (out/'save5-timing.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:', out/'save5-timing.json')


if __name__ == '__main__':
    if '--arm-timing' in sys.argv:
        arm_timing()
    else:
        unittest.main(verbosity=2)
