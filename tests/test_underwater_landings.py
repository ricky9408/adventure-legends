#!/usr/bin/env python3
"""Reciprocal authored doors and current-r6 landing helpers.
These execute real room logic behind synthetic host warps, not native travel.
Historical raw-bank parity is owned by the save-policy suite.
"""
from pathlib import Path
import ctypes as C,json,re,subprocess,tempfile,unittest
import test_underwater_game as W
import test_magma_game as M
ROOT=Path(__file__).resolve().parents[1]
TMP=tempfile.TemporaryDirectory(prefix='underwater-landings-');OUT=Path(TMP.name)
(OUT/'magma_game_test_ui.h').write_text('enum{'+','.join(k+'='+str(v)for k,v in M.IDS.items())+'};\n')
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC','-DMAGMA_GAME_HOST_TEST','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST','-Isrc','-I'+str(OUT),'tests/magma_game_host.c','tests/underwater_landing_magma_bridge.c',*M.sources,'src/underwater_quests.c','-Wl,--wrap=magma_anchor','-o',str(OUT/'magma.so')],cwd=ROOT,check=True)
M.L=C.CDLL(str(OUT/'magma.so'));M.SRAM=(C.c_ubyte*32768).in_dll(M.L,'save5_test_sram')
SPAWNS={46:[(240,288),(240,32),(80,272),(448,160)],47:[(240,288),(400,48),(64,272)],48:[(240,288),(240,32),(448,160)],49:[(120,140),(208,112)],50:[(120,140),(208,112)],51:[(240,288),(432,112),(32,160)],52:[(120,140),(208,112),(32,112)],53:[(120,140),(208,112)]}
PAIRS=[(46,(464,160),16,47,0,(240,304),128,3),(46,(240,16),64,48,0,(240,304),128,1),(47,(400,16),64,50,0,(120,146),128,1),(48,(240,16),64,49,0,(120,146),128,1),(48,(464,160),16,51,2,(16,160),32,2),(49,(224,112),16,52,2,(16,112),32,1),(50,(224,112),16,51,0,(240,304),128,1),(51,(464,112),16,52,0,(120,146),128,1),(52,(224,112),16,53,0,(120,146),128,1)]
class ReturnLandings(unittest.TestCase):
 def setUp(self):self.w=W.UnderwaterWorld();self.w.setUp()
 def move_exit(self,point,key,room,spawn):
  self.w.at(*point);W.L.direction(key);W.L.tick(1);self.assertEqual(W.L.settle_events(),1);self.assertEqual(W.v('room'),room);self.assertEqual(W.v('checkpoint_spawn'),spawn);self.assertEqual((W.v('px'),W.v('py')),SPAWNS[room][spawn]);self.assertFalse(W.L.underwater_game_solid(W.v('px'),W.v('py')));self.assertEqual(W.L.roundtrip(),1)
 def test_all_nine_reciprocal_door_pairs_arrive_at_the_return_door(self):
  self.w.main()
  for a,exit_a,key_a,b,spawn_b,exit_b,key_b,spawn_a in PAIRS:
   with self.subTest(pair=(a,b)):
    self.w.entry(a);self.move_exit(exit_a,key_a,b,spawn_b);self.move_exit(exit_b,key_b,a,spawn_a)
 def test_exact_spawn_rows_reload_and_anchor_scope(self):
  self.w.main()
  for a,rows in SPAWNS.items():
   self.assertEqual(W.L.underwater_game_spawn_count(a),len(rows))
   for s,point in enumerate(rows):
    x=C.c_int();y=C.c_int();self.assertEqual(W.L.underwater_game_spawn(a,s,C.byref(x),C.byref(y)),1);self.assertEqual((x.value,y.value),point)
    if a in(46,47)and s==2:
     self.assertEqual(W.L.underwater_game_request_enter(a,s),0)
     self.w.entry(a);self.w.target(80 if a==46 else 64,256);self.assertTrue(W.L.host_anchor_bits()&(1<<(a-46)))
    self.w.entry(a,s);self.assertEqual(W.L.roundtrip(),1);self.assertEqual(W.L.fresh(),1);self.assertEqual(W.v('room'),a);self.assertEqual(W.v('checkpoint_spawn'),s);self.assertEqual(W.L.underwater_game_enter(a,s),1);self.assertEqual((W.v('px'),W.v('py')),point)
   self.assertEqual(W.L.underwater_game_spawn(a,len(rows),None,None),0)
 def test_new_optional_entrances_preserve_story_gates(self):
  self.w.entry(46);self.assertEqual(W.L.underwater_game_request_enter(46,3),1)
  self.assertEqual(W.L.underwater_game_request_enter(48,2),2);self.assertEqual(W.L.settle_events(),1)
  self.assertEqual(W.L.underwater_game_request_enter(51,2),0);self.assertEqual(W.L.underwater_game_request_enter(52,2),0)
  self.w.guarantees();self.assertEqual(W.L.underwater_game_request_enter(51,2),0);self.assertEqual(W.L.underwater_game_request_enter(52,2),0)
  self.w.entry(50);self.w.field(0,49);self.w.field(1,52);self.w.target(120,104);self.assertEqual(W.L.underwater_game_request_enter(51,2),2);self.assertEqual(W.L.settle_events(),1);self.assertEqual(W.L.underwater_game_request_enter(52,2),0)
 def test_nacreway_south_transition_requires_its_visible_door(self):
  self.w.entry(46);self.w.at(120,304);W.L.direction(128);W.L.tick(1);self.assertEqual(W.v('room'),46)
  self.w.at(240,304);W.L.direction(128);W.L.tick(1);self.assertEqual(W.v('room'),38);self.assertEqual(W.v('checkpoint_spawn'),4)
 def test_layout_target_spawn_matches_runtime_routes(self):
  data={r['id']:r for r in json.loads((ROOT/'assets/underwater_region/layout.json').read_text())['rooms']}
  for a,exit_a,key_a,b,spawn_b,exit_b,key_b,spawn_a in PAIRS:
   for area,target,point,spawn in [(a,b,exit_a,spawn_b),(b,a,exit_b,spawn_a)]:
    row=next(e for e in data[area]['exits']if e['approach']==list(point));self.assertEqual((row['target'],row['target_spawn']),(target,spawn))
  row=next(e for e in data[46]['exits']if e['key']=='south');self.assertEqual((row['target'],row['target_spawn']),(38,4))
 def test_frozen_dispatch_checks_magma_return_before_scene_checkpoint_mutation(self):
  # Structural coverage of the actual engine guard, not a fabricated dispatch
  # implementation or a claim that this executes the whole native engine.
  source=(ROOT/'src/game.c').read_text();start=source.index('COLD void enter_room(int r,int fromnorth){');body=source[start:source.index('COLD void start_game(',start)];compact=re.sub(r'\s+','',body)
  guard='if(!magma_game_can_enter((unsigned)r)||(unsigned)fromnorth>=magma_game_spawn_count((unsigned)r)||(r==38&&fromnorth==4&&!(adventure_save.quests.region_flags[4]&1)))return;'
  self.assertIn('elseif(r>=38){'+guard+'}',compact)
  precheck=compact.index(guard)
  for mutation in ['creatures_begin_expedition(&adventure_save.roster)','room=r;','trials_enter(r);','checkpoint_spawn=fromnorth;','px=120;','spawn_enemies();','magma_game_enter((unsigned)r,(unsigned)fromnorth)']:
   self.assertIn(mutation,compact);self.assertLess(precheck,compact.index(mutation),mutation)
 def test_magma_lift_append_preserves_old_rows_gate_and_a_targets(self):
  m=M.MagmaRuntime();m.setUp();m.main();old=[(240,284),(304,32),(80,152),(112,264)]
  self.assertEqual(M.L.magma_game_spawn_count(38),5);self.assertEqual(M.L.magma_game_spawn_count(39),4)
  for s,pt in enumerate(old+[(416,240)]):
   x=C.c_int();y=C.c_int();self.assertEqual(M.L.magma_game_spawn(38,s,C.byref(x),C.byref(y)),1);self.assertEqual((x.value,y.value),pt)
  self.assertEqual(M.L.landing_validate_revision(5),1);M.L.snapshot_state();self.assertEqual(M.L.magma_game_enter(38,4),0);self.assertEqual(M.L.unchanged(),1)
  M.L.host_stamp_campaign(38,4);self.assertEqual(M.L.landing_validate_revision(5),0);self.assertEqual(M.L.valid(),0);M.L.host_stamp_campaign(38,0)
  self.assertEqual(M.L.landing_mark_nacreway(),1);m.entry(38,4);self.assertEqual((M.v('px'),M.v('py')),(416,240));m.at(416,240,1);M.L.snapshot_state();self.assertEqual(M.L.magma_game_interact(),0);self.assertEqual(M.L.unchanged(),1)
  self.assertEqual(M.L.roundtrip(),1);self.assertEqual(M.L.fresh(),1);self.assertEqual(M.v('checkpoint_spawn'),4);m.entry(38,4);self.assertEqual(M.L.valid(),1)
  # The old deferred anchor protocol must also accept this new legal prior spawn.
  m.target(112,248);self.assertEqual(M.L.host_settle_save(),1);self.assertEqual(M.L.host_campaign_spawn(),3);self.assertEqual(M.L.roundtrip(),1)
if __name__=='__main__':unittest.main(verbosity=2)
