#!/usr/bin/env python3
"""Keep historical reconstruction independent of later checkout housekeeping."""
import base64
import copy
import gzip
import json
from pathlib import Path
import stat
import unittest
from unittest.mock import patch

import selected_music_boundary as boundary


class HistoricalSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = boundary.load()
        boundary.authenticate(cls.contract, boundary.state(cls.contract))
        cls.packed = (boundary.ROOT / boundary.INVERSE_PATH).read_bytes()
        cls.entries = json.loads(gzip.decompress(cls.packed))
        cls.historical_ignore = base64.b64decode(cls.entries['.gitignore'], validate=True)
        assert boundary.sha(cls.historical_ignore) == cls.contract['parent_files']['.gitignore']

    def test_independent_from_live_gitignore(self):
        original_read = Path.read_bytes
        live_ignore = boundary.ROOT / '.gitignore'
        live_reads = []

        def read_bytes(path):
            if path == live_ignore:
                live_reads.append(path)
                return b'# Later checkout housekeeping\n.DS_Store\nfuture-cache/\n'
            return original_read(path)

        with patch.object(Path, 'read_bytes', read_bytes):
            with boundary.parent_view(self.contract) as view:
                files = {p.relative_to(view).as_posix(): p.read_bytes()
                         for p in view.rglob('*') if p.is_file()}
                modes = {p.relative_to(view).as_posix():
                         f'100{stat.S_IMODE(p.stat().st_mode):03o}'
                         for p in view.rglob('*') if p.is_file()}
                self.assertEqual(files['.gitignore'], self.historical_ignore)
                self.assertEqual({k: boundary.sha(v) for k, v in files.items()},
                                 self.contract['parent_files'])
                self.assertEqual(modes, self.contract['parent_modes'])
                self.assertEqual(boundary.prior.git_tree(files, modes),
                                 self.contract['parent_tree'])
        self.assertEqual(live_reads, [], 'historical reconstruction read live .gitignore')

    def assert_rejected(self, packed, contract, message):
        original_read = Path.read_bytes
        archive = boundary.ROOT / boundary.INVERSE_PATH

        def read_bytes(path):
            return packed if path == archive else original_read(path)

        with patch.object(Path, 'read_bytes', read_bytes):
            with self.assertRaisesRegex(AssertionError, message):
                with boundary.parent_view(contract):
                    self.fail('accepted corrupted historical reconstruction')

    def corrupted_entry(self):
        entries = dict(self.entries)
        corrupted = self.historical_ignore + b'\ncorrupted-history/\n'
        entries['.gitignore'] = base64.b64encode(corrupted).decode('ascii')
        packed = gzip.compress(json.dumps(entries, sort_keys=True, separators=(',', ':')).encode(),
                               mtime=0)
        contract = copy.deepcopy(self.contract)
        contract['inverse_sha256'] = boundary.sha(packed)
        return packed, contract, corrupted

    def test_archive_hash_rejects_tampering(self):
        self.assert_rejected(self.packed + b'corruption', self.contract,
                             'selected music inverse changed')

    def test_entry_hash_rejects_tampering_after_archive_repin(self):
        packed, contract, _ = self.corrupted_entry()
        self.assert_rejected(packed, contract, 'inverse byte set changed')

    def test_parent_hash_rejects_tampering_after_entry_repin(self):
        packed, contract, corrupted = self.corrupted_entry()
        contract['inverse_files_sha256']['.gitignore'] = boundary.sha(corrupted)
        self.assert_rejected(packed, contract, 'parent bytes changed')

    def test_tree_rejects_tampering_after_parent_repin(self):
        packed, contract, corrupted = self.corrupted_entry()
        contract['inverse_files_sha256']['.gitignore'] = boundary.sha(corrupted)
        contract['parent_files']['.gitignore'] = boundary.sha(corrupted)
        self.assert_rejected(packed, contract, 'not the exact previous main tree')


if __name__ == '__main__':
    unittest.main()
