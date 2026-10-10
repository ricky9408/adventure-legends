#!/usr/bin/env python3
"""Explicitly segmented same-candidate Return diagnostics, never acceptance.

Imports only a hash-paired snapshot produced by the controller journey on the
same exact ROM/ELF/symbols. The original complete producer remains untouched.
"""
from collections import deque
import argparse
import json
from pathlib import Path
import traceback

from return_journey import ReturnJourney, ROOT, digest
from magma_journey import MagmaJourney
from underwater_journey import UnderwaterJourney
from underwater_collection_route import UnderwaterCollectionRoute
from return_collection_route import TRIALS
from northern_journey import newest_bank
from return_journey import ReadOnlyGameEmulator, PLAY


class Followup(ReturnJourney):
    def report(self):
        super().report()
        path = self.out / 'return-journey.json'
        data = json.loads(path.read_text())
        data['segmented_diagnostic'] = True
        data['source_producer'] = getattr(self, 'source_producer', None)
        data['not_an_uninterrupted_acquisition_producer'] = True
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    def import_producer(self, path, expected_sha, snapshot):
        assert digest(path) == expected_sha, 'producer report differs from its explicit hash'
        producer = json.loads(Path(path).read_text())
        assert producer['controller_only'] and not producer['game_ram_writes']
        assert producer['finished_scope'] == 'full' and not producer['machine_state_loads']
        assert not producer['provenance']['cross_rom_machine_state_loaded']
        for key in ('rom_sha256', 'symbols_sha256', 'elf_sha256'):
            assert producer[key] == self.candidate[key]
        assert producer['source_manifest_sha256'] == self.source_manifest_sha
        assert all(f.get('kind') == 'native-cadence' for f in producer['failures']), 'producer has unresolved non-timing failure'
        saved = producer['snapshots'][snapshot]
        assert len(saved['obtained_form_ids']) == 104 and len(saved['individuals']) == 52
        assert saved['quests'].count(3) == 54 and len(saved['gear_items']) == 42
        self.source_producer = {'report': str(Path(path).resolve()), 'sha256': expected_sha,
                                'snapshot': snapshot, 'known_failures': producer['failures'],
                                'source_helper_manifest_sha256': digest(Path(path).parent / 'helper-source-hashes.json')}
        self.producer_snapshots = producer['snapshots']
        self.snapshots['paired-producer-import'] = saved
        self.restore('paired-producer-import')
        self.check(len(self.collection()) == 104 and len(self.live()) == 52, 'paired exact-candidate import contains genuinely earned104/52 producer state')
        self.snapshot('followup-start')

    def mask(self):
        if 38 <= self.get('room') < 54:
            return UnderwaterJourney.mask(self)
        return super().mask()

    def entry(self, target):
        here = self.get('room')
        if here >= 46 and here < 54 and target >= 46 and target < 54:
            return UnderwaterJourney.entry(self, target)
        if (here, target) in ((38, 39), (39, 38), (38, 40), (39, 41), (39, 42), (42, 43), (43, 44)):
            return MagmaJourney.entry(self, target)
        if (here, target) in ((40, 38), (41, 39), (42, 39), (43, 42), (44, 43)):
            return self.leave_interior(target)
        return super().entry(target)

    def travel(self, target, clear=False):
        graph = {0: [1, 54, 60], 1: [0, 16], 16: [1, 17, 22, 55], 17: [16, 56],
                 22: [16, 30, 57], 30: [22, 38, 58], 38: [30, 39, 40, 46],
                 39: [38, 41, 42], 40: [38], 41: [39], 42: [39, 43], 43: [42, 44], 44: [43],
                 46: [38, 47, 48], 47: [46, 50], 48: [46, 49, 51], 49: [48, 52],
                 50: [47, 51], 51: [50, 52, 48], 52: [51, 53, 49], 53: [52, 46],
                 54: [0], 55: [16], 56: [17], 57: [22], 58: [30, 59], 59: [58], 60: [0, 61], 61: [60]}
        queue, seen = deque([(self.get('room'), [])]), {self.get('room')}
        while queue:
            room, path = queue.popleft()
            if room == target:
                for destination in path:
                    self.entry(destination)
                if clear:
                    if target == 39:
                        self.target(80, 264)
                    if any(e['hp'] > 0 for e in self.enemies()):
                        self.clear_enemies()
                    self.step(60)
                return
            for destination in graph[room]:
                if destination not in seen:
                    seen.add(destination)
                    queue.append((destination, path + [destination]))
        raise AssertionError(('no connected old-repeat route', self.get('room'), target))

    def legacy_repeat_route(self):
        baseline = {c.instance_id: c.form_id for c in self.live()}
        history = self.collection()
        for form in (37, 40, 43, 46):
            area, x, y = {37: (39, 80, 232), 40: (41, 176, 64), 43: (40, 160, 112), 46: (39, 424, 240)}[form]
            self.travel(area, clear=True)
            self.goto(x, y + 16, radius=4)
            self.face(1)
            self.step(120)
            before = {c.instance_id: bytes(c) for c in self.live()}
            # Some historical synchronous validation occupies multiple native
            # frames. Keep the input released long enough to observe a genuine
            # second A edge, and retain every stall in the measured trace.
            self.measured('legacy-invitation-' + str(form), lambda: (self.tap('A', 2, 120), self.settle(), self.tap('A', 2, 120), self.settle()))
            fresh = [c for c in self.live() if c.instance_id not in before]
            self.check(len(fresh) == 1 and fresh[0].form_id == form and fresh[0].instance_id not in baseline,
                       'released Magma repeat source earns one additional real identity under revision7')
            self.check(all(bytes(c) == before[c.instance_id] for c in self.live() if c.instance_id in before),
                       'legacy repeat invitation alters no previous individual')
            self.snapshot('legacy-repeat-' + str(form))
        for form in range(49, 73, 3):
            before = len(self.live())
            UnderwaterCollectionRoute.repeat_underwater(self, form)
            self.check(len(self.live()) == before + 1, 'released Underwater repeat earns one additional real identity under revision7')
        self.check(len(self.live()) == 64 and self.collection() == history, 'all12 released repeat families remain actually obtainable under revision7')
        self.check(all(next(c for c in self.live() if c.instance_id == identity).form_id == form for identity, form in baseline.items()),
                   'all52 prior terminal individuals retain exact identity and form through old repeats')
        self.snapshot('legacy12-repeats64-retained')

    def trial_control_matrix(self):
        """Real controls at every nonterminal authored stage, paired branches.

        This supplements the uninterrupted producer rather than replacing it.
        Empty/sole-command cases are explicitly not applicable, not fake edits.
        """
        actions = {
            0: ['m', 0], 1: [0, 1, 'm'], 2: ['m', 0, 'w'],
            3: ['m', 0, 'w'], 4: ['m', 0, 'w'], 5: ['m', 0, 1],
            6: ['m', 0], 7: [0, 'm', 'w'], 8: ['m', 0],
            9: ['m', 0, 1, 'm'], 10: ['m', 0], 11: [0, 1, 'w'],
            12: ['m', 0, 'w'],
        }
        for index, definition in enumerate(TRIALS):
            source = self.producer_snapshots[f'trial-{index:02d}-start']
            self.snapshots[f'matrix-origin-{index:02d}'] = source
            self.restore(f'matrix-origin-{index:02d}')
            self.check(self.trial().index == index and not self.trial().replay,
                       'matrix begins at an original unearned same-candidate trial snapshot')
            original = self.state_signature()
            for stage, action in enumerate(actions[index]):
                if stage:
                    self.restore(previous)
                if action == 'm':
                    self.target(*definition[5])
                elif action == 'w':
                    self.goto(*definition[7], radius=4)
                    self.step(4)
                else:
                    self.trial_cast(index, action)
                self.check(self.trial().index == index, 'nonterminal prefix retains its explicit trial')
                previous = self.snapshot(f'matrix-{index:02d}-partial-{stage:02d}')
                proof = bytes(self.trial())
                person = self.roster().instances[self.trial().slot]
                identity, trial_flags = person.instance_id, person.trial_flags

                # Read-only journal viewing must not count as a selection edit.
                self.measured(f'trial{index}-stage{stage}-journal-view',
                              lambda: (self.open_tab(3), self.close_menu()))
                self.check(bytes(self.trial()) == proof, 'read-only journal view retains exact partial proof')
                self.check(next(c for c in self.live() if c.instance_id == identity).trial_flags == trial_flags,
                           'read-only journal gives no new trial credit')

                self.restore(previous)
                selected = self.roster().selected_party
                other = next(p for p in range(4) if p != selected and self.roster().party[p] < 160)
                self.select_slot(other)
                self.check(self.trial().index == 255, 'actual selected-individual change cancels partial proof')

                self.restore(previous)
                selected = self.roster().selected_party
                self.assign((selected + 1) % 4, self.selected().form_id)
                self.check(self.trial().index == 255, 'actual party-slot reorder cancels partial proof')

                self.restore(previous)
                c = self.selected()
                alternate = next((n for n in c.equipped if n and n != self.command()), None)
                if alternate is not None:
                    self.set_command(alternate)
                    self.check(self.trial().index == 255, 'actual equipped-command selection cancels partial proof')
                else:
                    self.cases.append({'trial': index, 'stage': stage, 'case': 'command-swap',
                                       'not_applicable': 'This predecessor has only one equipped learned command'})

                self.restore(previous)
                self.reset_return()
                self.check(next(c for c in self.live() if c.instance_id == identity).trial_flags == trial_flags,
                           'confirmed reset does not award trial credit')

                self.restore(previous)
                area = self.get('room')
                parent = self.return_geometry['rooms'][area - 54]['exits'][0]['target']
                self.entry(parent)
                self.entry(area)
                self.check(self.trial().index == 255 and next(c for c in self.live() if c.instance_id == identity).trial_flags == trial_flags,
                           'ordinary exit and reentry cancel partial proof without a reward')

                self.restore(previous)
                saved = self.snapshots[previous]
                bank = newest_bank(Path(saved['sram_path']).read_bytes())
                self.e.close()
                self.e = ReadOnlyGameEmulator(self.rom)
                self.e.load_save(saved['sram_path'])
                self.e.reset()
                self.step(150)
                self.measured(f'trial{index}-stage{stage}-bounded-cold',
                              lambda: (self.tap('START', 2, 90), self.settle()), cold_continue=True)
                now = newest_bank(self.e.bytes(0x0e000000, 32768))
                self.check(now[32:] == bank[32:] and self.trial().index == 255,
                           'SRAM-only cold Continue preserves durable payload and discards partial trial proof')
                self.cases.append({'trial': index, 'stage': stage,
                                   'completed_cases': ['read-only-view', 'selected-individual', 'party-reorder',
                                                       'command-if-available', 'reset', 'exit-reentry', 'cold-load'],
                                   'partial_snapshot': previous, 'original_trial_flags': trial_flags})
                self.report()
            self.check(original[2] == self.state_signature()[2], 'trial control matrix grants no gear reward')
        self.snapshot('all13-trial-controls-complete')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('rom', 'symbols', 'source-manifest', 'producer-report', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    for key in ('expected-rom-sha', 'expected-symbols-sha', 'expected-elf-sha', 'expected-manifest-sha', 'expected-producer-sha'):
        p.add_argument('--' + key, required=True)
    p.add_argument('--producer-snapshot', default='05-all104-cold-reboot-after')
    p.add_argument('--source-root', type=Path)
    p.add_argument('--work', choices=('new-repeats', 'legacy-repeats', 'trial-controls'), required=True)
    p.add_argument('--timing-mode', choices=('strict', 'collect-diagnostic'), default='collect-diagnostic')
    a = p.parse_args()
    r = Followup(a.rom, a.symbols, a.output, a.expected_rom_sha, a.expected_symbols_sha, a.expected_elf_sha,
                 a.source_manifest, a.expected_manifest_sha, source_root=a.source_root, timing_mode=a.timing_mode)
    try:
        r.boot()
        r.import_producer(a.producer_report, a.expected_producer_sha, a.producer_snapshot)
        if a.work == 'new-repeats':
            r.repeat_route()
        elif a.work == 'legacy-repeats':
            r.legacy_repeat_route()
        else:
            r.trial_control_matrix()
        r.finished_scope = 'segmented-' + a.work
        r.verify_closures()
    except Exception as exc:
        r.failures.append({'error': str(exc), 'traceback': traceback.format_exc(), 'status': r.status()})
        r.snapshot('failure', settle=False)
        raise
    finally:
        r.close_global_trace()
        r.report()
        r.e.close()
    return bool(r.failures)


if __name__ == '__main__':
    raise SystemExit(main())
