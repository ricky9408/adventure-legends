#!/usr/bin/env python3
"""Exact-ROM Party collection native checks. Controller-earned fresh menu flow;
explicitly logged RAM boundary fixtures for empty/sparse/duplicates/all160.
Ordinary historical SRAM migration is distinct from fresh collection acquisition.
"""
import argparse,ctypes as C,hashlib,json,shutil,subprocess
from pathlib import Path
from fractions import Fraction
from player_feedback_native import Run,ROOT,sha,LIMIT
from test_save5 import Save,Instance,Roster
FPS=Fraction(16777216,280896)
class Browsing(Run):
 def __init__(self,a):
  super().__init__(a);self.record=False;self.video_frames=0;self.rgb=hashlib.sha256()
  shutil.copyfile(__file__,self.out/'test-source/tests/companion_browsing_native.py');self.hashes['companion_browsing_test_sha256']=sha(__file__);self.hashes['test_sources']['tests/companion_browsing_native.py']=sha(__file__)
 def report(self):
  d=super().report();d['suite']='companion-browsing-native';d['scope']=__doc__;d['runtime_changes']='This suite checks retained quick-party inputs and save format on the supplied ROM; consult the current release diff for changes outside companion browsing';(self.out/'report.json').write_text(json.dumps(d,indent=2)+'\n');return d
 def step(self,n=1,keys=0,phase='measured'):
  if not self.record:return super().step(n,keys,phase)
  for _ in range(n):
   super().step(1,keys,phase);raw=self.e.screenshot().tobytes();self.encoder.stdin.write(raw);self.rgb.update(raw);self.video_frames+=1
 def party(self):
  self.tap('START');self.tap('DOWN');self.tap('A');self.check('controller opens Party',self.g('game_state')==3 and self.g('journal_tab')==2)
 def unchanged(self,before,label):
  self.check(label,(bytes(self.save_state().roster),self.e.bytes(0x0e000000,32768),self.g('save_feedback_requests'))==before)
 def snapshot(self):return (bytes(self.save_state().roster),self.e.bytes(0x0e000000,32768),self.g('save_feedback_requests'))
 def fresh(self):
  self.play();before=self.snapshot();self.party();self.shot('native-fresh-party');self.check('starting selected individual',self.g('quickparty_menu_candidate')==0)
  self.step(40,'A');self.check('held A opens detail only',self.g('quickparty_menu_detail')==1);self.unchanged(before,'held first A cannot assign');self.step(3);self.shot('native-fresh-detail');self.tap('B');self.check('B returns from detail to same candidate',not self.g('quickparty_menu_detail') and self.g('quickparty_menu_candidate')==0)
  self.tap('DOWN');self.check('next owned individual',self.g('quickparty_menu_candidate')==1);self.shot('native-second-party');self.tap('DOWN');self.check('Empty follows final owned individual',self.g('quickparty_menu_candidate')==255);self.shot('native-empty-action');self.tap('DOWN');self.check('Empty wraps to first',self.g('quickparty_menu_candidate')==0)
  self.tap('UP');self.check('Up wraps to Empty',self.g('quickparty_menu_candidate')==255);self.tap('UP');self.check('Up skips Empty to last',self.g('quickparty_menu_candidate')==1)
  for keys in ('SELECT','SELECT+A','L','R','LEFT+RIGHT','UP+DOWN'):
   candidate=self.g('quickparty_menu_candidate');self.tap(keys);self.check(keys+' has no collection action',self.g('quickparty_menu_candidate')==candidate and not self.g('quickparty_menu_detail'))
  self.tap('A');self.tap('B');self.tap('B');self.check('second B returns hub',self.g('journal_tab')==13);self.tap('B');self.check('third B resumes field',self.g('game_state')==1);self.unchanged(before,'all browsing/back paths preserve roster, SRAM and save requests')
  self.party();self.tap('DOWN');self.tap('A');self.tap('START');self.check('Start exits detail to field',self.g('game_state')==1);self.unchanged(before,'Start cancels detail without save')
 def prepared(self,indices,forms=False,valid=False):
  self.play();s=self.save_state();base=bytes(s.roster.instances[0]);story=[bytes(s.roster.instances[i]) for i in (0,1)];r=s.roster
  for i in range(160):r.instances[i]=Instance()
  for i in indices:
   r.instances[i]=Instance.from_buffer_copy(base);c=r.instances[i];c.instance_id=1001+i;c.flags=1|(4 if i%2 else 0)
   if i%2:c.level=50;c.xp=470596
   if forms and i==159:c.form_id=2
  if valid:
   for i in (0,1):r.instances[i]=Instance.from_buffer_copy(story[i])
  for i in range(4):r.party[i]=255
  if indices:r.party[0]=indices[0]
  if len(indices)>1:r.party[3]=indices[-1]
  r.selected_party=0;r.next_instance_id=1200
  raw=bytes(r)
  for off in range(0,len(raw),4):
   data=raw[off:off+4]
   for j,b in enumerate(data):
    self.put('adventure_save',b,1,Save.roster.offset+off+j,reason='synthetic boundary roster; no acquisition claimed')
  self.party();return self.snapshot()
 def boundaries(self):
  for label,indices in [('zero',[]),('one',[0]),('sparse',[0,79,159]),('maximum',list(range(160)))]:
   before=self.prepared(indices,forms=label=='sparse');self.shot('native-'+label+'-collection');candidate=indices[0] if indices else 255
   self.check(label+' starts expected candidate',self.g('quickparty_menu_candidate')==candidate)
   expected=indices+[255] if indices else [255]
   # Full forward/backward traversal includes every stored instance exactly once.
   for direction,step in [('DOWN',1),('UP',-1)]:
    for _ in expected:
     at=expected.index(candidate);candidate=expected[(at+step)%len(expected)];self.tap(direction)
     self.check(label+' '+direction+' candidate '+str(candidate),self.g('quickparty_menu_candidate')==candidate)
   self.unchanged(before,label+' complete round trips preserve all save/roster bytes')
   if indices:
    self.tap('UP');self.tap('UP');self.check(label+' end candidate selected',self.g('quickparty_menu_candidate')==indices[-1]);self.shot('native-'+label+'-last');self.tap('A');self.shot('native-'+label+'-last-detail');self.tap('B');self.unchanged(before,label+' detail cancel retains identity/favorites')
   if label=='maximum':
    self.tap('DOWN');self.tap('DOWN');self.check('max returns first before hold',self.g('quickparty_menu_candidate')==0)
    start=len(self.frames);self.step(1,'DOWN');self.check('hold starts one step',self.g('quickparty_menu_candidate')==1)
    self.step(17,'DOWN');self.check('hold delay remains 18 updates',self.g('quickparty_menu_candidate')==1)
    self.step(1,'DOWN');self.check('18th hold repeats',self.g('quickparty_menu_candidate')==2)
    self.step(5,'DOWN');self.check('repeat interval remains six',self.g('quickparty_menu_candidate')==2)
    self.step(1,'DOWN');self.check('sixth update repeats',self.g('quickparty_menu_candidate')==3)
    self.step(6*156,'DOWN');self.check('held Down reaches final individual without omissions',self.g('quickparty_menu_candidate')==159)
    frames=len(self.frames)-start;self.cases.append({'case':'all160-hold-traversal','updates_from_first_to_last':frames,'seconds_at_gba_rate':float(frames/FPS),'prior_repeat_timing_unchanged':True,'controller_earned_collection':False});self.step(3);self.shot('native-maximum-held-last');self.unchanged(before,'max held browse is save-free')
   self.tap('START')
 def assignment(self):
  before=self.prepared([0,1,79,159],valid=True);self.tap('DOWN');self.tap('DOWN');self.check('duplicate No080 selected',self.g('quickparty_menu_candidate')==79);self.shot('native-duplicate-preview');self.step(45,'A');self.check('held duplicate confirmation stays inspection',self.g('quickparty_menu_detail')==1);self.unchanged(before,'duplicate preview changes nothing');self.step(3);self.shot('native-duplicate-confirm');self.tap('A');self.check('fresh second A assigns exact duplicate instance',self.save_state().roster.party[0]==79)
  locked=bytes(self.save_state().roster);requests=self.g('save_feedback_requests');self.check('confirmed assignment enters busy save',self.g('game_state')==6);self.step(2,'B+START+DOWN');self.check('cancel/navigation chord cannot mutate committed busy assignment',self.g('game_state')==6 and bytes(self.save_state().roster)==locked and self.g('save_feedback_requests')==requests);self.step(3)
  self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested') and self.g('game_state')==3,1500);self.check('assignment save succeeds',not self.g('save_failed'));after=self.save_state();self.check('duplicate/favorite/instance values retained',after.roster.instances[79].instance_id==1080 and after.roster.instances[79].flags==5 and after.roster.instances[0].instance_id==1)
  path=self.out/'prepared-duplicate-assignment.sav';self.e.save(path);self.play(path);self.check('cold ordinary SRAM retains exact duplicate assignment',self.save_state().roster.party[0]==79 and self.save_state().roster.instances[79].instance_id==1080)
 def migration(self):
  self.play(True);before=self.snapshot();self.check('authentic old-save72 count retained',sum(bool(c.flags&1) for c in self.save_state().roster.instances)==72);self.party();self.shot('developer-legacy72-party');self.step(120,'DOWN');self.step(3);self.tap('A');self.tap('B');self.tap('START');self.unchanged(before,'legacy collection browsing preserves migrated roster and SRAM')
 def busy(self):
  self.play();self.step(55,'UP');self.wait(lambda:self.g('room')==1,180,'UP');self.check('controller travel starts ordinary save',self.g('save_feedback_background') or self.g('save_requested'));self.wait(lambda:not self.g('scene_present_phase'),30);self.step(3);self.check('travel writer still active after scene handoff',self.g('save_feedback_background') or self.g('save_requested'));self.party();self.step(30,'DOWN');self.tap('A');self.tap('B');self.tap('START');self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),1500);self.check('opening/canceling menu during travel save completes safely',self.g('game_state')==1 and not self.g('save_failed'))
 def video(self):
  self.play();self.case='spoiler-safe-controller-video';log=open(self.out/'video-encode.log','wb')
  self.encoder=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','240x160','-r',str(FPS),'-i','-','-c:v','ffv1',str(self.out/'native-frames.mkv')],stdin=subprocess.PIPE,stderr=log,stdout=subprocess.DEVNULL)
  self.e.lib.eb_audio_start.argtypes=[C.c_void_p,C.c_char_p];self.e.lib.eb_audio_start.restype=C.c_int;self.e.lib.eb_audio_stop.argtypes=[C.c_void_p];self.e.lib.eb_audio_stop.restype=C.c_uint
  assert self.e.lib.eb_audio_start(self.e.ptr,str(self.out/'native-game-audio.wav').encode())==1
  self.record=True;self.step(60);self.party();self.step(130);self.tap('DOWN');self.step(130);self.tap('A');self.step(160);self.tap('B');self.tap('DOWN');self.step(100);self.tap('UP');self.step(80);self.tap('B');self.tap('B');self.step(40);self.step(40,'L+RIGHT');self.step(80);self.record=False
  samples=self.e.lib.eb_audio_stop(self.e.ptr);self.encoder.stdin.close();assert self.encoder.wait()==0;log.close()
  subprocess.run(['ffmpeg','-y','-i',str(self.out/'native-frames.mkv'),'-i',str(self.out/'native-game-audio.wav'),'-vf','scale=960:640:flags=neighbor','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',str(self.out/'companion-browsing-preview.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(self.out/'companion-browsing-preview.mp4')],text=True));v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio');assert int(v['nb_read_frames'])==self.video_frames and abs(float(v['duration'])-float(a['duration']))<.05
  decoded=subprocess.check_output(['ffmpeg','-v','error','-i',str(self.out/'native-frames.mkv'),'-f','rawvideo','-pix_fmt','rgb24','-']);assert hashlib.sha256(decoded).hexdigest()==self.rgb.hexdigest()
  (self.out/'video-report.json').write_text(json.dumps({'rom_sha256':self.hashes['rom_sha256'],'frames':self.video_frames,'fps':str(FPS),'seconds':float(self.video_frames/FPS),'samples':samples,'native_rgb_sha256':self.rgb.hexdigest(),'controller_only':True,'fresh_game':True,'game_ram_writes_in_video':0,'spoiler_safe':'Only starting village/two starting companions; no ending or later forms','continuous_realtime_capture':True,'audio':'Native unchanged game music','video_sha256':sha(self.out/'companion-browsing-preview.mp4'),'streams':probe['streams']},indent=2)+'\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,default=ROOT/'build/emberbond.gba');p.add_argument('--symbols',type=Path,default=ROOT/'build/emberbond.sym');p.add_argument('--output',type=Path,required=True);p.add_argument('--cases',default='fresh,boundaries,assignment,migration,busy,menus,video');a=p.parse_args();r=Browsing(a)
 for name in a.cases.split(','):r.section(name,getattr(r,name))
 d=r.finish();return int(bool(d['failures']) or not d['performance']['strict_measured_pacing_pass'])
if __name__=='__main__':raise SystemExit(main())
