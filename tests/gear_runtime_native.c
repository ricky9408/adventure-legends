#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "gear_runtime.h"
#include "gear_menu.h"
#include "progression.h"
#include "regional_powers.h"
#include "northern_powers.h"
#include "southern_powers.h"
#include "advanced_powers.h"
#include "south_game.h"
#include "obj_layout.h"
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
Enemy enemies[6];Shot shots[12];Save5State adventure_save;
/* Chapter machines are absent from this bounded world; native chapter QA covers them. */
int north_game_target(int*x,int*y,int*r){(void)x;(void)y;(void)r;return 0;}
int north_game_weapon_hit(unsigned c,int x,int y,unsigned d){(void)c;(void)x;(void)y;(void)d;return 0;}
int south_game_target(int*x,int*y,int*r){(void)x;(void)y;(void)r;return 0;}
int south_game_weapon_hit(unsigned c,int x,int y,unsigned d){(void)c;(void)x;(void)y;(void)d;return 0;}
volatile int hp,max_hp,px,py,boss_hp,boss_x,boss_y,room;
volatile int spirit,stone_guard,guard_invuln;
int cx,cy,frame,power_effect;
int keys,gfx_slash_frame,face,roll_ticks,swing,sword_cd,combo_step,combo_timer,attack_buffer,swing_damage,slash_id,hitstop,boss_flash,boss_armor;
int ability_cd,ability_max,enemy_windups[6],enemy_clocks[6];
static unsigned char vram[16384];
static int wall_x=-100,wall_y=-100,boss_live;
int solid(int x,int y){return x<0||y<0||x>=480||y>=320||x==wall_x||y==wall_y;}
int near(int x,int y,int tx,int ty,int radius){return abs(x-tx)+abs(y-ty)<radius;}
int boss_active(void){return boss_live;}
int try_interaction(void){return 0;}
void move_player(int x,int y){px+=x/256;py+=y/256;}
CreatureInstance *progression_selected(void){return 0;}
void impact(int x,int y){(void)x;(void)y;}
void sfx(int n){(void)n;}
void kill_enemy(Enemy*e){e->hp=0;}
int region_game_practice_hit(unsigned c,int x,int y){(void)c;(void)x;(void)y;return 0;}
void obj_upload(const unsigned char *p,int w,int h,int off){assert(p&&w>0&&h>0&&w<=32&&h<=32&&off>=0&&off+w*h<=16384);memcpy(vram+off,p,(size_t)w*h);}
void obj_add(int o,int x,int y,int w,int h,int p,int d,int f){(void)x;(void)y;(void)p;(void)d;(void)f;assert(w>0&&h>0&&w<=32&&h<=32&&o>=0&&o+w*h<=16384);}
static void equip(unsigned slot,unsigned ref){EquipmentU16 h=(EquipmentU16)hero_hp_q4;assert(equipment_equip(&adventure_save.equipment,slot,ref,96,&h,0,0)==0);game_gear_apply(h);}

/* Synthetic passive ownership/loadouts exercise actual runtime derive,
 * preview and commit functions; no controller-acquisition claim. */
static unsigned item_ref(unsigned id){unsigned i;for(i=0;i<48;i++)if(adventure_save.equipment.bag[i].item_id==id)return i;abort();}
static void passive_equip(unsigned slot,unsigned id){EquipmentU16 h=(EquipmentU16)hero_hp_q4;EquipmentComparison preview,applied;
 assert(equipment_preview(&adventure_save.equipment,slot,id?item_ref(id):255,game_gear_base_hp(),h,0,&preview)==EQUIPMENT_OK);
 game_gear_bonus_stats(&preview.before);game_gear_bonus_stats(&preview.after);
 assert(!memcmp(&preview.before,&gear_stats,sizeof gear_stats));
 assert(equipment_equip(&adventure_save.equipment,slot,id?item_ref(id):255,game_gear_base_hp(),&h,0,&applied)==EQUIPMENT_OK);
 game_gear_apply_stats(h,&applied.after);assert(!memcmp(&preview.after,&gear_stats,sizeof gear_stats));
 assert(hero_hp_q4==preview.hp_after_q4);
}
static void later_passive_checks(void){unsigned i,bits;EquipmentStats old,first,raw;
 memset(&adventure_save,0,sizeof adventure_save);equipment_init(&adventure_save.equipment);max_hp=6;hero_hp_q4=63;ability_cd=37;
 game_health_refresh(0);old=gear_stats;
 for(bits=0;bits<16;bits++){
  adventure_save.economy.later_claims=(unsigned char)bits;game_health_refresh(0);
  assert(gear_stats.max_hp_q4==96+((bits&8)?16:0));assert(gear_stats.speed_q8==320+((bits&1)?16:0));
  assert(gear_stats.diagonal_q8==((gear_stats.speed_q8*181u+128u)>>8));
  assert(gear_stats.defense_q4==((bits&2)?2:0));assert(gear_stats.power_cooldown==75-((bits&4)?4:0));
  assert(gear_stats.attack_q4==old.attack_q4&&hero_hp_q4==63&&ability_cd==37);
  first=gear_stats;for(i=0;i<100;i++){game_health_refresh(0);assert(!memcmp(&gear_stats,&first,sizeof first));assert(hero_hp_q4==63&&ability_cd==37);}
 }
 game_health_fill();assert(hero_hp_q4==112);passive_equip(0,1);assert(hero_hp_q4==112);
 for(i=1;i<48;i++)assert(equipment_claim(&adventure_save.equipment,equipment_authored_ids[i],i,0)==EQUIPMENT_OK);
 adventure_save.economy.relics=3;max_hp=8;game_health_refresh(0);
 passive_equip(0,14);passive_equip(1,34);passive_equip(2,56);passive_equip(3,65);passive_equip(4,81);
 assert(gear_stats.max_hp_q4==192);game_health_fill();assert(hero_hp_q4==192);
 passive_equip(0,14);passive_equip(1,34);passive_equip(2,56);passive_equip(3,65);passive_equip(4,81);assert(hero_hp_q4==192);
 hero_hp_q4=63;
 passive_equip(0,2);passive_equip(3,67);passive_equip(4,82);assert(gear_stats.defense_q4==8);
 passive_equip(2,52);passive_equip(3,69);passive_equip(4,88);
 assert(gear_stats.power_cooldown==55&&game_power_cooldown(75)==55&&game_power_cooldown(20)==1&&game_power_cooldown(0)==1&&ability_cd==37);
 for(i=0;i<48;i++)passive_equip(equipment_definition(equipment_authored_ids[i])->slot,equipment_authored_ids[i]);
 assert(equipment_derive(&adventure_save.equipment,game_gear_base_hp(),&raw));raw.speed_q8=352;raw.defense_q4=8;game_gear_bonus_stats(&raw);
 assert(raw.speed_q8==352&&raw.diagonal_q8==249&&raw.defense_q4==8);
 puts("PASS later treasure actual runtime: all16 receipts, HP/defense/speed/diagonal/recovery caps, attack unchanged,100 refreshes each/no refill or cooldown reset, all48 gear preview/commit parity");
}

int main(void){
 unsigned body,ring,i;unsigned char arrows[128],pin[256],icons[320];
 max_hp=6;equipment_init(&adventure_save.equipment);game_health_refresh(1);assert(hero_hp_q4==96);
 assert(equipment_claim(&adventure_save.equipment,33,6,&body)==0);equip(1,body);assert(hero_hp_q4==96&&gear_stats.max_hp_q4==104);
 game_health_hurt(16,255);assert(hero_hp_q4==82&&hp==6);
 assert(equipment_claim(&adventure_save.equipment,81,11,&ring)==0);ability_cd=37;equip(4,ring);assert(ability_cd==37&&game_power_cooldown(75)==71&&game_power_cooldown(120)==116);
 game_health_fill();assert(hero_hp_q4==104);equip(1,255);assert(hero_hp_q4==96);for(i=0;i<100;i++){equip(1,body);assert(hero_hp_q4==96);equip(1,255);assert(hero_hp_q4==96);}
 game_attacks_reset();memcpy(icons,vram+GFX_OBJ_PHASE_ICONS,320);
 player_arrows[0]=(WeaponArrow){100*256,100*256,100,1024,1,0,32,0,0,255,{0,0}};
 player_arrows[1]=player_arrows[0];player_arrows[1].direction=3;
 game_draw_weapon();memcpy(arrows,vram+GFX_OBJ_PLAYER_ARROW,128);
 px=py=100;face=0;assert(regional_power(11));memcpy(pin,vram+GFX_OBJ_POWER_PIN,256);
 assert(!memcmp(arrows,vram+GFX_OBJ_PLAYER_ARROW,128));game_draw_weapon();assert(!memcmp(pin,vram+GFX_OBJ_POWER_PIN,256));
 player_arrows[0].direction=1;player_arrows[1].direction=2;game_draw_weapon();assert(!memcmp(pin,vram+GFX_OBJ_POWER_PIN,256));assert(!memcmp(icons,vram+GFX_OBJ_PHASE_ICONS,320));
 player_arrows[0].active=player_arrows[1].active=0;regional_powers_reset();assert(game_gear_busy()==0);shots[0].life=1;assert(game_gear_busy()==16);shots[0].owner=1;assert(game_gear_busy()==0);assert(regional_power(11));assert(game_gear_busy()==16);
 game_enemy_stagger(0,2);assert(enemy_stagger_ticks[0]==32);game_combat_tick();assert(enemy_stagger_ticks[0]==31);assert(enemies[0].flash==0);
 {unsigned d;for(d=0;d<4;d++){
    int dx=d==2?-1:d==3?1:0,dy=d==1?-1:d==0?1:0;
    memset(enemies,0,sizeof enemies);game_attacks_reset();regional_powers_reset();
    px=py=100;enemies[0]=(Enemy){100+dx*10,100+dy*10,4,0,0};game_enemy_health_reset();
    wall_x=dx?100+dx*5:-100;wall_y=dy?100+dy*5:-100;
    player_arrows[0]=(WeaponArrow){100*256,100*256,112*256,1024,1,(unsigned char)d,32,0,0,255,{0,0}};
    for(i=0;i<3;i++)game_arrows_update();assert(enemy_hp_q4[0]==64&&!player_arrows[0].active);
    weapon_action.phase=WEAPON_ACTIVE;weapon_action.weapon_class=EQUIPMENT_LANCE;weapon_action.direction=(unsigned char)d;weapon_action.reach_px=43;weapon_action.half_width_px=6;
    assert(!game_melee_hit(0,enemies[0].x,enemies[0].y,0)&&weapon_action.hit_mask==0);
    wall_x=wall_y=-100;assert(game_melee_hit(0,enemies[0].x,enemies[0].y,0));assert(!game_melee_hit(0,enemies[0].x,enemies[0].y,0));
    player_arrows[0]=(WeaponArrow){100*256,100*256,112*256,1024,1,(unsigned char)d,32,0,0,255,{0,0}};
    game_arrows_update();assert(enemy_hp_q4[0]==32&&!player_arrows[0].active);game_arrows_update();assert(enemy_hp_q4[0]==32);
    memset(enemies,0,sizeof enemies);boss_live=1;boss_x=100+dx*20;boss_y=100+dy*20;boss_armor=1;boss_flash=0;game_boss_health_set(20);
    wall_x=dx?100+dx*10:-100;wall_y=dy?100+dy*10:-100;
    player_arrows[0]=(WeaponArrow){100*256,100*256,112*256,1024,1,(unsigned char)d,32,0,0,255,{0,0}};
    for(i=0;i<4;i++)game_arrows_update();assert(boss_hp_q4==320&&!player_arrows[0].active);
    wall_x=wall_y=-100;player_arrows[0]=(WeaponArrow){100*256,100*256,112*256,1024,1,(unsigned char)d,32,0,0,255,{0,0}};game_arrows_update();assert(boss_hp_q4==304&&!player_arrows[0].active);boss_live=0;
 }}
 later_passive_checks();
 puts("PASS four-direction wall/target/boss LOS and exactly-once hit ledger; actual runtime: fractional HP/no-heal100cycles, cooldown cache, two arrows+pin+phase glyph separation, projectile locks, separate stagger timer");
 return 0;
}
