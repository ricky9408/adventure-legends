/* Evolved commands have explicit effects, separate from field capabilities. */
#include "advanced_powers.h"
#include "assets.h"
#include "creatures.h"
#include "gear_runtime.h"
typedef struct{int x,y,hp,flash,kind;} Enemy;
typedef struct{int x,y,dx,dy,life,owner;} Shot;
extern Enemy enemies[6];extern Shot shots[12];
extern volatile int px,py,spirit,stone_guard,guard_invuln;
extern int face,frame,ability_cd,ability_max,power_effect,enemy_windups[6];
extern int solid(int,int);
extern void kill_enemy(Enemy*),impact(int,int),sfx(int),obj_add(int,int,int,int,int,int,int,int);
int rooted_enemies[6],advanced_guard_charges;
unsigned char shot_effects[12],shot_phases[12];
static unsigned visible_cells;
int advanced_kind,advanced_time_left,advanced_origin_x,advanced_origin_y,advanced_direction,advanced_hit_mask,advanced_shield_left;
static int abs_i(int n){return n<0?-n:n;}
static int close_to(int x,int y,int xx,int yy,int d){return abs_i(x-xx)+abs_i(y-yy)<d;}
static void forward(int distance,int*x,int*y){*x=advanced_origin_x+(advanced_direction==2?-distance:advanced_direction==3?distance:0);*y=advanced_origin_y+(advanced_direction==1?-distance:advanced_direction==0?distance:0);}
static int segment_clear(int ax,int ay,int x,int y){int dx=abs_i(x-ax),sx=ax<x?1:-1,dy=-abs_i(y-ay),sy=ay<y?1:-1,error=dx+dy;while(ax!=x||ay!=y){int twice=error*2;if(twice>=dy){error+=dy;ax+=sx;}if(twice<=dx){error+=dx;ay+=sy;}if(solid(ax,ay))return 0;}return 1;}
static int path_clear(int x,int y){return segment_clear(advanced_origin_x,advanced_origin_y,x,y);}
void advanced_reset(void){int i;visible_cells=0;advanced_kind=advanced_time_left=advanced_guard_charges=advanced_shield_left=advanced_hit_mask=0;for(i=0;i<6;i++)rooted_enemies[i]=0;}
int advanced_power(unsigned command){int i;if(command<5||command>8)return 0;advanced_kind=command;advanced_origin_x=px;advanced_origin_y=py;advanced_direction=face;advanced_hit_mask=0;visible_cells=0;advanced_time_left=60;advanced_shield_left=1;ability_max=ability_cd=game_power_cooldown(creatures_ability(command)->cooldown_updates);power_effect=20;sfx(2);
 if(command==6){advanced_time_left=90;for(i=0;i<6;i++)if(enemies[i].hp&&close_to(enemies[i].x,enemies[i].y,px,py,46)&&path_clear(enemies[i].x,enemies[i].y)){rooted_enemies[i]=90;enemy_windups[i]=0;}}
 if(command==7){int reflected=0;advanced_time_left=25;for(i=0;i<12&&reflected<3;i++)if(shots[i].life&&shots[i].owner){int dx=shots[i].x-px,dy=shots[i].y-py,f=face==2?-dx:face==3?dx:face==1?-dy:dy,side=face<2?dx:dy;if(f>=-8&&f<=80&&abs_i(side)<=32&&path_clear(shots[i].x,shots[i].y)){shots[i].owner=0;shots[i].dx=-shots[i].dx;shots[i].dy=-shots[i].dy;shots[i].life=70;shot_effects[i]=SHOT_EFFECT_WIND;shot_phases[i]=CREATURE_WOOD;reflected++;}}}
 if(command==8){stone_guard=72;advanced_guard_charges=2;advanced_time_left=72;}
 return 1;}
void advanced_tick(void){int i;for(i=0;i<6;i++)if(rooted_enemies[i])rooted_enemies[i]--;if(!stone_guard)advanced_guard_charges=0;if(!advanced_time_left)return;advanced_time_left--;
 if(advanced_kind==5){int cell;visible_cells=0;for(cell=0;cell<3;cell++){int x,y;forward(16+cell*14,&x,&y);if(60-advanced_time_left<8+cell*6||60-advanced_time_left>24+cell*6||!path_clear(x,y))continue;visible_cells|=1u<<cell;for(i=0;i<6;i++)if(!(advanced_hit_mask&(1<<i))&&enemies[i].hp&&close_to(enemies[i].x,enemies[i].y,x,y,14)&&segment_clear(x,y,enemies[i].x,enemies[i].y)){advanced_hit_mask|=1<<i;game_enemy_hurt((unsigned)i,32,0,CREATURE_FIRE);enemies[i].flash=16;enemy_windups[i]=0;impact(enemies[i].x,enemies[i].y);if(enemies[i].hp<=0)kill_enemy(&enemies[i]);}}}
 if(advanced_kind==6&&advanced_shield_left){for(i=0;i<12;i++)if(shots[i].life&&shots[i].owner&&close_to(shots[i].x,shots[i].y,advanced_origin_x,advanced_origin_y,30)&&path_clear(shots[i].x,shots[i].y)){shots[i].life=0;advanced_shield_left=0;impact(advanced_origin_x,advanced_origin_y);break;}}
}
void advanced_draw(void){int i;if(!advanced_time_left)return;if(advanced_kind==5){for(i=0;i<3;i++){int x,y;forward(16+i*14,&x,&y);if(visible_cells&(1u<<i)){obj_add(SPR_FLAME_0*256,x-8,y-8,16,16,1,y,0);}}}
 else if(advanced_kind==6){for(i=0;i<4;i++){int x=advanced_origin_x+(i&1?20:-20),y=advanced_origin_y+(i&2?14:-14);obj_add(10560,x-4,y-4,8,8,1,y,0);}}
 else if(advanced_kind==7){for(i=0;i<6;i++){int x,y;forward(i*12,&x,&y);obj_add(10560,x-4+(frame&3),y-4,8,8,1,y,0);}}
 else if(advanced_kind==8&&stone_guard){obj_add(10624,px-16,py-5,8,8,1,py+1,0);if(advanced_guard_charges>1)obj_add(10624,px+8,py-5,8,8,1,py+1,0);}
}

/* This export mirrors advanced_draw's exact sprite placements/active checks.
 * It never advances time, sets visible_cells or calls an authoritative hook. */
void advanced_powers_field_geometry(unsigned command,ReturnLegacyEmit emit,void *context){
 int i;if(!emit||!advanced_time_left||command!=(unsigned)advanced_kind)return;
 if(command==5){for(i=0;i<3;i++)if(visible_cells&(1u<<i)){int x,y;forward(16+i*14,&x,&y);
  return_legacy_piece(emit,context,sprite_data[SPR_FLAME_0],x-8,y-8,16,RETURN_LEGACY_PIXELS);}}
 else if(command==6){for(i=0;i<4;i++){int x=advanced_origin_x+(i&1?20:-20),y=advanced_origin_y+(i&2?14:-14);
  return_legacy_piece(emit,context,0,x-4,y-4,8,RETURN_LEGACY_SPARK);}}
 else if(command==7){for(i=0;i<6;i++){int x,y;forward(i*12,&x,&y);
  return_legacy_piece(emit,context,0,x-4+(frame&3),y-4,8,RETURN_LEGACY_SPARK);}}
 else if(command==8&&stone_guard){return_legacy_piece(emit,context,0,px-16,py-5,8,RETURN_LEGACY_ARMOR);
  if(advanced_guard_charges>1)return_legacy_piece(emit,context,0,px+8,py-5,8,RETURN_LEGACY_ARMOR);}
}
