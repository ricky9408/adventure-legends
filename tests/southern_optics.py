#!/usr/bin/env python3
"""Native controller enumeration of every reachable incomplete optical state.

Room34 has2 controller-reachable states; rooms35/36 each have8. Immutable-ROM
collision descriptors route every walk. Each branch proves manual escape,
reentry, reset, and a solution with the guaranteed bases, without RAM writes.
This complements the separate synthetic host24-state pure-optics enumeration.
"""
import argparse, itertools
from pathlib import Path
from southern_journey import SouthernJourney

class SouthernOptics(SouthernJourney):
    def arrange(self,desired):
        keys=('mirror0','mirror1','shade')
        for i,key in enumerate(keys):
            if self.puzzle()[i]!=desired[i]:self.use(key)
        self.check(self.puzzle()==list(desired),'actual controller input reaches requested finite optical arrangement')
    def run(self,scope=None):
        self.boot();self.recruits_main()
        for room in (34,35,36):
            base=f'optics-{room}-base';self.snapshot(base);initial=self.puzzle();bit=1<<(room-34)
            states=[(0,0,1),(1,0,1)] if room==34 else list(itertools.product(range(2),repeat=3))
            for index,state in enumerate(states):
                self.restore(base);self.arrange(state);before=self.state().quests.objectives[24]
                if room in (34,35):self.check(not before&bit,'manual arrangements cannot grant required Water/Metal objective')
                self.snapshot(f'optics-{room}-state-{index}')
                if index==0:
                    puzzle=self.puzzle();objectives=bytes(self.state().quests);self.open_tab(7)
                    for key in ('UP','DOWN','R','LEFT','RIGHT'):self.tap(key,2,3)
                    self.check(self.puzzle()==puzzle and bytes(self.state().quests)==objectives,'journal navigation and command inputs freeze optical arrangement and objectives');self.close_menu()
                # The player really walks to the escape in each arrangement.
                self.leave_interior(31 if room==34 else room-1);self.entry(room)
                after=self.state().quests.objectives[24];self.check(after==before,'escape/reentry fabricates no objective')
                self.use('reset');self.check(self.state().quests.objectives[24]==before,'manual reset preserves exact durable prefix')
                desired=(1,0,1) if room==34 else (1,1,0) if room==35 else (0,0,0)
                self.arrange(desired)
                if room in (34,35):self.field_object('receiver',79 if room==34 else 85)
                self.check(self.state().quests.objectives[24]&bit,'guaranteed base/manual solution stays reachable after escape and reset')
                self.cases.append({'case':'native-optical-safety','room':room,'initial_state':state,'before_prefix':before,'completed_prefix':self.state().quests.objectives[24],'passed':True});self.report()
            self.entry(room+1)
        self.snapshot('all18-native-optical-states');self.coverage.append('all18-reachable-native-optical-states-escape-reset-reentry-solution')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','symbols','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True);p.add_argument('--scene-only',action='store_true');p.add_argument('--source-manifest',type=Path)
    a=p.parse_args();run=SouthernOptics(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,scene_only=a.scene_only,source_manifest=a.source_manifest)
    try:run.run()
    except Exception as exc:run.failures.append({'error':str(exc),'status':run.status()});run.snapshot('failure',settle=False);raise
    finally:run.report();run.e.close()
if __name__=='__main__':main()
