/* Synthetic fixtures + real old power handlers/catalog/art. Not controller
 * acquisition, native frame-budget acceptance or a complete world playthrough. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "return_legacy_powers.h"
#include "return_game.h"
#include "advanced_powers.h"
#include "regional_powers.h"
#include "northern_powers.h"
#include "southern_powers.h"
#include "progression.h"
#include "assets.h"
#include "obj_layout.h"
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
Enemy enemies[6];Shot shots[12];Save5State adventure_save;
volatile int room,px,py,game_state,summoned,spirit,stone_guard,guard_invuln;
int face,hitstop,cx,cy,ability_cd,ability_max,frame,power_effect,enemy_clocks[6],enemy_windups[6];
static unsigned token,field_count,field_hits,field_calls,uploads,draws,damage,collision_calls;
static int target_x,target_y,target_r=12,wall_count;
static struct {int x,y,w,h;} walls[64];
static unsigned char vram[16384];
static struct {int x,y,size,off;} draw[32];
static const unsigned commands[]={1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,23,24,25,26};
static const unsigned forms[]={2,5,8,11,2,5,8,11,14,14,16,20,20,23,23,26,26,29,29};
unsigned game_power_cooldown(unsigned v){return v;}
void game_enemy_hurt(unsigned i,unsigned base,unsigned attack,unsigned phase){assert(i<6);(void)attack;(void)phase;damage+=base;enemies[i].hp-=(int)base;}
void impact(int x,int y){(void)x;(void)y;}
void sfx(int n){(void)n;}
void kill_enemy(Enemy*e){e->hp=0;}
int near(int x,int y,int tx,int ty,int r){return abs(x-tx)+abs(y-ty)<r;}
CreatureInstance*progression_selected(void){CreatureRoster*r=&adventure_save.roster;return r->selected_party<4&&r->party[r->selected_party]<160?&r->instances[r->party[r->selected_party]]:0;}
int solid(int x,int y){int i;collision_calls++;if(x<0||y<0||x>=480||y>=320)return 1;
 for(i=0;i<wall_count;i++)if(x>=walls[i].x&&y>=walls[i].y&&x<walls[i].x+walls[i].w&&y<walls[i].y+walls[i].h)return 1;return 0;}
int return_game_is_room(unsigned r){return r>=54&&r<=61;}
int return_game_clear_box(int x0,int y0,int x1,int y1){int i;
 if(x0<0||y0<0||x1>=480||y1>=320||x0>x1||y0>y1)return 0;
 for(i=0;i<wall_count;i++)if(x0<walls[i].x+walls[i].w&&x1>=walls[i].x&&y0<walls[i].y+walls[i].h&&y1>=walls[i].y)return 0;
 return 1;}
int return_game_supercover(int x,int y,int tx,int ty){int dx=abs(tx-x),dy=-abs(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,e=dx+dy;
 if(solid(x,y)||solid(tx,ty))return 0;while(x!=tx||y!=ty){int twice=e*2,nx=x,ny=y;
  if(twice>=dy){e+=dy;nx+=sx;}if(twice<=dx){e+=dx;ny+=sy;}
  if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return 0;x=nx;y=ny;if(solid(x,y))return 0;}return 1;}
unsigned return_game_action_begin(unsigned channel){assert(channel==3);return ++token;}
int return_game_field_target(unsigned i,int*x,int*y,int*r){if(i>=field_count)return 0;*x=target_x+(int)i*80;*y=target_y;*r=target_r;return 1;}
int return_game_field_hit(unsigned i,unsigned command,unsigned id,unsigned form,unsigned t){CreatureInstance*c=progression_selected();field_calls++;
 if(t!=token||!c||c->instance_id!=id||c->form_id!=form||c->equipped[c->selected_command]!=command)return 0;
 assert(i<8);field_hits|=1u<<i;return 1;}
void obj_upload(const unsigned char*p,int w,int h,int off){assert(off>=0&&off+w*h<=16384);memcpy(vram+off,p,(size_t)(w*h));uploads++;}
void obj_add(int off,int x,int y,int w,int h,int priority,int depth,int flip){(void)priority;(void)depth;(void)flip;assert(w==h&&(w==8||w==16));assert(draws<32);draw[draws].x=x;draw[draws].y=y;draw[draws].size=w;draw[draws++].off=off;}
static void init_tiles(void){unsigned i;memset(vram,0,sizeof vram);for(i=0;i<64;i++){int x=(int)(i&7),y=(int)(i>>3);
 vram[10560+i]=(unsigned char)((x==3||y==3)&&x>0&&x<7&&y>0&&y<7);
 x-=3;y-=3;vram[10624+i]=(unsigned char)(abs(x)+abs(y)<5||(x==y&&x>-3&&x<3));}
 memcpy(vram+SPR_FLAME_0*256,sprite_data[SPR_FLAME_0],256);
}
static void setup(unsigned command){unsigned j,form=0;CreatureInstance*c;const CreatureForm*f;
 return_legacy_reset();regional_powers_reset();northern_powers_reset();southern_powers_reset();advanced_reset();
 memset(&adventure_save,0,sizeof adventure_save);memset(enemies,0,sizeof enemies);memset(shots,0,sizeof shots);memset(shot_effects,0,sizeof shot_effects);memset(shot_phases,255,sizeof shot_phases);
 memset(enemy_windups,0,sizeof enemy_windups);memset(enemy_clocks,0,sizeof enemy_clocks);
 for(j=0;j<sizeof commands/sizeof commands[0];j++)if(command==commands[j])form=forms[j];assert(form);
 adventure_save.roster.party[0]=0;adventure_save.roster.party[1]=1;adventure_save.roster.party[2]=adventure_save.roster.party[3]=255;
 c=&adventure_save.roster.instances[0];f=creatures_form(form);assert(f);c->form_id=(unsigned char)form;c->flags=CREATURE_OCCUPIED;c->instance_id=7;c->level=40;c->xp=creatures_xp_threshold(40);c->bond=80;c->polarity=f->polarity;c->equipped[0]=(unsigned char)command;
 assert(creatures_instance_validate(c));assert(creatures_command_learned(form,40,command));
 adventure_save.roster.instances[1]=*c;adventure_save.roster.instances[1].instance_id=8;
 room=54;px=py=cx=cy=100;face=1;game_state=summoned=1;hitstop=ability_cd=stone_guard=guard_invuln=frame=0;
 damage=field_count=field_calls=field_hits=uploads=draws=0;target_r=12;wall_count=0;init_tiles();
}
static int cast_power(unsigned c){int ok=1,slot=-1;assert(return_legacy_begin(c));
 if(c==1){slot=0;shots[0]=(Shot){px,py,face==2?-2:face==3?2:0,face==1?-2:face==0?2:0,90,0};northern_powers_shot_spawn(0);shot_effects[0]=SHOT_EFFECT_FIRE;shot_phases[0]=CREATURE_FIRE;}
 else if(c>=5&&c<=8)ok=advanced_power(c);else if(c>=9&&c<=11)ok=regional_power(c);else if(c>=13&&c<=16)ok=northern_power(c);else if(c>=23)ok=southern_power(c);
 return_legacy_confirm(ok,slot);return ok;
}
static void effects_tick(void){unsigned i;if(game_state!=1||hitstop)return;
 advanced_tick();regional_powers_tick();northern_powers_tick();southern_powers_tick();
 for(i=0;i<12;i++)if(shots[i].life){shots[i].life--;shots[i].x+=shots[i].dx;shots[i].y+=shots[i].dy;if(solid(shots[i].x,shots[i].y))shots[i].life=0;}
 if(ability_cd)ability_cd--;frame++;
}
static void effects_draw(unsigned c){draws=0;if(c==1&&shots[0].life)obj_add(SPR_FLAME_0*256,shots[0].x-8,shots[0].y-8,16,16,1,0,0);
 else if(c>=2&&c<=4)return_legacy_draw();else if(c<=8)advanced_draw();else if(c<=11)regional_powers_draw();else if(c<=16)northern_powers_draw();else southern_powers_draw();}
static int opaque(const ReturnLegacyPiece*p,int x,int y){int f,s;if(p->kind==RETURN_LEGACY_PIXELS)return !!p->pixels[y*p->size+x];
 if(p->kind==RETURN_LEGACY_SPARK)return !!vram[10560+y*8+x];if(p->kind==RETURN_LEGACY_ARMOR)return !!vram[10624+y*8+x];
 if(p->kind==RETURN_LEGACY_DROP)return y>=1&&y<=6&&abs(x-3)<=(y<4?y/2:2);
 f=p->kind==RETURN_LEGACY_PIN_DOWN?y-7:p->kind==RETURN_LEGACY_PIN_UP?7-y:p->kind==RETURN_LEGACY_PIN_LEFT?7-x:x-7;s=abs(p->kind<=RETURN_LEGACY_PIN_UP?x-7:y-7);
 return(f>=4&&f<=6&&s<=2)||(s==0&&f>=-5&&f<=6);}
static unsigned pieces,pixel_checks;
static void compare_piece(void*ctx,const ReturnLegacyPiece*p){unsigned i;int x,y,found=0;(void)ctx;pieces++;
 for(i=0;i<draws;i++)if(draw[i].x==p->x&&draw[i].y==p->y&&draw[i].size==p->size){found=1;
  for(y=0;y<p->size;y++)for(x=0;x<p->size;x++){assert(opaque(p,x,y)==!!vram[draw[i].off+y*p->size+x]);pixel_checks++;}break;}
 assert(found);
}
static void export(unsigned c,ReturnLegacyEmit emit){if(c>=5&&c<=8)advanced_powers_field_geometry(c,emit,0);else if(c>=9&&c<=11)regional_powers_field_geometry(c,emit,0);else if(c>=13&&c<=16)northern_powers_field_geometry(c,emit,0);else if(c>=23)southern_powers_field_geometry(c,emit,0);}
static void geometry_differential(void){unsigned j,d,a,variant;
 for(j=4;j<sizeof commands/sizeof commands[0];j++)for(d=0;d<4;d++)for(variant=0;variant<2;variant++){unsigned c=commands[j];setup(c);face=(int)d;assert(cast_power(c));
  for(a=0;a<96;a++){
   if(variant&&a==10){walls[0].x=100+(d==2?-20:d==3?20:-32);walls[0].y=100+(d==1?-20:d==0?20:-32);walls[0].w=d>=2?1:64;walls[0].h=d>=2?64:1;wall_count=1;}
   if(variant&&a==24)wall_count=0;
   effects_draw(c);export(c,compare_piece);effects_tick();
  }
 }printf("Read-only exports match %u actual opaque/transparent OBJ pixels across every facing/age and dynamic-wall mutation\n",pixel_checks);
}
static void base_pixel_differential(void){unsigned c,d,a,i,count=0;int x,y;
 for(c=1;c<=4;c++)for(d=0;d<4;d++){setup(c);face=(int)d;assert(cast_power(c));
  for(a=0;a<24;a++){effects_draw(c);
   if(a%7==0)for(y=52;y<=148;y++)for(x=52;x<=148;x++){int visible=0;
    for(i=0;i<draws;i++){int u=x-draw[i].x,v=y-draw[i].y;
     if(u>=0&&v>=0&&u<draw[i].size&&v<draw[i].size&&vram[draw[i].off+v*draw[i].size+u]){visible=1;break;}}
    assert(return_legacy_overlap(x,y,0)==visible);count++;
   }
   effects_tick();return_legacy_tick();
  }
 }printf("Base Fire1/Return-only2-4: %u exact visible-pixel versus point-overlap checks\n",count);
}
static void geometry_cases(void){unsigned j;setup(1);assert(cast_power(1));target_x=100;target_y=72;field_count=1;
 for(j=0;j<10;j++){effects_tick();return_legacy_tick();}assert(field_hits==1);assert(field_calls==1);
 setup(5);assert(cast_power(5));assert(!return_legacy_overlap(100,84,12));for(j=0;j<8;j++)effects_tick();assert(return_legacy_overlap(100,84,0));
 /* Opaque flame edge hits a target even when its center is outside the cell. */
 assert(return_legacy_overlap(100,69,12));assert(!return_legacy_overlap(100,54,12));
 walls[wall_count].x=95;walls[wall_count].y=75;walls[wall_count].w=11;walls[wall_count++].h=1;assert(!return_legacy_overlap(100,69,12));
 setup(6);assert(cast_power(6));assert(return_legacy_overlap(119,85,0));assert(!return_legacy_overlap(120,86,0));
 setup(9);assert(cast_power(9));assert(return_legacy_overlap(99,75,0));assert(!return_legacy_overlap(100,88,0));
 setup(24);assert(cast_power(24));assert(!return_legacy_overlap(100,70,12));for(j=0;j<6;j++)effects_tick();assert(return_legacy_overlap(100,95,12));
 setup(15);assert(cast_power(15));assert(!return_legacy_overlap(100,76,12));for(j=0;j<18;j++)effects_tick();assert(return_legacy_overlap(100,76,12));
 puts("Geometry: true target extent, transparent gaps, walls, no invisible-radius or future-guide proof");
}
static void identity_cases(void){unsigned c,j;for(j=0;j<sizeof commands/sizeof commands[0];j++){c=commands[j];setup(c);assert(cast_power(c));
 target_x=100;target_y=76;field_count=1;return_legacy_cancel();adventure_save.roster.selected_party=1;adventure_save.roster.selected_party=0;
 {int cd=ability_cd;for(c=0;c<100;c++){effects_tick();return_legacy_tick();}assert(!field_hits);assert(ability_cd<=cd);}}
 setup(1);assert(cast_power(1));target_x=100;target_y=84;field_count=1;shots[0].life=0;
 shots[0]=(Shot){100,84,0,-2,90,0};northern_powers_shot_spawn(0);return_legacy_tick();assert(!field_hits&&!return_legacy_cast_token());
 setup(1);assert(cast_power(1));shots[0].owner=1;assert(!return_legacy_overlap(100,100,12));
 setup(1);assert(cast_power(1));shot_effects[0]=SHOT_EFFECT_WIND;assert(!return_legacy_overlap(100,100,12));
 setup(1);assert(return_legacy_begin(1));shots[0]=(Shot){100,100,0,-2,90,0};northern_powers_shot_spawn(0);shot_effects[0]=SHOT_EFFECT_FIRE;shot_phases[0]=CREATURE_FIRE;return_legacy_confirm(0,0);assert(!return_legacy_cast_token());
 setup(2);assert(cast_power(2));target_x=100;target_y=84;field_count=1;game_state=3;for(j=0;j<100;j++){return_legacy_tick();return_legacy_draw();draws=0;}assert(!field_hits);game_state=1;hitstop=1;for(j=0;j<100;j++)return_legacy_tick();assert(!field_hits);hitstop=0;return_legacy_tick();assert(field_hits);
 setup(2);assert(cast_power(2));target_x=100;target_y=84;field_count=1;adventure_save.roster.party[1]=2;return_legacy_tick();adventure_save.roster.party[1]=1;return_legacy_tick();assert(!field_hits&&!return_legacy_cast_token());
 setup(2);assert(cast_power(2));target_x=100;target_y=84;field_count=1;token++;return_legacy_tick();assert(!field_hits&&!return_legacy_cast_token());
 setup(2);room=53;assert(!return_legacy_begin(2));return_legacy_confirm(1,-1);return_legacy_draw();assert(!draws);
 puts("Identity/provenance: failed cast, wrong slot/party/owner/effect, recycled shot, stale attempt, canceled selection, modal freeze");
}
static unsigned checksum(void){unsigned v=damage*7+uploads*11+(unsigned)ability_cd*13+(unsigned)stone_guard*17,i;
 for(i=0;i<6;i++)v=v*33u+(unsigned)enemies[i].hp+(unsigned)enemies[i].x+(unsigned)enemies[i].y+(unsigned)enemies[i].flash+(unsigned)rooted_enemies[i]+slowed_enemies[i];
 for(i=0;i<12;i++)v=v*33u+(unsigned)shots[i].life+(unsigned)shots[i].x+(unsigned)shots[i].y;
 return v+(unsigned)advanced_time_left+(unsigned)regional_power_time+(unsigned)northern_power_time+(unsigned)southern_power_time;}
static void noop_piece(void*ctx,const ReturnLegacyPiece*p){(void)ctx;(void)p;}
static void old_combat_unchanged(void){unsigned j,a,pass,trace[96];for(j=4;j<sizeof commands/sizeof commands[0];j++)for(pass=0;pass<2;pass++){
 unsigned c=commands[j];setup(c);enemies[0]=(Enemy){100,80,1000,0,0};enemies[1]=(Enemy){120,90,1000,0,0};assert(cast_power(c));
 for(a=0;a<96;a++){effects_tick();if(pass){export(c,noop_piece);(void)return_legacy_overlap(100,76,12);return_legacy_tick();}effects_draw(c);
  if(!pass)trace[a]=checksum();else assert(trace[a]==checksum());}
 }puts("Old combat/cooldown/animation-state traces identical with and without bridge/export observation");}
int main(void){geometry_differential();base_pixel_differential();geometry_cases();identity_cases();old_combat_unchanged();puts("Return legacy host tests passed");return 0;}
/* Python-only real authored-room collision probe entry points. Rectangles are
 * generated from geometry.json, expanded by the engine's five-pixel footprint. */
static int forbidden_count,forbidden[3][2];
void fixture_begin(unsigned command,int area,int x,int y,int tx,int ty){setup(command);room=area;px=cx=x;py=cy=y;face=1;target_x=tx;target_y=ty;field_count=1;forbidden_count=0;}
void fixture_forbid(int x,int y){assert(forbidden_count<3);forbidden[forbidden_count][0]=x;forbidden[forbidden_count++][1]=y;}
void fixture_wall(int x,int y,int w,int h){assert(wall_count<64);walls[wall_count].x=x;walls[wall_count].y=y;walls[wall_count].w=w;walls[wall_count++].h=h;}
int fixture_run(unsigned command){unsigned a;int first=0,i;if(solid(px,py)||solid(cx,cy)||solid(target_x,target_y))return -1;if(!cast_power(command))return -1;
 for(a=1;a<=96;a++){effects_tick();return_legacy_tick();
  for(i=0;i<forbidden_count;i++)if(return_legacy_overlap(forbidden[i][0],forbidden[i][1],12))return -2;
  if(field_hits&&!first)first=(int)a;
 }return first;}
