/* Original Magma commands; ROM code, bounded transient state, shared OBJ lease.
 * Every collision path uses endpoint-inclusive integer raster + corner cells.
 * Static scenery checks are cached, while enemy occupancy/identity remains live. */
#include "magma_powers.h"
#include "magma_power_art.h"
#include "magma_game.h"
#include "northern_powers.h"
#include "regional_powers.h"
#include "advanced_powers.h"
#include "gear_runtime.h"
#include "progression.h"
#include "combat_rules.h"
#include "obj_layout.h"
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
extern Enemy enemies[6];extern Shot shots[12];
extern volatile int px,py;
extern int face,ability_cd,ability_max,hitstop,enemy_windups[6],enemy_clocks[6];
extern int solid(int,int);
/* Optional engine proof: absent in older focused linkers, which retain the
 * original exact pixel path. No dependency on a future chapter is introduced. */
extern int game_clear_box(int,int,int,int) __attribute__((weak));
extern void kill_enemy(Enemy *),impact(int,int),sfx(int);
extern void obj_upload(const unsigned char *,int,int,int);
extern void obj_add(int,int,int,int,int,int,int,int);
int magma_power_kind,magma_power_time,magma_power_form;
int magma_power_direction,magma_power_origin_x,magma_power_origin_y;
int magma_power_age,magma_power_cooldown,magma_power_cast_time,magma_power_phase;
typedef struct {unsigned char startup,active,recovery,cooldown,damage,phase,objects;} Spec;
static const Spec specs[24]={
 {8,36,12,90,16,CREATURE_FIRE,1},{12,16,16,120,24,CREATURE_FIRE,2},
 {18,30,20,150,32,CREATURE_FIRE,3},{6,8,16,90,20,CREATURE_EARTH,1},
 {12,24,18,120,24,CREATURE_EARTH,1},{20,10,22,150,32,CREATURE_EARTH,1},
 {8,18,12,90,16,CREATURE_WOOD,1},{14,36,14,120,20,CREATURE_WOOD,2},
 {16,6,18,120,24,CREATURE_WOOD,1},{8,12,14,90,16,CREATURE_WATER,1},
 {12,30,18,120,24,CREATURE_WATER,3},{10,20,20,120,24,CREATURE_WATER,1},
 {6,12,16,90,20,CREATURE_METAL,2},{14,8,22,120,28,CREATURE_METAL,1},
 {16,20,16,120,24,CREATURE_METAL,2},{8,10,12,90,16,CREATURE_FIRE,1},
 {12,18,18,120,24,CREATURE_FIRE,2},{14,40,18,120,16,CREATURE_FIRE,1},
 {10,12,12,90,20,CREATURE_EARTH,3},{16,20,20,120,24,CREATURE_EARTH,2},
 {10,24,12,90,16,CREATURE_WOOD,1},{14,30,16,120,24,CREATURE_WOOD,2},
 {10,14,12,90,16,CREATURE_WATER,3},{18,24,18,120,24,CREATURE_WATER,1}
};
/* Raw/visible endpoints, exact cached segment and its origin/parent connection.
 * Twelve entries suffice for five separated two-edge lobes (ten entries). */
typedef struct {short x,y,tx,ty,ex,ey;unsigned char valid,open,whole,radius,parent,group,from,to;} Path;
static Path paths[12];
static unsigned short enemy_serial[6],guard_serial;
static short previous_x[6],previous_y[6],aim_x,aim_y;
static unsigned caster_id,lease_generation,chapter_token;
static unsigned char chapter_hit;
static unsigned char path_count,hit_mask,spent,aimed,ended_mask,guard_enemy,guard_grace,draw_count;
static signed char cast_side;
static unsigned char own_slow,own_root,own_stagger;
static const signed char fx[4]={0,0,-1,1},fy[4]={1,-1,0,0};
static int absolute(int x){return x<0?-x:x;}
static int dist(int x,int y,int tx,int ty){return absolute(x-tx)+absolute(y-ty);}
static int coordinate(int x,int y){return x>=0&&y>=0&&x<=1023&&y<=1023;}
static int clear(int x,int y,int tx,int ty){
 int dx,dy,sx,sy,err;
 if(!coordinate(x,y)||!coordinate(tx,ty)||dist(x,y,tx,ty)>192||solid(x,y)||solid(tx,ty))return 0;
 dx=absolute(tx-x);dy=-absolute(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;err=dx+dy;
 while(x!=tx||y!=ty){int e=err*2,nx=x,ny=y;
  if(e>=dy){err+=dy;nx+=sx;}if(e<=dx){err+=dx;ny+=sy;}
  if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return 0;
  x=nx;y=ny;if(solid(x,y))return 0;
 }return 1;
}
static int ordinary(unsigned i){return i<6&&enemies[i].hp>0&&(unsigned)enemies[i].kind<=2&&coordinate(enemies[i].x,enemies[i].y);}
static int active(void){return magma_power_time>0&&northern_powers_tiles_owner()==NORTHERN_TILES_MAGMA&&
 lease_generation==northern_powers_tiles_generation();}
static const Spec *spec(void){return magma_power_kind>=43&&magma_power_kind<=66?&specs[magma_power_kind-43]:0;}
static int live_window(void){const Spec*s=spec();return active()&&s&&magma_power_age>=s->startup&&magma_power_age<s->startup+s->active;}
static void point(int f,int s,int*x,int*y){int dx=fx[magma_power_direction],dy=fy[magma_power_direction];
 *x=magma_power_origin_x+f*dx-s*dy;*y=magma_power_origin_y+f*dy+s*dx;}
static void relative(int x,int y,int*f,int*s){int dx=fx[magma_power_direction],dy=fy[magma_power_direction];
 x-=magma_power_origin_x;y-=magma_power_origin_y;*f=x*dx+y*dy;*s=-x*dy+y*dx;}
void magma_powers_geometry_changed(void){unsigned i;for(i=0;i<12;i++)paths[i].valid=0;}
static void finish(void){magma_power_time=0;ended_mask=7;guard_grace=0;northern_powers_tiles_release(NORTHERN_TILES_MAGMA);}
int magma_powers_busy(void){return magma_power_time>0;}
int magma_powers_cast_matches_selected(void){CreatureInstance*c=progression_selected();return c&&(c->flags&CREATURE_OCCUPIED)&&
 caster_id&&c->instance_id==caster_id&&c->form_id==magma_power_form;}
static int same_caster(void){CreatureInstance*c=progression_selected();return magma_powers_cast_matches_selected()&&
 creatures_instance_validate(c)&&c->selected_command<2&&c->equipped[c->selected_command]==magma_power_kind;}
void magma_powers_enemy_spawn(unsigned i){if(i>=6)return;enemy_serial[i]++;
 /* Slot invalidation also prevents a wrapped serial from reviving old rights. */
 if(magma_power_time)hit_mask|=(unsigned char)(1u<<i);
 own_slow&=(unsigned char)~(1u<<i);own_root&=(unsigned char)~(1u<<i);own_stagger&=(unsigned char)~(1u<<i);
 if(guard_enemy==i){guard_enemy=6;guard_grace=0;}
 previous_x[i]=(short)enemies[i].x;previous_y[i]=(short)enemies[i].y;}
void magma_powers_reset(void){unsigned i;
 for(i=0;i<6;i++){
  if((own_slow&(1u<<i))&&slowed_enemies[i]<=18)slowed_enemies[i]=0;
  if((own_root&(1u<<i))&&rooted_enemies[i]<=12)rooted_enemies[i]=0;
  if((own_stagger&(1u<<i))&&enemy_stagger_ticks[i]<=16)enemy_stagger_ticks[i]=0;
 }own_slow=own_root=own_stagger=0;finish();magma_power_kind=magma_power_form=magma_power_direction=0;
 magma_power_origin_x=magma_power_origin_y=magma_power_age=magma_power_cooldown=magma_power_cast_time=magma_power_phase=0;
 caster_id=chapter_token=0;chapter_hit=0;path_count=hit_mask=spent=aimed=ended_mask=0;guard_enemy=6;aim_x=aim_y=0;cast_side=-1;
 for(i=0;i<6;i++){previous_x[i]=(short)enemies[i].x;previous_y[i]=(short)enemies[i].y;}
 magma_powers_geometry_changed();}
/* path_set does not invalidate unchanged geometry when only active masks change. */
static void path_set(unsigned n,int x,int y,int tx,int ty,unsigned radius,unsigned group,unsigned parent){Path*p;
 if(n>=12)return;
 p=&paths[n];
 if(p->x!=x||p->y!=y||p->tx!=tx||p->ty!=ty||p->parent!=parent){unsigned j;
  for(j=n;j<12;j++)paths[j].valid=0;
 }
 p->x=(short)x;p->y=(short)y;p->tx=(short)tx;p->ty=(short)ty;p->radius=(unsigned char)radius;
 p->from=0;p->to=96;p->group=(unsigned char)group;p->parent=(unsigned char)parent;if(path_count<=n)path_count=(unsigned char)(n+1);
}
static void line(unsigned n,int f,int s,int tf,int ts,unsigned radius,unsigned group,unsigned parent){int x,y,tx,ty;
 point(f,s,&x,&y);point(tf,ts,&tx,&ty);path_set(n,x,y,tx,ty,radius,group,parent);}
static void refresh_one(unsigned n){Path*p=&paths[n];int x,y,dx,dy,sx,sy,err;
 if(p->valid)return;
 p->valid=1;p->open=p->whole=0;
 if(p->parent){Path*q=&paths[p->parent-1];if(p->parent>n||!q->valid||!q->whole||q->tx!=p->x||q->ty!=p->y)return;}
 else if(!clear(magma_power_origin_x,magma_power_origin_y,p->x,p->y))return;
 x=p->x;y=p->y;if(!coordinate(p->tx,p->ty)||dist(x,y,p->tx,p->ty)>96||solid(x,y))return;
 p->open=1;p->ex=(short)x;p->ey=(short)y;
 /* An empty inclusive rectangle contains the entire raster and both diagonal
  * side cells. Failed proof changes nothing: clip with the original loop. */
 if(game_clear_box&&game_clear_box(x<p->tx?x:p->tx,y<p->ty?y:p->ty,x>p->tx?x:p->tx,y>p->ty?y:p->ty)){
  p->ex=p->tx;p->ey=p->ty;p->whole=1;return;
 }
 dx=absolute(p->tx-x);dy=-absolute(p->ty-y);
 sx=x<p->tx?1:-1;sy=y<p->ty?1:-1;err=dx+dy;
 while(x!=p->tx||y!=p->ty){int e=err*2,nx=x,ny=y;
  if(e>=dy){err+=dy;nx+=sx;}if(e<=dx){err+=dx;ny+=sy;}
  if((nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))||solid(nx,ny))return;
  x=nx;y=ny;p->ex=(short)x;p->ey=(short)y;
 }p->whole=1;
}
static void refresh(unsigned n){unsigned i;if(n>=12)return;for(i=0;i<=n;i++)refresh_one(i);
}
/* Exact raster proximity, with only short target LOS checked live. */
static int on_path(unsigned n,int qx,int qy){Path*p=&paths[n];int x,y,dx,dy,sx,sy,err,r=p->radius,step=0;
 refresh(n);if(!p->open||qx<(p->x<p->ex?p->x:p->ex)-r||qx>(p->x>p->ex?p->x:p->ex)+r||
 qy<(p->y<p->ey?p->y:p->ey)-r||qy>(p->y>p->ey?p->y:p->ey)+r)return 0;
 x=p->x;y=p->y;dx=absolute(p->ex-x);dy=-absolute(p->ey-y);sx=x<p->ex?1:-1;sy=y<p->ey?1:-1;err=dx+dy;
 for(;;){int e;if(step>=p->from&&step<=p->to&&dist(x,y,qx,qy)<=r&&clear(x,y,qx,qy))return 1;if(x==p->ex&&y==p->ey)return 0;
 e=err*2;if(e>=dy){err+=dy;x+=sx;}if(e<=dx){err+=dx;y+=sy;}step++;}
}
static int crossing(unsigned n,unsigned i){int x=previous_x[i],y=previous_y[i],tx=enemies[i].x,ty=enemies[i].y,dx,dy,sx,sy,err;
 if(on_path(n,tx,ty))return 1;
 if(dist(x,y,tx,ty)>24||!clear(x,y,tx,ty))return 0;
 dx=absolute(tx-x);dy=-absolute(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;err=dx+dy;
 while(x!=tx||y!=ty){int e=err*2;if(on_path(n,x,y))return 1;
 if(e>=dy){err+=dy;x+=sx;}if(e<=dx){err+=dx;y+=sy;}}
 return 0;
}
static int hurt(unsigned i){const Spec*s=spec();Enemy*e;
 if(!s||!ordinary(i)||(hit_mask&(1u<<i)))return 0;
 e=&enemies[i];hit_mask|=(unsigned char)(1u<<i);
 game_enemy_hurt(i,s->damage,0,(unsigned)magma_power_phase);e->flash=12;impact(e->x,e->y);
 if(e->hp<=0)kill_enemy(e);
 return 1;
}
static void halt(unsigned i,unsigned duration){if(!ordinary(i))return;
 if(enemy_stagger_ticks[i]<duration){enemy_stagger_ticks[i]=(unsigned char)duration;own_stagger|=(unsigned char)(1u<<i);}}
static int aim_point(int*x,int*y){unsigned i;int best=49,dx=fx[face],dy=fy[face];
 *x=px+dx*40;*y=py+dy*40;
 {int tx,ty;if(magma_game_target(&tx,&ty,0)&&coordinate(tx,ty)){int ex=tx-px,ey=ty-py,f=ex*dx+ey*dy,l=-ex*dy+ey*dx;
  if(f>=8&&f<best&&absolute(l)<=12&&dist(px,py,tx,ty)<=48&&clear(px,py,tx,ty)){best=f;*x=tx;*y=ty;}}}
 for(i=0;i<6;i++)if(ordinary(i)){int ex=enemies[i].x-px,ey=enemies[i].y-py,f=ex*dx+ey*dy,s=-ex*dy+ey*dx;
  if(f>=8&&f<best&&absolute(s)<=12&&dist(px,py,enemies[i].x,enemies[i].y)<=48&&clear(px,py,enemies[i].x,enemies[i].y)){
   best=f;*x=enemies[i].x;*y=enemies[i].y;}}
 return clear(px,py,*x,*y);
}
int magma_power_side(unsigned command,int side){CreatureInstance*c;const CreatureAbility*a;const Spec*s;unsigned i,cd;int x=0,y=0;
 if(command<43||command>66||ability_cd||magma_power_time||hitstop||face<0||face>3||
 (side!=-1&&side!=1)||!coordinate(px,py))return 0;
 c=progression_selected();a=creatures_ability(command);s=&specs[command-43];
 if(!c||!creatures_instance_validate(c)||c->selected_command>=2||c->equipped[c->selected_command]!=command||
 !creatures_command_learned(c->form_id,c->level,command)||!a||a->phase!=s->phase||a->cooldown_updates!=s->cooldown||solid(px,py))return 0;
 if((command==51||command==53)&&!aim_point(&x,&y))return 0;
 if(!northern_powers_tiles_claim(NORTHERN_TILES_MAGMA))return 0;
 magma_power_kind=(int)command;magma_power_form=c->form_id;caster_id=c->instance_id;magma_power_direction=face;
 magma_power_origin_x=px;magma_power_origin_y=py;magma_power_phase=a->phase;magma_power_age=0;
 magma_power_time=s->startup+s->active+s->recovery;magma_power_cast_time=s->startup;
 chapter_token=magma_game_action_begin(3);chapter_hit=0;
 cd=game_power_cooldown(s->cooldown);if(cd<s->cooldown-GAME_MAX_POWER_RECOVERY)cd=s->cooldown-GAME_MAX_POWER_RECOVERY;if(cd>s->cooldown)cd=s->cooldown;
 magma_power_cooldown=ability_cd=ability_max=(int)cd;cast_side=(signed char)side;aim_x=(short)x;aim_y=(short)y;
 hit_mask=spent=aimed=ended_mask=path_count=guard_grace=0;guard_enemy=6;
 for(i=0;i<6;i++){previous_x[i]=(short)enemies[i].x;previous_y[i]=(short)enemies[i].y;}
 magma_powers_geometry_changed();lease_generation=northern_powers_tiles_generation();
 obj_upload(magma_power_marks[command-43],16,16,GFX_OBJ_POWER_PIN);
 obj_upload(magma_power_particles[command-43],8,8,GFX_OBJ_WATER_DROP);sfx(2);return 1;
}
int magma_power(unsigned command){return magma_power_side(command,-1);}
int magma_powers_feedback(unsigned command){CreatureInstance*c;if(command<43||command>66||magma_power_time||face<0||face>3)return 0;
 c=progression_selected();if(!c||!creatures_instance_validate(c)||!creatures_command_learned(c->form_id,c->level,command))return 0;
 caster_id=c->instance_id;magma_power_form=c->form_id;magma_power_kind=(int)command;magma_power_direction=face;
 magma_power_origin_x=px;magma_power_origin_y=py;magma_power_cast_time=16;return 1;
}
int magma_powers_can_aim(void){return active()&&!hitstop&&!aimed&&magma_power_kind==51&&magma_power_age<12&&same_caster();}
unsigned magma_powers_hint(void){return magma_powers_can_aim()?MAGMA_HINT_LANDING:MAGMA_HINT_NONE;}
int magma_powers_aim(void){int x,y;if(!magma_powers_can_aim()||face<0||face>3||!aim_point(&x,&y)||
 dist(magma_power_origin_x,magma_power_origin_y,x,y)>48||!clear(magma_power_origin_x,magma_power_origin_y,x,y))return 0;
 aim_x=(short)x;aim_y=(short)y;aimed=1;magma_powers_geometry_changed();sfx(2);return 1;}
/* Paths are ground collision geometry. Animation may lift a visual glyph but
 * always leaves its exact ground footprint visible. The return mask selects
 * active components; warnings use the same segments without applying damage. */
static unsigned geometry(void){const Spec*s=spec();int a=s?magma_power_age-s->startup:0;
 unsigned mask=7;int t=a<0?0:a,side=cast_side;path_count=0;
 switch(magma_power_kind){
 case 43:line(0,8,-20,8,20,3,0,0);break;
 case 44:{int close=a<0?0:t>11?9:(t>>2)*3,h=16-close;
  line(0,12,-h,24,-h,3,0,0);line(1,24,-h,28,-h+5,3,0,1);
  line(2,12,h,24,h,3,1,0);line(3,24,h,28,h-5,3,1,3);break;}
 case 45:line(0,8,-8,26,-20,3,0,0);line(1,16,0,38,0,3,1,0);line(2,8,8,26,20,3,2,0);
  mask=a<0?7:t<10?1:t<20?2:4;break;
 case 46:line(0,5,0,22,-7,3,0,0);line(1,5,0,22,0,3,0,0);line(2,5,0,22,7,3,0,0);break;
 case 47:line(0,10,-10,16,-6,3,0,0);line(1,16,-6,16,6,3,0,1);line(2,16,6,10,10,3,0,2);break;
 case 48:line(0,10,-22,24,-14,3,0,0);line(1,24,-14,30,0,3,0,1);
  line(2,30,0,24,14,3,0,2);line(3,24,14,10,22,3,0,3);break;
 case 49:line(0,0,0,36,0,3,0,0);if(a>=0){paths[0].from=(unsigned char)(t*2);paths[0].to=(unsigned char)(t*2+2);}break;
 case 50:line(0,6,-12,38,-12,3,0,0);line(1,6,12,38,12,3,1,0);break;
 case 51:path_set(0,aim_x,aim_y,aim_x,aim_y,6,0,0);break;
 case 52:line(0,23,-5,33,-5,3,0,0);line(1,23,0,33,0,3,0,0);line(2,23,5,33,5,3,0,0);break;
 case 53:path_set(0,aim_x,aim_y-8,aim_x,aim_y-8,3,0,0);
  path_set(1,aim_x,aim_y,aim_x,aim_y,3,1,0);path_set(2,aim_x,aim_y+8,aim_x,aim_y+8,3,2,0);
  mask=a<0?7:t<10?1:t<20?2:4;break;
 case 54:line(0,18,-22,18,23,a>=0&&t>=4?6:2,0,0);
  if(a>=0){paths[0].from=(unsigned char)(t<15?t*3:45);paths[0].to=(unsigned char)(t<15?t*3+3:45);}break;
 case 55:line(0,6,-5,22,-5,3,0,0);line(1,6,5,22,5,3,1,0);mask=a<0?3:t<6?1:2;break;
 case 56:line(0,4,0,28,0,3,0,0);break;
 case 57:line(0,6,-10,22,6,3,0,0);line(1,22,6,22,24,3,1,1);mask=a<0?3:t<8?1:2;
  if(a>=8){paths[1].from=(unsigned char)((t-8)<9?(t-8)*2:18);paths[1].to=(unsigned char)((t-8)<9?(t-8)*2+2:18);}break;
 case 58:line(0,0,0,20,16*side,3,0,0);
  if(a>=0){paths[0].from=(unsigned char)(t*2);paths[0].to=(unsigned char)(t*2+2);}break;
 case 59:line(0,10,12,22,-12,3,0,0);line(1,22,-12,38,6,3,1,1);mask=a<0?3:t<9?1:2;break;
 case 60:if(a>=40){line(0,18,-8,30,-12,3,0,0);line(1,18,0,34,0,3,0,0);line(2,18,8,30,12,3,0,0);}
  else line(0,18,-8,18,8,3,0,0);
  break;
 case 61:line(0,0,0,28,-10,2,0,0);line(1,0,0,30,0,2,1,0);line(2,0,0,28,10,2,2,0);
  if(a>=0){unsigned i;for(i=0;i<3;i++){paths[i].from=(unsigned char)(t<10?t*3:30);paths[i].to=(unsigned char)(t<10?t*3+3:30);}}break;
 case 62:line(0,4,-14,28,-14,3,0,0);line(1,4,14,28,14,3,1,0);
  mask=a<0?3:t<10?1:2;break;
 case 63:line(0,0,0,36,0,3,0,0);if(a>=0){paths[0].from=(unsigned char)(t+(t>>1));paths[0].to=(unsigned char)(t+1+((t+1)>>1));}break;
 case 64:line(0,0,0,24,0,3,0,0);line(1,24,0,24,24*side,3,1,1);break;
 case 65:line(0,0,0,28,-20,2,0,0);line(1,0,0,32,0,2,1,0);line(2,0,0,28,20,2,2,0);
  if(a>=0){unsigned i;for(i=0;i<3;i++){paths[i].from=(unsigned char)(t*2);paths[i].to=(unsigned char)(t*2+2);}}break;
 case 66:{
  /* Five separated radial lobes. The broad lobe tips are the moving edge;
   * the centre and angular spaces stay harmless at every expansion step. */
  static const signed char lf[5]={32,10,-26,-26,10},ls[5]={0,30,19,-19,-30};unsigned i;
  for(i=0;i<5;i++){int r=a<0?9:9+t;line(i,0,0,lf[i],ls[i],3,0,0);
   {int major=absolute(lf[i]);if(absolute(ls[i])>major)major=absolute(ls[i]);
   paths[i].from=(unsigned char)((major*(r-2))>>5);paths[i].to=(unsigned char)((major*(r+2))>>5);}}
  break;}
 default:mask=0;break;
 }return mask;
}
static int projectile_command(void){return magma_power_kind==49||magma_power_kind==58||magma_power_kind==61||magma_power_kind==63||magma_power_kind==65;}
/* The explicit exposed chapter coupling is the sole boss exception. This
 * is damage only, never ordinary control. Its independent channel token and
 * our local cast bit survive weapon starts, aim, selection and closed windows. */
static __attribute__((noinline)) int hit_chapter(unsigned p){int x,y;const Spec*s=spec();unsigned q4;
 if(chapter_hit||!chapter_token||!s||!magma_game_target(&x,&y,0)||!coordinate(x,y)||!on_path(p,x,y))return 0;
 q4=combat_damage_q4(s->damage,0,0,(unsigned)magma_power_phase,COMBAT_NEUTRAL_PHASE,0);
 if(!magma_game_command_hit(x,y,q4,chapter_token))return 0;
 chapter_hit=1;impact(x,y);return 1;
}
static void damage_paths(unsigned mask){unsigned p,i;int moving=projectile_command();
 if(spent&&(magma_power_kind==43||magma_power_kind==52||magma_power_kind==55))return;
 for(p=0;p<path_count;p++)if((mask&(1u<<paths[p].group))&&!(ended_mask&(1u<<paths[p].group))){
  refresh(p);if(!paths[p].open)continue;
  for(i=0;i<6;i++)if(ordinary(i)&&!(hit_mask&(1u<<i))){int was_vulnerable=enemy_stagger_ticks[i]>0;
   int yes=(magma_power_kind==43||magma_power_kind==50)?crossing(p,i):on_path(p,enemies[i].x,enemies[i].y);
   if(!yes||!hurt(i))continue;
   if(magma_power_kind==46||magma_power_kind==48){enemy_windups[i]=0;halt(i,magma_power_kind==46?8:12);}
   if(magma_power_kind==49&&ordinary(i)&&slowed_enemies[i]<18){slowed_enemies[i]=18;own_slow|=(unsigned char)(1u<<i);}
   if(magma_power_kind==50&&ordinary(i)&&rooted_enemies[i]<12){rooted_enemies[i]=12;own_root|=(unsigned char)(1u<<i);}
   if(magma_power_kind==52){enemy_windups[i]=0;halt(i,12);}
   if(magma_power_kind==56&&was_vulnerable)halt(i,16);
   if(moving){ended_mask|=(unsigned char)(1u<<paths[p].group);break;}
   if(magma_power_kind==43||magma_power_kind==52||magma_power_kind==55){spent=1;return;}
  }
  if(!(ended_mask&(1u<<paths[p].group))&&hit_chapter(p)){
   if(moving)ended_mask|=(unsigned char)(1u<<paths[p].group);
   if(magma_power_kind==43||magma_power_kind==52||magma_power_kind==55){spent=1;return;}
  }
  /* A clipped path never gets resurrected after its missile reaches the wall. */
  if(moving&&!paths[p].whole){int length=absolute(paths[p].ex-paths[p].x),dy=absolute(paths[p].ey-paths[p].y);
   if(dy>length)length=dy;
   if(paths[p].to>=length)ended_mask|=(unsigned char)(1u<<paths[p].group);}
 }
}
int magma_powers_melee_guard(unsigned i,int x,int y){int f,s;
 if(!live_window()||hitstop||magma_power_kind!=47||!ordinary(i)||enemies[i].kind==2)return 0;
 if(guard_grace&&guard_enemy==i&&guard_serial==enemy_serial[i])return 1;
 if(spent||dist(px,py,magma_power_origin_x,magma_power_origin_y)>6||!coordinate(x,y)||
 dist(x,y,enemies[i].x,enemies[i].y)>4||!clear(x,y,px,py))return 0;
 relative(x,y,&f,&s);if(f<4||f>22||absolute(s)>10)return 0;
 spent=1;guard_enemy=(unsigned char)i;guard_serial=enemy_serial[i];guard_grace=8;
 hurt(i);return 1;
}
int magma_powers_intercept_shot(unsigned i,int x,int y,int tx,int ty,int eligible){int dx,dy,sx,sy,err;
 if(!live_window()||hitstop||magma_power_kind!=60||spent||eligible!=1||i>=12||shots[i].life<=0||shots[i].owner!=1||
 shots[i].x!=x||shots[i].y!=y||!coordinate(x,y)||!coordinate(tx,ty)||dist(x,y,tx,ty)>24||tx-x!=shots[i].dx||ty-y!=shots[i].dy)return 0;
 geometry();dx=absolute(tx-x);dy=-absolute(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;err=dx+dy;
 for(;;){int e,nx=x,ny=y;if(solid(x,y))return 0;
  if(on_path(0,x,y)){shots[i].life=0;spent=1;impact(x,y);return 1;}
  if(x==tx&&y==ty)return 0;
  e=err*2;if(e>=dy){err+=dy;nx+=sx;}if(e<=dx){err+=dx;ny+=sy;}
  if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return 0;
  x=nx;y=ny;
 }
}
void magma_powers_tick(void){const Spec*s;unsigned i,mask;
 if(hitstop)return;
 if(magma_power_cast_time)magma_power_cast_time--;
 if(!magma_power_time)return;
 if(!active()||!(s=spec())){finish();return;}
 magma_power_age++;if(guard_grace)guard_grace--;
 mask=geometry();
 if(live_window()&&magma_power_kind!=47&&magma_power_kind!=60){
  int t=magma_power_age-s->startup;
  if(magma_power_kind!=53||t==6||t==16||t==26)damage_paths(mask);
 }
 /* The screen's timed outward puff is a single ordinary hit at expiry, even
  * when it caught no projectile. Interception never creates a second puff. */
 if(magma_power_kind==60&&magma_power_age==s->startup+s->active){
  damage_paths(1);
 }
 for(i=0;i<6;i++){previous_x[i]=(short)enemies[i].x;previous_y[i]=(short)enemies[i].y;}
 if(--magma_power_time==0)finish();
}
static void draw_at(int x,int y,int large){if(draw_count>=24)return;draw_count++;
 obj_add(large?GFX_OBJ_POWER_PIN:GFX_OBJ_WATER_DROP,x-(large?8:4),y-(large?8:4),large?16:8,large?16:8,1,y+2,0);}
static void draw_path(unsigned n,int large){Path*p=&paths[n];int x,y,dx,dy,sx,sy,err,k=0,last=-9;
 refresh(n);if(!p->open)return;x=p->x;y=p->y;dx=absolute(p->ex-x);dy=-absolute(p->ey-y);
 sx=x<p->ex?1:-1;sy=y<p->ey?1:-1;err=dx+dy;
 for(;;){int e;if(k>=p->from&&k<=p->to&&(k-last>=6||(x==p->ex&&y==p->ey)||k==p->to)){
   draw_at(x,y,large);last=k;}
  if(x==p->ex&&y==p->ey)return;
  e=err*2;if(e>=dy){err+=dy;x+=sx;}if(e<=dx){err+=dx;y+=sy;}k++;
 }
}
void magma_powers_draw(void){const Spec*s=spec();unsigned mask,p;
 if(!active()||!s)return;
 draw_count=0;mask=geometry();
 if(magma_power_age>=s->startup+s->active){
  if(magma_power_kind==60&&magma_power_age<s->startup+s->active+6)mask=1;
  else return;
 }
 if(spent&&(magma_power_kind==43||magma_power_kind==52||magma_power_kind==55||magma_power_kind==47||
 (magma_power_kind==60&&magma_power_age<s->startup+s->active)))return;
 for(p=0;p<path_count;p++)if((mask&(1u<<paths[p].group))&&!(ended_mask&(1u<<paths[p].group)))
  draw_path(p,paths[p].radius>=6);
 /* Airborne body is presentation only; the checked ground footprint stays
  * visible and remains the sole collision authority. */
 if(magma_power_kind==49&&live_window()&&!(ended_mask&1)){int t=magma_power_age-s->startup,h,x,y;
  t=t<9?t:t-9;h=t<5?t*2:(8-t)*2;
  refresh(0);if(paths[0].open){int travel=(magma_power_age-s->startup)*2;point(travel,0,&x,&y);
   if(h>0&&travel<=absolute(paths[0].ex-paths[0].x)+absolute(paths[0].ey-paths[0].y))draw_at(x,y-h,1);}
 }
 if(magma_power_kind==51&&magma_power_age>=8&&magma_power_age<s->startup){
  refresh(0);if(paths[0].open)draw_at(aim_x,aim_y-(s->startup-magma_power_age)*2,1);
 }
 if(magma_power_kind==53){int a=magma_power_age-s->startup;unsigned g=(unsigned)(a<0?0:a<10?0:a<20?1:2);
  int descent=a<0?12:a-(int)g*10;
  refresh(g);if(paths[g].open&&descent<6)draw_at(paths[g].x,paths[g].y-(6-descent)*2,1);
 }
}
