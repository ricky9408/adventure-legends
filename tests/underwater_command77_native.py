#!/usr/bin/env python3
"""Diagnostic-only controller-acquired Gateshield usability probe.

Starts from a hash-pinned, controller-earned intermediate SRAM whose producer
failed its later timing gate. That failure is preserved and this run is excluded
from final acceptance. The terminal is acquired here by its actual trial/menu.
"""
import argparse,json,shutil
from pathlib import Path
from underwater_combat_native import UnderwaterCombat,ROOT,digest
class Command77(UnderwaterCombat):
    def acquire_and_probe(self):
        self.boot();self.test_sources['tests/underwater_command77_native.py']=digest(Path(__file__))
        dest=self.out/'test-source/tests/underwater_command77_native.py';shutil.copyfile(Path(__file__),dest)
        identity,idx=self.start_underwater_trial(58,1);self.solve_underwater_trial(idx)
        self.check(idx==6 and self.selected().instance_id==identity and self.selected().trial_flags&1,'real third-family trial earns command77 branch proof for exact individual')
        self.to_town();self.target(80,256);self.owned_select(58);self.open_tab(3);self.tap('SELECT');self.wait_evolution()
        if self.get('progression_evolution_target')!=59:self.tap('RIGHT')
        self.check(self.get('progression_evolution_target')==59,'native confirmation selects genuinely earned Gateshield branch')
        self.current_case='diagnostic-acquire-command77';self.trace('native-evolution-command77',180,lambda n:'A' if n<4 else 0)
        self.settle();self.close_menu();self.check(self.selected().form_id==59 and self.selected().instance_id==identity,'actual confirmed evolution preserves earned individual identity')
        self.forms={c.form_id for c in self.live()};self.set_command(77);self.ready();self.snapshot('combat-town-source')
        self.run_case('command77',self.command77)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('rom','symbols','output','source-report','source-manifest'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('expected-rom-sha','expected-symbols-sha','source-report-sha'):p.add_argument('--'+n,required=True)
    p.add_argument('--producer-source-root',type=Path);a=p.parse_args();r=Command77(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.source_report_sha,a.source_manifest,'10-all-eight-families-and-stories',True,a.producer_source_root)
    try:r.acquire_and_probe()
    except Exception as exc:r.failures.append({'case':'diagnostic-acquire-command77','error':str(exc),'status':r.status()});r.snapshot('diagnostic-acquisition-failure',False);raise
    finally:r.report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
