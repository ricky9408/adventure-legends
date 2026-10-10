#!/usr/bin/env python3
"""Real kernel overlap rejection; no game or physical GBA claim."""
import contextlib
import ctypes as C
import errno
import io
import json
import subprocess
import unittest
import player_feedback_host_mapping as helper


class ProtectedMapping(unittest.TestCase):
    def test_occupied_mapping_is_retained_and_never_retried(self):
        libc = C.CDLL(None, use_errno=True)
        libc.mmap.argtypes = [C.c_void_p, C.c_size_t, C.c_int, C.c_int, C.c_int, C.c_long]
        libc.mmap.restype = C.c_void_p
        libc.munmap.argtypes = [C.c_void_p, C.c_size_t]
        address = libc.mmap(None, helper.LENGTH, 3, 0x22, -1, 0)
        self.assertNotIn(address, (None, C.c_void_p(-1).value))
        old = helper.ADDRESSES
        try:
            memory = (C.c_ubyte * helper.LENGTH).from_address(address)
            sentinel = bytes((i * 17 + 29) % 256 for i in range(helper.LENGTH))
            memory[:] = sentinel
            helper.ADDRESSES = (address,)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
                helper.reserve_gba_pages()
            self.assertEqual(error.exception.code, 78)
            self.assertEqual(bytes(memory), sentinel, 'NOREPLACE must preserve every occupied byte')
            line = stderr.getvalue().strip()
            self.assertTrue(line.startswith(helper.policy.PREFIX))
            detail = json.loads(line[len(helper.policy.PREFIX):])
            self.assertEqual(detail['errno'], errno.EEXIST)
            self.assertTrue(detail['pre_map_overlaps'])
            self.assertFalse(detail['game_assertions_started'])
            self.assertFalse(detail['overwritten_mappings'])
            result = subprocess.CompletedProcess([], 78, '', stderr.getvalue())
            self.assertIsNone(helper.policy.collision_detail(result), 'Unknown/non-heap collisions are never retryable')
        finally:
            helper.ADDRESSES = old
            self.assertEqual(libc.munmap(address, helper.LENGTH), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
