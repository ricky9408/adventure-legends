#!/usr/bin/env python3
"""Authoring/generator tests only; not native acquisition, art or battle acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets/creatures'))
from validate_catalog import load_json, validate, validate_enabled
from generate_data import build_tables, build_indexes, generate
from catalog_policy import (REVISION_POLICY, SOUTHERN_FORMS, SOUTHERN_EDGES,
                            CAPABILITY_MASKS, TRIAL_POLICY)

DATA=load_json(ROOT/'assets/creatures/catalog.json')
ENABLED=load_json(ROOT/'assets/creatures/enabled.json')
IDENTITY=load_json(ROOT/'assets/creatures/identity-lock.json')
OLD_GATES=['bell_foundry_reopened','core_clear','ending_seen','five_phase_shrines','grove_clear','new_game','north_bearing_ready','north_counterworks_stable','north_harbor_ready','north_kiln_ready','north_lines_ready','north_markers_ready','north_tender_ready','reed_basin_restored','sky_clear','stilltide_covenant']
OLD_TRIALS=['balanced_reach','compass_round','dry_ledger','fragile_cargo','join_two_pools','mend_wind_loom','raise_amber_arch','restore_canopy','restore_hearth','stilltide_covenant','tension_roof']

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def archive():
    """Reconstruct immutable r3 source without depending on a sibling checkout."""
    c=copy.deepcopy(DATA);c['schema_version']=1;c['limits']['max_ability_id']=63
    c['field_capabilities']=c['field_capabilities'][:-1];del c['trial_bindings']
    for s in c['slots']:
        if s['id'] in SOUTHERN_FORMS:s['status']='reserved'
    c['forms']=[f for f in c['forms'] if f['id'] not in SOUTHERN_FORMS]
    c['abilities']=[a for a in c['abilities'] if a['id']<23]
    c['evolutions']=[e for e in c['evolutions'] if e['from'] not in SOUTHERN_FORMS]
    c['gates']=[g for g in c['gates'] if g['id'] in OLD_GATES]
    c['trials']=[t for t in c['trials'] if t['id'] in OLD_TRIALS]
    return c

def manifest(revision):
    p=REVISION_POLICY[revision]
    return {'content_revision':revision,'enabled_form_ids':copy.deepcopy(p['forms']),
            'enabled_ability_ids':copy.deepcopy(p['abilities']),
            'enabled_evolutions':copy.deepcopy(p['edges'])}

def branch_fixture():
    """Design-only reserved F013 fixture; never added to actual enabled rows."""
    c=copy.deepcopy(DATA)
    for id_,template_id,ability in [(37,25,43),(38,26,44),(39,26,45)]:
        f=copy.deepcopy(next(x for x in c['forms'] if x['id']==template_id))
        f.update(id=id_,name=f'Test branch {id_}',signature_ability=ability)
        f['silhouette']+=f' Test-only distinct form {id_}.'
        f['learnset']=[{'level':1,'ability_id':43}]+([] if id_==37 else [{'level':20,'ability_id':ability}])
        c['forms'].append(f)
        a=copy.deepcopy(c['abilities'][-1]);a.update(id=ability,name=f'Test command {ability}',handler=f'test_branch_{ability}',phase='wood',field_caps=f['field_caps']);c['abilities'].append(a)
        next(s for s in c['slots'] if s['id']==id_)['status']='proposed'
    for target,mask in ((38,1),(39,2)):
        trial=f'test_branch_{target}'
        e=copy.deepcopy(next(x for x in c['evolutions'] if x['from']==25));e.update({'from':37,'to':target,'required_trial':trial});c['evolutions'].append(e)
        c['trials'].append({'id':trial,'description':'Synthetic branch-specific trial, not enabled content.'})
        c['trial_bindings'].append({'trial_id':trial,'family_id':'F013','local_trial_id':mask,'wire_mask':mask,'introduced_content_revision':5,'prerequisite_trial_mask':0,'from_form_ids':[37]})
    for key in ('forms','abilities','trials'):c[key].sort(key=lambda x:x['id'])
    c['trial_bindings'].sort(key=lambda x:(x['family_id'],x['local_trial_id']))
    m={'enabled_form_ids':[37,38,39],'enabled_ability_ids':[43,44,45],'enabled_evolutions':[[37,38],[37,39]],'content_revision':4}
    return c,m

class SouthernAuthoringTests(unittest.TestCase):
    def assert_invalid(self,c,text=None):
        errors=validate(c,IDENTITY)
        self.assertTrue(errors,'damaged catalog was accepted')
        if text:self.assertIn(text,'\n'.join(errors))

    def test_reviewed_current_catalog(self):
        self.assertEqual([],validate(DATA,IDENTITY));self.assertEqual([],validate_enabled(DATA,ENABLED))
        self.assertEqual(42,len(DATA['forms']));self.assertEqual(41,len(ENABLED['enabled_form_ids']))
        self.assertEqual([121],sorted({f['id'] for f in DATA['forms']}-set(ENABLED['enabled_form_ids'])))
        self.assertNotIn(12,ENABLED['enabled_ability_ids'])

    def test_identity_and_schema1_byte_pins(self):
        self.assertEqual('fe553a9d963de059e7d6c0f8647ab6a3fe736c5fdf7ca8d3b18c6dedd3292969',hashlib.sha256((ROOT/'assets/creatures/identity-lock.json').read_bytes()).hexdigest())
        self.assertEqual('904846498906733d7ef8d3f7c1a60f0f419d3c52ba96d79d21be0ebb35a25781',hashlib.sha256((ROOT/'assets/creatures/catalog.v1.schema.json').read_bytes()).hexdigest())
        for key in ('id','key','family_id','tier','rarity'):
            self.assertEqual([s[key] for s in IDENTITY['slots']],[s[key] for s in DATA['slots']])

    def test_all_older_authored_rows_unchanged(self):
        c=archive()
        expected={'forms':'4dcc92debeb9bf5dc771f25feb8e7bf79cab279844032eba65b610f34857e8b5','abilities':'c49d9b2cef7a32b6fbaef106eb72f050068d283fc78205b332eb7f6a0cf87b8d','evolutions':'89727313b71bf51eff56a98202b8ae4edc2acc5a73516894e2aaecf2c99d6f6a','trials':'e2ae6e4bfd52057a8342bb18d0efb0e6c99f95a7d95d8e9c631d981bf0f09be3','gates':'b64b7481f68eff1f44c98e384e3b6981a0c137f84b4dd553b930025b312190e2'}
        for key,sha in expected.items():self.assertEqual(sha,digest(c[key]),key)
        self.assertEqual('00bc34ed8494cede6944a4191221f8652b9e8d04ae5e9958a7d3c5e674ce68e8',digest(c))

    def test_archive_schema_and_generation(self):
        c=archive();m=manifest(3)
        self.assertEqual([],validate(c,IDENTITY));self.assertEqual([],validate_enabled(c,m))
        old=generate(c,m);new=generate()
        for name,count,sha in [('creature_forms',21,'f3947892166ca17dbd0d4acf495d51c6e1f8a1affcf5ec08927f700b6b9ddfde'),('creature_learnsets',31,'1d2a9568df1b315af1c2b76e81f4e94bfbe1276b92835cd28adb1f2db8f84e1a'),('creature_evolutions',10,'abe7fce05555a1ad9f2872aa04501d01468faf18708b64612337bfd141b60ade'),('creature_abilities',21,'42497047eae3a86fe56e6244b41e4c759bb456f008e1a5cd2b9cfa95a5653a91')]:
            pattern=r'const [^\n]+ '+name+r'\[[^\n]+\] = \{\n(.*?)\n\};'
            rows=re.search(pattern,new,re.S).group(1).splitlines()
            block='\n'.join(rows[:count])+'\n'
            self.assertEqual(sha,hashlib.sha256(block.encode()).hexdigest())
            self.assertEqual(block,re.search(pattern,old,re.S).group(1)+'\n')

    def test_schema2_ceiling_is_not_runtime_enablement(self):
        for id_ in (64,128,255):
            c=copy.deepcopy(DATA)
            a=next(a for a in c['abilities'] if a['id']==12);a['id']=id_;c['abilities'].sort(key=lambda a:a['id'])
            f=next(f for f in c['forms'] if f['id']==121);f['signature_ability']=id_
            for command in f['learnset']:
                if command['ability_id']==12:command['ability_id']=id_
            f['learnset'].sort(key=lambda x:(x['level'],x['ability_id']))
            self.assertEqual([],validate(c,IDENTITY))
            m=copy.deepcopy(ENABLED);m['enabled_ability_ids'].append(id_)
            self.assertTrue(validate_enabled(c,m))
        c=copy.deepcopy(DATA);c['abilities'][-1]['id']=256;self.assert_invalid(c)
        c=archive();c['abilities'][-1]['id']=64;self.assert_invalid(c)

    def test_exact_enabled_revision_and_order(self):
        for revision in (0,5,True,4.0):
            m=copy.deepcopy(ENABLED);m['content_revision']=revision;self.assertTrue(validate_enabled(DATA,m))
        for key in ('enabled_form_ids','enabled_ability_ids','enabled_evolutions'):
            m=copy.deepcopy(ENABLED);m[key][0],m[key][1]=m[key][1],m[key][0];self.assertTrue(validate_enabled(DATA,m))
        for value in (12,43,64,255):
            m=copy.deepcopy(ENABLED);m['enabled_ability_ids'].append(value);self.assertTrue(validate_enabled(DATA,m))
        for value in (27,30,37,121,128):
            m=copy.deepcopy(ENABLED);m['enabled_form_ids'].append(value);self.assertTrue(validate_enabled(DATA,m))

    def test_capability_projection_is_append_only(self):
        self.assertEqual(0x02000000,CAPABILITY_MASKS['refract_beam'])
        self.assertEqual(26,len(DATA['field_capabilities']))
        c=copy.deepcopy(DATA);c['field_capabilities'][-2:]=reversed(c['field_capabilities'][-2:]);self.assert_invalid(c)

    def test_new_form_contract_and_offsets(self):
        f,l,e,a,layout=build_tables(DATA,ENABLED)
        self.assertEqual((41,61,20,41),(len(f),len(l),len(e),len(a)))
        self.assertEqual(REVISION_POLICY[3]['forms']+SOUTHERN_FORMS,[x['id'] for x in f])
        self.assertEqual(sorted(x['id'] for x in DATA['forms']),[x['id'] for x in DATA['forms']])
        for pair,(base,evolved) in enumerate(SOUTHERN_EDGES):
            self.assertEqual((31+3*pair,1,10+pair,1),layout[base])
            self.assertEqual((32+3*pair,2,0,0),layout[evolved])
            edge=e[10+pair]
            self.assertEqual('south_ready',edge['required_gate'])
            self.assertEqual((20,40) if pair in (0,2,5) else (24,45) if pair in (6,8) else (22,45),(edge['min_level'],edge['min_bond']))
            for id_,total in ((base,180),(evolved,240)):
                row=next(x for x in f if x['id']==id_);self.assertEqual(total,sum(row['stats'].values()))
                self.assertEqual('ordinary',next(s for s in DATA['slots'] if s['id']==id_)['rarity'])

    def test_trial_bindings_preserve_legacy_masks(self):
        for t in DATA['trial_bindings']:
            p=TRIAL_POLICY[t['trial_id']]
            self.assertEqual((p[0],p[1],p[2]),(t['family_id'],t['local_trial_id'],t['wire_mask']))
            if p[3]==4:self.assertEqual((1,1),(t['local_trial_id'],t['wire_mask']))
        self.assertNotIn('F006',[t['family_id'] for t in DATA['trial_bindings']])

    def test_trial_wire_and_local_key_adversaries(self):
        for field,value in [('local_trial_id',0),('local_trial_id',17),('local_trial_id',65537),('local_trial_id',True),('wire_mask',0),('wire_mask',3),('wire_mask',65536),('wire_mask',65537)]:
            c=copy.deepcopy(DATA);c['trial_bindings'][0][field]=value;self.assert_invalid(c)
        c=copy.deepcopy(DATA);c['trial_bindings'].insert(1,copy.deepcopy(c['trial_bindings'][0]));self.assert_invalid(c,'duplicate')
        c=copy.deepcopy(DATA);c['trial_bindings'][0]['family_id']='F010';self.assert_invalid(c,'family')
        c=copy.deepcopy(DATA);c['trial_bindings'][0]['prerequisite_trial_mask']=1;self.assert_invalid(c,'self prerequisite')
        c=copy.deepcopy(DATA);c['trial_bindings'][0]['prerequisite_trial_mask']=2;self.assert_invalid(c,'unknown prerequisite')
        c=copy.deepcopy(DATA);t=next(t for t in c['trial_bindings'] if t['family_id']=='F009');t['wire_mask']=2
        self.assertEqual([],validate(c,IDENTITY));self.assertTrue(validate_enabled(c,ENABLED))

    def test_wrong_family_even_with_equal_trial_mask(self):
        c=copy.deepcopy(DATA);e=next(e for e in c['evolutions'] if e['from']==25);e['required_trial']='south_drainage_branches'
        self.assert_invalid(c,'trial source/family mismatch')

    def test_inheritance_and_graph_adversaries(self):
        c=copy.deepcopy(DATA);next(f for f in c['forms'] if f['id']==26)['field_caps']=[];self.assert_invalid(c,'loses field capability')
        c=copy.deepcopy(DATA);next(f for f in c['forms'] if f['id']==26)['learnset'][0]['level']=2;self.assert_invalid(c,'delays inherited command')
        for target in (25,28,29,121):
            c=copy.deepcopy(DATA);next(e for e in c['evolutions'] if e['from']==25)['to']=target;self.assert_invalid(c)
        c=copy.deepcopy(DATA);c['evolutions'].append(copy.deepcopy(c['evolutions'][-1]));self.assert_invalid(c,'duplicate edge')

    def test_reviewed_branch_authoring_and_multi_edge_offsets(self):
        c,m=branch_fixture();self.assertEqual([],validate(c,IDENTITY));self.assertTrue(validate_enabled(c,m))
        forms,learns,edges,abilities,layout=build_tables(c,m)
        self.assertEqual((0,1,0,2),layout[37]);self.assertEqual((1,2,0,0),layout[38]);self.assertEqual((3,2,0,0),layout[39])
        self.assertEqual([[37,38],[37,39]],[[e['from'],e['to']] for e in edges])
        self.assertNotIn(37,ENABLED['enabled_form_ids'])

    def test_branch_duplicate_keys_masks_merge_and_cycle_fail(self):
        c,_=branch_fixture();ts=[t for t in c['trial_bindings'] if t['family_id']=='F013'];ts[1]['local_trial_id']=1;self.assert_invalid(c,'duplicate same-family local key')
        c,_=branch_fixture();ts=[t for t in c['trial_bindings'] if t['family_id']=='F013'];ts[1]['wire_mask']=1;self.assert_invalid(c,'duplicate same-family wire mask')
        c,_=branch_fixture();ts=[t for t in c['trial_bindings'] if t['family_id']=='F013'];ts[0]['prerequisite_trial_mask']=2;ts[1]['prerequisite_trial_mask']=1;self.assert_invalid(c,'cycle detected')
        c,_=branch_fixture();c['evolutions'][-1]['to']=38;self.assert_invalid(c,'merging branches')
        c,_=branch_fixture();c['evolutions'][-1]['to']=37;self.assert_invalid(c,'cycle detected')

    def test_table_bounds_and_contiguous_edges(self):
        c,m=branch_fixture();m['enabled_form_ids']=[37,38,39,25,26];m['enabled_evolutions']=[[37,38],[25,26],[37,39]]
        with self.assertRaisesRegex(ValueError,'contiguous'):build_tables(c,m)
        c=copy.deepcopy(DATA);c['forms'][0]['learnset']*=9
        with self.assertRaisesRegex(ValueError,'count'):build_tables(c,ENABLED)
        c=copy.deepcopy(DATA);c['forms'][0]['learnset'][0]['ability_id']=256
        with self.assertRaisesRegex(ValueError,'byte'):build_tables(c,ENABLED)
        m=copy.deepcopy(ENABLED);m['enabled_form_ids'].append(1)
        with self.assertRaisesRegex(ValueError,'duplicate'):build_tables(DATA,m)

    def test_rom_indexes_are_complete_row_plus_one_maps(self):
        forms,_,edges,abilities,_=build_tables(DATA,ENABLED)
        fi,ai,ei=build_indexes(forms,abilities,edges)
        self.assertEqual((129,256,129),(len(fi),len(ai),len(ei)))
        expected_forms={f['id']:i+1 for i,f in enumerate(forms)}
        expected_abilities={a['id']:i+1 for i,a in enumerate(abilities)}
        expected_incoming={e['to']:i+1 for i,e in enumerate(edges)}
        for id_ in range(129):
            self.assertEqual(expected_forms.get(id_,0),fi[id_])
            self.assertEqual(expected_incoming.get(id_,0),ei[id_])
        for id_ in range(256):self.assertEqual(expected_abilities.get(id_,0),ai[id_])
        for id_ in (0,12,43,64,128,255):self.assertEqual(0,ai[id_])
        for id_ in (0,3,27,30,37,121,128):self.assertEqual((0,0),(fi[id_],ei[id_]))
        for name,expected in [('creature_form_index',fi),('creature_ability_index',ai),('creature_incoming_evolution_index',ei)]:
            contents=re.search(r'const CreatureU8 '+name+r'\[[^\n]+\] = \{\n(.*?)\n\};',generate(),re.S).group(1)
            self.assertEqual(expected,[int(value) for value in re.findall(r'\d+',contents)])

    def test_rom_index_byte_boundary_and_reordered_rows(self):
        forms=[{'id':128},{'id':1}];abilities=[{'id':i} for i in range(1,256)]
        fi,ai,ei=build_indexes(forms,abilities,[{'from':128,'to':1}])
        self.assertEqual((1,2),(fi[128],fi[1]));self.assertEqual((1,255),(ai[1],ai[255]));self.assertEqual(1,ei[1])
        fi,ai,ei=build_indexes(list(reversed(forms)),list(reversed(abilities)),[])
        self.assertEqual((2,1),(fi[128],fi[1]));self.assertEqual((255,1),(ai[1],ai[255]));self.assertFalse(any(ei))
        c,m=branch_fixture();f,_,e,a,_=build_tables(c,m);fi,ai,ei=build_indexes(f,a,e)
        self.assertEqual((0,1,2),(ei[37],ei[38],ei[39]))

    def test_rom_index_bad_ids_counts_and_endpoints_fail_closed(self):
        for value in (-1,0,129,256,65537,True,1.0):
            with self.subTest(kind='form',value=value):
                with self.assertRaisesRegex(ValueError,'bounds'):build_indexes([{'id':value}],[],[])
        for value in (-1,0,256,65537,True,1.0):
            with self.subTest(kind='ability',value=value):
                with self.assertRaisesRegex(ValueError,'bounds'):build_indexes([], [{'id':value}],[])
        for key in ('from','to'):
            for value in (-1,0,129,65537,True,1.0):
                e={'from':1,'to':2};e[key]=value
                with self.subTest(kind=key,value=value):
                    with self.assertRaisesRegex(ValueError,'bounds'):build_indexes([{'id':1},{'id':2}],[],[e])
        for table in ('forms','abilities','evolutions'):
            f=[{'id':1}];a=[];e=[]
            if table=='forms':f=[{'id':1}]*256
            elif table=='abilities':a=[{'id':1}]*256
            else:e=[{'from':1,'to':1}]*256
            with self.assertRaisesRegex(ValueError,'count exceeds u8'):build_indexes(f,a,e)
        with self.assertRaisesRegex(ValueError,'duplicate'):build_indexes([{'id':1},{'id':1}],[],[])
        with self.assertRaisesRegex(ValueError,'duplicate'):build_indexes([], [{'id':255},{'id':255}],[])
        with self.assertRaisesRegex(ValueError,'duplicate'):build_indexes([{'id':1},{'id':2},{'id':3}],[],[{'from':1,'to':3},{'from':2,'to':3}])
        with self.assertRaisesRegex(ValueError,'disabled endpoint'):build_indexes([{'id':1}],[],[{'from':1,'to':2}])
        with self.assertRaisesRegex(ValueError,'disabled endpoint'):build_indexes([{'id':2}],[],[{'from':1,'to':2}])

    def test_catalog_edge_order_does_not_change_manifest_table_order(self):
        c=copy.deepcopy(DATA);c['evolutions'].reverse()
        self.assertEqual([],validate(c,IDENTITY));self.assertEqual([],validate_enabled(c,ENABLED))
        self.assertEqual(generate(),generate(c,ENABLED))

    def test_checked_in_generator_is_deterministic(self):
        self.assertEqual((ROOT/'src/creature_data.c').read_text(),generate())
        self.assertEqual(generate(),generate())

if __name__=='__main__':unittest.main(verbosity=2)
