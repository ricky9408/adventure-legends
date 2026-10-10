#!/usr/bin/env python3
"""Add a complete authentic roster-menu cycle to observe_horizons_stack.py.

Use the same run arguments with --scope roster and a fresh --output directory.
This extends only the host navigator; it cannot write game RAM or load states.
"""
from horizons_journey import HorizonsJourney
import observe_horizons_stack as observer

original_open_tab = HorizonsJourney.open_tab


def visit_full_roster(self, tab):
    original_open_tab(self, tab)
    if tab != 2 or getattr(self, '_stack_full_roster_seen', False):
        return
    expected={i for i,c in enumerate(self.roster().instances) if c.flags&1}
    seen=set()
    for _ in range(len(expected)+2):
        seen.add(self.get('quickparty_menu_candidate'))
        self.tap('DOWN',2,4)
    self.check(seen==expected|{255},'normal roster navigation visits every authentic individual and empty choice')
    self.cases.append({'complete_roster_menu_cycle':True,'visited_slots':sorted(seen),
                       'authentic_individuals':len(expected),'game_ram_writes':0})
    self._stack_full_roster_seen=True
    self.observe('complete-authentic-roster-menu-cycle')


if __name__=='__main__':
    HorizonsJourney.open_tab=visit_full_roster
    observer.main()
