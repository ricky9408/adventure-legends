#!/usr/bin/env python3
"""New art must retain cartridge layout and reject unreviewed pixel changes."""
from contextlib import contextmanager
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'assets'))
from legacy_art_successor import validate_legacy_prefix, sha
from redesign_art_guard import CONTRACT_PATH, SUCCESSOR_ID

CONTRACTS = [f'assets/{name}/legacy_prefix_sha256.json'
             for name in ('underwater_creatures', 'return_creatures')]


class RedesignArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='emberbond-art-review-')
        cls.root = Path(cls.temporary.name)
        cls.contract = json.loads((ROOT / CONTRACT_PATH).read_text())
        paths = {CONTRACT_PATH, 'assets/connected_roads_legacy_art_contract.json',
                 *cls.contract['base_asset_parts'], *cls.contract['authoring_sources']}
        for relative in CONTRACTS:
            paths.add(relative)
            paths.update(json.loads((ROOT / relative).read_text())['sha256'])
        for relative in paths:
            if (ROOT / relative).is_file():
                target = cls.root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def verify(self, relative=CONTRACTS[1]):
        return validate_legacy_prefix(self.root, self.root / relative, SUCCESSOR_ID)

    @contextmanager
    def edit(self, relative, value):
        path = self.root / relative
        before = path.read_bytes() if path.exists() else None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        try:
            yield
        finally:
            if before is None:
                path.unlink()
            else:
                path.write_bytes(before)

    def test_explicit_art_selection_retains_palette_and_memory_layout(self):
        for relative in CONTRACTS:
            with self.subTest(relative=relative):
                result = self.verify(relative)
                self.assertTrue(result['shared_palette_and_array_layout_unchanged'])
                self.assertFalse(result['unchanged'])
                with self.assertRaises(AssertionError):
                    validate_legacy_prefix(self.root, self.root / relative)
                with self.assertRaises(AssertionError):
                    validate_legacy_prefix(self.root, self.root / relative, 'connected-roads-c4')

    def test_protected_companion_pixels_and_historical_contracts_are_rejected(self):
        for relative in ('src/underwater_creature_art_data/part_000.inc', CONTRACTS[1]):
            with self.subTest(relative=relative):
                with self.edit(relative, (self.root / relative).read_bytes() + b'\n'):
                    with self.assertRaises(AssertionError):
                        self.verify()

    def test_extra_chunks_and_unreviewed_authoring_are_rejected(self):
        with self.edit('src/asset_data/part_999.inc', b'\n'):
            with self.assertRaisesRegex(AssertionError, 'Unexpected base art chunks'):
                self.verify()
        relative = 'assets/redesign_characters.py'
        with self.edit(relative, (self.root / relative).read_bytes() + b'\n'):
            with self.assertRaisesRegex(AssertionError, 'Unreviewed art authoring'):
                self.verify()

    def test_palette_changes_fail_even_after_a_chunk_hash_is_refreshed(self):
        relative = self.contract['base_asset_parts'][0]
        original = (self.root / relative).read_text()
        match = re.search(r'game_palette\[[^]]+\]\s*=\s*\{\s*(\d+)', original)
        self.assertIsNotNone(match)
        changed = original[:match.start(1)] + str((int(match[1]) + 1) % 32768) + original[match.end(1):]
        contract = json.loads((self.root / CONTRACT_PATH).read_text())
        for contract_relative, rule in contract['historical_contracts'].items():
            historical = json.loads((self.root / contract_relative).read_text())
            if relative in historical['sha256']:
                rule['reviewed_exceptions'][relative] = {
                    'historical_sha256': historical['sha256'][relative],
                    'successor_sha256': sha(changed.encode())}
        with self.edit(relative, changed.encode()), self.edit(CONTRACT_PATH, json.dumps(contract).encode()):
            with self.assertRaisesRegex(AssertionError, 'Unreviewed art pixels'):
                self.verify()

    def test_shared_palette_cannot_be_declared_replaceable(self):
        contract = json.loads((self.root / CONTRACT_PATH).read_text())
        contract['reviewed_arrays'].append('game_palette')
        with self.edit(CONTRACT_PATH, json.dumps(contract).encode()):
            with self.assertRaisesRegex(AssertionError, 'Shared palette is protected'):
                self.verify()


if __name__ == '__main__':
    unittest.main()
