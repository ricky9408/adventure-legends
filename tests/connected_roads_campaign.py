#!/usr/bin/env python3
"""Fresh controller campaign over the connected exterior roads.

Inherits all three-boss, quest, earned evolution and save-interruption assertions.
Only the changed village/Grove/ridge/cave path approaches are adapted. No game
RAM writes, machine-state imports or synthetic progression are permitted.
"""
import argparse,json,shutil,traceback
from pathlib import Path
from player_feedback_campaign import FeedbackCampaign,sha
ROOT=Path(__file__).resolve().parents[1]
class ConnectedCampaign(FeedbackCampaign):
 def __init__(self,*args):
  self.connected_helper=sha(__file__);self.connected_manifest=sha(ROOT/'assets/connected_roads.json')
  super().__init__(*args);shutil.copyfile(__file__,self.out/'connected_roads_campaign.py')
 def crossing(self,target):
  source=self.get('room');directions={(0,1):'UP',(1,0):'DOWN',(0,4):'RIGHT',(4,0):'LEFT',(0,9):'LEFT',(9,0):'RIGHT'}
  key=directions[(source,target)]
  if source==0:
   self.goto(x=120);self.goto(y=109 if target==9 else 124 if target==4 else 40)
  elif source==1:self.goto(x=240);self.goto(y=296)
  elif source==4:self.navigate(120,132);self.goto(y=124);self.goto(x=40)
  elif source==9:self.navigate(120,132);self.goto(x=200)
  for _ in range(450):
   if self.get('room')==target:break
   self.step(1,key)
  self.check(self.get('room')==target,f'controller cardinal road {source}->{target}')
  self.step(25);self.dialogs();self.check(self.get('room')==target,'opposite-edge arrival stays in its destination')
 def hub(self,target):
  self.check(self.get('room')==0,'chapter road starts in village');self.crossing(target)
 def nextroom(self,target,key='UP'):
  if (self.get('room'),target) in ((0,1),(1,0),(0,4),(4,0),(0,9),(9,0)):return self.crossing(target)
  return super().nextroom(target,key)
 def report(self):
  super().report()
  if not hasattr(self,'out'):return
  p=self.out/'player-feedback-campaign.json'
  if p.exists():
   d=json.loads(p.read_text());d['suite']='connected-roads-fresh-campaign';d['connected_helper_sha256']=self.connected_helper;d['road_manifest_sha256']=self.connected_manifest;p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('rom','symbols','bridge','output'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();r=ConnectedCampaign(a.rom,a.symbols,a.output,a.bridge)
 try:r.run()
 except Exception as e:r.failures.append({'error':repr(e),'status':r.status()});r.shot('failure');traceback.print_exc()
 finally:r.report();r.trace.close();r.e.close()
 return int(not r.route_complete or bool(r.failures) or any(r.metrics[k] for k in ('update_misses','flip_misses','cycle_overruns','faults','publication_spills')))
if __name__=='__main__':raise SystemExit(main())
