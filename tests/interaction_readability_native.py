#!/usr/bin/env python3
"""Controller-only interaction diagnostics from authenticated earned SRAM.

A changed-ROM boundary import is explicitly diagnostic, never fresh campaign
acceptance. Original saves are read only; outputs and SRAM exports are private.
"""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from journey_guidance_earned import RegionalJourney, sha

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--bridge', type=Path, required=True)
    p.add_argument('--source-report', type=Path, required=True)
    p.add_argument('--source-snapshot', required=True)
    p.add_argument('--case', choices=('rails', 'underwater', 'return', 'horizons', 'covenants'), required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    for name in ('candidate', 'bridge', 'source_report', 'output'):
        setattr(a, name, getattr(a, name).resolve())
    assert not a.output.exists(), 'Use a new evidence directory'
    a.output.mkdir(parents=True)
    rom = a.candidate / 'emberbond.gba'
    symbols = rom.with_suffix('.sym')
    manifest = a.candidate / 'source-hashes.json'
    hashes = json.loads(manifest.read_text())
    assert all(sha(ROOT / name) == value for name, value in hashes.items())
    producer = json.loads(a.source_report.read_text())
    assert producer['controller_only'] and producer['route_complete']
    assert not producer['failures'] and all(c['passed'] for c in producer['checks'])
    assert not any(producer[k] for k in ('game_ram_writes', 'machine_state_imports', 'historical_progress_imports'))
    source_save = Path(producer['snapshots'][a.source_snapshot]['sram_path']).resolve()
    source_hash = sha(source_save)
    args = SimpleNamespace(output=a.output, rom=rom, symbols=symbols, bridge=a.bridge,
                           source_root=ROOT, baseline=False, cross_rom_diagnostic=True,
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
            run.tap('A')
            run.check(run.get('game_state') == 2 if setting is None else run.e.read(setting, 1) != before,
                      'ordinary A reaches the intended dialogue or manual')
            run.snapshot('off-axis-after-A', settle=False)
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
