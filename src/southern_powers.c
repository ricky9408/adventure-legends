/* Twenty bounded Southern commands. Damage uses the real Q4/phase resolver.
 * No player movement, generic damage interception, boss retiming or heap use. */
#include "southern_powers.h"
#include "southern_power_art.h"
#include "northern_powers.h"
#include "advanced_powers.h"
#include "regional_powers.h"
#include "gear_runtime.h"
#include "progression.h"
#include "obj_layout.h"
#include "combat_rules.h"
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
extern Enemy enemies[6];extern Shot shots[12];
extern volatile int px,py;
extern int face,cx,cy,ability_cd,ability_max,hitstop,enemy_clocks[6],enemy_windups[6];
extern int solid(int,int);
extern void kill_enemy(Enemy *),impact(int,int),sfx(int);
extern void obj_upload(const unsigned char *,int,int,int);
extern void obj_add(int,int,int,int,int,int,int,int);
int southern_power_kind,southern_power_time,southern_power_form;
int southern_power_direction,southern_power_origin_x,southern_power_origin_y;
int southern_power_age,southern_power_cooldown,southern_power_cast_time;
int southern_power_phase;
typedef struct {short x,y,dx,dy,error;unsigned char life,stage,harmless,pad;} Missile;
static Missile missiles[3];
static short previous_x[6],previous_y[6];
static unsigned short enemy_serial[6],mark_serial[2];
static unsigned caster_id,lease_generation;
static unsigned char hit_mask,spent,mark_a,mark_b,delayed,redirected,redirect_left,slow_mask;
static unsigned char side_changed,startup_until,draw_count,guard_grace,guard_enemy;
static unsigned short guard_serial;
static signed char guard_side;
static int ax,ay,bx,by,ex,ey,delay_x,delay_y;
static short companion_start_x,companion_start_y;
/* Four exact fixed crescent raster spans: 17+25+25+17 points. The coordinates
 * are signed world-axis offsets, so rotations retain the original tie rules.
 * Only scenery validity is cached; moving targets and their short LOS are live. */
static signed char crescent_raster[84][2];
static unsigned char crescent_offsets[5],crescent_count,crescent_spans,crescent_valid;
static const signed char crescent_f[5]={0,16,36,16,0};
static const signed char crescent_s[5]={-18,-24,0,24,18};
typedef struct {short x,y,tx,ty;unsigned short serial_a,serial_b;
    unsigned char a,b,valid,result;} Sight;
static Sight mark_sight[2];
static const signed char fx[4]={0,0,-1,1},fy[4]={1,-1,0,0};
static const unsigned char phases[10]={CREATURE_WOOD,CREATURE_EARTH,CREATURE_WATER,
    CREATURE_FIRE,CREATURE_EARTH,CREATURE_METAL,CREATURE_WOOD,CREATURE_WATER,
    CREATURE_FIRE,CREATURE_METAL};
static const unsigned char lifetimes[20]={24,44,24,42,44,48,60,40,32,40,32,38,42,48,38,34,60,60,42,48};
static int absolute(int n){return n<0?-n:n;}
static int sign(int n){return(n>0)-(n<0);}
static int distance(int x,int y,int tx,int ty){return absolute(x-tx)+absolute(y-ty);}
/* World coordinates are bounded by the maps, and all local paths by96 pixels.
 * Side cells are tested at every diagonal step: no thin-wall/corner tunnelling. */
static int clear(int x,int y,int tx,int ty){
    int dx=absolute(tx-x),dy=-absolute(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,err=dx+dy;
    if(distance(x,y,tx,ty)>192||solid(x,y)||solid(tx,ty))return 0;
    while(x!=tx||y!=ty){int twice=err*2,nx=x,ny=y;
        if(twice>=dy){err+=dy;nx+=sx;}if(twice<=dx){err+=dx;ny+=sy;}
        if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return 0;
        x=nx;y=ny;if(solid(x,y))return 0;
    }return 1;
}
static void remember_sight(Sight *s,unsigned a,unsigned b,int x,int y,int tx,int ty,int result){
    s->x=(short)x;s->y=(short)y;s->tx=(short)tx;s->ty=(short)ty;s->a=(unsigned char)a;s->b=(unsigned char)b;
    s->serial_a=a<6?enemy_serial[a]:0;s->serial_b=b<6?enemy_serial[b]:0;s->result=(unsigned char)result;s->valid=1;
}
static int cached_sight(Sight *s,unsigned a,unsigned b,int x,int y,int tx,int ty){
    if(s->valid&&s->a==a&&s->b==b&&s->x==x&&s->y==y&&s->tx==tx&&s->ty==ty&&
       s->serial_a==(a<6?enemy_serial[a]:0)&&s->serial_b==(b<6?enemy_serial[b]:0))return s->result;
    remember_sight(s,a,b,x,y,tx,ty,clear(x,y,tx,ty));return s->result;
}
static void point(int f,int s,int *x,int *y){int dx=fx[southern_power_direction],dy=fy[southern_power_direction];
    *x=southern_power_origin_x+f*dx-s*dy;*y=southern_power_origin_y+f*dy+s*dx;
}
static void relative(int x,int y,int *f,int *s){int dx=fx[southern_power_direction],dy=fy[southern_power_direction];
    x-=southern_power_origin_x;y-=southern_power_origin_y;*f=x*dx+y*dy;*s=-x*dy+y*dx;
}
static int origin_clear(int x,int y){return clear(southern_power_origin_x,southern_power_origin_y,x,y);}
static int ordinary(unsigned i){return i<6&&enemies[i].hp>0&&(unsigned)enemies[i].kind<=2;}
static int mark_live(unsigned slot){unsigned i=slot?mark_b:mark_a;
    return i<6&&enemies[i].hp>0&&enemy_serial[i]==mark_serial[slot];
}
static int active(void){return southern_power_time>0&&
    northern_powers_tiles_owner()==NORTHERN_TILES_SOUTHERN&&
    lease_generation==northern_powers_tiles_generation();}
static void finish(void){unsigned i;southern_power_time=0;
    for(i=0;i<3;i++)missiles[i].life=0;
    slow_mask=0;northern_powers_tiles_release(NORTHERN_TILES_SOUTHERN);
}
int southern_powers_busy(void){return southern_power_time>0;}
int southern_powers_cast_matches_selected(void){CreatureInstance*c=progression_selected();
    return c&&(c->flags&CREATURE_OCCUPIED)&&caster_id&&c->instance_id==caster_id&&
        c->form_id==southern_power_form;
}
int southern_powers_companion_pose(int*x,int*y){
    if(!x||!y||!active()||southern_power_kind!=23||southern_power_age>12||!southern_powers_cast_matches_selected())return 0;
    *x=ex;*y=ey;return 1;
}
void southern_powers_enemy_spawn(unsigned i){
    if(i>=6)return;
    if(mark_sight[0].a==i||mark_sight[0].b==i)mark_sight[0].valid=0;
    if(mark_sight[1].a==i||mark_sight[1].b==i)mark_sight[1].valid=0;
    enemy_serial[i]++;
    /* Invalidate by slot too so even serial wrap cannot rebind an old mark. */
    if(mark_a==i)mark_a=6;
    if(mark_b==i)mark_b=6;
    if(redirected==i){redirected=6;redirect_left=0;}
    if(guard_enemy==i){guard_enemy=6;guard_grace=0;}
    hit_mask|=(unsigned char)(1u<<i); /* a recycled target never gains a second cast hit */
    previous_x[i]=(short)enemies[i].x;previous_y[i]=(short)enemies[i].y;
}
void southern_powers_geometry_changed(void){crescent_valid=crescent_spans=crescent_count=0;
    mark_sight[0].valid=mark_sight[1].valid=0;
}
void southern_powers_reset(void){unsigned i;
    southern_powers_geometry_changed();
    for(i=0;i<6;i++)if((slow_mask&(1u<<i))&&slowed_enemies[i]<=24)slowed_enemies[i]=0;
    slow_mask=0;
    southern_power_kind=southern_power_time=southern_power_form=0;
    southern_power_direction=southern_power_origin_x=southern_power_origin_y=0;
    southern_power_age=southern_power_cooldown=southern_power_cast_time=southern_power_phase=0;
    hit_mask=spent=delayed=redirect_left=side_changed=startup_until=0;
    mark_a=mark_b=redirected=guard_enemy=6;guard_grace=0;caster_id=0;guard_side=-1;
    ax=ay=bx=by=ex=ey=delay_x=delay_y=0;
    for(i=0;i<3;i++)missiles[i].life=0;
    northern_powers_tiles_release(NORTHERN_TILES_SOUTHERN);
}
/* Only call after a swept collision/LOS path has been established. */
static int confirmed_hurt(unsigned i,unsigned q4,int flash){Enemy *e;
    if(i>=6||(hit_mask&(1u<<i)))return 0;
    e=&enemies[i];if(e->hp<=0)return 0;
    hit_mask|=(unsigned char)(1u<<i);game_enemy_hurt(i,q4,0,(unsigned)southern_power_phase);
    if(flash)e->flash=12;
    impact(e->x,e->y);if(e->hp<=0)kill_enemy(e);return 1;
}
static int hurt(unsigned i,unsigned q4,int x,int y,int flash){
    if(i>=6||(hit_mask&(1u<<i))||enemies[i].hp<=0||!clear(x,y,enemies[i].x,enemies[i].y))return 0;
    return confirmed_hurt(i,q4,flash);
}
static void slow(unsigned i){unsigned n=southern_power_time<=24?(southern_power_time>0?(unsigned)southern_power_time-1u:0u):24u;
    if(slowed_enemies[i]<n){slowed_enemies[i]=(unsigned char)n;slow_mask|=(unsigned char)(1u<<i);}
}
static void radial(int x,int y,int r,unsigned q4){unsigned i;
    for(i=0;i<6;i++)if(enemies[i].hp>0&&distance(x,y,enemies[i].x,enemies[i].y)<=r)hurt(i,q4,x,y,1);
}
/* Cache construction walks exactly the same endpoint-inclusive Bresenham
 * raster and diagonal side cells as clear/span_damage. Incomplete spans never
 * become visible/damaging. The first draw builds this during the six-update
 * anticipation; later ticks/draws do not revisit unchanged scenery. */
static void crescent_refresh(void){unsigned p;
    if(crescent_valid)return;
    crescent_count=crescent_spans=0;crescent_offsets[0]=0;crescent_valid=1;
    for(p=0;p<4;p++){
        int x,y,tx,ty,dx,dy,sx,sy,err,complete=0;unsigned start=crescent_count;
        point(crescent_f[p],crescent_s[p],&x,&y);point(crescent_f[p+1],crescent_s[p+1],&tx,&ty);
        if((p==0&&!origin_clear(x,y))||solid(x,y)||solid(tx,ty))break;
        dx=absolute(tx-x);dy=-absolute(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;err=dx+dy;
        for(;;){int twice,nx=x,ny=y;
            if(crescent_count>=84)break;
            crescent_raster[crescent_count][0]=(signed char)(x-southern_power_origin_x);
            crescent_raster[crescent_count++][1]=(signed char)(y-southern_power_origin_y);
            if(x==tx&&y==ty){complete=1;break;}
            twice=err*2;if(twice>=dy){err+=dy;nx+=sx;}if(twice<=dx){err+=dx;ny+=sy;}
            if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))break;
            x=nx;y=ny;if(solid(x,y))break;
        }
        if(!complete){crescent_count=(unsigned char)start;break;}
        crescent_offsets[++crescent_spans]=crescent_count;
    }
}
static void crescent_damage(void){unsigned p,i;
    crescent_refresh();
    for(p=0;p<crescent_spans;p++){
        unsigned begin=crescent_offsets[p],end=crescent_offsets[p+1];
        int x=southern_power_origin_x+crescent_raster[begin][0],y=southern_power_origin_y+crescent_raster[begin][1];
        int tx=southern_power_origin_x+crescent_raster[end-1][0],ty=southern_power_origin_y+crescent_raster[end-1][1];
        for(i=0;i<6;i++)if(enemies[i].hp>0&&!(hit_mask&(1u<<i))){unsigned n;
            int qx=enemies[i].x,qy=enemies[i].y;
            /* Inclusive bounds are only an early rejection, never a hit test. */
            if(qx<(x<tx?x:tx)-4||qx>(x>tx?x:tx)+4||qy<(y<ty?y:ty)-4||qy>(y>ty?y:ty)+4)continue;
            for(n=begin;n<end;n++){
                int sx=southern_power_origin_x+crescent_raster[n][0],sy=southern_power_origin_y+crescent_raster[n][1];
                if(distance(sx,sy,qx,qy)<=4&&clear(sx,sy,qx,qy)){
                    if(confirmed_hurt(i,24,1))slow(i);
                    break;
                }
            }
        }
    }
}
static void push(unsigned i,int dx,int dy,unsigned n){unsigned step;
    if(!ordinary(i))return;
    for(step=0;step<n;step++){int nx=enemies[i].x+dx,ny=enemies[i].y+dy;
        if(!clear(enemies[i].x,enemies[i].y,nx,ny))break;
        enemies[i].x=nx;enemies[i].y=ny;
    }
}
static unsigned aimed_target(int x,int y,int direction,unsigned exclude,int ranged){unsigned i,chosen=6;int best=57;
    for(i=0;i<6;i++)if(i!=exclude&&enemies[i].hp>0&&(!ranged||(enemies[i].kind==2&&
       ((enemy_windups[i]>0&&enemy_windups[i]<=120)||
        (!enemy_windups[i]&&enemy_clocks[i]>=0&&enemy_clocks[i]<=40))))){int dx=enemies[i].x-x,dy=enemies[i].y-y;
        int f=dx*fx[direction]+dy*fy[direction],s=-dx*fy[direction]+dy*fx[direction];
        if(f>=4&&f<best&&absolute(s)<=12&&clear(x,y,enemies[i].x,enemies[i].y)){chosen=i;best=f;}
    }return chosen;
}
static int same_caster(void){CreatureInstance *c=progression_selected();
    return c&&creatures_instance_validate(c)&&c->instance_id==caster_id&&c->form_id==southern_power_form&&
        c->selected_command<2&&c->equipped[c->selected_command]==southern_power_kind;
}
int southern_powers_can_aim(void){return active()&&!hitstop&&!spent&&same_caster()&&
    ((southern_power_kind==32&&!side_changed&&southern_power_age<22)||
     (southern_power_kind==40&&mark_live(0)&&mark_b==6&&southern_power_age<48));}
unsigned southern_powers_hint(void){if(!southern_powers_can_aim())return SOUTHERN_HINT_NONE;
    return southern_power_kind==32?SOUTHERN_HINT_OTHER_SIDE:SOUTHERN_HINT_SECOND_TARGET;
}
int southern_powers_aim(void){unsigned t;
    if(!southern_powers_can_aim())return 0;
    if(southern_power_kind==32){int x,y;point(0,12,&x,&y);
        if(!origin_clear(x,y))return 0;
        guard_side=1;side_changed=1;
        startup_until=(unsigned char)(southern_power_age+6);ax=x;ay=y;return 1;}
    if(face<0||face>3)return 0;
    t=aimed_target(px,py,face,mark_a,0);
    if(t>=6||!clear(enemies[mark_a].x,enemies[mark_a].y,enemies[t].x,enemies[t].y))return 0;
    mark_b=(unsigned char)t;mark_serial[1]=enemy_serial[t];
    remember_sight(&mark_sight[1],mark_a,t,enemies[mark_a].x,enemies[mark_a].y,enemies[t].x,enemies[t].y,1);
    sfx(2);return 1;
}
static void missile(unsigned n,int x,int y,int dx,int dy,int harmless){
    missiles[n].x=(short)x;missiles[n].y=(short)y;missiles[n].dx=(short)dx;missiles[n].dy=(short)dy;
    missiles[n].error=(short)(absolute(ax-x)-absolute(ay-y));
    missiles[n].life=40;missiles[n].stage=0;missiles[n].harmless=(unsigned char)harmless;
}
int southern_power_side(unsigned command,int side){
    CreatureInstance *c;const CreatureAbility *a;unsigned base,cd,i,target=6;int x1,y1,x2,y2;
    int dx,dy;
    if(command<23||command>42||ability_cd||southern_power_time||hitstop||
       (side!=-1&&side!=1)||face<0||face>3)return 0;
    c=progression_selected();a=creatures_ability(command);
    if(!c||!creatures_instance_validate(c)||c->selected_command>1||
       c->equipped[c->selected_command]!=command||!creatures_command_learned(c->form_id,c->level,command)||
       !a||a->phase!=phases[(command-23)/2]||a->cooldown_updates<90||solid(px,py))return 0;
    dx=fx[face];dy=fy[face];x1=px+dx*24+dy*12;y1=py+dy*24-dx*12;
    x2=px+dx*24-dy*12;y2=py+dy*24+dx*12;
    if(command==23){x1=cx+dy*8;y1=cy-dx*8;x2=px+dx*12+dy*18;y2=py+dy*12-dx*18;
        if(!clear(cx,cy,x1,y1))return 0;}
    if(command==24){x1=px+dx*16+dy*16;y1=py+dy*16-dx*16;x2=px+dx*40;y2=py+dy*40;}
    if(command==26){x1=px+dx*16+dy*12;y1=py+dy*16-dx*12;x2=px+dx*28-dy*12;y2=py+dy*28+dx*12;}
    if(command==31||command==32){x1=px-dy*12*side;y1=py+dx*12*side;x2=x1;y2=y1;}
    if(command==35||command==36){x1=px+dx*20+dy*16;y1=py+dy*20-dx*16;x2=px+dx*20-dy*16;y2=py+dy*20+dx*16;}
    if(command==29||command==39||command==40){target=aimed_target(px,py,face,6,command==29);if(target>=6)return 0;
        x1=x2=enemies[target].x;y1=y2=enemies[target].y;}
    if((command==23||command==24||command==26||command==28||command==31||command==32||command==34||command==35||command==36)&&
       (!clear(px,py,x1,y1)||!clear(x1,y1,x2,y2)||!clear(px,py,x2,y2)))return 0;
    if(!northern_powers_tiles_claim(NORTHERN_TILES_SOUTHERN))return 0;
    southern_power_kind=(int)command;southern_power_form=c->form_id;caster_id=c->instance_id;
    southern_power_direction=face;southern_power_origin_x=px;southern_power_origin_y=py;
    southern_power_phase=a->phase;southern_power_age=0;southern_power_time=lifetimes[command-23];
    base=a->cooldown_updates;cd=game_power_cooldown(base);if(cd<base-8)cd=base-8;if(cd>base)cd=base;
    southern_power_cooldown=ability_cd=ability_max=(int)cd;southern_power_cast_time=20;
    ax=x1;ay=y1;bx=x2;by=y2;ex=command==23?cx:px;ey=command==23?cy:py;
    companion_start_x=(short)cx;companion_start_y=(short)cy;hit_mask=spent=delayed=side_changed=redirect_left=0;
    mark_a=(unsigned char)target;mark_b=redirected=guard_enemy=6;guard_grace=0;guard_side=(signed char)side;
    startup_until=(unsigned char)(command==31?4:command==32?6:8);
    if(target<6)mark_serial[0]=enemy_serial[target];
    for(i=0;i<3;i++)missiles[i].life=0;
    for(i=0;i<6;i++){previous_x[i]=(short)enemies[i].x;previous_y[i]=(short)enemies[i].y;}
    southern_powers_geometry_changed();
    lease_generation=northern_powers_tiles_generation();
    if(target<6)remember_sight(&mark_sight[0],6,target,px,py,enemies[target].x,enemies[target].y,1);
    obj_upload(southern_power_marks[(command-23)/2],16,16,GFX_OBJ_POWER_PIN);
    obj_upload(southern_power_particles[(command-23)/2],8,8,GFX_OBJ_WATER_DROP);sfx(2);
    if(command==29&&enemy_windups[target]>0)
        enemy_windups[target]=(int)southern_powers_windup(target,(unsigned)enemy_windups[target]);
    return 1;
}
int southern_power(unsigned command){return southern_power_side(command,-1);}
int southern_powers_feedback(unsigned command){CreatureInstance*c;
    if(command<23||command>42||southern_power_time)return 0;
    c=progression_selected();
    if(!c||!creatures_instance_validate(c)||face<0||face>3)return 0;
    caster_id=c->instance_id;southern_power_form=c->form_id;southern_power_kind=(int)command;southern_power_direction=face;
    southern_power_origin_x=px;southern_power_origin_y=py;southern_power_cast_time=20;return 1;
}
int southern_powers_melee_guard(unsigned i,int x,int y){int f,s;
    if(!active()||hitstop||!ordinary(i)||enemies[i].kind==2)return 0;
    if(guard_grace&&guard_enemy==i&&guard_serial==enemy_serial[i])return 1;
    if(spent||southern_power_time<12||
       southern_power_age<startup_until||distance(px,py,southern_power_origin_x,southern_power_origin_y)>6||
       !clear(x,y,px,py))return 0;
    relative(x,y,&f,&s);
    if(southern_power_kind==33){if(southern_power_age>16||f<4||f>22||absolute(s)>5)return 0;}
    else if(southern_power_kind==31||southern_power_kind==32){
        if(southern_power_age>30||absolute(f)>8||s*guard_side<4||s*guard_side>22)return 0;
    }else return 0;
    spent=1;guard_grace=12;guard_enemy=(unsigned char)i;guard_serial=enemy_serial[i];
    if(southern_power_kind==32){delayed=1;ex=ax;ey=ay;}
    else hurt(i,southern_power_kind==31?16:24,px,py,1);
    impact(x,y);return 1;
}
unsigned southern_powers_windup(unsigned i,unsigned base){
    if(!active()||hitstop||southern_power_kind!=29||spent||i!=mark_a||!ordinary(i)||
       !mark_live(0)||southern_power_time<=12||base==0||base>120||!origin_clear(enemies[i].x,enemies[i].y))return base;
    spent=1;delayed=12;delay_x=enemies[i].x;delay_y=enemies[i].y;return base+12;
}
int southern_powers_approach(unsigned i,int *x,int *y){int f,s,tx,ty;
    if(!x||!y||!active()||hitstop||!ordinary(i)||enemies[i].kind==2||southern_power_age<6)return 0;
    if(southern_power_kind!=26&&southern_power_kind!=35&&southern_power_kind!=36)return 0;
    if(redirected==i&&redirect_left){
        if(distance(enemies[i].x,enemies[i].y,ex,ey)<=3||!clear(enemies[i].x,enemies[i].y,ex,ey)){redirect_left=0;return 0;}
        *x=ex;*y=ey;return 1;
    }
    if(spent)return 0;
    relative(enemies[i].x,enemies[i].y,&f,&s);
    if(f<8||f>42||absolute(s)>24)return 0;
    if(southern_power_kind==26){if(absolute(f-22)>8)return 0;point(16,s<0?-24:24,&tx,&ty);}
    else if(southern_power_kind==35){tx=ax;ty=ay;}
    else {if(absolute(f-20)>8)return 0;
        if(distance(px,py,ax,ay)>=distance(px,py,bx,by)){tx=ax;ty=ay;}else{tx=bx;ty=by;}
    }
    if(!origin_clear(tx,ty)||!clear(enemies[i].x,enemies[i].y,tx,ty))return 0;
    spent=1;redirected=(unsigned char)i;redirect_left=12;ex=tx;ey=ty;*x=tx;*y=ty;
    if(southern_power_kind==36)hurt(i,16,tx,ty,1);
    return 1;
}
void southern_powers_weapon_hit(unsigned i){unsigned target;
    if(!active()||spent||southern_power_time<=8||i>=6||enemy_serial[i]!=mark_serial[i==mark_b?1:0])return;
    if(southern_power_kind==39){if(i!=mark_a||!mark_live(0))return;target=i;}
    else if(southern_power_kind==40){if(i!=mark_a&&i!=mark_b)return;
        target=i==mark_a?mark_b:mark_a;
        if(!mark_live(i==mark_a?1:0))return;
    }else return;
    if(!cached_sight(&mark_sight[1],i,target,enemies[i].x,enemies[i].y,enemies[target].x,enemies[target].y))return;
    spent=1;delayed=8;delay_x=enemies[i].x;delay_y=enemies[i].y;
    remember_sight(&mark_sight[1],6,target,delay_x,delay_y,enemies[target].x,enemies[target].y,1);
    /* Store target as the sole delayed mark; source no longer needs to live. */
    mark_a=(unsigned char)target;mark_serial[0]=enemy_serial[target];mark_b=6;
}
static int might_near(int x,int y,int tx,int ty,int qx,int qy,int r){
    int dx=tx-x,dy=ty-y;
    if(qx<(x<tx?x:tx)-r||qx>(x>tx?x:tx)+r||qy<(y<ty?y:ty)-r||qy>(y>ty?y:ty)+r)return 0;
    return absolute((qx-x)*dy-(qy-y)*dx)<=r*(absolute(dx)+absolute(dy));
}
static int near_segment(int x,int y,int tx,int ty,int qx,int qy,int radius){
    int dx=absolute(tx-x),dy=-absolute(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,err=dx+dy;
    if(distance(x,y,tx,ty)>192||!might_near(x,y,tx,ty,qx,qy,radius))return 0;
    for(;;){int twice;if(solid(x,y))return 0;
        if(distance(x,y,qx,qy)<=radius&&clear(x,y,qx,qy))return 1;
        if(x==tx&&y==ty)break;
        twice=err*2;
        {int nx=x,ny=y;if(twice>=dy){err+=dy;nx+=sx;}if(twice<=dx){err+=dx;ny+=sy;}
         if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return 0;
         x=nx;y=ny;}
    }return 0;
}
/* Sweep a fixed segment once for the whole six-slot hit ledger. This preserves
 * the exact Manhattan-radius/pixel/corner test of near_segment without walking
 * the same scenery six times. A complete-only caller discards a blocked span. */
static int span_damage(int x,int y,int tx,int ty,int radius,unsigned damage,int complete_only,int slowing){
    int dx=absolute(tx-x),dy=-absolute(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,err=dx+dy,complete=0;
    unsigned candidates=0,possible=0,i;
    for(i=0;i<6;i++)if(enemies[i].hp>0&&!(hit_mask&(1u<<i))&&might_near(x,y,tx,ty,enemies[i].x,enemies[i].y,radius))possible|=1u<<i;
    if(!possible)return clear(x,y,tx,ty);
    if(solid(x,y))return 0;
    for(;;){int twice,nx=x,ny=y;
        if(possible!=candidates)for(i=0;i<6;i++)if((possible&(1u<<i))&&!(candidates&(1u<<i))&&
           distance(x,y,enemies[i].x,enemies[i].y)<=radius&&clear(x,y,enemies[i].x,enemies[i].y))candidates|=1u<<i;
        if(x==tx&&y==ty){complete=1;break;}
        twice=err*2;if(twice>=dy){err+=dy;nx+=sx;}if(twice<=dx){err+=dx;ny+=sy;}
        if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))break;
        x=nx;y=ny;if(solid(x,y))break;
    }
    if(complete||!complete_only)for(i=0;i<6;i++)if((candidates&(1u<<i))&&confirmed_hurt(i,damage,1)&&slowing)slow(i);
    return complete;
}
int southern_powers_intercept_shot(unsigned i,int x,int y,int tx,int ty,int eligible){int f,s,tf,ts;
    if(!active()||hitstop||southern_power_kind!=28||spent||southern_power_age<6||southern_power_age>40||
       !eligible||i>=12||shots[i].life<=0||!shots[i].owner||distance(x,y,tx,ty)>16||
       !clear(x,y,tx,ty)||!origin_clear(ax,ay)||!origin_clear(bx,by)||!clear(ax,ay,bx,by))return 0;
    relative(x,y,&f,&s);relative(tx,ty,&tf,&ts);
    if(tf>=f||f<22||tf>26||!near_segment(x,y,tx,ty,(ax+bx)/2,(ay+by)/2,14))return 0;
    if(absolute(s)>16&&absolute(ts)>16)return 0;
    shots[i].life=0;spent=1;missile(0,ax,ay,-fy[southern_power_direction],fx[southern_power_direction],1);
    missile(1,bx,by,fy[southern_power_direction],-fx[southern_power_direction],1);
    missiles[0].life=missiles[1].life=10;radial(bx,by,12,24);return 1;
}
/* A projectile moves <=3 individually swept pixels/update, never skipping
 * collisions even when a diagonal changes both coordinates in one step. */
static void missile_tick(unsigned n){Missile *m=&missiles[n];unsigned step,i;int command=southern_power_kind;
    if(!m->life)return;
    if(command==42&&southern_power_age>=19&&!clear(m->x,m->y,cx,cy)){m->life=0;return;}
    for(step=0;step<(m->harmless?1u:3u)&&m->life;step++){
        int dx=m->dx,dy=m->dy,nx,ny;
        if(command==24){int tx=m->stage?bx:ax,ty=m->stage?by:ay,span_x,span_y,twice;
            if(m->x==tx&&m->y==ty){if(m->stage){m->life=0;break;}m->stage=1;tx=bx;ty=by;
                m->error=(short)(absolute(bx-ax)-absolute(by-ay));}
            span_x=absolute(tx-(m->stage?ax:southern_power_origin_x));
            span_y=absolute(ty-(m->stage?ay:southern_power_origin_y));
            twice=m->error*2;dx=dy=0;
            if(twice>=-span_y){m->error=(short)(m->error-span_y);dx=sign(tx-m->x);}
            if(twice<=span_x){m->error=(short)(m->error+span_x);dy=sign(ty-m->y);}
        }
        if(command==42&&southern_power_age>=19){m->stage=1;
            if(distance(m->x,m->y,cx,cy)<=3){m->life=0;break;}
            dx=sign(cx-m->x);dy=sign(cy-m->y);
        }
        nx=m->x+dx;ny=m->y+dy;
        if(!clear(m->x,m->y,nx,ny)){
            if(command==41&&!m->stage){int blocked_x=dx&&solid(m->x+dx,m->y),blocked_y=dy&&solid(m->x,m->y+dy);
                if(blocked_x||!blocked_y)dx=-dx;
                if(blocked_y||!blocked_x)dy=-dy;
                m->dx=(short)dx;m->dy=(short)dy;m->stage=1;
                nx=m->x+dx;ny=m->y+dy;if(!clear(m->x,m->y,nx,ny)){m->life=0;break;}
            }else {m->life=0;break;}
        }
        m->x=(short)nx;m->y=(short)ny;
        if(m->harmless)continue;
        for(i=0;i<6;i++)if(enemies[i].hp>0&&distance(nx,ny,enemies[i].x,enemies[i].y)<=5){
            unsigned damage=command==27?(m->stage?8u:16u):command==37?12u:command==41?20u:24u;
            if(hurt(i,damage,nx,ny,1)){
                if(command==37)slow(i);
                if(command==27&&!m->stage){int dx0=fx[southern_power_direction],dy0=fy[southern_power_direction];
                    missile(1,nx,ny,dx0-dy0,dy0+dx0,0);missile(2,nx,ny,dx0+dy0,dy0-dx0,0);
                    missiles[1].stage=missiles[2].stage=1;m->life=0;break;}
            }
        }
        if(command==37&&n==0&&distance(southern_power_origin_x,southern_power_origin_y,nx,ny)>=12){
            int dx0=fx[southern_power_direction],dy0=fy[southern_power_direction];
            missile(1,nx,ny,dx0-dy0,dy0+dx0,0);missile(2,nx,ny,dx0+dy0,dy0-dx0,0);m->life=0;
        }
    }
    if(m->life)m->life--;
}
static void geometry_tick(void){unsigned i;int age=southern_power_age;
    if(southern_power_kind==23){
        if(age<=4||(age>=9&&age<=12)){int n=age<=4?age:12-age;
            int tx=companion_start_x+fy[southern_power_direction]*n*2,ty=companion_start_y-fx[southern_power_direction]*n*2;
            if(!clear(ex,ey,tx,ty)){finish();return;}ex=tx;ey=ty;}
        if(age==6){int x1,y1,x2,y2;point(12,-18,&x1,&y1);point(12,2,&x2,&y2);
            if(clear(ex,ey,x1,y1))span_damage(x1,y1,x2,y2,4,16,0,0);}
    }else if(southern_power_kind==25&&age>=6&&age<=18){int reach=6+(age-6)*2;
        for(i=0;i<6;i++){int f,s;relative(enemies[i].x,enemies[i].y,&f,&s);
            if(f>=4&&f<=reach&&absolute(s)<=f/2&&hurt(i,20,southern_power_origin_x,southern_power_origin_y,1))
                push(i,fx[southern_power_direction],fy[southern_power_direction],6);}
    }else if(southern_power_kind==26&&age==30){
        if(origin_clear(ax,ay))span_damage(ax,ay,bx,by,7,20,1,0);
    }else if(southern_power_kind==30&&age>=6){int r=age>34?36:8+(age-6),lo=r-3,hi=r+3;
        for(i=0;i<6;i++){int x=enemies[i].x-southern_power_origin_x,y=enemies[i].y-southern_power_origin_y,d=x*x+y*y;
            if(d>=64&&d>=lo*lo&&d<=hi*hi)hurt(i,24,southern_power_origin_x,southern_power_origin_y,1);}
    }else if(southern_power_kind==32&&spent&&delayed){int x1,y1,x2,y2;
        int r=12+delayed*2;point(-8,r*guard_side,&x1,&y1);point(8,r*guard_side,&x2,&y2);
        if(origin_clear(x1,y1))span_damage(x1,y1,x2,y2,5,24,0,0);
        if(++delayed>10)delayed=0;
    }else if(southern_power_kind==34&&age>=6&&age<=30&&origin_clear(ax,ay)&&clear(ax,ay,bx,by)){
        for(i=0;i<6;i++){int f,s,pf,ps;relative(enemies[i].x,enemies[i].y,&f,&s);relative(previous_x[i],previous_y[i],&pf,&ps);
            if(((pf<24&&f>=24)||(pf>24&&f<=24))&&absolute(s)<=12&&absolute(ps)<=16&&
               clear(previous_x[i],previous_y[i],enemies[i].x,enemies[i].y))hurt(i,24,ax,ay,1);}
    }else if(southern_power_kind==38&&age>=6&&age<=26){
        crescent_damage();
    }
}
void southern_powers_tick(void){unsigned i;
    if(hitstop)return;
    if(southern_power_cast_time)southern_power_cast_time--;
    if(!southern_power_time)return;
    if(!active()){finish();return;}
    southern_power_age++;
    /* Remove an unspent mark before its final follow-up would outlive the cast. */
    if(!spent&&((southern_power_kind==29&&southern_power_time<=13)||
       ((southern_power_kind==39||southern_power_kind==40)&&southern_power_time<=9))){finish();return;}
    if(redirect_left)redirect_left--;
    if(guard_grace)guard_grace--;
    if(delayed&&(southern_power_kind==29||southern_power_kind==39||southern_power_kind==40)){
        if(--delayed==0){if(mark_live(0)&&cached_sight(&mark_sight[1],6,mark_a,delay_x,delay_y,enemies[mark_a].x,enemies[mark_a].y))
                confirmed_hurt(mark_a,southern_power_kind==40?24:16,southern_power_kind!=29);
            finish();return;}
    }
    if(southern_power_age==6){int dx=fx[southern_power_direction],dy=fy[southern_power_direction];
        if(southern_power_kind==24||southern_power_kind==27||southern_power_kind==37||southern_power_kind==41||southern_power_kind==42){
            missile(0,southern_power_origin_x,southern_power_origin_y,dx,dy,0);
            if(southern_power_kind==42){missile(1,southern_power_origin_x,southern_power_origin_y,dx-dy,dy+dx,0);
                missile(2,southern_power_origin_x,southern_power_origin_y,dx+dy,dy-dx,0);}
        }
    }
    geometry_tick();if(!southern_power_time)return;
    for(i=0;i<3;i++)missile_tick(i);
    if(spent&&((southern_power_kind==28&&!missiles[0].life&&!missiles[1].life)||
       ((southern_power_kind==35||southern_power_kind==36)&&!redirect_left)||
       (southern_power_kind>=31&&southern_power_kind<=33&&!guard_grace&&!delayed))){finish();return;}
    for(i=0;i<6;i++){previous_x[i]=(short)enemies[i].x;previous_y[i]=(short)enemies[i].y;}
    if(--southern_power_time==0)finish();
}
static void draw_checked(int x,int y,int large){
    if(draw_count>=24)return;
    draw_count++;
    obj_add(large?GFX_OBJ_POWER_PIN:GFX_OBJ_WATER_DROP,x-(large?8:4),y-(large?8:4),large?16:8,large?16:8,1,y+2,0);
}
static void particle(int x,int y,int large){if(!solid(x,y))draw_checked(x,y,large);}
static int draw_line(int x,int y,int tx,int ty){
    int dx=absolute(tx-x),dy=-absolute(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,err=dx+dy,count=0;
    if(distance(x,y,tx,ty)>96||solid(x,y))return 0;
    draw_checked(x,y,0);
    while(x!=tx||y!=ty){int twice=err*2,nx=x,ny=y;
        if(twice>=dy){err+=dy;nx+=sx;}if(twice<=dx){err+=dx;ny+=sy;}
        if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return 0;
        x=nx;y=ny;
        if(solid(x,y))return 0;
        if(++count==6||(x==tx&&y==ty)){draw_checked(x,y,0);count=0;}
    }return 1;
}
/* The exact same sampled raster as draw_line, called only with an endpoint-
 * and generation-keyed clear proof. Geometry mutation explicitly invalidates it. */
static void draw_known_line(int x,int y,int tx,int ty){
    int dx=absolute(tx-x),dy=-absolute(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,err=dx+dy,count=0;
    if(distance(x,y,tx,ty)>96)return;
    draw_checked(x,y,0);
    while(x!=tx||y!=ty){int twice=err*2;if(twice>=dy){err+=dy;x+=sx;}if(twice<=dx){err+=dx;y+=sy;}
        if(++count==6||(x==tx&&y==ty)){draw_checked(x,y,0);count=0;}
    }
}
void southern_powers_draw(void){unsigned i;int age=southern_power_age;
    if(!active())return;
    draw_count=0;
    switch(southern_power_kind){
    case 23:particle(ex,ey,1);if(age>=4){int x,y,tx,ty;point(12,-18,&x,&y);point(12,2,&tx,&ty);if(clear(ex,ey,x,y))draw_line(x,y,tx,ty);}break;
    case 24:draw_line(southern_power_origin_x,southern_power_origin_y,ax,ay);if(origin_clear(ax,ay))draw_line(ax,ay,bx,by);break;
    case 25:{int x,y,tx,ty,r=age<6?6:age>18?30:6+(age-6)*2;point(r,-r/2,&x,&y);point(r,r/2,&tx,&ty);
        draw_line(southern_power_origin_x,southern_power_origin_y,x,y);draw_line(southern_power_origin_x,southern_power_origin_y,tx,ty);break;}
    case 26:case 28:case 34:if(!(southern_power_kind==28&&spent)&&origin_clear(ax,ay)){draw_line(ax,ay,bx,by);particle(ax,ay,1);if(clear(ax,ay,bx,by))particle(bx,by,1);}break;
    case 29:case 39:case 40:if(mark_live(0)&&cached_sight(&mark_sight[0],6,mark_a,southern_power_origin_x,southern_power_origin_y,enemies[mark_a].x,enemies[mark_a].y))draw_checked(enemies[mark_a].x,enemies[mark_a].y,1);
        if(mark_live(0)&&mark_live(1)&&cached_sight(&mark_sight[1],mark_a,mark_b,enemies[mark_a].x,enemies[mark_a].y,enemies[mark_b].x,enemies[mark_b].y)){
            draw_known_line(enemies[mark_a].x,enemies[mark_a].y,enemies[mark_b].x,enemies[mark_b].y);draw_checked(enemies[mark_b].x,enemies[mark_b].y,1);
        }break;
    case 30:{static const signed char rx[8]={8,6,0,-6,-8,-6,0,6},ry[8]={0,6,8,6,0,-6,-8,-6};int r=age<6?8:age>34?36:8+age-6;
        for(i=0;i<8;i++){int x=southern_power_origin_x+rx[i]*r/8,y=southern_power_origin_y+ry[i]*r/8;if(origin_clear(x,y))particle(x,y,0);}break;}
    case 31:case 32:if(!spent&&origin_clear(ax,ay))particle(ax,ay,1);else if(delayed){int x,y;point(0,(12+delayed*2)*guard_side,&x,&y);if(origin_clear(x,y))particle(x,y,1);}break;
    case 33:{int x,y;point(12,0,&x,&y);if(!spent&&origin_clear(x,y))particle(x,y,1);break;}
    case 35:case 36:if(!spent||redirect_left){if(origin_clear(ax,ay))particle(ax,ay,1);
        if(southern_power_kind==36&&origin_clear(bx,by)){particle(bx,by,1);if(origin_clear(ax,ay))draw_line(ax,ay,bx,by);}}break;
    case 38:crescent_refresh();
        for(i=0;i<crescent_spans;i++){int x,y,tx,ty;point(crescent_f[i],crescent_s[i],&x,&y);point(crescent_f[i+1],crescent_s[i+1],&tx,&ty);
            if(i==0)draw_checked(x,y,1);
            /* Both even-delta segment midpoints lie on the validated sweep. */
            draw_checked((x+tx)/2,(y+ty)/2,0);draw_checked(tx,ty,1);
        }break;
    default:break;
    }
    for(i=0;i<3;i++)if(missiles[i].life)particle(missiles[i].x,missiles[i].y,!missiles[i].harmless);
}
