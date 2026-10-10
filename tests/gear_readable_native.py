#!/usr/bin/env python3
"""Exact-ROM native acceptance for the readable, two-row Gear comparison.

The controller scope retains the original 53-entry controller sweep, save
commits, wounded/current-timer snapshots, busy refusals, and authored caps.
The passive scope retains the integrated treasure and Porchlight ring cases,
with an extra no-command display boundary. Historical SRAM and every RAM
preparation are explicitly labelled developer fixtures, never user saves or
controller acquisition. No ROM patching or machine-state import is used.

Expected 4x7 digits, two-pixel decimal dots, 7x5 arrows, and placement are an
independent Python raster. Labels decode the canonical even-parity UiRuns
from the pinned ROM and translate them, independently of production's
parity-specific renderer. Checks read the actual displayed Mode4 VRAM page.
All screenshots are unscaled native 240x160 mGBA frames.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tools')]
from gear_preview_native import (
    GearNative, MEASURED, LIMIT, CREAM, GOLD, WORSE, TEAL, BACKGROUND, sha,
)
from gear_treasure_native import TreasureGear


# Frozen design contract, independent of source parsing and target glyph data.
DIGITS = (
    (6, 9, 9, 9, 9, 9, 6),
    (2, 6, 2, 2, 2, 2, 7),
    (6, 9, 1, 2, 4, 8, 15),
    (14, 1, 1, 6, 1, 1, 14),
    (2, 6, 10, 10, 15, 2, 2),
    (15, 8, 8, 14, 1, 1, 14),
    (6, 8, 8, 14, 9, 9, 6),
    (15, 1, 1, 2, 2, 4, 4),
    (6, 9, 9, 6, 9, 9, 6),
    (6, 9, 9, 7, 1, 1, 6),
)

LAYOUT = (
    ('attack', 'ATTACK', 12, 80, 93, 54, 0),
    ('defense', 'DEFENSE', 66, 80, 93, 54, 0),
    ('hearts', 'HEART', 120, 80, 93, 54, 1),
    ('walk', 'WALK', 174, 80, 93, 54, 2),
    ('recovery', 'RECOVERY', 12, 102, 115, 72, 3),
    ('distance', 'DISTANCE', 84, 102, 115, 72, 0),
    ('stagger', 'STAGGER', 156, 102, 115, 72, 0),
)
CONTROLLER_CASES = 'fresh_start,prepare_fixture,sweep,commits,boundary_caps,busy'
PASSIVE_CASES = 'combinations,boundary_cases,cache,compass,ring_choice,no_command'


class ReadableRaster:
    """Shared display oracle; gameplay fixtures remain in existing suites."""

    def __init__(self, args):
        super().__init__(args)
        self.label_checks = []
        self.candidate_name_checks = []
        self.native_image_checks = []
        self.readability_manifest = self.rom.parent / 'source-hashes.json'
        self.readability_sources = json.loads(self.readability_manifest.read_text())
        assert sha(self.rom.with_suffix('.elf')) == args.expected_elf_sha
        assert sha(self.readability_manifest) == args.expected_source_manifest_sha
        assert all(sha(ROOT / path) == value for path, value in self.readability_sources.items())
        self.hashes.update(
            readable_suite_sha256=sha(__file__),
            expected_elf_sha256=args.expected_elf_sha,
            source_manifest_sha256=sha(self.readability_manifest),
            inherited_controller_suite_sha256=sha(ROOT / 'tests/gear_preview_native.py'),
            inherited_passive_suite_sha256=sha(ROOT / 'tests/gear_treasure_native.py'),
        )
        for relative in ('tests/gear_readable_native.py', 'tests/gear_treasure_native.py',
                         'src/gear_preview_text.h', 'assets/gear_preview_labels.json',
                         'assets/gear_preview_text_metrics.json', 'src/ui.h'):
            source, target = ROOT / relative, self.out / 'test-source' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            self.hashes['test_sources'][relative] = sha(target)
        shutil.copyfile(self.readability_manifest, self.out / 'candidate-source-hashes.json')
        self.gp_names = re.findall(r' GP_([A-Z_]+),', (ROOT / 'src/gear_preview_text.h').read_text())
        self.ui_names = re.findall(r'\bTX_([A-Z_0-9]+),', (ROOT / 'src/ui.h').read_text())
        self.item_texts = {int(item): name for item, name in re.findall(
            r'case (\d+):return TX_([A-Z_0-9]+);', (ROOT / 'src/gear_menu.c').read_text())}

    @staticmethod
    def text_width(text):
        return sum(3 if char == '.' else 5 for char in text) - 1

    @staticmethod
    def paint_number(canvas, width, text, x, color):
        for char in text:
            if char == '.':
                for y in (5, 6):
                    canvas[y * width + x:y * width + x + 2] = bytes([color] * 2)
                x += 3
            else:
                for y, bits in enumerate(DIGITS[int(char)]):
                    for dx in range(4):
                        if bits & (8 >> dx):
                            canvas[y * width + x + dx] = color
                x += 5

    @staticmethod
    def paint_arrow(canvas, width, x):
        for dx in range(7):
            canvas[3 * width + x + dx] = TEAL
        for dx, dy in ((4, 1), (4, 2), (5, 2), (4, 4), (5, 4), (4, 5)):
            canvas[dy * width + x + dx] = TEAL

    def ui_record(self, name, table='gear_preview_texts'):
        index = (self.gp_names if table == 'gear_preview_texts' else self.ui_names).index(name)
        address = self.sym[table] + index * 16
        return dict(width=self.e.read(address, 2), height=self.e.read(address + 2, 1),
                    runs=self.e.read(address + 4), count=self.e.read(address + 12, 2))

    def canonical_text(self, name, color, table='gear_preview_texts'):
        record = self.ui_record(name, table)
        pixels = {}
        for i in range(record['count']):
            address = record['runs'] + i * 4
            offset = self.e.read(address, 2)
            count, mask = self.e.read(address + 2, 1), self.e.read(address + 3, 1)
            assert count and 1 <= mask <= 3
            for half in range(count):
                y, x = divmod(offset + half, 120)
                for bit in range(2):
                    if mask & (1 << bit):
                        assert x * 2 + bit < record['width'] and y < record['height']
                        pixels[(x * 2 + bit, y)] = color
        return record, pixels

    def displayed_vram(self):
        page = int(bool(self.e.read(0x04000000, 2) & 16))
        return page, self.e.bytes(0x0600a000 if page else 0x06000000, 240 * 160)

    def verify_label(self, name, y, color, x=None, table='gear_preview_texts',
                     capture=None, height=None, bounds=(12, 228)):
        record, pixels = self.canonical_text(name, color, table)
        x = (240 - record['width']) // 2 if x is None else x
        height = record['height'] if height is None else height
        assert pixels
        overflow = [(px, py) for px, py in pixels if py >= height]
        self.check('Label ' + name + ' ends above following row', not overflow,
                   {'overflow_pixels': overflow, 'height': height})
        expected = bytearray([BACKGROUND] * (240 * height))
        for (px, py), ink in pixels.items():
            if py < height:
                expected[py * 240 + x + px] = ink
        _, vram = self.displayed_vram()
        actual = vram[y * 240:(y + height) * 240]
        diffs = [dict(x=i % 240, y=y + i // 240, expected_palette=a, actual_palette=b)
                 for i, (a, b) in enumerate(zip(expected, actual))
                 if bounds[0] <= i % 240 < bounds[1] and a != b]
        row = dict(case=self.case, capture=capture, label=name, table=table,
                   x=x, y=y, width=record['width'], checked_height=height,
                   mismatches=len(diffs), first_differences=diffs[:12])
        self.label_checks.append(row)
        self.check('Actual readable label pixels ' + name, not diffs, row)

    def context(self, name):
        # Inherited passive cases use this to verify the cap explanation.
        self.verify_label(name, 124, TEAL, height=14)

    def context_name(self, comparison, before, after, command):
        if not command:
            return 'NO_COMMAND'
        if (before == after and comparison.before.weapon_class == comparison.after.weapon_class
                and comparison.before.phase == comparison.after.phase):
            return 'SAME'
        weapon = {1: 'SWORD', 2: 'LANCE', 3: 'BOW'}[comparison.after.weapon_class]
        if self.g('gear_menu_slot') == 0:
            return weapon
        economy = self.save_state().economy
        passive_reduction = (8 if economy.relics & 2 else 0) + (4 if economy.later_claims & 4 else 0)
        if before[4] == after[4] and 75 - comparison.after.power_cooldown >= 8 + passive_reduction:
            return 'RECOVERY_CAP'
        if before[6] == after[6] == 3:
            return 'STAGGER_CAP'
        return weapon

    def verify_candidate_name(self, capture):
        slot, candidate = self.g('gear_menu_slot'), self.g('gear_menu_candidate')
        item = self.save_state().equipment.bag[candidate].item_id if candidate < 48 else 0
        name = ('PF_STARTER' if slot == 0 else 'PF_UNEQUIP') if candidate == 255 else self.item_texts[item or 1]
        expected = bytearray([BACKGROUND] * (240 * 15))
        records = []
        for label, x, color, table in ((name, None, GOLD, 'ui_texts'),
                                       ('UP', 12, TEAL, 'gear_preview_texts'),
                                       ('DOWN', 216, TEAL, 'gear_preview_texts')):
            record, pixels = self.canonical_text(label, color, table)
            x = (240 - record['width']) // 2 if x is None else x
            for (px, py), ink in pixels.items():
                expected[py * 240 + x + px] = ink
            records.append(dict(label=label, x=x, width=record['width']))
        _, vram = self.displayed_vram()
        actual = vram[65 * 240:80 * 240]
        diffs = [dict(x=i % 240, y=65 + i // 240, expected_palette=a, actual_palette=b)
                 for i, (a, b) in enumerate(zip(expected, actual))
                 if 12 <= i % 240 < 228 and a != b]
        row = dict(capture=capture, item_id=item, slot=slot, texts=records,
                   mismatches=len(diffs), first_differences=diffs[:12])
        self.candidate_name_checks.append(row)
        self.check('Full native candidate name and browse arrows remain intact', not diffs, row)

    def rendered_comparison(self, name):
        comparison = self.expected()
        command = self.selected_command()
        before = self.projected(comparison.before, command)
        after = self.projected(comparison.after, command)
        page, vram = self.displayed_vram()
        fields = []
        for i, (field, label, x, label_y, y, width, format_kind) in enumerate(LAYOUT):
            old = self.value_text(before[i], format_kind)
            new = self.value_text(after[i], format_kind)
            color = CREAM if before[i] == after[i] else (
                GOLD if (after[i] > before[i]) != (field == 'recovery') else WORSE)
            expected = bytearray([BACKGROUND] * (width * 7))
            detail = i >= 4
            before_end, arrow_x, after_x = (32, 33, 41) if detail else (23, 24, 32)
            self.paint_arrow(expected, width, arrow_x)
            if field == 'recovery' and not command:
                old = new = '-'
                for start in (before_end - 6, after_x):
                    for dy in (3, 4):
                        expected[dy * width + start:dy * width + start + 6] = bytes([CREAM] * 6)
            else:
                assert self.text_width(old) <= before_end, (field, old)
                assert after_x + self.text_width(new) <= width, (field, new)
                self.paint_number(expected, width, old, before_end - self.text_width(old), CREAM)
                self.paint_number(expected, width, new, after_x, color)
            actual = b''.join(vram[(y + dy) * 240 + x:(y + dy) * 240 + x + width]
                              for dy in range(7))
            diffs = [dict(x=x + j % width, y=y + j // width,
                          expected_palette=a, actual_palette=b)
                     for j, (a, b) in enumerate(zip(expected, actual)) if a != b]
            fields.append(dict(field=field, before=old, after=new,
                               before_palette=CREAM, after_palette=color,
                               pixels=width * 7, checked_bounds=[x, y, x + width - 1, y + 6],
                               mismatched_pixels=len(diffs), first_differences=diffs[:12]))
            label_x = x + (width - self.ui_record(label)['width']) // 2
            self.verify_label(label, label_y, CREAM, x=label_x, capture=name + '.png',
                              height=13, bounds=(x, x + width))
        row = dict(case=self.case, capture=name + '.png', hardware_frame=self.e.frame,
                   displayed_page=page, command=command, fields=fields,
                   displayed_vram_sha256=hashlib.sha256(vram).hexdigest())
        self.pixel_checks.append(row)
        with gzip.open(self.out / (name + '.mode4.bin.gz'), 'wb') as stream:
            stream.write(vram)
        self.check(name + ': all seven complete number rows exactly match displayed VRAM',
                   all(not field['mismatched_pixels'] for field in fields), row)
        self.verify_candidate_name(name + '.png')
        self.verify_label(self.context_name(comparison, before, after, command),
                          124, TEAL, height=14, capture=name + '.png')
        self.verify_label('FOOTER', 138, TEAL, capture=name + '.png')
        path = self.out / (name + '.png')
        with Image.open(path) as image:
            size = image.size
        self.native_image_checks.append(dict(capture=name + '.png', size=list(size),
                                             png_sha256=sha(path)))
        self.check(name + ': actual screenshot stays unscaled 240x160', size == (240, 160))

    def report(self):
        result = super().report()
        if result and hasattr(self, 'label_checks'):
            result.update(suite='gear-readable-native-' + self.a.suite, scope=__doc__,
                          label_checks=self.label_checks,
                          candidate_name_checks=self.candidate_name_checks,
                          native_image_checks=self.native_image_checks,
                          readable_geometry={'digits': [4, 7], 'decimal_dot': [2, 2],
                                             'arrow': [7, 5], 'layout': LAYOUT,
                                             'context_y': 124, 'footer_y': 138})
            result['pixel_coverage']['label_checks'] = len(self.label_checks)
            result['pixel_coverage']['mismatched_label_pixels'] = sum(
                row['mismatches'] for row in self.label_checks)
            (self.out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
        return result

    def finish(self):
        self.check('Pinned ELF unchanged', sha(self.rom.with_suffix('.elf')) == self.a.expected_elf_sha)
        self.check('Pinned source manifest unchanged', sha(self.readability_manifest) == self.a.expected_source_manifest_sha)
        self.check('All production sources still match candidate manifest', all(
            sha(ROOT / path) == value for path, value in self.readability_sources.items()))
        if self.a.suite == 'controller' and 'sweep' in self.a.cases.split(','):
            self.check('Complete inherited controller sweep has exactly 53 entries', len(self.sweep_rows) == 53)
        if self.a.suite == 'passive' and self.a.cases == PASSIVE_CASES:
            self.check('Passive/ring coverage includes at least 33 native captures', len(self.pixel_checks) >= 33)
        measured = [row for row in self.frames if row['phase'] in MEASURED]
        commits = [row for row in measured if row['phase'] == 'commit_save']
        self.check('A/save frames have complete once-per-frame cadence', bool(commits) and all(
            row['delta'] == 1 and row['flip'] and row['cycles'] < LIMIT for row in commits),
            {'frames': len(commits), 'peak_cycles': max((row['cycles'] for row in commits), default=0)})
        return super().finish()


class ReadableGear(ReadableRaster, GearNative):
    pass


class ReadableTreasure(ReadableRaster, TreasureGear):
    def no_command(self):
        self.prepared(15, 7)
        self.phase_override = 'fixture_preparation'
        state = self.save_state()
        state.roster.selected_party = 255
        self.write_blob('adventure_save', bytes(state), reason=(
            'Explicit prepared developer no-selected-companion display fixture; no acquisition claim'))
        self.put('gear_menu_revision', self.g('gear_menu_revision') + 1,
                 reason='Invalidate Gear display after explicit no-command RAM preparation')
        self.phase_override = 'boundary'
        self.check('Prepared no-command fixture has no active selected command', self.selected_command() == 0)
        before = self.snapshot()
        self.shot('no-command-readable-dashes')
        self.context('NO_COMMAND')
        self.preserved('No-command display retains every current timer and prepared save byte', before)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--symbols', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-rom-sha', required=True)
    parser.add_argument('--expected-symbols-sha', required=True)
    parser.add_argument('--expected-elf-sha', required=True)
    parser.add_argument('--expected-source-manifest-sha', required=True)
    parser.add_argument('--suite', choices=('controller', 'passive'), required=True)
    parser.add_argument('--cases')
    args = parser.parse_args()
    if args.cases is None:
        args.cases = CONTROLLER_CASES if args.suite == 'controller' else PASSIVE_CASES
    run = (ReadableGear if args.suite == 'controller' else ReadableTreasure)(args)
    for name in args.cases.split(','):
        run.section(name, getattr(run, name))
    result = run.finish()
    return int(bool(result['failures']) or bool(result['performance']['pacing_exceptions'])
               or bool(result['performance']['native_faults']) or not result['exact_files_unchanged'])


if __name__ == '__main__':
    raise SystemExit(main())
