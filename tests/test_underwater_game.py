#!/usr/bin/env python3
"""Production Underwater world, synthetic host warps/shape-hit callback receipts.
This is not controller acquisition, native power-shape proof or cadence evidence.
"""
from pathlib import Path
import ctypes as C,json,subprocess,tempfile,unittest,os
ROOT=Path(__file__).resolve().parents[1]
TMP=tempfile.TemporaryDirectory(prefix='underwater-runtime-');OUT=Path(TMP.name)
UI=json.loads((ROOT/'assets/underwater_region/dialogue.json').read_text());IDS={'TX_'+k:4000+i for i,k in enumerate(UI)}
(OUT/'underwater_game_test_ui.h').write_text('enum{'+','.join(k+'='+str(v)for k,v in IDS.items())+'};\n')
sources=['src/underwater_game.c','src/underwater_art.c','src/underwater_quests.c','src/magma_quests.c','src/southern_quests.c','src/northern_quests.c','src/save5.c','src/save4.c','src/equipment.c','src/equipment_data.c','src/creatures.c','src/creature_data.c']
WORLD_POWERS=os.environ.get('UNDERWATER_WORLD_POWERS')=='1'
extra=['-DUNDERWATER_WORLD_POWERS','tests/underwater_world_power_bridge.c','src/underwater_powers.c','src/underwater_power_art.c','src/combat_rules.c'] if WORLD_POWERS else []
subprocess.run(['cc',*extra,'-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC','-DUNDERWATER_GAME_HOST_TEST','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST','-Isrc','-I'+str(OUT),'tests/underwater_game_host.c',*sources,'-Wl,--wrap=underwater_anchor','-o',str(OUT/'test.so')],cwd=ROOT,check=True)
L=C.CDLL(str(OUT/'test.so'))
SRAM=(C.c_ubyte*32768).in_dll(L,'save5_test_sram')
FIXTURE=(ROOT/'tests/fixtures/v5-revision5/magma-all65-town.sav').read_bytes()
def v(n):return C.c_int.in_dll(L,n).value
def b(n):return C.c_ubyte.in_dll(L,n).value
def toast():return next((k for k,x in IDS.items()if x==L.get_toast()),str(L.get_toast()))
class Puzzle(C.Structure):_fields_=[('mode',C.c_ubyte),('rotation',C.c_ubyte),('ballast',C.c_ubyte),('baffle',C.c_ubyte*2),('echo',C.c_ubyte),('walk',C.c_ubyte),('aux',C.c_ubyte)]
class Trial(C.Structure):_fields_=[('id',C.c_uint),('generation',C.c_uint),('party_signature',C.c_uint),('index',C.c_ubyte),('slot',C.c_ubyte),('form',C.c_ubyte),('family',C.c_ubyte),('key',C.c_ubyte),('source',C.c_ubyte),('command',C.c_ubyte),('selected_party',C.c_ubyte),('setting',C.c_ubyte*4),('casts',C.c_ubyte),('walk',C.c_ubyte),('order',C.c_ubyte),('failed',C.c_ubyte)]
def puzzle():return Puzzle.in_dll(L,'underwater_game_puzzle')
def trial():return Trial.in_dll(L,'underwater_game_trial')
class UnderwaterWorld(unittest.TestCase):
 def setUp(self):SRAM[:]=FIXTURE;self.assertEqual(L.fresh(),1)
 def entry(self,r,s=0):self.assertEqual(L.entry(r,s),1,(r,s));self.assertFalse(L.underwater_game_solid(v('px'),v('py')),(r,s,v('px'),v('py')))
 def at(self,x,y,f=1):L.at(x,y);L.facing(f);self.assertFalse(L.underwater_game_solid(x,y),(v('room'),x,y))
 def act(self,x,y,f=1):self.at(x,y,f);self.assertEqual(L.underwater_game_interact(),1,(v('room'),x,y,toast()));self.assertEqual(L.settle_events(),1)
 def target(self,x,y,f=1):dx,dy={0:(0,-16),1:(0,16),2:(16,0),3:(-16,0)}[f];self.act(x+dx,y+dy,f)
 def field(self,i,form=None,want=1):
  if form:self.assertLess(L.select_form(form),160)
  x=C.c_int();y=C.c_int();self.assertEqual(L.underwater_game_field_target(i,C.byref(x),C.byref(y),None),1);
  if WORLD_POWERS and want==1:
   cmd=L.progression_command();offset={67:24,70:24,73:12,76:12,79:8,82:16,85:6,88:12}[cmd];side=-10 if cmd==88 else 0
   candidates=[(-side,offset,1),(-offset,-side,3),(offset,side,2),(side,-offset,0)]
  else:candidates=[(0,24,1),(-24,0,3),(24,0,2),(0,-24,0)]
  for dx,dy,f in candidates:
   if not L.underwater_game_solid(x.value+dx,y.value+dy):self.at(x.value+dx,y.value+dy,f);break
  else:self.fail(('No safe field approach',v('room'),i))
  if WORLD_POWERS and want==1:self.assertEqual(L.real_cast(),1,(v('room'),i,toast()))
  else:self.assertEqual(L.synthetic_field(i),want,(v('room'),i,toast()))
  self.assertEqual(L.settle_events(),1)
 def guarantees(self):
  self.entry(46);self.target(144,104);self.target(120,72);self.assertEqual(L.qs(38),3)
  self.target(340,108);self.target(340,108);self.entry(47)
  for p in [(176,164),(304,164),(240,192)]:self.at(*p);L.tick(1)
  self.entry(46);self.target(340,72);self.assertEqual(L.qs(39),3);self.assertEqual(L.valid(),1)
 def main(self):
  self.guarantees();self.entry(50);self.field(0,49);self.field(1,52);self.target(120,104);self.assertEqual(L.qo(40),1,toast())
  self.entry(51);self.field(0,52);self.at(312,112);L.tick(1);self.field(1);self.target(240,80);self.assertEqual(L.qo(40),3)
  self.entry(52);self.act(80,96);self.field(0,49);self.target(120,112);self.assertEqual(L.qo(40),7)
  self.entry(53);self.field(0,49);self.field(1,52);self.target(176,80);self.target(120,112)
  for _ in range(3):
   self.at(24,136);L.tick(108);self.assertEqual(b('underwater_game_guardian_stage'),3);self.assertEqual(L.underwater_game_weapon_hit(1,120,48,16,0,L.underwater_game_action_begin(0)),1)
  self.assertEqual(L.settle_events(),1);self.assertEqual(L.qo(40),15);self.entry(46);self.target(120,72);self.assertEqual(L.qs(40),3);self.assertEqual(L.roundtrip(),1)
 def sources(self):
  self.main();self.entry(48);self.target(112,92);self.target(144,92);self.target(64,224);self.target(96,224)
  self.entry(47);self.target(352,160);self.target(376,184)
  self.entry(49);self.target(144,52);self.target(172,52);self.target(120,48);self.field(0,49);self.target(64,56)
  self.entry(51);self.target(160,80);self.target(160,112);self.target(144,96,f=2)
  self.assertEqual(L.flags(10),63);self.assertEqual(L.roundtrip(),1)
 def start(self,family,key):
  areas=[50,52,51,49,48,48,50,51,49,48,48,51,51,52,49,52];i=(family-17)*2+key-1;self.entry(areas[i]);slot=L.select_form(49+(family-17)*3);self.assertLess(slot,160);self.target((80 if key==1 else 400) if areas[i] in (48,51) else (48 if key==1 else 192),240 if areas[i] in (48,51) else 112);self.assertEqual(trial().index,i,toast());return slot
 def point(self,n):
  i=trial().index;ox,oy=(240,160) if v('room') in (48,51) else(120,80)
  offsets=[(-48,-20),(48,-20),(-48,20),(48,20),(0,-24),(0,28)]
  if i==9:return ox-36+n%3*36,oy-18+n//3*36
  if i==15:offsets=[(-48,-24),(48,-24),(0,32),(64,32),(0,-24),(0,28)]
  x,y=offsets[n];return ox+x,oy+y
 def manual(self,n,times=1):
  for _ in range(times):self.target(*self.point(n))
 def cast(self,n):
  # These host-only callback tests isolate world proof from native shape runtime.
  self.field(n)
 def walk(self,side):
  ox,oy=(240,160) if v('room') in(48,51) else(120,80);self.at(ox+side*64,oy+28);L.tick(1);self.assertEqual(L.settle_events(),1)
 def solve(self,i):
  if i==0:self.manual(0);self.manual(1);self.cast(0);self.cast(1)
  elif i==1:self.manual(0);self.cast(0);self.cast(1)
  elif i==2:self.cast(0);self.walk(1);self.cast(1)
  elif i==3:self.cast(0);self.cast(1);self.cast(1);self.walk(-1);self.walk(1)
  elif i==4:self.cast(0);self.cast(1);self.manual(4)
  elif i==5:self.manual(0);self.manual(1);self.walk(-1);self.walk(1);self.cast(4)
  elif i==6:self.manual(0);self.manual(1);self.manual(2);self.cast(4)
  elif i==7:self.manual(0);self.manual(1,2);self.cast(4)
  elif i==8:self.cast(0);self.manual(0);self.manual(1)
  elif i==9:
   for n in (0,1,2,5):self.cast(n)
  elif i==10:self.cast(2);self.manual(4,3)
  elif i==11:self.manual(0);self.manual(1,3);self.manual(2);self.cast(0);self.cast(1)
  elif i==12:self.manual(0);self.manual(1,3);self.cast(0);self.cast(1)
  elif i==13:
   self.manual(4,2);self.cast(4)
   for p in [(72,68),(72,108),(120,88),(168,68),(168,108),(120,88)]:self.at(*p);L.tick(1);self.assertEqual(L.settle_events(),1)
  elif i==14:self.manual(0);self.manual(1,3);self.cast(0);self.cast(1)
  elif i==15:
   for n in (0,1,2):self.manual(n)
   for n in (0,1,2):self.cast(n)
 def test_main_two_base_route_and_codec(self):self.main();self.assertEqual(L.invalid_saves(),0)
 def test_every_field_source(self):self.sources()
 def test_all_sixteen_geometry_trials(self):
  self.sources()
  for i in range(16):
   s=self.start(17+i//2,1+i%2);self.solve(i);self.assertTrue(L.trial(s)&(1<<(i%2)),(i,toast(),bytes(trial())));self.assertGreaterEqual(L.level(s),28);self.assertGreaterEqual(L.bond(s),45);self.assertEqual(L.valid(),1,i)
  self.assertEqual(L.roundtrip(),1)
 def test_geometry_and_spawn_contracts(self):
  self.assertEqual(L.collision_equivalence(),0)
  for a,n in [(46,0),(47,4),(48,2),(49,0),(50,1),(51,2),(52,1),(53,2)]:self.assertEqual(L.encounter_spawns(a),n,a)
 def repeat_demo(self,f):
  if f==17:
   self.entry(46);self.target(64,72);self.target(64,72);self.target(64,104)
  elif f==18:
   self.entry(46);self.target(416,72,3);self.at(448,108);L.tick(1);self.target(416,108)
  elif f==19:
   self.entry(48);self.target(368,208);self.at(400,208);L.tick(1);self.target(368,256)
  elif f==20:
   self.entry(47);self.target(392,240);self.at(424,240);L.tick(1);self.target(416,264)
  elif f==21:
   self.entry(49);self.target(208,64);self.target(208,64);self.target(208,96)
  elif f==22:
   self.entry(48)
   for _ in range(3):self.target(304,80)
   self.target(272,80);self.target(336,80)
  elif f==23:self.entry(51);self.target(384,64);self.target(416,64);self.target(400,96)
  else:self.entry(49);self.target(80,88);self.target(112,88);self.target(64,88)
 def test_eight_real_repeat_branches_and_fifty_retained(self):
  self.sources();self.assertEqual(L.roster_count(),42)
  for f in range(17,25):
   slot=self.start(f,1);self.solve((f-17)*2);base=49+(f-17)*3;self.assertEqual(L.evolve(slot,base+1),0)
   before=L.roster_count();digest=L.roster_event_digest();self.repeat_demo(f);self.assertEqual(L.roster_count(),before+1,(f,toast()));self.assertEqual(L.roster_event_digest(),digest)
   # Reopening the exact solved invitation is not a new attempt.
   L.underwater_game_interact();L.settle_events();self.assertEqual(L.roster_count(),before+1,f)
   extra=self.start(f,2);self.assertNotEqual(extra,slot);self.assertEqual(L.trial(extra),0);self.solve((f-17)*2+1);self.assertEqual(L.evolve(extra,base+2),0)
  self.assertEqual(L.flags(17),255);self.assertEqual(L.roster_count(),50);self.assertEqual(L.history_count(),89);self.assertEqual(L.roundtrip(),1)
  for area in range(46,54):
   self.entry(area);peak=L.max_camera_actors();self.assertLessEqual(peak+3,20,(area,peak))
 def test_all_eight_quests_and_side_route_gates(self):
  self.main();self.entry(46);self.target(160,176);self.target(304,176);self.target(240,240)
  for _ in range(3):self.target(240,104)
  self.assertEqual(L.qs(41),3,toast());self.entry(48);self.target(240,80);self.target(280,224,2);self.target(432,256);self.assertEqual(L.qs(42),3,toast())
  self.entry(47);self.target(64,112);self.target(112,112);self.target(64,112);self.assertEqual(L.qs(43),3)
  self.entry(46);self.target(384,128);self.entry(49);self.target(120,48);self.entry(46);self.target(384,160);self.assertEqual(L.qs(44),3)
  self.entry(53);self.target(208,112);self.assertEqual(v('room'),46)
  for r in (48,49,48,46):self.entry(r)
  self.target(240,272);self.assertEqual(L.qs(45),3,toast());self.assertEqual(L.roundtrip(),1)
 def test_trial_menu_selection_away_and_back_cannot_restore_proof(self):
  self.sources();slot=self.start(17,1);self.manual(0);self.manual(1);self.cast(0);L.underwater_game_selection_changed();L.select_form(52);L.select_slot(slot);self.assertEqual(trial().index,255);self.assertEqual(L.trial(slot),0)
 def test_pending_visit_keeps_old_checkpoint_and_cancel_is_unchanged(self):
  old=(v('room'),L.host_campaign_spawn());L.snapshot_state();self.assertEqual(L.underwater_game_request_enter(46,0),2);self.assertEqual((v('room'),L.host_campaign_spawn()),old);self.assertEqual(L.unchanged(),1);L.underwater_game_cancel_event();self.assertEqual(L.unchanged(),1);self.assertEqual(L.underwater_game_event_pending(),0)
 def test_connected_guardian_return_cancel_retry_and_walk_home(self):
  # These are real typed world jobs with synthetic positions, not native input.
  self.main();self.entry(53);self.at(32,112,2);L.host_set_auto_settle(0)
  self.assertEqual(b('underwater_game_guardian_stage'),4);self.assertEqual(L.qo(45),0)
  old=(v('room'),L.host_campaign_spawn());L.snapshot_state()
  self.assertEqual(L.underwater_game_road_departure(52,1),1)
  self.assertEqual((v('room'),L.host_campaign_spawn()),old);self.assertEqual(L.qo(45),0)
  self.assertEqual(L.underwater_game_event_pending(),1)
  L.modal(10);self.assertEqual(L.underwater_game_prepare_event(),1)
  L.underwater_game_cancel_event();L.modal(1)
  self.assertEqual(L.unchanged(),1);self.assertEqual(L.underwater_game_event_pending(),0)
  self.assertEqual(L.underwater_game_road_departure(52,1),1)
  self.assertEqual(v('room'),53);self.assertEqual(L.settle_events(),1)
  self.assertEqual((v('room'),L.host_campaign_spawn()),(52,1));self.assertEqual(L.qo(45),1)
  self.assertEqual(L.roundtrip(),1);L.host_set_auto_settle(1)
  # Ordinary roads bring the player back to town; this alone is not the Q45 loop.
  for r,s in ((51,1),(48,2),(46,1)):self.entry(r,s)
  self.assertEqual(L.qo(45),1)
  for r in (48,49,48,46):self.entry(r)
  self.assertEqual(L.qo(45),3);self.target(240,272)
  self.assertEqual(L.qs(45),3);self.assertEqual(L.roundtrip(),1)
  self.assertEqual(L.invalid_saves(),0)
 def test_connected_guardian_return_committed_cancel_and_revisit_are_idempotent(self):
  self.main();self.entry(53);L.host_set_auto_settle(0)
  self.assertEqual(L.underwater_game_road_departure(52,1),1);L.modal(10)
  for _ in range(1000):
   if not L.underwater_game_event_pending():break
   self.assertIn(L.underwater_game_prepare_event(),(1,2))
  else:self.fail('Guardian departure event did not finish')
  # The quest fact committed, but only the engine's later callback may travel.
  self.assertEqual(v('room'),53);self.assertEqual(L.qo(45),1)
  L.underwater_game_cancel_event();L.modal(1)
  self.assertEqual(L.underwater_game_road_departure(52,1),1)
  self.assertEqual((v('room'),L.host_campaign_spawn()),(52,1));self.assertEqual(L.valid(),1)
  self.assertEqual(L.roundtrip(),1);L.host_set_auto_settle(1)
  self.entry(53);L.snapshot_state();count=L.roster_count()
  self.assertEqual(L.underwater_game_road_departure(46,1),0)
  self.assertEqual(L.unchanged(),1);self.assertEqual(v('room'),53)
  self.assertEqual(L.underwater_game_road_departure(52,1),1)
  self.assertEqual(L.qo(45),1);self.assertEqual(L.roster_count(),count)
  self.assertEqual(L.roundtrip(),1);self.assertEqual(L.invalid_saves(),0)
 def test_reset_confirmation_isolated_and_every_small_puzzle_exit_reachable(self):
  # Exact pixel flood of every unique movable solid configuration. These are
  # synthetic geometry checks, not native controller traversal evidence.
  from collections import deque
  for area in (50,51,52,53):
   width,height=(480,320) if area==51 else(240,160)
   configs=[(0,a,b)for a in(0,1)for b in(0,1)] if area==52 else [(a,0,0)for a in(0,1)]
   for ballast,b0,b1 in configs:
    p=Puzzle();L.underwater_puzzle_reset(C.byref(p),area);p.ballast=ballast;p.baffle[:]=[b0,b1]
    ptr=C.byref(p);blocked=bytearray(L.underwater_puzzle_solid(ptr,area,x,y)for y in range(height)for x in range(width));start=(height-20)*width+width//2;self.assertFalse(blocked[start]);seen=bytearray(width*height);seen[start]=1;queue=deque([start]);count=0
    while queue:
     v=queue.popleft();count+=1
     for n in (v-1,v+1,v-width,v+width):
      if not seen[n] and not blocked[n]:seen[n]=1;queue.append(n)
    reset=(40,292) if area==51 else(40,132);self.assertTrue(seen[reset[1]*width+reset[0]],(area,ballast,b0,b1,reset))
    free=len(blocked)-sum(blocked)
    if count!=free:
     bad=next(i for i in range(len(seen))if not blocked[i] and not seen[i]);self.fail(('unreachable free pixel',area,ballast,b0,b1,bad%width,bad//width,count,free))
 def test_modal_ticks_do_not_age_world_or_complete_walk_proof(self):
  self.sources();self.start(18,1);self.cast(0);self.at(304,188)
  for mode in (2,3,4,5,6,7,8,9):
   L.modal(mode);before=(bytes(trial()),bytes(puzzle()),v('underwater_game_revision'));L.tick(300);self.assertEqual((bytes(trial()),bytes(puzzle()),v('underwater_game_revision')),before,mode)
 def test_changed_solids_refuse_to_overlap_the_player(self):
  for a,target,x,y,ballast in [(50,1,116,54,0),(51,0,284,136,0),(52,0,90,72,0),(53,1,64,60,1)]:
   p=Puzzle();L.underwater_puzzle_reset(C.byref(p),a);p.ballast=ballast;before=bytes(p);self.assertFalse(L.underwater_puzzle_solid(C.byref(p),a,x,y));self.assertEqual(L.underwater_puzzle_toggle(C.byref(p),a,target,x,y),0);self.assertEqual(bytes(p),before)
 def test_trial_cancellation_delays_restoring_an_overlapping_solid(self):
  self.sources();self.start(17,1);self.at(148,84);L.underwater_game_selection_changed();self.assertEqual(trial().index,255);self.assertFalse(L.underwater_game_solid(148,84));self.assertEqual(L.underwater_game_field_target(0,None,None,None),0);self.at(192,84);L.tick(1);self.assertTrue(L.underwater_game_solid(148,84));self.assertEqual(L.underwater_game_field_target(0,None,None,None),1)
 def test_wrong_commands_and_stale_tokens(self):
  self.guarantees();self.entry(50);self.field(0,52,2);self.assertEqual(puzzle().echo,0);self.field(1,49,2);self.assertEqual(puzzle().ballast,0)
  L.select_form(49);token=L.underwater_game_action_begin(3);old=L.selected_id();self.entry(50);self.assertEqual(L.underwater_game_field_hit(0,67,old,49,token),0)
 def test_selection_exit_and_reset_invalidate_trial(self):
  self.sources();s=self.start(17,1);self.manual(0);self.manual(1);self.cast(0);L.select_form(52);L.tick(1);self.assertEqual(trial().index,255);self.assertEqual(L.trial(s),0)
  self.start(17,1);self.manual(0);self.manual(1);self.cast(0);self.entry(50);self.assertEqual(trial().index,255)
 def test_deferred_anchor_preserves_exact_spawn_gate(self):
  self.guarantees();L.host_settle_save();L.host_set_auto_settle(0);old=L.host_campaign_spawn();L.at(80,272);L.facing(1);self.assertEqual(L.underwater_game_interact(),1);self.assertEqual(L.underwater_game_event_pending(),1);self.assertEqual(L.host_campaign_spawn(),old);self.assertEqual(L.host_anchor_bits()&1,0);self.assertEqual(L.settle_events(),1);self.assertEqual(L.host_anchor_bits()&1,1);self.assertEqual(L.host_campaign_spawn(),2)
if __name__=='__main__':unittest.main(verbosity=2)
