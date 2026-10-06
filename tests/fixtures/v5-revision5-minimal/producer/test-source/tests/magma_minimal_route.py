#!/usr/bin/env python3
"""Authenticated Southern minimal-eight to Magma main ending, native buttons only.

This suite earns ten actual retained individuals and ten history entries. It does
not synthesize catalog rows, prior progression, equipment, health or trial flags.
Developer-only evidence contains the complete route. No RAM/state writes are
allowed; the final independent session imports only its own exact-hash SRAM.
"""
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
from magma_journey import MagmaJourney, ROOT, Emulator, digest
from test_southern_frozen_fixtures import read_frozen_report, PINS
from test_save5 import Instance

OLD_FORMS = [1, 4, 7, 10, 19, 77, 79, 85]
OLD_QUESTS = [3 if q in (11, 13, 21, 22, 23, 24) else 0 for q in range(30)]

class ControllerOnlyEmulator(Emulator):
    def write(self, *args, **kwargs):
        raise AssertionError('Game RAM writes are forbidden')
    def state(self, path, load=False):
        assert not load, 'The minimal route never imports machine state'
        return super().state(path, False)

class MagmaMinimalRoute(MagmaJourney):
    def __init__(self, *args, **kwargs):
        self.completed = False
        self.session = 0
        self.imports = []
        self.field_commands = []
        self.records = {}
        super().__init__(*args, **kwargs)
        pin = PINS['minimal8']
        producer = read_frozen_report('minimal8')
        assert digest(self.fixture) == pin['fixture_sha256']
        assert producer['controller_only'] and producer['game_ram_writes'] == 0
        assert not producer['failures'] and all(c['passed'] for c in producer['checks'])
        endpoint = producer['snapshots'][pin['snapshot']]
        assert endpoint['sram_sha256'] == pin['fixture_sha256']
        assert endpoint['owned_form_ids'] == endpoint['obtained_form_ids'] == OLD_FORMS
        self.provenance['minimal_source_report_sha256'] = pin['report_sha256']
        self.provenance['minimal_source_snapshot'] = pin['snapshot']
        self.e.close()
        self.e = ControllerOnlyEmulator(self.rom)
        self.import_sram(self.fixture, digest(self.fixture))
        self.test_sources['tests/magma_minimal_route.py'] = digest(Path(__file__))
        self.test_sources['tests/test_southern_frozen_fixtures.py'] = digest(ROOT/'tests/test_southern_frozen_fixtures.py')
        for path, sha in self.test_sources.items():
            source = ROOT/path
            assert digest(source) == sha
            target = self.out/'test-source'/path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    def import_sram(self, path, sha):
        assert digest(path) == sha
        self.imports.append({'session': self.session, 'path': str(path), 'sha256': sha, 'machine_state_loaded': False})
        self.e.load_save(path)
        self.e.reset()

    def report(self):
        super().report()
        path = self.out/'magma-journey.json'
        data = json.loads(path.read_text())
        data.update(suite='magma-minimal-native-controller-route', completed=self.completed,
                    machine_state_loads=0, cold_sram_imports=self.imports,
                    field_commands=self.field_commands, state_records=self.records,
                    synthetic_gameplay=False, enabled_rows_are_not_acquisition_evidence=True,
                    coverage_scope='Main-only minimal prerequisite proof; no optional acquisitions or evolutions claimed')
        (self.out/'magma-minimal-route.json').write_text(json.dumps(data, indent=2)+'\n')

    def record(self, name):
        s = self.state()
        self.records[name] = {
            'status': self.status(), 'obtained_form_ids': self.collection(),
            'individuals': [{'instance_id': c.instance_id, 'form_id': c.form_id, 'record_hex': bytes(c).hex()} for c in self.live()],
            'quests': [self.quest(q) for q in range(38)], 'objectives': list(s.quests.objectives),
            'gear': [g.item_id for g in s.equipment.bag if g.item_id],
            'equipped': [s.equipment.bag[i].item_id if i < 48 else 0 for i in s.equipment.equipped],
            'old_instance_progression_deltas': [
                {'instance_id': c.instance_id, **{field: getattr(c, field)-getattr(Instance.from_buffer_copy(self.old_records[c.instance_id]), field)
                                                for field in ('level', 'bond', 'xp')}}
                for c in self.live() if c.instance_id in self.old_records]}
        self.report()

    def optional_absent(self):
        s = self.state()
        self.check([self.quest(q) for q in range(30)] == OLD_QUESTS, 'all thirty old quest states remain unchanged')
        self.check(list(s.quests.objectives[:30]) == self.old_objectives, 'all thirty old quest objective values remain unchanged')
        self.check([(s.quests.rewards[q>>3]>>(q&7))&1 for q in range(30)] == self.old_rewards, 'all thirty old quest reward receipts remain unchanged')
        self.check(list(s.quests.variables[:30]) == self.old_variables, 'all thirty old quest variables remain unchanged')
        self.check(self.get('chapter_flags') == 3, 'unearned Core and ending flags remain absent')
        self.check(all(not self.quest(q) and not s.quests.objectives[q] for q in range(33, 38)), 'all five optional Magma quests remain absent')
        self.check(all(not c.trial_flags for c in self.live()), 'no personal trial or evolved prerequisite is earned')
        current = {c.instance_id: c for c in self.live() if c.instance_id in self.old_records}
        self.check(set(current) == set(self.old_records), 'all eight historical individual IDs remain owned')
        for identity, raw in self.old_records.items():
            previous = Instance.from_buffer_copy(raw)
            present = current[identity]
            normalized = bytearray(bytes(present))
            for field in ('level', 'bond', 'xp'):
                self.check(getattr(present, field) >= getattr(previous, field), 'ordinary party progression never reduces old '+field)
                offset = getattr(Instance, field).offset
                size = getattr(Instance, field).size
                normalized[offset:offset+size] = raw[offset:offset+size]
            self.check(bytes(normalized) == raw, 'old instance keeps exact form identity commands seed and trial fields; only normal XP bond level may grow')

    def boot(self):
        super().boot()
        self.check(self.minimal, 'suite uses authenticated eight-individual source')
        self.check(self.collection() == OLD_FORMS and [c.form_id for c in self.live()] == OLD_FORMS, 'genuine source owns eight actual unevolved individuals and eight history entries')
        self.old_records = {c.instance_id: bytes(c) for c in self.live()}
        self.old_objectives = list(self.state().quests.objectives[:30])
        self.old_rewards = [(self.state().quests.rewards[q>>3]>>(q&7))&1 for q in range(30)]
        self.old_variables = list(self.state().quests.variables[:30])
        self.check([g.item_id for g in self.state().equipment.bag if g.item_id] == [1, 4], 'only guaranteed starter and prior mandatory quest equipment exist')
        self.optional_absent()
        self.record('before-new-teaching')

    def field(self, form, x, y, face=1):
        super().field(form, x, y, face)
        self.field_commands.append({'frame': self.e.frame, 'room': self.get('room'), 'form_id': form,
                                    'instance_id': self.selected().instance_id, 'target': [x, y]})

    def run(self):
        self.boot()
        self.recruits_main()
        self.check([c.form_id for c in self.live()] == OLD_FORMS+[31, 34], 'only two new teaching companions are actually recruited')
        self.check([c.instance_id for c in self.live()] == list(range(1, 11)), 'new individuals have IDs nine and ten, preserving all earlier IDs')
        self.main_route()
        self.check(set(self.main_selections) <= {31, 34}, 'entire mandatory path selects only new teaching companions31 and34')
        self.check(all(row['form_id'] in (31, 34) for row in self.field_commands), 'all required field actions use teaching bases31 and34')
        self.check([self.state().equipment.bag[i].item_id if i < 48 else 0 for i in self.state().equipment.equipped] == [1, 0, 0, 0, 0], 'main clear uses only starter sword with no equipped armor or accessories')
        self.check(self.collection() == sorted(OLD_FORMS+[31, 34]), 'main clear manufactures no optional or evolved history')
        self.optional_absent()
        self.record('main-cleared')
        name = self.snapshot('08-minimal-main-cleared')
        before = (bytes(self.roster()), bytes(self.state().quests), bytes(self.state().equipment))
        snap = self.snapshots[name]
        self.e.close()
        self.session += 1
        self.e = ControllerOnlyEmulator(self.rom)
        self.import_sram(snap['sram_path'], snap['sram_sha256'])
        self.step(150)
        self.tap('START', 2, 35)
        self.settle()
        self.check((bytes(self.roster()), bytes(self.state().quests), bytes(self.state().equipment)) == before, 'independent cold reboot preserves exact retained roster quests and equipment')
        self.check(self.get('room') == 38, 'independent reboot returns to actual new town checkpoint')
        self.optional_absent()
        self.record('independent-reboot')
        self.snapshot('09-minimal-independent-reboot')
        self.entry(30)
        self.check(self.get('room') == 30, 'ordinary lift returns to old region without a softlock')
        self.optional_absent()
        self.record('old-region-return')
        self.snapshot('10-minimal-old-region-return')
        self.completed = True
        self.report()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('rom', 'symbols', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    for key in ('expected-rom-sha', 'expected-symbols-sha'):
        parser.add_argument('--'+key, required=True)
    parser.add_argument('--source-sram', type=Path, default=ROOT/'tests/fixtures/v5-revision4/southern-minimal8-town.sav')
    parser.add_argument('--source-manifest', type=Path)
    a = parser.parse_args()
    run = MagmaMinimalRoute(a.rom, a.symbols, a.output, a.expected_rom_sha, a.expected_symbols_sha, a.source_sram, a.source_manifest)
    try:
        run.run()
    except Exception as exc:
        run.failures.append({'error': str(exc), 'status': run.status()})
        run.snapshot('failure', settle=False)
        raise
    finally:
        run.report()
        run.e.close()
    print(json.dumps({'completed': run.completed, 'checks': len(run.checks), 'report_sha256': digest(run.out/'magma-minimal-route.json')}))

if __name__ == '__main__':
    main()
