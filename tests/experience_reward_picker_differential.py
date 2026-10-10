"""Independent native render differential. Prepared UI reward and same-ROM
machine-state branches are explicit; this does not establish reward acquisition.
"""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
from PIL import ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_native import Native,sha
p=argparse.ArgumentParser(description=__doc__)
for name in ('rom','symbols','bridge','output','source-manifest'):p.add_argument('--'+name,type=Path,required=True)
for name in ('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+name,required=True)
a=p.parse_args()
out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);rom=a.rom.resolve();sp=a.symbols.resolve();bridge=a.bridge.resolve();manifest=a.source_manifest.resolve()
assert sha(rom)==a.expected_rom_sha and sha(sp)==a.expected_symbols_sha
sym={v[2]:int(v[0],16)for line in sp.read_text().splitlines()if len(v:=line.split())==3}
shutil.copyfile(__file__,out/'helper.py')
e=Native(rom,bridge);inputs=[];writes=[];frames=[];branch='boot';state_restores=0
def get(n):return e.read(sym[n])
def put(n,v,offset=0,reason='full-render reference cache invalidation'):
 writes.append({'branch':branch,'frame':e.frame,'symbol':n,'offset':offset,'value':v,'reason':reason});e.write(sym[n]+offset,v,4)
def step(n,k=0,full=False):
 inputs.append({'branch':branch,'frame':e.frame,'frames':n,'keys':k})
 for _ in range(n):
  if full:put('cache_valid',0);put('cache_valid',0,4)
  before=get('frame');page=e.read(0x04000000,2)&16;e.frames(1,k)
  frames.append({'branch':branch,'hw':e.frame,'delta':(get('frame')-before)&0xffffffff,'flip':page!=(e.read(0x04000000,2)&16),'cycles':get('render_cycles'),'reward_ticks':get('reward_ticks'),'picker':get('quickparty_open'),'faults':e.lib.eb_faults(e.ptr)})
def tap(k):step(2,k);step(4)
step(160);tap('A')
for _ in range(150):
 if get('game_state')==2:tap('A')
 elif get('game_state')in(6,10,12):step(10)
 else:break
step(140);assert get('game_state')==1
branch='prepared-reward'
for n,v in [('reward_ticks',95),('game_shop_reward_xp',180),('game_shop_reward_gold',6),('game_shop_revision',get('game_shop_revision')+1)]:put(n,v,reason='presentation-only reward setup; no gameplay acquisition claim')
step(4);e.screenshot(out/'prepared-reward.png');base=out/'prepared-reward.state';e.state(base)
cases={'open-hold':[(3,'L')],'select-while-held':[(3,'L'),(3,'L+UP')],'long-hold':[(130,'L')],'release':[(3,'L'),(3,0)],'cancel-and-release':[(3,'L'),(2,'L+B'),(3,0)]}
results=[]
for case,sequence in cases.items():
 views=[]
 for full in (False,True):
  branch=case+('-full'if full else'-cached');e.state(base,load=True);state_restores+=1
  for count,k in sequence:step(count,k,full)
  if case=='select-while-held':assert get('quickparty_candidate')==0,'Up must select the occupied starter slot'
  tail=sequence[-1][1];samples={}
  for _ in range(2):
   step(1,tail,full);page=int(bool(e.read(0x04000000,2)&16));samples[page]={'image':e.screenshot(),'oam':e.bytes(0x07000000,1024),'reward_ticks':get('reward_ticks'),'picker':get('quickparty_open'),'picker_candidate':get('quickparty_candidate')}
  views.append(samples)
 for page in (0,1):
  u,v=views[0][page],views[1][page];diff=ImageChops.difference(u['image'],v['image']);box=diff.getbbox();equal=box is None and u['oam']==v['oam']
  row={'case':case,'page':page,'passed':equal,'difference_bounds':box,'oam_equal':u['oam']==v['oam'],'reward_ticks':u['reward_ticks'],'picker':u['picker'],'picker_candidate':u['picker_candidate'],'cached_rgb_sha256':hashlib.sha256(u['image'].tobytes()).hexdigest(),'full_rgb_sha256':hashlib.sha256(v['image'].tobytes()).hexdigest()};results.append(row)
  if not equal or case in ('open-hold','release'):
   u['image'].save(out/f'{case}-page{page}-cached.png');v['image'].save(out/f'{case}-page{page}-full.png')
  if not equal:diff.save(out/f'{case}-page{page}-difference.png')
optimized=[f for f in frames if f['branch'].endswith('-cached')];perf={'measured_optimized_frames':len(optimized),'max_cycles':max(f['cycles']for f in optimized),'update_misses':sum(f['delta']!=1 for f in optimized),'flip_misses':sum(not f['flip']for f in optimized),'cycle_overruns':sum(f['cycles']>=280896 for f in optimized),'faults':max(f['faults']for f in optimized)}
pacing_pass=not any(perf[k]for k in ('update_misses','flip_misses','cycle_overruns','faults'))
reward_survives=all(r['reward_ticks']>0 for r in results if r['case']=='long-hold')
report={'passed':all(r['passed']for r in results)and pacing_pass and reward_survives,'reward_survives_long_hold':reward_survives,'scope':__doc__,'candidate':{'rom_sha256':sha(rom),'symbols_sha256':sha(sp),'source_manifest_sha256':sha(manifest),'bridge_sha256':sha(bridge),'helper_sha256':sha(__file__),'paths':{'rom':str(rom),'symbols':str(sp),'bridge':str(bridge),'source_manifest':str(manifest)}},'state_restores':state_restores,'cases':results,'optimized_pacing':perf,'inputs':inputs,'writes':writes}
(out/'result.json').write_text(json.dumps(report,indent=2));(out/'frames.json').write_text(json.dumps(frames,indent=2));print(json.dumps({'passed':report['passed'],'candidate':report['candidate'],'cases':results,'optimized_pacing':perf},indent=2));e.close();raise SystemExit(not report['passed'])
