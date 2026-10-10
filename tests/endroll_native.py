#!/usr/bin/env python3
"""Native endroll acceptance. Primary path uses only real controller input.
Historical SRAM is hash-pinned by repository provenance, not fresh acquisition.
Every hardware frame is measured; any optional RAM diagnostic is separately logged.
"""
import argparse,ctypes as C,json,sys,wave,shutil
from pathlib import Path
from player_feedback_native import Run,ROOT,sha,LIMIT
from test_save5 import Save
class Endroll(Run):
 def __init__(self,a):
  super().__init__(a);shutil.copyfile(__file__,self.out/"test-source/tests/endroll_native.py")
 def state(self):
  return {**super().state(),**{n:self.g(n) for n in ('ending_credits_phase','ending_credits_scroll','ending_credits_armed','ending_credits_revision','dpage','dcount','chapter_flags','save_feedback_started','save_feedback_requests')}}
 def ending_dialogue(self):
  self.tap('START');self.tap('DOWN');self.tap('DOWN');self.tap('RIGHT');self.tap('A');self.check('controller Quests list',self.g('journal_tab')==14);self.tap('A');self.check('controller opens current goal',self.g('journal_tab')==0);self.tap('A');self.check('goal A opens ending dialogue',self.g('game_state')==2)
  while self.g('game_state')==2 and self.g('dpage')<self.g('dcount')-1:self.tap('A')
 def final_hold(self,key):
  self.step(70,key);self.check('held final '+key+' stays on card unarmed',self.g('game_state')==5 and self.g('ending_credits_phase')==0 and self.g('ending_credits_armed')==0);self.step(3);self.check('release arms card',self.g('ending_credits_armed')==1)
 def snapshot(self):return {'save':self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)),'sram':self.e.bytes(0x0e000000,32768),'started':self.g('save_feedback_started'),'requests':self.g('save_feedback_requests'),'chapter':self.g('chapter_flags'),'completed':self.g('completed')}
 def unchanged(self,before,label):
  after=self.snapshot();self.check(label,after==before,{'different':[k for k in before if before[k]!=after[k]]})
 def replay(self):
  self.play(True);before=self.snapshot();self.ending_dialogue();self.final_hold('A');self.shot('native-ending-card');self.unchanged(before,'replay dialogue and card preserve all SRAM, progress, rewards and save counts')
  self.step(2,'A');self.check('fresh card A starts early roll',self.g('ending_credits_phase')==1 and not self.g('ending_credits_armed'));self.step(60,'A');self.check('held card A does not fast-forward roll',self.g('ending_credits_scroll')==0);self.step(3);self.shot('native-roll-start')
  self.e.lib.eb_audio_start.argtypes=[C.c_void_p,C.c_char_p];self.e.lib.eb_audio_start.restype=C.c_int;self.e.lib.eb_audio_stop.argtypes=[C.c_void_p];self.e.lib.eb_audio_stop.restype=C.c_uint
  self.check('native audio capture starts',self.e.lib.eb_audio_start(self.e.ptr,str(self.out/'endroll.wav').encode())==1)
  targets={340:'native-roll-music',440:'native-roll-gbj-credit',590:'native-roll-fonts',700:'native-roll-tools'}
  for target,name in targets.items():self.check('scroll reaches '+str(target),self.wait(lambda:self.g('ending_credits_scroll')>=target,2600));self.shot(name)
  self.check('whole roll reaches done',self.wait(lambda:self.g('ending_credits_phase')==2,1200));self.step(3);self.shot('native-roll-done');at=self.g('ending_credits_scroll');self.step(180);self.check('done remains idle',self.g('game_state')==5 and self.g('ending_credits_phase')==2 and self.g('ending_credits_scroll')==at)
  samples=self.e.lib.eb_audio_stop(self.e.ptr)
  with wave.open(str(self.out/'endroll.wav')) as wav:pcm=wav.readframes(wav.getnframes());audio={'samples':samples,'sample_rate':wav.getframerate(),'channels':wav.getnchannels(),'nonzero_bytes':sum(x!=0 for x in pcm)}
  self.check('endroll audio remains nonempty',samples>0 and audio['nonzero_bytes']>0,audio)
  self.unchanged(before,'entire automatic roll and done preserve all SRAM, progress, rewards and save counts')
  self.tap('A');self.check('done A replays roll',self.g('ending_credits_phase')==1 and self.g('ending_credits_scroll')<3);self.shot('native-roll-replay');self.step(150);self.step(30,'B');self.check('roll B exits and held B stays in field without summon',self.g('game_state')==1 and not self.g('summoned'));self.step(3)
  self.check('replay never starts save writer before exit',all(not f['bg'] and f['mode']!=6 for f in self.frames if f['case']==self.case and f['mode']==5))
 def boundaries(self):
  for key in ('A+B','A+START'):
   self.play(True);before=self.snapshot();self.ending_dialogue();self.final_hold(key);self.unchanged(before,'held '+key+' replay remains save-free');self.tap('A');self.step(10);self.step(30,'START');self.check('Start exits and held Start does not reopen journal',self.g('game_state')==1);self.step(3)
  self.play(True);self.ending_dialogue();self.final_hold('A');self.check('card automatically starts roll',self.wait(lambda:self.g('ending_credits_phase')==1,190));self.step(3)
  # Holding all ending keys during the final roll frames must not leak into done.
  self.step(1,'A');self.step(3)
  self.check('roll advances toward end',self.wait(lambda:self.g('ending_credits_scroll')>=849,3000))
  self.step(180,'A');self.check('held A at done cannot replay',self.g('ending_credits_phase')==2 and not self.g('ending_credits_armed'));self.step(3);self.tap('A');self.check('fresh A after release replays',self.g('ending_credits_phase')==1);self.step(3);self.tap('B')
  for key in ('B','START'):
   self.play(True);self.ending_dialogue();self.final_hold('A');self.step(40,key);self.check('card '+key+' exits safely',self.g('game_state')==1);self.step(3)
 def first_ending(self):
  fixture=ROOT/'tests/fixtures/v4/core-complete-ending-pending.sav';manifest=json.loads((fixture.parent/'manifest.json').read_text());entry=next(f for f in manifest['fixtures'] if f['file']==fixture.name);assert sha(fixture)==entry['sha256'];self.play(fixture)
  self.check('authentic pending fixture has no ending flag',not self.g('chapter_flags')&8);self.cases.append({'case':'first-ending-fixture','sha256':sha(fixture),'state':self.state(),'historical_controller_fixture':True})
  if self.g('room')!=0:
   self.location(0,120,120);self.step(4,phase='prepared');self.cases.append({'case':'first-ending-scope','scope':'RAM-prepared village placement from genuine pending fixture. Ending interaction is real input; no fresh acquisition claimed.'})
  self.check('walk to elder',self.navigate(120,110));self.tap('A');self.wait(lambda:self.g('game_state')==2,700)
  self.check('elder starts real ending dialogue',self.g('game_state')==2)
  while self.g('game_state')==2 and self.g('dpage')<self.g('dcount')-1:self.tap('A')
  self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),700)
  before=self.g('save_feedback_started');self.step(2,'A');self.step(600,'A');self.check('first ending flag set and completed',bool(self.g('chapter_flags')&8) and self.g('completed')==1);self.check('first ending commits exactly one writer after final dialogue',self.g('save_feedback_started')==before+1,{'before':before,'after':self.g('save_feedback_started')});self.check('first ending saved successfully and held A does not skip',not self.g('save_failed') and self.g('game_state')==5 and self.g('ending_credits_phase')==0);self.step(3);self.shot('native-first-ending-card');self.e.save(self.out/'first-ending.sav');self.play(self.out/'first-ending.sav');self.check('cold reload retains first ending completion',bool(self.g('chapter_flags')&8) and self.g('completed')==1)
 def save_failure_diagnostic(self):
  self.play(ROOT/'tests/fixtures/v4/core-complete-ending-pending.sav');self.navigate(120,110);self.tap('A');self.wait(lambda:self.g('game_state')==2,700)
  while self.g('game_state')==2 and self.g('dpage')<self.g('dcount')-1:self.tap('A')
  self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),700);self.step(1,'A')
  reached=self.wait(lambda:self.g('writer_phase')==13 and self.g('game_state')==6,700,'A')
  self.check('first ending enters real pending writer',reached)
  if not reached:return
  before=(self.g('ending_credits_phase'),self.g('ending_credits_scroll'),self.g('ending_credits_armed'));self.step(1,'A');self.check('ending presentation pauses while save pending',before==(self.g('ending_credits_phase'),self.g('ending_credits_scroll'),self.g('ending_credits_armed')))
  address=0x0e000000+self.g('writer_destination')+min(self.g('writer_position')+600,6000);value=self.e.read(address,1)^1
  self.writes.append({'case':self.case,'frame':self.e.frame,'address':hex(address),'value':value,'width':1,'reason':'Diagnostic inactive-bank SRAM corruption before native verification; no campaign/RAM state preparation'});self.e.write(address,value,1)
  self.wait(lambda:self.g('game_state')!=6,700,'A');self.check('failed first-ending save remains visible on ending card',self.g('save_failed')==1 and self.g('save_failure_notice')==1 and self.g('game_state')==5);self.step(3);self.shot('diagnostic-ending-save-failure')
  baseline=self.snapshot();self.tap('A');self.check('failed-save card can open roll without implicit retry',self.g('ending_credits_phase')==1);self.step(60);self.unchanged(baseline,'credit replay does not retry failed save or mutate progress');self.check('save error remains visible during roll',self.g('save_failed')==1 and self.g('save_failure_notice')==1);self.shot('diagnostic-roll-save-failure');self.tap('B');self.check('exit still reaches village after failed save',self.g('game_state')==1)
 def title_only(self):self.boot(True);self.shot('native-title-no-credit')
 def report(self):
  d=super().report();d['suite']='endroll-native';d['scope']='Historical completed-save controller-only replay; authentic pending-save first-ending controller route unless separately labeled RAM-prepared.';d['provenance']['endroll_test_sha256']=sha(__file__);(self.out/'report.json').write_text(json.dumps(d,indent=2)+'\n');return d
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--rom',type=Path,default=ROOT/'build/emberbond.gba');p.add_argument('--symbols',type=Path,default=ROOT/'build/emberbond.sym');p.add_argument('--expected-rom-sha');p.add_argument('--expected-symbols-sha');p.add_argument('--cases',default='title_only,replay,boundaries,first_ending,save_failure_diagnostic');a=p.parse_args();r=Endroll(a)
 for name in a.cases.split(','):r.section(name,getattr(r,name))
 d=r.finish();raise SystemExit(int(bool(d['failures']) or not d['performance']['strict_measured_pacing_pass']))
