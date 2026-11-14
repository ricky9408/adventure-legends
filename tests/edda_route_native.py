#!/usr/bin/env python3
"""Earn Edda's whole route with controller input from an empty mGBA cartridge.

The original and Northern campaign routes earn quest21. This adapter visits
Edda's dispatch table, defers the choices, accepts them, and cold Continues.
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
from northern_journey import NorthernJourney, newest_bank


def edda_events(run):
    return run.e.bytes(run.sym['adventure_save'] + Save.relationships.offset, 1)[0]


def conversation(run, expected, label, cancel=False):
    run.goto(192, 176, radius=4)
    run.face(1)
    run.tap('A')
    run.check(run.get('game_state') == 2, label + ' opens a conversation')
    run.e.screenshot(run.out / ('edda-' + label + '-open.png'))
    run.tap('A')
    run.check(run.get('game_state') == 2, label + ' reaches its concluding page')
    run.e.screenshot(run.out / ('edda-' + label + '-choice.png'))
    if cancel:
        run.tap('B')
        run.check(run.get('game_state') == 1 and edda_events(run) == expected,
                  label + ' B leaves the event unrecorded')
        run.e.screenshot(run.out / ('edda-' + label + '-deferred.png'))
        return
    run.tap('A')
    run.settle()


def edda_north_route(run):
    run.guidance('first-arrival')
    run.act(168, 208)
    for x in (304, 160):
        run.act(x, 224)
    run.act(168, 208)
    run.reward(11, 19)
    run.assign(0, 19)
    run.select_form(19)
    run.entry(23)
    run.act(240, 208)
    run.act(320, 208)
    run.act(352, 176)
    run.reward(13, 77)
    run.assign(1, 77)
    run.select_form(19)
    run.entry(26)
    for room in (26, 27, 28):
        NorthernJourney.puzzle_room(run, room)
    NorthernJourney.machine(run, 1)
    run.to_town()
    run.act(104, 208)
    run.check(run.quest(21) == 3 and edda_events(run) == 0,
              'original Northern reward is earned before Edda events')
    run.snapshot('edda-quest-earned')

    conversation(run, 0, 'dispatch', cancel=True)
    for before, after, label in ((0, 1, 'dispatch'), (1, 3, 'delivery'),
                                 (3, 7, 'letter'), (7, 15, 'dating'),
                                 (15, 31, 'marriage')):
        if before:
            run.entry(23)
            run.entry(22)
        run.check(edda_events(run) == before, label + ' waits for its own visit')
        if before in (7, 15):
            conversation(run, before, label, cancel=True)
        conversation(run, before, label)
        run.check(edda_events(run) == after, label + ' records exactly one event')
        run.snapshot('edda-' + label + '-accepted')
        run.goto(192, 176, radius=4)
        run.face(1)
        run.tap('A')
        run.settle()
        run.check(edda_events(run) == after, label + ' cannot repeat for affinity')

    run.cold_reboot('edda-marriage')
    run.check(edda_events(run) == 31 and run.quest(21) == 3,
              'cold Continue retains Edda marriage and Northern reward')
    run.snapshot('edda-cold-continue')
    run.coverage.append('edda-quest-earned-dispatch-delivery-letter-dating-marriage-cold-continue')
    run.chapter_checkpoint('north-main')
    run.entry(30)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output', type=Path, required=True)
    args, _ = parser.parse_known_args()
    journey.TreasureRegionalJourney.north_route = edda_north_route
    sys.argv.extend(['--stop-after', 'north'])
    result = journey.main()
    if result == 0:
        output = args.output.resolve()
        campaign = json.loads((output / 'summary.json').read_text())
        region = json.loads((output / 'regions/report.json').read_text())
        expected = {'north-edda-quest-earned': 0, 'north-edda-dispatch-accepted': 1,
                    'north-edda-delivery-accepted': 3,
                    'north-edda-letter-accepted': 7,
                    'north-edda-dating-accepted': 15,
                    'north-edda-marriage-accepted': 31,
                    'north-edda-cold-continue': 31}
        observed = {name: newest_bank(Path(region['snapshots'][name]['sram_path']).read_bytes())[5088]
                    for name in expected}
        accepted = (campaign['requested_scope_completed'] and
                    campaign['presented_journey_pacing_passed'] and
                    campaign['controller_only'] and
                    not campaign['game_ram_writes'] and
                    not campaign['machine_state_imports'] and
                    not campaign['historical_progress_imports'] and
                    not region['failures'] and observed == expected and
                    'edda-quest-earned-dispatch-delivery-letter-dating-marriage-cold-continue'
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
                  'screenshots': sorted(p.name for p in (output / 'regions').glob('edda-*.png'))}
        (output / 'edda-summary.json').write_text(json.dumps(report, indent=2) + '\n')
        result = int(not accepted)
    raise SystemExit(result)
