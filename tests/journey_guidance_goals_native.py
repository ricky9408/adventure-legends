#!/usr/bin/env python3
"""Native goal/celebration inspection; historical checkpoints are not acquisition."""
import argparse,ctypes as C,gzip,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_campaign import ControllerNative
from mgba_runner import keymask
from test_save5 import Save
class Strict(ControllerNative):
 def __init__(self,*a):
  super().__init__(*a);self.lib.eb_write=self.write;self.lib.eb_state=self.state
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--bridge',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 assert not a.output.exists();a.output.mkdir(parents=True)
 m=json.loads((a.candidate/'candidate.json').read_text());rom=a.candidate/'emberbond.gba';symbols=a.candidate/'emberbond.sym'
 for p in (rom,symbols):assert sha(p)==m['files'][p.name]['sha256']
 sym={v[2]:int(v[0],16) for l in symbols.read_text().splitlines() if len(v:=l.split())==3}
 report={'scope':'Controller-only presentation and legacy-save inspection. Historical QA saves are not current acquisition. No game-memory writes or machine states.','candidate':m,'bridge_sha256':sha(a.bridge),'helper_sha256':sha(__file__),'sessions':[]}
 cases=[('fresh',None),('lights-pending','tests/fixtures/v4/core-complete-ending-pending.sav'),('lights-complete','tests/fixtures/v4/finished-ending.sav'),('north-complete','tests/fixtures/v5-revision3/northern-main-only-sky.sav'),('south-complete','tests/fixtures/v5-revision4/southern-minimal8-town.sav'),('mountain-complete','tests/fixtures/v5-revision5-minimal/magma-minimal10-town.sav'),('sea-complete','tests/fixtures/v5-revision6/underwater-minimal12-town.sav'),('return-complete','tests/fixtures/horizons-native-prior-h/minimal-north-lifecycle/main-route-cold-save-after.sav'),('horizons-complete','tests/fixtures/v5-revision8/horizons-all120-64-cold.sav')]
 frames=gzip.open(a.output/'frames.jsonl.gz','wt')
 for name,fixture in cases:
  row={'name':name,'fixture':fixture,'inputs':[],'screenshots':[],'measured_updates':0,'misses':0,'overruns':0,'peak_cycles':0};report['sessions'].append(row)
  e=Strict(rom,a.bridge);measured=False
  def g(n):return e.read(sym[n])
  def step(n,k=0):
   row['inputs'].append({'frame':e.frame,'frames':n,'keys':keymask(k)})
   for _ in range(n):
    previous=g('frame');e.frames(1,k);delta=(g('frame')-previous)&0xffffffff
    f={'session':name,'frame':e.frame,'mode':g('game_state'),'delta':delta,'cycles':g('render_cycles'),'measured':measured,'faults':e.lib.eb_faults(e.ptr)}
    frames.write(json.dumps(f,separators=(',',':'))+'\n');assert not f['faults'];assert not g('save_failed')
    if measured:
     row['measured_updates']+=1;row['misses']+=delta!=1;row['overruns']+=f['cycles']>=280896;row['peak_cycles']=max(row['peak_cycles'],f['cycles'])
  def tap(k):step(2,k);step(4)
  def shot(suffix):
   step(4);p=a.output/(name+'-'+suffix+'.png');e.screenshot(p);row['screenshots'].append({'path':p.name,'sha256':sha(p),'frame':e.frame,'room':g('room'),'mode':g('game_state')})
  if fixture:
   source=ROOT/fixture;row['fixture_sha256']=sha(source);copy=a.output/(name+'-input.sav');shutil.copyfile(source,copy);e.load_save(copy);e.reset()
  step(160);tap('A')
  for _ in range(1600):
   if g('game_state') in (2,14):tap('A')
   elif g('game_state')==1 and not g('save_requested') and not g('save_feedback_background') and not g('scene_present_phase'):break
   else:step(1)
  else:raise AssertionError(('Continue did not settle',name))
  step(160)
  for _ in range(2400):
   if not g('save_requested') and not g('save_feedback_background') and not g('scene_present_phase') and g('game_state')==1:break
   step(1)
  else:raise AssertionError(('Background save did not settle',name))
  before=e.bytes(sym['adventure_save'],C.sizeof(Save));sram=e.bytes(0x0e000000,32768)
  measured=True;tap('START');tap('RIGHT');tap('DOWN');tap('DOWN');tap('A');tap('A');assert g('journal_tab')==0
  shot('goal');tap('SELECT');tap('R');step(30)
  after=e.bytes(sym['adventure_save'],C.sizeof(Save));after_sram=e.bytes(0x0e000000,32768)
  row['state_byte_changes']=[i for i,(x,y) in enumerate(zip(before,after)) if x!=y]
  row['sram_byte_changes']=[i for i,(x,y) in enumerate(zip(sram,after_sram)) if x!=y]
  (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
  assert before==after,('Save5 changed',name,row['state_byte_changes'])
  assert sram==after_sram,('SRAM changed',name,row['sram_byte_changes'][:32])
  tap('B');assert g('journal_tab')==14;tap('START');assert g('game_state')==1
  row['browsing_save_unchanged']=True;row['browsing_sram_unchanged']=True
  if name=='lights-pending':
   # Loaded checkpoint is at the home elder. This interaction earns only the
   # original ending on this candidate; prior three lights remain historical.
   measured=False;step(10,'UP');tap('A')
   for _ in range(24):
    if g('game_state')==2:tap('A')
    elif g('game_state') in (6,10,12):step(20)
    else:break
   assert g('game_state')==5,('Expected chapter card',g('game_state'))
   step(60);measured=True;shot('chapter-card');tap('A');assert g('game_state')==1
   measured=False;step(140);assert g('chapter_flags')&8
   tap('START');tap('RIGHT');tap('DOWN');tap('DOWN');tap('A');tap('A');shot('next-goal');tap('START')
  row['final_room']=g('room');row['final_chapter_flags']=g('chapter_flags');row['core_faults']=e.lib.eb_faults(e.ptr)
  e.close();(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 frames.close();report['result']='PASS' if all(not r['misses'] and not r['overruns'] for r in report['sessions']) else 'FAIL_CADENCE'
 (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'result':report['result'],'sessions':len(report['sessions']),'peak':max(r['peak_cycles'] for r in report['sessions']),'misses':sum(r['misses'] for r in report['sessions'])}))
 return report['result']!='PASS'
if __name__=='__main__':raise SystemExit(main())
