#!/usr/bin/env python3
"""Whole-bank historical save5 differential, against a pinned Southern oracle.

Run: python3 tests/test_save5_history_differential.py
The default oracle is the minimal frozen Southern source closure shipped under
tests/fixtures/southern-policy-oracle. SAVE5_HISTORY_BASELINE may explicitly select
an equivalent frozen Southern checkout. All required source/header/helper/SRAM
inputs are SHA256-pinned and compiled in a private temporary snapshot, with only
that snapshot's includes. No sibling checkout is required or automatically used.
The production candidate is independently snapshotted and compiled. Neither
source tree is changed, and this suite writes no evidence/build files there.

Every synthetic bank has a correct independently computed CRC32. These are host
codec/adversarial fixtures, never evidence of controller-earned acquisitions.
For EVERY case, compare acceptance, save5_has_valid, every decoded state byte,
failure-output atomicity, and complete SRAM immutability. Every single-bank
case isolates the bank from legacy or second-bank fallbacks.
"""
import collections
import ctypes as C
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import shlex
import shutil
import subprocess
import tempfile
import unittest

from test_save5 import A, B, SIZE, ROOT, Save, repair_crc

PACKAGED_BASELINE = ROOT / 'tests/fixtures/southern-policy-oracle'
BASELINE = Path(os.environ.get('SAVE5_HISTORY_BASELINE', PACKAGED_BASELINE)).resolve()
BASELINE_MANIFEST_SHA = 'a68c79b40b1c8e67088a51daa972736e16253ac6ac94c3ba72e7cbc22c469ff8'
SOURCES = ('save4', 'save5', 'creatures', 'creature_data', 'equipment',
           'equipment_data', 'southern_quests')
BASELINE_SHA = {
    'save4': 'c6f15dd66c56cf6f6703742f9e7e02ae1662e124ed1e3260c39c14421cb69c7c',
    'save5': 'f0b1c2ce7e5b502694cd1244c785e4b6dc356b968efd5f273500b45d946ad059',
    'creatures': 'b239046f8e04b18dbbd7d330c36cbfd96dadd01d444d34084ddc75eb4cd4e53c',
    'creature_data': 'eaa427f100f808790b122c49db34820be2b5fa54213e00f67dcc69780c4fe1c2',
    'equipment': '79414903f649cb9af3aba502042e366eea215b500869a80223210a0cf6ba02ec',
    'equipment_data': 'a9f6c1ac1ec0c889700f6aa54fe18025a28d66eba60fc36d93ffd9fe664b8c05',
    'southern_quests': '3296c70118e2c88f8d70dc3a68a4017b0525fbaa47e5826a9dc98443bdef491b',
}
FIXTURES = (
    (1, 'all-evolved-village.sav',
     '26d271e3c37d456f5eefcda9900be10d702eb60aa43ebc108eec96f0740f50a8'),
    (1, 'pr5-evolved-reversed-party.sav',
     '806283f8ee36f4eb139822d74e8c176cf4c2e08f30c9e27ed5da82ae5f21d4d1'),
    (2, 'all-eleven-town.sav',
     '74f39c496a1e93eb47c5b50828513033899be0567a1391cf99869750defa9106'),
    (3, 'northern-all21-town.sav',
     'f4e853c85445b8567263a1a875eba967e552e0dcae30958ca42f39bfec4e4479'),
    (4, 'southern-all41-town.sav',
     '0bd83c19eb0dee81b3cd9e2b48462f6362b559786e38fa119312fe05787b0bd3'),
    (4, 'southern-minimal8-town.sav',
     '968066ed983bd48fc2af0d7ffeb79f635624037ef2099809fd00c97aaa04cc0c'),
)
QUEST_MASKS = (7, 3, 7, 7, 3, 1, 1, 1, 3, 7, 1, 3, 7, 3, 7, 7,
               3, 7, 7, 3, 7, 15, 3, 3, 15, 7, 3, 3, 3, 3)
SOURCE_QUEST = (-1, 7, -1, 6, -1, 4, 0, 8, 1, 9, 5, 10, 6,
                16, 17, 18, 19, 19, 20, 22, 29, 25, 27, 26, 28)
ITEMS = (1, 2, 9, 10, 17, 18, 33, 34, 49, 50, 65, 81, 82,
         3, 11, 19, 35, 51, 83, 4, 12, 36, 52, 66, 84)
ITEM_SLOT = {item: (0 if item < 32 else 1 if item < 48 else
                    2 if item < 64 else 3 if item < 80 else 4) for item in ITEMS}
BYTE_EDGES = (0, 1, 2, 3, 7, 15, 31, 63, 127, 128, 254, 255)

HARNESS = r'''
#include "save5.h"
#include <string.h>
unsigned history_state_size(void) { return sizeof(Save5State); }
/* Return low-bit acceptance, plus an error code if a read contract is broken. */
static unsigned history_probe_staged(Save5State *out) {
    unsigned accepted, valid, i;
    unsigned char before[32768];
    memcpy(before, save5_test_sram, sizeof before);
    memset(out, 0xcc, sizeof *out);
    accepted = (unsigned)save5_load(out);
    valid = (unsigned)save5_has_valid();
    if (accepted != valid) return 10u + accepted;
    if (save5_test_write_count()) return 20u + accepted;
    if (memcmp(before, save5_test_sram, sizeof before)) return 30u + accepted;
    if (!accepted) for (i=0; i<sizeof *out; ++i)
        if (((unsigned char *)out)[i] != 0xcc) return 40u;
    return accepted;
}
static void history_reset(void) {
    save5_test_reset_writer();
    save5_test_fail_after(-1);
    save5_test_corrupt_write(-1, 0);
    memset(save5_test_sram, 0xff, sizeof save5_test_sram);
}
unsigned history_probe_bank(const unsigned char *bank, unsigned offset, Save5State *out) {
    history_reset();
    if (offset != SAVE5_BANK_A && offset != SAVE5_BANK_B) return 50u;
    memcpy(save5_test_sram + offset, bank, SAVE5_BANK_SIZE);
    return history_probe_staged(out);
}
unsigned history_probe_image(const unsigned char *image, Save5State *out) {
    history_reset();
    memcpy(save5_test_sram, image, sizeof save5_test_sram);
    return history_probe_staged(out);
}
int history_fresh(Save5State *s) {
    memset(s, 0, sizeof *s);
    s->campaign.chapter_flags = 3;
    s->campaign.story_seen = 10;
    if (!creatures_migrate_legacy(&s->roster, 3, 0)) return 0;
    equipment_init(&s->equipment);
    return save5_validate(s);
}
int history_encode(const Save5State *s, unsigned char *bank) {
    history_reset();
    if (!save5_store(s)) return 0;
    memcpy(bank, save5_test_sram + SAVE5_BANK_A, SAVE5_BANK_SIZE);
    return 1;
}
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fixture_bytes(revision, filename, digest):
    fixture_root=ROOT if revision==4 else BASELINE
    data = (fixture_root / f'tests/fixtures/v5-revision{revision}' / filename).read_bytes()
    if len(data) != 32768 or sha(data) != digest:
        raise AssertionError(f'Frozen historical fixture mismatch: {filename}')
    return data


def build_library(source_root, folder, oracle=False, data_transform=None):
    """Independent regular translation units, no source include/renaming tricks."""
    folder.mkdir()
    source_hashes = {}
    # Include future private policy .h/.inc files without sharing include paths.
    for path in (source_root / 'src').iterdir():
        if path.is_file() and path.suffix in ('.c', '.h', '.inc'):
            data = path.read_bytes()
            (folder / path.name).write_bytes(data)
            source_hashes[path.name] = sha(data)
    if data_transform:
        path = folder / 'equipment_data.c'
        path.write_text(data_transform(path.read_text()))
    (folder / 'history_harness.c').write_text(HARNESS)
    inputs = [folder / f'{name}.c' for name in SOURCES]
    inputs.append(folder / 'history_harness.c')
    if oracle:
        # The frozen event helpers create an authentic-grammar revision4 seed.
        # They are synthetic setup, not a substitute for controller evidence.
        data = fixture_bytes(*next(f for f in FIXTURES if f[0]==3))
        (folder / 'southern_n5_fixture.h').write_text(
            'static const unsigned char southern_n5_fixture[32768]={' +
            ','.join(map(str, data)) + '};\n')
        shutil.copyfile(BASELINE / 'tests/southern_save_sanitizer.c',
                        folder / 'southern_save_sanitizer.c')
        inputs.append(folder / 'southern_save_sanitizer.c')
    so = folder / 'history.so'
    subprocess.run(shlex.split(os.environ.get('HOST_CC', 'cc')) + [
        '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-ffreestanding',
        '-fno-builtin', '-DSAVE4_HOST_TEST', '-DSAVE5_HOST_TEST',
        '-DSOUTHERN_SETUP_ONLY', '-shared', '-fPIC', '-I' + str(folder),
        *map(str, inputs), '-o', str(so)], check=True)
    lib = C.CDLL(str(so))
    lib.history_probe_bank.argtypes = [C.c_void_p, C.c_uint, C.POINTER(Save)]
    lib.history_probe_image.argtypes = [C.c_void_p, C.POINTER(Save)]
    lib.history_probe_bank.restype = lib.history_probe_image.restype = C.c_uint
    lib.history_state_size.restype = C.c_uint
    lib.history_fresh.argtypes = [C.POINTER(Save)]
    lib.history_encode.argtypes = [C.POINTER(Save), C.c_void_p]
    if oracle:
        lib.southern_test_completed.argtypes = [C.POINTER(Save), C.c_uint]
    if lib.history_state_size() != C.sizeof(Save):
        raise AssertionError('Save5State ABI differs from test ctypes declaration')
    lib._source_hashes = source_hashes
    return lib


def with_revision(bank, revision):
    result = bytearray(bank)
    result[12:14] = revision.to_bytes(2, 'little')
    if revision == 1:
        result[4032:4296] = bytes(264)
        result[4544:5056] = bytes(512)
    return bytes(repair_crc(result))


def set_quest(bank, quest, state, objectives, reward=None, sources=False):
    """Edit the wire directly, independently of both implementations' setters."""
    offset, shift = 4032 + quest // 4, (quest % 4) * 2
    bank[offset] = (bank[offset] & ~(3 << shift)) | (state << shift)
    bank[4048 + 2 * quest:4050 + 2 * quest] = objectives.to_bytes(2, 'little')
    offset, bit = 4176 + quest // 8, 1 << (quest % 8)
    claimed = (state == 3) if reward is None else reward
    if claimed:
        bank[offset] |= bit
    else:
        bank[offset] &= ~bit
    if sources:
        for source, tied in enumerate(SOURCE_QUEST):
            if tied == quest:
                offset, bit = 5024 + source // 8, 1 << (source % 8)
                if state == 3:
                    bank[offset] |= bit
                else:
                    bank[offset] &= ~bit


class HistoricalSaveDifferentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        provenance_bytes = (PACKAGED_BASELINE / 'provenance.json').read_bytes()
        if sha(provenance_bytes) != BASELINE_MANIFEST_SHA:
            raise AssertionError('Frozen Southern oracle manifest changed')
        provenance = json.loads(provenance_bytes)
        for row in provenance['files']:
            data = (BASELINE / row['path']).read_bytes()
            if len(data) != row['bytes'] or sha(data) != row['sha256']:
                raise AssertionError('Historical oracle input changed: ' + row['path'])
        print('Frozen Southern oracle:', BASELINE, flush=True)
        for name, expected in BASELINE_SHA.items():
            actual = sha((BASELINE / 'src' / f'{name}.c').read_bytes())
            if actual != expected:
                raise AssertionError(f'Historical oracle changed: {name}.c: {actual}')
        cls.tmp = tempfile.TemporaryDirectory(prefix='save5-history-differential-')
        cls.addClassCleanup(cls.tmp.cleanup)
        folder = Path(cls.tmp.name)
        cls.baseline = build_library(BASELINE, folder / 'baseline', oracle=True)
        cls.candidate = build_library(ROOT, folder / 'candidate')
        cls.counts = collections.Counter()
        cls.images = []
        cls.completed = {}
        cls.original_banks = []
        for revision, filename, digest in FIXTURES:
            data = fixture_bytes(revision, filename, digest)
            cls.images.append((filename, data))
            for offset in (A, B):
                bank = data[offset:offset + SIZE]
                cls.original_banks.append((f'{filename}:{offset:#x}', bank))
            latest = max((A, B), key=lambda off: int.from_bytes(data[off+8:off+12], 'little'))
            cls.completed.setdefault(revision, data[latest:latest + SIZE])
        state = Save()
        if cls.baseline.southern_test_completed(C.byref(state), 0):
            raise AssertionError('Could not construct frozen Southern completed state')
        bank = (C.c_ubyte * SIZE)()
        if not cls.baseline.history_encode(C.byref(state), bank):
            raise AssertionError('Could not encode frozen Southern completed state')
        cls.completed[4] = bytes(bank)
        if not cls.baseline.history_fresh(C.byref(state)):
            raise AssertionError('Could not construct frozen fresh state')
        if not cls.baseline.history_encode(C.byref(state), bank):
            raise AssertionError('Could not encode frozen fresh state')
        cls.minimal = {r: with_revision(bytes(bank), r) for r in range(1, 5)}
        cls.out_old, cls.out_new = Save(), Save()
        for r in range(1, 5):
            for seed in (cls.completed[r], cls.minimal[r]):
                if cls.baseline.history_probe_bank(seed, A, C.byref(cls.out_old)) != 1:
                    raise AssertionError(f'Invalid oracle seed for revision {r}')

    @classmethod
    def tearDownClass(cls):
        # Include reproducible counts/hashes in stdout without mutating the repo.
        print('\n' + json.dumps({
            'suite': 'historical-save5-whole-bank-differential',
            'counts': dict(sorted(cls.counts.items())),
            'baseline_save5_sha256': BASELINE_SHA['save5'],
            'candidate_save5_sha256': cls.candidate._source_hashes['save5.c'],
            'deterministic_random_seed': 0x53415635,
        }, sort_keys=True))
        # Read-only oracle guarantee includes all snapshotted headers and sources.
        for filename, digest in cls.baseline._source_hashes.items():
            if sha((BASELINE / 'src' / filename).read_bytes()) != digest:
                raise AssertionError(f'Frozen source changed during differential: {filename}')

    def compare(self, bank, label, expected=None, group='bank', offset=A, candidate=None):
        data = bytes(repair_crc(bank))
        old = self.baseline.history_probe_bank(data, offset, C.byref(self.out_old))
        new = (candidate or self.candidate).history_probe_bank(data, offset, C.byref(self.out_new))
        if old not in (0, 1) or new not in (0, 1):
            self.fail(f'{label}: read contract violated: baseline={old}, candidate={new}')
        if old != new:
            changes = [(i, bank[i]) for i in range(len(bank))
                       if i < 47 or 4032 <= i < 4296 or 4544 <= i < 5056]
            self.fail(f'{label}: baseline={old}, candidate={new}; bank_sha256={sha(data)}; '
                      f'wire={changes}')
        if bytes(self.out_old) != bytes(self.out_new):
            diffs = [(i, a, b) for i, (a, b) in
                     enumerate(zip(bytes(self.out_old), bytes(self.out_new))) if a != b]
            self.fail(f'{label}: decoded state mismatch: {diffs[:30]}')
        if expected is not None:
            self.assertEqual(old, expected, label)
        self.counts[group] += 1
        self.counts['accepted' if old else 'rejected'] += 1
        self.counts[f'revision{int.from_bytes(data[12:14], "little")}'] += 1
        return old

    def test_01_original_images_banks_and_valid_seeds(self):
        for label, image in self.images:
            old = self.baseline.history_probe_image(image, C.byref(self.out_old))
            new = self.candidate.history_probe_image(image, C.byref(self.out_new))
            self.assertEqual((old, new), (1, 1), label)
            self.assertEqual(bytes(self.out_old), bytes(self.out_new), label)
            self.counts['complete_original_sram_images'] += 1
        for label, bank in self.original_banks:
            # Preserve/check original CRC, rather than silently repairing fixtures.
            self.assertEqual(bytes(repair_crc(bank)), bank, label)
            for offset in (A, B):
                self.compare(bank, label, expected=1, group='original_banks', offset=offset)
        for revision in range(1, 5):
            for kind, seeds in (('minimal', self.minimal), ('completed', self.completed)):
                self.compare(seeds[revision], (revision, kind), expected=1, group='valid_seeds')

    def test_02_crc_valid_single_byte_mutants(self):
        # Broad complete-field coverage: every campaign, quest, and equipment
        # byte, including high-ID bytes and every reserved field.
        offsets = [*range(32, 47), *range(4032, 4296), *range(4544, 5056)]
        for revision in range(1, 5):
            for kind, seeds in (('minimal', self.minimal), ('completed', self.completed)):
                original = seeds[revision]
                for offset in offsets:
                    for value in BYTE_EDGES:
                        if value == original[offset]:
                            continue
                        bank = bytearray(original)
                        bank[offset] = value
                        self.compare(bank, (revision, kind, offset, value), group='single_byte_mutants')
        self.assertGreater(self.counts['single_byte_mutants'], 60000)

    def test_03_all_byte_values_for_gates_variables_and_anchors(self):
        offsets = (32, 33, 34, 4187, 4193, 4248, 4249, 4250, 4256, 4266,
                   4280, 4281, 4282, 5024, 5025, 5026, 5027)
        for revision, original in self.completed.items():
            for offset in offsets:
                for value in range(256):
                    bank = bytearray(original)
                    bank[offset] = value
                    self.compare(bank, (revision, offset, value), group='all_byte_gate_values')

    def test_04_rooms_spawns_and_anchor_prerequisite_combinations(self):
        for revision, original in self.completed.items():
            for room, spawn in itertools.product(range(256), range(8)):
                bank = bytearray(original)
                bank[32:34] = bytes((room, spawn))
                self.compare(bank, (revision, room, spawn), group='room_spawn_pairs')
            # Isolate anchors from room ranges, including both present/absent
            # visits and town returns retaining historically earned anchors.
            for room, region in ((16, 0), (17, 0), (22, 1), (23, 1), (30, 2), (31, 2)):
                for spawn, anchor, visited in itertools.product(range(6), range(4), (False, True)):
                    bank = bytearray(original)
                    bank[32:34] = bytes((room, spawn))
                    bank[4280 + region] = anchor
                    bit = 1 << (room - (16, 22, 30)[region])
                    if visited:
                        bank[4248 + region] |= bit
                    else:
                        bank[4248 + region] &= ~bit
                    self.compare(bank, (revision, room, spawn, anchor, visited), group='anchor_visit_pairs')

    def test_05_quest_state_objective_reward_and_source_combinations(self):
        accepted = 0
        for revision, original in self.completed.items():
            for quest in range(64):
                mask = QUEST_MASKS[quest] if quest < len(QUEST_MASKS) else 0
                values = sorted({0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 14, 15, 16,
                                 31, 255, 256, 32768, 65535, mask})
                for state, objectives, reward in itertools.product(range(4), values, (False, True)):
                    bank = bytearray(original)
                    set_quest(bank, quest, state, objectives, reward, sources=True)
                    if quest in (3, 9) and not state:
                        bank[4184 + quest] = 0
                    accepted += self.compare(bank, (revision, quest, state, objectives, reward),
                                             group='quest_combinations')
            # Fresh active/ready quests exercise valid partial progress, including
            # zero-objective ACTIVE and the objective-prefix exception.
            for quest in range((0, 0, 11, 22, 30)[revision]):
                mask = QUEST_MASKS[quest]
                for objectives in range(mask + 1):
                    bank = bytearray(self.minimal[revision])
                    bank[4248] = 1
                    if revision >= 3:
                        bank[4249] = 1
                    set_quest(bank, quest, 2 if objectives == mask else 1, objectives)
                    accepted += self.compare(bank, (revision, 'fresh', quest, objectives),
                                             group='fresh_quest_combinations')
        self.assertGreater(accepted, 100)

    def test_06_equipment_ids_categories_refs_seen_and_sources(self):
        for revision in range(1, 5):
            original = self.minimal[revision]
            for item in (*range(512), 512, 1023, 32767, 32768, 65535):
                bank = bytearray(original)
                # A valid-shaped second record with its matching discovery bit;
                # no arbitrary current helper resolves identity for the oracle.
                bank[4552:4560] = item.to_bytes(2, 'little') + bytes((0, int(item == 1), 1, 0, 0, 0))
                if item < 512:
                    bank[4944 + item // 8] |= 1 << (item % 8)
                for category in range(5):
                    trial = bytearray(bank)
                    trial[4928 + category] = 1
                    self.compare(trial, (revision, item, category), group='equipment_id_category_pairs')
            original = self.completed[revision]
            for category, reference in itertools.product(range(5), range(256)):
                bank = bytearray(original)
                bank[4928 + category] = reference
                self.compare(bank, (revision, category, reference), group='equipment_refs')
            for source in range(64):
                for claimed, seen in itertools.product((False, True), repeat=2):
                    bank = bytearray(original)
                    offset, bit = 5024 + source // 8, 1 << (source % 8)
                    bank[offset] = bank[offset] | bit if claimed else bank[offset] & ~bit
                    if source < len(ITEMS):
                        item = ITEMS[source]
                        offset, bit = 4944 + item // 8, 1 << (item % 8)
                        bank[offset] = bank[offset] | bit if seen else bank[offset] & ~bit
                    self.compare(bank, (revision, source, claimed, seen), group='equipment_source_seen_pairs')
            # Every authored class/category can be carried with no claim, and
            # discovery history can outlive a removed nonstarter bag record.
            for slot in range(1, 48):
                bank = bytearray(original)
                bank[4544 + 8*slot:4552 + 8*slot] = bytes(8)
                for category in range(5):
                    if bank[4928 + category] == slot:
                        bank[4928 + category] = 0 if category == 0 else 255
                self.compare(bank, (revision, 'retained-history-removed-item', slot),
                             group='removed_equipment_records')

    def test_07_valid_gear_layouts_and_independent_historical_ledgers(self):
        rng = random.Random(0x53415635)
        for revision, original in self.completed.items():
            for iteration in range(128):
                bank = bytearray(original)
                # Persistent generic reward/event/aid ledgers historically permit
                # bits now used elsewhere. New content must not reinterpret them.
                bank[129:144] = bytes(value | rng.randrange(256) for value in original[129:144])
                bank[4456:4536] = bytes(rng.randrange(256) for _ in range(80))
                # Preserve story-required low nibble while randomizing generic bits.
                bank[128] |= rng.randrange(16) << 4
                if revision >= 2:
                    count = (0, 0, 13, 19, 25)[revision]
                    records = [bytes(bank[4544 + i*8:4552 + i*8]) for i in range(48)]
                    indices = list(range(1, 48))
                    rng.shuffle(indices)
                    mapping = {0: 0, **dict(zip(range(1, 48), indices))}
                    for old_slot, record in enumerate(records):
                        new_slot = mapping[old_slot]
                        bank[4544 + 8*new_slot:4552 + 8*new_slot] = record
                    for category in range(5):
                        choices = [mapping[i] for i, record in enumerate(records)
                                   if int.from_bytes(record[:2], 'little') in ITEMS[:count]
                                   and ITEM_SLOT[int.from_bytes(record[:2], 'little')] == category]
                        if category:
                            choices.append(255)
                        bank[4928 + category] = rng.choice(choices)
                self.compare(bank, (revision, iteration), expected=1, group='valid_combination_seeds')

    def test_08_revision_boundaries_and_crc_valid_header_padding(self):
        for revision, original in self.completed.items():
            for advertised in (0, 1, 2, 3, 4, 6, 255, 256, 65535):
                bank = bytearray(original)
                bank[12:14] = advertised.to_bytes(2, 'little')
                self.compare(bank, (revision, 'advertised', advertised), group='revision_crossovers')
            for offset in (*range(21, 32), *range(47, 96), *range(144, 160),
                           *range(4005, 4008), *range(4012, 4032),
                           *range(4536, 4544), 5056, 5057, 5119, 6143):
                for value in (1, 128, 255):
                    bank = bytearray(original)
                    bank[offset] = value
                    self.compare(bank, (revision, 'reserved', offset, value), expected=0,
                                 group='reserved_padding')


    def test_09_runtime_equipment_drift_cannot_change_historical_meaning(self):
        def replace_one(old, new):
            def transform(text):
                self.assertEqual(text.count(old), 1, old)
                return text.replace(old, new)
            return transform

        # These mutate only temporary copies. Weapon class is intentionally a
        # negative control: the frozen record/ref validator does not inspect it.
        variants = {
            'source-map': replace_one('1, 2, 9, 10, 17,', '1, 9, 2, 10, 17,'),
            'category-slot': replace_one('[9] = {9, 0, 2, 0,', '[9] = {9, 4, 0, 0,'),
            'record-flags': replace_one('[9] = {9, 0, 2, 0,', '[9] = {9, 0, 2, 1,'),
            'disabled-item': replace_one('[9] = {9, 0, 2, 0,', '[9] = {0, 0, 2, 0,'),
            'starter-flags': replace_one('[1] = {1, 0, 1, 1,', '[1] = {1, 0, 1, 0,'),
            'disabled-starter': replace_one('[1] = {1, 0, 1, 1,', '[1] = {0, 0, 1, 1,'),
            'weapon-class-control': replace_one('[9] = {9, 0, 2, 0,', '[9] = {9, 0, 3, 0,'),
        }
        witnesses = {}
        for revision in (2, 3, 4):
            bank = bytearray(self.minimal[revision])
            bank[4248] = 1
            bank[4552:4560] = bytes((9, 0, 0, 0, 1, 0, 0, 0))
            bank[4945] |= 2
            bank[5024] |= 4
            bank[4928] = 1
            witnesses[revision] = bytes(repair_crc(bank))
            self.compare(bank, ('drift-witness', revision), expected=1,
                         group='catalog_drift_witnesses')

        for name, transform in variants.items():
            old = build_library(BASELINE, Path(self.tmp.name) / ('drift-old-' + name),
                                data_transform=transform)
            new = build_library(ROOT, Path(self.tmp.name) / ('drift-new-' + name),
                                data_transform=transform)
            legacy = self.minimal[1]
            legacy_result = old.history_probe_bank(legacy, A, C.byref(self.out_old))
            self.assertEqual(legacy_result, 0 if name in ('starter-flags', 'disabled-starter') else 1, name)
            self.compare(legacy, (name, 'revision1-starter'), expected=1,
                         group='catalog_drift_valid_banks', candidate=new)
            disagreement = 0
            for revision, bank in witnesses.items():
                result = old.history_probe_bank(bank, A, C.byref(self.out_old))
                self.assertIn(result, (0, 1), name)
                disagreement += result != 1
                self.compare(bank, (name, 'witness', revision), expected=1,
                             group='catalog_drift_valid_banks', candidate=new)
            if name == 'weapon-class-control':
                self.assertEqual(disagreement, 0, 'Class is not a frozen validation field')
            else:
                self.assertEqual(disagreement, 3, 'Mutation must break the old dynamic oracle')
            for revision in range(1, 5):
                for kind, seeds in (('minimal', self.minimal), ('completed', self.completed)):
                    self.compare(seeds[revision], (name, kind, revision), expected=1,
                                 group='catalog_drift_valid_banks', candidate=new)
            # Full malformed banks are compared under the altered catalog too;
            # matching valid fixtures alone would miss accidentally permissive
            # fallback to current records, category refs, seen bits or sources.
            for revision, original in witnesses.items():
                for offset in (*range(4544, 4576), *range(4928, 4933),
                               *range(4944, 4956), *range(5024, 5032)):
                    for value in BYTE_EDGES:
                        bank = bytearray(original)
                        bank[offset] = value
                        self.compare(bank, (name, revision, offset, value),
                                     group='catalog_drift_mutants', candidate=new)


if __name__ == '__main__':
    unittest.main(verbosity=2)
