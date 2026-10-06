"""Adversarial DESIGN MODEL tests; not production runtime or historical save tests."""
import copy,json,random,unittest,itertools
from pathlib import Path
from terminal_admission import *
ROOT=Path(__file__).resolve().parent
POLICY=build_policy(json.loads((ROOT/'identity-lock.snapshot.json').read_text()))

class MutationModel:
    """Small transactional proof harness. All source/edge/trial gates assumed true.
    Returned refusals must leave every visible and persistent model field unchanged.
    """
    def __init__(self,forms):
        self.instances=[(i+1,f) for i,f in enumerate(forms)]
        self.next_id=len(forms)+1;self.claims=set();self.history=set(forms);self.gear_claims=set()
    def forms(self):return [f for _,f in self.instances]
    def snapshot(self):return copy.deepcopy(self.__dict__)
    def capture(self,base,source,repeatable=False,gear_full=False):
        if source in self.claims and not repeatable:return 'ALREADY_CLAIMED'
        candidate=self.forms()+[base]
        result=evaluate(self.forms(),candidate,POLICY)
        if not result.allowed:return result.reason
        if gear_full:return 'GEAR_FULL'
        staged=self.snapshot()
        staged['instances'].append((staged['next_id'],base));staged['next_id']+=1
        staged['claims'].add(source);staged['history'].add(base)
        self.__dict__.update(staged)
        return result.reason
    def evolve(self,index,target,confirmed=True):
        if not confirmed:return 'DEFER'
        old=self.instances[index][1]
        if POLICY[old].family!=POLICY[target].family or POLICY[old].terminal_mask&POLICY[target].terminal_mask!=POLICY[target].terminal_mask:
            return 'INVALID_EDGE'
        candidate=self.forms();candidate[index]=target
        result=evaluate(self.forms(),candidate,POLICY)
        if not result.allowed:return result.reason
        iid,_=self.instances[index];self.instances[index]=(iid,target);self.history.add(target)
        return result.reason

class CapacityTests(unittest.TestCase):
    def test_matching_formula_against_exhaustive_assignments(self):
        for size in range(7):
            for masks in itertools.product((1,2,3),repeat=size):
                matching={0}
                for mask in masks:
                    matching|={used|bit for used in tuple(matching) for bit in (1,2) if mask&bit and not used&bit}
                nbase=masks.count(3);a=masks.count(1);b=masks.count(2)
                self.assertEqual(branch_coverage(nbase,a,b),max(x.bit_count() for x in matching))
    def test_locked72(self):
        families={p.family:p.terminals for p in POLICY.values()}
        self.assertEqual((len(families),sum(map(len,families.values()))),(60,72))
    def test_linear_duplicates_one_opportunity(self):self.assertEqual(coverage([1,2,3],POLICY).viable,1)
    def test_one_flexible_base_is_one_not_two(self):self.assertEqual(coverage([37],POLICY).viable,1)
    def test_two_flexible_bases_cover_two(self):self.assertEqual(coverage([37,37],POLICY).viable,2)
    def test_same_terminal_twice_covers_one(self):self.assertEqual(coverage([38,38],POLICY).viable,1)
    def test_opposite_terminal_pair(self):self.assertEqual(coverage([38,39],POLICY).viable,2)
    def test_base_plus_either_terminal(self):
        for x in [38,39]:self.assertEqual(coverage([37,x],POLICY).viable,2)
    def test_88_extras_exact(self):
        c=coverage([1]*89,POLICY);self.assertEqual((c.viable,c.excess,c.admission_safe),(1,88,True))
    def test_89th_extra_refused_before_full(self):
        m=MutationModel([1]*89);before=m.snapshot()
        self.assertEqual(m.capture(1,'extra'),'EXTRA_COPY_BUDGET');self.assertEqual(m.snapshot(),before)
    def test_missing_family_admitted_at_limit(self):
        m=MutationModel([1]*89);self.assertEqual(m.capture(31,'Q30'),'ADMIT')
        self.assertEqual((len(m.instances),coverage(m.forms(),POLICY).excess),(90,88))
    def test_missing_branch_base_admitted_at_limit(self):
        m=MutationModel([1]*89+[38]);self.assertEqual(m.capture(37,'branch0',True),'ADMIT')
        self.assertEqual(coverage(m.forms(),POLICY).excess,88)
    def test_wrong_terminal_last_flexible_refused(self):
        m=MutationModel([1]*89+[38,37]);before=m.snapshot()
        self.assertEqual(m.evolve(90,38),'LAST_RESERVED_BRANCH_OPPORTUNITY');self.assertEqual(m.snapshot(),before)
        self.assertEqual(m.evolve(90,39),'ADMIT');self.assertEqual(m.instances[90][0],91)
    def test_reverse_wrong_terminal_refused(self):
        m=MutationModel([1]*89+[39,37]);before=m.snapshot()
        self.assertEqual(m.evolve(90,39),'LAST_RESERVED_BRANCH_OPPORTUNITY');self.assertEqual(m.snapshot(),before)
        self.assertEqual(m.evolve(90,38),'ADMIT')
    def test_wrong_terminal_allowed_with_one_slack_then_recovery(self):
        m=MutationModel([1]*88+[38,37]);self.assertEqual(coverage(m.forms(),POLICY).excess,87)
        self.assertEqual(m.evolve(89,38),'ADMIT');self.assertEqual(coverage(m.forms(),POLICY).excess,88)
        self.assertEqual(m.capture(37,'branch0',True),'ADMIT')
        self.assertEqual(m.evolve(len(m.instances)-1,39),'ADMIT')
    def test_first_branch_choice_always_possible_at_limit(self):
        for target in (38,39):
            m=MutationModel([1]*89+[37]);self.assertEqual(m.evolve(89,target),'ADMIT')
    def test_idempotent_claim_not_refused_at_limit(self):
        m=MutationModel([1]*89);self.assertEqual(m.capture(31,'Q30'),'ADMIT');before=m.snapshot()
        self.assertEqual(m.capture(31,'Q30'),'ALREADY_CLAIMED');self.assertEqual(m.snapshot(),before)
    def test_repeat_source_refusal_has_no_new_identity_or_receipt(self):
        m=MutationModel([1]*89+[38,39]);m.claims.add('branch0');before=m.snapshot()
        self.assertEqual(m.capture(37,'branch0',True),'EXTRA_COPY_BUDGET');self.assertEqual(m.snapshot(),before)
    def test_refusal_preserves_evolution_trial_history_identity(self):
        m=MutationModel([1]*89+[38,37]);m.trials={91:3};before=m.snapshot()
        self.assertEqual(m.evolve(90,38),'LAST_RESERVED_BRANCH_OPPORTUNITY');self.assertEqual(m.snapshot(),before)
    def test_defer_byte_unchanged(self):
        m=MutationModel([1]*89+[38,37]);before=m.snapshot()
        self.assertEqual(m.evolve(90,39,False),'DEFER');self.assertEqual(m.snapshot(),before)
    def test_mixed_reward_full_gear_atomic(self):
        m=MutationModel([1]*89);before=m.snapshot()
        self.assertEqual(m.capture(31,'Q30',gear_full=True),'GEAR_FULL');self.assertEqual(m.snapshot(),before)
        self.assertEqual(m.capture(31,'Q30'),'ADMIT')
    def test_all_future_roots_reserved_even_before_enablement(self):
        m=MutationModel([1]*89);out,captures=terminalize_without_coverage_loss(m.forms(),POLICY)
        self.assertEqual((len(out),coverage(out,POLICY).viable,captures),(160,72,71))
        # This is a capacity proof, not authorization to enable unimplemented roots.
    def test_full_160_safe_roster_has_complete_coverage(self):
        terminal={p.family:p.terminals for p in POLICY.values()};forms=[f for ts in terminal.values() for f in ts]+[3]*88
        self.assertEqual((len(forms),coverage(forms,POLICY).viable),(160,72))
        m=MutationModel(forms);before=m.snapshot();self.assertEqual(m.capture(37,'repeat',True),'ROSTER_FULL');self.assertEqual(m.snapshot(),before)
    def test_history_does_not_count_as_viable_owned_coverage(self):
        m=MutationModel([1]*89+[38,37]);m.history.update(range(1,129))
        self.assertEqual(m.evolve(90,38),'LAST_RESERVED_BRANCH_OPPORTUNITY')
    def test_legacy_overbudget_load_not_rejected_or_normalized(self):
        # The admission module has no bank reader; valid old states remain representable.
        m=MutationModel([1]*159);before=m.snapshot();c=coverage(m.forms(),POLICY)
        self.assertFalse(c.admission_safe);self.assertEqual(m.snapshot(),before)
        result=evaluate(m.forms(),m.forms()+[31],POLICY)
        self.assertTrue(result.allowed);self.assertFalse(result.completion_guaranteed_by_capacity)
        self.assertEqual(result.reason,'ADMIT_LEGACY_NONWORSENING_ONLY')
    def test_legacy_overbudget_not_falsely_recoverable(self):
        with self.assertRaises(ValueError):terminalize_without_coverage_loss([1]*159,POLICY)
    def test_legacy_excess_may_not_worsen(self):
        m=MutationModel([1]*159);before=m.snapshot()
        self.assertEqual(m.capture(1,'extra'),'EXTRA_COPY_BUDGET');self.assertEqual(m.snapshot(),before)
    def test_full_legacy_retained_unchanged(self):
        m=MutationModel([1]*160);before=m.snapshot();self.assertEqual(m.capture(31,'Q30'),'ROSTER_FULL');self.assertEqual(m.snapshot(),before)
        self.assertEqual(m.evolve(0,2),'ADMIT_LEGACY_NONWORSENING_ONLY')
    def test_wrong_family_not_an_escape(self):
        m=MutationModel([1]*89+[38,37]);before=m.snapshot()
        self.assertEqual(m.evolve(90,41),'INVALID_EDGE');self.assertEqual(m.snapshot(),before)
    def test_exhaustive_sufficient_states(self):
        r=exhaustive_choice_order_proof()
        self.assertEqual(r['global_safe_capacity_states'],6497)
        self.assertEqual(r['branch_count_states'],129764)
    def test_varied_mutation_orders_always_retain_completion(self):
        rng=random.Random(0x72_160_88)
        initial=[1,4,7,10,13,16,19,22,73,75,77,25,28,79,81,83,85,87,89,91,93]
        roots=sorted({min(f for f,p in POLICY.items() if p.family==row.family) for row in POLICY.values()})
        for _ in range(200):
            forms=list(initial)
            # Random orders include duplicates of any currently modeled root, premature
            # same-branch choices, repeated refusals and later missing-family acquisition.
            for __ in range(220):
                if rng.randrange(3) or not forms:
                    candidate=forms+[rng.choice(roots)]
                else:
                    index=rng.randrange(len(forms));targets=POLICY[forms[index]].terminals
                    candidate=list(forms);candidate[index]=rng.choice(targets)
                if evaluate(forms,candidate,POLICY).allowed:forms=candidate
                self.assertTrue(coverage(forms,POLICY).admission_safe)
            out,captures=terminalize_without_coverage_loss(forms,POLICY)
            self.assertEqual(coverage(out,POLICY).viable,72);self.assertLessEqual(len(out),160)
            self.assertEqual(captures,72-coverage(forms,POLICY).viable)

if __name__=='__main__':unittest.main()
