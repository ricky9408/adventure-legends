#!/usr/bin/env python3
"""Spoiler-free, continuous native menu/shop/entrance demonstration.

Starts from authenticated controller-earned SRAM from this exact candidate.
Only buttons change gameplay. Captures actual RGB and mGBA audio; production
cadence is checked for every recorded frame. This is not a listening review.
"""
from __future__ import annotations
import argparse, ctypes as C, gzip, hashlib, json, math, shutil, subprocess, wave
from array import array
from fractions import Fraction
from pathlib import Path
from player_feedback_campaign import ControllerNative
from player_feedback_native import sha
from mgba_runner import keymask
from test_save5 import Save

FPS=Fraction(16777216,280896)
LIMIT=280896

class Capture:
 allowed_capture_states=(1,3,6,11,12)
 def __init__(self,a):
  self.a=a;self.out=a.output.resolve();self.out.mkdir(parents=True,exist_ok=False)
  p=json.loads(a.producer.read_text());assert sha(a.producer)==a.producer_sha
  assert p['controller_only'] and p['game_ram_writes']==p['machine_state_imports']==0
  assert p['route_complete'] and p['native_cadence_passed'] and not p['failures']
  assert sha(a.rom)==p['candidate']['rom_sha256'] and sha(a.symbols)==p['candidate']['symbols_sha256']
  bridge=a.producer.parent/'bridge.so';assert sha(bridge)==p['candidate']['bridge_sha256']
  record=p['checkpoints']['grove-complete'];source=a.producer.parent/Path(record['sram_path']).name
  assert sha(source)==record['sram_sha256'] and record['status']['room']==0
  for src,dst in ((a.producer,'producer.json'),(source,'source-earned.sav'),(bridge,'bridge.so')):shutil.copyfile(src,self.out/dst)
  self.producer=p;self.sym={v[2]:int(v[0],16) for line in a.symbols.read_text().splitlines() if len(v:=line.split())==3}
  self.e=ControllerNative(a.rom,self.out/'bridge.so');self.e.load_save(self.out/'source-earned.sav');self.e.reset()
  self.e.lib.eb_audio_start.argtypes=[C.c_void_p,C.c_char_p];self.e.lib.eb_audio_start.restype=C.c_int
  self.e.lib.eb_audio_stop.argtypes=[C.c_void_p];self.e.lib.eb_audio_stop.restype=C.c_uint
  self.recording=False;self.encoder=None;self.rows=[];self.inputs=[];self.shots={};self.rgb_hash=hashlib.sha256()
 def g(self,name):return self.e.read(self.sym[name])
 def state(self):return Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)))
 def roster_progress(self):
  r=self.state().roster
  return (bytes(r.instances),bytes(r.party),r.selected_party,r.next_instance_id,bytes(r.seen),bytes(r.obtained),bytes(r.rewards),bytes(r.lifetime_field_aid))
 def step(self,count=1,keys=0):
  mask=keymask(keys);self.inputs.append({'frame':self.e.frame,'recording':self.recording,'frames':count,'keys':mask})
  for _ in range(count):
   before=self.g('frame');page=self.e.read(0x04000000,2)&16;self.e.frames(1,mask)
   assert not self.e.lib.eb_faults(self.e.ptr) and not self.g('save_failed')
   if self.recording:
    row={'frame':self.e.frame,'offset':len(self.rows),'mode':self.g('game_state'),'room':self.g('room'),'x':self.g('px'),'y':self.g('py'),'delta':(self.g('frame')-before)&0xffffffff,'flip':page!=(self.e.read(0x04000000,2)&16),'cycles':self.g('render_cycles'),'music_faults':self.g('music_faults'),'music_recoveries':self.g('music_recoveries'),'music_stopped':self.g('music_stopped'),'quickparty_open':self.g('quickparty_open')}
    assert row['delta']==1 and row['flip'] and row['cycles']<LIMIT,('native cadence',row)
    assert row['room'] in (0,1) and row['mode'] in self.allowed_capture_states,('public route left safe scope',row)
    assert not any(row[k] for k in ('music_faults','music_recoveries','music_stopped'))
    rgb=self.e.screenshot().tobytes();row['rgb_sha256']=hashlib.sha256(rgb).hexdigest();self.rgb_hash.update(rgb);self.rows.append(row);self.encoder.stdin.write(rgb)
 def tap(self,k):self.step(2,k);self.step(4)
 def settle(self):
  for _ in range(1500):
   if self.g('game_state') not in (6,10,12) and not self.g('save_feedback_background') and not self.g('save_requested'):return
   self.step()
  raise AssertionError('transaction did not settle')
 def goto(self,x=None,y=None):
  for name,target,lo,hi in (('px',x,'LEFT','RIGHT'),('py',y,'UP','DOWN')):
   if target is None:continue
   for _ in range(500):
    old=self.g(name)
    if abs(old-target)<=2:break
    assert self.g('game_state')==1
    self.step(1,lo if old>target else hi)
   else:raise AssertionError(('blocked path',name,target,self.g(name)))
  self.step(3)
 def shot(self,name):
  self.step(3);p=self.out/(name+'.png');im=self.e.screenshot(p);im.resize((960,640),0).save(self.out/(name+'-4x.png'));self.shots[p.name]={'offset':len(self.rows)-1,'sha256':sha(p),'native_rgb_sha256':hashlib.sha256(im.tobytes()).hexdigest()}
 def prepare(self):
  self.step(160);assert self.g('game_state')==0;self.tap('A')
  for _ in range(1600):
   if self.g('game_state')==1 and self.g('frame'):break
   self.step()
  self.settle();self.step(160)
  assert self.g('room')==0 and self.g('game_state')==1
  self.goto(x=120,y=126)
  # The same earned save has three familiar base companions. Show Midori.
  self.step(14,'L');self.step(6,'L+RIGHT');self.step(6)
  if not self.g('summoned'):self.tap('B')
  assert self.g('spirit')==1
  self.before=self.roster_progress();self.before_flags=(self.g('chapter_flags'),self.g('room_flags'))
  self.e.save(self.out/'capture-start.sav')
 def begin(self):
  self.log=(self.out/'encoder.log').open('w')
  self.encoder=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','240x160','-framerate',str(FPS),'-i','-','-map','0:v','-c:v','ffv1','-level','3',str(self.out/'native-frames.mkv'),'-map','0:v','-vf','scale=960:640:flags=neighbor','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',str(self.out/'silent.mp4')],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=self.log)
  self.e.audio_start(self.out/'native-game-audio.wav');self.recording=True
 def route(self):
  self.step(48);self.shot('native-village')
  self.goto(y=101);self.goto(x=58);self.step(18);self.tap('A');assert self.g('game_state')==11;self.step(95);self.shot('native-shop')
  gold=self.state().economy.gold;tonics=self.state().economy.supplies[0]
  self.tap('A');self.step(40);self.tap('A');self.settle();self.step(80)
  assert self.state().economy.gold==gold-18 and self.state().economy.supplies[0]==tonics+1
  self.tap('B');assert self.g('game_state')==1;self.goto(x=120);self.goto(y=126)
  self.shot('native-village-clean');self.tap('START');self.step(70);self.shot('native-menu-hub');self.tap('RIGHT');self.tap('A');assert self.g('journal_tab')==4;self.step(65)
  self.tap('RIGHT');self.step(45);self.tap('RIGHT');self.step(65);self.shot('native-equipment-parts');self.tap('B');assert self.g('journal_tab')==13;self.step(20);self.tap('START')
  self.step(18,'L');self.step(18,'L+UP');self.step(24);self.step(18,'L');self.step(18,'L+RIGHT');self.step(36)
  # The familiar open village arch leads directly into the field by walking.
  self.goto(x=120)
  for _ in range(160):
   if self.g('room')==1:break
   self.step(1,'UP')
  assert self.g('room')==1;self.step(24);self.shot('native-walk-through-entrance');self.step(24)
  # Ordinary expedition counters reset on departure; owned individuals, XP,
  # history, selected commands and party must remain unchanged.
  assert self.roster_progress()==self.before and self.g('chapter_flags')==self.before_flags[0]
 def finish(self):
  self.recording=False;samples=self.e.audio_stop();self.encoder.stdin.close();assert self.encoder.wait()==0;self.encoder=None;self.log.close()
  duration=len(self.rows)/float(FPS)
  subprocess.run(['ffmpeg','-y','-i',str(self.out/'silent.mp4'),'-i',str(self.out/'native-game-audio.wav'),'-c:v','copy','-c:a','aac','-ar','48000','-b:a','160k','-movflags','+faststart',str(self.out/'player-feedback-native-teaser.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(self.out/'player-feedback-native-teaser.mp4')],text=True));v=next(s for s in probe['streams'] if s['codec_type']=='video');au=next(s for s in probe['streams'] if s['codec_type']=='audio')
  assert int(v['nb_frames'])==int(v['nb_read_frames'])==len(self.rows) and Fraction(v['r_frame_rate'])==FPS
  assert (v['width'],v['height'])==(960,640) and abs(float(au['duration'])-float(v['duration']))<.05
  with wave.open(str(self.out/'native-game-audio.wav'))as w:
   pcm=array('h',w.readframes(w.getnframes()));sound={'samples':w.getnframes(),'rate':w.getframerate(),'channels':w.getnchannels(),'duration':w.getnframes()/w.getframerate(),'peak':max(abs(x)for x in pcm),'rms':math.sqrt(sum(x*x for x in pcm)/len(pcm)),'clipped_samples':sum(abs(x)>=32767 for x in pcm)}
  assert samples==sound['samples'] and sound['peak'] and not sound['clipped_samples'] and abs(sound['duration']-duration)<.05
  decoder=subprocess.Popen(['ffmpeg','-v','error','-i',str(self.out/'native-frames.mkv'),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE);h=hashlib.sha256();count=0
  while chunk:=decoder.stdout.read(1048576):h.update(chunk);count+=len(chunk)
  assert decoder.wait()==0 and count==len(self.rows)*240*160*3 and h.hexdigest()==self.rgb_hash.hexdigest()
  self.e.save(self.out/'capture-end.sav')
  with gzip.open(self.out/'capture-frames.jsonl.gz','wt')as f:
   for row in self.rows:f.write(json.dumps(row,separators=(',',':'))+'\n')
  report={'scope':__doc__,'passed':True,'controller_only':True,'game_ram_writes':0,'machine_state_imports':0,'physical_hardware_tested':False,'listening_review_performed':False,'producer_sha256':self.a.producer_sha,'candidate':self.producer['candidate'],'helper_sha256':sha(__file__),'source_sram_sha256':sha(self.out/'source-earned.sav'),'hardware_frames':len(self.rows),'seconds':duration,'fps':str(FPS),'max_cycles':max(r['cycles']for r in self.rows),'native_rgb_sha256':h.hexdigest(),'audio':sound,'inputs':self.inputs,'previews':self.shots,'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in self.out.iterdir()if p.suffix in ('.png','.mp4','.wav','.sav','.gz')}}
  (self.out/'teaser-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'video':str(self.out/'player-feedback-native-teaser.mp4'),'frames':len(self.rows),'seconds':duration,'max_cycles':report['max_cycles']}))
 def close(self):
  if self.recording:self.e.audio_stop();self.recording=False
  if self.encoder:self.encoder.stdin.close();self.encoder.wait();self.log.close()
  self.e.close()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('rom','symbols','producer','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--producer-sha',required=True);a=p.parse_args();r=Capture(a)
 try:r.prepare();r.begin();r.route();r.finish()
 finally:r.close()
if __name__=='__main__':main()
