#!/usr/bin/env python3
"""Magma append-only authoring, exact policy and generation fault tests."""
from copy import deepcopy
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets/creatures'))
from catalog_policy import REVISION_POLICY, TRIAL_POLICY, TRIAL_PREREQUISITES
from validate_catalog import validate,validate_enabled,load_json
from generate_data import generate,build_tables,build_trial_masks,terminal_topology
class MagmaCatalogPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=load_json(ROOT/'assets/creatures/catalog.json');cls.e=load_json(ROOT/'assets/creatures/enabled.json');cls.lock=load_json(ROOT/'assets/creatures/identity-lock.json')
    def test_exact_current_manifest_and_generation(self):
        self.assertEqual(validate(self.c,self.lock),[]);self.assertEqual(validate_enabled(self.c,self.e),[])
        self.assertEqual(self.e['content_revision'],5)
        tables=build_tables(self.c,self.e);self.assertEqual(tuple(len(t) for t in tables[:4]),(65,102,35,65))
        self.assertEqual(generate(self.c,self.e),(ROOT/'src/creature_data.c').read_text())
        self.assertEqual(hashlib.sha256((ROOT/'assets/creatures/identity-lock.json').read_bytes()).hexdigest(),'fe553a9d963de059e7d6c0f8647ab6a3fe736c5fdf7ca8d3b18c6dedd3292969')
    def test_every_old_revision_manifest_stays_explicit(self):
        for revision,counts in [(1,(8,12,4,8)),(2,(11,16,5,11)),(3,(21,31,10,21)),(4,(41,61,20,41))]:
            policy=REVISION_POLICY[revision];e={'content_revision':revision,'enabled_form_ids':policy['forms'],'enabled_evolutions':policy['edges'],'enabled_ability_ids':policy['abilities']}
            self.assertEqual(validate_enabled(self.c,e),[])
            self.assertEqual(tuple(len(t) for t in build_tables(self.c,e)[:4]),counts)
    def test_only_reviewed_individual_polarity_flips(self):
        for id in list(range(31,49))+list(range(95,101)):
            c=deepcopy(self.c);f=next(f for f in c['forms'] if f['id']==id);f['polarity']='yang' if f['polarity']=='yin' else 'yin'
            # Flipping a base changes family inference, but unchanged evolved
            # rows (or explicit39/48 overrides) still reject that family change.
            self.assertTrue(validate_enabled(c,self.e),id)
    def test_old_semantic_relationships_cannot_change(self):
        for field,value in [('polarity','yin'),('phase','water'),('signature_ability',43),('stats',{'vitality':36,'power':36,'guard':36,'focus':36,'haste':36})]:
            c=deepcopy(self.c);f=next(f for f in c['forms'] if f['id']==1);f[field]=value;self.assertTrue(validate_enabled(c,self.e),field)
        c=deepcopy(self.c);c['evolutions'][0]['min_level']+=1;self.assertTrue(validate_enabled(c,self.e))
    def test_exact_trial_dependencies_and_wrong_family_sources(self):
        for family,key,expected in [('F011',2,3),('F012',2,3),('F013',2,2),('F016',2,2)]:
            t=next(t for t in self.c['trial_bindings'] if t['family_id']==family and t['local_trial_id']==key)
            self.assertEqual(build_trial_masks(self.c)[t['trial_id']],expected)
            c=deepcopy(self.c);m=next(m for m in c['trial_bindings'] if m['trial_id']==t['trial_id']);m['prerequisite_trial_mask']^=1;self.assertTrue(validate_enabled(c,self.e))
            c=deepcopy(self.c);m=next(m for m in c['trial_bindings'] if m['trial_id']==t['trial_id']);m['from_form_ids']=[1];self.assertTrue(validate(c,self.lock));self.assertTrue(validate_enabled(c,self.e))
    def test_full_terminal_metadata_independent_of_enablement(self):
        rows=terminal_topology();self.assertEqual(len(rows),128)
        allocation=json.loads((ROOT/'docs/magma-design/magma_allocation.json').read_text());self.assertEqual(rows,allocation['terminal_admission']['form_terminal_masks'])
        self.assertEqual(len({(r['family_id'],t) for r in rows for t in r['terminal_form_ids']}),72)
        for r in rows:
            self.assertIn(r['reachable_terminal_mask'],(1,2,3))
        self.assertEqual([r['reachable_terminal_mask'] for r in rows[36:39]],[3,1,2])
    def test_unknown_enabled_id_and_ability12_reject(self):
        for key,value in [('enabled_form_ids',121),('enabled_ability_ids',12),('enabled_evolutions',[1,3])]:
            e=deepcopy(self.e);e[key].append(value);self.assertTrue(validate_enabled(self.c,e))
    def test_generated_offset_limits_and_contiguous_branches(self):
        e=deepcopy(self.e);index=e['enabled_evolutions'].index([37,39]);e['enabled_evolutions'].insert(0,e['enabled_evolutions'].pop(index))
        with self.assertRaisesRegex(ValueError,'contiguous'):build_tables(self.c,e)
        c=deepcopy(self.c);f=next(f for f in c['forms'] if f['id']==31);f['learnset']=[{'level':1,'ability_id':43}]*9
        with self.assertRaisesRegex(ValueError,'count'):build_tables(c,self.e)
if __name__=='__main__':unittest.main(verbosity=2)
