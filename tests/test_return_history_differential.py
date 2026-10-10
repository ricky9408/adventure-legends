#!/usr/bin/env python3
"""Exact delivered Underwater oracle versus Return for content revisions 1..6.

The independent oracle is a SHA-pinned source-only archive, not a sibling checkout.
Each implementation compiles a private source closure with no shared include path.
Adversarial banks have independently recomputed CRC32. These host tests are codec
and policy evidence, never evidence of controller-earned Return acquisitions.
"""
import collections
import ctypes as C
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import random
import re
import shlex
import subprocess
import tarfile
import tempfile
import unittest

from test_save5 import ROOT, Save, A, B, SIZE, repair_crc, compare_state
from test_save5_history_differential import HARNESS, FIXTURES as EARLY_FIXTURES

ORACLE = ROOT / 'tests/fixtures/underwater-policy-oracle'
MANIFEST_SHA = '5a88ad1d8cf2172c4ac1fb1c5dfb085aaff12d9cbc41910e997373412f1c71de'
SOURCE_COMMIT = '1acf788854b8ce6827c01a5ddbdd97035a8d9889'
SOURCES = ('save4', 'save5', 'creatures', 'creature_data', 'equipment',
           'equipment_data', 'southern_quests', 'magma_quests')
FIXTURES = (*EARLY_FIXTURES,
    (5, 'magma-all65-town.sav', 'a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858'),
    (6, 'underwater-all89-town.sav', '41cf371618208e0097fe6ee10393e3185b4bffb2af9dad9e5f81e2663d6673a0'),
    (6, 'underwater-minimal12-town.sav', '3f5bbccab022f86b38f4d180e8cf66b04c055791fe4804ddbebbdefb5406aeda'))
EDGES = (0, 1, 2, 3, 7, 15, 31, 63, 127, 128, 254, 255)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def extract_oracle(folder):
    """Check every byte before extracting regular, allowlisted source files only."""
    raw = (ORACLE / 'provenance.json').read_bytes()
    assert digest(raw) == MANIFEST_SHA, 'Frozen Underwater manifest changed'
    manifest = json.loads(raw)
    assert manifest['source_commit'] == SOURCE_COMMIT
    rows = {row['path']: row for row in manifest['files']}
    seen = set()
    for archive in manifest['archives']:
        data = (ORACLE / archive['path']).read_bytes()
        assert len(data) == archive['bytes'] and digest(data) == archive['sha256']
        assert len(data) < 75000
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as source:
            for member in source:
                assert member.isfile() and member.name in rows and member.name not in seen
                assert Path(member.name).parts[0] == 'src' and '..' not in Path(member.name).parts
                raw = source.extractfile(member).read()
                expected = rows[member.name]
                assert len(raw) == expected['bytes'] and digest(raw) == expected['sha256'], member.name
                target = folder / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                seen.add(member.name)
    assert seen == set(rows)
    return manifest


def source_closure(root, names=SOURCES):
    pending = ['src/' + name + '.c' for name in names]
    result = {}
    while pending:
        path = pending.pop()
        if path in result:
            continue
        data = (root / path).read_bytes()
        result[path] = data
        for name in re.findall(rb'^\s*#include\s*"([^"]+)"', data, re.M):
            pending.append(str(Path(path).parent / name.decode()))
    return result


def erase_live_tables(name, data):
    """Mutate live data in a temporary copy; preserve every historical policy."""
    if name not in ('creature_data.c', 'equipment_data.c'):
        return data
    text = data.decode()
    text, count = re.subn(r'(const\s+\w+\s+\w+\[[^\n=]+\]\s*=\s*)\{.*?\};',
                          r'\1{0};', text, flags=re.S)
    assert count >= (8 if name == 'creature_data.c' else 3), (name, count)
    return text.encode()


def build(root, folder, transform=None, extra_harness=''):
    folder.mkdir()
    hashes = {}
    for path, data in source_closure(root).items():
        name = Path(path).name
        hashes[name] = digest(data)
        (folder / name).write_bytes(transform(name, data) if transform else data)
    from history_abi_compat import adapt_harness,bind_compat
    harness,old_abi=adapt_harness(root,HARNESS + extra_harness)
    (folder / 'probe.c').write_text(harness)
    so = folder / 'history.so'
    subprocess.run(shlex.split(os.environ.get('HOST_CC', 'cc')) + [
        '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-ffreestanding',
        '-fno-builtin', '-DSAVE4_HOST_TEST', '-DSAVE5_HOST_TEST', '-shared',
        '-fPIC', '-I' + str(folder), *[str(folder / (n + '.c')) for n in SOURCES],
        str(folder / 'probe.c'), '-o', str(so)], check=True)
    lib = C.CDLL(str(so))
    bind_compat(lib,old_abi)
    lib.history_probe_bank.argtypes = [C.c_void_p, C.c_uint, C.POINTER(Save)]
    lib.history_probe_image.argtypes = [C.c_void_p, C.POINTER(Save)]
    lib.history_encode.argtypes = [C.POINTER(Save), C.c_void_p]
    lib.history_fresh.argtypes = [C.POINTER(Save)]
    lib.save5_validate_revision.argtypes = [C.POINTER(Save), C.c_uint]
    lib.save5_validate.argtypes = [C.POINTER(Save)]
    lib._hashes = hashes
    assert lib.history_state_size() == C.sizeof(Save)
    return lib


class ReturnHistoricalDifferential(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='return-history-')
        cls.addClassCleanup(cls.tmp.cleanup)
        folder = Path(cls.tmp.name)
        cls.oracle = folder / 'oracle'
        cls.manifest = extract_oracle(cls.oracle)
        cls.old = build(cls.oracle, folder / 'old')
        cls.new = build(ROOT, folder / 'new')
        cls.oldout, cls.newout = Save(), Save()
        cls.counts = collections.Counter()
        cls.images, cls.seeds, cls.states = [], {}, {}
        for revision, name, sha in FIXTURES:
            raw = (ROOT / f'tests/fixtures/v5-revision{revision}' / name).read_bytes()
            assert len(raw) == 32768 and digest(raw) == sha, name
            cls.images.append((revision, name, raw))
            offset = max((A, B), key=lambda p: int.from_bytes(raw[p + 8:p + 12], 'little'))
            cls.seeds.setdefault(revision, raw[offset:offset + SIZE])
            state = Save()
            assert cls.old.history_probe_image(raw, C.byref(state)) == 1, name
            cls.states.setdefault(revision, bytes(state))

    @classmethod
    def tearDownClass(cls):
        for row in cls.manifest['files']:
            assert digest((cls.oracle / row['path']).read_bytes()) == row['sha256']
        print(json.dumps({'suite': 'return-history-differential', 'counts': dict(cls.counts),
              'oracle_commit': SOURCE_COMMIT, 'oracle_manifest_sha256': MANIFEST_SHA,
              'candidate_source_sha256': cls.new._hashes}, sort_keys=True))

    def compare(self, bank, expected=None, label='mutant', offset=A, candidate=None, crc=True):
        bank = bytes(repair_crc(bank)) if crc else bytes(bank)
        old = self.old.history_probe_bank(bank, offset, C.byref(self.oldout))
        new = (candidate or self.new).history_probe_bank(bank, offset, C.byref(self.newout))
        self.assertIn(old, (0, 1), ('oracle read contract', label))
        self.assertIn(new, (0, 1), ('candidate read contract', label))
        self.assertEqual(old, new, (label, digest(bank)))
        self.assertEqual(bytes(self.oldout), bytes(self.newout), (label, 'decoded/failure bytes'))
        if expected is not None:
            self.assertEqual(old, expected, label)
        self.counts['banks'] += 1
        self.counts['accepted' if old else 'rejected'] += 1
        self.counts['revision' + str(int.from_bytes(bank[12:14], 'little'))] += 1
        if old:
            rev = int.from_bytes(bank[12:14], 'little')
            self.assertEqual(self.old.save5_validate_revision(C.byref(self.oldout), rev), 1, label)
            self.assertEqual((candidate or self.new).save5_validate_revision(C.byref(self.newout), rev), 1, label)
            self.counts['accepted_blocking_validations'] += 1
        return old

    def test_original_banks_and_images_resave_as_current8_wire5_without_gain(self):
        for revision, name, data in self.images:
            for lib, output in ((self.old, self.oldout), (self.new, self.newout)):
                self.assertEqual(lib.history_probe_image(data, C.byref(output)), 1, name)
            self.assertEqual(bytes(self.oldout), bytes(self.newout), name)
            before = compare_state(self.newout)
            encoded = (C.c_ubyte * SIZE)()
            self.assertEqual(self.new.history_encode(C.byref(self.newout), encoded), 1, name)
            self.assertEqual(bytes(encoded)[2:3], b'\x05', name)
            self.assertEqual(bytes(encoded)[12:14], b'\x0b\x00', name)
            self.assertEqual(self.new.history_probe_bank(encoded, A, C.byref(self.newout)), 1, name)
            self.assertEqual(compare_state(self.newout), before, (name, 'unearned state gain'))
            self.counts['unchanged_resaved_images'] += 1
            for start, target in itertools.product((A, B), repeat=2):
                bank = data[start:start + SIZE]
                self.assertEqual(bytes(repair_crc(bank)), bank, name)
                self.compare(bank, 1, name, target)

    def test_campaign_quest_equipment_all_bytes_crc_valid(self):
        for rev, seed in self.seeds.items():
            for offset in (*range(32, 47), *range(4032, 4296), *range(4544, 5056)):
                for value in EDGES:
                    if value != seed[offset]:
                        bank = bytearray(seed); bank[offset] = value
                        self.compare(bank, label=(rev, offset, value))

    def test_minimal_banks_and_sparse_controller_fixtures(self):
        state, encoded = Save(), (C.c_ubyte * SIZE)()
        self.assertEqual(self.old.history_fresh(C.byref(state)), 1)
        self.assertEqual(self.old.history_encode(C.byref(state), encoded), 1)
        seeds = []
        for rev in range(1, 7):
            bank = bytearray(encoded); bank[12:14] = rev.to_bytes(2, 'little')
            if rev == 1:
                bank[4032:4296] = bytes(264); bank[4544:5056] = bytes(512)
            seeds.append((rev, 'minimal-synthetic', bytes(repair_crc(bank))))
        for rev, name, image in self.images:
            if 'minimal' in name:
                offset = max((A, B), key=lambda p: int.from_bytes(image[p + 8:p + 12], 'little'))
                seeds.append((rev, name, image[offset:offset + SIZE]))
        for rev, name, seed in seeds:
            self.compare(seed, 1, (rev, name))
            for offset in (*range(32, 47), *range(4032, 4296), *range(4544, 5056)):
                for value in EDGES:
                    if value != seed[offset]:
                        bank = bytearray(seed); bank[offset] = value
                        self.compare(bank, label=(rev, name, offset, value))
                        self.counts['minimal_bank_mutants'] += 1

    def test_rooms_spawns_anchors_and_region_values(self):
        for rev, seed in self.seeds.items():
            for room, spawn in itertools.product(range(256), range(8)):
                bank = bytearray(seed); bank[32:34] = bytes((room, spawn))
                self.compare(bank, label=(rev, 'room-spawn', room, spawn))
            for offset in (*range(4248, 4280), *range(4280, 4296)):
                for value in range(256):
                    bank = bytearray(seed); bank[offset] = value
                    self.compare(bank, label=(rev, 'region-anchor', offset, value))

    def test_form_and_command_all_byte_values(self):
        for rev, seed in self.seeds.items():
            for offset in (160, 176, 177, 178, 179):
                for value in range(256):
                    bank = bytearray(seed); bank[offset] = value
                    self.compare(bank, label=(rev, 'identity-command', offset, value))
            for offset in (*range(80, 85), *range(96, 144)):
                for bit in range(8):
                    bank = bytearray(seed); bank[offset] ^= 1 << bit
                    self.compare(bank, label=(rev, 'party-collection', offset, bit))

    def test_all_retained_forms_mask_bond_and_evolution_edges(self):
        rng = random.Random(0x52455437)
        for rev, seed in self.seeds.items():
            for slot in range(160):
                offset = 160 + 24 * slot
                if not seed[offset]:
                    continue
                for mask, bond in itertools.product((0, 1, 2, 3, 4, 7, 15, 31, 255, 65535),
                                                     (0, 1, 39, 40, 44, 45, 100, 101)):
                    bank = bytearray(seed)
                    bank[offset + 3] = bond
                    bank[offset + 14:offset + 16] = mask.to_bytes(2, 'little')
                    if self.compare(bank, label=(rev, 'retained', slot, mask, bond)):
                        before = compare_state(self.newout); encoded = (C.c_ubyte * SIZE)()
                        self.assertEqual(self.new.history_encode(C.byref(self.newout), encoded), 1,
                                         (rev, slot, mask, bond, 'old legal state tightened'))
                        self.assertEqual(self.new.history_probe_bank(encoded, A, C.byref(self.newout)), 1)
                        self.assertEqual(compare_state(self.newout), before)
                        self.counts['unchanged_weakened_resaves'] += 1
            for _ in range(1024):
                bank = bytearray(seed)
                for _ in range(rng.randrange(1, 6)):
                    bank[rng.randrange(SIZE)] = rng.randrange(256)
                self.compare(bank, label=(rev, 'multi-byte-random'))

    def test_blocking_validator_exact_revision_and_nonmutation(self):
        for rev, raw in self.states.items():
            self.assertEqual(self.old.save5_validate_revision(C.byref(Save.from_buffer_copy(raw)), rev), 1)
            for offset in range(C.sizeof(Save)):
                for value in (0, 1, 127, 255):
                    changed = bytearray(raw); changed[offset] = value
                    old, new = Save.from_buffer_copy(changed), Save.from_buffer_copy(changed)
                    a = self.old.save5_validate_revision(C.byref(old), rev)
                    b = self.new.save5_validate_revision(C.byref(new), rev)
                    self.assertEqual(a, b, (rev, 'blocking', offset, value))
                    self.assertEqual(bytes(old), changed); self.assertEqual(bytes(new), changed)
                    self.counts['blocking_mutants'] += 1
        for rev in (0, 9, 255, 256, 65535, 0xffffffff):
            self.assertEqual(self.old.save5_validate_revision(None, rev), 0)
            self.assertEqual(self.new.save5_validate_revision(None, rev), 0)

    def test_frozen_r1_to_r6_ignore_erased_live_creature_and_equipment_data(self):
        mutant = build(ROOT, Path(self.tmp.name) / 'erased-live', erase_live_tables)
        for rev, name, image in self.images:
            self.assertEqual(mutant.history_probe_image(image, C.byref(self.newout)), 1, name)
            self.assertEqual(mutant.save5_validate_revision(C.byref(self.newout), rev), 1, name)
            self.assertEqual(mutant.save5_validate(C.byref(self.newout)), 0, 'control must break live validation')
            for offset in (A, B):
                self.compare(image[offset:offset + SIZE], 1, (name, 'erased-live'), candidate=mutant)
        for rev, seed in self.seeds.items():
            for offset in (*range(32, 47), *range(4248, 4296), 160, 163, 174, 175, 176, 177,
                           4544, 4545, 4944, 4954, 5024, 5028):
                for value in EDGES:
                    bank = bytearray(seed); bank[offset] = value
                    self.compare(bank, label=(rev, 'erased-live', offset, value), candidate=mutant)

    def test_padding_headers_bad_crc_and_unknown_newer_bank_fallback(self):
        for rev, seed in self.seeds.items():
            for offset in (*range(0, 32), *range(47, 80), *range(85, 96), *range(144, 160),
                           *range(4296, 4352), *range(5056, SIZE)):
                bank = bytearray(seed); bank[offset] ^= 128
                self.compare(bank, label=(rev, 'header-reserve', offset))
            for offset in (0, 12, 16, 20, 160, 4032, 4544, SIZE - 1):
                bank = bytearray(seed); bank[offset] ^= 1
                self.compare(bank, 0, (rev, 'bad-crc', offset), crc=False)
            for unknown in (0, 12, 255, 256, 65535):
                bank = bytearray(seed); bank[12:14] = unknown.to_bytes(2, 'little')
                self.compare(bank, 0, (rev, 'unknown', unknown))
                for good, bad in ((A, B), (B, A)):
                    bank[8:12] = (0x7fffffff).to_bytes(4, 'little')
                    image = bytearray([255]) * 32768
                    image[good:good + SIZE] = seed; image[bad:bad + SIZE] = repair_crc(bank)
                    self.assertEqual(self.old.history_probe_image(bytes(image), C.byref(self.oldout)), 1)
                    self.assertEqual(self.new.history_probe_image(bytes(image), C.byref(self.newout)), 1)
                    self.assertEqual(bytes(self.oldout), bytes(self.newout))
                    self.counts['invalid_newer_fallbacks'] += 1


if __name__ == '__main__':
    unittest.main(verbosity=2)
