#!/usr/bin/env python3
"""Actual world/jobs/save policy, synthetic tagged hits. Native acceptance separate."""
from pathlib import Path
import ctypes as C,json,subprocess,tempfile,unittest,sys
from horizons_host_support import Save,FIXTURE
ROOT=Path(__file__).resolve().parents[1]
class World(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='horizons-world-');cls.addClassCleanup(cls.tmp.cleanup)
  p=Path(cls.tmp.name)/'world.so';sources=['tests/horizons_world_host.c']+['src/'+s+'.c'for s in ['horizons_art','horizons_creature_art','horizons_quests','save4','save5','creatures','creature_data','equipment','equipment_data','progression_events']]
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-fPIC','-shared','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-Isrc',*sources,'-o',str(p)],cwd=ROOT,check=True);cls.l=C.CDLL(str(p));cls.sram=(C.c_ubyte*32768).in_dll(cls.l,'save5_test_sram');cls.s=Save.in_dll(cls.l,'adventure_save')
 def setUp(self):self.sram[:]=FIXTURE.read_bytes();self.assertEqual(self.l.fresh(),1)
 def at(self,x,y,f=1):self.l.at(x,y,f);self.assertFalse(self.l.horizons_game_solid(x,y),(C.c_int.in_dll(self.l,'room').value,x,y))
 def old(self,r,spawn=0):self.l.old_room(r,spawn)
 def act(self,x,y,old=False,f=1):
  dx,dy={1:(0,18),0:(0,-18),2:(18,0),3:(-18,0)}[f];self.at(x+dx,y+dy,f);self.assertEqual((self.l.horizons_game_old_interact if old else self.l.horizons_game_interact)(),1,(x,y,self.l.get_toast()));self.assertEqual(self.l.settle(),1,(x,y,self.l.get_toast()))
 def entry(self,r,s=0):self.assertEqual(self.l.entry(r,s),1,(r,s));self.assertEqual(self.l.valid(),1)
 def select(self,form,cmd):
  if not any(c.form_id==form for c in self.s.roster.instances):form+=1
  self.assertLess(self.l.select_form(form,cmd),160);return next(i for i,c in enumerate(self.s.roster.instances)if c.form_id==form)
 def field(self,i,x,y,f=1,form=None,cmd=None,want=1):
  if form:self.select(form,cmd)
  self.at(x,y,f);self.assertEqual(self.l.synthetic_field(i),want,(C.c_int.in_dll(self.l,'room').value,i,self.l.get_toast()));self.assertEqual(self.l.settle(),1)
 def walk(self,x,y):self.at(x,y);self.l.tick();self.assertEqual(self.l.settle(),1)
 def invite(self,x,y):self.act(x,y);self.act(x,y)
 def intro(self):
  self.old(60);self.act(64,112,True);self.old(61);self.entry(62);self.act(208,208);self.act(272,208);self.walk(240,240);self.invite(352,224);self.act(120,208);self.assertEqual(self.l.qs(54),3)
 def stage(self):
  self.entry(63);self.act(136,80);self.act(80,96);self.field(0,224,90,2,105,106)
  for _ in range(16):self.l.tick()
  self.assertEqual(self.l.get_setting(0),1);self.field(0,256,90,2)
  for _ in range(16):self.l.tick()
  self.walk(256,128);self.entry(64);self.field(0,64,88,1);self.field(2,176,88,1);self.field(3,208,120,1,101,102);self.entry(63);self.invite(416,96);self.act(416,96);self.assertEqual(self.l.qs(55),3)
 def water(self):
  self.entry(63);self.entry(65);self.act(96,176);self.act(336,208);self.field(0,336,192,1,103,104);self.entry(66);self.field(0,176,248,2,105,106);self.field(2,176,104,1,103,104);self.field(3,208,104,1);self.invite(64,256);self.entry(65);self.act(352,272);self.assertEqual(self.l.qs(56),3)
 def finale(self):
  self.entry(67);self.field(0,48,224,3,109,110);self.act(352,224);self.select(107,108);self.at(300,208,2);t=self.l.action();self.assertEqual(self.l.hit(1,t,1,0),1);self.assertEqual(self.l.hit(2,t,2,1),1);self.assertEqual(self.l.settle(),1);self.entry(68);self.field(0,48,96,1,105,106);self.field(1,120,96,1,101,102);self.field(2,192,96,1,103,104);self.invite(192,112);self.entry(62);self.act(120,208);self.assertEqual(self.l.qs(57),3)
 def chapter(self,reverse=False):
  self.intro()
  if reverse:self.water();self.stage()
  else:self.stage();self.water()
  self.finale()
 def test_main_both_orders(self):
  self.chapter();self.setUp();self.chapter(True)
 def test_all_four_personal_trials_and_rehearsal(self):
  self.chapter()
  cases=[(64,105,106,(32,48),(64,120),(120,112)),(67,107,108,(368,208),(400,240),(368,272)),(66,109,110,(48,72),(80,248),(64,288)),(68,111,112,(48,112),(112,112),(160,136))]
  for i,(area,form,cmd,lectern,w1,w2) in enumerate(cases):
   self.entry(area);slot=self.select(form,cmd);self.act(*lectern);self.assertEqual(self.l.get_mode(),3)
   if i==0:self.field(0,64,88);self.field(1,176,88)
   elif i==1:
    self.at(300,208,2);t=self.l.action();self.assertEqual(self.l.hit(0,t,1,0),1);self.act(300,232,f=0);self.assertEqual(self.l.hit(1,t,2,1),1)
   elif i==2:self.field(0,112,248,3);self.act(80,160)
   else:self.act(80,112);self.field(0,48,88,3);self.field(1,128,88,3)
   self.walk(*w1);self.walk(*w2);self.assertEqual(self.l.trial_mask(slot)&1024,1024,i);self.assertGreaterEqual(self.l.level(slot),34);self.assertGreaterEqual(self.l.bond(slot),60);self.assertEqual(self.l.valid(),1)
 def test_four_evolved_exhibits_require_distinct_second_targets(self):
  self.test_all_four_personal_trials_and_rehearsal()
  cases=[(63,105,106,(336,128),(336,104),(336,54,0),(336,112),(400,112)),(67,107,108,(368,208),(300,232),(268,208,3),(400,240),(368,272)),(66,109,110,(48,72),(80,160),(132,256,3),(80,248),(64,288)),(68,111,112,(48,112),(80,112),(64,94,3),(112,112),(160,136))]
  for i,(area,base,cmd,lectern,manual,origin,w1,w2) in enumerate(cases):
   slot=self.select(base,cmd);self.assertEqual(self.l.evolve(slot,base+1),0);self.entry(area);self.select(base+1,cmd+1);self.act(*lectern);self.assertEqual(self.l.get_mode(),4,i);self.act(*manual);self.l.snapshot_state();self.at(*origin);t=self.l.action();self.assertEqual(self.l.hit(0,t,1,0),1);self.assertEqual(self.l.hit(0,t,2,1 if i==1 else 0),0);self.assertEqual(self.l.get_stage(),0);self.assertEqual(self.l.hit(1,t,2,1 if i==1 else 0),1);self.walk(*w1);self.walk(*w2);self.assertEqual(self.l.get_mode(),0);self.assertEqual(self.l.unchanged(),1);self.assertEqual(self.l.valid(),1)
 def first_optional(self,i):
  data={4:(63,(64,64),(80,96),(112,96)),5:(64,(200,112),(176,120),(160,112)),6:(65,(416,256),(384,224),(416,224)),7:(67,(64,192),(48,144),(96,192)),8:(69,(208,112),(48,48),(176,112)),9:(66,(48,208),(48,176),(80,208)),10:(62,(304,272),(304,240),(336,272)),11:(68,(48,112),(80,112),(48,136))}
  area,invite,manual,walk=data[i];self.entry(area)
  if i==6:self.select(3,1)
  elif i==9:self.select(103,104)
  elif i==10:self.select(6,2)
  elif i==11:self.select(9,3)
  self.act(*invite);self.assertEqual(self.l.get_mode(),1,i)
  if i==4:self.act(*manual);self.act(*manual)
  elif i==5:self.act(*manual)
  elif i==6:self.act(*manual);self.field(0,384,280)
  elif i==7:self.act(*manual);self.act(80,144)
  elif i==8:self.act(*manual);self.act(192,32)
  elif i==9:self.act(*manual);self.field(0,48,192)
  elif i==10:self.field(0,320,264)
  elif i==11:self.act(*manual);self.field(0,80,120);self.field(0,80,120,form=101,cmd=102)
  self.walk(*walk);self.assertEqual(self.l.get_stage(),3,i);self.invite(*invite);self.assertEqual(self.l.get_mode(),0,i)
 def test_all_optional_firsts_and_declined_discoveries(self):
  self.chapter();before=self.l.count()
  for i in range(4,12):self.first_optional(i)
  self.assertEqual(self.l.count(),before+8);self.assertEqual(self.l.valid(),1)
 def test_all_twelve_repeats_require_fresh_solution(self):
  self.chapter()
  for i in range(4,12):self.first_optional(i)
  data=[(62,105,106,(352,224),(352,256),(352,176),(384,208)),(63,107,108,(416,96),(416,128),(392,96),(440,96)),(66,109,110,(64,256),(64,224),(48,240),(80,272)),(68,111,112,(192,112),(160,136),(176,112),(216,112)),(63,113,114,(64,64),(80,96),(48,64),(112,96)),(64,114,115,(200,112),(176,120),(200,104),(160,112)),(65,115,116,(416,256),(384,224),(384,256),(416,224)),(67,116,117,(64,192),(48,144),(64,144),(96,192)),(69,117,118,(208,112),(48,48),(192,64),(176,112)),(66,118,119,(48,208),(48,176),(48,160),(80,208)),(62,119,120,(304,272),(304,240),(320,240),(336,272)),(68,120,121,(48,112),(80,112),(80,88),(48,136))]
  for i,(area,form,cmd,invite,manual,target,walk) in enumerate(data):
   self.entry(area);self.select(form,cmd);before=self.l.count();self.act(*invite);self.assertEqual(self.l.get_mode(),2,i)
   if i!=7 and i!=10:self.act(*manual)
   x,y=target
   if i==0:self.field(0,x+32,y,2)
   elif i==1:
    self.at(x+12,y,2);t=self.l.action();self.assertEqual(self.l.hit(0,t,1,0),1);self.assertEqual(self.l.hit(1,t,2,1),1)
   elif i==2:self.field(0,x-24,y,3)
   elif i in (8,9):
    self.at(196 if i==8 else 52,88 if i==8 else 180,1);t=self.l.action();self.assertEqual(self.l.hit(0,t,1,0),1);self.assertEqual(self.l.hit(0,t,2,0),0);self.assertEqual(self.l.get_stage(),0);self.assertEqual(self.l.hit(1,t,2,0),1)
   elif i==7:self.field(0,x,y+24);self.act(*manual)
   else:self.field(0,x,y+24)
   self.walk(*walk);self.assertEqual(self.l.get_stage(),3,i);self.act(*invite);self.l.horizons_game_input(2,0);self.assertEqual(self.l.count(),before);self.act(*invite);self.act(*invite);self.assertEqual(self.l.count(),before+1,i);self.assertEqual(self.l.valid(),1)
   self.act(*invite);self.assertEqual(self.l.count(),before+1);self.assertEqual(self.l.get_stage(),0)
 def test_actor_coordinates_remain_world_space_under_scrolling(self):
  self.intro();self.l.draw(62,120,160);self.assertEqual(self.l.actor_at(352,224),1);self.assertEqual(self.l.actor_at(120,208),1);self.assertEqual(self.l.actor_at(232,64),0)
  self.l.draw(63,240,0);self.assertEqual(self.l.actor_at(416,96),1);self.assertEqual(self.l.actor_at(176,96),0)
  self.l.draw(66,0,160);self.assertEqual(self.l.actor_at(64,256),1);self.assertEqual(self.l.actor_at(64,96),0)
 def test_geometry_collision_and_actor_budget(self):
  self.assertEqual(self.l.collision_equivalence(),0)
  for a in range(62,70):
   for x,y in ((0,0),(240,0),(0,160),(240,160)):
    self.assertLessEqual(self.l.draw(a,x,y),20)
 def test_stale_cast_and_ordinary_selection(self):
  self.intro();self.entry(63);self.entry(64);self.select(105,106);self.at(64,88);t=self.l.action();self.assertEqual(self.l.hit(0,t,1,0),1);self.select(101,102);self.assertEqual(self.l.get_setting(0),1);self.assertEqual(self.l.hit(2,t,1,0),0)
 def test_carriage_reversal_and_occupied_destination(self):
  self.intro();self.entry(63);self.act(136,80);self.act(80,96);self.select(105,106);self.at(224,90,2);self.assertEqual(self.l.synthetic_field(0),1)
  for _ in range(16):self.l.tick()
  self.assertEqual(self.l.get_setting(0),1);self.field(0,192,90,3)
  for _ in range(16):self.l.tick()
  self.assertEqual(self.l.get_setting(0),0)
 def test_recruit_prompt_cancel_leave_and_preflight_abandon(self):
  self.intro();self.select(105,106);self.act(352,224);self.act(352,256);self.field(0,384,176,2);self.walk(384,208);before=self.l.count();self.act(352,224);self.assertNotEqual(self.l.confirmation(),0);self.at(240,240);self.l.tick();self.assertEqual(self.l.confirmation(),0);self.act(352,224);self.assertEqual(self.l.count(),before)
  self.at(352,242);self.assertEqual(self.l.horizons_game_interact(),1);self.l.snapshot_state();self.assertEqual(self.l.horizons_game_prepare_event(),1);self.l.horizons_game_menu_abandoned();self.assertEqual(self.l.unchanged(),1);self.assertEqual(self.l.count(),before);self.assertEqual(self.l.get_mode(),0)
 def test_reset_reconstructs_committed_work_and_closes_prompts(self):
  self.intro();self.entry(63);self.act(136,80);self.act(80,96);self.select(105,106);self.field(0,224,90,2)
  for _ in range(16):self.l.tick()
  self.assertEqual(self.l.get_setting(0),1);self.act(24,132,f=0);self.l.horizons_game_input(2,0);self.assertEqual(self.l.get_setting(0),1);self.act(24,132,f=0);self.act(24,132,f=0);self.assertEqual(self.l.get_setting(0),0)
  self.act(80,96);self.field(0,224,90,2)
  for _ in range(16):self.l.tick()
  self.field(0,256,90,2)
  for _ in range(16):self.l.tick()
  self.walk(256,128);self.act(24,132,f=0);self.act(24,132,f=0);self.assertEqual(self.l.get_setting(0),2);self.assertEqual(self.l.qo(55)&2,2)
 def test_trial_selection_edit_revokes_owner_and_pending_floor(self):
  self.intro();self.entry(63);self.entry(64);slot=self.select(105,106);self.act(32,48);self.field(0,64,88);self.field(1,176,88);self.walk(64,120);self.select(101,102);self.assertEqual(self.l.get_mode(),0);self.walk(120,112);self.assertEqual(self.l.trial_mask(slot)&1024,0)
 def test_direction_uses_bound_effect_snapshot_not_mutable_player_face(self):
  self.intro();self.entry(63);self.act(136,80);self.act(80,96);self.select(105,106);self.at(224,90,1);t=self.l.action();self.l.aim_effect(2);self.at(224,90,3);self.assertEqual(self.l.hit(0,t,1,0),1)
  for _ in range(16):self.l.tick()
  self.assertEqual(self.l.get_setting(0),1);self.at(256,90,1);t=self.l.action();self.at(256,90,2);self.assertEqual(self.l.hit(0,t,1,0),2);self.assertEqual(self.l.get_setting(0),1)
  self.at(256,90,1);t=self.l.action();self.l.aim_effect(2);self.l.corrupt_effect_origin();self.assertEqual(self.l.hit(0,t,1,0),0)
 def test_press_moves_only_one_notch_per_cast(self):
  self.intro();self.entry(63);self.entry(65);self.act(96,176);self.act(336,208);self.field(0,336,192,1,103,104);self.entry(66);self.select(105,106);self.at(170,248,2);t=self.l.action();self.assertEqual(self.l.hit(0,t,1,0),1);self.assertEqual(self.l.get_setting(0),1);self.assertEqual(self.l.hit(0,t,2,0),0);self.assertEqual(self.l.get_setting(0),1)
 def test_same_cast_wax_rejects_new_cast(self):
  self.intro();self.stage();self.water();self.entry(67);self.field(0,48,224,3,109,110);self.act(352,224);self.select(107,108);self.at(300,208,2);t=self.l.action();self.assertEqual(self.l.hit(1,t,1,0),1);u=self.l.action();self.assertEqual(self.l.hit(2,u,2,1),2);self.assertEqual(self.l.qo(57),1);self.assertEqual(self.l.hit(2,t,2,1),0)
if __name__=='__main__':unittest.main()
