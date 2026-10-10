#!/usr/bin/env python3
"""Spoiler-free controller recording of the experience-polish UI and exploration.

Uses the current-ROM controller-earned first-chapter save, inherits the exact
producer/ROM/bridge checks and lossless native RGB/audio verification. No game
RAM writes or machine-state imports. Public route stays in village/first field.
"""
import argparse,json
from pathlib import Path
from capture_player_feedback_teaser import Capture
from player_feedback_native import sha

class ExperienceCapture(Capture):
 def route(self):
  self.step(42);self.shot('native-village')
  # The direct courtyard path used to stop with an unsolicited locked-route
  # dialogue. Its ordinary LEFT approach now remains under player control.
  self.goto(x=67);self.goto(y=97);self.step(24);self.shot('native-shop-prompt')
  self.tap('A');assert self.g('game_state')==11;self.step(85);self.shot('native-shop-effects')
  gold=self.state().economy.gold;stock=self.state().economy.supplies[0]
  self.tap('A');self.step(48);self.shot('native-purchase-confirmation');self.tap('A');self.settle();self.step(55)
  assert self.state().economy.gold==gold-18 and self.state().economy.supplies[0]==stock+1
  self.tap('B');assert self.g('game_state')==1
  # A second previously interrupting village threshold lies on this crossing.
  self.goto(y=107);self.goto(x=120);self.goto(y=126);self.step(45)
  self.tap('START');self.step(45);self.tap('A');assert self.g('journal_tab')==15
  self.step(65);self.shot('native-items-effects');self.tap('B');assert self.g('journal_tab')==13
  self.tap('RIGHT');self.tap('A');assert self.g('journal_tab')==4;self.step(40);self.tap('RIGHT');self.step(35);self.tap('RIGHT');self.step(40)
  self.tap('B');self.tap('START');self.step(18,'L');self.step(18,'L+UP');self.step(18);self.step(18,'L');self.step(18,'L+RIGHT');self.step(25)
  self.goto(x=120)
  for _ in range(160):
   if self.g('room')==1:break
   self.step(1,'UP')
  assert self.g('room')==1;self.step(28);self.shot('native-walk-through-entrance');self.step(24)
  assert self.roster_progress()==self.before and self.g('chapter_flags')==self.before_flags[0]

 def finish(self):
  super().finish()
  p=self.out/'teaser-report.json';r=json.loads(p.read_text());r['scope']=__doc__
  r['inherited_capture_helper_sha256']=r['helper_sha256'];r['helper_sha256']=sha(__file__)
  r['capture_helpers']={name:sha(Path(__file__).parent/name) for name in ('capture_experience_teaser.py','capture_player_feedback_teaser.py','player_feedback_campaign.py','player_feedback_native.py')}
  p.write_text(json.dumps(r,indent=2)+'\n')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('rom','symbols','producer','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--producer-sha',required=True);a=p.parse_args();r=ExperienceCapture(a)
 try:r.prepare();r.begin();r.route();r.finish()
 finally:r.close()
if __name__=='__main__':main()
