#!/usr/bin/env python3
"""Shared Horizons authored data and exact H boundary; no gameplay claim."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'assets/creatures'))
from catalog_source import load_json
from catalog_policy import REVISION_POLICY, CAPABILITY_MASKS
from generate_data import build_tables, build_indexes, build_trial_masks, generate
from released_policy import frozen_v7, validate_compatibility
from validate_catalog import validate, validate_enabled


class HorizonsCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = load_json(ROOT / 'assets/creatures/catalog.json')
        cls.e = load_json(ROOT / 'assets/creatures/enabled.json')
        cls.lock = load_json(ROOT / 'assets/creatures/identity-lock.json')
        cls.plan = load_json(ROOT / 'docs/horizons-design/shared_horizons_plan.json')

    def test_exact_append_and_reserved_namespaces(self):
        self.assertEqual(validate(self.c, self.lock), [])
        self.assertEqual(validate_enabled(self.c, self.e), [])
        # Check the immutable revision8 whitelist independently of current9.
        p=REVISION_POLICY[8]
        e=dict(content_revision=8,enabled_form_ids=p['forms'],enabled_ability_ids=p['abilities'],enabled_evolutions=p['edges'])
        self.assertEqual(validate_enabled(self.c,e), [])
        self.assertEqual(e['enabled_form_ids'][:104], REVISION_POLICY[7]['forms'])
        self.assertEqual(e['enabled_form_ids'][104:], list(range(105, 121)))
        self.assertEqual(e['enabled_ability_ids'][:104], REVISION_POLICY[7]['abilities'])
        self.assertEqual(e['enabled_ability_ids'][104:], list(range(106, 122)))
        self.assertEqual(e['enabled_evolutions'][:64], REVISION_POLICY[7]['edges'])
        self.assertEqual(e['enabled_evolutions'][64:], [[105,106],[107,108],[109,110],[111,112]])
        forms, learns, edges, abilities, _ = build_tables(self.c, e)
        self.assertEqual(tuple(map(len, (forms, learns, edges, abilities))), (120,200,68,120))
        indexes = build_indexes(forms, abilities, edges)
        self.assertTrue(indexes[1][121])
        self.assertEqual(indexes[1][12], 0)
        self.assertFalse(any(indexes[0][121:]))
        self.assertFalse(any(indexes[1][122:]))
        self.assertEqual(len({s['family_id'] for s in self.c['slots'] if s['id'] in e['enabled_form_ids']}), 52)
        self.assertEqual(len(CAPABILITY_MASKS), 30)

    def test_every_form_and_command_matches_the_finite_plan(self):
        forms = {f['id']:f for f in self.c['forms']}
        abilities = {a['id']:a for a in self.c['abilities']}
        slots = {s['id']:s for s in self.c['slots']}
        for expected in self.plan['forms']:
            with self.subTest(form=expected['id']):
                f = forms[expected['id']]
                for key in ('name','phase','polarity','stats','stat_total','silhouette','motion'):
                    self.assertEqual(f[key], expected[key], key)
                for key in ('family_id','tier','rarity'):
                    self.assertEqual(slots[f['id']][key], expected[key], key)
                self.assertEqual(f['field_caps'], expected['field_capabilities'])
                self.assertEqual(f['signature_ability'], expected['signature_command'])
                self.assertEqual(f['learnset'], [dict(level=l['level'],ability_id=l['command']) for l in expected['learnset']])
                a = abilities[f['signature_ability']]
                self.assertEqual(a['name'], expected['ability']['name'])
                self.assertEqual(a['phase'], expected['phase'])
                self.assertEqual(a['cooldown_updates'], expected['ability']['cooldown_active_updates'])
                self.assertEqual(a['field_caps'], expected['field_capabilities'])
                self.assertEqual(a['effect'], expected['ability']['combat']+' Field: '+expected['ability']['field'])
                self.assertEqual(f['acquisition']['repeatable'], expected['tier']==1)

    def test_trials_have_exact_owner_floors_and_gate(self):
        bindings = {t['family_id']:t for t in self.c['trial_bindings'] if t['introduced_content_revision']==8}
        edges = {e['from']:e for e in self.c['evolutions']}
        self.assertEqual(set(bindings), {'F041','F042','F043','F044'})
        masks = build_trial_masks(self.c)
        for expected in self.plan['trials']:
            b = bindings[expected['family_id']]
            e = edges[expected['from_form']]
            self.assertEqual((b['local_trial_id'],b['wire_mask'],b['prerequisite_trial_mask'],b['from_form_ids']), (1,1024,0,[expected['from_form']]))
            self.assertEqual(masks[b['trial_id']], 1024)
            self.assertEqual((e['to'],e['min_level'],e['min_bond'],e['required_gate'],e['required_trial']), (expected['to_form'],34,60,'horizons_ready',b['trial_id']))
            self.assertTrue(e['player_confirm'])
            self.assertIsNone(e['consumed_item'])
            self.assertEqual(e['location'], 'sanctuary')

    def test_h_generated_rows_are_exact_prefixes(self):
        current = generate(self.c, self.e)
        self.assertEqual(current, (ROOT/'src/creature_data.c').read_text())
        old = (ROOT/'tests/fixtures/return-h-policy-oracle/src/creature_data.c').read_text()
        for name, count in [('creature_forms',104),('creature_learnsets',180),('creature_evolutions',64),('creature_abilities',104)]:
            pattern = r'const [^\n]+ '+name+r'\[[^\n]+\] = \{\n(.*?)\n\};'
            actual = re.search(pattern,current,re.S)[1].splitlines()
            expected = re.search(pattern,old,re.S)[1].splitlines()
            self.assertEqual(len(expected), count)
            self.assertEqual(actual[:count], expected, name)
        self.assertEqual(validate_compatibility(self.c,8), [])
        self.assertEqual((len(frozen_v7()['forms']),len(frozen_v7()['abilities']),len(frozen_v7()['evolutions'])), (104,104,64))

    def test_new_commands_cannot_cross_family_or_learn_level(self):
        for form, mutation in [(105,{'signature_ability':108}), (105,{'learnset':[dict(level=1,ability_id=108)]}), (106,{'learnset':[dict(level=1,ability_id=106),dict(level=33,ability_id=107)]})]:
            c = deepcopy(self.c)
            next(f for f in c['forms'] if f['id']==form).update(mutation)
            self.assertTrue(validate_enabled(c,self.e), (form,mutation))
        c = deepcopy(self.c)
        next(f for f in c['forms'] if f['id']==1)['learnset'].append(dict(level=1,ability_id=106))
        self.assertTrue(validate_enabled(c,self.e))
        for field,value in [('min_level',33),('min_bond',59),('required_gate','return_ready')]:
            c = deepcopy(self.c)
            next(e for e in c['evolutions'] if e['from']==105)[field] = value
            self.assertTrue(validate_enabled(c,self.e), field)

    def test_trial_adversaries_cannot_rebind_equal_masks(self):
        for field,value in [('family_id','F042'),('local_trial_id',2),('wire_mask',1),('introduced_content_revision',7),('prerequisite_trial_mask',1),('from_form_ids',[107])]:
            c = deepcopy(self.c)
            next(t for t in c['trial_bindings'] if t['family_id']=='F041')[field] = value
            self.assertTrue(validate_enabled(c,self.e), field)
        c = deepcopy(self.c)
        other = next(t for t in c['trial_bindings'] if t['family_id']=='F042')['trial_id']
        next(e for e in c['evolutions'] if e['from']==105)['required_trial'] = other
        self.assertTrue(validate(c,self.lock))

    def test_seven_manifest_cannot_claim_eight_content(self):
        e = deepcopy(self.e)
        e['content_revision'] = 7
        self.assertTrue(validate_enabled(self.c,e))
        for key,value in [('enabled_form_ids',121),('enabled_ability_ids',12),('enabled_ability_ids',122)]:
            e = deepcopy(self.e)
            e[key].append(value)
            self.assertTrue(validate_enabled(self.c,e), (key,value))
        for kind,id_,field,value in [('forms',101,'name','Changed Hingelet'),('forms',104,'polarity','yin'),('abilities',105,'cooldown_updates',121)]:
            c = deepcopy(self.c)
            next(r for r in c[kind] if r['id']==id_)[field] = value
            self.assertTrue(validate_compatibility(c,8), (kind,id_,field))
        c = deepcopy(self.c)
        next(e for e in c['evolutions'] if e['from']==103)['min_bond'] -= 1
        self.assertTrue(validate_compatibility(c,8))

    def test_gear_definitions_and_sources_match_plan_and_h(self):
        c = load_json(ROOT/'assets/equipment/catalog.json')
        blob = (ROOT/'assets/equipment/released-v7.json').read_bytes()
        self.assertEqual(hashlib.sha256(blob).hexdigest(), '8f0741e4b24469a7444e9bf62476b1d53d27c587df6cb98b875ef80257d853ab')
        old = json.loads(blob)
        self.assertEqual(c['items'][:42], old['items'])
        self.assertEqual(c['reward_sources'][:42], old['reward_sources'])
        self.assertEqual(len(c['items']),48)
        for actual,expected in zip(c['items'][42:46],self.plan['gear']):
            self.assertEqual((actual['id'],actual['name'],actual['slot'],actual.get('weapon_class')), (expected['item_id'],expected['name'],expected['slot'],expected['weapon_class']))
            self.assertEqual(actual['stats'], dict(zip(self.plan['bonus_order'],expected['bonuses'])))
        self.assertEqual(c['reward_sources'][42:46], [dict(source_id=g['source_id'],item_id=g['item_id']) for g in self.plan['gear']])

    def test_equipment_generator_rejects_h_mutations(self):
        path = ROOT/'assets/equipment/generate_data.py'
        spec = importlib.util.spec_from_file_location('horizons_equipment_generator',path)
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        source = load_json(generator.SOURCE)
        with tempfile.TemporaryDirectory() as tmp:
            generator.SOURCE = Path(tmp)/'catalog.json'
            for field,value in [('name','Changed Patient Ring'),('description',['Changed','Again']),('stats',dict(source['items'][41]['stats'],stagger=2))]:
                c = deepcopy(source)
                c['items'][41][field] = value
                generator.SOURCE.write_text(json.dumps(c))
                with self.assertRaisesRegex(AssertionError,'revision7 equipment definitions'):
                    generator.generate()


if __name__ == '__main__':
    unittest.main(verbosity=2)
