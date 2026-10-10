#!/usr/bin/env python3
"""Exact-ROM mGBA Gear comparison controller and native-frame evidence.

The bundled historical SRAM is a developer fixture, never a user's save. Its
late collection is not claimed as controller acquisition. The harness prepares
an explicitly labelled passive-bonus SRAM through the native save writer, then
uses real controller input for the entire 48-item plus five-removal sweep.
Individually logged RAM fixtures cover wounded HP, current cooldowns, busy
committed actions/projectiles and boundaries. No ROM patches or state imports.
"""
from __future__ import annotations
import argparse
import ctypes as C
import gzip
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tools')]
from player_feedback_native import Run, sha, LIMIT
from test_save5 import Save, Economy
from test_equipment import State, Stats, Comparison, Definition, Weapon, IDS, build

SLOTS = ('weapon', 'body', 'boots', 'belt', 'ring')
TRANSIENTS = ('hero_hp_q4', 'hp', 'ability_cd', 'ability_max', 'heal_cd', 'roll_ticks',
              'roll_cd', 'roll_dx', 'roll_dy', 'weapon_action', 'player_arrows',
              'shots', 'shot_phases', 'ordinary_hostile_shots', 'swing', 'sword_cd',
              'combo_step', 'combo_timer', 'attack_buffer', 'swing_damage', 'slash_id',
              'invuln', 'guard_invuln', 'stone_guard', 'hitstop', 'power_effect',
              'enemy_hp_q4', 'enemy_stagger_ticks', 'magma_melee_token',
              'magma_arrow_tokens')
MEASURED = {'cold_entry', 'candidate_redraw', 'slot_redraw', 'held_repeat',
            'commit_save', 'cancel', 'return', 'busy', 'boundary', 'idle'}
DIGITS = ((7,5,5,5,7), (2,6,2,2,7), (7,1,7,4,7), (7,1,7,1,7),
          (5,5,7,1,1), (7,4,7,1,7), (7,4,7,5,7), (7,1,1,1,1),
          (7,5,7,5,7), (7,5,7,1,7))
CREAM, GOLD, WORSE, TEAL, BACKGROUND = 47, 46, 75, 80, 1


class Ability(C.Structure):
    _fields_ = [('id', C.c_ubyte), ('phase', C.c_ubyte),
                ('cooldown_updates', C.c_ushort), ('field_caps', C.c_uint)]


def unpack(value):
    return {name: int(getattr(value, name)) for name, _ in value._fields_}


class GearNative(Run):
    def __init__(self, args):
        super().__init__(args)
        self.hashes['reconstructed_after_workspace_loss'] = False
        self.hashes['suite_source_sha256'] = sha(__file__)
        self.hashes['elf_sha256'] = sha(self.rom.with_suffix('.elf'))
        self.hashes['invocation'] = [sys.executable, *sys.argv]
        shutil.copy2(__file__, self.out / 'test-source/tests/gear_preview_native.py')
        for relative in ('tests/test_equipment.py', 'src/equipment.c', 'src/equipment_data.c',
                         'src/combat_rules.c', 'src/creatures.c', 'src/creature_data.c',
                         'src/gear_preview.c', 'src/gear_menu.c', 'src/gear_runtime.c',
                         'src/companion_guide.c'):
            source, target = ROOT / relative, self.out / 'test-source' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            self.hashes['test_sources'][relative] = sha(target)
        self.oracle = build(self.out, 'equipment-oracle')
        self.definitions = (Definition * 512).in_dll(self.oracle, 'equipment_definitions')
        self.weapons = (Weapon * 4).in_dll(self.oracle, 'equipment_weapons')
        self.oracle.creatures_ability.argtypes = [C.c_uint]
        self.oracle.creatures_ability.restype = C.POINTER(Ability)
        nm = ROOT / 'tools/sysroot/usr/bin/arm-none-eabi-nm'
        listing = subprocess.check_output([str(nm), '-S', str(self.rom.with_suffix('.elf'))], text=True)
        self.sizes = {v[3]: int(v[1], 16) for line in listing.splitlines() if len(v := line.split()) == 4}
        self.sweep_rows = []
        self.boundaries = []
        self.snapshot_checks = []
        self.pixel_checks = []
        self.prepared_save = self.out / 'PREPARED-all48-passives-developer-fixture.sav'
        self.provenance = {'source_fixture': str(self.fixture.relative_to(ROOT)),
                           'source_fixture_sha256': self.fixture_sha,
                           'source_scope': 'Bundled historical developer SRAM; no user save or acquisition claim',
                           'machine_state_imports': 0, 'rom_patches': 0}

    def shot(self, name):
        super().shot(name)
        if self.g('game_state') == 3 and self.g('journal_tab') == 4:
            self.rendered_comparison(name)

    def selected_command(self):
        roster = self.save_state().roster
        slot = roster.party[roster.selected_party] if roster.selected_party < 4 else 255
        if slot >= 160:
            return 0
        member = roster.instances[slot]
        return member.equipped[member.selected_command] if member.flags & 1 and member.selected_command < 2 else 0

    def projected(self, stats, command):
        """Independent display arithmetic from effective stats and native catalog."""
        opening = self.weapons[stats.weapon_class].moves[0]
        ability = self.oracle.creatures_ability(command)
        base = (75 if command <= 4 else ability.contents.cooldown_updates) if ability else 0
        recovery = max(1, base - (75 - stats.power_cooldown)) if base else 0
        return (opening.damage_q4 + stats.attack_q4, stats.defense_q4,
                stats.max_hp_q4, (stats.speed_q8 * 25 + 4) // 8,
                (recovery * 438900 + 131072) // 262144,
                opening.reach_px + stats.reach_px, stats.stagger)

    @staticmethod
    def value_text(value, format_kind):
        if format_kind == 1:
            return f'{value / 16:.4f}'.rstrip('0').rstrip('.')
        if format_kind == 2:
            return f'{value // 10}.{value % 10}'
        if format_kind == 3:
            return f'{value // 100}.{value % 100:02d}'
        return str(value)

    @staticmethod
    def text_width(text):
        return sum(2 if c == '.' else 4 for c in text) - 1

    @staticmethod
    def paint_number(canvas, width, text, x, color):
        for char in text:
            if char == '.':
                canvas[4 * width + x] = color
                x += 2
            else:
                for y, bits in enumerate(DIGITS[int(char)]):
                    for dx in range(3):
                        if bits & (4 >> dx):
                            canvas[y * width + x + dx] = color
                x += 4

    def rendered_comparison(self, name):
        """Compare complete Mode4 numeric spans, including blank pixels/colors.

        Captures are the real mGBA RGB display. This separately checks the live
        displayed VRAM page, not the renderer's offscreen buffer or its cache.
        Every before/after digit, decimal, arrow and intervening blank is checked.
        """
        cmp = self.expected()
        command = self.selected_command()
        before, after = self.projected(cmp.before, command), self.projected(cmp.after, command)
        page = int(bool(self.e.read(0x04000000, 2) & 16))
        vram = self.e.bytes(0x0600a000 if page else 0x06000000, 240 * 160)
        fields = []
        layout = (('attack',14,86,54,0), ('defense',68,86,54,0),
                  ('hearts',122,86,54,1), ('walk',176,86,54,2),
                  ('recovery',14,101,72,3), ('distance',86,101,72,0),
                  ('stagger',158,101,72,0))
        for i, (field, x, y, width, format_kind) in enumerate(layout):
            old, new = self.value_text(before[i], format_kind), self.value_text(after[i], format_kind)
            color = CREAM if before[i] == after[i] else GOLD if (after[i] > before[i]) != (field == 'recovery') else WORSE
            expected = bytearray([BACKGROUND] * (width * 5))
            span_start = ((30 if y == 86 else 43) - self.text_width(old) - 1)
            arrow_x = 31 if y == 86 else 45
            for dx in range(5):
                expected[width + arrow_x + dx] = TEAL
            for dy in range(3):
                expected[dy * width + arrow_x + 3] = TEAL
            if field == 'recovery' and not command:
                old = new = '-'
                span_start = 38
                for start in (39, 52):
                    expected[2 * width + start:2 * width + start + 3] = bytes([CREAM] * 3)
            else:
                self.paint_number(expected, width, old, (30 if y == 86 else 43) - self.text_width(old), CREAM)
                self.paint_number(expected, width, new, 37 if y == 86 else 52, color)
            actual = b''.join(vram[(y + dy) * 240 + x:(y + dy) * 240 + x + width] for dy in range(5))
            differences = [{'x': x + j % width, 'y': y + j // width,
                            'expected_palette': a, 'actual_palette': b}
                           for j, (a, b) in enumerate(zip(expected, actual))
                           if j % width >= span_start and a != b]
            fields.append({'field': field, 'before': old, 'after': new,
                           'before_palette': CREAM, 'after_palette': color,
                           'pixels': (width - span_start) * 5,
                           'checked_bounds': [x + span_start, y, x + width - 1, y + 4],
                           'mismatched_pixels': len(differences),
                           'first_differences': differences[:12]})
        row = {'case': self.case, 'capture': name + '.png', 'hardware_frame': self.e.frame,
               'displayed_page': page, 'command': command, 'fields': fields,
               'displayed_vram_sha256': hashlib.sha256(vram).hexdigest()}
        self.pixel_checks.append(row)
        with gzip.open(self.out / (name + '.mode4.bin.gz'), 'wb') as stream:
            stream.write(vram)
        self.check(name + ': all seven before/after values and colors match displayed pixels',
                   all(not f['mismatched_pixels'] for f in fields), row)

    def step(self, n=1, keys=0, phase='measured'):
        for _ in range(n):
            super().step(1, keys, phase)
            row = self.frames[-1]
            for name in ('journal_tab', 'gear_menu_slot', 'gear_menu_candidate', 'gear_menu_revision'):
                row[name] = self.g(name)

    def write_blob(self, name, data, offset=0, reason='Explicit prepared RAM boundary fixture'):
        data = bytes(data)
        self.writes.append({'case': self.case, 'emulator_id': self.emulator_id,
                            'frame': self.e.frame, 'symbol': name, 'offset': offset,
                            'length': len(data), 'bytes_hex': data.hex(), 'reason': reason})
        for i, byte in enumerate(data):
            self.e.write(self.sym[name] + offset + i, byte, 1)

    def snapshot(self, include_save=True, include_stats=True):
        result = {n: self.e.bytes(self.sym[n], self.sizes[n]).hex()
                  for n in TRANSIENTS if n in self.sym and n in self.sizes}
        if include_save:
            result['adventure_save'] = self.e.bytes(self.sym['adventure_save'], C.sizeof(Save)).hex()
        if include_stats:
            result['gear_stats'] = self.e.bytes(self.sym['gear_stats'], C.sizeof(Stats)).hex()
        return result

    def preserved(self, label, before, include_save=True, include_stats=True):
        after = self.snapshot(include_save, include_stats)
        changed = {k: {'before': v, 'after': after.get(k)} for k, v in before.items() if after.get(k) != v}
        self.snapshot_checks.append({'case': self.case, 'label': label, 'symbols': list(before),
                                     'before_sha256': hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
                                     'after_sha256': hashlib.sha256(json.dumps(after, sort_keys=True).encode()).hexdigest(),
                                     'changes': changed})
        self.check(label, not changed, {'changed_symbols': list(changed)})

    def open_gear(self):
        self.phase_override = 'cold_entry'
        if self.g('game_state') == 1:
            self.tap('START')
        if self.g('journal_tab') == 13:
            while self.g('journal_nav_category') != 1:
                if self.g('journal_nav_category') & 1:
                    self.tap('DOWN')
                else:
                    self.tap('RIGHT')
            self.tap('A')
        self.check('Controller opens Gear', self.g('game_state') == 3 and self.g('journal_tab') == 4)
        self.phase_override = 'idle'

    def choose_slot(self, slot):
        self.phase_override = 'slot_redraw'
        for _ in range(5):
            if self.g('gear_menu_slot') == slot:
                break
            self.tap('RIGHT')
        assert self.g('gear_menu_slot') == slot
        self.phase_override = 'candidate_redraw'

    def choose(self, item, slot=None):
        if slot is None:
            slot = self.definitions[item].slot
        self.choose_slot(slot)
        reference = 255 if item == 0 else next(i for i, r in enumerate(self.save_state().equipment.bag) if r.item_id == item)
        for _ in range(50):
            if self.g('gear_menu_candidate') == reference:
                return reference
            self.tap('DOWN')
        raise AssertionError(('Controller cannot select', item, slot, reference))

    def expected(self, slot=None, candidate=None):
        s = self.save_state()
        state = State.from_buffer_copy(bytes(s.equipment))
        cmp = Comparison()
        slot = self.g('gear_menu_slot') if slot is None else slot
        candidate = self.g('gear_menu_candidate') if candidate is None else candidate
        base = (self.g('max_hp') + bool(s.economy.relics & 1)) * 16
        result = self.oracle.equipment_preview(C.byref(state), slot, candidate, base,
                                                self.g('hero_hp_q4'), 0, C.byref(cmp))
        assert result == 0, result
        for stats in (cmp.before, cmp.after):
            recovery = min(8, 75 - stats.power_cooldown + 42 - stats.roll_cooldown)
            stats.power_cooldown = 75 - recovery - (8 if s.economy.relics & 2 else 0)
            stats.attack_q4 = min(32, stats.attack_q4 + 4 * (s.economy.upgrade + bool(s.economy.relics & 4)))
        return cmp

    def commit(self, label):
        cmp = self.expected()
        before = self.snapshot(include_save=False, include_stats=False)
        hp_before = self.g('hero_hp_q4')
        self.phase_override = 'commit_save'
        self.tap('A')
        settled = self.wait(lambda: self.g('game_state') == 3 and not self.g('save_requested')
                            and not self.g('save_feedback_background') and not self.g('save_begin_pending'), 1800)
        self.step(4)
        self.check(label + ': save completes', settled and not self.g('save_failed'))
        self.check(label + ': validated after stats applied exactly',
                   self.e.bytes(self.sym['gear_stats'], C.sizeof(Stats)) == bytes(cmp.after),
                   {'expected': unpack(cmp.after), 'actual': unpack(Stats.from_buffer_copy(self.e.bytes(self.sym['gear_stats'], C.sizeof(Stats))))})
        self.check(label + ': no healing', self.g('hero_hp_q4') == min(hp_before, cmp.after.max_hp_q4))
        # HP may clamp on removing health capacity; no other active state resets.
        before['hero_hp_q4'] = self.e.bytes(self.sym['hero_hp_q4'], self.sizes['hero_hp_q4']).hex()
        before['hp'] = self.e.bytes(self.sym['hp'], self.sizes['hp']).hex()
        self.preserved(label + ': all current cooldown/action/projectile state preserved', before, False, False)
        self.phase_override = 'idle'

    def fresh_start(self):
        self.play()
        before_equipment = bytes(self.save_state().equipment)
        self.open_gear()
        self.shot('controller-new-game-cold-gear')
        before = self.snapshot()
        for slot in range(5):
            self.choose_slot(slot)
            self.tap('DOWN')
            self.preserved('Fresh game browse slot ' + str(slot) + ' preserves state', before)
        self.check('New game browsing never auto-equips', bytes(self.save_state().equipment) == before_equipment)
        self.phase_override = 'cancel'
        self.tap('B')
        self.preserved('Fresh game B cancel preserves state', before)

    def prepare_fixture(self):
        self.phase_override = 'fixture_preparation'
        self.play(True)
        self.check('Host oracle catalog exactly matches native ROM table',
                   self.e.bytes(self.sym['equipment_definitions'], C.sizeof(self.definitions)) == bytes(self.definitions))
        self.check('Host opening-move catalog exactly matches native ROM table',
                   self.e.bytes(self.sym['equipment_weapons'], C.sizeof(self.weapons)) == bytes(self.weapons))
        abilities = (Ability * 128).in_dll(self.oracle, 'creature_abilities')
        self.check('Host ability cooldown catalog exactly matches native ROM table',
                   self.e.bytes(self.sym['creature_abilities'], C.sizeof(abilities)) == bytes(abilities))
        ids = {r.item_id for r in self.save_state().equipment.bag if r.item_id}
        self.check('Historical developer fixture contains all 48 current authored items', ids == set(IDS), sorted(ids))
        assert ids == set(IDS), 'Source fixture must contain all current items; do not fabricate acquisition'
        self.open_gear()
        self.phase_override = 'fixture_preparation'
        self.write_blob('adventure_save', bytes([0, 255, 255, 255, 255]),
                        Save.equipment.offset + State.equipped.offset,
                        'Prepared developer fixture: baseline starter and empty optional slots')
        econ = Economy.from_buffer_copy(bytes(self.save_state().economy))
        econ.earned, econ.spent, econ.gold = 320, 120, 200
        econ.relics, econ.boss_claims, econ.upgrade = 7, 7, 1
        self.write_blob('adventure_save', bytes(econ), Save.economy.offset,
                        'Prepared developer fixture: earned boss passive flags and one upgrade, no user save')
        self.choose(1)
        self.commit('Prepared fixture native writer')
        self.e.save(self.prepared_save)
        self.provenance['prepared_sram_sha256'] = sha(self.prepared_save)
        self.provenance['prepared_sram'] = self.prepared_save.name
        self.provenance['prepared_sram_changes'] = 'Equipped refs reset; relics/claims 7; upgrade 1; earned 320/spent 120/gold 200; native writer export'
        self.play(self.prepared_save)
        self.check('Independent cold load preserves prepared all48 and passive flags',
                   {r.item_id for r in self.save_state().equipment.bag} == set(IDS)
                   and self.save_state().economy.relics == 7 and self.save_state().economy.upgrade == 1)

    def wounded_pause(self):
        self.open_gear()
        self.phase_override = 'fixture_preparation'
        for name, value in (('hero_hp_q4', 83), ('hp', 6), ('ability_cd', 137),
                            ('ability_max', 180), ('heal_cd', 213), ('invuln', 38),
                            ('guard_invuln', 17), ('stone_guard', 41), ('power_effect', 22)):
            self.put(name, value, reason='Prepared wounded/current-timer fixture after actual controller menu entry')
        self.phase_override = 'idle'
        self.step(4)

    def sweep(self):
        self.play(self.prepared_save)
        self.wounded_pause()
        before = self.snapshot()
        sram = self.e.bytes(0x0e000000, 32768)
        visited = set()
        for slot in range(5):
            self.choose_slot(slot)
            first = self.g('gear_menu_candidate')
            rows = []
            for _ in range(50):
                candidate = self.g('gear_menu_candidate')
                item = 0 if candidate == 255 else self.save_state().equipment.bag[candidate].item_id
                cmp = self.expected()
                name = self.oracle.equipment_name(item).decode() if item else ('Starter Sword' if slot == 0 else 'Remove')
                path = f'sweep/{slot}-{SLOTS[slot]}-{item:02d}'
                (self.out / 'sweep').mkdir(exist_ok=True)
                self.shot(path)
                row = {'slot': slot, 'candidate': candidate, 'item_id': item, 'name': name,
                       'before': unpack(cmp.before), 'after': unpack(cmp.after),
                       'hp_before_q4': cmp.hp_before_q4, 'hp_after_q4': cmp.hp_after_q4,
                       'capture': path + '.png', 'frame': self.e.frame}
                self.sweep_rows.append(row)
                rows.append(item)
                visited.add((slot, item))
                self.preserved(f'{SLOTS[slot]} {item}: browse preserves complete runtime and save', before)
                self.phase_override = 'candidate_redraw'
                self.tap('DOWN')
                if self.g('gear_menu_candidate') == first:
                    break
            expected = {i for i in IDS if self.definitions[i].slot == slot} | {0}
            self.check(SLOTS[slot] + ': controller wraps every owned item and removal once', set(rows) == expected and len(rows) == len(expected), rows)
        self.check('All48 plus five removal entries reached by controller', len(visited) == 53, len(visited))
        self.check('Browsing never writes cartridge SRAM', self.e.bytes(0x0e000000, 32768) == sram)
        self.phase_override = 'held_repeat'
        start = len(self.frames)
        self.step(55, 'DOWN')
        self.step(4)
        changed = [r['hw'] for i, r in enumerate(self.frames[start:])
                   if i and r['gear_menu_candidate'] != self.frames[start + i - 1]['gear_menu_candidate']]
        self.check('Held Down produces deliberate repeated candidate redraws', len(changed) >= 5, changed)
        self.preserved('Held repeat never mutates save or complete current state', before)
        self.phase_override = 'cancel'
        self.tap('B')
        self.check('B returns to hub', self.g('journal_tab') == 13 and self.g('game_state') == 3)
        self.preserved('B cancel preserves complete runtime and save', before)
        self.check('Cancel never writes cartridge SRAM', self.e.bytes(0x0e000000, 32768) == sram)
        self.open_gear()
        self.phase_override = 'return'
        self.step(1, 'START')
        self.check('Start closes Gear to play', self.g('game_state') == 1)
        self.preserved('Start closes before advancing current action/timers', before)
        self.step(4)

    def commits(self):
        self.play(self.prepared_save)
        self.wounded_pause()
        for item in (35, 53, 66, 19, 83, 86, 89):
            self.choose(item)
            self.shot('preview-commit-' + str(item))
            self.commit('Equip ' + self.oracle.equipment_name(item).decode())
            self.shot('commit-' + str(item))
        ring83, ring86 = self.definitions[83], self.definitions[86]
        self.check('Duplicate-effect rings remain distinct owned identities',
                   bytes(ring83.stats) == bytes(ring86.stats) and self.oracle.equipment_name(83) != self.oracle.equipment_name(86))
        for slot in range(5):
            self.choose(0, slot)
            self.shot('preview-remove-' + SLOTS[slot])
            self.commit('Remove ' + SLOTS[slot])
            wanted = 0 if slot == 0 else 255
            self.check('Removal keeps documented reference ' + SLOTS[slot], self.save_state().equipment.equipped[slot] == wanted)
        persisted = bytes(self.save_state().equipment)
        save = self.out / 'PREPARED-controller-commits.sav'
        self.e.save(save)
        self.play(save)
        self.check('Controller commits survive an independent cold SRAM reload', bytes(self.save_state().equipment) == persisted)

    def boundary_caps(self):
        self.play(self.prepared_save)
        self.wounded_pause()
        for item in (52, 69, 88):
            self.choose(item)
            self.commit('Reach recovery cap using item ' + str(item))
        self.check('Reachable gear recovery 8 plus Feather8 caps at16', self.e.read(self.sym['gear_stats'] + 9, 1) == 59)
        for item in (81, 88, 89):
            self.choose(item)
            cmp = self.expected()
            self.check('Capped recovery comparison ' + str(item) + ' remains59', cmp.after.power_cooldown == 59)
            self.shot('boundary-recovery-cap-' + str(item))
            self.boundaries.append({'kind': 'recovery', 'candidate': item, 'before': unpack(cmp.before), 'after': unpack(cmp.after)})
        self.choose(50)
        self.commit('Reach recovery cap with Surestep boots')
        self.choose(52)
        cmp = self.expected()
        self.check('Recovery cap hides no speed penalty: Surestep to Softsand',
                   cmp.before.power_cooldown == cmp.after.power_cooldown == 59 and cmp.after.speed_q8 < cmp.before.speed_q8)
        self.shot('boundary-recovery-unchanged-speed-worse')
        self.boundaries.append({'kind': 'recovery-cap-speed-tradeoff', 'before': unpack(cmp.before), 'after': unpack(cmp.after)})
        for item in (4, 67, 84):
            self.choose(item)
            self.commit('Reach stagger cap using item ' + str(item))
        self.check('Reachable stagger four raw points caps at3', self.e.read(self.sym['gear_stats'] + 11, 1) == 3)
        self.choose(82)
        cmp = self.expected()
        self.check('Stagger capped candidate stays3', cmp.before.stagger == cmp.after.stagger == 3)
        self.shot('boundary-stagger-cap')
        self.boundaries.append({'kind': 'stagger', 'candidate': 82, 'before': unpack(cmp.before), 'after': unpack(cmp.after)})
        self.choose(0, 3)
        cmp = self.expected()
        self.check('Removing Bricklayer belt at capped stagger preserves3', cmp.before.stagger == cmp.after.stagger == 3)
        self.shot('boundary-stagger-unchanged-belt-removal')
        self.boundaries.append({'kind': 'stagger-cap-removal', 'before': unpack(cmp.before), 'after': unpack(cmp.after)})
        for item in (1, 35, 53, 66):
            self.choose(item)
            self.commit('Fractional health candidate ' + str(item))
        self.choose(34)
        self.shot('boundary-quarter-hearts-and-capacity-growth')
        cmp = self.expected()
        self.check('Fractional heart comparison includes exact quarter units', cmp.before.max_hp_q4 % 16 == 12)
        self.boundaries.append({'kind': 'hearts', 'before': unpack(cmp.before), 'after': unpack(cmp.after)})
        self.phase_override = 'fixture_preparation'
        self.put('max_hp', 8, reason='Prepared maximum authored base-health fixture; next native gear commit recalculates live stats')
        self.put('relic_found', 1, reason='Prepared matching campaign heart-capacity flag, not controller acquisition')
        for item in (14, 34, 56, 65):
            self.choose(item)
            self.commit('Reach highest authored HP using item ' + str(item))
        self.choose(40)
        self.shot('boundary-widest-reachable-heart-values')
        cmp = self.expected()
        self.check('Widest reachable heart comparison renders11.25 exactly',
                   cmp.before.max_hp_q4 == 180 and cmp.after.max_hp_q4 == 180)
        self.boundaries.append({'kind': 'highest-authored-hp', 'before': unpack(cmp.before), 'after': unpack(cmp.after)})
        # Full current HP fixture proves lowering capacity clamps but cannot heal.
        self.phase_override = 'fixture_preparation'
        self.put('hero_hp_q4', self.e.read(self.sym['gear_stats'], 2), reason='Prepared current HP at actual derived maximum for capacity removal')
        self.put('hp', (self.g('hero_hp_q4') + 15) // 16)
        self.choose(0, 1)
        self.shot('boundary-hp-clamp-before-removal')
        self.commit('Remove health gear at maximum')
        self.shot('boundary-hp-clamp-after-removal')

    def busy(self):
        self.play(self.prepared_save)
        self.wounded_pause()
        self.choose(2)
        for name, action_phase, arrow, projectile in (('melee-windup', 1, False, False),
                                                   ('melee-active', 2, False, False),
                                                   ('melee-recovery', 3, False, False),
                                                   ('live-arrow', 0, True, False),
                                                   ('live-player-projectile', 0, False, True)):
            self.phase_override = 'fixture_preparation'
            action = bytearray(20)
            action[2], action[3], action[4] = 1, action_phase, 1
            action[6], action[8], action[9] = 7, 2, 19
            action[12:18] = bytes((32, 8, 29, 18, 2, 255))
            self.write_blob('weapon_action', action, reason='Prepared committed action fixture: ' + name)
            arrows = bytearray(40)
            if arrow:
                import struct
                arrows[:20] = struct.pack('<iiHHBBBBBBBB', 120 * 256, 90 * 256, 60 * 256, 1024, 1, 1, 32, 8, 2, 255, 0, 0)
            self.write_blob('player_arrows', arrows, reason='Prepared live-arrow fixture: ' + name)
            shots = bytearray(self.sizes['shots'])
            if projectile:
                import struct
                shots[:24] = struct.pack('<iiiiii', 120, 90, 1, 0, 47, 0)
            self.write_blob('shots', shots, reason='Prepared player projectile fixture: ' + name)
            self.phase_override = 'busy'
            self.step(4)
            before = self.snapshot()
            sram = self.e.bytes(0x0e000000, 32768)
            self.tap('DOWN')
            self.tap('UP')
            self.preserved(name + ': preview preserves every current action/projectile byte', before)
            self.tap('A')
            self.step(8)
            self.check(name + ': A refuses equipment mutation while busy', self.g('game_state') == 3 and self.g('journal_tab') == 4)
            self.preserved(name + ': denied commit preserves full runtime/save', before)
            self.check(name + ': denied commit leaves cartridge SRAM unchanged', self.e.bytes(0x0e000000, 32768) == sram)
            self.shot('busy-' + name)
            self.tap('B')
            self.preserved(name + ': B cancel preserves full runtime/save', before)
            self.open_gear()
            self.choose(2)
        self.provenance['busy_scope'] = ('Committed melee phases and live player arrows/projectiles. Existing modal-entry policy cancels un-fired bow charging and queued input; removed roll state is always zero. Those are not treated as menu mutations.')

    def report(self):
        if not hasattr(self, 'sweep_rows'):
            return {}
        measured = [r for r in self.frames if r['phase'] in MEASURED]
        phases = {}
        for phase in sorted({r['phase'] for r in measured}):
            rows = [r for r in measured if r['phase'] == phase]
            completed = {}
            for r in rows:
                p = r.get('completed_profile')
                if p:
                    completed[(r['emulator_id'], p['serial'])] = {'cycles': r['cycles'], **p}
            exceptions = [r for r in rows if r['cycles'] >= LIMIT or r['delta'] != 1 or not r['flip']]
            phases[phase] = {'hardware_frames': len(rows), 'completed_work_samples': len(completed),
                             'peak_render_cycles': max((r['cycles'] for r in rows), default=0),
                             'peak_completed_work_cycles': max((p['cycles'] for p in completed.values()), default=0),
                             'pacing_exceptions': len(exceptions), 'exception_examples': exceptions[:6]}
        failures = [c for c in self.checks if not c['passed']]
        result = {'suite': 'gear-preview-native', 'complete': self.complete, 'provenance': {**self.hashes, **self.provenance},
                  'scope': __doc__, 'checks': len(self.checks), 'failures': failures,
                  'assertions': self.checks, 'sweep': self.sweep_rows, 'boundaries': self.boundaries,
                  'snapshot_checks': self.snapshot_checks, 'pixel_checks': self.pixel_checks, 'cases': self.cases,
                  'pixel_coverage': {'captures': len(self.pixel_checks),
                                     'before_after_value_pairs': sum(len(c['fields']) for c in self.pixel_checks),
                                     'verified_palette_pixels': sum(f['pixels'] for c in self.pixel_checks for f in c['fields']),
                                     'mismatched_pixels': sum(f['mismatched_pixels'] for c in self.pixel_checks for f in c['fields'])},
                  'game_ram_fixture_writes': len(self.writes), 'machine_state_imports': self.state_loads,
                  'performance': {'hardware_cycle_limit_exclusive': LIMIT, 'phases': phases,
                                  'measured_frames': len(measured),
                                  'peak_cycles': max((r['cycles'] for r in measured), default=0),
                                  'pacing_exceptions': sum(v['pacing_exceptions'] for v in phases.values()),
                                  'native_faults': max((r['faults'] for r in self.frames), default=0)},
                  'exact_files_unchanged': sha(self.rom) == self.hashes['rom_sha256'] and sha(self.symbols) == self.hashes['symbols_sha256']}
        (self.out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
        return result

    def finish(self):
        self.case = 'summary'
        measured = [r for r in self.frames if r['phase'] in MEASURED]
        profiles = [{'cycles': r['cycles'], **r['completed_profile']}
                    for r in measured if r.get('completed_profile')]
        self.check('Every completed render-work sample is strictly below hardware frame budget',
                   bool(profiles) and all(p['cycles'] < LIMIT for p in profiles),
                   {'samples': len(profiles), 'limit_exclusive': LIMIT,
                    'peak_cycles': max((p['cycles'] for p in profiles), default=0)})
        self.check('Every measured hardware frame advances once and flips display page',
                   bool(measured) and all(r['delta'] == 1 and r['flip'] for r in measured),
                   {'frames': len(measured)})
        deferred = [p for p in profiles if p.get('deferred_actors')]
        self.check('Completed deferred render work stays wholly in VBlank',
                   all(160 <= p['vblank_start'] <= p['vblank_end'] < 228 and p['vblank_cycles'] <= 83776 for p in deferred),
                   {'samples': len(deferred), 'peak_vblank_cycles': max((p['vblank_cycles'] for p in deferred), default=0)})
        music = [r['music'] for r in measured if r.get('music')]
        self.check('Native music stays active without faults or recovery',
                   bool(music) and all(not p.get('music_faults') and not p.get('music_recoveries') and not p.get('music_stopped') for p in music)
                   and max(p.get('music_irq_count', 0) for p in music) > 0)
        if self.e:
            self.check('Final native emulator fault count zero', self.e.lib.eb_faults(self.e.ptr) == 0)
            self.e.close()
            self.e = None
        for name, data in (('native-frames', self.frames), ('controller-inputs', self.inputs), ('PREPARED-ram-writes', self.writes)):
            with gzip.open(self.out / (name + '.jsonl.gz'), 'wt') as f:
                for row in data:
                    f.write(json.dumps(row, separators=(',', ':')) + '\n')
        self.complete = True
        result = self.report()
        print(json.dumps({k: result[k] for k in ('checks', 'failures', 'performance', 'exact_files_unchanged')}, indent=2))
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'build/emberbond.gba')
    parser.add_argument('--symbols', type=Path, default=ROOT / 'build/emberbond.sym')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-rom-sha', required=True)
    parser.add_argument('--expected-symbols-sha', required=True)
    parser.add_argument('--cases', default='fresh_start,prepare_fixture,sweep,commits,boundary_caps,busy')
    args = parser.parse_args()
    run = GearNative(args)
    for name in args.cases.split(','):
        run.section(name, getattr(run, name))
    result = run.finish()
    return int(bool(result['failures']) or bool(result['performance']['pacing_exceptions'])
               or bool(result['performance']['native_faults']) or not result['exact_files_unchanged'])


if __name__ == '__main__':
    raise SystemExit(main())
