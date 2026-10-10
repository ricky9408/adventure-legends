/* Synthetic real-catalog/real-Q4 tests, not controller-route evidence. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "horizons_powers.h"
#include "horizons_power_art.h"
#include "northern_powers.h"
#include "horizons_game.h"
#include "progression.h"
#include "gear_runtime.h"
#include "combat_rules.h"
#include "obj_layout.h"
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
Enemy enemies[6];Shot shots[12];volatile int px,py,room;
int face,ability_cd,ability_max,hitstop;
unsigned char slowed_enemies[6];
static CreatureInstance caster;
static unsigned owner,generation,token,revoked,field_count,field_calls,field_accepts,field_beats,draws,max_draws,solid_calls,max_solid;
static int field_x,field_y,field_radius=12,absent,wall_count;
static unsigned char vram[16384];
static int draw_x[32],draw_y[32],draw_off[32],draw_w[32];
static struct {int x,y,w,h;} walls[8];
static const unsigned lifetime[16]={38,48,42,50,30,42,32,44,36,44,36,44,38,38,44,34};
static const unsigned cooldown[16]={72,88,84,100,66,86,64,84,80,92,74,88,72,76,90,70};
static const unsigned startup[16]={6,8,8,8,6,8,6,8,10,6,6,8,6,6,8,6};
static const unsigned active_time[16]={24,30,24,32,12,22,18,26,10,30,20,24,24,22,28,16};
static const unsigned damage[16]={16,32,32,16,32,16,32,16,48,16,32,16,16,16,32,32};
int northern_powers_tiles_claim(unsigned o){if(owner||o!=NORTHERN_TILES_HORIZONS)return 0;owner=o;generation++;return 1;}
int northern_powers_tiles_release(unsigned o){if(owner!=o||horizons_power_time)return 0;owner=0;generation++;return 1;}
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
int horizons_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
unsigned horizons_game_action_begin(unsigned c){assert(c==3);revoked=0;return ++token;}
void horizons_game_revoke_cast(unsigned t){if(t==token)revoked=1;}
int horizons_game_field_target(unsigned i,int*x,int*y,int*r){if(i>=field_count)return 0;*x=field_x;*y=field_y;*r=field_radius;return 1;}
int horizons_game_field_hit(unsigned i,unsigned command,unsigned identity,unsigned form,unsigned t){assert(i<field_count);field_calls++;
 if(revoked||identity!=caster.instance_id||form!=caster.form_id||command!=caster.equipped[caster.selected_command]||t!=token)return 0;
 field_accepts++;field_beats|=1u<<horizons_powers_beat();return 1;}
static void enemy(unsigned i,int f,int s,int kind){enemies[i]=(Enemy){100+f,100+s,100,0,kind};enemy_hp_q4[i]=1600;enemy_phases[i]=255;horizons_powers_enemy_spawn(i);}
static void shot(unsigned i,int f,int s,int df,int ds,int hostile){shots[i]=(Shot){100+f,100+s,df,ds,90,hostile};horizons_powers_shot_spawn(i);}
static void wall(int x,int y,int w,int h){assert(wall_count<8);walls[wall_count].x=x;walls[wall_count].y=y;walls[wall_count].w=w;walls[wall_count++].h=h;horizons_powers_geometry_changed();}
static void setup(unsigned c){const CreatureForm*f;horizons_powers_reset();owner=0;memset(enemies,0,sizeof enemies);memset(shots,0,sizeof shots);memset(slowed_enemies,0,sizeof slowed_enemies);memset(enemy_stagger_ticks,0,6);
 field_count=field_calls=field_accepts=field_beats=draws=solid_calls=revoked=0;wall_count=absent=ability_cd=hitstop=0;field_radius=12;px=py=100;room=62;face=3;
 f=creatures_form(c-1);assert(f);memset(&caster,0,sizeof caster);caster.form_id=f->id;caster.flags=CREATURE_OCCUPIED;caster.level=40;caster.xp=creatures_xp_threshold(40);caster.bond=80;caster.instance_id=7;caster.polarity=f->polarity;caster.trial_flags=(c==107||c==109||c==111||c==113)?1024:0;caster.equipped[0]=(CreatureU8)c;
 assert(creatures_instance_validate(&caster));gear_stats.power_cooldown=EQUIPMENT_BASE_POWER_COOLDOWN;
}
static void tick(void){solid_calls=0;horizons_powers_tick();if(!hitstop&&ability_cd)ability_cd--;draws=0;horizons_powers_draw();if(draws>max_draws)max_draws=draws;if(solid_calls>max_solid)max_solid=solid_calls;assert(draws<=25);assert(horizons_powers_moving_objects()<=2);}
static void updates(unsigned n){while(n--)tick();}
static void prepare_hit(unsigned c){unsigned i;int f=0,s=0;switch(c){
 case 106:f=16;break;case 107:f=16;break;case 108:f=10;break;case 109:f=28;break;
 case 110:f=24;break;case 111:f=12;s=-8;break;case 112:f=20;s=-6;break;case 113:f=16;s=-6;break;
 case 114:f=24;break;case 115:f=16;s=-8;break;case 116:f=-12;s=-12;break;case 117:f=18;break;
 case 118:f=16;s=-8;break;case 119:f=14;s=-10;break;case 120:f=23;break;case 121:f=24;s=8;break;}
 for(i=0;i<6;i++)enemy(i,f,s,0);
}
static void help(unsigned c,unsigned age){if((c==108||c==109)&&age==12)assert(horizons_powers_input(256)==2);
 if(c==120&&age==10){unsigned i;for(i=0;i<6;i++)enemies[i].x++;}}
static void all_commands(void){unsigned c,a,i;for(c=106;c<=121;c++){setup(c);prepare_hit(c);assert(horizons_power(c));assert(horizons_power_form==(int)c-1);assert(horizons_power_phase==creatures_ability(c)->phase);assert(ability_cd==(int)cooldown[c-106]);assert(!horizons_power(c));
 for(a=1;a<=lifetime[c-106];a++){tick();help(c,a);}assert(!horizons_power_time&&!owner);assert(horizons_power_age==(int)lifetime[c-106]);
 for(i=0;i<6;i++){if(enemy_hp_q4[i]!=1600-(int)damage[c-106])printf("command %u slot%u damage %d expected%u\n",c,i,1600-enemy_hp_q4[i],damage[c-106]);assert(enemy_hp_q4[i]==1600-(int)damage[c-106]);}
 }puts("16 distinct commands: real catalog, six enemy slots, finite duration and once-per-cast damage");}
static void guards(void){unsigned q;for(q=0;q<2;q++){unsigned c=q?115:109;int side=q?-8:0;setup(c);assert(horizons_power(c));updates(8);
 shot(0,20,side,-4,0,1);assert(!horizons_powers_intercept_shot(0,120,100+side,116,100+side,0));assert(shots[0].life);
 shots[0].owner=0;assert(!horizons_powers_intercept_shot(0,120,100+side,116,100+side,1));shots[0].owner=1;
 assert(!horizons_powers_intercept_shot(0,120,100+side,115,100+side,1));
 shot(1,16,side,4,0,1);assert(!horizons_powers_intercept_shot(1,116,100+side,120,100+side,1));
 assert(horizons_powers_intercept_shot(0,120,100+side,116,100+side,1));assert(!shots[0].life);
 shot(0,20,side,-4,0,1);tick();assert(!horizons_powers_intercept_shot(0,120,100+side,116,100+side,1));assert(shots[0].life);
 }
 setup(115);assert(horizons_power(115));updates(8);shot(0,22,0,-4,0,1);assert(!horizons_powers_intercept_shot(0,122,100,118,100,1));
 setup(109);enemy(0,28,0,0);assert(horizons_power(109));updates(8);shot(0,22,0,-4,0,1);assert(horizons_powers_intercept_shot(0,122,100,118,100,1));assert(horizons_powers_input(256)==2);updates(42);assert(enemy_hp_q4[0]==1552);
 puts("one ordinary-shot guard: provenance, direction, exact segment, reuse and shelter aperture");}
static void controls(void){unsigned c;for(c=106;c<=121;c++){int age,cd,time,d;unsigned t;setup(c);assert(horizons_power(c));updates(4);age=horizons_power_age;cd=ability_cd;time=horizons_power_time;t=horizons_powers_cast_token();d=horizons_power_direction;
 hitstop=1;updates(20);assert(horizons_power_age==age&&ability_cd==cd&&horizons_power_time==time);assert(!horizons_powers_input(16|256));hitstop=0;
 assert(!horizons_powers_input(16|32));assert(horizons_power_direction==d);horizons_powers_selection_changed();caster.instance_id=8;caster.instance_id=7;assert(!horizons_powers_can_aim());assert(!horizons_powers_can_release());assert(horizons_powers_cast_token()==t&&revoked);
 updates(lifetime[c-106]+2);assert(!horizons_power_time);assert(ability_cd>0);horizons_powers_reset();assert(ability_cd>0);
 }
 setup(108);assert(horizons_power(108));updates(8);{int cd=ability_cd,age=horizons_power_age;unsigned id=horizons_powers_caster_id(),t=horizons_powers_cast_token();px+=20;assert(horizons_powers_input(256)==2);assert(ability_cd==cd&&horizons_power_age==age&&horizons_power_origin_x==100&&horizons_powers_caster_id()==id&&horizons_powers_cast_token()==t);assert(!horizons_powers_input(256));}
 setup(108);enemy(0,10,0,0);assert(horizons_power(108));updates(30);assert(!horizons_powers_can_release());assert(!horizons_powers_input(256));updates(12);assert(enemy_hp_q4[0]==1600);
 setup(107);assert(horizons_power(107));assert(horizons_powers_input(64)==1);assert(!horizons_powers_input(128));updates(9);assert(!horizons_powers_can_aim());
 puts("freeze/control: immutable cast, fresh release, one early edge, expiry and no cooldown refund");}
static void geometry_cases(void){unsigned c;for(c=106;c<=121;c++){setup(c);field_count=1;field_x=124;field_y=100;wall(111,0,2,320);assert(horizons_power(c));updates(lifetime[c-106]);assert(!field_accepts);}
 setup(118);assert(horizons_power(118));updates(6);assert(!horizons_powers_overlap(116,100,0));assert(horizons_powers_overlap(116,92,0));assert(!horizons_powers_overlap(118,94,0));assert(horizons_powers_overlap(116,80,12));assert(!horizons_powers_overlap(116,77,12));
 setup(119);assert(horizons_power(119));updates(18);assert(!horizons_powers_overlap(128,100,0));assert(horizons_powers_overlap(128,112,0));
 setup(116);assert(horizons_power(116));updates(16);assert(!horizons_powers_overlap(120,100,12));assert(horizons_powers_overlap(88,88,1));
 setup(114);field_count=1;field_x=124;field_y=100;assert(horizons_power(114));updates(4);wall(111,0,1,320);wall_count=0;updates(32);assert(revoked&&!field_accepts);
 setup(114);field_count=1;field_x=124;field_y=100;assert(horizons_power(114));token++;updates(36);assert(!field_accepts);
 setup(108);field_count=1;field_x=108;field_y=100;field_radius=0;assert(horizons_power(108));updates(12);assert(field_accepts==1&&field_beats==2);assert(horizons_powers_input(256)==2);updates(30);assert(field_accepts==2&&field_beats==6);
 setup(112);enemy(0,30,-6,0);wall(116,100,1,1);assert(horizons_power(112));updates(16);wall_count=0;updates(16);assert(enemy_hp_q4[0]==1600); /* first-wall stop survives later clear geometry */
 setup(121);enemy(0,24,0,0);wall(112,100,1,1);assert(horizons_power(121));updates(14);assert(!horizons_powers_overlap(124,100,0));updates(20);assert(enemy_hp_q4[0]==1600); /* radial fan cannot reach behind a narrow occluder */
 setup(108);enemy(0,10,0,0);wall(104,100,1,1);assert(horizons_power(108));updates(12);assert(horizons_powers_input(256)==2);updates(30);assert(enemy_hp_q4[0]==1600);
 puts("fields: exact pixels/octagon, gaps, one-pixel first-wall stops, radial LOS, permanent revocation, same-token two beats");}
static void identity_movement(void){setup(114);enemy(0,24,0,0);assert(horizons_power(114));updates(12);assert(enemy_hp_q4[0]==1552);enemy(0,24,0,0);updates(24);assert(enemy_hp_q4[0]==1600);
 setup(110);enemy(0,24,0,0);assert(horizons_power(110));updates(6);assert(enemy_hp_q4[0]==1568&&enemies[0].x==132);
 setup(110);enemy(0,24,0,3);assert(horizons_power(110));updates(6);assert(enemy_hp_q4[0]==1568&&enemies[0].x==124);
 setup(110);enemy(0,24,0,0);wall(130,104,1,1);assert(horizons_power(110));updates(6);assert(enemies[0].x==125);
 setup(110);enemy(0,24,0,0);enemy(1,33,0,0);assert(horizons_power(110));updates(6);assert(enemies[0].x==124);
 setup(110);enemy(0,24,0,0);assert(horizons_power(110));px=134;py=106;updates(6);assert(enemies[0].x==125);
 setup(117);enemy(0,18,0,0);assert(horizons_power(117));updates(8);assert(enemy_stagger_ticks[0]==18);
 setup(120);enemy(0,24,0,0);assert(horizons_power(120));updates(12);assert(enemy_hp_q4[0]==1600&&!slowed_enemies[0]);
 setup(120);enemy(0,23,0,0);assert(horizons_power(120));updates(9);enemies[0].x++;tick();assert(enemy_hp_q4[0]==1568&&slowed_enemies[0]==18);slowed_enemies[0]=3;updates(8);assert(slowed_enemies[0]==3);
 setup(120);enemy(0,23,0,3);assert(horizons_power(120));updates(9);enemies[0].x++;tick();assert(enemy_hp_q4[0]==1600&&!slowed_enemies[0]);
 puts("enemy serials and movement: recycle immunity, swept feet, boss immobility, grounded stagger and nonstacking crossing slow");}
static void spacing(void){setup(106);enemy(0,70,0,0);assert(horizons_power(106));updates(18);enemies[0].x=140;updates(20);assert(enemy_hp_q4[0]==1568);
 setup(111);enemy(0,38,-8,0);assert(horizons_power(111));updates(42);assert(enemy_hp_q4[0]==1552);
 setup(113);enemy(0,52,8,0);assert(horizons_power(113));updates(44);assert(enemy_hp_q4[0]==1552);
 setup(118);enemy(0,30,8,0);assert(horizons_power(118));updates(38);assert(enemy_hp_q4[0]==1568);
 setup(119);enemy(0,28,12,0);assert(horizons_power(119));updates(38);assert(enemy_hp_q4[0]==1568);
 setup(107);field_count=1;field_x=130;field_y=80;field_radius=0;wall(113,100,1,1);assert(horizons_power(107));updates(48);assert(!field_accepts);
 puts("range decisions: stronger return/far beat and independently clipped corner legs");}
static void phase_damage(void){unsigned c,p,a;for(c=106;c<=121;c++)for(p=0;p<6;p++){setup(c);prepare_hit(c);enemy_phases[0]=(unsigned char)(p==5?255:p);assert(horizons_power(c));for(a=1;a<=lifetime[c-106];a++){tick();help(c,a);}assert(enemy_hp_q4[0]==1600-(int)combat_damage_q4(damage[c-106],0,0,creatures_ability(c)->phase,p==5?255:p,0));}puts("all16 commands across five phases plus neutral use real Q4 damage");}
static void invalid(void){unsigned c;setup(106);for(c=0;c<512;c++)if(c!=106)assert(!horizons_power(c));assert(!horizons_power(~0u));face=4;assert(!horizons_power(106));face=3;absent=1;assert(!horizons_power(106));absent=0;owner=NORTHERN_TILES_RETURN;assert(!horizons_power(106));owner=0;caster.equipped[0]=107;assert(!horizons_power(106));caster.equipped[0]=106;caster.instance_id=0;assert(!horizons_power(106));puts("invalid/full-width command, identity, face, ownership and lease refusals");}
static void art_pixels(void){unsigned c,d,a,k,checked=0;int x,y;for(c=0;c<16;c++)for(k=0;k<2;k++)for(y=0;y<8;y++)for(x=0;x<8;x++)assert(!!horizons_power_particles[c][k][y*8+x]==(abs(x-3)+abs(y-3)<=2));
 for(c=106;c<=121;c++)for(d=0;d<4;d++){setup(c);face=(int)d;assert(horizons_power(c));for(a=1;a<=lifetime[c-106];a++){tick();if((c==108||c==109)&&a==12){assert(horizons_powers_input(256)==2);continue;}if(a<startup[c-106]||a>=startup[c-106]+active_time[c-106]||a%5)continue;
  for(y=36;y<=164;y++)for(x=36;x<=164;x++){unsigned j;int pixel=0;for(j=0;j<draws;j++){int u=x-draw_x[j],v=y-draw_y[j];if(draw_off[j]!=GFX_OBJ_WATER_DROP||draw_w[j]!=8||u<0||v<0||u>=8||v>=8)continue;if(vram[draw_off[j]+v*8+u])pixel=1;}
   assert(horizons_powers_overlap(x,y,0)==pixel);checked++;}
 }}printf("all4 facings: %u actual native tile pixel/point overlap comparisons\n",checked);}
static void preview(const char*path){unsigned c,a,k,j;FILE*f=fopen(path,"wb");assert(f);
 for(c=106;c<=121;c++){unsigned ages[4]={startup[c-106]+1,startup[c-106]+7,startup[c-106]+14,startup[c-106]+active_time[c-106]-2};
  setup(c);assert(horizons_power(c));for(a=1;a<=lifetime[c-106];a++){tick();for(k=0;k<4;k++)if(a==ages[k]){unsigned char pix[104*80];int x,y;memset(pix,0,sizeof pix);
   for(j=0;j<draws;j++)for(y=0;y<draw_w[j];y++)for(x=0;x<draw_w[j];x++){int xx=draw_x[j]+x-68,yy=draw_y[j]+y-60;unsigned char v=vram[draw_off[j]+y*draw_w[j]+x];if(v&&xx>=0&&xx<104&&yy>=0&&yy<80)pix[yy*104+xx]=v;}
   assert(fwrite(pix,1,sizeof pix,f)==sizeof pix);
  }if((c==108||c==109)&&a==12)assert(horizons_powers_input(256)==2);}
 }assert(!fclose(f));}
int main(void){invalid();all_commands();guards();controls();geometry_cases();identity_movement();spacing();phase_damage();art_pixels();printf("Horizons host passed; maximum draws=%u, tick solid probes=%u\n",max_draws,max_solid);if(getenv("HORIZONS_POWER_PREVIEW"))preview(getenv("HORIZONS_POWER_PREVIEW"));return 0;}
