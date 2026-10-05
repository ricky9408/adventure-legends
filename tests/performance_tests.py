#!/usr/bin/env python3
"""Measure game cadence in emulated GBA frames, never host execution FPS.

Scene setup uses controller input only. Each capture restores a controller-reached
mGBA savestate afterward, so stress windows cannot alter the traversal. No game
RAM is written. ROM/symbol overrides let the same test compare immutable builds.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from mgba_runner import Emulator

GBA_CLOCK_HZ = 16777216
GBA_CYCLES_PER_FRAME = 280896
GBA_REFRESH_HZ = GBA_CLOCK_HZ / GBA_CYCLES_PER_FRAME


def read_symbols(path):
    return {words[2]: int(words[0], 16) for line in Path(path).read_text().splitlines()
            if len(words := line.split()) == 3}


class PerformanceRun:
    def __init__(self, rom, symbols, output, frames=360):
        self.rom = Path(rom).resolve()
        self.symbol_path = Path(symbols).resolve()
        self.sym = read_symbols(self.symbol_path)
        self.output = Path(output).resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.e = Emulator(self.rom)
        self.capture_frames = frames
        self.scenes = []
        self.motion = None
        self.transitions = []
        self.route = []

    def get(self, name):
        return self.e.read(self.sym[name])

    def sampled_cycle_summary(self, samples, worst_before):
        if not samples:
            return None
        values = sorted(samples)
        return {'measurement': 'hardware timer 2/3: input + update + render, excluding VBlank wait and OAM commit',
                'sampling': 'last completed timing value read once per emulated hardware frame; long work can leave repeated previous values',
                'sample_count': len(values), 'minimum': values[0],
                'median': values[len(values) // 2], 'p95': values[int((len(values) - 1) * 0.95)],
                'maximum': values[-1], 'maximum_fraction_of_frame_budget': values[-1] / GBA_CYCLES_PER_FRAME,
                'engine_worst_since_boot_before': worst_before,
                'engine_worst_since_boot_after': self.get('worst_render_cycles')}

    def status(self):
        return {name: self.get(name) for name in
                ('game_state', 'room', 'px', 'py', 'hp', 'spirit', 'summoned',
                 'bridge_open', 'torches', 'boss_hp', 'boss_armor', 'ability_cd', 'toast_ticks', 'frame')}

    def step(self, frames, key=0):
        self.e.frames(frames, key)

    def tap(self, key):
        # Deliberately long enough for the original 15 Hz pause screen.
        self.step(10, key)
        self.step(10)

    def require(self, condition, label):
        if not condition:
            raise AssertionError(f'{label}: {self.status()}')
        self.route.append(label)

    def dialogs(self):
        for _ in range(10):
            if self.get('game_state') != 2:
                return
            self.tap('A')
        raise AssertionError(f'dialogue did not terminate: {self.status()}')

    def goto(self, x=None, y=None):
        for name, target, lo, hi in [('px', x, 'LEFT', 'RIGHT'), ('py', y, 'UP', 'DOWN')]:
            if target is None:
                continue
            for _ in range(450):
                value = self.get(name)
                if abs(value - target) <= 1:
                    break
                self.step(2, lo if value > target else hi)
            else:
                raise AssertionError(f'movement blocked {name}={target}: {self.status()}')
        self.step(4)

    def nextroom(self, target):
        if self.get('room') == 1 and target == 2:
            self.goto(x=240)
            self.goto(y=92)
            self.goto(x=368)
        for _ in range(450):
            if self.get('room') == target:
                break
            self.step(2, 'UP')
        self.require(self.get('room') == target, f'controller entered room {target}')
        self.step(8)

    def defend(self, frames):
        for _ in range((frames + 23) // 24):
            living = []
            for i in range(6):
                address = self.sym['enemies'] + i * 20
                x, y, hp = [self.e.read(address + offset) for offset in (0, 4, 8)]
                if hp:
                    living.append((abs(x - self.get('px')) + abs(y - self.get('py')), x, y))
            if living:
                _, x, y = min(living)
                dx, dy = x - self.get('px'), y - self.get('py')
                key = ('LEFT' if dx < 0 else 'RIGHT') if abs(dx) > abs(dy) else ('UP' if dy < 0 else 'DOWN')
                self.step(2, key)
                self.tap('A')
                self.step(2)
            else:
                self.step(24)

    def measure(self, name, target_interval=1, controls=None):
        """Sample frame counter and displayed bitmap page at every hardware frame.

        target_interval=1 means 59.7275 Hz; 2 permits intentionally paced 29.864 Hz.
        The `frame` symbol increments at update() entry. Display flips measure
        completed/presented rendering independently, not necessarily new artwork.
        """
        state_path = self.output / f'{name}.state'
        self.step(12)
        self.e.state(state_path)
        self.e.screenshot(self.output / f'{name}-start.png')
        initial = self.status()
        previous = self.get('frame')
        display_page = self.e.read(0x04000000, 2) & 0x10
        start_frame = self.e.frame
        cycle_samples = []
        worst_before = self.get('worst_render_cycles') if 'render_cycles' in self.sym else None
        update_events, present_events, deltas, observed_states = [], [], [], Counter()
        unchanged, longest_stall = 0, 0
        scene_activity = Counter()
        peak_projectiles = 0
        for offset in range(1, self.capture_frames + 1):
            self.e.frames(1, controls(offset) if controls else 0)
            counter = self.get('frame')
            if 'render_cycles' in self.sym:
                cycle_samples.append(self.get('render_cycles'))
            delta = (counter - previous) & 0xffffffff
            if delta > 16:
                raise AssertionError(f'Unexpected frame reset during {name}: {previous} -> {counter}')
            previous = counter
            deltas.append(delta)
            if delta:
                update_events.append(offset)
                unchanged = 0
            else:
                unchanged += 1
                longest_stall = max(longest_stall, unchanged)
            next_page = self.e.read(0x04000000, 2) & 0x10
            if next_page != display_page:
                present_events.append(offset)
            display_page = next_page
            observed_states[f'{self.get("game_state")}:{self.get("room")}'] += 1
            for label, symbol in [('summoned_frames', 'summoned'), ('toast_frames', 'toast_ticks'),
                                  ('cooldown_frames', 'ability_cd'), ('boss_exposed_frames', 'boss_armor')]:
                if self.get(symbol):
                    scene_activity[label] += 1
            live_projectiles = sum(bool(self.e.read(self.sym['shots'] + i * 24 + 16)) for i in range(12))
            peak_projectiles = max(peak_projectiles, live_projectiles)
            if live_projectiles:
                scene_activity['projectile_frames'] += 1
        elapsed = self.e.frame - start_frame
        assert elapsed == self.capture_frames, (elapsed, self.capture_frames)
        intervals = [b - a for a, b in zip(update_events, update_events[1:])]
        present_intervals = [b - a for a, b in zip(present_events, present_events[1:])]
        update_count = sum(deltas)
        valid_scene = set(observed_states) == {f'{initial["game_state"]}:{initial["room"]}'}
        target_met = (valid_scene and update_count >= elapsed // target_interval - 1
                      and max(intervals, default=elapsed) <= target_interval
                      and longest_stall < target_interval)
        result = {
            'scene': name,
            'emulated_frames': elapsed,
            'emulated_seconds': elapsed / GBA_REFRESH_HZ,
            'update_count': update_count,
            'updates_per_emulated_second': update_count / elapsed * GBA_REFRESH_HZ,
            'update_intervals_hardware_frames': dict(sorted(Counter(intervals).items())),
            'update_deltas_per_hardware_frame': dict(sorted(Counter(deltas).items())),
            'longest_update_interval_frames': max(intervals, default=None),
            'longest_stall_frames_without_update': longest_stall,
            'longest_stall_ms': longest_stall / GBA_REFRESH_HZ * 1000,
            'display_page_flip_count': len(present_events),
            'display_page_flip_intervals_hardware_frames': dict(sorted(Counter(present_intervals).items())),
            'target': {'maximum_interval_hardware_frames': target_interval,
                       'minimum_updates_per_emulated_second': GBA_REFRESH_HZ / target_interval,
                       'met': target_met},
            'scene_stayed_valid': valid_scene,
            'observed_state_room_frames': dict(observed_states),
            'activity_hardware_frames': dict(scene_activity),
            'peak_live_projectiles': peak_projectiles,
            'render_cycles': self.sampled_cycle_summary(cycle_samples, worst_before),
            'initial': initial,
            'final': self.status(),
            'controller_input': 'none' if controls is None else 'scripted, see scenario definition',
            'update_event_offsets': update_events,
            'display_page_flip_offsets': present_events,
        }
        self.e.screenshot(self.output / f'{name}-end.png')
        self.scenes.append(result)
        print(f'{name}: {update_count}/{elapsed} updates; '
              f'{result["updates_per_emulated_second"]:.3f} Hz; '
              f'intervals {result["update_intervals_hardware_frames"]}; '
              f'presented {len(present_events)}; target={target_met}', flush=True)
        self.e.state(state_path, load=True)
        self.write_report()
        return result

    def measure_transition(self, name, key, expected_state):
        """Capture cold-cache/input latency instead of hiding it in scene warmup."""
        previous = self.get('frame')
        cycle_samples = []
        worst_before = self.get('worst_render_cycles') if 'render_cycles' in self.sym else None
        events, states = [], []
        no_update = longest_stall = resets = 0
        for offset in range(1, 61):
            self.e.frames(1, key if offset <= 10 else 0)
            counter = self.get('frame')
            state = self.get('game_state')
            if 'render_cycles' in self.sym:
                cycle_samples.append(self.get('render_cycles'))
            states.append(state)
            if counter != previous:
                events.append(offset)
                no_update = 0
                if counter < previous:
                    resets += 1
            else:
                no_update += 1
                longest_stall = max(longest_stall, no_update)
            previous = counter
        intervals = [b - a for a, b in zip(events, events[1:])]
        latency = next((i + 1 for i, state in enumerate(states) if state == expected_state), None)
        result = {'transition': name, 'controller_input': key, 'emulated_frames': 60,
                  'expected_state': expected_state, 'first_expected_state_hardware_frame': latency,
                  'frame_counter_resets': resets,
                  'render_cycles': self.sampled_cycle_summary(cycle_samples, worst_before),
                  'update_intervals_hardware_frames': dict(sorted(Counter(intervals).items())),
                  'longest_update_interval_frames': max(intervals, default=None),
                  'longest_stall_frames_without_update': longest_stall,
                  'state_sequence': states,
                  'target': {'maximum_input_latency_hardware_frames': 2,
                             'maximum_update_gap_hardware_frames': 2,
                             'met': latency is not None and latency <= 2
                                    and max(intervals, default=60) <= 2 and longest_stall < 2}}
        self.transitions.append(result)
        self.e.screenshot(self.output / f'{name}-end.png')
        print(f'{name}: input latency={latency} hardware frame(s); '
              f'max update gap={result["longest_update_interval_frames"]}; '
              f'target={result["target"]["met"]}', flush=True)
        self.require(self.get('game_state') == expected_state, f'controller transition {name}')
        self.write_report()

    def measure_motion(self):
        """Probe an obstacle-free village patch through input and readback only."""
        checkpoint = self.output / 'village-motion-checkpoint.state'
        self.e.state(checkpoint)
        probes = []
        for key in ('RIGHT', 'LEFT', 'UP', 'RIGHT+UP', 'LEFT+UP'):
            self.e.state(checkpoint, load=True)
            start = self.status()
            steps = Counter()
            previous = (start['px'], start['py'])
            for _ in range(24):
                self.e.frames(1, key)
                point = (self.get('px'), self.get('py'))
                steps[f'{point[0] - previous[0]}:{point[1] - previous[1]}'] += 1
                previous = point
            dx, dy = previous[0] - start['px'], previous[1] - start['py']
            probes.append({'input': key, 'emulated_frames': 24,
                           'updates': self.get('frame') - start['frame'],
                           'dx': dx, 'dy': dy, 'distance_pixels': math.hypot(dx, dy),
                           'per_frame_dx_dy_histogram': dict(steps),
                           'gameplay_stayed_valid': self.get('game_state') == 1 and self.get('room') == 0})
        cardinal = sum(probe['distance_pixels'] for probe in probes[:3]) / 3
        diagonal = sum(probe['distance_pixels'] for probe in probes[3:]) / 2
        ratio = diagonal / cardinal if cardinal else None
        symmetric = all(abs(abs(probe['dx']) - abs(probe['dy'])) <= 1 for probe in probes[3:])
        self.motion = {'probes': probes, 'diagonal_to_cardinal_distance_ratio': ratio,
                       'diagonal_axes_differ_by_at_most_one_pixel': symmetric,
                       'target_ratio': [0.95, 1.05],
                       'target_met': bool(ratio and 0.95 <= ratio <= 1.05 and symmetric
                                          and all(probe['gameplay_stayed_valid'] for probe in probes))}
        print(f'motion: diagonal/cardinal={ratio:.4f}; symmetric={symmetric}; '
              f'target={self.motion["target_met"]}', flush=True)
        self.e.state(checkpoint, load=True)
        self.write_report()

    def write_report(self):
        report = {
            'rom': str(self.rom.relative_to(ROOT)) if self.rom.is_relative_to(ROOT) else self.rom.name,
            'rom_sha256': hashlib.sha256(self.rom.read_bytes()).hexdigest(),
            'rom_bytes': self.rom.stat().st_size,
            'symbols': str(self.symbol_path.relative_to(ROOT)) if self.symbol_path.is_relative_to(ROOT) else self.symbol_path.name,
            'symbols_sha256': hashlib.sha256(self.symbol_path.read_bytes()).hexdigest(),
            'emulator': 'mGBA 0.10 through tools/mgba_runner.Emulator',
            'hardware_refresh_hz': GBA_REFRESH_HZ,
            'hardware_cycles_per_frame': GBA_CYCLES_PER_FRAME,
            'method': 'One Emulator.frames(1) call, then read frame symbol and DISPCNT page bit; no wall-clock FPS',
            'controller_only_scene_setup': True,
            'game_ram_injection': False,
            'savestate_policy': 'Snapshots made only after controller-only traversal; restored only to resume that traversal after independent measurements',
            'scope': 'Representative repeatable scene windows; not exhaustive all-frame worst-case proof or physical-hardware validation',
            'route_checks': self.route,
            'all_targets_met': bool(self.scenes) and all(scene['target']['met'] for scene in self.scenes)
                               and bool(self.motion and self.motion['target_met'])
                               and all(t['target']['met'] for t in self.transitions),
            'motion': self.motion,
            'transitions': self.transitions,
            'scenes': self.scenes,
        }
        (self.output / 'metrics.json').write_text(json.dumps(report, indent=2) + '\n')

    def run(self):
        self.step(90)
        self.require(self.get('game_state') == 0, 'booted title')
        self.measure('title', 2)
        self.measure_transition('open_intro', 'START', 2)
        self.require(self.get('game_state') == 2, 'opened introduction')
        self.measure('intro_dialog', 2)
        self.dialogs()
        self.require(self.get('game_state') == 1, 'entered village gameplay')
        self.measure('village_idle')
        self.measure('village_motion', controls=lambda n: 'LEFT' if (n // 36) % 2 else 'RIGHT')
        self.measure_motion()
        self.measure_transition('open_pause', 'START', 3)
        self.require(self.get('game_state') == 3, 'opened pause')
        self.measure('pause', 2)
        self.measure_transition('close_pause', 'B', 1)
        self.require(self.get('game_state') == 1, 'closed pause')
        self.nextroom(1)
        self.goto(y=180)
        self.measure('forest_combat', controls=lambda n: 'A' if n % 24 < 10 else 0)
        self.tap('B')
        self.measure('forest_summon_toast', controls=lambda n: 'A' if n % 24 < 10 else 0)
        self.tap('L')
        self.tap('R')
        self.require(self.get('bridge_open') == 1, 'nature companion opened bridge')
        self.measure('bridge_dialog', 2)
        self.dialogs()
        self.measure('forest_companion', controls=lambda n: 'A' if n % 24 < 10 else 0)
        self.nextroom(2)
        self.require(self.get('game_state') == 2, 'opened temple dialogue')
        self.measure('temple_dialog', 2)
        self.dialogs()
        self.measure('temple_combat', controls=lambda n: 'A' if n % 24 < 10 else 0)
        self.tap('L')
        self.goto(y=94)
        self.goto(x=64)
        self.goto(y=84)
        self.defend(160)
        self.goto(x=64, y=84)
        self.tap('R')
        self.require(self.get('torches') == 1, 'lit first brazier')
        self.goto(y=94)
        self.goto(x=176)
        self.goto(y=84)
        self.defend(160)
        self.goto(x=176, y=84)
        self.tap('R')
        self.require(self.get('torches') == 3, 'lit second brazier')
        self.measure('gate_dialog', 2)
        self.dialogs()
        self.goto(y=94)
        self.goto(x=120)
        self.nextroom(3)
        self.require(self.get('game_state') == 2, 'opened boss dialogue')
        self.measure('boss_dialog', 2)
        self.dialogs()
        # At the south edge, radial attacks are active but contact is avoidable.
        self.measure('boss_armored', controls=lambda n: 'LEFT' if (n // 48) % 2 else 'RIGHT')
        self.goto(y=100)
        self.step(160)
        self.tap('R')
        self.require(self.get('boss_armor') > 0, 'fire companion exposed boss')
        self.goto(y=139)
        self.measure('boss_exposed', controls=lambda n: 'LEFT' if (n // 48) % 2 else 'RIGHT')
        self.write_report()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'build/emberbond.gba')
    parser.add_argument('--symbols', type=Path, default=ROOT / 'build/emberbond.sym')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/perf-final')
    parser.add_argument('--frames', type=int, default=360)
    parser.add_argument('--strict', action='store_true', help='exit nonzero if a measured cadence target is missed')
    args = parser.parse_args()
    if args.frames < 60:
        parser.error('--frames must be at least 60')
    run = PerformanceRun(args.rom, args.symbols, args.output, args.frames)
    try:
        run.run()
    finally:
        run.write_report()
        run.e.close()
    if args.strict and (any(not scene['target']['met'] for scene in run.scenes)
                        or not run.motion or not run.motion['target_met']
                        or any(not t['target']['met'] for t in run.transitions)):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
