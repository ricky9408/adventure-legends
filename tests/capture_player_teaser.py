#!/usr/bin/env python3
"""Spoiler-free opening footage: actual native frames and emulator audio."""
from pathlib import Path
import sys,json,subprocess,hashlib
import playthrough as T
OUT=T.ROOT/'build/player-teaser';OUT.mkdir(parents=True,exist_ok=True);T.OUT=OUT
class Teaser(T.Play):
 def __init__(self):
  super().__init__(False)
  self.encoder=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','240x160','-r','59.72750056960583','-i','-','-vf','scale=960:640:flags=neighbor','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p',str(OUT/'silent.mp4')],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
  self.e.audio_start(OUT/'audio.wav');self.count=0
 def step(self,n,key=0):
  for _ in range(n):self.e.frames(1,key);self.encoder.stdin.write(self.e.screenshot().tobytes());self.count+=1
 def finish(self):
  self.e.audio_stop();self.encoder.stdin.close();assert self.encoder.wait()==0
  subprocess.run(['ffmpeg','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'audio.wav'),'-c:v','copy','-c:a','aac','-shortest','-movflags','+faststart',str(OUT/'emberbond-gameplay.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  (OUT/'capture.json').write_text(json.dumps({'controller_only':True,'game_ram_writes':0,'frames':self.count,'duration_seconds':self.count/59.72750056960583,'scope':'Opening village and southern grove only; no boss solution, reward location, late companion or ending','rom_sha256':hashlib.sha256((T.ROOT/'build/emberbond.gba').read_bytes()).hexdigest()},indent=2));self.e.close()
p=Teaser()
try:
 p.step(90);p.tap('START');p.dialogs();p.step(50);p.shot('village');p.nextroom(1);p.step(25);p.shot('grove')
 p.tap('B');p.step(90);p.shot('homura');p.goto(y=236);p.step(1,'LEFT');p.tap('A');p.step(12);p.tap('A');p.step(14);p.tap('A');p.step(30);p.tap('R');p.step(55);p.step(1,'RIGHT');p.tap('SELECT');p.step(45);p.goto(x=290);p.goto(y=245);p.defend(150);p.shot('sword');p.goto(x=260);p.goto(y=262);p.tap('L');p.step(70);p.tap('R');p.step(40);p.shot('midori');p.step(42,'UP+LEFT');p.step(42,'DOWN+RIGHT');p.step(60);p.finish()
except Exception:
 p.encoder.stdin.close();p.encoder.wait();p.e.close();raise
