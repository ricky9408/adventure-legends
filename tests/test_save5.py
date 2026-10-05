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
ENABLED = (1, 2, 4, 5, 7, 8, 10, 11)


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


class Save(C.Structure):
    _fields_ = [('campaign', CampaignSave), ('roster', Roster),
                ('quest_reserved', C.c_ubyte * 264), ('equipment_reserved', C.c_ubyte * 512)]


def repair_crc(b):
    b = bytearray(b)
    b[16:20] = bytes(4)
    commit, b[20] = b[20], 0
    b[16:20] = binascii.crc32(b).to_bytes(4, 'little')
    b[20] = commit
    return b


def compare_state(s):
    return fields(s.campaign), bytes(s.roster), bytes(s.quest_reserved), bytes(s.equipment_reserved)


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
            *[str(ROOT / 'src' / name) for name in ('save4.c', 'save5.c', 'creatures.c', 'creature_data.c')],
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
        cls.lib.creatures_roster_init.argtypes = [C.POINTER(Roster)]
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
        for lo, hi in ((21,32), (47,96), (144,160), (4005,4008), (4012,4296), (4536,6144)):
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
        changes = [('quest_reserved', 1), ('equipment_reserved', 1)]
        for attr, value in changes:
            broken = Save.from_buffer_copy(bytes(s))
            getattr(broken, attr)[0] = value
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
        mutations = [(0, 0), (2, 6), (3, 31), (4, 1), (6, 0), (12, 2),
                     (14, 1), (21, 1), (32, 14), (34, 2), (46, 3), (47, 1),
                     (96, 255), (112, 0), (128, 0), (144, 1),
                     (160+1, 0x81), (160+2, 2), (160+3, 101), (160+8, 0),
                     (160+12, 1), (160+14, 2), (160+16, 255), (160+17, 255),
                     (160+18, 2), (160+19, 2),
                     (4000, 160), (4000, 2), (4001, 0), (4004, 4), (4004, 255),
                     (4005, 1), (4008, 0), (4012, 1), (4032, 1), (4296, 11),
                     (4298, 1), (4536, 1), (4544, 1), (5056, 1), (6143, 1)]
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


ARM_TIMING_MAIN = r"""
#include "save5.h"
#ifndef BENCH_BUDGET
#define BENCH_BUDGET 1024
#endif
#define REG16(a) (*(volatile unsigned short *)(a))
static Save5State state;
volatile unsigned begin_cycles[12], step_cycles[12][256], step_counts[12], results[12], completed;
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
    bench(0); bench(1); bench(2);
    state.campaign.chapter_flags=3; state.campaign.story_seen=10;
    creatures_migrate_legacy(&state.roster,3,0);
    bench(3); bench(4); bench(5);
    for(i=4;i<160;++i) creatures_grant(&state.roster,forms[i&7],50,100,0,0);
    bench(6); bench(7); bench(8);
    creatures_migrate_legacy(&state.roster,3,0);
    for(i=4;i<160;++i) creatures_grant(&state.roster,11,50,100,0,0);
    bench(9); bench(10); bench(11);
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
    sources = ['save4', 'save5', 'creatures', 'creature_data']
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
              'full-evolved-roster-after-mixed', 'full-evolved-roster-mixed-banks', 'full-evolved-roster-two-banks']
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
