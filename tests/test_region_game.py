#!/usr/bin/env python3
"""Actual regional C runtime with synthetic engine bridges, not controller QA.

The production quest/reward/save code is linked unmodified. Bag-FULL delivery
is a clearly labeled linker fault injection: 13 unique authored items cannot
naturally fill a 48-slot bag. Roster-FULL is exercised with 160 valid instances.
Crate accessibility is checked over the complete reachable push-state graph.
"""
from collections import deque
from pathlib import Path
import ctypes, json, os, re, subprocess, tempfile, unittest
from PIL import ImageFont
ROOT=Path(__file__).resolve().parents[1]
UI=json.loads((ROOT/'assets/region/ui_additions.json').read_text())
UI.update({'MG_RESERVED': '', 'MG_RESERVEDB': ''})  # Host-only imported current capacity-refusal labels
LAYOUT=json.loads((ROOT/'assets/region/layout.json').read_text())
TMP=tempfile.TemporaryDirectory(prefix='region-game-tests-')
OUT=Path(TMP.name)
(OUT/'region_game_test_ui.h').write_text('enum {\n'+''.join(f'TX_{k}={1000+i},\n' for i,k in enumerate(UI))+'};\n')
HARNESS=r'''
#include <string.h>
#include "region_game.h"
#include "regional_quests.h"
#include "progression.h"
#include "region_game_test_ui.h"
Save5State adventure_save;
unsigned progression_revision,progression_forms[PROGRESSION_SPIRIT_COUNT];
volatile int room,px,py,game_state,summoned,roll_ticks,transition_lock,checkpoint_spawn,camera_x,camera_y;
volatile unsigned chapter_flags;
int face,keys,journal_tab;
static unsigned save_calls,invalid_saves,health_calls,actor_calls,last_a,last_b,last_toast,weapon_class=1,entry_safe=1,bag_full;
static int last_room=-1,last_spawn=-1;
static Save5State snapshot;
CreatureInstance *progression_selected(void){unsigned p=adventure_save.roster.selected_party,s;if(p>=4)return 0;s=adventure_save.roster.party[p];return s<160?&adventure_save.roster.instances[s]:0;}
unsigned progression_command(void){CreatureInstance*c=progression_selected();return c?c->equipped[c->selected_command]:0;}
void progression_refresh(void){progression_revision++;}
void save_game(void){save_calls++;if(!save5_validate(&adventure_save))invalid_saves++;}
void dialogue(int a,int b,int next){(void)next;last_a=(unsigned)a;last_b=(unsigned)b;game_state=2;}
void toast(int a){last_toast=(unsigned)a;}
void text(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void centered(int a,int b,int c){(void)a;(void)b;(void)c;}
void box(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void rect(int a,int b,int c,int d,unsigned char e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void line(int a,int b,int c,int d,int e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void sprite(const unsigned char*a,int b,int c,int d,int e,int f){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;}
void region_actor(unsigned a,int b,int c){(void)a;(void)b;(void)c;actor_calls++;}
void region_form_actor(unsigned a,int b,int c){(void)a;(void)b;(void)c;actor_calls++;}
int game_region_entry_safe(void){return (int)entry_safe;}
void game_health_fill(void){health_calls++;}
unsigned game_weapon_class(void){return weapon_class;}
void game_region_warp(int x,int y){px=x;py=y;}
void enter_room(int area,int spawn){last_room=area;last_spawn=spawn;if(area>=16){region_game_enter((unsigned)area,(unsigned)spawn);}else{room=area;checkpoint_spawn=0;px=168;py=264;adventure_save.campaign.room=(Save4U8)area;adventure_save.campaign.spawn=0;}}
unsigned __real_equipment_claim_many(EquipmentState*,const EquipmentU8*,unsigned);
unsigned __wrap_equipment_claim_many(EquipmentState*s,const EquipmentU8*a,unsigned n){return bag_full?EQUIPMENT_FULL:__real_equipment_claim_many(s,a,n);}
void test_fresh(unsigned flags){memset(&adventure_save,0,sizeof adventure_save);chapter_flags=flags;adventure_save.campaign.chapter_flags=(Save4U8)flags;
 adventure_save.campaign.story_seen=(Save4U16)((flags&1?2:0)|(flags&2?8:0)|(flags&8?32:0));creatures_migrate_legacy(&adventure_save.roster,flags,0);equipment_init(&adventure_save.equipment);
 room=0;px=120;py=132;game_state=1;summoned=1;roll_ticks=transition_lock=checkpoint_spawn=0;keys=face=journal_tab=0;camera_x=camera_y=0;
 save_calls=invalid_saves=health_calls=actor_calls=last_a=last_b=last_toast=bag_full=0;entry_safe=1;weapon_class=1;last_room=last_spawn=-1;region_game_journal_selection=0;region_game_reset();
}
int test_enter(unsigned area,unsigned spawn){game_state=1;keys=0;return region_game_enter(area,spawn);}
void test_at(int x,int y,unsigned f){px=x;py=y;face=(int)f;game_state=1;keys=0;}
int test_select(unsigned cmd){unsigned i,j,k;for(i=0;i<160;i++){CreatureInstance*c=&adventure_save.roster.instances[i];if(!(c->flags&CREATURE_OCCUPIED)||!creatures_command_learned(c->form_id,c->level,cmd))continue;
 for(j=0;j<4;j++)if(adventure_save.roster.party[j]==i)break;
 if(j<4){unsigned old=adventure_save.roster.party[0];adventure_save.roster.party[0]=(CreatureU8)i;adventure_save.roster.party[j]=(CreatureU8)old;}else adventure_save.roster.party[0]=(CreatureU8)i;
 adventure_save.roster.selected_party=0;for(k=0;k<2;k++)if(c->equipped[k]==cmd){creatures_select_command(c,k);return 1;}
 if(!creatures_equip(c,0,cmd))return 0;
 return creatures_select_command(c,0);
 }return 0;}
void test_unsummon(void){summoned=0;}
void test_summon(void){summoned=1;}
void test_weapon(unsigned c){weapon_class=c;}
void test_keys(int k,int rolling){keys=k;roll_ticks=rolling;game_state=1;}
void test_lock(int lock){transition_lock=lock;}
void test_entry_safe(unsigned b){entry_safe=b;}
void test_force_bag_full(unsigned b){bag_full=b;}
unsigned test_state(unsigned q){return save5_quest_state(&adventure_save.quests,q);}
unsigned test_objectives(unsigned q){return adventure_save.quests.objectives[q];}
unsigned test_variable(unsigned q){return adventure_save.quests.variables[q];}
unsigned test_equipment(void){return equipment_count(&adventure_save.equipment);}
unsigned test_roster(void){return creatures_roster_count(&adventure_save.roster);}
unsigned test_saves(void){return save_calls;}
unsigned test_invalid_saves(void){return invalid_saves;}
unsigned test_health_calls(void){return health_calls;}
unsigned test_last_a(void){return last_a;}
unsigned test_last_toast(void){return last_toast;}
int test_last_room(void){return last_room;}
int test_last_spawn(void){return last_spawn;}
unsigned test_campaign_room(void){return adventure_save.campaign.room;}
unsigned test_campaign_spawn(void){return adventure_save.campaign.spawn;}
unsigned test_campaign_flags(void){return adventure_save.campaign.chapter_flags;}
void test_stale_campaign_flags(void){adventure_save.campaign.chapter_flags=0;}
int test_valid(void){return save5_validate(&adventure_save);}
void test_snapshot(void){snapshot=adventure_save;}
int test_unchanged(void){return memcmp(&snapshot,&adventure_save,sizeof snapshot)==0;}
void test_fill_roster(void){while(creatures_roster_count(&adventure_save.roster)<160)if(creatures_grant(&adventure_save.roster,1,1,0,0,0)==255)break;}
void test_free_last(void){unsigned i;for(i=160;i>0;i--)if(adventure_save.roster.instances[i-1].flags==CREATURE_OCCUPIED){memset(&adventure_save.roster.instances[i-1],0,sizeof(CreatureInstance));adventure_save.roster.expedition_bond[i-1]=0;break;}}
void test_all_wishes(void){unsigned i;for(i=0;i<160;i++){CreatureInstance*c=&adventure_save.roster.instances[i];unsigned f=creatures_legacy_spirit(c->form_id);if((c->flags&CREATURE_STORY_LOCKED)&&f<4)creatures_mark_trial(c,1u<<f);}}
int test_water_evolve(void){unsigned i;for(i=0;i<160;i++)if(adventure_save.roster.instances[i].form_id==13)return (int)creatures_evolve(&adventure_save.roster,i,(chapter_flags&7)|8,1,1);return -1;}
unsigned test_water_trial(void){unsigned i;for(i=0;i<160;i++)if(adventure_save.roster.instances[i].form_id==13||adventure_save.roster.instances[i].form_id==14)return adventure_save.roster.instances[i].trial_flags;return 0;}
int test_roundtrip(void){Save5State restored;if(!save5_store(&adventure_save)||!save5_load(&restored))return 0;return !memcmp(&restored.quests,&adventure_save.quests,sizeof restored.quests)&&!memcmp(&restored.roster,&adventure_save.roster,sizeof restored.roster)&&!memcmp(&restored.equipment,&adventure_save.equipment,sizeof restored.equipment);}
unsigned test_draw(void){actor_calls=0;region_game_draw_actors();region_game_draw_overlay();region_game_draw_journal();return actor_calls;}
void test_menu(unsigned selection){journal_tab=5;region_game_journal_selection=selection;}
void test_crates(int a,int b,int c,int d){region_game_crates[0][0]=(short)a;region_game_crates[0][1]=(short)b;region_game_crates[1][0]=(short)c;region_game_crates[1][1]=(short)d;}
'''
(OUT/'bridges.c').write_text(HARNESS)
SOURCES=['src/region_game.c','src/region_art.c','src/regional_quests.c','src/save5.c','src/save4.c','src/equipment.c','src/equipment_data.c','src/creatures.c','src/creature_data.c']
FLAGS=['-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-DREGION_GAME_HOST_TEST','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST',f'-I{OUT}','-Isrc']
subprocess.run(['cc',*FLAGS,'-shared','-fPIC',str(OUT/'bridges.c'),*SOURCES,'-Wl,--wrap=equipment_claim_many','-o',str(OUT/'runtime.so')],cwd=ROOT,check=True)
LIB=ctypes.CDLL(str(OUT/'runtime.so'))
for name in ('test_fresh','test_at','test_unsummon','test_summon','test_weapon','test_keys','test_lock','test_entry_safe','test_force_bag_full','test_stale_campaign_flags','test_snapshot','test_fill_roster','test_free_last','test_all_wishes','test_menu','test_crates','region_game_tick','region_game_reset'):
    getattr(LIB,name).restype=None

def get_int(name):return ctypes.c_int.in_dll(LIB,name).value

def bytes_array(name,n):return list((ctypes.c_ubyte*n).in_dll(LIB,name))

def foot_block(room,x,y):
    if x<5 or y<5 or x>=room['width']-5 or y>=room['height']-5:return True
    return any(x+5>=rx and x-5<rx+w and y+5>=ry and y-5<ry+h for rx,ry,w,h in [s['rect'] for s in room['solids']])


def crate_graph():
    """Exact 16px rail centers plus real reset/exit approaches, cardinal sweeps."""
    room=LAYOUT['rooms'][4]
    points={(x,y) for x in range(32,209,16) for y in range(40,137,16) if not foot_block(room,x,y)}
    points|={(120,132),(120,136),(120,149),(32,128),(208,96)}
    points=sorted(points);idx={p:i for i,p in enumerate(points)};edges=[[] for _ in points]
    for i,(x,y) in enumerate(points):
        for j,(xx,yy) in enumerate(points):
            if j<=i or (x!=xx and y!=yy) or abs(x-xx)+abs(y-yy)>16:continue
            steps=abs(x-xx)+abs(y-yy)
            if all(not foot_block(room,x+(xx-x)*k//steps,y+(yy-y)*k//steps) for k in range(steps+1)):
                edges[i].append(j);edges[j].append(i)
    rail={(x,y) for x in range(64,177,16) for y in range(56,105,16)}
    def reachable(crates,start):
        forbidden={idx[p] for p in crates};seen={start};q=[start]
        while q:
            p=q.pop()
            for n in edges[p]:
                if n not in forbidden and n not in seen:seen.add(n);q.append(n)
        return seen
    start_crates=((80,88),(144,88));start=idx[(120,132)]
    s=(start_crates,min(reachable(start_crates,start)));queue=deque([s]);parent={s:None};moves={};solved=None
    reset=idx[(32,128)];exit_=idx[(120,149)];spindle=idx[(208,96)]
    dirs=[(0,1,0),(0,-1,1),(-1,0,2),(1,0,3)]
    while queue:
        current=queue.popleft();crates,player=current;seen=reachable(crates,player)
        if reset not in seen or exit_ not in seen:raise AssertionError(('trapped state',current))
        if set(crates)=={(80,56),(160,104)}:
            if spindle not in seen:raise AssertionError('spindle unreachable after correct placement')
            if solved is None:solved=current
        for i,(x,y) in enumerate(crates):
            for dx,dy,f in dirs:
                behind=(x-dx*16,y-dy*16);dest=(x+dx*16,y+dy*16)
                if behind not in idx or idx[behind] not in seen or dest not in rail or dest==crates[1-i]:continue
                new=list(crates);new[i]=dest;new=tuple(new);next_state=(new,min(reachable(new,idx[behind])))
                if next_state not in parent:parent[next_state]=current;moves[next_state]=(behind,f,dest,i);queue.append(next_state)
    if solved is None:raise AssertionError('no crate solution')
    route=[];p=solved
    while parent[p] is not None:route.append(moves[p]);p=parent[p]
    route.reverse()
    return len(parent),route,rail


class RegionRuntimeTests(unittest.TestCase):
    def setUp(self):LIB.test_fresh(15)
    def enter(self,room,spawn=0):self.assertEqual(LIB.test_enter(room,spawn),1)
    def at(self,x,y,face=0):LIB.test_at(x,y,face)
    def interact(self,x,y,face=0):self.at(x,y,face);return LIB.region_game_interact()
    def power(self,cmd,x,y):self.assertEqual(LIB.test_select(cmd),1);self.at(x,y);self.assertEqual(LIB.region_game_power(cmd),1)
    def state(self,q):return LIB.test_state(q)
    def town(self):self.enter(16)
    def water(self):
        self.town();self.enter(17);self.power(2,98,44);self.power(3,184,88);self.assertEqual(self.interact(184,88),1);self.assertEqual(self.state(2),3)
    def metal(self):
        self.water();self.enter(18);self.power(1,48,72);self.power(9,80,120);self.power(3,96,80);self.assertEqual(self.state(3),2);self.interact(96,80);self.assertEqual(self.state(3),3)
    def pools(self):
        self.water();self.enter(19);self.power(9,64,86);self.power(9,176,86);self.interact(64,130);self.interact(176,130);self.assertEqual(self.state(4),3)
    def practice(self):
        self.town();self.interact(320,150);self.interact(432,256);self.interact(456,256)
        for cls in (1,2,3):LIB.test_weapon(cls);self.at(440,296);self.assertEqual(LIB.region_game_practice_hit(cls,440,280),1)
        self.assertEqual(self.state(0),2)

    def test_gate_entry_safe_camp_and_checkpoint_stamping(self):
        LIB.test_fresh(0);self.assertEqual(LIB.test_enter(16,0),0)
        LIB.test_fresh(1);self.assertEqual(LIB.test_enter(18,0),0)
        ctypes.c_int.in_dll(LIB,'room').value=1
        self.assertEqual(self.interact(120,248),0)
        self.assertEqual(self.interact(150,248),0)
        LIB.test_entry_safe(0);self.assertEqual(self.interact(168,248),0)
        LIB.test_entry_safe(1);LIB.test_stale_campaign_flags();self.assertEqual(self.interact(168,248),1)
        self.assertEqual(get_int('room'),16);self.assertEqual(LIB.test_campaign_flags(),1)
        self.assertEqual((get_int('px'),get_int('py')),(240,284))
        self.interact(104,232);self.assertEqual(LIB.test_campaign_spawn(),2);self.assertEqual(LIB.test_health_calls(),1)
        self.assertEqual(LIB.test_invalid_saves(),0);self.assertEqual(LIB.test_valid(),1)
        self.assertEqual(LIB.test_enter(16,6),0)

    def test_practice_requires_actual_hit_and_current_class(self):
        self.town();self.interact(320,150)
        self.assertEqual(self.interact(440,296),0,'The target must not consume A before the actual weapon hit');self.assertEqual(LIB.test_objectives(0),0)
        self.at(440,296);LIB.test_weapon(1)
        self.assertEqual(LIB.region_game_practice_hit(2,440,280),0)
        self.assertEqual(LIB.region_game_practice_hit(1,400,280),0)
        self.assertEqual(LIB.test_objectives(0),0)
        for cls in (1,2,3):LIB.test_weapon(cls);self.assertEqual(LIB.region_game_practice_hit(cls,440,280),1)
        self.assertEqual(LIB.test_objectives(0),7);self.assertEqual(self.state(0),2)
        before=LIB.test_equipment();self.interact(320,150);self.assertEqual(self.state(0),3);self.assertEqual(LIB.test_equipment(),before+1)
        LIB.test_snapshot();self.at(440,296);LIB.region_game_practice_hit(3,440,280);self.assertEqual(LIB.test_unchanged(),1)

    def test_dry_road_order_and_replay(self):
        self.town();self.enter(17);self.power(2,240,199);self.assertEqual(LIB.test_objectives(1),0);self.assertEqual(LIB.region_game_solid(240,168),1)
        self.interact(264,216);self.assertEqual(LIB.test_objectives(1),1)
        self.power(1,240,199);self.assertEqual(LIB.test_objectives(1),1)
        self.power(2,240,199);self.assertEqual(LIB.region_game_solid(240,168),0);self.assertEqual(self.state(1),2)
        self.enter(16);self.interact(264,252);self.assertEqual(self.state(1),3)
        self.enter(17);LIB.test_snapshot();self.interact(264,216);self.assertEqual(LIB.test_unchanged(),1)
        self.assertEqual(LIB.test_invalid_saves(),0)

    def test_water_recruit_wrong_power_unsummoned_and_full_roster_retry(self):
        self.town();self.enter(17)
        self.power(1,98,44);self.assertEqual(LIB.test_objectives(2),0)
        LIB.test_select(2);LIB.test_unsummon();self.at(98,44);self.assertEqual(LIB.region_game_power(2),0);LIB.test_summon()
        self.power(2,98,44);self.power(3,184,88);LIB.test_fill_roster();self.assertEqual(LIB.test_roster(),160)
        self.interact(184,88);self.assertEqual(self.state(2),2);self.assertEqual(LIB.test_roster(),160);self.assertEqual(LIB.test_valid(),1)
        LIB.test_snapshot();self.interact(184,88);self.assertEqual(LIB.test_unchanged(),1)
        LIB.test_free_last();self.interact(184,88);self.assertEqual(self.state(2),3);self.assertEqual(LIB.test_roster(),160)
        count=LIB.test_roster();self.interact(184,88);self.assertEqual(LIB.test_roster(),count);self.assertEqual(LIB.test_invalid_saves(),0)

    def test_foundry_wrong_sequence_reset_reentry_and_metal_latch_ring(self):
        self.water();self.enter(18)
        self.power(9,80,120);self.assertEqual(bytes_array('region_game_foundry_step',1),[0])
        self.power(1,48,72);self.assertEqual(bytes_array('region_game_foundry_step',1),[1])
        self.power(3,96,80);self.assertEqual(bytes_array('region_game_foundry_step',1),[0]);self.assertEqual(LIB.test_objectives(3),0)
        self.power(1,48,72);self.interact(48,128);self.assertEqual(bytes_array('region_game_foundry_step',1),[0])
        self.power(1,48,72);self.enter(16);self.enter(18);self.assertEqual(bytes_array('region_game_foundry_step',1),[0])
        self.power(1,48,72);self.power(9,80,120);self.power(3,96,80);self.assertEqual(self.state(3),2);self.assertEqual(LIB.test_variable(3),3)
        self.interact(96,80);self.assertEqual(self.state(3),3)
        self.power(11,96,80);self.assertEqual(self.state(10),0)
        self.power(1,184,72);self.assertEqual(self.state(7),0)
        self.power(11,184,72);self.assertEqual(self.state(7),3)
        self.power(11,96,80);self.assertEqual(self.state(10),3)
        count=LIB.test_equipment();self.at(184,72);self.assertEqual(LIB.region_game_power(11),0);self.assertEqual(LIB.test_equipment(),count)
        self.assertEqual(LIB.test_invalid_saves(),0);self.assertEqual(LIB.test_roundtrip(),1)

    def test_paired_pools_base_water_trial_reset_and_evolved_shortcut(self):
        self.water();self.enter(19);self.interact(64,130);self.power(9,64,86);self.assertEqual(bytes_array('region_game_pool_levels',2),[0,0])
        self.interact(48,132);self.assertEqual(bytes_array('region_game_valves',2),[0,0])
        self.power(1,64,86);self.assertEqual(bytes_array('region_game_pool_levels',2),[0,0])
        self.power(9,64,86);self.power(9,176,86);self.assertEqual(self.state(4),1)
        self.interact(64,130);self.interact(176,130);self.assertEqual(self.state(4),3);self.assertEqual(LIB.test_water_trial(),16)
        self.assertEqual(LIB.test_water_evolve(),0);self.enter(17);self.power(10,296,140);self.assertEqual((get_int('px'),get_int('py')),(424,124))
        self.power(10,424,124);self.assertEqual((get_int('px'),get_int('py')),(296,140))
        self.enter(19);self.interact(48,132);self.assertEqual(bytes_array('region_game_pool_levels',2),[1,1]);self.assertEqual(bytes_array('region_game_valves',2),[1,1])
        self.assertEqual(LIB.test_invalid_saves(),0);self.assertEqual(LIB.test_valid(),1)

    def test_storehouse_full_state_graph_and_runtime_solution(self):
        states,route,rail=crate_graph();self.assertGreaterEqual(states,900);self.assertGreaterEqual(len(route),4)
        self.town();self.interact(88,152,1);self.enter(20)
        for behind,f,dest,i in route:
            self.at(*behind,f);self.assertEqual(LIB.region_game_solid(*behind),0);self.assertEqual(LIB.region_game_try_push(*behind,f),1)
            crates=list((ctypes.c_short*4).in_dll(LIB,'region_game_crates'));self.assertEqual(tuple(crates[i*2:i*2+2]),dest)
        self.assertEqual(LIB.region_game_plate_mask(),3);self.interact(208,96);self.assertEqual(self.state(5),2)
        self.enter(16);self.enter(20);self.assertEqual(LIB.region_game_plate_mask(),3)
        self.enter(17);count=LIB.test_equipment();self.interact(72,44);self.assertEqual(self.state(5),3);self.assertEqual(LIB.test_equipment(),count+1)
        LIB.test_snapshot();self.interact(72,44);self.assertEqual(LIB.test_unchanged(),1)
        self.assertEqual(LIB.test_invalid_saves(),0)
        print(f'Crate finite-state proof: {states} reachable arrangements/components; reset and exit reachable in every state; shortest solution {len(route)} pushes')

    def test_crate_dead_end_reset_and_all_rooms_exit_without_companion(self):
        self.metal();self.enter(20);self.interact(80,104,1);self.assertEqual(list((ctypes.c_short*4).in_dll(LIB,'region_game_crates'))[:2],[80,72])
        self.enter(16);self.enter(20);self.assertEqual(list((ctypes.c_short*4).in_dll(LIB,'region_game_crates'))[:2],[80,88])
        self.interact(80,104,1);self.interact(48,128);self.assertEqual(list((ctypes.c_short*4).in_dll(LIB,'region_game_crates'))[:2],[80,88])
        for area in (18,19,20,21):
            self.enter(area);LIB.test_unsummon();self.at(120,149);self.assertEqual(LIB.region_game_solid(120,149),0);LIB.test_keys(128,0);LIB.region_game_tick();self.assertEqual(LIB.test_last_room(),17 if area==19 else 16)
        self.enter(16);self.at(240,304);LIB.test_keys(128,0);LIB.test_lock(1);LIB.region_game_tick();self.assertEqual(get_int('room'),16);LIB.test_lock(0);LIB.region_game_tick();self.assertEqual(get_int('room'),1);self.assertEqual(LIB.test_campaign_spawn(),0)

    def test_garden_real_separate_rolls_wrong_order_and_reentry(self):
        self.town();self.enter(21);self.interact(64,136)
        def sensor(x,y,rolling):self.at(x,y);LIB.test_keys(0,rolling);LIB.region_game_tick()
        sensor(72,72,0);self.assertEqual(bytes_array('region_game_garden_step',1),[0])
        sensor(120,72,8);self.assertEqual(bytes_array('region_game_garden_step',1),[0])
        sensor(72,72,0);sensor(72,72,8);self.assertEqual(bytes_array('region_game_garden_step',1),[1])
        sensor(120,72,7);self.assertEqual(bytes_array('region_game_garden_step',1),[1])
        self.enter(16);self.enter(21);self.assertEqual(bytes_array('region_game_garden_step',1),[0])
        for x,y in ((72,72),(120,72),(168,104)):
            sensor(x,y,0);sensor(x,y,8)
        self.assertEqual(self.state(9),2);self.assertEqual(LIB.test_variable(9),3);self.interact(184,64);self.assertEqual(self.state(9),3)
        self.enter(21);self.assertEqual(bytes_array('region_game_garden_step',1),[3]);self.assertEqual(LIB.test_invalid_saves(),0)

    def test_craft_four_wishes_and_fault_injected_bag_retry(self):
        self.practice();LIB.test_force_bag_full(1);self.interact(320,150);self.assertEqual(self.state(0),2)
        LIB.test_snapshot();self.interact(320,150);self.assertEqual(LIB.test_unchanged(),1)
        LIB.test_force_bag_full(0);self.interact(320,150);self.assertEqual(self.state(0),3)
        self.metal();self.enter(18);self.power(4,152,120);self.assertEqual(LIB.test_objectives(8),0)
        self.power(1,48,72);self.power(4,152,120);self.assertEqual(self.state(8),2);self.enter(16);self.interact(320,150);self.assertEqual(self.state(8),3)
        self.interact(182,250);self.assertEqual(self.state(6),1);LIB.test_all_wishes();self.interact(182,250);self.assertEqual(self.state(6),3)
        self.assertEqual(LIB.test_invalid_saves(),0);self.assertEqual(LIB.test_roundtrip(),1)

    def test_sanitized_native_runtime(self):
        smoke=r'''
#include <assert.h>
#include <stdio.h>
static void act(int x,int y,unsigned f){test_at(x,y,f);assert(region_game_interact());}
static void power(unsigned c,int x,int y){assert(test_select(c));test_at(x,y,0);assert(region_game_power(c));}
int main(void){unsigned c;test_fresh(15);assert(test_enter(16,0));act(320,150,0);
 for(c=1;c<=3;c++){test_weapon(c);test_at(440,296,0);assert(region_game_practice_hit(c,440,280));}
 test_force_bag_full(1);act(320,150,0);assert(test_state(0)==2);test_force_bag_full(0);act(320,150,0);assert(test_state(0)==3);
 assert(test_enter(17,0));act(264,216,0);power(2,240,199);assert(test_enter(16,0));act(264,252,0);
 assert(test_enter(17,0));power(2,98,44);power(3,184,88);act(184,88,0);assert(test_state(2)==3);
 assert(test_enter(18,0));power(1,48,72);power(9,80,120);power(3,96,80);act(96,80,0);assert(test_state(3)==3);
 power(11,184,72);power(11,96,80);power(1,48,72);power(4,152,120);assert(test_enter(16,0));act(320,150,0);
 assert(test_enter(19,0));power(9,64,86);power(9,176,86);act(64,130,0);act(176,130,0);assert(test_state(4)==3);
 assert(test_water_evolve()==0);assert(test_enter(17,0));power(10,296,140);assert(px==424&&py==124);
 assert(test_enter(20,0));act(80,104,1);act(80,88,1);act(128,88,3);act(160,72,0);assert(region_game_plate_mask()==3);act(208,96,0);
 assert(test_enter(17,0));act(72,44,0);assert(test_state(5)==3);
 assert(test_enter(21,0));act(64,136,0);
 {static const int xy[3][2]={{72,72},{120,72},{168,104}};for(c=0;c<3;c++){test_at(xy[c][0],xy[c][1],0);test_keys(0,0);region_game_tick();test_keys(0,8);region_game_tick();}}
 act(184,64,0);assert(test_state(9)==3);assert(test_enter(16,0));test_all_wishes();act(182,250,0);
 for(c=0;c<11;c++)assert(test_state(c)==3);
 for(c=16;c<=21;c++){assert(test_enter(c,0));assert(test_draw()<=20);}
 assert(test_invalid_saves()==0);assert(test_valid());assert(test_roundtrip());
 puts("sanitized regional runtime: all 11 quests, replay-safe rewards, native draw bridges and save roundtrip passed");return 0;}
'''
        source=OUT/'sanitized_runtime.c';source.write_text(HARNESS+smoke);exe=OUT/'sanitized_runtime'
        subprocess.run(['cc',*FLAGS,'-fsanitize=address,undefined','-fno-omit-frame-pointer',str(source),*SOURCES,'-Wl,--wrap=equipment_claim_many','-o',str(exe)],cwd=ROOT,check=True)
        subprocess.run([str(exe)],cwd=ROOT,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'),check=True)

    def test_draw_actor_budget_journal_and_strings(self):
        self.metal()
        for area in range(16,22):
            self.enter(area);self.assertLessEqual(LIB.test_draw(),20);self.assertGreater(LIB.region_game_name(),0)
        LIB.test_menu(0);self.assertEqual(LIB.region_game_menu_input(64),1);self.assertEqual(ctypes.c_uint.in_dll(LIB,'region_game_journal_selection').value,10)
        self.assertEqual(LIB.region_game_menu_input(128),1);self.assertEqual(ctypes.c_uint.in_dll(LIB,'region_game_journal_selection').value,0)
        self.assertEqual(LIB.region_game_menu_input(1),0)
        used=set(re.findall(r'TX_(RG_\w+)',(ROOT/'src/region_game.c').read_text()));self.assertFalse(used-UI.keys())
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',12,index=0)
        for key,value in UI.items():self.assertLessEqual(font.getbbox(value)[2]+1,214,(key,value))


if __name__=='__main__':
    try:unittest.main(verbosity=2)
    finally:TMP.cleanup()
