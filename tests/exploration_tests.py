#!/usr/bin/env python3
"""Independent real-ROM exploration and save-contract tests for the full campaign.

All ordinary setup and gameplay uses controller inputs. Read-only symbol probes
observe the running ARM program. Savestates preserve only controller-reached
positions; no game RAM is injected. The migration/corruption cases load explicit
SRAM input files, just as an emulator would. Frame pacing measures emulated GBA
frames and display-page flips, never host execution speed.
"""
from __future__ import annotations
import argparse
import binascii
import zlib
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from mgba_runner import Emulator

CYCLES_PER_FRAME = 280896
REFRESH_HZ = 16777216 / CYCLES_PER_FRAME
PLAY, DIALOG, PAUSE, DEAD, WIN = 1, 2, 3, 4, 5
BANK_A, BANK_B, BANK_SIZE = 0x200, 0x1a00, 6144
GROVE_CLEAR, SKY_CLEAR, CORE_CLEAR, ENDING_SEEN = 1, 2, 4, 8
SEEN_LEGACY_RECAP, SEEN_WIND_JOIN = 1, 2
LEGACY_FIXTURES = ROOT / 'tests/fixtures/legacy'


def bank_crc5(data):
    b=bytearray(data);b[16:21]=bytes(5)
    return zlib.crc32(b)&0xffffffff


def committed_banks(data):
    """Independently inspect the current explicitly encoded save5 contract."""
    result=[]
    for offset in (BANK_A,BANK_B):
        b=data[offset:offset+BANK_SIZE]
        if len(b)==BANK_SIZE and b[:4]==b'EB\x05\x20' and b[20]==0xa5 and bank_crc5(b)==int.from_bytes(b[16:20],'little'):
            c=b[32:96]
            result.append({'offset':offset,'sequence':int.from_bytes(b[8:12],'little'),
                           'room':c[0],'spawn':c[1],'chapter_flags':c[2],'bridge':c[3],
                           'torches':c[4],'relic':c[5],'camp':c[6],'optional_flags':c[7],
                           'room_flags':int.from_bytes(c[8:12],'little'),
                           'story_seen':int.from_bytes(c[12:14],'little'),'spirit':c[14]})
    return result


def newest_bank(banks):
    if len(banks) == 1:
        return banks[0]
    a, b = banks
    delta = (b['sequence'] - a['sequence']) & 0xffffffff
    return b if 0 < delta < 0x80000000 else a


def symbols(path):
    return {w[2]: int(w[0], 16) for line in Path(path).read_text().splitlines()
            if len(w := line.split()) == 3}


class ExplorationRun:
    def __init__(self, rom, symbol_path, output, v2_save=None):
        self.rom = Path(rom).resolve()
        self.symbol_path = Path(symbol_path).resolve()
        self.sym = symbols(self.symbol_path)
        self.out = Path(output).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.rom_digest = hashlib.sha256(self.rom.read_bytes()).hexdigest()
        self.symbol_digest = hashlib.sha256(self.symbol_path.read_bytes()).hexdigest()
        self.rom_bytes = self.rom.stat().st_size
        (self.out / 'tested.gba').write_bytes(self.rom.read_bytes())
        (self.out / 'tested.sym').write_bytes(self.symbol_path.read_bytes())
        self.rom = self.out / 'tested.gba'
        self.e = Emulator(self.rom)
        self.v2_save = v2_save
        self.passes, self.failures, self.inputs, self.scenes = [], [], [], []
        self.completed_v2_save = None
        self.observations = {}
        self.camera_trace = []

    def get(self, name):
        return self.e.read(self.sym[name])

    def status(self):
        names = ('game_state', 'room', 'px', 'py', 'hp', 'max_hp', 'spirit',
                 'summoned', 'bridge_open', 'torches', 'boss_hp', 'boss_armor',
                 'ability_cd', 'heal_cd', 'camera_x', 'camera_y', 'roll_ticks',
                 'roll_cd', 'relic_found', 'camp_unlocked', 'combo_step', 'frame',
                 'chapter_flags', 'room_flags', 'optional_flags', 'story_seen',
                 'loaded_save_version', 'checkpoint_spawn', 'completed')
        return {name: self.get(name) for name in names if name in self.sym}

    def step(self, count, keys=0):
        self.inputs.append({'emulator_frame': self.e.frame, 'frames': count, 'keys': keys})
        self.e.frames(count, keys)
        for _ in range(180):
            if self.get('game_state')!=6:break
            self.inputs.append({'emulator_frame':self.e.frame,'frames':1,'keys':0,'reason':'SAVE_PENDING'})
            self.e.frames(1,0)
        else:raise AssertionError('Transactional save did not finish')
        if 'camera_x' in self.sym and self.get('room') == 1:
            cx, cy = self.get('camera_x'), self.get('camera_y')
            if not (0 <= cx <= 240 and 0 <= cy <= 160):
                raise AssertionError(f'Camera escaped bounds: {cx}, {cy}')
            self.camera_trace.append({'frame': self.get('frame'), 'x': cx, 'y': cy,
                                      'player_x': self.get('px'), 'player_y': self.get('py')})

    def tap(self, keys, hold=2, release=2):
        self.step(hold, keys)
        self.step(release)

    def check(self, condition, label, fatal=True):
        if not condition:
            self.failures.append({'check': label, 'status': self.status()})
            self.write_report()
            if fatal:
                raise AssertionError(f'{label}: {self.status()}')
            print('FAIL', label, flush=True)
            return
        self.passes.append(label)
        print('PASS', label, flush=True)

    def shot(self, name):
        self.e.screenshot(self.out / f'{name}.png')

    def dialogs(self):
        for _ in range(12):
            if self.get('game_state') != DIALOG:
                return
            self.tap('A', 4, 4)
        raise AssertionError(f'Dialogue did not terminate: {self.status()}')

    def fresh(self):
        self.step(90)
        self.check(self.get('game_state') == 0, 'native ROM boots to title')
        self.tap('SELECT', 4, 4)
        self.dialogs()
        self.check(self.get('game_state') == PLAY and self.get('room') == 0,
                   'title Select starts a fresh adventure')

    def goto(self, x=None, y=None):
        """Follow a known collision-free orthogonal segment using buttons only."""
        for name, target, lower, higher in [('px', x, 'LEFT', 'RIGHT'), ('py', y, 'UP', 'DOWN')]:
            if target is None:
                continue
            stagnant = 0
            for _ in range(700):
                old = self.get(name)
                if abs(old - target) <= 1:
                    break
                if self.get('game_state') != PLAY:
                    raise AssertionError(f'Movement interrupted toward {name}={target}: {self.status()}')
                self.step(1, lower if old > target else higher)
                stagnant = stagnant + 1 if self.get(name) == old else 0
                if stagnant > 12:
                    raise AssertionError(f'Collision toward {name}={target}: {self.status()}')
            else:
                raise AssertionError(f'Movement exhausted toward {name}={target}: {self.status()}')
        self.step(2)

    def nextroom(self, target, key='UP'):
        for _ in range(450):
            if self.get('room') == target:
                break
            self.step(2, key)
        self.check(self.get('room') == target, f'controller enters room {target}')
        self.step(8)

    def snapshot(self, name):
        path = self.out / f'{name}.state'
        self.e.state(path)
        # Raw mGBA machine states do not include SRAM. Branching tests must
        # restore the checkpoint bytes paired with the controller-reached state.
        path.with_suffix('.state.sav').write_bytes(self.e.bytes(0x0e000000, 32768))
        return path

    def restore(self, path):
        self.e.load_save(path.with_suffix('.state.sav'))
        self.e.state(path, load=True)

    def save(self, name):
        path = self.out / f'{name}.sav'
        path.write_bytes(self.e.bytes(0x0e000000, 32768))
        return path

    def reopen(self, save):
        self.e.close()
        self.e = Emulator(self.rom)
        self.e.load_save(save)
        self.e.reset()
        self.step(90)

    def cadence(self, name, controls, frames=360):
        state = self.snapshot(name)
        self.shot(f'{name}-start')
        start = self.status()
        last = self.get('frame')
        page = self.e.read(0x04000000, 2) & 0x10
        deltas, flips, cycles, cameras, timing_samples = [], [], [], [], []
        states, activity = Counter(), Counter()
        peak_shots = 0
        for offset in range(frames):
            self.step(1, controls(offset))
            current = self.get('frame')
            deltas.append((current-last) & 0xffffffff)
            last = current
            current_page = self.e.read(0x04000000, 2) & 0x10
            flips.append(current_page != page)
            page = current_page
            cycles.append(self.get('render_cycles'))
            cameras.append((self.get('camera_x'), self.get('camera_y')))
            states[f'{self.get("game_state")}:{self.get("room")}'] += 1
            live_shots = sum(bool(self.e.read(self.sym['shots']+i*24+16)) for i in range(12))
            peak_shots = max(peak_shots, live_shots)
            for label, field in [('summoned_frames', 'summoned'), ('toast_frames', 'toast_ticks'),
                                 ('swing_frames', 'swing'), ('roll_frames', 'roll_ticks')]:
                if self.get(field):
                    activity[label] += 1
            if live_shots:
                activity['projectile_frames'] += 1
            if any(self.e.read(self.sym['enemy_windups']+i*4) for i in range(6)):
                activity['enemy_windup_frames'] += 1
            timing_samples.append({'hardware_offset': offset, 'simulation_frame': current,
                                   'delta': deltas[-1], 'page_flip': bool(flips[-1]),
                                   'render_cycles': cycles[-1], 'camera': list(cameras[-1]),
                                   'player': [self.get('px'), self.get('py')],
                                   'swing': self.get('swing'), 'combo': self.get('combo_step'),
                                   'toast_ticks': self.get('toast_ticks'), 'live_shots': live_shots})
        camera_changes = sum(a != b for a,b in zip(cameras,cameras[1:]))
        x_alignments = dict(Counter(x % 4 for x, y in cameras))
        valid = set(states) == {f'{start["game_state"]}:{start["room"]}'}
        result = {'scene': name, 'hardware_frames': frames,
                  'simulation_updates': sum(deltas), 'display_page_flips': sum(flips),
                  'update_delta_histogram': dict(Counter(deltas)),
                  'updates_per_emulated_second': sum(deltas)/frames*REFRESH_HZ,
                  'cycles_max': max(cycles), 'cycles_median': sorted(cycles)[len(cycles)//2],
                  'cycles_max_frame_fraction': max(cycles)/CYCLES_PER_FRAME,
                  'camera_changes': camera_changes, 'camera_x_mod4_histogram': x_alignments,
                  'camera_x_range': [min(x for x,y in cameras), max(x for x,y in cameras)],
                  'camera_y_range': [min(y for x,y in cameras), max(y for x,y in cameras)],
                  'peak_projectiles': peak_shots, 'activity_hardware_frames': dict(activity),
                  'observed_states': dict(states),
                  'scene_stayed_valid': valid,
                  'anomaly_samples': [v for v in timing_samples if v['delta'] != 1 or v['render_cycles'] >= CYCLES_PER_FRAME],
                  'one_update_and_present_per_frame': valid and all(d == 1 for d in deltas) and all(flips),
                  'initial': start, 'final': self.status()}
        self.scenes.append(result)
        self.shot(f'{name}-end')
        self.restore(state)
        self.write_report()
        print('CADENCE', json.dumps(result), flush=True)
        return result

    def viewport_alignment_case(self):
        """Compare displayed bitmap VRAM with the original ROM atlas exactly.

        Hardware sprites are composited separately, so they cannot hide a bad
        background copy. All160 rows participate; only the small authored
        bridge/trial floor-decoration bounds are masked. Transient text expires
        before comparison, and no HUD or unused strip is excluded.
        """
        state = self.snapshot('viewport-alignment-start')
        self.goto(y=280)
        atlas = self.e.bytes(self.sym['overworld_bitmap'], 480*320)
        observed = {}
        for _ in range(14):
            self.step(150)
            cx, cy = self.get('camera_x'), self.get('camera_y')
            phase = cx % 4
            if phase not in observed:
                page = 0x0600a000 if self.e.read(0x04000000, 2) & 0x10 else 0x06000000
                actual = self.e.bytes(page, 160*240)
                expected = b''.join(atlas[(cy+y)*480+cx:(cy+y)*480+cx+240] for y in range(160))
                from fullscreen_tests import FullscreenRun
                mask=FullscreenRun.bitmap_mask(self,cx,cy)
                mismatch = sum(a != b for i,(a,b) in enumerate(zip(actual, expected)) if not mask[i])
                observed[phase] = {'camera': [cx,cy], 'compared_pixels': len(actual),
                                   'mismatched_pixels': mismatch}
                self.check(mismatch == 0,
                           f'displayed viewport matches ROM atlas exactly at camera x mod 4 = {phase}')
                self.shot(f'viewport-alignment-{phase}')
            if len(observed) == 4:
                break
            self.step(1, 'RIGHT')
        self.check(len(observed) == 4, 'pixel verification covers every viewport word alignment')
        self.observations['viewport_pixel_alignment'] = observed
        self.restore(state)

    def ranged_attack_case(self):
        state = self.snapshot('ranger-probe-start')
        index = 1  # Southern ranger: (326,238), checked from live enemy data.
        address = self.sym['enemies'] + index*20
        self.check(self.e.read(address+16) == 2 and self.e.read(address+8) > 0,
                   'controller route reaches a live ranged enemy')
        wind = lambda: self.e.read(self.sym['enemy_windups'] + index*4)
        aim = lambda: (self.e.read(self.sym['enemy_aimx'] + index*4),
                       self.e.read(self.sym['enemy_aimy'] + index*4))
        started = fired = None
        prior = wind()
        telegraph_samples = []
        fixed_aim = None
        for _ in range(700):
            self.step(1, 'LEFT' if started is not None and self.get('frame')-started < 20 else 0)
            current = wind()
            if prior == 0 and current == 30:
                started, fixed_aim = self.get('frame'), aim()
                self.shot('09-ranger-telegraph')
            if started is not None:
                telegraph_samples.append({'frame': self.get('frame'), 'windup': current,
                                          'aim': list(aim()), 'hp': self.get('hp')})
                if prior == 1 and current == 0:
                    fired = self.get('frame')
                    new_projectiles = sum(self.e.read(self.sym['shots']+i*24+16) == 90
                                          and self.e.read(self.sym['shots']+i*24+20) == 1 for i in range(12))
                    self.check(new_projectiles > 0, 'ranger releases its projectile after the telegraph')
                    break
            prior = current
        self.check(started is not None and fired is not None and fired-started == 30,
                   'ranger gives a full 30-update warning before firing')
        self.check(all(tuple(v['aim']) == fixed_aim for v in telegraph_samples),
                   'ranged aim remains locked throughout the telegraph')
        self.observations['ranged_telegraph'] = {'start_update': started, 'fire_update': fired,
                                                'aim_locked': all(tuple(v['aim']) == fixed_aim for v in telegraph_samples),
                                                'samples': telegraph_samples}
        self.shot('10-ranger-fired')
        self.restore(state)

    def fixture(self, name):
        path = LEGACY_FIXTURES / name
        manifest = json.loads((LEGACY_FIXTURES / 'manifest.json').read_text())
        expected = next(item for item in manifest['fixtures'] if item['file'] == name)
        data = path.read_bytes()
        self.check(len(data) == manifest['size_bytes_each']
                   and hashlib.sha256(data).hexdigest() == expected['sha256'],
                   f'authentic legacy fixture has its pinned size and hash: {name}')
        return path

    def legacy_case(self, source, version, complete=False):
        source = Path(source)
        original = source.read_bytes()
        digest = hashlib.sha256(original).hexdigest()
        self.reopen(source)
        self.check(self.get('has_save') == 1, f'version {version} checkpoint is recognized: {source.name}')
        self.tap('START', 4, 4)
        self.check(self.get('loaded_save_version') == version and self.get('quest_started') == 1,
                   f'version {version} migration records its source and starts the quest')
        if complete:
            self.check(self.get('game_state') == DIALOG and self.get('room') == 0
                       and self.get('chapter_flags') == GROVE_CLEAR and self.get('completed') == 0,
                       f'completed version {version} resumes the pending grove recap in the village')
            self.check(self.get('story_seen') & (SEEN_LEGACY_RECAP | SEEN_WIND_JOIN) == 0,
                       f'completed version {version} does not mark its recap seen prematurely')
        else:
            self.check(self.get('room') == original[3] and self.get('bridge_open') == original[4]
                       and self.get('torches') == original[5],
                       f'version {version} migration preserves area and puzzle progression')
        relic, camp = (original[8], original[9]) if version == 3 else (0, 0)
        self.check(self.get('max_hp') == (8 if relic else 6)
                   and self.get('relic_found') == relic and self.get('camp_unlocked') == camp,
                   f'version {version} migration preserves or safely defaults exploration rewards')
        self.check(self.e.bytes(0x0e000000, 13) == original[:13],
                   f'version {version} migration leaves all legacy bytes untouched')
        banks = committed_banks(self.e.bytes(0x0e000000, 32768))
        self.check(bool(banks), f'continued version {version} checkpoint creates a committed version 5 bank')
        if complete:
            self.dialogs()
            self.check(self.get('game_state') == PLAY and self.get('room') == 0
                       and self.get('chapter_flags') == GROVE_CLEAR and self.get('completed') == 0
                       and self.get('story_seen') & 3 == 3,
                       f'completed version {version} continues the campaign after its recap')
            spirits = []
            for _ in range(3):
                self.tap('L', 4, 4)
                spirits.append(self.get('spirit'))
            self.check(spirits == [1, 2, 0],
                       f'completed version {version} unlocks wind while stone remains locked')
        elif camp:
            self.check(self.get('px') == 120 and self.get('py') == 264,
                       'legacy camp checkpoint migrates to the explicit version 5 camp spawn')
        name = f'migrated-v{version}-' + ('completed' if complete else 'relic-camp' if relic else 'bridge')
        migrated = self.save(name)
        self.shot(name)
        self.reopen(migrated)
        self.tap('START', 4, 4)
        self.check(self.get('loaded_save_version') == 5 and self.get('game_state') == PLAY
                   and self.get('room') == (0 if complete else original[3])
                   and self.get('max_hp') == (8 if relic else 6)
                   and self.get('bridge_open') == original[4],
                   f'migrated version {version} checkpoint survives an independent version 5 reopen')
        self.check(hashlib.sha256(source.read_bytes()).hexdigest() == digest,
                   f'loading version {version} leaves its source input file unchanged')
        self.observations.setdefault('legacy_saves', []).append({
            'source': str(source.relative_to(ROOT) if source.is_relative_to(ROOT) else source),
            'sha256': digest, 'source_header': list(original[:13]),
            'version': version, 'completed_chapter': complete,
            'v5_banks_after_continue': banks})
        return migrated

    def migration_cases(self):
        # Authentic, hash-pinned SRAM inputs are distinct from the ordinary
        # controller-only route above. CLI overrides remain supported.
        source = self.v2_save or self.fixture('baseline-v2-bridge.sav')
        migrated = self.legacy_case(source, 2)
        complete = self.completed_v2_save or self.fixture('v2-completed/checkpoint.sav')
        self.legacy_case(complete, 2, complete=True)
        self.legacy_case(self.fixture('migrated-v3.sav'), 3)
        self.legacy_case(self.fixture('relic-camp-checkpoint.sav'), 3)
        self.legacy_case(self.fixture('full-journey/checkpoint.sav'), 3, complete=True)

        # Preserve the legacy checksum/field-validation regressions. These
        # fixtures contain no v5 banks, so no valid newer bank can mask them.
        for name, label in [
            ('explicit-corrupt-copy.sav', 'corrupted legacy version 3 checksum'),
            ('invalid-out-of-range-room.sav', 'legacy version 3 out-of-range room'),
            ('invalid-invalid-camp-flag.sav', 'legacy version 3 invalid camp flag'),
            ('invalid-inconsistent-maximum-health.sav', 'legacy version 3 inconsistent maximum health'),
            ('invalid-unknown-reserved-flag.sav', 'legacy version 3 unknown reserved flag'),
        ]:
            self.reopen(self.fixture(name))
            self.check(self.get('has_save') == 0, f'rejects {label}')

        # Corrupt v5 records, not the preserved legacy checksum. A checkpoint
        # earned in this run has no valid legacy fallback and has both banks.
        checkpoint = self.out / 'relic-camp-checkpoint.sav'
        original = checkpoint.read_bytes()
        banks = committed_banks(original)
        self.check(len(banks) == 2 and original[:2] != b'EB',
                   'fresh controller-earned checkpoint has two version 5 banks and no legacy fallback')
        latest = newest_bank(banks)
        older = next(bank for bank in banks if bank is not latest)
        data = bytearray(original)
        data[latest['offset'] + 16] ^= 1
        fallback = self.out / 'v5-newest-bank-corrupt.sav'
        fallback.write_bytes(data)
        self.reopen(fallback)
        self.check(self.get('has_save') == 1, 'one corrupt version 5 bank preserves the older checkpoint')
        self.tap('START', 4, 4)
        self.check(self.get('loaded_save_version') == 5 and self.get('room') == older['room']
                   and self.get('checkpoint_spawn') == older['spawn']
                   and self.get('relic_found') == older['relic']
                   and self.get('camp_unlocked') == older['camp']
                   and self.get('bridge_open') == older['bridge'],
                   'version 5 corruption fallback restores the older bank progression and spawn')
        for bank in banks:
            data[bank['offset'] + 16] = original[bank['offset'] + 16] ^ 1
        corrupt = self.out / 'v5-both-banks-corrupt.sav'
        corrupt.write_bytes(data)
        self.reopen(corrupt)
        self.check(self.get('has_save') == 0, 'corrupted checksums in both version 5 banks are rejected')
        self.observations['version4_corruption'] = {
            'source_banks': banks, 'newest_corrupted_offset': latest['offset'],
            'fallback_bank': older,
            'method': 'Explicit SRAM-file copies only; newest bank CRC, then both bank CRCs are corrupted'}
        for label, offset, value in [
            ('out-of-range room', 32, 14), ('invalid camp flag', 38, 2),
            ('unknown reserved flag', 47, 1), ('nonsequential chapter flags', 34, 2),
            ('locked spirit selection', 46, 3), ('invalid grove spawn', 33, 5),
        ]:
            data = bytearray(original)
            for bank in banks:
                base = bank['offset']
                data[base + offset] = value
                data[base + 30:base + 32] = binascii.crc_hqx(data[base:base + 16], 0xffff).to_bytes(2, 'little')
            invalid = self.out / ('v5-invalid-' + label.replace(' ', '-') + '.sav')
            invalid.write_bytes(data)
            self.reopen(invalid)
            self.check(self.get('has_save') == 0,
                       f'version 5 rejects {label} in both banks even with valid checksums')

        # Migration keeps a last-resort legacy copy even if every new bank is
        # damaged. This is separate from rejection without a legacy fallback.
        data = bytearray(migrated.read_bytes())
        for bank in committed_banks(data):
            data[bank['offset'] + 16] ^= 1
        legacy_fallback = self.out / 'v5-corrupt-with-legacy-fallback.sav'
        legacy_fallback.write_bytes(data)
        self.reopen(legacy_fallback)
        self.check(self.get('has_save') == 1, 'both damaged version 5 banks retain a valid legacy fallback')
        self.tap('START', 4, 4)
        self.check(self.get('loaded_save_version') == 2 and self.get('bridge_open') == 1,
                   'damaged migrated banks recover the preserved legacy bridge checkpoint')

        self.reopen(checkpoint)
        self.tap('SELECT', 4, 4)
        self.dialogs()
        self.check(self.get('room') == 0 and self.get('max_hp') == 6
                   and self.get('relic_found') == self.get('camp_unlocked') == self.get('bridge_open') == 0
                   and self.get('chapter_flags') == self.get('room_flags') == self.get('story_seen') == 0,
                   'title Select starts fresh and clears upgraded exploration and campaign progression')
        self.e.reset()
        self.step(90)
        self.tap('START', 4, 4)
        self.check(self.get('room') == 0 and self.get('max_hp') == 6 and self.get('relic_found') == 0
                   and self.get('loaded_save_version') == 5,
                   'fresh-adventure replacement checkpoint persists after another boot')

    def write_report(self):
        result = {'rom_sha256': self.rom_digest,
                  'rom_bytes': self.rom_bytes,
                  'symbols_sha256': self.symbol_digest,
                  'emulator': 'mGBA 0.10.5 ARM ROM execution',
                  'ordinary_gameplay_controller_only': True,
                  'game_ram_injection': False,
                  'savestate_policy': 'Controller-reached machine states are restored with their paired SRAM snapshots',
                  'pacing_method': 'One emulated GBA frame, read simulation frame and DISPCNT page flip',
                  'scope_limit': 'Representative emulator tests, not exhaustive or physical-hardware validation',
                  'passes': self.passes, 'failures': self.failures,
                  'observations': self.observations, 'scenes': self.scenes,
                  'camera_trace': self.camera_trace,
                  'input_log': self.inputs, 'final': self.status()}
        (self.out / 'exploration-tests.json').write_text(json.dumps(result, indent=2)+'\n')

    def run(self):
        self.fresh()
        self.shot('01-village')
        self.tap('START', 4, 4)
        self.check(self.get('game_state') == PAUSE, 'Start opens the journal')
        before = self.get('journal_tab')
        self.tap('A', 4, 4)
        self.check(self.get('game_state') == PAUSE and self.get('journal_tab') != before,
                   'journal A switches the selected guide tab')
        self.shot('01-journal-map')
        self.tap('A', 4, 4)
        self.check(self.get('journal_tab') == 2, 'journal includes the companion guide as its third tab')
        self.shot('01-journal-companions')
        self.tap('A', 4, 4)
        self.check(self.get('journal_tab') == 3, 'journal includes companion growth as its fourth tab')
        self.tap('A',4,4)
        self.check(self.get('journal_tab') == before, 'journal cycles through four tabs and returns to quest controls')
        self.shot('01-journal-controls')
        self.tap('B', 4, 4)
        self.nextroom(1)
        self.check(self.get('px') == 240 and self.get('py') > 270,
                   'forest arrival uses scrolling-world coordinates')
        self.check(self.get('camera_y') == 160, 'camera clamps at the south edge')
        self.shot('02-forest-arrival')
        self.tap('START', 4, 4)
        before_map = self.e.screenshot().tobytes()
        self.shot('02-forest-map')
        self.tap('A', 4, 4)
        self.check(self.e.screenshot().tobytes() != before_map,
                   'forest journal switches from the map to the companion guide')
        self.tap('B', 4, 4)
        arrival = self.snapshot('arrival')
        self.goto(y=248)
        self.goto(x=118)
        self.step(30)
        self.check(self.get('camera_x') == 0, 'camera clamps at the west edge')
        self.tap('A', 4, 4)
        self.dialogs()
        self.check(self.get('camp_unlocked') == 1 and self.get('hp') == self.get('max_hp'),
                   'campfire interaction heals and activates the checkpoint')
        self.shot('03-campfire')
        self.goto(x=240)
        self.goto(y=180)
        self.step(12, 'UP')
        self.check(self.get('bridge_open') == 0 and self.get('py') >= 176,
                   'closed river blocks ordinary movement')
        self.step(2, 'UP+SELECT')
        self.check(self.get('game_state') == PLAY and self.get('roll_ticks') > 0,
                   'Select starts a dodge roll without opening the journal')
        self.step(14, 'UP')
        self.check(self.get('py') >= 176 and self.get('roll_ticks') == 0,
                   'dodge roll cannot tunnel through the closed river')
        oldcd = self.get('roll_cd')
        self.tap('SELECT')
        self.check(0 < self.get('roll_cd') < oldcd and self.get('roll_ticks') == 0,
                   'a second Select cannot bypass the dodge cooldown')
        self.step(self.get('roll_cd') + 2)
        self.tap('R', 4, 4)
        self.check(self.get('bridge_open') == 0, 'unsummoned power cannot grow the bridge')
        self.tap('B', 4, 4)
        self.tap('R', 4, 4)
        self.check(self.get('bridge_open') == 0, 'fire power cannot grow the nature bridge')
        self.tap('L', 4, 4)
        self.step(self.get('ability_cd') + 2)
        self.tap('R', 4, 4)
        self.check(self.get('bridge_open') == 1, 'summoned Midori grows the bridge')
        self.dialogs()
        self.shot('04-grown-bridge')
        self.goto(x=218)
        self.step(20, 'UP')
        self.check(self.get('py') >= 176,
                   'open bridge does not make the adjacent river passable')
        self.goto(x=240)
        self.goto(y=92)
        self.check(self.get('py') < 156, 'grown bridge permits crossing to the north bank')
        self.check(self.get('camera_y') < 160, 'camera follows northward movement')
        self.goto(x=92)
        self.goto(y=72)
        self.tap('A', 4, 4)
        self.dialogs()
        self.check(self.get('relic_found') == 1 and self.get('max_hp') == 8 and self.get('hp') == 8,
                   'optional grove chest grants two permanent hearts and full healing')
        self.shot('05-relic-chest')
        hud = [(self.e.read(0x07000000+i*8+2,2)&511,self.e.read(0x07000000+i*8,2)&255) for i in range(11)]
        self.step(30)
        self.tap('A', 4, 4)
        self.dialogs()
        self.check(self.get('max_hp') == 8 and self.get('relic_found') == 1,
                   'reopening the chest cannot grant the relic twice')
        self.goto(y=92)
        self.goto(x=368)
        self.step(30)
        self.check(self.get('camera_x') == 240, 'camera clamps at the east edge')
        self.goto(y=48)
        self.step(30)
        self.check(self.get('camera_y') == 0, 'camera clamps at the north edge')
        self.check([(self.e.read(0x07000000+i*8+2,2)&511,self.e.read(0x07000000+i*8,2)&255) for i in range(11)] == hud,
                   'floating hearts, companion and action remain fixed while the world scrolls')
        self.shot('06-northeast-temple-gate')
        self.nextroom(2)
        self.dialogs()
        self.check(self.get('camera_x') == 0 and self.get('camera_y') == 0,
                   'entering the temple resets the camera for a fixed room')
        self.nextroom(1, 'DOWN')
        self.check(self.get('px') == 368 and self.get('py') == 43,
                   'returning from the temple arrives at the northeast forest gate')
        entrance = self.save('north-entrance-checkpoint')
        self.reopen(entrance)
        self.tap('START', 4, 4)
        self.check(self.get('room') == 1 and self.get('px') == 368 and self.get('py') == 43,
                   'version 5 reload preserves the recorded north entrance instead of moving to an older camp')
        self.goto(y=92)
        self.goto(x=240)
        self.goto(y=248)
        self.goto(x=118)
        self.tap('A', 4, 4)
        self.dialogs()
        self.check(self.get('checkpoint_spawn') == 2,
                   'revisiting the campfire records the explicit camp checkpoint spawn')
        save = self.save('relic-camp-checkpoint')
        self.reopen(save)
        self.check(self.get('has_save') == 1, 'independent emulator recognizes the version 5 checkpoint')
        self.tap('START', 4, 4)
        self.check(self.get('room') == 1 and self.get('px') == 120 and self.get('py') == 264,
                   'continued forest checkpoint resumes at the activated campfire')
        self.check(self.get('relic_found') == 1 and self.get('max_hp') == 8 and self.get('hp') == 8,
                   'version 5 reload preserves relic capacity and restores full health')
        self.check(self.get('bridge_open') == 1 and self.get('camp_unlocked') == 1,
                   'version 5 reload preserves bridge and camp progression')
        self.shot('07-reloaded-camp')
        self.goto(y=248)
        self.goto(x=240)
        self.nextroom(0, 'DOWN')
        self.nextroom(1)
        self.check(self.get('px') == 240 and 283 <= self.get('py') <= 287 and self.get('camp_unlocked') == 1,
                   'ordinary village reentry uses the physical southern entrance even after unlocking camp')
        self.reopen(save)
        self.tap('START', 4, 4)
        # Take ordinary contact damage, heal, then die and retry at the camp.
        self.goto(x=180)
        for _ in range(300):
            if self.get('hp') < 8:
                break
            self.step(4)
        self.check(0 < self.get('hp') < 8, 'forest enemy contact causes real damage')
        self.goto(x=120)
        self.tap('A', 4, 4)
        self.dialogs()
        self.check(self.get('hp') == 8, 'returning to the campfire heals actual damage')
        self.goto(x=180)
        for _ in range(1000):
            if self.get('game_state') == DEAD:
                break
            self.step(4)
        self.check(self.get('game_state') == DEAD and self.get('hp') == 0,
                   'forest threats can naturally defeat an idle player')
        self.shot('08-forest-death')
        self.tap('A', 4, 4)
        self.check(self.get('game_state') == PLAY and self.get('px') == 120 and self.get('py') == 264,
                   'death retry returns to the campfire checkpoint')
        self.check(self.get('hp') == 8 and self.get('max_hp') == 8 and self.get('relic_found') == 1,
                   'death retry preserves the relic and restores all eight hearts')
        self.check(self.get('roll_ticks') == 0 and self.get('roll_cd') == 0,
                   'death retry clears dodge state and cooldown')
        self.goto(y=248)
        self.goto(x=240)
        self.viewport_alignment_case()
        self.tap('B', 4, 4)
        self.ranged_attack_case()
        horizontal = self.cadence('scrolling-horizontal-sprites',
                                 lambda n: ('RIGHT' if (n//48)%2 == 0 else 'LEFT') + ('+A' if n%24 < 2 else ''))
        self.check(horizontal['camera_changes'] > 100,
                   'horizontal stress window actually scrolls the camera')
        self.check(horizontal['one_update_and_present_per_frame'],
                   'horizontal scrolling with active sprites presents every hardware frame', fatal=False)
        vertical = self.cadence('scrolling-vertical-sprites',
                               lambda n: ('UP' if (n//48)%2 == 0 else 'DOWN') + ('+A' if n%24 < 2 else ''))
        self.check(vertical['camera_changes'] > 100,
                   'vertical stress window actually scrolls the camera')
        self.check(vertical['one_update_and_present_per_frame'],
                   'vertical scrolling with active sprites presents every hardware frame', fatal=False)
        diagonal = self.cadence('scrolling-diagonal-sprites',
                               lambda n: ('UP+LEFT' if (n//48)%2 == 0 else 'DOWN+RIGHT') + ('+A' if n%24 < 2 else ''))
        self.check(diagonal['camera_x_range'][1]-diagonal['camera_x_range'][0] > 15
                   and diagonal['camera_y_range'][1]-diagonal['camera_y_range'][0] > 15,
                   'diagonal stress window scrolls both camera axes together')
        self.check(diagonal['one_update_and_present_per_frame'],
                   'diagonal scrolling with active sprites presents every hardware frame', fatal=False)
        rolls = self.cadence('scrolling-dodge-roll',
                             lambda n: ('RIGHT' if (n//48)%2 == 0 else 'LEFT') + ('+SELECT' if n%48 == 0 else ''))
        self.check(rolls['activity_hardware_frames'].get('roll_frames', 0) >= 60,
                   'dodge stress window contains repeated active rolls')
        self.check(rolls['one_update_and_present_per_frame'],
                   'scrolling dodge rolls and projectiles present every hardware frame', fatal=False)
        state = self.snapshot('combo-start')
        combo_states = []
        for n in range(150):
            self.step(1, 'A' if n%15 == 0 else 0)
            combo_states.append(self.get('combo_step'))
        self.observations['combo_step_histogram'] = dict(Counter(combo_states))
        self.check({1, 2, 3}.issubset(combo_states),
                   'timed repeated A inputs advance through three sword-combo stages')
        self.restore(state)
        self.migration_cases()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, default=ROOT/'build/emberbond.gba')
    p.add_argument('--symbols', type=Path, default=ROOT/'build/emberbond.sym')
    p.add_argument('--output', type=Path, default=ROOT/'build/exploration')
    p.add_argument('--v2-save', type=Path, help='Authentic v2 bridge SRAM override; defaults to the hash-pinned portable legacy fixture')
    p.add_argument('--v2-completed-save', type=Path, help='Optional authentic completed version 2 SRAM')
    a = p.parse_args()
    run = ExplorationRun(a.rom, a.symbols, a.output, a.v2_save)
    run.completed_v2_save = a.v2_completed_save
    try:
        run.run()
    except Exception as exc:
        run.failures.append({'error': str(exc), 'status': run.status()})
        raise
    finally:
        run.write_report()
        run.e.close()
    return int(bool(run.failures))


if __name__ == '__main__':
    raise SystemExit(main())
