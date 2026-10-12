#!/usr/bin/env python3
"""Controller-only interaction diagnostics from authenticated earned SRAM.

A changed-ROM boundary import is explicitly diagnostic, never fresh campaign
acceptance. Original saves are read only; outputs and SRAM exports are private.
"""
import argparse
import json
import struct
from pathlib import Path
from types import SimpleNamespace

from journey_guidance_earned import RegionalJourney, sha

ROOT = Path(__file__).resolve().parents[1]


def field_hints(run):
    rows = []
    for index, (a0, a1, a2, _) in enumerate(struct.iter_unpack('<4H', run.e.bytes(0x07000000, 1024))):
        # Bitmap modes reserve the lower 512 OBJ tiles (see obj_add).
        if not a0 & 0x200 and a2 & 1023 == 512 + 10496 // 32:
            rows.append(dict(index=index, x=a1 & 511, y=a0 & 255))
    return rows


def check_hint(run, point, label='contextual A cue', visible=True):
    hints = field_hints(run)
    expected = ((point[0] - 4 - run.get('camera_x')) & 511, (point[1] - 21 - run.get('camera_y')) & 255)
    matching = [h for h in hints if (h['x'], h['y']) == expected]
    # Optional companions already use the same glyph for recruitment notices.
    # Keep that independent cue in the record; require one at the real A target.
    run.cases.append(dict(case=label, target=list(point), expected_visible=visible,
                          hints=hints, matching=matching, status=run.status()))
    run.check(len(matching) == int(visible), label + ' has exactly the expected active OAM count at its target')


def settle_camera(run):
    stable = 0
    for _ in range(90):
        before = (run.get('camera_x'), run.get('camera_y'))
        run.raw_step(1)
        if before == (run.get('camera_x'), run.get('camera_y')):
            stable += 1
            if stable == 6:
                return
        else:
            stable = 0
    raise AssertionError('camera did not settle for the OAM position check')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--source-root', type=Path, default=ROOT)
    p.add_argument('--bridge', type=Path, required=True)
    p.add_argument('--source-report', type=Path, required=True)
    p.add_argument('--source-snapshot', required=True)
    p.add_argument('--case', choices=('rails', 'underwater', 'return', 'horizons', 'covenants'), required=True)
    p.add_argument('--check-prompts', action='store_true', help='requires the integrated OBJ_HINT renderer hook')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    for name in ('candidate', 'source_root', 'bridge', 'source_report', 'output'):
        setattr(a, name, getattr(a, name).resolve())
    assert not a.output.exists(), 'Use a new evidence directory'
    a.output.mkdir(parents=True)
    rom = a.candidate / 'emberbond.gba'
    symbols = rom.with_suffix('.sym')
    manifest = a.candidate / 'source-hashes.json'
    hashes = json.loads(manifest.read_text())
    assert all(sha(a.source_root / name) == value for name, value in hashes.items())
    producer = json.loads(a.source_report.read_text())
    assert producer['controller_only'] and producer['route_complete']
    assert not producer['failures'] and all(c['passed'] for c in producer['checks'])
    assert not any(producer[k] for k in ('game_ram_writes', 'machine_state_imports', 'historical_progress_imports'))
    source_save = Path(producer['snapshots'][a.source_snapshot]['sram_path']).resolve()
    source_hash = sha(source_save)
    args = SimpleNamespace(output=a.output, rom=rom, symbols=symbols, bridge=a.bridge,
                           source_root=a.source_root, baseline=False, cross_rom_diagnostic=True,
                           diagnostic_boundary_report=a.source_report,
                           expected_rom_sha=sha(rom), expected_symbols_sha=sha(symbols))
    args.candidate = dict(rom_sha256=args.expected_rom_sha, symbols_sha256=args.expected_symbols_sha,
                          elf_sha256=sha(rom.with_suffix('.elf')),
                          source_manifest_sha256=sha(manifest), bridge_sha256=sha(a.bridge))
    (a.output / 'candidate.json').write_text(json.dumps(args.candidate, indent=2) + '\n')
    run = None
    try:
        run = RegionalJourney(args, source_save, a.source_report)
        run.chapter = a.case
        if a.case == 'rails':
            run.entry(23)
            run.entry(26)
            run.assign(0, 77)
            run.select_slot(0)
            run.set_command(21)
            initial = run.puzzle()[0]
            for turn in range(4):
                bearing = (initial + turn) & 3
                run.check(run.puzzle()[0] == bearing, 'rail bearing earned by real command')
                if run.get('summoned'):
                    run.tap('B')
                run.goto(204, 136, radius=2)
                run.step(180)
                run.snapshot(('north', 'east', 'south', 'west')[bearing])
                if turn < 3:
                    run.ready()
                    run.goto(120, 112, radius=2)
                    run.tap('R')
                    run.settle()
        else:
            if a.case == 'return':
                run.entry(54)
            target, approach, facing = {
                'underwater': ((144, 104), (136, 120), 1),
                'return': ((272, 240), (264, 256), 1),
                'horizons': ((208, 208), (200, 224), 1),
                'covenants': ((128, 272), (120, 256), 0),
            }[a.case]
            run.goto(*approach, radius=1)
            run.face(facing)
            x, y = run.get('px'), run.get('py')
            forward = y - target[1] if facing == 1 else target[1] - y
            side = abs(x - target[0])
            run.check(6 <= forward <= 26 and side <= 10 and side > forward // 2,
                      'controller reaches new off-axis range outside old taper')
            setting = None
            if a.case == 'horizons':
                setting = run.locals['horizons_game.c:setting'][0]
                before = run.e.read(setting, 1)
            run.snapshot('off-axis-before-A')
            if a.check_prompts:
                settle_camera(run)
                check_hint(run, target)
            run.tap('A')
            run.check(run.get('game_state') == 2 if setting is None else run.e.read(setting, 1) != before,
                      'ordinary A reaches the intended dialogue or manual')
            run.snapshot('off-axis-after-A', settle=False)
            if a.check_prompts:
                if run.get('game_state') == 2:
                    check_hint(run, target, 'dialogue hides ordinary A cue', visible=False)
                run.settle()
                run.raw_step(4, 'L')
                run.check(run.get('quickparty_open'), 'real L hold opens the quick picker')
                check_hint(run, target, 'quick picker hides ordinary A cue', visible=False)
                run.e.screenshot(run.out / 'picker-no-hint.png')
                run.raw_step(4)
                merchant = (304, 284) if a.case == 'underwater' else (208, 284)
                run.goto(merchant[0], merchant[1] + 16, radius=2)
                settle_camera(run)
                check_hint(run, merchant, 'merchant takes A cue priority')
                run.snapshot('merchant-one-hint')
                run.tap('A')
                run.check(run.get('game_state') == 11, 'A opens the regional merchant instead of a field target')
                check_hint(run, merchant, 'shop modal hides merchant A cue', visible=False)
                run.snapshot('merchant-shop-priority', settle=False)
        run.coverage.append('targeted-readability-cross-ROM-diagnostic')
    except Exception as e:
        if run is not None:
            run.failures.append(str(e))
        raise
    finally:
        if run is not None:
            run.close()
        assert sha(source_save) == source_hash, 'Producer SRAM must remain unchanged'


if __name__ == '__main__':
    main()
