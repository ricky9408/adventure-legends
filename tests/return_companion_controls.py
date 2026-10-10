#!/usr/bin/env python3
"""Earned-SRAM, controller-only companion art/control/combat observations.

No machine-state import, writes, save editing, recompilation, or synthetic enemy
setup. This is supplemental to the independently authenticated acquisition run.
Every post-loader hardware frame is sampled, including menus and navigation.
Failures remain failures even while independent diagnostic cases continue.
"""
from __future__ import annotations
import argparse, ctypes as C, gzip, hashlib, json, struct, traceback
from pathlib import Path
from PIL import Image, ImageDraw
from return_journey import ReturnJourney, ReadOnlyGameEmulator, ROOT, digest, PLAY, PAUSE, DEAD
from region_journey import RegionJourney
from northern_journey import newest_bank
from test_save5 import Save, Roster, Instance

FORMS=(3,6,9,12,15,17,18,21,24,27,30,101,102,103,104)
KEYS=('DOWN','UP','LEFT','RIGHT')
BODY=0x06014000+6400
SHADOW=0x06014000+6656
sha=lambda b:hashlib.sha256(b).hexdigest()
class Mark(C.Structure):
 _fields_=[('x',C.c_short),('y',C.c_short),('flags',C.c_ubyte),('pad',C.c_ubyte)]
class Point(C.Structure):
 _fields_=[('x',C.c_short),('y',C.c_short)]
class Cast(C.Structure):
 _fields_=[('marks',Mark*24),('previous',Point*6)]+[(n,C.c_uint) for n in ('caster','lease','token')]+[('serial',C.c_ushort*6),('bound_serial',C.c_ushort*6),('shot_serial',C.c_ushort*12),('caught_shot_serial',C.c_ushort)]+[(n,C.c_short)for n in ('drop_x','drop_y','last_x','last_y','field_x','field_y')]+[(n,C.c_ubyte)for n in ('field_valid','field_radius','field_result','build_live','count','hits','fields','revoked','aimed','dirty','art_live','spent','released','release_age','charged','guard_used','stopped','carry_steps','caught_shot','geometry_age','moving','quiet_used')]+[('side',C.c_byte)]

def tile_bytes(p,w=16,h=16):
 return bytes(p[(ty+y)*w+tx+x]for ty in range(0,h,8)for tx in range(0,w,8)for y in range(8)for x in range(8))

class EarnedEmulator(ReadOnlyGameEmulator):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw);self.lib.eb_state=self.state
 def state(self,*a,**kw):raise AssertionError('Machine-state import/export is forbidden in this SRAM-only suite')

class CompanionControls(ReturnJourney):
 def __init__(self,*a,**kw):
  self.sequence=0;self.stage='initializing';self.gate=False;self.capture_art=False;self.native=[];self.loaded=[];self.summary={'sampled_frames':0,'strict_frames':0,'max_cycles':0,'max_obj':0,'exceptions':[]};self.art_cases=[];self.combat_cases=[];self.control_cases=[];self.native_file=None;self.producer=None;self.prefix=None;self.summary.update(loader_frames=0,cold_prefixes=[])
  super().__init__(*a,**kw)
  self.native_file=gzip.open(self.out/'native-frames.jsonl.gz','wt',encoding='utf-8')
  address,size=self.locals['return_powers.c:cast'];assert size==C.sizeof(Cast),(size,C.sizeof(Cast));self.cast_address=address
  self.rom_bytes=self.rom.read_bytes();self.walk_index={};self.cast_index={}
  for i,f in enumerate(FORMS):
   for d in range(4):
    for n in range(4):
     b=self.rom_read('return_creature_direction_frames',((i*4+d)*4+n)*256,256);self.walk_index[sha(tile_bytes(b))]=(f,d,n)
    for n in range(3):
     b=self.rom_read('return_creature_ability_frames',((i*4+d)*3+n)*256,256);self.cast_index[sha(tile_bytes(b))]=(f,d,n)
  self.report()
 def rom_read(self,name,off,n):
  at=self.sym[name]-0x08000000+off;return self.rom_bytes[at:at+n]
 def selected(self):
  base=self.sym['adventure_save']+Save.roster.offset
  party=self.e.read(base+Roster.selected_party.offset,1);slot=self.e.read(base+Roster.party.offset+party,1)
  assert party<4 and slot<160
  return Instance.from_buffer_copy(self.e.bytes(base+Roster.instances.offset+slot*C.sizeof(Instance),C.sizeof(Instance)))
 def cast(self):return Cast.from_buffer_copy(self.e.bytes(self.cast_address,C.sizeof(Cast)))
 def report(self):
  if not hasattr(self,'candidate'):return
  d={'suite':'earned-return-companion-native-controls','controller_only':True,'game_ram_writes':0,'machine_state_loads':0,'physical_hardware_tested':False,'release_acceptance':False,'source_producer':self.producer,'cold_sram_sources':self.loaded,**self.candidate,'source_root':str(self.source_root),'source_manifest_sha256':self.source_manifest_sha,'helper_sources':getattr(self,'test_sources',{}),'cadence':self.summary,'art_cases':self.art_cases,'combat_cases':self.combat_cases,'control_cases':self.control_cases,'checks':self.checks,'failures':self.failures,'stage':self.stage,'native_frame_capture':'native-frames.jsonl.gz','inputs':self.inputs,'scope_limits':['Supplemental cold-SRAM branches, not an acquisition producer','No physical GBA','Bosses already defeated in earned roster: active-boss exclusion needs separately labeled synthetic test','Per-frame measurements retain failures without relaxing update/flip/cycle/OBJ limits']}
  (self.out/'companion-controls.json').write_text(json.dumps(d,indent=2)+'\n')
 def restore(self,*a,**kw):raise AssertionError('Machine-state import is forbidden in earned companion QA')
 def observation(self):
  c=self.cast();return {'form':self.selected().form_id,'identity':self.selected().instance_id,'command':self.command(),'room':self.get('room'),'hero':[self.get('px'),self.get('py')],'companion':[self.get('cx'),self.get('cy')],'summoned':self.get('summoned'),'kind':self.get('return_power_kind'),'age':self.get('return_power_age'),'time':self.get('return_power_time'),'cooldown':self.get('ability_cd'),'hitstop':self.get('hitstop'),'state':self.get('game_state'),'released':c.released,'release_age':c.release_age,'charged':c.charged,'guard_used':c.guard_used,'revoked':c.revoked,'hits':c.hits,'carry_steps':c.carry_steps,'drop':[c.drop_x,c.drop_y],'origin':[self.get('return_power_origin_x'),self.get('return_power_origin_y')],'quiet_used':c.quiet_used,'side':c.side,'marks':[[m.x,m.y,m.flags]for m in c.marks[:c.count]],'enemies':self.enemies(),'windups':[self.e.read(self.sym['enemy_windups']+i*4)for i in range(6)],'shots':[dict(s,ordinary=self.e.read(self.sym['ordinary_hostile_shots']+i,1))for i,s in enumerate(self.shots())],'weapon':self.action(),'arrows':self.arrows()}
 def step(self,n,keys=0):
  if not self.native_file:return RegionJourney.step(self,n,keys)
  self.inputs.append({'sequence':self.sequence,'frame':self.e.frame,'frames':n,'keys':keys,'stage':self.stage})
  for _ in range(n):
   old=self.get('frame');display_before=self.e.read(0x04000000,2);page=display_before&16;state=self.get('game_state');room=self.get('room')
   self.e.frames(1,keys);new=self.get('frame');self.sequence+=1
   display_after=self.e.read(0x04000000,2);exempt=False
   if self.prefix is not None:
    prefix=self.prefix;prefix['hardware_frames']+=1
    assert prefix['hardware_frames']<=160,'Cold loader prefix exceeded160 hardware frames'
    blank=prefix['kind']=='startup'and(display_before&128 or display_after&128 or self.get('render_cycles')==0)
    if new<old or new==0 or blank:
     prefix['started']=True;prefix['excluded_frames']+=1;exempt=True
    elif prefix['started']:prefix['done']=True;self.prefix=None
   self.gate=not exempt
   row={'sequence':self.sequence,'hardware_frame':self.e.frame,'stage':self.stage,'keys':keys,'before':old,'after':new,'updates':(new-old)&0xffffffff,'flip':bool((self.e.read(0x04000000,2)&16)!=page),'cycles':self.get('render_cycles'),'obj':self.get('obj_count'),'state_before':state,'state':self.get('game_state'),'room':self.get('room'),'strict':self.gate,'cold_loader_exempt':exempt,'display_before':display_before,'display_after':display_after}
   if room!=row['room']:self.transitions.append({'frame':self.e.frame,'from':room,'to':row['room'],'keys':keys})
   self.summary['sampled_frames']+=1
   if exempt:self.summary['loader_frames']+=1
   if self.gate:
    self.summary['strict_frames']+=1;self.summary['max_cycles']=max(self.summary['max_cycles'],row['cycles']);self.summary['max_obj']=max(self.summary['max_obj'],row['obj'])
    if row['updates']!=1 or not row['flip'] or row['cycles']>=280896 or row['obj']>128:self.summary['exceptions'].append(row.copy())
   if self.capture_art:
    raw=self.e.bytes(BODY,256);shadow=self.e.bytes(SHADOW,256);h=sha(raw);row.update(self.observation());row.update(body_vram=raw.hex(),shadow_vram=shadow.hex(),oam=self.oam(),body_walk=self.walk_index.get(h),body_cast=self.cast_index.get(h),body_sha256=h,display_page=(self.e.read(0x04000000,2)>>4)&1)
    self.native.append(row)
   self.native_file.write(json.dumps(row,separators=(',',':'))+'\n')
 def attach_producer(self,path,expected):
  assert digest(path)==expected
  p=json.loads(Path(path).read_text());assert p['controller_only'] and p['game_ram_writes']==0 and p['machine_state_loads']==0
  assert p['finished_scope']=='full' and not p['failures'];assert all(c['passed']for c in p['checks'])
  for k in ('rom_sha256','symbols_sha256','elf_sha256'):assert p[k]==self.candidate[k]
  assert p['source_manifest_sha256']==self.source_manifest_sha
  self.producer={'path':str(Path(path).resolve()),'sha256':expected,'source_helper_manifest_sha256':digest(Path(path).parent/'helper-source-hashes.json')};self.producer_data=p
  self.final_key=next(k for k in reversed(p['snapshots'])if k.startswith('05-all104-cold-reboot') and k.endswith('after'))
  s=p['snapshots'][self.final_key];assert len(s['obtained_form_ids'])==104 and len(s['individuals'])==52
  self.report()
 def begin_prefix(self,kind):
  self.prefix={'kind':kind,'source':self.stage,'sequence_start':self.sequence,'hardware_frames':0,'excluded_frames':0,'started':kind=='startup','done':False}
  self.summary['cold_prefixes'].append(self.prefix)
 def cold(self,key):
  s=self.producer_data['snapshots'][key];p=Path(s['sram_path']);assert digest(p)==s['sram_sha256'];b=newest_bank(p.read_bytes());assert int.from_bytes(b[12:14],'little')==7
  self.capture_art=False;self.gate=False;self.stage='cold-'+key;self.e.close();self.e=EarnedEmulator(self.rom);self.e.load_save(p);self.e.reset();self.begin_prefix('startup');self.step(150);self.begin_prefix('continue');self.step(1,'START')
  for _ in range(160):
   self.step(1)
   if self.get('frame')>0 and self.get('game_state')==PLAY:break
  else:raise AssertionError('Cold Continue failed')
  self.gate=True;self.step(5);self.settle();self.loaded.append({'snapshot':key,'path':str(p),'sha256':s['sram_sha256'],'history':len(self.collection()),'individuals':len(self.live()),'sram_only':True})
  self.check(newest_bank(self.e.bytes(0x0e000000,32768))[32:]==b[32:],'cold SRAM payload preserved before new inputs')
  self.report()
 def soft(self,ok,label,detail=None):
  self.checks.append({'passed':bool(ok),'label':label,'sequence':self.sequence})
  if not ok:self.failures.append({'case':self.stage,'label':label,'detail':detail});self.report()
 def observe(self,n,keys=0):
  start=len(self.native);self.capture_art=True
  try:self.step(n,keys)
  finally:self.capture_art=False
  return self.native[start:]
 def prepare(self,form,town=True):
  self.stage='select-form-'+str(form);self.owned_select(form);self.set_command(91+FORMS.index(form));self.ready()
  if town and self.get('room')!=0:self.travel(0)
  self.ready();self.goto(120,132,radius=2);self.step(8)
 def portrait(self,form):
  self.stage='portrait-'+str(form);self.open_tab(3);self.step(3)
  page=0xa000 if self.e.read(0x04000000,2)&16 else 0
  raw=b''.join(self.e.bytes(0x06000000+page+(56+y)*240+18,32)for y in range(32));expected=self.rom_read('return_creature_portraits',FORMS.index(form)*1024,1024)
  errors=[i for i,(a,b)in enumerate(zip(raw,expected))if b and a!=b]
  self.soft(not errors,'all opaque native portrait pixels match pinned ROM art',{'form':form,'mismatch_count':len(errors)})
  self.e.screenshot(self.out/f'portrait-{form}.png');self.close_menu()
  return {'opaque_pixels':sum(bool(b)for b in expected),'mismatches':len(errors),'native_sha256':sha(raw)}
 def art_form(self,form):
  self.prepare(form);identity=self.selected().instance_id;portrait=self.portrait(form);walk=set();casts=set();captured=[]
  # Different native movement directions and genuine roll input. No coordinate,
  # animation, selected identity or VRAM value is ever injected.
  for d in range(4):
   self.stage=f'form{form}-direction{d}';self.goto(120,132,radius=2);self.ready();self.face(d)
   rows=self.observe(32,KEYS[d]);captured.extend(rows)
   self.goto(120,132,radius=2);self.ready();self.face(d);rows=self.observe(1,'R');rows+=self.observe(11);self.e.screenshot(self.out/f'form-{form}-direction-{d}-active.png');rows+=self.observe(12)
   if self.get('return_power_kind')in (91,99):rows+=self.observe(1,'R')
   rows+=self.observe(80);captured.extend(rows)
   self.e.screenshot(self.out/f'form-{form}-direction-{d}.png')
  # A normal follower stays behind the hero, so cardinal walking alone does
  # not necessarily show every facing. Fresh B summon gives a real convergence
  # trajectory; staggered native roll bursts cover each 7-update walk cel.
  for d in range(4):
   for phase in range(8):
    self.stage=f'form{form}-walk{d}-burst{phase}'
    self.goto(120,132,radius=2);self.ready();self.step(phase+1)
    if self.get('summoned'):self.step(1,'B');self.step(1)
    self.step(1,'B')
    captured.extend(self.observe(12,KEYS[d]+'+SELECT'))
    self.step(24)
  for row in captured:
   if row['body_walk']and row['body_walk'][0]==form:walk.add(tuple(row['body_walk'][1:]))
   if row['body_cast']and row['body_cast'][0]==form:casts.add(tuple(row['body_cast'][1:]))
  current=[r for r in captured if r['state']==PLAY and r['summoned']]
  unmatched=[r['sequence']for r in current if not ((r['body_walk']and r['body_walk'][0]==form)or(r['body_cast']and r['body_cast'][0]==form))]
  body_rows=[r for r in current if any(o['tile']==712 and o['w']==o['h']==16 for o in r['oam'])]
  shadow_rows=[r for r in body_rows if any(o['tile']==720 and o['priority']==2 for o in r['oam'])]
  expected_shadow=tile_bytes(self.rom_read('hero_shadow',0,256)).hex()
  self.soft(all(r['shadow_vram']==expected_shadow for r in body_rows),'native shadow VRAM exactly matches cartridge shadow artwork',{'form':form})
  self.soft(not unmatched,'every sampled body VRAM image is an exact current form art leaf',{'form':form,'unmatched':unmatched})
  self.soft(len(walk)==16,'all four native walk frames in all four directions observed',{'form':form,'observed':sorted(walk)})
  self.soft(len(casts)==12,'all four directions and three native current-cast poses observed',{'form':form,'observed':sorted(casts)})
  self.soft(bool(body_rows)and len(shadow_rows)==len(body_rows),'summoned body and native shadow submitted to actual OAM',{'form':form,'body_frames':len(body_rows),'shadow_frames':len(shadow_rows)})
  self.soft(self.selected().instance_id==identity,'all movement/casts retain original individual identity')
  case={'form':form,'command':91+FORMS.index(form),'instance_id':identity,'portrait':portrait,'walk_leaves':sorted(walk),'cast_leaves':sorted(casts),'frames':len(captured),'body_oam_frames':len(body_rows),'shadow_oam_frames':len(shadow_rows),'unmatched_vram_frames':unmatched}
  self.art_cases.append(case);self.report();print('art',form,case,flush=True)
 def ranger_windup(self,minimum=24):
  for _ in range(240):
   if self.e.read(self.sym['enemy_windups']+2*4)>=minimum:return
   self.step(1)
  raise AssertionError('Native ranger did not begin its next real windup')
 def cast_combat(self,form):
  self.cold('evolved-17' if form in (17,101,103)else self.final_key);self.prepare(form);self.travel(61);self.stage='combat-'+str(form)
  command=91+FORMS.index(form)
  x,y={91:(120,146),94:(124,140),97:(108,140),100:(120,134),101:(108,140),102:(103,111),103:(120,146),99:(120,122),104:(40,60),105:(120,146)}.get(command,(120,140))
  if command in (95,98,104):
   for _ in range(3):
    enemy=self.enemies()[0];self.goto(enemy['x'],enemy['y']+(35 if command==98 else 24),radius=2)
  else:self.goto(x,y,radius=2)
  self.face(1);self.ready()
  if command in (92,94,96,103):self.ranger_windup(24)
  if command==102:
   self.ranger_windup(28);self.step(12,'RIGHT+DOWN+SELECT');self.step(1,'UP')
  before=self.observation();rows=self.observe(1,'R');release_sequence=None
  for n in range(114):
   c=self.cast();age=self.get('return_power_age');key=0
   if command==91 and age>=22 and not c.released:key='R'
   if command==96 and c.charged and age>=8 and not c.released:key='R'
   if command==99 and age>=12 and not c.released:key='R'
   if command==98 and n<48:key='UP+SELECT'if n<12 else'UP'
   if key=='R':release_sequence=self.sequence+1
   rows+=self.observe(1,key)
  self.e.screenshot(self.out/f'combat-{command}.png');after=self.observation()
  damage=[before['enemies'][i]['hp_q4']-min(r['enemies'][i]['hp_q4']for r in rows)for i in range(6)]
  guarded=any(r['guard_used']for r in rows);charged=any(r['charged']for r in rows);hits=any(r['hits']for r in rows)
  self.soft(any(r['time']and r['kind']==command for r in rows),'earned selected signature activates through actual R',{'form':form,'command':command})
  self.soft(after['time']==0,'actual signature expires finitely without cooldown refund',{'command':command,'after':after['time']})
  drops=[sum(b['enemies'][i]['hp_q4']<a['enemies'][i]['hp_q4']for a,b in zip([before]+rows,rows))for i in range(6)]
  self.soft(all(n<=1 for n in drops),'one damage receipt maximum per native enemy identity during this cast',{'command':command,'damage_updates_per_slot':drops})
  if command in (92,103):self.soft(guarded,'guard catches native ordinary hostile shot',{'command':command})
  else:self.soft(any(n>0 for n in damage),'signature damages a genuinely spawned ordinary foe through native collision',{'command':command,'damage':damage})
  if command in (91,96,99):self.soft(release_sequence is not None and any(r['released']for r in rows),'fresh R release observed within this same actual cast',{'command':command,'release_sequence':release_sequence})
  if command==102:self.soft(any(r['quiet_used']for r in rows),'side quiet cut cancels actual native ranger windup')
  case={'form':form,'command':command,'source_snapshot':self.loaded[-1]['snapshot'],'before':before,'after':after,'damage_q4_by_slot':damage,'ordinary_guard_observed':guarded,'charged_observed':charged,'hit_receipt_observed':hits,'fresh_R_sequence':release_sequence,'sequences':[rows[0]['sequence'],rows[-1]['sequence']]}
  self.combat_cases.append(case);self.report();print('combat',command,'damage',damage,'guard',guarded,'charged',charged,flush=True)
 def preview(self):
  self.cold(self.final_key);self.prepare(3);self.goto(152,133,radius=3);self.face(2);self.step(150);self.e.screenshot(self.out/'harmless-town-native.png')
  im=self.e.screenshot();im.resize((720,480),Image.Resampling.NEAREST).save(self.out/'harmless-town-3x.png');self.report()
 def controls(self):
  self.cold(self.final_key);self.prepare(3);self.stage='fresh-r-pause-picker';self.face(1);rows=self.observe(1,'R');rows+=self.observe(11);c=self.cast();self.soft(c.released==0,'hearth begins unreleased before fresh R')
  self.step(1,'START');self.step(3);frozen=(self.get('return_power_age'),self.get('ability_cd'));self.step(16);self.soft(frozen==(self.get('return_power_age'),self.get('ability_cd')),'pause freezes cast age and shared cooldown')
  self.step(1,'START');self.step(3);self.step(1,'L');self.step(16,'L');frozen=(self.get('return_power_age'),self.get('ability_cd'));self.step(8,'L');self.soft(frozen==(self.get('return_power_age'),self.get('ability_cd')),'held picker freezes cast age and shared cooldown');self.step(1);self.step(2)
  self.observe(1,'R');self.soft(self.cast().released==1,'fresh R releases same hearth cast');self.observe(80)
  self.control_cases.append({'case':'pause-picker-fresh-r','passed_checks_recorded':True});self.report()
 def weapons(self):
  for cls in (1,2,3):
   self.cold(self.final_key);self.prepare(3);self.equip_class(cls);self.travel(61);self.stage='weapon-class-'+str(cls)
   self.goto(120,130 if cls<3 else 145,radius=2);self.face(1);self.step(40)
   before=self.observation();rows=self.observe(24 if cls==3 else 1,'A');rows+=self.observe(55)
   damage=[before['enemies'][i]['hp_q4']-min(r['enemies'][i]['hp_q4']for r in rows)for i in range(6)]
   self.soft(any(n>0 for n in damage),'actual player weapon damages native ordinary enemy',{'class':cls,'damage':damage})
   self.soft(not any(r['time']for r in rows),'A weapon input does not activate companion signature',{'class':cls})
   self.control_cases.append({'case':'weapon','class':cls,'damage_q4_by_slot':damage,'sequences':[rows[0]['sequence'],rows[-1]['sequence']]});self.e.screenshot(self.out/f'weapon-combat-{cls}.png');self.report()
 def cancellation_controls(self):
  self.cold(self.final_key);self.prepare(3);self.stage='held-r-no-retrigger';self.face(1);rows=self.observe(200,'R');self.step(1)
  self.soft(any(r['released']and r['release_age']==44 for r in rows),'held R waits for finite automatic hearth release at age44')
  self.soft(rows[-1]['cooldown']==0 and rows[-1]['time']==0,'holding R through cooldown does not manufacture another cast')
  self.stage='identity-revocation';self.ready();self.observe(1,'R');self.observe(12);original=self.selected().instance_id;old_cd=self.get('ability_cd');self.assign(2,6);self.select_slot(2);c=self.cast()
  self.soft(self.selected().instance_id!=original and c.revoked,'actual menu reassignment and selected-identity change revoke old cast rights')
  self.soft(0<self.get('ability_cd')<=old_cd,'selection never refunds shared cooldown');self.observe(1,'R');self.soft(self.get('return_power_kind')==91,'new selected companion cannot replace active cast during shared cooldown');self.observe(100)
  self.control_cases.append({'case':'held-R-and-identity-revocation'});self.report()
  self.cold(self.final_key);self.prepare(3);self.stage='transition-cancellation';self.goto(176,128,radius=2);self.face(1);self.observe(1,'R');self.observe(8);old=self.get('ability_cd');self.tap('A');self.settle()
  self.soft(self.get('room')==54 and self.get('return_power_time')==0,'real board transition clears active power')
  self.soft(self.get('ability_cd')>0 and self.get('ability_cd')<=old,'room reset does not refund shared cooldown');self.control_cases.append({'case':'transition-cancellation'});self.report()
  self.cold(self.final_key);self.prepare(3);self.travel(61);self.stage='death-cancellation';self.goto(120,122,radius=1);self.ready()
  for _ in range(12000):
   if self.hp_q4()<=16 and 4<=self.get('invuln')<=8:break
   if self.get('game_state')==DEAD:break
   self.step(1)
  self.observe(1,'R');rows=self.observe(100)
  self.soft(any(r['time']>0 for r in rows)and any(r['state']==DEAD and r['time']==0 for r in rows),'real death cancels a genuinely active cast')
  self.control_cases.append({'case':'death-cancellation','sequences':[rows[0]['sequence'],rows[-1]['sequence']]});self.report()
 def extra_controls(self):
  self.cold(self.final_key);self.prepare(24);self.stage='bounded-moving-heat';self.face(1);rows=self.observe(1,'R');rows+=self.observe(40,'UP');rows+=self.observe(25)
  releases=[r for r in rows if r['released']]
  self.soft(bool(releases)and releases[0]['release_age']<=26 and max(r['carry_steps']for r in rows)<=16,'moving heat automatically deposits within26 updates and16 carried pixels')
  self.soft(bool(releases)and len({tuple(r['drop'])for r in releases})==1,'continued native player movement never drags deposited crescent')
  self.control_cases.append({'case':'bounded-moving-heat','release_age':releases[0]['release_age']if releases else None,'carry_steps':max(r['carry_steps']for r in rows),'drop':releases[0]['drop']if releases else None});self.report()
  self.cold(self.final_key);self.prepare(3);self.stage='full52-selector-browse';before=self.state_signature();selected=self.selected().instance_id;party=bytes(self.roster().party);self.open_tab(2);seen=set()
  for n in range(53):
   seen.add(self.get('quickparty_menu_candidate'));self.tap('DOWN',2,3)
   if n in (0,26,52):self.e.screenshot(self.out/f'selector52-{n}.png')
  self.soft(len(seen)==53 and 255 in seen,'controller storage browser reaches all52 retained individuals plus empty choice')
  self.soft(bytes(self.roster().party)==party and self.selected().instance_id==selected and self.state_signature()==before,'full collection browsing preserves party, selected identity, roster, quests and gear');self.close_menu();self.control_cases.append({'case':'52-individual-selector','candidates':sorted(seen)});self.report()
  self.stage='fresh-cardinal-aim';self.ready();self.face(1);self.observe(1,'R');self.observe(1);self.observe(1,'RIGHT');self.soft(self.get('return_power_direction')==3 and self.cast().aimed,'first fresh cardinal edge chooses facing during the first8 updates');self.observe(1,'UP');self.soft(self.get('return_power_direction')==3,'later direction cannot redirect already committed facing');self.observe(160)
  self.face(1);self.observe(1,'R');self.observe(1,'DOWN+RIGHT');self.soft(self.get('return_power_direction')==1 and not self.cast().aimed,'diagonal edge does not silently choose cardinal facing');self.observe(1);self.observe(1,'LEFT');self.soft(self.get('return_power_direction')==2 and self.cast().aimed,'valid cardinal after ignored diagonal still chooses facing');self.observe(160)
  self.stage='early-hearth-release';self.face(1);self.observe(1,'R');self.observe(8);self.observe(1,'R');self.soft(self.cast().released and not self.cast().charged and self.cast().release_age<20,'fresh R can release an uncharged hearth before its ember catch');self.observe(160);self.control_cases.append({'case':'fresh-cardinal-and-early-hearth'});self.report()
  self.cold('evolved-17');self.prepare(17);self.stage='empty-notch-no-bank';self.face(1);self.observe(1,'R');self.observe(10);cd=self.get('ability_cd');self.observe(1,'R');self.soft(not self.cast().released and not self.cast().charged and self.get('ability_cd')<cd,'fresh R cannot release or refund an empty notch');self.observe(50);self.soft(self.get('return_power_time')==0 and not self.cast().charged,'empty notch expires without retained charge');self.control_cases.append({'case':'empty-notch-no-bank'});self.report()
 def close(self):
  if self.native_file:self.native_file.close();self.native_file=None
  self.close_global_trace();self.report();self.e.close()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('rom','symbols','source-manifest','source-root','producer-report','output'):p.add_argument('--'+k,type=Path,required=True)
 for k in ('rom-sha','symbols-sha','elf-sha','manifest-sha','producer-sha'):p.add_argument('--'+k,required=True)
 p.add_argument('--work',choices=('art','combat','controls','controls-extra','preview','all'),default='all');p.add_argument('--forms',default=','.join(map(str,FORMS)));a=p.parse_args()
 r=CompanionControls(a.rom,a.symbols,a.output,a.rom_sha,a.symbols_sha,a.elf_sha,a.source_manifest,a.manifest_sha,source_root=a.source_root)
 try:
  r.attach_producer(a.producer_report,a.producer_sha)
  if a.work in ('art','all'):
   for f in map(int,a.forms.split(',')):
    r.cold('evolved-17'if f in (17,101,103)else r.final_key);r.art_form(f)
  if a.work in ('combat','all'):
   for f in map(int,a.forms.split(',')):r.cast_combat(f)
  if a.work in ('controls','all'):r.controls();r.cancellation_controls();r.weapons()
  if a.work in ('controls-extra','all'):r.extra_controls()
  if a.work in ('preview','all'):r.preview()
  r.verify_closures();r.soft(not r.summary['exceptions'],'every active hardware frame has exactly one update and flip within280896 cycles and128OBJ',r.summary['exceptions']);r.stage='finished-'+a.work
 except Exception as exc:
  r.failures.append({'error':str(exc),'traceback':traceback.format_exc(),'stage':r.stage});r.e.screenshot(r.out/'failure.png');raise
 finally:r.close()
 return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
