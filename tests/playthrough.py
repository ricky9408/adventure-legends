#!/usr/bin/env python3
"""Controller-only first-chapter regression of the real campaign GBA ROM.
The complete three-lantern route lives in campaign_tests.py.
"""
from pathlib import Path
import sys, subprocess, json, os, hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
ROM=Path(os.environ.get('EMBERBOND_TEST_ROM',ROOT/'build/emberbond.gba')).resolve()
SYMBOLS=Path(os.environ.get('EMBERBOND_TEST_SYMBOLS',ROOT/'build/emberbond.sym')).resolve()
sym={w[2]:int(w[0],16) for ln in SYMBOLS.read_text().splitlines() if len(w:=ln.split())==3}
OUT=Path(os.environ.get('EMBERBOND_TEST_OUTPUT',ROOT/'build/qa')).resolve();OUT.mkdir(parents=True,exist_ok=True)
class Play:
 def __init__(self,video=False):
  self.e=Emulator(ROM);self.video=video;self.logs=[];self.frames=[]
  if video:self.e.audio_start(OUT/'playthrough.wav')
 def get(self,n):return self.e.read(sym[n])
 def step(self,n,key=0):
  if self.video:
   for _ in range(n):
    self.e.frames(1,key)
    self.frames.append(self.e.screenshot())
  else:self.e.frames(n,key)
  for _ in range(180):
   if self.get('game_state')!=6:break
   self.e.frames(1,0)
   if self.video:self.frames.append(self.e.screenshot())
  else:raise AssertionError('Transactional save did not finish')
 def tap(self,key,hold=10,release=10):self.step(hold,key);self.step(release)
 def check(self,b,label):
  assert b,label+' '+str(self.status());self.logs.append(label);print('PASS',label,flush=True)
 def status(self):return {n:self.get(n) for n in ['game_state','room','px','py','hp','spirit','summoned','bridge_open','torches','boss_hp','boss_armor','ability_cd','chapter_flags','room_flags','story_seen','save_failed','frame']}
 def shot(self,name):self.e.screenshot(OUT/(name+'.png'))
 def dialogs(self):
  for _ in range(8):
   if self.get('game_state')!=2:return
   self.tap('A')
  raise AssertionError('dialogue did not terminate')
 def goto(self,x=None,y=None):
  for n,t,klo,khi in [('px',x,'LEFT','RIGHT'),('py',y,'UP','DOWN')]:
   if t is None:continue
   for _ in range(350):
    v=self.get(n)
    if abs(v-t)<=1:break
    self.step(2,klo if v>t else khi)
   else:raise AssertionError('movement blocked '+n+' target '+str(t)+' '+str(self.status()))
  self.step(4)
 def defend(self,n):
  for _ in range((n+23)//24):
   living=[]
   for i in range(6):
    a=sym['enemies']+i*20;x=self.e.read(a);y=self.e.read(a+4);h=self.e.read(a+8)
    if h:living.append((abs(x-self.get('px'))+abs(y-self.get('py')),x,y))
   if living:
    _,x,y=min(living);dx=x-self.get('px');dy=y-self.get('py')
    key=('LEFT' if dx<0 else 'RIGHT') if abs(dx)>abs(dy) else ('UP' if dy<0 else 'DOWN')
    self.step(2,key);self.tap('A');self.step(2)
   else:self.step(24)
 def nextroom(self,target):
  if self.get('room')==1 and target==2:
   self.goto(x=240);self.goto(y=92);self.goto(x=368)
  for _ in range(400):
   if self.get('room')==target:break
   self.step(2,'UP')
  self.check(self.get('room')==target,'entered room '+str(target));self.step(8)
 def play(self):
  self.step(90);self.check(self.get('game_state')==0,'booted title');self.shot('01-title');self.tap('START');self.check(self.get('game_state')==2,'Japanese introduction');self.shot('02-story');self.dialogs();self.check(self.get('game_state')==1,'dialogue returns to play');self.shot('03-village')
  self.tap('START');self.check(self.get('game_state')==3,'pause opened');old=self.get('px');self.step(24,'LEFT');self.check(self.get('px')==old,'pause blocks movement');self.shot('04-controls');self.tap('B');self.check(self.get('game_state')==1,'B closes pause')
  self.nextroom(1);self.goto(y=180);self.tap('R');self.check(self.get('bridge_open')==0,'unsummoned ability cannot solve puzzle');self.step(35,'UP');self.check(176<=self.get('py')<=180,'river blocks passage before puzzle');self.tap('B');self.check(self.get('summoned')==1,'summoned fire companion');self.tap('L');self.check(self.get('spirit')==1,'switched to nature companion');self.tap('R');self.check(self.get('bridge_open')==1,'nature power grows bridge');self.dialogs();self.shot('05-grown-bridge');self.nextroom(2);self.dialogs();self.check(self.get('torches')==0,'temple begins sealed');self.shot('06-temple')
  self.tap('L');self.goto(y=94);self.goto(x=64);self.goto(y=84)
  self.defend(160);self.goto(x=64,y=84);self.tap('R');self.check(self.get('torches')==1,'first brazier lights');self.goto(y=94);self.goto(x=176);self.goto(y=84);self.defend(160);self.goto(x=176,y=84);self.tap('R');self.check(self.get('torches')==3,'second brazier opens gate');self.dialogs();self.shot('07-open-gate');self.goto(y=94);self.goto(x=120);self.nextroom(3);self.dialogs();self.shot('08-guardian')
  self.goto(y=100);self.step(self.get('ability_cd')+2);self.tap('R',2,2);self.check(self.get('boss_armor')>0,'fire breaks guardian armor');self.goto(y=92)
  for i in range(30):
   if self.get('game_state')==2:break
   if self.get('boss_armor')==0 and self.get('ability_cd')==0:self.tap('R',2,2)
   # Face up, stay outside contact range, swing each cooldown.
   self.goto(x=self.get('boss_x'),y=self.get('boss_y')+30);self.step(1,'UP');self.tap('A',2,2);self.step(18)
   if i==2:self.shot('09-sword-boss')
   print('BOSS',i,self.status(),flush=True)
  self.check(self.get('boss_hp')==0,'guardian defeated with sword');self.check(self.get('chapter_flags')==1,'first lantern reward committed before dialogue');self.dialogs();self.check(self.get('game_state')==1 and self.get('room')==0,'first chapter continues safely in village');self.check(self.get('completed')==0,'first guardian is not the campaign ending');self.tap('L');self.tap('L');self.check(self.get('spirit')==2,'earned Fuuri is selectable');self.check(self.get('save_failed')==0,'first chapter save transaction succeeded');self.shot('10-wind-joins-village');self.step(90)
  (OUT/'playthrough.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(ROM.read_bytes()).hexdigest(),'symbols_sha256':hashlib.sha256(SYMBOLS.read_bytes()).hexdigest(),'passes':self.logs,'final':self.status(),'emulator_frames':self.e.frame,'controller_only':True},indent=2)+'\n')
  # Persist real SRAM for an independent new emulator instance.
  (OUT/'checkpoint.sav').write_bytes(self.e.bytes(0x0E000000,32768))
  if self.video:
   self.e.audio_stop()
   proc=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','240x160','-r','59.7275','-i','-','-i',str(OUT/'playthrough.wav'),'-shortest','-vf','scale=960:640:flags=neighbor','-c:v','libx264','-c:a','aac','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'playthrough.mp4')],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
   for im in self.frames:proc.stdin.write(im.tobytes())
   proc.stdin.close();assert proc.wait()==0
  self.e.close()
if __name__=='__main__':Play('--video' in sys.argv).play()
