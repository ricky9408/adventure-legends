#!/usr/bin/env python3
"""Bounded read parity, atomicity, interruption and historical migration.

Fixtures are codec/controller-history inputs, not new campaign play evidence.
No SRAM write occurs before, during or after a reader job.
"""
import ctypes as C
from pathlib import Path
import unittest
from test_save5 import Save5Tests, Save, ROOT, A, B, SIZE, BUSY, DONE, FAILED, repair_crc, compare_state


class LoadJobTests(unittest.TestCase):
    reset = Save5Tests.reset
    fresh = Save5Tests.fresh
    store = Save5Tests.store
    put = Save5Tests.put

    @classmethod
    def setUpClass(cls):
        Save5Tests.setUpClass.__func__(cls)
        cls.lib.save5_load_begin.argtypes = [C.POINTER(Save)]
        cls.lib.save5_load_begin.restype = C.c_int
        cls.lib.save5_load_step.argtypes = [C.c_uint]
        cls.lib.save5_load_step.restype = C.c_uint
        cls.lib.save5_preflight_begin.argtypes = [C.POINTER(Save)]
        cls.lib.save5_preflight_begin.restype = C.c_uint

    def setUp(self):
        self.reset()

    def run_reader(self, budget=1024, probe=False):
        before = bytes(self.sram)
        output = Save.from_buffer_copy(b'\xcc' * C.sizeof(Save))
        expected = Save.from_buffer_copy(bytes(output))
        accepted = self.lib.save5_load(C.byref(expected))
        self.assertEqual(self.lib.save5_load_begin(None if probe else C.byref(output)), 1)
        previous = self.lib.save5_load_progress()
        self.assertEqual(self.lib.save5_load_step(0), BUSY)
        self.assertEqual(self.lib.save5_test_step_work(), 0)
        self.assertEqual(self.lib.save5_load_progress(), previous)
        calls = 0
        while self.lib.save5_load_status() == BUSY:
            self.assertEqual(bytes(output), b'\xcc' * C.sizeof(Save))
            status = self.lib.save5_load_step(budget)
            self.assertLessEqual(self.lib.save5_test_step_work(), min(budget, 1024))
            calls += 1
            self.assertLess(calls, 100000)
            progress = self.lib.save5_load_progress()
            self.assertGreaterEqual(progress, previous)
            self.assertLessEqual(progress, self.lib.save5_load_progress_total())
            previous = progress
            self.assertEqual(bytes(self.sram), before)
        self.assertEqual(status, DONE if accepted else FAILED)
        if probe or not accepted:
            self.assertEqual(bytes(output), b'\xcc' * C.sizeof(Save))
        elif expected.campaign.loaded_version < 5:
            # Unmodified v2/v3/v4 decoder has unspecified C struct padding;
            # compare every named field and all roster/quest/gear/economy bytes.
            self.assertEqual(compare_state(output), compare_state(expected))
        else:
            self.assertEqual(bytes(output), bytes(expected))
        self.assertEqual(bytes(self.sram), before)
        return accepted, calls

    def test_current_and_empty_budget_edges(self):
        self.store(self.fresh(3, 2))
        image = bytes(self.sram)
        for budget in (1, 17, 512, 1024, 0xffffffff):
            with self.subTest(budget=budget):
                self.reset(); self.put(image)
                self.assertEqual(self.run_reader(budget)[0], 1)
                self.assertEqual(self.run_reader(budget, probe=True)[0], 1)
        self.reset()
        self.assertEqual(self.run_reader()[0], 0)

    def test_all_shipped_save_images_match_blocking(self):
        count = 0
        for path in sorted((ROOT / 'tests/fixtures').rglob('*.sav')):
            image = path.read_bytes()
            if len(image) != 32768:
                continue
            with self.subTest(fixture=str(path.relative_to(ROOT))):
                self.reset(); self.put(image); self.run_reader()
            count += 1
        self.assertGreater(count, 20)
        print('Compared bounded reader with blocking decoder for', count, 'shipped SRAM images')

    def test_every_interruption_preserves_output_and_sram(self):
        self.store(self.fresh(3, 2)); image = bytes(self.sram)
        # Interrupt at every individual budgeted slice, not merely phase ends.
        _, calls = self.run_reader(512)
        for cut in range(calls):
            self.reset(); self.put(image)
            output = Save.from_buffer_copy(b'\xcc' * C.sizeof(Save))
            self.assertEqual(self.lib.save5_load_begin(C.byref(output)), 1)
            for _ in range(cut):
                self.assertEqual(self.lib.save5_load_step(512), BUSY)
            self.lib.save5_load_cancel()
            self.assertEqual(bytes(output), b'\xcc' * C.sizeof(Save))
            self.assertEqual(bytes(self.sram), image)
            self.assertEqual(self.lib.save5_load_status(), 0)
            self.assertEqual(self.run_reader()[0], 1)

    def test_reader_excludes_scratch_owners_and_blocking_reads(self):
        s = self.fresh(); self.store(s); output = Save()
        self.assertEqual(self.lib.save5_load_begin(C.byref(output)), 1)
        self.assertEqual(self.lib.save5_load_begin(C.byref(output)), 0)
        self.assertEqual(self.lib.save5_begin(C.byref(s)), 0)
        self.assertEqual(self.lib.save5_preflight_begin(C.byref(s)), 0)
        self.assertEqual(self.lib.save5_load(C.byref(output)), 0)
        self.assertEqual(self.lib.save5_has_valid(), 0)
        while self.lib.save5_load_step(1024) == BUSY:
            pass
        self.assertEqual(self.lib.save5_begin(C.byref(output)), 1)
        self.assertEqual(self.lib.save5_load_begin(C.byref(output)), 0)
        self.lib.save5_test_reset_writer()
        token = self.lib.save5_preflight_begin(C.byref(s))
        self.assertNotEqual(token, 0)
        self.assertEqual(self.lib.save5_load_begin(C.byref(output)), 0)
        self.lib.save5_preflight_cancel()
        self.assertEqual(self.lib.save5_load_begin(C.byref(output)), 1)

    def test_crc_valid_corruption_and_newest_bank_fallback(self):
        s = self.fresh(3, 2); self.store(s); self.store(s)
        image = bytes(self.sram)
        for offset in (2, 12, 32, 96, 160, 4010, 4032, 4544, 5056, 5088, 6143):
            corrupt = bytearray(image)
            for bank in (A, B):
                body = bytearray(corrupt[bank:bank+SIZE]); body[offset] ^= 0x80
                corrupt[bank:bank+SIZE] = repair_crc(body)
            self.reset(); self.put(corrupt)
            self.run_reader()
        corrupt = bytearray(image); corrupt[B+5088] = 1
        self.reset(); self.put(corrupt)
        self.assertEqual(self.run_reader()[0], 1)

    def test_revision11_wallet_is_immutable_and_revision12_ack_survives(self):
        s = self.fresh(3, 2)
        self.store(s)
        old = bytearray(self.sram)
        old[A+12:A+14] = (11).to_bytes(2, 'little')
        old[A:A+SIZE] = repair_crc(old[A:A+SIZE])
        self.reset(); self.put(old)
        self.assertEqual(self.run_reader()[0], 1)
        # A prior save cannot carry future story acknowledgement or paid gear.
        for reserved_offset, value in ((5080, 1), (5081, 3)):
            bad = bytearray(old)
            bad[A+reserved_offset] = value
            bad[A:A+SIZE] = repair_crc(bad[A:A+SIZE])
            self.reset(); self.put(bad)
            self.assertEqual(self.run_reader()[0], 0)
        self.reset(); s.economy.reserved[1] = 3; self.store(s)
        self.assertEqual(self.run_reader()[0], 1)


if __name__ == '__main__':
    unittest.main(defaultTest='LoadJobTests')
