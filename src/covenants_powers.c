/* Original finite legendary decisions. Only visible indexed pixels collide.
 * No heap, new timer/IRQ/DMA/audio, private cooldown, save writes or IWRAM. */
#include "covenants_powers.h"
#include "covenants_power_art.h"
#include "covenants_game.h"
#include "horizons_game.h"
#include "return_game.h"
#include "underwater_game.h"
#include "northern_powers.h"
#include "progression.h"
#include "gear_runtime.h"
#include "obj_layout.h"
#include "collision_rects.h"
#include "connected_road_region.h"
#include "north_art.h"
#include "south_art.h"
typedef struct { int x,y,hp,flash,kind; } Enemy;
typedef struct { int x,y,dx,dy,life,owner; } Shot;
extern Enemy enemies[6];
extern Shot shots[12];
extern volatile int px,py,room;
extern int face,ability_cd,ability_max,hitstop;
extern unsigned char slowed_enemies[6];
extern int solid(int,int),game_clear_box(int,int,int,int);
extern void kill_enemy(Enemy*),impact(int,int),sfx(int);
extern void obj_upload(const unsigned char*,int,int,int);
extern void obj_add(int,int,int,int,int,int,int,int);
int covenants_power_kind,covenants_power_time,covenants_power_form;
int covenants_power_direction,covenants_power_origin_x,covenants_power_origin_y;
int covenants_power_age,covenants_power_cooldown,covenants_power_cast_time,covenants_power_phase;
typedef struct { unsigned char startup,active,settle,cooldown,damage,phase; } Spec;
static const Spec specs[8] = {
    {6,136,6,240,24,4}, {6,90,6,180,32,0}, {6,60,6,210,48,1},
    {6,120,6,200,32,2}, {6,60,6,165,32,3}, {6,100,6,195,0,0},
    {6,48,6,180,32,4}, {6,120,6,240,32,1}
};
enum { DAMAGE=1,FIELD=2,GUARD=4,MARK_CAP=24,GEOMETRY_RECT_CAP=48,GEOMETRY_RADIUS=64 };
/* Signed local coordinates keep24 native pixel stamps in72 bytes. */
typedef struct { signed char f,s; unsigned char flags; } Mark;
typedef struct {
    CovenantsPowerProof proof;
    Mark marks[MARK_CAP];
    unsigned lease,caught_serial[3];
    unsigned short serial[6],bound_serial[6];
    short previous_x[6],previous_y[6];
    unsigned char count,hits,fields[2],revoked,dirty,art_live;
    unsigned char release_age,caught_count,caught_slot[3],spent,beat,moving,stopped,boss_hit;
} Cast;
typedef struct {
    short walls[GEOMETRY_RECT_CAP][4],x0,y0,x1,y1,area;
    unsigned char valid,count;
} Geometry;
static Cast cast;
static Geometry collision;
static unsigned action_serial;
typedef char covenants_power_budget[(sizeof(Cast)+sizeof(Geometry)+12*sizeof(int)<=768)?1:-1];
static const signed char dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};
static int ab(int x) { return x<0?-x:x; }
static int dist(int x,int y,int tx,int ty) { return ab(x-tx)+ab(y-ty); }
static int coord(int x,int y) { return x>=0&&y>=0&&x<=1023&&y<=1023; }
static int index_of(unsigned command) { return command==12?0:(command>=122&&command<=128?(int)command-121:-1); }
static const Spec *spec(void) { int i=index_of((unsigned)covenants_power_kind);return i<0?0:&specs[i]; }
static int active(void) {
    return covenants_power_time>0&&cast.lease==northern_powers_tiles_generation()&&
           northern_powers_tiles_owner()==NORTHERN_TILES_COVENANTS;
}
static int window(void) {
    const Spec *s=spec();
    return active()&&s&&covenants_power_age>=s->startup&&covenants_power_age<s->startup+s->active;
}
/* Same proven bounded exact rectangle representation as accepted Horizons C.
 * Failed fills are cached; no repeated full-room scans within a cast. */
static int geometry_snapshot(int x0,int y0,int x1,int y1) {
    int n;
    if(!collision.valid||collision.area!=room) {
        int ox=covenants_power_origin_x,oy=covenants_power_origin_y;
        collision.x0=(short)(ox>GEOMETRY_RADIUS?ox-GEOMETRY_RADIUS:0);
        collision.y0=(short)(oy>GEOMETRY_RADIUS?oy-GEOMETRY_RADIUS:0);
        collision.x1=(short)(ox<1023-GEOMETRY_RADIUS?ox+GEOMETRY_RADIUS:1023);
        collision.y1=(short)(oy<1023-GEOMETRY_RADIUS?oy+GEOMETRY_RADIUS:1023);
        collision.area=(short)room;collision.valid=2;collision.count=0;
        n=game_collision_rects(collision.x0,collision.y0,collision.x1,collision.y1,
                               collision.walls,GEOMETRY_RECT_CAP);
        if(n>=0&&(unsigned)n<=GEOMETRY_RECT_CAP) { collision.count=(unsigned char)n;collision.valid=1; }
    }
    return collision.valid==1&&x0>=collision.x0&&y0>=collision.y0&&x1<=collision.x1&&y1<=collision.y1;
}
static int clear_box(int x0,int y0,int x1,int y1) {
    unsigned i;
    if(x0>x1||y0>y1||!coord(x0,y0)||!coord(x1,y1))return 0;
    if(!geometry_snapshot(x0,y0,x1,y1))return game_clear_box(x0,y0,x1,y1);
    for(i=0;i<collision.count;i++) {
        const short *r=collision.walls[i];
        if(x1>=r[0]&&x0<=r[2]&&y1>=r[1]&&y0<=r[3])return 0;
    }
    return 1;
}
/* Exact Bresenham supercover tested against occupied horizontal slabs. */
static int rectangle_ray(int x,int y,int tx,int ty) {
    unsigned i,ax=(unsigned)ab(tx-x),ay=(unsigned)ab(ty-y);
    int sx=x<tx?1:-1,sy=y<ty?1:-1;
    int minx=x<tx?x:tx,maxx=x>tx?x:tx,miny=y<ty?y:ty,maxy=y>ty?y:ty;
    for(i=0;i<collision.count;i++) {
        const short *r=collision.walls[i];unsigned k,last,u,v;int low,high,left,right;
        if(maxx<r[0]||minx>r[2]||maxy<r[1]||miny>r[3])continue;
        low=r[1]>miny?r[1]:miny;high=r[3]<maxy?r[3]:maxy;
        k=(unsigned)(sy>0?low-y:y-high);last=(unsigned)(sy>0?high-y:y-low);
        if(!ay) { u=0;v=ax; }
        else if(ax<=ay) { u=((k?k-1:0)*ax+ay/2)/ay;v=((last<ay?last+1:last)*ax+ay/2)/ay; }
        else { u=k?(k*ax-ax/2+ay-1)/ay-1:0;v=last<ay?((last+1)*ax-ax/2+ay-1)/ay:ax; }
        left=x+sx*(int)u;right=x+sx*(int)v;
        if(left>right) { int swap=left;left=right;right=swap; }
        if(right>=r[0]&&left<=r[2])return 0;
    }
    return 1;
}
/* A complete13-pixel stamp shares one small cone. Reject unrelated rectangles
 * once for the entire cone, instead of scanning all48 rectangles13 times. */
static __attribute__((noinline)) int rectangle_stamp(int x,int y,int ox,int oy) {
    unsigned i;int a,b,l=x-2<ox?x-2:ox,r=x+2>ox?x+2:ox;
    int t=y-2<oy?y-2:oy,d=y+2>oy?y+2:oy;
    for(i=0;i<collision.count;i++) {
        const short *rect=collision.walls[i];
        if(r<rect[0]||l>rect[2]||d<rect[1]||t>rect[3])continue;
        for(b=-2;b<=2;b++)for(a=-2;a<=2;a++) {
            unsigned ax,ay,k,last,u,v;int tx=x+a,ty=y+b,sx,sy,minx,maxx,miny,maxy,low,high,left,right;
            if(ab(a)+ab(b)>2)continue;
            minx=ox<tx?ox:tx;maxx=ox>tx?ox:tx;miny=oy<ty?oy:ty;maxy=oy>ty?oy:ty;
            if(maxx<rect[0]||minx>rect[2]||maxy<rect[1]||miny>rect[3])continue;
            ax=(unsigned)ab(tx-ox);ay=(unsigned)ab(ty-oy);sx=ox<tx?1:-1;sy=oy<ty?1:-1;
            low=rect[1]>miny?rect[1]:miny;high=rect[3]<maxy?rect[3]:maxy;
            k=(unsigned)(sy>0?low-oy:oy-high);last=(unsigned)(sy>0?high-oy:oy-low);
            if(!ay) { u=0;v=ax; }
            else if(ax<=ay) { u=((k?k-1:0)*ax+ay/2)/ay;v=((last<ay?last+1:last)*ax+ay/2)/ay; }
            else { u=k?(k*ax-ax/2+ay-1)/ay-1:0;v=last<ay?((last+1)*ax-ax/2+ay-1)/ay:ax; }
            left=ox+sx*(int)u;right=ox+sx*(int)v;
            if(left>right) { int swap=left;left=right;right=swap; }
            if(right>=rect[0]&&left<=rect[2])return 0;
        }
    }
    return 1;
}
/* Exact fallback for dense North/South collision, without per-pixel solid(). */
static int old_rows_clear(int x,int y,int tx,int ty) {
    const unsigned short *rows,*bands,*b;
    unsigned width,height,offset,n,ax,ay,k=0,last,u,v,area=(unsigned)room;
    int sx=x<tx?1:-1,sy=y<ty?1:-1,left,right;
    if(area>=30u) {
        const SouthArtRoom *r=&south_art_rooms[area-30u];
        width=r->width;height=r->height;rows=r->collision_rows;bands=r->collision_bands;
    } else {
        const NorthArtRoom *r=&north_art_rooms[area-22u];
        width=r->width;height=r->height;rows=r->collision_rows;bands=r->collision_bands;
    }
    if((unsigned)x>=width||(unsigned)tx>=width||(unsigned)y>=height||(unsigned)ty>=height)return 0;
    ax=(unsigned)ab(tx-x);ay=(unsigned)ab(ty-y);
    for(;;) {
        offset=rows[y];last=k;
        while(last<ay&&rows[y+sy]==offset) { y+=sy;last++; }
        if(!ay) { u=0;v=ax; }
        else if(ax<=ay) { u=((k?k-1:0)*ax+ay/2)/ay;v=((last<ay?last+1:last)*ax+ay/2)/ay; }
        else { u=k?(k*ax-ax/2+ay-1)/ay-1:0;v=last<ay?((last+1)*ax-ax/2+ay-1)/ay:ax; }
        left=x+sx*(int)u;right=x+sx*(int)v;
        if(left>right) { int swap=left;left=right;right=swap; }
        b=bands+offset;n=*b++;
        while(n--) { if((unsigned)right<b[0])break;if((unsigned)left<b[1])return 0;b+=2; }
        if(last==ay)return 1;
        k=last+1;y+=sy;
    }
}
static int clear(int x,int y,int tx,int ty) {
    int result;
    if(!coord(x,y)||!coord(tx,ty)||dist(x,y,tx,ty)>128)return 0;
    if(geometry_snapshot(x<tx?x:tx,y<ty?y:ty,x>tx?x:tx,y>ty?y:ty))return rectangle_ray(x,y,tx,ty);
    if(clear_box(x<tx?x:tx,y<ty?y:ty,x>tx?x:tx,y>ty?y:ty))return 1;
    if((unsigned)(room-70)<8u) { result=covenants_game_supercover(x,y,tx,ty);if(result>=0)return result; }
    if((unsigned)(room-62)<8u) { result=horizons_game_supercover(x,y,tx,ty);if(result>=0)return result; }
    if((unsigned)(room-54)<8u) { result=return_game_supercover(x,y,tx,ty);if(result>=0)return result; }
    if((unsigned)(room-46)<8u) { result=underwater_game_supercover(x,y,tx,ty);if(result>=0)return result; }
    if((unsigned)(room-22)<16u){
  /* A dense/unsupported snapshot still obeys newly opened road strips and
   * closed fences; untouched rays keep the generated-row fast path. */
  result=road_region_ray((unsigned)room,x,y,tx,ty,solid);
  return result>=0?result:old_rows_clear(x,y,tx,ty);
 }
    /* Unknown or overflow geometry is conservatively clipped. Never restart
     * the expensive legacy solid scan once for every pixel of every stamp. */
    return 0;
}
static void world(int f,int s,int *x,int *y) {
    int d=covenants_power_direction;
    *x=covenants_power_origin_x+f*dx[d]-s*dy[d];
    *y=covenants_power_origin_y+f*dy[d]+s*dx[d];
}
static void local(int x,int y,int *f,int *s) {
    int d=covenants_power_direction;
    x-=covenants_power_origin_x;y-=covenants_power_origin_y;
    *f=x*dx[d]+y*dy[d];*s=-x*dy[d]+y*dx[d];
}
static int connected(int x,int y) { return clear(covenants_power_origin_x,covenants_power_origin_y,x,y); }
/* Every visible stamp pixel has direct LOS from the segment's true origin.
 * Paths around corners explicitly prove each leg; they do not borrow a ray
 * from the player after the initial cast. */
static int stamp_clear(int x,int y,int ox,int oy) {
    int a,b;
    if(!coord(x-2,y-2)||!coord(x+2,y+2))return 0;
    if(geometry_snapshot((x<ox?x:ox)-2,(y<oy?y:oy)-2,(x>ox?x:ox)+2,(y>oy?y:oy)+2))
        return rectangle_ray(ox,oy,x,y)&&rectangle_stamp(x,y,ox,oy);
    if(clear_box((x<ox?x:ox)-2,(y<oy?y:oy)-2,(x>ox?x:ox)+2,(y>oy?y:oy)+2))return 1;
    if(!clear(ox,oy,x,y))return 0;
    for(b=-2;b<=2;b++)for(a=-2;a<=2;a++)if(ab(a)+ab(b)<=2&&!clear(ox,oy,x+a,y+b))return 0;
    return 1;
}
static int mark(int f,int s,unsigned flags,int ox,int oy) {
    unsigned i;int x,y;
    if(f < -62||f>62||s < -62||s>62)return 0;
    world(f,s,&x,&y);
    if(!stamp_clear(x,y,ox,oy))return 0;
    for(i=0;i<cast.count;i++)if(cast.marks[i].f==f&&cast.marks[i].s==s) { cast.marks[i].flags|=(unsigned char)flags;return 1; }
    if(cast.count>=MARK_CAP)return 0;
    cast.marks[cast.count].f=(signed char)f;cast.marks[cast.count].s=(signed char)s;
    cast.marks[cast.count++].flags=(unsigned char)flags;return 1;
}
static void point(int f,int s,unsigned flags) { mark(f,s,flags,covenants_power_origin_x,covenants_power_origin_y); }
static void line(int f,int s,int tf,int ts,unsigned flags,int anchored) {
    int ax=ab(tf-f),ay=-ab(ts-s),sx=f<tf?1:-1,sy=s<ts?1:-1,e=ax+ay,n=0,ox,oy;
    world(f,s,&ox,&oy);
    if(anchored) { ox=covenants_power_origin_x;oy=covenants_power_origin_y; }
    else if(!connected(ox,oy))return;
    for(;;) {
        int q;
        /* Only emitted stamps need a query; each stamp proves its entire
         * original-origin supercover, including every skipped middle pixel. */
        if((!(n&3)||(f==tf&&s==ts))&&!mark(f,s,flags,ox,oy)&&!anchored)break;
        if(f==tf&&s==ts)break;
        q=e*2;if(q>=ay) { e+=ay;f+=sx; }if(q<=ax) { e+=ax;s+=sy; }n++;
    }
}
/* The fixed perimeter's old raster emits these24 unique points in this exact
 * order. Validate each point against current geometry, but never raster-walk
 * four segments or scan prior marks to rediscover their known uniqueness. */
static const signed char ring_points[24][2]={
    {24,0},{20,4},{16,8},{12,12},{8,16},{4,20},{0,24},{-4,20},
    {-8,16},{-12,12},{-16,8},{-20,4},{-24,0},{-20,-4},{-16,-8},
    {-12,-12},{-8,-16},{-4,-20},{0,-24},{4,-20},{8,-16},{12,-12},
    {16,-8},{20,-4}
};
static void ring(unsigned flags) {
    unsigned i;int x,y;
    for(i=0;i<24;i++) {
        Mark *m;world(ring_points[i][0],ring_points[i][1],&x,&y);
        if(!stamp_clear(x,y,covenants_power_origin_x,covenants_power_origin_y))continue;
        m=&cast.marks[cast.count++];m->f=ring_points[i][0];m->s=ring_points[i][1];m->flags=(unsigned char)flags;
    }
}
static int same_party(void) {
    unsigned i;CreatureRoster *r=&adventure_save.roster;
    if(r->selected_party!=cast.proof.selected_party)return 0;
    for(i=0;i<4;i++) {
        const CovenantsPowerMember *p=&cast.proof.party[i];const CreatureInstance *c;
        if(r->party[i]!=p->slot)return 0;
        if(p->slot==CREATURE_EMPTY_SLOT)continue;
        if(p->slot>=CREATURE_ROSTER_CAPACITY)return 0;
        c=&r->instances[p->slot];
        if(!(c->flags&CREATURE_OCCUPIED)||c->instance_id!=p->instance||c->form_id!=p->form||
           c->equipped[0]!=p->equipped[0]||c->equipped[1]!=p->equipped[1]||
           c->selected_command!=p->selected_command||c->polarity!=p->polarity)return 0;
    }
    return 1;
}
int covenants_powers_cast_matches_selected(void) {
    CreatureInstance *c=progression_selected();
    return active()&&same_party()&&c&&(c->flags&CREATURE_OCCUPIED)&&c->instance_id==cast.proof.caster&&
           c->form_id==cast.proof.form&&c->selected_command<2&&c->equipped[c->selected_command]==cast.proof.command&&
           covenants_power_form==cast.proof.form&&covenants_power_kind==cast.proof.command&&
           covenants_power_direction==cast.proof.direction&&covenants_power_origin_x==cast.proof.origin_x&&
           covenants_power_origin_y==cast.proof.origin_y;
}
static int same_scene(void) {
    return room==cast.proof.area&&cast.proof.scene==covenants_game_scene_generation()&&
           cast.proof.attempt==covenants_game_attempt_generation();
}
static void revoke(void) {
    if(!cast.revoked&&cast.proof.token)covenants_game_revoke_cast(cast.proof.token);
    cast.revoked=1;
}
static void finish(void) {
    revoke();covenants_power_time=covenants_power_cast_time=0;cast.count=0;
    northern_powers_tiles_release(NORTHERN_TILES_COVENANTS);
}
const CovenantsPowerProof *covenants_powers_proof(void) {
    if(!active()||cast.revoked||!same_scene()||!covenants_powers_cast_matches_selected()||
       cast.proof.geometry!=covenants_game_geometry_revision())return 0;
    return &cast.proof;
}
void covenants_powers_selection_changed(void) { if(covenants_power_time)finish(); }
void covenants_powers_geometry_changed(void) {
    collision.valid=0;
    if(covenants_power_time) { revoke();cast.dirty=1; }
}
void covenants_powers_reset(void) {
    unsigned i;
    if(covenants_power_time)finish();
    for(i=0;i<sizeof cast;i++)((unsigned char*)&cast)[i]=0;
    collision.valid=0;
    covenants_power_kind=covenants_power_form=covenants_power_direction=0;
    covenants_power_origin_x=covenants_power_origin_y=covenants_power_age=0;
    covenants_power_time=covenants_power_cast_time=covenants_power_cooldown=covenants_power_phase=0;
}
void covenants_powers_enemy_spawn(unsigned i) {
    if(i>=6)return;
    if(++cast.serial[i]==0)cast.serial[i]=1;
    if(covenants_power_time)cast.hits|=(unsigned char)(1u<<i);
    cast.previous_x[i]=(short)enemies[i].x;cast.previous_y[i]=(short)enemies[i].y;
}
void covenants_powers_shot_spawn(unsigned i) {
    unsigned j;
    if(i>=12)return;
    /* Northern's required spawn hook owns the actual projectile generation.
     * Even wrap cannot resurrect a previously consumed live tuple. */
    for(j=0;j<cast.caught_count;j++)if(cast.caught_slot[j]==i)cast.caught_slot[j]=255;
}
int covenants_powers_busy(void) { return covenants_power_time>0; }
unsigned covenants_powers_cast_token(void) { return cast.proof.token; }
unsigned covenants_powers_caster_id(void) { return cast.proof.caster; }
unsigned covenants_powers_moving_objects(void) { return active()?cast.moving:0; }
unsigned covenants_powers_beat(void) { return window()&&!cast.dirty&&covenants_powers_proof()?cast.beat:0; }
unsigned covenants_powers_release_phase(void) { return covenants_powers_beat()==2; }
unsigned covenants_powers_state_bytes(void) { return sizeof cast+sizeof collision+11u*sizeof(int); }
int covenants_powers_can_release(void) {
    return covenants_power_kind==12&&window()&&!hitstop&&!cast.release_age&&
           covenants_power_age>=36&&covenants_power_age<126&&covenants_powers_proof()!=0;
}
int covenants_powers_input(unsigned pressed) {
    if((pressed&256u)&&covenants_powers_can_release()) {
        cast.release_age=(unsigned char)covenants_power_age;cast.dirty=1;
        covenants_power_time=22;
        return 2;
    }
    return 0;
}
unsigned covenants_powers_hint(void) {
    if(!active()||!covenants_powers_cast_matches_selected())return COVENANTS_POWER_HINT_NONE;
    switch(covenants_power_kind) {
    case 12:return cast.release_age?COVENANTS_POWER_HINT_NONE:COVENANTS_POWER_HINT_WARD;
    case 123:return covenants_power_age<42?COVENANTS_POWER_HINT_BANK:COVENANTS_POWER_HINT_NONE;
    case 124:return COVENANTS_POWER_HINT_HOLD;
    case 126:return COVENANTS_POWER_HINT_GAP;
    case 128:return covenants_power_age<66?COVENANTS_POWER_HINT_WAIT:COVENANTS_POWER_HINT_GAP;
    default:return COVENANTS_POWER_HINT_NONE;
    }
}
int covenants_powers_companion_pose(void) {
    const Spec *s=spec();int age;
    if(!s||!active()||!covenants_powers_cast_matches_selected())return -1;
    age=covenants_power_age;
    if(covenants_power_kind==123&&age<42)return 0;
    if(age<s->startup)return 0;
    if(covenants_power_kind==12&&cast.release_age)return age-cast.release_age<6?1:2;
    if(covenants_power_kind==123&&age<48)return 1;
    return age<s->startup+6?1:2;
}
/* Logical parts at most3, rasterized into at most24 exact native stamps.
 * Decorative startup uses the same clipped geometry with no authority. */
static void geometry(void) {
    const Spec *sp=spec();int t,f,s,i,ox,oy,x,y;unsigned flags,live;
    cast.count=cast.moving=0;cast.dirty=0;cast.beat=1;
    if(!sp)return;
    t=covenants_power_age-sp->startup;live=(unsigned)window();
    flags=live?(DAMAGE|FIELD):0;
    switch(covenants_power_kind) {
    case 12:
        if(t>=120&&!cast.release_age)cast.release_age=(unsigned char)covenants_power_age;
        if(!cast.release_age) {
            for(i=0;i<3;i++)if(!(cast.spent&(1u<<i)))point(14,(i-1)*12,live?(FIELD|GUARD|(unsigned)i*16u):0);
        } else {
            cast.beat=2;f=14+(covenants_power_age-cast.release_age)*2;
            if(f>44)break;
            for(i=0;i<3;i++)if(!(cast.spent&(1u<<i))) {
                s=(i-1)*12;world(14,s,&ox,&oy);world(f,s,&x,&y);
                if(!connected(ox,oy)||!clear(ox,oy,x,y)||!stamp_clear(x,y,ox,oy))cast.spent|=(unsigned char)(1u<<i);
                else { mark(f,s,flags|(unsigned)i*16u,ox,oy);cast.moving++; }
            }
        }
        break;
    case 122:
        line(8,0,28,0,flags,1);
        /* The second leg is connected to the proven first corner. */
        line(28,0,28,20,flags,0);
        break;
    case 123:
        if(t<36)point(-8,0,live?FIELD:0);
        else if(!cast.stopped) {
            cast.beat=2;f=8+(t-36)*2;world(4,0,&ox,&oy);world(f,0,&x,&y);
            if(!connected(ox,oy)||!clear(ox,oy,x,y)||!stamp_clear(x,y,ox,oy))cast.stopped=1;
            else { mark(f,0,flags,ox,oy);cast.moving=1; }
        }
        break;
    case 124:
        ring(flags);
        break;
    case 125:
        cast.beat=(unsigned char)(t<16?1:2);
        flags=live?(FIELD|(t<16?DAMAGE:(t<32&&cast.caught_count<1?GUARD:0))):0;
        line(12,-12,24,0,flags,1);line(24,0,12,12,flags,1);
        break;
    case 126:
        flags=live?(FIELD|(cast.caught_count<2?GUARD:0)):0;
        line(-12,-16,16,-16,flags,1);line(16,-16,16,16,flags,1);line(16,16,-12,16,flags,1);
        break;
    case 127:
        if(t<0) { line(4,0,28,0,0,1);line(28,0,28,24,0,0);break; }
        if(cast.stopped)break;
        world(4,0,&x,&y);
        if(!connected(x,y)) { cast.stopped=1;break; }
        if(t<16) { f=4+t*24/15;s=0;world(4,0,&ox,&oy); }
        else if(t<32) { f=28;s=(t-16)*24/15;world(28,0,&ox,&oy);cast.beat=2; }
        else { f=28-(t-32)*12/15;s=24;world(28,24,&ox,&oy);cast.beat=2; }
        /* Each leg is reached through the previous leg, never a new origin ray. */
        world(28,0,&x,&y);
        if(t>=16&&!connected(x,y)) { cast.stopped=1;break; }
        if(t>=32) { int xx,yy;world(28,24,&xx,&yy);if(!clear(x,y,xx,yy)) { cast.stopped=1;break; } }
        world(f,s,&x,&y);
        if(!clear(ox,oy,x,y)||!stamp_clear(x,y,ox,oy))cast.stopped=1;
        else { mark(f,s,flags,ox,oy);cast.moving=1; }
        break;
    case 128:
        cast.beat=(unsigned char)(t<60?1:2);
        flags=live?(FIELD|(t>=60?DAMAGE:0)):0;
        line(4,-16,20,-16,flags,1);
        line(20,-16,20,16,flags|(live&&cast.caught_count<2?GUARD:0),1);
        line(20,16,4,16,flags,1);
        break;
    }
}
static int contains(int x,int y,unsigned flags) {
    unsigned i;int f,s;
    if(!window()||cast.dirty||!coord(x,y))return 0;
    local(x,y,&f,&s);
    for(i=0;i<cast.count;i++)if((cast.marks[i].flags&flags)&&dist(f,s,cast.marks[i].f,cast.marks[i].s)<=2)return 1;
    return 0;
}
static int overlap(int x,int y,int radius,unsigned flags) {
    unsigned i;int a,b,xx,yy,rx,ry,mx,my;
    if(!window()||cast.dirty||!coord(x,y)||radius<0||radius>24)return 0;
    for(i=0;i<cast.count;i++) {
        const Mark *m=&cast.marks[i];
        if(!(m->flags&flags))continue;
        world(m->f,m->s,&mx,&my);
        if(ab(mx-x)>radius+2||ab(my-y)>radius+2)continue;
        for(b=-2;b<=2;b++)for(a=-2;a<=2;a++) {
            if(ab(a)+ab(b)>2)continue;
            xx=mx+a;yy=my+b;rx=ab(xx-x);ry=ab(yy-y);
            if(rx<=radius&&ry<=radius&&rx+ry<=radius+3&&clear(xx,yy,x,y))return (int)i+1;
        }
    }
    return 0;
}
int covenants_powers_overlap(int x,int y,int radius) {
    return covenants_powers_proof()!=0&&overlap(x,y,radius,FIELD);
}
static int enemy_bound(unsigned i) {
    return i<6&&enemies[i].hp>0&&(unsigned)enemies[i].kind<=3&&coord(enemies[i].x,enemies[i].y)&&
           cast.serial[i]&&cast.serial[i]==cast.bound_serial[i];
}
static int ordinary(unsigned i) { return enemy_bound(i)&&(unsigned)enemies[i].kind<=2; }
static void push(unsigned i) {
    unsigned n,j;int x,y;
    if(!ordinary(i)||!clear_box(enemies[i].x-4,enemies[i].y-4,enemies[i].x+4,enemies[i].y+4))return;
    for(n=0;n<8;n++) {
        int ok=1;x=enemies[i].x+dx[covenants_power_direction];y=enemies[i].y+dy[covenants_power_direction];
        if(!clear_box(x-4,y-4,x+4,y+4)||!clear(enemies[i].x,enemies[i].y,x,y)||
           (ab(px-x)<9&&ab(py-y)<9))break;
        for(j=0;j<6;j++)if(j!=i&&enemies[j].hp>0&&ab(enemies[j].x-x)<9&&ab(enemies[j].y-y)<9)ok=0;
        if(!ok)break;
        enemies[i].x=x;enemies[i].y=y;
    }
}
static void spend_drop_at(int x,int y) {
    unsigned i;int f,s;
    local(x,y,&f,&s);
    for(i=0;i<cast.count;i++)if(dist(f,s,cast.marks[i].f,cast.marks[i].s)<=2) {
        cast.spent|=(unsigned char)(1u<<(cast.marks[i].flags>>4));
        cast.count--;
        cast.marks[i].f=cast.marks[cast.count].f;
        cast.marks[i].s=cast.marks[cast.count].s;
        cast.marks[i].flags=cast.marks[cast.count].flags;
        if(cast.moving)cast.moving--;
        return;
    }
}
static void combat(void) {
    const Spec *s=spec();unsigned i;
    if(!s||!covenants_powers_cast_matches_selected()||!same_scene())return;
    for(i=0;i<6;i++) {
        int distance,previous;
        if(!enemy_bound(i))continue;
        if(covenants_power_kind==122&&ordinary(i)&&contains(enemies[i].x,enemies[i].y,DAMAGE)&&slowed_enemies[i]<2)slowed_enemies[i]=2;
        if(!s->damage||(cast.hits&(1u<<i))||!contains(enemies[i].x,enemies[i].y,DAMAGE))continue;
        if(covenants_power_kind==124) {
            if(!ordinary(i))continue;
            distance=dist(enemies[i].x,enemies[i].y,covenants_power_origin_x,covenants_power_origin_y);
            previous=dist(cast.previous_x[i],cast.previous_y[i],covenants_power_origin_x,covenants_power_origin_y);
            if(!((previous>24&&distance<=24)||(previous<24&&distance>=24))||
               dist(enemies[i].x,enemies[i].y,cast.previous_x[i],cast.previous_y[i])>8||
               !clear(cast.previous_x[i],cast.previous_y[i],enemies[i].x,enemies[i].y))continue;
        }
        cast.hits|=(unsigned char)(1u<<i);
        game_enemy_hurt(i,s->damage,0,(unsigned)covenants_power_phase);
        enemies[i].flash=12;impact(enemies[i].x,enemies[i].y);
        if(covenants_power_kind==12)spend_drop_at(enemies[i].x,enemies[i].y);
        if(covenants_power_kind==123) { cast.stopped=1;cast.count=0;cast.moving=0; }
        if(covenants_power_kind==127)push(i);
        if(enemies[i].hp<=0)kill_enemy(&enemies[i]);
        if(covenants_power_kind==123)break;
    }
}
int covenants_powers_intercept_shot(unsigned i,int x,int y,int tx,int ty,int eligible) {
    unsigned serial,j,cap;int f,s,tf,ts,ax,ay,sx,sy,e,n=0;Shot *shot;
    if(eligible!=1||i>=12||!window()||cast.dirty||!covenants_powers_cast_matches_selected()||!same_scene())return 0;
    cap=covenants_power_kind==12?3u:covenants_power_kind==125?1u:
        (covenants_power_kind==126||covenants_power_kind==128)?2u:0u;
    if(cast.caught_count>=cap||!cap)return 0;
    if(covenants_power_kind==12&&cast.release_age)return 0;
    shot=&shots[i];serial=northern_powers_shot_serial(i);
    if(!serial||!shot->life||!shot->owner||shot->x!=x||shot->y!=y||
       shot->dx < -8||shot->dx>8||shot->dy < -8||shot->dy>8||
       !coord(x,y)||!coord(tx,ty)||tx!=x+shot->dx||ty!=y+shot->dy||dist(x,y,tx,ty)>8)return 0;
    for(j=0;j<cast.caught_count;j++)if(cast.caught_slot[j]==i&&cast.caught_serial[j]==serial)return 0;
    local(x,y,&f,&s);local(tx,ty,&tf,&ts);
    if(covenants_power_kind==126) {
        if(ab(tf)+ab(ts)>=ab(f)+ab(s))return 0;
    } else if(tf>=f)return 0;
    if(!clear(x,y,tx,ty))return 0;
    ax=ab(tx-x);ay=-ab(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;e=ax+ay;
    for(;;) {
        int q;
        if(contains(x,y,GUARD)) {
            cast.caught_slot[cast.caught_count]=(unsigned char)i;cast.caught_serial[cast.caught_count++]=serial;
            shot->life=0;impact(x,y);
            if(covenants_power_kind==12)spend_drop_at(x,y);
            if(cast.caught_count>=cap)for(j=0;j<cast.count;j++)cast.marks[j].flags&=(unsigned char)~GUARD;
            return 1;
        }
        if((x==tx&&y==ty)||++n>8)break;
        q=e*2;if(q>=ay) { e+=ay;x+=sx; }if(q<=ax) { e+=ax;y+=sy; }
    }
    return 0;
}
unsigned covenants_powers_boss_damage(int x,int y,int radius,int eligible) {
    const Spec *s=spec();int contact,mx,my;
    if(eligible!=1||!s||!s->damage||cast.boss_hit||!covenants_powers_cast_matches_selected()||
       !same_scene())return 0;
    contact=overlap(x,y,radius,DAMAGE);if(!contact)return 0;
    cast.boss_hit=1;
    if(covenants_power_kind==12) {
        world(cast.marks[contact-1].f,cast.marks[contact-1].s,&mx,&my);spend_drop_at(mx,my);
    }
    if(covenants_power_kind==123) { cast.stopped=1;cast.count=0;cast.moving=0; }
    return s->damage;
}
int covenants_power(unsigned command) {
    CreatureInstance *c;CreatureRoster *r=&adventure_save.roster;
    const CreatureAbility *a;const Spec *s;unsigned i,cd;int index=index_of(command);
    if(index<0||ability_cd||covenants_power_time||hitstop||face<0||face>3||!coord(px,py)||solid(px,py))return 0;
    c=progression_selected();a=creatures_ability(command);s=&specs[index];
    if(!c||!creatures_instance_validate(c)||c->form_id!=(unsigned)index+121u||c->selected_command>=2||
       c->equipped[c->selected_command]!=command||!creatures_command_learned(c->form_id,c->level,command)||
       !a||a->phase!=s->phase||a->cooldown_updates!=s->cooldown||r->selected_party>=4)return 0;
    if(r->party[r->selected_party]>=CREATURE_ROSTER_CAPACITY||c!=&r->instances[r->party[r->selected_party]])return 0;
    for(i=0;i<4;i++)if(r->party[i]!=CREATURE_EMPTY_SLOT&&r->party[i]>=CREATURE_ROSTER_CAPACITY)return 0;
    if(!northern_powers_tiles_claim(NORTHERN_TILES_COVENANTS))return 0;
    collision.valid=0;covenants_power_kind=(int)command;covenants_power_form=c->form_id;
    covenants_power_direction=face;covenants_power_phase=a->phase;
    covenants_power_origin_x=px;covenants_power_origin_y=py;covenants_power_age=0;
    covenants_power_time=s->startup+s->active+s->settle;covenants_power_cast_time=s->startup;
    cast.lease=northern_powers_tiles_generation();cast.proof.caster=c->instance_id;
    cast.proof.form=c->form_id;cast.proof.command=(unsigned char)command;cast.proof.direction=(unsigned char)face;
    cast.proof.origin_x=(short)px;cast.proof.origin_y=(short)py;cast.proof.area=(short)room;
    cast.proof.selected_party=r->selected_party;cast.proof.owner_slot=r->party[r->selected_party];
    cast.proof.scene=covenants_game_scene_generation();cast.proof.attempt=covenants_game_attempt_generation();
    cast.proof.geometry=covenants_game_geometry_revision();
    if(++action_serial==0)action_serial=1;
    cast.proof.action_serial=action_serial;
    for(i=0;i<4;i++) {
        CovenantsPowerMember *p=&cast.proof.party[i];const CreatureInstance *member;
        p->slot=r->party[i];p->instance=0;p->form=p->equipped[0]=p->equipped[1]=p->selected_command=p->polarity=0;
        if(p->slot==CREATURE_EMPTY_SLOT)continue;
        member=&r->instances[p->slot];p->instance=member->instance_id;p->form=member->form_id;
        p->equipped[0]=member->equipped[0];p->equipped[1]=member->equipped[1];
        p->selected_command=member->selected_command;p->polarity=member->polarity;
    }
    cast.count=cast.hits=cast.fields[0]=cast.fields[1]=cast.revoked=cast.art_live=0;
    cast.release_age=cast.caught_count=cast.spent=cast.moving=cast.stopped=cast.boss_hit=0;
    cast.proof.token=(unsigned)(room-70)<8u?covenants_game_action_begin(3):0;
    for(i=0;i<6;i++) {
        cast.bound_serial[i]=cast.serial[i];cast.previous_x[i]=(short)enemies[i].x;cast.previous_y[i]=(short)enemies[i].y;
    }
    cd=game_power_cooldown(s->cooldown);
    if(cd<(unsigned)s->cooldown-GAME_MAX_POWER_RECOVERY)cd=(unsigned)s->cooldown-GAME_MAX_POWER_RECOVERY;
    if(cd>s->cooldown)cd=s->cooldown;
    covenants_power_cooldown=ability_cd=ability_max=(int)cd;
    obj_upload(covenants_power_marks[index],16,16,GFX_OBJ_POWER_PIN);
    obj_upload(covenants_power_particles[index][0],8,8,GFX_OBJ_WATER_DROP);
    geometry();sfx(2);return 1;
}
static int retain_complete_geometry(void) {
    unsigned expected,i;int x,y,l=covenants_power_origin_x,r=l,t=covenants_power_origin_y,b=t;
    switch(covenants_power_kind) {
    case 122:expected=11;break;
    case 124:expected=24;break;
    case 125:expected=7;break;
    case 126:expected=23;break;
    case 128:expected=17;break;
    default:return 0;
    }
    if(cast.count!=expected||!window())return 0;
    for(i=0;i<cast.count;i++) {
        world(cast.marks[i].f,cast.marks[i].s,&x,&y);
        if(x-2<l)l=x-2;
        if(x+2>r)r=x+2;
        if(y-2<t)t=y-2;
        if(y+2>b)b=y+2;
    }
    /* No partial/failed snapshot is a certificate, even if a fallback exists.
     * This complete current occupied union must cover the original origin,
     * every exact native pixel and all connecting rays/segment origins. */
    return geometry_snapshot(l,t,r,b)&&clear_box(l,t,r,b);
}
void covenants_powers_tick(void) {
    unsigned i;int x,y,r,index,age;const Spec *s;
    if(hitstop||!covenants_power_time)return;
    if(!active()||!same_scene()||!covenants_powers_cast_matches_selected()) { finish();return; }
    if(!cast.revoked&&cast.proof.geometry!=covenants_game_geometry_revision())covenants_powers_geometry_changed();
    if(covenants_power_cast_time)covenants_power_cast_time--;
    covenants_power_age++;index=index_of((unsigned)covenants_power_kind);s=&specs[index];age=covenants_power_age;
    /* Opening a practice shortcut may not change any stationary effect pixels.
     * Reuse only a complete immutable shape certified clear by the NEW exact
     * snapshot. Field proof remains permanently revoked. */
    if(cast.dirty&&retain_complete_geometry())cast.dirty=0;
    /* Stationary outlines keep their exact clipped stamps. Only moving parts,
     * phase boundaries, changed geometry or a fresh release rebuild them. */
    if(!cast.dirty&&covenants_power_kind==126&&age==s->startup+s->active) {
        /* Shelter settling changes only authority flags. The23 ordered
         * clipped pixels remain stationary and already have flat colors.
         * A simultaneous geometry revision still takes the full rebuild. */
        for(i=0;i<cast.count;i++)cast.marks[i].flags=0;
        cast.moving=0;
    } else if(cast.dirty||age==s->startup||age==s->startup+s->active||
       (covenants_power_kind==12&&(cast.release_age||age==126))||
       (covenants_power_kind==123&&age>=42)||covenants_power_kind==127||
       (covenants_power_kind==125&&(age==22||age==38))||
       (covenants_power_kind==128&&age==66))geometry();
    if(window()) {
        if(!cast.art_live) {
            obj_upload(covenants_power_particles[index][0],8,8,GFX_OBJ_POWER_PIN);
            obj_upload(covenants_power_particles[index][1],8,8,GFX_OBJ_WATER_DROP);cast.art_live=1;
        }
        combat();
        if(cast.proof.token&&covenants_powers_proof())for(i=0;i<8;i++) {
            unsigned beat=cast.beat==2?1u:0u;
            if(cast.fields[beat]&(1u<<i))continue;
            if(!covenants_game_field_target(i,&x,&y,&r))break;
            if(covenants_powers_overlap(x,y,r)&&covenants_game_field_hit(i,(unsigned)covenants_power_kind,
               cast.proof.caster,(unsigned)covenants_power_form,cast.proof.token))cast.fields[beat]|=(unsigned char)(1u<<i);
            if(cast.dirty||!covenants_powers_proof())break;
        }
    }
    for(i=0;i<6;i++) { cast.previous_x[i]=(short)enemies[i].x;cast.previous_y[i]=(short)enemies[i].y; }
    if(--covenants_power_time==0)finish();
}
void covenants_powers_draw(void) {
    unsigned i;int x,y;
    if(!active()||cast.dirty||!covenants_powers_cast_matches_selected()||!same_scene())return;
    if(!cast.art_live)obj_add(GFX_OBJ_POWER_PIN,covenants_power_origin_x-8,covenants_power_origin_y-25,
                              16,16,1,covenants_power_origin_y+2,0);
    for(i=0;i<cast.count;i++) {
        const Mark *m=&cast.marks[i];world(m->f,m->s,&x,&y);
        obj_add(cast.art_live&&!(m->flags&DAMAGE)?GFX_OBJ_POWER_PIN:GFX_OBJ_WATER_DROP,x-3,y-3,8,8,1,y+2,0);
    }
}
