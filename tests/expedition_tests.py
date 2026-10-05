#!/usr/bin/env python3
"""Controller-only expedition boundaries, repeat credit, and checkpoint reloads.

Starts from hash-pinned, controller-earned shipped v4 checkpoints, then uses
only normal buttons on the supplied ROM. Symbol reads observe the roster;
neither the test nor its helpers write game RAM or fabricate save records.
"""
import argparse
import hashlib
import json
from pathlib import Path

from evolution_tests import EvolutionRun, ROOT
from test_creatures import Roster


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ExpeditionRun(EvolutionRun):
    def __init__(self, rom, symbols, output):
        super().__init__(rom, symbols, output, exhaustive=False)
        self.fixtures = []
        self.ledger_samples = []

    def fixture(self, name):
        directory = ROOT / 'tests/fixtures/v4'
        manifest = json.loads((directory / 'manifest.json').read_text())
        evidence = next(f for f in manifest['fixtures'] if f['file'] == name)
        source = directory / name
        self.check(digest(source) == evidence['sha256'], name + ': authentic fixture hash matches')
        self.fixtures.append(dict(evidence))
        self.reopen(source)
        self.dialogs()
        self.check(self.get('loaded_save_version') == 4, name + ': original format is migrated by the ROM')

    def sample(self, label):
        roster = self.roster()
        party = [slot for slot in roster.party if slot != 255]
        self.ledger_samples.append({
            'label': label, 'room': self.get('room'),
            'xp': [roster.instances[i].xp for i in party],
            'bond': [roster.instances[i].bond for i in party],
            'expedition_bond': [roster.expedition_bond[i] for i in party],
            'events': [i for i in range(512) if roster.expedition_events[i // 8] & (1 << (i % 8))],
            'lifetime_field_aid': bytes(roster.lifetime_field_aid).hex(),
            'roster_sha256': hashlib.sha256(bytes(roster)).hexdigest(),
        })
        return roster

    def departure(self, target, label):
        before = self.roster()
        expected = Roster.from_buffer_copy(bytes(before))
        expected.expedition_bond[:] = bytes(160)
        expected.expedition_events[:] = bytes(64)
        self.hub(target)
        self.check(bytes(self.roster()) == bytes(expected),
                   label + ': actual village departure resets only expedition credit')
        self.sample(label)

    def clear_ridge(self, credited, label):
        before = self.roster()
        self.check(sum(self.e.read(self.sym['enemies'] + i * 20 + 8) > 0 for i in range(6)) == 2,
                   label + ': two authored enemies are present')
        self.defend(1000)
        self.check(not any(self.e.read(self.sym['enemies'] + i * 20 + 8) for i in range(6)),
                   label + ': both enemies are defeated through controller combat')
        after = self.sample(label)
        if credited:
            for slot in before.party:
                if slot == 255:
                    continue
                self.check(after.instances[slot].xp == before.instances[slot].xp + 120 and
                           after.instances[slot].bond == before.instances[slot].bond + 2 and
                           after.expedition_bond[slot] == before.expedition_bond[slot] + 2,
                           label + ': party slot ' + str(slot) + ' earns exactly two encounter rewards')
            self.check(after.expedition_events[3] & 3 == 3, label + ': both shared encounter bits are set')
        else:
            self.check(bytes(after) == bytes(before), label + ': same-expedition respawns award no duplicate XP or bond')

    def reload_checkpoint(self, name, room):
        self.settle_save()
        before = bytes(self.roster())
        saved = self.save(name)
        self.reopen(saved)
        self.dialogs()
        self.check(self.get('loaded_save_version') == 5 and self.get('room') == room,
                   name + ': independent emulator resumes the actual saved room')
        self.check(bytes(self.roster()) == before,
                   name + ': reload preserves complete roster, XP, bond and expedition ledgers')
        self.sample(name)

    def sky_trips(self):
        self.fixture('grove-complete.sav')
        self.departure(4, 'Sky trip one')
        self.clear_ridge(True, 'Sky trip one combat')
        self.object('trail_rest')
        self.reload_checkpoint('sky-same-expedition', 4)
        self.clear_ridge(False, 'Sky combat after checkpoint reload')
        self.nextroom(0, 'DOWN')
        self.check(any(self.roster().expedition_events), 'Returning to village alone preserves earned event credit')
        self.departure(4, 'Sky trip two')
        self.clear_ridge(True, 'Sky trip two combat')
        self.nextroom(0, 'DOWN')

    def core_trips(self):
        self.fixture('sky-complete.sav')
        # Earn real event credit before taking the first direct Core exit.
        self.departure(4, 'Core preparation Sky trip')
        self.clear_ridge(True, 'Core preparation combat')
        self.nextroom(0, 'DOWN')
        self.departure(9, 'Core trip one')
        self.navigate(208, 120, radius=10)
        self.tap('A')
        self.dialogs()
        self.check(self.get('room') == 15, 'Core trip enters the authored Amber workshop')
        self.select(3)
        for x, y, face in ((88, 104, 'UP'), (88, 88, 'UP'),
                           (120, 88, 'RIGHT'), (152, 72, 'DOWN')):
            self.navigate(x, y, radius=1)
            self.step(1, face)
            self.step(1)
            self.tap('A')
        self.navigate(200, 80, radius=1)
        self.ready()
        self.tap('R')
        self.dialogs()
        earned = self.sample('Core workshop completed')
        self.check(earned.expedition_events[48] & 128 and
                   earned.lifetime_field_aid[0] & 128 and self.instance(3).trial_flags & 8,
                   'Core workshop earns real expedition credit and permanent trial/aid records')
        self.navigate(120, 136)
        self.nextroom(9, 'DOWN')
        if self.get('py') > 136:
            self.goto(y=134)
        self.object('slope_rest')
        self.reload_checkpoint('core-same-expedition', 9)
        self.nextroom(0, 'DOWN')
        self.departure(9, 'Core trip two')
        self.check(self.roster().lifetime_field_aid[0] & 128 and self.instance(3).trial_flags & 8,
                   'Repeated Core departure preserves permanent aid and personal trial credit')

    def run(self):
        self.sky_trips()
        self.core_trips()
        for fixture in self.fixtures:
            self.check(digest(ROOT / 'tests/fixtures/v4' / fixture['file']) == fixture['sha256'],
                       fixture['file'] + ': original fixture remains unchanged')

    def report(self):
        result = {
            'suite': 'expedition-controller-regression',
            'rom_sha256': digest(self.rom), 'symbol_sha256': digest(self.symbol_path),
            'controller_only': True, 'game_ram_writes': 0,
            'fixtures': self.fixtures, 'passes': self.passes, 'failures': self.failures,
            'ledger_samples': self.ledger_samples, 'final': self.status(),
            'controller_inputs': 'controller-inputs.json',
        }
        (self.out / 'expedition-report.json').write_text(json.dumps(result, indent=2) + '\n')
        (self.out / 'controller-inputs.json').write_text(json.dumps(self.inputs, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'build/emberbond.gba')
    parser.add_argument('--symbols', type=Path, default=ROOT / 'build/emberbond.sym')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/expedition-qa')
    args = parser.parse_args()
    run = ExpeditionRun(args.rom, args.symbols, args.output)
    try:
        run.run()
    except Exception as exc:
        run.failures.append({'error': str(exc), 'status': run.status()})
        run.shot('failure')
        raise
    finally:
        run.report()
        run.e.close()
    return int(bool(run.failures))


if __name__ == '__main__':
    raise SystemExit(main())
