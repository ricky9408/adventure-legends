/* Synthetic scene integration using REAL current catalog and Q4 damage.
 * This is not controller-earned playability, cadence or acquisition evidence. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "return_powers.h"
#include "return_power_art.h"
#include "northern_powers.h"
#include "return_game.h"
#include "progression.h"
#include "gear_runtime.h"
#include "combat_rules.h"
#include "obj_layout.h"
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
Enemy enemies[6];Shot shots[12];volatile int px,py,room;
int face,ability_cd,ability_max,hitstop;
int enemy_windups[6],enemy_clocks[6],enemy_aimx[6],enemy_aimy[6];
static CreatureInstance caster;
static unsigned owner,generation,token,field_count,field_calls,field_accepts,draws,max_draws,solid_calls,max_solid;
static int field_x,field_y,field_radius=12,absent,wall_count;
static unsigned char vram[16384];
static int draw_x[32],draw_y[32],draw_off[32],draw_w[32];
static struct {int x,y,w,h;} walls[8];
static const unsigned forms[15]={3,6,9,12,15,17,18,21,24,27,30,101,102,103,104};
static const unsigned masks[15]={1025,1026,1028,1032,1040,1024,3072,1056,1088,1025,1025,0,1024,0,1024};
static const unsigned lifetime[15]={72,60,56,48,48,42,52,60,54,50,60,24,48,30,42};
static const unsigned cooldown[15]={135,150,135,150,135,120,150,135,150,135,150,90,120,90,120};
static const unsigned damage[15]={32,0,28,24,20,24,28,24,28,28,24,16,0,20,24};
static const unsigned startup[15]={10,10,10,10,10,8,12,10,10,10,12,8,10,8,10};
int northern_powers_tiles_claim(unsigned o){if(owner||o!=NORTHERN_TILES_RETURN)return 0;owner=o;generation++;return 1;}
int northern_powers_tiles_release(unsigned o){if(owner!=o||return_power_time)return 0;owner=0;generation++;return 1;}
unsigned northern_powers_tiles_owner(void){return owner;}
unsigned northern_powers_tiles_generation(void){return generation;}
CreatureInstance*progression_selected(void){return absent?0:&caster;}
void impact(int x,int y){(void)x;(void)y;}
void sfx(int s){(void)s;}
void kill_enemy(Enemy*e){assert(e>=enemies&&e<enemies+6);e->hp=0;}
void obj_upload(const unsigned char*p,int w,int h,int off){assert(off==GFX_OBJ_POWER_PIN||off==GFX_OBJ_WATER_DROP);memcpy(vram+off,p,(unsigned)(w*h));}
void obj_add(int off,int x,int y,int w,int h,int priority,int depth,int flip){(void)priority;(void)depth;(void)flip;assert((off==GFX_OBJ_POWER_PIN||off==GFX_OBJ_WATER_DROP)&&(w==8||w==16)&&(h==8||h==16));assert(draws<32);draw_x[draws]=x;draw_y[draws]=y;draw_off[draws]=off;draw_w[draws]=w;draws++;}
int solid(int x,int y){int i;solid_calls++;if(x<0||y<0||x>=480||y>=320)return 1;
 for(i=0;i<wall_count;i++)if(x>=walls[i].x&&y>=walls[i].y&&x<walls[i].x+walls[i].w&&y<walls[i].y+walls[i].h)return 1;return 0;}
int game_clear_box(int x0,int y0,int x1,int y1){int i;if(x0<0||y0<0||x1>=480||y1>=320||x0>x1||y0>y1)return 0;
 for(i=0;i<wall_count;i++)if(x0<walls[i].x+walls[i].w&&x1>=walls[i].x&&y0<walls[i].y+walls[i].h&&y1>=walls[i].y)return 0;return 1;}
int return_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
unsigned return_game_action_begin(unsigned c){assert(c==3);return ++token;}
int return_game_field_target(unsigned i,int*x,int*y,int*r){if(i>=field_count)return 0;*x=field_x;*y=field_y;*r=field_radius;return 1;}
int return_game_field_hit(unsigned i,unsigned command,unsigned identity,unsigned form,unsigned t){assert(i<field_count);field_calls++;
 if(identity!=caster.instance_id||form!=caster.form_id||command!=caster.equipped[caster.selected_command]||t!=token)return 0;field_accepts++;return 1;}
static void enemy(unsigned i,int f,int s,int kind){enemies[i]=(Enemy){100+f,100+s,100,0,kind};enemy_hp_q4[i]=1600;enemy_phases[i]=255;return_powers_enemy_spawn(i);}
static void shot(unsigned i,int f,int s,int df,int ds,int hostile){shots[i]=(Shot){100+f,100+s,df,ds,90,hostile};return_powers_shot_spawn(i);}
static void wall(int x,int y,int w,int h){assert(wall_count<8);walls[wall_count].x=x;walls[wall_count].y=y;walls[wall_count].w=w;walls[wall_count++].h=h;return_powers_geometry_changed();}
static void setup(unsigned c){const CreatureForm*f;return_powers_reset();owner=0;memset(enemies,0,sizeof enemies);memset(shots,0,sizeof shots);memset(enemy_windups,0,sizeof enemy_windups);memset(enemy_aimx,0,sizeof enemy_aimx);memset(enemy_aimy,0,sizeof enemy_aimy);
 field_count=field_calls=field_accepts=draws=solid_calls=0;wall_count=absent=ability_cd=hitstop=0;field_radius=12;px=py=100;room=54;face=3;
 f=creatures_form(forms[c-91]);assert(f);memset(&caster,0,sizeof caster);caster.form_id=f->id;caster.flags=CREATURE_OCCUPIED;caster.level=40;caster.xp=creatures_xp_threshold(40);caster.bond=80;caster.instance_id=7;caster.polarity=f->polarity;caster.trial_flags=masks[c-91];caster.equipped[0]=(CreatureU8)c;
 assert(creatures_instance_validate(&caster));gear_stats.power_cooldown=EQUIPMENT_BASE_POWER_COOLDOWN;
}
static void tick(void){solid_calls=0;return_powers_tick();if(!hitstop&&ability_cd)ability_cd--;draws=0;return_powers_draw();if(draws>max_draws)max_draws=draws;if(solid_calls>max_solid)max_solid=solid_calls;assert(draws<=25);assert(return_powers_moving_objects()<=2);}
static void updates(unsigned n){while(n--)tick();}
static void prepare_hit(unsigned c){unsigned i;
 switch(c){
 case 91:enemy(0,30,0,0);break;
 case 93:enemy(0,10,0,0);break;
 case 94:enemy(0,24,0,0);break;
 case 95:enemy(0,20,0,0);break;
 case 96:enemy(0,26,0,0);break;
 case 97:enemy(0,20,12,0);break;
 case 98:enemy(0,33,0,0);break;
 case 99:enemy(0,10,0,0);break;
 case 100:enemy(0,12,0,0);break;
 case 101:enemy(0,20,-12,0);break;
 case 102:enemy(0,20,-8,2);enemy_windups[0]=30;enemy_aimy[0]=-2;break;
 case 104:enemy(0,14,0,0);break;
 case 105:enemy(0,34,0,0);break;
 default:enemy(0,20,0,0);break;
 }
 for(i=1;i<6;i++){enemies[i]=enemies[0];enemy_hp_q4[i]=1600;enemy_phases[i]=255;enemy_windups[i]=enemy_windups[0];enemy_aimy[i]=enemy_aimy[0];return_powers_enemy_spawn(i);}
}
static void help(unsigned c,unsigned age){if(c==91&&age==22)assert(return_powers_input(256)&2);
 if((c==94&&age==10)||(c==96&&age==8)){shot(0,22,0,-4,0,1);assert(return_powers_intercept_shot(0,122,100,118,100,1));assert(!shots[0].life);if(c==96)assert(return_powers_input(256)&2);}
 if(c==95&&age==10){unsigned i;for(i=0;i<6;i++)enemies[i].x++;}
 if(c==98&&age==12){unsigned i;for(i=0;i<6;i++)enemies[i].x++;}
}
static void all_commands(void){unsigned c,a,i;for(c=91;c<=105;c++){setup(c);prepare_hit(c);assert(return_power(c));assert(return_power_form==(int)forms[c-91]);assert(return_power_phase==creatures_ability(c)->phase);assert(ability_cd==(int)cooldown[c-91]);assert(!return_power(c));
 for(a=1;a<=lifetime[c-91];a++){tick();help(c,a);}assert(!return_power_time&&!owner);assert(return_power_age==(int)lifetime[c-91]);
 if(damage[c-91])assert(enemy_hp_q4[0]==1600-(int)damage[c-91]);else assert(enemy_hp_q4[0]==1600);
 for(i=1;i<6;i++){int single=c==95||c==98||c==102||c==104;if(damage[c-91])assert(enemy_hp_q4[i]==1600-(single?0:(int)damage[c-91]));}
 }printf("all15 commands: distinct authored hits/guards, six slots, once per cast\n");}
static void guard_cases(void){const unsigned guards[4]={92,94,96,103};unsigned q;for(q=0;q<4;q++){unsigned c=guards[q];int pos=c==92?24:c==103?29:22;setup(c);assert(return_power(c));updates(startup[c-91]);
 shot(0,pos,0,-4,0,1);assert(!return_powers_intercept_shot(0,100+pos,100,96+pos,100,0));assert(shots[0].life); /* explicit boss/special provenance exclusion */
 shots[0].owner=0;assert(!return_powers_intercept_shot(0,100+pos,100,96+pos,100,1));shots[0].owner=1;
 shot(1,pos-4,0,4,0,1);assert(!return_powers_intercept_shot(1,96+pos,100,100+pos,100,1)); /* open back */
 assert(return_powers_intercept_shot(0,100+pos,100,96+pos,100,1));assert(!shots[0].life);
 shot(0,pos,0,-4,0,1);tick();assert(!return_powers_intercept_shot(0,100+pos,100,96+pos,100,1));assert(shots[0].life); /* recycled pool serial cannot recycle guard */
 }puts("ordinary-only guards: front/back, owner, pool reuse, one consumption");}
static void controls(void){unsigned c;for(c=91;c<=105;c++){int age,cd,time;setup(c);assert(return_power(c));updates(4);age=return_power_age;cd=ability_cd;time=return_power_time;hitstop=1;updates(20);assert(return_power_age==age&&ability_cd==cd&&return_power_time==time);hitstop=0;
 assert(return_powers_input(16|32)==0);return_powers_selection_changed();caster.instance_id=8;caster.instance_id=7;assert(!return_powers_can_aim());updates(lifetime[c-91]+2);assert(!return_power_time);assert(ability_cd>0);return_powers_reset();assert(ability_cd>0);}
 setup(91);assert(return_power(91));updates(8);{int cd=ability_cd,age=return_power_age;assert(return_powers_input(256)==2);assert(ability_cd==cd&&return_power_age==age);assert(!return_powers_input(256));}updates(80);
 setup(96);assert(return_power(96));updates(8);assert(!return_powers_input(256));updates(80);assert(!return_power_time);puts("control/cancel: freeze, fresh direction, finite release, no cooldown refunds");}
static void geometry_cases(void){unsigned c;for(c=91;c<=105;c++){setup(c);field_count=1;field_x=124;field_y=100;wall(111,0,2,320);assert(return_power(c));updates(lifetime[c-91]);assert(field_accepts==0);}
 setup(97);enemy(0,20,0,0);assert(return_power(97));updates(40);assert(enemy_hp_q4[0]==1600);assert(!return_powers_overlap(120,100,0));assert(return_powers_overlap(120,112,0));assert(return_powers_overlap(120,111,0));assert(!return_powers_overlap(122,114,0));
 /* Target boundary intersects a genuine live pixel even when center is well
  * outside that narrow lane. Radius12 octagon includes dx0,dy12. */
 assert(return_powers_overlap(120,124,12));assert(!return_powers_overlap(120,127,12));
 wall(120,114,1,10);tick();assert(!return_powers_overlap(120,125,12));
 setup(97);field_count=1;field_x=120;field_y=112;assert(return_power(97));return_powers_selection_changed();updates(40);assert(!field_accepts);puts("geometry: exact visible diamond/target extents, gaps, wall LOS, revoked fields");}
static void identity_displacement(void){unsigned c;setup(97);enemy(0,20,12,0);assert(return_power(97));updates(12);assert(enemy_hp_q4[0]<1600);enemy(0,20,12,0);updates(40);assert(enemy_hp_q4[0]==1600);
 for(c=95;c<=104;c++){int x,y;if(c!=95&&c!=98&&c!=101&&c!=104)continue;setup(c);prepare_hit(c);assert(return_power(c));x=enemies[0].x;y=enemies[0].y;wall(x+3,y-16,1,32);{unsigned a;for(a=1;a<=lifetime[c-91];a++){tick();help(c,a);}}assert(abs(enemies[0].x-x)+abs(enemies[0].y-y)<=9);assert(!solid(enemies[0].x,enemies[0].y));}
 setup(104);enemy(0,14,0,3);assert(return_power(104));updates(40);assert(enemy_hp_q4[0]==1600&&enemies[0].y==100);
 setup(102);prepare_hit(102);enemy_aimy[0]=2;assert(return_power(102));updates(24);assert(enemy_windups[0]==30&&enemy_hp_q4[0]==1600);puts("identity/displacement: slot reuse, walls, ordinary-only, quiet-cut wrong side");}
static void art_contract(void){unsigned c,k;int x,y;assert(return_power_marks[0][11*16+3]==13);assert(return_power_marks[1][4*16+12]==50);
 for(c=0;c<15;c++)for(k=0;k<2;k++)for(y=0;y<8;y++)for(x=0;x<8;x++)assert(!!return_power_particles[c][k][y*8+x]==(abs(x-3)+abs(y-3)<=2));
 puts("art: row-major preview icons and exact13-pixel native collision masks");}
static void refined_contract_cases(void){unsigned a;int before;
 setup(91);enemy(0,26,0,0);assert(return_power(91));updates(8);before=ability_cd;assert(return_powers_input(256)==2);assert(ability_cd==before);updates(64);assert(enemy_hp_q4[0]==1584);
 setup(91);enemy(0,38,0,0);assert(return_power(91));updates(72);assert(enemy_hp_q4[0]==1568); /* own ember and finite automatic release */
 setup(96);enemy(0,26,0,0);assert(return_power(96));updates(8);shot(0,22,0,-4,0,1);assert(return_powers_intercept_shot(0,122,100,118,100,1));updates(34);assert(!return_power_time&&enemy_hp_q4[0]==1576);
 setup(99);assert(return_power(99));for(a=0;a<16;a++){px++;tick();}assert(px==116&&py==100);assert(!return_powers_can_release());updates(54);assert(!return_power_time);
 setup(104);enemy(0,14,0,0);assert(return_power(104));updates(30);assert(enemies[0].x==114&&enemies[0].y==92&&px==100&&py==100);
 setup(104);enemy(0,14,0,0);wall(117,94,1,1);assert(return_power(104));updates(30);assert(enemies[0].x==114&&enemies[0].y==100); /* one-pixel offset wall */
 setup(97);field_count=1;field_x=120;field_y=112;assert(return_power(97));token++;updates(52);assert(!field_accepts);
 setup(97);field_count=1;field_x=120;field_y=112;assert(return_power(97));updates(52);assert(field_accepts==1&&field_calls==1);
 puts("refined controls: owned hearth charge/weak release, auto counter, bounded carried heat, exact swept deposit, stale/once field token");
}
static void phase_damage_cases(void){unsigned c,phase,a;for(c=91;c<=105;c++)for(phase=0;phase<6;phase++){
 setup(c);prepare_hit(c);enemy_phases[0]=(unsigned char)(phase==5?255:phase);assert(return_power(c));
 for(a=1;a<=lifetime[c-91];a++){tick();help(c,a);}
 assert(enemy_hp_q4[0]==1600-(int)combat_damage_q4(damage[c-91],0,0,creatures_ability(c)->phase,phase==5?255:phase,0));
 }puts("all15 commands across five phases and neutral use real Q4 runtime");}
static void facings_and_pixels(void){unsigned c,d,a;int x,y;unsigned checked=0;
 for(c=91;c<=105;c++)for(d=0;d<4;d++){setup(c);face=(int)d;assert(return_power(c));
  for(a=1;a<=lifetime[c-91];a++){tick();if(a<startup[c-91]||a>=lifetime[c-91]-(c==96?2:6))continue;
   /* Every 5th active frame, compare rasterized native tile pixels against
    * exact point overlap. Bounds include all command placements/motion. */
   if(a%5)continue;
   for(y=54;y<=146;y++)for(x=54;x<=146;x++){unsigned j;int pixel=0;
    for(j=0;j<draws;j++){int u=x-draw_x[j],v=y-draw_y[j];if(draw_off[j]!=GFX_OBJ_WATER_DROP||draw_w[j]!=8||u<0||v<0||u>=8||v>=8)continue;if(vram[draw_off[j]+v*8+u])pixel=1;}
    assert(return_powers_overlap(x,y,0)==pixel);checked++;
   }
  }
 }
 printf("all4 facings: %u exact visible pixel/point overlap comparisons\n",checked);
}
int main(void){art_contract();refined_contract_cases();phase_damage_cases();facings_and_pixels();all_commands();guard_cases();controls();geometry_cases();identity_displacement();printf("Return host passed; maximum draw=%u, tick solid probes=%u\n",max_draws,max_solid);return 0;}
