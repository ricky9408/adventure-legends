#!/usr/bin/env python3
"""Future-policy gates only. Synthetic third tiers/branches are not gameplay."""
import copy, ctypes as C, importlib.util, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from test_creature_branches import branch_sources
from test_creature_sparse import ROOT, edit_array, refresh_key_indexes
from test_creatures import Instance, Roster
from retained_source_adapter import expand_local_includes
from test_southern_catalog import before_return
sys.path.insert(0,str(ROOT/'assets/creatures'))
from generate_data import build_trial_masks
from released_policy import validate_compatibility
from catalog_source import load_catalog

def append(text,name,rows):return edit_array(text,name,lambda body:body+'\n'+rows)
def linear_sources():
    # The formerly synthetic F001 third tier is now reviewed Return7 content.
    # Exercise that actual graph and its complete dependency mask; do not append
    # duplicate form3/ability91 identities to make a broken synthetic catalog.
    h=(ROOT/'src/creatures.h').read_text()
    c=expand_local_includes(ROOT/'src/creatures.c')
    d=(ROOT/'src/creature_data.c').read_text()
    return h,c,d

def multi_branch_sources():
    # Independent1/2 branch masks are now reviewed production policy.
    return branch_sources()

HARNESS=r'''
#include "creatures.h"
#include <assert.h>
#include <string.h>
static CreatureRoster r,before;
#ifndef CONTEXT
#define CONTEXT 256
#endif
int main(void){CreatureInstance *c;unsigned target,mask,rev;
#ifdef INVALID
 assert(!creatures_catalog_validate()); return 0;
#endif
 assert(creatures_catalog_validate());creatures_roster_init(&r);
#ifdef LINEAR
 assert(creatures_grant_story(&r,0,0)==0);c=&r.instances[0];
 c->level=50;c->xp=creatures_xp_threshold(50);c->bond=100;
 assert(creatures_trial_mask_for_key(1,2)==1024);
 assert(creatures_family_trial(1)==1 && creatures_family_trial(2)==1 && creatures_family_trial(3)==1);
 before=r;assert(!creatures_mark_trial_qualified(c,1,2));assert(!memcmp(&r,&before,sizeof r));
 assert(creatures_mark_trial(c,1));assert(!creatures_mark_trial(c,1025));
 assert(creatures_evolution_to(1,2)->trial_flag==1);
 assert(creatures_evolve_to(&r,0,2,1,1,1)==CREATURE_EVOLVE_READY);
 assert(creatures_evolution_count(2)==1 && creatures_evolution_to(2,3)->trial_flag==1025);
 for(rev=1;rev<=6;++rev)assert(creatures_instance_validate_revision(c,rev));
 assert(creatures_can_evolve_to(c,3,4096,1)==CREATURE_EVOLVE_TRIAL);
 assert(creatures_mark_trial_qualified(c,1,2));assert(c->trial_flags==1025);
 assert(creatures_mark_trial(c,1));assert(c->trial_flags==1025);
 before=r;assert(!creatures_mark_trial_qualified(c,2,2));assert(!memcmp(&r,&before,sizeof r));
 for(rev=1;rev<=6;++rev)assert(!creatures_instance_validate_revision(c,rev));
 before=r;assert(creatures_evolve_to(&r,0,3,4096,1,0)==CREATURE_EVOLVE_DEFERRED);assert(!memcmp(&r,&before,sizeof r));
 assert(creatures_evolve_to(&r,0,3,4096,1,1)==CREATURE_EVOLVE_READY);
 assert(c->form_id==3 && c->instance_id==before.instances[0].instance_id && c->trial_flags==1025);
 assert(c->flags==before.instances[0].flags && creatures_legacy_spirit(3)==0);
 assert(creatures_roster_validate(&r));
 /* Return terminal3 now requires its complete earned chain. The old
  * synthetic mask0/mask1 cases remain explicit adverse checks. */
 for(mask=0;mask<65536;++mask){c->trial_flags=(CreatureU16)mask;assert(creatures_instance_validate(c)==(mask==1025));}
 (void)target;
#else
 for(target=38;target<=39;++target)for(mask=0;mask<4;++mask){
  creatures_roster_init(&r);assert(creatures_grant(&r,37,50,100,0,0)==0);c=&r.instances[0];
  if(mask&1)assert(creatures_mark_trial_qualified(c,13,1));
  if(mask&2)assert(creatures_mark_trial_qualified(c,13,2));
  assert(c->trial_flags==mask);before=r;
  assert(creatures_can_evolve(c,CONTEXT,1)==CREATURE_EVOLVE_AMBIGUOUS);
  assert(creatures_evolve(&r,0,CONTEXT,1,1)==CREATURE_EVOLVE_AMBIGUOUS);assert(!memcmp(&r,&before,sizeof r));
  if(mask&(target==38?1:2)){
   assert(creatures_evolve_to(&r,0,target,CONTEXT,1,0)==CREATURE_EVOLVE_DEFERRED);assert(!memcmp(&r,&before,sizeof r));
   assert(creatures_evolve_to(&r,0,target,CONTEXT,1,1)==CREATURE_EVOLVE_READY);
   assert(c->trial_flags==mask && c->instance_id==before.instances[0].instance_id);
  }else{assert(creatures_evolve_to(&r,0,target,CONTEXT,1,1)==CREATURE_EVOLVE_TRIAL);assert(!memcmp(&r,&before,sizeof r));}
 }
 (void)rev;
#endif
 return 0;}
'''

def native(sources,linear=False,invalid=False,context=256):
    with tempfile.TemporaryDirectory(prefix='magma-policy-') as tmp:
        p=Path(tmp)
        for name,source in zip(('creatures.h','creatures.c','creature_data.c'),sources):(p/name).write_text(source)
        (p/'creature_history_v5.inc').write_bytes((ROOT/'src/creature_history_v5.inc').read_bytes())
        (p/'creature_admission_job.inc').write_bytes((ROOT/'src/creature_admission_job.inc').read_bytes())
        (p/'test.c').write_text(HARNESS)
        flags=['-std=c99','-O1','-Wall','-Wextra','-Werror','-pedantic','-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie','-I'+str(p)]
        flags+=['-DCONTEXT='+str(context)]
        if linear:flags+=['-DLINEAR']
        if invalid:flags+=['-DINVALID']
        subprocess.run(['cc',*flags,str(p/'test.c'),str(p/'creatures.c'),str(p/'creature_data.c'),'-o',str(p/'test')],check=True)
        subprocess.run([str(p/'test')],check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'))

class MagmaArchitectureTests(unittest.TestCase):
    def test_released_F001_third_tier_and_every_u16_trial_pattern(self):native(linear_sources(),linear=True)
    def test_branch_each_key_and_both_keys_keep_explicit_target_and_decline(self):native(multi_branch_sources())
    def test_future_u16_context_is_not_truncated(self):
        h,c,d=multi_branch_sources()
        self.assertIn('CREATURE_EVOLUTION_CONTEXT_MASK = 16383',h)
        h=h.replace('CREATURE_EVOLUTION_CONTEXT_MASK = 16383','CREATURE_EVOLUTION_CONTEXT_MASK = 32767')
        for old,new in [('{37, 38, 26, 45, 1, 256}','{37, 38, 26, 45, 1, 16384}'),('{37, 39, 26, 45, 2, 256}','{37, 39, 26, 45, 2, 16384}')]:
            self.assertIn(old,c);self.assertIn(old,d)
            c=c.replace(old,new);d=d.replace(old,new)
        native((h,c,d),context=16384)
    def test_trial_alias_unknown_dependencies_cycles_and_unclosed_edge_fail(self):
        h,c,d=linear_sources()
        for old,new in [('{1, 2, 1024, 1, 7}','{1, 1, 1024, 1, 7}'),('{1, 2, 1024, 1, 7}','{1, 2, 1, 0, 7}'),('{1, 2, 1024, 1, 7}','{1, 2, 1024, 2, 7}'),('{1, 1, CREATURE_TRIAL_HEARTH, 0, 1}','{1, 1, CREATURE_TRIAL_HEARTH, 1024, 1}'),('{1, 2, 1024, 1, 7}','{1, 2, 1024, 1, 8}')]:
            with self.subTest(new=new):self.assertIn(old,c);native((h,c.replace(old,new,1),d),linear=True,invalid=True)
        self.assertIn('{2, 3, 32, 60, 1025, 4096}',c);self.assertIn('{2, 3, 32, 60, 1025, 4096}',d)
        native((h,c.replace('{2, 3, 32, 60, 1025, 4096}','{2, 3, 32, 60, 1024, 4096}'),d.replace('{2, 3, 32, 60, 1025, 4096}','{2, 3, 32, 60, 1024, 4096}')),linear=True,invalid=True)
    def test_frozen_policy_generation_is_exact(self):subprocess.run([sys.executable,str(ROOT/'tools/generate_creature_history.py'),'--check'],check=True)
    def test_semantic_prefix_lock_accepts_extension_rejects_rewrite(self):
        cat=load_catalog(ROOT/'assets/creatures/catalog.json');self.assertFalse(validate_compatibility(cat))
        added=before_return(cat);f=next(f for f in added['forms'] if f['id']==2)
        f['learnset'].append({'level':30,'ability_id':43});added['evolutions'].append(dict(added['evolutions'][0],**{'from':2,'to':3,'min_level':30,'required_trial':'future_trial'}))
        self.assertFalse(validate_compatibility(added))
        for field,value in [('level',2),('ability_id',23)]:
            changed=copy.deepcopy(cat);changed['forms'][0]['learnset'][0][field]=value;self.assertTrue(validate_compatibility(changed))
        changed=copy.deepcopy(cat);changed['evolutions'][0]['min_level']=13;self.assertTrue(validate_compatibility(changed))
        changed=copy.deepcopy(cat);changed['trial_bindings'][0]['wire_mask']=1024;self.assertTrue(validate_compatibility(changed))
    def test_authoring_resolves_linear_prerequisites_and_branch_subsets(self):
        cat={'trial_bindings':[{'trial_id':'one','family_id':'F011','local_trial_id':1,'wire_mask':1,'prerequisite_trial_mask':0,'introduced_content_revision':5}, {'trial_id':'two','family_id':'F011','local_trial_id':2,'wire_mask':2,'prerequisite_trial_mask':1,'introduced_content_revision':5}]}
        self.assertEqual(build_trial_masks(cat),{'one':1,'two':3})
        cat['trial_bindings'][1]['prerequisite_trial_mask']=0;self.assertEqual(build_trial_masks(cat),{'one':1,'two':2})
        cat['trial_bindings'][0]['prerequisite_trial_mask']=2;cat['trial_bindings'][1]['prerequisite_trial_mask']=1
        with self.assertRaises(ValueError):build_trial_masks(cat)

if __name__=='__main__':unittest.main(verbosity=2)
