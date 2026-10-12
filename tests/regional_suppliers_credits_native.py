#!/usr/bin/env python3
"""Controller-only diagnostics from this review's earned SRAM snapshots.

Prior-ROM campaign acquisition is authenticated and explicitly labeled. This
does not substitute for a fresh route on the integrated candidate. Mutation
and machine-state imports are disabled, including direct-library escape paths.
"""
from pathlib import Path
from collections import deque
import argparse,ctypes as C,gzip,hashlib,json,re,shutil,struct,sys,traceback

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Diagnostics:
 def __init__(self,a):
  self.a=a;self.root=a.source_root.resolve();sys.path[:0]=[str(self.root/'tests'),str(self.root/'tools')]
  from journey_guidance_earned import StrictNative
  from test_save5 import Save
  from mgba_runner import keymask
  self.Native,self.Save,self.keymask=StrictNative,Save,keymask
  self.out=a.output.resolve();self.out.mkdir(parents=True,exist_ok=False)
  self.rom=a.rom.resolve();self.symbols=a.symbols.resolve();self.bridge=a.bridge.resolve()
  self.sym={v[2]:int(v[0],16) for line in self.symbols.read_text().splitlines() if len(v:=line.split())==3}
  self.producer=json.loads(a.producer_report.read_text());assert self.producer['controller_only'] and not self.producer['game_ram_writes'] and not self.producer['machine_state_imports'] and self.producer['route_complete'] and not self.producer['failures'] and all(c['passed'] for c in self.producer['checks'])
  self.candidate={n:sha(p) for n,p in [('rom',self.rom),('symbols',self.symbols),('elf',self.rom.with_suffix('.elf')),('bridge',self.bridge),('source_manifest',self.rom.parent/'source-hashes.json')]}
  if a.expected_rom_sha:assert self.candidate['rom']==a.expected_rom_sha
  manifest=json.loads((self.rom.parent/'source-hashes.json').read_text());assert all(sha(self.root/name)==value for name,value in manifest.items())
  shutil.copyfile(a.producer_report,self.out/'source-controller-producer.json');shutil.copyfile(__file__,self.out/'diagnostics-helper.py')
  self.e=None;self.case='';self.session=0;self.phase='boot';self.checks=[];self.failures=[];self.captures=[];self.sources=[];self.inputs=[];self.observations=[]
  self.metrics={'active_frames':0,'active_update_misses':0,'active_flip_misses':0,'active_overruns':0,'active_max_cycles':0,'faults':0}
  self.frames=gzip.open(self.out/'native-frames.jsonl.gz','wt');self.mask_cache={}
 def g(self,n,w=4):return self.e.read(self.sym[n],w)
 def state(self):return self.Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(self.Save)))
 def status(self):return {n:self.g(n) for n in ('game_state','room','px','py','hero_hp_q4','save_failed','save_requested','save_feedback_background','game_shop_selection','game_shop_confirm','ending_credits_phase','ending_credits_scroll','ending_credits_armed') if n in self.sym}
 def check(self,label,ok,detail=None):
  row={'case':self.case,'label':label,'passed':bool(ok),'frame':self.e.frame,'detail':detail};self.checks.append(row)
  if not ok:self.failures.append(row);raise AssertionError((label,self.status(),detail))
 def step(self,n=1,k=0):
  mask=self.keymask(k);self.inputs.append({'case':self.case,'session':self.session,'hardware_frame':self.e.frame,'frames':n,'keys':mask,'phase':self.phase})
  for _ in range(n):
   before=self.g('frame');page=self.e.read(0x04000000,2)&16;self.e.frames(1,mask)
   row={'case':self.case,'session':self.session,'hw':self.e.frame,'phase':self.phase,'delta':(self.g('frame')-before)&0xffffffff,'flip':bool(page!=(self.e.read(0x04000000,2)&16)),'cycles':self.g('render_cycles'),**self.status()}
   self.frames.write(json.dumps(row,separators=(',',':'))+'\n')
   faults=self.e.lib.eb_faults(self.e.ptr);self.metrics['faults']=max(self.metrics['faults'],faults)
   if self.phase=='active':
    m=self.metrics;m['active_frames']+=1;m['active_update_misses']+=row['delta']!=1;m['active_flip_misses']+=not row['flip'];m['active_overruns']+=row['cycles']>=280896;m['active_max_cycles']=max(m['active_max_cycles'],row['cycles'])
 def tap(self,k,n=2,r=3):self.step(n,k);self.step(r)
 def wait(self,pred,limit=1500,k=0):
  for _ in range(limit):
   if pred():return True
   self.step(1,k)
  return False
 def drain(self):self.check('background save settles',self.wait(lambda:not self.g('save_requested') and not self.g('save_feedback_background') and self.g('game_state') not in (6,10,12)))
 def boot(self,path,source=None):
  if self.e:self.e.close()
  self.session+=1;self.phase='boot';self.e=self.Native(self.rom,self.bridge)
  self.e.load_save(path);self.e.reset();self.check('cold title ready',self.wait(lambda:self.g('game_state')==0 and self.e.frame>=160))
  self.tap('A');self.check('A cold Continue reaches field',self.wait(lambda:self.g('game_state')==1));self.drain();self.step(4);self.phase='active'
  self.check('Continue has no save failure',not self.g('save_failed'))
  if source:self.sources.append(source)
 def load_earned(self,name):
  snap=self.producer['snapshots'][name];source=Path(snap['sram_path']);assert sha(source)==snap['sram_sha256']
  copied=self.out/(name+'.input.sav');shutil.copyfile(source,copied)
  self.boot(copied,{'snapshot':name,'sram_sha256':sha(copied),'producer_report_sha256':sha(self.a.producer_report),'producer_rom_sha256':self.producer['candidate']['rom_sha256'],'candidate_rom_sha256':self.candidate['rom'],'cross_rom_save_use':self.producer['candidate']['rom_sha256']!=self.candidate['rom']})
  assert sha(source)==snap['sram_sha256']
 def shot(self,name):
  self.step(3);p=self.out/(name+'.png')
  if p.exists():name+='-'+str(len(self.captures));p=self.out/(name+'.png')
  self.e.screenshot(p);self.captures.append({'label':name,'png_sha256':sha(p),'case':self.case,'status':self.status(),'hardware_frame':self.e.frame})
 def saved(self,name):
  self.drain();p=self.out/(name+'.sav');self.e.save(p);return p
 def mask(self):
  room=self.g('room')
  if room in self.mask_cache:return self.mask_cache[room]
  if room==0:
   body=re.search(r'asset_solids_village\[.*?\] = \{(.*?)\};',(self.root/'src/asset_collisions.h').read_text(),re.S)[1]
   rects=[tuple(map(int,s.split(','))) for s in re.findall(r'\{([^}]+)\}',body)];w,h,margin=240,160,0;bounds=(12,28,228,153)
  else:
   families={16:('region','region_reedhaven'),22:('north','north_hearthwake_quay'),30:('south','south_sunlace_anchorage'),38:('magma','magma_kilnstep_commons'),46:('underwater','underwater_nacreway'),54:('return','return_greenwake_common'),62:('horizons','horizons_room62'),70:('covenants','covenants_room70')}
   family,name=families[room];text=''.join(p.read_text() for p in sorted((self.root/'src'/f'{family}_art_data').glob('part_*.inc')))
   body=re.search(r'const \w+ArtRect '+name+r'_solids\[.*?\] = \{(.*?)\};',text,re.S)[1]
   rects=[tuple(map(int,r)) for r in re.findall(r'\{\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\}',body)];w,h,margin=480,320,5;bounds=(8,8,472,304)
  b=bytearray(w*h);left,top,right,bottom=bounds
  for y in range(h):
   for x in range(w):
    if not left<=x<=right or not top<=y<=bottom:b[y*w+x]=1
  for x,y,rw,rh in rects:
   lo,hi=max(0,x-margin),min(w,x+rw+margin)
   for yy in range(max(0,y-margin),min(h,y+rh+margin)):b[yy*w+lo:yy*w+hi]=b'\1'*(hi-lo)
  # Supplier navigation must walk around unrelated authored lift/ferry/stair
  # apertures. Preserve an arrival aperture when its latch owns our spawn.
  if 'travel_entries' in self.sym:
   count=self.g('travel_entry_count');assert count<=64;sx,sy=self.g('px'),self.g('py')
   for i in range(count):
    area,action,target,spawn,x,y,rw,rh=struct.unpack('<4Bhh2B',self.e.bytes(self.sym['travel_entries']+10*i,10))
    latched='latched' in self.sym and self.e.read(self.sym['latched']+4*(i//32))&(1<<(i%32))
    if area!=room or latched or x-16<=sx<x+rw+16 and y-16<=sy<y+rh+16:continue
    lo,hi=max(0,x-4),min(w,x+rw+4)
    for yy in range(max(0,y-4),min(h,y+rh+4)):b[yy*w+lo:yy*w+hi]=b'\1'*(hi-lo)
  self.mask_cache[room]=(b,w,h);return b,w,h
 def navigate(self,tx,ty,radius=3):
  original=self.g('room');b,w,h=self.mask();goal=ty*w+tx;queue=deque([goal]);parent={goal:None}
  while queue:
   p=queue.popleft();x,y=p%w,p//w
   for n in (p-1,p+1,p-w,p+w):
    if 0<=n<w*h and abs(n%w-x)+abs(n//w-y)==1 and not b[n] and n not in parent:parent[n]=p;queue.append(n)
  for _ in range(1600):
   self.check('route remains in expected town',self.g('room')==original and self.g('game_state')==1)
   x,y=self.g('px'),self.g('py')
   if abs(x-tx)+abs(y-ty)<=radius:return
   here=y*w+x;assert here in parent,('no safe foot route',self.status(),tx,ty)
   nxt=parent[here];direction=nxt-here;length=1;p=nxt
   while parent[p] is not None and parent[p]-p==direction:length+=1;p=parent[p]
   if length<=2 and parent[p] is not None:
    turn=parent[p]-p
    if 0<=here+2*turn<w*h and not b[here+turn] and not b[here+2*turn]:direction=turn;length=2
   self.step(max(1,min(10,int(length/1.25))),{1:'RIGHT',-1:'LEFT',w:'DOWN',-w:'UP'}[direction])
  raise AssertionError(('controller route stalled',self.status(),tx,ty))
 def supplier(self,index,name):
  rooms=(16,22,30,38,46,54,62,70);xs=(208,240,160,304,304,208,208,208);ys=(284,272,272,284,284,284,284,284);ids=(2,49,67,85,54,68,86,6);prices=(96,144,180,216,252,288,324,360)
  self.case='supplier-'+str(rooms[index]);self.load_earned(name);self.check('earned Continue starts in supplier town',self.g('room')==rooms[index])
  b,w,h=self.mask();approach=next((xs[index]+dx,ys[index]+dy) for dx,dy in ((-16,0),(16,0),(0,-16),(0,16)) if not b[(ys[index]+dy)*w+xs[index]+dx])
  self.navigate(*approach,3);self.shot(self.case+'-merchant');self.tap('A');self.check('A opens actual regional supplier',self.g('game_state')==11)
  supply_before=self.state();supply_hp=self.g('hero_hp_q4');self.tap('A');self.tap('A');self.check('regional tonic transaction settles',self.wait(lambda:self.g('game_state')!=12));supply_after=self.state()
  self.check('regional Heart Tonic costs18 and adds one supply',supply_after.economy.gold==supply_before.economy.gold-18 and supply_after.economy.supplies[0]==supply_before.economy.supplies[0]+1)
  self.check('buying a tonic preserves equipment and does not heal',bytes(supply_after.equipment)==bytes(supply_before.equipment) and self.g('hero_hp_q4')==supply_hp);self.shot(self.case+'-tonic-purchase')
  for _ in range(3+index):self.tap('DOWN')
  self.check('chapter stock contains newly added gear',self.g('game_shop_selection')==3+index);self.shot(self.case+'-price-effect')
  before=self.state();owned=bool(before.equipment.seen[ids[index]>>3]&(1<<(ids[index]&7)));hp=self.g('hero_hp_q4');slots=bytes(before.equipment.equipped)
  self.step(45,'A');self.check('held initial A only opens confirmation',self.g('game_shop_confirm')==1 and self.state().economy.gold==before.economy.gold);self.step(3);self.shot(self.case+'-confirmation')
  self.tap('A');self.check('purchase leaves busy state',self.wait(lambda:self.g('game_state')!=12));after=self.state();bought=not owned and before.economy.gold>=prices[index]
  if bought:
   self.check('gear costs exact inspected price',after.economy.gold==before.economy.gold-prices[index]);self.check('paid receipt and unique item appear together',bool(after.economy.reserved[0]&(1<<index)) and sum(r.item_id==ids[index] for r in after.equipment.bag)==1)
   self.check('gear purchase neither equips nor heals',bytes(after.equipment.equipped)==slots and self.g('hero_hp_q4')==hp);self.shot(self.case+'-purchase-saved')
   exported=self.saved(self.case+'-purchase');self.boot(exported);continued=self.state();self.check('cold Continue retains exact debit and unique gear',continued.economy.gold==after.economy.gold and bytes(continued.equipment)==bytes(after.equipment) and bytes(continued.economy)==bytes(after.economy));self.shot(self.case+'-continued')
   self.navigate(*approach,3);self.tap('A')
   for _ in range(3+index):self.tap('DOWN')
   self.tap('A');self.tap('A');self.check('owned gear refuses repeated spending after Continue',bytes(self.state().equipment)==bytes(continued.equipment) and bytes(self.state().economy)==bytes(continued.economy));self.shot(self.case+'-already-owned')
  else:
   self.check('owned or unaffordable gear preserves balance and ownership',bytes(before.equipment)==bytes(after.equipment) and bytes(before.economy)==bytes(after.economy));self.shot(self.case+('-already-owned' if owned else '-no-gold'))
  self.observations.append({'case':self.case,'gear_id':ids[index],'gear_price':prices[index],'source_already_seen':owned,'imported_gold':supply_before.economy.gold,'tonic_price':18,'before_gear_gold':before.economy.gold,'purchased':bought,'final_gold':after.economy.gold})
 def immutable(self):return {'save':self.e.bytes(self.sym['adventure_save'],C.sizeof(self.Save)),'sram':self.e.bytes(0x0e000000,32768),'requests':self.g('save_feedback_requests'),'starts':self.g('save_feedback_started')}
 def offer(self):
  self.navigate(120,110,4);self.tap('A');self.check('elder replay starts authored dialogue',self.g('game_state')==2)
  while self.g('game_state')==2 and self.g('dpage')<self.g('dcount')-1:self.tap('A')
  self.step(90,'A');self.check('held final A leaves homecoming offer unarmed',self.g('game_state')==5 and not self.g('ending_credits_phase') and not self.g('ending_credits_armed'));self.shot('homecoming-held-A');self.step(3);self.check('release arms homecoming choice',self.g('ending_credits_armed')==1)
 def credits(self):
  self.case='Q63-completed-homecoming';self.load_earned('covenants-homecoming-after-continue');self.check('completed Q63 retained',self.state().quests.states[15]>>6==3);self.drain();self.navigate(120,110,4);before=self.immutable();position=(self.g('room'),self.g('px'),self.g('py'),self.g('hero_hp_q4'))
  self.offer();self.step(240);self.check('idle homecoming does not auto-start credits',not self.g('ending_credits_phase'));self.shot('homecoming-choice');self.tap('B');self.check('B resumes exact field position and health',self.g('game_state')==1 and position==(self.g('room'),self.g('px'),self.g('py'),self.g('hero_hp_q4')));self.check('B choice changes no durable data or save counters',self.immutable()==before);self.shot('homecoming-B-explore')
  self.offer();self.tap('A');self.check('fresh A starts existing credits',self.g('ending_credits_phase')==1);self.shot('homecoming-credits-start')
  for target,label in ((440,'homecoming-credits-GBJ'),(700,'homecoming-credits-tools')):
   self.check('credits scroll reaches '+str(target),self.wait(lambda:self.g('ending_credits_scroll')>=target,3000));self.shot(label)
  self.check('full endroll reaches stable thanks',self.wait(lambda:self.g('ending_credits_phase')==2,1200));self.step(3);self.shot('homecoming-credits-thanks');self.tap('A');self.check('A replays endroll',self.g('ending_credits_phase')==1 and self.g('ending_credits_scroll')<4);self.shot('homecoming-credits-replay');self.step(3);self.tap('B');self.check('roll B resumes exact field position',self.g('game_state')==1 and position==(self.g('room'),self.g('px'),self.g('py'),self.g('hero_hp_q4')));self.check('offer roll replay and exit change no durable data',self.immutable()==before)
  exported=self.saved('homecoming-replay-complete');old=self.state();self.boot(exported);self.check('Continue retains final quest and optional invitations',bytes(self.state().quests)==bytes(old.quests) and bytes(self.state().equipment)==bytes(old.equipment) and bytes(self.state().roster)==bytes(old.roster));self.shot('homecoming-after-Continue')
 def run(self):
  names=('river-river-main-after-continue','north-north-main-after-continue','north-southern-ferry-spawn0-after-continue','magma-magma-main-after-continue','underwater-03-two-teaching-companions','return-room54-greenwake-first','horizons-01-horizons-intro','covenants-01-final-chapter-welcome')
  for i,name in enumerate(names):
   try:self.supplier(i,name)
   except Exception as ex:self.failures.append({'case':self.case,'exception':repr(ex),'status':self.status()});traceback.print_exc();self.shot(self.case+'-failure')
  try:self.credits()
  except Exception as ex:self.failures.append({'case':self.case,'exception':repr(ex),'status':self.status()});traceback.print_exc();self.shot('homecoming-failure')
 def finish(self):
  pacing_ok=not any(self.metrics[n] for n in ('active_update_misses','active_flip_misses','active_overruns','faults'))
  row={'case':'all','label':'measured active frames preserve update/presentation/cycle limits and no emulator faults','passed':pacing_ok,'metrics':self.metrics};self.checks.append(row)
  if not pacing_ok:self.failures.append(row)
  if self.e:self.e.close()
  self.frames.close();data={'scope':'Controller-only native diagnostics from this review\'s prior-ROM earned campaign SRAM; not fresh candidate acquisition','controller_only':True,'game_ram_writes':0,'machine_state_imports':0,'personal_save_access':False,'helper_sha256':sha(__file__),'candidate':self.candidate,'source_imports':self.sources,'checks':self.checks,'failures':self.failures,'captures':self.captures,'observations':self.observations,'inputs':self.inputs,'metrics':self.metrics}
  (self.out/'report.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({'output':str(self.out),'failures':self.failures,'observations':self.observations,'metrics':self.metrics},indent=2));return bool(self.failures)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('source-root','rom','symbols','bridge','producer-report','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--expected-rom-sha');a=p.parse_args();r=Diagnostics(a)
 try:r.run()
 finally:failed=r.finish()
 raise SystemExit(int(failed))
