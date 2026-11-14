#!/usr/bin/env python3
"""Persistent personal events survive current saves; old adventures gain none.
Synthetic codec tests, not controller-earned romance scene evidence.
"""
import ctypes as C
import itertools
import unittest
from test_save5 import Save5Tests, Save, A, B, SIZE, repair_crc, compare_state
from test_save5_load_job import LoadJobTests


class RelationshipSaveTests(unittest.TestCase):
    reset = Save5Tests.reset
    fresh = Save5Tests.fresh
    store = Save5Tests.store
    put = Save5Tests.put
    run_reader = LoadJobTests.run_reader

    @classmethod
    def setUpClass(cls):
        LoadJobTests.setUpClass.__func__(cls)
        cls.lib.save5_validate_revision.argtypes = [C.POINTER(Save), C.c_uint]
        cls.lib.save5_preflight_status.argtypes = [C.c_uint]
        cls.lib.save5_preflight_step.argtypes = [C.c_uint, C.c_uint]
        cls.lib.save5_preflight_matches.argtypes = [C.c_uint, C.POINTER(Save)]

    def setUp(self):
        self.reset()
        self.lib.save5_load_cancel()
        self.lib.save5_preflight_cancel()

    def test_all_legal_relationship_combinations_roundtrip(self):
        for events in itertools.product((0, 1, 3, 7, 15, 31), repeat=4):
            s = self.fresh()
            s.relationships[:] = events
            self.store(s)
            got = Save()
            self.assertEqual(self.lib.save5_load(C.byref(got)), 1)
            self.assertEqual(compare_state(got), compare_state(s))
        self.assertEqual(bytes(got.relationships), bytes([31] * 4))

    def test_current_wire_rejects_every_invalid_relationship_byte_atomically(self):
        s = self.fresh(); self.store(s)
        original = bytes(self.sram[A:A+SIZE])
        for person in range(4):
            for value in range(256):
                bank = bytearray(original); bank[5088+person] = value
                self.reset(); self.put(repair_crc(bank), A)
                before = bytes(self.sram)
                got = Save.from_buffer_copy(b'\xcc' * C.sizeof(Save))
                accepted = value in (0, 1, 3, 7, 15, 31)
                self.assertEqual(self.lib.save5_load(C.byref(got)), int(accepted))
                if accepted:
                    self.assertEqual(got.relationships[person], value)
                else:
                    self.assertEqual(bytes(got), b'\xcc' * C.sizeof(Save))
                self.assertEqual(bytes(self.sram), before)

    def test_revision12_migration_never_awards_relationship_events(self):
        s = self.fresh(); self.store(s)
        bank = bytearray(self.sram[A:A+SIZE])
        bank[12:14] = (12).to_bytes(2, 'little')
        bank[6:8] = (5088).to_bytes(2, 'little')
        self.reset(); self.put(repair_crc(bank), A)
        got = Save()
        self.assertEqual(self.lib.save5_load(C.byref(got)), 1)
        self.assertEqual(bytes(got.relationships), bytes(4))
        self.assertEqual(self.run_reader()[0], 1)
        for person in range(4):
            bad = bytearray(bank); bad[5088+person] = 1
            self.reset(); self.put(repair_crc(bad), A)
            self.assertEqual(self.run_reader()[0], 0)
            s.relationships[person] = 1
            self.assertEqual(self.lib.save5_validate_revision(C.byref(s), 12), 0)
            s.relationships[person] = 0

    def test_incremental_read_preserves_events_and_rejects_bad_newest_bank(self):
        old = self.fresh(); old.relationships[:] = [1, 3, 7, 15]; self.store(old)
        new = Save.from_buffer_copy(bytes(old)); new.relationships[:] = [31] * 4
        self.store(new)
        image = bytes(self.sram)
        for budget in (1, 17, 1024, 0xffffffff):
            self.reset(); self.put(image)
            self.assertEqual(self.run_reader(budget)[0], 1)
        bad = bytearray(image)
        bad[B+5088] = 2
        bad[B:B+SIZE] = repair_crc(bad[B:B+SIZE])
        self.reset(); self.put(bad)
        got = Save(); self.assertEqual(self.lib.save5_load(C.byref(got)), 1)
        self.assertEqual(compare_state(got), compare_state(old))
        self.assertEqual(self.run_reader()[0], 1)

    def test_invalid_runtime_state_never_reaches_sram(self):
        s = self.fresh(); s.relationships[0] = 2
        before = bytes(self.sram)
        self.assertEqual(self.lib.save5_validate(C.byref(s)), 0)
        self.assertEqual(self.lib.save5_store(C.byref(s)), 0)
        self.assertEqual(bytes(self.sram), before)
        self.lib.save5_test_reset_writer()
        token = self.lib.save5_preflight_begin(C.byref(s))
        self.assertTrue(token)
        for _ in range(1000):
            if self.lib.save5_preflight_status(token) != 1:
                break
            self.lib.save5_preflight_step(token, 1024)
        self.assertEqual(self.lib.save5_preflight_status(token), 3)
        self.assertEqual(bytes(self.sram), before)

    def test_preflight_includes_relationships_in_exact_snapshot_match(self):
        s = self.fresh(); s.relationships[:] = [31, 15, 7, 3]
        token = self.lib.save5_preflight_begin(C.byref(s))
        self.assertTrue(token)
        for _ in range(1000):
            if self.lib.save5_preflight_status(token) != 1:
                break
            self.lib.save5_preflight_step(token, 1024)
        self.assertEqual(self.lib.save5_preflight_status(token), 2)
        self.assertEqual(self.lib.save5_preflight_matches(token, C.byref(s)), 1)
        s.relationships[3] = 7
        self.assertEqual(self.lib.save5_preflight_matches(token, C.byref(s)), 0)
        self.lib.save5_preflight_cancel()

    def test_every_cut_preserves_old_or_complete_relationship_ledger(self):
        old = self.fresh(); old.relationships[:] = [1, 3, 7, 15]
        self.store(old); image = bytes(self.sram)
        new = Save.from_buffer_copy(bytes(old)); new.relationships[:] = [31] * 4
        self.store(new); writes = self.lib.save5_test_write_count()
        self.assertGreater(writes, SIZE)
        for cut in range(writes + 1):
            self.reset(); self.put(image)
            self.lib.save5_test_fail_after(cut)
            self.lib.save5_store(C.byref(new))
            self.lib.save5_test_reset_writer()
            self.lib.save5_test_fail_after(-1)
            got = Save()
            self.assertEqual(self.lib.save5_load(C.byref(got)), 1, cut)
            self.assertIn(compare_state(got), (compare_state(old), compare_state(new)), cut)


if __name__ == '__main__':
    unittest.main(defaultTest='RelationshipSaveTests')
