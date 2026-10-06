#!/usr/bin/env python3
"""Synthetic host-only Northern objective-order and capacity fault coverage.

This is deliberately NOT native acquisition or collection evidence. It calls the
production C runtime through the separately compiled host bridge from
 test_north_game.py and writes a plain, source-hashed report.
"""
from __future__ import annotations
import argparse, ctypes, hashlib, itertools, json
from pathlib import Path
from test_north_game import L, ROOT

MASKS={11:3,12:7,13:3,14:7,15:7,16:3,17:7,18:7,19:3,20:7,21:15}

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def grant(q):
    assert L.offer(q) in (0,1)
    for b in (1,2,4,8):
        if MASKS[q]&b:assert L.objective(q,b) in (1,2)
    assert L.claim(q)==3

def prepare(q):
    L.fresh();assert L.entry(22,0)==1
    if q==13:grant(11)
    if q>=16:
        grant(11);grant(13)
        for recruit in (12,14,15):grant(recruit)
    assert L.offer(q) in (0,1)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    cases=[]
    def record(case,**data):cases.append({'case':case,'passed':True,**data})
    for q,mask in MASKS.items():
        bits=[b for b in (1,2,4,8) if mask&b]
        for order in itertools.permutations(bits):
            prepare(q)
            if q==21:
                for bit in order:
                    before=L.qo(q);result=L.objective(q,bit)
                    accepted=before&(bit-1)==bit-1
                    assert result in (1,2) if accepted else result==4
                    assert L.qo(q)==(before|bit if accepted else before)
                # A wrong attempt cannot permanently strand a legal route.
                for bit in bits:
                    if not L.qo(q)&bit:assert L.objective(q,bit) in (1,2)
            else:
                for bit in order:assert L.objective(q,bit) in (1,2)
            assert L.qs(q)==2 and L.qo(q)==mask
            assert L.claim(q)==3 and L.qs(q)==3 and L.valid()==1
            L.snapshot_state();assert L.claim(q)==0 and L.unchanged()==1
            record('objective-order',quest=q,order=list(order),sequential=q==21)
    for q in range(11,16):
        prepare(q)
        for bit in (1,2,4):
            if MASKS[q]&bit:assert L.objective(q,bit) in (1,2)
        L.fill_roster();L.snapshot_state()
        assert L.claim(q)==5 and L.unchanged()==1 and L.qs(q)==2
        L.free_last();assert L.claim(q)==3
        record('synthetic-roster-full-atomic-retry',quest=q,capacity=160)
    for q in range(16,21):
        prepare(q)
        for bit in (1,2,4):
            if MASKS[q]&bit:assert L.objective(q,bit) in (1,2)
        L.bag_full(1);L.snapshot_state()
        assert L.claim(q)==5 and L.unchanged()==1 and L.qs(q)==2
        L.bag_full(0);assert L.claim(q)==3 and L.valid()==1
        record('synthetic-equipment-full-training-atomic-retry',quest=q)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps({'suite':'northern-synthetic-host-orders-capacity','native':False,'controller_only':False,
        'evidence_scope':'Synthetic host model/fault tests only. Does not establish cartridge acquisition, combat, or rendering.',
        'sources':{f:digest(ROOT/f) for f in ('src/north_game.c','src/northern_quests.c','src/save5.c','src/creatures.c','tests/test_north_game.py','tests/northern_host_cases.py')},
        'cases':cases,'count':len(cases)},indent=2)+'\n')
    print(f'{len(cases)} synthetic host cases pass; native obtainability remains separately gated')
if __name__=='__main__':main()
