/* Return I old-command field proof. All geometry is read-only historical state,
 * except explicitly visible finite base2..4 overlays in Return rooms. No heap,
 * IWRAM routines, resident OBJ allocation, combat damage or cooldown writes. */
#include "return_legacy_powers.h"
#include "return_legacy_geometry.h"
#include "return_game.h"
#include "field_world.h"
#include "advanced_powers.h"
#include "regional_powers.h"
#include "northern_powers.h"
#include "southern_powers.h"
#include "progression.h"
#include "assets.h"
typedef struct {int x,y,dx,dy,life,owner;} Shot;
extern Shot shots[12];
extern volatile int room,px,py,game_state,summoned;
extern int face,hitstop;
extern int solid(int,int);
extern void obj_add(int,int,int,int,int,int,int,int);
typedef struct {
 unsigned id,party,token;
 short x,y;
 unsigned short shot_serial;
 unsigned char area,slot,selected,form,command,command_slot,direction;
 unsigned char pending,rights,shot,overlay,hits;
} LegacyCast;
static LegacyCast cast;
static int absolute(int x){return x<0?-x:x;}
int return_legacy_box_certificate(int x,int y,int tx,int ty){
 int x0=x<tx?x:tx,y0=y<ty?y:ty,x1=x>tx?x:tx,y1=y>ty?y:ty;
 if(!field_world_is_room((unsigned)room))return 0;
 return field_world_clear_box(x0,y0,x1,y1);
}

static unsigned party(void){const CreatureRoster*r=&adventure_save.roster;
 return r->party[0]|(unsigned)r->party[1]<<8|(unsigned)r->party[2]<<16|(unsigned)r->party[3]<<24;}
static int supported(unsigned c){return (c>=1&&c<=11)||(c>=13&&c<=16)||(c>=23&&c<=26);}
static int same_participant(void){CreatureInstance*c=progression_selected();const CreatureRoster*r=&adventure_save.roster;
 return summoned&&room==cast.area&&r->selected_party==cast.selected&&cast.selected<4&&
  r->party[cast.selected]==cast.slot&&party()==cast.party&&cast.slot<CREATURE_ROSTER_CAPACITY&&
  c==&r->instances[cast.slot]&&(c->flags&CREATURE_OCCUPIED)&&c->instance_id==cast.id&&
  c->form_id==cast.form&&c->selected_command==cast.command_slot&&cast.command_slot<2&&
  c->equipped[cast.command_slot]==cast.command&&creatures_command_learned(c->form_id,c->level,cast.command);
}
void return_legacy_cancel(void){cast.token=0;cast.rights=cast.pending=0;}
void return_legacy_reset(void){return_legacy_cancel();cast.command=cast.overlay=cast.hits=0;cast.shot=255;}
unsigned return_legacy_begin(unsigned command){CreatureInstance*c;CreatureRoster*r=&adventure_save.roster;unsigned slot;
 return_legacy_reset();
 if(!field_world_is_room((unsigned)room)||game_state!=1||hitstop||!summoned||!supported(command)||face<0||face>3||r->selected_party>=4)return 0;
 slot=r->party[r->selected_party];if(slot>=CREATURE_ROSTER_CAPACITY)return 0;
 c=progression_selected();if(c!=&r->instances[slot]||!creatures_instance_validate(c)||c->selected_command>1||
  c->equipped[c->selected_command]!=command||!creatures_command_learned(c->form_id,c->level,command))return 0;
 cast.id=c->instance_id;cast.party=party();cast.x=(short)px;cast.y=(short)py;
 cast.area=(unsigned char)room;cast.slot=(unsigned char)slot;cast.selected=r->selected_party;
 cast.form=c->form_id;cast.command=(unsigned char)command;cast.command_slot=c->selected_command;cast.direction=(unsigned char)face;
 cast.token=field_world_action_begin(3);cast.pending=cast.token!=0;return cast.token;
}
void return_legacy_confirm(int success,int shot_index){
 if(!cast.pending)return;
 cast.pending=0;
 if(!success||!cast.token||!same_participant()){return_legacy_cancel();return;}
 if(cast.command==1){Shot*s;
  if(shot_index<0||shot_index>=12){return_legacy_cancel();return;}s=&shots[shot_index];
  /* Exact fresh ordinary engine missile, not a reflected, hostile or special
   * pool occupant. The index came from THIS cast's successful fire_shot call. */
  if(s->life!=90||s->owner||s->x!=cast.x||s->y!=cast.y||
    s->dx!=(cast.direction==2?-2:cast.direction==3?2:0)||
    s->dy!=(cast.direction==1?-2:cast.direction==0?2:0)||
    shot_effects[shot_index]!=SHOT_EFFECT_FIRE||shot_phases[shot_index]!=CREATURE_FIRE){return_legacy_cancel();return;}
  cast.shot=(unsigned char)shot_index;cast.shot_serial=(unsigned short)northern_powers_shot_serial((unsigned)shot_index);
 }else if(cast.command<=4)cast.overlay=24;
 else if(cast.command<=8){if(advanced_kind!=cast.command||advanced_time_left<=0){return_legacy_cancel();return;}}
 else if(cast.command<=11){if(regional_power_kind!=cast.command||regional_power_time<=0){return_legacy_cancel();return;}}
 else if(cast.command<=16){if(northern_power_kind!=cast.command||northern_power_time<=0){return_legacy_cancel();return;}}
 else if(southern_power_kind!=cast.command||southern_power_time<=0){return_legacy_cancel();return;}
 cast.rights=1;
}
static int fire_live(void){unsigned i=cast.shot;
 return i<12&&northern_powers_shot_serial(i)==cast.shot_serial&&shots[i].life>0&&
  !shots[i].owner&&shot_effects[i]==SHOT_EFFECT_FIRE&&shot_phases[i]==CREATURE_FIRE;
}
static int effect_live(void){
 if(cast.command==1)return fire_live();
 if(cast.command<=4)return cast.overlay>0;
 if(cast.command<=8)return advanced_kind==cast.command&&advanced_time_left>0&&advanced_origin_x==cast.x&&advanced_origin_y==cast.y&&advanced_direction==cast.direction;
 if(cast.command<=11)return regional_power_kind==cast.command&&regional_power_time>0&&regional_power_form==cast.form;
 if(cast.command<=16)return northern_power_kind==cast.command&&northern_power_time>0&&northern_power_form==cast.form&&northern_power_origin_x==cast.x&&northern_power_origin_y==cast.y&&northern_power_direction==cast.direction;
 return southern_power_kind==cast.command&&southern_power_time>0&&southern_power_form==cast.form&&southern_power_origin_x==cast.x&&southern_power_origin_y==cast.y&&southern_power_direction==cast.direction;
}
/* The engine uploads these exact masks once for old spark/armor art. The
 * water and pin masks below exactly match regional_power's procedural upload. */
static int opaque(const ReturnLegacyPiece*p,int x,int y){int f,s,dx,dy;
 if((unsigned)x>=p->size||(unsigned)y>=p->size)return 0;
 if(p->kind==RETURN_LEGACY_PIXELS)return p->pixels&&p->pixels[y*p->size+x];
 if(p->kind==RETURN_LEGACY_SPARK)return (x==3||y==3)&&x>0&&x<7&&y>0&&y<7;
 if(p->kind==RETURN_LEGACY_ARMOR){dx=x-3;dy=y-3;return absolute(dx)+absolute(dy)<5||(dx==dy&&dx>-3&&dx<3);}
 if(p->kind==RETURN_LEGACY_DROP){s=absolute(x-3);return y>=1&&y<=6&&s<=(y<4?y/2:2);}
 f=p->kind==RETURN_LEGACY_PIN_DOWN?y-7:p->kind==RETURN_LEGACY_PIN_UP?7-y:p->kind==RETURN_LEGACY_PIN_LEFT?7-x:x-7;
 s=absolute(p->kind<=RETURN_LEGACY_PIN_UP?x-7:y-7);
 return (f>=4&&f<=6&&s<=2)||(s==0&&f>=-5&&f<=6);
}
static void overlay_geometry(ReturnLegacyEmit emit,void *context){int i,dx=cast.direction==2?-1:cast.direction==3?1:0,dy=cast.direction==1?-1:cast.direction==0?1:0;
 if(!cast.overlay)return;
 if(cast.command==2||cast.command==4){for(i=-1;i<=1;i++){int x=cast.x+dx*16-dy*i*8,y=cast.y+dy*16+dx*i*8;
  if(return_legacy_box_certificate(cast.x,cast.y,x,y)||field_world_supercover(cast.x,cast.y,x,y)>0)return_legacy_piece(emit,context,0,x-4,y-4,8,cast.command==2?RETURN_LEGACY_SPARK:RETURN_LEGACY_ARMOR);}}
 else if(cast.command==3){for(i=1;i<=4;i++){int x=cast.x+dx*i*10,y=cast.y+dy*i*10;
  if(return_legacy_box_certificate(cast.x,cast.y,x,y)||field_world_supercover(cast.x,cast.y,x,y)>0)return_legacy_piece(emit,context,0,x-4,y-4,8,RETURN_LEGACY_SPARK);}}
}
static void geometry(ReturnLegacyEmit emit,void *context){
 if(!field_world_is_room((unsigned)room)||room!=cast.area)return;
 if(cast.command==1){if(fire_live()){Shot*s=&shots[cast.shot];return_legacy_piece(emit,context,sprite_data[SPR_FLAME_0],s->x-8,s->y-8,16,RETURN_LEGACY_PIXELS);}}
 else if(cast.command<=4)overlay_geometry(emit,context);
 else if(cast.command<=8)advanced_powers_field_geometry(cast.command,emit,context);
 else if(cast.command<=11)regional_powers_field_geometry(cast.command,emit,context);
 else if(cast.command<=16)northern_powers_field_geometry(cast.command,emit,context);
 else southern_powers_field_geometry(cast.command,emit,context);
}
typedef struct {short x,y;unsigned char radius,index,clear;} FieldTarget;
typedef struct {FieldTarget targets[8];unsigned char count,overlap;} FieldQuery;
static int piece_overlap(const ReturnLegacyPiece*p,FieldTarget*t){
 int tx=t->x,ty=t->y,r=t->radius;
 int x,y,x0=tx-r-p->x,y0=ty-r-p->y,x1=tx+r-p->x,y1=ty+r-p->y;
 if(x0>=p->size||y0>=p->size||x1<0||y1<0)return 0;
 if(x0<0)x0=0;
 if(y0<0)y0=0;
 if(x1>=p->size)x1=p->size-1;
 if(y1>=p->size)y1=p->size-1;
 for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++){int wx=p->x+x,wy=p->y+y;
  /* For r12 this is exactly abs(dx)<=12,abs(dy)<=12,abs(dx)+abs(dy)<=15. */
  if(absolute(wx-tx)+absolute(wy-ty)>r+r/4||!opaque(p,x,y))continue;
  /* A whole rectangle enclosing origin, target and every candidate pixel is
   * a same-call LOS certificate, never a collision/shape approximation. Most
   * authored workspaces satisfy it, so no ray is repeated per opaque pixel.
   * If scenery intersects it, require the direct origin/target supercover,
   * then test the actual overlapping pixel's two rays below. */
  if(!t->clear){int bx0=tx-r,by0=ty-r,bx1=tx+r,by1=ty+r;
   if(cast.x<bx0)bx0=cast.x;
   if(cast.y<by0)by0=cast.y;
   if(cast.x>bx1)bx1=cast.x;
   if(cast.y>by1)by1=cast.y;
   t->clear=(unsigned char)(field_world_clear_box(bx0,by0,bx1,by1)?1:
     field_world_supercover(cast.x,cast.y,tx,ty)>0?2:3);
  }
  if(t->clear==1)return 1;
  if(t->clear==3)return 0;
  if(field_world_supercover(cast.x,cast.y,wx,wy)>0&&field_world_supercover(wx,wy,tx,ty)>0)return 1;
 }return 0;
}
static void query_piece(void*context,const ReturnLegacyPiece*p){FieldQuery*q=context;unsigned i;
 for(i=0;i<q->count;i++)if(!(q->overlap&(1u<<i))&&piece_overlap(p,&q->targets[i]))q->overlap|=(unsigned char)(1u<<i);
}
int return_legacy_overlap(int x,int y,int radius){FieldQuery q;
 if(!cast.rights||!cast.token||!same_participant()||!effect_live()||radius<0||radius>16||(unsigned)x>1023u||(unsigned)y>1023u)return 0;
 q.count=1;q.overlap=0;q.targets[0].x=(short)x;q.targets[0].y=(short)y;q.targets[0].radius=(unsigned char)radius;q.targets[0].clear=0;
 geometry(query_piece,&q);return q.overlap!=0;
}
/* Keep temporary target-output integers out of the query owner's stack frame.
 * The eight-target query remains stack-owned and synchronous; no shared cache
 * or new mutable state is introduced by the second world backend. */
static __attribute__((noinline)) void field_targets(FieldQuery*q){unsigned i;
 q->count=q->overlap=0;
 for(i=0;i<8;i++){int x,y,r;if((cast.hits&(1u<<i))||!field_world_target(i,&x,&y,&r)||r<0||r>16||(unsigned)x>1023u||(unsigned)y>1023u)continue;
  q->targets[q->count].x=(short)x;q->targets[q->count].y=(short)y;q->targets[q->count].radius=(unsigned char)r;q->targets[q->count].clear=0;q->targets[q->count++].index=(unsigned char)i;}
}
void return_legacy_tick(void){FieldQuery q;unsigned i;
 if(game_state!=1||hitstop)return;
 if(cast.overlay)cast.overlay--;
 if(!cast.rights||!cast.token)return;
 if(!same_participant()||!effect_live()){return_legacy_cancel();return;}
 field_targets(&q);
 if(!q.count)return;
 geometry(query_piece,&q);
 for(i=0;i<q.count;i++)if(q.overlap&(1u<<i)){int result=field_world_hit(q.targets[i].index,cast.command,cast.id,cast.form,cast.token);
  if(result)cast.hits|=(unsigned char)(1u<<q.targets[i].index);else {return_legacy_cancel();break;}}
}
static void draw_piece(void*context,const ReturnLegacyPiece*p){(void)context;
 obj_add(p->kind==RETURN_LEGACY_ARMOR?10624:10560,p->x,p->y,8,8,1,p->y+6,0);
}
void return_legacy_draw(void){if(field_world_is_room((unsigned)room)&&room==cast.area&&cast.command>=2&&cast.command<=4)overlay_geometry(draw_piece,0);}
unsigned return_legacy_cast_token(void){return cast.rights?cast.token:0;}
unsigned return_legacy_caster_id(void){return cast.id;}
