#!/usr/bin/env python3
"""Earn Ressa's kiln route with controller input from an empty mGBA cartridge."""
import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tools')]
import treasure_full_journey as journey
from interaction_readability_native import check_hint
from test_save5 import Save
from northern_journey import newest_bank


def ressa_events(run):
    return run.e.bytes(run.sym['adventure_save'] + Save.relationships.offset + 1, 1)[0]


def conversation(run, expected, label, cancel=False):
    run.goto(192, 192, radius=4)
    run.face(1)
    run.tap('A')
    run.check(run.get('game_state') == 2, label + ' opens a kiln conversation')
    run.e.screenshot(run.out / ('ressa-' + label + '-open.png'))
    run.tap('A')
    run.check(run.get('game_state') == 2, label + ' reaches its concluding page')
    run.e.screenshot(run.out / ('ressa-' + label + '-choice.png'))
    if cancel:
        run.tap('B')
        run.check(run.get('game_state') == 1 and ressa_events(run) == expected,
                  label + ' B leaves the event unrecorded')
        run.e.screenshot(run.out / ('ressa-' + label + '-deferred.png'))
        return
    run.tap('A')
    run.settle()


def ressa_magma_route(run):
    magma = journey.journey.MagmaJourney
    run.guidance('first-arrival')
    magma.recruits_main(run)
    run.entry(42)
    run.clear_enemies()
    run.field(31, 48, 68, 3)
    run.slide(0, ['DOWN', 'DOWN'] + ['RIGHT'] * 6 + ['UP', 'UP'])
    run.check(run.state().quests.objectives[32] & 1, 'base heat and brick solve intake')
    run.entry(43)
    run.clear_enemies()
    run.slide(0, ['DOWN', 'RIGHT', 'RIGHT'], side=2)
    run.slide(0, ['UP'] * 4)
    run.slide(1, ['LEFT', 'UP'])
    run.field(34, 168, 104)
    run.check(run.state().quests.objectives[32] & 2, 'base brace solves vault')
    run.entry(44)
    run.clear_enemies()
    run.field(31, 48, 68, 3)
    run.slide(0, ['DOWN', 'DOWN'] + ['RIGHT'] * 6 + ['UP', 'UP'])
    run.slide(1, ['LEFT'] + ['UP'] * 3, side=2)
    run.field(34, 168, 104)
    run.goto(208, 104)
    run.face(2)
    for _ in range(4):
        if run.state().quests.objectives[32] & 4:
            break
        run.tap('A', 2, 24)
        run.settle()
    run.check(run.state().quests.objectives[32] & 4,
              'starter sword opens prepared gallery pin')
    run.entry(45)
    magma.machine(run)
    run.entry(38)
    run.target(160, 176)
    run.target(112, 248)
    run.check(run.quest(32) == 3 and ressa_events(run) == 0,
              'original kiln reward is earned before Ressa events')
    run.snapshot('ressa-quest-earned')
    run.goto(192, 192, radius=4)
    run.face(1)
    run.step(8)
    check_hint(run, (192, 176), 'earned Ressa bowl A cue')
    run.e.screenshot(run.out / 'ressa-bowl-a-cue.png')

    conversation(run, 0, 'tile', cancel=True)
    for before, after, label in ((0, 1, 'tile'), (1, 3, 'firing'),
                                 (3, 7, 'story'), (7, 15, 'dating'),
                                 (15, 31, 'marriage')):
        if before:
            run.entry(39)
            run.entry(38)
        run.check(ressa_events(run) == before, label + ' waits for its own visit')
        if before in (7, 15):
            conversation(run, before, label, cancel=True)
        conversation(run, before, label)
        run.check(ressa_events(run) == after, label + ' records exactly one event')
        run.snapshot('ressa-' + label + '-accepted')
        run.goto(192, 192, radius=4)
        run.face(1)
        run.tap('A')
        run.settle()
        run.check(ressa_events(run) == after, label + ' cannot repeat for affinity')

    run.cold_reboot('ressa-marriage')
    run.check(ressa_events(run) == 31 and run.quest(32) == 3,
              'cold Continue retains Ressa marriage and original kiln reward')
    run.snapshot('ressa-cold-continue')
    run.entry(39)
    run.entry(38)
    run.goto(192, 192, radius=4)
    run.face(1)
    run.tap('A')
    run.check(run.get('game_state') == 2, 'married revisit opens her new greeting')
    run.e.screenshot(run.out / 'ressa-spouse-revisit.png')
    run.settle()
    run.check(ressa_events(run) == 31, 'married revisit has no new event')
    run.coverage.append('ressa-quest-earned-tile-firing-story-dating-marriage-cold-continue-revisit')
    run.chapter_checkpoint('magma-main')
    run.entry(46)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output', type=Path, required=True)
    args, _ = parser.parse_known_args()
    journey.TreasureRegionalJourney.magma_route = ressa_magma_route
    sys.argv.extend(['--stop-after', 'magma'])
    result = journey.main()
    if result == 0:
        output = args.output.resolve()
        campaign = json.loads((output / 'summary.json').read_text())
        region = json.loads((output / 'regions/report.json').read_text())
        expected = {'magma-ressa-quest-earned': 0,
                    'magma-ressa-tile-accepted': 1,
                    'magma-ressa-firing-accepted': 3,
                    'magma-ressa-story-accepted': 7,
                    'magma-ressa-dating-accepted': 15,
                    'magma-ressa-marriage-accepted': 31,
                    'magma-ressa-cold-continue': 31}
        observed = {name: newest_bank(Path(region['snapshots'][name]['sram_path']).read_bytes())[5089]
                    for name in expected}
        accepted = (campaign['requested_scope_completed'] and
                    campaign['presented_journey_pacing_passed'] and
                    campaign['controller_only'] and
                    not campaign['game_ram_writes'] and
                    not campaign['machine_state_imports'] and
                    not campaign['historical_progress_imports'] and
                    not region['failures'] and observed == expected and
                    'ressa-quest-earned-tile-firing-story-dating-marriage-cold-continue-revisit'
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
                  'screenshots': sorted(p.name for p in (output / 'regions').glob('ressa-*.png'))}
        (output / 'ressa-summary.json').write_text(json.dumps(report, indent=2) + '\n')
        result = int(not accepted)
    raise SystemExit(result)
