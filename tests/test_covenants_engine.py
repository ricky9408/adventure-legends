#!/usr/bin/env python3
"""Extracted current engine dispatch/waves/boss windows. Host, not native route evidence."""
from pathlib import Path
import hashlib,json,os,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
def function(text,name):
 masked=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"',lambda m:' '*len(m[0]),text,flags=re.S)
 match=re.search(r'^(?:static\s+)?(?:COLD\s+)?(?:unsigned|int|void)\s+'+name+r'\([^;{}]*\)\s*\{',masked,re.M)
 assert match,name
 end=masked.index('{',match.start())+1;depth=1
 while depth:depth+=(masked[end]=='{')-(masked[end]=='}');end+=1
 return text[match.start():end]+'\n'
GAME=(ROOT/'src/game.c').read_text();ENGINE=(ROOT/'src/covenants_engine.inc').read_text();WORLD=(ROOT/'src/covenants_geometry.inc').read_text()
HEAD=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "creatures.h"
#include "covenants_game.h"
#include "covenants_art.h"
#include "progression_events.h"
#include "connected_road_region.h"
#define COLD
#define MAX_ENEMIES 6
#define SAVE4_GROVE_CLEAR 1
#define SAVE4_SKY_CLEAR 2
#define SAVE4_CORE_CLEAR 4
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
Enemy enemies[6];Shot shots[12];
int room=77,px=120,py=40,cx=120,cy=56,summoned=0;
int enemy_hp_q4[6],enemy_clocks[6],enemy_windups[6],enemy_aimx[6],enemy_aimy[6];
unsigned char enemy_stagger_ticks[6],rooted_enemies[6],slowed_enemies[6],enemy_phases[6],ordinary_hostile_shots[12];
unsigned char defeated_enemy_mask;
unsigned char covenants_wave_enemies;unsigned short covenants_wave_shots;
unsigned enemy_serial[6][6],shot_serial[4][12];
#define ENEMY_HOOK(n,i) void n(unsigned k){assert(k<6);enemy_serial[i][k]++;}
#define SHOT_HOOK(n,i) void n(unsigned k){assert(k<12);shot_serial[i][k]++;}
ENEMY_HOOK(southern_powers_enemy_spawn,0) ENEMY_HOOK(magma_powers_enemy_spawn,1)
ENEMY_HOOK(underwater_powers_enemy_spawn,2) ENEMY_HOOK(return_powers_enemy_spawn,3)
ENEMY_HOOK(horizons_powers_enemy_spawn,4) ENEMY_HOOK(covenants_powers_enemy_spawn,5)
SHOT_HOOK(northern_powers_shot_spawn,0) SHOT_HOOK(return_powers_shot_spawn,1)
SHOT_HOOK(horizons_powers_shot_spawn,2) SHOT_HOOK(covenants_powers_shot_spawn,3)
int ab(int x){return x<0?-x:x;}
int covenants_game_is_room(unsigned a){return a-70u<8u;}
int covenants_game_solid(int x,int y){return covenants_game_geometry_solid((unsigned)room,x,y);}
int boss_x=120,boss_y=64,boss_flash,boss_armor,boss_hp=20,boss_hp_q4=320,boss_time;
int boss_state,boss_phase,boss_pattern,boss_state_ticks,boss_aimx,boss_aimy,boss_dx,boss_dy,hazard_mode;
unsigned char covenants_cooldown_owned;
int ability_cd,hitstop,covenants_power_time,covenants_power_phase=CREATURE_WATER;
unsigned hook_queries,hook_eligible,hook_base,damage_calls,last_base,last_attack,last_phase,rewards;
int melee;
struct {unsigned damage_q4,attack_q4,element;} weapon_action={48,7,CREATURE_FIRE};
unsigned covenants_powers_boss_damage(int x,int y,int r,int eligible){assert(x==boss_x&&y==boss_y&&r==16);hook_queries++;hook_eligible=eligible;return eligible?hook_base:0;}
void game_boss_hurt(unsigned base,unsigned attack,unsigned phase){damage_calls++;last_base=base;last_attack=attack;last_phase=phase;boss_hp_q4-=base;boss_hp=(boss_hp_q4+15)/16;}
int game_melee_hit(unsigned i,int x,int y,int b){assert(i==6&&x==boss_x&&y==boss_y&&b==1);return melee;}
void game_boss_health_set(unsigned hp){boss_hp=hp;boss_hp_q4=hp*16;}
int boss_active(void){return 1;}
void boss_reward(void){rewards++;}
void impact(int x,int y){(void)x;(void)y;}
void sfx(int x){(void)x;}
void damage(void){}
int sign(int x){return(x>0)-(x<0);}
void fire_shot(int x,int y,int dx,int dy,int owner){(void)x;(void)y;(void)dx;(void)dy;(void)owner;}
void fire_fan(int n){(void)n;}
int near(int x,int y,int a,int b,int d){return ab(x-a)+ab(y-b)<d;}
void boss_set_state(int s){boss_state=s;boss_state_ticks=0;}
int in_rect(int x,int y,int w,int h){return px>=x&&py>=y&&px<x+w&&py<y+h;}
void zero(void*p,int n){memset(p,0,(unsigned)n);}
void campaign_boss_update(void);
'''
CHECKS=r'''
static void waves(void){
 unsigned i,j;Enemy protected;
 for(i=70;i<78;i++)for(j=0;j<6;j++)assert(progression_encounter_event(i,j)==CREATURE_EVENT_CAPACITY);
 assert(!game_covenants_spawn_wave(4));room=76;assert(!game_covenants_spawn_wave(0));room=77;
 enemies[4]=(Enemy){8,8,77,3,9};protected=enemies[4];
 px=64;py=120;assert(!game_covenants_spawn_wave(1));assert(!covenants_wave_enemies);
 px=120;py=40;assert(game_covenants_spawn_wave(1));assert(game_covenants_enemies_alive()==2);
 assert(enemies[0].x==64&&enemies[1].x==176&&enemies[0].hp==4&&enemy_phases[0]==CREATURE_WOOD&&enemy_phases[1]==CREATURE_WATER);
 assert(!game_covenants_spawn_wave(2));
 for(i=0;i<6;i++)assert(enemy_serial[i][0]==1&&enemy_serial[i][1]==1&&enemy_serial[i][4]==0);
 enemies[0].hp=enemies[1].hp=0;assert(game_covenants_enemies_alive()==0);
 px=120;py=136;assert(!game_covenants_spawn_wave(2));px=120;py=40;
 assert(game_covenants_spawn_wave(2));assert(game_covenants_enemies_alive()==3&&enemies[2].kind==2);
 assert(enemy_phases[0]==CREATURE_METAL&&enemy_phases[1]==CREATURE_EARTH&&enemy_phases[2]==CREATURE_FIRE);
 shots[0]=(Shot){1,1,0,0,50,1};shots[1]=(Shot){2,2,0,0,50,1};shots[2]=(Shot){3,3,0,0,50,1};
 ordinary_hostile_shots[0]=ordinary_hostile_shots[2]=1;covenants_wave_shots=3;
 enemies[0].kind=9;enemies[0].hp=88;assert(game_covenants_spawn_wave(0));
 assert(enemies[0].hp==88&&enemies[1].hp==0&&enemies[2].hp==0);
 assert(!memcmp(&protected,&enemies[4],sizeof protected));
 assert(shots[0].life==0&&shots[1].life==50&&shots[2].life==50);
 for(i=0;i<4;i++)assert(shot_serial[i][0]==1&&!shot_serial[i][1]&&!shot_serial[i][2]);
 enemies[0].hp=0;assert(game_covenants_spawn_wave(3));assert(game_covenants_enemies_alive()==3);
 assert(enemies[0].x==72&&enemies[1].x==168&&enemies[2].hp==5&&enemy_phases[2]==CREATURE_METAL);
 assert(game_covenants_spawn_wave(0));assert(!game_covenants_enemies_alive());
}
static void boss_reset(int area,int state,int flash){room=area;boss_state=state;boss_state_ticks=boss_time=0;boss_phase=0;boss_hp=20;boss_hp_q4=320;boss_armor=area==3?60:0;boss_flash=flash;hook_queries=damage_calls=hook_eligible=rewards=0;hook_base=32;covenants_power_time=1;covenants_cooldown_owned=0;ability_cd=0;melee=0;px=40;py=40;}
static void bosses(void){
 int state,phase;
 for(state=0;state<7;state++){boss_reset(8,state,0);update_boss();assert(hook_queries==(state==5));assert(damage_calls==(state==5));if(state==5)assert(last_base==32&&last_attack==0&&last_phase==CREATURE_WATER&&boss_flash==16);}
 boss_reset(3,0,0);boss_armor=0;update_boss();assert(!hook_queries&&!damage_calls);
 boss_reset(3,0,0);update_boss();assert(hook_queries==1&&damage_calls==1&&boss_flash==16);
 boss_reset(3,0,8);update_boss();assert(!hook_queries&&!damage_calls);
 boss_reset(8,5,8);update_boss();assert(!hook_queries&&!damage_calls);
 boss_reset(13,5,0);boss_hp=16;boss_hp_q4=256;update_boss();assert(boss_state==6&&boss_phase==1&&!hook_queries&&!damage_calls);
 boss_reset(13,5,0);boss_hp=17;boss_hp_q4=272;update_boss();assert(damage_calls==1&&boss_state==6&&boss_phase==1&&boss_hp_q4==256);
 boss_reset(8,5,0);hook_base=0;melee=1;update_boss();assert(damage_calls==1&&last_base==32&&last_attack==7&&last_phase==CREATURE_FIRE);
 boss_reset(8,5,0);covenants_power_time=0;melee=1;update_boss();assert(!hook_queries&&damage_calls==1);
 for(phase=0;phase<2;phase++){
  boss_reset(13,5,0);boss_phase=phase;boss_hp=17-phase*8;boss_hp_q4=boss_hp*16;ability_cd=171;covenants_cooldown_owned=1;
  update_boss();assert(boss_state==6&&boss_phase==phase+1&&ability_cd==171);
  boss_reset(13,5,0);boss_phase=phase;boss_hp=16-phase*8;boss_hp_q4=boss_hp*16;ability_cd=171;covenants_cooldown_owned=1;
  update_boss();assert(boss_state==6&&boss_phase==phase+1&&ability_cd==171);
  /* A dismissed/expired legendary still owns its remaining shared recovery. */
  boss_reset(13,5,0);boss_phase=phase;boss_hp=17-phase*8;boss_hp_q4=boss_hp*16;ability_cd=171;covenants_cooldown_owned=1;covenants_power_time=0;melee=1;
  update_boss();assert(boss_state==6&&boss_phase==phase+1&&ability_cd==171);
  boss_reset(13,5,0);boss_phase=phase;boss_hp=17-phase*8;boss_hp_q4=boss_hp*16;ability_cd=171;covenants_power_time=0;melee=1;
  update_boss();assert(boss_state==6&&boss_phase==phase+1&&ability_cd==0);
 }
}
int main(void){waves();bosses();puts("PASS: exact waves, blocked retry, protected actors/shots, all spawn generations, no XP namespace, authored boss windows and phase clamps");return 0;}
'''
def main():
 sources=['src/game.c','src/covenants_engine.inc','src/covenants_geometry.inc','src/connected_road_region.h','src/connected_roads.h','src/horizons_engine.inc','src/progression_events.c']
 code=HEAD+function(WORLD,'covenants_game_geometry_solid')+function((ROOT/'src/horizons_engine.inc').read_text(),'game_region_actor_overlap')
 for name in ['covenants_enemy_generation','covenants_shot_generation','game_covenants_enemies_alive','game_covenants_spawn_wave','covenants_boss_contact','game_boss_contact','game_boss_phase_cooldown']:code+=function(ENGINE,name)
 code+=function(GAME,'update_boss')+function(GAME,'campaign_boss_update')+CHECKS
 results={}
 with tempfile.TemporaryDirectory(prefix='covenants-engine-')as folder:
  p=Path(folder)
  for mode,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
   c=p/(mode+'.c');c.write_text(code);exe=p/mode
   subprocess.run(['cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*flags,'-Isrc',str(c),'src/covenants_art.c','src/progression_events.c','-o',str(exe)],cwd=ROOT,check=True)
   run=subprocess.run([str(exe)],capture_output=True,text=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'},check=True);results[mode]=run.stdout.strip();print(run.stdout.strip())
  mutant=code.replace('if(!covenants_cooldown_owned)ability_cd=0;','ability_cd=0;');assert mutant!=code
  c=p/'negative-phase-refund.c';c.write_text(mutant);exe=p/'negative-phase-refund'
  subprocess.run(['cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Isrc',str(c),'src/covenants_art.c','src/progression_events.c','-o',str(exe)],cwd=ROOT,check=True)
  failure=subprocess.run([str(exe)],capture_output=True,text=True);assert failure.returncode!=0 and 'ability_cd==171' in failure.stderr
  results['restored_refund_bug_rejected']={'exit_code':failure.returncode,'stderr':failure.stderr.strip()};print('PASS: original Core cooldown-refund mutation rejected')
 out=ROOT/'build/covenants-engine-host.json';out.write_text(json.dumps({'scope':__doc__,'native_gameplay':False,'results':results,'sources':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}},indent=2)+'\n')
if __name__=='__main__':main()
