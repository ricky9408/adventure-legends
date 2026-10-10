#!/usr/bin/env python3
"""Real world/jobs/save policy with synthetic host input and field-hit callbacks.
Geometry and causality tests, not controller-earned/native cast acceptance.
"""
from pathlib import Path
import ctypes as C,json,subprocess,tempfile,unittest,random,sys
from return_host_support import Save,Instance,Roster,TRIALS
ROOT=Path(__file__).resolve().parents[1]
class World(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='return-world-');cls.addClassCleanup(cls.tmp.cleanup)
  sources=['tests/return_world_host.c']+['src/'+s+'.c'for s in ['return_art','return_quests','save4','save5','creatures','creature_data','equipment','equipment_data','progression_events']]
  p=Path(cls.tmp.name)/'world.so';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-fPIC','-shared','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-Isrc',*sources,'-o',str(p)],cwd=ROOT,check=True);cls.l=C.CDLL(str(p));cls.sram=(C.c_ubyte*32768).in_dll(cls.l,'save5_test_sram');cls.s=Save.in_dll(cls.l,'adventure_save');cls.geom=json.loads((ROOT/'assets/return_region/geometry.json').read_text())['rooms']
 def setUp(self):self.load('underwater-all89-town.sav')
 def load(self,name):self.sram[:]=(ROOT/'tests/fixtures/v5-revision6'/name).read_bytes();self.assertEqual(self.l.fresh(),1)
 def at(self,x,y,f=1):self.l.at(x,y,f);self.assertFalse(self.l.return_game_solid(x,y))
 def old(self,room,spawn=0):self.l.old_room(room,spawn)
 def act(self,x,y,old=False,f=1):
  dx,dy={1:(0,18),0:(0,-18),2:(18,0),3:(-18,0)}[f];self.at(x+dx,y+dy,f);self.assertEqual((self.l.return_game_old_interact if old else self.l.return_game_interact)(),1,(C.c_int.in_dll(self.l,'room').value,x,y,self.l.get_toast()));self.assertEqual(self.l.settle(),1,(x,y,self.l.get_toast()))
 def entry(self,a,s=0):self.assertEqual(self.l.entry(a,s),1,a);self.assertFalse(self.l.return_game_solid(C.c_int.in_dll(self.l,'px').value,C.c_int.in_dll(self.l,'py').value))
 def field(self,index,form=None,command=None,want=1):
  if form:self.assertLess(self.l.select_form(form,command),160)
  x=C.c_int();y=C.c_int();self.assertEqual(self.l.return_game_field_target(index,C.byref(x),C.byref(y),None),1)
  self.at(x.value,y.value+24);self.assertEqual(self.l.synthetic_field(index),want,(C.c_int.in_dll(self.l,'room').value,index,self.l.get_toast()));self.assertEqual(self.l.settle(),1)
 def intro(self):
  self.old(46);self.act(200,272,True);self.old(0);self.act(152,112,True);self.assertEqual(self.l.qs(46),3);self.entry(54)
 def north(self):
  self.old(16);self.act(368,152,True,f=2);self.entry(55);self.act(64,112);self.act(176,112);self.old(16);self.act(368,152,True,f=2);self.act(368,152,True,f=2);self.assertEqual(self.l.qs(47),3);self.entry(57);self.field(0,101,102);self.act(352,272);self.field(1,7 if any(c.form_id==7 for c in self.s.roster.instances) else 8,3);self.old(22);self.act(192,192,True);self.assertEqual(self.l.qs(48),3)
 def south(self):
  self.entry(58);self.act(80,80);self.act(160,80);self.act(128,144);self.old(30);self.act(448,192,True);self.act(448,192,True);self.assertEqual(self.l.qs(49),3);self.entry(59);self.act(120,104);self.field(0,103,104);self.entry(56);self.act(288,256);self.field(0,103,104);self.field(1);self.old(16);self.act(112,144,True);self.assertEqual(self.l.qs(50),3)
 def finale(self):
  self.entry(60);self.act(120,104)
  for i,f,c in [(0,4,2),(1,1,1),(2,10,4),(3,101,102),(4,103,104)]:
   if not any(v.form_id==f for v in self.s.roster.instances):f+=1
   self.field(i,f,c)
  self.assertEqual(self.l.phase(),5);self.entry(61);self.field(0,101,102);self.field(1,103,104);self.old(0);self.act(152,112,True);self.assertEqual(self.l.qs(51),3);self.assertEqual(self.l.valid(),1)
 def chapter(self):self.intro();self.north();self.south();self.finale()
 def test_main_both_arm_orders(self):
  self.chapter();self.setUp();self.intro();self.south();self.north();self.finale()
 def test_minimal_route_both_orders_no_evolution_or_new_gear(self):
  for reverse in [False,True]:
   self.load('underwater-minimal12-town.sav');old=[(c.instance_id,c.form_id)for c in self.s.roster.instances if c.form_id];self.intro()
   if reverse:self.south();self.north()
   else:self.north();self.south()
   self.finale();self.assertEqual([(c.instance_id,c.form_id)for c in self.s.roster.instances if c.form_id][:len(old)],old);self.assertEqual(self.l.count(),14)
 def test_all_side_quests_and_five_gear_sources(self):
  self.chapter();self.old(22);self.act(352,176,True);self.entry(57);self.act(304,272);self.field(2,2,1);self.old(16);self.act(112,144,True);self.assertEqual(self.l.qs(52),3)
  self.entry(54);self.field(0,5,2);self.field(1,2,1);self.act(240,240);self.entry(56);self.act(432,256);self.entry(57);self.act(432,272);self.entry(58);self.act(240,240);self.old(30);self.act(448,192,True);self.assertEqual(self.l.qs(53),3)
  self.assertEqual(self.l.valid(),1)
 def test_trial_rejects_wrong_side_stale_selection_and_menu(self):
  self.chapter();self.entry(54);slot=self.l.select_form(2,1);self.act(48,144);self.act(96,144);self.at(64,56,0);self.assertEqual(self.l.synthetic_field(0),2);self.assertEqual(self.l.trial_stage(),0);self.assertEqual(self.l.trial_mask(slot)&1024,0)
  self.field(0);self.assertEqual(self.l.trial_stage(),1);self.l.return_game_menu_abandoned();self.assertEqual(self.l.trial_index(),255);self.assertEqual(self.l.trial_mask(slot)&1024,0)
  self.act(48,144);self.act(96,144);self.field(0);self.l.select_form(5,2);self.assertEqual(self.l.trial_index(),255);self.assertEqual(self.l.trial_mask(slot)&1024,0)
 def test_all_geometry_pixels_and_rect_ray_certificates(self):
  self.assertEqual(self.l.collision_equivalence(),0);R=random.Random(174)
  for r in self.geom:
   self.old(r['id'])
   for mask in range(8):
    self.l.mask_setting(mask)
    for _ in range(200):
     x=R.randrange(r['width']);y=R.randrange(r['height']);tx=max(0,min(r['width']-1,x+R.randrange(-50,51)));ty=max(0,min(r['height']-1,y+R.randrange(-50,51)))
     self.assertEqual(self.l.return_game_supercover(x,y,tx,ty),self.l.reference_ray(x,y,tx,ty),(r['id'],mask,x,y,tx,ty))
     x0,x1=sorted([x,tx]);y0,y1=sorted([y,ty]);want=not any(self.l.return_game_solid(xx,yy)for yy in range(y0,y1+1)for xx in range(x0,x1+1))
     self.assertEqual(self.l.return_game_clear_box(x0,y0,x1,y1),want)
 def test_dynamic_refuses_hero_overlap_and_visible_change(self):
  self.intro();self.entry(55);self.at(92,68);self.assertEqual(self.l.set_one(0,1),0);self.at(64,130);self.assertEqual(self.l.set_one(0,1),1);self.assertTrue(self.l.return_game_solid(92,68));self.assertFalse(self.l.return_game_solid(104,92))
 def test_all_trials_and_sequential_f6(self):
  self.chapter()
  for i,t in enumerate(TRIALS):
   self.entry(t['area']);slot=self.l.select_form(t['from_form'],t['allowed_predecessor_commands'][0]);self.assertLess(slot,160)
   work=next(w for r in self.geom for w in r['trial_workspaces']if w['index']==i);self.act(*work['lectern']);self.assertEqual(self.l.trial_index(),i,(i,self.l.get_toast()))
   def manual():self.act(*work['manual'][0])
   def walk():self.at(*work['walk'][0]);self.l.tick();self.assertEqual(self.l.settle(),1)
   if i in (0,2,3,4,5,6,8,9,10,12):manual()
   if i in (0,5,6,8,10):
    for n in range(3 if i==5 else 2):self.field(n)
   elif i==1:self.field(0);self.field(1);manual();walk()
   elif i in (2,3,4,12):self.field(0);walk();self.field(1)
   elif i==7:self.field(0);manual();walk();self.field(1)
   elif i==9:self.field(0);self.field(1);manual();walk()
   elif i==11:self.field(0);self.field(1);walk();self.field(2)
   self.assertEqual(self.l.trial_mask(slot)&t['wire_mask'],t['wire_mask'],i);self.assertGreaterEqual(self.l.level(slot),t['level_floor']);self.assertGreaterEqual(self.l.bond(slot),t['bond_floor']);self.assertEqual(self.l.evolve(slot,t['to_form']),0);self.assertEqual(self.l.valid(),1)
  # All15 new signatures retain an actual tagged field role after the story.
  roles=[(3,91,54,2),(6,92,54,3),(9,93,57,1),(12,94,60,2),(15,95,56,2),(17,96,55,0),(18,97,55,1),(21,98,56,3),(24,99,57,3),(27,100,58,0),(30,101,58,1),(102,102,57,0),(102,103,55,0),(104,104,59,0),(104,105,58,2)]
  for f,cmd,area,target in roles:
   if f==17:f=18 # Sequential family retains its learned previous signature96
   self.entry(area)
   if area==57 and target==1:self.act(352,272)
   if area==59:self.act(120,104)
   self.field(target,f,cmd)
 def test_every_trial_lifecycle_wrong_order_selection_party_reset_and_replay(self):
  self.chapter()
  for i,t in enumerate(TRIALS):
   work=next(w for r in self.geom for w in r['trial_workspaces']if w['index']==i)
   def start():
    self.entry(t['area']);slot=self.l.select_form(t['from_form'],t['allowed_predecessor_commands'][0]);self.assertLess(slot,160);self.act(*work['lectern']);self.assertEqual(self.l.trial_index(),i);return slot
   def manual():self.act(*work['manual'][0])
   def walk():self.at(*work['walk'][0]);self.l.tick();self.assertEqual(self.l.settle(),1)
   def solve():
    if i in (0,2,3,4,5,6,8,9,10,12):manual()
    if i in (0,5,6,8,10):
     for n in range(3 if i==5 else 2):self.field(n)
    elif i==1:self.field(0);self.field(1);manual();walk()
    elif i in (2,3,4,12):self.field(0);walk();self.field(1)
    elif i==7:self.field(0);manual();walk();self.field(1)
    elif i==9:self.field(0);self.field(1);manual();walk()
    elif i==11:self.field(0);self.field(1);walk();self.field(2)
   slot=start();before=bytes(self.s);x,y=work['targets'][0];self.at(x,y-12,0);self.assertEqual(self.l.synthetic_field(0),2);self.assertEqual(bytes(self.s),before)
   self.field(len(work['targets'])-1,want=2);self.assertEqual(bytes(self.s),before)
   self.l.return_game_menu_abandoned();self.assertEqual(self.l.trial_index(),255);self.assertEqual(bytes(self.s),before)
   slot=start();a,b=self.s.roster.party[0],self.s.roster.party[1];self.s.roster.party[0]=b;self.s.roster.party[1]=a;self.l.tick();self.assertEqual(self.l.trial_index(),255);self.s.roster.party[0]=a;self.s.roster.party[1]=b
   slot=start();self.l.return_game_reset();self.assertEqual(self.l.trial_index(),255);self.assertEqual(self.l.trial_mask(slot)&t['wire_mask'],0)
   slot=start();solve();self.assertEqual(self.l.trial_mask(slot)&t['wire_mask'],t['wire_mask']);earned=bytes(self.s)
   self.act(*work['lectern']);self.assertEqual(self.l.trial_index(),i);solve();self.assertEqual(bytes(self.s),earned,('rehearsal mutated',i));self.assertEqual(self.l.evolve(slot,t['to_form']),0)
 def test_read_only_journal_picker_preserve_personal_proof_and_real_edit_invalidates(self):
  self.chapter();self.entry(54);slot=self.l.select_form(2,1);self.act(48,144);self.act(96,144);self.field(0)
  before=bytes(self.s);proof=(self.l.trial_index(),self.l.trial_stage(),self.l.trial_casts(),self.l.attempt_id(),self.l.room_scene())
  for mode in (0,1,0,1):
   self.l.view_roundtrip(mode);self.assertEqual(bytes(self.s),before);self.assertEqual((self.l.trial_index(),self.l.trial_stage(),self.l.trial_casts(),self.l.attempt_id(),self.l.room_scene()),proof)
  self.field(1);self.assertEqual(self.l.trial_mask(slot)&1024,1024)
  self.act(48,144);self.act(96,144);self.field(0);self.l.select_form(5,2);self.l.select_form(2,1);self.assertEqual(self.l.trial_index(),255)
  self.act(48,144);self.act(96,144);self.field(0);self.l.select_form(2,5);self.l.select_form(2,1);self.assertEqual(self.l.trial_index(),255)
 def test_repeat_walkaway_unrelated_a_and_read_only_modals_require_new_confirmation(self):
  self.chapter()
  for area,form,cmd,invite,manuals,walk in [(55,101,102,(208,80),[(64,112),(176,112)],(208,112)),(58,103,104,(400,240),[(368,272)],(400,272))]:
   self.entry(area);self.l.select_form(form,cmd);self.act(*invite)
   self.l.select_form(2,1);self.l.select_form(form,cmd);self.assertEqual(self.l.repeat_source(),0);self.act(*invite)
   for p in manuals:self.act(*p)
   self.field(0);self.at(*walk);self.l.tick();self.assertEqual(self.l.repeat_status(),2)
   before=bytes(self.s);attempt=self.l.attempt_id();n=self.l.count();source=self.l.repeat_source()
   for mode in (0,1):
    self.l.view_roundtrip(mode);self.assertEqual(bytes(self.s),before);self.assertEqual((self.l.repeat_status(),self.l.attempt_id(),self.l.repeat_source()),(2,attempt,source))
   self.act(*invite);self.assertEqual(self.l.confirmation(),1)
   # Merely facing away cancels the prompt, while the solved attempt survives.
   self.at(invite[0],invite[1]+18,0);self.l.tick();self.assertEqual(self.l.confirmation(),0);self.assertEqual(self.l.repeat_status(),2);self.assertEqual(self.l.attempt_id(),attempt)
   # An unrelated A on empty safe floor cannot grant, even if the input hook
   # was not called; interact() independently scopes the pending prompt.
   self.at(120 if area==55 else 240,140 if area==55 else 288);self.assertEqual(self.l.return_game_interact(),0);self.assertEqual(self.l.count(),n)
   self.act(*invite);self.assertEqual(self.l.confirmation(),1);self.assertEqual(self.l.count(),n)
   for mode in (0,1):self.l.view_roundtrip(mode);self.assertEqual(self.l.confirmation(),1)
   # Walk away while a prompt exists, invoke input rather than tick, then return.
   self.at(120 if area==55 else 240,140 if area==55 else 288);self.l.return_game_input(0,0);self.assertEqual(self.l.confirmation(),0);self.assertEqual(self.l.repeat_status(),2)
   self.act(*invite);self.assertEqual(self.l.count(),n);self.assertEqual(self.l.confirmation(),1)
   self.l.return_game_input(2,0);self.assertEqual(self.l.confirmation(),0);self.assertEqual(self.l.repeat_status(),2)
   self.act(*invite);self.assertEqual(self.l.count(),n);self.act(*invite);self.assertEqual(self.l.count(),n+1)
   self.act(*invite);self.assertEqual(self.l.count(),n+1);self.assertEqual(self.l.valid(),1)
 def test_repeats_solved_consumed_once_and_cancel(self):
  self.chapter()
  for area,form,cmd,invite,manuals,target,walk in [(55,101,102,(208,80),[(64,112),(176,112)],0,(208,112)),(58,103,104,(400,240),[(368,272)],0,(400,272))]:
   self.entry(area);self.l.select_form(form,cmd);self.act(*invite)
   for p in manuals:self.act(*p)
   self.field(target);self.at(*walk);self.l.tick();self.assertEqual(self.l.repeat_status(),2);n=self.l.count();self.act(*invite);self.l.return_game_input(2,0);self.assertEqual(self.l.count(),n);self.act(*invite);self.act(*invite);self.assertEqual(self.l.count(),n+1);self.act(*invite);self.assertEqual(self.l.count(),n+1);self.assertEqual(self.l.valid(),1)
if __name__=='__main__':unittest.main()
