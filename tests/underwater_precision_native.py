#!/usr/bin/env python3
"""Diagnostic placement refinement for thin authored Underwater signatures.

Planning predicts controller steps only. Runtime position is always produced by
actual D-pad input, then checked independently. No RAM edits or enemy grants.
Exact-pixel planning is a developer probe, not evidence of easy player aiming.
"""
import argparse,heapq,shutil
from pathlib import Path
from underwater_combat_native import UnderwaterCombat,ROOT,digest
class PrecisionCombat(UnderwaterCombat):
    def align(self,x,y,direction):
        self.goto(x,y,radius=3)
        mask,w,h=self.mask();speed=self.e.read(self.sym['gear_stats']+2,2);diag=self.e.read(self.sym['gear_stats']+4,2)
        start=(self.get('px_q8'),self.get('py_q8'),self.get('face'));actions=((1,0,'RIGHT'),(-1,0,'LEFT'),(0,-1,'UP'),(0,1,'DOWN'),(1,-1,'RIGHT+UP'),(-1,-1,'LEFT+UP'),(1,1,'RIGHT+DOWN'),(-1,1,'LEFT+DOWN'))
        q=[(0,0,start,())];seen={start:0};route=None
        while q and len(seen)<150000:
            _,cost,state,path=heapq.heappop(q);qx,qy,face=state
            if (qx>>8,qy>>8,face)==(x,y,direction):route=path;break
            if cost>=12:continue
            for dx,dy,key in actions:
                nx,ny=qx,qy;mx,my=dx*(diag if dx and dy else speed),dy*(diag if dx and dy else speed)
                while mx or my:
                    sx=max(-256,min(256,mx));sy=max(-256,min(256,my));oldx,oldy=nx>>8,ny>>8
                    ax,ay=nx+sx,ny+sy
                    if 0<=ax>>8<w and 0<=oldy<h and not mask[oldy*w+(ax>>8)]:nx=ax
                    if 0<=oldx<w and 0<=ay>>8<h and not mask[(ay>>8)*w+oldx]:ny=ay
                    mx-=sx;my-=sy
                nf=(0 if dy>0 else 1) if dy else 3 if dx>0 else 2
                st=(nx,ny,nf)
                if abs((nx>>8)-x)>7 or abs((ny>>8)-y)>7 or seen.get(st,999)<=cost+1:continue
                seen[st]=cost+1;distance=abs((nx>>8)-x)+abs((ny>>8)-y)+(nf!=direction)*0.25
                heapq.heappush(q,(cost+1+distance/2,cost+1,st,path+(key,)))
        self.check(route is not None,'read-only near-target planning finds finite actual D-pad route')
        before=[self.get('px'),self.get('py'),self.get('face')]
        for key in route:self.step(1,key)
        self.step(1)
        after=[self.get('px'),self.get('py'),self.get('face')]
        self.cases.append({'case':'developer-controller-precision-placement','before':before,'wanted':[x,y,direction],'after':after,'keys':list(route),'predicted_not_runtime_evidence':True})
        self.check(after==[x,y,direction],'actual ordinary D-pad reaches exact requested test position and facing')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('rom','symbols','output','source-report','source-manifest','producer-source-root'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('expected-rom-sha','expected-symbols-sha','source-report-sha'):p.add_argument('--'+n,required=True)
    p.add_argument('--acceptance',action='store_true');p.add_argument('--cold-cross-rom',action='store_true');p.add_argument('--case',default='direct-71,direct-80,direct-81,direct-84,direct-87');a=p.parse_args()
    r=PrecisionCombat(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.source_report_sha,a.source_manifest,'11-all89-earned-town',not a.acceptance,a.producer_source_root,a.cold_cross_rom)
    r.test_sources['tests/underwater_precision_native.py']=digest(Path(__file__));shutil.copyfile(Path(__file__),r.out/'test-source/tests/underwater_precision_native.py')
    try:r.run(a.case)
    finally:r.report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
