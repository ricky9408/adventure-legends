/* Fifteen original, finite Return decisions. No dynamic allocation, persistent
 * receipts, save validation, new OBJ storage, or IWRAM code. Every damaging/
 * field pixel is one of the diamonds actually submitted to the OBJ renderer. */
#include "return_powers.h"
#include "return_power_art.h"
#include "return_game.h"
#include "field_world.h"
#include "northern_powers.h"
#include "progression.h"
#include "gear_runtime.h"
#include "obj_layout.h"
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
extern Enemy enemies[6];extern Shot shots[12];
extern volatile int px,py,room;
extern int face,ability_cd,ability_max,hitstop;
extern int enemy_windups[6],enemy_clocks[6],enemy_aimx[6],enemy_aimy[6];
extern int solid(int,int),game_clear_box(int,int,int,int);
extern void kill_enemy(Enemy*),impact(int,int),sfx(int);
extern void obj_upload(const unsigned char*,int,int,int);
extern void obj_add(int,int,int,int,int,int,int,int);
int return_power_kind,return_power_time,return_power_form;
int return_power_direction,return_power_origin_x,return_power_origin_y;
int return_power_age,return_power_cooldown,return_power_cast_time,return_power_phase;
typedef struct {unsigned char startup,lifetime,cooldown,damage,phase;} Spec;
static const Spec specs[15]={
 {10,72,135,32,1},{10,60,150,0,0},{10,56,135,28,0},
 {10,48,150,24,2},{10,48,135,20,4},{8,42,120,24,3},
 {12,52,150,28,3},{10,60,135,24,0},{10,54,150,28,1},
 {10,50,135,28,0},{12,60,150,24,2},{8,24,90,16,3},
 {10,48,120,0,3},{8,30,90,20,4},{10,42,120,24,4}};
enum { DAMAGE=1,FIELD=2,GUARD=4,MARK_CAP=24 };
typedef struct {short x,y;unsigned char flags,pad;} Mark;
typedef struct {short x,y;} Point;
typedef struct {
 Mark marks[MARK_CAP];Point previous[6];
 unsigned caster,lease,token;
 unsigned short serial[6],bound_serial[6],shot_serial[12],caught_shot_serial;
 short drop_x,drop_y,last_x,last_y,field_x,field_y;
 unsigned char field_valid,field_radius,field_result,build_live;
 unsigned char count,hits,fields,revoked,aimed,dirty,art_live,spent;
 unsigned char released,release_age,charged,guard_used,stopped,carry_steps;
 unsigned char caught_shot,geometry_age,moving,quiet_used;
 signed char side;
} Cast;
static Cast cast;
typedef char return_cast_budget[(sizeof(Cast)+10*sizeof(int)<=512)?1:-1];
static const signed char dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};
static int ab(int v){return v<0?-v:v;}
static int dist(int x,int y,int tx,int ty){return ab(x-tx)+ab(y-ty);}
static int coord(int x,int y){return x>=0&&y>=0&&x<=1023&&y<=1023;}
static const Spec*spec(void){return (unsigned)(return_power_kind-91)<15u?&specs[return_power_kind-91]:0;}
static int active(void){return return_power_time>0&&cast.lease==northern_powers_tiles_generation()&&northern_powers_tiles_owner()==NORTHERN_TILES_RETURN;}
static int window(void){const Spec*s=spec();return active()&&s&&return_power_age>=s->startup&&return_power_age<s->lifetime-(return_power_kind==96?2:6);}
/* Endpoint-inclusive supercover, including BOTH side cells at diagonal steps.
 * Return's room implementation accelerates this exact predicate. Unsupported
 * old rooms retain bounded pixel traversal, never a proximity substitute. */
static int clear(int x,int y,int tx,int ty){int ax,ay,sx,sy,e,r;
 if(!coord(x,y)||!coord(tx,ty)||dist(x,y,tx,ty)>128)return 0;
 if(game_clear_box(x<tx?x:tx,y<ty?y:ty,x>tx?x:tx,y>ty?y:ty))return 1;
 if(field_world_is_room((unsigned)room)){r=field_world_supercover(x,y,tx,ty);if(r>=0)return r;}
 if(solid(x,y)||solid(tx,ty))return 0;
 ax=ab(tx-x);ay=-ab(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;e=ax+ay;
 while(x!=tx||y!=ty){int q=e*2,nx=x,ny=y;
  if(q>=ay){e+=ay;nx+=sx;}if(q<=ax){e+=ax;ny+=sy;}
  if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return 0;
  x=nx;y=ny;if(solid(x,y))return 0;
 }return 1;
}
static void world(int f,int s,int*x,int*y){int d=return_power_direction;
 *x=return_power_origin_x+f*dx[d]-s*dy[d];*y=return_power_origin_y+f*dy[d]+s*dx[d];}
static void local(int x,int y,int*f,int*s){int d=return_power_direction;
 x-=return_power_origin_x;y-=return_power_origin_y;*f=x*dx[d]+y*dy[d];*s=-x*dy[d]+y*dx[d];}
static int connected(int x,int y){return clear(return_power_origin_x,return_power_origin_y,x,y);}
static int stamp_clear(int x,int y){int a,b;
 if(!coord(x-2,y-2)||!coord(x+2,y+2))return 0;
 if(game_clear_box(x-2,y-2,x+2,y+2))return 1;
 for(b=-2;b<=2;b++)for(a=-2;a<=2;a++)if(ab(a)+ab(b)<=2&&solid(x+a,y+b))return 0;
 return 1;
}
static void mark(int x,int y,unsigned flags,int path){unsigned i;Mark*m;
 if(!path||cast.count>=MARK_CAP||(path!=2&&!stamp_clear(x,y)))return;
 for(i=0;i<cast.count;i++)if(cast.marks[i].x==x&&cast.marks[i].y==y){cast.marks[i].pad|=(unsigned char)flags;if(cast.build_live)cast.marks[i].flags|=(unsigned char)flags;return;}
 m=&cast.marks[cast.count++];m->x=(short)x;m->y=(short)y;m->flags=cast.build_live?(unsigned char)flags:0;m->pad=(unsigned char)flags;
}
static void point(int f,int s,unsigned flags){int x,y;world(f,s,&x,&y);mark(x,y,flags,connected(x,y));}
/* Raster stroke is a chain of exact radius2 diamond stamps, every4 raster
 * steps plus endpoints. The deliberately narrow scalloped outline is also
 * the collision mask, not an invisible continuous/inflated strip. */
static void line_world(int x,int y,int tx,int ty,unsigned flags,int path){int ax,ay,sx,sy,e,n=0,box,ray;
 if(!path||!coord(x,y)||!coord(tx,ty)||dist(x,y,tx,ty)>72)return;
 ax=ab(tx-x);ay=-ab(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;e=ax+ay;
 box=game_clear_box((x<tx?x:tx)-2,(y<ty?y:ty)-2,(x>tx?x:tx)+2,(y>ty?y:ty)+2);
 ray=box||clear(x,y,tx,ty);if(!ray&&solid(x,y))return;
 for(;;){int q,nx=x,ny=y;if(!(n&3)||(x==tx&&y==ty))mark(x,y,flags,box?2:1);
  if(x==tx&&y==ty)break;
  q=e*2;if(q>=ay){e+=ay;nx+=sx;}if(q<=ax){e+=ax;ny+=sy;}
  if(!ray&&!clear(x,y,nx,ny))break;
  x=nx;y=ny;n++;
 }
}
static void line(int f,int s,int tf,int ts,unsigned flags){int x,y,tx,ty;
 world(f,s,&x,&y);world(tf,ts,&tx,&ty);line_world(x,y,tx,ty,flags,connected(x,y));}
static void crescent(int x,int y,int size,unsigned flags){int d=return_power_direction;
 int ax=x-size*dx[d]-size*dy[d],ay=y-size*dy[d]+size*dx[d];
 int bx=x+size*dx[d],by=y+size*dy[d];
 int cx=x-size*dx[d]+size*dy[d],cy=y-size*dy[d]-size*dx[d];
 line_world(ax,ay,bx,by,flags,clear(x,y,ax,ay));line_world(bx,by,cx,cy,flags,clear(x,y,bx,by));
}
static int ordinary(unsigned i){return i<6&&enemies[i].hp>0&&(unsigned)enemies[i].kind<=2&&coord(enemies[i].x,enemies[i].y);}
static int bound(unsigned i){return ordinary(i)&&cast.serial[i]==cast.bound_serial[i];}
int return_powers_cast_matches_selected(void){CreatureInstance*c=progression_selected();return c&&(c->flags&CREATURE_OCCUPIED)&&cast.caster&&c->instance_id==cast.caster&&c->form_id==return_power_form;}
static int same_selected(void){CreatureInstance*c=progression_selected();return return_powers_cast_matches_selected()&&c->selected_command<2&&c->equipped[c->selected_command]==return_power_kind;}
static void finish(void){return_power_time=0;cast.count=0;northern_powers_tiles_release(NORTHERN_TILES_RETURN);}
void return_powers_reset(void){unsigned i;finish();for(i=0;i<sizeof cast;i++)((unsigned char*)&cast)[i]=0;
 return_power_kind=return_power_form=return_power_direction=0;return_power_origin_x=return_power_origin_y=0;
 return_power_age=return_power_cooldown=return_power_cast_time=return_power_phase=0;cast.side=-1;cast.caught_shot=12;
 /* The engine alone decides whether room/death rules also clear ability_cd. */
}
void return_powers_enemy_spawn(unsigned i){if(i>=6)return;if(++cast.serial[i]==0)cast.serial[i]=1;
 if(return_power_time)cast.hits|=(unsigned char)(1u<<i);
 cast.previous[i].x=(short)enemies[i].x;cast.previous[i].y=(short)enemies[i].y;
}
void return_powers_shot_spawn(unsigned i){if(i>=12)return;if(++cast.shot_serial[i]==0)cast.shot_serial[i]=1;}
void return_powers_selection_changed(void){if(return_power_time){if(cast.token)field_world_revoke_cast(cast.token);cast.revoked=1;cast.aimed=1;}}
void return_powers_geometry_changed(void){if(return_power_time){cast.dirty=1;cast.field_valid=0;}}
int return_powers_busy(void){return return_power_time>0;}
unsigned return_powers_cast_token(void){return cast.token;}
unsigned return_powers_caster_id(void){return cast.caster;}
unsigned return_powers_moving_objects(void){return active()?cast.moving:0;}
static void release(void){if(cast.released)return;cast.released=1;cast.release_age=(unsigned char)return_power_age;cast.dirty=1;
 if(return_power_kind==99){cast.drop_x=cast.last_x;cast.drop_y=cast.last_y;}
}
static int side_command(void){return return_power_kind==93||return_power_kind==95||return_power_kind==98||return_power_kind==100||return_power_kind==101||return_power_kind==102||return_power_kind==104||return_power_kind==105;}
int return_powers_can_aim(void){return active()&&!hitstop&&!cast.revoked&&!cast.aimed&&return_power_age<8&&same_selected();}
int return_powers_can_release(void){return active()&&!hitstop&&!cast.revoked&&same_selected()&&!cast.released&&return_power_age>=8&&
 (return_power_kind==91||return_power_kind==99||(return_power_kind==96&&cast.charged));}
unsigned return_powers_hint(void){if(!active()||cast.revoked||!same_selected())return RETURN_POWER_HINT_NONE;
 if(return_powers_can_aim())return return_power_kind==102?RETURN_POWER_HINT_QUIET_SIDE:side_command()?RETURN_POWER_HINT_SIDE:RETURN_POWER_HINT_FACE;
 if(return_powers_can_release())return return_power_kind==91?(cast.charged?RETURN_POWER_HINT_HEARTH_RELEASE:RETURN_POWER_HINT_HEARTH_CHARGE):return_power_kind==96?RETURN_POWER_HINT_NOTCH_RELEASE:RETURN_POWER_HINT_CARRY_RELEASE;
 if(return_power_kind==96&&!cast.released&&!cast.charged)return RETURN_POWER_HINT_NOTCH_CATCH;
 return RETURN_POWER_HINT_NONE;
}
int return_powers_input(unsigned pressed){unsigned p=pressed&240u;int result=0,d=-1;
 if(return_powers_can_aim()&&p&&!(p&(p-1))){d=p==16?3:p==32?2:p==64?1:0;
  if(side_command()){int cross=-dx[d]*dy[return_power_direction]+dy[d]*dx[return_power_direction];if(cross){cast.side=(signed char)(cross>0?1:-1);cast.aimed=1;result=1;}}
  else{ return_power_direction=d;cast.aimed=1;result=1;}
  if(result)cast.dirty=1;
 }
 if((pressed&256u)&&return_powers_can_release()){release();result|=2;}
 return result;
}
int return_powers_companion_pose(void){const Spec*s=spec();int a;
 if(!active()||!s||!same_selected())return -1;
 a=return_power_age;if(cast.released)a-=cast.release_age;else a-=s->startup;
 if(a<0)return 0;
 if(a<4)return 1;
 if(a<10)return 2;
 return -1;
}
/* All geometry is rebuilt only on an active simulation update. Draw is pure.
 * The last6 updates (2 for finite late notch release) are visible recovery
 * without collision or field authority. */
static void geometry(void){const Spec*s=spec();int t,f,z,x,y,tx,ty,live;unsigned fl;
 cast.count=0;cast.moving=0;cast.dirty=0;cast.field_valid=0;cast.geometry_age=(unsigned char)return_power_age;
 if(!s)return;
 t=return_power_age-s->startup;live=window();fl=DAMAGE|FIELD;cast.build_live=(unsigned char)live;
 switch(return_power_kind){
 case 91:world(20,0,&x,&y);
  if(!cast.released){line(16,-8,24,-8,FIELD);line(24,-8,24,8,FIELD);line(24,8,16,8,FIELD);
   if(return_power_age<20){f=return_power_age;point(f,0,0);cast.moving=1;}else if(connected(x,y)){cast.charged=1;point(20,0,FIELD);}}
  else{t=return_power_age-cast.release_age;if(t<18){int k=cast.charged?10:6;int travel=t<8?t:8;world(20+travel,0,&x,&y);if(connected(x,y))crescent(x,y,k,fl);cast.moving=t<8;}}
  break;
 case 92:line(22,-12,22,12,(FIELD|(!cast.guard_used?GUARD:0)));line(14,-12,22,-12,FIELD);line(14,12,22,12,FIELD);break;
 case 93:/* Out, one right-angle corner, then retrace the SAME route. */
  if(t<0){line(4,0,28,0,0);line(28,0,28,cast.side*16,0);break;}
  if(t<14){f=2+t*2;z=0;}else if(t<22){f=28;z=(t-13)*2*cast.side;}else if(t<30){f=28;z=(29-t)*2*cast.side;}else{f=28-(t-29)*2;z=0;}
  if(f<2)break;
  world(28,0,&tx,&ty);world(f,z,&x,&y);
  mark(x,y,fl,z==0?connected(x,y):(connected(tx,ty)&&clear(tx,ty,x,y)));cast.moving=1;break;
 case 94:if(!cast.charged){line(20,-8,20,8,(FIELD|(!cast.guard_used?GUARD:0)));line(12,-8,20,-8,0);line(12,8,20,8,0);}
  else{f=20+(return_power_age-cast.release_age)*2;if(f<=40){line(f,-6,f,6,fl);cast.moving=1;}}
  break;
 case 95:line(16,0,28,0,fl);line(28,0,28,cast.side*12,fl);line(28,cast.side*12,20,cast.side*12,FIELD);break;
 case 96:if(!cast.released){line(20,-8,20,-4,FIELD);line(20,4,20,8,FIELD);point(20,0,(FIELD|(!cast.guard_used?GUARD:0)));}
  else if(cast.charged){f=20+(return_power_age-cast.release_age)*3;if(f<=44){line(f,-4,f,4,fl);cast.moving=1;}}
  break;
 case 97:line(12,-12,36,-12,fl);line(12,12,36,12,fl);break;
 case 98:line(10,0,20,cast.side*4,0);line(20,cast.side*4,34,0,0);line(34,-8,34,8,FIELD);break;
 case 99:if(!cast.released){if(connected(cast.last_x,cast.last_y)){mark(cast.last_x,cast.last_y,FIELD,1);cast.moving=1;}}
  else if(clear(return_power_origin_x,return_power_origin_y,cast.drop_x,cast.drop_y))crescent(cast.drop_x,cast.drop_y,10,fl);
  break;
 case 100:/* One banked outward skip, never returns; blocked first leg cannot
             * authorize the second leg, even if endpoint itself is empty. */
  if(t<0){line(4,0,24,0,0);line(24,0,24,cast.side*24,0);break;}
  f=t<10?4+t*2:24;z=t<10?0:(t-9)*2*cast.side;if(ab(z)>24)break;
  world(24,0,&tx,&ty);world(f,z,&x,&y);mark(x,y,fl,z==0?connected(x,y):(connected(tx,ty)&&clear(tx,ty,x,y)));cast.moving=1;break;
 case 101:line(12,-12,36,-12,fl);line(20,12,36,12,fl);break;
 case 102:line(12,cast.side*8,28,cast.side*8,fl);break;
 case 103:if(cast.guard_used)point(28,0,FIELD);else{line(14,-12,28,0,FIELD|GUARD);line(28,0,14,12,FIELD|GUARD);}break;
 case 104:f=t<0?20:8+t*2;if(f<=36){line(f,-4,f,4,fl);point(28,cast.side*8,0);cast.moving=t>=0;}break;
 case 105:/* Unequal paths and velocities meet at the same tip on update18. */
  if(t<0){line(4,-12,34,0,0);line(10,16,22,16,0);line(22,16,34,0,0);break;}
  if(t<=18){int a=4+t*30/18,b=-12+t*12/18;world(a,b,&x,&y);mark(x,y,fl,connected(x,y));
   if(t<8){a=10+t*12/8;b=16;}else{a=22+(t-8)*12/10;b=16-(t-8)*16/10;}
   world(22,16,&tx,&ty);world(a,b,&x,&y);mark(x,y,fl,t<8?connected(x,y):(connected(tx,ty)&&clear(tx,ty,x,y)));cast.moving=2;}
  else if(t<24)point(34,0,fl);
  break;
 }
}
static void refresh_flags(void){unsigned i;int live=window();cast.field_valid=0;
 for(i=0;i<cast.count;i++)cast.marks[i].flags=live?(unsigned char)(cast.marks[i].pad&(~(cast.guard_used?GUARD:0))):0;
}
static int contains(int x,int y,unsigned flags){unsigned i;if(!window()||cast.dirty)return 0;
 for(i=0;i<cast.count;i++)if((cast.marks[i].flags&flags)&&dist(x,y,cast.marks[i].x,cast.marks[i].y)<=2)return 1;
 return 0;}
/* Exact intersecting visible diamond pixel inside target's drawn octagon.
 * Both the path that produced the stamp AND pixel-to-target LOS are required. */
static int overlap(int x,int y,int radius){unsigned i;int a,b,xx,yy,rx,ry;
 if(!window()||cast.dirty||!coord(x,y)||radius<0||radius>16)return 0;
 for(i=0;i<cast.count;i++){Mark*m=&cast.marks[i];if(!(m->flags&FIELD)||ab(m->x-x)>radius+2||ab(m->y-y)>radius+2)continue;
  for(b=-2;b<=2;b++)for(a=-2;a<=2;a++){if(ab(a)+ab(b)>2)continue;xx=m->x+a;yy=m->y+b;rx=ab(xx-x);ry=ab(yy-y);
   if(rx<=radius&&ry<=radius&&rx+ry<=radius+3&&clear(xx,yy,x,y))return 1;}
 }return 0;
}
int return_powers_overlap(int x,int y,int radius){int result;if(cast.dirty||!window())return 0;
 if(cast.field_valid&&x==cast.field_x&&y==cast.field_y&&radius==cast.field_radius)return cast.field_result;
 result=overlap(x,y,radius);
 if(coord(x,y)&&radius>=0&&radius<=16){cast.field_x=(short)x;cast.field_y=(short)y;cast.field_radius=(unsigned char)radius;cast.field_result=(unsigned char)result;cast.field_valid=1;}
 return result;
}
static void hurt(unsigned i){const Spec*s=spec();unsigned damage;if(!bound(i)||!s||(cast.hits&(1u<<i)))return;
 cast.hits|=(unsigned char)(1u<<i);damage=s->damage;if(return_power_kind==91&&!cast.charged)damage/=2;
 if(!damage)return;
 game_enemy_hurt(i,damage,0,(unsigned)return_power_phase);enemies[i].flash=12;impact(enemies[i].x,enemies[i].y);if(enemies[i].hp<=0)kill_enemy(&enemies[i]);}
/* Exact radius4 square footprint, checked once at its initial position and
 * then only the nine newly entered leading-edge pixels per one-pixel step.
 * This is a swept square, including one-pixel walls between old sample points. */
static int foot_open(int x,int y){int a,b;if(game_clear_box(x-4,y-4,x+4,y+4))return 1;
 for(b=-4;b<=4;b++)for(a=-4;a<=4;a++)if(solid(x+a,y+b))return 0;
 return 1;}
static int pocket_open(unsigned i,int x,int y){unsigned j;if(!foot_open(x,y))return 0;
 for(j=0;j<6;j++)if(j!=i&&enemies[j].hp>0&&ab(enemies[j].x-x)<9&&ab(enemies[j].y-y)<9)return 0;
 return ab(px-x)>=9||ab(py-y)>=9;
}
static void push(unsigned i,int tx,int ty,unsigned budget){unsigned n;int a;
 if(!bound(i)||budget>8||!foot_open(enemies[i].x,enemies[i].y))return;
 for(n=0;n<budget;n++){int x=enemies[i].x,y=enemies[i].y,nx=x,ny=y,ok=1;if(x==tx&&y==ty)break;
  if(ab(tx-x)>=ab(ty-y))nx+=tx>x?1:-1;else ny+=ty>y?1:-1;
  if(!clear(x,y,nx,ny))break;
  if(nx!=x){int edge=nx+(nx>x?4:-4);if(!game_clear_box(edge,ny-4,edge,ny+4))for(a=-4;a<=4;a++)if(solid(edge,ny+a))ok=0;}
  else{int edge=ny+(ny>y?4:-4);if(!game_clear_box(nx-4,edge,nx+4,edge))for(a=-4;a<=4;a++)if(solid(nx+a,edge))ok=0;}
  if(!ok)break;
  {unsigned j;for(j=0;j<6;j++)if(j!=i&&enemies[j].hp>0&&ab(enemies[j].x-nx)<9&&ab(enemies[j].y-ny)<9)ok=0;}
  if(!ok)break;
  enemies[i].x=nx;enemies[i].y=ny;
 }
}
static int honest_move(unsigned i){return dist(cast.previous[i].x,cast.previous[i].y,enemies[i].x,enemies[i].y)<=8&&clear(cast.previous[i].x,cast.previous[i].y,enemies[i].x,enemies[i].y);}
static int quiet_side(unsigned i){int ax=enemy_aimx[i],ay=enemy_aimy[i],rx=return_power_origin_x-enemies[i].x,ry=return_power_origin_y-enemies[i].y,cross;
 if(enemies[i].kind!=2||enemy_windups[i]<=0||(ax==0&&ay==0)||cast.quiet_used)return 0;
 cross=rx*(-ay)+ry*ax;return cross*cast.side>=8&&ab(rx*ax+ry*ay)<=24;
}
static void combat(void){unsigned i;int f,z,pf,pz,x,y;
 for(i=0;i<6;i++){if(!bound(i)||(cast.hits&(1u<<i)))continue;
  if(return_power_kind==98){if(cast.spent)break;local(enemies[i].x,enemies[i].y,&f,&z);local(cast.previous[i].x,cast.previous[i].y,&pf,&pz);
   if(!(pf<34&&f>=34&&ab(z)<=8&&ab(pz)<=8&&honest_move(i)&&contains(enemies[i].x,enemies[i].y,FIELD)))continue;
   cast.spent=1;world(26,0,&x,&y);hurt(i);push(i,x,y,8);continue;}
  if(!contains(enemies[i].x,enemies[i].y,DAMAGE))continue;
  if(return_power_kind==95){if(cast.spent||!honest_move(i)||dist(cast.previous[i].x,cast.previous[i].y,enemies[i].x,enemies[i].y)==0)continue;
   cast.spent=1;world(28,cast.side*12,&x,&y);hurt(i);if(pocket_open(i,x,y))push(i,x,y,8);}
  else if(return_power_kind==102){if(!quiet_side(i))continue;cast.quiet_used=1;enemy_windups[i]=0;enemy_clocks[i]=60;hurt(i);}
  else if(return_power_kind==104){if(cast.spent||enemies[i].kind>1)continue;cast.spent=1;
   x=enemies[i].x-dy[return_power_direction]*cast.side*8;y=enemies[i].y+dx[return_power_direction]*cast.side*8;hurt(i);if(pocket_open(i,x,y))push(i,x,y,8);}
  else if(return_power_kind==101){local(enemies[i].x,enemies[i].y,&f,&z);x=enemies[i].x-dy[return_power_direction]*(z<0?-6:6);y=enemies[i].y+dx[return_power_direction]*(z<0?-6:6);hurt(i);push(i,x,y,6);}
  else hurt(i);
 }
}
int return_powers_intercept_shot(unsigned i,int x,int y,int tx,int ty,int eligible){int f,z,tf,tz,ax,ay,sx,sy,e,n=0;
 Shot*shot;if(!eligible||i>=12||!window()||cast.dirty||cast.guard_used)return 0;
 if(return_power_kind!=92&&return_power_kind!=94&&return_power_kind!=96&&return_power_kind!=103)return 0;
 shot=&shots[i];if(!shot->life||!shot->owner||shot->x!=x||shot->y!=y||tx!=x+shot->dx||ty!=y+shot->dy||dist(x,y,tx,ty)>8||!cast.shot_serial[i])return 0;
 local(x,y,&f,&z);local(tx,ty,&tf,&tz);if(tf>=f||f<(return_power_kind==103?14:18))return 0;
 if(return_power_kind==96&&(ab(z)>2||ab(tz)>2))return 0;
 if(!clear(x,y,tx,ty))return 0;
 ax=ab(tx-x);ay=-ab(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;e=ax+ay;
 for(;;){int q;if(contains(x,y,GUARD)){cast.guard_used=1;cast.caught_shot=(unsigned char)i;cast.caught_shot_serial=cast.shot_serial[i];shot->life=0;impact(x,y);
   if(return_power_kind==94){cast.charged=1;cast.release_age=(unsigned char)return_power_age;}
   if(return_power_kind==96)cast.charged=1;
   if(return_power_kind==94)cast.dirty=1;
   else if(return_power_kind==103){unsigned j;int tipx,tipy,found=0;world(28,0,&tipx,&tipy);
    for(j=0;j<cast.count;j++)if(cast.marks[j].x==tipx&&cast.marks[j].y==tipy){cast.marks[0].x=cast.marks[j].x;cast.marks[0].y=cast.marks[j].y;cast.marks[0].flags=cast.marks[j].flags;cast.marks[0].pad=cast.marks[j].pad;cast.count=1;found=1;break;}
    if(!found)cast.count=0;
    refresh_flags();
   }else refresh_flags();
   return 1;}
  if((x==tx&&y==ty)||++n>8)break;
  q=e*2;if(q>=ay){e+=ay;x+=sx;}if(q<=ax){e+=ax;y+=sy;}
 }return 0;
}
int return_power(unsigned command){CreatureInstance*c;const CreatureAbility*a;const Spec*s;unsigned i,cd;
 if(command<91||command>105||ability_cd||return_power_time||hitstop||face<0||face>3||!coord(px,py)||solid(px,py))return 0;
 c=progression_selected();a=creatures_ability(command);s=&specs[command-91];
 if(!c||!creatures_instance_validate(c)||c->selected_command>=2||c->equipped[c->selected_command]!=command||!creatures_command_learned(c->form_id,c->level,command)||!a||a->phase!=s->phase||a->cooldown_updates!=s->cooldown)return 0;
 if(!northern_powers_tiles_claim(NORTHERN_TILES_RETURN))return 0;
 return_power_kind=(int)command;return_power_form=c->form_id;return_power_direction=face;return_power_phase=a->phase;
 return_power_origin_x=px;return_power_origin_y=py;return_power_age=0;return_power_time=s->lifetime;return_power_cast_time=s->startup;
 cast.caster=c->instance_id;cast.lease=northern_powers_tiles_generation();cast.token=field_world_action_begin(3);
 cast.count=cast.hits=cast.fields=cast.revoked=cast.aimed=cast.art_live=cast.spent=0;
 cast.released=cast.release_age=cast.charged=cast.guard_used=cast.stopped=cast.carry_steps=cast.moving=cast.quiet_used=0;
 cast.side=-1;cast.caught_shot=12;cast.last_x=cast.drop_x=(short)px;cast.last_y=cast.drop_y=(short)py;
 for(i=0;i<6;i++){cast.bound_serial[i]=cast.serial[i];cast.previous[i].x=(short)enemies[i].x;cast.previous[i].y=(short)enemies[i].y;}
 cd=game_power_cooldown(s->cooldown);if(cd<s->cooldown-GAME_MAX_POWER_RECOVERY)cd=s->cooldown-GAME_MAX_POWER_RECOVERY;if(cd>s->cooldown)cd=s->cooldown;
 return_power_cooldown=ability_cd=ability_max=(int)cd;
 obj_upload(return_power_marks[command-91],16,16,GFX_OBJ_POWER_PIN);obj_upload(return_power_particles[command-91][0],8,8,GFX_OBJ_WATER_DROP);geometry();sfx(2);return 1;
}
void return_powers_tick(void){const Spec*s;unsigned i;int x,y,r,moved;
 if(hitstop)return;
 if(return_power_cast_time)return_power_cast_time--;
 if(!return_power_time)return;
 if(!active()||!(s=spec())){finish();return;}
 return_power_age++;
 if(return_power_kind==99&&!cast.released){moved=dist(cast.last_x,cast.last_y,px,py);
  if(moved<=4&&cast.carry_steps+moved<=16&&clear(cast.last_x,cast.last_y,px,py)&&connected(px,py)){cast.carry_steps+=(unsigned char)moved;cast.last_x=(short)px;cast.last_y=(short)py;}
  if(return_power_age>=26||moved>4||cast.carry_steps>=16)release();
 }
 if(return_power_kind==91&&!cast.released&&return_power_age>=44)release();
 if(return_power_kind==96&&!cast.released&&return_power_age>=34){if(cast.charged)release();else{cast.released=1;cast.release_age=(unsigned char)return_power_age;}}
 /* Static geometry is reused; recovery transitions and reactive changes are
  * always rebuilt. Moving authored traces remain at most two objects. */
 if(return_power_age==s->startup||return_power_age==s->lifetime-(return_power_kind==96?2:6))refresh_flags();
 if(cast.dirty||
  (return_power_kind==91&&(return_power_age<=20||(cast.released&&(return_power_age-cast.release_age<=8||return_power_age-cast.release_age==18))))||return_power_kind==93||(return_power_kind==94&&cast.charged)||(return_power_kind==96&&cast.released)||(return_power_kind==99&&!cast.released)||return_power_kind==100||return_power_kind==104||return_power_kind==105)geometry();
 if(window()){
  if(!cast.art_live){obj_upload(return_power_particles[return_power_kind-91][0],8,8,GFX_OBJ_POWER_PIN);obj_upload(return_power_particles[return_power_kind-91][1],8,8,GFX_OBJ_WATER_DROP);cast.art_live=1;}
  combat();
  if(cast.token&&!cast.revoked&&same_selected())for(i=0;i<8;i++){
   if(cast.fields&(1u<<i))continue;
   if(!field_world_target(i,&x,&y,&r))break;
   if(return_powers_overlap(x,y,r)&&field_world_hit(i,(unsigned)return_power_kind,cast.caster,(unsigned)return_power_form,cast.token))cast.fields|=(unsigned char)(1u<<i);
   if(cast.dirty)break;
  }
 }
 for(i=0;i<6;i++){cast.previous[i].x=(short)enemies[i].x;cast.previous[i].y=(short)enemies[i].y;}
 if(--return_power_time==0)finish();
}
void return_powers_draw(void){unsigned i;if(!active()||cast.dirty)return;
 if(!cast.art_live)obj_add(GFX_OBJ_POWER_PIN,return_power_origin_x-8,return_power_origin_y-25,16,16,1,return_power_origin_y+2,0);
 for(i=0;i<cast.count;i++){Mark*m=&cast.marks[i];obj_add(cast.art_live&&!m->flags?GFX_OBJ_POWER_PIN:GFX_OBJ_WATER_DROP,m->x-3,m->y-3,8,8,1,m->y+2,0);}
}
