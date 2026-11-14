#!/usr/bin/env python3
"""Earn Mina's whole route with physical mGBA input from blank SRAM.

The existing original and Southern campaign drivers earn quest24. This adapter
then walks between harbor visits, cancels both choices, accepts them, and cold
Continues. It never writes game RAM or imports a prepared relationship ledger.
"""
import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tools')]
import treasure_full_journey as journey
from test_save5 import Save
from northern_journey import newest_bank


def mina_events(run):
    return run.e.bytes(run.sym['adventure_save'] + Save.relationships.offset + 2, 1)[0]


def conversation(run, place, expected, label, cancel=False):
    run.goto(400, 230 if place == 'plot' else 206, radius=4)
    run.face(1)
    run.tap('A')
    run.check(run.get('game_state') == 2, label + ' opens a visible conversation')
    run.e.screenshot(run.out / ('mina-' + label + '-open.png'))
    if cancel:
        run.tap('A')
        run.check(run.get('game_state') == 2, label + ' reaches its explicit choice')
        run.e.screenshot(run.out / ('mina-' + label + '-choice.png'))
        run.tap('B')
        run.check(run.get('game_state') == 1 and mina_events(run) == expected,
                  label + ' B leaves the event unrecorded')
        run.e.screenshot(run.out / ('mina-' + label + '-deferred.png'))
        return
    run.tap('A')
    run.check(run.get('game_state') == 2, label + ' shows its concluding page')
    run.e.screenshot(run.out / ('mina-' + label + '-ending.png'))
    run.tap('A')
    run.settle()


def mina_south_route(run):
    south = journey.journey.SouthernJourney
    run.guidance('first-arrival')
    south.recruits_main(run)
    for area in (34, 35, 36):
        south.puzzle_room(run, area)
    south.machine(run, 1)
    run.to_town()
    run.use('rest')
    run.check(run.quest(24) == 3 and mina_events(run) == 0,
              'quest24 is earned and Mina starts with no recorded event')
    run.snapshot('mina-quest-earned')

    run.goto(400, 206, radius=4)
    run.face(1)
    run.tap('A')
    run.check(run.get('game_state') == 2 and mina_events(run) == 0,
              'Mina invites planting without awarding relationship progress')
    run.e.screenshot(run.out / 'mina-invitation.png')
    run.settle()
    run.goto(400, 230, radius=4)
    run.face(1)
    run.tap('A')
    run.check(run.get('game_state') == 2, 'planting begins at the garden plot')
    run.tap('B')
    run.check(run.get('game_state') == 1 and mina_events(run) == 0,
              'B cancels planting without recording it')
    conversation(run, 'plot', 0, 'plant')
    run.check(mina_events(run) == 1, 'shared planting is recorded once after its final A')
    run.snapshot('mina-planted')

    for before, after, label in ((1, 3, 'growth'), (3, 7, 'story'),
                                 (7, 15, 'dating'), (15, 31, 'marriage')):
        run.entry(31)
        run.entry(30)
        run.check(mina_events(run) == before, label + ' waits for a separate harbor visit')
        if before in (7, 15):
            conversation(run, 'mina', before, label, cancel=True)
        conversation(run, 'mina', before, label)
        run.check(mina_events(run) == after, label + ' commits exactly one event')
        run.snapshot('mina-' + label + '-accepted')
        run.goto(400, 206, radius=4)
        run.face(1)
        run.tap('A')
        run.settle()
        run.check(mina_events(run) == after, label + ' cannot be repeated for progress')

    run.cold_reboot('mina-marriage')
    run.check(mina_events(run) == 31 and run.quest(24) == 3,
              'cold Continue preserves marriage and the original chapter receipt')
    run.snapshot('mina-cold-continue')
    run.coverage.append('mina-quest-earned-plant-return-story-dating-marriage-cold-continue')
    run.chapter_checkpoint('south-main')
    run.entry(38)


if __name__ == '__main__':
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--output', type=Path, required=True)
    args, _ = p.parse_known_args()
    journey.TreasureRegionalJourney.south_route = mina_south_route
    sys.argv.extend(['--stop-after', 'south'])
    result = journey.main()
    if result == 0:
        output = args.output.resolve()
        campaign = json.loads((output / 'summary.json').read_text())
        region = json.loads((output / 'regions/report.json').read_text())
        expected = {'south-mina-quest-earned': 0, 'south-mina-planted': 1,
                    'south-mina-growth-accepted': 3, 'south-mina-story-accepted': 7,
                    'south-mina-dating-accepted': 15,
                    'south-mina-marriage-accepted': 31,
                    'south-mina-cold-continue': 31}
        observed = {name: newest_bank(Path(region['snapshots'][name]['sram_path']).read_bytes())[5090]
                    for name in expected}
        accepted = (campaign['requested_scope_completed'] and
                    campaign['presented_journey_pacing_passed'] and
                    campaign['controller_only'] and
                    not campaign['game_ram_writes'] and
                    not campaign['machine_state_imports'] and
                    not campaign['historical_progress_imports'] and
                    not region['failures'] and observed == expected and
                    'mina-quest-earned-plant-return-story-dating-marriage-cold-continue'
                    in region['coverage'])
        report = {'accepted': bool(accepted), 'scope': __doc__,
                  'candidate': campaign['candidate'],
                  'controller_only': campaign['controller_only'],
                  'game_ram_writes': campaign['game_ram_writes'],
                  'machine_state_imports': campaign['machine_state_imports'],
                  'historical_progress_imports': campaign['historical_progress_imports'],
                  'passed_checks': campaign['passed_checks'],
                  'presented_journey_pacing_passed': campaign['presented_journey_pacing_passed'],
                  'relationship_snapshots': observed,
                  'screenshots': sorted(p.name for p in (output / 'regions').glob('mina-*.png'))}
        (output / 'mina-summary.json').write_text(json.dumps(report, indent=2) + '\n')
        result = int(not accepted)
    raise SystemExit(result)
