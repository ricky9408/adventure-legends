#!/usr/bin/env python3
"""Read-only controller access to practical help after skipping the opening."""
from pathlib import Path
import argparse,sys,ctypes as C,json,hashlib,random
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tests')]
from player_feedback_native import Native
from test_save5 import Save
class Strict(Native):
 def write(self,*a,**kw):raise AssertionError('No RAM writes')
 def state(self,*a,**kw):raise AssertionError('No machine states')
 def __exit__(self,kind,value,traceback):
  if kind and hasattr(self,'failure_hook'):self.failure_hook(str(value))
  return super().__exit__(kind,value,traceback)
def main():
 p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=9408);p.add_argument('--save',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();a.output.mkdir(parents=True)
 sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 s={v[2]:int(v[0],16)for line in(ROOT/'build/emberbond.sym').read_text().splitlines()if len(v:=line.split())==3}
 report={'controller_only':True,'memory_writes':0,'machine_state_loads':0,'rom_sha256':sha(ROOT/'build/emberbond.gba'),'save_sha256':sha(a.save),'frames':0,'peak_cycles':0,'misses':0,'screenshots':[],'seed':a.seed,'inputs':[]}
 with Strict(str(ROOT/'build/emberbond.gba'),str(a.bridge))as e:
  def failure(error):
   report.update(result='FAIL',error=error)
   (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
   try:e.screenshot(a.output/'failure.png')
   except Exception as capture_error:print('Failure capture unavailable:',capture_error,file=sys.stderr)
  e.failure_hook=failure
  e.lib.eb_write=e.write;e.lib.eb_state=e.state;e.load_save(a.save);e.reset();e.frames(160);e.tap('A',2,180)
  g=lambda n:e.read(s[n]);state=lambda:e.bytes(s['adventure_save'],C.sizeof(Save));raw=lambda:e.bytes(0x0e000000,32768)
  assert g('game_state')==1
  # Cold Continue can start a routine checkpoint refresh. Compare read-only
  # browsing only after that already-pending writer has fully completed.
  for _ in range(1600):
   if not g('save_requested') and not g('save_feedback_background') and not g('scene_present_phase'):break
   e.frames(1)
  else:raise AssertionError('Cold Continue writer did not settle')
  report['baseline_frame']=g('frame');report['baseline_save_requested']=g('save_requested');report['baseline_background_writer']=g('save_feedback_background')
  before=state();sram=raw()
  def step(n,k=0):
   report['inputs'].append({'frame':e.frame,'frames':n,'keys':k})
   for _ in range(n):
    f=g('frame');page=e.read(0x04000000,2)&16;e.frames(1,k);c=g('render_cycles');report['frames']+=1;report['peak_cycles']=max(c,report['peak_cycles']);report['misses']+=(g('frame')-f)!=1 or page==(e.read(0x04000000,2)&16)or c>=280896;assert not e.lib.eb_faults(e.ptr)
  def tap(k):step(2,k);step(4)
  def shot(name):
   step(4);path=a.output/(name+'.png');e.screenshot(path);report['screenshots'].append({'file':path.name,'sha256':sha(path)})
  tap('START');assert g('journal_tab')==13;shot('post-skip-hub')
  tap('UP');tap('A');assert g('journal_tab')==16;shot('post-skip-controls')
  tap('B');tap('RIGHT');tap('UP');tap('A');assert g('journal_tab')==14;tap('A');assert g('journal_tab')==0;shot('post-skip-goal')
  tap('B');tap('B');tap('UP');tap('LEFT');tap('A');assert g('journal_tab')==2;tap('A');tap('DOWN');shot('post-skip-companion-field')
  tap('START');assert g('game_state')==1
  # A bounded seeded directional stress route stays within the read-only hub.
  # Persist the seed and inputs so the exact failure can be rerun locally.
  tap('START');assert g('journal_tab')==13
  rng=random.Random(a.seed)
  for _ in range(40):
   tap(rng.choice(('UP','DOWN','LEFT','RIGHT')))
   assert g('game_state')==3 and g('journal_tab')==13
  shot('seeded-hub-navigation');tap('START');step(30)
  assert g('game_state')==1;assert state()==before and raw()==sram;assert not report['misses']
 report['complete_save5_and_sram_unchanged']=True;report['result']='PASS';(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
