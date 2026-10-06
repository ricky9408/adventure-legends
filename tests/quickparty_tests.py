#!/usr/bin/env python3
"""Native mGBA quick-picker and collection assignment integration checks.

Normal cases start a new game and use only GBA buttons. They never fabricate
ownership, write game RAM, or load another ROM's state. Immutable ROM/symbol
copies, inputs, screenshots, machine states and SRAM accompany the JSON report.
Power-cut cases reload exact SRAM captured during a controller-started save.
Optional --synthetic-interruptions writes ONLY game_state to test cancellation
under fault injection. Those cases and their writes are reported separately;
they are never presented as controller-reachable campaign evidence.
"""
from __future__ import annotations

import argparse
import binascii
from collections import Counter
import json
from pathlib import Path
import re
import struct

from evolution_tests import EvolutionRun, ROOT, PLAY, PAUSE, SAVE_PENDING, digest

EMPTY = 255
DIRECTIONS = ('UP', 'RIGHT', 'DOWN', 'LEFT')
CYCLES_PER_FRAME = 280896
COMPANION_OBJ_TILE = 512 + 6400 // 32
FAMILY = {1: 0, 2: 0, 4: 1, 5: 1, 7: 2, 8: 2, 10: 3, 11: 3}


class QuickPartyRun(EvolutionRun):
    def __init__(self, rom, symbols, output):
        super().__init__(rom, symbols, output, optional=False, exhaustive=False)
        self.synthetic_faults = []
        self.normal_pass_count = 0
        # Read the current source instrumentation layout instead of pinning a
        # cache row width. ROM behavior remains measured by native execution.
        source = (ROOT / 'src/game.c').read_text()
        width = re.search(r'#define\s+CACHE_FIELDS\s+(\d+)', source)
        initializer = re.search(r'void\s+render\s*\(void\)\s*\{\s*(?:game_geometry_sync\(\);\s*)?u32\s+key\[CACHE_FIELDS\]\s*=\s*\{([^}]+)\}', source)
        assert width and initializer, 'Missing renderer cache instrumentation declaration'
        fields = [item.strip() for item in initializer.group(1).split(',')]
        self.cache_field_count = int(width.group(1))
        assert len(fields) == self.cache_field_count, 'Renderer cache fields and initializer disagree'
        self.cache_camera_axes = tuple(next(i for i, field in enumerate(fields)
                                           if re.search(r'\b' + axis + r'\b', field))
                                       for axis in ('camera_x', 'camera_y'))
        assert len(set(self.cache_camera_axes)) == 2, 'Camera cache axes must be distinct'
        self.cache_source_contract = {'source_sha256': digest(ROOT / 'src/game.c'),
                                      'row_fields': self.cache_field_count,
                                      'camera_indices': list(self.cache_camera_axes),
                                      'basis': 'source-derived read-only observation layout; not runtime behavior evidence'}
        self.check(all(self.has(name) for name in (
            'quickparty_open', 'quickparty_candidate', 'quickparty_hold_updates',
            'quickparty_revision', 'quickparty_menu_slot', 'quickparty_menu_candidate',
        )), 'ROM exposes read-only quick-party QA symbols')

    def status(self):
        result = super().status()
        for name in ('quickparty_open', 'quickparty_candidate', 'quickparty_hold_updates',
                     'quickparty_revision', 'quickparty_menu_slot', 'quickparty_menu_candidate'):
            if self.has(name):
                result[name] = self.get(name)
        return result

    def party(self):
        return list(self.roster().party)

    def selection(self):
        return self.roster().selected_party, self.get('spirit')

    def contract(self, label):
        roster = self.roster()
        assigned = [slot for slot in roster.party if slot != EMPTY]
        self.check(bool(assigned), label + ': at least one quick slot stays assigned')
        self.check(len(assigned) == len(set(assigned)), label + ': party has no duplicate instance')
        self.check(all(slot < 160 and roster.instances[slot].flags & 1 for slot in assigned),
                   label + ': every assignment references an owned instance')
        selected = roster.selected_party
        self.check(selected < 4 and roster.party[selected] != EMPTY,
                   label + ': selected_party references a valid assigned slot')
        self.check(FAMILY[roster.instances[roster.party[selected]].form_id] == self.get('spirit'),
                   label + ': legacy spirit matches selected party instance')
        return roster

    def body_count(self):
        count = 0
        for a0, _a1, a2, _pad in struct.iter_unpack('<HHHH', self.e.bytes(0x07000000, 1024)):
            if a0 & 0x300 != 0x200 and a2 & 1023 == COMPANION_OBJ_TILE:
                count += 1
        return count

    def no_duplicate_body(self, label, visible=False):
        count = self.body_count()
        self.check(count <= 1, label + ': no duplicate active companion OBJ')
        if visible:
            self.check(count == int(bool(self.get('summoned'))),
                       label + ': rendered companion body matches summon state')

    def picker(self, direction, hold=3):
        before = self.selection()
        summoned = self.get('summoned')
        self.step(hold, 'L+' + direction)
        self.check(self.get('quickparty_open') == 1, direction + ': L opens quick picker')
        self.check(self.selection() == before, direction + ': preview does not commit while L is held')
        self.check(self.get('quickparty_candidate') == DIRECTIONS.index(direction),
                   direction + ': same-frame L+direction targets the correct quick slot')
        self.shot('picker-' + direction.lower())
        self.no_duplicate_body(direction + ' preview')
        self.step(3)
        self.check(self.get('quickparty_open') == 0, direction + ': release L closes picker')
        self.check(self.roster().selected_party == DIRECTIONS.index(direction),
                   direction + ': release L commits that assigned slot')
        self.check(self.get('summoned') == summoned, direction + ': switching preserves summon state')
        self.contract(direction + ' commit')
        self.no_duplicate_body(direction + ' commit', visible=True)

    def threshold_cases(self, baseline):
        for updates, cycles in ((1, True), (2, True), (12, True), (13, False), (40, False)):
            self.restore(baseline)
            before = self.selection()
            self.step(updates, 'L')
            observed = self.get('quickparty_hold_updates')
            self.check(observed == min(updates, 13),
                       f'neutral hold {updates}: duration counts updates and saturates beyond tap threshold')
            self.check(self.selection() == before, f'neutral hold {updates}: no eager L-press cycle')
            self.step(3)
            expected = (1, 1) if cycles else before
            self.check(self.selection() == expected,
                       f'neutral hold {updates}: ' + ('short tap cycles once' if cycles else 'long hold leaves selection unchanged'))
            self.check(not self.get('quickparty_open'), f'neutral hold {updates}: release closes overlay')
        self.restore(baseline)
        self.tap('L')
        self.tap('L')
        self.check(self.selection() == (0, 0), 'tap cycling skips empty slots and wraps to first assignment')

    def direction_cases(self, baseline):
        self.restore(baseline)
        self.picker('RIGHT')
        self.picker('UP')
        self.tap('B')
        self.picker('RIGHT')
        self.picker('UP')
        self.restore(baseline)
        for direction in ('DOWN', 'LEFT'):
            before = self.selection()
            self.step(4, 'L+' + direction)
            self.check(self.get('quickparty_candidate') not in range(4),
                       direction + ': empty slot has no valid candidate')
            self.step(3)
            self.check(self.selection() == before,
                       direction + ': releasing over an empty slot never falls back to tap cycling')
        # A direction preview survives a neutral hold, until superseded by a
        # later single direction. No edge-trigger assumption is made here.
        self.step(2, 'L+UP')
        self.step(2, 'L+RIGHT')
        self.step(18, 'L')
        self.check(self.get('quickparty_candidate') == 1,
                   'latest single cardinal remains the candidate through neutral hold')
        self.step(3)
        self.check(self.selection() == (1, 1), 'release chooses the latest valid direction, not the first')
        self.restore(baseline)
        for combination in ('UP+RIGHT', 'LEFT+RIGHT', 'UP+DOWN', 'UP+RIGHT+DOWN+LEFT'):
            self.step(2, 'L+RIGHT')
            self.step(3, 'L+' + combination)
            self.check(self.get('quickparty_candidate') not in range(4),
                       combination + ': ambiguous input clears the previous candidate')
            self.step(3)
            self.check(self.selection() == (0, 0), combination + ': ambiguous release does not commit or tap-cycle')
        self.step(2, 'L+RIGHT+UP')
        self.step(2, 'L+RIGHT')
        self.step(3)
        self.check(self.selection() == (1, 1), 'single cardinal after ambiguity becomes a valid new candidate')
        self.restore(baseline)
        self.step(2, 'L+RIGHT')
        self.step(2, 'L+DOWN')
        self.check(self.get('quickparty_candidate') not in range(4),
                   'empty single cardinal clears an earlier valid candidate')
        self.step(3)
        self.check(self.selection() == (0, 0), 'empty direction after valid preview cancels without tap fallback')
        self.restore(baseline)

    def cancellation_case(self, baseline):
        for summoned in (False, True):
            self.restore(baseline)
            if summoned:
                self.tap('B')
            before = self.selection()
            self.step(2, 'L+RIGHT')
            position = self.get('px'), self.get('py')
            self.step(2, 'L+B')
            self.step(24, 'L+RIGHT+A+R+SELECT+START')
            self.check(self.selection() == before, 'B cancel: held-L directions cannot revive a cancelled choice')
            self.check(bool(self.get('summoned')) == summoned, 'B cancel: B is consumed instead of toggling summon')
            self.check(self.get('game_state') == PLAY and (self.get('px'), self.get('py')) == position,
                       'B cancel: gameplay and other actions stay locked until L is released')
            self.step(3)
            self.check(self.selection() == before and not self.get('quickparty_open'),
                       'B cancel: release does not commit a stale candidate or cycle')
            self.picker('RIGHT')
            self.tap('B')
            self.check(bool(self.get('summoned')) != summoned,
                       'B cancel: a new post-release B press works normally')
        self.restore(baseline)
        self.step(3, 'L+B+RIGHT')
        self.step(3)
        self.check(self.selection() == (0, 0) and not self.get('summoned'),
                   'same-frame L+B+direction cancels without a summon or selection side effect')
        self.restore(baseline)

    def start_interruption_case(self, baseline):
        self.restore(baseline)
        before = self.selection()
        self.step(2, 'L+RIGHT')
        self.step(2, 'L+START')
        self.check(self.get('game_state') == PAUSE and not self.get('quickparty_open'),
                   'native START interrupts picker and opens journal')
        self.check(self.selection() == before, 'native START never commits the interrupted candidate')
        self.step(3, 'L')
        self.step(2, 'L+B')
        self.check(self.get('game_state') == PLAY, 'native B exits journal while L is still held')
        self.step(12, 'L+RIGHT')
        self.check(not self.get('quickparty_open') and self.selection() == before,
                   'return from journal keeps interrupted L held input latched until release')
        self.step(3)
        self.check(self.selection() == before, 'release after journal interruption cannot tap-cycle')
        self.picker('RIGHT')
        self.restore(baseline)

    def world_fingerprint(self):
        scalars = ('room', 'px', 'py', 'px_q8', 'py_q8', 'cx', 'cy', 'cx_q8', 'cy_q8',
                   'hp', 'face', 'ticks', 'walk_phase', 'ability_cd', 'heal_cd', 'roll_ticks',
                   'roll_cd', 'swing', 'sword_cd', 'combo_timer', 'attack_buffer', 'hitstop',
                   'stone_guard', 'guard_invuln', 'invuln', 'power_effect', 'boss_hp',
                   'boss_x', 'boss_y', 'boss_time', 'boss_armor', 'boss_state_ticks',
                   'boss_state', 'boss_phase', 'boss_pattern', 'hazard_mode',
                   'boss_aimx', 'boss_aimy', 'boss_dx', 'boss_dy',
                   'advanced_kind', 'advanced_time_left', 'advanced_shield_left',
                   'camera_x', 'camera_y', 'room_flags', 'chapter_flags')
        result = {name: self.get(name) for name in scalars if self.has(name)}
        for name, size in (('enemies', 120), ('shots', 288), ('impacts', 72),
                           ('enemy_clocks', 24), ('enemy_windups', 24),
                           ('rooted_enemies', 24), ('shot_effects', 12)):
            result[name] = self.e.bytes(self.sym[name], size).hex()
        return result

    def freeze_case(self, baseline, grove=False):
        self.restore(baseline)
        scene = 'grove' if grove else 'village'
        if grove:
            self.nextroom(1)
            self.check(any(self.e.read(self.sym['enemies'] + i * 20 + 8) for i in range(6)),
                       'grove freeze setup includes live controller-reached enemies')
        self.tap('B')
        self.step(1, 'R')
        self.step(1)
        self.check(self.get('ability_cd') > 0 and any(
            self.e.read(self.sym['shots'] + i * 24 + 16) for i in range(12)),
            'freeze setup: real controller use creates a live projectile and nonzero cooldown')
        before = self.world_fingerprint()
        self.step(2, 'L+RIGHT')
        self.check(self.world_fingerprint() == before,
                   'opening selector freezes active world state on its first update')
        cycles, deltas, flips = [], [], []
        old_frame = self.get('frame')
        old_page = self.e.read(0x04000000, 2) & 16
        for i in range(80):
            self.step(1, 'L+RIGHT+A+R+SELECT')
            now = self.get('frame')
            page = self.e.read(0x04000000, 2) & 16
            deltas.append((now - old_frame) & 0xffffffff)
            flips.append(page != old_page)
            cycles.append(self.get('render_cycles'))
            old_frame, old_page = now, page
        after = self.world_fingerprint()
        self.observations['selector_freeze_' + scene] = {'before': before, 'after': after, 'frames': 80}
        self.check(after == before,
                   'selector freezes movement, projectiles, enemies, combat timers and effects under mixed inputs')
        self.check(self.get('game_state') == PLAY and self.get('summoned') == 1,
                   'selector consumes attack, power and dodge inputs without dismissing companion')
        self.check(all(d == 1 for d in deltas) and all(flips),
                   'selector still updates input and presents every native hardware frame')
        self.check(max(cycles) < CYCLES_PER_FRAME, 'selector renderer remains within the native frame budget')
        self.scenes.append({'scene': scene + '-live-projectile-quick-picker', 'hardware_frames': len(cycles),
                            'simulation_updates': sum(deltas), 'display_flips': sum(flips),
                            'update_histogram': dict(Counter(deltas)), 'maximum_cycles': max(cycles),
                            'frame_budget_cycles': CYCLES_PER_FRAME})
        self.no_duplicate_body('frozen selector')
        self.shot('picker-live-projectile-frozen-' + scene)
        self.step(1, 'RIGHT+A+R')
        self.check(self.selection() == (1, 1), 'frozen-world selector commits chosen companion on release')
        self.check(self.world_fingerprint() == before,
                   'release update consumes still-held direction, attack and power without advancing the world')
        self.step(2)
        self.check(self.get('ability_cd') < before['ability_cd'], 'world cooldown resumes after selector release')
        self.no_duplicate_body('resumed world', visible=True)
        self.restore(baseline)

    def transition_cadence_case(self, baseline, name, settle_updates=4, opening_evidence=None):
        self.restore(baseline)
        self.step(settle_updates)
        old_frame = self.get('frame')
        old_page = self.e.read(0x04000000, 2) & 16
        samples = []
        sequence = [(1, 'L', 'cold-open'), (1, 'L+UP', 'choose-up'),
                    (1, 'L+RIGHT', 'choose-right'), (1, 'L+DOWN', 'choose-down'),
                    (1, 'L+LEFT', 'choose-left'), (1, 'L+RIGHT', 'reselect-right'),
                    (1, 0, 'release-commit'), (2, 0, 'closed-world'),
                    (1, 'L+UP', 'cold-open-same-frame-direction'),
                    (1, 'L+B', 'cancel-close'), (1, 'L', 'cancel-latch'),
                    (2, 0, 'cancel-release'), (1, 'L+LEFT', 'open-again'),
                    (1, 0, 'close-again'), (2, 0, 'closed-world-final')]
        for count, keys, phase in sequence:
            for _ in range(count):
                self.raw_step(1, keys)
                now = self.get('frame')
                page = self.e.read(0x04000000, 2) & 16
                samples.append({'phase': phase, 'keys': keys,
                                'update_delta': (now - old_frame) & 0xffffffff,
                                'display_flip': page != old_page,
                                'render_cycles': self.get('render_cycles')})
                old_frame, old_page = now, page
                if opening_evidence is not None and len(samples) == 1:
                    target = opening_evidence['next_update_render_page']
                    camera = opening_evidence['camera']
                    updated = [self.e.read(self.sym['cache_fields'] + (target * self.cache_field_count + axis) * 4)
                               for axis in self.cache_camera_axes]
                    self.check(self.get('page') == target and updated == camera,
                               name + ': first L update refreshes the stale next-render-page camera key')
                    self.check([self.get('camera_x'), self.get('camera_y')] == camera,
                               name + ': first L update freezes camera immediately after movement')
                    opening_evidence['first_open_render_cycles'] = self.get('render_cycles')
                    self.fallback_pixel_case(name, target, camera, opening_evidence)
        self.check(all(s['update_delta'] == 1 and s['display_flip'] for s in samples),
                   name + ': cold open, every directional redraw and close present at native cadence')
        self.check(max(s['render_cycles'] for s in samples) < CYCLES_PER_FRAME,
                   name + ': cold overlay and changing portrait/name fit hardware frame budget')
        self.scenes.append({'scene': name, 'hardware_frames': len(samples),
                            'simulation_updates': sum(s['update_delta'] for s in samples),
                            'display_flips': sum(s['display_flip'] for s in samples),
                            'maximum_cycles': max(s['render_cycles'] for s in samples),
                            'frame_budget_cycles': CYCLES_PER_FRAME, 'samples': samples,
                            'opening_evidence': opening_evidence})
        self.restore(baseline)

    def fallback_pixel_case(self, name, page, camera, evidence):
        """Top source rows are outside the picker; HUD graphics are OBJ only."""
        cx, cy = camera
        rows = 20
        actual = self.e.bytes(0x0600a000 if page else 0x06000000, rows * 240)
        expected = b''.join(self.e.bytes(self.sym['overworld_bitmap'] + (cy + y) * 480 + cx, 240)
                            for y in range(rows))
        # Only the authored opened bridge can alter these source rows at the
        # controller-reached south-grove location used by this check.
        def decorated(index):
            x, y = index % 240, index // 240
            return bool(self.get('bridge_open') and
                        226 - cx <= x < 257 - cx and 152 - cy <= y < 181 - cy)
        compared = [i for i in range(rows * 240) if not decorated(i)]
        mismatch = [i for i in compared if actual[i] != expected[i]]
        evidence.update({'outside_panel_compared_pixels': len(compared),
                         'outside_panel_mismatched_pixels': len(mismatch),
                         'mismatch_examples': [[i % 240, i // 240, actual[i], expected[i]]
                                               for i in mismatch[:10]]})
        self.check(len(compared) >= 4000 and not mismatch,
                   name + ': stale-page fallback refreshes source pixels outside the overlay')

    def movement_alignment_cadence(self, baseline, name):
        """Do not warm the back page between movement and the opening L."""
        self.restore(baseline)
        self.check(self.get('room') == 1 and self.get('game_state') == PLAY,
                   name + ': alignment route starts in controller-reached grove')
        seen = set()
        observations = []
        for movement_update in range(48):
            before_position = self.get('px')
            self.raw_step(1, 'RIGHT')
            camera = [self.get('camera_x'), self.get('camera_y')]
            phase = camera[0] % 4
            # At mGBA's frame boundary the pending page is already rendered,
            # but not presented. After that VBlank, page^1 becomes the back
            # page rendered by the very next input update. Inspect that page,
            # not the already-fresh pending page.
            pending_page = self.get('page')
            target = pending_page ^ 1
            old_camera = [self.e.read(self.sym['cache_fields'] + (target * self.cache_field_count + axis) * 4)
                          for axis in self.cache_camera_axes]
            if phase in seen or camera == old_camera:
                continue
            self.check(self.get('game_state') == PLAY and self.get('px') != before_position and
                       self.e.read(self.sym['cache_valid'] + target * 4),
                       name + f' alignment {phase}: movement leaves a valid but stale next-render page')
            evidence = {'camera': camera, 'camera_word_alignment': phase,
                        'next_update_render_page': target, 'cached_camera_before_open': old_camera,
                        'pending_page': pending_page,
                        'displayed_page': int(bool(self.e.read(0x04000000, 2) & 16)),
                        'movement_updates': movement_update + 1,
                        'provenance': 'normal RIGHT movement immediately followed by L; zero settling updates'}
            snapshot = self.snapshot(name + f'-alignment-{phase}-after-movement')
            self.transition_cadence_case(snapshot, name + f'-alignment-{phase}',
                                         settle_updates=0, opening_evidence=evidence)
            observations.append(evidence)
            seen.add(phase)
            if seen == {0, 1, 2, 3}:
                break
        self.check(seen == {0, 1, 2, 3}, name + ': immediate movement-to-L fallback covers all four camera x alignments')
        self.observations[name + '_movement_alignment'] = observations
        self.restore(baseline)

    def collection(self):
        if self.get('game_state') == PLAY:
            self.tap('START')
        self.check(self.get('game_state') == PAUSE, 'Start opens journal for party assignment')
        for _ in range(7):
            if self.get('journal_tab') == 2:
                break
            self.tap('A')
        self.check(self.get('journal_tab') == 2, 'collection assignment is journal tab2')

    def menu_target(self, slot):
        for _ in range(4):
            if self.get('quickparty_menu_slot') == slot:
                break
            self.tap('RIGHT')
        self.check(self.get('quickparty_menu_slot') == slot, f'collection targets quick slot {slot}')

    def menu_candidate(self, instance):
        allowed = {i for i, c in enumerate(self.roster().instances) if c.flags & 1} | {EMPTY}
        for _ in range(len(allowed) + 1):
            candidate = self.get('quickparty_menu_candidate')
            self.check(candidate in allowed, 'collection candidate is owned or empty; never a locked placeholder')
            if candidate == instance:
                return
            self.tap('DOWN')
        self.check(False, f'collection can select owned instance {instance}')

    def assign(self, slot, instance, expected):
        self.menu_target(slot)
        self.menu_candidate(instance)
        before = bytes(self.roster().instances)
        self.tap('R')
        self.check(self.get('game_state') == PAUSE and self.get('journal_tab') == 2,
                   'assignment save returns to collection panel')
        self.check(self.party() == expected, 'R assigns or swaps exactly the chosen instance and target')
        self.check(bytes(self.roster().instances) == before,
                   'party assignment preserves every owned instance byte and story lock')
        self.contract('assignment')

    def assignment_cases(self, baseline):
        self.restore(baseline)
        self.collection()
        initial = self.snapshot('collection-original')
        roster_bytes = bytes(self.roster().instances)
        self.shot('collection-two-owned')
        self.menu_target(0)
        self.menu_candidate(0)
        no_op_roster = bytes(self.roster())
        no_op_sram = self.e.bytes(0x0e000000, 32768)
        self.auto_save = False
        self.tap('R')
        self.check(self.get('game_state') == PAUSE and bytes(self.roster()) == no_op_roster and
                   self.e.bytes(0x0e000000, 32768) == no_op_sram,
                   'assigning the same instance to the same slot is a complete no-op without an SRAM write')
        self.auto_save = True
        seen = set()
        start = self.get('quickparty_menu_candidate')
        for _ in range(3):
            seen.add(self.get('quickparty_menu_candidate'))
            self.tap('DOWN')
        self.check(seen == {0, 1, EMPTY} and self.get('quickparty_menu_candidate') == start,
                   'candidate cycling wraps over exactly the two owned instances and empty')
        self.tap('UP')
        backward = self.get('quickparty_menu_candidate')
        self.tap('DOWN')
        self.check(backward != start and self.get('quickparty_menu_candidate') == start,
                   'UP reverses DOWN candidate navigation')
        self.menu_target(0)
        self.tap('LEFT')
        self.check(self.get('quickparty_menu_slot') == 3, 'LEFT wraps target from UP slot to LEFT slot')
        self.tap('RIGHT')
        self.check(self.get('quickparty_menu_slot') == 0, 'RIGHT wraps target from LEFT slot to UP slot')
        self.assign(0, 1, [1, 0, EMPTY, EMPTY])
        self.assign(2, 0, [1, EMPTY, 0, EMPTY])
        self.assign(3, 1, [EMPTY, EMPTY, 0, 1])
        self.shot('collection-remapped-down-left')
        self.check(bytes(self.roster().instances) == roster_bytes,
                   'swapping and moving story companions cannot release them from the collection')
        self.tap('B')
        self.picker('DOWN')
        self.picker('LEFT')
        self.tap('L')
        self.check(self.selection() == (2, 0), 'tap cycle honors remapped party order and skips leading empties')
        self.collection()
        before = self.selection()
        self.tap('L')
        self.check(self.get('game_state') == PAUSE and not self.get('quickparty_open') and
                   self.selection() == (3, 1) and self.selection() != before,
                   'collection L cycles assigned companion without opening world picker')
        self.contract('journal selection')
        self.tap('A')
        self.check(self.get('game_state') == PAUSE and self.get('journal_tab') == 3,
                   'collection A still advances to the growth journal page')
        self.collection()
        self.menu_target(2)
        self.tap('SELECT')
        self.check(self.get('game_state') == PAUSE and self.party() == [EMPTY, EMPTY, EMPTY, 1],
                   'Select clears the targeted quick slot without closing journal')
        self.contract('one remaining assignment')
        before = bytes(self.roster())
        self.menu_target(3)
        self.tap('SELECT')
        self.check(bytes(self.roster()) == before, 'Select cannot clear the final assigned companion')
        self.menu_candidate(EMPTY)
        self.tap('R')
        self.check(bytes(self.roster()) == before, 'R with empty candidate also cannot clear the final assignment')
        self.check(bytes(self.roster().instances) == roster_bytes,
                   'clear operations leave all owned story instances intact and reassignable')
        self.tap('B')
        self.tap('L')
        self.check(self.selection() == (3, 1), 'tap with a single assigned slot remains on that companion')
        self.collection()
        self.assign(0, 0, [0, EMPTY, EMPTY, 1])
        self.assign(3, EMPTY, [0, EMPTY, EMPTY, EMPTY])
        self.assign(2, 1, [0, EMPTY, 1, EMPTY])
        self.persist_case()
        self.restore(initial)

    def valid_banks(self, data):
        valid = []
        for address in (0x200, 0x1a00):
            bank = bytearray(data[address:address + 6144])
            if bank[:4] != b'EB\x05\x20' or bank[20] != 0xa5:
                continue
            expected = int.from_bytes(bank[16:20], 'little')
            bank[16:20] = bytes(4)
            bank[20] = 0
            if binascii.crc32(bank) != expected:
                continue
            valid.append({'offset': address, 'sequence': int.from_bytes(bank[8:12], 'little'),
                          'revision': int.from_bytes(bank[12:14], 'little'),
                          'party': list(bank[4000:4004]), 'selected_party': bank[4004],
                          'spirit': bank[46]})
        return valid

    def persist_case(self):
        before = bytes(self.roster())
        selection = self.selection()
        revision = int(re.search(r'SAVE5_CONTENT_REVISION\s*=\s*(\d+)', (ROOT/'src/save5.h').read_text()).group(1))
        saved = self.save('assigned-party-revision'+str(revision))
        banks = self.valid_banks(saved.read_bytes())
        self.check(bool(banks) and all(b['revision'] == revision for b in banks),
                   f'assignment uses CRC-valid save5 content revision{revision} banks')
        self.observations['assignment_banks'] = banks
        self.reopen(saved)
        self.dialogs()
        self.check(bytes(self.roster()) == before and self.selection() == selection,
                   'independent mGBA reboot preserves assignments, selected slot and every roster byte')
        self.check(self.get('loaded_save_version') == 5 and not self.get('quickparty_open'),
                   'assignment reload opens save5 with no stale quick-picker overlay')
        self.contract('reloaded assignment')
        self.snapshot('assignment-reloaded')
        self.collection()

    def interruption_case(self):
        """Every writer boundary uses authentic captured SRAM, no RAM mutation."""
        self.collection()
        self.menu_target(0)
        self.menu_candidate(1)
        original = self.snapshot('assignment-before-power-cut')
        before = bytes(self.roster())
        self.auto_save = False
        self.raw_step(2, 'R')
        self.check(self.get('game_state') == SAVE_PENDING, 'R assignment enters transactional SAVE_PENDING')
        after = bytes(self.roster())
        self.check(after != before, 'power-cut exercise starts a real changed party assignment')
        samples = []
        for index in range(180):
            samples.append(self.save(f'assignment-power-cut-{index:02d}'))
            if self.get('game_state') != SAVE_PENDING:
                break
            self.raw_step(1, 'L+RIGHT+A+B+SELECT+START+R')
            self.check(not self.get('quickparty_open') and bytes(self.roster()) == after,
                       f'assignment save tick {index}: mixed input cannot open picker or mutate roster')
        else:
            self.check(False, 'assignment transaction finishes within 180 frames')
        self.raw_step(2)
        self.auto_save = True
        recovered = []
        for index, sample in enumerate(samples):
            self.reopen(sample)
            self.dialogs()
            actual = bytes(self.roster())
            self.check(actual in (before, after),
                       f'assignment power cut {index}: reboot gets only complete old or new roster')
            self.contract(f'assignment power cut {index}')
            recovered.append({'frame_offset': index, 'sha256': digest(sample), 'new': actual == after})
        self.check(not recovered[0]['new'] and recovered[-1]['new'],
                   'power-cut coverage includes both uncommitted old and committed new assignments')
        self.observations['assignment_power_cuts'] = recovered
        self.restore(original)

    def evolve_reordered_case(self, report, report_path):
        source = report['snapshots']['evolution-0-ready']
        state = Path(source['path'])
        sram = Path(source['sram_path'])
        if not state.is_absolute():
            state = report_path.parent / state
        if not sram.is_absolute():
            sram = report_path.parent / sram
        self.check(digest(state) == source['state_sha256'] and digest(sram) == source['sram_sha256'],
                   'pending evolution input matches exact controller-earned state and SRAM hashes')
        copied = self.out / 'controller-pending-evolution-input.state'
        copied.write_bytes(state.read_bytes())
        copied.with_suffix('.state.sav').write_bytes(sram.read_bytes())
        self.restore(copied)
        roster = self.contract('pending evolution input')
        actual = roster.party[roster.selected_party]
        self.check(roster.instances[actual].form_id == 1 and self.get('spirit') == 0,
                   'controller-earned pending evolution belongs to Homura')
        target = (roster.selected_party + 2) % 4
        expected = list(roster.party)
        prior_slot = roster.selected_party
        expected[prior_slot], expected[target] = expected[target], expected[prior_slot]
        self.collection()
        self.assign(target, actual, expected)
        roster = self.roster()
        self.check(roster.selected_party == target and self.get('spirit') == 0,
                   'pending evolution selection follows Homura to a different quick slot')
        before = [bytes(c) for c in roster.instances]
        self.tap('A')
        self.check(self.get('journal_tab') == 3, 'reordered pending evolution opens growth page')
        self.tap('SELECT')
        self.check(self.get('game_state') == 7, 'reordered eligible instance enters evolution confirmation')
        self.tap('B')
        self.check(bytes(self.roster()) == bytes(roster),
                   'declining reordered evolution preserves selection, party and all creature data')
        self.tap('SELECT')
        self.wait_evolution()
        self.tap('A')
        self.wait_evolution(8)
        self.check(self.get('game_state') == 8, 'explicit confirmation evolves the reordered selected instance')
        self.step(100)
        self.check(self.get('game_state') == PAUSE, 'reordered evolution animation and save return to journal')
        after = self.roster()
        changed = [i for i, c in enumerate(after.instances) if bytes(c) != before[i]]
        self.check(changed == [actual] and after.instances[actual].form_id == 2,
                   'evolution transforms only Homura instance, never the quick-slot-index creature')
        old, new = roster.instances[actual], after.instances[actual]
        self.check((new.instance_id, new.xp, new.bond, new.trial_flags, new.cosmetic_seed) ==
                   (old.instance_id, old.xp, old.bond, old.trial_flags, old.cosmetic_seed),
                   'reordered evolution preserves the selected creature identity and earned progress')
        self.check(list(after.party) == expected and after.selected_party == target,
                   'reordered evolution preserves party permutation and selected quick slot')
        self.contract('evolution after reorder')
        self.shot('evolution-after-reorder')
        self.reload_roster('evolution-after-reorder')
        self.snapshot('evolution-after-reorder')
        self.observations['pending_evolution_source'] = {
            'state_sha256': digest(copied), 'sram_sha256': digest(copied.with_suffix('.state.sav')),
            'original_roster_instance': actual, 'moved_to_party_slot': target,
            'provenance': 'matching controller-earned pending evolution; reordered and evolved with buttons'}

    def run_evolved(self, report_path):
        """Supplemental exact-ROM journey input; no manufactured advanced forms."""
        report_path = Path(report_path).resolve()
        report = json.loads(report_path.read_text())
        self.check(report.get('controller_only') is True and report.get('game_ram_writes') == 0 and
                   not report.get('failures'), 'evolved input is a passing controller-only journey')
        self.check(report['candidate']['rom_sha256'] == self.candidate['rom_sha256'] and
                   report['candidate']['symbols_sha256'] == self.candidate['symbols_sha256'],
                   'evolved journey uses the exact tested ROM and symbol hashes')
        source = report['snapshots']['all-evolved-village']
        state = Path(source['path'])
        sram = Path(source['sram_path'])
        if not state.is_absolute():
            state = report_path.parent / state
        if not sram.is_absolute():
            sram = report_path.parent / sram
        self.check(digest(state) == source['state_sha256'] and digest(sram) == source['sram_sha256'],
                   'evolved state and paired SRAM match controller-journey provenance hashes')
        copied = self.out / 'controller-evolved-input.state'
        copied.write_bytes(state.read_bytes())
        copied.with_suffix('.state.sav').write_bytes(sram.read_bytes())
        self.observations['evolved_journey_source'] = {
            'report': str(report_path), 'report_sha256': digest(report_path),
            'state_sha256': digest(copied), 'sram_sha256': digest(copied.with_suffix('.state.sav')),
            'provenance': 'exact-ROM controller-earned four evolved instances and eight obtained forms'}
        self.evolve_reordered_case(report, report_path)
        self.restore(copied)
        if self.get('game_state') == PAUSE:
            self.tap('B')
        roster = self.contract('evolved controller input')
        owned = [i for i, c in enumerate(roster.instances) if c.flags & 1]
        self.check(len(owned) == 4 and {roster.instances[i].form_id for i in owned} == {2, 5, 8, 11},
                   'evolved setup owns exactly the four personally evolved companions')
        self.check({i + 1 for i in range(128) if roster.obtained[i // 8] & (1 << (i % 8))} ==
                   {1, 2, 4, 5, 7, 8, 10, 11}, 'controller journey obtained all eight authored forms')
        original_instances = bytes(roster.instances)
        selected_identity = roster.instances[roster.party[roster.selected_party]].instance_id
        self.collection()
        for target, instance in enumerate(reversed(owned)):
            expected = self.party()
            source_slot = expected.index(instance)
            expected[source_slot], expected[target] = expected[target], expected[source_slot]
            self.assign(target, instance, expected)
        roster = self.roster()
        self.check(self.party() == list(reversed(owned)) and bytes(roster.instances) == original_instances,
                   'full evolved party reversal preserves every identity, form and earned progression byte')
        self.check(roster.instances[roster.party[roster.selected_party]].instance_id == selected_identity,
                   'full reversal follows selected instance identity across slot permutations')
        self.persist_case()
        self.tap('B')
        for direction in DIRECTIONS:
            self.picker(direction)
        # Growth R must edit the currently selected INSTANCE after permutation,
        # not the roster entry whose index happens to equal selected_party.
        for target in range(4):
            self.picker(DIRECTIONS[target])
            roster = self.roster()
            actual_slot = roster.party[target]
            before = [bytes(c) for c in roster.instances]
            family = self.get('spirit')
            self.collection()
            self.tap('A')
            self.tap('R')
            after = self.roster()
            changed = [i for i, c in enumerate(after.instances) if bytes(c) != before[i]]
            self.check(changed == [actual_slot],
                       f'evolved slot {target}: growth R modifies only the selected reordered instance')
            self.check(after.instances[actual_slot].equipped[after.instances[actual_slot].selected_command] == family + 1,
                       f'evolved slot {target}: original command belongs to selected family')
            self.tap('R')
            self.check(bytes(self.roster().instances) == bytes(roster.instances),
                       f'evolved slot {target}: advanced command restoration preserves all instance bytes')
            self.tap('B')
        self.goto(144, 126)
        if not self.get('summoned'):
            self.tap('B')
        self.ready()
        baseline = self.snapshot('evolved-reversed-party')
        self.transition_cadence_case(baseline, 'evolved-four-portrait-cold-overlay')
        for target in range(4):
            self.restore(baseline)
            self.picker(DIRECTIONS[target])
            family = self.get('spirit')
            self.step(1, 'R')
            self.step(1)
            self.check(self.get('advanced_kind') == family + 5 and self.get('advanced_time_left') > 0 and
                       self.get('ability_cd') > 0, f'evolved family {family}: real R input starts its advanced effect')
            before = self.world_fingerprint()
            other = (target + 1) % 4
            self.step(32, 'L+' + DIRECTIONS[other])
            self.check(self.world_fingerprint() == before,
                       f'evolved family {family}: picker freezes active advanced effect and shared cooldown')
            self.shot(f'evolved-family-{family}-effect-frozen')
            self.step(1)
            self.check(self.world_fingerprint() == before and self.roster().selected_party == other,
                       f'evolved family {family}: release switches slot without resetting or ticking active effect')
            self.step(1, 'R')
            self.check(self.get('ability_cd') == before['ability_cd'] - 1 and
                       self.get('advanced_time_left') == before['advanced_time_left'] - 1 and
                       self.get('advanced_kind') == family + 5,
                       f'evolved family {family}: new companion cannot bypass shared cooldown or replace cast identity')
            self.no_duplicate_body(f'evolved family {family} switched effect', visible=True)
        self.restore(baseline)
        self.goto(x=120)
        self.nextroom(1)
        grove = self.snapshot('evolved-reversed-grove')
        self.transition_cadence_case(grove, 'evolved-four-portrait-grove-cold-overlay')
        self.movement_alignment_cadence(grove, 'evolved-grove-immediate-open')
        self.step(2, 'L+UP')
        self.shot('evolved-grove-picker')
        boss_source = report['snapshots']['boss-13-phase-1-state-6']
        boss_state = Path(boss_source['path'])
        boss_sram = Path(boss_source['sram_path'])
        if not boss_state.is_absolute():
            boss_state = report_path.parent / boss_state
        if not boss_sram.is_absolute():
            boss_sram = report_path.parent / boss_sram
        self.check(digest(boss_state) == boss_source['state_sha256'] and
                   digest(boss_sram) == boss_source['sram_sha256'],
                   'live boss input matches exact controller-earned state and SRAM hashes')
        boss = self.out / 'controller-live-boss-input.state'
        boss.write_bytes(boss_state.read_bytes())
        boss.with_suffix('.state.sav').write_bytes(boss_sram.read_bytes())
        self.restore(boss)
        self.check(self.get('room') == 13 and self.get('boss_hp') > 0 and
                   len([c for c in self.roster().instances if c.flags & 1]) == 4,
                   'boss cadence uses a live encounter and four normally owned companions')
        self.transition_cadence_case(boss, 'live-core-boss-four-portrait-cold-overlay')
        self.step(4)
        before = self.world_fingerprint()
        self.step(2, 'L+RIGHT')
        self.step(36, 'L+UP')
        self.check(self.world_fingerprint() == before,
                   'live boss selector freezes phase, hazards, projectiles and combat timers')
        self.shot('live-boss-picker-frozen')
        self.step(1)
        self.check(self.world_fingerprint() == before,
                   'live boss release commits without advancing encounter on closing update')
        self.observations['live_boss_source'] = {
            'state_sha256': digest(boss), 'sram_sha256': digest(boss.with_suffix('.state.sav')),
            'provenance': 'exact-ROM controller-earned live boss phase and party'}
        self.restore(baseline)
        self.normal_pass_count = len(self.passes)
        self.report()

    def synthetic_interruption_cases(self, baseline):
        """Fault-only test: do not claim these transitions are button-reachable."""
        for state, name in ((2, 'DIALOG'), (3, 'PAUSE'), (4, 'DEAD')):
            self.restore(baseline)
            before = self.selection()
            self.step(2, 'L+RIGHT')
            event = {'kind': 'synthetic-game-state-interruption', 'target': name,
                     'game_ram_writes': 1, 'address': hex(self.sym['game_state']),
                     'value': state, 'emulator_frame': self.e.frame,
                     'provenance': 'deliberately injected state, not reachable-transition evidence'}
            self.synthetic_faults.append(event)
            self.e.write(self.sym['game_state'], state)
            self.raw_step(2, 'L')
            self.check(not self.get('quickparty_open') and self.selection() == before,
                       f'SYNTHETIC {name}: non-play interruption closes picker without committing')
            self.raw_step(2)
            self.check(self.selection() == before,
                       f'SYNTHETIC {name}: release cannot apply the interrupted candidate')
        self.restore(baseline)

    def run(self, synthetic=False):
        self.step(90)
        self.check(self.get('game_state') == 0, 'fresh immutable candidate boots to title')
        self.tap('SELECT', 4, 4)
        self.dialogs()
        self.step(140)
        self.check(self.get('game_state') == PLAY and self.get('room') == 0,
                   'controller new-game setup reaches safe village')
        self.check(self.party() == [0, 1, EMPTY, EMPTY] and self.selection() == (0, 0),
                   'new game starts with two owned story companions and two empty quick slots')
        self.contract('new game')
        baseline = self.snapshot('quickparty-controller-baseline')
        self.transition_cadence_case(baseline, 'opening-two-companion-cold-overlay')
        self.threshold_cases(baseline)
        self.direction_cases(baseline)
        self.cancellation_case(baseline)
        self.start_interruption_case(baseline)
        self.freeze_case(baseline)
        self.freeze_case(baseline, grove=True)
        self.restore(baseline)
        self.nextroom(1)
        self.movement_alignment_cadence(self.snapshot('opening-grove-movement'),
                                       'opening-grove-immediate-open')
        self.restore(baseline)
        self.assignment_cases(baseline)
        self.interruption_case()
        self.restore(baseline)
        self.normal_pass_count = len(self.passes)
        if synthetic:
            self.synthetic_interruption_cases(baseline)
        self.report()

    def report(self):
        result = {'suite': 'quick-party-native-controller-integration',
                  'candidate': getattr(self, 'candidate', {}),
                  'cache_observation_source_contract': getattr(self, 'cache_source_contract', {}),
                  'passes': self.passes,
                  'failures': self.failures, 'controller_only': not bool(getattr(self, 'synthetic_faults', [])),
                  'normal_game_ram_writes': 0,
                  'normal_pass_count': getattr(self, 'normal_pass_count', 0),
                  'synthetic_faults': getattr(self, 'synthetic_faults', []),
                  'synthetic_game_ram_writes': len(getattr(self, 'synthetic_faults', [])),
                  'fixture_policy': 'new-game controller setup; power cuts use captured SRAM; optional synthetic cases separately labeled',
                  'save_pending_checks': getattr(self, 'save_checks', []),
                  'performance': self.scenes, 'snapshots': self.snapshots,
                  'observations': self.observations, 'final': self.status(),
                  'emulator_frame': self.e.frame}
        (self.out / 'quickparty-report.json').write_text(json.dumps(result, indent=2) + '\n')
        (self.out / 'controller-inputs.json').write_text(json.dumps(self.inputs, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--symbols', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/quickparty-qa')
    parser.add_argument('--journey', type=Path,
                        help='run evolved supplemental checks using a matching controller evolution-report.json')
    parser.add_argument('--synthetic-interruptions', action='store_true',
                        help='also run separately labeled non-play game_state fault injection')
    args = parser.parse_args()
    run = QuickPartyRun(args.rom, args.symbols, args.output)
    try:
        if args.journey:
            run.run_evolved(args.journey)
        else:
            run.run(args.synthetic_interruptions)
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
