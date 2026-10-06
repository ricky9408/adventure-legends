#!/usr/bin/env python3
"""Same-ROM native machine timing, modal pause, attack priority and retry cases."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from northern_stress import NorthernStress
from northern_journey import *

class BossControls(NorthernStress):
    def activate(self):
        self.cast_owned(19,64,124);self.cast_owned(77,176,124);self.goto(120,124)
        self.tap('A',1,0);self.check(self.get('north_game_machine_stage',1)==1,'actual handle begins machine telegraph')
    def run(self,scope='all'):
        self.restore('04-machine-ready');self.equip_item(0,1)
        self.goto(120,80);self.face(1);self.tap('A',2,25)
        self.check(self.get('north_game_machine_hp',1)==128,'ordinary sword cannot damage closed coupling before activation')
        self.activate();self.snapshot('boss-controls-activated')
        changes=[];before=self.get('north_game_machine_stage',1)
        for _ in range(230):
            self.step(1);stage=self.get('north_game_machine_stage',1)
            if stage!=before:
                changes.append({'stage':stage,'timer':self.get('north_game_machine_ticks',1),'active_tick':self.get('ticks'),'hardware_frame':self.e.frame})
                before=stage
        self.check([(r['stage'],r['timer']) for r in changes[:4]]==[(2,24),(3,90),(4,30),(1,60)],'native timer transitions expose exact24/90/30/60 active-update windows')
        self.check([changes[i+1]['active_tick']-changes[i]['active_tick'] for i in range(3)]==[24,90,30],'native elapsed active updates match each telegraphed stage duration')
        self.cases.append({'case':'native-machine-stage-timing','transitions':changes,'passed':True})
        self.restore('boss-controls-activated');self.tap('START',1,2)
        self.check(self.get('game_state')==PAUSE,'actual journal opens during machine telegraph')
        held=(self.get('north_game_machine_stage',1),self.get('north_game_machine_ticks',1),self.get('north_game_machine_hp',1))
        self.step(180);self.check(held==(self.get('north_game_machine_stage',1),self.get('north_game_machine_ticks',1),self.get('north_game_machine_hp',1)),'paused journal freezes machine stage timer and health')
        self.close_menu();self.goto(120,108);self.tap('A',1,1)
        self.check(self.get('game_state')==PLAY,'active central handle does not swallow real weapon A into clue dialogue')
        self.check(self.action()['class']==1 and self.action()['phase']!=0,'near-handle A starts a real sword action during the encounter')
        self.step(40);self.act(32,132)
        self.check(self.get('north_game_machine_stage',1)==0 and self.get('north_game_machine_hp',1)==128,'always reachable west reset safely restores active machine')
        self.exit_north(28);self.entry(29)
        self.check(self.get('north_game_machine_stage',1)==0 and self.get('north_game_machine_hp',1)==128,'unfinished machine safely resets after ordinary exit/reentry')
        self.activate();self.goto(120,87)
        before_quests=bytes(self.state().quests);before_ids={c.instance_id for c in self.live()}
        for _ in range(300):
            if self.get('game_state')==DEAD:break
            self.step(10)
        self.check(self.get('game_state')==DEAD,'real telegraphed sweep damage reaches death without health injection')
        self.e.screenshot(self.out/'boss-ordinary-sweep-death.png');self.tap('A',2,30);self.settle()
        self.check(self.get('room')==29 and self.get('north_game_machine_stage',1)==0 and self.get('north_game_machine_hp',1)==128,'ordinary retry returns to a safe unstarted machine checkpoint')
        self.check(bytes(self.state().quests)==before_quests and {c.instance_id for c in self.live()}==before_ids,'machine death/retry preserves earned objectives and instance identities')
        self.snapshot('boss-controls-retry-complete')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('rom','symbols','output','journey-report'):p.add_argument('--'+k,required=True,type=Path)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True);a=p.parse_args()
    run=BossControls(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,journey_report=a.journey_report)
    try:run.run()
    except Exception as e:run.failures.append({'error':str(e),'status':run.status()});run.snapshot('boss-controls-failure',settle=False);raise
    finally:run.report();run.e.close()
if __name__=='__main__':main()
