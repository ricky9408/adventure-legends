#!/usr/bin/env python3
"""Spoiler-safe continuous endroll; historical authenticated developer save, native audio/pixels."""
from __future__ import annotations
import argparse, ctypes as C, gzip, hashlib, json, math, shutil, subprocess, sys, wave
from array import array
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_campaign import ControllerNative
from player_feedback_native import sha
from mgba_runner import keymask
FPS=Fraction(16777216,280896)
EXPECTED='a94e9dee47f4de0a2f984d6a90b3d80e2c9a6a512157bf10ff2f1e65f088b684'
class Capture:
 def __init__(self,a):
  self.a=a;self.out=a.output.resolve();self.out.mkdir(parents=True,exist_ok=False)
  assert sha(a.rom)==EXPECTED
  for src,name in ((a.rom,'capture.gba'),(a.symbols,'capture.sym'),(a.bridge,'bridge.so'),(Path(__file__),'capture-harness.py')):shutil.copyfile(src,self.out/name)
  self.sym={v[2]:int(v[0],16) for line in a.symbols.read_text().splitlines() if len(v:=line.split())==3}
  self.e=ControllerNative(self.out/'capture.gba',self.out/'bridge.so')
  for name,args,ret in [('eb_audio_start',[C.c_void_p,C.c_char_p],C.c_int),('eb_audio_stop',[C.c_void_p],C.c_uint)]:
   f=getattr(self.e.lib,name);f.argtypes=args;f.restype=ret
  self.rows=[];self.inputs=[];self.shots={};self.rgb=hashlib.sha256();self.encoder=None;self.recording=False
 def g(self,n,w=4):return self.e.read(self.sym[n],w)
 def step(self,n=1,keys=0):
  mask=keymask(keys);self.inputs.append({'emulator_frame':self.e.frame,'video_frame':len(self.rows) if self.recording else None,'frames':n,'keys':mask})
  for _ in range(n):
   before=self.g('frame');page=self.e.read(0x04000000,2)&16;self.e.frames(1,mask)
   assert not self.e.lib.eb_faults(self.e.ptr) and not self.g('save_failed')
   if self.recording:
    im=self.e.screenshot();rgb=im.tobytes();self.rgb.update(rgb)
    row={'offset':len(self.rows),'hardware_frame':self.e.frame,'mode':self.g('game_state'),'room':self.g('room'),'x':self.g('px'),'y':self.g('py'),'delta':(self.g('frame')-before)&0xffffffff,'flip':page!=(self.e.read(0x04000000,2)&16),'cycles':self.g('render_cycles'),'credits_phase':self.g('ending_credits_phase'),'credits_scroll':self.g('ending_credits_scroll'),'rgb_sha256':hashlib.sha256(rgb).hexdigest()}
    self.rows.append(row);self.encoder.stdin.write(rgb)
 def tap(self,key):self.step(2,key);self.step(4)
 def shot(self,name):
  p=self.out/(name+'.png');im=self.e.screenshot(p);im.resize((960,640),0).save(self.out/(name+'-4x.png'));self.shots[name]={'frame':len(self.rows)-1,'seconds':(len(self.rows)-1)/float(FPS),'sha256':sha(p)}
 def begin(self):
  self.fixture=ROOT/'tests/fixtures/v5-revision9/covenants-all128-72-cold.sav'
  provenance=self.fixture.parent/'provenance.json'
  entry=next(f for f in json.loads(provenance.read_text())['fixtures'] if f['path'].endswith(self.fixture.name))
  assert sha(self.fixture)==entry['sha256']
  shutil.copyfile(self.fixture,self.out/'historical-developer-save.sav');shutil.copyfile(provenance,self.out/'fixture-provenance.json')
  self.sources={}
  for relative in ('src/ending_credits.c','src/ending_credits.h','src/ending_credits_text.h','tests/endroll_native.py','tests/player_feedback_native.py','tests/player_feedback_campaign.py','tests/player_feedback_mgba_bridge.c','tools/mgba_bridge.c','tools/mgba_runner.py'):
   target=self.out/'source'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,target);self.sources[relative]=sha(target)
  self.e.load_save(self.out/'historical-developer-save.sav');self.e.reset()
  self.step(160);assert self.g('game_state')==0 and self.g('has_save')
  self.tap('A');self.wait(lambda:self.g('game_state') not in (6,10,12))
  for _ in range(15):
   if self.g('game_state') in (2,14):self.tap('A')
   else:break
  self.wait(lambda:self.g('game_state')==1);self.step(100)
  self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'))
  self.initial_sram_sha=hashlib.sha256(self.e.bytes(0x0e000000,32768)).hexdigest()
  self.tap('START');self.tap('DOWN');self.tap('DOWN');self.tap('RIGHT');self.tap('A');assert self.g('journal_tab')==14
  self.tap('A');assert self.g('journal_tab')==0
  self.tap('A');assert self.g('game_state')==2
  for _ in range(100):
   if self.g('dpage')==self.g('dcount')-1:break
   self.tap('A')
  self.step(70,'A');assert self.g('game_state')==5 and self.g('ending_credits_phase')==0
  self.step(3);self.step(2,'A');assert self.g('ending_credits_phase')==1
  # Let both display buffers publish the credits while held A keeps scroll at zero.
  # Recording starts only after the story card is fully replaced.
  self.step(4,'A');assert self.g('ending_credits_scroll')==0
  self.log=(self.out/'encoder.log').open('w')
  self.encoder=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','240x160','-framerate',str(FPS),'-i','-','-map','0:v','-c:v','ffv1','-level','3',str(self.out/'native-frames.mkv'),'-map','0:v','-vf','scale=960:640:flags=neighbor','-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p',str(self.out/'silent.mp4')],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=self.log)
  self.e.audio_start(self.out/'native-game-audio.wav');self.recording=True
 def wait(self,predicate,limit=1500):
  for _ in range(limit):
   if predicate():return
   self.step()
  raise AssertionError('Controller route timed out')
 def route(self):
  self.step(1);self.shot('01-endroll-begin')
  for scroll,name in ((440,'02-gbj-geebee'),(590,'03-fonts'),(700,'04-tools')):
   self.wait(lambda:self.g('ending_credits_scroll')>=scroll,2800);self.shot(name)
  self.wait(lambda:self.g('ending_credits_phase')==2,1000);self.step(4);self.shot('05-thanks');self.step(176)
  assert hashlib.sha256(self.e.bytes(0x0e000000,32768)).hexdigest()==self.initial_sram_sha
 def finish(self):
  self.recording=False;samples=self.e.audio_stop();self.encoder.stdin.close();assert self.encoder.wait()==0;self.encoder=None;self.log.close()
  subprocess.run(['ffmpeg','-y','-i',str(self.out/'silent.mp4'),'-i',str(self.out/'native-game-audio.wav'),'-c:v','copy','-c:a','aac','-ar','48000','-b:a','160k','-movflags','+faststart',str(self.out/'endroll-native-preview.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  duration=len(self.rows)/float(FPS)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(self.out/'endroll-native-preview.mp4')],text=True));v=next(s for s in probe['streams'] if s['codec_type']=='video');au=next(s for s in probe['streams'] if s['codec_type']=='audio')
  assert int(v['nb_frames'])==int(v['nb_read_frames'])==len(self.rows) and Fraction(v['r_frame_rate'])==FPS
  assert (v['width'],v['height'])==(960,640) and abs(float(au['duration'])-float(v['duration']))<.05
  with wave.open(str(self.out/'native-game-audio.wav'))as w:
   pcm=array('h',w.readframes(w.getnframes()));sound={'samples':w.getnframes(),'rate':w.getframerate(),'channels':w.getnchannels(),'duration':w.getnframes()/w.getframerate(),'peak':max(abs(x)for x in pcm),'rms':math.sqrt(sum(x*x for x in pcm)/len(pcm)),'clipped_samples':sum(abs(x)>=32767 for x in pcm)}
  assert samples==sound['samples'] and sound['peak'] and not sound['clipped_samples'] and abs(sound['duration']-duration)<.05
  decoder=subprocess.Popen(['ffmpeg','-v','error','-i',str(self.out/'native-frames.mkv'),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE);h=hashlib.sha256();count=0
  while chunk:=decoder.stdout.read(1048576):h.update(chunk);count+=len(chunk)
  assert decoder.wait()==0 and count==len(self.rows)*240*160*3 and h.hexdigest()==self.rgb.hexdigest()
  with gzip.open(self.out/'capture-frames.jsonl.gz','wt')as f:
   for row in self.rows:f.write(json.dumps(row,separators=(',',':'))+'\n')
  subprocess.run(['ffmpeg','-y','-i',str(self.out/'native-frames.mkv'),'-i',str(self.out/'native-game-audio.wav'),'-c:v','copy','-c:a','pcm_s16le',str(self.out/'native-av-master.mkv')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  transported=subprocess.check_output(['ffmpeg','-v','error','-i',str(self.out/'native-av-master.mkv'),'-map','0:a','-f','s16le','-'])
  assert transported==pcm.tobytes()
  sound['pcm_sha256']=hashlib.sha256(pcm.tobytes()).hexdigest();sound['lossless_master_audio_transport_exact']=True
  assert all(r['mode']==5 and r['credits_phase'] in (1,2) for r in self.rows)
  assert not any(r['delta']!=1 or not r['flip'] or r['cycles']>=280896 for r in self.rows)
  report={'passed':True,'scope':__doc__,'rom_sha256':EXPECTED,'symbols_sha256':sha(self.a.symbols),'bridge_sha256':sha(self.out/'bridge.so'),'harness_sha256':sha(__file__),'controller_only':True,'game_ram_writes':0,'machine_state_imports':0,'sram_imports':1,'historical_developer_save':True,'fresh_acquisition_claimed':False,'fixture_sha256':sha(self.fixture),'fixture_provenance_sha256':sha(self.out/'fixture-provenance.json'),'source_hashes':self.sources,'story_card_in_recording':False,'initial_sram_sha256':self.initial_sram_sha,'continuous_capture':True,'speed_change':False,'physical_hardware_tested':False,'listening_review_performed':False,'fps':str(FPS),'frames':len(self.rows),'seconds':duration,'native_rgb_sha256':h.hexdigest(),'audio':sound,'max_render_cycles':max(r['cycles']for r in self.rows),'update_delta_anomalies':[r['offset']for r in self.rows if r['delta']!=1],'nonflip_frames':[r['offset']for r in self.rows if not r['flip']],'inputs':self.inputs,'previews':self.shots,'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in self.out.iterdir() if p.suffix in ('.png','.mkv','.mp4','.wav','.gz')}}
  (self.out/'teaser-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'video':str(self.out/'endroll-native-preview.mp4'),'seconds':duration,'sha256':sha(self.out/'endroll-native-preview.mp4')}),flush=True)
 def close(self):
  if self.recording:self.e.audio_stop()
  if self.encoder:self.encoder.stdin.close();self.encoder.wait();self.log.close()
  self.e.close()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','symbols','bridge','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();c=Capture(a)
 try:c.begin();c.route();c.finish()
 finally:c.close()
if __name__=='__main__':main()
