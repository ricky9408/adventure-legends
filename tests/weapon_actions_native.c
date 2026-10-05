#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "weapon_actions.h"
static unsigned checks;
#define CHECK(x) do {assert(x);++checks;} while(0)
static EquipmentStats stats(unsigned cls){EquipmentStats s={96,320,226,0,0,42,75,0,0,0,255};s.weapon_class=(EquipmentU8)cls;return s;}
static unsigned tick(WeaponAttack*a,EquipmentStats*s,unsigned d,int h,int p,unsigned live){return weapon_action_tick(a,s,d,h,p,live);}
static void melee(void){
    WeaponAttack a;EquipmentStats s=stats(1);unsigned e,i,d;weapon_action_init(&a);
    CHECK(tick(&a,&s,3,1,1,0)==WEAPON_EVENT_START);
    CHECK(a.phase==WEAPON_WINDUP);
    CHECK(tick(&a,&s,3,1,0,0)==0);
    CHECK(tick(&a,&s,0,1,0,0)==WEAPON_EVENT_ACTIVE);
    CHECK(a.direction==3);
    CHECK(a.damage_q4==32);
    CHECK(a.combo==1);
    CHECK(weapon_action_contains(&a,100,100,129,100));
    CHECK(!weapon_action_contains(&a,100,100,130,100));
    CHECK(!weapon_action_contains(&a,100,100,93,100));
    CHECK(!weapon_action_contains(&a,100,100,110,120));
    CHECK(weapon_action_can_hit(&a,0));
    CHECK(weapon_action_mark_hit(&a,0));
    CHECK(!weapon_action_mark_hit(&a,0));
    CHECK(weapon_action_mark_hit(&a,15));
    CHECK(!weapon_action_mark_hit(&a,16));
    for(i=3;i<=17;i++)tick(&a,&s,3,0,0,0);
    CHECK(a.phase==WEAPON_IDLE);
    tick(&a,&s,3,1,1,0);
    CHECK(a.combo==2);
    CHECK(a.hit_mask==0);
    for(i=1;i<=17;i++)tick(&a,&s,3,0,0,0);
    tick(&a,&s,3,1,1,0);
    CHECK(a.combo==3);
    CHECK(a.damage_q4==48);
    CHECK(tick(&a,&s,3,0,0,0)==0);
    CHECK(tick(&a,&s,3,0,0,0)==0);
    CHECK(tick(&a,&s,3,0,0,0)==WEAPON_EVENT_ACTIVE);
    for(i=4;i<=24;i++)tick(&a,&s,3,0,0,0);
    tick(&a,&s,3,1,1,0);
    CHECK(a.combo==1);
    for(i=0;i<100;i++)tick(&a,&s,3,0,0,0);
    CHECK(!a.combo_clock);
    for(d=0;d<4;d++){
        weapon_action_init(&a);s=stats(2);s.attack_q4=4;s.reach_px=4;s.stagger=1;
        tick(&a,&s,d,1,1,0);
    CHECK(a.damage_q4==48&&a.reach_px==47);
        s.attack_q4=24;s.reach_px=0;s.stagger=3;
        for(i=1;i<6;i++)CHECK(tick(&a,&s,(d+1)%4,0,0,0)==0);
        CHECK(a.attack_q4==4&&a.reach_px==47&&a.stagger==1);
        for(i=6;i<9;i++){e=tick(&a,&s,(d+1)%4,0,0,0);
    CHECK(e==WEAPON_EVENT_ACTIVE);
    CHECK(a.direction==d);}
        CHECK(tick(&a,&s,d,0,0,0)==0);
    CHECK(a.phase==WEAPON_RECOVERY);
        for(i=10;i<=29;i++)tick(&a,&s,d,0,0,0);
    CHECK(a.phase==WEAPON_IDLE);
    }
    weapon_action_init(&a);s=stats(2);tick(&a,&s,3,1,1,0);
    for(i=1;i<=6;i++)tick(&a,&s,3,0,0,0);
    CHECK(weapon_action_contains(&a,100,100,143,106));
    CHECK(!weapon_action_contains(&a,100,100,143,107));
    CHECK(!weapon_action_contains(&a,100,100,99,100));
    CHECK(!weapon_action_contains(&a,100,100,144,100));
    CHECK(!weapon_action_contains(&a,-1,100,100,100));
}
static void buffers(void){
    WeaponAttack a;EquipmentStats s=stats(1);unsigned i,e;weapon_action_init(&a);tick(&a,&s,0,1,1,0);
    for(i=1;i<=16;i++)tick(&a,&s,0,0,i==15,0);
    e=tick(&a,&s,2,0,0,0);
    CHECK(e==(WEAPON_EVENT_FINISH|WEAPON_EVENT_START));
    CHECK(a.direction==2&&a.combo==2);
    for(i=1;i<=17;i++)tick(&a,&s,0,0,i==3,0);
    CHECK(a.phase==WEAPON_IDLE);
    weapon_action_init(&a);tick(&a,&s,0,1,1,0);for(i=1;i<=15;i++)tick(&a,&s,0,0,i==15,0);
    CHECK(a.buffer);weapon_action_suspend(&a);
    CHECK(!a.buffer);
    CHECK(a.age==15);
    tick(&a,&s,0,1,0,0);tick(&a,&s,0,1,0,0);
    CHECK(a.phase==WEAPON_IDLE);
    tick(&a,&s,0,1,1,0);
    CHECK(a.phase==WEAPON_IDLE);tick(&a,&s,0,0,0,0);
    CHECK(tick(&a,&s,0,1,1,0)==WEAPON_EVENT_START);
}
static void bow(void){
    WeaponAttack a;WeaponArrow arrow={0},other={0};EquipmentStats s=stats(3);unsigned e,i;
    weapon_action_init(&a);
    CHECK(tick(&a,&s,0,1,1,0)==WEAPON_EVENT_START);
    CHECK(a.phase==WEAPON_CHARGING);
    CHECK(tick(&a,&s,1,0,0,0)==0);
    CHECK(a.phase==WEAPON_WINDUP&&a.age==2);
    CHECK(tick(&a,&s,2,0,0,0)==0);e=tick(&a,&s,3,0,0,0);
    CHECK(e==WEAPON_EVENT_ARROW);
    CHECK(a.direction==1&&a.damage_q4==32&&a.reach_px==112);
    CHECK(weapon_arrow_spawn(&arrow,&a,100,100));
    CHECK(!weapon_arrow_spawn(&other,&a,100,100));
    CHECK(arrow.direction==1&&arrow.remaining_q8==112*256&&arrow.speed_q8==1024);
    CHECK(weapon_action_busy(&a,1)==(EQUIPMENT_BUSY_RECOVERING|EQUIPMENT_BUSY_PLAYER_PROJECTILE));
    for(i=1;i<23;i++)CHECK(tick(&a,&s,0,0,0,1)==0);
    CHECK(tick(&a,&s,0,0,0,1)==WEAPON_EVENT_FINISH);
    weapon_action_init(&a);s.attack_q4=4;s.reach_px=4;tick(&a,&s,0,1,1,0);
    for(i=1;i<24;i++)tick(&a,&s,3,1,0,0);
    CHECK(a.charge==24);
    CHECK(tick(&a,&s,3,0,0,0)==WEAPON_EVENT_ARROW);
    CHECK(a.damage_q4==48&&a.reach_px==148&&a.attack_q4==4);
    for(i=0;i<23;i++)tick(&a,&s,0,0,0,0);
    tick(&a,&s,0,1,1,0);for(i=1;i<200;i++)tick(&a,&s,2,1,0,0);
    CHECK(a.charge==45&&a.phase==WEAPON_CHARGING);
    CHECK(tick(&a,&s,2,0,0,2)==WEAPON_EVENT_BLOCKED);
    CHECK(!a.arrow_pending);
    weapon_action_init(&a);tick(&a,&s,0,1,1,0);weapon_action_suspend(&a);
    CHECK(a.phase==WEAPON_IDLE);
    for(i=0;i<50;i++)CHECK(tick(&a,&s,0,1,0,0)==0);
    CHECK(tick(&a,&s,0,0,0,0)==0);
    CHECK(a.phase==WEAPON_IDLE);
    tick(&a,&s,0,1,1,0);tick(&a,&s,0,0,0,0);weapon_action_suspend(&a);
    for(i=0;i<50;i++)CHECK(tick(&a,&s,0,0,0,0)==0);
    CHECK(a.phase==WEAPON_IDLE);
}
typedef struct {int wall,target,wcalls,tcalls,lastx;} World;
static int wall(void*p,int x,int y){World*w=p;(void)y;++w->wcalls;w->lastx=x;return x==w->wall;}
static int target(void*p,int x,int y){World*w=p;(void)y;++w->tcalls;return x==w->target;}
static WeaponArrow make_arrow(void){WeaponArrow a={100*256,100*256,112*256,1024,1,3,32,4,0,255,{0,0}};return a;}
static void arrows(void){
    WeaponArrow a=make_arrow();World w={102,103,0,0,0};unsigned i;
    weapon_arrow_tick(&a,wall,target,&w);
    CHECK(!a.active);
    CHECK(a.x_q8==102*256);
    CHECK(w.wcalls==2&&w.tcalls==1);a=make_arrow();w=(World){200,102,0,0,0};
    weapon_arrow_tick(&a,wall,target,&w);
    CHECK(!a.active&&a.x_q8==102*256);
    CHECK(w.tcalls==2);
    a=make_arrow();w=(World){-1,-1,0,0,0};for(i=0;i<28;i++)weapon_arrow_tick(&a,wall,target,&w);
    CHECK(!a.active&&a.x_q8==212*256&&a.remaining_q8==0);
    CHECK(w.wcalls==112&&w.tcalls==112);
    a=make_arrow();a.direction=2;a.x_q8=1*256;weapon_arrow_tick(&a,wall,target,&w);
    CHECK(!a.active);
    a=make_arrow();a.speed_q8=65535;weapon_arrow_tick(&a,wall,target,&w);
    CHECK(!a.active);
    a=make_arrow();weapon_arrow_tick(&a,0,target,&w);
    CHECK(a.x_q8==100*256&&a.active);
}
static void invalid_and_fuzz(void){
    WeaponAttack a,old;EquipmentStats s=stats(1);unsigned i,r=123,e;weapon_action_init(&a);old=a;
    CHECK(!tick(&a,&s,4,1,1,0));
    CHECK(!memcmp(&a,&old,sizeof a));
    CHECK(!tick(&a,&s,0,1,1,3));
    CHECK(!memcmp(&a,&old,sizeof a));
    s.weapon_class=0;
    CHECK(!tick(&a,&s,0,1,1,0));
    CHECK(!memcmp(&a,&old,sizeof a));
    for(i=0;i<200000;i++){
        r=r*1664525u+1013904223u;
        if((r&1023u)==0)weapon_action_init(&a);
        if((r&127u)==1)weapon_action_suspend(&a);
        s=stats(1+((r>>16)%3));s.attack_q4=(r>>12)%25;s.reach_px=(r>>8)%5;
        e=tick(&a,&s,(r>>4)&3,r&1,(r>>1)&1,(r>>24)%3);
        CHECK(e<32&&a.phase<=WEAPON_CHARGING&&a.direction<4&&a.charge<=45);
        if(e&WEAPON_EVENT_ARROW){WeaponArrow arrow={0};
    CHECK(weapon_arrow_spawn(&arrow,&a,480,320));}
    }
}
int main(void){melee();buffers();bow();arrows();invalid_and_fuzz();printf("weapon action checks: %u\n",checks);return 0;}
