#!/usr/bin/env python3
"""A revoked chapter job must not cancel a later admission owner."""
import ctypes as C
import tempfile
import unittest

from horizons_host_support import (
    BUSY, DONE, FAILED, Request, Roster, Save, build, generation, main, move,
)


class PreflightOwnership(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='horizons-ownership-')
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.lib = build(cls.tmp.name)
        cls.lib.save5_preflight_snapshot.restype = C.POINTER(Save)
        cls.lib.creatures_admission_job_begin.argtypes = [
            C.POINTER(Roster), C.c_uint, C.c_uint,
        ]

    def setUp(self):
        self.s = main(self.lib)
        move(self.lib, self.s, 64)
        request = Request(operation=7, source=6, family=46, room=64)
        self.scene = generation()
        self.old = self.lib.horizons_job_begin(
            C.byref(self.s), C.byref(request), self.scene, 1)
        self.assertTrue(self.old)
        while self.lib.horizons_job_phase(self.old) != 3:
            self.assertEqual(self.lib.horizons_job_step(
                self.old, 1024, self.scene, 1), BUSY)
        self.before = bytes(self.s)

    def tearDown(self):
        self.lib.horizons_job_cancel()
        self.lib.creatures_admission_job_cancel()
        self.lib.save5_preflight_cancel()

    def acquire_new_owner_after_load(self):
        self.loaded = Save()
        self.assertEqual(self.lib.save5_load(C.byref(self.loaded)), 1)
        self.assertEqual(self.lib.save5_preflight_status(self.old), FAILED)
        self.new = self.lib.save5_preflight_begin(C.byref(self.loaded))
        self.assertTrue(self.new)
        status = BUSY
        while status == BUSY:
            status = self.lib.save5_preflight_step(self.new, 1024)
        self.assertEqual(status, DONE)
        snapshot = self.lib.save5_preflight_snapshot(self.new)
        self.admission = self.lib.creatures_admission_job_begin(
            C.byref(snapshot.contents.roster), 105, 255)
        self.assertTrue(self.admission)
        self.assertEqual(self.lib.creatures_admission_job_step(self.admission, 4), 0)
        self.loaded_before = bytes(self.loaded)

    def assert_new_owner_survives(self):
        self.assertEqual(self.lib.save5_preflight_status(self.new), DONE)
        result = 0
        for _ in range(40):
            result = self.lib.creatures_admission_job_step(self.admission, 4)
            if result:
                break
        self.assertEqual(result, 1, 'Stale chapter cleanup canceled the newer admission')
        self.assertEqual(self.lib.creatures_admission_job_result(self.admission, None), 0)
        self.assertEqual(bytes(self.s), self.before)
        self.assertEqual(bytes(self.loaded), self.loaded_before)

    def test_stale_explicit_cancel_preserves_new_owner(self):
        self.acquire_new_owner_after_load()
        self.lib.horizons_job_cancel()
        self.assert_new_owner_survives()

    def test_stale_step_failure_preserves_new_owner(self):
        self.acquire_new_owner_after_load()
        self.assertEqual(self.lib.horizons_job_step(
            self.old, 1024, self.scene, 1), FAILED)
        self.assert_new_owner_survives()

    def test_owned_cancel_releases_preflight_without_mutation(self):
        self.lib.horizons_job_cancel()
        self.assertEqual(self.lib.save5_preflight_status(self.old), FAILED)
        self.assertEqual(bytes(self.s), self.before)
        self.assertTrue(self.lib.save5_preflight_begin(C.byref(self.s)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
