#!/usr/bin/env python3
"""Portable positive and in-memory/export-copy negative tests; originals untouched."""
import binascii
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
VERIFIER = runpy.run_path(str(HERE / 'verify_fixture.py'))


def repaired(raw, relative_offset, value):
    """Deliberately malformed test bytes in memory, never a gameplay fixture."""
    data = bytearray(raw)
    for start in (0x200, 0x1a00):
        data[start + relative_offset] = value
        bank = bytearray(data[start:start + 6144])
        bank[16:20] = bytes(4)
        bank[20] = 0
        data[start + 16:start + 20] = binascii.crc32(bank).to_bytes(4, 'little')
    return bytes(data)


class FixtureVerifierTests(unittest.TestCase):
    def test_self_contained_export_and_optimized_python(self):
        with tempfile.TemporaryDirectory(prefix='magma-minimal-export-') as folder:
            exported = Path(folder) / 'fixture'
            shutil.copytree(HERE, exported, ignore=shutil.ignore_patterns('__pycache__'))
            for flags in (('-I', '-S'), ('-I', '-S', '-O')):
                run = subprocess.run([sys.executable, *flags, str(exported / 'verify_fixture.py')],
                                     cwd=folder, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                result = json.loads(run.stdout)
                self.assertTrue(result['passed'])
                self.assertEqual(result['owned_individuals'], 10)
                self.assertFalse(result['original_run_reverified'])

    def test_export_corruption_is_rejected(self):
        for target in ('magma-minimal10-town.sav', 'producer/report_parts/part_000.txt',
                       'producer/test-source/tests/magma_journey.py'):
            with self.subTest(target=target), tempfile.TemporaryDirectory(prefix='magma-minimal-negative-') as folder:
                exported = Path(folder) / 'fixture'
                shutil.copytree(HERE, exported, ignore=shutil.ignore_patterns('__pycache__'))
                path = exported / target
                bad = bytearray(path.read_bytes())
                bad[-1] ^= 1
                path.write_bytes(bad)
                run = subprocess.run([sys.executable, '-I', '-S', '-O', str(exported / 'verify_fixture.py')],
                                     cwd=folder, capture_output=True, text=True)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn('FAILED', run.stderr)

    def test_missing_ledger_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='magma-minimal-no-ledger-') as folder:
            exported = Path(folder) / 'fixture'
            shutil.copytree(HERE, exported, ignore=shutil.ignore_patterns('__pycache__'))
            (exported / 'CHECKSUMS.json').unlink()
            run = subprocess.run([sys.executable, '-I', '-S', str(exported / 'verify_fixture.py')],
                                 capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)

    def test_unlisted_file_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='magma-minimal-inventory-') as folder:
            exported = Path(folder) / 'fixture'
            shutil.copytree(HERE, exported, ignore=shutil.ignore_patterns('__pycache__'))
            (exported / 'unexpected.txt').write_text('not authenticated\n')
            run = subprocess.run([sys.executable, '-I', '-S', str(exported / 'verify_fixture.py')],
                                 capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('inventory', run.stderr)

    def test_crc_rejects_in_memory_corruption(self):
        bad = bytearray((HERE / 'magma-minimal10-town.sav').read_bytes())
        bad[0x200 + 162] ^= 1
        with self.assertRaisesRegex(ValueError, 'CRC'):
            VERIFIER['decode_banks'](bytes(bad), 5)

    def test_semantics_reject_crc_repaired_optional_progress_and_identity(self):
        raw = (HERE / 'magma-minimal10-town.sav').read_bytes()
        # Optional quest33 occupies bits2..3 in quest byte8, following quest32.
        for offset, value in ((4032 + 8, 15), (160 + 24 + 8, 99), (160, 2)):
            with self.subTest(offset=offset):
                banks = VERIFIER['decode_banks'](repaired(raw, offset, value), 5)
                with self.assertRaises(ValueError):
                    VERIFIER['check_semantics'](banks[0])

    def test_personal_trial_rejected_even_with_valid_crc(self):
        raw = (HERE / 'magma-minimal10-town.sav').read_bytes()
        with self.assertRaisesRegex(ValueError, 'trial'):
            VERIFIER['decode_banks'](repaired(raw, 160 + 14, 1), 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
