#!/usr/bin/env python3
"""Real current world/transactions with synthetic positions and live-effect stubs.

Renderer geometry is independently proven elsewhere. This suite is not native
controller acquisition or pacing acceptance. No production state is edited.
"""
from pathlib import Path
import ctypes as C, hashlib, json, os, subprocess, unittest
import covenants_host_support as H
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/covenants-world-review'
class World(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  OUT.mkdir(parents=True,exist_ok=True)
  source=(ROOT/'src/covenants_game.c').read_text()
  cls.core_only=not (ROOT/'src/covenants_draw.inc').exists()
  assert not cls.core_only,'Complete world review requires the production draw layer'
  (OUT/'covenants_world_source.inc').write_text(source)
  files=['tests/covenants_world_host.c']+['src/'+s+'.c'for s in ['covenants_art','covenants_quests','save4','save5','creatures','creature_data','equipment','equipment_data','progression_events']]
  cls.hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in files+['src/covenants_game.c','src/covenants_geometry.inc','src/covenants_work.inc','src/covenants_fields.inc','src/covenants_interact.inc','src/covenants_work_data.inc']+(['src/covenants_draw.inc'] if not cls.core_only else [])}
  for name,data in H.source_closure(ROOT,('covenants_game','covenants_art','covenants_quests','save4','save5','creatures','creature_data','equipment','equipment_data','progression_events')).items():cls.hashes[name]=hashlib.sha256(data).hexdigest()
  for name in ('tests/test_covenants_world.py','tests/covenants_host_support.py'):cls.hashes[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
  sanitized=os.environ.get('COVENANTS_WORLD_SANITIZE')=='1'
  cls.sanitized=sanitized
  p=OUT/('world-sanitized.so' if sanitized else 'world.so')
  sanitize=['-fsanitize=address,undefined','-fno-omit-frame-pointer'] if sanitized else []
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-Wl,--no-undefined','-fPIC','-shared','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-Isrc','-I'+str(OUT),*sanitize,*files,'-o',str(p)],cwd=ROOT,check=True)
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-Isrc','-c','src/covenants_game.c','-o',str(OUT/'strict-world.o')],cwd=ROOT,check=True)
  cls.l=C.CDLL(str(p));cls.l.sram=(C.c_ubyte*32768).in_dll(cls.l,'save5_test_sram');cls.s=H.Save.in_dll(cls.l,'adventure_save')
  cls.l.covenants_job_begin.argtypes=[C.POINTER(H.Save),C.POINTER(H.Request),C.c_uint,C.c_uint]
  cls.l.covenants_job_step.argtypes=[C.c_uint]*4
 @classmethod
 def tearDownClass(cls):
  assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in cls.hashes.items()),'Production source changed during tests; rerun'
  (OUT/('sanitized-source-report.json' if cls.sanitized else 'strict-source-report.json')).write_text(json.dumps({'scope':'Real world and save jobs; synthetic effect certificates and positions; no native claim','draw_excluded':cls.core_only,'source_sha256':cls.hashes,'raw_world_state_member_sum_bytes':cls.l.world_bytes(),'allocation_note':'See arm-report.json for allocated data+bss including alignment','sanitizers':['address','undefined'] if cls.sanitized else []},indent=2)+'\n')
 def setUp(self):
  H._generation=max(H._generation,self.l.covenants_game_scene_generation())+1
  s=H.enter(self.l);C.memmove(C.addressof(self.s),C.addressof(s),C.sizeof(s));self.l.adopt_fixture(H.generation())
 def at(self,x,y,f=1):self.l.at(x,y,f)
 def act(self,x,y,f=1):
  dx,dy={1:(0,18),0:(0,-18),2:(18,0),3:(-18,0)}[f];self.at(x+dx,y+dy,f)
  self.assertEqual(self.l.covenants_game_interact(),1,(C.c_int.in_dll(self.l,'room').value,x,y,self.l.get_toast()));self.assertEqual(self.l.settle(),1)
 def entry(self,r,s=0):self.assertEqual(self.l.entry(r,s),1,(r,s))
 def select(self,form,cmd):
  if not any(c.form_id==form for c in self.s.roster.instances):form+=1
  slot=self.l.select_form(form,cmd);self.assertLess(slot,160,(form,cmd,slot));return slot
 def hit(self,i,form,cmd,x,y,f=1,beat=1,release=0):
  self.select(form,cmd);self.at(x,y,f);token=self.l.action();self.assertNotEqual(token,0);self.assertEqual(self.l.hit(i,token,beat,release),1,(i,cmd,self.l.get_toast()));return token
 def heat(self,a,b,x,y):
  self.select(107,108);self.at(x,y,3);token=self.l.action();self.assertEqual(self.l.hit(a,token,1,0),1);self.assertEqual(self.l.hit(b,token,2,1),1)
 def tick(self,n=1):self.l.tick(n);self.assertEqual(self.l.settle(),1)
 def test_geometry_data_targets_match_actual_world(self):
  data=json.loads((ROOT/'assets/covenants_world/geometry.json').read_text())
  for r in data['rooms']:
   # Target API is selected by active lower/upper quest; pre-authorized state
   # construction uses the real typed jobs, not direct quest-bit mutation.
   if r['id']==74:
    for src in range(1,5):H.fulfill(self.l,self.s,src)
    H.claim(self.l,self.s,61,70);H.offer(self.l,self.s,62,74)
   self.entry(r['id']);idx=0
   for station in r['stations']:
    for t in station['targets']:
     x=C.c_int();y=C.c_int();rad=C.c_int();self.assertEqual(self.l.covenants_game_field_target(idx,C.byref(x),C.byref(y),C.byref(rad)),1)
     self.assertEqual([x.value,y.value],t['center']);self.assertEqual(rad.value,t['radius']);idx+=1
 def test_stale_source_scene_owner_geometry_and_overlap(self):
  for fault in range(9):
   self.setUp();self.entry(70);self.select(105,106);self.at(120,240);t=self.l.action();self.l.fault(fault);self.assertEqual(self.l.hit(0,t,1,0),0,fault);self.assertEqual(self.l.get_setting(0),0)
 def test_party_equipment_and_command_mutation_revokes(self):
  mutations=[lambda c:setattr(c,'instance_id',c.instance_id+1),lambda c:setattr(c,'form_id',c.form_id+1),lambda c:setattr(c,'selected_command',1),lambda c:c.equipped.__setitem__(1,1),lambda c:setattr(c,'flags',c.flags^2),lambda c:self.s.roster.party.__setitem__(1,159),lambda c:self.s.roster.__setattr__('selected_party',1),lambda c:self.s.equipment.equipped.__setitem__(0,0),lambda c:setattr(self.s.equipment.bag[next(i for i in self.s.equipment.equipped if i<48)],'rank',7)]
  for i,mutate in enumerate(mutations):
   self.setUp();self.entry(70);slot=self.select(105,106);self.at(120,240);t=self.l.action();mutate(self.s.roster.instances[slot]);self.assertEqual(self.l.hit(0,t,1,0),0,i);self.assertEqual(self.l.get_setting(0),0)
 def test_field_receipt_pauses_outside_play_without_spending_cast(self):
  self.entry(70);self.select(105,106);self.at(120,240);token=self.l.action();self.assertNotEqual(token,0)
  game_state=C.c_int.in_dll(self.l,'game_state')
  for state in (0,2,3,4,5,6,7,8,9,10):
   game_state.value=state;self.assertEqual(self.l.hit(0,token,1,0),0,state)
   self.assertEqual(self.l.get_setting(0),0);self.assertEqual(self.l.cast_id(),token)
  game_state.value=1;self.assertEqual(self.l.hit(0,token,1,0),1);self.assertEqual(self.l.get_setting(0),1)
 def test_heat_requires_same_cast_and_both_beats(self):
  self.entry(70);self.select(107,108);self.at(160,112,3);t=self.l.action();self.assertEqual(self.l.hit(2,t,2,1),0);self.assertEqual(self.l.get_setting(0),0)
  t=self.l.action();self.assertEqual(self.l.hit(1,t,1,0),1);new=self.l.action();self.assertEqual(self.l.hit(2,new,2,1),0);self.assertEqual(self.l.get_setting(0),0)
  t=self.l.action();self.assertEqual(self.l.hit(1,t,1,0),1);self.assertEqual(self.l.hit(2,t,2,0),0);self.assertEqual(self.l.get_setting(0),0)
  self.heat(1,2,160,112);self.assertEqual(self.l.get_setting(0),2)
 def test_partial_progress_reset_deliberate_confirm_and_freeze(self):
  self.entry(70);self.hit(0,105,106,120,240);self.assertEqual(self.l.get_setting(0),1)
  self.select(103,104);self.assertEqual(self.l.get_setting(0),1)
  self.act(48,296);self.assertEqual(self.l.confirmation(0),1);self.assertEqual(self.l.get_setting(0),1)
  self.l.covenants_game_input(2,0);self.assertEqual(self.l.confirmation(0),0);self.assertEqual(self.l.get_setting(0),1)
  self.act(48,296);self.at(120,240);self.l.covenants_game_input(0,0);self.assertEqual(self.l.confirmation(0),0)
  self.act(48,296);self.act(48,296);self.assertEqual(self.l.get_setting(0),0)
  self.hit(0,105,106,120,240);self.entry(71);self.entry(70);self.assertEqual(self.l.get_setting(0),0)
 def test_orchard_moving_body_obstruction_returns_safe(self):
  self.entry(71);self.hit(0,105,106,48,112);self.act(120,232);self.assertEqual(self.l.get_moving_state(),1)
  self.at(118,112);self.tick();self.assertEqual(self.l.get_moving_x(),88);self.assertEqual(self.l.get_moving_state(),2)
  self.at(192,232);self.tick(70);self.assertEqual(self.l.get_moving_x(),88);self.assertEqual(self.l.get_moving_state(),0)
 def follow(self,stage,limit=2000):
  for _ in range(limit):
   if self.l.get_stage()==stage:return
   x=self.l.get_npc_x();y=self.l.get_npc_y();self.at(x,y+20);self.tick(3)
  self.fail(('NPC stalled',C.c_int.in_dll(self.l,'room').value,self.l.get_npc_x(),self.l.get_npc_y(),self.l.get_stage(),self.l.get_moving_x(),self.l.get_moving_state()))
 def upper(self):
  for src in range(1,5):H.fulfill(self.l,self.s,src)
  H.claim(self.l,self.s,61,70);H.offer(self.l,self.s,62,74);self.l.adopt_fixture(H.generation())
 def test_eight_distinct_mechanisms(self):
  self.entry(70);self.hit(0,105,106,120,240);self.heat(1,2,160,112);self.hit(3,109,110,320,112);self.hit(4,101,102,320,240);self.hit(5,103,104,120,160)
  self.act(144,264);self.act(144,264);self.act(352,176);self.act(144,240);self.act(336,272);self.tick();self.assertTrue(self.l.covenants_fulfilled(C.byref(self.s),1))
  self.entry(71);self.hit(0,105,106,48,112);self.hit(1,103,104,192,112);self.act(120,232);self.at(192,232);self.tick(70)
  self.assertEqual(self.l.get_moving_x(),120);self.act(96,192);self.act(160,192);self.act(160,232);self.follow(3);self.assertTrue(self.l.covenants_fulfilled(C.byref(self.s),2))
  self.entry(72);self.act(336,104);self.heat(0,1,96,104);self.hit(2,101,102,224,104);self.tick(72)
  for x in (144,272,384):self.act(x,104)
  self.tick();self.assertTrue(self.l.covenants_fulfilled(C.byref(self.s),3))
  self.entry(73);self.hit(0,109,110,48,64);self.hit(1,105,106,192,64);self.act(64,128);self.follow(4);self.assertTrue(self.l.covenants_fulfilled(C.byref(self.s),4))
  self.entry(70);self.act(128,272);self.assertEqual(self.l.settle(),1);self.entry(74);self.act(136,264)
  self.hit(0,105,106,192,112);self.act(120,240);self.act(240,136);self.hit(1,101,102,288,112)
  for point in ((120,216),(360,240),(240,168)):self.act(*point)
  self.tick();self.assertTrue(self.l.covenants_fulfilled(C.byref(self.s),5))
  self.entry(75);self.hit(0,105,106,120,64);self.act(192,232);self.hit(1,111,112,112,184);self.act(160,208);self.follow(4);self.assertTrue(self.l.covenants_fulfilled(C.byref(self.s),6))
  self.entry(76);self.hit(0,109,110,96,96);self.act(112,128);self.follow(3)
  self.hit(1,103,104,240,112);self.at(320,128);self.tick(60);self.assertEqual(self.l.get_moving_x(),272)
  self.hit(2,103,104,384,120);self.act(384,120);self.follow(6);self.assertTrue(self.l.covenants_fulfilled(C.byref(self.s),7))
  self.entry(77);self.act(120,120);self.heat(0,1,72,112);self.hit(2,109,110,120,96);self.hit(3,101,102,168,112)
  for _ in range(3):self.act(120,120);self.l.enemies_clear()
  self.act(120,120);self.assertTrue(self.l.covenants_fulfilled(C.byref(self.s),8))
  self.assertEqual(self.s.quests.region_flags[23],0,'Covenant work must not grant invitations')
 def test_upper_circuit_mechanisms(self):
  self.upper();self.entry(74)
  self.hit(0,105,106,192,112);self.act(120,240);self.act(240,136);self.hit(1,101,102,288,112)
  for point in ((120,216),(360,240),(240,168)):self.act(*point)
  self.tick();self.assertTrue(self.l.covenants_fulfilled(C.byref(self.s),5))
  self.entry(75);self.hit(0,105,106,120,64);self.act(192,232);self.hit(1,111,112,112,184);self.act(160,208);self.follow(4);self.assertTrue(self.l.covenants_fulfilled(C.byref(self.s),6))
  self.entry(76);self.hit(0,109,110,96,96);self.act(112,128);self.follow(3)
  self.hit(1,103,104,240,112);self.at(320,128);self.tick(60);self.assertEqual(self.l.get_moving_x(),272)
  self.hit(2,103,104,384,120);self.act(384,120);self.follow(6);self.assertTrue(self.l.covenants_fulfilled(C.byref(self.s),7))
  self.entry(77);self.act(120,120);self.heat(0,1,72,112);self.hit(2,109,110,120,96);self.hit(3,101,102,168,112)
  for _ in range(3):self.act(120,120);self.l.enemies_clear()
  self.act(120,120);self.assertTrue(self.l.covenants_fulfilled(C.byref(self.s),8))
  self.assertEqual(self.s.quests.region_flags[23],0,'Covenant work must not grant invitations')
 def test_unique_invitations_declines_and_repeats(self):
  self.upper()
  for src in range(5,9):H.fulfill(self.l,self.s,src)
  self.l.adopt_fixture(H.generation())
  for src in range(1,9):
   self.entry(69+src);x,y=(432,272) if src in (1,5) else (192,272) if src in (2,6) else (432,112) if src in (3,7) else (192,112)
   before=self.l.creatures_roster_count(C.byref(self.s.roster));self.act(x,y);self.assertEqual(self.l.confirmation(1),src);self.l.covenants_game_input(2,0);self.assertEqual(self.l.creatures_roster_count(C.byref(self.s.roster)),before)
   self.act(x,y);self.act(x,y);self.assertEqual(self.l.creatures_roster_count(C.byref(self.s.roster)),before+1)
   self.act(x,y);self.act(x,y);self.assertEqual(self.l.creatures_roster_count(C.byref(self.s.roster)),before+1)
   self.assertEqual(sum(c.form_id==120+src for c in self.s.roster.instances),1)
 def test_practice_exact_targets_same_cast_no_durable_reward(self):
  H._generation=max(H._generation,self.l.covenants_game_scene_generation())+1
  complete=H.story(self.l,True);C.memmove(C.addressof(self.s),C.addressof(complete),C.sizeof(complete));self.l.adopt_fixture(H.generation())
  data=json.loads((ROOT/'assets/covenants_world/geometry.json').read_text())
  for info in data['rooms']:
   p=info['practice'];self.entry(info['id']);self.select(p['form'],p['command']);self.act(*info['manual'][0]);self.assertEqual(self.l.get_mode(),1)
   for i,target in enumerate(p['targets']):
    x=C.c_int();y=C.c_int();r=C.c_int();self.assertEqual(self.l.covenants_game_field_target(i,C.byref(x),C.byref(y),C.byref(r)),1);self.assertEqual([x.value,y.value],target['center'])
   self.at(*p['start_xy'],p['face']);before=bytes(self.s);t=self.l.action()
   if p['command'] in (122,127):
    self.assertEqual(self.l.hit(0,t,1,0),1);new=self.l.action();self.assertEqual(self.l.hit(1,new,1,0),1);self.assertEqual(self.l.get_practice_ticks(),0,'Partial targets must not accumulate across casts');t=self.l.action()
   if p['command']==123:
    self.assertEqual(self.l.hit(1,t,2,1),0);t=self.l.action();self.assertEqual(self.l.hit(0,t,1,0),1);new=self.l.action();self.assertEqual(self.l.hit(1,new,2,1),0);t=self.l.action()
   for i in range(len(p['targets'])):self.assertEqual(self.l.hit(i,t,2 if p['command']==123 and i==1 else 1,int(p['command']==12 or p['command']==123 and i==1)),1)
   if p['command']==124:self.tick(90)
   self.assertGreater(self.l.get_practice_ticks(),0,(p['command'],'practice did not activate'));self.assertEqual(bytes(self.s),before)
   self.at(24,128);self.tick(400);self.assertEqual(self.l.get_practice_ticks(),0);self.assertEqual(bytes(self.s),before)
 def test_menu_pause_and_held_practice_revocation(self):
  H._generation=max(H._generation,self.l.covenants_game_scene_generation())+1
  complete=H.story(self.l,True);C.memmove(C.addressof(self.s),C.addressof(complete),C.sizeof(complete));self.l.adopt_fixture(H.generation())
  self.entry(73);self.select(124,124);self.act(120,128);self.at(48,64);t=self.l.action();self.assertEqual(self.l.hit(0,t,1,0),1)
  C.c_int.in_dll(self.l,'game_state').value=3;self.l.tick(100);self.assertEqual(self.l.cast_id(),t);self.assertEqual(self.l.get_practice_ticks(),0)
  C.c_int.in_dll(self.l,'game_state').value=1;self.l.tick(5);self.assertEqual(self.l.get_practice_ticks(),0)
  self.l.covenants_game_selection_changed();self.l.tick(30);self.assertEqual(self.l.get_practice_ticks(),0);self.assertEqual(self.l.cast_id(),0)
 def test_practice_strip_stays_open_under_actor(self):
  H._generation=max(H._generation,self.l.covenants_game_scene_generation())+1
  complete=H.story(self.l,True);C.memmove(C.addressof(self.s),C.addressof(complete),C.sizeof(complete));self.l.adopt_fixture(H.generation())
  self.entry(70);self.select(121,12);self.act(144,264);self.at(120,160);t=self.l.action();self.assertEqual(self.l.hit(0,t,1,1),1)
  self.at(240,144);self.tick(400);self.assertEqual(self.l.get_practice_ticks(),1);self.assertFalse(self.l.covenants_game_solid(240,144))
  self.at(330,160);self.tick();self.assertEqual(self.l.get_practice_ticks(),0);self.assertTrue(self.l.covenants_game_solid(240,144))
 def test_npc_obstruction_pauses_and_resumes(self):
  self.entry(71);self.hit(0,105,106,48,112);self.hit(1,103,104,192,112);self.act(120,232);self.at(192,232);self.tick(70)
  self.act(96,192);self.act(160,192);self.act(160,232)
  before=self.l.get_toast_count();self.at(168,232);self.tick(30);self.assertEqual(self.l.get_npc_x(),160)
  self.assertEqual(self.l.get_blocked_ticks(),10);self.assertEqual(self.l.get_toast_count(),before+1)
  self.tick(120);self.assertEqual(self.l.get_npc_x(),160);self.assertEqual(self.l.get_toast_count(),before+1,'Hint must not repeat while continuously obstructed')
  self.at(160,252);self.tick(3);self.assertEqual(self.l.get_npc_x(),161);self.assertEqual(self.l.get_blocked_ticks(),0)
  self.at(169,232);self.tick(30);self.assertEqual(self.l.get_npc_x(),161);self.assertEqual(self.l.get_toast_count(),before+2,'A new obstruction can show a fresh hint')
  self.l.covenants_game_reset();self.assertEqual(self.l.get_stage(),0);self.assertEqual(self.l.get_npc_x(),160);self.assertEqual(self.l.get_blocked_ticks(),0)
 def test_completed_ferry_reconstructs_arrival(self):
  self.upper();H.move(self.l,self.s,75);H.fulfill(self.l,self.s,7);self.l.adopt_fixture(H.generation());self.entry(76)
  self.assertEqual(self.l.get_stage(),6);self.assertEqual((self.l.get_npc_x(),self.l.get_npc_y()),(384,128));self.assertEqual(self.l.get_moving_x(),272)
  before=bytes(self.s);self.l.covenants_game_reset();self.assertEqual(self.l.get_stage(),6);self.assertEqual(bytes(self.s),before)
 def test_old_scene_prepared_before_first_tick(self):
  for destination,position in ((0,(0,0)),(62,(416,32))):
   C.c_int.in_dll(self.l,'room').value=8;self.l.covenants_game_reset()
   C.c_int.in_dll(self.l,'room').value=destination;self.at(8,140)
   prior=bytes(self.s);revision=C.c_uint.in_dll(self.l,'covenants_game_revision').value
   scene=self.l.covenants_game_scene_generation();self.l.covenants_game_prepare_old_scene()
   self.assertEqual((self.l.get_npc_x(),self.l.get_npc_y()),position)
   self.assertEqual(C.c_uint.in_dll(self.l,'covenants_game_revision').value,revision+1)
   self.assertNotEqual(self.l.covenants_game_scene_generation(),scene)
   revision+=1;scene=self.l.covenants_game_scene_generation()
   self.l.covenants_game_prepare_old_scene();self.l.covenants_game_tick_old()
   self.assertEqual(C.c_uint.in_dll(self.l,'covenants_game_revision').value,revision)
   self.assertEqual(self.l.covenants_game_scene_generation(),scene)
   self.assertEqual(bytes(self.s),prior)
 def test_world_memory_budget(self):self.assertLessEqual(self.l.world_bytes(),512)
if __name__=='__main__':unittest.main(verbosity=2)
