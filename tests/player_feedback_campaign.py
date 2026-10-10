#!/usr/bin/env python3
"""Fresh controller-only feedback campaign plus earned evolution.

Only button input changes gameplay. Game-RAM write and machine-state APIs are
hard-disabled. Final Continue imports only this run's controller-earned SRAM.
Historical pre-recovery test outcomes are not reused by this reconstructed helper.
"""
from __future__ import annotations
import argparse,ctypes as C,gzip,hashlib,json,shutil,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
import campaign_tests
from campaign_tests import PLAY,DIALOG,PAUSE
from evolution_tests import EvolutionRun
from player_feedback_native import Native,sha
from mgba_runner import keymask
from test_save5 import Save
class ControllerNative(Native):
 def write(self,*a,**k):raise AssertionError('Controller journey forbids game-RAM writes')
 def state(self,*a,**k):raise AssertionError('Controller journey forbids machine states')
class FeedbackCampaign(EvolutionRun):
 def __init__(self,rom,symbols,output,bridge):
  self.bridge=Path(bridge).resolve();self.session=0;self.mode='boot';self.route_complete=False;self.receipts=[];self.checkpoints=[];self.powercuts=[];self.powercut_results=[];self.capture_cuts=False;self.handoff={}
  self.metrics={'measured_frames':0,'max_cycles':0,'update_misses':0,'flip_misses':0,'cycle_overruns':0,'faults':0,'deferred_publications':0,'publication_spills':0,'max_deferred_actor_cycles':0,'max_vblank_cycles':0,'latest_vblank_end':0};self.publication_serials=set()
  campaign_tests.Emulator=lambda candidate:ControllerNative(candidate,self.bridge)
  super().__init__(rom,symbols,output,optional=True,exhaustive=False)
  origin=self.bridge;self.bridge=self.out/'bridge.so';shutil.copyfile(origin,self.bridge);assert sha(origin)==sha(self.bridge)
  sources={};native_receipt_path=origin.parent/'bridge-build.json';native_receipt=json.loads(native_receipt_path.read_text()) if native_receipt_path.is_file() else None
  if native_receipt:assert native_receipt['bridge_sha256']==sha(origin)
  for rel in ('tests/player_feedback_mgba_bridge.c','tools/mgba_bridge.c'):
   target=self.out/'bridge-source'/rel;target.parent.mkdir(parents=True,exist_ok=True);source=origin.parent/'bridge-source'/rel if native_receipt else ROOT/rel;shutil.copyfile(source,target);sources[rel]=sha(target)
   if native_receipt:assert sources[rel]==native_receipt['sources'][rel]
  (self.out/'bridge-build-context.json').write_text(json.dumps({'bridge_origin':str(origin),'bridge_sha256':sha(self.bridge),'sources':sources,'binary_policy':'supplied native bridge copied byte-for-byte; exact retained build sources' if native_receipt else 'supplied native bridge copied byte-for-byte; source closure captured at run time','verified_native_build':native_receipt,'source_build_recipe':['cc','-std=c11','-D_GNU_SOURCE','-O2','-fPIC','-shared','tests/player_feedback_mgba_bridge.c','-Itools/sysroot/usr/include','-Ltools/sysroot/usr/lib/x86_64-linux-gnu','-Wl,-rpath,'+str((ROOT/'tools/sysroot/usr/lib/x86_64-linux-gnu').resolve()),'-o','bridge.so','-lmgba']},indent=2)+'\n')
  shutil.copyfile(self.source_rom.with_suffix('.elf'),self.out/'tested.elf');self.trace=gzip.open(self.out/'native-frames.jsonl.gz','wt')
  manifest=self.source_rom.parent/'source-hashes.json';assert manifest.is_file(),'Current production source receipt is required'
  runtime_sources=json.loads(manifest.read_text());assert all(sha(ROOT/name)==value for name,value in runtime_sources.items()),'Runtime sources differ from production build receipt'
  shutil.copyfile(manifest,self.out/'candidate-source-hashes.json')
  self.candidate.update(bridge_sha256=sha(self.bridge),helper_sha256=sha(__file__),elf_sha256=sha(self.out/'tested.elf'),source_manifest_sha256=sha(self.out/'candidate-source-hashes.json'))
  (self.out/'candidate.json').write_text(json.dumps(self.candidate,indent=2)+'\n')
  producer_sources={}
  for rel in ('tests/player_feedback_campaign.py','tests/campaign_tests.py','tests/evolution_tests.py','tests/region_journey.py','tests/player_feedback_native.py','tools/mgba_runner.py','tests/test_save5.py','tests/test_save4.py','tests/test_creatures.py'):
   target=self.out/'test-source'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target);producer_sources[rel]=sha(target)
  assert producer_sources['tests/player_feedback_campaign.py']==self.candidate['helper_sha256']
  (self.out/'producer-source-receipt.json').write_text(json.dumps({'candidate':self.candidate,'sources':producer_sources},indent=2)+'\n')
 def dialogs(self,reward=None):
  if 'opening_scene_begin' in self.sym and self.get('game_state')==14:
   # Successor-only opening; historical ROMs retain their original route.
   # Title activation remains the existing cold-new-game scope. Every page
   # after that is measured normally; dedicated opening QA also gates entry.
   self.mode='journey';before=self.e.bytes(0x0e000000,32768)
   self.check(self.e.read(self.sym['opening_page'],1)==0,'opening begins on first authored page')
   for page in range(8):
    self.check(self.get('game_state')==14 and self.e.read(self.sym['opening_page'],1)==page,'opening page '+str(page)+' reached through fresh A')
    self.step(24);self.check(self.e.bytes(0x0e000000,32768)==before,'opening does not touch SRAM before completion')
    self.tap('A',2,4)
   self.drain_background();self.check(self.get('game_state')==1 and self.get('room')==0,'opening reaches village and first checkpoint')
  return super().dialogs(reward)
 def raw_step(self,count,keys=0):
  mask=keymask(keys)&~4
  self.inputs.append({'session':self.session,'emulator_frame':self.e.frame,'frames':count,'keys':mask,'phase':self.mode})
  for _ in range(count):
   if self.capture_cuts and self.get('game_state')==8:self.capture_cut('animation-frame')
   room=self.get('room');before=self.get('frame');page=self.e.read(0x04000000,2)&16;self.e.frames(1,mask)
   now=self.get('frame');shown=self.e.read(0x04000000,2)&16
   row={'session':self.session,'hw':self.e.frame,'phase':self.mode,'delta':(now-before)&0xffffffff,'flip':shown!=page,'cycles':self.get('render_cycles'),'mode':self.get('game_state'),'room':self.get('room'),'x':self.get('px'),'y':self.get('py')}
   for metric in ('save_begin_cycles','save_begin_max_cycles','save_step_cycles','save_step_max_cycles','render_world_cycles','render_card_cycles','render_actors_cycles','scene_present_phase'):
    if metric in self.sym:row[metric]=self.get(metric)
   if 'render_profile_serial' in self.sym:
    serial=self.get('render_profile_serial')
    if not serial&1:
     profile={name:self.get('render_profile_'+name) for name in ('world','card','actors','save_begin','save_step','frame','state','room','update','save','render','music','deferred_actors','vblank_cycles','vblank_start','vblank_end','commit') if 'render_profile_'+name in self.sym}
     if self.get('render_profile_serial')==serial:row['completed_profile']={'serial':serial,**profile}
   self.trace.write(json.dumps(row,separators=(',',':'))+'\n')
   if self.mode=='journey':
    m=self.metrics;m['measured_frames']+=1;m['max_cycles']=max(m['max_cycles'],row['cycles']);m['update_misses']+=row['delta']!=1;m['flip_misses']+=not row['flip'];m['cycle_overruns']+=row['cycles']>=280896
    profile=row.get('completed_profile',{});serial=(self.session,profile.get('serial'))
    if profile.get('deferred_actors',0) and serial not in self.publication_serials:
     self.publication_serials.add(serial);m['deferred_publications']+=1;m['max_deferred_actor_cycles']=max(m['max_deferred_actor_cycles'],profile['deferred_actors']);m['max_vblank_cycles']=max(m['max_vblank_cycles'],profile['vblank_cycles']);m['latest_vblank_end']=max(m['latest_vblank_end'],profile['vblank_end']);m['publication_spills']+=not(160<=profile['vblank_start']<=profile['vblank_end']<228 and profile['vblank_cycles']<=83776)
   faults=self.e.lib.eb_faults(self.e.ptr);self.metrics['faults']=max(self.metrics['faults'],faults);assert not faults,('core fault',self.status());assert not self.get('save_failed'),('save failure',self.status())
   if room!=self.get('room'):self.edges.append([room,self.get('room')])
   if self.get('room') not in self.visits:self.visits.append(self.get('room'))
 def step(self,count,keys=0):
  if count:self.raw_step(count,keys)
  self.settle_save()
 def settle_save(self,intrusive=False):
  del intrusive
  for _ in range(1200):
   state=self.get('game_state')
   if state in (6,10,12):
    if self.capture_cuts and state==6:self.capture_cut('writer-frame')
    self.raw_step(1);continue
   if state==13:
    self.receipts.append({'frame':self.e.frame,'state':self.save_state().economy.boss_claims,'gold':self.save_state().economy.gold});self.shot('boss-treasure-'+str(len(self.receipts)));self.raw_step(3);self.raw_step(2,'A');self.raw_step(3);continue
   return
  raise AssertionError(('transaction did not settle',self.status()))
 def drain_background(self):
  self.settle_save()
  for _ in range(1500):
   if not self.get('save_feedback_background') and not self.get('save_requested'):return
   self.step(1)
  raise AssertionError('ordinary save did not settle')
 def save_state(self):return Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)))
 def snapshot(self,name):
  self.drain_background();path=self.out/(name+'.sav');method=self.e.save(path)
  self.snapshots[name]={'path':str(path),'sram_path':str(path),'sram_sha256':sha(path),'status':self.status(),'provenance':'current-ROM buttons only; ordinary SRAM export; no machine state','export_method':method};return path
 def restore(self,*a,**k):raise AssertionError('No machine-state restoration')
 def reload_case(self,name,expected_state=None):
  del expected_state
  self.snapshot(name);self.checkpoints.append({'name':name,'frame':self.e.frame})
 def reload_roster(self,name):self.reload_case(name)
 def menu_case(self,name):
  self.tap('START');self.check(self.get('game_state')==3 and self.get('journal_tab')==13,name+': Start opens hub')
  fixed={n:self.get(n) for n in ('px','py','hp','ability_cd','heal_cd','boss_hp','boss_armor')};self.step(20);self.check(all(self.get(n)==v for n,v in fixed.items()),name+': hub freezes gameplay')
  self.tap('RIGHT');self.tap('A');self.check(self.get('journal_tab')==4,name+': A enters Equipment');self.tap('B');self.check(self.get('journal_tab')==13,name+': B returns to hub');self.shot(name+'-hub');self.tap('START');self.check(self.get('game_state')==1,name+': Start closes hub')
 def hub(self,target):
  self.check(self.get('room')==0,'chapter travel starts in village');self.goto(y=128);key='RIGHT' if target==4 else 'LEFT'
  for _ in range(200):
   if self.get('room')==target:break
   self.step(1,key)
  self.check(self.get('room')==target,f'walk through chapter entrance {target} without A');self.step(24);self.dialogs()
 def walk_toward(self,x,y,dodge=False):
  del dodge
  return campaign_tests.CampaignRun.walk_toward(self,x,y,False)
 def cadence(self,name,frames=300,control=None):
  start=self.e.frame
  for offset in range(frames):self.step(1,control(offset) if control else 0)
  result={'scene':name,'hardware_frames':self.e.frame-start,'native_trace':'native-frames.jsonl.gz','branching':False};self.scenes.append(result);self.shot(name+'-cadence');return result
 def first_chapter(self):
  self.step(160);self.check(self.get('game_state')==0,'fresh cartridge boots to title');self.shot('01-title');self.tap('A',4,4);self.dialogs();self.mode='journey'
  self.check(self.get('game_state')==1 and self.get('room')==0,'A begins a genuine fresh adventure');self.check(self.get('chapter_flags')==self.get('room_flags')==0,'fresh adventure has no progression');self.menu_case('village');self.nextroom(1)
  self.goto(y=272);self.goto(x=120);self.goto(y=248);self.tap('A');self.dialogs();self.goto(y=272);self.goto(x=240);self.goto(y=180)
  self.select(1);self.ready();self.tap('R');self.dialogs();self.check(self.get('bridge_open')==1,'Midori earns grove bridge')
  self.goto(x=240);self.goto(y=92);self.goto(x=92);self.goto(y=72);self.tap('A');self.dialogs();self.check(self.get('max_hp')==8,'optional heart earned by interaction')
  self.goto(y=92);self.goto(x=368);self.nextroom(2);self.dialogs();self.select(0)
  for x,bit in ((64,1),(176,2)):
   self.goto(y=94);self.goto(x=x);self.goto(y=84);self.defend(300);self.goto(x=x,y=84);self.ready();self.tap('R');self.dialogs();self.check(self.get('torches')&bit,'authored brazier lit with Homura')
  self.goto(y=94);self.goto(x=120);self.nextroom(3);self.dialogs();self.snapshot('grove-boss-entry');self.goto(y=100);self.ready();self.tap('R');self.goto(y=96)
  for _ in range(6000):
   if self.get('game_state')==2:break
   if self.get('game_state')!=1:self.check(False,'grove boss route remains alive')
   if not self.get('boss_armor') and not self.get('ability_cd'):self.step(10,'RIGHT');self.tap('R')
   if self.get('boss_armor')>12 and not self.get('combo_timer') and not self.get('sword_cd'):self.goto(x=self.get('boss_x'),y=self.get('boss_y')+30);self.step(1,'UP');self.tap('A')
   else:self.step(1)
  self.check(self.get('boss_hp')==0 and self.flags(['GROVE_CLEAR']),'first boss and story reward earned');self.dialogs('grove-reward');self.check(self.get('room')==0,'first boss returns to village');self.select(2);self.reload_case('grove-complete')
 def growth(self,family):
  if self.get('game_state')==3:self.tap('START')
  self.select(family,summon=False);self.tap('START');self.tap('RIGHT');self.tap('DOWN');self.tap('A');self.check(self.get('game_state')==3 and self.get('journal_tab')==3,'A opens named Growth entry');self.check(self.get('spirit')==family,'Growth shows actual selected individual')
 def earned_fire_trial(self):
  self.nextroom(1)
  for i,(x,y) in enumerate(((184,280),(296,208),(320,72))):
   self.navigate(x,y,radius=16);self.select(0);self.ready();self.tap('R');self.dialogs();self.check(self.roster().lifetime_field_aid[0]&(1<<i),f'fire wish{i+1} earned at real object');self.snapshot('earned-fire-wish-'+str(i+1))
  self.check(self.instance(0).trial_flags&1,'three field objects earn fire trial');self.navigate(240,292);self.nextroom(0,'DOWN')
 def capture_cut(self,label):
  path=self.out/f'evolution-cut-{len(self.powercuts):03d}-{label}.sav';method=self.e.save(path)
  self.powercuts.append({'path':str(path),'sha256':sha(path),'label':label,'session':self.session,'hardware_frame':self.e.frame,'mode':self.get('game_state'),'export_method':method})
 def wait_evolution(self,target_state=7,require_ready=True,max_frames=180):
  pairing=self.evolution_observer();trace=[];previous=(self.get('frame'),self.e.read(0x04000000,2)&16)
  for _ in range(max_frames+1):
   state=self.get('game_state');phase=self.e.read(pairing['address']+8)
   if state==target_state and phase==0:break
   self.check(state==7 and 1<=phase<=6,'bounded evolution owns a known confirmation phase')
   if len(trace)==max_frames:raise AssertionError('evolution phase exceeded bounded observation')
   before_image=self.e.screenshot().tobytes();before_oam=self.e.bytes(0x07000000,1024)
   # The committed handoff must publish rather than honor a late cancel.
   action='A+B+START+LEFT' if phase==6 else 0
   self.raw_step(1,action);now=self.get('frame');page=self.e.read(0x04000000,2)&16;after_phase=self.e.read(pairing['address']+8)
   trace.append({'hardware_frame':self.e.frame,'update_delta':(now-previous[0])&0xffffffff,'page_flip':page!=previous[1],'cycles':self.get('render_cycles'),'phase':after_phase,'state':self.get('game_state'),'keys':keymask(action)})
   previous=(now,page)
   if after_phase==6:
    after_image=self.e.screenshot().tobytes();after_oam=self.e.bytes(0x07000000,1024);self.check(before_image==after_image,'commit frame preserves the exact prior displayed image');self.check(before_oam==after_oam,'commit frame preserves all1024 hardware OAM bytes')
    self.check(self.get('game_state')==7 and self.instance(0).form_id==2 and self.e.read(pairing['address'])!=0,'committed individual retains the immutable lease until publication')
    self.handoff={'hardware_frame':self.e.frame,'frozen_rgb_sha256':hashlib.sha256(after_image).hexdigest(),'frozen_oam_sha256':hashlib.sha256(after_oam).hexdigest(),'instance_id':self.instance(0).instance_id,'form':self.instance(0).form_id,'save_token':self.e.read(pairing['address'])}
    if self.capture_cuts:self.capture_cut('committed-before-publication')
   if phase==6:
    self.check(self.get('game_state')==8 and self.instance(0).form_id==2,'postcommit A/B/Start/direction chord is consumed and publishes once')
    if self.capture_cuts:self.capture_cut('published-before-animation-save')
  if not hasattr(self,'evolution_waits'):self.evolution_waits=[]
  self.evolution_waits.append({'target_state':target_state,'trace':trace})
  (self.out/'evolution-waits.json').write_text(json.dumps({'pairing':pairing,'known_phases':list(range(7)),'controller_only':True,'game_ram_writes':0,'waits':self.evolution_waits},indent=2)+'\n')
  self.check(all(r['update_delta']==1 and r['page_flip'] and r['cycles']<280896 for r in trace),'bounded evolution updates and presents every native frame')
  self.check(self.get('game_state')==target_state and self.e.read(pairing['address']+8)==0,'evolution reaches the requested published/ready state')
  if require_ready and target_state==7:self.check(self.get('progression_evolution_reason')==0,'prepared evolution is genuinely eligible')
 def verify_powercuts(self):
  recovered=[]
  for record in self.powercuts:
   e=ControllerNative(self.rom,self.bridge);inputs=[]
   def g(n):return e.read(self.sym[n])
   def step(n=1,k=0):inputs.append({'frames':n,'keys':keymask(k)});e.frames(n,k)
   try:
    e.load_save(record['path']);e.reset();step(160);self.check(g('game_state')==0 and g('has_save')==1,'power-cut SRAM has a complete loadable record')
    step(2,'A');step(3)
    for _ in range(1600):
     if g('game_state')==1 and g('frame'):break
     if g('game_state')==2:step(2,'A');step(3)
     else:step()
    else:raise AssertionError('power-cut cold Continue did not reach play')
    state=Save.from_buffer_copy(e.bytes(self.sym['adventure_save'],C.sizeof(Save)));recovered.append(bytes(state))
    self.check(not g('save_failed') and e.lib.eb_faults(e.ptr)==0,'power-cut cold Continue has no save/core fault')
    self.check(sha(record['path'])==record['sha256'],'power-cut input SRAM remains byte-identical')
    self.powercut_results.append({'source':record,'cold_inputs':inputs,'state_sha256':hashlib.sha256(bytes(state)).hexdigest(),'occupied':sum(bool(c.flags&1) for c in state.roster.instances),'target_form':next(c.form_id for c in state.roster.instances if c.flags&1 and c.instance_id==self.handoff['instance_id'])})
   finally:e.close()
  self.check(bool(recovered) and recovered[0]!=recovered[-1],'power-cut oracle has distinct complete old and new records')
  self.check(self.powercut_results[0]['target_form']==1 and self.powercut_results[-1]['target_form']==2,'power-cut endpoints preserve original and committed evolution respectively')
  self.check(all(value in (recovered[0],recovered[-1]) for value in recovered),'every native writer boundary recovers the complete old or new Save5 state')
  self.check(len({r['occupied'] for r in self.powercut_results})==1,'no power-cut boundary duplicates or drops an owned individual')
  (self.out/'evolution-power-cuts.json').write_text(json.dumps({'scope':'controller-earned SRAM cuts at native observed writer-frame boundaries, not every byte write','controller_only':True,'game_ram_writes':0,'machine_state_imports':0,'cuts':self.powercut_results},indent=2)+'\n')
 def earned_evolution(self):
  self.growth(0);self.tap('DOWN');before=bytes(self.instance(0));identity=self.instance(0).instance_id;self.tap('A');self.check(self.get('game_state')==7,'visible A evolution opens confirm');self.wait_evolution();self.shot('earned-evolution-confirmation');self.tap('B');self.check(self.get('game_state')==3 and bytes(self.instance(0))==before,'B declines without changing individual')
  self.tap('A');self.wait_evolution();self.capture_cut('before-confirm');self.capture_cuts=True;self.tap('A');self.wait_evolution(8)
  for _ in range(400):
   if self.get('game_state')!=8:break
   self.step(1)
  self.settle_save();self.capture_cuts=False;self.capture_cut('verified-after-animation');self.check(self.get('game_state')==3 and self.instance(0).form_id==2,'fresh A completes earned Homura evolution');self.check(self.instance(0).instance_id==identity,'evolution keeps same individual');self.shot('earned-evolution-complete');self.check(self.get('progression_menu_row')==0,'animation returns to command row');self.tap('RIGHT');self.check(self.instance(0).equipped[self.instance(0).selected_command]==1,'learned command remains preview before A');self.tap('A');self.check(self.get('progression_menu_detail')==1 and self.instance(0).equipped[self.instance(0).selected_command]==1,'first A inspects learned command without equipping');self.tap('A');self.check(self.instance(0).equipped[self.instance(0).selected_command]==5,'second A selects learned command');self.tap('LEFT');self.tap('A');self.check(self.get('progression_menu_detail')==1 and self.instance(0).equipped[self.instance(0).selected_command]==5,'first A previews original power without equipping');self.tap('A');self.check(self.instance(0).equipped[self.instance(0).selected_command]==1,'second A reselects original power');self.tap('START');self.snapshot('earned-evolution-village')
 def cold_verify(self):
  self.drain_background();before=self.save_state();path=self.snapshot('controller-complete');self.e.close();self.session+=1;self.e=ControllerNative(self.rom,self.bridge);self.e.load_save(path);self.e.reset();self.mode='cold_continue';self.step(160);self.tap('A',4,4)
  for _ in range(1200):
   if self.get('game_state')==1 and self.get('frame'):break
   self.step(1)
  self.dialogs();self.drain_background();after=self.save_state();self.check((self.get('chapter_flags')&7)==7,'cold Continue retains all3 bosses');self.check(bytes(after.roster)==bytes(before.roster),'cold Continue preserves complete roster');self.check(bytes(after.economy)==bytes(before.economy),'cold Continue preserves money and treasures');self.shot('controller-complete-cold-continue');self.snapshot('controller-complete-cold');self.mode='journey'
 def run(self):
  self.first_chapter();self.chapter_two();self.chapter_three();self.earned_fire_trial();self.earned_evolution();self.check(self.save_state().economy.boss_claims==7,'three unique earned boss treasures owned once');self.cold_verify();self.verify_powercuts()
  if 'render_profile_deferred_actors' in self.sym:
   self.check(self.metrics['deferred_publications']>0,'actual scene OBJ publications were observed');self.check(not self.metrics['publication_spills'],'all deferred actor uploads and publication remain wholly within VBlank')
  self.route_complete=True;self.report()
 def report(self):
  if not hasattr(self,'e') or not self.e.ptr:return
  data={'suite':'player-feedback-fresh-campaign-and-earned-evolution','controller_only':True,'game_ram_writes':0,'machine_state_imports':0,'synthetic_progression':False,'candidate':getattr(self,'candidate',{}),'route_complete':self.route_complete,'passes':self.passes,'failures':self.failures,'final':self.status(),'visited_rooms':self.visits,'edges':self.edges,'checkpoints':self.snapshots,'boss_receipts':self.receipts,'evolution_handoff':self.handoff,'power_cut_boundaries':len(self.powercut_results),'native_observation':self.metrics,'native_cadence_passed':not any(self.metrics[k] for k in ('update_misses','flip_misses','cycle_overruns','faults','publication_spills')),'timing_scope':'journey only; boot and cold Continue labeled separately','native_frame_trace':'native-frames.jsonl.gz','emulator_frame':self.e.frame}
  with gzip.open(self.out/'controller-inputs.json.gz','wt') as f:json.dump(self.inputs,f)
  data['input_trace_sha256']=sha(self.out/'controller-inputs.json.gz')
  (self.out/'player-feedback-campaign.json').write_text(json.dumps(data,indent=2)+'\n')
  if hasattr(self,'trace'):self.trace.flush()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists() and any(a.output.iterdir()):p.error('output must be new or empty; preserve earlier evidence')
 r=FeedbackCampaign(a.rom,a.symbols,a.output,a.bridge)
 try:r.run()
 except Exception as e:r.failures.append({'error':repr(e),'status':r.status()});r.shot('failure');r.report();traceback.print_exc();return 1
 finally:r.report();r.trace.close();r.e.close()
 return int(not r.route_complete or bool(r.failures) or any(r.metrics[k] for k in ('update_misses','flip_misses','cycle_overruns','faults','publication_spills')))
if __name__=='__main__':raise SystemExit(main())
