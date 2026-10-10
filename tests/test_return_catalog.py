#!/usr/bin/env python3
"""Return I exact authored content, immutable relations, and bounded generation."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'assets/creatures'))
from catalog_source import CatalogError, MAX_SOURCE_BYTES, load_json
from catalog_policy import REVISION_POLICY, RETURN_FORMS, RETURN_EDGES
from generate_data import build_tables, build_trial_masks, generate
from validate_catalog import validate, validate_enabled
from released_policy import frozen_v6, validate_compatibility
FORMS = [3,6,9,12,15,17,18,21,24,27,30,101,102,103,104]
EDGES = [[2,3],[5,6],[8,9],[11,12],[14,15],[16,17],[17,18],
         [20,21],[23,24],[26,27],[29,30],[101,102],[103,104]]
SIGNATURES = list(range(91,106))
STATS = [[52, 67, 40, 76, 50], [72, 29, 64, 82, 38], [40, 42, 38, 78, 87], [80, 49, 86, 36, 34], [57, 38, 49, 84, 57], [42, 63, 52, 46, 37], [54, 74, 63, 55, 39], [57, 38, 51, 84, 55], [66, 45, 66, 78, 30], [42, 57, 38, 66, 82], [62, 70, 63, 37, 53], [33, 28, 43, 46, 30], [46, 36, 59, 64, 35], [30, 40, 26, 42, 42], [42, 53, 36, 56, 53]]
# Stat vectors copied below are asserted from the authoritative authored plan in
# the implementation check; avoid external workspace dependencies in this suite.
COOLDOWNS = [135,150,135,150,135,120,150,135,150,135,150,90,120,90,120]
GEAR = [21,39,55,69,87]
BONUSES = [[0,0,0,4,0,0,8,0],[0,3,4,-2,0,0,0,0],
           [0,0,0,4,2,0,0,0],[0,0,4,0,0,3,0,0],[0,1,0,-2,0,1,0,1]]

class ReturnCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = load_json(ROOT/'assets/creatures/catalog.json')
        cls.e = load_json(ROOT/'assets/creatures/enabled.json')
        cls.identity = load_json(ROOT/'assets/creatures/identity-lock.json')

    def test_exact_append_and_generated_counts(self):
        self.assertEqual(validate(self.c, self.identity), [])
        self.assertEqual(validate_enabled(self.c, self.e), [])
        self.assertEqual(RETURN_FORMS, FORMS)
        self.assertEqual(RETURN_EDGES, EDGES)
        self.assertEqual(self.e['content_revision'], 9)
        self.assertEqual(self.e['enabled_form_ids'][89:104], FORMS)
        self.assertEqual(self.e['enabled_evolutions'][51:64], EDGES)
        self.assertEqual(self.e['enabled_ability_ids'][89:104], SIGNATURES)
        self.assertEqual(tuple(len(x) for x in build_tables(self.c, self.e)[:4]), (128,209,68,128))
        self.assertEqual(generate(self.c,self.e), (ROOT/'src/creature_data.c').read_text())
        self.assertNotIn(12,REVISION_POLICY[7]['abilities'])
        self.assertFalse(set(range(121,129)) & set(REVISION_POLICY[7]['forms']))

    def test_all_prior_revision_manifests_stay_usable(self):
        counts = [(8,12,4,8),(11,16,5,11),(21,31,10,21),(41,61,20,41),
                  (65,102,35,65),(89,142,51,89),(104,180,64,104),(120,200,68,120)]
        for rev,expected in enumerate(counts,1):
            p = REVISION_POLICY[rev]
            e = dict(content_revision=rev, enabled_form_ids=p['forms'],
                     enabled_evolutions=p['edges'], enabled_ability_ids=p['abilities'])
            self.assertEqual(validate_enabled(self.c,e), [], rev)
            self.assertEqual(tuple(len(x) for x in build_tables(self.c,e)[:4]), expected)

    def test_form_names_stats_and_command_inheritance(self):
        f = {x['id']:x for x in self.c['forms']}
        a = {x['id']:x for x in self.c['abilities']}
        for i,id_ in enumerate(FORMS):
            self.assertEqual(list(f[id_]['stats'].values()), STATS[i],id_)
            self.assertEqual(f[id_]['signature_ability'], SIGNATURES[i])
            self.assertEqual(a[SIGNATURES[i]]['cooldown_updates'], COOLDOWNS[i])
            self.assertEqual(a[SIGNATURES[i]]['field_caps'], f[id_]['field_caps'])
        for source,target in EDGES:
            self.assertEqual(f[target]['learnset'][:-1], f[source]['learnset'])
            self.assertEqual(f[target]['learnset'][-1]['level'],28 if target in (17,102,104) else 32)
        for id_ in [101,103]:
            self.assertEqual(f[id_]['learnset'],[dict(level=1,ability_id=f[id_]['signature_ability'])])
            self.assertTrue(f[id_]['acquisition']['repeatable'])

    def test_trials_are_family_and_stage_qualified(self):
        added = [t for t in self.c['trial_bindings'] if t['introduced_content_revision']==7]
        self.assertEqual(len(added),13)
        masks = build_trial_masks(self.c)
        expected = [(1,2,1024,1,2),(2,2,1024,2,5),(3,2,1024,4,8),
                    (4,2,1024,8,11),(5,2,1024,16,14),(6,1,1024,0,16),
                    (6,2,2048,1024,17),(7,2,1024,32,20),(8,2,1024,64,23),
                    (9,2,1024,1,26),(10,2,1024,1,29),(39,1,1024,0,101),(40,1,1024,0,103)]
        self.assertEqual([(int(t['family_id'][1:]),t['local_trial_id'],t['wire_mask'],
                           t['prerequisite_trial_mask'],t['from_form_ids'][0]) for t in added],expected)
        for t in added:
            self.assertEqual(masks[t['trial_id']],t['wire_mask']|t['prerequisite_trial_mask'])
            for field,value in [('family_id','F060'),('wire_mask',4),
                                ('from_form_ids',[1]),('prerequisite_trial_mask',0),
                                ('introduced_content_revision',8)]:
                if t[field]==value:continue
                c=deepcopy(self.c)
                next(x for x in c['trial_bindings'] if x['trial_id']==t['trial_id'])[field]=value
                self.assertTrue(validate_enabled(c,self.e),(t['trial_id'],field))

    def test_released6_relations_immutable(self):
        old=frozen_v6()
        self.assertEqual((len(old['forms']),len(old['abilities']),len(old['evolutions'])),(89,89,51))
        self.assertEqual(validate_compatibility(self.c,7),[])
        for kind,id_,field,value in [('forms',49,'name','Changed name'),
                                    ('forms',49,'polarity','yang'),
                                    ('abilities',90,'cooldown_updates',121)]:
            c=deepcopy(self.c)
            next(x for x in c[kind] if x['id']==id_)[field]=value
            self.assertTrue(validate_compatibility(c,7),(kind,field))
        c=deepcopy(self.c)
        next(x for x in c['evolutions'] if x['from']==70)['min_level']+=1
        self.assertTrue(validate_compatibility(c,7))

    def test_sources_and_generated_text_are_below75000(self):
        self.assertEqual(MAX_SOURCE_BYTES,75000)
        descriptor=json.loads((ROOT/'assets/creatures/catalog.json').read_text())
        paths=[ROOT/'assets/creatures/catalog.json']
        paths += [ROOT/'assets/creatures'/name for chunk in descriptor['sections'].values() for name in chunk]
        paths += [ROOT/'src/creature_data.c',ROOT/'src/equipment_data.c',
                  ROOT/'assets/history/released-creature-relations-v6.json']
        for p in paths:self.assertLess(p.stat().st_size,75000,p)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'catalog.json').write_text('{"$catalog_source":1,"sections":{"forms":["large.json"]}}')
            (p/'large.json').write_text('[]'+' '*74998)
            with self.assertRaises(CatalogError):load_json(p/'catalog.json')

    def test_equipment_appends_exact_sources_and_bonuses(self):
        c=json.loads((ROOT/'assets/equipment/catalog.json').read_text())
        old=json.loads((ROOT/'assets/equipment/released-v6.json').read_text())
        self.assertEqual(c['items'][:37],old['items'])
        self.assertEqual(c['reward_sources'][:37],old['reward_sources'])
        self.assertEqual([x['id'] for x in c['items'][37:42]],GEAR)
        self.assertEqual([list(x['stats'].values()) for x in c['items'][37:42]],BONUSES)
        self.assertEqual(c['reward_sources'][37:42],[dict(source_id=i,item_id=id_) for i,id_ in enumerate(GEAR,37)])
        path=ROOT/'assets/equipment/generate_data.py'
        spec=importlib.util.spec_from_file_location('return_equipment_generator',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertEqual(module.generate(),(ROOT/'src/equipment_data.c').read_text())
        self.assertEqual(len(c['items']),48)

if __name__=='__main__':unittest.main(verbosity=2)
