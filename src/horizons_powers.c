/* Original Shared Horizons decisions. Collision and field authority consist
 * solely of the exact radius2 diamond pixels submitted to OBJ. No heap,
 * persistent state, music/DMA ownership, resident OBJ or IWRAM allocation. */
#include "horizons_powers.h"
#include "horizons_power_art.h"
#include "horizons_game.h"
#include "field_world.h"
#include "northern_powers.h"
#include "progression.h"
#include "gear_runtime.h"
#include "obj_layout.h"
#include "north_art.h"
#include "south_art.h"
#include "collision_rects.h"
#include "connected_road_region.h"
#include "underwater_game.h"
#include "return_game.h"
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
extern Enemy enemies[6];extern Shot shots[12];
extern volatile int px,py,room;
extern int face,ability_cd,ability_max,hitstop;
extern unsigned char slowed_enemies[6];
extern int solid(int,int),game_clear_box(int,int,int,int);
extern void kill_enemy(Enemy*),impact(int,int),sfx(int);
extern void obj_upload(const unsigned char*,int,int,int);
extern void obj_add(int,int,int,int,int,int,int,int);
int horizons_power_kind,horizons_power_time,horizons_power_form;
int horizons_power_direction,horizons_power_origin_x,horizons_power_origin_y;
int horizons_power_age,horizons_power_cooldown,horizons_power_cast_time,horizons_power_phase;
typedef struct {unsigned char startup,active,settle,cooldown,damage,phase;} Spec;
static const Spec specs[16]={
 {6,24,8,72,16,0},{8,30,10,88,32,0},{8,24,10,84,32,1},{8,32,10,100,16,1},
 {6,12,12,66,32,2},{8,22,12,86,16,2},{6,18,8,64,32,4},{8,26,10,84,16,4},
 {10,10,16,80,48,3},{6,30,8,92,16,0},{6,20,10,74,32,1},{8,24,12,88,16,2},
 {6,24,8,72,16,3},{6,22,10,76,16,4},{8,28,8,90,32,0},{6,16,12,70,32,3}};
enum { DAMAGE=1,FIELD=2,GUARD=4,MARK_CAP=24 };
typedef struct {short x,y;unsigned char flags,pad;} Mark;
typedef struct {short x,y;} Point;
typedef struct {
 Mark marks[MARK_CAP];Point previous[6];
 unsigned caster,lease,token;
 unsigned short serial[6],bound_serial[6],shot_serial[12],caught_serial;
 short field_x,field_y;
 unsigned char count,hits,fields[2],revoked,aimed,dirty,art_live;
 unsigned char released,release_age,guard_used,caught_shot,beat,moving,stopped;
 unsigned char field_valid,field_radius,field_result,build_live;
 signed char side;
} Cast;
static Cast cast;
enum { GEOMETRY_RECT_CAP=48,GEOMETRY_RADIUS=64 };
typedef struct {short walls[GEOMETRY_RECT_CAP][4],x0,y0,x1,y1,area;unsigned char valid,count;} Geometry;
static Geometry collision;
typedef char horizons_cast_budget[(sizeof(Cast)+sizeof(Geometry)+12*sizeof(int)<=1024)?1:-1];
static const signed char dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};
static int ab(int v){return v<0?-v:v;}
static int dist(int x,int y,int tx,int ty){return ab(x-tx)+ab(y-ty);}
static int coord(int x,int y){return x>=0&&y>=0&&x<=1023&&y<=1023;}
static const Spec*spec(void){return (unsigned)(horizons_power_kind-106)<16u?&specs[horizons_power_kind-106]:0;}
static int active(void){return horizons_power_time>0&&cast.lease==northern_powers_tiles_generation()&&northern_powers_tiles_owner()==NORTHERN_TILES_HORIZONS;}
static int window(void){const Spec*s=spec();return active()&&s&&horizons_power_age>=s->startup&&horizons_power_age<s->startup+s->active;}
/* Exact query-local geometry, never an inferred visibility or damage mask.
 * Unknown/overflow snapshots retain the original collision path. */
static int geometry_snapshot(int x0,int y0,int x1,int y1){int n;
 if(!collision.valid||collision.area!=room){int ox=horizons_power_origin_x,oy=horizons_power_origin_y;
  collision.x0=(short)(ox>GEOMETRY_RADIUS?ox-GEOMETRY_RADIUS:0);collision.y0=(short)(oy>GEOMETRY_RADIUS?oy-GEOMETRY_RADIUS:0);
  collision.x1=(short)(ox<1023-GEOMETRY_RADIUS?ox+GEOMETRY_RADIUS:1023);collision.y1=(short)(oy<1023-GEOMETRY_RADIUS?oy+GEOMETRY_RADIUS:1023);
  collision.area=(short)room;collision.valid=2;collision.count=0;
  n=game_collision_rects(collision.x0,collision.y0,collision.x1,collision.y1,collision.walls,GEOMETRY_RECT_CAP);
  if(n>=0&&(unsigned)n<=GEOMETRY_RECT_CAP){collision.count=(unsigned char)n;collision.valid=1;}
 }
 return collision.valid==1&&x0>=collision.x0&&y0>=collision.y0&&x1<=collision.x1&&y1<=collision.y1;
}
static int clear_box(int x0,int y0,int x1,int y1){unsigned i;
 if(x0>x1||y0>y1)return 0;
 if(!geometry_snapshot(x0,y0,x1,y1))return game_clear_box(x0,y0,x1,y1);
 for(i=0;i<collision.count;i++){const short*r=collision.walls[i];if(x1>=r[0]&&x0<=r[2]&&y1>=r[1]&&y0<=r[3])return 0;}
 return 1;
}
static int blocked(int x,int y){return geometry_snapshot(x,y,x,y)?!clear_box(x,y,x,y):solid(x,y);}
/* Exact original supercover coverage of a rectangle's horizontal slab.
 * y-major center x(k)=floor((k*dx+dy/2)/dy); adjacent rows supply both corner
 * cells. The x-major inverse finds the first step in each boundary row. */
static int rectangle_ray(int x,int y,int tx,int ty){unsigned i,ax=(unsigned)ab(tx-x),ay=(unsigned)ab(ty-y);int sx=x<tx?1:-1,sy=y<ty?1:-1;
 int minx=x<tx?x:tx,maxx=x>tx?x:tx,miny=y<ty?y:ty,maxy=y>ty?y:ty;
 for(i=0;i<collision.count;i++){const short*r=collision.walls[i];unsigned k,last,u,v;int low,high,left,right;
  if(maxx<r[0]||minx>r[2]||maxy<r[1]||miny>r[3])continue;
  low=r[1]>miny?r[1]:miny;high=r[3]<maxy?r[3]:maxy;
  k=(unsigned)(sy>0?low-y:y-high);last=(unsigned)(sy>0?high-y:y-low);
  if(!ay){u=0;v=ax;}
  else if(ax<=ay){u=((k?k-1:0)*ax+ay/2)/ay;v=((last<ay?last+1:last)*ax+ay/2)/ay;}
  else{u=k?(k*ax-ax/2+ay-1)/ay-1:0;v=last<ay?((last+1)*ax-ax/2+ay-1)/ay:ax;}
  left=x+sx*(int)u;right=x+sx*(int)v;if(left>right){int swap=left;left=right;right=swap;}
  if(right>=r[0]&&left<=r[2])return 0;
 }return 1;
}
/* North/South collision is exactly the generated half-open row intervals.
 * Consecutive equal row records form a slab. The two bounding x coordinates
 * below include both diagonal side cells of the original Bresenham raster,
 * so testing the slab against its sorted intervals is an exact supercover. */
static int old_rows_clear(int x,int y,int tx,int ty){
 const unsigned short *rows,*bands,*b;unsigned width,height,offset,n,ax,ay,k=0,last,u,v,area=(unsigned)room;
 int sx=x<tx?1:-1,sy=y<ty?1:-1,left,right;
 if(area>=30u){const SouthArtRoom*r=&south_art_rooms[area-30u];width=r->width;height=r->height;rows=r->collision_rows;bands=r->collision_bands;}
 else{const NorthArtRoom*r=&north_art_rooms[area-22u];width=r->width;height=r->height;rows=r->collision_rows;bands=r->collision_bands;}
 if((unsigned)x>=width||(unsigned)tx>=width||(unsigned)y>=height||(unsigned)ty>=height)return 0;
 ax=(unsigned)ab(tx-x);ay=(unsigned)ab(ty-y);
 for(;;){offset=rows[y];last=k;
  while(last<ay&&rows[y+sy]==offset){y+=sy;last++;}
  if(!ay){u=0;v=ax;}
  else if(ax<=ay){u=((k?k-1:0)*ax+ay/2)/ay;v=((last<ay?last+1:last)*ax+ay/2)/ay;}
  else{u=k?(k*ax-ax/2+ay-1)/ay-1:0;v=last<ay?((last+1)*ax-ax/2+ay-1)/ay:ax;}
  left=x+sx*(int)u;right=x+sx*(int)v;if(left>right){int swap=left;left=right;right=swap;}
  b=bands+offset;n=*b++;
  while(n--){if((unsigned)right<b[0])break;if((unsigned)left<b[1])return 0;b+=2;}
  if(last==ay)return 1;
  k=last+1;y+=sy;
 }
}
/* Inclusive bounded supercover: diagonal travel checks both side cells. */
static int clear(int x,int y,int tx,int ty){int ax,ay,sx,sy,e,r;
 if(!coord(x,y)||!coord(tx,ty)||dist(x,y,tx,ty)>128)return 0;
 if(geometry_snapshot(x<tx?x:tx,y<ty?y:ty,x>tx?x:tx,y>ty?y:ty))return rectangle_ray(x,y,tx,ty);
 if(clear_box(x<tx?x:tx,y<ty?y:ty,x>tx?x:tx,y>ty?y:ty))return 1;
 if((unsigned)(room-62)<16u){r=field_world_supercover(x,y,tx,ty);return r>0;}
 if((unsigned)(room-22)<16u){
  /* A dense/unsupported snapshot still obeys newly opened road strips and
   * closed fences; untouched rays keep the generated-row fast path. */
  r=road_region_ray((unsigned)room,x,y,tx,ty,solid);
  return r>=0?r:old_rows_clear(x,y,tx,ty);
 }
 if((unsigned)(room-46)<8u){r=underwater_game_supercover(x,y,tx,ty);if(r>=0)return r;}
 if((unsigned)(room-54)<8u){r=return_game_supercover(x,y,tx,ty);if(r>=0)return r;}
 if(blocked(x,y)||blocked(tx,ty))return 0;
 ax=ab(tx-x);ay=-ab(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;e=ax+ay;
 while(x!=tx||y!=ty){int q=e*2,nx=x,ny=y;
  if(q>=ay){e+=ay;nx+=sx;}if(q<=ax){e+=ax;ny+=sy;}
  if(nx!=x&&ny!=y&&(blocked(nx,y)||blocked(x,ny)))return 0;
  x=nx;y=ny;if(blocked(x,y))return 0;
 }return 1;
}
static void world(int f,int s,int*x,int*y){int d=horizons_power_direction;
 *x=horizons_power_origin_x+f*dx[d]-s*dy[d];*y=horizons_power_origin_y+f*dy[d]+s*dx[d];}
static void local(int x,int y,int*f,int*s){int d=horizons_power_direction;
 x-=horizons_power_origin_x;y-=horizons_power_origin_y;*f=x*dx[d]+y*dy[d];*s=-x*dy[d]+y*dx[d];}
static int connected(int x,int y){return clear(horizons_power_origin_x,horizons_power_origin_y,x,y);}
static int stamp_clear(int x,int y){int a,b;
 if(!coord(x-2,y-2)||!coord(x+2,y+2))return 0;
 if(clear_box(x-2,y-2,x+2,y+2))return 1;
 for(b=-2;b<=2;b++)for(a=-2;a<=2;a++)if(ab(a)+ab(b)<=2&&blocked(x+a,y+b))return 0;
 return 1;
}
static void mark(int x,int y,unsigned flags,int path){unsigned i;Mark*m;
 if(!path||cast.count>=MARK_CAP||(path!=2&&!stamp_clear(x,y)))return;
 for(i=0;i<cast.count;i++)if(cast.marks[i].x==x&&cast.marks[i].y==y){cast.marks[i].pad|=(unsigned char)flags;if(cast.build_live)cast.marks[i].flags|=(unsigned char)flags;return;}
 m=&cast.marks[cast.count++];m->x=(short)x;m->y=(short)y;m->pad=(unsigned char)flags;m->flags=cast.build_live?(unsigned char)flags:0;
}
static void point(int f,int s,unsigned flags){int x,y;world(f,s,&x,&y);mark(x,y,flags,connected(x,y));}
/* Only the drawn scalloped stamps collide; no inflated invisible line. */
static void line_world(int x,int y,int tx,int ty,unsigned flags,int path){int ax,ay,sx,sy,e,n=0,box,ray;
 if(!path||!coord(x,y)||!coord(tx,ty)||dist(x,y,tx,ty)>72)return;
 ax=ab(tx-x);ay=-ab(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;e=ax+ay;
 box=clear_box((x<tx?x:tx)-2,(y<ty?y:ty)-2,(x>tx?x:tx)+2,(y>ty?y:ty)+2);
 ray=box||clear(x,y,tx,ty);if(!ray&&blocked(x,y))return;
 for(;;){int q,nx=x,ny=y;if(!(n&3)||(x==tx&&y==ty))mark(x,y,flags,box?2:1);
  if(x==tx&&y==ty)break;
  q=e*2;if(q>=ay){e+=ay;nx+=sx;}if(q<=ax){e+=ax;ny+=sy;}
  if(!ray&&!clear(x,y,nx,ny))break;
  x=nx;y=ny;n++;
 }
}
static void line(int f,int s,int tf,int ts,unsigned flags){int x,y,tx,ty;world(f,s,&x,&y);world(tf,ts,&tx,&ty);line_world(x,y,tx,ty,flags,connected(x,y));}
/* A radial stamp is drawn only when all13 of its pixels have direct LOS.
 * Otherwise a clear neighboring center could leak its radius2 edge behind a
 * one-pixel occluder. Open rectangles keep this fast in ordinary rooms. */
static void radial_point(int f,int s,unsigned flags){int x,y,a,b,ox=horizons_power_origin_x,oy=horizons_power_origin_y;world(f,s,&x,&y);
 if(!coord(x-2,y-2)||!coord(x+2,y+2))return;
 if(clear_box((x<ox?x:ox)-2,(y<oy?y:oy)-2,(x>ox?x:ox)+2,(y>oy?y:oy)+2)){mark(x,y,flags,2);return;}
 for(b=-2;b<=2;b++)for(a=-2;a<=2;a++)if(ab(a)+ab(b)<=2&&!clear(ox,oy,x+a,y+b))return;
 mark(x,y,flags,1);
}
/* Radial effects cannot borrow a clear side route around an occluder. */
static void radial_line(int f,int s,int tf,int ts,unsigned flags){int ax=ab(tf-f),ay=-ab(ts-s),sx=f<tf?1:-1,sy=s<ts?1:-1,e=ax+ay,n=0;
 for(;;){int q;if(!(n&3)||(f==tf&&s==ts))radial_point(f,s,flags);if(f==tf&&s==ts)break;
  q=e*2;if(q>=ay){e+=ay;f+=sx;}if(q<=ax){e+=ax;s+=sy;}n++;
 }
}
/* A moving blade follows four parallel straight lanes. The first obstruction
 * of ANY occupied lane ends this projectile, including a one-pixel wall that
 * a new diagonal ray to a later frame could otherwise bypass. */
static void blade(int f,int side,unsigned flags,int moving){int z,x,y,sx,sy;
 if(cast.stopped)return;
 for(z=-6;z<=6;z+=4){world(4,side+z,&sx,&sy);world(f,side+z,&x,&y);
  if(!connected(sx,sy)||!clear(sx,sy,x,y)||!stamp_clear(x,y)){if(moving)cast.stopped=1;return;}
 }
 for(z=-6;z<=6;z+=4){world(f,side+z,&x,&y);mark(x,y,flags,2);}
 cast.moving=(unsigned char)moving;
}
/* Small filled splash built from exact contiguous diamond centers. */
static void splash(int f,int s,int radius,unsigned flags){int a,b;
 for(b=-radius;b<=radius;b+=4)for(a=-radius;a<=radius;a+=4)if(ab(a)+ab(b)<=radius)point(f+a,s+b,flags);
}
static int enemy_live(unsigned i){return i<6&&enemies[i].hp>0&&(unsigned)enemies[i].kind<=3&&coord(enemies[i].x,enemies[i].y);}
static int ordinary(unsigned i){return enemy_live(i)&&(unsigned)enemies[i].kind<=2;}
static int bound(unsigned i){return enemy_live(i)&&cast.serial[i]==cast.bound_serial[i];}
int horizons_powers_cast_matches_selected(void){CreatureInstance*c=progression_selected();return c&&(c->flags&CREATURE_OCCUPIED)&&cast.caster&&c->instance_id==cast.caster&&c->form_id==horizons_power_form;}
static int same_selected(void){CreatureInstance*c=progression_selected();return horizons_powers_cast_matches_selected()&&c->selected_command<2&&c->equipped[c->selected_command]==horizons_power_kind;}
static void revoke(void){if(cast.token)field_world_revoke_cast(cast.token);cast.revoked=1;cast.aimed=1;}
static void finish(void){horizons_power_time=0;cast.count=0;northern_powers_tiles_release(NORTHERN_TILES_HORIZONS);}
void horizons_powers_reset(void){unsigned i;collision.valid=0;if(horizons_power_time)revoke();finish();for(i=0;i<sizeof cast;i++)((unsigned char*)&cast)[i]=0;
 horizons_power_kind=horizons_power_form=horizons_power_direction=0;horizons_power_origin_x=horizons_power_origin_y=0;
 horizons_power_age=horizons_power_cooldown=horizons_power_cast_time=horizons_power_phase=0;cast.side=-1;cast.caught_shot=12;
 /* Only engine room/death policy may clear ability_cd. */
}
void horizons_powers_enemy_spawn(unsigned i){if(i>=6)return;if(++cast.serial[i]==0)cast.serial[i]=1;
 if(horizons_power_time)cast.hits|=(unsigned char)(1u<<i);
 cast.previous[i].x=(short)enemies[i].x;cast.previous[i].y=(short)enemies[i].y;
}
void horizons_powers_shot_spawn(unsigned i){if(i>=12)return;if(++cast.shot_serial[i]==0)cast.shot_serial[i]=1;}
void horizons_powers_selection_changed(void){collision.valid=0;if(horizons_power_time)revoke();}
void horizons_powers_geometry_changed(void){collision.valid=0;if(horizons_power_time){revoke();cast.dirty=1;cast.field_valid=0;}}
int horizons_powers_busy(void){return horizons_power_time>0;}
unsigned horizons_powers_cast_token(void){return cast.token;}
unsigned horizons_powers_caster_id(void){return cast.caster;}
unsigned horizons_powers_moving_objects(void){return active()?cast.moving:0;}
unsigned horizons_powers_beat(void){return window()&&!cast.dirty?cast.beat:0;}
unsigned horizons_powers_release_phase(void){return window()&&cast.released&&!cast.dirty?1u:0u;}
static int side_command(void){return horizons_power_kind==107||horizons_power_kind==111||horizons_power_kind==112;}
int horizons_powers_can_aim(void){return active()&&!hitstop&&!cast.revoked&&!cast.aimed&&horizons_power_age<8&&same_selected();}
int horizons_powers_can_release(void){return active()&&!hitstop&&!cast.revoked&&same_selected()&&!cast.released&&horizons_power_age>=8&&
 ((horizons_power_kind==108&&horizons_power_age<30)||(horizons_power_kind==109&&horizons_power_age<36));}
unsigned horizons_powers_hint(void){if(!active()||cast.revoked||!same_selected())return HORIZONS_POWER_HINT_NONE;
 if(horizons_powers_can_aim())return side_command()?HORIZONS_POWER_HINT_SIDE:HORIZONS_POWER_HINT_FACE;
 if(horizons_powers_can_release())return horizons_power_kind==109&&!cast.guard_used?HORIZONS_POWER_HINT_CATCH:HORIZONS_POWER_HINT_RELEASE;
 if(horizons_power_kind==108&&!cast.released)return HORIZONS_POWER_HINT_GATHER;
 if(horizons_power_kind==117&&window())return HORIZONS_POWER_HINT_HOLD;
 if((horizons_power_kind==111||horizons_power_kind==113||horizons_power_kind==118)&&window())return HORIZONS_POWER_HINT_TWO_BEATS;
 return HORIZONS_POWER_HINT_NONE;
}
int horizons_powers_input(unsigned pressed){unsigned p=pressed&240u;int result=0,d=-1;
 if(horizons_powers_can_aim()&&p&&!(p&(p-1))){d=p==16?3:p==32?2:p==64?1:0;
  if(side_command()){int cross=-dx[d]*dy[horizons_power_direction]+dy[d]*dx[horizons_power_direction];if(cross){cast.side=(signed char)(cross>0?1:-1);cast.aimed=1;result=1;}}
  else{horizons_power_direction=d;cast.aimed=1;result=1;}
  if(result)cast.dirty=1;
 }
 if((pressed&256u)&&horizons_powers_can_release()){cast.released=1;cast.release_age=(unsigned char)horizons_power_age;cast.dirty=1;result|=2;}
 return result;
}
int horizons_powers_companion_pose(void){const Spec*s=spec();int a;if(!active()||!s||!same_selected())return -1;
 a=horizons_power_age;if(a<s->startup)return 0;
 if(a>=s->startup+s->active)return 2;
 if(cast.released)return a-cast.release_age<6?1:2;
 return a<s->startup+6?1:2;
}
/* The following sixteen silhouettes are deliberately distinct in both time
 * and negative space. Startup/settle geometry is decorative, never authority. */
static void geometry(void){const Spec*s=spec();int t,f,z,x,y,tx,ty;unsigned fl=DAMAGE|FIELD;
 cast.count=cast.moving=0;cast.dirty=cast.field_valid=0;cast.beat=1;cast.build_live=(unsigned char)window();if(!s)return;
 t=horizons_power_age-s->startup;
 switch(horizons_power_kind){
 case 106: /* One straight hem, out then precisely the same route back. */
  if(t<0){line(4,0,44,0,0);break;}
  cast.beat=(unsigned char)(t<12?1:2);f=t<12?4+t*4:48-(t-12)*4;
  if(f>=4&&f<=48){line(f-2,0,f,0,fl);cast.moving=1;}break;
 case 107: /* One32px leg, then one32px perpendicular leg. */
  if(t<0){line(2,0,30,0,0);line(30,0,30,cast.side*32,0);break;}
  f=t<15?2+t*2:30;z=t<15?0:(t-14)*2*cast.side;cast.beat=(unsigned char)(t<15?1:2);
  if(ab(z)<=32){world(30,0,&tx,&ty);world(f,z,&x,&y);mark(x,y,fl,z==0?connected(x,y):(connected(tx,ty)&&clear(tx,ty,x,y)));cast.moving=1;}break;
 case 108: /* Warmth is gathered locally; release expands at the ORIGINAL origin. */
  if(!cast.released){line(8,-4,8,4,FIELD);if(horizons_power_age>=30){cast.count=0;cast.build_live=0;}}
  else{cast.beat=2;f=horizons_power_age-cast.release_age;if(f<10){z=4+(f<4?f:4)*2;
    radial_line(-z,0,0,-z,fl);radial_line(0,-z,z,0,fl);radial_line(z,0,0,z,fl);radial_line(0,z,-z,0,fl);cast.moving=f<4;}}break;
 case 109: /* Catch crescent has an open rear; its answer is a separate short ember. */
  if(!cast.released){line(12,-10,20,0,FIELD|(!cast.guard_used?GUARD:0));line(20,0,12,10,FIELD|(!cast.guard_used?GUARD:0));}
  else{cast.beat=2;f=20+(horizons_power_age-cast.release_age)*2;if(f<=36){point(f,0,fl);cast.moving=1;}}break;
 case 110:line(10,-4,24,0,fl);line(24,0,10,4,fl);break;
 case 111: /* Near and far pads never fill the separating gap. */
  if(t<0){line(12,cast.side*8-4,12,cast.side*8+4,0);line(38,cast.side*8-4,38,cast.side*8+4,0);break;}
  cast.beat=(unsigned char)(t<10?1:2);f=t<10?12:38;line(f-2,cast.side*8-4,f+2,cast.side*8+4,fl);break;
 case 112:f=t<0?8:8+t*2;if(f<=42)blade(f,cast.side*6,fl,t>=0);break;
 case 113:cast.beat=(unsigned char)(t<10?1:2);f=t<10?16:52;z=t<10?-6:8;line(f-4,z,f+4,z,fl);break;
 case 114:line(4,0,34,0,fl);break;
 case 115: /* Nest aperture: no front-center stamp in the open shelter slit. */
  line(12,-12,20,-4,fl|(!cast.guard_used?GUARD:0));line(20,4,12,12,fl|(!cast.guard_used?GUARD:0));break;
 case 116: /* Clockwise quarter arc: beside, rear diagonal, then rear. */
  if(t<0){line(0,-24,-24,0,0);break;}
  if(t<20){f=-(t*24/19);z=-(24-t*24/19);line(f-2,z+2,f+2,z-2,fl);cast.moving=1;}break;
 case 117:line(10,-8,18,-8,fl);line(18,-8,18,8,fl);line(18,8,10,8,fl);break;
 case 118: /* Short first stroke; longer delayed partner, center remains empty. */
  cast.beat=(unsigned char)(t<8?1:2);if(t<8)line(8,-8,24,-8,fl);else if(t<24)line(8,8,38,8,fl);break;
 case 119: /* Unequal splash discs, two offset lanes with a dry middle. */
  if(t<0){point(14,-10,0);point(28,12,0);break;}
  if(t<10){splash(14,-10,4,fl);cast.moving=1;}
  else{cast.beat=2;splash(28,12,8,fl);cast.moving=1;}break;
 case 120:line(24,-12,24,12,fl);break;
 case 121: /* Expanding front fan: width grows with range; never a rear circle. */
  f=t<0?8:8+(t<14?t:14)*2;z=(f-4)/2;radial_line(f,-z,f,z,fl);cast.moving=t>=0&&t<14;break;
 }
}
static int contains(int x,int y,unsigned flags){unsigned i;if(!window()||cast.dirty)return 0;
 for(i=0;i<cast.count;i++)if((cast.marks[i].flags&flags)&&dist(x,y,cast.marks[i].x,cast.marks[i].y)<=2)return 1;
 return 0;
}
static int overlap(int x,int y,int radius){unsigned i;int a,b,xx,yy,rx,ry;
 if(!window()||cast.dirty||!coord(x,y)||radius<0||radius>16)return 0;
 for(i=0;i<cast.count;i++){Mark*m=&cast.marks[i];if(!(m->flags&FIELD)||ab(m->x-x)>radius+2||ab(m->y-y)>radius+2)continue;
  for(b=-2;b<=2;b++)for(a=-2;a<=2;a++){if(ab(a)+ab(b)>2)continue;xx=m->x+a;yy=m->y+b;rx=ab(xx-x);ry=ab(yy-y);
   if(rx<=radius&&ry<=radius&&rx+ry<=radius+3&&clear(xx,yy,x,y))return 1;}
 }return 0;
}
int horizons_powers_overlap(int x,int y,int radius){int result;if(cast.dirty||!window())return 0;
 if(cast.field_valid&&x==cast.field_x&&y==cast.field_y&&radius==cast.field_radius)return cast.field_result;
 result=overlap(x,y,radius);if(coord(x,y)&&radius>=0&&radius<=16){cast.field_x=(short)x;cast.field_y=(short)y;cast.field_radius=(unsigned char)radius;cast.field_result=(unsigned char)result;cast.field_valid=1;}return result;
}
static void hurt(unsigned i){const Spec*s=spec();unsigned damage;if(!bound(i)||!s||(cast.hits&(1u<<i)))return;
 cast.hits|=(unsigned char)(1u<<i);damage=s->damage;
 if(horizons_power_kind==106&&cast.beat==2)damage=32;
 if(horizons_power_kind==109&&cast.guard_used)damage=48;
 if((horizons_power_kind==111||horizons_power_kind==113)&&cast.beat==2)damage=48;
 if((horizons_power_kind==118||horizons_power_kind==119)&&cast.beat==2)damage=32;
 game_enemy_hurt(i,damage,0,(unsigned)horizons_power_phase);enemies[i].flash=12;impact(enemies[i].x,enemies[i].y);if(enemies[i].hp<=0)kill_enemy(&enemies[i]);
}
static int foot_open(int x,int y){int a,b;if(clear_box(x-4,y-4,x+4,y+4))return 1;
 for(b=-4;b<=4;b++)for(a=-4;a<=4;a++)if(blocked(x+a,y+b))return 0;
 return 1;
}
/* Full swept9x9 foot; each one-pixel step rechecks walls, player and actors. */
static void push(unsigned i){unsigned n,j;int x,y;if(!ordinary(i)||!foot_open(enemies[i].x,enemies[i].y))return;
 for(n=0;n<8;n++){int ok=1;x=enemies[i].x+dx[horizons_power_direction];y=enemies[i].y+dy[horizons_power_direction];
  if(!foot_open(x,y)||!clear(enemies[i].x,enemies[i].y,x,y)||(ab(px-x)<9&&ab(py-y)<9))break;
  for(j=0;j<6;j++)if(j!=i&&enemies[j].hp>0&&ab(enemies[j].x-x)<9&&ab(enemies[j].y-y)<9)ok=0;
  if(!ok)break;
  enemies[i].x=x;enemies[i].y=y;
 }
}
static void combat(void){unsigned i;for(i=0;i<6;i++){int f,z,pf,pz;if(!bound(i)||(cast.hits&(1u<<i))||!contains(enemies[i].x,enemies[i].y,DAMAGE))continue;
 if(horizons_power_kind==120){if(!ordinary(i))continue;local(enemies[i].x,enemies[i].y,&f,&z);local(cast.previous[i].x,cast.previous[i].y,&pf,&pz);
  if(!((pf<24&&f>=24)||(pf>24&&f<=24))||ab(z)>12||ab(pz)>12||dist(cast.previous[i].x,cast.previous[i].y,enemies[i].x,enemies[i].y)>8||!clear(cast.previous[i].x,cast.previous[i].y,enemies[i].x,enemies[i].y))continue;
 }
 hurt(i);
 if(horizons_power_kind==110)push(i);
 if(horizons_power_kind==117&&ordinary(i)&&enemy_stagger_ticks[i]<18)enemy_stagger_ticks[i]=18;
 if(horizons_power_kind==120&&ordinary(i)&&!slowed_enemies[i])slowed_enemies[i]=18;
}}
int horizons_powers_intercept_shot(unsigned i,int x,int y,int tx,int ty,int eligible){int f,z,tf,tz,ax,ay,sx,sy,e,n=0;Shot*shot;
 if(!eligible||i>=12||!window()||cast.dirty||cast.guard_used||cast.released||(horizons_power_kind!=109&&horizons_power_kind!=115))return 0;
 shot=&shots[i];if(!coord(x,y)||!coord(tx,ty)||shot->dx < -8||shot->dx>8||shot->dy < -8||shot->dy>8)return 0;
 if(!shot->life||!shot->owner||shot->x!=x||shot->y!=y||tx!=x+shot->dx||ty!=y+shot->dy||dist(x,y,tx,ty)>8||!cast.shot_serial[i])return 0;
 local(x,y,&f,&z);local(tx,ty,&tf,&tz);if(tf>=f||f<10||!clear(x,y,tx,ty))return 0;
 ax=ab(tx-x);ay=-ab(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;e=ax+ay;
 for(;;){int q;if(contains(x,y,GUARD)){unsigned j;cast.guard_used=1;cast.caught_shot=(unsigned char)i;cast.caught_serial=cast.shot_serial[i];shot->life=0;impact(x,y);
   for(j=0;j<cast.count;j++)cast.marks[j].flags&=(unsigned char)~GUARD;
   return 1;}
  if((x==tx&&y==ty)||++n>8)break;
  q=e*2;if(q>=ay){e+=ay;x+=sx;}if(q<=ax){e+=ax;y+=sy;}
 }return 0;
}
int horizons_power(unsigned command){CreatureInstance*c;const CreatureAbility*a;const Spec*s;unsigned i,cd;
 if(command<106||command>121||ability_cd||horizons_power_time||hitstop||face<0||face>3||!coord(px,py)||blocked(px,py))return 0;
 c=progression_selected();a=creatures_ability(command);s=&specs[command-106];
 if(!c||!creatures_instance_validate(c)||c->selected_command>=2||c->equipped[c->selected_command]!=command||!creatures_command_learned(c->form_id,c->level,command)||!a||a->phase!=s->phase||a->cooldown_updates!=s->cooldown)return 0;
 if(!northern_powers_tiles_claim(NORTHERN_TILES_HORIZONS))return 0;
 collision.valid=0;horizons_power_kind=(int)command;horizons_power_form=c->form_id;horizons_power_direction=face;horizons_power_phase=a->phase;
 horizons_power_origin_x=px;horizons_power_origin_y=py;horizons_power_age=0;horizons_power_time=s->startup+s->active+s->settle;horizons_power_cast_time=s->startup;
 cast.caster=c->instance_id;cast.lease=northern_powers_tiles_generation();cast.token=(unsigned)(room-62)<16u?field_world_action_begin(3):0;
 cast.count=cast.hits=cast.fields[0]=cast.fields[1]=cast.revoked=cast.aimed=cast.art_live=0;
 cast.released=cast.release_age=cast.guard_used=cast.moving=cast.stopped=0;cast.side=-1;cast.caught_shot=12;
 for(i=0;i<6;i++){cast.bound_serial[i]=cast.serial[i];cast.previous[i].x=(short)enemies[i].x;cast.previous[i].y=(short)enemies[i].y;}
 cd=game_power_cooldown(s->cooldown);if(cd<s->cooldown-GAME_MAX_POWER_RECOVERY)cd=s->cooldown-GAME_MAX_POWER_RECOVERY;if(cd>s->cooldown)cd=s->cooldown;
 horizons_power_cooldown=ability_cd=ability_max=(int)cd;
 obj_upload(horizons_power_marks[command-106],16,16,GFX_OBJ_POWER_PIN);obj_upload(horizons_power_particles[command-106][0],8,8,GFX_OBJ_WATER_DROP);geometry();sfx(2);return 1;
}
void horizons_powers_tick(void){const Spec*s;unsigned i;int x,y,r;if(hitstop)return;
 if(horizons_power_cast_time)horizons_power_cast_time--;
 if(!horizons_power_time)return;
 if(!active()||!(s=spec())){finish();return;}
 horizons_power_age++;
 /* Max24 stamps and6 enemies; no roster scan, allocation or mutable save. */
 geometry();
 if(window()){
  if(!cast.art_live){obj_upload(horizons_power_particles[horizons_power_kind-106][0],8,8,GFX_OBJ_POWER_PIN);obj_upload(horizons_power_particles[horizons_power_kind-106][1],8,8,GFX_OBJ_WATER_DROP);cast.art_live=1;}
  combat();
  if(cast.token&&!cast.revoked&&same_selected())for(i=0;i<8;i++){unsigned beat=cast.beat==2?1u:0u;
   if(cast.fields[beat]&(1u<<i))continue;
   if(!field_world_target(i,&x,&y,&r))break;
   if(horizons_powers_overlap(x,y,r)&&field_world_hit(i,(unsigned)horizons_power_kind,cast.caster,(unsigned)horizons_power_form,cast.token))cast.fields[beat]|=(unsigned char)(1u<<i);
   if(cast.dirty)break;
  }
 }
 for(i=0;i<6;i++){cast.previous[i].x=(short)enemies[i].x;cast.previous[i].y=(short)enemies[i].y;}
 if(--horizons_power_time==0)finish();
}
void horizons_powers_draw(void){unsigned i;if(!active()||cast.dirty)return;
 if(!cast.art_live)obj_add(GFX_OBJ_POWER_PIN,horizons_power_origin_x-8,horizons_power_origin_y-25,16,16,1,horizons_power_origin_y+2,0);
 for(i=0;i<cast.count;i++){Mark*m=&cast.marks[i];obj_add(cast.art_live&&!m->flags?GFX_OBJ_POWER_PIN:GFX_OBJ_WATER_DROP,m->x-3,m->y-3,8,8,1,m->y+2,0);}
}
