#!/usr/bin/env python3
"""Revision6 core acceptance and exact immutable revision5 differential.

Host-only synthetic fixtures do not establish native acquisition or delivery.
"""
import ctypes as C
import hashlib,json,os,random,shlex,subprocess,sys,tempfile,unittest
from pathlib import Path
from test_creatures import ROOT,Instance,Roster,Form,build,U8
from test_magma_creature_core import configure,Learn,Ability
from test_southern_creature_core import historical_prefix_bytes
from test_southern_catalog import before_return
sys.path.insert(0,str(ROOT/'assets/creatures'))
from catalog_source import load_catalog,load_json,CatalogError
from catalog_policy import REVISION_POLICY,CAPABILITY_MASKS
from generate_data import generate,build_tables
from validate_catalog import validate,validate_enabled
from released_policy import validate_compatibility
OLD_SOURCE=ROOT/'tests/fixtures/magma-policy-oracle/src'
V5=json.loads((ROOT/'assets/history/creatures-v5.json').read_text())
LOOKUP={p['id']:p for p in V5['forms']}
NEW=json.loads((ROOT/'docs/underwater-design/creature_forms.json').read_text())

def compile_native(sanitize=False,harness='underwater_creature_native.c'):
    with tempfile.TemporaryDirectory(prefix='uw-native-') as d:
        out=Path(d)/'test';cmd=shlex.split(os.environ.get('HOST_CC','cc'))+['-std=c99','-O1' if sanitize else '-O2','-Wall','-Wextra','-Werror','-pedantic','-I'+str(ROOT/'src')]
        if sanitize:cmd+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie']
        subprocess.run(cmd+[str(ROOT/'src/creatures.c'),str(ROOT/'src/creature_data.c'),str(ROOT/'tests'/harness),'-o',str(out)],check=True)
        subprocess.run([str(out)],check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'))

class UnderwaterCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='uw-core-');cls.addClassCleanup(cls.tmp.cleanup)
        cls.lib=configure(build(cls.tmp.name))
        # Full final-Magma source snapshot is separately pinned by Save5 oracle tests.
        for name in ['creatures.c','creatures.h','creature_data.c']:
            expected=V5['source_sha256']['src/'+name]
            if hashlib.sha256((OLD_SOURCE/name).read_bytes()).hexdigest()!=expected:raise AssertionError('Magma baseline changed: '+name)
        out=Path(cls.tmp.name)/'oracle.so'
        subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC','-I'+str(OLD_SOURCE),str(OLD_SOURCE/'creatures.c'),str(OLD_SOURCE/'creature_data.c'),'-o',str(out)],check=True)
        cls.old=configure(C.CDLL(str(out)))
        cls.old.creatures_instance_validate.argtypes=[C.POINTER(Instance)]
        cls.old.creatures_roster_validate.argtypes=[C.POINTER(Roster)]

    def test_exact_released_runtime_prefixes(self):
        for name,size in [('creature_forms',65*32),('creature_learnsets',102*2),('creature_evolutions',35*8),('creature_abilities',65*8)]:
            self.assertEqual(historical_prefix_bytes(self.lib,name,size),bytes((U8*size).in_dll(self.old,name)),name)

    def test_every_new_form_definition_and_command_inheritance(self):
        for row in NEW:
            f=self.lib.creatures_form(row['id']).contents
            self.assertEqual(self.lib.creatures_name(f.id).decode(),row['name'])
            self.assertEqual(f.polarity,['yin','yang'].index(row['polarity']))
            self.assertEqual(f.phase,['wood','fire','earth','metal','water'].index(row['phase']))
            self.assertEqual(f.field_caps,sum(CAPABILITY_MASKS[c] for c in row['field_caps']))
            self.assertEqual(list(f.stats),[row['stats'][key] for key in ['vitality','power','guard','focus','haste']])
            for level in range(0,52):
                for command in range(0,92):
                    expected=1<=level<=50 and any(l['level']<=level and l['ability_id']==command for l in row['learnset'])
                    self.assertEqual(bool(self.lib.creatures_command_learned(f.id,level,command)),expected)
            for revision in range(1,6):self.assertFalse(self.lib.creatures_form_allowed_revision(f.id,revision))
        self.assertFalse(self.lib.creatures_ability(12))
        for id in range(121,129):self.assertFalse(self.lib.creatures_form(id))

    def test_revision5_exact_old_acceptance_differential(self):
        rng=random.Random(0x554e4445);comparisons=0
        for p in V5['forms']:
            c=Instance();c.form_id=p['id'];c.flags=1;c.instance_id=1;c.level=50;c.xp=470596;c.bond=0;c.polarity=p['polarity'];c.equipped[0]=p['learn'][0][1]
            cases=[bytes(c)]
            for level in {1,p['min_level']-1,p['min_level'],50}:
                if level<1:continue
                for mask in [0,1,2,3,p['trial_mask'],65535]:
                    v=Instance.from_buffer_copy(c);v.level=level;v.xp=4*(level-1)**3;v.trial_flags=mask;cases.append(bytes(v))
            for _ in range(192):
                raw=bytearray(bytes(c));raw[rng.randrange(24)]=rng.randrange(256);cases.append(bytes(raw))
            for raw in cases:
                value=Instance.from_buffer_copy(raw);before=bytes(value)
                expected=self.old.creatures_instance_validate(C.byref(value))
                self.assertEqual(self.lib.creatures_instance_validate_revision(C.byref(value),5),expected,(p['id'],raw.hex()))
                self.assertEqual(bytes(value),before)
                comparisons+=1
        for id in list(range(130))+[256,65537,0xffffffff]:
            self.assertEqual(self.lib.creatures_form_allowed_revision(id,5),self.old.creatures_form_allowed_revision(id,5))
            self.assertEqual(self.lib.creatures_trial_allowed_mask(id,5),self.old.creatures_trial_allowed_mask(id,5))
            for level in [0,1,12,20,26,28,32,50,51]:
                for command in list(range(92))+[255,256,65537,0xffffffff]:
                    self.assertEqual(self.lib.creatures_command_learned_revision(id,level,command,5),self.old.creatures_command_learned_revision(id,level,command,5))
        self.assertGreater(comparisons,13000)

    def test_revision5_does_not_consult_live_polarity_trial_learn_or_evolution(self):
        data=(ROOT/'src/creature_data.c').read_text()
        # Remove live rows from both identity indexes; frozen APIs must remain available.
        import re
        for name in ['creature_form_index','creature_ability_index','creature_incoming_evolution_index']:
            data=re.sub(r'(const CreatureU8 '+name+r'\[[^\n]+\] = \{).*?\n\};',r'\1\n    0\n};',data,flags=re.S)
        lib=configure(build(self.tmp.name,data,'no-live-authority'))
        self.assertFalse(lib.creatures_form(31))
        for p in V5['forms']:
            c=Instance();c.form_id=p['id'];c.flags=1;c.instance_id=1;c.level=50;c.xp=470596;c.polarity=p['polarity'];c.equipped[0]=p['learn'][0][1]
            self.assertTrue(lib.creatures_instance_validate_revision(C.byref(c),5),p['id'])
            self.assertFalse(lib.creatures_instance_validate(C.byref(c)))
        for id in [31,34]:
            p=LOOKUP[id];c=Instance();c.form_id=id;c.flags=1;c.instance_id=1;c.level=50;c.xp=470596;c.polarity=p['polarity'];c.equipped[0]=p['learn'][0][1];c.trial_flags=2
            self.assertFalse(lib.creatures_instance_validate_revision(C.byref(c),5))

    def test_strict_native(self):compile_native()
    def test_address_undefined_sanitizers(self):compile_native(True)
    def test_bounded_admission_strict(self):compile_native(False,'underwater_admission_job_native.c')
    def test_bounded_admission_sanitizers(self):compile_native(True,'underwater_admission_job_native.c')

class UnderwaterCatalogTests(unittest.TestCase):
    def test_fragments_generate_exact_tables_and_old_values(self):
        catalog=load_catalog(ROOT/'assets/creatures/catalog.json');enabled=load_json(ROOT/'assets/creatures/enabled.json')
        self.assertFalse(validate(catalog,load_json(ROOT/'assets/creatures/identity-lock.json')))
        self.assertFalse(validate_enabled(catalog,enabled));self.assertFalse(validate_compatibility(catalog,6))
        self.assertEqual(tuple(len(x) for x in build_tables(catalog,enabled)[:4]),(120,200,68,120))
        self.assertEqual(generate(catalog,enabled),(ROOT/'src/creature_data.c').read_text())
        descriptor=json.loads((ROOT/'assets/creatures/catalog.json').read_text())
        for paths in descriptor['sections'].values():
            for p in paths:self.assertLess((ROOT/'assets/creatures'/p).stat().st_size,90000)
        for p in ['src/creatures.c','src/creature_data.c','src/creature_history_v5.inc','assets/history/creatures-v5.json','assets/history/released-creature-relations-v5.json']:
            self.assertLess((ROOT/p).stat().st_size,90000)
        for revision,counts in [(1,(8,12,4,8)),(2,(11,16,5,11)),(3,(21,31,10,21)),(4,(41,61,20,41)),(5,(65,102,35,65)),(6,(89,142,51,89))]:
            p=REVISION_POLICY[revision];manifest={'content_revision':revision,'enabled_form_ids':p['forms'],'enabled_ability_ids':p['abilities'],'enabled_evolutions':p['edges']}
            self.assertFalse(validate_enabled(catalog,manifest));self.assertEqual(tuple(len(x) for x in build_tables(catalog,manifest)[:4]),counts)
    def test_pre_extension_catalog_canonical_values_are_exact(self):
        c=before_return(load_catalog(ROOT/'assets/creatures/catalog.json'))
        c['forms']=[f for f in c['forms'] if not 49<=f['id']<=72]
        c['abilities']=[a for a in c['abilities'] if a['id']<67]
        c['evolutions']=[e for e in c['evolutions'] if not 49<=e['from']<=72]
        c['gates']=[g for g in c['gates'] if not g['id'].startswith('underwater_') and g['id']!='palinode_open']
        c['trials']=[t for t in c['trials'] if not t['id'].startswith('uw_')]
        c['trial_bindings']=[t for t in c['trial_bindings'] if t['introduced_content_revision']<6]
        c['field_capabilities']=c['field_capabilities'][:26]
        for slot in c['slots']:
            if 49<=slot['id']<=72:slot['status']='reserved'
        self.assertEqual(hashlib.sha256(json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'ebe05e3fa2b35c7fcd3e32d5235b95fc0010e003acb8439b23eef58fa9b16ec0')

    def test_fragment_paths_duplicate_keys_and_oversize_reject(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'catalog.json';part=Path(d)/'part.json';part.write_text('[{"id":1}]')
            for files in [['../part.json'],['/part.json'],['part.json','part.json'],['part.json','./part.json']]:
                p.write_text(json.dumps({'$catalog_source':1,'sections':{'forms':files}}))
                with self.assertRaises(CatalogError):load_catalog(p)
            p.write_text('{"id":1,"id":2}')
            with self.assertRaises(CatalogError):load_json(p)
            p.write_text(json.dumps({'$catalog_source':1,'sections':{'forms':['part.json']}}));part.write_text(' '*90000+'[]')
            with self.assertRaises(CatalogError):load_catalog(p)
    def test_frozen_history_reproducible(self):
        subprocess.run([sys.executable,str(ROOT/'tools/generate_creature_history.py'),'--check'],check=True)
        subprocess.run([sys.executable,str(ROOT/'assets/creatures/format_catalog.py'),'--check'],check=True)

if __name__=='__main__':unittest.main(verbosity=2)
