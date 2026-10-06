#!/usr/bin/env python3
"""Independent native minimal-player lifecycle/exit QA; controller input only.

Consumes a successful exact-candidate main journey, then imports only its
hash-checked SRAM into fresh emulator instances. No machine state is loaded.
Helper imports are from an immutable evidence snapshot, not a mutable checkout.
All failures are retained. This is emulator evidence, not handheld testing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import traceback

ROM_SHA = '0d7fd78733405a6fc8ec6eeca68ad207dfb11b91dcfe44a8d67f312552b46675'
SYM_SHA = 'da6615df0f932eb5f096442092962d2fa28fad684758640c65175bc535d8b176'
MANIFEST_SHA = 'f75b5b9924bda3e9118e64f80f12f5905d1d72cef166980c3d8a94d407484580'
HELPER_SHA = '0ce885569b4af71a17853a9c0f373656756aa247a3a36f061d57336ca428611a'
MINIMAL_SHA = 'f584de3b29cb77731148b31b99dc40e0c7e4ec05f1aac42e0d38dd5b44612eeb'
ALL65_SHA = 'a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858'
EXPECTED_FORMS = [1, 4, 7, 10, 19, 31, 34, 49, 52, 77, 79, 85]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    global ROM_SHA,SYM_SHA,MANIFEST_SHA,HELPER_SHA
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('rom', 'symbols', 'source-manifest', 'helper-snapshot', 'source-sram', 'source-report', 'output'):
        p.add_argument('--' + arg, type=Path, required=True)
    for label, default in (('expected-rom-sha',ROM_SHA),('expected-symbols-sha',SYM_SHA),('expected-manifest-sha',MANIFEST_SHA),('expected-helper-sha',HELPER_SHA)):
        p.add_argument('--'+label,default=default)
    p.add_argument('--loading-policy',choices=('strict-historical','bounded-cold'),default='strict-historical')
    a = p.parse_args()
    ROM_SHA,SYM_SHA,MANIFEST_SHA,HELPER_SHA=a.expected_rom_sha,a.expected_symbols_sha,a.expected_manifest_sha,a.expected_helper_sha
    a.output.mkdir(parents=True, exist_ok=True)
    assert sha(a.rom) == ROM_SHA and sha(a.symbols) == SYM_SHA
    assert sha(a.source_manifest) == MANIFEST_SHA and sha(a.source_sram) == MINIMAL_SHA
    pinned = json.loads((a.helper_snapshot / 'source-snapshot-hashes.json').read_text())
    assert all(sha(a.helper_snapshot / key) == val for key, val in pinned.items())
    assert sha(a.helper_snapshot / 'tests/underwater_journey.py') == HELPER_SHA
    sys.dont_write_bytecode = True
    sys.path.insert(0, str((a.helper_snapshot / 'tests').resolve()))
    from underwater_journey import UnderwaterJourney, ReadOnlyGameEmulator, PLAY, DEAD, SAVING, EVENT_PENDING
    from northern_journey import newest_bank
    source = json.loads(a.source_report.read_text())
    assert source['rom_sha256'] == ROM_SHA and source['symbols_sha256'] == SYM_SHA
    assert source['controller_only'] and source['game_ram_writes'] == 0
    assert not source['provenance']['cross_rom_machine_state_loaded']
    assert source['provenance']['sram_sha256'] == MINIMAL_SHA
    assert source['source_manifest_sha256'] == MANIFEST_SHA
    assert not source['failures'] and all(c['passed'] for c in source['checks'])
    terminal = source['snapshots']['09-main-cleared-town']
    initial_sram = Path(terminal['sram_path'])
    assert sha(initial_sram) == terminal['sram_sha256']
    assert terminal['obtained_form_ids'] == EXPECTED_FORMS
    assert len(terminal['owned_form_ids']) == 12

    class ColdOnlyEmulator(ReadOnlyGameEmulator):
        """Block both public and direct bridge writes and machine-state imports."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._state_function = self.lib.eb_state
            def guarded_state(ptr, path, load):
                if load:
                    raise AssertionError('Machine-state imports are forbidden in this suite')
                return self._state_function(ptr, path, 0)
            self.lib.eb_state = guarded_state
        def state(self, path, load=False):
            if load:
                raise AssertionError('Machine-state imports are forbidden in this suite')
            return super().state(path, False)

    class Review(UnderwaterJourney):
        def __init__(self):
            self.review = {
                'suite': 'underwater-independent-minimal-native-review',
                'candidate_frozen': True, 'controller_only': True,
                'game_ram_writes': 0, 'machine_state_loads': 0,
                'source_main_report_sha256': sha(a.source_report),
                'source_main_report': str(a.source_report.resolve()),
                'source_main_assertions': len(source['checks']),
                'source_main_terminal_sram_sha256': sha(initial_sram),
                'helper_source_snapshot_sha256': sha(a.helper_snapshot / 'source-snapshot-hashes.json'),
                'review_source_sha256': sha(__file__),
                'cold_boots': [], 'exit_checks': [], 'damage_trace': [],
                'scope_limits': ['Native emulator, not physical handheld',
                                 'Main route, save/reboot, death/retry, and ordinary exits; optional quests/trials are out of scope']}
            self.trace = None
            super().__init__(a.rom, a.symbols, a.output, ROM_SHA, SYM_SHA,
                             fixture=a.source_sram, source_manifest=a.source_manifest)
            self.e.close()
            self.e = None
            self.first_ten = [self.source_bank[160+i*24:184+i*24] for i in range(10)]
        def report(self):
            super().report()
            data = {**self.review, **self.candidate,
                    'source_manifest_sha256': self.source_manifest_sha,
                    'provenance': self.provenance,
                    'checks': self.checks, 'failures': self.failures,
                    'cases': self.cases, 'snapshots': self.snapshots,
                    'frame_windows': self.frame_windows,
                    'inputs': self.inputs, 'transitions': self.transitions}
            (self.out / 'underwater-minimal-review.json').write_text(json.dumps(data, indent=2) + '\n')
        def step(self, n, keys=0):
            if self.trace is None:
                return super().step(n, keys)
            for _ in range(n):
                frame = self.get('frame')
                page = self.e.read(0x04000000, 2) & 16
                super().step(1, keys)
                self.trace.append({'hardware_frame': self.e.frame,
                                   'frame_before': frame, 'frame_after': self.get('frame'),
                                   'counter_reset': self.get('frame') < frame,
                                   'delta': (self.get('frame') - frame) & 0xffffffff,
                                   'flip': (self.e.read(0x04000000, 2) & 16) != page,
                                   'cycles': self.get('render_cycles'),
                                   'state': self.get('game_state'),
                                   'room': self.get('room')})
        def measured(self, name, callback, defer_failure=False, loading=False):
            assert self.trace is None
            self.trace = []
            try:
                callback()
            finally:
                trace, self.trace = self.trace, None
                result = {'name': name, 'hardware_frames': len(trace),
                          'updates': sum(row['delta'] for row in trace if not row['counter_reset']),
                          'raw_modulo_delta_sum': sum(row['delta'] for row in trace),
                          'counter_resets': sum(row['counter_reset'] for row in trace),
                          'flips': sum(row['flip'] for row in trace),
                          'max_cycles': max((row['cycles'] for row in trace), default=0),
                          'save_frames': sum(row['state'] == SAVING for row in trace),
                          'event_frames': sum(row['state'] == EVENT_PENDING for row in trace),
                          'trace': trace}
                self.frame_windows.append(result)
                self.report()
            if loading:
                result['scope']='cold Continue decode and initial checkpoint before active play'
                result['strict_cadence_pass']=bool(trace) and all(row['delta']==1 and row['flip'] and row['cycles']<280896 for row in trace)
                result['gameplay_cadence_exemption']=True
                self.check(0<len(trace)<=120 and self.get('game_state')==PLAY and not self.get('save_failed'),name+' completes bounded cold loading within120 hardware frames before play')
                self.report();return result
            try:
                self.check(bool(trace) and all(row['delta'] == 1 and row['flip'] and row['cycles'] < 280896 for row in trace),
                           name + ' updates and page-flips every native hardware frame within budget')
            except AssertionError as exc:
                if not defer_failure:
                    raise
                self.failures.append({'case': name, 'kind': 'whole-action-native-timing',
                                      'error': str(exc), 'status': self.status(),
                                      'bad_frames': [row for row in trace if row['delta'] != 1 or not row['flip'] or row['cycles'] >= 280896]})
            return result
        def stable(self):
            s = self.state()
            return bytes(s.roster), bytes(s.quests), bytes(s.equipment)
        def retained(self, label):
            self.check(self.collection() == EXPECTED_FORMS and len(self.live()) == 12,
                       label + ': exactly twelve retained base individuals and histories')
            self.check(sorted(c.instance_id for c in self.live()) == list(range(1, 13)),
                       label + ': all original identities plus only the two teaching identities')
            self.check(all(self.quest(q) == 3 for q in (38, 39, 40)) and self.state().quests.objectives[40] == 15,
                       label + ': all three new main quests and all four archive objectives retained')
            self.check(all(self.quest(q) == 0 for q in range(41, 45)) and all(c.trial_flags == 0 for c in self.live()),
                       label + ': no optional quest/trial or evolution requirement introduced')
            for i, old in enumerate(self.first_ten):
                new = bytes(self.state().roster.instances[i])
                self.check(new[:2] == old[:2] and new[8:] == old[8:],
                           label + f': original individual{i+1} identity/form/commands/seed/trials retained')
        def cold_boot(self, save, label, expected_sha=None):
            if expected_sha:
                assert sha(save) == expected_sha
            bank = newest_bank(Path(save).read_bytes())
            if self.e:
                self.e.close()
            self.e = ColdOnlyEmulator(self.rom)
            self.check(int.from_bytes(bank[12:14], 'little') == 6, label + ': source is genuine current-revision SRAM')
            self.e.load_save(save)
            self.e.reset()
            self.step(150)
            self.measured(label + '-whole-continue', lambda: (self.tap('START', 2, 50), self.settle()), defer_failure=True,loading=a.loading_policy=='bounded-cold')
            self.check(self.get('game_state') == PLAY and self.get('save_failed') == 0,
                       label + ': fresh emulator Continue completes normally')
            current = newest_bank(self.e.bytes(0x0e000000, 32768))
            self.check(current[32:] == bank[32:], label + ': Continue retains exact durable SRAM payload')
            self.review['cold_boots'].append({'label': label, 'source_sram_sha256': sha(save),
                                              'source_sram_path': str(Path(save).resolve()),
                                              'fresh_emulator': True, 'machine_state_loaded': False,
                                              'status': self.status()})
            self.retained(label)
        def baseline(self, name):
            self.cold_boot(initial_sram, name, terminal['sram_sha256'])
        def safe_save(self, room, name):
            self.check(self.get('room') == room, name + ': at intended anchor room')
            x = 80 if room == 46 else 64
            self.goto(x, 272, radius=4)
            self.face(1)
            result = self.measured(name, lambda: (self.tap('A', 2, 3), self.settle()))
            self.check(self.get('checkpoint_spawn') == 2 and self.get('hp') > 0,
                       name + ': native rest records real safe checkpoint')
            self.check(result['save_frames'] > 0 and result['event_frames'] > 0,
                       name + ': timing includes actual staged anchor event and SRAM save')
            return self.snapshot(name)
        def cold_save_case(self):
            self.baseline('main-independent-cold-import')
            self.snapshot('10-main-independent-cold-import')
            self.safe_save(46, '11-main-native-save')
            before = self.stable()
            s = self.snapshots['11-main-native-save']
            self.cold_boot(s['sram_path'], 'native-save-independent-reboot', s['sram_sha256'])
            self.check(self.stable() == before, 'native rest and independent reboot preserve exact roster, quest, and equipment bytes')
            self.snapshot('12-main-native-reboot')
        def checked_exit(self, target, expected_spawn=None):
            source_room = self.get('room')
            before_forms = self.collection()
            before_ids = [(c.instance_id, c.form_id) for c in self.live()]
            def move():
                for _ in range(60):
                    if not self.get('transition_lock'):
                        break
                    self.step(1)
                self.check(not self.get('transition_lock'), f'exit{source_room}->{target}: existing transition debounce clears naturally')
                if source_room == 38 and target == 46:
                    self.goto(416, 240, radius=4)
                    self.face(1)
                    self.tap('A')
                    self.settle()
                    self.check(self.get('room') == 46, 'real shell-lift interaction re-enters Underwater with retained new progress')
                else:
                    self.entry(target)
            self.measured(f'whole-exit-{source_room}-to-{target}', move, defer_failure=True)
            self.check(self.get('game_state') == PLAY and not self.get('save_failed'),
                       f'exit{source_room}->{target}: valid live destination')
            if expected_spawn is not None:
                self.check(self.get('checkpoint_spawn') == expected_spawn,
                           f'exit{source_room}->{target}: reciprocal spawn{expected_spawn}')
            self.check(self.collection() == before_forms and [(c.instance_id, c.form_id) for c in self.live()] == before_ids,
                       f'exit{source_room}->{target}: exact owned identities and history retained')
            self.check(all(self.quest(q) == 3 for q in (38, 39, 40)),
                       f'exit{source_room}->{target}: new main progress retained')
            x, y = self.get('px'), self.get('py')
            blocked, w, h = self.mask()
            self.check(0 <= x < w and 0 <= y < h and not blocked[y*w+x],
                       f'exit{source_room}->{target}: physical landing is collision-clear')
            self.review['exit_checks'].append({'from': source_room, 'to': target,
                                              'spawn': self.get('checkpoint_spawn'), 'position': [x, y],
                                              'frame': self.e.frame})
            self.report()
        def surface_return_case(self):
            self.baseline('surface-return-baseline')
            self.checked_exit(38, 4)
            self.check((self.get('px'), self.get('py')) == (416, 240),
                       'Underwater south return lands at Magma shell-lift spawn4 (416,240)')
            self.snapshot('13-magma-shell-lift-return')
            self.checked_exit(46, 0)
            self.snapshot('14-underwater-shell-lift-reentry')
            self.retained('surface reciprocal return')
        def gardens_case(self):
            self.baseline('optional-ordinary-exits-baseline')
            for room, spawn in ((47,0),(46,3),(48,0),(49,0),(48,1),(46,1)):
                self.checked_exit(room, spawn)
            self.snapshot('15-optional-gardens-return')
            self.retained('ordinary optional garden exits')
        def archive_case(self):
            self.baseline('archive-reciprocal-exits-baseline')
            for room, spawn in ((47,0),(50,0),(47,1),(50,0),(51,0),(50,1),(51,0),(52,0),
                                (51,1),(48,2),(51,2),(52,0),(49,1),(52,2),(53,0),(52,1),(53,0),(46,1)):
                self.checked_exit(room, spawn)
            self.snapshot('16-archive-reciprocal-returns')
            self.retained('archive reciprocal and optional shortcut exits')
        def cold_dialog_case(self):
            self.baseline('cold-dialogs-baseline')
            before = self.stable()
            self.measured('cold-keeper-return-dialog', lambda: self.target(120, 72), defer_failure=True)
            self.measured('cold-shellwright-return-dialog', lambda: self.target(340, 72), defer_failure=True)
            self.check(self.stable() == before, 'repeated keeper and shellwright dialogs are exact durable no-ops')
            self.owned_select(49)
            before = self.stable()
            def preview():
                self.open_tab(3)
                self.tap('SELECT', 2, 4)
                self.wait_evolution(require_ready=False)
            self.measured('cold-ineligible-base-evolution-preview', preview, defer_failure=True)
            self.check(self.get('game_state') == 7 and self.get('progression_evolution_reason') != 0,
                       'minimal base evolution remains visibly ineligible without earned personal trials')
            self.tap('B', 2, 4)
            self.close_menu()
            self.check(self.stable() == before, 'declining ineligible evolution preview preserves exact durable state')
            self.review['evolution_scope'] = 'Ineligible two-branch preview and cancel only; no eligible preparation, evolution, or trial progress fabricated'
            self.snapshot('21-minimal-cold-dialogs-evolution-preview')
        def death_case(self):
            self.baseline('death-retry-baseline')
            self.checked_exit(47, 0)
            self.safe_save(47, '17-commons-safe-rest')
            if self.get('summoned'):
                self.tap('B')
                self.settle()
            before = self.stable()
            self.goto(96, 176, radius=4)
            for _ in range(800):
                self.review['damage_trace'].append({'frame': self.e.frame, 'state': self.get('game_state'),
                                                    'hp_q4': self.hp_q4(),
                                                    'position': [self.get('px'), self.get('py')],
                                                    'live_enemies': [e for e in self.enemies() if e['hp'] > 0]})
                if self.get('game_state') == DEAD:
                    break
                self.step(10)
            self.check(self.get('game_state') == DEAD, 'ordinary Underwater enemy damage reaches death without HP injection')
            self.snapshot('18-ordinary-underwater-death', settle=False)
            self.measured('ordinary-death-retry-native', lambda: (self.tap('A', 2, 30), self.settle()))
            self.check(self.get('room') == 47 and self.get('checkpoint_spawn') == 2 and self.hp_q4() > 0,
                       'ordinary death retry reaches the genuine Commons safe checkpoint')
            self.check(self.stable() == before, 'death/retry preserves exact roster, quests and equipment without duplicates')
            self.retained('death/retry')
            self.snapshot('19-ordinary-underwater-retry')
            s = self.snapshots['19-ordinary-underwater-retry']
            self.cold_boot(s['sram_path'], 'death-retry-independent-reboot', s['sram_sha256'])
            self.check(self.stable() == before, 'post-death independent reboot preserves exact new main progress')
            self.snapshot('20-post-death-cold-reboot')

    r = Review()
    try:
        for name, fn in (('cold-native-save-reboot',r.cold_save_case),
                         ('magma-surface-reciprocal-return',r.surface_return_case),
                         ('ordinary-optional-garden-exits',r.gardens_case),
                         ('archive-and-shortcut-reciprocal-exits',r.archive_case),
                         ('ordinary-death-retry-reboot',r.death_case),
                         ('cold-dialogs-and-ineligible-preview',r.cold_dialog_case)):
            try:
                prior_failures = len(r.failures)
                fn()
                r.cases.append({'case': name, 'passed': len(r.failures) == prior_failures})
            except Exception as exc:
                r.failures.append({'case': name, 'error': str(exc), 'traceback': traceback.format_exc(),
                                   'status': r.status() if r.e else None})
                r.cases.append({'case': name, 'passed': False})
                if r.e:
                    r.snapshot('failure-' + name, settle=False)
                print('FAILED', name, str(exc), flush=True)
            r.report()
        assert all(sha(a.helper_snapshot / k) == v for k, v in pinned.items()), 'Helper snapshot changed during review'
        assert sha(a.rom) == ROM_SHA and sha(a.symbols) == SYM_SHA, 'Candidate changed during review'
        assert all(sha(r.source_root / k) == v for k, v in r.source_hashes.items()), 'Frozen runtime source changed'
    finally:
        r.report()
        if r.e:
            r.e.close()
    print(json.dumps({'checks':len(r.checks), 'failures':r.failures, 'cases':r.cases}, indent=2))
    return bool(r.failures)


if __name__ == '__main__':
    raise SystemExit(main())
