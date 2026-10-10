#!/usr/bin/env python3
"""Spoiler-free continuous native road crossing, scrolling and return recording.

Starts from this exact candidate's authenticated controller-earned first-chapter
SRAM. Buttons alone drive the route. Captures native RGB and actual emulator
sound, retaining the inherited frame/audio/lossless-master checks. No listening
quality claim or synthetic progression is made.
"""
import argparse,json
from pathlib import Path
from capture_player_feedback_teaser import Capture
from player_feedback_native import sha

class RoadCapture(Capture):
 def prepare(self):
  super().prepare()
  self.step(120)
  assert not self.g('toast_ticks')
 def clear_arrival(self):
  self.settle()
  for _ in range(300):
   if not self.g('transition') and not self.g('scene_present_phase'):break
   self.step()
  else:raise AssertionError('arrival did not become visible')
  self.step(36)
 def cross(self,target,key):
  for _ in range(400):
   if self.g('room')==target:break
   self.step(1,key)
  assert self.g('room')==target,('road did not cross',target,key)
  self.clear_arrival()
 def route(self):
  self.step(45);self.shot('native-village-roads')
  self.goto(x=120);self.goto(y=40);self.step(24)
  self.cross(1,'UP');self.shot('native-grove-south-arrival')
  # Follow the same road into a larger map. The camera starts scrolling before
  # any map exit: only the actual world boundary owns the return transition.
  initial_camera=self.g('camera_y');self.goto(x=240);self.goto(y=216)
  self.step(32);assert self.g('room')==1 and self.g('camera_y')<initial_camera
  self.shot('native-scrolling-road')
  self.step(18,'L');self.step(16,'L+UP');self.step(22)
  self.step(18,'L');self.step(16,'L+RIGHT');self.step(24)
  self.goto(x=240);self.goto(y=296);self.step(18)
  self.cross(0,'DOWN');self.shot('native-village-north-arrival')
  self.goto(y=79);self.step(44);self.shot('native-connected-village')
  assert self.roster_progress()==self.before and self.g('chapter_flags')==self.before_flags[0]
 def finish(self):
  super().finish()
  p=self.out/'teaser-report.json';r=json.loads(p.read_text());r['scope']=__doc__
  r['inherited_capture_helper_sha256']=r['helper_sha256'];r['helper_sha256']=sha(__file__)
  r['capture_helpers']={name:sha(Path(__file__).parent/name) for name in ('capture_connected_roads_teaser.py','capture_player_feedback_teaser.py','player_feedback_campaign.py','player_feedback_native.py')}
  r['road_manifest_sha256']=sha(Path(__file__).resolve().parents[1]/'assets/connected_roads.json')
  p.write_text(json.dumps(r,indent=2)+'\n')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('rom','symbols','producer','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--producer-sha',required=True);a=p.parse_args();r=RoadCapture(a)
 try:r.prepare();r.begin();r.route();r.finish()
 finally:r.close()
if __name__=='__main__':main()
