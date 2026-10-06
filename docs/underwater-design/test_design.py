#!/usr/bin/env python3
"""Design-model tests; do not confuse their proof with native execution."""
import copy,itertools,json,unittest
from pathlib import Path
from design_model import State,Instance,coverage,admitted,T
from validate_design import validate,BASE,ROOT

def old_state():
 e=json.loads((BASE/'assets/creatures/enabled.json').read_text())
 outgoing={edge[0] for edge in e['enabled_evolutions']}
 leaves=sorted(set(e['enabled_form_ids'])-outgoing)
 assert len(leaves)==34
 return State(instances=[Instance(i+1,f) for i,f in enumerate(leaves)],histories=set(e['enabled_form_ids']),next_id=35)

class DesignTests(unittest.TestCase):
 def test_schema_and_allocations(self):self.assertEqual(validate()['status'],'PASS')
 def test_all_256_first_branch_choices_complete_89_50(self):
  for choices in itertools.product([1,2],repeat=8):
   st=old_state()
   for family,key in zip(range(17,25),choices):
    self.assertEqual(st.grant(family,1),'GRANTED');slot=len(st.instances)-1;i=st.instances[slot]
    self.assertEqual(st.trial(slot,i.iid,family,key),'TRAINED')
    self.assertEqual(st.evolve(slot,i.iid,49+3*(family-17)+key,True),'EVOLVED')
    self.assertEqual(st.grant(family,2,True),'GRANTED');slot=len(st.instances)-1;i=st.instances[slot]
    self.assertEqual(st.trial(slot,i.iid,family,3-key),'TRAINED')
    self.assertEqual(st.evolve(slot,i.iid,49+3*(family-17)+3-key,True),'EVOLVED')
   self.assertEqual((len(st.histories),len(st.instances),len({i.iid for i in st.instances})),(89,50,50))
   self.assertEqual(coverage([i.form for i in st.instances])['viable'],50)
 def test_each_family_repeat_same_attempt_no_duplicate(self):
  for family in range(17,25):
   st=old_state();st.grant(family,1);slot=len(st.instances)-1;i=st.instances[slot]
   st.trial(slot,i.iid,family,1);st.evolve(slot,i.iid,50+3*(family-17),True)
   self.assertEqual(st.grant(family,2,True),'GRANTED');before=copy.deepcopy(st)
   for _ in range(64):self.assertEqual(st.grant(family,2,True),'UNCHANGED')
   self.assertEqual(st,before)
 def test_first_receipt_retry_before_capacity_and_id(self):
  st=old_state();st.grant(17,1);st.next_id=2**32-1;before=copy.deepcopy(st)
  self.assertEqual(st.grant(17,9),'UNCHANGED');self.assertEqual(st,before)
 def test_new_repeat_attempt_has_no_event_xp_or_old_trial(self):
  st=old_state();st.grant(19,1);slot=len(st.instances)-1;i=st.instances[slot]
  st.trial(slot,i.iid,19,1);st.evolve(slot,i.iid,56,True);xp=st.event_xp
  self.assertEqual(st.grant(19,2,True),'GRANTED')
  self.assertEqual(st.event_xp,xp);self.assertEqual(st.instances[-1].trials,0)
  self.assertNotEqual(st.instances[-1].iid,i.iid)
  self.assertEqual(st.grant(19,3,True),'GRANTED');self.assertEqual(st.event_xp,xp)
 def test_per_instance_floor_with_existing_lifetime_aid(self):
  st=old_state();st.grant(17,1);a=len(st.instances)-1;i=st.instances[a]
  st.trial(a,i.iid,17,1);st.evolve(a,i.iid,50,True);st.grant(17,2,True)
  b=len(st.instances)-1;j=st.instances[b];xp=st.event_xp
  self.assertEqual(st.trial(b,j.iid,17,1),'TRAINED');self.assertEqual(st.event_xp,xp)
  self.assertEqual((j.level,j.bond,j.trials),(28,45,1));self.assertEqual((i.form,i.trials),(50,1))
 def test_wrong_family_keys_and_identity_unchanged(self):
  for fam in range(17,25):
   st=old_state();st.grant(fam,1);slot=len(st.instances)-1;i=st.instances[slot]
   for wrong in range(17,25):
    if wrong==fam:continue
    for key in [1,2]:
     before=copy.deepcopy(st);self.assertEqual(st.trial(slot,i.iid,wrong,key),'INVALID');self.assertEqual(st,before)
   before=copy.deepcopy(st);self.assertEqual(st.trial(slot,i.iid+1,fam,1),'INVALID');self.assertEqual(st,before)
   self.assertEqual(st.trial(slot,i.iid,fam,3),'INVALID');self.assertEqual(st,before)
 def test_both_keys_choose_either_but_cannot_cross_branches(self):
  for fam in range(17,25):
   for targetkey in [1,2]:
    st=old_state();st.grant(fam,1);slot=len(st.instances)-1;i=st.instances[slot];base=i.form
    self.assertEqual(st.trial(slot,i.iid,fam,1),'TRAINED');self.assertEqual(st.trial(slot,i.iid,fam,2),'TRAINED')
    self.assertEqual(i.trials,3);before=copy.deepcopy(st)
    self.assertEqual(st.evolve(slot,i.iid,base+targetkey,False),'DEFERRED');self.assertEqual(st,before)
    self.assertEqual(st.evolve(slot,i.iid,base+targetkey,True),'EVOLVED');self.assertEqual(i.trials,3)
    after=copy.deepcopy(st);self.assertEqual(st.evolve(slot,i.iid,base+3-targetkey,True),'NO_EDGE');self.assertEqual(st,after)
 def test_unproven_or_interrupted_trial_has_no_floors(self):
  st=old_state();st.grant(17,1);slot=len(st.instances)-1;i=st.instances[slot];before=copy.deepcopy(st)
  self.assertEqual(st.trial(slot,i.iid,17,1,proof=False),'LOCKED');self.assertEqual(st,before)
 def test_completed_trial_does_not_refill_lowered_stats(self):
  st=old_state();st.grant(17,1);slot=len(st.instances)-1;i=st.instances[slot];st.trial(slot,i.iid,17,1)
  # Deliberately malformed input is used only to test idempotent replay order in this design model.
  i.bond=1;before=copy.deepcopy(st);self.assertEqual(st.trial(slot,i.iid,17,1),'UNCHANGED');self.assertEqual(st,before)
 def test_terminal_72_plus_88_extras_exactly_160(self):
  terminal=sorted({f for row in T.values() for f in row['terminal_form_ids']})
  self.assertEqual(len(terminal),72)
  c=coverage(terminal+[terminal[0]]*88);self.assertEqual((c['occupied'],c['viable'],c['excess'],c['missing']),(160,72,88,0));self.assertTrue(c['safe'])
  self.assertFalse(admitted(terminal+[terminal[0]]*88,terminal+[terminal[0]]*89))
 def test_88_extras_leave_all_new_opportunities(self):
  st=old_state();forms=[i.form for i in st.instances]+[1]*88
  self.assertTrue(coverage(forms)['safe'])
  for family in range(17,25):
   base=49+3*(family-17)
   for target in [base+1,base+2]:
    self.assertTrue(admitted(forms,forms+[base]));forms.append(base)
    after=forms[:-1]+[target];self.assertTrue(admitted(forms,after));forms=after
  self.assertEqual((len(forms),coverage(forms)['viable'],coverage(forms)['excess']),(138,50,88))
  self.assertFalse(admitted(forms,forms+[49]))
 def test_branch_coverage_loss_boundary_only(self):
  # Safe small collections may choose a duplicate branch;88 extras must not become89.
  self.assertTrue(admitted([49,50],[50,50]))
  before=[49,50]+[1]*89 # one viable F001 plus88 extras, and two branch opportunities
  after=[50,50]+[1]*89
  self.assertEqual(coverage(before)['excess'],88);self.assertFalse(admitted(before,after))
 def test_grandfathered_nonworsening_not_load_rejection(self):
  before=[1]*159;after=before+[49]
  self.assertFalse(coverage(before)['safe']);self.assertTrue(admitted(before,after))
  self.assertFalse(admitted(before,before+[1]))
  self.assertTrue(admitted([1]*160,[2]+[1]*159))
 def test_id_exhaustion_and_repeat_locked_are_atomic(self):
  st=old_state();before=copy.deepcopy(st)
  self.assertEqual(st.grant(17,1,True),'LOCKED');self.assertEqual(st,before)
  st.next_id=2**32-1;before=copy.deepcopy(st)
  self.assertEqual(st.grant(17,1),'ID_EXHAUSTED');self.assertEqual(st,before)
 def test_main_story_graph_has_no_optional_requirements(self):
  world=json.loads((ROOT/'world_plan.json').read_text());areas={a['id']:a for a in world['areas']}
  unlocked={46,47};claimed={38,39};prefix=0
  for area,nextprefix in [(50,1),(51,3),(52,7),(53,15)]:
   self.assertEqual(areas[area]['entry_objective_prefix'],prefix)
   unlocked.add(area);prefix=nextprefix
  self.assertEqual(prefix,15)
  self.assertNotIn(48,unlocked);self.assertNotIn(49,unlocked)
  self.assertFalse(world['route_contract']['requires_optional_old_quests'])

if __name__=='__main__':unittest.main(verbosity=2)
