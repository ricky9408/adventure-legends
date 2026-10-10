#!/usr/bin/env python3
"""Spoiler-free continuous village morning, map and companion guide recording.

New Adventure is selected through actual title confirmation, starting from a
same-ROM authenticated disposable test save. The recording shows early story
beats, an explicit skip, then read-only menus and quick field switching.
No user save is loaded or overwritten. Native audio is captured, not reviewed
for musical quality. The inherited lossless-frame/audio/cadence gates apply.
"""
import argparse,json
from pathlib import Path
from capture_player_feedback_teaser import Capture
from player_feedback_native import sha

class JourneyCapture(Capture):
 allowed_capture_states=Capture.allowed_capture_states+(14,)
 def prepare(self):
  self.step(160);assert self.g('game_state')==0
  self.tap('DOWN');self.tap('A');assert self.g('game_state')==9
  self.tap('A');self.step(6);assert self.g('game_state')==14
  assert self.e.read(self.sym['opening_page'],1)==0
  self.before=self.roster_progress();self.before_flags=(self.g('chapter_flags'),self.g('room_flags'))
  self.e.save(self.out/'capture-start.sav')
 def route(self):
  self.step(150);self.shot('native-village-morning')
  for page in range(1,4):
   self.tap('A');assert self.e.read(self.sym['opening_page'],1)==page
   self.step(150)
  self.shot('native-lantern-story');self.tap('START');self.settle();self.step(135)
  assert self.g('game_state')==1 and self.g('room')==0
  self.shot('native-ready-to-explore')
  self.tap('START');self.step(45);self.tap('DOWN');self.tap('DOWN');self.tap('A')
  assert self.g('journal_tab')==1
  self.step(130);self.shot('native-known-roads');self.tap('A');self.step(75);self.tap('B');self.step(24);self.tap('B')
  assert self.g('journal_tab')==13
  self.tap('UP');self.tap('A');assert self.g('journal_tab')==2
  self.tap('A');self.step(130);self.shot('native-companion-description')
  self.tap('DOWN');self.step(100);self.shot('native-companion-field-help')
  self.tap('B');self.tap('B');self.tap('START');assert self.g('game_state')==1
  self.step(18,'L');self.step(18,'L+RIGHT');self.step(24)
  self.tap('B');self.step(48);self.shot('native-companion-together')
  self.goto(x=120);self.goto(y=40)
  for _ in range(300):
   if self.g('room')==1:break
   self.step(1,'UP')
  assert self.g('room')==1;self.settle();self.step(60);self.shot('native-next-road')
  # Field selection is intentional; no growth, assignment or command changes.
  after=self.roster_progress();assert after[:2]==self.before[:2] and after[3:]==self.before[3:]
  assert self.g('chapter_flags')==self.before_flags[0]
 def finish(self):
  super().finish();path=self.out/'teaser-report.json';report=json.loads(path.read_text())
  report['scope']=__doc__;report['inherited_capture_helper_sha256']=report['helper_sha256'];report['helper_sha256']=sha(__file__)
  report['initialization']='Actual New Adventure confirmation on a disposable same-ROM generated test save; no synthetic game RAM or state imports.'
  report['opening_pages_shown']=[0,1,2,3];report['opening_skip']='Fresh Start, shown continuously'
  report['capture_helpers']={name:sha(Path(__file__).parent/name)for name in ('capture_journey_guidance_teaser.py','capture_player_feedback_teaser.py','player_feedback_campaign.py','player_feedback_native.py')}
  path.write_text(json.dumps(report,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','symbols','producer','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--producer-sha',required=True);a=p.parse_args();r=JourneyCapture(a)
 try:r.prepare();r.begin();r.route();r.finish()
 finally:r.close()
if __name__=='__main__':main()
