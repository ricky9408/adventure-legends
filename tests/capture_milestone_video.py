#!/usr/bin/env python3
"""Controller-only optional-route movie, streamed to ffmpeg at real GBA cadence."""
from pathlib import Path
import json,subprocess
import playthrough as T
ROOT=T.ROOT;OUT=ROOT/'build/milestone-video';OUT.mkdir(parents=True,exist_ok=True);T.OUT=OUT
class Movie(T.Play):
 def __init__(self):
  super().__init__(False)
  self.encoder=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','240x160','-r','59.7275','-i','-','-vf','scale=960:640:flags=neighbor','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p',str(OUT/'silent.mp4')],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
  self.e.audio_start(OUT/'gameplay.wav')
 def step(self,n,key=0):
  for _ in range(n):
   self.e.frames(1,key);self.encoder.stdin.write(self.e.screenshot().tobytes())
 def finish(self):
  self.e.audio_stop();self.encoder.stdin.close();assert self.encoder.wait()==0
  subprocess.run(['ffmpeg','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'gameplay.wav'),'-c:v','copy','-c:a','aac','-shortest','-movflags','+faststart',str(OUT/'emberbond-gameplay.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  (OUT/'capture.json').write_text(json.dumps({'controller_only':True,'game_ram_injection':False,'frames':self.e.frame,'final':self.status(),'max_hp':self.get('max_hp'),'relic_found':self.get('relic_found'),'camp_unlocked':self.get('camp_unlocked')},indent=2)+'\n');self.e.close()
p=Movie()
try:
 p.step(120);p.tap('START');p.dialogs();p.step(60);p.nextroom(1);p.step(60);p.shot('01-scrolling-arrival')
 p.goto(y=248);p.goto(x=136);p.defend(90);p.goto(x=136,y=248);p.tap('A');p.check(p.get('camp_unlocked')==1,'camp recorded');p.step(120);p.shot('02-campfire');p.dialogs()
 p.tap('START');p.step(120);p.shot('03-field-map');p.tap('A');p.step(60);p.tap('B')
 p.goto(x=240,y=180);p.tap('L');p.tap('B');p.tap('R');p.check(p.get('bridge_open')==1,'bridge grown');p.step(90);p.dialogs();p.step(60);p.shot('04-river-crossing')
 p.goto(y=92);p.goto(x=92);p.goto(y=88);p.tap('A');p.check(p.get('relic_found')==1,'optional relic discovered');p.step(120);p.dialogs();p.defend(90);p.shot('05-relic-upgrade')
 p.goto(y=92);p.goto(x=330);p.tap('L');p.step(60);p.step(2,'RIGHT');p.tap('SELECT');p.step(45);p.tap('R');p.step(40);p.shot('06-ranged-combat');p.goto(x=368)
 for _ in range(200):
  if p.get('room')==2:break
  p.step(2,'UP')
 p.check(p.get('room')==2,'temple reached');p.dialogs();p.goto(y=94);p.goto(x=64);p.goto(y=84);p.defend(160);p.goto(x=64,y=84);p.tap('R');p.check(p.get('torches')==1,'first brazier');p.goto(y=94);p.goto(x=176);p.goto(y=84);p.defend(160);p.goto(x=176,y=84);p.tap('R');p.check(p.get('torches')==3,'temple opened');p.dialogs();p.goto(y=94);p.goto(x=120);p.nextroom(3);p.dialogs();p.goto(y=100);p.step(160);p.tap('R');p.goto(y=92)
 for _ in range(30):
  if p.get('game_state')==2:break
  if p.get('boss_armor')<50 and not p.get('ability_cd'):p.tap('R')
  p.goto(x=p.get('boss_x'),y=p.get('boss_y')+28);p.step(2,'UP');p.step(2);p.tap('A');p.step(22)
 p.check(p.get('boss_hp')==0,'guardian defeated');p.dialogs();p.check(p.get('game_state')==5,'chapter ending');p.step(180);p.finish()
except Exception:
 p.encoder.stdin.close();p.encoder.wait();p.e.close();raise
