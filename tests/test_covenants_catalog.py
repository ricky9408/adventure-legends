#!/usr/bin/env python3
"""Final current catalog contracts and preservation; no native gameplay claim."""
from copy import deepcopy
import ctypes as C
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets/creatures'))
from catalog_source import load_json
from catalog_policy import REVISION_POLICY, COVENANT_SIGNATURES, CAPABILITY_MASKS
from generate_data import build_tables, build_indexes, generate
from validate_catalog import validate, validate_enabled


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


class CovenantsCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_json(ROOT/'assets/creatures/catalog.json')
        cls.enabled=load_json(ROOT/'assets/creatures/enabled.json')
        cls.identity=load_json(ROOT/'assets/creatures/identity-lock.json')

    def test_final_finite_counts_and_distinct_command_namespaces(self):
        c,e=self.catalog,self.enabled
        self.assertEqual(validate(c,self.identity),[])
        self.assertEqual(validate_enabled(c,e),[])
        self.assertEqual((c['schema_version'],e['content_revision']),(3,9))
        f,l,v,a,layout=build_tables(c,e)
        self.assertEqual(tuple(map(len,(f,l,v,a))),(128,209,68,128))
        self.assertEqual(e['enabled_form_ids'][:120],REVISION_POLICY[8]['forms'])
        self.assertEqual(e['enabled_ability_ids'][:120],REVISION_POLICY[8]['abilities'])
        self.assertEqual(e['enabled_form_ids'][120:],list(range(121,129)))
        self.assertEqual(e['enabled_ability_ids'][120:],[12]+list(range(122,129)))
        self.assertEqual(e['enabled_evolutions'],REVISION_POLICY[8]['edges'])
        self.assertEqual(len({s['family_id'] for s in c['slots']}),60)
        self.assertEqual(len(CAPABILITY_MASKS),30)
        self.assertEqual(layout[121],(200,2,0,0))
        self.assertEqual(layout[128],(208,1,0,0))
        fi,ai,ei=build_indexes(f,a,v)
        self.assertTrue(all(fi[1:]));self.assertTrue(all(ai[1:129]))
        self.assertFalse(any(ai[129:]));self.assertFalse(any(ei[121:]))
        by_id={x['id']:x for x in f}
        self.assertEqual((by_id[120]['name'],by_id[120]['signature_ability']),('Cymbalop',121))
        self.assertEqual((by_id[121]['name'],by_id[121]['signature_ability']),('Stilltide Orrery',12))

    def test_schema2_and_stilltide_draft_are_unchanged(self):
        self.assertEqual(hashlib.sha256((ROOT/'assets/creatures/catalog.schema.json').read_bytes()).hexdigest(),
            'e3a24a701752b8a79dbab4d95d09d5f32ffd8bff2d3a5961ec51c404aba5acaf')
        f=next(f for f in self.catalog['forms'] if f['id']==121)
        self.assertEqual(digest(f),'69567e7f808054bc5f035592d492dee805905bbe62bf99bd8f8a0752350a3a20')
        a=next(a for a in self.catalog['abilities'] if a['id']==12)
        self.assertEqual(a,dict(id=12,name='Quiet Orbit',phase='water',handler='quiet_orbit',cooldown_updates=240,
            effect='Place three orbiting drops that cancel at most three projectiles over 120 updates; each saved drop becomes one counter-shot on expiry.',
            field_caps=['fill_basin','reveal_current','link_pools']))
        from test_southern_catalog import before_return
        old=before_return(self.catalog)
        self.assertEqual(old['schema_version'],2)
        self.assertEqual(validate(old,self.identity),[])
        old['legendary_gates'][0]['required_phase_count']=0
        self.assertTrue(validate(old,self.identity))

    def test_final_roster_matches_the_authored_design(self):
        expected=[
            (121,'Stilltide Orrery','water','yin',[70,45,65,95,55],['fill_basin','reveal_current','link_pools'],'Quiet Orbit',240),
            (122,'Vowbough','wood','yang',[72,60,56,74,68],['grow_roots','reel_load'],'Bending Bower',180),
            (123,'Kilnwhorl','fire','yang',[84,76,70,66,34],['store_heat','ignite'],'Banked Spiral',210),
            (124,'Cairnward','earth','yin',[86,48,90,68,38],['press_weight','shift_ballast'],'Patient Ground',200),
            (125,'Bellmantle','metal','yang',[56,78,62,70,64],['tune_latch','echo_outline'],'Answering Edge',165),
            (126,'Shadeweaver','wood','yin',[54,46,58,94,78],['unfold_screen','grow_roots'],'Open Shelter',195),
            (127,'Tideplume','water','yang',[60,66,44,82,78],['float_load','shift_ballast'],'Waiting Wake',180),
            (128,'Hearthmoth','fire','yin',[76,40,72,90,52],['store_heat','unfold_screen'],'Last Ember',240)]
        forms={f['id']:f for f in self.catalog['forms']}
        abilities={a['id']:a for a in self.catalog['abilities']}
        for id_,name,phase,polarity,stats,caps,command,cooldown in expected:
            f=forms[id_];a=abilities[COVENANT_SIGNATURES[id_]]
            self.assertEqual((f['name'],f['phase'],f['polarity'],list(f['stats'].values()),f['field_caps']),
                             (name,phase,polarity,stats,caps),id_)
            self.assertEqual((a['name'],a['phase'],a['field_caps'],a['cooldown_updates']),
                             (command,phase,caps,cooldown),id_)

    def test_all_eight_current_gate_contracts(self):
        rules=self.catalog['covenant_gates'];self.assertEqual(len(rules),8)
        self.assertEqual([r['form_id'] for r in rules],list(range(121,129)))
        for i,r in enumerate(rules):
            self.assertEqual((r['family_id'],r['area'],r['source_token']),(f'F{i+53:03d}',i+70,i+1))
            self.assertEqual((r['covenant_index'],r['receipt_index'],r['covenant_bit'],r['receipt_bit']),(22,23,1<<i,1<<i))
            self.assertEqual((r['objective_quest'],r['objective_bit'],r['requires_quest_claim']),
                (61 if i<4 else 62,1<<(i%4),60 if i<4 else 61))
            self.assertEqual((r['grant_level'],r['grant_bond'],r['grant_trial_flags']),(36,60,0))
            self.assertFalse(r['repeatable']);self.assertTrue(r['requires_confirmation'])
            self.assertTrue(set(r['required_support_commands'])<={102,104,106,108,110,112})
        self.assertEqual([r['required_phase_count'] for r in rules],[5,0,0,0,0,0,0,0])
        self.assertEqual([r['opposite_polarity_switches'] for r in rules],[2,0,0,0,0,0,0,0])
        self.assertFalse(any(b['family_id']>='F053' for b in self.catalog['trial_bindings']))

    def test_gate_mutations_reject_without_exceptions(self):
        cases=[('form_id',120),('family_id','F054'),('gate','missing'),('area',71),('source_namespace','HorizonsRequest.UNIQUE_INVITE'),
               ('source_token',2),('covenant_index',13),('receipt_index',15),('covenant_bit',3),('receipt_bit',2),
               ('objective_quest',62),('objective_bit',2),('requires_quest_claim',61),('grant_level',35),('grant_bond',59),
               ('grant_trial_flags',1),('required_support_commands',[12,122]),('required_phase_count',0),
               ('opposite_polarity_switches',0),('repeatable',True),('requires_confirmation',False)]
        for key,value in cases:
            with self.subTest(key=key):
                c=deepcopy(self.catalog);c['covenant_gates'][0][key]=value
                self.assertTrue(validate(c,self.identity))
        c=deepcopy(self.catalog);c['covenant_gates'][1]['required_phase_count']=5
        self.assertTrue(validate(c,self.identity))
        c=deepcopy(self.catalog);c['covenant_gates'][1]['min_level']=30
        self.assertTrue(validate(c,self.identity))

    def test_accepted_c_rows_and_generated_prefixes_preserved(self):
        c=self.catalog
        self.assertEqual(digest([f for f in c['forms'] if f['id']<=120]),'fd77eb542395d355cdae9d98dcaea107677c781472fdc095321972233f5597b0')
        self.assertEqual(digest([a for a in c['abilities'] if a['id']<=121]),'02049bdd048a00c09c0f73cfddfb5673d5a87f36dde333d8f0905ff398149cda')
        output=generate(c,self.enabled)
        self.assertEqual(output,(ROOT/'src/creature_data.c').read_text())
        for name,count,sha in [('creature_forms',120,'74ae92e97f7e52fa8c6faada2c77ef3dea32549cebc1778eff4125bef089fc26'),
            ('creature_learnsets',200,'b86436357dbe36e375b462a1c8e3601ff1b4cc2b4e63e68d061359069d8be7b5'),
            ('creature_evolutions',68,'0479aae983e71d63fc1ed4ced23284b75dae2524517c42c23dd65b074ef55d18'),
            ('creature_abilities',120,'02b46b42da2e9de68b4b9e3afaa9d57cf8d45fba61163d4e6de274a8b5c78d2d')]:
            block=re.search(r'const [^\n]+ '+name+r'\[[^\n]+\] = \{\n(.*?)\n\};',output,re.S)[1]
            prefix='\n'.join(block.splitlines()[:count])
            self.assertEqual(hashlib.sha256(prefix.encode()).hexdigest(),sha,name)

    def test_preservation_mutations_and_wrong_command_owners_reject(self):
        for section,id_,key,value in [('forms',120,'name','Changed Cymbalop'),('forms',121,'name','Changed Stilltide'),
            ('forms',122,'signature_ability',121),('abilities',12,'cooldown_updates',239),
            ('abilities',121,'cooldown_updates',71)]:
            c=deepcopy(self.catalog);next(x for x in c[section] if x['id']==id_)[key]=value
            self.assertTrue(validate_enabled(c,self.enabled),(section,id_,key))
        for id_,learns in [(121,[dict(level=1,ability_id=9),dict(level=29,ability_id=12)]),
                          (122,[dict(level=1,ability_id=121)])]:
            c=deepcopy(self.catalog);next(x for x in c['forms'] if x['id']==id_)['learnset']=learns
            self.assertTrue(validate_enabled(c,self.enabled),id_)
        for revision in range(1,9):
            p=REVISION_POLICY[revision]
            e=dict(content_revision=revision,enabled_form_ids=p['forms'],enabled_ability_ids=p['abilities'],enabled_evolutions=p['edges'])
            self.assertEqual(validate_enabled(self.catalog,e),[],revision)
            for key,value in [('enabled_form_ids',121),('enabled_ability_ids',12)]:
                bad=deepcopy(e);bad[key].append(value)
                self.assertTrue(validate_enabled(self.catalog,bad),(revision,key))

    def test_equipment_append_and_original_rules(self):
        c=load_json(ROOT/'assets/equipment/catalog.json')
        self.assertEqual(len(c['items']),48)
        old=dict(c,items=c['items'][:46],reward_sources=c['reward_sources'][:46])
        self.assertEqual(digest(old),'da7acb332f10967d9fbf10bf2c75b5670025c0b88d94053a35c2e2f0a3a4d62a')
        self.assertEqual(c['reward_sources'][46:],[dict(source_id=46,item_id=40),dict(source_id=47,item_id=89)])
        self.assertEqual([(x['id'],x['name'],x['slot']) for x in c['items'][46:]],[(40,'Wayfarer Coat','body'),(89,'Porchlight Ring','ring')])
        self.assertEqual([list(x['stats'].values()) for x in c['items'][46:]],[[0,1,16,-4,0,0,0,0],[0,0,0,-4,1,4,0,0]])
        spec=importlib.util.spec_from_file_location('covenants_equipment_generator',ROOT/'assets/equipment/generate_data.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertEqual(module.generate(),(ROOT/'src/equipment_data.c').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            module.SOURCE=Path(tmp)/'catalog.json'
            for index,field,value in [(42,'name','Changed Bridgegrain'),(46,'name','Changed Coat')]:
                bad=deepcopy(c);bad['items'][index][field]=value;module.SOURCE.write_text(json.dumps(bad))
                with self.assertRaises(AssertionError):module.generate()
            bad=deepcopy(c);bad['items'][47]['stats']['power_reduction']=5;module.SOURCE.write_text(json.dumps(bad))
            with self.assertRaises(AssertionError):module.generate()


class CovenantsNativeCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_creatures import build
        cls.tmp=tempfile.TemporaryDirectory(prefix='covenant-catalog-')
        cls.lib=build(cls.tmp.name)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_strict_c_catalog_and_every_final_form(self):
        lib=self.lib
        self.assertEqual(lib.creatures_catalog_validate(),1)
        for form in range(121,129):
            f=lib.creatures_form(form).contents
            self.assertEqual((f.id,f.family,f.rarity,f.tier),(form,form-68,1,1))
            self.assertEqual(sum(f.stats),330)
            self.assertEqual((f.evolution_count,lib.creatures_trial_allowed_mask(form,9)),(0,0))
            self.assertEqual(f.signature_ability,12 if form==121 else form)
            self.assertEqual(lib.creatures_command_learned(form,36,f.signature_ability),1)
        self.assertEqual(lib.creatures_command_learned(121,29,12),0)
        self.assertEqual(lib.creatures_command_learned(121,30,12),1)
        self.assertEqual(lib.creatures_command_learned(121,36,121),0)
        self.assertEqual(lib.creatures_command_learned(120,1,121),1)
        self.assertEqual(lib.creatures_command_learned(120,36,12),0)

    def test_corrupt_legendary_rom_rows_fail_closed(self):
        from test_creatures import build
        original=(ROOT/'src/creature_data.c').read_text()
        changes=[('{121, 53, 4, 0, 1, 1,','{121, 53, 4, 0, 1, 0,'),
                 ('{122, 54, 0, 1, 1, 1,','{122, 54, 0, 1, 1, 0,'),
                 ('    {30, 12},','    {29, 12},'),
                 ('    {1, 122},','    {1, 121},')]
        for i,(before,after) in enumerate(changes):
            self.assertEqual(original.count(before),1,before)
            bad=build(self.tmp.name,original.replace(before,after),tag='invalid_'+str(i))
            self.assertEqual(bad.creatures_catalog_validate(),0,before)


if __name__=='__main__':unittest.main(verbosity=2)
