#!/usr/bin/env python3
"""Focused controller-only successor exploration and merchant-prompt evidence.

A fresh cartridge earns every state. No game RAM writes, imported saves, or
machine states. A second fresh campaign earns the first boss before exercising
its newly available walking chapter entrance. This is not full-game acceptance.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,re,shutil,struct,sys,traceback
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_native import Native,sha
from player_feedback_campaign import FeedbackCampaign
from mgba_runner import keymask
class ButtonsOnly(Native):
 def write(self,*a,**k):raise AssertionError('Game-RAM writes are forbidden')
 def state(self,*a,**k):raise AssertionError('Machine states are forbidden')
 def load_save(self,*a,**k):raise AssertionError('Imported SRAM is forbidden')
class Exploration:
 def __init__(self,a):
  self.out=a.output/'fresh-village';self.out.mkdir(parents=True);self.inputs=[];self.shots=[];self.checks=[];self.rows=[];self.measured=False
  self.rom=self.out/'tested.gba';shutil.copyfile(a.rom,self.rom);shutil.copyfile(a.symbols,self.out/'tested.sym')
  self.sym={v[2]:int(v[0],16) for line in a.symbols.read_text().splitlines() if len(v:=line.split())==3}
  self.ids=list(dict.fromkeys(re.findall(r'\bTX_[A-Z0-9_]+\b',(ROOT/'src/ui.h').read_text())))
  self.candidate={'rom_sha256':sha(self.rom),'symbols_sha256':sha(a.symbols),'bridge_sha256':sha(a.bridge),'helper_sha256':sha(__file__)}
  self.e=ButtonsOnly(self.rom,a.bridge)
 def g(self,n):return self.e.read(self.sym[n])
 def status(self):return {n:self.g(n) for n in ('game_state','room','px','py','frame','toast_id','toast_ticks','swing','quickparty_open','spirit','summoned','transition_lock','scene_present_phase')}
 def step(self,n=1,k=0):
  self.inputs.append({'hardware_frame':self.e.frame,'frames':n,'keys':keymask(k),'status':self.status()})
  for _ in range(n):
   before=self.g('frame');page=self.e.read(0x04000000,2)&16;self.e.frames(1,k)
   if self.measured:self.rows.append({'hardware_frame':self.e.frame,'delta':(self.g('frame')-before)&0xffffffff,'flip':page!=(self.e.read(0x04000000,2)&16),'cycles':self.g('render_cycles'),'faults':self.e.lib.eb_faults(self.e.ptr),'status':self.status()})
 def tap(self,k,h=2,r=4):self.step(h,k);self.step(r)
 def check(self,label,condition):
  self.checks.append({'label':label,'passed':bool(condition),'status':self.status()});assert condition,(label,self.status());print('PASS',label,flush=True)
 def shot(self,name,keys=0):
  self.step(4,keys);p=self.out/(name+'.png');self.e.screenshot(p);self.shots.append({'name':name,'path':str(p),'sha256':sha(p),'status':self.status()})
 def goto(self,x=None,y=None,limit=400):
  for _ in range(limit):
   if x is not None and abs(self.g('px')-x)>1:k='RIGHT' if self.g('px')<x else 'LEFT'
   elif y is not None and abs(self.g('py')-y)>1:k='DOWN' if self.g('py')<y else 'UP'
   else:return
   self.step(1,k);assert self.g('game_state')==1,self.status()
  raise AssertionError(('navigation blocked',x,y,self.status()))
 def approach_closed_west(self):
  # Observe the real fixed-point next step so A/R lands on the crossing frame.
  speed=self.e.read(self.sym['gear_stats']+2,2)
  for _ in range(100):
   if (self.g('px_q8')-speed)>>8<=92:return
   self.step(1,'LEFT')
  raise AssertionError('west threshold approach did not finish')
 def hint(self):
  data=self.e.bytes(0x07000000,1024)
  return any((a0&0x300)!=0x200 and (a0&255)==73 and (a1&511)==52 and (a2&1023)==840 for a0,a1,a2,_ in struct.iter_unpack('<HHHH',data))
 def run(self):
  self.step(160);self.tap('A')
  for _ in range(120):
   if self.g('game_state')==2:self.tap('A')
   elif self.g('game_state') in (6,10,12):self.step(10)
   else:break
  self.step(120);self.check('fresh village starts without chapter progress',self.g('game_state')==1 and self.g('room')==0 and not self.g('chapter_flags'));self.measured=True
  self.shot('01-village-spawn');self.approach_closed_west();self.step(1,'LEFT+A')
  self.check('crossing a closed chapter route retains fresh attack A',self.g('room')==0 and self.g('game_state')==1 and self.g('swing')>0)
  self.check('village route hint is plain and nonmodal',self.g('toast_id')==self.ids.index('TX_PF_ROUTE_LATER') and self.g('toast_ticks')==110)
  self.shot('02-closed-route-attack');before=self.g('toast_ticks');self.step(5,'LEFT');self.check('held movement does not refresh a latched hint',self.g('toast_ticks')==before-5)
  x,y,t=self.g('px'),self.g('py'),self.g('toast_ticks');self.step(1,'L+UP');self.step(15,'L');self.check('fast picker opens by the closed threshold and pauses movement',self.g('quickparty_open')==1 and (self.g('px'),self.g('py'))==(x,y) and self.g('toast_ticks')==t);self.shot('03-picker-by-route','L');self.step(4);self.check('picker release returns directly to movement',not self.g('quickparty_open') and self.g('game_state')==1)
  self.goto(x=67);self.goto(y=97);self.shot('04-shop-prompt');self.check('merchant A marker appears in the real interaction range',self.hint())
  self.tap('START');self.shot('05-shop-prompt-hidden-by-menu');self.check('merchant marker is hidden in the hub',not self.hint());self.tap('B');self.step(4);self.check('merchant marker returns after closing the hub',self.hint())
  self.step(4,'L');self.shot('06-shop-prompt-hidden-by-picker','L');self.check('merchant marker is hidden in the held-L picker',not self.hint());self.step(2,'L+B');self.step(4);self.check('B cancels the picker and restores the marker after release',not self.g('quickparty_open') and self.hint())
  self.tap('A');self.shot('07-shop-open');self.check('A opens the shop and hides the world marker',self.g('game_state')==11 and not self.hint());self.tap('B');self.step(4);self.check('B returns to the world and restores merchant marker',self.g('game_state')==1 and self.hint())
  self.goto(y=126);self.step(4);self.check('merchant marker clears outside real talk range',not self.hint());self.goto(y=107);self.goto(x=120);self.shot('08-shop-to-mainpath');self.check('shop-to-main-path walk crosses a closed later route freely',self.g('game_state')==1 and self.g('room')==0 and self.g('toast_id')==self.ids.index('TX_PF_ROUTE_LATER'))
  self.goto(y=126);self.goto(x=120);self.step(125);self.check('brief closed-route hint expires',self.g('toast_ticks')==0)
  self.approach_closed_west();self.step(1,'LEFT');self.check('walking out past the latch and returning shows hint again',self.g('toast_id')==self.ids.index('TX_PF_ROUTE_LATER') and self.g('toast_ticks')>100)
  self.goto(x=120);self.tap('B');self.check('companion summoned before testing R through closed route',self.g('summoned')==1);self.approach_closed_west();self.step(1,'LEFT+R');self.check('closed threshold does not swallow companion R',self.g('game_state')==1 and self.g('ability_cd')>0);self.shot('09-closed-route-power');self.step(150);self.shot('10-hint-cleanly-cleared')
  self.check('all measured village/picker/shop frames update and display on cadence',not any(r['delta']!=1 or not r['flip'] or r['cycles']>=280896 or r['faults'] for r in self.rows))
 def report(self):
  with gzip.open(self.out/'native-frames.jsonl.gz','wt')as f:
   for r in self.rows:f.write(json.dumps(r)+'\n')
  (self.out/'inputs.json').write_text(json.dumps(self.inputs,indent=2))
  (self.out/'exploration.json').write_text(json.dumps({'suite':'experience-polish-fresh-village','controller_only':True,'game_ram_writes':0,'machine_state_inputs':0,'imported_saves':0,'candidate':self.candidate,'checks':self.checks,'shots':self.shots,'measured_frames':len(self.rows),'max_cycles':max([r['cycles']for r in self.rows],default=0)},indent=2))
class FirstChapter(FeedbackCampaign):
 def report(self):
  super().report()
  if not hasattr(self,'e')or not self.e.ptr:return
  p=self.out/'player-feedback-campaign.json'
  if p.exists():
   d=json.loads(p.read_text());d['suite']='experience-polish-controller-earned-first-chapter-entry';d['scope']='First boss earned with buttons, allowed walking chapter gate and arrival tested; not the full campaign';d['route_complete']=getattr(self,'focused_complete',False);p.write_text(json.dumps(d,indent=2))
 def run(self):
  self.first_chapter();self.goto(y=128);self.hub(4);self.shot('allowed-east-chapter-arrival');self.check(self.get('room')==4,'controller-earned chapter gate still enters with walking only')
  self.step(18,'RIGHT');self.check(self.get('room')==4,'held arrival direction does not bounce back');self.shot('allowed-arrival-held-direction')
  self.goto(x=120);self.nextroom(0,'DOWN');self.step(25);self.step(12,'RIGHT');self.check(self.get('room')==0,'earned return to village preserves held-direction entrance latch');self.step(15);self.check(self.get('room')==0,'earned return remains stable on neutral input');self.shot('allowed-return-to-village')
  self.check(not any(self.metrics[k]for k in ('update_misses','flip_misses','cycle_overruns','faults','publication_spills')),'earned route and allowed handoff preserve native cadence');self.focused_complete=True

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('rom','symbols','bridge','output'):p.add_argument('--'+key,type=Path,required=True)
 p.add_argument('--skip-earned-chapter',action='store_true');a=p.parse_args()
 if a.output.exists()and any(a.output.iterdir()):p.error('output must be fresh; earlier evidence is retained')
 a.output.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(Path(__file__),a.output/'experience_exploration_native.py')
 shutil.copyfile(a.rom.parent/'source-hashes.json',a.output/'candidate-source-hashes.json')
 r=Exploration(a)
 try:r.run()
 except Exception:r.shot('failure');traceback.print_exc();return 1
 finally:r.report();r.e.close()
 if not a.skip_earned_chapter:
  c=FirstChapter(a.rom,a.symbols,a.output/'earned-chapter',a.bridge)
  try:c.run()
  except Exception:c.shot('failure');traceback.print_exc();return 1
  finally:c.report();c.trace.close();c.e.close()
 return 0
if __name__=='__main__':raise SystemExit(main())
