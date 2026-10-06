#!/usr/bin/env python3
"""Focused Japanese key, semantic and native-pixel UI checks; no game writes.

Run normally for tests, or with --previews to rebuild explicitly labelled
240x160 text mockups in docs/underwater-localization/previews/. These are not
emulator screenshots or release/controller acceptance evidence.
"""
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
FONT = ImageFont.truetype(FONT_PATH, 12, index=0)
LABEL_FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 8)
DIALOGUE = ROOT / 'assets/underwater_region/dialogue_ja.json'
UI = ROOT / 'assets/underwater_ui.json'
SOURCE = ROOT / 'assets/underwater_region/dialogue.json'
EXPECTED_SOURCE_SHA256 = '67a32a8e12bae0cfa451946c955663a8e0051259c026e7d68e04a240be8c2476'
GEAR_IDS = (6, 13, 38, 54, 68, 86)


def strict_json(path):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError(f'Duplicate key {key} in {path}')
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs)


def width(value):
    # Keep exactly in step with assets/generate_ui.py, including +1.
    return FONT.getbbox(value)[2] + 1


def all_texts():
    return {**strict_json(DIALOGUE), **strict_json(UI)}


def context_limit(key):
    if key == 'UW_PREPARING':
        return 154  # 166px pending-transaction modal, 6px padding each side
    if key.startswith('E_UW_NAME_'):
        return 96  # evolution branch card: x+(96-width)/2
    if re.fullmatch(r'UW_(?:Q\d+|TRIAL\d+)', key):
        return 156  # x14 title must end before status at x176, with 6px gap
    if key in ('UW_UNSEEN', 'UW_ACTIVE', 'UW_READY', 'UW_CLAIMED'):
        return 50  # status x176, right inset at226
    return 214


class UnderwaterLocalizationTests(unittest.TestCase):
    def test_english_source_unchanged_since_translation_review(self):
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), EXPECTED_SOURCE_SHA256,
                         'English source changed: re-review Japanese meanings before updating the pin')

    def test_reviewed_portal_and_guardian_meanings(self):
        english,japanese=strict_json(SOURCE),strict_json(DIALOGUE)
        self.assertEqual(english['UW_PORTAL_WAIT_B'],'First, tell Ressa the mountain is safe.')
        self.assertIn('「山に息を通そう」の報告',japanese['UW_PORTAL_WAIT_B'])
        self.assertIn('your weapon',english['UW_JOINT_OPEN'])
        self.assertIn('武器',japanese['UW_JOINT_OPEN'])

    def test_dialogue_key_order_and_coverage(self):
        english, japanese = strict_json(SOURCE), strict_json(DIALOGUE)
        self.assertEqual(len(english), 188)
        self.assertEqual(list(english), list(japanese))

    def test_ui_keys_exactly_cover_new_contract(self):
        expected = {f'E_UW_NAME_{n}' for n in range(49, 73)}
        expected |= {f'E_UW_CMD_{n}' for n in range(67, 91)}
        expected |= {f'E_UW_WISH_{n}' for n in range(8)}
        expected |= {'E_UW_MORE', 'E_UW_LATER', 'UW_PREPARING',
                     'UW_AIM_SIDE', 'UW_AIM_CORNER', 'UW_AIM_AXIS'}
        expected |= {f'G_{kind}{n}' for n in GEAR_IDS for kind in ('ITEM', 'DESC')}
        self.assertEqual(set(strict_json(UI)), expected)
        self.assertFalse(set(strict_json(UI)) & set(strict_json(DIALOGUE)))

    def test_native_pixel_width_and_raster_height(self):
        for key, value in all_texts().items():
            with self.subTest(key=key, text=value):
                self.assertIsInstance(value, str)
                self.assertTrue(value)
                self.assertEqual(value, value.strip())
                self.assertNotRegex(value, r'[\r\n\t]')
                self.assertRegex(value, r'[ぁ-んァ-ヶ一-龯]')
                self.assertLessEqual(width(value), context_limit(key))
                box = FONT.getbbox(value)
                self.assertGreaterEqual(box[1] - 2, 0)
                self.assertLessEqual(box[3] - 2, 15)

    def test_form_names_are_unique_and_match_family_rows(self):
        sys.path.insert(0, str(ROOT / 'assets/creatures'))
        from catalog_source import load_json
        catalog = load_json(ROOT / 'assets/creatures/catalog.json')
        forms = [f for f in catalog['forms'] if 49 <= f['id'] <= 72]
        self.assertEqual({f['id'] for f in forms}, set(range(49, 73)))
        ui = strict_json(UI)
        names = [ui[f'E_UW_NAME_{f["id"]}'] for f in forms]
        self.assertEqual(len(names), len(set(names)))
        for f in forms:
            self.assertEqual(f['signature_ability'], f['id'] + 18)
        old_names = set()
        for path in (ROOT / 'assets/creatures/ui_additions.json', ROOT / 'assets/magma_ui.json'):
            for key, value in strict_json(path).items():
                if 'NAME' in key:
                    old_names.add(value)
        self.assertFalse(old_names & set(names))

    def test_player_facing_direction_order_and_guardian_language(self):
        d, ui = strict_json(DIALOGUE), strict_json(UI)
        self.assertIn('武器', d['UW_JOINT_OPEN'])
        self.assertNotIn('剣', d['UW_JOINT_OPEN'])
        self.assertIn('左上', d['UW_TRIAL9A'])
        self.assertIn('右下', d['UW_TRIAL9A'])
        self.assertLess(d['UW_TRIAL9A'].index('左上'), d['UW_TRIAL9A'].index('右下'))
        self.assertIn('四枚', d['UW_TRIAL9B'])
        self.assertIn('×印', d['UW_TRIAL9B'])
        self.assertIn('左下', d['UW_TRIAL10A'])
        self.assertIn('五つ', d['UW_TRIAL10B'])
        self.assertIn('一周ずつ', d['UW_TRIAL13B'])
        self.assertIn('交点', d['UW_TRIAL13B'])
        self.assertIn('三つ', d['UW_TRIAL15A'])
        self.assertIn('残る角', d['UW_TRIAL15B'])
        self.assertIn('下側', d['UW_RETURN_LOOPB'])
        self.assertIn('向こう側', d['UW_FAR_HANDLE'])
        self.assertIn('ふたつ', d['UW_BASINS'])
        for key in ('UW_HEAT_ORDER', 'UW_TRIAL8A'):
            self.assertLess(d[key].index('温め'), d[key].index('回'))
        self.assertLess(d['UW_HEAT_ORDER'].index('回'), d['UW_HEAT_ORDER'].index('冷'))
        self.assertLess(d['UW_OVERLAYB'].index('響き'), d['UW_OVERLAYB'].index('重し'))
        self.assertLess(d['UW_OVERLAYB'].index('重し'), d['UW_OVERLAYB'].index('回す'))
        self.assertIn('スミツボミ', d['UW_ECHO_NEEDED'])
        self.assertEqual(ui['E_UW_NAME_49'], 'スミツボミ')
        self.assertIn('ウキガイ', d['UW_BALLAST_NEEDED'])
        self.assertEqual(ui['E_UW_NAME_52'], 'ウキガイ')
        magma = strict_json(ROOT / 'assets/magma_region/dialogue.json')
        self.assertIn(magma['MG_Q32'], d['UW_PORTAL_WAIT_B'])
        self.assertIn('報告', d['UW_PORTAL_WAIT_B'])
        for key in ('UW_AIM_SIDE', 'UW_AIM_CORNER', 'UW_AIM_AXIS'):
            self.assertTrue(ui[key].startswith('R直後'))
            self.assertEqual(ui[key].count('R'), 1)
            self.assertIn('押す', ui[key])
            self.assertNotRegex(ui[key], r'もう一度R|再びR|Rを二')
        self.assertIn('←か→', ui['UW_AIM_SIDE'])
        self.assertIn('一方向', ui['UW_AIM_CORNER'])
        self.assertIn('↑か↓', ui['UW_AIM_AXIS'])

    def test_gear_descriptions_match_actual_stat_vectors(self):
        items = {i['id']: i for i in strict_json(ROOT / 'assets/equipment/catalog.json')['items']}
        expected = {
            6: {'attack_q4': 1, 'reach_px': 3},
            13: {'defense_q4': 1, 'speed_q8_delta': -2, 'reach_px': 4},
            38: {'defense_q4': 2, 'hp_q4': 4},
            54: {'speed_q8_delta': 6, 'roll_reduction': 1},
            68: {'hp_q4': 8, 'speed_q8_delta': -2, 'power_reduction': 2},
            86: {'defense_q4': 1, 'power_reduction': 2},
        }
        ui = strict_json(UI)
        for item_id, stats in expected.items():
            with self.subTest(item_id=item_id):
                nonzero = {k: v for k, v in items[item_id]['stats'].items() if v}
                self.assertEqual(nonzero, stats)
                self.assertNotRegex(ui[f'G_DESC{item_id}'], r'酸素|息継ぎ|呼吸|通行許可')
        for item_id, bonuses in {
            6: ('攻撃+1', '間合い+3'),
            13: ('防御+1', '間合い+4', '少し遅い'),
            38: ('防御+2', '体力+0.25'),
            54: ('足取り軽く', '回避待ち-1'),
            68: ('体力+0.5', '技待ち-2', '少し遅い'),
            86: ('防御+1', '技待ち-2'),
        }.items():
            for bonus in bonuses:
                self.assertIn(bonus, ui[f'G_DESC{item_id}'])


def render_previews():
    """Draw exact glyph masks/layout boxes on a neutral, labelled mock canvas."""
    output = ROOT / 'docs/underwater-localization/previews'
    output.mkdir(parents=True, exist_ok=True)
    texts = all_texts()
    colors = {'bg': '#102530', 'border': '#508384', 'panel': '#173643',
              'cream': '#f4edce', 'gold': '#e5c97d', 'teal': '#96c8c0'}

    def base():
        image = Image.new('RGB', (240, 160), colors['bg'])
        draw = ImageDraw.Draw(image)
        draw.text((8, 3), 'LOCALIZATION PREVIEW', font=LABEL_FONT, fill=colors['gold'])
        draw.text((8, 15), 'TEXT MOCKUP / NOT EMULATOR', font=LABEL_FONT, fill=colors['teal'])
        return image

    def box(image, x, y, w, h):
        ImageDraw.Draw(image).rectangle((x, y, x+w-1, y+h-1), fill=colors['panel'], outline=colors['border'])

    def text(image, key, x=None, y=0, color='cream'):
        value = texts[key]
        mask = Image.new('1', (width(value), 15), 0)
        ImageDraw.Draw(mask).text((0, -2), value, font=FONT, fill=1, stroke_width=0)
        if x is None:
            x = (240 - mask.width) // 2
        image.paste(colors[color], (x, y), mask)

    images = []
    for stem, title, a, b, status in (
        ('01_journal', 'UW_Q40', 'UW_CLUE40A', 'UW_CLUE40B', 'UW_ACTIVE'),
        ('02_trial_direction', 'UW_TRIAL9', 'UW_TRIAL9A', 'UW_TRIAL9B', 'UW_ACTIVE'),
    ):
        im = base(); box(im, 8, 31, 224, 122)
        text(im, 'UW_JOURNAL', y=34, color='gold')
        text(im, title, 14, 54, 'gold'); text(im, status, 176, 54, 'teal')
        text(im, a, 14, 76); text(im, b, 14, 94)
        text(im, 'UW_KEYS', y=138, color='teal')
        im.save(output / f'{stem}.png'); images.append(im)

    im = base(); box(im, 5, 99, 230, 56)
    text(im, 'UW_ROOM46', 13, 103, 'gold')
    text(im, 'UW_PORTAL_WAIT_A', 13, 120); text(im, 'UW_PORTAL_WAIT_B', 13, 136)
    im.save(output / '03_portal_dialogue.png'); images.append(im)

    im = base(); box(im, 10, 37, 220, 116)
    text(im, 'E_UW_MORE', y=42, color='gold')
    for key, x in (('E_UW_NAME_53', 20), ('E_UW_NAME_54', 124)):
        box(im, x, 61, 96, 41)
        text(im, key, x+(96-width(texts[key]))//2, 63)
    text(im, 'E_UW_LATER', y=115, color='gold')
    text(im, 'E_UW_CMD_70', y=136, color='teal')
    im.save(output / '04_branch_name_slots.png'); images.append(im)

    im = base(); box(im, 37, 77, 166, 34)
    text(im, 'UW_PREPARING', y=85, color='gold')
    box(im, 8, 130, 224, 23); text(im, 'UW_AIM_SIDE', y=134, color='teal')
    im.save(output / '05_pending_and_aim.png'); images.append(im)

    im = base(); box(im, 8, 31, 224, 123)
    text(im, 'G_ITEM68', y=47, color='gold'); text(im, 'G_DESC68', y=65)
    text(im, 'G_ITEM38', y=98, color='gold'); text(im, 'G_DESC38', y=116)
    im.save(output / '06_equipment_descriptions.png'); images.append(im)

    sheet = Image.new('RGB', (3*240, 2*160), colors['bg'])
    for i, im in enumerate(images):
        sheet.paste(im, ((i % 3)*240, (i // 3)*160))
    sheet.save(output / 'localization_preview_sheet_1x.png')
    metrics = [{'key': key, 'width_px': width(value), 'limit_px': context_limit(key)}
               for key, value in texts.items()]
    (output / 'width_report.json').write_text(json.dumps({
        'kind': 'localization preview, not emulator screenshots',
        'canvas': [240, 160], 'font': FONT_PATH, 'font_px': 12,
        'dialogue_keys': len(strict_json(DIALOGUE)), 'ui_keys': len(strict_json(UI)),
        'maximum_width_px': max(row['width_px'] for row in metrics),
        'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'metrics': metrics,
    }, ensure_ascii=False, indent=2)+'\n')
    print(f'Wrote six native-size localization previews, one 1x sheet and width report to {output}')


if __name__ == '__main__':
    if '--previews' in sys.argv:
        render_previews()
    else:
        unittest.main()
