#!/usr/bin/env python3
"""Production Magma runtime host checks. Warped approach tests are synthetic,
not native controller acquisition, performance, or a hardware claim."""
from pathlib import Path
import ctypes as C,json,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
TMP=tempfile.TemporaryDirectory(prefix='magma-runtime-');OUT=Path(TMP.name)
UI=json.loads((ROOT/'assets/magma_region/dialogue.json').read_text());IDS={'TX_'+k:3000+i for i,k in enumerate(UI)}
(OUT/'magma_game_test_ui.h').write_text('enum{'+','.join(k+'='+str(v)for k,v in IDS.items())+'};\n')
sources=['src/magma_game.c','src/magma_art.c','src/magma_quests.c','src/southern_quests.c','src/northern_quests.c','src/save5.c','src/save4.c','src/equipment.c','src/equipment_data.c','src/creatures.c','src/creature_data.c']
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC','-DMAGMA_GAME_HOST_TEST','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST','-Isrc','-I'+str(OUT),'tests/magma_game_host.c',*sources,'-Wl,--wrap=magma_anchor','-o',str(OUT/'test.so')],cwd=ROOT,check=True)
L=C.CDLL(str(OUT/'test.so'))
class Puzzle(C.Structure):_fields_=[('cell',C.c_ubyte*2),('heat',C.c_ubyte),('brace',C.c_ubyte)]
SRAM=(C.c_ubyte*32768).in_dll(L,'save5_test_sram')
FIXTURE=(ROOT/'tests/fixtures/v5-revision4/southern-minimal8-town.sav').read_bytes()
def v(n):return C.c_int.in_dll(L,n).value
def b(n):return C.c_ubyte.in_dll(L,n).value
def p():return Puzzle.in_dll(L,'magma_game_puzzle')
def pos(i):return 48+p().cell[i]%7*24,32+p().cell[i]//7*18
def toast():return next((k for k,x in IDS.items()if x==L.get_toast()),str(L.get_toast()))
class MagmaRuntime(unittest.TestCase):
 def setUp(self):SRAM[:]=FIXTURE;self.assertEqual(L.fresh(),1);L.set_actor_overlap(0)
 def entry(self,r,s=0):self.assertEqual(L.entry(r,s),1);self.assertLessEqual(L.max_camera_actors()+3,20,r)
 def at(self,x,y,face=1):L.at(x,y);L.facing(face);self.assertFalse(L.magma_game_solid(x,y),(v('room'),x,y))
 def act(self,x,y,face=1):self.at(x,y,face);self.assertIn(L.magma_game_interact(),(1,3),(v('room'),x,y,toast()))
 def target(self,x,y,face=1):
  dx,dy={0:(0,-16),1:(0,16),2:(16,0),3:(-16,0)}[face];self.act(x+dx,y+dy,face)
 def power(self,x,y,form=None,face=1,want=1):
  if form:self.assertLess(L.select_form(form),160)
  dx,dy={0:(0,-16),1:(0,16),2:(16,0),3:(-16,0)}[face];self.at(x+dx,y+dy,face);self.assertEqual(L.magma_game_power(0xffffffff),want,(v('room'),x,y,form,toast()))
 def slide(self,i,dirs,side=1):
  x,y=pos(i);dx,dy={0:(0,-16),1:(0,16),2:(16,0),3:(-16,0)}[side];self.act(x+dx,y+dy,side);self.assertTrue(L.magma_game_grabbed(),(v('room'),i,x,y,toast()))
  for d in dirs:
   before=bytes(p());self.assertEqual(L.magma_game_input(d,0),1);self.assertNotEqual(bytes(p()),before,(v('room'),i,d,toast()))
  L.magma_game_input(1,0)
 def guarantees(self):
  self.entry(38);self.target(160,176);self.target(144,232);self.assertTrue(L.magma_game_grabbed());L.magma_game_input(16,0);L.magma_game_input(16,0);L.magma_game_input(1,0);self.assertEqual(L.qo(30),1);self.target(224,208);self.target(160,176);self.assertEqual(L.qs(30),3,toast())
  self.entry(39);self.target(192,192);self.target(240,192);self.target(288,192);self.assertEqual(L.qs(31),3,toast());self.assertEqual(L.valid(),1)
 def main_to44(self):
  self.guarantees();self.entry(42);self.power(48,68,34,want=2);self.power(48,68,31,face=3);self.slide(0,[128,128]+[16]*6+[64,64]);self.assertEqual(L.qo(32),1,toast());self.entry(43);self.slide(0,[128,16,16],side=2);self.slide(0,[64]*4);self.slide(1,[32,64]);self.power(168,104,34);self.assertEqual(L.qo(32),3,toast());self.entry(44)
 def main(self):
  self.main_to44();self.power(48,68,31,face=3);self.slide(0,[128,128]+[16]*6+[64,64]);self.slide(1,[32]+[64]*3,side=2);self.power(168,104,34);self.at(208,104,2);L.weapon(1);self.assertEqual(L.magma_game_weapon_hit(1,192,104,16,0,L.magma_game_action_begin(0)),1);self.assertEqual(L.qo(32),7);self.entry(45);self.target(120,112);self.at(24,136);L.tick(96);self.assertEqual(b('magma_game_machine_stage'),3);self.target(32,80);self.at(120,88);token=L.magma_game_action_begin(0);self.assertEqual(L.magma_game_weapon_hit(1,120,64,192,0,token),1);self.assertEqual(L.qo(32),15);self.entry(38);self.target(160,176);self.assertEqual(L.qs(32),3);self.assertEqual(L.invalid_saves(),0);self.assertEqual(L.roundtrip(),1)
 def optional(self):
  self.main();self.entry(40)
  self.target(48,64)
  # Round/thick: low+closed, triangle/thin: high+closed, square/decorated: wide+open.
  self.target(168,64);self.target(88,64);self.target(168,64);self.target(88,64);self.target(128,64);self.target(168,64);self.target(208,80)
  self.target(144,96);self.target(176,96);self.target(192,112);self.target(56,112);self.target(88,112);self.target(120,112)
  self.entry(38);self.target(384,208);self.entry(40);self.target(48,96);self.target(80,96);self.target(112,96);self.entry(38);self.target(384,176)
  self.entry(39);self.target(72,208);self.target(104,208);self.target(392,208);self.target(424,208);self.target(272,96);self.target(304,96);self.target(304,96)
  self.target(128,264);L.magma_game_input(16,0);L.magma_game_input(16,0);L.magma_game_input(1,0);self.target(104,112);self.target(136,216)
  self.target(368,264);self.entry(44);self.target(72,112);self.entry(39);self.target(336,240);self.target(304,232)
  self.entry(41);self.target(48,64);self.target(80,64);self.target(112,64);self.target(144,64);self.target(208,80);self.target(48,96);self.target(80,96);self.target(144,96);self.target(176,96);self.target(192,112)
  self.assertEqual(L.flags(9),127)
  for q in range(33,38):self.assertEqual(L.qs(q),3,(q,toast()))
  self.assertEqual(L.valid(),1);self.assertEqual(L.invalid_saves(),0)
 def test_real_module_minimal_guaranteed_route(self):self.main()
 def test_all_seven_invitations_and_six_optional_stories(self):self.optional();self.assertEqual(L.roundtrip(),1)
 def test_static_engine_collision_and_spawns(self):
  self.assertEqual(L.collision_equivalence(),0)
  for a in range(38,46):self.assertIn(L.encounter_spawns(a),(0,1,2,5))
 def test_grab_blocks_live_actor_modal_and_resets(self):
  self.guarantees();self.entry(42);self.target(48,68,3);old=bytes(p());L.set_actor_overlap(1);L.magma_game_input(128,0);self.assertEqual(bytes(p()),old);L.set_actor_overlap(0);L.modal(3);self.assertEqual(L.magma_game_input(128,0),0);self.assertEqual(L.magma_game_interact(),0);self.assertEqual(L.magma_game_power(43),0);L.modal(1);L.magma_game_input(128,0);self.assertNotEqual(bytes(p()),old);L.magma_game_reset();self.assertEqual(bytes(p()),old)
 def test_boss_all_weapons_and_once_per_action(self):
  for weapon in (1,2,3):
   self.setUp();self.main_to44();self.power(48,68,31,face=3);self.slide(0,[128,128]+[16]*6+[64,64]);self.slide(1,[32]+[64]*3,side=2);self.power(168,104,34);self.at(208,104,2);L.weapon(weapon);self.assertEqual(L.magma_game_weapon_hit(weapon,192,104,16,0,L.magma_game_action_begin(0)),1);self.entry(45);self.target(120,112);self.at(24,136);token=L.magma_game_action_begin(0);self.assertEqual(L.magma_game_weapon_hit(weapon,120,64,16,0,token),0);L.tick(96);self.target(32,80);self.at(120,88);self.assertEqual(L.magma_game_weapon_hit(weapon,120,64,16,0,token),1);self.assertEqual(L.magma_game_weapon_hit(weapon,120,64,16,0,token),0);self.assertEqual(b('magma_game_machine_hp'),176);cast=L.magma_game_action_begin(3);self.assertEqual(L.magma_game_command_hit(120,64,16,cast),1);L.magma_game_action_begin(1);self.assertEqual(L.magma_game_command_hit(120,64,16,cast),0);L.modal(3);ticks=b('magma_game_machine_ticks');L.tick(500);self.assertEqual(b('magma_game_machine_ticks'),ticks)
 def start_trial(self,form,area,key=1):
  self.entry(area);slot=L.select_form(form);self.assertLess(slot,160)
  xy={38:((432,280),(400,280)),39:((208,248),(272,248))}.get(area,((24,112),(216,112)))[key-1]
  self.target(*xy);return slot
 def teaching_trial0(self):
  slot=self.start_trial(31,38);self.power(144,232);self.target(144,232);L.magma_game_input(16,0);L.magma_game_input(16,0);L.magma_game_input(1,0)
  self.entry(40);self.power(48,86,face=3);self.slide(0,[16,16]);self.entry(42);self.power(48,68,face=3);self.slide(0,[128,128]+[16]*6+[64,64]);self.assertEqual(L.trial(slot),1,toast());return slot
 def teaching_trial2(self):
  slot=self.start_trial(34,39);self.power(176,128);self.power(272,128);self.entry(43);self.slide(0,[128,16,16],side=2);self.slide(0,[64]*4);self.slide(1,[32,64]);self.power(168,104);self.assertEqual(L.trial(slot),1,toast());return slot
 def test_all_fifteen_same_instance_trials_and_tiers(self):
  self.optional();s=self.teaching_trial0();self.assertEqual(L.evolve(s,32),0);s=self.start_trial(32,40,2)
  self.power(48,86,face=3);self.slide(0,[16,16]);self.slide(0,[16,16]);self.target(144,112);self.slide(0,[32]*4);self.power(48,86,face=3);self.slide(0,[16]*5);self.slide(0,[32]);self.target(144,112);self.slide(0,[32]*4);self.power(48,86,face=3);self.slide(0,[16]*6);self.entry(44);self.target(72,112);self.assertEqual(L.trial(s),3,toast());self.assertEqual(L.evolve(s,33),0)
  s=self.teaching_trial2();self.assertEqual(L.evolve(s,35),0);s=self.start_trial(35,39,2);self.power(320,112);self.power(320,264,face=0);self.entry(44);self.slide(0,[128,128]+[16]*6+[64,64]);self.slide(1,[32]+[64]*3,side=2);self.power(48,104,face=3);self.assertEqual(L.trial(s),3,toast());self.assertEqual(L.evolve(s,36),0)
  s=self.start_trial(37,39);self.power(72,176,face=0);self.power(104,176,face=0);self.assertEqual(L.trial(s),1,toast());s=self.start_trial(37,39,2);self.target(392,208);self.power(328,128);self.power(360,128);self.target(336,240);self.entry(40);self.target(168,64);self.assertEqual(L.trial(s),3,toast())
  s=self.start_trial(40,41);self.power(48,64);self.power(112,64);self.target(80,96);self.target(144,96);self.target(176,96);self.assertEqual(L.trial(s),1,toast());s=self.start_trial(40,39,2);self.power(272,128);self.entry(41);self.power(48,64);self.entry(39);self.power(304,128);self.entry(41);self.power(112,64);self.assertEqual(L.trial(s),3,toast())
  s=self.start_trial(43,40);self.target(128,64);self.power(144,96,face=2);self.power(176,96,face=2);self.entry(41);self.power(176,96,face=2);self.assertEqual(L.trial(s),1,toast());s=self.start_trial(43,40,2);self.power(80,96,face=2);self.power(112,96,face=3);self.target(48,96);self.assertEqual(L.trial(s),3,toast())
  s=self.start_trial(46,39);self.power(392,208);self.power(424,240);self.entry(44);self.power(72,112);self.assertEqual(L.trial(s),1,toast());s=self.start_trial(46,39,2);self.power(392,208);self.target(424,240);self.entry(40);self.power(128,64);self.assertEqual(L.trial(s),3,toast())
  s=self.start_trial(95,39);self.target(272,96);self.power(304,96);self.target(128,112);self.power(160,112);self.entry(41);self.target(48,64);self.power(80,64);self.assertEqual(L.trial(s),1,toast())
  s=self.start_trial(97,40);self.target(128,64);self.power(56,112);self.power(88,112);self.entry(44);self.power(48,104,face=3);self.assertEqual(L.trial(s),1,toast())
  s=self.start_trial(99,41);self.target(80,96);self.target(144,96);self.entry(38);self.power(288,248);self.entry(41);self.power(112,64);self.power(176,96);self.assertEqual(L.trial(s),1,toast());self.assertEqual(L.invalid_saves(),0);self.assertEqual(L.roundtrip(),1)
 def test_trial_partial_cannot_transfer_and_restart_death_clear(self):
  self.optional();slot=self.start_trial(40,39,2);self.power(272,128);copy=L.duplicate(40);self.assertLess(copy,160);L.select_slot(copy);self.entry(41);self.power(48,64,want=2);self.assertEqual(toast(),'TX_MG_SAME');self.assertEqual(L.trial(copy),0);L.select_slot(slot);self.power(48,64);L.magma_game_reset();self.entry(39);self.power(304,128,want=0);self.assertEqual(L.trial(slot),0)
 def test_four_repeat_sources_real_individuals_no_event_farming(self):
  self.optional()
  for form,area,point in [(37,39,(80,232)),(40,41,(176,64)),(43,40,(160,112)),(46,39,(424,240))]:
   slot=self.start_trial(form,area)
   if form==37:self.power(72,176,face=0);self.power(104,176,face=0)
   elif form==40:self.power(48,64);self.power(112,64);self.target(80,96);self.target(144,96);self.target(176,96)
   elif form==43:self.target(128,64);self.power(144,96,face=2);self.power(176,96,face=2);self.entry(41);self.power(176,96,face=2)
   else:self.power(392,208);self.power(424,240);self.entry(44);self.power(72,112)
   self.assertEqual(L.evolve(slot,form+1),0);L.magma_game_reset();self.entry(area);count=L.roster_count();digest=L.roster_event_digest();self.target(*point);self.target(*point);self.assertEqual(L.roster_count(),count+1);self.assertEqual(L.roster_event_digest(),digest);self.target(*point);self.assertEqual(L.roster_count(),count+1);self.target(*point);self.assertEqual(L.roster_count(),count+2);self.assertEqual(L.roster_event_digest(),digest)
  self.assertEqual(L.flags(16),15);self.assertEqual(L.roundtrip(),1)
 def test_capacity_refusal_keeps_source_and_missing_branch_still_fits(self):
  self.optional();s=self.start_trial(37,39);self.power(72,176,face=0);self.power(104,176,face=0);self.assertEqual(L.evolve(s,38),0);L.magma_game_reset();self.entry(39);self.target(80,232);self.target(80,232)
  s=self.start_trial(37,39);self.power(72,176,face=0);self.power(104,176,face=0);self.assertEqual(L.evolve(s,38),0);L.magma_game_reset();self.entry(39);L.fill_reserved();self.assertEqual(L.excess(),88);self.assertEqual(L.valid(),1)
  n=L.roster_count();self.target(80,232);self.target(80,232);self.assertEqual(L.roster_count(),n+1);self.assertEqual(L.excess(),88);self.target(80,232);L.snapshot_state();self.target(80,232);self.assertEqual(L.unchanged(),1);self.assertEqual(toast(),'TX_MG_CHANGED')
  # Dialogue captures a refusal without replacing or erasing an instance.
  self.assertEqual(L.roster_count(),n+1);self.assertEqual(L.valid(),1);L.fill_historical_full();self.assertEqual(L.roster_count(),160);L.snapshot_state();self.target(80,232);self.assertEqual(L.unchanged(),1);self.assertEqual(L.roundtrip(),1)
 def test_diversion_waits_for_successful_window_without_speed_gate(self):
  self.main();self.entry(45);L.magma_game_reset()
  # Fresh test encounter: explicit fixture supplies unfinished boss stage only.
  C.c_ubyte.in_dll(L,'magma_game_machine_stage').value=0;C.c_ubyte.in_dll(L,'magma_game_machine_hp').value=192
  self.target(120,112);self.target(32,80);self.at(24,136);L.tick(216*3+96);self.assertEqual(b('magma_game_machine_stage'),3);self.assertEqual(L.magma_game_target(0,0,0),1)
  token=L.magma_game_action_begin(0);self.assertEqual(L.magma_game_weapon_hit(1,120,64,16,0,token),1);L.tick(120+96);self.assertEqual(b('magma_game_machine_stage'),3);self.assertEqual(L.magma_game_target(0,0,0),0)
 def test_every_damaging_sweep_position_invalidates_bitmap_cache(self):
  self.main();self.entry(45)
  # Seed each remaining stage2 clock independently, so the one-hit-per-sweep
  # guard is fresh. The rect probe observes production overlay draw calls.
  for remaining in range(36,0,-1):
   L.magma_game_reset();C.c_ubyte.in_dll(L,'magma_game_machine_stage').value=2;C.c_ubyte.in_dll(L,'magma_game_machine_ticks').value=remaining;C.c_ubyte.in_dll(L,'magma_game_machine_hp').value=192
   expected_x=48+(37-remaining)*4;self.at(expected_x+6,85);revision=v('magma_game_revision');hurt=L.hurt();old_x=L.sample_overlay_sweep();self.assertEqual(old_x,expected_x-4)
   L.tick(1);self.assertEqual(L.hurt(),hurt+16,(remaining,expected_x));self.assertNotEqual(v('magma_game_revision'),revision,(remaining,expected_x))
   if remaining>1:
    self.assertEqual(b('magma_game_machine_stage'),2);self.assertEqual(L.sample_overlay_sweep(),expected_x);self.assertEqual(L.sample_overlay_sweep_y(),76)
   else:self.assertEqual(b('magma_game_machine_stage'),3);self.assertEqual(L.sample_overlay_sweep(),-1)
  # Dialogue/menu/save/death freezes leave the cache key and hazard pixels
  # unchanged; draw calls themselves must never advance or invalidate them.
  L.magma_game_reset();C.c_ubyte.in_dll(L,'magma_game_machine_stage').value=2;C.c_ubyte.in_dll(L,'magma_game_machine_ticks').value=20;self.at(24,136)
  for mode in (2,3,4,5,6,7,8,9):
   L.modal(mode);before=(v('magma_game_revision'),b('magma_game_machine_ticks'),L.sample_overlay_sweep());L.tick(200);after=(v('magma_game_revision'),b('magma_game_machine_ticks'),L.sample_overlay_sweep());self.assertEqual(after,before,mode)
 def test_q35_screen_repair_persists_travel_reset_and_codec_reload(self):
  self.guarantees();self.entry(39)
  def screen():
   words=(C.c_uint*3)();L.magma_game_collision_inputs(words);return words[0]
  self.assertEqual(screen(),128);self.target(128,264);L.magma_game_input(16,0);L.magma_game_input(1,0);self.assertEqual(screen(),152);self.assertEqual(L.qo(35),0)
  # An incomplete, unsaved arrangement still resets to the taught start.
  L.magma_game_reset();self.assertEqual(screen(),128);self.assertEqual(L.qo(35),0)
  self.target(128,264);L.magma_game_input(16,0);L.magma_game_input(16,0);L.magma_game_input(1,0);self.assertEqual(L.qo(35),1);self.assertEqual(screen(),176)
  for reset_kind in ('travel','death_or_load_reset','codec_reload'):
   if reset_kind=='travel':self.entry(38);self.entry(39)
   elif reset_kind=='death_or_load_reset':L.magma_game_reset()
   else:self.assertEqual(L.roundtrip(),1);self.assertEqual(L.fresh(),1);self.assertEqual(v('room'),39)
   self.assertEqual(screen(),176,reset_kind);self.assertEqual(L.qo(35),1);self.assertFalse(L.magma_game_solid(128,264));self.assertTrue(L.magma_game_solid(176,264))
  self.target(104,112);self.target(136,216);self.assertEqual(L.qs(35),3);self.entry(38);self.entry(39);L.magma_game_reset();self.assertEqual(screen(),176);self.assertEqual(L.roundtrip(),1);self.assertEqual(L.fresh(),1);self.assertEqual(screen(),176);self.assertEqual(L.qs(35),3)
  # All fifteen runtime trial flows also run after Q35 is claimed in the
  # existing full-trial test, proving they do not require the old screen rest.
 def test_rest_validation_deferred_once_without_revision_or_reward(self):
  self.guarantees();self.entry(38);self.assertEqual(L.host_settle_save(),1);L.host_set_auto_settle(0)
  calls=L.host_anchor_calls();writes=L.host_writes();fills=L.host_health_fills();old_spawn=L.host_campaign_spawn();old_checkpoint=v('checkpoint_spawn');digest=L.roster_event_digest();n=L.roster_count()
  self.target(112,248);self.assertEqual(L.magma_game_save_prepare_pending(),1);self.assertEqual(L.host_anchor_calls(),calls);self.assertEqual(L.host_writes(),writes);self.assertEqual(L.host_health_fills(),fills+1);self.assertEqual(v('checkpoint_spawn'),3);self.assertEqual(L.host_campaign_spawn(),old_spawn);self.assertEqual(L.host_anchor_bits()&1,0);self.assertEqual(L.valid(),1)
  revision=(v('magma_game_revision'),v('progression_revision'));L.modal(6);self.assertEqual(L.magma_game_prepare_save(),1);self.assertEqual(L.host_anchor_calls(),calls+1);self.assertEqual(L.magma_game_save_prepare_pending(),0);self.assertEqual(L.host_anchor_bits()&1,1);self.assertEqual(L.host_campaign_spawn(),3);self.assertEqual(v('checkpoint_spawn'),3);self.assertEqual((v('magma_game_revision'),v('progression_revision')),revision);self.assertEqual(L.magma_game_prepare_save(),0);self.assertEqual(L.host_anchor_calls(),calls+1);self.assertEqual(L.roster_count(),n);self.assertEqual(L.roster_event_digest(),digest);self.assertEqual(L.host_settle_save(),1);self.assertEqual(L.host_writes(),writes+1);self.assertEqual(L.roundtrip(),1)
  # An already-lit anchor still receives its real UNCHANGED validation once.
  self.target(112,248);L.modal(6);revision=(v('magma_game_revision'),v('progression_revision'));self.assertEqual(L.magma_game_prepare_save(),1);self.assertEqual(L.host_anchor_calls(),calls+2);self.assertEqual((v('magma_game_revision'),v('progression_revision')),revision);self.assertEqual(L.host_settle_save(),1)
  self.assertNotEqual(old_checkpoint,3)
 def test_rest_prepare_cancellation_mismatch_and_invalid_state_fail_closed(self):
  for failure in ('wrong_mode','room_mismatch','restamped_snapshot','invalid_roster','reset_cancel'):
   self.setUp();self.guarantees();self.entry(39);self.assertEqual(L.host_settle_save(),1);L.host_set_auto_settle(0);old_checkpoint=v('checkpoint_spawn');old_spawn=L.host_campaign_spawn();calls=L.host_anchor_calls();self.target(80,264);self.assertEqual(L.magma_game_save_prepare_pending(),1)
   if failure=='room_mismatch':C.c_int.in_dll(L,'room').value=38;L.modal(6)
   elif failure=='restamped_snapshot':L.host_stamp_campaign(39,1);L.modal(6)
   elif failure=='invalid_roster':L.host_corrupt_roster_level();L.modal(6)
   elif failure=='reset_cancel':L.magma_game_reset();L.modal(6)
   self.assertEqual(L.magma_game_prepare_save(),0,failure);self.assertEqual(L.magma_game_save_prepare_pending(),0);self.assertEqual(L.host_anchor_bits()&2,0);self.assertEqual(L.host_anchor_calls(),calls+(failure=='invalid_roster'));self.assertEqual(L.magma_game_prepare_save(),0);self.assertEqual(L.host_anchor_calls(),calls+(failure=='invalid_roster'))
   if failure!='room_mismatch':self.assertEqual(v('checkpoint_spawn'),old_checkpoint,failure)
   if failure!='restamped_snapshot':self.assertEqual(L.host_campaign_spawn(),old_spawn,failure)
 def test_host_save_bridge_prepares_town_and_field_before_codec_write(self):
  self.guarantees()
  for area,point,bit in [(38,(112,248),1),(39,(80,264),2)]:
   self.entry(area);self.assertEqual(L.host_settle_save(),1);before=L.host_anchor_calls();writes=L.host_writes();self.target(*point);self.assertEqual(L.host_anchor_calls(),before);self.assertEqual(L.host_anchor_bits()&bit,0);self.assertEqual(L.host_settle_save(),1);self.assertEqual(L.host_anchor_calls(),before+1);self.assertEqual(L.host_writes(),writes+1);self.assertEqual(L.host_anchor_bits()&bit,bit);self.assertEqual(L.roundtrip(),1);self.assertEqual(L.fresh(),1);self.assertEqual(v('room'),area);self.assertEqual(L.host_campaign_spawn(),3);self.assertEqual(L.magma_game_save_prepare_pending(),0)
 def test_failed_queued_anchor_prevents_host_codec_write(self):
  self.guarantees();self.entry(39);self.assertEqual(L.host_settle_save(),1);L.host_set_auto_settle(0);writes=L.host_writes();calls=L.host_anchor_calls();failed=L.invalid_saves();checkpoint=v('checkpoint_spawn');self.target(80,264);L.host_corrupt_roster_level()
  self.assertEqual(L.host_settle_save(),0);self.assertEqual(L.host_writes(),writes);self.assertEqual(L.host_anchor_calls(),calls+1);self.assertEqual(L.invalid_saves(),failed+1);self.assertEqual(L.magma_game_save_prepare_pending(),0);self.assertEqual(L.host_anchor_bits()&2,0);self.assertEqual(v('checkpoint_spawn'),checkpoint)
if __name__=='__main__':unittest.main(verbosity=2)
