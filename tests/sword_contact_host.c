#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "weapon_actions.h"
#include "combat_rules.h"
#include "enemy_types.h"
#include "ui.h"

#define COLD
#define MAX_ENEMIES 6
#define PLAY 1
#define DEAD 4
#define SHOT_EFFECT_FIRE 1
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
Enemy enemies[6];Shot shots[12];EquipmentStats gear_stats;WeaponAttack weapon_action;
volatile int px,py;
int hero_hp_q4,hp,game_state,invuln,guard_invuln,stone_guard,advanced_guard_charges;
int deaths,summoned,hitstop,room,frame,torches,boss_hp,boss_x,boss_y,boss_time,boss_armor,boss_flash;
int enemy_clocks[6],enemy_windups[6],enemy_aimx[6],enemy_aimy[6],rooted_enemies[6];
int covenants_power_time,horizons_power_time,return_power_time;
int enemy_hp_q4[6];unsigned char enemy_phases[6],enemy_stagger_ticks[6];
unsigned char slowed_enemies[6],ordinary_hostile_shots[12],shot_effects[12],shot_phases[12];
unsigned short covenants_wave_shots;unsigned char covenants_wave_enemies;
static int wall_x=-1,wall_y=-1,melee_events,southern_guard_calls,magma_guard_calls;

int ab(int n){return n<0?-n:n;}
int sign(int n){return (n>0)-(n<0);}
int near(int x,int y,int xx,int yy,int radius){return ab(x-xx)+ab(y-yy)<=radius;}
int solid(int x,int y){return x==wall_x&&y==wall_y;}
int scrolling_room(void){return 0;}
int world_width(void){return 240;}
int world_height(void){return 160;}
int boss_active(void){return boss_hp>0;}
int game_boss_contact(void){return 0;}
unsigned creatures_phase_multiplier_q8(unsigned a,unsigned b){(void)a;(void)b;return 256;}
void zero(void*p,unsigned n){memset(p,0,n);}
void impact(int x,int y){(void)x;(void)y;}
void toast(int n){(void)n;}
void sfx(int n){(void)n;}
void game_shop_scene_change(void){}
void game_road_cancel(void){}
void game_story_reward_cancel(void){}
void progression_evolution_cancel(void){}
void game_attacks_reset(void){}
void regional_powers_reset(void){}
void northern_powers_reset(void){}
void southern_powers_reset(void){}
void south_game_reset(void){}
void magma_powers_reset(void){}
void magma_game_reset(void){}
void underwater_powers_reset(void){}
void underwater_game_reset(void){}
void return_powers_reset(void){}
void horizons_powers_reset(void){}
void return_game_reset(void){}
void horizons_game_reset(void){}
void covenants_powers_reset(void){}
void covenants_game_reset(void){}
void return_legacy_reset(void){}
void kill_enemy(Enemy*e){e->hp=0;}
unsigned southern_powers_windup(unsigned i,unsigned n){(void)i;return n;}
void southern_powers_approach(unsigned i,int*x,int*y){(void)i;(void)x;(void)y;}
void southern_powers_weapon_hit(unsigned i){(void)i;melee_events++;}
int southern_powers_melee_guard(unsigned i,int x,int y){(void)i;(void)x;(void)y;southern_guard_calls++;return 0;}
int magma_powers_melee_guard(unsigned i,int x,int y){(void)i;(void)x;(void)y;magma_guard_calls++;return 0;}
int enemy_tactics_update(unsigned i){(void)i;return 0;}
int fire_shot(int x,int y,int dx,int dy,int owner){(void)x;(void)y;(void)dx;(void)dy;(void)owner;return -1;}
void game_boss_health_set(unsigned n){(void)n;}
void boss_reward(void){}
void campaign_boss_update(void){}
int covenants_powers_intercept_shot(unsigned i,int x,int y,int nx,int ny,int hostile){(void)i;(void)x;(void)y;(void)nx;(void)ny;(void)hostile;return 0;}
int horizons_powers_intercept_shot(unsigned i,int x,int y,int nx,int ny,int hostile){(void)i;(void)x;(void)y;(void)nx;(void)ny;(void)hostile;return 0;}
int return_powers_intercept_shot(unsigned i,int x,int y,int nx,int ny,int hostile){(void)i;(void)x;(void)y;(void)nx;(void)ny;(void)hostile;return 0;}
int magma_powers_intercept_shot(unsigned i,int x,int y,int nx,int ny,int hostile){(void)i;(void)x;(void)y;(void)nx;(void)ny;(void)hostile;return 0;}
int southern_powers_intercept_shot(unsigned i,int x,int y,int nx,int ny,int hostile){(void)i;(void)x;(void)y;(void)nx;(void)ny;(void)hostile;return 0;}
int northern_powers_shot_is_reflected(unsigned i){(void)i;return 0;}
void save_game(void){}
void dialogue(int a,int b,int state){(void)a;(void)b;(void)state;}
void game_health_hurt(unsigned base,unsigned phase);
void game_enemy_stagger(unsigned i,unsigned bonus);
void game_enemy_hurt(unsigned i,unsigned base,unsigned attack,unsigned phase);
int game_melee_hit(unsigned target,int x,int y,int boss);
void damage_phase(unsigned phase);
void damage(void);

#include "production.inc"

static void reset(void){
    memset(enemies,0,sizeof enemies);memset(shots,0,sizeof shots);
    memset(enemy_hp_q4,0,sizeof enemy_hp_q4);memset(enemy_stagger_ticks,0,sizeof enemy_stagger_ticks);
    memset(enemy_clocks,0,sizeof enemy_clocks);memset(enemy_windups,0,sizeof enemy_windups);
    memset(rooted_enemies,0,sizeof rooted_enemies);memset(shot_effects,0,sizeof shot_effects);
    memset(&weapon_action,0,sizeof weapon_action);memset(&gear_stats,0,sizeof gear_stats);
    px=100;py=95;room=1;game_state=PLAY;hp=6;hero_hp_q4=96;gear_stats.max_hp_q4=96;
    gear_stats.weapon_class=EQUIPMENT_SWORD;weapon_action.phase=WEAPON_ACTIVE;
    weapon_action.weapon_class=EQUIPMENT_SWORD;weapon_action.direction=0;
    weapon_action.reach_px=29;weapon_action.half_width_px=12;
    weapon_action.damage_q4=16;weapon_action.element=COMBAT_NEUTRAL_PHASE;
    invuln=guard_invuln=stone_guard=hitstop=frame=melee_events=0;
    southern_guard_calls=magma_guard_calls=0;
    wall_x=wall_y=-1;boss_hp=boss_time=boss_armor=boss_flash=torches=0;
}
static void enemy(int x,int y){
    enemies[0]=(Enemy){x,y,2,0,ENEMY_SLIME};enemy_hp_q4[0]=32;
    enemy_phases[0]=COMBAT_NEUTRAL_PHASE;
}
int main(void){
    reset();enemy(100,100);update_enemies();
    assert(melee_events==1&&enemies[0].hp==1&&weapon_action.hit_mask==1);
    assert(hero_hp_q4==96&&invuln==0);
    assert(southern_guard_calls==1&&magma_guard_calls==1);
    enemies[0].x=100;enemies[0].y=86;update_enemies();
    assert(hero_hp_q4==96&&invuln==0);
    assert(southern_guard_calls==2&&magma_guard_calls==2);
    weapon_action.phase=WEAPON_RECOVERY;update_enemies();
    assert(hero_hp_q4==80&&invuln==80);

    reset();enemy(100,100);enemies[0].flash=2;update_enemies();
    assert(melee_events==0&&hero_hp_q4==96&&invuln==0);

    reset();enemy(100,85);update_enemies();
    assert(melee_events==0&&hero_hp_q4==80&&invuln==80);

    reset();enemy(100,100);weapon_action.weapon_class=EQUIPMENT_LANCE;update_enemies();
    assert(melee_events==1&&hero_hp_q4==80&&invuln==80);

    reset();shots[0]=(Shot){100,95,0,0,2,1};shot_phases[0]=COMBAT_NEUTRAL_PHASE;
    update_shots();assert(hero_hp_q4==80&&invuln==80);

    reset();boss_hp=3;boss_x=100;boss_y=100;update_boss();
    assert(hero_hp_q4==80&&invuln==80);
    puts("PASS real melee and damage paths: hit/inside arc, outside arc, recovery, hostile shot, boss contact");
    return 0;
}
