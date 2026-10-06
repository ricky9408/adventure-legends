#!/usr/bin/env python3
"""Paired read-only diagnostics for a frozen native Underwater cast.
Inclusive profile wrappers affect timings; this is never release acceptance.
"""
import argparse,shutil,struct
from pathlib import Path
from underwater_geometry_stress_native import GeometryStress
from underwater_combat_native import digest
LABELS=('cast','geometry','certify_box','clear','field_overlap','clear_box','supercover')
class ProfileRun(GeometryStress):
    def row(self):
        row=super().row()
        if 'underwater_power_profile' in self.sym:
            raw=struct.unpack('<21I',self.e.bytes(self.sym['underwater_power_profile'],84))
            row['inclusive_profile']={name:dict(zip(('calls','cycles','maximum_cycles'),raw[i*3:i*3+3])) for i,name in enumerate(LABELS)}
        return row

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('rom','symbols','output','source-report','source-manifest','producer-source-root'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('expected-rom-sha','expected-symbols-sha','source-report-sha'):p.add_argument('--'+n,required=True)
    a=p.parse_args();r=ProfileRun(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.source_report_sha,a.source_manifest,'11-all89-earned-town',True,a.producer_source_root,True)
    r.source_evidence.update(instrumented_profile='underwater_power_profile' in r.sym,profile_caveat='Inclusive nested timer calls and wrapper inlining overhead; not release timing acceptance')
    r.test_sources['tests/underwater_profile_native.py']=digest(Path(__file__));shutil.copyfile(Path(__file__),r.out/'test-source/tests/underwater_profile_native.py')
    try:r.sweep('87:5',True)
    finally:r.report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
