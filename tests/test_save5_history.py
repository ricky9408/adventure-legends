#!/usr/bin/env python3
"""Immutable revision1..4 save-policy regression/mutation tests.

These are host codec tests. No synthetic SRAM is evidence of native gameplay.
The original suites and controller fixture bytes remain unchanged.
"""
import ctypes as C
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_save5 import A, B, SIZE, BUSY, DONE, FAILED, Save, Quests, Roster, Equipment, repair_crc, compare_state

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('save4', 'save5', 'creatures', 'creature_data', 'equipment', 'equipment_data')
SCHEMA_SHA256 = '64a750f78eb068bcbbe097881bc624a606cf13fb3244a8393b14b9f0c323e7a7'
POLICY_SHA256 = '82459e1adb8321a4cdbadd6259116995bab077fd25294837ad72f8bdc1b44b23'


def build(directory, name, replacements=None):
    files = []
    for stem in SOURCES:
        path = ROOT / 'src' / (stem + '.c')
        if replacements and stem in replacements:
            source = path.read_text()
            for before, after in replacements[stem]:
                assert before in source, (stem, before)
                source = source.replace(before, after, 1)
            path = directory / (name + '-' + stem + '.c')
            path.write_text(source)
        files.append(str(path))
    target = directory / (name + '.so')
    subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-ffreestanding', '-fno-builtin', '-DSAVE4_HOST_TEST', '-DSAVE5_HOST_TEST',
                    '-shared', '-fPIC', '-I' + str(ROOT / 'src'), *files, '-o', str(target)], check=True)
    lib = C.CDLL(str(target))
    lib.sram = (C.c_ubyte * 32768).in_dll(lib, 'save5_test_sram')
    for fn in ('save5_load', 'save5_store', 'save5_begin', 'save5_validate'):
        getattr(lib, fn).argtypes = [C.POINTER(Save)]
    lib.save5_validate_revision.argtypes = [C.POINTER(Save), C.c_uint]
    lib.save5_quests_validate.argtypes = [C.POINTER(Quests)]
    lib.creatures_migrate_legacy.argtypes = [C.POINTER(Roster), C.c_uint, C.c_uint]
    lib.equipment_init.argtypes = [C.POINTER(Equipment)]
    lib.save5_step.argtypes = [C.c_uint]
    return lib


def install(lib, data):
    lib.save5_test_reset_writer()
    lib.save5_test_fail_after(-1)
    lib.save5_test_corrupt_write(-1, 0)
    lib.sram[:] = data


def image(a=None, b=None):
    data = bytearray([255]) * 32768
    if a is not None:
        data[A:A+SIZE] = a
    if b is not None:
        data[B:B+SIZE] = b
    return data


def finish(lib):
    step = 0
    while lib.save5_status() == BUSY:
        budget = (0, 1, 7, 128, 1024, 3072, 0xffffffff)[step % 7]
        lib.save5_step(budget)
        assert lib.save5_test_step_work() <= min(budget, 3072)
        step += 1
        assert step < 500000
    return lib.save5_status()


class HistoricalSavePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='save5-history-policy-')
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.directory = Path(cls.tmp.name)
        cls.base = build(cls.directory, 'base')
        cls.broad = build(cls.directory, 'current-quest-broadened', {
            'save5': [('quest_masks[38] = {7,3,7,7', 'quest_masks[38] = {15,3,7,7')]
        })
        cls.narrow = build(cls.directory, 'current-quest-narrowed', {
            'save5': [('quest_masks[38] = {7,3,7,7', 'quest_masks[38] = {3,3,7,7')]
        })
        cls.command = build(cls.directory, 'current-command-removed', {
            'creature_data': [('    {1, 1},', '    {1, 23},')]
        })
        cls.gates = build(cls.directory, 'current-gates-and-source-quest-changed', {
            'save5': [
                ('equipment_source_quest[31] = {-1,7,-1,6,-1,4,0,8,1,9,5,10,6',
                 'equipment_source_quest[31] = {-1,0,-1,6,-1,4,7,8,1,9,5,10,6'),
                ('trial_recruit[5] = {11,12,14,15,13}', 'trial_recruit[5] = {12,11,14,15,13}'),
                ('if ((q->region_flags[1] & 240u) && !harbor) return 0;',
                 'if ((q->region_flags[1] & 240u) && !harbor) { /* future current gate */ }'),
                ('if (q->variables[i] > 3 ||', 'if (q->variables[i] > 7 ||'),
                ('if (s->room == 16) return s->spawn <= 5;', 'if (s->room == 16) return s->spawn <= 4;'),
            ]
        })

    def minimal_bank(self, revision=2):
        s = Save()
        s.campaign.chapter_flags = 1
        s.campaign.story_seen = 2
        self.assertEqual(self.base.creatures_migrate_legacy(C.byref(s.roster), 1, 0), 1)
        self.base.equipment_init(C.byref(s.equipment))
        s.quests.region_flags[0] = 1
        s.quests.states[0] = 1
        s.quests.objectives[0] = 1
        install(self.base, image())
        self.assertEqual(self.base.save5_store(C.byref(s)), 1)
        bank = bytearray(self.base.sram[A:A+SIZE])
        bank[12:14] = revision.to_bytes(2, 'little')
        bank[8:12] = (17).to_bytes(4, 'little')
        return repair_crc(bank), s

    def test_release_prefix_is_locked(self):
        content = (ROOT / 'src/save5_history_policy.h').read_text()
        schema = content[content.index('typedef struct Save5HistoryVersion'):content.index('/* BEGIN LOCKED RELEASES 1-4 */')]
        self.assertEqual(hashlib.sha256(schema.encode()).hexdigest(), SCHEMA_SHA256, 'Historical row schema changed')
        block = content.split('/* BEGIN LOCKED RELEASES 1-4 */', 1)[1].split('/* END LOCKED RELEASES 1-4 */', 1)[0]
        self.assertEqual(hashlib.sha256(block.encode()).hexdigest(), POLICY_SHA256,
                         'Released rows changed: add separately reviewed new revision rows; do not rewrite old policy')

    def test_current_q0_broadening_cannot_admit_old_active_bit8(self):
        good, s = self.minimal_bank()
        bad = bytearray(good)
        bad[4048:4050] = (8).to_bytes(2, 'little')
        bad[8:12] = (18).to_bytes(4, 'little')
        bad = repair_crc(bad)
        s.quests.objectives[0] = 8
        self.assertEqual(self.base.save5_validate(C.byref(s)), 0)
        self.assertEqual(self.broad.save5_validate(C.byref(s)), 1)  # mutation really broadened CURRENT
        for revision in (2, 3, 4):
            with self.subTest(revision=revision):
                mutated = bytearray(bad)
                mutated[12:14] = revision.to_bytes(2, 'little')
                data = image(repair_crc(mutated))
                for lib in (self.base, self.broad):
                    install(lib, data)
                    out = Save.from_buffer_copy(bytes([0x5a]) * C.sizeof(Save))
                    before = bytes(out)
                    self.assertEqual(lib.save5_load(C.byref(out)), 0)
                    self.assertEqual(lib.save5_has_valid(), 0)
                    self.assertEqual(bytes(out), before)
                    self.assertEqual(bytes(lib.sram), data)
        # Revision5 has an explicit typed policy too: broadening current Q0 cannot
        # silently change the frozen old quest interpretation in its wire bank.
        install(self.broad, image(good))
        before = bytes(self.broad.sram)
        self.assertEqual(self.broad.save5_begin(C.byref(s)), 1)
        self.assertEqual(finish(self.broad), FAILED)
        self.assertEqual(self.broad.save5_test_write_count(), 0)
        self.assertEqual(bytes(self.broad.sram), before)

    def test_streamed_old_bank_selection_and_migration_use_exact_policy(self):
        good, s = self.minimal_bank()
        bad = bytearray(good)
        bad[4048:4050] = (8).to_bytes(2, 'little')
        bad[8:12] = (18).to_bytes(4, 'little')
        bad = repair_crc(bad)
        for lib in (self.base, self.broad):
            with self.subTest(library=lib._name):
                data = image(good, bad)
                install(lib, data)
                loaded = Save()
                self.assertEqual(lib.save5_has_valid(), 1)
                self.assertEqual(lib.save5_load(C.byref(loaded)), 1)
                self.assertEqual(loaded.quests.objectives[0], 1)
                self.assertEqual(loaded.campaign.sequence, 17)
                self.assertEqual(lib.save5_validate_revision(C.byref(loaded), 2), 1)
                self.assertEqual(lib.save5_begin(C.byref(loaded)), 1)
                self.assertEqual(finish(lib), DONE)
                self.assertEqual(bytes(lib.sram[A:A+SIZE]), good)
                migrated = bytes(lib.sram[B:B+SIZE])
                self.assertEqual(int.from_bytes(migrated[8:12], 'little'), 18)
                self.assertEqual(migrated[12:14], b'\x05\0')
                self.assertEqual(migrated[32:], good[32:])
                self.assertEqual(lib.save5_test_write_count(), 6145)
                self.assertEqual(lib.save5_load(C.byref(loaded)), 1)
                self.assertEqual(loaded.quests.objectives[0], 1)

    def test_current_narrowing_does_not_reject_historical_load(self):
        data = (ROOT / 'tests/fixtures/v5-revision2/all-eleven-town.sav').read_bytes()
        expected = Save()
        install(self.base, data)
        self.assertEqual(self.base.save5_load(C.byref(expected)), 1)
        for lib in (self.narrow, self.gates):
            install(lib, data)
            actual = Save()
            self.assertEqual(lib.save5_has_valid(), 1)
            self.assertEqual(lib.save5_load(C.byref(actual)), 1)
            self.assertEqual(compare_state(actual), compare_state(expected))
            self.assertEqual(lib.save5_validate_revision(C.byref(actual), 2), 1)
            self.assertEqual(bytes(lib.sram), data)
        self.assertEqual(self.narrow.save5_validate(C.byref(actual)), 0)
        self.assertEqual(self.narrow.save5_begin(C.byref(actual)), 1)
        self.assertEqual(finish(self.narrow), FAILED)
        self.assertEqual(self.narrow.save5_test_write_count(), 0)
        self.assertEqual(bytes(self.narrow.sram), data)

    def test_historical_variable_gate_room_and_sourcequest_are_independent(self):
        for fixture in sorted((ROOT / 'tests/fixtures').glob('v5-revision*/*.sav')):
            data = fixture.read_bytes()
            expected = Save()
            install(self.base, data)
            self.assertEqual(self.base.save5_load(C.byref(expected)), 1)
            actual = Save()
            install(self.gates, data)
            self.assertEqual(self.gates.save5_load(C.byref(actual)), 1)
            self.assertEqual(compare_state(actual), compare_state(expected))
        good, s = self.minimal_bank()
        # State/variable values that a future current policy explicitly allows
        # still cannot enter a released revision through either scan path.
        s.quests.states[0] |= 1 << 6
        s.quests.variables[3] = 4
        self.assertEqual(self.gates.save5_validate(C.byref(s)), 1)
        bank = bytearray(good)
        bank[4032] |= 1 << 6
        bank[4187] = 4
        install(self.gates, image(repair_crc(bank)))
        self.assertEqual(self.gates.save5_has_valid(), 0)
        self.assertEqual(self.gates.save5_begin(C.byref(s)), 1)
        self.assertEqual(finish(self.gates), FAILED)
        self.assertEqual(self.gates.save5_test_write_count(), 0)
        # Source1/item2 used to belong to Q7. Swapping its live Q0 mapping may
        # not admit a source1 claim for Q0 with no Q7 claim.
        bank = bytearray(good)
        bank[4032] = 3
        bank[4048:4050] = (7).to_bytes(2, 'little')
        bank[4176] = 1
        bank[4944] |= 4  # seen item2
        bank[5024] |= 2  # source1 claimed
        install(self.gates, image(repair_crc(bank)))
        self.assertEqual(self.gates.save5_has_valid(), 0)
        s.quests.states[0] = 3
        s.quests.variables[3] = 0
        s.quests.objectives[0] = 7
        s.quests.rewards[0] = 1
        s.equipment.seen[0] |= 4
        s.equipment.reward_claims[0] |= 2
        self.assertEqual(self.gates.save5_validate(C.byref(s)), 1)
        self.assertEqual(self.base.save5_validate(C.byref(s)), 0)
        self.assertEqual(self.gates.save5_begin(C.byref(s)), 1)
        self.assertEqual(finish(self.gates), FAILED)
        self.assertEqual(self.gates.save5_test_write_count(), 0)
        # A legal historical town return spawn cannot be narrowed by today's
        # campaign public validator after its exact historical scan passed.
        bank = bytearray(good)
        bank[32:34] = bytes((16, 5))
        install(self.gates, image(repair_crc(bank)))
        loaded = Save()
        self.assertEqual(self.gates.save5_load(C.byref(loaded)), 1)
        self.assertEqual((loaded.campaign.room, loaded.campaign.spawn), (16, 5))
        self.assertEqual(self.gates.save5_validate(C.byref(loaded)), 0)

    def test_removed_current_command_survives_load_without_unsafe_resave(self):
        bank, unused = self.minimal_bank()
        for revision in (1, 2, 3, 4):
            with self.subTest(revision=revision):
                source = bytearray(bank)
                source[12:14] = revision.to_bytes(2, 'little')
                if revision == 1:
                    source[4032:4296] = bytes(264)
                    source[4544:5056] = bytes(512)
                data = image(repair_crc(source))
                expected = Save()
                install(self.base, data)
                self.assertEqual(self.base.save5_load(C.byref(expected)), 1)
                actual = Save()
                install(self.command, data)
                self.assertEqual(self.command.save5_load(C.byref(actual)), 1)
                self.assertEqual(self.command.save5_has_valid(), 1)
                self.assertEqual(compare_state(actual), compare_state(expected))
                self.assertEqual(actual.roster.instances[0].equipped[0], 1)
                self.assertEqual(self.command.save5_validate_revision(C.byref(actual), revision), 1)
                self.assertEqual(self.command.save5_validate(C.byref(actual)), 0)
                self.assertEqual(self.command.save5_store(C.byref(actual)), 0)
                self.assertEqual(self.command.save5_status(), FAILED)
                self.assertEqual(self.command.save5_test_write_count(), 0)
                self.assertEqual(bytes(self.command.sram), data)
                self.assertEqual(compare_state(actual), compare_state(expected))

    def test_revision1_migration_exception_is_only_decoded_canonical_starter(self):
        data = (ROOT / 'tests/fixtures/v5-revision1/all-evolved-village.sav').read_bytes()
        install(self.base, data)
        loaded = Save()
        self.assertEqual(self.base.save5_load(C.byref(loaded)), 1)
        self.assertEqual(self.base.save5_validate_revision(C.byref(loaded), 1), 1)
        loaded.equipment.reward_claims[0] = 0
        self.assertEqual(self.base.save5_validate_revision(C.byref(loaded), 1), 0)
        for revision in (0, 6, 0xffffffff):
            self.assertEqual(self.base.save5_validate_revision(C.byref(loaded), revision), 0)
        self.assertEqual(C.sizeof(loaded.roster.instances[0]), 24)
        self.assertEqual(len(loaded.roster.instances), 160)
        self.assertEqual(SIZE, 6144)
        self.assertEqual((A, B), (0x200, 0x1a00))


if __name__ == '__main__':
    unittest.main(verbosity=2)
