/* Twenty-four original Underwater signatures. One instance-bound cast, ROM
 * code, bounded geometry and no allocation. Synthetic host tests are not a
 * controller acquisition or full-engine cadence claim. */
#include "underwater_powers.h"
#include "underwater_power_art.h"
#include "underwater_game.h"
#include "northern_powers.h"
#include "progression.h"
#include "gear_runtime.h"
#include "combat_rules.h"
#include "obj_layout.h"
typedef struct {int x,y,hp,flash,kind;} Enemy;
extern Enemy enemies[6];
extern volatile int px,py;
extern int face,ability_cd,ability_max,hitstop;
extern int solid(int,int);
extern void kill_enemy(Enemy*),impact(int,int),sfx(int);
extern void obj_upload(const unsigned char*,int,int,int);
extern void obj_add(int,int,int,int,int,int,int,int);
int underwater_power_kind,underwater_power_time,underwater_power_form;
int underwater_power_direction,underwater_power_origin_x,underwater_power_origin_y;
int underwater_power_age,underwater_power_cooldown,underwater_power_cast_time,underwater_power_phase;
typedef struct {unsigned char startup,active,lifetime,cooldown,damage,phase;} Spec;
static const Spec specs[24]={
 {12,18,36,90,16,4},{14,12,38,120,24,4},{16,24,48,120,24,4},
 {12,6,28,90,16,2},{14,32,54,120,24,2},{16,20,48,120,24,2},
 {12,20,40,90,16,0},{16,18,44,120,24,0},{16,24,48,120,24,0},
 {12,28,44,90,16,3},{14,132,154,180,24,3},{18,4,34,120,24,3},
 {12,16,36,90,16,1},{16,24,50,120,24,1},{12,24,56,120,24,1},
 {12,15,38,90,16,0},{16,16,44,120,24,0},{16,18,46,120,24,0},
 {12,24,44,90,16,3},{16,14,42,120,24,3},{18,24,52,120,24,3},
 {12,16,36,90,16,4},{18,24,52,120,24,4},{20,4,38,120,24,4}
};
/* kind0 raster stroke with Manhattan radius, kind1 axis-aligned cell in
 * WORLD coordinates, kind2 harmless outline. No invisible inflated hitbox. */
typedef struct {short x,y,tx,ty;unsigned char radius,kind,live,open;} Segment;
typedef struct {short x,y;} Point;
typedef struct {
 Segment seg[12];Point marks[24],previous[6],trail[4];
 unsigned caster,lease,token;
 unsigned short serial[6],caught_serial;
 short entry_x,entry_y,crawl_x,crawl_y,field_x,field_y,box_x0,box_y0,box_x1,box_y1;
 unsigned char count,mark_count,hits,fields,caught,catch_age,spent,choice,aimed;
 unsigned char dirty,geometry_key,art_live,boss_hit,stopped,crawl_mode,crawl_steps,trail_count;
 signed char side;
 unsigned char ink,path_checked,field_radius,field_valid,field_result,box_known,box_open;
 /* Exact per-pixel memoization in the central16x16 square: two bits/pixel,
  * zero unknown, one empty, two solid. Invalidated on every collision edit. */
 unsigned char collision[64];
} Cast;
static Cast cast;
typedef char underwater_cast_budget[(sizeof(Cast)+10*sizeof(int)<=512)?1:-1];
static const signed char dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};
/* quarter circle in Q4, inclusive endpoints, generated from original geometry */
static const signed char quarter[19][2]={{16,0},{16,1},{16,3},{15,4},{15,5},{15,7},{14,8},{13,9},{12,10},{11,11},{10,12},{9,13},{8,14},{7,15},{5,15},{4,15},{3,16},{1,16},{0,16}};
#include "underwater_tip_orbit.inc"
static int abs_i(int x){return x<0?-x:x;}
static int distance(int x,int y,int tx,int ty){return abs_i(x-tx)+abs_i(y-ty);}
static int coord(int x,int y){return x>=0&&y>=0&&x<=1023&&y<=1023;}
static int in_clear_box(int x,int y){return cast.box_open&&x>=cast.box_x0&&x<=cast.box_x1&&y>=cast.box_y0&&y<=cast.box_y1;}
static int blocked(int x,int y){unsigned xx=(unsigned)(x-underwater_power_origin_x+8),yy=(unsigned)(y-underwater_power_origin_y+8),p,b,v;
 if(in_clear_box(x,y))return 0;
 if(xx>=16||yy>=16)return solid(x,y);
 p=xx+yy*16;b=(p&3)*2;v=(cast.collision[p>>2]>>b)&3;
 if(v)return v==2;
 v=solid(x,y)?2u:1u;cast.collision[p>>2]|=(unsigned char)(v<<b);return v==2;
}
/* Endpoint-inclusive supercover; two side cells prevent diagonal corner leaks.
 * Every loop is bounded by validated Manhattan distance<=160. */
static int clear(int x,int y,int tx,int ty){int ax,ay,sx,sy,e;
 if(!coord(x,y)||!coord(tx,ty)||distance(x,y,tx,ty)>160)return 0;
 if(in_clear_box(x,y)&&in_clear_box(tx,ty))return 1;
 /* An obstacle elsewhere in the cast's broad bounds must not force every
  * unrelated ray back through hundreds of repeated world pixel queries. */
 if(distance(x,y,tx,ty)>8&&underwater_game_clear_box(x<tx?x:tx,y<ty?y:ty,x>tx?x:tx,y>ty?y:ty))return 1;
 if(blocked(x,y)||blocked(tx,ty))return 0;
 if(x==tx){sy=y<ty?1:-1;while(y!=ty){y+=sy;if(blocked(x,y))return 0;}return 1;}
 if(y==ty){sx=x<tx?1:-1;while(x!=tx){x+=sx;if(blocked(x,y))return 0;}return 1;}
 ax=abs_i(tx-x);ay=-abs_i(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;e=ax+ay;
 while(x!=tx||y!=ty){int twice=e*2,nx=x,ny=y;
  if(twice>=ay){e+=ay;nx+=sx;}if(twice<=ax){e+=ax;ny+=sy;}
  if(nx!=x&&ny!=y&&(blocked(nx,y)||blocked(x,ny)))return 0;
  x=nx;y=ny;if(blocked(x,y))return 0;
 }return 1;
}
static void world(int f,int s,int*x,int*y){int d=underwater_power_direction;
 *x=underwater_power_origin_x+f*dx[d]-s*dy[d];*y=underwater_power_origin_y+f*dy[d]+s*dx[d];}
static void local(int x,int y,int*f,int*s){int d=underwater_power_direction;
 x-=underwater_power_origin_x;y-=underwater_power_origin_y;*f=x*dx[d]+y*dy[d];*s=-x*dy[d]+y*dx[d];}
static int connected(int x,int y){return clear(underwater_power_origin_x,underwater_power_origin_y,x,y);}
static const Spec*spec(void){return underwater_power_kind>=67&&underwater_power_kind<=90?&specs[underwater_power_kind-67]:0;}
static int active(void){return underwater_power_time>0&&cast.lease==northern_powers_tiles_generation()&&northern_powers_tiles_owner()==NORTHERN_TILES_UNDERWATER;}
static int window(void){const Spec*s=spec();return active()&&s&&underwater_power_age>=s->startup&&underwater_power_age<s->startup+s->active;}
int underwater_powers_busy(void){return underwater_power_time>0;}
int underwater_powers_cast_matches_selected(void){CreatureInstance*c=progression_selected();return c&&(c->flags&CREATURE_OCCUPIED)&&cast.caster&&c->instance_id==cast.caster&&c->form_id==underwater_power_form;}
static int same_selected(void){CreatureInstance*c=progression_selected();return underwater_powers_cast_matches_selected()&&c->selected_command<2&&c->equipped[c->selected_command]==underwater_power_kind;}
int underwater_powers_companion_pose(void){const Spec*s=spec();
 if(!active()||!s||!same_selected())return -1;
 if(underwater_power_age<s->startup)return 0;
 if(underwater_power_age<s->startup+4)return 1;
 if(underwater_power_age<s->startup+10)return 2;
 return -1;
}
static int ordinary(unsigned i){return i<6&&enemies[i].hp>0&&(unsigned)enemies[i].kind<=2&&coord(enemies[i].x,enemies[i].y);}
static void finish(void){underwater_power_time=0;northern_powers_tiles_release(NORTHERN_TILES_UNDERWATER);cast.mark_count=cast.count=0;}
void underwater_powers_reset(void){unsigned i;finish();underwater_power_kind=underwater_power_form=underwater_power_direction=0;
 underwater_power_origin_x=underwater_power_origin_y=underwater_power_age=underwater_power_cooldown=underwater_power_cast_time=underwater_power_phase=0;
 /* Engine cooldown deliberately survives this reset. Death/entry may clear it
  * according to engine rules, but selecting an individual must never do so. */
 for(i=0;i<sizeof cast;i++)((unsigned char*)&cast)[i]=0;
 cast.caught=6;cast.side=-1;}
void underwater_powers_enemy_spawn(unsigned i){if(i>=6)return;cast.serial[i]++;
 if(underwater_power_time)cast.hits|=(unsigned char)(1u<<i);
 if(cast.caught==i){cast.caught=6;cast.spent=1;}
 cast.previous[i].x=(short)enemies[i].x;cast.previous[i].y=(short)enemies[i].y;
}
void underwater_powers_geometry_changed(void){cast.dirty=1;cast.field_valid=0;cast.path_checked=0;cast.box_known=cast.box_open=0;{unsigned i;for(i=0;i<sizeof cast.collision;i++)cast.collision[i]=0;}}
void underwater_powers_selection_changed(void){if(underwater_power_time){cast.fields=255;cast.aimed=1;
 if(underwater_power_kind==81)cast.stopped=1;}}
static void mark(int x,int y){if(cast.mark_count<24&&coord(x,y)&&!blocked(x,y)){
 cast.marks[cast.mark_count].x=(short)(x|(cast.ink?2048:0));cast.marks[cast.mark_count++].y=(short)y;}}
static void local_mark(int f,int s){int x,y;world(f,s,&x,&y);if(connected(x,y))mark(x,y);}
/* Clips a visible/damaging stroke at its first obstacle. parent_ok is supplied
 * by the exact preceding polyline legs, never just an endpoint beyond a wall. */
static void stroke_world(int x,int y,int tx,int ty,unsigned radius,unsigned live,int parent_ok,unsigned kind){
 Segment*p;int ax,ay,sx,sy,e,n=0;
 if(cast.count>=12||!parent_ok||!coord(x,y)||!coord(tx,ty)||distance(x,y,tx,ty)>96||blocked(x,y))return;
 p=&cast.seg[cast.count++];p->x=(short)x;p->y=(short)y;p->tx=(short)x;p->ty=(short)y;
 cast.ink=(unsigned char)!live;
 p->radius=(unsigned char)radius;p->kind=(unsigned char)kind;p->live=(unsigned char)live;p->open=1;
 ax=abs_i(tx-x);ay=-abs_i(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;e=ax+ay;
 for(;;){int twice,nx=x,ny=y;if((n&3)==0)mark(x,y);p->tx=(short)x;p->ty=(short)y;
  if(x==tx&&y==ty)break;
  twice=e*2;if(twice>=ay){e+=ay;nx+=sx;}if(twice<=ax){e+=ax;ny+=sy;}
  if((nx!=x&&ny!=y&&(blocked(nx,y)||blocked(x,ny)))||blocked(nx,ny))break;
  x=nx;y=ny;n++;
 }
}
static void stroke(int f,int s,int tf,int ts,unsigned radius,unsigned live){int x,y,tx,ty;world(f,s,&x,&y);world(tf,ts,&tx,&ty);stroke_world(x,y,tx,ty,radius,live,connected(x,y),0);}
static void rectangle(int f0,int f1,int s0,int s1,unsigned live){Segment*p;int x,y,tx,ty,cx,cy;
 if(cast.count>=12||f0>f1||s0>s1)return;
 world(f0,s0,&x,&y);world(f1,s1,&tx,&ty);world((f0+f1)/2,(s0+s1)/2,&cx,&cy);
 if(!connected(cx,cy))return;
 p=&cast.seg[cast.count++];p->x=(short)(x<tx?x:tx);p->tx=(short)(x>tx?x:tx);
 p->y=(short)(y<ty?y:ty);p->ty=(short)(y>ty?y:ty);p->radius=0;p->kind=1;p->live=(unsigned char)live;p->open=1;cast.ink=(unsigned char)!live;
 mark(p->x,p->y);mark(p->tx,p->y);mark(p->tx,p->ty);mark(p->x,p->ty);if(live)mark(cx,cy);
}
static void cell(int f,int s,int width,int height,unsigned live){rectangle(f-width/2,f+(width-1)/2,s-height/2,s+(height-1)/2,live);}
static int on_segment(const Segment*p,int x,int y){int ax,ay,sx,sy,e,pxx=p->x,pyy=p->y,r=p->radius;
 if(!p->live||!p->open)return 0;
 if(p->kind==1)return x>=p->x&&x<=p->tx&&y>=p->y&&y<=p->ty&&connected(x,y);
 if(x<(p->x<p->tx?p->x:p->tx)-r||x>(p->x>p->tx?p->x:p->tx)+r||
 y<(p->y<p->ty?p->y:p->ty)-r||y>(p->y>p->ty?p->y:p->ty)+r)return 0;
 ax=abs_i(p->tx-pxx);ay=-abs_i(p->ty-pyy);sx=pxx<p->tx?1:-1;sy=pyy<p->ty?1:-1;e=ax+ay;
 for(;;){int twice;if(distance(pxx,pyy,x,y)<=r&&clear(pxx,pyy,x,y))return 1;if(pxx==p->tx&&pyy==p->ty)return 0;
  twice=e*2;if(twice>=ay){e+=ay;pxx+=sx;}if(twice<=ax){e+=ax;pyy+=sy;}}
}
static int filled(int f,int s,int t){int q=f-24,z=s*cast.side;
 switch(underwater_power_kind){
 case 78:return f>=12&&f<36&&s>=-14&&s<14&&!(z>=-11&&z<-5&&f>=17&&f<27)&&!(z>=4&&z<10&&f>=21&&f<31);
 case 89:if(abs_i(q)>14||abs_i(s)>14||abs_i(q-z)<=3)return 0;return t<12?q-z>3:q-z< -3;
 case 90:q*=cast.side;if(q< -10||q>24||abs_i(s)*34>18*(24-q))return 0;return abs_i(f-24)>=3||abs_i(s)>=3;
 default:return 0;
 }
}
static int triangle_open(void){int x,y;world(24+cast.side*24,0,&x,&y);if(!connected(x,y))return 0;
 world(24-cast.side*10,-18,&x,&y);if(!connected(x,y))return 0;world(24-cast.side*10,18,&x,&y);return connected(x,y);}
static int contains(int x,int y){unsigned i;int f,s,t;const Spec*sp=spec();if(cast.dirty||!window()||!coord(x,y)||!sp)return 0;
 t=underwater_power_age-sp->startup;
 if(underwater_power_kind==78||underwater_power_kind==89||underwater_power_kind==90){
  local(x,y,&f,&s);return filled(f,s,t)&&connected(x,y)&&(underwater_power_kind!=90||!cast.stopped);}
 for(i=0;i<cast.count;i++)if(on_segment(&cast.seg[i],x,y))return 1;
 return 0;
}
/* Field rings are the exact enclosed octagon drawn by ring(): square radius
 * r with corners bevelled to (r,3). Enemies and bosses still use point tests.
 * Intersections must belong to the real clipped shape AND see the field center;
 * target size cannot authorize a pixel inside a stencil hole or across a wall. */
static int field_point(const Segment*p,int x,int y,int tx,int ty,int radius){int a=abs_i(x-tx),b=abs_i(y-ty),f,l,t;
 if(a>radius||b>radius||a+b>radius+3)return 0;
 if(p){if(!on_segment(p,x,y))return 0;}
 else{local(x,y,&f,&l);t=underwater_power_age-spec()->startup;
  if(!filled(f,l,t)||!connected(x,y))return 0;}
 return clear(x,y,tx,ty);
}
static int field_box(const Segment*p,int tx,int ty,int radius,int x0,int y0,int x1,int y1){int x,y,nx,ny;
 if(x0<tx-radius)x0=tx-radius;
 if(y0<ty-radius)y0=ty-radius;
 if(x1>tx+radius)x1=tx+radius;
 if(y1>ty+radius)y1=ty+radius;
 if(x0>x1||y0>y1)return 0;
 nx=tx<x0?x0:tx>x1?x1:tx;ny=ty<y0?y0:ty>y1?y1:ty;
 if(field_point(p,nx,ny,tx,ty,radius))return 1;
 /* Try the target-center row first, avoiding a raster search through a
  * stencil's safe aperture before reaching either solid side of it. */
 for(x=x0;x<=x1;x++)if(x!=nx&&field_point(p,x,ny,tx,ty,radius))return 1;
 for(y=y0;y<=y1;y++)if(y!=ny)for(x=x0;x<=x1;x++)
  if(field_point(p,x,y,tx,ty,radius))return 1;
 return 0;
}
static __attribute__((noinline)) int field_stroke(const Segment*p,int tx,int ty,int radius){int x=p->x,y=p->y,ax=abs_i(p->tx-x),ay=-abs_i(p->ty-y);
 int sx=x<p->tx?1:-1,sy=y<p->ty?1:-1,e=ax+ay,r=p->radius;
 for(;;){int a,b,twice;
  if(abs_i(x-tx)<=radius+r&&abs_i(y-ty)<=radius+r&&distance(x,y,tx,ty)<=radius+3+r)
   for(a=-r;a<=r;a++)for(b=abs_i(a)-r;b<=r-abs_i(a);b++){
    int xx=x+a,yy=y+b,fx=abs_i(xx-tx),fy=abs_i(yy-ty);
    if(fx<=radius&&fy<=radius&&fx+fy<=radius+3&&clear(x,y,xx,yy)&&clear(xx,yy,tx,ty))return 1;
   }
  if(x==p->tx&&y==p->ty)return 0;
  twice=e*2;if(twice>=ay){e+=ay;x+=sx;}if(twice<=ax){e+=ax;y+=sy;}
 }
}
static __attribute__((noinline)) int field_overlap(int x,int y,int radius){unsigned i;int x0,y0,x1,y1;const Segment*p;
 if(cast.dirty||!window()||!coord(x,y)||radius<0||radius>10||blocked(x,y))return 0;
 if(underwater_power_kind==78||underwater_power_kind==89||underwater_power_kind==90){
  if(underwater_power_kind==90&&cast.stopped)return 0;
  /* Broad bounds only: field_point always checks the exact nonconvex stencil. */
  world(0,-18,&x0,&y0);world(48,18,&x1,&y1);
  return field_box(0,x,y,radius,x0<x1?x0:x1,y0<y1?y0:y1,x0>x1?x0:x1,y0>y1?y0:y1);
 }
 for(i=0;i<cast.count;i++){p=&cast.seg[i];if(!p->live||!p->open)continue;
  x0=p->x<p->tx?p->x:p->tx;x1=p->x>p->tx?p->x:p->tx;
  y0=p->y<p->ty?p->y:p->ty;y1=p->y>p->ty?p->y:p->ty;
  if(x0-p->radius>x+radius||x1+p->radius<x-radius||y0-p->radius>y+radius||y1+p->radius<y-radius)continue;
  if(p->kind==1){if(field_box(p,x,y,radius,x0,y0,x1,y1))return 1;}
  else if(field_stroke(p,x,y,radius))return 1;
 }
 return 0;
}
static int field_contains(int x,int y,int radius){int result;
 if(cast.dirty)return 0;
 if(cast.field_valid&&x==cast.field_x&&y==cast.field_y&&radius==cast.field_radius)return cast.field_result;
 result=field_overlap(x,y,radius);
 if(coord(x,y)&&radius>=0&&radius<=10){cast.field_x=(short)x;cast.field_y=(short)y;cast.field_radius=(unsigned char)radius;
  cast.field_result=(unsigned char)result;cast.field_valid=1;}
 return result;
}
static void hook_point(int p,int *f,int*s){if(p<=20){*f=p;*s=0;}else if(p<=32){*f=20;*s=(p-20)*cast.side;}else{*f=52-p;*s=12*cast.side;}}
static void zig_point(int p,int*f,int*s){if(p<=12){*f=p;*s=0;}else if(p<=24){*f=12;*s=(p-12)*cast.side;}else{*f=p-12;*s=12*cast.side;}}
/* Path identity is the cast itself. These tips never borrow a hostile/friendly
 * Shot slot, and cannot silently reflect/consume a different live projectile. */
static void path_tip(int p,int old,int zig){int f,s,of,os,x,y,tx,ty,j,pf=0,ps=0,ok=1;
 if(cast.path_checked){if(zig)zig_point(cast.path_checked,&pf,&ps);else hook_point(cast.path_checked,&pf,&ps);}
 for(j=cast.path_checked;j<=p;j++){int cf,cs,cx,cy,lx,ly;if(zig)zig_point(j,&cf,&cs);else hook_point(j,&cf,&cs);
  world(cf,cs,&cx,&cy);world(pf,ps,&lx,&ly);if(!clear(lx,ly,cx,cy)){ok=0;break;}pf=cf;ps=cs;}
 if(!ok){cast.stopped=1;return;}if(p>cast.path_checked)cast.path_checked=(unsigned char)p;if(zig){zig_point(p,&f,&s);zig_point(old,&of,&os);}else{hook_point(p,&f,&s);hook_point(old,&of,&os);}
 world(of,os,&x,&y);world(f,s,&tx,&ty);stroke_world(x,y,tx,ty,zig?3:1,1,1,0);
}
static int trace_total(void){unsigned i;int n=0;for(i=1;i<cast.trail_count;i++)n+=distance(cast.trail[i-1].x,cast.trail[i-1].y,cast.trail[i].x,cast.trail[i].y);return n;}
static void trace_at(int p,int*x,int*y){unsigned i;*x=cast.trail[cast.trail_count-1].x;*y=cast.trail[cast.trail_count-1].y;
 for(i=cast.trail_count-1;i>0&&p;i--){int tx=cast.trail[i-1].x,ty=cast.trail[i-1].y,step;
  for(step=0;step<12&&p&&(*x!=tx||*y!=ty);step++,p--){if(*x!=tx)*x+=*x<tx?1:-1;else *y+=*y<ty?1:-1;}}
}
static void record_trail(void){int x,y,i;Point*p;if(underwater_power_kind!=81||underwater_power_age>12||underwater_power_age%4||cast.trail_count>=4||!same_selected())return;
 p=&cast.trail[cast.trail_count-1];x=p->x;y=p->y;
 /* Bound recording to honest nearby positions. A warp does not author a line. */
 if(!coord(px,py)||distance(x,y,px,py)>24){cast.stopped=1;return;}
 for(i=0;i<12&&(x!=px||y!=py);i++){int nx=x,ny=y;if(abs_i(px-x)>=abs_i(py-y))nx+=px>x?1:-1;else ny+=py>y?1:-1;
  if(!clear(x,y,nx,ny))break;
  x=nx;y=ny;}
 cast.trail[cast.trail_count].x=(short)x;cast.trail[cast.trail_count++].y=(short)y;
}
/* Static warnings and their exact stencil do not need to retrace every ray
 * each hardware update. Cache only geometry; ages, hit tests and input continue.
 * Collision fingerprints invalidate this cache before any later hook. */
static unsigned geometry_key(void){const Spec*s=spec();int t;if(!s)return 255;
 t=underwater_power_age-s->startup;if(t>=s->active)return 255;
 if(underwater_power_kind==81){if(t<12)return cast.trail_count;return 64u+(unsigned)t;}
 if(underwater_power_kind==78||underwater_power_kind==90)return 1;
 if(t<0)return 0;
 switch(underwater_power_kind){
 case 69:return 1u+(unsigned)t/6u;
 case 70:return 1;
 case 71:case 77:return cast.caught<6?2:1;
 case 72:return 1u+(unsigned)t/5u;
 case 75:return 1u+(unsigned)t/8u;
 case 87:return 1u+(unsigned)t/6u;
 case 89:return 1u+(unsigned)t/12u;
 default:return 1u+(unsigned)t;
 }
}
/* Proof of an entirely empty rectangle makes every supercover wholly inside
 * it trivially clear. The world checks exact row bands and puzzle rectangles;
 * failure merely falls back to pixel tests. Bounds include the cast origin. */
static void certify_box(void){static const signed char bounds[24][4]={
 {0,40,-5,5},{0,49,-16,16},{0,48,-17,17},{0,30,-9,9},{0,35,-11,11},{0,30,-19,19},
 {0,22,-14,14},{0,38,-18,18},{0,38,-17,17},{0,18,-28,28},{0,35,-7,7},{0,36,-15,15},
 {0,34,-8,8},{-26,26,-26,26},{-38,38,-38,38},{-18,18,-18,18},{0,30,-25,25},{0,38,-11,11},
 {0,26,-14,14},{0,50,-22,22},{0,58,-18,18},{0,26,-14,14},{0,40,-16,16},{0,50,-20,20}};
 const signed char*b=bounds[underwater_power_kind-67];int x,y,xx,yy;
 if(cast.box_known)return;
 world(b[0],b[2],&x,&y);world(b[1],b[3],&xx,&yy);
 cast.box_x0=(short)(x<xx?x:xx);cast.box_x1=(short)(x>xx?x:xx);
 cast.box_y0=(short)(y<yy?y:yy);cast.box_y1=(short)(y>yy?y:yy);
 cast.box_open=(unsigned char)underwater_game_clear_box(cast.box_x0,cast.box_y0,cast.box_x1,cast.box_y1);cast.box_known=1;
}
static void geometry(void){const Spec*sp=spec();int t,live,j,k,f,s,a,b,x,y,tx,ty;if(!sp)return;
 certify_box();cast.count=cast.mark_count=0;cast.field_valid=0;cast.dirty=0;cast.geometry_key=(unsigned char)geometry_key();t=underwater_power_age-sp->startup;live=t>=0&&t<sp->active;cast.ink=(unsigned char)!live;
 if(t<0)t=0;
 if(t>=sp->active)return;
 switch(underwater_power_kind){
 case 67: /* warning brackets show the ONLY damaging range */
  if(!live){stroke(18,-4,18,4,0,0);stroke(30,-4,30,4,0,0);}else{
   f=t<9?(t+1)*4:36-(t-9)*4;cast.ink=1;local_mark(f,0);
   if(t>=9){a=f;b=f+4;if(a<18)a=18;if(b>30)b=30;if(a<=b)stroke(a,0,b,0,4,1);}}
  break;
 case 68:{static const signed char fold[12][2]={{14,14},{15,13},{16,12},{17,11},{18,9},{18,8},{19,7},{19,6},{20,4},{20,3},{20,1},{20,0}};
  a=fold[t][0];b=fold[t][1]*cast.side;stroke(28-a,b,28,0,1,live);stroke(28,0,28+a,-b,1,live);}break;
 case 69:for(j=0;j<4;j++){static const signed char corners[4][2]={{4,-12},{44,-12},{44,12},{4,12}};
  k=((t/6)+cast.choice)&3;if(!live||j==k)cell(corners[j][0],corners[j][1],8,8,live);}break;
 case 70:cell(24,0,12,16,live);break;
 case 71:stroke(14,-10,34,-10,0,0);stroke(34,-10,34,10,0,0);stroke(34,10,14,10,0,0);stroke(14,10,14,-10,0,0);
  if(cast.caught<6)mark(cast.entry_x,cast.entry_y);
  break;
 case 72:k=(t/5)&1;cell(24,-11,12,14,live&&(k==(cast.side<0?0:1)));cell(24,11,12,14,live&&(k==(cast.side<0?1:0)));break;
 case 73:if(!live){stroke(0,0,20,0,0,0);stroke(20,0,20,12*cast.side,0,0);stroke(20,12*cast.side,12,12*cast.side,0,0);}else if(!cast.stopped)path_tip((t+1)*2,t*2,0);break;
 case 74:k=live?(t*18)/17:0;f=quarter[k][0];s=quarter[k][1]*cast.side;
  world(20,0,&x,&y);world(20+(f*6)/16,(s*6)/16,&tx,&ty);
  if(!connected(x,y)||!clear(x,y,tx,ty))break;
  stroke(20+(f*6)/16,(s*6)/16,20+f,s,1,live);
  if(!live){stroke(20,0,36,0,0,0);stroke(20,0,20,16*cast.side,0,0);}break;
 case 75:for(j=0;j<3;j++)if(!live||j==t/8)cell(12+j*12,((j&1)?-10:10)*cast.side,4,12,live);break;
 case 76:if(!live){stroke(0,0,16,0,0,0);stroke(16,0,16,24*cast.side,0,0);}else if(!cast.stopped){
  int nx=cast.crawl_x,ny=cast.crawl_y;int vx=dx[underwater_power_direction],vy=dy[underwater_power_direction];
  local(nx,ny,&f,&s);world(f,0,&x,&y);
  if(!connected(x,y)||!clear(x,y,nx,ny)){cast.stopped=1;break;}
  if(!cast.crawl_mode){if(t<16){tx=nx+vx;ty=ny+vy;if(clear(nx,ny,tx,ty)){cast.crawl_x=(short)tx;cast.crawl_y=(short)ty;}else cast.crawl_mode=1;}
   else cast.stopped=1;}
  if(cast.crawl_mode){/* Wall must stay immediately forward; convex corners stop. */
   if(cast.crawl_steps>=24||!blocked(cast.crawl_x+vx,cast.crawl_y+vy)){cast.stopped=1;break;}
   tx=cast.crawl_x-vy*cast.side;ty=cast.crawl_y+vx*cast.side;
   if(!clear(cast.crawl_x,cast.crawl_y,tx,ty)||!blocked(tx+vx,ty+vy)){cast.stopped=1;break;}
   cast.crawl_x=(short)tx;cast.crawl_y=(short)ty;cast.crawl_steps++;}
  stroke_world(nx,ny,cast.crawl_x,cast.crawl_y,3,1,1,0);
 }break;
 case 77:stroke(15,-6,33,-6,0,0);stroke(15,6,33,6,0,0);if(cast.caught<6)cell(24,0,2,2,0);break;
 case 78:case 89:case 90:
  if(underwater_power_kind==90&&!triangle_open())cast.stopped=1;
  /* Boundary samples fit the24-object budget and leave every aperture clear.
   * Active interior stipples use the exact predicate, never a full-square tile. */
  if(underwater_power_kind==78){
   for(a=12;a<=35;a+=11){local_mark(a,-14);local_mark(a,13);}
   for(b=-7;b<=7;b+=7){local_mark(12,b);local_mark(35,b);}
   local_mark(16,-11*cast.side);local_mark(27,-11*cast.side);local_mark(16,-5*cast.side);local_mark(27,-5*cast.side);
   local_mark(20,4*cast.side);local_mark(31,4*cast.side);local_mark(20,10*cast.side);local_mark(31,10*cast.side);
  }else if(underwater_power_kind==89){
   for(a=10;a<=38;a+=14)for(b=-14;b<=14;b+=14)if(filled(a,b,t))local_mark(a,b);
   for(a=12;a<=36;a+=6){b=(a-24+(t<12?-4:4))*cast.side;if(abs_i(b)<=14)local_mark(a,b);}
  }else if(!cast.stopped){
   local_mark(24+24*cast.side,0);local_mark(24-10*cast.side,-18);local_mark(24-10*cast.side,18);
   for(j=1;j<4;j++){local_mark(24+(24-j*8)*cast.side,-j*4);local_mark(24+(24-j*8)*cast.side,j*4);}
   local_mark(24-10*cast.side,-6);local_mark(24-10*cast.side,6);
   local_mark(20,-4);local_mark(20,4);local_mark(28,-4);local_mark(28,4);
  }
  if(live&&underwater_power_kind==89)for(a=16;a<=32;a+=8)for(b=-8;b<=8;b+=8)if(filled(a,b,t)&&cast.mark_count<24&&!(underwater_power_kind==90&&cast.stopped))local_mark(a,b);
  break;
 case 79:{static const signed char wave[17]={0,2,3,5,6,5,3,2,0,-2,-3,-5,-6,-5,-3,-2,0};
  if(!live){for(j=0;j<4;j++)stroke(j*8,0,j*8+4,6*cast.side*(j&1?-1:1),0,0);}else if(!cast.stopped){
   int ok=1;for(j=cast.path_checked;j<(t+1)*2;j++){world(j,wave[j&15]*cast.side,&x,&y);world(j+1,wave[(j+1)&15]*cast.side,&tx,&ty);if(!clear(x,y,tx,ty)){ok=0;break;}}
   if(!ok)cast.stopped=1;else {cast.path_checked=(unsigned char)((t+1)*2);stroke(t*2,wave[(t*2)&15]*cast.side,(t+1)*2,wave[((t+1)*2)&15]*cast.side,1,1);}}}
  break;
 case 80:k=t<12?1:-1;a=t<12?4+(t*8)/11:8+((t-12)*16)/11;
  for(j=0;j<3;j++){int n=j*6,m=n+6;stroke(k*quarter[n][0]*a/16,cast.side*k*quarter[n][1]*a/16,k*quarter[m][0]*a/16,cast.side*k*quarter[m][1]*a/16,1,live);}break;
 case 81:if(!live||t<12){for(j=1;j<cast.trail_count;j++)stroke_world(cast.trail[j-1].x,cast.trail[j-1].y,cast.trail[j].x,cast.trail[j].y,0,0,1,2);}
  else if(!cast.stopped){a=trace_total();if(!a)cell(0,0,8,8,1);else{j=(t-12)*3;k=j+3;if(j>a)j=a;if(k>a)k=a;trace_at(j,&x,&y);trace_at(k,&tx,&ty);
    if(clear(x,y,tx,ty))stroke_world(x,y,tx,ty,1,1,1,0);else cast.stopped=1;}}break;
 case 82:k=live?t+1:0;for(j=0;j<5;j++){f=underwater_tip_orbit[k][j][0];s=underwater_tip_orbit[k][j][1]*cast.side;cell(f,s,4,4,live);}break;
 case 83:a=live?6+(t*18)/15:24;b=live?6+(t*6)/15:12;if(cast.side>0){k=a;a=b;b=k;}
  rectangle(14,17,-a,-5,live);rectangle(14,17,4,a-1,live);rectangle(16-b,11,-2,1,live);rectangle(20,15+b,-2,1,live);break;
 case 84:k=live?t:0;a=12-(k*4)/17;b=(k*9)/17*cast.side;f=s=0;
  for(j=0;j<3;j++){int nf=f+a,ns=s+((j&1)?-b:b);world(f,s,&x,&y);world(nf,ns,&tx,&ty);
   if(!clear(x,y,tx,ty))break;
   if(!live)stroke(f,s,nf,ns,0,0);else cell(nf,ns,2,2,1);f=nf;s=ns;}
  if(live){f=s=0;for(j=0;j<3;j++){int nf=f+a,ns=s+((j&1)?-b:b);world(f,s,&x,&y);world(nf,ns,&tx,&ty);if(!clear(x,y,tx,ty))break;stroke(f,s,nf,ns,0,0);f=nf;s=ns;}}break;
 case 85:if(!live){stroke(0,0,12,0,0,0);stroke(12,0,12,cast.side*12,0,0);stroke(12,cast.side*12,24,cast.side*12,0,0);}else if(!cast.stopped){
  k=(t%12)*3;if((t/6)&1){a=36-k;b=a-3;if(b<0)b=0;path_tip(a,b,1);}else path_tip(k+3,k,1);
  zig_point(36-k,&f,&s);cast.ink=1;local_mark(f,s);}break;
 case 86:k=live?(t*18)/13:0;stroke(28,0,28+(quarter[k][0]*20)/16,(quarter[k][1]*20)/16*cast.side,1,live);
  if(!live)stroke(28,0,28,20*cast.side,0,0);
  break;
 case 87:cast.ink=1;for(b=0;b<2;b++)for(j=0;j<8;j++){static const signed char ring[8][2]={{16,0},{11,11},{0,16},{-11,11},{-16,0},{-11,-11},{0,-16},{11,-11}};
  k=(((t/12)&1)^(cast.side>0));if(live&&b!=k&&(j&1))continue;
  a=b?16:10;f=b?40:14;local_mark(f+ring[j][0]*a/16,ring[j][1]*a/16);}
  cell(24,0,8,8,live&&(t%12>=6));break;
 case 88:a=live?((t+1)*3)/2:0;b=live?(t*3)/2:0;
  if(!cast.stopped){for(j=0;j<4;j++){int sf=-11+j*6+(cast.side>0?3:0),n;for(n=b;n<=a;n++){world(n,sf,&x,&y);
    if(blocked(x,y)||blocked(x-dy[underwater_power_direction],y+dx[underwater_power_direction])||blocked(x+dy[underwater_power_direction],y-dx[underwater_power_direction]))cast.stopped=1;}}
   if(!cast.stopped)for(j=0;j<4;j++){int sf=-11+j*6+(cast.side>0?3:0);rectangle(b,a,sf-1,sf+1,live);}}
  break;
 }
}
static void hurt(unsigned i){const Spec*s=spec();if(!ordinary(i)||!s||(cast.hits&(1u<<i)))return;
 cast.hits|=(unsigned char)(1u<<i);game_enemy_hurt(i,s->damage,0,(unsigned)underwater_power_phase);
 enemies[i].flash=12;impact(enemies[i].x,enemies[i].y);if(enemies[i].hp<=0)kill_enemy(&enemies[i]);}
static void push(unsigned i,int tx,int ty,unsigned budget){unsigned j;if(!ordinary(i))return;
 for(j=0;j<budget;j++){int x=enemies[i].x,y=enemies[i].y,nx=x,ny=y;if(x==tx&&y==ty)break;
  if(abs_i(tx-x)>=abs_i(ty-y))nx+=tx>x?1:-1;else ny+=ty>y?1:-1;
  /* Radius-four enemy footprint, checked every pixel; never a teleport. */
  if(!clear(x,y,nx,ny)||blocked(nx-4,ny)||blocked(nx+4,ny)||blocked(nx,ny-4)||blocked(nx,ny+4))break;
  enemies[i].x=nx;enemies[i].y=ny;
 }
}
static int moved_honestly(unsigned i){return distance(cast.previous[i].x,cast.previous[i].y,enemies[i].x,enemies[i].y)<=24&&clear(cast.previous[i].x,cast.previous[i].y,enemies[i].x,enemies[i].y);}
static void catch_target(void){unsigned i;int f,s,pf,ps;if(cast.spent)return;
 if(cast.caught<6){i=cast.caught;if(!ordinary(i)||cast.serial[i]!=cast.caught_serial||!moved_honestly(i)||!connected(enemies[i].x,enemies[i].y)){cast.spent=1;cast.caught=6;return;}
  local(enemies[i].x,enemies[i].y,&f,&s);
  if(underwater_power_kind==71){if(abs_i(f-24)>14||abs_i(s)>14){cast.spent=1;return;}
   if(underwater_power_age-cast.catch_age>=8){hurt(i);push(i,cast.entry_x,cast.entry_y,8);cast.spent=1;}}
  else if(f<15&&abs_i(s)<=6){hurt(i);cast.spent=1;}else if(f>33||abs_i(s)>6)cast.spent=1;
  return;
 }
 for(i=0;i<6;i++)if(ordinary(i)&&!(cast.hits&(1u<<i))){
  local(enemies[i].x,enemies[i].y,&f,&s);local(cast.previous[i].x,cast.previous[i].y,&pf,&ps);
  if(underwater_power_kind==71){if(!(f>=14&&f<=34&&abs_i(s)<=10&&(pf<14||pf>34||abs_i(ps)>10)))continue;}
  else if(!(pf>33&&f<=33&&abs_i(s)<=6&&abs_i(ps)<=6))continue;
  if(!moved_honestly(i)||!connected(enemies[i].x,enemies[i].y))continue;
  cast.caught=(unsigned char)i;cast.caught_serial=cast.serial[i];cast.catch_age=(unsigned char)underwater_power_age;
  if(underwater_power_kind==71){
   int x=cast.previous[i].x,y=cast.previous[i].y,tx=enemies[i].x,ty=enemies[i].y;
   int ax=abs_i(tx-x),ay=-abs_i(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,e=ax+ay,n;
   /* Record the actual intersected entry edge, not an arbitrary old position. */
   for(n=0;n<=24;n++){int ef,es,twice;local(x,y,&ef,&es);
    if(ef>=14&&ef<=34&&abs_i(es)<=10)break;
    twice=e*2;if(twice>=ay){e+=ay;x+=sx;}if(twice<=ax){e+=ax;y+=sy;}}
   cast.entry_x=(short)x;cast.entry_y=(short)y;
  }else if(f<15){hurt(i);cast.spent=1;} /* Honest one-update traversal. */
  break;
 }
}
int underwater_powers_can_aim(void){return active()&&!hitstop&&!cast.aimed&&underwater_power_age<8&&same_selected()&&underwater_power_kind!=67&&underwater_power_kind!=71&&underwater_power_kind!=77&&underwater_power_kind!=81;}
unsigned underwater_powers_hint(void){if(!underwater_powers_can_aim())return 0;return underwater_power_kind==69?2:(underwater_power_kind==83||underwater_power_kind==90)?3:1;}
int underwater_powers_input(unsigned pressed){unsigned p=pressed&240u;if(!underwater_powers_can_aim()||!p||(p&(p-1)))return 0;
 if(underwater_power_kind==69)cast.choice=(unsigned char)(p==64?0:p==16?1:p==128?2:3);
 else if(underwater_power_kind==83||underwater_power_kind==90){if(p!=64&&p!=128)return 0;cast.side=p==64?1:-1;}
 else{if(p!=16&&p!=32)return 0;cast.side=p==16?1:-1;}
 cast.aimed=1;cast.dirty=1;return 1;
}
int underwater_power(unsigned command){CreatureInstance*c;const CreatureAbility*a;const Spec*s;unsigned i,cd;
 if(command<67||command>90||ability_cd||underwater_power_time||hitstop||face<0||face>3||!coord(px,py)||solid(px,py))return 0;
 c=progression_selected();a=creatures_ability(command);s=&specs[command-67];
 if(!c||!creatures_instance_validate(c)||c->selected_command>=2||c->equipped[c->selected_command]!=command||
 !creatures_command_learned(c->form_id,c->level,command)||!a||a->phase!=s->phase||a->cooldown_updates!=s->cooldown)return 0;
 if(!northern_powers_tiles_claim(NORTHERN_TILES_UNDERWATER))return 0;
 underwater_power_kind=(int)command;underwater_power_form=c->form_id;underwater_power_direction=face;
 underwater_power_origin_x=px;underwater_power_origin_y=py;underwater_power_phase=a->phase;underwater_power_age=0;
 underwater_power_time=s->lifetime;underwater_power_cast_time=s->startup;
 cast.caster=c->instance_id;cast.lease=northern_powers_tiles_generation();cast.token=underwater_game_action_begin(3);
 cast.hits=cast.fields=cast.spent=cast.choice=cast.aimed=cast.art_live=cast.boss_hit=cast.stopped=cast.crawl_mode=cast.crawl_steps=0;
 cast.path_checked=cast.box_known=cast.box_open=0;for(i=0;i<sizeof cast.collision;i++)cast.collision[i]=0;
 cast.caught=6;cast.side=-1;cast.crawl_x=(short)px;cast.crawl_y=(short)py;
 cast.trail_count=1;cast.trail[0].x=(short)px;cast.trail[0].y=(short)py;
 for(i=0;i<6;i++){cast.previous[i].x=(short)enemies[i].x;cast.previous[i].y=(short)enemies[i].y;}
 cd=game_power_cooldown(s->cooldown);if(cd<s->cooldown-8u)cd=s->cooldown-8u;if(cd>s->cooldown)cd=s->cooldown;
 underwater_power_cooldown=ability_cd=ability_max=(int)cd;
 obj_upload(underwater_power_marks[command-67],16,16,GFX_OBJ_POWER_PIN);
 obj_upload(underwater_power_particles[command-67][0],8,8,GFX_OBJ_WATER_DROP);geometry();sfx(2);return 1;
}
int underwater_powers_feedback(unsigned command){CreatureInstance*c;if(command<67||command>90||underwater_power_time||face<0||face>3)return 0;
 c=progression_selected();if(!c||!creatures_instance_validate(c)||!creatures_command_learned(c->form_id,c->level,command))return 0;
 underwater_power_cast_time=12;return 1;
}
void underwater_powers_tick(void){unsigned i;const Spec*s;int x,y,r;if(hitstop)return;
 if(underwater_power_cast_time)underwater_power_cast_time--;
 if(!underwater_power_time)return;
 if(!active()||!(s=spec())){finish();return;}
 underwater_power_age++;record_trail();if(cast.dirty||cast.geometry_key!=geometry_key())geometry();
 if(window()){
  cast.field_valid=0;
  if(!cast.art_live){obj_upload(underwater_power_particles[underwater_power_kind-67][0],8,8,GFX_OBJ_POWER_PIN);obj_upload(underwater_power_particles[underwater_power_kind-67][1],8,8,GFX_OBJ_WATER_DROP);cast.art_live=1;if(underwater_power_kind==78||underwater_power_kind==90)for(i=0;i<cast.mark_count;i++)cast.marks[i].x&=1023;}
  if(underwater_power_kind==71||underwater_power_kind==77)catch_target();
  else for(i=0;i<6;i++)if(ordinary(i)&&!(cast.hits&(1u<<i))&&contains(enemies[i].x,enemies[i].y)){
   hurt(i);if(underwater_power_kind==70){int d=underwater_power_direction;push(i,enemies[i].x-dy[d]*cast.side*6,enemies[i].y+dx[d]*cast.side*6,6);}}
  if(cast.token&&same_selected())for(i=0;i<8;i++){
   if(!underwater_game_field_target(i,&x,&y,&r))break;
   if(!(cast.fields&(1u<<i))&&field_contains(x,y,r)){int result=underwater_game_field_hit(i,(unsigned)underwater_power_kind,cast.caster,(unsigned)underwater_power_form,cast.token);
    if(result)cast.fields|=(unsigned char)(1u<<i);}}
  if(!cast.boss_hit&&cast.token&&underwater_game_target(&x,&y,&r)&&contains(x,y)){
   unsigned q=combat_damage_q4(s->damage,0,0,(unsigned)underwater_power_phase,COMBAT_NEUTRAL_PHASE,0);
   if(underwater_game_command_hit(x,y,q,cast.token))cast.boss_hit=1;}
 }
 for(i=0;i<6;i++){cast.previous[i].x=(short)enemies[i].x;cast.previous[i].y=(short)enemies[i].y;}
 if(--underwater_power_time==0)finish();
}
void underwater_powers_draw(void){unsigned i;if(!active())return;
 /* Dirty scenery is allowed to clip the cached display, never advance ages or
  * any moving tip. Rendering otherwise has zero collision/roster probes. */
 if(cast.dirty){cast.mark_count=0;return;}
 if(!cast.art_live)obj_add(GFX_OBJ_POWER_PIN,underwater_power_origin_x-8,underwater_power_origin_y-25,16,16,1,underwater_power_origin_y+2,0);
 for(i=0;i<cast.mark_count;i++){int x=cast.marks[i].x&1023;
  obj_add(cast.art_live&&(cast.marks[i].x&2048)?GFX_OBJ_POWER_PIN:GFX_OBJ_WATER_DROP,x-4,cast.marks[i].y-4,8,8,1,cast.marks[i].y+2,0);}

}
