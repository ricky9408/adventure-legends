#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "enemy_tactics.h"
#include "gear_runtime.h"
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
#define MAX_ENEMIES 6
#define PLAY 1
Enemy enemies[6];Shot shots[12];WeaponAttack weapon_action;
volatile int px,py,game_state;
int frame,enemy_clocks[6],enemy_windups[6],enemy_aimx[6],enemy_aimy[6],rooted_enemies[6];
unsigned char slowed_enemies[6],enemy_stagger_ticks[6],enemy_phases[6],shot_phases[12],ordinary_hostile_shots[12];
int hitstop,room,invuln,guard_invuln;
unsigned char covenants_wave_enemies;
unsigned short covenants_wave_shots;
static int wall_x,wall_y,damage_calls,shot_calls,kill_calls,melee,draw_calls;
static unsigned art_key;
static const unsigned char*art_pixels;
int ab(int x){return x<0?-x:x;}
int sign(int x){return x<0?-1:x>0?1:0;}
int near(int x,int y,int xx,int yy,int r){return ab(x-xx)+ab(y-yy)<=r;}
int solid(int x,int y){return x<5||y<5||x>475||y>315||x==wall_x||y==wall_y;}
unsigned southern_powers_windup(unsigned i,unsigned n){(void)i;return n;}
void southern_powers_approach(unsigned i,int*x,int*y){(void)i;(void)x;(void)y;}
void southern_powers_weapon_hit(unsigned i){(void)i;}
int southern_powers_melee_guard(unsigned i,int x,int y){(void)i;(void)x;(void)y;return 0;}
int magma_powers_melee_guard(unsigned i,int x,int y){(void)i;(void)x;(void)y;return 0;}
int game_melee_hit(unsigned i,int x,int y,int r){(void)i;(void)x;(void)y;(void)r;return melee;}
void game_enemy_hurt(unsigned i,unsigned d,unsigned a,unsigned p){(void)a;(void)p;enemies[i].hp-=(int)((d+15)/16);}
void game_enemy_stagger(unsigned i,unsigned n){enemy_stagger_ticks[i]=(unsigned char)n;}
void sfx(int n){(void)n;}
void kill_enemy(Enemy*e){e->hp=0;kill_calls++;}
int fire_shot(int x,int y,int dx,int dy,int owner){(void)x;(void)y;(void)dx;(void)dy;(void)owner;shot_calls++;return -1;}
void damage_phase(unsigned phase){(void)phase;damage_calls++;}
void region_pixels_actor(unsigned key,const unsigned char*p,int x,int y){(void)x;(void)y;art_key=key;art_pixels=p;draw_calls++;}
#include "enemy_update_source.inc"
static void reset(void){
 memset(enemies,0,sizeof enemies);memset(shots,0,sizeof shots);
 memset(enemy_clocks,0,sizeof enemy_clocks);memset(enemy_windups,0,sizeof enemy_windups);
 memset(enemy_aimx,0,sizeof enemy_aimx);memset(enemy_aimy,0,sizeof enemy_aimy);
 memset(rooted_enemies,0,sizeof rooted_enemies);memset(slowed_enemies,0,sizeof slowed_enemies);
 memset(enemy_stagger_ticks,0,sizeof enemy_stagger_ticks);
 enemies[3]=(Enemy){200,100,5,0,ENEMY_LANE_CHARGER};px=250;py=100;game_state=PLAY;
 wall_x=wall_y=-1;damage_calls=shot_calls=kill_calls=melee=draw_calls=hitstop=0;
 weapon_action.damage_q4=16;weapon_action.stagger=0;
}
static void tick(unsigned n){while(n--){frame++;update_enemies();}}
static void rush(void){tick(1);assert(enemy_windups[3]==42);tick(42);assert(enemy_clocks[3]==-18);}
int main(void){
 unsigned i;int x;
 reset();tick(1);assert(enemy_windups[3]==42&&enemies[3].x==200&&shot_calls==0);
 px=200;py=100;tick(41);assert(enemies[3].x==200&&damage_calls==0&&enemy_windups[3]==1);
 tick(1);assert(enemy_clocks[3]==-18&&enemies[3].x==200);
 reset();rush();px=250;py=132;tick(18);assert(enemies[3].x==254&&enemies[3].y==100&&damage_calls==0);
 assert(enemy_clocks[3]==90);tick(90);assert(enemies[3].x==254&&enemy_clocks[3]==0&&enemy_windups[3]==0);
 reset();rush();wall_x=202;tick(1);assert(enemies[3].x==201&&enemy_clocks[3]==90);
 reset();px=200;py=150;rush();wall_y=102;tick(1);assert(enemies[3].y==101&&enemy_clocks[3]==90);
 reset();px=240;rush();tick(12);assert(damage_calls>0&&shot_calls==0);
 for(i=0;i<3;i++){
  reset();rush();tick(2);x=enemies[3].x;
  if(i==0)enemies[3].flash=16;else if(i==1)enemy_stagger_ticks[3]=8;else rooted_enemies[3]=45;
  tick(1);assert(enemies[3].x==x&&enemy_clocks[3]==90&&enemy_windups[3]==0&&enemy_aimx[3]==0);
 }
 reset();tick(1);melee=1;tick(1);assert(enemies[3].hp==4&&enemy_windups[3]==0&&enemy_clocks[3]==90&&hitstop==3);
 reset();rush();x=enemies[3].x;game_state=4;enemy_tactics_update(3);assert(enemies[3].x==x&&enemy_clocks[3]==-18);
 game_state=3;enemy_tactics_update(3);assert(enemies[3].x==x&&enemy_clocks[3]==-18);
 reset();rush();enemies[3].hp=0;tick(100);assert(enemy_clocks[3]==-18&&kill_calls==0&&shot_calls==0);
 reset();rush();reset();assert(enemy_windups[3]==0&&enemy_clocks[3]==0);tick(1);assert(enemy_windups[3]==42);
 reset();rush();slowed_enemies[3]=1;frame=1;enemy_tactics_update(3);assert(enemies[3].x==200&&enemy_clocks[3]==-18);
 frame=2;enemy_tactics_update(3);assert(enemies[3].x==203&&enemy_clocks[3]==-17);
 reset();enemy_tactics_draw(3);assert(draw_calls==1&&art_key==20480&&art_pixels);
 tick(1);enemy_tactics_draw(3);assert(draw_calls==2&&art_key==20487);
 reset();enemies[3].kind=0;enemy_tactics_update(3);assert(enemy_windups[3]==0);enemy_tactics_update(6);enemy_tactics_draw(6);
 puts("PASS:42-update warning, locked lane,18-step rush,90-update recovery, thin-wall probes, damage gating, interrupt/modal/dead/reset/slow guards, same actor cache");return 0;
}
