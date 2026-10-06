#!/usr/bin/env python3
"""Natural animation-phase sweep at the controller-reached worst cast origin.
Uses only ordinary idle updates and buttons, with exact-ROM state/SRAM branches.
"""
import argparse,shutil
from pathlib import Path
from underwater_combat_native import UnderwaterCombat,digest
class PhaseStress(UnderwaterCombat):
    def sweep(self):
        self.boot();self.test_sources['tests/underwater_phase_stress_native.py']=digest(Path(__file__));shutil.copyfile(Path(__file__),self.out/'test-source/tests/underwater_phase_stress_native.py')
        self.prepare(87);self.align(400,256,1);self.ready();self.snapshot('natural-phase-source',False)
        for delay in range(32):
            def probe(delay=delay):
                self.restore('natural-phase-source');self.step(delay)
                rows=self.trace('natural-phase-'+str(delay),60,lambda n:'R+UP' if n==0 else 'RIGHT+UP' if n<18 else 'RIGHT+DOWN' if n<36 else 0,True)
                self.check(any(r['power']['kind']==87 and r['power']['time'] for r in rows),'actual command87 starts after the natural animation phase offset')
                self.cases.append(dict(case='natural-phase-'+str(delay),idle_updates=delay,passed=True))
            self.run_case('natural-phase-'+str(delay),probe)
        self.restore('combat-town-source');self.report()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('rom','symbols','output','source-report','source-manifest','producer-source-root'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('expected-rom-sha','expected-symbols-sha','source-report-sha'):p.add_argument('--'+n,required=True)
    p.add_argument('--acceptance',action='store_true');a=p.parse_args();r=PhaseStress(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.source_report_sha,a.source_manifest,'11-all89-earned-town',not a.acceptance,a.producer_source_root,not a.acceptance)
    try:r.sweep()
    finally:r.report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
