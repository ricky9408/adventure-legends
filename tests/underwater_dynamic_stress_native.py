#!/usr/bin/env python3
"""Real-controller command87 stress with dense town actors and both Stacks walls.
Ballast changes are earned casts; no RAM edits or synthetic collision states.
"""
import argparse,shutil
from pathlib import Path
from underwater_combat_native import UnderwaterCombat,digest,DIRECTIONS
class DynamicStress(UnderwaterCombat):
    def probe_scene(self,room,ballast,x,y,d):
        self.restore('combat-town-source');self.owned_select(69);self.set_command(87);self.ready()
        if room!=46:self.travel(room)
        if ballast:
            self.owned_select(53);self.set_command(70);self.ready();self.align(176,168,1)
            self.trace('real-ballast-change',120,lambda n:'R' if n==0 else 0,True);self.settle()
            self.check(self.e.read(self.sym['underwater_game_puzzle']+2,1)==1,'real controller cast changes Stacks ballast to alternate wall state')
            self.owned_select(69);self.set_command(87);self.ready()
        self.check(self.get('room')==room and self.e.read(self.sym['underwater_game_puzzle']+2,1)==ballast,'probe observes the actual intended room and puzzle geometry')
        self.align(x,y,d);self.ready();before=list(self.e.bytes(self.sym['underwater_game_puzzle'],8))
        rows=self.trace('dynamic-'+str(room)+'-'+str(ballast)+'-'+str(x)+'-'+str(y),60,lambda n:'R+'+DIRECTIONS[d] if n==0 else ('RIGHT+UP' if d==1 else 'LEFT+UP') if n<18 else 'RIGHT+DOWN' if n<36 else 0,True)
        live=[r for r in rows if r['power']['kind']==87 and r['power']['time']]
        self.check(bool(live),'command87 actually runs in the dense-actor or dynamic-wall room')
        self.cases.append(dict(case=self.current_case,room=room,ballast=ballast,puzzle_before=before,puzzle_after=list(self.e.bytes(self.sym['underwater_game_puzzle'],8)),actual_origin=[live[0]['power']['origin_x'],live[0]['power']['origin_y']],actual_direction=live[0]['power']['direction'],camera_positions=len({tuple(r['camera']) for r in live}),hero_positions=len({tuple(r['hero']) for r in live}),passed=True))
    def sweep(self):
        self.boot();self.test_sources['tests/underwater_dynamic_stress_native.py']=digest(Path(__file__));shutil.copyfile(Path(__file__),self.out/'test-source/tests/underwater_dynamic_stress_native.py')
        for args in ((46,0,240,200,1),(46,0,304,176,2),(51,0,278,170,1),(51,1,302,170,1)):
            self.run_case('room-'+str(args[0])+'-ballast-'+str(args[1])+'-x'+str(args[2]),lambda args=args:self.probe_scene(*args))
        self.restore('combat-town-source');self.report()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('rom','symbols','output','source-report','source-manifest','producer-source-root'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('expected-rom-sha','expected-symbols-sha','source-report-sha'):p.add_argument('--'+n,required=True)
    p.add_argument('--acceptance',action='store_true');a=p.parse_args();r=DynamicStress(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.source_report_sha,a.source_manifest,'11-all89-earned-town',not a.acceptance,a.producer_source_root,not a.acceptance)
    try:r.sweep()
    finally:r.report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
