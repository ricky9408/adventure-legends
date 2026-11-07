#!/usr/bin/env python3
"""Current authored and generated player copy must describe available actions."""
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REMOVED = re.compile(r'回避|\b(?:dodge|roll)\b', re.IGNORECASE)


def load(path):
    return json.loads((ROOT / path).read_text())


class CurrentActionCopy(unittest.TestCase):
    def assert_current(self, strings):
        for text in strings:
            self.assertIsNone(REMOVED.search(text), text)

    def test_authored_tutorial_matches_live_copy(self):
        campaign = load('assets/campaign_dialogue.json')
        lines = [line for scene in campaign['dialogue'].values()
                 for page in scene['pages'] for line in page]
        self.assert_current(lines + list(campaign['labels'].values()))
        garden = load('assets/region/ui_additions.json')
        self.assert_current(garden.values())
        self.assertEqual(garden['RG_GARDEN_A'], '西、中央、東。葉を順に踏もう。')
        live = load('assets/ui_texts.json')
        self.assertEqual(campaign['labels']['CONTROL_DODGE'], live['C_CONTROL_DODGE'])
        for name in ('RG_GARDEN_A', 'RG_GARDEN_B'):
            self.assertEqual(garden[name], live[name])

    def test_generated_ui_corpus(self):
        for path in (ROOT / 'assets').glob('ui_texts*.json'):
            self.assert_current(json.loads(path.read_text()).values())

    def test_ui_generator_before_and_after_overrides(self):
        # Exercise the real source merge without writing over build inputs.
        path = ROOT / 'assets/generate_ui.py'
        source = path.read_text().split('items=[]', 1)[0]
        sys.path.insert(0, str(ROOT / 'assets'))
        try:
            context = {'__file__': str(path)}
            exec(compile(source, str(path), 'exec'), context)
        finally:
            sys.path.pop(0)
        self.assert_current(context['texts'].values())

    def test_shop_recovery_copy(self):
        labels = load('assets/regional_shop_labels.json')
        self.assert_current(spec['text'] for spec in labels.values())
        self.assertEqual(labels['EFFECT_4']['text'], '歩み 約＋１.９％　技待 約０.０２秒短縮')
        metrics = load('assets/regional_shop_text_metrics.json')
        for name, spec in labels.items():
            self.assertEqual(spec['text'], metrics[name]['text'])

    def test_equipment_current_overlay_and_generation(self):
        path = ROOT / 'assets/equipment/generate_data.py'
        spec = importlib.util.spec_from_file_location('current_equipment_generator', path)
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        result = generator.generate()
        self.assertEqual(result, (ROOT / 'src/equipment_data.c').read_text())
        self.assert_current(re.findall(r'"([^"\n]*)"', result))
        descriptions = load('assets/equipment/player_descriptions.json')
        catalog = load('assets/equipment/catalog.json')
        for item in catalog['items']:
            self.assert_current(descriptions.get(str(item['id']), item['description']))
        self.assertEqual(descriptions['89'][0], 'Power wait -5.')
        # The runtime combines both persisted recovery bonuses; no save stat changes.
        runtime = (ROOT / 'src/gear_runtime.c').read_text()
        self.assertIn('(EQUIPMENT_BASE_POWER_COOLDOWN-stats->power_cooldown)+(EQUIPMENT_BASE_ROLL_COOLDOWN-stats->roll_cooldown)', runtime)

    def test_equipment_overlay_rejects_malformed_pairs(self):
        path = ROOT / 'assets/equipment/generate_data.py'
        spec = importlib.util.spec_from_file_location('equipment_negative_copy', path)
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        original = Path.read_text
        overlay = ROOT / 'assets/equipment/player_descriptions.json'
        for bad in ({'50': 'ab'}, {'50': [1, 2]}, {'50': ['one']},
                    {'50': ['one', 'two', 'three']}, {'999': ['one', 'two']}):
            def read(candidate, *args, **kwargs):
                return json.dumps(bad) if candidate == overlay else original(candidate, *args, **kwargs)
            with self.subTest(bad=bad), patch.object(Path, 'read_text', read):
                with self.assertRaises(AssertionError):
                    generator.generate()

    def test_guard_rejects_removed_action_spellings(self):
        for text in ('SELECT 回避', 'Try a dodge.', 'Roll cooldown -3.', 'next roll'):
            self.assertIsNotNone(REMOVED.search(text))
        self.assertIsNone(REMOVED.search('credits scroll automatically'))


if __name__ == '__main__':
    unittest.main()
