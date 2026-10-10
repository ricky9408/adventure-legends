#!/usr/bin/env python3
"""Full-engine Return feasibility with EXPLICIT synthetic RAM fixture setup.

Not a controller-earned route, save/acquisition acceptance, or final cadence gate.
After each setup, the actual engine generates ranger shots and interprets R.
No executable bytes or power-private state are patched. Every setup write is
recorded. Do not combine this report with player-facing release acceptance.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,struct,sys,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
from test_save5 import Save
from test_creatures import Roster,Instance
SHA=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
FORMS=(3,6,9,12,15,17,18,21,24,27,30,101,102,103,104)
MASKS=(1025,1026,1028,1032,1040,1024,3072,1056,1088,1025,1025,0,1024,0,1024)
class Probe:
 def __init__(self,args):
  self.a=args;self.out=args.output;self.out.mkdir(parents=True,exist_ok=True)
  assert SHA(args.rom)==args.rom_sha and SHA(args.symbols)==args.symbols_sha
  for src,name in [(args.rom,'tested.gba'),(args.symbols,'tested.sym')]:shutil.copyfile(src,self.out/name)
  args.rom=self.out/'tested.gba';args.symbols=self.out/'tested.sym'
  assert SHA(args.rom)==args.rom_sha and SHA(args.symbols)==args.symbols_sha
  self.sym={}
  for line in args.symbols.read_text().splitlines():
   p=line.split()
   if len(p)==3:self.sym[p[2]]=int(p[0],16)
  self.writes=[];self.rows=[];self.failures=[]
 def put(self,name,value,width=4,offset=0):
  address=self.sym[name]+offset;self.e.write(address,value&((1<<(width*8))-1),width);self.writes.append({'symbol':name,'offset':offset,'width':width,'value':value})
 def get(self,name):return self.e.read(self.sym[name])
 def setup(self,c,enemy=True,side=False):
  self.e=Emulator(self.a.rom);self.e.load_save(self.a.fixture);self.e.reset();self.e.frames(150);self.e.tap('START',2,100)
  # Synthetic isolated old-room workspace avoids invoking new world proof.
  for name,value in dict(game_state=1,room=0,px=120,py=126,px_q8=120*256,py_q8=126*256,cx=134,cy=126,cx_q8=134*256,cy_q8=126*256,face=1,summoned=1,ability_cd=0,hitstop=0,transition=0,transition_lock=0,area_ticks=0,invuln=1000,walk=0,frame=0).items():self.put(name,value)
  base=self.sym['adventure_save']+Save.roster.offset
  party=self.e.read(base+Roster.selected_party.offset,1);slot=self.e.read(base+Roster.party.offset+party,1)
  assert party<4 and slot<160
  addr=base+Roster.instances.offset+slot*C.sizeof(Instance)
  current=Instance.from_buffer_copy(self.e.bytes(addr,C.sizeof(Instance)))
  form=FORMS[c-91];row=self.e.read(self.sym['creature_form_index']+form,1)-1;assert 0<=row<104;f=self.sym['creature_forms']+row*32;assert self.e.read(f,1)==form;current.form_id=form;current.flags|=1;current.level=40;current.bond=80;current.xp=0;current.trial_flags=MASKS[c-91];current.equipped[0]=c;current.equipped[1]=0;current.selected_command=0;current.polarity=self.e.read(f+3,1)
  # XP threshold is observed from compiled ROM table via level formula in
  # current catalog code, rather than weakening instance validation.
  # Exact current threshold: four times (level-1) cubed.
  current.xp=4*39**3
  for i,b in enumerate(bytes(current)):self.put('adventure_save',b,1,Save.roster.offset+Roster.instances.offset+slot*C.sizeof(Instance)+i)
  for name,size in [('enemies',120),('shots',288),('ordinary_hostile_shots',12),('enemy_clocks',24),('enemy_windups',24),('enemy_aimx',24),('enemy_aimy',24),('enemy_stagger_ticks',6),('rooted_enemies',24)]:
   for i in range(size):self.put(name,0,1,i)
  # Permit both native bitmap pages and the synthetic selected form to repaint
  # coherently before introducing an enemy or pressing the genuine R input.
  self.e.frames(12)
  if enemy:
   # Real kind2 ranger starts a genuine existing windup and subsequently calls
   # fire_shot / ordinary provenance / spawn callback in normal engine code.
   x,y=(112,106) if side else (120,90)
   for j,v in enumerate((x,y,100,0,2)):self.put('enemies',v,4,j*4)
   self.put('enemy_hp_q4',1600);self.put('enemy_phases',255,1);self.put('enemy_windups',24 if side else 12);self.put('enemy_clocks',100)
   self.put('enemy_aimx',-2 if side else 0);self.put('enemy_aimy',0 if side else 2)
  self.e.frames(1)
 def state(self):
  return {'hardware_frame':self.e.frame,'update_counter':self.get('frame'),'display_page':int(bool(self.e.read(0x04000000,2)&16)),'render_cycles':self.get('render_cycles'),'kind':self.get('return_power_kind'),'age':self.get('return_power_age'),'time':self.get('return_power_time'),'cooldown':self.get('ability_cd'),'hint_unobserved':True,'hp_q4':self.e.read(self.sym['enemy_hp_q4']),'windup':self.e.read(self.sym['enemy_windups']),'shots':[list(struct.unpack('<6i',self.e.bytes(self.sym['shots']+i*24,24)))+[self.e.read(self.sym['ordinary_hostile_shots']+i,1)] for i in range(12)]}
 def case(self,c,side=False,release=False):
  self.setup(c,True,side);before=self.state();trace=[before];self.e.frames(1,'R');trace.append(self.state());self.e.frames(1);trace.append(self.state())
  assert trace[-1]['kind']==c and trace[-1]['time']>0,('native cast rejected',c,trace[-1])
  saw_shot=False;ended=None;cd_at_release=None
  for n in range(80):
   state=self.state();live=[r for r in state['shots'] if r[4]>0 and r[5] and r[6]]
   saw_shot|=bool(live)
   if release and n==22:
    cd_at_release=state['cooldown'];self.e.frames(1,'R')
   else:self.e.frames(1)
   trace.append(self.state())
   if not trace[-1]['time'] and ended is None:ended=n
  after=self.state()
  # Shot interception must happen well before it could reach the player at126.
  # The module is not given a projectile by the test; native ranger created it.
  disappearance=[(a['age'],b['age']) for a,b in zip(trace,trace[1:]) if any(r[4]>0 and r[5] and r[6] for r in a['shots']) and not any(r[4]>0 and r[5] and r[6] for r in b['shots'])]
  if not side:
   assert saw_shot and disappearance,('native ordinary shot not created/removed',c)
   assert any(any(r[4]>0 and r[5] and r[6] and r[1]<=110 for r in a['shots']) and not any(r[4]>0 and r[5] and r[6] for r in b['shots']) for a,b in zip(trace,trace[1:])),('shot survived until hero or expired elsewhere',c)
   if c in (94,96):assert after['hp_q4']<before['hp_q4'],('counter never reached ordinary ranger',c)
  else:assert after['hp_q4']<before['hp_q4'] and any(r['windup']==0 and r['age']<=12 for r in trace),('quiet-cut did not cancel native windup',trace)
  assert ended is not None and after['cooldown']>0
  cadence=[{'hardware':b['hardware_frame']-a['hardware_frame'],'updates':b['update_counter']-a['update_counter'],'page_changed':a['display_page']!=b['display_page']} for a,b in zip(trace,trace[1:])]
  profile=[[self.e.read(self.sym['return_power_profile']+(i*3+j)*4) for j in range(3)] for i in range(7)] if 'return_power_profile' in self.sym else None
  row={'sampled_cadence_passed':all(x['updates']==x['hardware'] and x['page_changed']==bool(x['hardware']&1) for x in cadence),'module_profile':profile,'frame_samples':cadence,'max_sampled_render_cycles':max(r['render_cycles'] for r in trace),'command':c,'synthetic_fixture':True,'ordinary_projectile_generated_by_engine':saw_shot,'disappearance_age_pairs':disappearance,'fresh_R_release':release,'cooldown_before_release':cd_at_release,'before':before,'after':after,'trace':trace}
  self.e.screenshot(self.out/f'command-{c}.png');self.rows.append(row);self.e.close();self.report()
 def cast_case(self,c):
  targets={91:(30,0,2),93:(10,0,2),95:(20,0,0),97:(20,12,2),98:(33,0,0),99:(10,0,2),100:(12,0,2),101:(20,-12,2),104:(16,0,0),105:(34,0,2)}
  self.setup(c,False);f,side,kind=targets[c]
  for j,v in enumerate((120+side,126-f,100,0,kind)):self.put('enemies',v,4,j*4)
  self.put('enemy_hp_q4',1600);self.put('enemy_phases',255,1);self.put('enemy_clocks',100)
  before=self.state();trace=[before];self.e.frames(1,'R');trace.append(self.state());self.e.frames(1);trace.append(self.state())
  assert trace[-1]['kind']==c and trace[-1]['time']>0,('native cast rejected',c,trace[-1])
  for n in range(85):
   age=trace[-1]['age']
   if c==91 and n==22 or c==99 and n==16:self.e.frames(1,'R')
   else:self.e.frames(1,'UP' if c==98 and n<48 else 0)
   trace.append(self.state())
   if n==12:self.e.screenshot(self.out/f'command-{c}-active.png')
  after=self.state();assert after['hp_q4']<before['hp_q4'],('native authored hit not feasible',c,[(r['age'],r['hp_q4']) for r in trace])
  cadence=[{'hardware':b['hardware_frame']-a['hardware_frame'],'updates':b['update_counter']-a['update_counter'],'page_changed':a['display_page']!=b['display_page']} for a,b in zip(trace,trace[1:])]
  self.rows.append({'command':c,'synthetic_fixture':True,'actual_ordinary_movement':kind==0,'controller_lure':c==98,'before':before,'after':after,'trace':trace,'frame_samples':cadence,'sampled_cadence_passed':all(x['updates']==x['hardware'] and x['page_changed']==bool(x['hardware']&1) for x in cadence),'max_sampled_render_cycles':max(r['render_cycles'] for r in trace)})
  self.e.close();self.report()
 def modal_case(self):
  self.setup(91,False);trace=[];self.e.frames(1,'R');self.e.frames(12)
  assert self.get('return_power_time')>0
  # Genuine native pause and quick-party selector inputs, no power-state writes.
  self.e.frames(1,'START');self.e.frames(3);paused=(self.get('return_power_age'),self.get('ability_cd'));self.e.frames(12)
  assert (self.get('return_power_age'),self.get('ability_cd'))==paused
  self.e.frames(1,'START');self.e.frames(2);resumed=self.get('return_power_age');assert resumed>paused[0]
  self.e.frames(1,'L');picked=(self.get('return_power_age'),self.get('ability_cd'));self.e.frames(12,'L')
  assert (self.get('return_power_age'),self.get('ability_cd'))==picked
  self.e.frames(1,0);self.e.frames(3);assert self.get('return_power_age')>=picked[0]
  self.rows.append({'case':'native-pause-picker-freeze','synthetic_fixture':True,'native_inputs_only_after_setup':True,'paused_age_cooldown':paused,'picker_age_cooldown':picked,'passed':True})
  self.e.close();self.report()
 def report(self):
  data={'suite':'return-native-engine-synthetic-fixture-feasibility','controller_only':False,'excluded_from_release_acquisition_acceptance':True,'game_ram_setup_writes':self.writes,'code_or_private_power_state_writes':0,'ROM_sha256':self.a.rom_sha,'symbols_sha256':self.a.symbols_sha,'fixture_sha256':SHA(self.a.fixture),'test_sha256':SHA(__file__),'cases':self.rows,'failures':self.failures,'limits':['Synthetic setup; no earned acquisition','No physical GBA','No claim of exact final release','Additional controller-earned guard side/boss/occlusion and all-power cadence gates required']}
  (self.out/'engine-feasibility.json').write_text(json.dumps(data,indent=2)+'\n')
 def run(self):
  try:
   for c in (92,94,96,103):self.case(c,release=c==96)
   self.case(102,side=True)
   if self.a.all_commands:
    for c in (91,93,95,97,98,99,100,101,104,105):self.cast_case(c)
    self.modal_case()
  except Exception as exc:self.failures.append(repr(exc));self.report();raise
  self.report()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True);p.add_argument('--rom-sha',required=True);p.add_argument('--symbols-sha',required=True);p.add_argument('--fixture',type=Path,default=ROOT/'tests/fixtures/v5-revision6/underwater-all89-town.sav');p.add_argument('--output',type=Path,required=True);p.add_argument('--all-commands',action='store_true');a=p.parse_args();Probe(a).run()
if __name__=='__main__':main()
