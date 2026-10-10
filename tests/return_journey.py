#!/usr/bin/env python3
"""Return I controller journey on a pinned candidate; developer spoilers.

The only cross-ROM input is authenticated delivered revision6 SRAM. All new
progress comes from buttons. Both Python and direct bridge RAM writes are
blocked. An incomplete/segmented diagnostic is never a release acceptance.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import ctypes as C
import gzip
import inspect
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import traceback

from magma_journey import MagmaJourney, elf_locals
from region_journey import RegionJourney, Emulator, ROOT, digest, PLAY, DIALOG, PAUSE, DEAD, SAVING
from northern_journey import newest_bank
from southern_journey import SouthernJourney
from return_collection_route import ReturnCollectionRoute
from test_save5 import Save, Roster
from return_native_dependencies import freeze_emulator_library, preload_frozen

ALL89_SHA = '41cf371618208e0097fe6ee10393e3185b4bffb2af9dad9e5f81e2663d6673a0'
MINIMAL12_SHA = '3f5bbccab022f86b38f4d180e8cf66b04c055791fe4804ddbebbdefb5406aeda'
UNDERWATER_ROM = 'df3733446cda3d41c2e78da134b25cd446846d6283e4ac5dc47b3fcaa3f98607'
EVENT_PENDING = 10
NEW_FORMS = [3, 6, 9, 12, 15, 17, 18, 21, 24, 27, 30, 101, 102, 103, 104]


def preserve_pinned_file(source, destination, expected):
    """Preserve immutable evidence without redundant same-filesystem ROMs."""
    source, destination = Path(source), Path(destination)
    assert digest(source) == expected
    if destination.exists():
        assert digest(destination) == expected, 'Refusing to overwrite different evidence'
        return
    try:
        os.link(source, destination)
    except OSError:
        shutil.copyfile(source, destination)
    assert digest(destination) == expected


class ReadOnlyGameEmulator(Emulator):
    boot_sequence = itertools.count(1)

    def __init__(self, *args, **kwargs):
        preload_frozen(ROOT)
        super().__init__(*args, **kwargs)
        self.lib.eb_write = self.write
        self.boot_serial = next(self.boot_sequence)

    def reset(self):
        super().reset()
        self.boot_serial = next(self.boot_sequence)

    def write(self, *args, **kwargs):
        raise AssertionError('Game RAM writes are forbidden, including direct eb_write')


class ReturnTrial(C.Structure):
    _fields_ = [(n, C.c_uint) for n in ('instance_id', 'scene', 'attempt', 'party')] + [
        (n, C.c_ubyte) for n in ('index', 'slot', 'form', 'command', 'selected', 'family',
                                'key', 'stage', 'setting', 'casts', 'walk', 'replay')]


class ReturnJourney(ReturnCollectionRoute, MagmaJourney):
    def __init__(self, rom, symbols, output, rom_sha, symbols_sha, elf_sha,
                 source_manifest, manifest_sha, fixture=None, source_root=None, timing_mode='strict'):
        self.source_rom, self.source_symbols = Path(rom).resolve(), Path(symbols).resolve()
        self.out = Path(output).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        assert not (self.out / 'return-journey.json').exists(), 'Use a fresh evidence directory; earlier reports are immutable'
        self.target_sha, self.symbol_sha = rom_sha, symbols_sha
        self.rom, self.symbol_path, self.elf = [self.out / ('tested.' + s) for s in ('gba', 'sym', 'elf')]
        for src, dst, sha in ((self.source_rom, self.rom, rom_sha),
                              (self.source_symbols, self.symbol_path, symbols_sha),
                              (self.source_rom.with_suffix('.elf'), self.elf, elf_sha)):
            preserve_pinned_file(src, dst, sha)
        self.locals = elf_locals(self.elf, self.rom)
        rows = [p for line in self.symbol_path.read_text().splitlines() if len(p := line.split()) == 3]
        counts = Counter(p[2] for p in rows)
        self.sym = {p[2]: int(p[0], 16) for p in rows if counts[p[2]] == 1}
        manifest = Path(source_manifest).resolve()
        assert digest(manifest) == manifest_sha, 'source manifest must be explicitly pinned'
        self.source_hashes = json.loads(manifest.read_text())
        roots = [Path(source_root).resolve()] if source_root else [manifest.parent / 'runtime-source', manifest.parent / 'source', manifest.parent.parent, *manifest.parents, ROOT]
        self.source_root = next((r for r in roots if all((r / p).is_file() and digest(r / p) == h for p, h in self.source_hashes.items())), None)
        assert self.source_root is not None, 'No complete matching frozen source closure'
        self.source_manifest_sha = manifest_sha
        shutil.copyfile(manifest, self.out / 'candidate-source-hashes.json')
        self.fixture = Path(fixture or ROOT / 'tests/fixtures/v5-revision6/underwater-all89-town.sav').resolve()
        fixture_sha = digest(self.fixture)
        assert fixture_sha in (ALL89_SHA, MINIMAL12_SHA), 'Only delivered, earned revision6 SRAM is allowed'
        self.minimal = fixture_sha == MINIMAL12_SHA
        self.prior_count, self.prior_history = (12, 12) if self.minimal else (50, 89)
        self.source_bytes = self.fixture.read_bytes()
        self.source_bank = newest_bank(self.source_bytes)
        assert int.from_bytes(self.source_bank[12:14], 'little') == 6
        self.provenance = {'fixture_path': str(self.fixture), 'sram_sha256': fixture_sha,
                           'source_rom_sha256': UNDERWATER_ROM, 'minimal_prior_route': self.minimal,
                           'cross_rom_machine_state_loaded': False}
        self.candidate = {'rom_sha256': rom_sha, 'symbols_sha256': symbols_sha, 'elf_sha256': elf_sha,
                          'rom_bytes': self.rom.stat().st_size, 'bridge_sha256': digest(ROOT / 'tools/mgba_bridge.so')}
        self.inputs, self.checks, self.failures, self.transitions = [], [], [], []
        self.cases, self.coverage, self.acquisitions, self.frame_windows = [], [], [], []
        self.snapshots, self.timings, self.pixel_cases, self.main_selections = {}, {}, [], []
        self.main_only, self.trace, self.machine_state_loads = False, None, 0
        self.finished_scope = None
        self.timing_mode = timing_mode
        self.global_enabled = True
        self.global_native = {'enabled': True, 'hardware_frames': 0, 'strict_frames': 0,
                              'loader_frames': 0, 'maximum_cycles': 0, 'maximum_obj_count': 0,
                              'exceptions': [], 'cold_prefixes': [], 'closed': False,
                              'trace_path': str(self.out / 'native-global.jsonl.gz')}
        self._native_stream = gzip.open(self.global_native['trace_path'], 'wt', encoding='utf-8', compresslevel=6)
        self._observed_boot_serial = None
        self._initial_prefix = None
        self._continue_prefix = None
        self.test_sources = self.freeze_helpers()
        navigation_root = self.out / 'helper-source'
        self.layout = json.loads((navigation_root / 'assets/region/layout.json').read_text())
        self.world = json.loads((navigation_root / 'assets/world_manifest.json').read_text())
        self.campaign = json.loads((navigation_root / 'assets/campaign_layouts.json').read_text())
        self.campaign_rooms = {r['id']: r for r in self.campaign['rooms']}
        self.return_geometry = json.loads((navigation_root / 'assets/return_region/geometry.json').read_text())
        ui_enum = re.search(r'enum\s*\{(.*?)\};', (self.source_root / 'src/ui.h').read_text(), re.S).group(1)
        self.ui_ids = {name.strip(): index for index, name in enumerate(ui_enum.split(',')) if name.strip()}
        self.e = ReadOnlyGameEmulator(self.rom)
        self.e.load_save(self.fixture)
        self.e.reset()
        self.mask_cache, self.descriptors = {}, {}
        for name, start in (('north', 22), ('south', 30), ('magma', 38), ('underwater', 46), ('return', 54)):
            table = self.sym[name + '_art_rooms']
            candidates = []
            for stride in (20, 28, 32):
                found = []
                for i in range(8):
                    a = table + i * stride
                    w, h = struct.unpack('<HH', self.e.bytes(a, 4))
                    bitmap = self.e.read(a + 4)
                    if (w, h) not in ((240, 160), (480, 320)) or bitmap not in [v for k, v in self.sym.items() if k.startswith(name + '_background_')]:
                        break
                    found.append({'address': a, 'width': w, 'height': h, 'bitmap': bitmap, 'stride': stride})
                if len(found) == 8:
                    candidates.append(found)
            assert len(candidates) == 1, ('ambiguous compiled room descriptor', name)
            self.descriptors.update({start + i: r for i, r in enumerate(candidates[0])})
        assert C.sizeof(ReturnTrial) == 28
        self.report()

    def freeze_helpers(self):
        paths = {Path(__file__).resolve(), ROOT / 'tests/return_collection_route.py', ROOT / 'tools/mgba_bridge.c', ROOT / 'tools/mgba_bridge.so'}
        paths.update(ROOT / p for p in ('assets/region/layout.json', 'assets/world_manifest.json',
                                        'assets/campaign_layouts.json', 'assets/return_region/geometry.json'))
        for module in tuple(sys.modules.values()):
            name = getattr(module, '__file__', None)
            if name and Path(name).is_file() and Path(name).resolve().is_relative_to(ROOT):
                paths.add(Path(name).resolve())
        sources = {}
        for p in sorted(paths):
            relative = p.relative_to(ROOT)
            dest = self.out / 'helper-source' / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest)
            sources[str(relative)] = digest(p)
        sources.update(freeze_emulator_library(ROOT, self.out / 'helper-source'))
        (self.out / 'helper-source-hashes.json').write_text(json.dumps(sources, indent=2) + '\n')
        return sources

    def verify_closures(self):
        self.check(all(digest(self.source_root / p) == sha for p, sha in self.source_hashes.items()), 'frozen source closure remains exact')
        self.check(all(digest(self.out / 'helper-source' / p) == sha for p, sha in self.test_sources.items()), 'copied helper closure remains exact')
        self.check(digest(self.rom) == self.target_sha and digest(self.symbol_path) == self.symbol_sha, 'tested ROM and symbols remain exact')

    def report(self):
        data = {'suite': 'return-native-controller-journey', 'development_diagnostic': True,
                'release_acceptance': False, 'finished_scope': self.finished_scope,
                'timing_mode': self.timing_mode,
                'controller_only': True, 'game_ram_writes': 0, 'physical_handheld_tested': False,
                'player_facing': False, 'machine_state_loads': self.machine_state_loads,
                **self.candidate, 'provenance': self.provenance,
                'source_manifest_sha256': self.source_manifest_sha, 'source_root': str(self.source_root),
                'helper_sources': self.test_sources, 'checks': self.checks, 'failures': self.failures,
                'snapshots': self.snapshots, 'inputs': self.inputs, 'transitions': self.transitions,
                'cases': self.cases, 'acquisitions': self.acquisitions, 'coverage': self.coverage,
                'main_route_selected_forms': sorted(set(self.main_selections)), 'frame_windows': self.frame_windows,
                'global_native': self.global_native,
                'scope_limits': ['No physical GBA measurement', 'Finite representative cadence windows, not exhaustive timing proof',
                                 'Full capacity, ID exhaustion and bytewise fault matrix belong to separate suites',
                                 'Diagnostic failures remain in their original reports; reruns do not replace them']}
        (self.out / 'return-journey.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    def local_bytes(self, name, size):
        address, actual = self.locals['return_game.c:' + name]
        assert size == actual, (name, actual)
        return self.e.bytes(address, size)

    def setting(self):
        return list(self.local_bytes('setting', 6))

    def return_local(self, name, size=1):
        return self.local(name, size, file='return_game.c')

    def trial(self):
        return ReturnTrial.from_buffer_copy(self.e.bytes(self.sym['return_game_trial'], C.sizeof(ReturnTrial)))

    def state_signature(self):
        s = self.state()
        return bytes(s.roster), bytes(s.quests), bytes(s.equipment)

    def step(self, n, keys=0):
        if getattr(self, 'global_enabled', False):
            return self.global_step(n, keys)
        if self.trace is None:
            return MagmaJourney.step(self, n, keys)
        for _ in range(n):
            old, page, state = self.get('frame'), self.e.read(0x04000000, 2) & 16, self.get('game_state')
            MagmaJourney.step(self, 1, keys)
            new = self.get('frame')
            self.trace.append({'hardware_frame': self.e.frame, 'update_delta': (new - old) & 0xffffffff,
                               'frame_before': old, 'frame_after': new,
                               'counter_reset': new < old, 'page_flip': (self.e.read(0x04000000, 2) & 16) != page,
                               'cycles': self.get('render_cycles'), 'state_before': state,
                               'state_after': self.get('game_state'), 'room': self.get('room'),
                               'journal_tab': self.get('journal_tab'),
                               'toast_id': self.get('toast_id'), 'toast_ticks': self.get('toast_ticks'),
                               'obj_count': self.get('obj_count')})

    def global_step(self, n, keys=0):
        """Observe every real hardware frame, without per-frame roster copies."""
        batch = {'frame': self.e.frame, 'frames': 0, 'requested_frames': int(n), 'keys': keys}
        self.inputs.append(batch)
        if self.e.boot_serial != self._observed_boot_serial:
            self._observed_boot_serial = self.e.boot_serial
            self._initial_prefix = {'kind': 'startup', 'boot_serial': self.e.boot_serial,
                                    'hardware_frames': 0, 'excluded_frames': 0, 'started': True, 'done': False}
            self.global_native['cold_prefixes'].append(self._initial_prefix)
        for _ in range(n):
            old, display_before = self.get('frame'), self.e.read(0x04000000, 2)
            page = display_before & 16
            state, room = self.get('game_state'), self.get('room')
            self.e.frames(1, keys)
            batch['frames'] += 1
            new, after_room = self.get('frame'), self.get('room')
            display_after = self.e.read(0x04000000, 2)
            row = {'hardware_frame': self.e.frame, 'sample_index': self.global_native['hardware_frames'],
                   'boot_serial': self.e.boot_serial, 'frame_before': old, 'frame_after': new,
                   'update_delta': (new - old) & 0xffffffff, 'counter_reset': new < old,
                   'page_flip': (display_after & 16) != page,
                   'display_before': display_before, 'display_after': display_after,
                   'cycles': self.get('render_cycles'), 'state_before': state, 'state_after': self.get('game_state'),
                   'room': after_room, 'journal_tab': self.get('journal_tab'),
                   'toast_id': self.get('toast_id'), 'toast_ticks': self.get('toast_ticks'),
                   'obj_count': self.get('obj_count')}
            prefix = self._continue_prefix if self._continue_prefix is not None else self._initial_prefix
            exempt = False
            if prefix is not None and not prefix['done']:
                prefix['hardware_frames'] += 1
                self.check(prefix['hardware_frames'] <= 160, 'global cold loader prefix stays within160 hardware frames')
                startup_blank = prefix['kind'] == 'startup' and (display_before & 128 or display_after & 128 or row['cycles'] == 0)
                if row['counter_reset'] or new == 0 or startup_blank:
                    prefix['started'] = True
                    prefix['excluded_frames'] += 1
                    exempt = True
                elif prefix['started']:
                    prefix['done'] = True
            row['cold_loader_exempt'] = exempt
            self.global_native['hardware_frames'] += 1
            if exempt:
                self.global_native['loader_frames'] += 1
            else:
                self.global_native['strict_frames'] += 1
                self.global_native['maximum_cycles'] = max(self.global_native['maximum_cycles'], row['cycles'])
                self.global_native['maximum_obj_count'] = max(self.global_native['maximum_obj_count'], row['obj_count'])
            self._native_stream.write(json.dumps(row, separators=(',', ':')) + '\n')
            if self.trace is not None:
                self.trace.append(row)
            if room != after_room:
                self.transitions.append({'frame': self.e.frame, 'from': room, 'to': after_room, 'keys': keys})
            if self.main_only and row['state_after'] == PLAY:
                base = self.sym['adventure_save'] + Save.roster.offset
                selected = self.e.read(base + Roster.selected_party.offset, 1)
                slot = self.e.read(base + Roster.party.offset + selected, 1) if selected < 4 else 255
                if slot < 160:
                    form = self.e.read(base + Roster.instances.offset + slot * 24, 1)
                    self.main_selections.append(form)
            bad = not exempt and (row['update_delta'] != 1 or not row['page_flip'] or row['cycles'] >= 280896 or row['obj_count'] > 128)
            if bad:
                self.global_native['exceptions'].append(row)
                self._native_stream.flush()
                label = 'global hardware frame has one update/flip within cycle/OAM budget'
                if self.timing_mode == 'collect-diagnostic':
                    self.checks.append({'label': label, 'passed': False, 'frame': self.e.frame})
                    self.failures.append({'kind': 'global-native-cadence', 'row': row, 'continued_only_for_diagnosis': True})
                else:
                    self.check(False, label)

    def close_global_trace(self):
        if getattr(self, 'global_enabled', False) and not self.global_native['closed']:
            self._native_stream.close()
            self.global_native['closed'] = True
            self.global_native['trace_sha256'] = digest(self.global_native['trace_path'])

    def measured(self, name, callback, cold_continue=False, strict=True):
        assert self.trace is None
        previous_prefix = getattr(self, '_continue_prefix', None)
        if cold_continue and getattr(self, 'global_enabled', False):
            self._continue_prefix = {'kind': 'continue', 'name': name, 'hardware_frames': 0,
                                     'excluded_frames': 0, 'started': False, 'done': False}
            self.global_native['cold_prefixes'].append(self._continue_prefix)
        self.trace = []
        try:
            result = callback()
        finally:
            rows, self.trace = self.trace, None
            self._continue_prefix = previous_prefix
            exceptions = [r for r in rows if r['update_delta'] != 1 or not r['page_flip'] or r['cycles'] >= 280896 or r['obj_count'] > 128]
            loader_rows = [r for r in rows if cold_continue and (r['counter_reset'] or r['frame_after'] == 0)]
            post_loader_exceptions = [r for r in exceptions if r not in loader_rows]
            self.frame_windows.append({'name': name, 'hardware_frames': len(rows), 'trace': rows,
                                       'maximum_cycles': max((r['cycles'] for r in rows), default=0),
                                       'raw_exceptions': exceptions, 'cold_continue_only': cold_continue,
                                       'loader_hardware_frames': len(loader_rows),
                                       'post_loader_exceptions': post_loader_exceptions if cold_continue else [],
                                       'exclusion': 'Only the reset/frame-zero cold loader prefix; subsequent menu/save/play frames remain strict' if cold_continue else None})
            self.report()
        if cold_continue:
            self.check(0 < len(rows) <= 160 and self.get('game_state') == PLAY and not self.get('save_failed'),
                       name + ' is bounded to160 hardware frames and returns to live play')
            self.check(not post_loader_exceptions, name + ' has no cadence exemption after the cold loader prefix')
        elif strict:
            label = name + ' presents one update and flip per hardware frame within cycle/OAM budgets'
            if exceptions and self.timing_mode == 'collect-diagnostic':
                self.checks.append({'label': label, 'passed': False, 'frame': self.e.frame})
                self.failures.append({'kind': 'native-cadence', 'case': name, 'raw_exceptions': exceptions,
                                      'continued_only_for_diagnosis': True})
            else:
                self.check(not exceptions, label)
        return result

    def cadence(self, name, count=120, keys=None):
        return self.measured(name, lambda: [self.step(1, keys(i) if keys else 0) for i in range(count)])

    def settle(self):
        for _ in range(900):
            state = self.get('game_state')
            if state in (SAVING, EVENT_PENDING, 8):
                self.step(2)
            elif state == DIALOG:
                self.tap('A', 2, 3)
            else:
                self.check(not self.get('save_failed'), 'incremental save reports no failure')
                return
        raise AssertionError(('bounded modal failed to settle', self.status()))

    def snapshot(self, name, settle=True):
        base, suffix = name, 1
        while name in self.snapshots:
            suffix += 1
            name = f'{base}-{suffix:02d}'
        if settle:
            self.settle()
            # Modal state may clear before the next displayed native page. Give
            # both pages a real render before calling the image an arrival.
            self.step(3)
            self.settle()
        state, save, shot = [self.out / (name + suffix) for suffix in ('.state', '.sav', '.png')]
        self.e.state(state)
        save.write_bytes(self.e.bytes(0x0e000000, 32768))
        self.e.screenshot(shot)
        self.snapshots[name] = {'rom_sha256': self.target_sha, 'symbols_sha256': self.symbol_sha,
                                'elf_sha256': self.candidate['elf_sha256'], 'state_path': str(state),
                                'state_sha256': digest(state), 'sram_path': str(save), 'sram_sha256': digest(save),
                                'screenshot': str(shot), 'status': self.status(), 'quests': [self.quest(q) for q in range(54)],
                                'obtained_form_ids': self.collection(),
                                'individuals': [{'slot': i, 'form': c.form_id, 'instance_id': c.instance_id,
                                                 'trial_flags': c.trial_flags, 'level': c.level, 'bond': c.bond}
                                                for i, c in enumerate(self.roster().instances) if c.flags & 1],
                                'gear_items': [g.item_id for g in self.state().equipment.bag if g.item_id],
                                'oam': self.oam(),
                                'objectives': list(self.state().quests.objectives)[46:54],
                                'trial': {n: getattr(self.trial(), n) for n, _ in ReturnTrial._fields_}}
        self.report()
        print(name, self.status(), flush=True)
        return name

    def restore(self, name):
        saved = self.snapshots[name]
        assert saved['rom_sha256'] == digest(self.rom) == self.target_sha
        assert saved['symbols_sha256'] == digest(self.symbol_path) == self.symbol_sha
        assert saved['elf_sha256'] == digest(self.elf)
        assert digest(saved['state_path']) == saved['state_sha256'] and digest(saved['sram_path']) == saved['sram_sha256']
        self.e.load_save(saved['sram_path'])
        self.e.state(saved['state_path'], True)
        self.machine_state_loads += 1
        self.cases.append({'same_candidate_restore': name, 'frame': self.e.frame, 'paired_sram_sha256': saved['sram_sha256']})
        self.step(4)

    def mask(self):
        room = self.get('room')
        if room == 0:
            # The old helper normally opens mutable ROOT/src/asset_collisions.h.
            # Resolve that one legacy input against the frozen source closure.
            source = (self.source_root / 'src/asset_collisions.h').read_text()
            body = re.search(r'asset_solids_village\[.*?\] = \{(.*?)\};', source, re.S).group(1)
            rects = [list(map(int, row.split(','))) for row in re.findall(r'\{([^}]+)\}', body)]
            w, h = 240, 160
            b = bytearray(int(not (12 <= x < 228 and 28 <= y < 153)) for y in range(h) for x in range(w))
            for x, y, rw, rh in rects:
                for yy in range(max(0, y), min(h, y + rh)):
                    lo, hi = max(0, x), min(w, x + rw)
                    b[yy*w + lo:yy*w + hi] = b'\1' * (hi - lo)
            return b, w, h
        if room < 22:
            return RegionJourney.mask(self)
        raw, w, h = SouthernJourney.mask(self)
        b = bytearray(raw)
        if room >= 54:
            settings = self.setting()
            blocks = [d['states'][int(bool(settings[d['setting']]))] for d in self.return_geometry['rooms'][room - 54].get('dynamic_rectangles', [])]
            for x, y, rw, rh in blocks:
                for yy in range(max(0, y - 5), min(h, y + rh + 5)):
                    lo, hi = max(0, x - 5), min(w, x + rw + 5)
                    b[yy * w + lo:yy * w + hi] = b'\1' * (hi - lo)
        return b, w, h

    def boot(self):
        self.step(150)
        self.measured('bounded-cold-revision6-continue', lambda: (self.tap('START', 2, 90), self.settle()), cold_continue=True)
        self.check(self.get('game_state') == PLAY and self.get('room') == 46, 'delivered Underwater town resumes by normal Continue')
        bank = newest_bank(self.e.bytes(0x0e000000, 32768))
        self.check(int.from_bytes(bank[12:14], 'little') == 7, 'ordinary Continue commits content revision7')
        self.check(bank[32:] == self.source_bank[32:], 'revision6 to7 preserves every durable payload byte before new actions')
        offset = self.source_bytes.index(self.source_bank)
        self.check(self.e.bytes(0x0e000000 + offset, 6144) == self.source_bank, 'forward migration preserves the prior committed source bank')
        self.check(len(self.live()) == self.prior_count and len(self.collection()) == self.prior_history, 'migration gives no automatic companion or history')
        self.check(not any(self.quest(q) or self.state().quests.objectives[q] for q in range(46, 54)) and not self.state().quests.region_flags[5] and not self.state().quests.anchors[5], 'migration gives no Return quest, objective, visit or anchor')
        self.old_ids = {c.instance_id for c in self.live()}
        self.old_history = self.collection()
        self.old_equipped = bytes(self.state().equipment.equipped)
        self.snapshot('00-revision7-exact-migration')
        self.cadence('cold-town-active', 120)
        self.measured('cold-journal-open-scroll-close', lambda: (self.open_tab(9), self.tap('DOWN', 2, 4), self.tap('UP', 2, 4), self.close_menu()))

    def entry(self, target):
        here = self.get('room')
        boards = {(0, 54): (176, 112, 1), (0, 60): (104, 112, 1),
                  (16, 55): (424, 144, 3), (17, 56): (264, 284, 1),
                  (22, 57): (416, 144, 1), (30, 58): (432, 256, 1),
                  (58, 59): (432, 256, 1), (60, 61): (208, 112, 1)}
        old = {(1, 16): (168, 248, 1), (16, 22): (400, 280, 1),
               (22, 16): (240, 264, 1), (22, 30): (208, 224, 1),
               (30, 22): (240, 264, 1), (30, 38): (288, 248, 1),
               (38, 30): (240, 268, 1), (38, 46): (416, 224, 1)}
        exits = {(0, 1): (120, 31, 'UP'), (1, 0): (240, 303, 'DOWN'),
                 (16, 1): (240, 299, 'DOWN'), (16, 17): (240, 32, 'UP'),
                 (17, 16): (240, 299, 'DOWN'), (46, 38): (240, 304, 'DOWN')}
        if here >= 54:
            room = self.return_geometry['rooms'][here - 54]
            parent = room['exits'][0]['target']
            if target == parent:
                exits[(here, target)] = (room['width'] // 2, room['height'] - 15, 'DOWN')
        if (here, target) in boards:
            self.target(*boards[here, target])
        elif (here, target) == (22, 30):
            # Existing ferry is a walk-on marker, unlike Return's facing boards.
            self.act(208, 224, 1)
        elif (here, target) in old:
            self.target(*old[here, target])
        elif (here, target) in exits:
            x, y, key = exits[here, target]
            self.goto(x, y, radius=4)
            for _ in range(30):
                if self.get('room') != here:
                    break
                self.step(2, key)
                self.settle()
        else:
            raise AssertionError(('unimplemented ordinary transition', here, target))
        self.check(self.get('room') == target, f'ordinary controller exit {here} reaches {target}')
        self.transitions[-1]['verified_destination'] = target

    def travel(self, target, clear=False):
        graph = {0: [1, 54, 60], 1: [0, 16], 16: [1, 17, 22, 55], 17: [16, 56],
                 22: [16, 30, 57], 30: [22, 38, 58], 38: [30, 46], 46: [38],
                 54: [0], 55: [16], 56: [17], 57: [22], 58: [30, 59], 59: [58], 60: [0, 61], 61: [60]}
        queue, seen = deque([(self.get('room'), [])]), {self.get('room')}
        while queue:
            room, path = queue.popleft()
            if room == target:
                for destination in path:
                    self.entry(destination)
                return
            for destination in graph[room]:
                if destination not in seen:
                    seen.add(destination)
                    queue.append((destination, path + [destination]))
        raise AssertionError(('no controller route', self.get('room'), target))

    def cast_target(self, form, command, x, y, distance=24, direction=1, label=None, prepare=True):
        if prepare:
            self.owned_select(form)
            self.set_command(command)
        self.ready()
        dx, dy = {0: (0, -distance), 1: (0, distance), 2: (distance, 0), 3: (-distance, 0)}[direction]
        self.goto(x + dx, y + dy, radius=4)
        self.face(direction)
        self.ready()
        before = {'instance_id': self.selected().instance_id, 'form': self.selected().form_id,
                  'command': self.command(), 'hero': [self.get('px'), self.get('py')], 'target': [x, y],
                  'direction': direction, 'trial': {n: getattr(self.trial(), n) for n, _ in ReturnTrial._fields_}}
        self.measured(label or f'cast-{form}-{command}-area{self.get("room")}', lambda: (self.tap('R', 2, 120), self.settle()))
        self.check(self.selected().instance_id == before['instance_id'], 'actual cast retains exact selected individual')
        self.cases.append({'field_cast': before, 'after_setting': self.setting(), 'frame': self.e.frame})

    def source_invitation(self, q, form, point):
        before = self.state_signature()
        self.target(*point)
        self.check(self.state_signature() == before and self.return_local('invite_confirm') == q, 'first A only previews the explicit source invitation')
        self.tap('B')
        self.check(self.state_signature() == before and not self.return_local('invite_confirm'), 'B cancels source invitation without changing durable state')
        self.target(*point)
        self.step(20, 'DOWN')
        self.check(self.state_signature() == before and not self.return_local('invite_confirm'), 'walking away cancels source invitation harmlessly')
        self.target(*point)
        self.check(self.state_signature() == before, 'fresh first A after walkaway still cannot recruit')
        identities = {c.instance_id for c in self.live()}
        self.tap('A')
        self.settle()
        fresh = [c for c in self.live() if c.instance_id not in identities]
        self.check(self.quest(q) == 3 and len(fresh) == 1 and fresh[0].form_id == form, 'fresh second A earns exactly one guaranteed individual')
        c = fresh[0]
        self.check(not c.flags & 2 and not c.trial_flags and c.level >= 28 and c.bond >= 25, 'new recruit is ordinary, untrialed and receives its stated floor')
        self.acquisitions.append({'quest': q, 'form': form, 'instance_id': c.instance_id, 'frame': self.e.frame, 'source': 'explicit second-A first invitation'})
        after = self.state_signature()
        claimed_objective = self.state().quests.objectives[q]
        claimed_receipt = self.state().quests.rewards[q >> 3] & (1 << (q & 7))
        self.target(*point)
        # Curator's same physical table may now offer the separate optional
        # survey. That legitimate offer is not a duplicated source reward.
        now = self.state_signature()
        self.check((now[0], now[2]) == (after[0], after[2]) and self.quest(q) == 3 and
                   self.state().quests.objectives[q] == claimed_objective and
                   self.state().quests.rewards[q >> 3] & (1 << (q & 7)) == claimed_receipt,
                   'claimed source cannot duplicate the invitation or its quest/item reward')

    def initialize_return(self):
        self.target(200, 272)
        self.check(self.state().quests.objectives[46] == 1, 'actual archive copy begins the return witness')
        self.travel(0)
        self.snapshot('01-village-before-return')
        self.target(152, 112)
        self.check(self.quest(46) == 3, 'village witness claims quest46')
        self.entry(54)
        self.snapshot('room54-greenwake-first')
        self.target(72, 256)
        self.check(self.state().quests.anchors[5] & 1, 'ordinary rest records Greenwake anchor')
        self.entry(0)

    def northern_arm(self):
        self.travel(16)
        self.snapshot('town16-before-return')
        self.target(368, 152, 2)
        self.entry(55)
        self.snapshot('room55-attic-first')
        self.target(64, 112)
        self.check(self.setting()[:2] == [1, 0], 'first support changes real dynamic geometry')
        self.entry(16)
        self.entry(55)
        self.check(self.setting()[:2] == [0, 0], 'leaving and re-entering resets incomplete supports')
        self.target(64, 112)
        self.target(176, 112)
        self.check(self.state().quests.objectives[47] & 2, 'both manual supports earn the safe-exit objective')
        self.entry(16)
        self.source_invitation(47, 101, (368, 152, 2))
        self.snapshot('town16-after-return')
        self.travel(57)
        self.snapshot('room57-sailwalk-first')
        self.cast_target(101, 102, 320, 208)
        self.check(self.state().quests.objectives[48] & 1, 'guaranteed base shrew quiet command solves the seam')
        self.target(352, 272)
        self.cast_target(self.story_form(7), 3, 400, 240)
        self.check(self.state().quests.objectives[48] & 2 and self.setting()[2], 'real base wind after manual brake moves the sail boom')
        self.travel(22)
        self.target(192, 192)
        self.check(self.quest(48) == 3, 'returned Edda report claims northern arm')
        self.snapshot('town22-after-return')

    def southern_arm(self):
        self.travel(30)
        self.snapshot('town30-before-return')
        self.entry(58)
        self.snapshot('room58-terraces-first')
        for point in ((80, 80), (160, 80), (128, 144)):
            self.target(*point)
        self.check(self.state().quests.objectives[49] & 3 == 3, 'manual shade panels and bank require no optional power')
        self.travel(30)
        self.source_invitation(49, 103, (448, 192, 1))
        self.snapshot('town30-after-return')
        self.travel(59)
        self.snapshot('room59-landing-first')
        self.target(120, 104)
        self.cast_target(103, 104, 64, 56)
        self.check(self.state().quests.objectives[50] & 1, 'guaranteed base fin-walker moves the actual skiff')
        self.travel(56)
        self.snapshot('room56-gardens-first')
        self.target(288, 256)
        self.cast_target(103, 104, 240, 96)
        self.cast_target(103, 104, 240, 208)
        self.check(self.state().quests.objectives[50] & 2, 'both real water receivers complete the clear-bank work')
        self.travel(16)
        self.target(112, 144)
        self.check(self.quest(50) == 3, 'Mira receives actual southern-arm delivery')

    def story_form(self, base):
        return next(c.form_id for c in self.live() if c.flags & 2 and base <= c.form_id <= base + 2)

    def main_route(self, arm_order='north-first'):
        self.main_only = True
        self.initialize_return()
        for arm in ((self.northern_arm, self.southern_arm) if arm_order == 'north-first' else (self.southern_arm, self.northern_arm)):
            arm()
        self.travel(60)
        self.snapshot('room60-maproom-first')
        self.target(120, 104)
        for index, (form, command, x, y) in enumerate(((self.story_form(4), 2, 56, 48), (self.story_form(1), 1, 96, 40),
                                                     (self.story_form(10), 4, 144, 40), (101, 102, 184, 48), (103, 104, 120, 104))):
            self.cast_target(form, command, x, y)
            self.check(self.return_local('phase_step') == index + 1, 'five-capability map preserves each petal across real four-slot swaps')
        self.entry(61)
        self.snapshot('room61-causeway-first')
        self.cast_target(101, 102, 64, 56)
        self.cast_target(103, 104, 176, 56)
        self.check(self.state().quests.objectives[51] & 7 == 7, 'both genuine causeway powers earn the final return witness')
        self.travel(0)
        self.target(152, 112)
        self.check(all(self.quest(q) == 3 for q in range(46, 52)), 'six required Return quests are genuinely claimed')
        self.check(self.old_ids <= {c.instance_id for c in self.live()} and len(self.live()) == self.prior_count + 2, 'main route retains all prior identities and adds only two invitations')
        self.check(bytes(self.state().equipment.equipped) == self.old_equipped, 'main route uses no new equipped gear')
        if self.minimal:
            self.check(set(self.main_selections) <= set(self.old_history + [101, 103]), 'minimal route selects no optional evolved or unearned form')
            self.check(self.collection() == sorted(self.old_history + [101, 103]), 'minimal route completes with no evolution, optional recruitment or history grant')
        self.main_only = False
        self.coverage.append('controller-main-route-' + arm_order)
        self.snapshot('02-main-return-complete')

    def cold_reboot(self, name):
        self.settle()
        before = self.state_signature()
        self.snapshot(name + '-before')
        saved = self.snapshots[name + '-before']
        self.e.close()
        self.e = ReadOnlyGameEmulator(self.rom)
        self.e.load_save(saved['sram_path'])
        self.e.reset()
        self.step(150)
        self.measured(name + '-bounded-cold-continue', lambda: (self.tap('START', 2, 90), self.settle()), cold_continue=True)
        self.check(self.state_signature() == before, 'cold SRAM-only reboot preserves exact roster, quest and equipment bytes')
        self.check(self.trial().index == 255 and not self.return_local('repeat_active'), 'cold reboot discards transient trial and repeat proof')
        self.snapshot(name + '-after')

    def lifecycle(self):
        self.travel(54)
        self.goto(72, 274, radius=4)
        self.face(1)
        self.measured('whole-native-return-rest-save', lambda: (self.tap('A'), self.settle()))
        self.check(self.get('checkpoint_spawn') == 2, 'actual Greenwake rest commits its sanctuary checkpoint')
        self.cold_reboot('main-route-cold-save')
        identities = [(c.instance_id, c.form_id) for c in self.live()]
        history = self.collection()
        quests = bytes(self.state().quests)
        self.travel(61)
        self.goto(120, 116, radius=4)
        # Stand in the genuine enemy arena. No health or position writes, and
        # no artificial hazard trigger. This is a finite actual-damage case.
        damage = []
        for _ in range(1200):
            damage.append({'hardware_frame': self.e.frame, 'hp': self.get('hp'), 'state': self.get('game_state')})
            if self.get('game_state') == DEAD:
                break
            self.step(10)
        self.cases.append({'name': 'ordinary-enemy-death', 'trace': damage})
        self.check(self.get('game_state') == DEAD, 'real Return enemy damage reaches death without injected health')
        self.snapshot('native-return-death', settle=False)
        self.measured('whole-death-controller-retry', lambda: (self.tap('A', 2, 30), self.settle()))
        self.check(self.get('game_state') == PLAY and self.get('hp') > 0, 'ordinary A retry returns to a live safe checkpoint')
        self.check([(c.instance_id, c.form_id) for c in self.live()] == identities and self.collection() == history,
                   'death and retry preserve every exact individual and history')
        self.check(bytes(self.state().quests) == quests, 'death and retry duplicate and lose no quest reward')
        self.check(self.trial().index == 255 and not self.return_local('repeat_active'), 'death and retry discard partial proof')
        self.travel(54)
        self.target(72, 256)
        self.snapshot('native-return-death-recovered')

    def run(self, scope, arm_order):
        self.boot()
        if scope != 'migration':
            self.main_route(arm_order)
        if scope in ('full', 'repeats'):
            self.collection_route()
        if scope == 'repeats':
            self.repeat_route()
        if scope == 'lifecycle':
            self.lifecycle()
        self.finished_scope = scope
        self.verify_closures()
        self.report()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('rom', 'symbols', 'output', 'source-manifest'):
        p.add_argument('--' + key, type=Path, required=True)
    for key in ('expected-rom-sha', 'expected-symbols-sha', 'expected-elf-sha', 'expected-manifest-sha'):
        p.add_argument('--' + key, required=True)
    p.add_argument('--source-root', type=Path)
    p.add_argument('--source-sram', type=Path)
    p.add_argument('--scope', choices=('migration', 'main', 'full', 'repeats', 'lifecycle'), default='migration')
    p.add_argument('--arm-order', choices=('north-first', 'south-first'), default='north-first')
    p.add_argument('--timing-mode', choices=('strict', 'collect-diagnostic'), default='strict')
    a = p.parse_args()
    r = ReturnJourney(a.rom, a.symbols, a.output, a.expected_rom_sha, a.expected_symbols_sha,
                      a.expected_elf_sha, a.source_manifest, a.expected_manifest_sha, a.source_sram, a.source_root, a.timing_mode)
    try:
        r.run(a.scope, a.arm_order)
    except Exception as exc:
        r.failures.append({'error': str(exc), 'traceback': traceback.format_exc(), 'status': r.status()})
        r.snapshot('failure', settle=False)
        raise
    finally:
        r.close_global_trace()
        r.report()
        r.e.close()
    return bool(r.failures)


if __name__ == '__main__':
    raise SystemExit(main())
