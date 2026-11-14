#!/usr/bin/env python3
"""Relationship milestones: consent events, replay safety and independent partners.
This is a host-core test, not a playable scene or save migration claim.
"""
import ctypes as C
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class State(C.Structure):
    _fields_ = [('events', C.c_ubyte * 4)]


class RelationshipsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='emberbond-relationships-')
        cls.addClassCleanup(cls.tmp.cleanup)
        lib = Path(cls.tmp.name) / 'relationships.so'
        flags = ['-fsanitize=undefined', '-fno-sanitize-recover=all'] if os.getenv('RELATIONSHIPS_SANITIZE') else []
        subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-shared', '-fPIC', *flags, str(ROOT / 'src/relationships.c'),
                        '-o', str(lib)], check=True)
        cls.core = C.CDLL(str(lib))
        cls.core.relationships_valid.argtypes = [C.POINTER(State)]
        cls.core.relationships_affinity.argtypes = [C.POINTER(State), C.c_uint]
        cls.core.relationships_stage.argtypes = [C.POINTER(State), C.c_uint]
        cls.core.relationships_record.argtypes = [C.POINTER(State), C.c_uint, C.c_uint]

    def test_friendship_never_automatically_becomes_romance(self):
        for person in range(4):
            s = State()
            stages = [1, 2, 2, 3, 4]
            affinity = [10, 30, 60, 60, 60]
            for event, stage in enumerate(stages):
                self.assertEqual(self.core.relationships_record(C.byref(s), person, event), 1)
                self.assertEqual(self.core.relationships_stage(C.byref(s), person), stage)
                self.assertEqual(self.core.relationships_affinity(C.byref(s), person), affinity[event])
                self.assertEqual(self.core.relationships_valid(C.byref(s)), 1)
                before = bytes(s)
                for _ in range(20):
                    self.assertEqual(self.core.relationships_record(C.byref(s), person, event), 0)
                self.assertEqual(bytes(s), before)

    def test_all_byte_states_and_events_have_atomic_bounded_transitions(self):
        valid = [0, 1, 3, 7, 15, 31]
        for person in range(4):
            for value in range(256):
                for event in range(7):
                    s = State()
                    s.events[person] = value
                    before = bytes(s)
                    self.assertEqual(self.core.relationships_valid(C.byref(s)), int(value in valid))
                    expected = event < 5 and value == (1 << event) - 1
                    self.assertEqual(self.core.relationships_record(C.byref(s), person, event), int(expected))
                    if expected:
                        self.assertEqual(s.events[person], value | (1 << event))
                        self.assertEqual(bytes(s)[:person], before[:person])
                        self.assertEqual(bytes(s)[person+1:], before[person+1:])
                    else:
                        self.assertEqual(bytes(s), before)

    def test_existing_marriages_never_block_another_independent_route(self):
        s = State()
        for person in [2, 0, 3, 1]:
            for event in range(5):
                self.assertEqual(self.core.relationships_record(C.byref(s), person, event), 1)
            self.assertEqual(self.core.relationships_stage(C.byref(s), person), 4)
        self.assertEqual(bytes(s), bytes([31] * 4))

    def test_invalid_inputs_do_not_change_any_route(self):
        s = State()
        for person, event in [(4, 0), (0xffffffff, 0), (0, 5), (0, 0xffffffff)]:
            self.assertEqual(self.core.relationships_record(C.byref(s), person, event), 0)
            self.assertEqual(bytes(s), bytes(4))
        s.events[3] = 255
        self.assertEqual(self.core.relationships_record(C.byref(s), 0, 0), 0)
        self.assertEqual(bytes(s), bytes([0, 0, 0, 255]))
        self.assertEqual(self.core.relationships_valid(None), 0)
        self.assertEqual(self.core.relationships_record(None, 0, 0), 0)
        self.assertEqual(self.core.relationships_stage(None, 0), 0)
        self.assertEqual(self.core.relationships_stage(C.byref(s), 4), 0)


if __name__ == '__main__':
    unittest.main()
