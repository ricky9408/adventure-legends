#!/usr/bin/env python3
"""Native main route from genuine prior Sky-clear SRAM, with no ending/river grind.

The four story companions remain genuinely owned (including normal Kohaku resume
ownership). The Northern mandatory route never selects or commands Earth. All
Northern quest progress, two guaranteed recruits and machine damage use buttons.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from northern_journey import *
SKY_SHA='c77f7ac55c0103d4ad454dd642469f50318b5356ba76489c8802a608c896381d'

class SkyRoute(NorthernJourney):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fixture=ROOT/'tests/fixtures/v4/sky-complete.sav';assert digest(self.fixture)==SKY_SHA
        self.e.load_save(self.fixture);self.e.reset()
        self.provenance={'fixture_path':str(self.fixture),'sram_sha256':SKY_SHA,'source_machine_state_loaded':False,
            'scope':'Authentic prior Sky-clear story SRAM. No ending, Reedhaven quests, Northern progress or synthetic roster.'}
    def boot(self):
        self.step(150);self.tap('START',2,35);self.settle()
        self.check(self.get('chapter_flags')&3==3 and not self.get('chapter_flags')&12,'genuine Sky-clear fixture has no Core-clear or ending')
        self.check(all(self.quest(q)==0 for q in range(22)),'both new regions begin with zero quests')
        self.old_ids={c.instance_id for c in self.live()}
        self.check(any(c.form_id==10 for c in self.live()),'normal story/resume ownership retains Kohaku')
        self.snapshot('sky-clear-source')
        self.check(self.get('room')==0,'Sky-clear SRAM resumes at original village')
        self.goto(120,32);self.step(8,'UP');self.settle();self.check(self.get('room')==1,'normal Grove north route')
        self.goto(168,260)
        for _ in range(25):
            if self.get('room')==16:break
            self.face(1);self.tap('A',2,22);self.settle()
        self.check(self.get('room')==16,'first ordinary Reedhaven visit reaches ferry')
        self.entry(22)
        self.check(all(self.quest(q)==0 for q in range(11)),'ferry does not require any optional Reedhaven quest')
        self.snapshot('01-quay-entry-no-ending-or-river-quests')
    def main_route(self):
        self.recruits_main()
        for room in (26,27,28):self.puzzle_room(room)
        self.snapshot('04-machine-ready');self.machine(1)
        self.check(not set(self.main_selections)&{10,11,75,76},'Sky-clear mandatory route never selects Earth')
        self.check(self.old_ids<={c.instance_id for c in self.live()},'Sky-clear route retains all original owned companions')
        self.main_only=False;self.to_town();self.act(104,208)
        self.check(self.quest(21)==3 and not self.get('chapter_flags')&12,'Northern completion leaves earlier Core and ending unearned')
        self.check(all(self.quest(q)==0 for q in range(11)),'full Northern main remains independent of optional river quests')
        self.snapshot('sky-main-complete-without-earth-ending-river')
    def run(self,scope='main'):self.boot();self.main_route()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('rom','symbols','output'):p.add_argument('--'+k,required=True,type=Path)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True);a=p.parse_args()
    run=SkyRoute(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha)
    try:run.run()
    except Exception as e:run.failures.append({'error':str(e),'status':run.status()});run.snapshot('failure',settle=False);raise
    finally:run.report();run.e.close()
if __name__=='__main__':main()
