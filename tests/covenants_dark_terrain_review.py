#!/usr/bin/env python3
"""Native dark-floor visual supplement from synthetic, validated SRAM.

Reuses a completed frozen engine diagnostic. Only the host save's checkpoint is
changed, through validation and the normal writer. No game RAM/state injection;
invented host completion is not controller acquisition evidence.
"""
import argparse
import ctypes as C
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from mgba_runner import Emulator
import covenants_host_support as host

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    source, out = args.source.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    inherited = json.loads((source / 'report.json').read_text())
    assert inherited['finished'] and inherited['all_checks_passed'] and inherited['cadence_passed']
    candidate = source / 'candidate'
    assert all(sha(candidate / n) == h for n, h in inherited['candidate'].items())
    manifest = json.loads((candidate / 'source-hashes.json').read_text())
    host.ROOT = source / 'runtime-source'
    assert all(sha(host.ROOT / n) == h for n, h in manifest.items())
    symbols = {p[2]: int(p[0], 16) for line in (candidate / 'emberbond.sym').read_text().splitlines()
               if len(p := line.split()) == 3}
    report = {'scope': __doc__, 'candidate': inherited['candidate'], 'source_report_sha256': sha(source/'report.json'),
              'source_diagnostic': str(source), 'helper_sha256': sha(__file__), 'synthetic_fixture': True,
              'game_ram_writes': 0, 'machine_state_loads': 0, 'controller_earned_128': False,
              'release_acceptance': False, 'cases': [], 'exceptions': [], 'finished': False}
    with tempfile.TemporaryDirectory(prefix='covenants-dark-') as tmp, gzip.open(out/'frames.jsonl.gz', 'wt') as trace:
        lib = host.build(tmp)
        report['host_runtime_hashes'] = lib.source_hashes
        for index, form in enumerate(range(121, 129)):
            original = source/f'synthetic-room{70+index}-form{form}.sav'
            assert sha(original) == inherited['cases'][index]['fixture_sha256']
            lib.sram[:] = original.read_bytes()
            save = host.Save()
            assert lib.save5_load(C.byref(save)) == 1
            save.campaign.room, save.campaign.spawn = 3, 0
            assert lib.save5_validate(C.byref(save)) == 1
            lib.save5_test_reset_writer()
            lib.save5_test_fail_after(-1)
            assert lib.save5_store(C.byref(save)) == 1
            fixture = out/f'synthetic-dark-form{form}.sav'
            fixture.write_bytes(bytes(lib.sram))
            case = {'form': form, 'room': 3, 'original_fixture_sha256': sha(original),
                    'fixture_sha256': sha(fixture), 'measured_frames': 0, 'maximum_cycles': 0,
                    'maximum_oam': 0, 'screenshots': []}
            report['cases'].append(case)
            with Emulator(candidate/'emberbond.gba') as emu:
                emu.load_save(fixture)
                emu.reset()
                get = lambda n: emu.read(symbols[n])
                stage = 'cold-load'
                def step(count, keys=0, measured=True):
                    for _ in range(count):
                        frame, display = get('frame'), emu.read(0x04000000, 2)
                        emu.frames(1, keys)
                        if not measured:
                            continue
                        row = {'form': form, 'stage': stage, 'hardware_frame': emu.frame, 'keys': keys,
                               'update_delta': (get('frame')-frame)&0xffffffff,
                               'page_flip': bool((display^emu.read(0x04000000,2))&16),
                               'cycles': get('render_cycles'), 'oam': get('obj_count'),
                               'room': get('room'), 'state': get('game_state'),
                               'power_age': get('covenants_power_age'), 'power_time': get('covenants_power_time'),
                               'music': [get(n) for n in ('music_faults','music_recoveries','music_stopped')]}
                        trace.write(json.dumps(row, separators=(',',':'))+'\n')
                        case['measured_frames'] += 1
                        case['maximum_cycles'] = max(case['maximum_cycles'], row['cycles'])
                        case['maximum_oam'] = max(case['maximum_oam'], row['oam'])
                        if row['update_delta'] != 1 or not row['page_flip'] or row['cycles'] >= 280896 or row['oam'] > 128 or any(row['music']):
                            report['exceptions'].append(row)
                        assert row['room'] == 3 and row['state'] == 1
                def shot(name):
                    path = out/f'form{form}-{name}.png'
                    emu.screenshot(path)
                    case['screenshots'].append({'file': path.name, 'sha256': sha(path)})
                step(160, measured=False)
                assert get('game_state') == 0 and get('has_save') == 1
                step(1, 8, False)
                step(1, 0, False)
                for _ in range(360):
                    if get('game_state') == 1 and get('room') == 3 and not any(get(n) for n in ('save_begin_pending','save_completion_pending','save_requested')):
                        break
                    step(1, measured=False)
                else:
                    raise AssertionError('cold load failed')
                step(4, measured=False)
                stage = 'walk'
                if not get('summoned'):
                    step(1, 2)
                    step(1)
                step(24, 64)
                for direction, keys in [('right',16),('down',128),('left',32),('up',64)]:
                    step(12, keys)
                    step(12)
                    shot('walk-'+direction)
                stage = 'cast'
                step(1, 256)
                step(1)
                assert get('covenants_power_time') > 0
                frames = []
                while get('covenants_power_time'):
                    step(1)
                    if emu.frame%3 == 0:
                        frames.append(emu.screenshot())
                    if get('covenants_power_age') in (7,23,43,67,87):
                        shot('cast-age'+str(get('covenants_power_age')))
                frames[0].save(out/f'form{form}-dark-native.gif', save_all=True, append_images=frames[1:], duration=50, loop=0)
                step(3)
            (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    sheet = Image.new('RGB',(4*240,4*176),'#102139')
    draw = ImageDraw.Draw(sheet)
    for index, case in enumerate(report['cases']):
        for scene in range(2):
            x, y = (index%4)*240, (index//4*2+scene)*176
            label = 'walk-up' if scene == 0 else 'cast-age23'
            draw.text((x+3,y+2),f'{case["form"]} dark {label}',fill='white')
            sheet.paste(Image.open(out/f'form{case["form"]}-{label}.png'),(x,y+16))
    sheet.save(out/'dark-native-contact-sheet.png')
    sheet.convert('L').save(out/'dark-native-contact-sheet-gray.png')
    report['finished'] = True
    report['cadence_passed'] = not report['exceptions']
    report['candidate_still_exact'] = all(sha(candidate/n)==h for n,h in inherited['candidate'].items())
    (out/'executed-helper.py').write_bytes(Path(__file__).read_bytes())
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'finished': True, 'cadence_passed': report['cadence_passed'],
                      'measured_frames': sum(c['measured_frames'] for c in report['cases']),
                      'maximum_cycles': max(c['maximum_cycles'] for c in report['cases'])},indent=2))
    return 0 if report['cadence_passed'] and report['candidate_still_exact'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
