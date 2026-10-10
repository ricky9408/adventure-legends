#!/usr/bin/env python3
"""Harness guard tests only: no emulator boot, progress fixture, or game RAM.

Synthetic byte strings below exercise file-pair rejection, not gameplay. Native
acquisition/cadence evidence is exclusively the separately recorded journeys.
"""
from pathlib import Path
import io
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from return_journey import ReturnJourney, ReadOnlyGameEmulator, Emulator, ROOT, digest


class HarnessGuards(unittest.TestCase):
    def synthetic_global(self, frames):
        run = ReturnJourney.__new__(ReturnJourney)
        data = {'frame': 10, 'display': 0x1444, 'game_state': 1, 'room': 54, 'render_cycles': 1000}
        emulator = SimpleNamespace(frame=100, boot_serial=1)
        queue = iter(frames)

        def advance(count, keys):
            self.assertEqual(count, 1)
            emulator.frame += 1
            data.update(next(queue))

        emulator.frames = advance
        emulator.read = lambda address, width=4: data['display']
        run.e, run.get = emulator, lambda name, width=4: data.get(name, 0)
        run.inputs, run.transitions, run.checks, run.failures = [], [], [], []
        run.main_only, run.trace, run.timing_mode = False, None, 'strict'
        run._native_stream = io.StringIO()
        run._observed_boot_serial, run._initial_prefix, run._continue_prefix = 1, None, None
        run.global_native = {'hardware_frames': 0, 'strict_frames': 0, 'loader_frames': 0,
                             'maximum_cycles': 0, 'maximum_obj_count': 0, 'exceptions': [], 'cold_prefixes': []}
        return run

    def test_global_sampler_rejects_missed_presentation_below_cycle_limit(self):
        run = self.synthetic_global([
            {'frame': 11, 'display': 0x1454},
            {'frame': 11, 'display': 0x1454, 'render_cycles': 250000},
            {'frame': 12, 'display': 0x1444},
        ])
        with self.assertRaises(AssertionError):
            run.global_step(3)
        self.assertEqual(run.global_native['hardware_frames'], 2)
        self.assertEqual(run.global_native['strict_frames'], 2)
        self.assertEqual(len(run.global_native['exceptions']), 1)
        self.assertEqual(run.inputs[0]['frames'], 2)
        self.assertEqual(run.inputs[0]['requested_frames'], 3)

    def test_continue_exemption_ends_when_native_updates_resume(self):
        run = self.synthetic_global([
            {'frame': 0, 'display': 0x1454},
            {'frame': 1, 'display': 0x1444},
            {'frame': 1, 'display': 0x1444, 'render_cycles': 1000},
        ])
        run._continue_prefix = {'kind': 'continue', 'hardware_frames': 0, 'excluded_frames': 0,
                                'started': False, 'done': False}
        with self.assertRaises(AssertionError):
            run.global_step(3)
        self.assertTrue(run._continue_prefix['done'])
        self.assertEqual(run.global_native['loader_frames'], 1)
        self.assertEqual(run.global_native['strict_frames'], 2)
        self.assertEqual(len(run.global_native['exceptions']), 1)

    def test_both_game_write_routes_are_blocked(self):
        with patch.object(Emulator, '__init__', lambda self, *a, **k: setattr(self, 'lib', SimpleNamespace())):
            emulator = ReadOnlyGameEmulator('not-a-ROM')
        for write in (emulator.write, emulator.lib.eb_write):
            with self.assertRaisesRegex(AssertionError, 'Game RAM writes are forbidden'):
                write(0x02000000, 123, 4)

    def pair(self, directory):
        run = ReturnJourney.__new__(ReturnJourney)
        calls = []
        run.e = SimpleNamespace(load_save=lambda path: calls.append(('save', path)),
                                state=lambda path, load: calls.append(('state', path, load)), frame=0)
        run.step = lambda frames: calls.append(('step', frames))
        run.cases, run.machine_state_loads = [], 0
        files = {}
        for name in ('rom', 'symbol_path', 'elf', 'state', 'save'):
            path = Path(directory) / name
            path.write_bytes(('synthetic pairing unit input ' + name).encode())
            files[name] = path
        run.rom, run.symbol_path, run.elf = files['rom'], files['symbol_path'], files['elf']
        run.target_sha, run.symbol_sha = digest(run.rom), digest(run.symbol_path)
        run.snapshots = {'paired': {'rom_sha256': run.target_sha, 'symbols_sha256': run.symbol_sha,
                                     'elf_sha256': digest(run.elf), 'state_path': str(files['state']),
                                     'state_sha256': digest(files['state']), 'sram_path': str(files['save']),
                                     'sram_sha256': digest(files['save'])}}
        return run, files, calls

    def test_valid_pair_restores_sram_before_machine_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            run, files, calls = self.pair(tmp)
            run.restore('paired')
            self.assertEqual(calls, [('save', str(files['save'])), ('state', str(files['state']), True), ('step', 4)])
            self.assertEqual(run.machine_state_loads, 1)
            self.assertEqual(run.cases[0]['same_candidate_restore'], 'paired')

    def test_every_changed_pair_file_is_rejected_before_any_load(self):
        for name in ('rom', 'symbol_path', 'elf', 'state', 'save'):
            with self.subTest(file=name), tempfile.TemporaryDirectory() as tmp:
                run, files, calls = self.pair(tmp)
                files[name].write_bytes(b'changed synthetic input')
                with self.assertRaises(AssertionError):
                    run.restore('paired')
                self.assertEqual(calls, [])
                self.assertEqual(run.machine_state_loads, 0)

    def test_historical_controller_sources_remain_unedited(self):
        hashes = {
            'tests/underwater_journey.py': 'e6ff183a9f2e178e954584eebdf54f51a5943100d0499fbad092cc2c7c6f6b6e',
            'tests/underwater_collection_route.py': 'fcdba2f202c96214aad45ed711d6f211d5cfb383fddda8ba8a94bc2c132a2f89',
            'tests/magma_journey.py': '511f7ba84ef7d840c5f3edded805fffb9d53edb042ce0315a09469b5ed58dc07',
        }
        for path, expected in hashes.items():
            with self.subTest(path=path):
                self.assertEqual(digest(ROOT / path), expected)


if __name__ == '__main__':
    unittest.main()
