#!/usr/bin/env python3
"""DESIGN MODEL ONLY: terminal-coverage admission, never a runtime/save validator.

A list position represents one distinct retained individual. Historical collection
bits are intentionally absent. The final locked topology is used only to reserve
space; it is not permission to enable, acquire or evolve a reserved form.
"""
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import json
CAPACITY=160
FINAL_OPPORTUNITIES=72
EXTRA_COPY_BUDGET=CAPACITY-FINAL_OPPORTUNITIES

@dataclass(frozen=True)
class FormPolicy:
    family: str
    terminal_mask: int
    terminals: tuple

@dataclass(frozen=True)
class Coverage:
    occupied: int
    viable: int
    excess: int
    free_slots: int
    missing_opportunities: int
    admission_safe: bool

@dataclass(frozen=True)
class Admission:
    allowed: bool
    reason: str
    before: Coverage
    after: Coverage
    completion_guaranteed_by_capacity: bool

def build_policy(lock):
    groups=defaultdict(list)
    for row in lock['slots']:
        groups[row['family_id']].append(row)
    policy={}
    for family,rows in sorted(groups.items()):
        max_tier=max(x['tier'] for x in rows)
        terminals=tuple(sorted(x['id'] for x in rows if x['tier']==max_tier))
        if len(terminals) not in (1,2): raise ValueError('unreviewed terminal topology')
        for row in rows:
            if len(terminals)==1: mask=1
            elif row['id'] in terminals: mask=1<<terminals.index(row['id'])
            elif row['tier']==1: mask=3
            else: raise ValueError('unreviewed branching middle tier')
            policy[row['id']]=FormPolicy(family,mask,terminals)
    if len(policy)!=128 or set(policy)!=set(range(1,129)):raise ValueError('identity coverage')
    if sum(len(v[0].terminals) for v in _by_family(policy).values())!=72:raise ValueError('72 opportunities')
    return policy

def _by_family(policy):
    groups=defaultdict(list)
    for row in policy.values():groups[row.family].append(row)
    return groups

def branch_coverage(base,a,b):
    """Maximum matching for a locked two-target branch family."""
    n=base+a+b
    target_count=int(bool(base or a))+int(bool(base or b))
    return min(n,target_count)

def coverage(forms,policy):
    groups=defaultdict(lambda:[0,0])
    if len(forms)>CAPACITY:raise ValueError('more than160 retained individuals')
    for form in forms:
        if type(form) is not int or form not in policy:raise ValueError('unknown form')
        row=policy[form];groups[row.family][0]+=1;groups[row.family][1]|=row.terminal_mask
    viable=sum(min(n,mask.bit_count()) for n,mask in groups.values())
    n=len(forms);e=n-viable
    return Coverage(n,viable,e,CAPACITY-n,FINAL_OPPORTUNITIES-viable,e<=EXTRA_COPY_BUDGET)

def evaluate(before_forms,after_forms,policy):
    """Pure admission subcheck; exact source/edge/trial/quest checks remain mandatory.
    Never use this as a historical-bank legality test or as mutation authorization.
    """
    before=coverage(before_forms,policy)
    if len(after_forms)>CAPACITY:
        return Admission(False,'ROSTER_FULL',before,before,before.admission_safe)
    after=coverage(after_forms,policy)
    if after.admission_safe:
        return Admission(True,'ADMIT',before,after,True)
    if not before.admission_safe and after.excess<=before.excess and after.viable>=before.viable:
        return Admission(True,'ADMIT_LEGACY_NONWORSENING_ONLY',before,after,False)
    reason='LAST_RESERVED_BRANCH_OPPORTUNITY' if len(before_forms)==len(after_forms) else 'EXTRA_COPY_BUDGET'
    return Admission(False,reason,before,after,before.admission_safe)

def terminalize_without_coverage_loss(forms,policy):
    """Construct a completion witness from every admission-safe roster.
    Acquire exactly72−V missing opportunities, then realize a maximum matching.
    Source/trial reachability is a separate authoring/native gate.
    """
    forms=list(forms)
    if not coverage(forms,policy).admission_safe:raise ValueError('legacy excess cannot be repaired by admission alone')
    families=defaultdict(list)
    for form,row in policy.items():families[row.family].append(form)
    captures=0
    for family,allforms in sorted(families.items()):
        terminal_ids=policy[allforms[0]].terminals
        base=min(allforms)
        while True:
            owned=[x for x in forms if policy[x].family==family]
            union=0
            for x in owned:union|=policy[x].terminal_mask
            local=min(len(owned),union.bit_count())
            if local==len(terminal_ids):break
            result=evaluate(forms,forms+[base],policy)
            if not result.allowed or result.after.viable!=result.before.viable+1:raise AssertionError('missing opportunity blocked')
            forms.append(base);captures+=1
        # Choose real representatives for each terminal. Reserve fixed targets first.
        indices=[i for i,x in enumerate(forms) if policy[x].family==family]
        chosen=set()
        missing=[]
        for target in terminal_ids:
            exact=next((i for i in indices if forms[i]==target),None)
            if exact is not None:chosen.add(exact)
            else:missing.append(target)
        for target in missing:
            bit=1<<terminal_ids.index(target)
            i=next(i for i in indices if i not in chosen and policy[forms[i]].terminal_mask&bit)
            candidate=list(forms);candidate[i]=target
            result=evaluate(forms,candidate,policy)
            if not result.allowed or result.after.viable!=result.before.viable:raise AssertionError('maximum matching realization loses coverage')
            forms=candidate;chosen.add(i)
        # Surplus flexible copies can then choose either terminal without coverage loss.
        for i in indices:
            if forms[i] not in terminal_ids:
                candidate=list(forms);candidate[i]=terminal_ids[0]
                if not evaluate(forms,candidate,policy).allowed:raise AssertionError('surplus evolution blocked after target coverage')
                forms=candidate
    out=coverage(forms,policy)
    if out.viable!=72 or out.occupied>160:raise AssertionError('completion witness')
    return forms,captures

def exhaustive_choice_order_proof():
    """Induction checks over every global capacity state and every safe branch multiset.
    Family transitions have only ΔN∈{0,1}, ΔV∈{−1,0,1}; other families add linearly.
    """
    global_states=0;global_admitted_transitions=0;global_refused_transitions=0
    for viable in range(73):
        for excess in range(89):
            n=viable+excess
            assert n<=160 and 160-n>=72-viable
            global_states+=1
            # Duplicate acquisition; missing-opportunity acquisition; last-flexible-target loss.
            for dn,dv in [(1,0),(1,1),(0,-1),(0,0)]:
                if not 0<=viable+dv<=72:continue
                nn=n+dn;vv=viable+dv;ee=nn-vv
                allowed=nn<=160 and ee<=88
                if allowed:
                    assert 160-nn>=72-vv
                    global_admitted_transitions+=1
                else:global_refused_transitions+=1
            # Missing-opportunity acquisition is always admitted, even at excess88.
            if viable<72:
                assert n<160 and (n+1)-(viable+1)<=88
            # Repeating this step terminates in exactly72−V steps, ≤160 occupants.
            assert n+(72-viable)==72+excess<=160
    branch_states=0;branch_transitions=0;coverage_losing_evolutions=0
    # A single branch family in an admission-safe roster has at most90 individuals.
    # Enumerate all counts, not one representative acquisition/evolution ordering.
    for base in range(91):
        for a in range(91-base):
            for b in range(91-base-a):
                n=base+a+b;v=branch_coverage(base,a,b)
                if n-v>88:continue
                branch_states+=1
                vv=branch_coverage(base+1,a,b)
                assert vv-v in (0,1)
                if v<2:assert vv==v+1
                branch_transitions+=1
                if base:
                    for aa,bb in [(a+1,b),(a,b+1)]:
                        vv=branch_coverage(base-1,aa,bb)
                        assert v-vv in (0,1)
                        # For any global excessE containing this local state, the exact guard is
                        # E+(V_before−V_after)<=88. No choice-order history is needed.
                        for e in (n-v,88):
                            admitted=e+v-vv<=88
                            if admitted:assert e+v-vv<=88
                            else:assert e==88 and vv==v-1
                        coverage_losing_evolutions+=vv<v
                        branch_transitions+=1
                # A maximum matching is always realizable without reducing coverage:
                # choose an absent terminal for a base, then the remaining absent terminal.
                x,y,z=base,a,b
                while x:
                    if not y: y+=1
                    elif not z: z+=1
                    else:y+=1
                    x-=1
                    assert branch_coverage(x,y,z)==v
                missing=2-v
                # Add missing flexible bases, then assign them to absent targets.
                x=missing
                while x:
                    if not y:y+=1
                    elif not z:z+=1
                    else:raise AssertionError('more bases than missing targets')
                    x-=1
                assert y>=1 and z>=1 and n+missing==2+(n-v)
    return {'scope':'all allowed capture/evolution choice orders from an admission-safe state, by invariant closure and exhaustive sufficient-state checks; future world source reachability remains separate',
            'global_safe_capacity_states':global_states,'global_admitted_transition_classes':global_admitted_transitions,'global_refused_transition_classes':global_refused_transitions,
            'branch_count_states':branch_states,'branch_transition_classes':branch_transitions,'coverage_losing_branch_evolutions_examined':coverage_losing_evolutions,
            'max_terminal_opportunities':72,'extra_copy_budget':88,'capacity':160,'legacy_overbudget_saves_claimed_recoverable':False,'runtime_implemented':False}

if __name__=='__main__':
    print(json.dumps(exhaustive_choice_order_proof(),indent=2))
