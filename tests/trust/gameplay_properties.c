#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "combat_rules.h"
#include "collision_rects.h"
#include "gear_runtime.h"
#include "progression.h"
#include "weapon_actions.h"
#ifndef GAMEPLAY_CONTROLS_HEADER
#define GAMEPLAY_CONTROLS_HEADER "field_controls.h"
#endif
#include GAMEPLAY_CONTROLS_HEADER

extern volatile int room,px,py;
extern volatile int game_state,ticks,stone_guard,transition_lock;
extern int px_q8,py_q8;
extern int step_cd,face,invuln,roll_ticks,roll_cd;
extern int keys,pressed,hitstop,ability_cd,heal_cd;
extern volatile int guard_invuln;
extern int solid(int,int),world_width(void),world_height(void);
extern void move_player(int,int);
extern int field_step_try(unsigned);
extern void update(void);

static unsigned long checks,corners,moves,damage_cases,bonus_cases,control_cases,arrow_cases;
static unsigned long geometry_queries,geometry_points,geometry_fallbacks,step_cases;
static unsigned room_corners[78];

#define REQUIRE(condition) do { \
 ++checks; \
 if(!(condition)){fprintf(stderr,"%s:%d: %s (room=%d px=%d py=%d)\n",__FILE__,__LINE__,#condition,room,px,py);return 1;} \
} while(0)

static void place(int x,int y,unsigned fx,unsigned fy){
 px=x;py=y;px_q8=x*256+(int)fx;py_q8=y*256+(int)fy;
}

static int movement_stays_outside_solids(void){
 static const int direction[8][2]={{1,0},{-1,0},{0,1},{0,-1},{1,1},{-1,1},{1,-1},{-1,-1}};
 static const int distances[3]={181,352,3072};
 unsigned area,d,n,variant;
 for(area=0;area<78;area++){
  int x,y,width,height;
  room=(int)area;width=world_width();height=world_height();
  REQUIRE(width>=240&&width<=480&&height>=160&&height<=320);
  for(y=1;y<height-1;y++)for(x=1;x<width-1;x++){
   if(solid(x,y))continue;
   for(d=4;d<8;d++){
    int dx=direction[d][0],dy=direction[d][1];
    if(solid(x+dx,y)||solid(x,y+dy)||!solid(x+dx,y+dy))continue;
    ++corners;++room_corners[area];
    place(x,y,0,0);move_player(dx*256,dy*256);
    REQUIRE(!solid(px,py));
    REQUIRE(px==px_q8/256&&py==py_q8/256);
    REQUIRE(abs(px-x)<=1&&abs(py-y)<=1);
    REQUIRE(px!=x||py!=y);
   }
   if(x%17||y%17)continue;
   for(d=0;d<8;d++)for(n=0;n<3;n++)for(variant=0;variant<2;variant++){
    int oldx,oldy,dx=direction[d][0]*distances[n],dy=direction[d][1]*distances[n];
    place(x,y,variant?255u:0u,variant?127u:0u);oldx=px_q8;oldy=py_q8;
    move_player(dx,dy);++moves;
    REQUIRE(!solid(px,py));
    REQUIRE(px==px_q8/256&&py==py_q8/256);
    REQUIRE(abs(px_q8-oldx)<=abs(dx)&&abs(py_q8-oldy)<=abs(dy));
    REQUIRE(!dx||((px_q8-oldx)*direction[d][0]>=0));
    REQUIRE(!dy||((py_q8-oldy)*direction[d][1]>=0));
   }
  }
 }
 REQUIRE(corners>100&&moves>10000);
 return 0;
}

static int invalid_rooms_do_not_authorize_movement(void){
 static const int invalid[4]={-1,78,INT_MIN,INT_MAX};
 unsigned i;
 for(i=0;i<4;i++){
  room=invalid[i];REQUIRE(solid(120,80));
  place(120,80,0,0);move_player(256,256);
  REQUIRE(px==120&&py==80&&px_q8==120*256&&py_q8==80*256);
 }
 return 0;
}

static int cardinal_steps_are_bounded_without_defensive_bonuses(void){
 static const unsigned axes[4]={16,32,64,128};
 static const int direction[4][2]={{1,0},{-1,0},{0,-1},{0,1}};
 static const unsigned invalid[7]={0,1,2,4,8,48,UINT_MAX};
 unsigned d,i;
 room=14;
 for(d=0;d<4;d++){
  int dx=direction[d][0],dy=direction[d][1];
  place(120,100,0,0);step_cd=0;invuln=7;guard_invuln=9;roll_ticks=11;roll_cd=13;
  REQUIRE(field_step_try(axes[d]));++step_cases;
  REQUIRE(px==120+12*dx&&py==100+12*dy&&step_cd==18);
  REQUIRE(invuln==7&&guard_invuln==9&&roll_ticks==11&&roll_cd==13);
  REQUIRE(!field_step_try(axes[d]));
  REQUIRE(px==120+12*dx&&py==100+12*dy&&step_cd==18);
 }
 for(i=0;i<7;i++){
  place(120,100,0,0);step_cd=0;face=3;
  REQUIRE(!field_step_try(invalid[i]));++step_cases;
  REQUIRE(px==120&&py==100&&!step_cd&&face==3);
 }
 return 0;
}

static int modal_and_hitstop_frames_do_not_advance_gameplay_clocks(void){
 unsigned state,frame;
 room=14;place(120,100,0,0);keys=pressed=0;ticks=0;
 for(state=2;state<=3;state++){
  game_state=(int)state;step_cd=11;ability_cd=17;invuln=19;guard_invuln=23;
  heal_cd=29;stone_guard=31;transition_lock=37;
  weapon_action_init(&weapon_action);weapon_action.weapon_class=EQUIPMENT_SWORD;
  weapon_action.phase=WEAPON_WINDUP;weapon_action.age=1;
  for(frame=0;frame<8;frame++){
   update();
   REQUIRE(game_state==(int)state&&ticks==0&&px==120&&py==100);
   REQUIRE(step_cd==11&&ability_cd==17&&invuln==19&&guard_invuln==23);
   REQUIRE(heal_cd==29&&stone_guard==31&&transition_lock==37);
   REQUIRE(weapon_action.age==1&&weapon_action.phase==WEAPON_WINDUP);
  }
 }
 game_state=1;hitstop=2;
 update();REQUIRE(ticks==1&&hitstop==1&&step_cd==11&&ability_cd==17&&invuln==19);
 update();REQUIRE(ticks==2&&hitstop==0&&step_cd==11&&ability_cd==17&&invuln==19);
 weapon_action_init(&weapon_action);
 gear_stats=(EquipmentStats){96,320,226,0,0,42,75,0,0,1,255};
 update();
 REQUIRE(game_state==1&&ticks==3&&step_cd==10&&ability_cd==16&&invuln==18);
 REQUIRE(guard_invuln==22&&heal_cd==28&&stone_guard==30&&transition_lock==36);
 keys=pressed=8;update();
 REQUIRE(game_state==3&&step_cd==10&&ability_cd==16&&invuln==18);
 REQUIRE(guard_invuln==22&&heal_cd==28&&stone_guard==30&&transition_lock==36);
 return 0;
}

static int rectangles_match_the_actual_point_predicate(void){
 unsigned area;
 for(area=0;area<78;area++){
  unsigned supported=0;
  int width,height,x0,y0;
  room=(int)area;width=world_width();height=world_height();
  for(y0=-8;y0<height+8;y0+=29)for(x0=-8;x0<width+8;x0+=29){
   short rects[256][4],guarded[258][4];
   int x1=x0+15,y1=y0+15,count,i,x,y;
   count=game_collision_rects(x0,y0,x1,y1,rects,256);++geometry_queries;
   REQUIRE(count>=-1&&count<=256);
   if(count<0){++geometry_fallbacks;continue;}
   ++supported;
   for(i=0;i<count;i++){
    REQUIRE(rects[i][0]>=x0&&rects[i][1]>=y0&&rects[i][2]<=x1&&rects[i][3]<=y1);
    REQUIRE(rects[i][0]<=rects[i][2]&&rects[i][1]<=rects[i][3]);
   }
   for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++){
    int occupied=0;
    for(i=0;i<count;i++)if(x>=rects[i][0]&&x<=rects[i][2]&&y>=rects[i][1]&&y<=rects[i][3])occupied=1;
    REQUIRE(occupied==!!solid(x,y));++geometry_points;
   }
   if(count>1){
    unsigned cap=(unsigned)count-1;
    memset(guarded,0x66,sizeof guarded);
    REQUIRE(game_collision_rects(x0,y0,x1,y1,guarded+1,cap)==-1);
    for(i=0;i<4;i++)REQUIRE(guarded[0][i]==0x6666&&guarded[cap+1][i]==0x6666);
   }
  }
  if(area<46||area>=54)REQUIRE(supported>0);
  {
   short out[256][4];
   REQUIRE(game_collision_rects(0,0,15,15,out,0)==-1);
   REQUIRE(game_collision_rects(0,0,15,15,out,257)==-1);
   REQUIRE(game_collision_rects(0,0,15,15,0,256)==-1);
   REQUIRE(game_collision_rects(16,0,15,15,out,256)==-1);
   REQUIRE(game_collision_rects(INT_MIN,0,INT_MAX,15,out,256)==-1);
  }
 }
 REQUIRE(geometry_queries>1000&&geometry_points>100000);
 return 0;
}

static int damage_is_bounded_and_monotone(void){
 static const unsigned phases[6]={0,1,2,3,4,255};
 static const unsigned invalid[5]={5,6,254,256,UINT_MAX};
 unsigned a,d,base,attack,defense,i;
 for(a=0;a<6;a++)for(d=0;d<6;d++){
  unsigned multiplier=combat_phase_multiplier_q8(phases[a],phases[d]);
  REQUIRE(multiplier>=224&&multiplier<=320);
  if(a==5||d==5||a==d)REQUIRE(multiplier==256);
  for(base=1;base<=255;base++)for(attack=0;attack<=24;attack++){
   unsigned previous=256;
   for(defense=0;defense<=255;defense++){
    unsigned damage=combat_damage_q4(base,attack,defense,phases[a],phases[d],0);
    ++damage_cases;
    REQUIRE(damage>=4&&damage<=255&&damage<=previous);
    REQUIRE(combat_damage_q4(base,attack,defense,phases[a],phases[d],1)==0);
    if(attack)REQUIRE(damage>=combat_damage_q4(base,attack-1,defense,phases[a],phases[d],0));
    if(base>1)REQUIRE(damage>=combat_damage_q4(base-1,attack,defense,phases[a],phases[d],0));
    previous=damage;
   }
  }
 }
 REQUIRE(combat_damage_q4(0,0,0,255,255,0)==0);
 REQUIRE(combat_damage_q4(256,0,0,255,255,0)==0);
 REQUIRE(combat_damage_q4(32,25,0,255,255,0)==0);
 REQUIRE(combat_damage_q4(32,0,256,255,255,0)==0);
 for(i=0;i<5;i++){
  REQUIRE(combat_damage_q4(32,0,0,invalid[i],255,0)==0);
  REQUIRE(combat_damage_q4(32,0,0,255,invalid[i],0)==0);
 }
 return 0;
}

static int permanent_bonuses_preserve_attackability(void){
 unsigned attack,upgrade,relics,later,weapon;
 for(attack=0;attack<=24;attack++)for(upgrade=0;upgrade<2;upgrade++)
 for(relics=0;relics<8;relics++)for(later=0;later<16;later++)for(weapon=1;weapon<=3;weapon++){
  EquipmentStats stats={96,320,226,0,0,42,75,0,0,1,255};
  WeaponAttack action;
  stats.attack_q4=(EquipmentU8)attack;stats.weapon_class=(EquipmentU8)weapon;
  adventure_save.economy.upgrade=(unsigned char)upgrade;
  adventure_save.economy.relics=(unsigned char)relics;
  adventure_save.economy.later_claims=(unsigned char)later;
  game_gear_bonus_stats(&stats);weapon_action_init(&action);++bonus_cases;
  REQUIRE(stats.attack_q4>=attack&&stats.attack_q4<=EQUIPMENT_MAX_ATTACK_Q4);
  REQUIRE(stats.defense_q4<=EQUIPMENT_MAX_DEFENSE_Q4);
  REQUIRE(stats.speed_q8<=EQUIPMENT_MAX_SPEED_Q8);
  REQUIRE(weapon_action_tick(&action,&stats,0,1,1,0)&WEAPON_EVENT_START);
  REQUIRE(combat_damage_q4(32,stats.attack_q4,0,stats.phase,255,0)>=32);
 }
 return 0;
}

static int physical_button_sequences_have_one_owner(void){
 unsigned sequence;
 for(sequence=0;sequence<4096;sequence++){
  FieldControlState state;
  unsigned frame,previous=0,blocked=0;
  field_controls_reset(&state,0);
  for(frame=0;frame<6;frame++){
   unsigned buttons=(sequence>>(frame*2))&3u;
   unsigned held=(buttons&1u?2u:0u)|(buttons&2u?256u:0u)|16u;
   unsigned pressed=held&~previous;
   FieldControlInput actual=field_controls_read(&state,held,pressed);
   if(!(buttons&1u))blocked=0;
   else if(buttons&2u)blocked=1;
   ++control_cases;
   REQUIRE(actual.companion_pressed==(pressed&256u));
   REQUIRE(!!(actual.power_held&256u)==(!!(buttons&1u)&&!blocked));
   REQUIRE(!!(actual.power_pressed&256u)==(!!(pressed&2u)&&!blocked));
   REQUIRE(!(actual.power_pressed&2u)&&!(actual.power_held&2u));
   REQUIRE(actual.power_held&16u);
   previous=held;
  }
 }
 {
  FieldControlState state;
  FieldControlInput actual;
  field_controls_reset(&state,2);
  actual=field_controls_read(&state,2,0);REQUIRE(!(actual.power_held&256u));
  field_controls_read(&state,0,0);
  actual=field_controls_read(&state,2,2);REQUIRE(actual.power_pressed&256u);
 }
 return 0;
}

typedef struct {int ox,oy,dx,dy,wall,probes,targets,hit;} ArrowScenario;

static int arrow_wall(void*context,int x,int y){
 ArrowScenario*s=context;
 int distance=(x-s->ox)*s->dx+(y-s->oy)*s->dy;
 if(distance!=s->probes+1||x!=s->ox+s->dx*distance||y!=s->oy+s->dy*distance)s->hit=-1;
 ++s->probes;
 return distance==s->wall;
}

static int arrow_target(void*context,int x,int y){
 ArrowScenario*s=context;
 int distance=(x-s->ox)*s->dx+(y-s->oy)*s->dy;
 ++s->targets;
 if(distance>=s->wall)s->hit=-1;
 return 0;
}

static int arrows_visit_every_pixel_before_any_target(void){
 static const int direction[4][2]={{0,1},{0,-1},{-1,0},{1,0}};
 unsigned d,speed,wall,target;
 for(d=0;d<4;d++)for(speed=1;speed<=8;speed++)for(wall=1;wall<=speed;wall++){
  WeaponArrow arrow={0};
  ArrowScenario scenario={500,500,direction[d][0],direction[d][1],(int)wall,0,0,0};
  arrow.x_q8=500*256;arrow.y_q8=500*256;arrow.remaining_q8=100*256;
  arrow.speed_q8=(EquipmentU16)(speed*256);arrow.active=1;arrow.direction=(EquipmentU8)d;
  weapon_arrow_tick(&arrow,arrow_wall,arrow_target,&scenario);++arrow_cases;
  REQUIRE(!arrow.active&&scenario.hit==0);
  REQUIRE(scenario.probes==(int)wall&&scenario.targets==(int)wall-1);
 }
 for(target=0;target<16;target++){
  WeaponAttack action={0};action.phase=WEAPON_ACTIVE;action.weapon_class=EQUIPMENT_SWORD;
  REQUIRE(weapon_action_mark_hit(&action,target));
  REQUIRE(!weapon_action_mark_hit(&action,target));
  REQUIRE(!weapon_action_mark_hit(&action,16));
  REQUIRE(!weapon_action_mark_hit(&action,UINT_MAX));
 }
 return 0;
}

#undef main
int main(int argc,char**argv){
 int failed=0;
 if(argc!=2)return 2;
 if(!strcmp(argv[1],"movement"))failed=movement_stays_outside_solids()||cardinal_steps_are_bounded_without_defensive_bonuses();
 else if(!strcmp(argv[1],"invalid_rooms"))failed=invalid_rooms_do_not_authorize_movement();
 else if(!strcmp(argv[1],"geometry"))failed=rectangles_match_the_actual_point_predicate();
 else if(!strcmp(argv[1],"updates"))failed=modal_and_hitstop_frames_do_not_advance_gameplay_clocks();
 else if(!strcmp(argv[1],"combat"))failed=damage_is_bounded_and_monotone()||permanent_bonuses_preserve_attackability();
 else if(!strcmp(argv[1],"controls"))failed=physical_button_sequences_have_one_owner();
 else if(!strcmp(argv[1],"arrows"))failed=arrows_visit_every_pixel_before_any_target();
 else return 2;
 if(failed)return 1;
 printf("{\"scenario\":\"%s\",\"checks\":%lu,\"corners\":%lu,\"moves\":%lu,\"damage_cases\":%lu,\"bonus_cases\":%lu,\"control_cases\":%lu,\"arrow_cases\":%lu,\"geometry_queries\":%lu,\"geometry_points\":%lu,\"geometry_fallbacks\":%lu,\"step_cases\":%lu}\n",argv[1],checks,corners,moves,damage_cases,bonus_cases,control_cases,arrow_cases,geometry_queries,geometry_points,geometry_fallbacks,step_cases);
 return 0;
}
