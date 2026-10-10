#!/usr/bin/env python3
"""Controlled K/B comparison: identical earned89/50 SRAM, old repeat37 only.

No Return quest or form is introduced before measurement. No machine state is
imported. Native timing failures are observations, never acceptance passes.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import struct
import traceback

from return_journey import ROOT, digest, ALL89_SHA, ReadOnlyGameEmulator, ReturnJourney, PLAY
from magma_journey import MagmaJourney, elf_locals
from southern_journey import SouthernJourney
from underwater_journey import UnderwaterJourney
from northern_journey import newest_bank


class Baseline(MagmaJourney):
    step = ReturnJourney.step
    measured = ReturnJourney.measured
    cadence = ReturnJourney.cadence
    settle = ReturnJourney.settle
    freeze_helpers = ReturnJourney.freeze_helpers

    def __init__(self, args):
        self.source_rom, self.source_symbols = args.rom.resolve(), args.symbols.resolve()
        self.out = args.output.resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.rom, self.symbol_path, self.elf = [self.out / ('tested.' + s) for s in ('gba', 'sym', 'elf')]
        self.target_sha, self.symbol_sha = args.expected_rom_sha, args.expected_symbols_sha
        for src, dst, expected in ((self.source_rom, self.rom, self.target_sha),
                                   (self.source_symbols, self.symbol_path, self.symbol_sha),
                                   (self.source_rom.with_suffix('.elf'), self.elf, args.expected_elf_sha)):
            assert digest(src) == expected
            shutil.copyfile(src, dst)
        self.locals = elf_locals(self.elf, self.rom)
        rows = [p for line in self.symbol_path.read_text().splitlines() if len(p := line.split()) == 3]
        counts = Counter(p[2] for p in rows)
        self.sym = {p[2]: int(p[0], 16) for p in rows if counts[p[2]] == 1}
        assert digest(args.source_manifest) == args.expected_manifest_sha
        self.source_hashes = json.loads(args.source_manifest.read_text())
        self.source_root = args.source_root.resolve()
        assert all(digest(self.source_root / p) == sha for p, sha in self.source_hashes.items())
        self.source_manifest_sha = args.expected_manifest_sha
        shutil.copyfile(args.source_manifest, self.out / 'candidate-source-hashes.json')
        self.fixture = ROOT / 'tests/fixtures/v5-revision6/underwater-all89-town.sav'
        assert digest(self.fixture) == ALL89_SHA
        self.source_bytes = self.fixture.read_bytes()
        self.source_bank = newest_bank(self.source_bytes)
        self.expected_revision = args.expected_revision
        self.candidate = {'rom_sha256': self.target_sha, 'symbols_sha256': self.symbol_sha,
                          'elf_sha256': args.expected_elf_sha, 'rom_bytes': self.rom.stat().st_size,
                          'bridge_sha256': digest(ROOT / 'tools/mgba_bridge.so')}
        self.provenance = {'fixture': str(self.fixture), 'sram_sha256': ALL89_SHA,
                           'cross_rom_machine_state_loaded': False}
        self.inputs, self.checks, self.failures, self.transitions = [], [], [], []
        self.cases, self.frame_windows, self.acquisitions, self.main_selections = [], [], [], []
        self.snapshots, self.timings = {}, {}
        self.main_only, self.minimal, self.trace = False, False, None
        self.timing_mode, self.finished = 'collect-diagnostic', False
        self.test_sources = self.freeze_helpers()
        self.e = ReadOnlyGameEmulator(self.rom)
        self.e.load_save(self.fixture)
        self.e.reset()
        self.descriptors, self.mask_cache = {}, {}
        for name, start in (('magma', 38), ('underwater', 46)):
            table = self.sym[name + '_art_rooms']
            valid = []
            for stride in (20, 28, 32):
                found = []
                for i in range(8):
                    address = table + i * stride
                    w, h = struct.unpack('<HH', self.e.bytes(address, 4))
                    bitmap = self.e.read(address + 4)
                    if (w, h) not in ((240, 160), (480, 320)) or bitmap not in [v for k, v in self.sym.items() if k.startswith(name + '_background_')]:
                        break
                    found.append({'address': address, 'width': w, 'height': h, 'bitmap': bitmap, 'stride': stride})
                if len(found) == 8:
                    valid.append(found)
            assert len(valid) == 1
            self.descriptors.update({start + i: row for i, row in enumerate(valid[0])})
        self.report()

    def report(self):
        data = {'suite': 'paired-legacy-repeat-baseline', 'controller_only': True, 'game_ram_writes': 0,
                'machine_state_loads': 0, 'release_acceptance': False, 'finished': self.finished,
                **self.candidate, 'provenance': self.provenance,
                'source_manifest_sha256': self.source_manifest_sha, 'source_root': str(self.source_root),
                'test_sources': self.test_sources, 'checks': self.checks, 'failures': self.failures,
                'inputs': self.inputs, 'cases': self.cases, 'frame_windows': self.frame_windows,
                'snapshots': self.snapshots, 'transitions': self.transitions}
        (self.out / 'legacy-baseline.json').write_text(json.dumps(data, indent=2) + '\n')

    def mask(self):
        if self.get('room') == 46:
            return SouthernJourney.mask(self)
        return MagmaJourney.mask(self)

    def snapshot(self, name):
        self.settle()
        self.step(3)
        save, shot = self.out / (name + '.sav'), self.out / (name + '.png')
        save.write_bytes(self.e.bytes(0x0e000000, 32768))
        self.e.screenshot(shot)
        self.snapshots[name] = {'sram_path': str(save), 'sram_sha256': digest(save),
                                'screenshot': str(shot), 'status': self.status(),
                                'forms': self.collection(), 'individuals': [
                                    {'id': c.instance_id, 'form': c.form_id} for c in self.live()]}
        self.report()

    def run(self):
        self.step(150)
        self.measured('bounded-cold-identical-source-continue',
                      lambda: (self.tap('START', 2, 90), self.settle()), cold_continue=True)
        bank = newest_bank(self.e.bytes(0x0e000000, 32768))
        self.check(self.get('room') == 46 and self.get('game_state') == PLAY, 'identical authenticated fixture resumes in46')
        self.check(int.from_bytes(bank[12:14], 'little') == self.expected_revision and bank[32:] == self.source_bank[32:],
                   'candidate cold boot preserves identical89-history durable source payload')
        self.check(len(self.collection()) == 89 and len(self.live()) == 50, 'comparison begins with exactly89 histories and50 real individuals')
        self.snapshot('identical-source-cold')
        UnderwaterJourney.entry(self, 38)
        MagmaJourney.entry(self, 39)
        self.target(80, 264)
        self.clear_enemies()
        self.goto(80, 248, radius=4)
        self.face(1)
        self.step(120)
        self.snapshot('repeat37-before')
        previous = {c.instance_id: bytes(c) for c in self.live()}
        self.measured('identical-source-repeat37-two-real-A',
                      lambda: (self.tap('A', 2, 120), self.settle(), self.tap('A', 2, 120), self.settle()))
        fresh = [c for c in self.live() if c.instance_id not in previous]
        self.check(len(fresh) == 1 and fresh[0].form_id == 37, 'identical-source comparison really grants one repeat37')
        self.check(all(bytes(c) == previous[c.instance_id] for c in self.live() if c.instance_id in previous),
                   'repeat preserves all previous individual bytes')
        self.snapshot('repeat37-after')
        self.check(all(digest(self.source_root / p) == sha for p, sha in self.source_hashes.items()), 'paired runtime source closure stays exact')
        self.finished = True
        self.report()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('rom', 'symbols', 'source-manifest', 'source-root', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    for name in ('expected-rom-sha', 'expected-symbols-sha', 'expected-elf-sha', 'expected-manifest-sha'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--expected-revision', type=int, choices=(6, 7), required=True)
    a = p.parse_args()
    r = Baseline(a)
    try:
        r.run()
    except Exception as exc:
        r.failures.append({'error': str(exc), 'traceback': traceback.format_exc(), 'status': r.status()})
        r.snapshot('failure')
        raise
    finally:
        r.report()
        r.e.close()
    return bool(r.failures)


if __name__ == '__main__':
    raise SystemExit(main())
