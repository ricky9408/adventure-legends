#!/usr/bin/env python3
"""Prepared native cache/full-render comparison; includes a controller-replayed
real double kill and explicitly synthetic presentation-only room/flag cases.
Same-ROM state restores and cache/flag writes are logged; no acquisition claim.
"""
from pathlib import Path
import argparse,ctypes as C,gzip,json,re,shutil,sys,hashlib
from PIL import ImageChops
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_native import Native,sha
p=argparse.ArgumentParser(description=__doc__)
for name in ('rom','symbols','bridge','source-manifest','controller-inputs','output'):p.add_argument('--'+name,type=Path,required=True)
for name in ('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+name,required=True)
p.add_argument('--reference-uncached-notices',action='store_true')
a=p.parse_args();O=a.output.resolve();O.mkdir(parents=True,exist_ok=False)
source_map=json.loads(a.source_manifest.read_text());assert all(sha(ROOT/n)==v for n,v in source_map.items()),'source changed after build receipt'
for s,n in [(a.rom,'tested.gba'),(a.symbols,'tested.sym'),(a.bridge,'bridge.so'),(a.source_manifest,'source-hashes.json'),(a.controller_inputs,'controller-inputs.json.gz')]:shutil.copyfile(s,O/n)
assert sha(O/'tested.gba')==a.expected_rom_sha
assert sha(O/'tested.sym')==a.expected_symbols_sha
shutil.copyfile(__file__,O/'helper.py');sym={v[2]:int(v[0],16)for l in(O/'tested.sym').read_text().splitlines()if len(v:=l.split())==3}
e=Native(O/'tested.gba',O/'bridge.so');writes=[];results=[];trace=[];phase='controller-prefix';restores=0

def g(n):return e.read(sym[n])
def put(n,v,off=0):writes.append({'phase':phase,'hw':e.frame,'symbol':n,'offset':off,'value':v});e.write(sym[n]+off,v,4)
def step(n,k=0,full=False):
 for _ in range(n):
  if full:put('cache_valid',0);put('cache_valid',0,4)
  e.frames(1,k)
def capture():
 return {'frame':g('frame'),'kills':g('kills'),'revision':g('progression_revision'),'room_flags':g('room_flags'),'chapter_flags':g('chapter_flags'),'quickparty_revision':g('quickparty_revision'),'gear_menu_revision':g('gear_menu_revision'),'shop_revision':g('game_shop_revision'),'strip_valid':[e.read(sym['play_strip_valid']+4*i)for i in range(2)],'strip_clean':[e.read(sym['play_strip_clean']+4*i)for i in range(2)],'cache_fields':[[e.read(sym['cache_fields']+4*(p*45+i))for i in range(45)]for p in range(2)],'profile_frame':g('render_profile_frame'),'profile_world':g('render_profile_world'),'profile_card':g('render_profile_card')}
def compare(label,base,mutate):
 global phase,restores
 samples=[]
 for full in [False,True]:
  phase=label+('-full'if full else'-cached');e.state(base,load=True);restores+=1
  if full and a.reference_uncached_notices:put('play_notice_cache_disabled',1)
  mutate();step(3,full=full);v={}
  for _ in range(2):
   step(1,full=full);page=int(bool(e.read(0x04000000,2)&16));v[page]=(e.screenshot(),e.bytes(0x07000000,1024),g('frame'))
  samples.append(v)
 for page in [0,1]:
  cached,reference=samples[0][page],samples[1][page];dif=ImageChops.difference(cached[0],reference[0]);bounds=dif.getbbox();ok=bounds is None and cached[1]==reference[1]and cached[2]==reference[2]
  results.append({'case':label,'page':page,'passed':ok,'difference_bounds':bounds,'oam_equal':cached[1]==reference[1],'logical_frames':[cached[2],reference[2]]})
  if not ok or label=='actual-double-kill':cached[0].save(O/f'{label}-{page}-cached.png');reference[0].save(O/f'{label}-{page}-full.png')
  if not ok:dif.save(O/f'{label}-{page}-difference.png')
inputs=json.load(gzip.open(O/'controller-inputs.json.gz','rt'))
for row in inputs:
 if row['session']!=0:continue
 assert e.frame==row['emulator_frame']
 for _ in range(row['frames']):
  if e.frame>=5356:break
  step(1,row['keys'])
  if e.frame>=5349:trace.append({'hw':e.frame,**capture()})
 if e.frame>=5356:break
assert g('room')==6 and g('kills')==4 and g('game_shop_reward_xp')==180 and g('game_shop_reward_gold')==6
actual=O/'actual-post-double-kill.state';e.state(actual);compare('actual-double-kill',actual,lambda:None)
# Freeze field simulation, while native drawing, OAM and overlay timers still run.
layout=json.load(open(ROOT/'assets/campaign_layouts.json'));fb=layout['flags'];chapter={'GROVE_CLEAR':1,'SKY_CLEAR':2,'CORE_CLEAR':4,'ENDING_SEEN':8}
for room in layout['rooms']:
 r=room['id']
 if not 4<=r<=13:continue
 phase=f'prepare-room{r}';e.state(actual,load=True);restores+=1
 for n,v in [('room',r),('game_state',1),('px',120),('py',120),('px_q8',120*256),('py_q8',120*256),('cx',134),('cy',123),('cx_q8',134*256),('cy_q8',123*256),('camera_x',0),('camera_y',0),('transition',0),('transition_lock',0),('scene_present_phase',0),('hitstop',200),('invuln',0),('summoned',0),('room_flags',0),('chapter_flags',0),('reward_ticks',0),('toast_ticks',0),('area_ticks',0),('save_requested',0),('save_feedback_background',0),('gfx_props_room',0xffffffff),('cache_valid',0)]:put(n,v)
 put('cache_valid',0,4)
 for i in range(6):put('enemies',0,i*20+8)
 step(3);base=O/f'room{r}.state';e.state(base)
 def xp():
  put('progression_revision',g('progression_revision')+1);put('game_shop_reward_xp',180);put('game_shop_reward_gold',6);put('reward_ticks',95);put('game_shop_revision',g('game_shop_revision')+1)
 compare(f'room{r}-xp-revision',base,xp)
 for k,obstacle in enumerate(room.get('dynamic_solids',[])):
  rf=sum(1<<fb[n]for n in obstacle['blocking_unless_all']if n in fb);cf=sum(chapter[n]for n in obstacle['blocking_unless_all']if n in chapter)
  def flags(rf=rf,cf=cf):put('room_flags',rf);put('chapter_flags',cf);put('progression_revision',g('progression_revision')+1)
  compare(f'room{r}-flag{k}',base,flags)
unchanged=all(sha(ROOT/n)==v for n,v in source_map.items())
report={'scope':__doc__,'passed':all(x['passed']for x in results)and unchanged and not e.lib.eb_faults(e.ptr),'source_unchanged_during_run':unchanged,'candidate':{n:sha(O/n)for n in['tested.gba','tested.sym','bridge.so','helper.py','source-hashes.json','controller-inputs.json.gz']},'comparisons':results,'cases':len(results),'writes':writes,'same_rom_state_restores':restores,'reference_uncached_notices':a.reference_uncached_notices,'double_kill_trace':trace,'faults':e.lib.eb_faults(e.ptr)}
(O/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'comparisons':len(results),'failures':[r for r in results if not r['passed']],'faults':report['faults']},indent=2));e.close();raise SystemExit(not report['passed'])
