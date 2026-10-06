#!/usr/bin/env python3
"""Controller-only dense-scenery stress of the two most expensive signatures.

Actual earned collection is cold-imported for diagnostics only. Each origin is
reached by walking in the real Commons; no collision, enemy or player edits.
"""
import argparse,shutil
from pathlib import Path
from underwater_combat_native import UnderwaterCombat,digest,DIRECTIONS
SCENES=((304,176,3),(304,196,0),(304,248,3),(400,192,0),(408,224,2),(400,256,1),(176,80,2),(176,120,1),(96,128,1),(256,80,3),(368,80,2),(338,161,0))
class GeometryStress(UnderwaterCombat):
    def scenario(self,cmd,index,aim_right=False):
        x,y,d=SCENES[index];self.prepare(cmd);self.align(x,y,d);self.ready()
        label='scenery-'+str(cmd)+'-'+str(index)+('-aim-right' if aim_right else '')
        rows=self.trace(label,self.life[cmd-67]+8,lambda n:'R+'+DIRECTIONS[d] if n==0 else ('RIGHT+UP' if aim_right else 'RIGHT+DOWN' if d in (0,3) else 'LEFT+UP') if n<18 else ('LEFT+UP' if d in (0,3) else 'RIGHT+DOWN') if n<36 else 0,True)
        if aim_right:self.check(any(r['power']['age']<=2 and r['power']['aimed'] and r['power']['side']==1 for r in rows),'real early Right edge changes startup aim while continuing upward movement')
        self.check(any(r['power']['kind']==cmd and r['power']['time']>0 for r in rows),'real near-scenery R starts requested command')
        live=[r for r in rows if r['power']['time']];self.cases.append(dict(case='scenery-'+str(cmd)+'-'+str(index),requested_approach=[x,y,d],actual_origin=[live[0]['power']['origin_x'],live[0]['power']['origin_y']],actual_direction=live[0]['power']['direction'],camera_positions=len({tuple(r['camera']) for r in live}),hero_positions=len({tuple(r['hero']) for r in live}),passed=True))
    def sweep(self,only=None,aim_right=False):
        self.boot();self.test_sources['tests/underwater_geometry_stress_native.py']=digest(Path(__file__));shutil.copyfile(Path(__file__),self.out/'test-source/tests/underwater_geometry_stress_native.py')
        for cmd in (87,90):
            for i in ([5,1,7,8,3,0,2,4,6,9,10,11] if cmd==87 else range(len(SCENES))):
                if only and str(cmd)+':'+str(i) not in only.split(','):continue
                self.run_case('scenery-'+str(cmd)+'-'+str(i)+('-aim-right' if aim_right else ''),lambda cmd=cmd,i=i:self.scenario(cmd,i,aim_right))
        self.restore('combat-town-source');self.report()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('rom','symbols','output','source-report','source-manifest','producer-source-root'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('expected-rom-sha','expected-symbols-sha','source-report-sha'):p.add_argument('--'+n,required=True)
    p.add_argument('--acceptance',action='store_true');p.add_argument('--only');p.add_argument('--aim-right',action='store_true');a=p.parse_args();r=GeometryStress(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.source_report_sha,a.source_manifest,'11-all89-earned-town',not a.acceptance,a.producer_source_root,not a.acceptance)
    try:r.sweep(a.only,a.aim_right)
    finally:r.report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
