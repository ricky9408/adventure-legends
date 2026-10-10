#!/usr/bin/env python3
"""Continuous, spoiler-free Equipment/Treasures I4 gameplay and native audio.

Loads authenticated, same-build I4 first-Grove SRAM through ordinary cold
Continue on frozen I4. The source was earned from empty cartridge SRAM with
controller input only. Before recording,
real controller input visits the early practice racks, completes three weapon
targets, earns Patchwork Mail, and walks home. The clip demonstrates previously
earned equipment; it does not claim that acquisition happened within the clip.
No ROM patch, game-RAM write, machine-state import, video cut, or speed change.
"""
from __future__ import annotations
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tools')]
from capture_player_feedback_teaser import Capture, FPS
from player_feedback_campaign import ControllerNative
from player_feedback_native import sha
from region_journey import RegionJourney
from connected_roads_journey import ConnectedRoadJourneyMixin
from test_equipment import Stats

ROM_SHA = 'cab76cd98317dfa1dbeaf2713cb4bab42bcdf0973c60cefe3de7e1fbf1aaeddc'
SYM_SHA = '20f0697a7cc14ca960c3660b40e1458115a474f091ca960410790edc6f130a24'
ELF_SHA = 'f688d553b90b224554d10fb1d7adf8bc5ade71dd9f01ec76f689171572daf787'
MANIFEST_SHA = '0bb0d65a1011a375e846e9427b8cd0a5571c316a8f1e98c716818eaabbecb88c'
SOURCE_ROM_SHA = 'cab76cd98317dfa1dbeaf2713cb4bab42bcdf0973c60cefe3de7e1fbf1aaeddc'
SOURCE_SYM_SHA = '20f0697a7cc14ca960c3660b40e1458115a474f091ca960410790edc6f130a24'
SNAPSHOT = 'original-grove-complete-after-continue'


class ReadOnlyNative(ControllerNative):
    def __init__(self, rom, bridge):
        super().__init__(rom, bridge)
        self.lib.eb_write = self.write
        self.lib.eb_state = self.state


class EquipmentCapture(Capture, ConnectedRoadJourneyMixin, RegionJourney):
    def __init__(self, a):
        self.a = a
        self.out = a.output.resolve()
        self.out.mkdir(parents=True, exist_ok=False)
        p = json.loads(a.producer.read_text())
        assert sha(a.producer) == a.producer_sha
        assert p['controller_only'] and p['game_ram_writes'] == p['machine_state_imports'] == 0
        assert p['historical_progress_imports'] == 0 and p['provenance']['initial_sram'] == 'empty cartridge'
        assert p['route_complete'] and not p['failures']
        assert not any(p['metrics'][k] for k in ('active_update_misses', 'active_flip_misses', 'active_overruns', 'faults'))
        assert sha(a.rom) == ROM_SHA and sha(a.symbols) == SYM_SHA
        assert sha(a.rom.with_suffix('.elf')) == ELF_SHA
        assert sha(a.rom.parent / 'source-hashes.json') == MANIFEST_SHA
        assert p['candidate']['rom_sha256'] == SOURCE_ROM_SHA
        assert p['candidate']['symbols_sha256'] == SOURCE_SYM_SHA
        assert sha(a.bridge) == p['candidate']['bridge_sha256']
        record = p['snapshots'][SNAPSHOT]
        source = Path(record['sram_path'])
        assert sha(source) == record['sram_sha256'] and record['candidate_sha256'] == SOURCE_ROM_SHA
        assert record['status']['room'] == 0 and record['status']['chapter_flags'] == 1
        assert record['owned_forms'] == [1, 4, 7]
        for src, name in ((a.producer, 'producer.json'), (source, 'source-earned.sav'), (a.bridge, 'bridge.so')):
            shutil.copyfile(src, self.out / name)
        self.producer = p
        self.capture_candidate = {'rom_sha256': ROM_SHA, 'symbols_sha256': SYM_SHA,
                                  'elf_sha256': ELF_SHA, 'source_manifest_sha256': MANIFEST_SHA,
                                  'bridge_sha256': sha(a.bridge)}
        self.sym = {v[2]: int(v[0], 16) for line in a.symbols.read_text().splitlines() if len(v := line.split()) == 3}
        self.e = ReadOnlyNative(a.rom, self.out / 'bridge.so')
        self.e.load_save(self.out / 'source-earned.sav')
        self.e.reset()
        self.e.lib.eb_audio_start.argtypes = [C.c_void_p, C.c_char_p]
        self.e.lib.eb_audio_start.restype = C.c_int
        self.e.lib.eb_audio_stop.argtypes = [C.c_void_p]
        self.e.lib.eb_audio_stop.restype = C.c_uint
        self.recording = False
        self.encoder = None
        self.rows, self.inputs, self.observations, self.chapters = [], [], [], []
        self.shots = {}
        self.rgb_hash = hashlib.sha256()
        self.layout = json.loads((ROOT / 'assets/region/layout.json').read_text())
        self.world = json.loads((ROOT / 'assets/world_manifest.json').read_text())
        self.campaign = json.loads((ROOT / 'assets/campaign_layouts.json').read_text())
        self.campaign_rooms = {r['id']: r for r in self.campaign['rooms']}
        self.source_snapshot = record

    def get(self, name, width=4):
        return self.e.read(self.sym[name], width)

    def check(self, yes, label):
        if not yes:
            raise AssertionError((label, self.status()))

    def entry(self, target):
        if target != 0:
            return ConnectedRoadJourneyMixin.entry(self, target)
        # Current cold village checkpoints normalize north arrival to zero.
        # Match the current earned-route adapter rather than the old manifest's
        # persisted spawn assertion; no coordinate or checkpoint is changed.
        assert self.g('room') == 1
        self.goto(240, 296, radius=2)
        for _ in range(600):
            if self.g('room') != 1:
                break
            self.step(1, 'DOWN')
        self.settle()
        assert self.g('room') == 0 and self.g('checkpoint_spawn') == 0

    def settle(self):
        for _ in range(2000):
            mode = self.g('game_state')
            if mode == 2 and not self.recording:
                self.tap('A')
            elif mode in (6, 10, 12) or self.g('save_feedback_background') or self.g('save_requested') or self.g('scene_present_phase'):
                self.step()
            else:
                return
        raise AssertionError(('transaction did not settle', self.status()))

    def goto(self, x=None, y=None, radius=4):
        if x is not None and y is not None and not self.recording:
            return RegionJourney.goto(self, x, y, radius)
        return Capture.goto(self, x, y)

    def act(self, x, y, facing=None):
        self.goto(x, y)
        if facing is not None:
            self.tap(('DOWN', 'UP', 'LEFT', 'RIGHT')[facing])
        self.tap('A')
        self.settle()

    def open_gear(self):
        self.tap('START')
        assert self.g('journal_tab') == 13
        self.tap('RIGHT')
        self.tap('A')
        assert self.g('journal_tab') == 4 and self.g('gear_menu_slot') == 0

    def choose_item(self, item):
        for _ in range(50):
            ref = self.g('gear_menu_candidate')
            chosen = self.state().equipment.bag[ref].item_id if ref < 48 else 0
            if chosen == item:
                return
            self.tap('DOWN')
        raise AssertionError(('item unavailable', item))

    def equip_weapon(self, item):
        self.step(90)
        self.open_gear()
        self.choose_item(item)
        self.tap('A')
        self.settle()
        self.tap('B')
        self.tap('START')
        assert self.state().equipment.bag[self.state().equipment.equipped[0]].item_id == item

    def owned_items(self):
        return [r.item_id for r in self.state().equipment.bag if r.item_id]

    def observe(self, label):
        stats = Stats.from_buffer_copy(self.e.bytes(self.sym['gear_stats'], C.sizeof(Stats)))
        s = self.state()
        row = {'label': label, 'hardware_frame': self.e.frame, 'recorded_offset': len(self.rows),
               'room': self.g('room'), 'part': self.g('gear_menu_slot'),
               'candidate_ref': self.g('gear_menu_candidate'), 'owned_items': self.owned_items(),
               'equipped_refs': list(s.equipment.equipped), 'coins': s.economy.gold,
               'effective_stats': {name: getattr(stats, name) for name, _ in Stats._fields_}}
        self.observations.append(row)
        return row

    def prepare(self):
        Capture.prepare(self)
        assert self.owned_items() == [1]
        self.preparation_start = self.observe('earned first-Grove source after cold Continue')
        self.entry(1)
        self.entry(16)
        self.act(320, 150, 1)
        assert self.quest(0) == 1
        self.act(432, 256, 1)
        self.act(456, 256, 1)
        assert self.owned_items() == [1, 9, 17]
        for weapon, cls in ((1, 1), (9, 2), (17, 3)):
            self.equip_weapon(weapon)
            self.goto(440, 298 if cls < 3 else 305)
            self.tap('UP')
            self.step(2, 'A')
            self.step(70)
            self.settle()
            assert self.state().quests.objectives[0] & (1 << (cls - 1))
        self.act(320, 150, 1)
        assert self.quest(0) == 3 and self.owned_items() == [1, 9, 17, 33]
        self.equip_weapon(1)
        self.entry(1)
        self.entry(0)
        self.goto(120, 120)
        self.step(140)
        assert self.g('chapter_flags') == 1 and self.g('room') == 0
        assert [c.form_id for c in self.state().roster.instances if c.flags & 1] == [1, 4, 7]
        self.before = self.roster_progress()
        self.before_flags = (self.g('chapter_flags'), self.g('room_flags'))
        self.preparation_end = self.observe('controller-earned practice gear, back at village')
        self.e.save(self.out / 'capture-start.sav')
        self.preparation_frames = self.e.frame
        self.preparation_inputs = len(self.inputs)

    def beat(self, name):
        self.chapters.append({'name': name, 'offset': len(self.rows), 'seconds': len(self.rows) / float(FPS)})

    def route(self):
        self.beat('village and previously earned equipment')
        self.step(30)
        self.shot('native-village')
        self.goto(y=101)
        self.goto(x=58)
        self.tap('A')
        assert self.g('game_state') == 11
        self.beat('village shop coins and prices')
        self.step(110)
        self.shot('native-shop-prices')
        self.tap('DOWN')
        self.step(40)
        self.tap('B')
        self.goto(x=120)
        self.goto(y=120)
        self.open_gear()
        self.beat('weapon comparison and A equip')
        self.step(45)
        self.shot('native-sword-equipped')
        self.choose_item(9)
        self.step(130)
        self.shot('native-lance-preview')
        self.observe('practice lance preview, before A')
        self.tap('A')
        self.settle()
        self.step(65)
        self.shot('native-lance-equipped')
        assert self.e.read(self.sym['gear_stats'] + 12, 1) == 2
        self.observe('practice lance equipped with A')
        self.choose_item(1)
        self.tap('A')
        self.settle()
        self.step(20)
        self.tap('RIGHT')
        assert self.g('gear_menu_slot') == 1
        self.choose_item(33)
        self.beat('body effective stats before and after')
        self.step(155)
        self.shot('native-equipment-preview')
        before = self.observe('Patchwork Mail preview, before A')['effective_stats']
        self.tap('A')
        self.settle()
        self.step(110)
        self.shot('native-mail-equipped')
        after = self.observe('Patchwork Mail equipped with A')['effective_stats']
        assert after['defense_q4'] == before['defense_q4'] + 2
        assert after['max_hp_q4'] == before['max_hp_q4'] + 8
        assert after['speed_q8'] == before['speed_q8'] - 4
        self.beat('left and right part tabs, B back')
        for slot in (2, 3, 4):
            self.tap('RIGHT')
            assert self.g('gear_menu_slot') == slot
            self.step(35)
        self.tap('LEFT')
        assert self.g('gear_menu_slot') == 3
        self.step(30)
        self.tap('B')
        assert self.g('journal_tab') == 13
        self.step(25)
        self.tap('START')
        self.beat('smooth field movement, sword, and held-L switching')
        self.step(20, 'RIGHT')
        self.step(12, 'DOWN')
        self.tap('A')
        self.step(38)
        self.step(18, 'L')
        self.step(10, 'L+UP')
        self.step(32)
        self.step(18, 'L')
        self.step(10, 'L+RIGHT')
        self.step(32)
        self.goto(x=120)
        self.goto(y=40)
        for _ in range(300):
            if self.g('room') == 1:
                break
            self.step(1, 'UP')
        assert self.g('room') == 1
        self.settle()
        self.step(35, 'UP')
        self.tap('A')
        self.step(40)
        self.shot('native-field-sword')
        after_roster = self.roster_progress()
        assert after_roster[:2] == self.before[:2] and after_roster[3:] == self.before[3:]
        assert self.g('chapter_flags') == self.before_flags[0]
        assert 20 <= len(self.rows) / float(FPS) <= 35

    def finish(self):
        Capture.finish(self)
        old = self.out / 'player-feedback-native-teaser.mp4'
        video = self.out / 'equipment-rewards-native-teaser.mp4'
        old.rename(video)
        path = self.out / 'teaser-report.json'
        report = json.loads(path.read_text())
        report['scope'] = __doc__
        report['candidate'] = self.capture_candidate
        report['source_candidate'] = self.producer['candidate']
        report['inherited_capture_helper_sha256'] = report['helper_sha256']
        report['helper_sha256'] = sha(__file__)
        report['files'][video.name] = report['files'].pop(old.name)
        report.update(source_snapshot_name=SNAPSHOT, source_snapshot=self.source_snapshot,
                      initialization='Cold Continue of authenticated same-build I4 first-Grove earned cartridge SRAM on exact frozen I4; source gameplay began from empty cartridge SRAM',
                      cross_build_sram_preparation=False, source_gameplay_build='I4', capture_gameplay_build='I4',
                      source_upgrade_difference='None; source and capture use the exact same frozen I4 ROM, including readable 4x7 gear numerals and bounded exact snapshot copy',
                      preparation='Unrecorded actual-controller visit to the early practice racks; sword/lance/bow practice hits earn Patchwork Mail; equip starter sword and walk home. No game-memory edits or machine-state imports.',
                      acquisition_claim='Gear was earned before the clip, not acquired within it.',
                      preparation_frames=self.preparation_frames, preparation_input_records=self.preparation_inputs,
                      preparation_start=self.preparation_start, preparation_end=self.preparation_end,
                      observations=self.observations, chapters=self.chapters,
                      native_resolution=[240, 160], video_resolution=[960, 640],
                      scaling='4x nearest-neighbor only; every native hardware frame retained at original cadence',
                      soundtrack_changed=False, human_musical_listening_verified=False,
                      spoiler_gate={'rooms': sorted(set(r['room'] for r in self.rows)), 'owned_forms': [1, 4, 7],
                                    'gear_items_shown': [1, 9, 33], 'late_treasures_or_endings_shown': False},
                      cadence={'update_misses': sum(r['delta'] != 1 for r in self.rows),
                               'flip_misses': sum(not r['flip'] for r in self.rows),
                               'overruns': sum(r['cycles'] >= 280896 for r in self.rows),
                               'music_faults': max(r['music_faults'] for r in self.rows),
                               'music_recoveries': max(r['music_recoveries'] for r in self.rows),
                               'music_stopped': max(r['music_stopped'] for r in self.rows)})
        report['capture_helpers'] = {str(p.relative_to(ROOT)): sha(p) for p in (
            Path(__file__), ROOT / 'tests/capture_player_feedback_teaser.py',
            ROOT / 'tests/player_feedback_campaign.py', ROOT / 'tests/player_feedback_native.py',
            ROOT / 'tests/region_journey.py', ROOT / 'tests/connected_roads_journey.py',
            ROOT / 'tests/test_equipment.py', ROOT / 'tests/test_save5.py', ROOT / 'tools/mgba_runner.py')}
        report['decoded_lossless_master_exact'] = True
        report['source_candidate_unchanged'] = sha(self.a.rom) == ROM_SHA and sha(self.a.symbols) == SYM_SHA
        report['files']['native-frames.mkv'] = {'bytes': (self.out / 'native-frames.mkv').stat().st_size, 'sha256': sha(self.out / 'native-frames.mkv')}
        path.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'video': str(video), 'preview': str(self.out / 'native-equipment-preview.png'),
                          'report': str(path), 'seconds': report['seconds'], 'cadence': report['cadence']}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('rom', 'symbols', 'producer', 'bridge', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--producer-sha', required=True)
    a = p.parse_args()
    r = EquipmentCapture(a)
    try:
        r.prepare()
        r.begin()
        r.route()
        r.finish()
    except Exception as exc:
        r.e.screenshot(r.out / 'failure.png')
        (r.out / 'failure.json').write_text(json.dumps({'error': str(exc), 'status': r.status(), 'inputs': r.inputs}, indent=2) + '\n')
        raise
    finally:
        r.close()


if __name__ == '__main__':
    main()
