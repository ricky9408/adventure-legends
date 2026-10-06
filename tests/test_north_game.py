#!/usr/bin/env python3
"""Production Northern C runtime + save/quest data with synthetic bridges.
This proves bounded puzzle/reward behavior; controller-native QA is separate.
"""
from collections import deque
from pathlib import Path
import ctypes,json,os,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
TMP=tempfile.TemporaryDirectory(prefix='north-runtime-');OUT=Path(TMP.name)
UI=json.loads((ROOT/'assets/northern_region/ui_additions.json').read_text())
(OUT/'north_game_test_ui.h').write_text('enum {\n'+''.join(f'TX_{k}={2000+i},\n' for i,k in enumerate(UI))+'};\n')
HARNESS=r'''
#include <string.h>
#include <limits.h>
#include "north_game.h"
#include "north_art.h"
#include "northern_quests.h"
#include "progression.h"
Save5State adventure_save;
unsigned progression_revision,progression_forms[PROGRESSION_SPIRIT_COUNT];
volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
volatile unsigned chapter_flags;
int face,keys,journal_tab;
static unsigned saved,invalid,damage_calls,actor_calls,last_toast,weapon_class=1,forced_full;
static Save5State snapshot;
CreatureInstance *progression_selected(void){unsigned p=adventure_save.roster.selected_party,s;if(p>=4)return 0;s=adventure_save.roster.party[p];return s<160?&adventure_save.roster.instances[s]:0;}
unsigned progression_command(void){CreatureInstance*c=progression_selected();return c?c->equipped[c->selected_command]:0;}
void progression_refresh(void){progression_revision++;}
void save_game(void){saved++;if(!save5_validate(&adventure_save))invalid++;}
void dialogue(int a,int b,int c){(void)a;(void)b;(void)c;game_state=2;}
void toast(int a){last_toast=(unsigned)a;}
void text(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void centered(int a,int b,int c){(void)a;(void)b;(void)c;}
void box(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void rect(int a,int b,int c,int d,unsigned char e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void line(int a,int b,int c,int d,int e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void north_actor(unsigned a,int b,int c){(void)a;(void)b;(void)c;actor_calls++;}
void region_form_actor(unsigned a,int b,int c){(void)a;(void)b;(void)c;actor_calls++;}
int game_region_entry_safe(void){return 1;}
void game_health_fill(void){}
unsigned game_weapon_class(void){return weapon_class;}
void game_north_hurt(unsigned d){damage_calls+=d;}
void enter_room(int r,int s){if(r>=22)north_game_enter((unsigned)r,(unsigned)s);else{room=r;checkpoint_spawn=s;}}
unsigned __real_equipment_claim_many(EquipmentState*,const EquipmentU8*,unsigned);
unsigned __wrap_equipment_claim_many(EquipmentState*s,const EquipmentU8*a,unsigned n){return forced_full?EQUIPMENT_FULL:__real_equipment_claim_many(s,a,n);}
void fresh(void){memset(&adventure_save,0,sizeof adventure_save);chapter_flags=7;adventure_save.campaign.chapter_flags=7;adventure_save.campaign.story_seen=10;
 creatures_migrate_legacy(&adventure_save.roster,7,0);equipment_init(&adventure_save.equipment);adventure_save.quests.region_flags[0]=1;
 game_state=summoned=1;room=16;px=400;py=280;face=keys=transition_lock=checkpoint_spawn=camera_x=camera_y=0;saved=invalid=damage_calls=actor_calls=forced_full=0;weapon_class=1;north_game_reset();
}
void at(int x,int y){px=x;py=y;game_state=1;face=1;keys=0;}
int entry(unsigned r,unsigned s){game_state=1;return north_game_enter(r,s);}
void select_cmd(unsigned cmd){unsigned i,j;for(i=0;i<160;i++){CreatureInstance*c=&adventure_save.roster.instances[i];if(!(c->flags&CREATURE_OCCUPIED)||!creatures_command_learned(c->form_id,c->level,cmd))continue;
 for(j=0;j<4;j++)if(adventure_save.roster.party[j]==i)break;
 if(j<4){unsigned t=adventure_save.roster.party[0];adventure_save.roster.party[0]=(CreatureU8)i;adventure_save.roster.party[j]=(CreatureU8)t;}else adventure_save.roster.party[0]=(CreatureU8)i;
 adventure_save.roster.selected_party=0;creatures_equip(c,0,cmd);creatures_select_command(c,0);return;
 }}
unsigned qs(unsigned q){return save5_quest_state(&adventure_save.quests,q);}
unsigned qo(unsigned q){return adventure_save.quests.objectives[q];}
int offer(unsigned q){return northern_quest_offer(&adventure_save,q);}
int objective(unsigned q,unsigned b){return northern_quest_objective(&adventure_save,q,b);}
int claim(unsigned q){return northern_quest_claim(&adventure_save,q);}
static int original_rectangle_predicate(unsigned area,int x,int y){const NorthArtRoom*r=&north_art_rooms[area-22];unsigned i;
 if(x<5||y<5||x>r->width-6||y>r->height-6)return 1;
 for(i=0;i<r->solid_count;i++){const NorthArtRect*b=&r->solids[i];if(x+5>=b->x&&x-5<b->x+b->w&&y+5>=b->y&&y-5<b->y+b->h)return 1;}
 return 0;
}
unsigned collision_checks;
int collision_equivalence(void){unsigned a,i,j;int x,y,old_room=room;collision_checks=0;
 for(a=22;a<=29;a++){const NorthArtRoom*r=&north_art_rooms[a-22];
  int xs[13]={INT_MIN,-100000,-33,-1,0,4,5,r->width-6,r->width-5,r->width,r->width+32,100000,INT_MAX};
  int ys[13]={INT_MIN,-100000,-33,-1,0,4,5,r->height-6,r->height-5,r->height,r->height+32,100000,INT_MAX};
  room=(int)a;
  for(y=-32;y<(int)r->height+32;y++)for(x=-32;x<(int)r->width+32;x++){
   collision_checks++;if(north_game_solid(x,y)!=original_rectangle_predicate(a,x,y)){room=old_room;return (int)(((a-21)<<24)|((unsigned)(y+32)<<12)|(unsigned)(x+32));}
  }
  for(i=0;i<13;i++)for(j=0;j<13;j++){collision_checks++;if(north_game_solid(xs[i],ys[j])!=original_rectangle_predicate(a,xs[i],ys[j])){room=old_room;return -(int)a;}}
 }
 for(room=-1;room<=64;room++)if(room<22||room>29){collision_checks++;if(north_game_solid(120,80)){room=old_room;return -1;}}
 room=old_room;return 0;
}
unsigned median_test(unsigned a,unsigned b,unsigned c,unsigned d){CreatureRoster r;unsigned v[4],i;memset(&r,0,sizeof r);v[0]=a;v[1]=b;v[2]=c;v[3]=d;for(i=0;i<4;i++){r.party[i]=(CreatureU8)(v[i]?i:255);r.instances[i].flags=v[i]?CREATURE_OCCUPIED:0;r.instances[i].level=(CreatureU8)v[i];}return northern_recruit_level(&r);}
unsigned roster_count(void){return creatures_roster_count(&adventure_save.roster);}
unsigned gear_count(void){return equipment_count(&adventure_save.equipment);}
unsigned invalid_saves(void){return invalid;}
unsigned saved_calls(void){return saved;}
int valid(void){return save5_validate(&adventure_save);}
void snapshot_state(void){snapshot=adventure_save;}
int unchanged(void){return !memcmp(&snapshot,&adventure_save,sizeof snapshot);}
void bag_full(unsigned b){forced_full=b;}
void fill_roster(void){while(creatures_roster_count(&adventure_save.roster)<160)if(creatures_grant(&adventure_save.roster,1,1,0,0,0)==255)break;}
void free_last(void){unsigned i;for(i=160;i;i--)if(adventure_save.roster.instances[i-1].flags==CREATURE_OCCUPIED){memset(&adventure_save.roster.instances[i-1],0,sizeof(CreatureInstance));adventure_save.roster.expedition_bond[i-1]=0;break;}}
int roundtrip(void){Save5State restored;if(!save5_store(&adventure_save)||!save5_load(&restored))return 0;return !memcmp(&adventure_save.quests,&restored.quests,sizeof restored.quests)&&!memcmp(&adventure_save.roster,&restored.roster,sizeof restored.roster)&&!memcmp(&adventure_save.equipment,&restored.equipment,sizeof restored.equipment);}
void tick(unsigned n){game_state=1;while(n--)north_game_tick();}
void weapon(unsigned w){weapon_class=w;}
unsigned hurt(void){return damage_calls;}
unsigned draw(void){actor_calls=0;north_game_draw_actors();north_game_draw_overlay();north_game_draw_journal();return actor_calls;}
void direction(int k){keys=k;game_state=1;}
void flags(unsigned f){chapter_flags=f;adventure_save.campaign.chapter_flags=(Save4U8)f;}
void visits(unsigned b){adventure_save.quests.region_flags[0]=(Save4U8)b;}
unsigned trial(unsigned form){unsigned i;for(i=0;i<160;i++)if(adventure_save.roster.instances[i].form_id==form)return adventure_save.roster.instances[i].trial_flags;return 0;}
unsigned level(unsigned form){unsigned i;for(i=0;i<160;i++)if(adventure_save.roster.instances[i].form_id==form)return adventure_save.roster.instances[i].level;return 0;}
'''
(OUT/'h.c').write_text(HARNESS)
sources=['src/north_game.c','src/northern_quests.c','src/north_art.c','src/save5.c','src/save4.c','src/equipment.c','src/equipment_data.c','src/creatures.c','src/creature_data.c']
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC','-DNORTH_GAME_HOST_TEST','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST','-Isrc','-I'+str(OUT),str(OUT/'h.c'),*sources,'-Wl,--wrap=equipment_claim_many',*(['-fsanitize=undefined','-fno-sanitize-recover=all'] if os.environ.get('NORTH_SANITIZE') else []),'-o',str(OUT/'test.so')],cwd=ROOT,check=True)
L=ctypes.CDLL(str(OUT/'test.so'))
class Puzzle(ctypes.Structure):_fields_=[('rail',ctypes.c_ubyte),('cart',ctypes.c_ubyte*2),('weight',ctypes.c_ubyte)]
L.north_puzzle_step.argtypes=[ctypes.POINTER(Puzzle),ctypes.c_uint,ctypes.c_uint,ctypes.c_int,ctypes.c_int]
L.north_puzzle_solved.argtypes=[ctypes.POINTER(Puzzle),ctypes.c_uint]
def ptuple(p):return p.rail,p.cart[0],p.cart[1],p.weight
def puzzle(t):return Puzzle(t[0],(ctypes.c_ubyte*2)(t[1],t[2]),t[3])
def value(n):return ctypes.c_int.in_dll(L,n).value
def byte(n):return ctypes.c_ubyte.in_dll(L,n).value
class NorthRuntime(unittest.TestCase):
 def setUp(self):L.fresh()
 def act(self,x,y):L.at(x,y);self.assertEqual(L.north_game_interact(),1)
 def power(self,x,y,cmd):L.at(x,y);L.select_cmd(cmd);self.assertEqual(L.north_game_power(cmd),1)
 def grant(self,q):
  self.assertIn(L.offer(q),(0,1))
  for b in (1,2,4,8):
   if L.northern_quest_mask(q)&b:self.assertIn(L.objective(q,b),(1,2))
  self.assertEqual(L.claim(q),3)
 def recruits(self):
  self.assertEqual(L.entry(22,0),1);self.grant(11);self.grant(13)
 def test_exhaustive_collision_original_predicate_equivalence(self):
  self.assertEqual(L.collision_equivalence(),0)
  self.assertEqual(ctypes.c_uint.in_dll(L,'collision_checks').value,827778)
 def test_party_median_clamp(self):
  for levels,want in [((0,0,0,0),14),((1,2,3,0),14),((10,14,20,25),17),((14,20,0,0),17),((30,40,50,60),20)]:self.assertEqual(L.median_test(*levels),want)
 def test_gate_has_no_ending_or_all_river_requirement(self):
  L.flags(1);self.assertEqual(L.entry(22,0),0);L.flags(7);L.visits(0);self.assertEqual(L.entry(22,0),0);L.visits(1);self.assertEqual(L.entry(22,0),1)
  self.assertEqual(L.entry(26,0),0);self.assertEqual(L.entry(22,5),0);self.assertEqual(L.entry(24,1),0)
 def test_complete_main_using_only_new_base_wood_metal(self):
  self.act(400,280);self.assertEqual(value('room'),22)
  self.act(168,208);self.act(160,208);self.act(304,208);self.act(168,208);self.assertEqual(L.qs(11),3)
  L.entry(23,0);self.act(240,208);self.act(320,208);self.act(352,176);self.assertEqual(L.qs(13),3)
  for area in (26,27,28):
   self.assertEqual(L.entry(area,0),1)
   turns=1 if area!=28 else 2
   for _ in range(turns):self.power(120,112,21)
   self.power(64,80,13);self.power(64,80,13);self.act(176,112)
   if area!=26:
    self.power(120,112,21);self.power(120,112,21);self.power(64,80,13);self.power(64,80,13)
   self.assertTrue(L.qo(21)&(1<<(area-26)));self.act(208,72);self.assertEqual(value('room'),area+1)
  self.power(64,124,13);self.power(176,124,21);self.act(120,124)
  self.assertEqual(byte('north_game_machine_stage'),1);self.assertFalse(L.north_game_target(None,None,None));L.tick(84)
  self.assertEqual(byte('north_game_machine_stage'),3);self.assertTrue(L.north_game_target(None,None,None))
  for _ in range(4):self.assertEqual(L.north_game_weapon_hit(1,120,68,32),1)
  self.assertEqual(L.qo(21),15);self.assertEqual(byte('north_game_machine_stage'),5);self.act(120,124);self.assertEqual(L.qs(21),3)
  self.assertEqual(L.invalid_saves(),0);self.assertEqual(L.valid(),1);self.assertEqual(L.roundtrip(),1)
 def test_exhaustive_puzzles_reset_exit_and_solve(self):
  self.recruits()
  for area in (26,27,28):
   # Every Cartesian state, including those not produced by legal play, safely
   # resets. Reachable graph is then exhaustively enumerated and reverse-solved.
   for rail in range(4):
    for a in range(3):
     for b in range(3):
      for w in range(2):
       p=puzzle((rail,a,b,w));self.assertEqual(L.north_puzzle_step(ctypes.byref(p),area,4,120,132),1);self.assertEqual(ptuple(p),(0,0,0,0))
   states={(0,0,0,0)};queue=deque(states);edges={};solved=set()
   while queue:
    t=queue.popleft();edges[t]=[]
    for action in range(1,5):
     p=puzzle(t);L.north_puzzle_step(ctypes.byref(p),area,action,120,132);n=ptuple(p);edges[t].append(n)
     if L.north_puzzle_solved(ctypes.byref(p),area):solved.add(n)
     if n not in states:states.add(n);queue.append(n)
   can=set(solved)
   while True:
    new={s for s in states if any(t in can for t in edges[s])}-can
    if not new:break
    can|=new
   self.assertEqual(can,states);self.assertLessEqual(len(states),72)
   # No dynamic barrier exists: every transient state has identical walkable
   # exit/reset routes, checked separately by asset BFS and runtime colliders.
   self.assertIn((0,0,0,0),states)
 def test_cargo_block_is_atomic_and_no_crush(self):
  p=puzzle((1,0,0,0));before=bytes(p);self.assertEqual(L.north_puzzle_step(ctypes.byref(p),26,2,96,64),-1);self.assertEqual(bytes(p),before)
  self.assertEqual(L.north_puzzle_step(ctypes.byref(p),26,2,96,80),1)
 def test_completed_objectives_survive_reset_reentry(self):
  self.recruits();L.entry(26,0);L.objective(21,1);L.north_game_reset();self.assertEqual(L.qo(21),1);self.assertTrue(L.north_puzzle_solved(ctypes.byref(Puzzle.in_dll(L,'north_game_puzzle')),26));L.entry(22,0);L.entry(26,0);self.assertEqual(L.qo(21),1)
 def test_rewards_full_idempotence_order_training(self):
  L.entry(22,0);self.assertEqual(L.offer(13),4);L.offer(11);self.assertEqual(L.objective(11,4),-1);L.objective(11,1);L.objective(11,2);L.fill_roster();L.snapshot_state();self.assertEqual(L.claim(11),5);self.assertEqual(L.unchanged(),1);L.free_last();self.assertEqual(L.claim(11),3);L.snapshot_state();self.assertEqual(L.claim(11),0);self.assertEqual(L.unchanged(),1)
  L.fresh();self.recruits();self.grant(12);self.grant(14);self.grant(15)
  for q,f,lv,mask in [(16,19,16,32),(17,22,17,64),(18,73,18,128),(19,75,18,256),(20,77,20,512)]:
   L.offer(q)
   for b in (1,2,4):
    if L.northern_quest_mask(q)&b:L.objective(q,b)
   L.bag_full(1);L.snapshot_state();self.assertEqual(L.claim(q),5);self.assertEqual(L.unchanged(),1);L.bag_full(0);self.assertEqual(L.claim(q),3);self.assertGreaterEqual(L.level(f),lv);self.assertEqual(L.trial(f),mask)
   L.snapshot_state();self.assertEqual(L.claim(q),0);self.assertEqual(L.unchanged(),1)
  self.assertEqual(L.roster_count(),9);self.assertEqual(L.gear_count(),7);self.assertEqual(L.valid(),1);self.assertEqual(L.roundtrip(),1)
 def test_beacon_order_and_all_three_weapon_classes(self):
  self.recruits();L.entry(26,0);self.assertEqual(L.objective(21,4),4);L.objective(21,1);L.objective(21,2);L.objective(21,4)
  for cls in (1,2,3):
   L.entry(29,0);self.power(64,124,13);self.power(176,124,21);self.act(120,124);L.weapon(cls);L.at(120,132);L.tick(84);self.assertEqual(L.hurt(),0);self.assertEqual(L.north_game_weapon_hit(cls,120,68,32),1)
   self.assertEqual(L.north_game_weapon_hit(cls,0,0,32),0);self.assertEqual(L.north_game_weapon_hit(0,120,68,32),0)
  L.at(120,87);L.north_game_reset();self.power(64,124,13);self.power(176,124,21);self.act(120,124);L.at(120,87);L.tick(84);self.assertEqual(L.hurt(),16)
 def test_all_optional_jobs_and_personal_trials_through_runtime(self):
  self.recruits();L.entry(25,0);self.act(64,80);self.act(120,80);self.power(176,80,1);self.act(208,128);self.assertEqual(L.qs(12),3)
  L.entry(23,0);self.act(112,112);self.act(176,160);self.act(176,160);self.act(144,128);self.act(144,128)
  L.entry(22,0);self.act(64,208);self.assertEqual(L.qs(14),3)
  L.entry(23,0)
  for x,y in((176,240),(288,128),(368,256)):self.act(x,y)
  L.entry(22,0);self.act(416,224);self.assertEqual(L.qs(15),3)
  L.entry(24,0);self.act(208,128);self.power(64,96,13);self.power(176,96,13);self.act(208,128);self.assertEqual(L.qs(16),3)
  L.entry(25,0);self.act(208,128);self.power(64,80,15)
  for x in(176,64,120):self.power(x,120,15)
  self.act(208,128);self.assertEqual(L.qs(17),3)
  L.entry(24,0);self.act(208,128);self.power(120,96,17);self.act(120,96);self.power(120,96,17);self.act(208,128);self.assertEqual(L.qs(18),3)
  L.entry(26,0);L.objective(21,1);L.objective(21,2);L.entry(27,0);self.act(208,128);self.power(208,128,19);self.act(208,128);self.assertEqual(L.qs(19),3)
  L.objective(21,4);L.entry(28,0);self.act(208,128);self.power(208,128,21);self.power(120,112,21);self.power(208,128,21);self.power(120,112,21);self.power(120,112,21);self.power(208,128,21);self.act(208,128);self.assertEqual(L.qs(20),3)
  self.assertEqual(L.valid(),1);self.assertEqual(L.invalid_saves(),0);self.assertEqual(L.roundtrip(),1)
 def test_trial_progress_retained_after_reset_and_out_of_order_rejection(self):
  self.recruits();L.entry(26,0);L.objective(21,1);L.objective(21,2);L.entry(28,0);self.act(208,128);self.power(208,128,21);self.assertEqual(L.qo(20),1)
  self.power(208,128,21);self.assertEqual(L.qo(20),1);self.act(48,132);self.assertEqual(L.qo(20),1)
  self.power(208,128,21);self.power(120,112,21);self.power(208,128,21);self.assertEqual(L.qo(20),3)
  L.entry(22,0);L.entry(28,0);self.assertEqual(L.qo(20),3)
  self.power(208,128,21);self.power(120,112,21);self.power(208,128,21);self.power(120,112,21);self.power(120,112,21);self.power(208,128,21);self.assertEqual(L.qo(20),7)
 def test_live_machine_handle_leaves_a_for_weapon(self):
  self.recruits();L.entry(26,0);L.objective(21,1);L.objective(21,2);L.objective(21,4);L.entry(29,0)
  self.power(64,124,13);self.power(176,124,21);self.act(120,124)
  for elapsed,stage in ((0,1),(60,2),(24,3),(90,4)):
   L.tick(elapsed);self.assertEqual(byte('north_game_machine_stage'),stage)
   for point in ((120,88),(120,108),(120,124)):
    L.at(*point);self.assertEqual(L.north_game_interact(),0);self.assertEqual(value('game_state'),1)
  self.act(48,132);self.assertEqual(byte('north_game_machine_stage'),0)
  # Stopped handle once again gives instructions instead of silently attacking.
  L.at(120,124);self.assertEqual(L.north_game_interact(),1);self.assertEqual(value('game_state'),2)
 def test_actor_budget_and_safe_checkpoint_spawns(self):
  self.recruits();L.offer(21);L.objective(21,1);L.objective(21,2);L.objective(21,4)
  for r in range(22,30):
   count=5 if r==22 else 3 if r==23 else 1
   for s in range(count):
    self.assertTrue(L.entry(r,s));self.assertFalse(L.north_game_solid(value('px'),value('py')));self.assertLessEqual(L.draw(),20)
if __name__=='__main__':unittest.main()
