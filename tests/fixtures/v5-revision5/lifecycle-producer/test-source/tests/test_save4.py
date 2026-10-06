#!/usr/bin/env python3
"""Format-4 HOST-SIMULATED SRAM tests; never launch or inject a game/emulator.

Run: python3 tests/test_save4.py
Requires a host C compiler, Python 3, and no third-party Python packages. The
shared library lives in a temporary directory. SAVE4_HOST_TEST backing SRAM and
fault injection do not exist in the cartridge build.

The authentic-fixture headers below were copied byte-for-byte from controller-
only milestone playthrough SRAM. Their complete 32 KiB file hashes are pinned.
When those sibling build artifacts are available, their full files are verified
and tested too; the byte-identical header regression cases are always run.
"""
import binascii
import ctypes as C
import hashlib
import itertools
import os
from pathlib import Path
import random
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BANK_A, BANK_B, SIZE = 0x40, 0x80, 32
GROVE, SKY, CORE, ENDING = 1, 2, 4, 8
SOUTH, NORTH, CAMP, ELDER, EAST, WEST = range(6)
SKY_BRIDGE, SKY_VANE, PATROL, RELAY_L, RELAY_R, RELAY_F = (1 << i for i in range(6))
CORE_PATH, WEIGHT_W, WEIGHT_E, WELL, ROOTS, THORNS = (1 << i for i in range(6, 12))
LAMPS = tuple(1 << i for i in range(12, 16))
SKY_PATH = SKY_BRIDGE | SKY_VANE
SKY_PATROL = SKY_PATH | PATROL
SKY_ALL = SKY_PATROL | RELAY_L | RELAY_R | RELAY_F
WEIGHTS = CORE_PATH | WEIGHT_W | WEIGHT_E
ROOT_PATH = WEIGHTS | WELL | ROOTS | THORNS
ALL_LAMPS = sum(LAMPS)
SEEN_LEGACY, SEEN_WIND, SEEN_SKY, SEEN_STONE, SEEN_CORE, SEEN_RELEASE, SEEN_CHIME = (1 << i for i in range(7))


class CampaignSave(C.Structure):
    _fields_ = [
        ('room', C.c_ubyte), ('spawn', C.c_ubyte), ('chapter_flags', C.c_ubyte),
        ('bridge', C.c_ubyte), ('torches', C.c_ubyte), ('relic', C.c_ubyte),
        ('camp', C.c_ubyte), ('room_flags', C.c_uint), ('optional_flags', C.c_ubyte),
        ('story_seen', C.c_ushort), ('spirit', C.c_ubyte),
        ('sequence', C.c_uint), ('loaded_version', C.c_ubyte),
    ]


def state(**kwargs):
    s = CampaignSave()
    for key, val in kwargs.items():
        setattr(s, key, val)
    return s


def copy_state(s):
    return CampaignSave.from_buffer_copy(bytes(s))


def fields(s, metadata=False):
    return tuple(getattr(s, k) for k, _ in CampaignSave._fields_
                 if metadata or k not in ('sequence', 'loaded_version'))


def crc(data):
    return binascii.crc_hqx(data, 0xffff)


def record(s, sequence=1):
    b = bytearray(32)
    b[:5] = b'EB\x04\x20\xa5'
    b[5:9] = sequence.to_bytes(4, 'little')
    b[9:16] = bytes([s.room, s.spawn, s.chapter_flags, s.bridge,
                     s.torches, s.relic, s.camp])
    b[16:20] = s.room_flags.to_bytes(4, 'little')
    b[20] = s.optional_flags
    b[21:23] = s.story_seen.to_bytes(2, 'little')
    b[23] = s.spirit
    return repair_crc(b)


def repair_crc(b):
    b = bytearray(b)
    b[30:32] = crc(b[:30]).to_bytes(2, 'little')
    return b


def legacy(version, room=0, bridge=0, torches=0, completed=0, quest=1, relic=0, camp=0):
    b = bytearray(b'\xff' * 13)
    b[:8] = bytes([0x45, 0x42, version, room, bridge, torches, completed, quest])
    if version == 2:
        b[8] = sum(b[:8]) & 255
    else:
        b[8:12] = bytes([relic, camp, 8 if relic else 6, 0])
        b[12] = (0x3d + sum(b[:12])) & 255
    return b


def repair_legacy(b):
    b = bytearray(b)
    if b[2] == 2:
        b[8] = sum(b[:8]) & 255
    else:
        b[12] = (0x3d + sum(b[:12])) & 255
    return b


AUTHENTIC_FIXTURES = [
    ('baseline-v2-bridge.sav', '45420201010000018cffffffff',
     'b4d25b2475fdd3b597b4829972422f621bedb7b05e481926f00c4da3ca155d68', True),
    ('v2-completed/checkpoint.sav', '454202030103010192ffffffff',
     '335785eab2716aa28440d92b0c28a6063c046049836ce7a5893e5c8b2641e09f', True),
    ('full-journey/checkpoint.sav', '454203030103010100000600d6',
     'cd08082f4f8f5761b3a7d7a3f9623f06135be503fa4a80020093d4ad397a92f2', True),
    ('migrated-v3.sav', '454203010100000100000600d0',
     'd12f787508277a7289668055c929f674f5991b6e9b1950041f7dc69d9a1ff8ed', True),
    ('relic-camp-checkpoint.sav', '454203010100000101010800d4',
     '0d8833ed2b0b38eab32158cd597211b9770796d03a07e4665d6330d9cda8cf14', True),
    ('explicit-corrupt-copy.sav', '454203010000000100000600d0',
     '53c93b9141641e1fd092dccf4144f32418f11332dbfa65e34973b071358533e2', False),
    ('invalid-inconsistent-maximum-health.sav', '454203010100000100000800d2',
     '9085bdd69e3061191e13459e8389e7eb2a69672f472712c0bc0db60bdc42f503', False),
    ('invalid-invalid-camp-flag.sav', '454203010100000100020600d2',
     'beafec5bf5fbb69196da5f05bad1be6be71593749849ac6e4e07b34e0f4aeabd', False),
    ('invalid-out-of-range-room.sav', '454203040100000100000600d3',
     'd5c34101722b283fa0851511f9b65e77397ef165c358c5eb49f7845b88bd296c', False),
    ('invalid-unknown-reserved-flag.sav', '454203010100000100000601d1',
     '5c20534505204efe0f495e59a5f63d9e3a1edbe862234e1d3e30cce6c0cd4877', False),
]


class Save4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='emberbond-save4-host-')
        cls.addClassCleanup(cls.tmp.cleanup)
        so = Path(cls.tmp.name) / 'save4.so'
        compiler = shlex.split(os.environ.get('HOST_CC', 'cc'))
        subprocess.run(compiler + [
            '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-ffreestanding',
            '-fno-builtin', '-DSAVE4_HOST_TEST', '-shared', '-fPIC',
            str(ROOT / 'src/save4.c'), '-o', str(so),
        ], check=True)
        cls.lib = C.CDLL(str(so))
        cls.sram = (C.c_ubyte * 256).in_dll(cls.lib, 'save4_test_sram')
        cls.lib.save4_load.argtypes = [C.POINTER(CampaignSave)]
        cls.lib.save4_load.restype = C.c_int
        cls.lib.save4_store.argtypes = [C.POINTER(CampaignSave)]
        cls.lib.save4_store.restype = C.c_int
        cls.lib.save4_has_valid.restype = C.c_int
        cls.lib.save4_crc16.argtypes = [C.POINTER(C.c_ubyte), C.c_uint]
        cls.lib.save4_crc16.restype = C.c_ushort
        cls.lib.save4_max_hp.argtypes = [C.POINTER(CampaignSave)]
        cls.lib.save4_max_hp.restype = C.c_uint
        cls.lib.save4_unlock_mask.argtypes = [C.c_uint]
        cls.lib.save4_unlock_mask.restype = C.c_uint
        cls.lib.save4_test_fail_after.argtypes = [C.c_int]
        cls.lib.save4_test_write_count.restype = C.c_uint
        cls.lib.save4_test_corrupt_write.argtypes = [C.c_int, C.c_ubyte]

    def setUp(self):
        self.reset()

    def reset(self, byte=255):
        self.sram[:] = bytes([byte]) * 256
        self.lib.save4_test_fail_after(-1)
        self.lib.save4_test_corrupt_write(-1, 0)

    def put(self, data, offset=0):
        self.sram[offset:offset + len(data)] = data

    def load(self):
        s = state()
        self.assertEqual(self.lib.save4_load(C.byref(s)), 1)
        return s

    def store(self, s):
        before = bytes(s)
        self.assertEqual(self.lib.save4_store(C.byref(s)), 1)
        self.assertEqual(bytes(s), before, 'store mutated caller or metadata')

    def assert_invalid(self):
        snapshot = bytes(self.sram)
        sentinel = CampaignSave.from_buffer_copy(bytes([0xcc]) * C.sizeof(CampaignSave))
        original = bytes(sentinel)
        self.assertEqual(self.lib.save4_load(C.byref(sentinel)), 0)
        self.assertEqual(bytes(sentinel), original, 'failed load changed output')
        self.assertEqual(self.lib.save4_has_valid(), 0)
        self.assertEqual(bytes(self.sram), snapshot, 'read-only API mutated SRAM')

    def assert_round_trip(self, s):
        self.store(s)
        loaded = self.load()
        expected = copy_state(s)
        if (s.chapter_flags & CORE or
                (s.chapter_flags & SKY and not s.story_seen & SEEN_STONE) or
                (s.chapter_flags & GROVE and not s.story_seen & SEEN_WIND)):
            expected.room, expected.spawn = 0, ELDER
        self.assertEqual(fields(loaded), fields(expected))
        self.assertEqual(loaded.loaded_version, 4)
        return loaded

    def test_crc_vector_and_independent_random_oracle(self):
        rng = random.Random(4204)
        for value in [b'', b'123456789'] + [rng.randbytes(n) for n in range(1, 256)]:
            array = (C.c_ubyte * len(value)).from_buffer_copy(value)
            self.assertEqual(self.lib.save4_crc16(array, len(value)), crc(value))
        self.assertEqual(crc(b'123456789'), 0x29b1)

    def test_derived_health_and_companion_unlocks(self):
        for chapter, mask in [(0, 3), (1, 7), (3, 15), (7, 15), (15, 15)]:
            self.assertEqual(self.lib.save4_unlock_mask(chapter), mask)
        for relic, hp in [(0, 6), (1, 8)]:
            self.assertEqual(self.lib.save4_max_hp(C.byref(state(relic=relic))), hp)

    def test_no_valid_save_is_read_only_and_null_is_safe(self):
        for byte in (0, 255, 0xcc):
            self.reset(byte)
            self.assert_invalid()
        self.assertEqual(self.lib.save4_load(None), 0)
        self.assertEqual(self.lib.save4_store(None), 0)
        self.assertEqual(self.lib.save4_test_write_count(), 0)

    def test_every_exact_legacy_payload_combination_and_two_saves(self):
        # 128 v2 + 512 v3 valid combinations, including quest=0 and odd-looking
        # but valid old completion/puzzle combinations. Never revoke a clear.
        count = 0
        for version in (2, 3):
            optional = [(0, 0)] if version == 2 else itertools.product(range(2), repeat=2)
            for relic, camp in optional:
                for room, bridge, torches, done, quest in itertools.product(
                        range(4), range(2), range(4), range(2), range(2)):
                    with self.subTest(version=version, room=room, bridge=bridge,
                                      torches=torches, done=done, quest=quest,
                                      relic=relic, camp=camp):
                        self.reset()
                        old = legacy(version, room, bridge, torches, done, quest, relic, camp)
                        self.put(old)
                        before = bytes(self.sram)
                        s = self.load()
                        self.assertEqual(self.lib.save4_has_valid(), 1)
                        self.assertEqual(bytes(self.sram), before)
                        self.assertEqual((s.loaded_version, s.sequence), (version, 0))
                        self.assertEqual((s.bridge, s.torches, s.relic, s.camp),
                                         (bridge, torches, relic, camp))
                        self.assertEqual(s.chapter_flags, GROVE if done else 0)
                        self.assertEqual((s.room_flags, s.optional_flags, s.story_seen), (0, 0, 0))
                        self.assertEqual((s.room, s.spawn), (0, ELDER) if done else
                                         (room, CAMP if room == 1 and camp else SOUTH))
                        first = self.assert_round_trip(s)
                        self.assertEqual(first.sequence, 1)
                        second = self.assert_round_trip(first)
                        self.assertEqual(second.sequence, 2)
                        self.assertEqual(bytes(self.sram[:13]), old)
                        self.assertEqual(fields(second), fields(s))
                        count += 1
        self.assertEqual(count, 640)

    def test_legacy_named_regression_scenarios(self):
        for version, room, bridge, torches, done, relic, camp in [
            (2, 0, 0, 0, 0, 0, 0), (2, 1, 1, 0, 0, 0, 0),
            (2, 2, 1, 1, 0, 0, 0), (2, 3, 1, 3, 0, 0, 0),
            (2, 3, 1, 3, 1, 0, 0), (3, 3, 1, 3, 1, 1, 1),
            (3, 3, 1, 3, 1, 0, 0),
        ]:
            with self.subTest(version=version, room=room, torches=torches, done=done):
                self.reset()
                self.put(legacy(version, room, bridge, torches, done, 1, relic, camp))
                s = self.load()
                self.assertEqual(s.chapter_flags, done)
                self.assertEqual(s.relic, relic)
                self.assertEqual(s.camp, camp)
                if done:
                    self.assertEqual((s.room, s.spawn), (0, ELDER))
                    self.assertEqual(self.lib.save4_unlock_mask(s.chapter_flags), 7)

    def test_legacy_corruption_and_exact_field_validation(self):
        for version in (2, 3):
            base = legacy(version, room=1, bridge=1)
            mutations = [(0, 0), (1, 0), (2, 1), (2, 4), (3, 4), (4, 2),
                         (5, 4), (6, 2), (7, 2)]
            if version == 3:
                mutations += [(8, 2), (9, 2), (10, 8), (10, 7), (11, 1)]
            for index, value in mutations:
                with self.subTest(version=version, index=index, value=value):
                    self.reset()
                    b = bytearray(base)
                    b[index] = value
                    self.put(repair_legacy(b))
                    self.assert_invalid()
            for index in range(9 if version == 2 else 13):
                self.reset()
                b = bytearray(base)
                b[index] ^= 1
                self.put(b)
                self.assert_invalid()

    def test_authentic_published_save_headers(self):
        for name, header, _, valid in AUTHENTIC_FIXTURES:
            with self.subTest(fixture=name):
                self.reset()
                old = bytes.fromhex(header)
                self.put(old)
                if valid:
                    migrated = self.load()
                    self.assert_round_trip(migrated)
                    self.assert_round_trip(self.load())
                    self.assertEqual(bytes(self.sram[:13]), old)
                    if 'checkpoint.sav' in name and 'relic' not in name:
                        self.assertEqual(migrated.chapter_flags, GROVE)
                        self.assertEqual((migrated.room, migrated.spawn), (0, ELDER))
                else:
                    self.assert_invalid()

    def test_authentic_full_fixture_hashes_when_available(self):
        base = ROOT.parent / 'adventure-legends-next/build/exploration'
        if not base.exists():
            self.skipTest('full original build artifacts absent; exact embedded headers tested above')
        for name, header, digest, valid in AUTHENTIC_FIXTURES:
            with self.subTest(fixture=name):
                data = (base / name).read_bytes()
                self.assertEqual(len(data), 32768)
                self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
                self.assertEqual(data[:13], bytes.fromhex(header))
                self.reset()
                self.put(data[:256])
                if valid:
                    self.assert_round_trip(self.load())
                else:
                    self.assert_invalid()

    def test_serialization_byte_order_reserved_zero_and_metadata_ignored(self):
        s = state(room=12, spawn=NORTH, chapter_flags=3, bridge=1, torches=3,
                  relic=1, camp=1, room_flags=0xffff, optional_flags=1,
                  story_seen=SEEN_WIND | SEEN_STONE | SEEN_CHIME, spirit=3,
                  sequence=0xffffffff, loaded_version=99)
        self.store(s)
        self.assertEqual(bytes(self.sram[BANK_A:BANK_A+32]), record(s, 1))
        self.assertEqual(bytes(self.sram[:13]), b'\xff' * 13)
        self.assertEqual(bytes(self.sram[BANK_A+24:BANK_A+30]), b'\0' * 6)
        self.assertEqual(self.load().sequence, 1)

    def test_partial_relay_all_activation_orders(self):
        for order in itertools.permutations((RELAY_L, RELAY_R, RELAY_F)):
            self.reset()
            s = state(room=7, chapter_flags=1, room_flags=SKY_PATROL, story_seen=SEEN_WIND, spirit=2)
            self.assert_round_trip(s)
            for bit in order:
                s.room_flags |= bit
                self.assert_round_trip(s)
            s.room, s.spawn = 8, SOUTH
            self.assert_round_trip(s)

    def test_partial_weights_well_and_thorns_before_roots(self):
        for order in itertools.permutations((WEIGHT_W, WEIGHT_E)):
            self.reset()
            s = state(room=10, chapter_flags=3, room_flags=SKY_ALL | CORE_PATH,
                      story_seen=SEEN_WIND | SEEN_STONE, spirit=3)
            self.assert_round_trip(s)
            for bit in order:
                s.room_flags |= bit
                self.assert_round_trip(s)
            s.room = 11
            self.assert_round_trip(s)
            for bit in (THORNS, WELL, ROOTS):
                s.room_flags |= bit
                self.assert_round_trip(s)
        # The uncapped-well-without-roots state also exists without burned thorns.
        s.room_flags = SKY_ALL | WEIGHTS | WELL
        self.assert_round_trip(s)

    def test_final_lamps_all_24_activation_orders_and_boss_entry(self):
        for order in itertools.permutations(LAMPS):
            self.reset()
            s = state(room=12, chapter_flags=3, room_flags=SKY_ALL | ROOT_PATH,
                      story_seen=SEEN_WIND | SEEN_STONE, spirit=3)
            self.assert_round_trip(s)
            for bit in order:
                s.room_flags |= bit
                self.assert_round_trip(s)
            s.room = 13
            self.assert_round_trip(s)

    def test_clear_before_dialogue_and_ending_normalize_to_village(self):
        for s in [
            state(room=3, chapter_flags=GROVE),
            state(room=8, chapter_flags=GROVE | SKY, room_flags=SKY_ALL, story_seen=SEEN_WIND, spirit=3),
            state(room=13, chapter_flags=7, room_flags=0xffff, story_seen=SEEN_WIND | SEEN_STONE),
            state(room=13, chapter_flags=15, room_flags=0xffff, story_seen=0x7f, optional_flags=1),
            state(room=0, chapter_flags=15, room_flags=0xffff, story_seen=0x7f, optional_flags=1),
        ]:
            self.reset()
            loaded = self.assert_round_trip(s)
            self.assertEqual((loaded.room, loaded.spawn), (0, ELDER))
            self.assertEqual(loaded.chapter_flags, s.chapter_flags)
        # Ordinary cleared boss visits remain safe after the join is seen.
        for s in [state(room=3, chapter_flags=1, story_seen=SEEN_WIND),
                  state(room=8, chapter_flags=3, room_flags=SKY_ALL,
                        story_seen=SEEN_WIND | SEEN_STONE)]:
            self.reset()
            self.assertEqual(self.assert_round_trip(s).room, s.room)

    def test_invalid_records_even_with_recomputed_crc(self):
        valid = state(room=0, chapter_flags=3, room_flags=0xffff,
                      story_seen=SEEN_WIND | SEEN_STONE, optional_flags=1, spirit=3)
        mutations = [(0, 0), (1, 0), (2, 3), (3, 31), (3, 33), (4, 0),
                     (9, 14), (10, 6), (11, 0x10), (12, 2), (13, 4),
                     (14, 2), (15, 2), (18, 1), (19, 1), (20, 2),
                     (21, 0x80), (22, 1), (23, 4)]
        mutations += [(i, 1) for i in range(24, 30)]
        for index, value in mutations:
            with self.subTest(index=index, value=value):
                self.reset()
                b = record(valid)
                b[index] = value
                self.put(repair_crc(b), BANK_A)
                self.assert_invalid()

    def test_invalid_semantic_states_cannot_load_or_write(self):
        cases = []
        cases += [state(chapter_flags=v) for v in range(256) if v not in (0, 1, 3, 7, 15)]
        cases += [state(spirit=2), state(chapter_flags=1, spirit=3)]
        cases += [state(room=0, spawn=x) for x in (NORTH, CAMP)]
        cases += [state(room=1, spawn=CAMP), state(room=1, spawn=NORTH)]
        cases += [state(room=1, spawn=x, camp=1) for x in (ELDER, EAST, WEST)]
        cases += [state(room=2, spawn=NORTH, torches=t) for t in range(3)]
        cases += [state(room=2, spawn=CAMP, camp=1), state(room=3, spawn=ELDER)]
        cases += [state(room=0, spawn=EAST), state(room=0, spawn=WEST, chapter_flags=1)]
        cases += [state(room=r) for r in range(4, 14)]
        cases += [state(room=r, chapter_flags=1, story_seen=SEEN_WIND) for r in range(9, 14)]
        cases += [state(room_flags=SKY_BRIDGE), state(chapter_flags=1, room_flags=CORE_PATH)]
        cases += [state(optional_flags=1), state(story_seen=SEEN_LEGACY),
                  state(story_seen=SEEN_WIND), state(story_seen=SEEN_SKY),
                  state(chapter_flags=1, story_seen=SEEN_STONE),
                  state(chapter_flags=1, story_seen=SEEN_CORE),
                  state(chapter_flags=3, story_seen=SEEN_RELEASE),
                  state(chapter_flags=3, story_seen=SEEN_CHIME)]
        cases += [state(chapter_flags=3, story_seen=SEEN_WIND | SEEN_STONE, room_flags=f)
                  for f in (SKY_VANE, PATROL, RELAY_L, RELAY_R, RELAY_F,
                            WEIGHT_W, WEIGHT_E, WELL, ROOTS, THORNS, *LAMPS,
                            WEIGHTS | ROOTS)]
        for i, s in enumerate(cases):
            with self.subTest(case=i, data=fields(s)):
                self.reset()
                self.put(record(s), BANK_A)
                self.assert_invalid()
                before = bytes(self.sram)
                self.assertEqual(self.lib.save4_store(C.byref(s)), 0)
                self.assertEqual(bytes(self.sram), before)
                self.assertEqual(self.lib.save4_test_write_count(), 0)

    def test_room_and_north_spawn_access_requirements(self):
        entry = {4: 0, 5: 0, 6: SKY_PATH, 7: SKY_PATROL, 8: SKY_ALL,
                 9: 0, 10: CORE_PATH, 11: WEIGHTS, 12: ROOT_PATH, 13: ROOT_PATH | ALL_LAMPS}
        north = {5: SKY_PATH, 6: SKY_PATROL, 7: SKY_ALL, 9: CORE_PATH,
                 10: WEIGHTS, 11: ROOT_PATH, 12: ROOT_PATH | ALL_LAMPS}
        for room in range(4, 14):
            for spawn in (SOUTH, NORTH):
                required = entry[room] | (north.get(room, 0) if spawn == NORTH else 0)
                s = state(room=room, spawn=spawn, chapter_flags=3,
                          room_flags=required, story_seen=SEEN_WIND | SEEN_STONE)
                self.reset()
                self.assert_round_trip(s)
                for bit in [1 << b for b in range(16) if required & (1 << b)]:
                    with self.subTest(room=room, spawn=spawn, missing=bit):
                        self.reset()
                        s.room_flags = required & ~bit
                        self.put(record(s), BANK_A)
                        self.assert_invalid()

    def test_every_single_bit_corruption_falls_back(self):
        older = state(room=1, relic=1, camp=1, bridge=1)
        newer = state(room=7, chapter_flags=1, room_flags=SKY_ALL,
                      story_seen=SEEN_WIND, spirit=2)
        self.put(record(older, 8), BANK_A)
        self.put(record(newer, 9), BANK_B)
        initial = bytes(self.sram)
        for bit in range(SIZE * 8):
            with self.subTest(bit=bit):
                self.put(initial)
                self.sram[BANK_B + bit // 8] ^= 1 << (bit % 8)
                before = bytes(self.sram)
                s = self.load()
                self.assertEqual(fields(s), fields(older))
                self.assertEqual(s.sequence, 8)
                self.assertEqual(bytes(self.sram), before)
        # A lone corrupt bank gives no valid continue, not a synthetic new game.
        for bit in range(SIZE * 8):
            self.reset()
            self.put(record(newer, 9), BANK_A)
            self.sram[BANK_A + bit // 8] ^= 1 << (bit % 8)
            self.assert_invalid()

    def test_invalid_newer_semantic_bank_does_not_win(self):
        old = state(room=1, relic=1, camp=1)
        bad = state(room=13, chapter_flags=3, story_seen=SEEN_WIND | SEEN_STONE)
        self.put(record(old, 1), BANK_A)
        self.put(record(bad, 1000), BANK_B)
        self.assertEqual(fields(self.load()), fields(old))
        self.assert_round_trip(old)
        self.assertEqual(self.load().sequence, 2)

    def test_bad_v4_falls_back_to_full_legacy_without_writes(self):
        self.put(legacy(3, 3, 1, 3, 1, 0, 1, 1))
        self.put(record(state(), 100), BANK_A)
        self.sram[BANK_A + 31] ^= 1
        before = bytes(self.sram)
        s = self.load()
        self.assertEqual((s.loaded_version, s.chapter_flags, s.relic, s.camp), (3, 1, 1, 1))
        self.assertEqual(bytes(self.sram), before)

    def test_valid_v4_beats_legacy_even_with_less_progress(self):
        self.put(legacy(3, 3, 1, 3, 1, 1, 1, 1))
        self.put(record(state(), 0), BANK_B)
        s = self.load()
        self.assertEqual((s.loaded_version, s.sequence, s.chapter_flags, s.relic), (4, 0, 0, 0))

    def test_sequence_wrap_ties_and_ambiguous_half_range(self):
        a, b = state(relic=1), state(camp=1)
        for sa, sb, winner in [(1, 2, b), (2, 1, a), (77, 77, a),
                               (0xffffffff, 0, b), (0, 0xffffffff, a),
                               (0, 0x7fffffff, b), (0, 0x80000000, a),
                               (0x80000000, 0, a)]:
            with self.subTest(a=sa, b=sb):
                self.reset()
                self.put(record(a, sa), BANK_A)
                self.put(record(b, sb), BANK_B)
                self.assertEqual(fields(self.load()), fields(winner))
        self.reset()
        self.put(record(a, 0xfffffffe), BANK_A)
        self.put(record(b, 0xffffffff), BANK_B)
        self.store(a)
        self.assertEqual(self.load().sequence, 0)
        self.assertEqual(fields(self.load()), fields(a))
        self.store(b)
        self.assertEqual(self.load().sequence, 1)

    def interruption_case(self, initial, old, new):
        # Exactly 33 writes: invalidate, 31 remaining bytes, commit last.
        for prefix in range(34):
            with self.subTest(prefix=prefix):
                self.reset()
                self.put(initial)
                self.lib.save4_test_fail_after(prefix)
                result = self.lib.save4_store(C.byref(new))
                self.assertEqual(result, int(prefix == 33))
                self.assertEqual(self.lib.save4_test_write_count(), min(prefix, 33))
                if prefix == 33:
                    got = self.load()
                    self.assertEqual(fields(got), fields(new))
                elif old is not None:
                    self.assertEqual(fields(self.load()), fields(old))
                else:
                    self.assert_invalid()
                self.assertEqual(bytes(self.sram[:13]), initial[:13])
                # Both gaps and unrelated simulated SRAM must remain unchanged.
                self.assertEqual(bytes(self.sram[13:BANK_A]), initial[13:BANK_A])
                self.assertEqual(bytes(self.sram[BANK_A+32:BANK_B]), initial[BANK_A+32:BANK_B])
                self.assertEqual(bytes(self.sram[BANK_B+32:]), initial[BANK_B+32:])

    def test_every_interruption_prefix_first_save_and_legacy_migration(self):
        new = state(room=1, bridge=1, relic=1, camp=1)
        self.interruption_case(bytes(self.sram), None, new)
        self.reset()
        self.put(legacy(3, 3, 1, 3, 1, 1, 1, 1))
        old = self.load()
        self.interruption_case(bytes(self.sram), old, old)

    def test_every_interruption_prefix_with_one_or_two_valid_banks(self):
        old = state(room=1, bridge=1, relic=1, camp=1)
        new = state(room=7, chapter_flags=1, room_flags=SKY_ALL, story_seen=SEEN_WIND, spirit=2)
        for first, second in [(BANK_A, None), (BANK_B, None), (BANK_A, BANK_B), (BANK_B, BANK_A)]:
            with self.subTest(active=first, older=second):
                self.reset()
                if second is not None:
                    self.put(record(state(), 4), second)
                self.put(record(old, 5), first)
                initial = bytes(self.sram)
                self.interruption_case(initial, old, new)
                self.assertEqual(bytes(self.sram[first:first+32]), initial[first:first+32])

    def test_every_interruption_prefix_on_deliberate_new_game(self):
        old = state(room=0, spawn=ELDER, chapter_flags=15, room_flags=0xffff,
                    bridge=1, torches=3, relic=1, camp=1, optional_flags=1, story_seen=0x7f, spirit=3)
        self.put(legacy(3, 3, 1, 3, 1, 1, 1, 1))
        self.put(record(old, 50), BANK_A)
        self.put(record(old, 49), BANK_B)
        initial = bytes(self.sram)
        self.interruption_case(initial, old, state())
        self.lib.save4_test_fail_after(-1)
        self.assertEqual((self.load().sequence, self.load().chapter_flags), (51, 0))
        self.store(self.load())
        self.assertEqual((self.load().sequence, self.load().chapter_flags), (52, 0))
        # Both banks now contain new-game state. A subsequent one-bank loss
        # cannot revive the intentionally replaced previous campaign.
        self.sram[BANK_A + 30] ^= 1
        self.assertEqual(self.load().chapter_flags, 0)

    def test_each_write_readback_fault_preserves_active_bank(self):
        old, new = state(room=1, camp=1), state(room=2, relic=1, bridge=1)
        for index in range(33):
            with self.subTest(write=index):
                self.reset()
                self.put(record(old, 7), BANK_A)
                self.put(record(state(), 6), BANK_B)
                before = bytes(self.sram[BANK_A:BANK_A+32])
                self.lib.save4_test_corrupt_write(index, 1)
                self.assertEqual(self.lib.save4_store(C.byref(new)), 0)
                self.assertEqual(fields(self.load()), fields(old))
                self.assertEqual(bytes(self.sram[BANK_A:BANK_A+32]), before)

    def test_arm_object_has_no_runtime_dependencies_or_test_hooks(self):
        prefix = ROOT / 'tools/sysroot/usr/bin/arm-none-eabi-'
        cc = str(prefix) + 'gcc'
        nm = str(prefix) + 'nm'
        if not Path(cc).exists():
            cc = shutil.which('arm-none-eabi-gcc')
            nm = shutil.which('arm-none-eabi-nm')
        if not cc or not nm:
            self.skipTest('ARM cross-compiler unavailable; host checks still run')
        obj = Path(self.tmp.name) / 'save4-arm.o'
        subprocess.run([cc, '-std=c99', '-mcpu=arm7tdmi', '-mthumb-interwork', '-mthumb',
                        '-O2', '-ffreestanding', '-fno-builtin', '-Wall', '-Wextra', '-Werror',
                        '-c', str(ROOT / 'src/save4.c'), '-o', str(obj)], check=True)
        undefined = subprocess.check_output([nm, '-u', str(obj)], text=True).strip()
        self.assertEqual(undefined, '', 'save module needs runtime/library symbols')
        symbols = subprocess.check_output([nm, str(obj)], text=True)
        self.assertNotIn('save4_test_', symbols, 'host injection leaked into cartridge code')


if __name__ == '__main__':
    print('HOST-SIMULATED SRAM TESTS: no emulator or real-game RAM injection', flush=True)
    unittest.main(verbosity=2)
