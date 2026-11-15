#!/usr/bin/env python3
"""Compare two immutable ROMs under identical fresh-cartridge controller input.

Readback compares gameplay state, weapon state, and final Save5/SRAM; timing is
gated independently for each ROM. No game RAM or machine states are injected.
This bounded opening/menu/combat/road route does not certify every chapter.
"""
import argparse
import ctypes as C
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from mgba_runner import keymask
from test_save5 import Save

FIELDS = ('frame', 'game_state', 'room', 'px', 'py', 'px_q8', 'py_q8',
          'face', 'walk', 'walk_phase', 'hp', 'hero_hp_q4', 'summoned', 'spirit',
          'ability_cd', 'step_cd', 'swing', 'sword_cd', 'transition_lock',
          'camera_x', 'camera_y', 'quickparty_open', 'save_requested',
          'save_feedback_background', 'bridge_open', 'torches', 'hitstop',
          'chapter_flags', 'room_flags', 'optional_flags', 'story_seen')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True,
                        help='Directory containing immutable emberbond.gba/.sym/.elf')
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--bridge', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    lib = C.CDLL(str(args.bridge.resolve()))
    signatures = [
        ('eb_open', [C.c_char_p], C.c_void_p), ('eb_close', [C.c_void_p], None),
        ('eb_frames', [C.c_void_p, C.c_uint, C.c_uint], None),
        ('eb_read', [C.c_void_p, C.c_uint32, C.c_uint], C.c_uint32),
        ('eb_rgb', [C.c_void_p, C.c_void_p], None)]
    for name, arguments, result in signatures:
        function = getattr(lib, name)
        function.argtypes = arguments
        function.restype = result
    has_fault_counter = hasattr(lib, 'eb_faults')
    if has_fault_counter:
        lib.eb_faults.argtypes = [C.c_void_p]
        lib.eb_faults.restype = C.c_uint
    runs = []
    report = {'result': 'RUNNING', 'controller_only': True, 'game_ram_writes': 0,
              'machine_state_imports': 0, 'physical_hardware_tested': False,
              'core_fault_counter_available': has_fault_counter,
              'scope': __doc__, 'bridge_sha256': digest(args.bridge),
              'harness_sha256': digest(__file__), 'fields': FIELDS,
              'inputs': [], 'checkpoints': [], 'strict_frames': 0}
    trace = gzip.open(out / 'frames.jsonl.gz', 'wt')

    def read(run, name):
        return lib.eb_read(run['core'], run['symbols'][name], 4)

    def raw(run, address, size):
        return bytes(lib.eb_read(run['core'], address + offset, 1) for offset in range(size))

    def state(run):
        row = {name: read(run, name) for name in FIELDS}
        row['weapon_action'] = raw(run, run['symbols']['weapon_action'], 20).hex()
        return row

    def step(count, keys=0, label='route', strict=True):
        mask = keymask(keys)
        report['inputs'].append({'label': label, 'frames': count, 'keys': mask})
        for _ in range(count):
            rows = []
            for run in runs:
                previous = read(run, 'frame')
                previous_serial = read(run, 'render_profile_serial')
                page = lib.eb_read(run['core'], 0x04000000, 2) & 16
                lib.eb_frames(run['core'], 1, mask)
                row = state(run)
                timing = {'delta': (row['frame'] - previous) & 0xffffffff,
                          'presentation_delta': (read(run, 'render_profile_serial') - previous_serial) & 0xffffffff,
                          'flip': page != (lib.eb_read(run['core'], 0x04000000, 2) & 16),
                          'cycles': read(run, 'render_cycles'),
                          'faults': lib.eb_faults(run['core']) if has_fault_counter else None}
                run['peak_cycles'] = max(run['peak_cycles'], timing['cycles'])
                rows.append({'state': row, 'timing': timing})
            trace.write(json.dumps({'label': label, 'keys': mask, 'strict': strict,
                                    'baseline': rows[0], 'candidate': rows[1]}) + '\n')
            if strict:
                report['strict_frames'] += 1
                assert rows[0]['state'] == rows[1]['state'], {
                    'label': label, 'different': {name: [rows[0]['state'][name], rows[1]['state'][name]]
                    for name in rows[0]['state'] if rows[0]['state'][name] != rows[1]['state'][name]}}
                for index, row in enumerate(rows):
                    timing = row['timing']
                    assert timing['presentation_delta'] == 2 and timing['flip'] and timing['cycles'] < 280896, (index, label, timing)
                    assert not timing['faults'], (index, label, timing)

    def tap(keys, label='tap'):
        step(2, keys, label)
        step(5, 0, label + '-release')

    def checkpoint(name):
        from PIL import Image
        saved = []
        for run in runs:
            pixels = (C.c_uint8 * (240 * 160 * 3))()
            lib.eb_rgb(run['core'], pixels)
            Image.frombytes('RGB', (240, 160), bytes(pixels)).save(out / (name + '-' + run['name'] + '.png'))
            save = raw(run, run['symbols']['adventure_save'], C.sizeof(Save))
            sram = raw(run, 0x0e000000, 32768)
            saved.append({'save5_sha256': hashlib.sha256(save).hexdigest(),
                          'sram_sha256': hashlib.sha256(sram).hexdigest(), 'state': state(run)})
        assert saved[0] == saved[1], (name, saved)
        report['checkpoints'].append({'name': name, **saved[1]})

    def goto(name, target):
        low, high = ('LEFT', 'RIGHT') if name == 'px' else ('UP', 'DOWN')
        for _ in range(350):
            value = read(runs[0], name)
            if abs(value - target) <= 1:
                return
            step(1, low if value > target else high, 'walk-to-road')
        raise AssertionError(('blocked controller route', name, target, state(runs[0])))

    try:
        for name, directory in [('baseline', args.baseline), ('candidate', args.candidate)]:
            directory = directory.resolve()
            symbols = {words[2]: int(words[0], 16) for line in (directory / 'emberbond.sym').read_text().splitlines()
                       if len(words := line.split()) == 3}
            core = lib.eb_open(str(directory / 'emberbond.gba').encode())
            assert core, name
            runs.append({'name': name, 'core': core, 'symbols': symbols,
                         'peak_cycles': 0, 'sha256': {suffix: digest(directory / ('emberbond.' + suffix))
                         for suffix in ('gba', 'elf', 'sym')}})
        step(160, label='cold-boot', strict=False)
        assert all(read(run, 'game_state') == 0 for run in runs)
        checkpoint('title')
        tap('A', 'start-opening')
        assert read(runs[0], 'game_state') == 14
        for beat in range(8):
            assert all(lib.eb_read(run['core'], run['symbols']['opening_page'], 1) == beat for run in runs)
            step(24, label='opening-page-' + str(beat))
            tap('A', 'opening-advance-' + str(beat))
        report['opening_pages'] = 8
        for _ in range(1500):
            if all(read(run, 'game_state') == 1 and not read(run, 'save_requested')
                   and not read(run, 'save_feedback_background') for run in runs):
                break
            step(1, label='first-save')
        else:
            raise AssertionError('Opening checkpoint did not settle')
        checkpoint('village')
        for _ in range(6):
            tap('A', 'sword-combo')
        step(30, label='sword-recovery')
        tap('START', 'menu-open')
        assert read(runs[0], 'game_state') == 3
        step(20, label='menu-paused')
        tap('RIGHT', 'menu-browse')
        tap('LEFT', 'menu-return')
        tap('START', 'menu-close')
        tap('R', 'summon')
        tap('B', 'power')
        step(100, label='power-recovery')
        tap('SELECT', 'field-goal')
        tap('L+RIGHT', 'short-step')
        step(16, 'L', 'carousel-hold')
        step(5, label='carousel-release')
        checkpoint('field-actions')
        goto('px', 120)
        goto('py', 55)
        for _ in range(200):
            if read(runs[0], 'room') == 1:
                break
            step(1, 'UP', 'village-road')
        else:
            raise AssertionError('Controller did not reach forest road')
        step(120, label='forest-arrival')
        checkpoint('forest-road')
        for index in range(240):
            direction = 'RIGHT' if index % 80 < 40 else 'LEFT'
            step(1, direction + ('+A' if index % 20 < 2 else ''), 'forest-walk-sword')
        step(120, label='forest-rest')
        checkpoint('forest-finish')
        report['result'] = 'PASS'
    except Exception as error:
        report['result'] = 'FAIL'
        report['error'] = repr(error)
        raise
    finally:
        trace.close()
        report['frames_sha256'] = digest(out / 'frames.jsonl.gz')
        report['runs'] = [{key: value for key, value in run.items() if key not in ('core', 'symbols')} for run in runs]
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        for run in runs:
            lib.eb_close(run['core'])
    print(json.dumps({'result': report['result'], 'strict_frames': report['strict_frames'],
                      'report': str(out / 'report.json')}))


if __name__ == '__main__':
    main()
