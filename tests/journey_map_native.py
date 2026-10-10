#!/usr/bin/env python3
"""Controller-only map inspection on authenticated, explicitly prepared saves.

This is UI/topology presentation evidence with three short road returns, not fresh regional acquisition.
Game-RAM writes and machine-state imports are forbidden by ControllerNative.
"""
from pathlib import Path
import argparse,ctypes as C,gzip,hashlib,json,shutil,sys,traceback
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_campaign import ControllerNative
from connected_roads_fixtures import CheckpointFixtures
from mgba_runner import keymask
from test_save5 import Save

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class MapRun:
 def __init__(self,a):
  self.out=a.output.resolve();self.out.mkdir(parents=True,exist_ok=False)
  self.rom=a.rom.resolve();self.symbols=a.symbols.resolve();self.bridge=a.bridge.resolve()
  self.sym={v[2]:int(v[0],16) for line in self.symbols.read_text().splitlines() if len(v:=line.split())==3}
  manifest=json.loads((self.rom.parent/'source-hashes.json').read_text())
  assert all(sha(ROOT/name)==value for name,value in manifest.items()),'Candidate source closure changed'
  for p in (self.rom,self.symbols,self.bridge):shutil.copyfile(p,self.out/p.name)
  shutil.copyfile(self.rom.parent/'source-hashes.json',self.out/'source-hashes.json')
  self.report={'scope':__doc__,'candidate':{'rom_sha256':sha(self.rom),'symbols_sha256':sha(self.symbols),'bridge_sha256':sha(self.bridge),'helper_sha256':sha(__file__)},'game_ram_writes':0,'machine_state_imports':0,'sessions':[],'failures':[]}
  self.trace=gzip.open(self.out/'frames.jsonl.gz','wt');self.e=None;self.session=None;self.measure=False
 def g(self,name):return self.e.read(self.sym[name])
 def state(self):return {n:self.g(n) for n in ('game_state','room','px','py','journal_tab','journal_nav_revision','save_failed')}
 def step(self,n,key=0):
  self.session['inputs'].append({'frame':self.e.frame,'frames':n,'keys':keymask(key)})
  for _ in range(n):
   old=self.g('frame');page=self.e.read(0x04000000,2)&16;self.e.frames(1,key)
   if self.measure:
    row={'session':self.session['label'],'phase':getattr(self,'phase',-1),'frame':self.e.frame,'delta':(self.g('frame')-old)&0xffffffff,'flip':page!=(self.e.read(0x04000000,2)&16),'cycles':self.g('render_cycles'),'state':self.g('game_state'),'tab':self.g('journal_tab')}
    for name in ('update','render','world','card','music'):
     symbol='render_profile_'+name
     if symbol in self.sym:row[name]=self.g(symbol)
    self.trace.write(json.dumps(row,separators=(',',':'))+'\n')
    m=self.session['cadence'];m['frames']+=1;m['max_cycles']=max(m['max_cycles'],row['cycles']);m['update_misses']+=row['delta']!=1;m['flip_misses']+=not row['flip'];m['overruns']+=row['cycles']>=280896
   assert not self.e.lib.eb_faults(self.e.ptr),self.state()
   assert not self.g('save_failed'),self.state()
 def tap(self,key):self.step(2,key);self.step(4)
 def shot(self,name):
  self.step(3);p=self.out/(self.session['label']+'-'+name+'.png');self.e.screenshot(p)
  self.session['screenshots'].append({'path':p.name,'sha256':sha(p),'state':self.state()})
 def start(self,label,save=None):
  self.session={'label':label,'prepared_progress':bool(save),'inputs':[],'screenshots':[],'cadence':{'frames':0,'max_cycles':0,'update_misses':0,'flip_misses':0,'overruns':0}}
  self.report['sessions'].append(self.session);self.measure=False;self.e=ControllerNative(self.rom,self.bridge)
  if save:self.session['input_save']={'path':str(save),'sha256':sha(save)};self.e.load_save(save);self.e.reset()
  self.step(160);self.tap('A')
  for _ in range(1500):
   if self.g('game_state') in (2,14):self.tap('A')
   elif self.g('game_state')==1 and not self.g('save_feedback_background') and not self.g('save_requested'):break
   else:self.step(1)
  assert self.g('game_state')==1,self.state()
  self.step(30)
 def inspect(self,close=True):
  before=self.e.bytes(self.sym['adventure_save'],C.sizeof(Save));position=(self.g('room'),self.g('px'),self.g('py'))
  self.measure=True;self.tap('START');self.tap('DOWN');self.tap('DOWN');self.tap('A')
  assert self.g('game_state')==3 and self.g('journal_tab')==1,self.state();self.shot('current-map')
  for page in (1,2):
   for _ in range(3):self.tap('DOWN')
   self.shot('exits-'+str(page))
  fixed=self.e.screenshot().tobytes();self.tap('SELECT');assert self.e.screenshot().tobytes()==fixed,'Select changed Map'
  self.tap('A');self.shot('places');self.tap('DOWN');self.tap('A');self.shot('chosen-place')
  self.tap('B');assert self.g('journal_tab')==1;self.tap('RIGHT');self.shot('next-region')
  self.tap('B');self.shot('current-again');self.tap('B');assert self.g('journal_tab')==13
  self.tap('A');assert self.g('journal_tab')==1;self.shot('reopened');self.tap('START');self.measure=False
  assert self.g('game_state')==1 and position==(self.g('room'),self.g('px'),self.g('py'))
  assert self.e.bytes(self.sym['adventure_save'],C.sizeof(Save))==before,'Map inspection changed Save5 bytes'
  self.session['save_bytes_unchanged']=True;self.session['position_unchanged']=True;self.session['faults']=self.e.lib.eb_faults(self.e.ptr)
  if close:self.e.close();self.e=None
 def cross(self,target,key):
  source=self.g('room');start=self.e.frame
  for _ in range(700):
   if self.g('room')!=source:break
   if self.g('game_state')==2:self.tap('A')
   else:self.step(1,key if self.g('game_state')==1 else 0)
  assert self.g('room')==target,('Map direction did not reach its named neighbor',source,target,self.state())
  for _ in range(1500):
   if self.g('game_state')==1 and not self.g('save_feedback_background') and not self.g('save_requested'):break
   if self.g('game_state')==2:self.tap('A')
   else:self.step(1)
  self.session.setdefault('road_crossings',[]).append({'from':source,'to':target,'direction':key,'first_frame':start,'last_frame':self.e.frame,'controller_only':True})
  self.measure=True;self.tap('START');self.tap('DOWN');self.tap('DOWN');self.tap('A');self.shot('walk-arrived-'+str(target));self.tap('START');self.measure=False
 def phases(self,save,new_pause):
  self.start('prepared-first-open-phases' if new_pause else 'prepared-reopen-phases',save)
  before=self.e.bytes(self.sym['adventure_save'],C.sizeof(Save))
  if not new_pause:self.tap('START');self.tap('DOWN');self.tap('DOWN')
  for delay in range(32):
   self.step(delay);self.phase=delay;self.measure=True
   if new_pause:self.tap('START');self.tap('DOWN');self.tap('DOWN')
   self.tap('A');self.tap('A');self.tap('B');self.tap('B')
   assert self.g('game_state')==3 and self.g('journal_tab')==13,self.state()
   if new_pause:self.tap('START')
   self.measure=False;self.phase=-1
  self.session['save_bytes_unchanged']=self.e.bytes(self.sym['adventure_save'],C.sizeof(Save))==before
  assert self.session['save_bytes_unchanged'];self.session['faults']=self.e.lib.eb_faults(self.e.ptr)
  self.e.close();self.e=None
 def run(self):
  fixture=CheckpointFixtures(self.out/'fixtures')
  try:
   prepared={a:fixture.create(a,0) for a in (0,1,4,9,16,22,30,38,46,54,55,62,70)}
   middle=fixture.create(46,3);late=fixture.create(62,5)
  finally:fixture.close()
  self.start('fresh');self.inspect()
  for area,save in prepared.items():
   assert save is not None;self.start('prepared-'+str(area),save);assert self.g('room')==area,self.state();self.inspect()
  for label,save,source,target,outward,homeward in [('fresh-road-return',None,0,1,'UP','DOWN'),('prepared-middle-road-return',middle,46,47,'RIGHT','LEFT'),('prepared-cross-region-return',late,62,70,'UP','DOWN')]:
   self.start(label,save);assert self.g('room')==source;self.inspect(close=False);self.cross(target,outward);self.cross(source,homeward);self.e.close();self.e=None
  self.phases(prepared[62],False);self.phases(prepared[62],True)
 def finish(self):
  if self.e:self.session['last_state']=self.state();self.e.close()
  self.trace.close();self.report['passed']=not self.report['failures'] and all(not any(s['cadence'][k] for k in ('update_misses','flip_misses','overruns')) for s in self.report['sessions'])
  (self.out/'report.json').write_text(json.dumps(self.report,indent=2)+'\n')
  print(json.dumps({'passed':self.report['passed'],'sessions':len(self.report['sessions']),'screenshots':sum(len(s['screenshots']) for s in self.report['sessions']),'cadence':[dict(label=s['label'],**s['cadence']) for s in self.report['sessions']],'failures':self.report['failures'],'report':str(self.out/'report.json')},indent=2))

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('rom','symbols','bridge','output'):p.add_argument('--'+key,type=Path,required=True)
 r=MapRun(p.parse_args())
 try:r.run()
 except Exception as e:r.report['failures'].append(repr(e));traceback.print_exc()
 finally:r.finish()
 return int(not r.report['passed'])
if __name__=='__main__':raise SystemExit(main())
