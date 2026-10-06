#!/usr/bin/env python3
"""Production Southern runtime with read-only historical fixture + synthetic input.
This verifies module behavior, NOT controller-native collection/obtainability.
"""
from pathlib import Path
import ctypes as C,itertools,json,os,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
TMP=tempfile.TemporaryDirectory(prefix='south-runtime-');OUT=Path(TMP.name)
UI=json.loads((ROOT/'assets/southern_region/ui_additions.json').read_text())
UI.update({'MG_RESERVED': '', 'MG_RESERVEDB': ''})  # Host-only imported current capacity-refusal labels
(OUT/'south_game_test_ui.h').write_text('enum{'+','.join('TX_'+k+'='+str(3000+i) for i,k in enumerate(UI))+'};\n')
HARNESS=r'''
#include <string.h>
#include <limits.h>
#include "south_game.h"
#include "south_art.h"
#include "southern_quests.h"
#include "progression.h"
Save5State adventure_save;
unsigned progression_revision,progression_forms[PROGRESSION_SPIRIT_COUNT];
volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
volatile unsigned chapter_flags;
int face,keys,journal_tab;
static unsigned saved,invalid,hurt_calls,actors,last_toast,weapon_class=1;
unsigned camera_maxima[8];
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
void south_actor(unsigned a,int x,int y){(void)a;if(x-camera_x>-8&&x-camera_x<248&&y-camera_y>-8&&y-camera_y<168)actors++;}
void region_form_actor(unsigned a,int x,int y){south_actor(a,x,y);}
void game_health_fill(void){}
void game_region_warp(int x,int y){px=x;py=y;}
unsigned game_weapon_class(void){return weapon_class;}
void game_north_hurt(unsigned d){hurt_calls+=d;}
void enter_room(int r,int s){if(r>=30)south_game_enter((unsigned)r,(unsigned)s);else{room=r;checkpoint_spawn=s;}}
int fresh(void){save5_test_reset_writer();save5_test_fail_after(-1);memset(&adventure_save,0,sizeof adventure_save);if(!save5_load(&adventure_save))return 0;chapter_flags=adventure_save.campaign.chapter_flags;room=adventure_save.campaign.room;checkpoint_spawn=adventure_save.campaign.spawn;game_state=summoned=1;face=keys=transition_lock=camera_x=camera_y=0;saved=invalid=hurt_calls=actors=0;weapon_class=1;south_game_reset();return save5_validate(&adventure_save);}
void at(int x,int y){px=x;py=y;game_state=1;face=1;keys=0;}
int entry(unsigned r,unsigned s){game_state=1;return south_game_enter(r,s);}
unsigned select_form(unsigned form){unsigned i,j;for(i=0;i<160;i++)if(adventure_save.roster.instances[i].form_id==form){for(j=0;j<4;j++)if(adventure_save.roster.party[j]==i)break;if(j<4){unsigned t=adventure_save.roster.party[0];adventure_save.roster.party[0]=(CreatureU8)i;adventure_save.roster.party[j]=(CreatureU8)t;}else adventure_save.roster.party[0]=(CreatureU8)i;adventure_save.roster.selected_party=0;return i;}return 255;}
void select_slot(unsigned i){unsigned j;for(j=0;j<4;j++)if(adventure_save.roster.party[j]==i)break;if(j<4){unsigned t=adventure_save.roster.party[0];adventure_save.roster.party[0]=(CreatureU8)i;adventure_save.roster.party[j]=(CreatureU8)t;}else adventure_save.roster.party[0]=(CreatureU8)i;adventure_save.roster.selected_party=0;}
unsigned duplicate(unsigned form){return creatures_grant(&adventure_save.roster,form,18,20,0,0);}
unsigned qs(unsigned q){return save5_quest_state(&adventure_save.quests,q);}
unsigned qo(unsigned q){return adventure_save.quests.objectives[q];}
unsigned source(unsigned t){return southern_source_claimed(&adventure_save,t);}
unsigned flags(unsigned b){return adventure_save.quests.region_flags[b];}
unsigned roster_count(void){return creatures_roster_count(&adventure_save.roster);}
unsigned invalid_saves(void){return invalid;}
int valid(void){return save5_validate(&adventure_save);}
void snapshot_state(void){snapshot=adventure_save;}
int unchanged(void){return !memcmp(&snapshot,&adventure_save,sizeof snapshot);}
int roundtrip(void){Save5State r;if(!save5_store(&adventure_save)||!save5_load(&r))return 0;return !memcmp(&adventure_save.quests,&r.quests,sizeof r.quests)&&!memcmp(&adventure_save.roster,&r.roster,sizeof r.roster)&&!memcmp(&adventure_save.equipment,&r.equipment,sizeof r.equipment);}
void tick(unsigned n){while(n--)south_game_tick();}
void modal(unsigned m){game_state=(int)m;}
void summon(unsigned m){summoned=(int)m;}
void weapon(unsigned w){weapon_class=w;}
unsigned hurt(void){return hurt_calls;}
unsigned draw(int x,int y){actors=0;camera_x=x;camera_y=y;south_game_draw_actors();south_game_draw_overlay();south_game_draw_journal();return actors;}
void direction(int k){keys=k;game_state=1;}
unsigned trial(unsigned slot){return slot<160?adventure_save.roster.instances[slot].trial_flags:0;}
unsigned level(unsigned slot){return slot<160?adventure_save.roster.instances[slot].level:0;}
unsigned bond(unsigned slot){return slot<160?adventure_save.roster.instances[slot].bond:0;}
unsigned encounter_spawns(unsigned area){const SouthEnemySpawn*e;unsigned n=south_game_enemy_spawns(area,&e),i;int oldroom=room;room=(int)area;for(i=0;i<n;i++)if(south_game_solid(e[i].x,e[i].y)||e[i].phase>=5||(e[i].kind!=0&&e[i].kind!=2)||!e[i].hp){room=oldroom;return 255;}room=oldroom;return n;}
unsigned max_camera_actors(void){const SouthEnemySpawn*e;unsigned n=south_game_enemy_spawns((unsigned)room,&e),i,max=0;int x,y,mx=room<32?240:0,my=room<32?160:0;for(y=0;y<=my;y++)for(x=0;x<=mx;x++){unsigned count=draw(x,y);for(i=0;i<n;i++)if(e[i].kind==2&&e[i].x-x>-8&&e[i].x-x<248&&e[i].y-y>-8&&e[i].y-y<168)count++;if(count>max)max=count;}if(room>=30&&room<=37&&max>camera_maxima[room-30])camera_maxima[room-30]=max;return max;}
int collision_equivalence(void){unsigned a,i;int x,y,old=room;for(a=30;a<=37;a++){const SouthArtRoom*r=&south_art_rooms[a-30];room=(int)a;for(y=-6;y<r->height+6;y++)for(x=-6;x<r->width+6;x++){int expected=x<5||y<5||x>r->width-6||y>r->height-6;for(i=0;i<r->solid_count;i++){const SouthArtRect*s=&r->solids[i];if(x+5>=s->x&&x-5<s->x+s->w&&y+5>=s->y&&y-5<s->y+s->h)expected=1;}if(south_game_solid(x,y)!=expected){room=old;return (int)a;}}if(!south_game_solid(INT_MIN,INT_MAX)||!south_game_solid(INT_MAX,INT_MIN)){room=old;return -1;}}room=old;return 0;}
'''
(OUT/'h.c').write_text(HARNESS)
sources=['src/south_game.c','src/south_art.c','src/southern_quests.c','src/northern_quests.c','src/save5.c','src/save4.c','src/equipment.c','src/equipment_data.c','src/creatures.c','src/creature_data.c']
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC','-DSOUTH_GAME_HOST_TEST','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST','-Isrc','-I'+str(OUT),str(OUT/'h.c'),*sources,*(['-fsanitize=undefined','-fno-sanitize-recover=all'] if os.environ.get('SOUTH_SANITIZE') else []),'-o',str(OUT/'test.so')],cwd=ROOT,check=True)
L=C.CDLL(str(OUT/'test.so'))
class Puzzle(C.Structure):_fields_=[('mirror',C.c_ubyte*2),('shade',C.c_ubyte)]
class Beam(C.Structure):_fields_=[('x1',C.c_short),('y1',C.c_short),('x2',C.c_short),('y2',C.c_short),('end_kind',C.c_ubyte)]
L.south_puzzle_step.argtypes=[C.POINTER(Puzzle),C.c_uint,C.c_uint]
L.south_puzzle_solved.argtypes=[C.POINTER(Puzzle),C.c_uint]
L.south_puzzle_beam.argtypes=[C.POINTER(Puzzle),C.c_uint,C.POINTER(Beam)]
SRAM=(C.c_ubyte*32768).in_dll(L,'save5_test_sram')
FIXTURE=(ROOT/'tests/fixtures/v5-revision3/northern-all21-town.sav').read_bytes()
def val(n):return C.c_int.in_dll(L,n).value
def byte(n):return C.c_ubyte.in_dll(L,n).value
def puzzle(t):return Puzzle((C.c_ubyte*2)(t[0],t[1]),t[2])
class SouthRuntime(unittest.TestCase):
 def setUp(self):SRAM[:]=FIXTURE;self.assertEqual(L.fresh(),1)
 def entry(self,r,s=0):self.assertEqual(L.entry(r,s),1);self.assertLessEqual(L.max_camera_actors(),20,(r,s))
 def act(self,x,y):L.at(x,y);self.assertEqual(L.south_game_interact(),1,(val('room'),x,y))
 def power(self,x,y,form=None,want=1):
  if form:self.assertLess(L.select_form(form),160)
  L.at(x,y);self.assertEqual(L.south_game_power(0),want,(val('room'),x,y,form))
 def guarantees(self):
  self.entry(30);self.act(144,176);self.act(192,192);self.act(192,240);self.act(192,208);self.act(144,176);self.assertEqual(L.qs(22),3)
  self.entry(31);self.act(352,176);self.act(304,208);self.act(352,208);self.act(352,176);self.assertEqual(L.qs(23),3);self.assertEqual(L.valid(),1)
 def main_to35(self):
  self.guarantees();self.entry(34);self.act(112,72);self.power(112,120,79);self.assertEqual(L.qo(24),1);self.entry(35)
 def main_to37(self):
  self.main_to35();self.act(112,72);self.act(96,104);self.act(176,96);self.power(208,104,85);self.assertEqual(L.qo(24),3);self.entry(36);self.act(80,120);self.act(80,64);self.act(176,120);self.assertEqual(L.qo(24),7);self.entry(37)
 def test_all_optical_states_bounded_and_reset_solvable(self):
  for area in (34,35,36):
   solutions=[]
   for t in itertools.product(range(2),repeat=3):
    p=puzzle(t);b=(Beam*4)();n=L.south_puzzle_beam(C.byref(p),area,b);self.assertTrue(1<=n<=4)
    for seg in b[:n]:self.assertTrue(seg.x1==seg.x2 or seg.y1==seg.y2)
    if L.south_puzzle_solved(C.byref(p),area):solutions.append(t)
    for action in (1,2,3,4):
     q=Puzzle.from_buffer_copy(p);r=L.south_puzzle_step(C.byref(q),area,action);self.assertIn(r,(-1,1))
     if action==4:self.assertEqual(tuple(q.mirror),(1,1) if area==36 else (0,0));self.assertEqual(q.shade,1)
   self.assertTrue(solutions)
   # Every authored arrangement reaches a solution through only manual inputs.
   for initial in itertools.product(range(2),repeat=3):
    pending=[initial];seen={initial};found=False
    while pending:
     t=pending.pop();p=puzzle(t)
     if L.south_puzzle_solved(C.byref(p),area):found=True;break
     for action in (1,2,3,4):
      q=Puzzle.from_buffer_copy(p)
      if L.south_puzzle_step(C.byref(q),area,action)<0:continue
      nxt=tuple(q.mirror)+(q.shade,)
      if nxt not in seen:seen.add(nxt);pending.append(nxt)
    self.assertTrue(found,(area,initial))
  for bad in ((2,0,0),(0,255,0),(0,0,2)):
   p=puzzle(bad);before=bytes(p);self.assertEqual(L.south_puzzle_step(C.byref(p),34,4),-1);self.assertEqual(bytes(p),before)
 def test_guaranteed_route_manual_controls_cannot_bypass(self):
  self.entry(30);self.assertEqual(L.entry(34,0),0);self.guarantees();self.entry(34);L.snapshot_state();self.act(112,72);self.assertEqual(L.qo(24),0);self.power(112,120,85,2);self.assertEqual(L.qo(24),0);self.power(112,120,79);self.assertEqual(L.qo(24),1)
  self.entry(35);self.act(112,72);self.act(96,104);self.act(176,96);self.assertEqual(L.qo(24),1);self.power(208,104,79,2);self.assertEqual(L.qo(24),1);self.power(208,104,85);self.assertEqual(L.qo(24),3);self.assertEqual(L.invalid_saves(),0)
 def test_power_capability_is_selected_active_and_command_independent(self):
  self.guarantees();self.entry(34);self.act(112,72);L.select_form(79);L.summon(0);self.power(112,120,want=2);self.assertEqual(L.qo(24),0);L.summon(1);L.at(112,120);self.assertEqual(L.south_game_power(0xffffffff),1);self.assertEqual(L.qo(24),1)
 def test_all_exits_resets_and_modal_freeze(self):
  self.main_to37();self.act(120,112);L.modal(3);t=byte('south_game_machine_ticks');L.tick(200);self.assertEqual(byte('south_game_machine_ticks'),t);self.assertEqual(L.south_game_power(27),0);self.assertEqual(L.south_game_interact(),0)
  for area in range(32,38):
   self.entry(area);L.snapshot_state();self.act(48,132);self.assertEqual(L.qo(24),7);self.assertEqual(L.unchanged(),1);self.act(120,148);self.assertEqual(val('room'),30 if area==32 else 31 if area in (33,34) else area-1)
 def test_boss_all_weapon_classes_damage_only_exposure_and_mobile_telegraph(self):
  for w in (1,2,3):
   self.setUp();self.main_to37();self.act(120,112);L.at(24,112);L.weapon(w);self.assertEqual(L.south_game_weapon_hit(w,120,64,144),0);L.tick(60);self.assertEqual(byte('south_game_machine_stage'),2);L.tick(40);self.assertEqual(byte('south_game_machine_stage'),3);self.assertEqual(L.hurt(),0);self.assertEqual(L.south_game_weapon_hit(w,152,64,144),0);self.act(192,112);L.at(152,84);self.assertEqual(L.south_game_weapon_hit(w,152,64,144),1);self.assertEqual(L.qo(24),15);self.act(120,112);self.assertEqual(L.qs(24),3);self.assertEqual(L.roundtrip(),1);self.act(120,112);self.assertEqual(val('room'),30)
 def optional(self):
  self.guarantees();self.entry(31)
  for xy in ((128,224),(160,224),(144,208),(128,80),(160,80),(384,240),(416,240),(400,208),(256,144),(224,144),(256,112)):self.act(*xy)
  self.entry(33)
  for xy in ((208,48),(40,72),(56,48),(112,48),(168,48),(176,96)):self.act(*xy)
  self.entry(32)
  for xy in ((48,48),(176,48),(72,80),(168,80)):self.act(*xy)
  self.entry(30);self.act(240,176);self.entry(32);self.act(120,112);self.entry(31);self.act(288,96)
  self.assertEqual(L.flags(8),255)
 def test_all_eight_encounters_clues_prerequisites_idempotence(self):
  self.guarantees();self.entry(31);n=L.roster_count()
  for xy in ((144,208),(160,80),(400,208),(256,112),(288,96)):self.act(*xy)
  self.assertEqual(L.roster_count(),n);self.setUp();self.optional();self.assertEqual(L.roster_count(),21);self.assertEqual(L.roundtrip(),1)
  n=L.roster_count();self.act(288,96);self.assertEqual(L.roster_count(),n);self.assertEqual(L.valid(),1);self.assertEqual(L.invalid_saves(),0)
 def test_all_side_quests_visible_actions(self):
  self.optional();self.entry(30)
  for xy in ((312,192),(280,208),(312,208),(344,208),(312,192),(64,224),(144,144),(320,144),(64,224),(352,240),(128,248),(384,248),(352,240),(112,176),(48,176)):self.act(*xy)
  for q in (25,26,27,28,29):self.assertEqual(L.qs(q),3,q)
  self.assertEqual(L.invalid_saves(),0);self.assertLessEqual(L.max_camera_actors(),20)
 def start(self,form,area):
  self.entry(area);slot=L.select_form(form);self.assertLess(slot,160)
  self.act(*{30:(432,224),31:(240,256),32:(208,132),33:(32,104),35:(208,132)}[area]);return slot
 def test_ten_personal_trials_actual_geometry_and_training(self):
  self.optional()
  s=self.start(25,31);self.power(128,208);self.power(176,160);self.entry(32);self.power(56,120);self.assertEqual(L.trial(s),1);self.assertLessEqual(L.max_camera_actors(),20)
  s=self.start(28,33)
  for x in (56,112,168):self.power(x,96)
  self.assertEqual(L.trial(s),1);self.assertLessEqual(L.max_camera_actors(),20)
  s=self.start(79,30);self.act(192,176);self.power(160,208);self.act(192,176);self.power(208,208);self.act(192,176);self.power(256,208);self.assertEqual(L.trial(s),1);self.assertLessEqual(L.max_camera_actors(),20)
  s=self.start(81,33);self.act(208,128)
  for x in (56,112,168):self.power(x,112)
  self.assertEqual(L.trial(s),1);self.assertLessEqual(L.max_camera_actors(),20)
  s=self.start(83,31);self.act(384,240);self.power(368,192);self.act(416,240);self.power(400,192);self.act(384,240);self.power(432,192);self.assertEqual(L.trial(s),1);self.assertLessEqual(L.max_camera_actors(),20)
  self.entry(34);self.act(112,72);self.power(112,120,79)
  s=self.start(85,35);self.act(176,80)
  for xy in ((48,112),(112,128),(176,128)):self.power(*xy)
  self.assertEqual(L.trial(s),1);self.assertLessEqual(L.max_camera_actors(),20)
  s=self.start(87,32);self.act(168,80);self.power(48,80);self.act(72,80);self.act(168,80);self.power(120,80);self.act(72,80);self.power(192,80);self.assertEqual(L.trial(s),1);self.assertLessEqual(L.max_camera_actors(),20)
  s=self.start(89,31)
  for xy in ((224,112),(272,176),(320,112)):self.power(*xy);self.act(*xy)
  self.assertEqual(L.trial(s),1);self.assertLessEqual(L.max_camera_actors(),20)
  s=self.start(91,32);self.act(168,80);self.power(48,48);self.act(168,80);self.power(120,48);self.act(72,80);self.power(192,48);self.assertEqual(L.trial(s),1);self.assertLessEqual(L.max_camera_actors(),20)
  s=self.start(93,33);self.power(56,64);self.act(208,80);self.power(112,64);self.act(208,80);self.power(168,64);self.assertEqual(L.trial(s),1);self.assertLessEqual(L.max_camera_actors(),20)
  for form,lv,bond in ((25,20,40),(28,22,45),(79,20,40),(81,22,45),(83,22,45),(85,20,40),(87,24,45),(89,22,45),(91,24,45),(93,22,45)):
   slot=L.select_form(form);self.assertEqual(L.trial(slot),1,form);self.assertGreaterEqual(L.level(slot),lv);self.assertGreaterEqual(L.bond(slot),bond)
  self.assertEqual(L.valid(),1);self.assertEqual(L.invalid_saves(),0);self.assertEqual(L.roundtrip(),1)
 def test_trial_wrong_order_duplicate_object_wrong_copy_and_reset(self):
  self.optional();s=self.start(28,33);other=L.duplicate(28);self.power(112,96,want=2);self.assertEqual(L.trial(s),0);self.power(56,96);self.power(56,96,want=2);L.select_slot(other);self.power(112,96,want=2);L.select_slot(s);self.power(112,96);self.act(48,132);self.power(168,96,want=0);self.assertEqual(L.trial(s),0);self.assertEqual(L.trial(other),0)
 def test_permanent_shortcuts_and_exact_ferry_return(self):
  self.guarantees();self.entry(32);self.act(208,80);self.assertEqual(val('room'),32)
  self.act(72,80);self.act(168,80);self.assertEqual(L.qs(29),2);self.act(208,80);self.assertEqual(val('room'),30);self.assertEqual(val('checkpoint_spawn'),4)
  self.entry(32);self.act(208,80);self.assertEqual(val('room'),30)
  self.main_to37();self.entry(36);self.act(208,128);self.assertEqual(val('room'),31);self.assertEqual(val('checkpoint_spawn'),1)
  self.entry(30);self.act(240,264);self.assertEqual((val('room'),val('px'),val('py'),val('checkpoint_spawn')),(22,208,224,0))
 def test_invalid_entries_and_npc_talk_do_not_grant_objectives(self):
  for area,spawn in ((29,0),(38,0),(0xffffffff,0),(30,5),(31,4),(32,1)):
   L.snapshot_state();self.assertEqual(L.entry(area,spawn),0);self.assertEqual(L.unchanged(),1)
  self.entry(30);self.act(144,176);self.assertEqual(L.qs(22),1);self.assertEqual(L.qo(22),0);n=L.roster_count();self.act(144,176);self.assertEqual(L.roster_count(),n);self.assertEqual(L.qo(22),0)
 def test_facing_stall_uses_marked_approach_without_sideways_porter(self):
  self.entry(30)
  # Authored scene approach, facing up: the third stall is directly ahead,
  # while the closer porter is eight pixels to the right on the same row.
  self.act(344,224);self.assertEqual(L.qo(25),4);self.assertEqual(L.qs(27),0)
  # The same standing point, turned right, deliberately addresses the porter.
  L.at(344,224);C.c_int.in_dll(L,'face').value=3
  self.assertEqual(L.south_game_interact(),1);self.assertEqual(L.qs(27),1);self.assertEqual(L.qo(25),4)
  # His original below/left/right approaches remain usable without touching
  # the stall. Repeat-talk does not fabricate a delivery objective.
  for x,y,facing in ((352,240,1),(336,224,3),(368,224,2),(352,208,0)):
   L.at(x,y);C.c_int.in_dll(L,'face').value=facing;self.assertEqual(L.south_game_interact(),1);self.assertEqual(L.qo(27),0)
  self.assertEqual(L.qo(25),4);self.assertEqual(L.invalid_saves(),0)
  # Native trace's closer approach also crossed the previous backward +8
  # tolerance boundary: the porter must not intercept that position either.
  self.setUp();self.entry(30);self.act(343,216);self.assertEqual(L.qo(25),4);self.assertEqual(L.qs(27),0)
 def test_conservative_all_conditional_actor_positions_fit_every_camera(self):
  # Superstates intentionally combine mutually exclusive conditions, such as
  # unclaimed teaching companion plus completed trial, so they bound every
  # reachable quest/recruit arrangement rather than only the sampled journey.
  town=[(144,160),(112,160),(312,176),(64,208),(352,224),(400,192),(48,160),(112,208),(240,264),(192,176),(240,176),(432,208),(280,208),(312,208),(344,208),(192,240),(192,208),(144,128),(320,128),(128,248),(384,248),(176,160),(400,216),(160,192),(208,192),(256,192)]
  field=[(352,160),(80,248),(240,240),(384,240),(416,240),(304,192),(352,192),(128,224),(160,224),(128,80),(224,144),(144,208),(160,80),(400,208),(256,112),(288,96),(336,144),(432,128),(336,64)]
  for points in [town,field+[(128,192),(176,144)],field+[(368,176),(400,176),(432,176)],field+[(224,112),(272,176),(320,112)]]:
   for x in range(241):
    ys=[py for px,py in points if x-8<px<x+248]
    for y in range(161):self.assertLessEqual(sum(y-8<py<y+168 for py in ys),20,(x,y))
 def test_exact_collision_and_enemy_spawns_and_actor_budget(self):
  self.assertEqual(L.collision_equivalence(),0);self.optional()
  for r,n in ((30,0),(31,5),(33,2),(37,0)):self.assertEqual(L.encounter_spawns(r),n)
  for area in range(30,34):
   self.entry(area);self.assertLessEqual(L.max_camera_actors(),20,area)
if __name__=='__main__':
 result=unittest.main(exit=False).result
 print('Maximum regional actor slots by room30–37, including ranged enemies:',list((C.c_uint*8).in_dll(L,'camera_maxima')))
 raise SystemExit(0 if result.wasSuccessful() else 1)
