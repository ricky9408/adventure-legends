#!/usr/bin/env python3
"""Read-only native visual supplement using the completed engine diagnostic's
explicitly synthetic, validated SRAM fixtures. No RAM writes or machine states.
The fixture's invented history is never controller-obtainability evidence.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import shutil
import sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from mgba_runner import Emulator

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    inherited = json.loads((source / 'report.json').read_text())
    assert inherited['finished'] and inherited['all_checks_passed'] and inherited['cadence_passed']
    candidate = source / 'candidate'
    assert all(sha(candidate / name) == value for name, value in inherited['candidate'].items())
    symbols = {p[2]: int(p[0], 16) for line in (candidate / 'emberbond.sym').read_text().splitlines()
               if len(p := line.split()) == 3}
    report = {'scope': __doc__, 'candidate': inherited['candidate'],
              'source_diagnostic': str(source), 'source_report_sha256': sha(source / 'report.json'),
              'synthetic_fixture': True, 'controller_earned_128': False,
              'release_acceptance': False, 'game_ram_writes': 0, 'machine_state_loads': 0,
              'helper_sha256': sha(__file__), 'cases': [], 'exceptions': [], 'finished': False}
    commands = [12] + list(range(122, 129))
    dirs = [('down', 128, 0), ('up', 64, 1), ('left', 32, 2), ('right', 16, 3)]
    snapshots = []
    with gzip.open(output / 'frames.jsonl.gz', 'wt', encoding='utf8') as stream:
        for index, form in enumerate(range(121, 129)):
            area = 70 + index
            fixture = source / f'synthetic-room{area}-form{form}.sav'
            assert sha(fixture) == inherited['cases'][index]['fixture_sha256']
            case = {'form': form, 'room': area, 'fixture_sha256': sha(fixture),
                    'walk_tuples': [], 'cast_tuples': [], 'native_tile_checks': 0,
                    'direction_cases': [], 'maximum_cycles': 0, 'maximum_oam': 0,
                    'measured_frames': 0, 'portraits': [], 'phase_captures': []}
            report['cases'].append(case)
            with Emulator(candidate / 'emberbond.gba') as emu:
                emu.load_save(fixture)
                emu.reset()
                get = lambda name: emu.read(symbols[name])
                last_code = None
                stage = 'loader'
                capture = []
                pose_shots = {}
                walk_tiles = {}
                cast_tiles = {}
                expected_face = None
                def save_report():
                    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
                def observe_tile():
                    nonlocal last_code
                    code = get('gfx_companion_frame')
                    if get('game_state') != 1 or not get('summoned') or code == last_code:
                        return
                    last_code = code
                    low = code & 0x0fffffff
                    direction = (low // 4) & 3
                    gait = low & 3
                    cast = code >= 268435456
                    if cast:
                        pose = (code - 268435456) // 536870912
                        assert pose < 3 and direction == expected_face, (form, 'cast face', direction, expected_face)
                        address = symbols['covenants_creature_art_cast'] + (((form-121)*4+direction)*3+pose)*256
                        pair = [direction, pose]
                        if pair not in case['cast_tuples']:
                            case['cast_tuples'].append(pair)
                        if (direction, pose) not in pose_shots:
                            name = f'form{form}-{stage}-pose{pose}.png'
                            emu.screenshot(output / name)
                            pose_shots[(direction, pose)] = name
                            snapshots.append((f'{form} {stage} pose{pose}', output / name))
                    else:
                        pose = gait
                        address = symbols['covenants_creature_art_walk'] + (((form-121)*4+direction)*4+gait)*256
                        pair = [direction, gait]
                        if pair not in case['walk_tuples']:
                            case['walk_tuples'].append(pair)
                    native = emu.bytes(0x06014000 + 6400, 256)
                    pixels = emu.bytes(address, 256)
                    tiled = bytes(pixels[(ty+y)*16+tx+x]
                                  for ty in range(0, 16, 8) for tx in range(0, 16, 8)
                                  for y in range(8) for x in range(8))
                    assert native == tiled, (form, direction, pose, 'native upload differs')
                    case['native_tile_checks'] += 1
                    target = cast_tiles if cast else walk_tiles
                    target[(direction, pose)] = pixels
                def step(count, keys=0, measured=True, record=False):
                    for _ in range(count):
                        before = get('frame')
                        displayed_age = get('covenants_power_age')
                        display = emu.read(0x04000000, 2)
                        emu.frames(1, keys)
                        if not measured:
                            continue
                        row = {'form': form, 'room': get('room'), 'stage': stage,
                               'hardware_frame': emu.frame, 'keys': keys,
                               'update_delta': (get('frame') - before) & 0xffffffff,
                               'page_flip': bool((display ^ emu.read(0x04000000, 2)) & 16),
                               'cycles': get('render_cycles'), 'oam': get('obj_count'),
                               'power_age': get('covenants_power_age'), 'power_time': get('covenants_power_time'),
                               'player': [get('px'), get('py')], 'companion': [get('cx'), get('cy')],
                               'code': get('gfx_companion_frame')}
                        case['measured_frames'] += 1
                        case['maximum_cycles'] = max(case['maximum_cycles'], row['cycles'])
                        case['maximum_oam'] = max(case['maximum_oam'], row['oam'])
                        if row['update_delta'] != 1 or not row['page_flip'] or row['cycles'] >= 280896 or row['oam'] > 128:
                            report['exceptions'].append(row)
                        assert row['room'] == area, ('unexpected room transition', area, row)
                        stream.write(json.dumps(row, separators=(',', ':')) + '\n')
                        observe_tile()
                        if expected_face is not None and row['power_time'] and (
                            (form == 125 and row['power_age'] in (7, 21, 22, 23, 37, 38, 39)) or
                            (form == 128 and row['power_age'] in (65, 66, 67))):
                            flat = highlighted = 0
                            for obj in range(128):
                                at = 0x07000000 + obj*8
                                a0, a1, a2 = (emu.read(at+n*2, 2) for n in range(3))
                                if a0&0x0300 == 0x0200 or a0>>14 or a1>>14:
                                    continue
                                flat += (a2&1023) == 1000
                                highlighted += (a2&1023) == 1018
                            name = f'form{form}-{stage}-phase-age{row["power_age"]}.png'
                            emu.screenshot(output / name)
                            # runFrame returns after VBlank with the next PLAY
                            # update already begun. Hardware OAM was committed
                            # from the preceding rendered update, not live age.
                            case['phase_captures'].append({'direction': expected_face, 'age': row['power_age'],
                                'displayed_age': displayed_age,
                                'flat_native_objects': flat, 'highlighted_native_objects': highlighted,
                                'file': name})
                        if record and emu.frame % 3 == 0:
                            capture.append(emu.screenshot())
                def tap(key):
                    step(1, key)
                    step(1)
                step(160, measured=False)
                assert get('game_state') == 0 and get('has_save') == 1
                step(1, 8, False)
                step(1, 0, False)
                for _ in range(360):
                    if get('game_state') == 1 and get('room') == area and not any(get(n) for n in ('save_begin_pending', 'save_completion_pending', 'save_requested')):
                        break
                    step(1, measured=False)
                else:
                    raise AssertionError(('cold load failed', form))
                step(4, measured=False)
                stage = 'walk'
                start_x, start_y = get('px'), get('py')
                if not get('summoned'):
                    tap(2)
                width = 480 if area in (70, 72, 74, 76) else 240
                height = 320 if area in (70, 71, 74, 75) else 160
                horizontal = (16, 32) if get('px') < width//2 else (32, 16)
                vertical = (128, 64) if get('py') < height//2 else (64, 128)
                for key in horizontal + vertical:
                    step(32, key, record=True)
                    step(48, record=True)
                if capture:
                    capture[0].save(output / f'form{form}-walking-native.gif', save_all=True,
                                    append_images=capture[1:], duration=50, loop=0)
                # Obstructions can make equal outward/back input durations end
                # at different coordinates. Return by observed controller
                # movement to the known safe cold-load position before casts.
                stage = 'return-to-cast-origin'
                for axis, target, negative, positive in [('py', start_y, 64, 128), ('px', start_x, 32, 16)]:
                    for _ in range(160):
                        value = get(axis)
                        if abs(value-target) <= 1:
                            break
                        step(1, negative if value>target else positive)
                    else:
                        raise AssertionError(('safe origin return blocked', form, axis, get(axis), target))
                    step(1)
                step(32)
                for direction_name, key, direction in dirs:
                    stage = direction_name
                    step(get('ability_cd') + 2)
                    tap(key)
                    expected_face = direction
                    capture = []
                    tap(256)
                    assert get('covenants_power_time') > 0 and get('covenants_power_kind') == commands[index]
                    assert get('covenants_power_direction') == direction
                    while get('covenants_power_time'):
                        step(1, record=True)
                    step(3, record=True)
                    keys_found = sorted(pose for d, pose in cast_tiles if d == direction)
                    assert keys_found == [0, 1, 2], (form, direction, keys_found)
                    name = f'form{form}-{direction_name}-native.gif'
                    capture[0].save(output / name, save_all=True, append_images=capture[1:], duration=50, loop=0)
                    case['direction_cases'].append({'direction': direction_name, 'cast_poses': keys_found, 'motion': name})
                for tab in (2, 3):
                    p = source / f'room{area}-form{form}-journal{tab}.png'
                    shutil.copyfile(p, output / p.name)
                    case['portraits'].append({'file': p.name, 'sha256': sha(p)})
                save_report()
    # Native screenshots are kept unchanged. Enlarged/grayscale sheets are
    # explicitly derived review aids and never substituted for screenshots.
    rows = (len(snapshots)+3)//4
    sheet = Image.new('RGB', (4*240, rows*174), '#102139')
    draw = ImageDraw.Draw(sheet)
    for n, (label, path) in enumerate(snapshots):
        x = (n%4)*240
        y = (n//4)*174
        draw.text((x+3, y+2), label, fill='#ffedc3')
        sheet.paste(Image.open(path), (x, y+14))
    sheet.save(output / 'cast-facing-contact-sheet.png')
    sheet.convert('L').save(output / 'cast-facing-contact-sheet-gray.png')
    report['finished'] = True
    report['all_four_cast_facings'] = all(len(case['cast_tuples']) == 12 for case in report['cases'])
    report['all_four_walk_facings'] = all(len(case['walk_tuples']) == 16 for case in report['cases'])
    report['cadence_passed'] = not report['exceptions']
    report['phase_native_selection_passed'] = all(
        row['highlighted_native_objects'] > 0 and row['flat_native_objects'] == 0
        if ((case['form'] == 125 and row['displayed_age'] < 22) or (case['form'] == 128 and row['displayed_age'] >= 66))
        else row['flat_native_objects'] > 0 and row['highlighted_native_objects'] == 0
        for case in report['cases'] for row in case['phase_captures'])
    report['candidate_still_exact'] = all(sha(candidate/name) == value for name, value in inherited['candidate'].items())
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    checks = ('finished', 'all_four_cast_facings', 'all_four_walk_facings',
              'phase_native_selection_passed', 'cadence_passed', 'candidate_still_exact')
    print(json.dumps({key: report[key] for key in checks}, indent=2))
    return 0 if all(report[key] for key in checks) else 1

if __name__ == '__main__':
    raise SystemExit(main())
