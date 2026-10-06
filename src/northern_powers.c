/* Bounded Northern companion combat. No field tags are inferred from phase,
 * ownership, or form. Geometry and damage are deliberately separate. */
#include "northern_powers.h"
#include "northern_power_art.h"
#include "advanced_powers.h"
#include "regional_powers.h"
#include "gear_runtime.h"
#include "progression.h"
#include "obj_layout.h"
#include "combat_rules.h"

typedef struct { int x,y,hp,flash,kind; } Enemy;
typedef struct { int x,y,dx,dy,life,owner; } Shot;
extern Enemy enemies[6];
extern Shot shots[12];
extern volatile int px,py;
extern int face,ability_cd,ability_max,enemy_windups[6];
extern int southern_power_time;
extern int solid(int,int);
extern void kill_enemy(Enemy *),impact(int,int),sfx(int);
extern void obj_upload(const unsigned char *,int,int,int);
extern void obj_add(int,int,int,int,int,int,int,int);

int northern_power_kind,northern_power_time,northern_power_form;
int northern_power_direction,northern_power_origin_x,northern_power_origin_y;
int northern_power_age,northern_power_cooldown,northern_power_cast_time;
static int ax,ay,bx,by,effect_x,effect_y,travel,pulse_age;
static unsigned char enemy_hits,redirect_count;
static unsigned short shot_serial[12],turned_serial[12],friendly_serial[12];
static unsigned short turned_slots,friendly_slots;
static unsigned tile_owner,tile_generation,cast_tile_generation;
typedef struct { unsigned char phase,lifetime; } PowerSpec;
static const PowerSpec specs[10]={
    {CREATURE_WOOD,18},{CREATURE_WOOD,60},
    {CREATURE_FIRE,36},{CREATURE_FIRE,48},
    {CREATURE_WATER,18},{CREATURE_WATER,48},
    {CREATURE_EARTH,36},{CREATURE_EARTH,48},
    {CREATURE_METAL,18},{CREATURE_METAL,48}
};
static const signed char forward_x[4]={0,0,-1,1};
static const signed char forward_y[4]={1,-1,0,0};
static int absolute(int n){return n<0?-n:n;}
static int sign(int n){return (n>0)-(n<0);}
static int near_point(int x,int y,int tx,int ty,int radius){
    return absolute(x-tx)+absolute(y-ty)<=radius;
}
/* Includes both endpoints. Check side-adjacent pixels at diagonal corners as
 * well, so a line cannot leak between two touching blocked squares. */
static int clear_segment(int x,int y,int tx,int ty){
    int dx=absolute(tx-x),dy=-absolute(ty-y),sx=x<tx?1:-1;
    int sy=y<ty?1:-1,error=dx+dy;
    if(solid(x,y)||solid(tx,ty))return 0;
    while(x!=tx||y!=ty){
        int twice=error*2,nx=x,ny=y;
        if(twice>=dy){error+=dy;nx+=sx;}
        if(twice<=dx){error+=dx;ny+=sy;}
        if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return 0;
        x=nx;y=ny;
        if(solid(x,y))return 0;
    }
    return 1;
}
static void point_at(int forward,int side,int *x,int *y){
    int dx=forward_x[northern_power_direction],dy=forward_y[northern_power_direction];
    *x=northern_power_origin_x+dx*forward-dy*side;
    *y=northern_power_origin_y+dy*forward+dx*side;
}
static void relative(int x,int y,int *forward,int *side){
    int dx=forward_x[northern_power_direction],dy=forward_y[northern_power_direction];
    x-=northern_power_origin_x;y-=northern_power_origin_y;
    *forward=x*dx+y*dy;*side=-x*dy+y*dx;
}
static int origin_clear(int x,int y){
    return clear_segment(northern_power_origin_x,northern_power_origin_y,x,y);
}
unsigned northern_powers_tiles_owner(void){return tile_owner;}
unsigned northern_powers_tiles_generation(void){return tile_generation;}
int northern_powers_tiles_claim(unsigned owner){
    if(owner!=NORTHERN_TILES_REGIONAL&&owner!=NORTHERN_TILES_NORTHERN&&
       owner!=NORTHERN_TILES_SOUTHERN)return 0;
    /* Also protect a regional effect created before the lease adapter was wired. */
    if(tile_owner!=NORTHERN_TILES_NONE||northern_power_time>0||regional_power_time>0||
       southern_power_time>0)return 0;
    tile_owner=owner;tile_generation++;
    return 1;
}
int northern_powers_tiles_release(unsigned owner){
    if(owner!=tile_owner||owner==NORTHERN_TILES_NONE)return 0;
    if((owner==NORTHERN_TILES_NORTHERN&&northern_power_time>0)||
       (owner==NORTHERN_TILES_REGIONAL&&regional_power_time>0)||
       (owner==NORTHERN_TILES_SOUTHERN&&southern_power_time>0))return 0;
    tile_owner=NORTHERN_TILES_NONE;tile_generation++;
    return 1;
}
void northern_powers_shot_spawn(unsigned i){
    if(i>=12)return;
    shot_serial[i]++;
    /* Clear the slot marks as well: even generation wrap cannot alias a cast. */
    turned_slots&=(unsigned short)~(1u<<i);
    friendly_slots&=(unsigned short)~(1u<<i);
}
int northern_powers_shot_is_reflected(unsigned i){
    return i<12&&(friendly_slots&(1u<<i))&&friendly_serial[i]==shot_serial[i]&&
        shots[i].life>0&&!shots[i].owner&&shot_phases[i]==CREATURE_METAL&&
        shot_effects[i]==SHOT_EFFECT_NONE;
}
int northern_powers_busy(void){
    unsigned i;
    if(northern_power_time>0)return 1;
    for(i=0;i<12;i++)if(northern_powers_shot_is_reflected(i))return 1;
    return 0;
}
void northern_powers_reset(void){
    unsigned i;
    /* Do not kill an unrelated recycled hostile or friendly slot. */
    for(i=0;i<12;i++)if(northern_powers_shot_is_reflected(i)){
        shots[i].life=0;shot_effects[i]=SHOT_EFFECT_NONE;
        shot_phases[i]=COMBAT_NEUTRAL_PHASE;
    }
    northern_power_kind=northern_power_time=northern_power_form=0;
    northern_power_age=northern_power_cooldown=northern_power_direction=0;
    northern_power_cast_time=0;
    northern_power_origin_x=northern_power_origin_y=0;
    ax=ay=bx=by=effect_x=effect_y=travel=pulse_age=0;
    enemy_hits=redirect_count=0;turned_slots=friendly_slots=0;
    northern_powers_tiles_release(NORTHERN_TILES_NORTHERN);
}
static void finish_effect(void){
    northern_power_time=0;
    northern_powers_tiles_release(NORTHERN_TILES_NORTHERN);
}
static int hurt(unsigned i,unsigned q4,unsigned phase,int x,int y){
    Enemy *e=&enemies[i];
    if(e->hp<=0||(enemy_hits&(1u<<i))||!clear_segment(x,y,e->x,e->y))return 0;
    enemy_hits|=(unsigned char)(1u<<i);
    game_enemy_hurt(i,q4,0,phase);
    e->flash=16;enemy_windups[i]=0;impact(e->x,e->y);
    if(e->hp<=0)kill_enemy(e);
    return 1;
}
static void radius_damage(int x,int y,int radius,unsigned q4,unsigned phase){
    unsigned i;
    for(i=0;i<6;i++)if(enemies[i].hp>0&&
       near_point(x,y,enemies[i].x,enemies[i].y,radius))hurt(i,q4,phase,x,y);
}
/* Each step moves exactly one pixel in one axis; displacement is <=the budget
 * even diagonally. Only the three existing ordinary pool kinds can move. Bosses
 * use a separate runtime and are never addressed or moved here. */
static void displace(unsigned i,int dx,int dy,unsigned budget,int pull){
    Enemy *e=&enemies[i];unsigned step;
    if(e->hp<=0||(unsigned)e->kind>2)return;
    for(step=0;step<budget;step++){
        int nx=e->x,ny=e->y;
        if(pull){
            int x=northern_power_origin_x-e->x,y=northern_power_origin_y-e->y;
            if(absolute(x)+absolute(y)<=12)break;
            if(absolute(x)>=absolute(y))nx+=sign(x);else ny+=sign(y);
        }else {nx+=dx;ny+=dy;}
        if(solid(nx,ny)||!clear_segment(e->x,e->y,nx,ny))break;
        e->x=nx;e->y=ny;
    }
}
static void threadhold(void){
    unsigned i,chosen=6;int best=49;
    for(i=0;i<6;i++)if(enemies[i].hp>0){
        int f,s;relative(enemies[i].x,enemies[i].y,&f,&s);
        if(f>=6&&f<best&&absolute(s)<=5&&origin_clear(enemies[i].x,enemies[i].y)){
            chosen=i;best=f;
        }
    }
    if(chosen<6){
        hurt(chosen,16,CREATURE_WOOD,northern_power_origin_x,northern_power_origin_y);
        displace(chosen,0,0,8,1);ax=enemies[chosen].x;ay=enemies[chosen].y;
    }
}
static void washback(void){
    unsigned i;
    for(i=0;i<6;i++)if(enemies[i].hp>0){
        int f,s;relative(enemies[i].x,enemies[i].y,&f,&s);
        if(f>=4&&f<=28&&absolute(s)<=12&&
           hurt(i,24,CREATURE_WATER,northern_power_origin_x,northern_power_origin_y))
            displace(i,forward_x[northern_power_direction],forward_y[northern_power_direction],10,0);
    }
}
/* Cast geometry is validated before any authoritative state, cooldown or tile
 * is changed. Distances are at most 48; no grid buffers or unbounded searches. */
static int prepare_geometry(unsigned command,int x,int y,int direction,
                            int *out_ax,int *out_ay,int *out_bx,int *out_by){
    int dx=forward_x[direction],dy=forward_y[direction];
    int distance=command==13?48:command==16?16:command==20||command==21?20:24;
    int x1=x+dx*distance,y1=y+dy*distance,x2=x1,y2=y1;
    if(solid(x,y))return 0;
    if(command==13||command==17){
        int step;distance=command==13?48:24;x1=x;y1=y;
        for(step=0;step<distance;step++){
            int nx=x1+dx,ny=y1+dy;
            if(solid(nx,ny))break;
            x1=nx;y1=ny;
        }
        if(x1==x&&y1==y)return 0;
        x2=x1;y2=y1;
    }else if(command==14){x1+=dy*14;y1-=dx*14;x2-=dy*14;y2+=dx*14;}
    else if(command==16){x2=x+dx*40;y2=y+dy*40;}
    else if(command==18){x2-=dy*24;y2+=dx*24;}
    if(!clear_segment(x,y,x1,y1)||!clear_segment(x1,y1,x2,y2))return 0;
    /* The bent wake intentionally checks its two segments rather than an
     * imaginary straight shortcut from caster to the final endpoint. */
    if(command!=18&&!clear_segment(x,y,x2,y2))return 0;
    *out_ax=x1;*out_ay=y1;*out_bx=x2;*out_by=y2;
    return 1;
}
int northern_power(unsigned command){
    CreatureInstance *c;const CreatureAbility *ability;const PowerSpec *spec;
    int x1,y1,x2,y2;unsigned base,cooldown;
    if(command<13||command>22||ability_cd||northern_power_time||regional_power_time)return 0;
    c=progression_selected();ability=creatures_ability(command);spec=&specs[command-13];
    if(!c||!creatures_instance_validate(c)||!creatures_form(c->form_id)||
       c->selected_command>1||c->equipped[c->selected_command]!=command||
       !creatures_command_learned(c->form_id,c->level,command)||!ability||
       ability->phase!=spec->phase||ability->cooldown_updates<90||face<0||face>3)return 0;
    if(!prepare_geometry(command,px,py,face,&x1,&y1,&x2,&y2))return 0;
    if(!northern_powers_tiles_claim(NORTHERN_TILES_NORTHERN))return 0;
    base=ability->cooldown_updates;cooldown=game_power_cooldown(base);
    if(cooldown<base-8)cooldown=base-8;
    if(cooldown>base)cooldown=base;
    northern_power_kind=(int)command;northern_power_time=spec->lifetime;
    northern_power_form=c->form_id;northern_power_direction=face;
    northern_power_origin_x=px;northern_power_origin_y=py;
    northern_power_age=0;northern_power_cooldown=(int)cooldown;northern_power_cast_time=20;
    ability_max=ability_cd=(int)cooldown;
    ax=x1;ay=y1;bx=x2;by=y2;effect_x=ax;effect_y=ay;
    if(command==18){effect_x=px;effect_y=py;}
    travel=pulse_age=0;enemy_hits=redirect_count=0;turned_slots=0;
    cast_tile_generation=tile_generation;
    obj_upload(northern_power_marks[spec->phase],16,16,GFX_OBJ_POWER_PIN);
    obj_upload(northern_power_particles[spec->phase],8,8,GFX_OBJ_WATER_DROP);
    sfx(2);
    if(command==13)threadhold();
    if(command==17)washback();
    return 1;
}
static void span_damage(void){
    unsigned i;
    if(!origin_clear(ax,ay)||!origin_clear(bx,by)||!clear_segment(ax,ay,bx,by))return;
    for(i=0;i<6;i++)if(enemies[i].hp>0){
        int f,s,x,y;relative(enemies[i].x,enemies[i].y,&f,&s);
        if(absolute(f-24)>5||absolute(s)>14)continue;
        point_at(24,s,&x,&y);hurt(i,24,CREATURE_WOOD,x,y);
    }
}
static void drawer_tick(void){
    /* First pad waits 12 updates, translates every pixel over 12 updates,
     * then waits until update 30 to burst at the second visible pad. */
    if(northern_power_age>=12&&northern_power_age<24){
        unsigned step;
        for(step=0;step<2;step++){
            int nx=effect_x+forward_x[northern_power_direction];
            int ny=effect_y+forward_y[northern_power_direction];
            if(!clear_segment(effect_x,effect_y,nx,ny)){finish_effect();return;}
            effect_x=nx;effect_y=ny;travel++;
        }
    }
    if(northern_power_age>=30&&northern_power_age<38&&travel==24&&
       origin_clear(ax,ay)&&clear_segment(ax,ay,bx,by))
        radius_damage(bx,by,14,24,CREATURE_FIRE);
}
static void wake_tick(void){
    unsigned step;
    if(northern_power_age<=12||travel>=48)return;
    for(step=0;step<2&&travel<48;step++){
        int dx=forward_x[northern_power_direction],dy=forward_y[northern_power_direction];
        int nx=effect_x+(travel<24?dx:-dy),ny=effect_y+(travel<24?dy:dx);
        if(!clear_segment(effect_x,effect_y,nx,ny)){finish_effect();return;}
        /* Recheck the already-travelled segment, too, if a room mechanism moves. */
        if((travel<24&&!origin_clear(nx,ny))||
           (travel>=24&&(!origin_clear(ax,ay)||!clear_segment(ax,ay,nx,ny)))){
            finish_effect();return;
        }
        effect_x=nx;effect_y=ny;travel++;
        radius_damage(effect_x,effect_y,8,24,CREATURE_WATER);
    }
}
static int can_turn(unsigned i){
    int f,s,nx,ny;Shot *shot=&shots[i];
    if(shot->life<=0||!shot->owner||(!shot->dx&&!shot->dy)||
       shot->dx < -8||shot->dx > 8||shot->dy < -8||shot->dy > 8||
       (turned_slots&(1u<<i)&&turned_serial[i]==shot_serial[i]))return 0;
    relative(shot->x,shot->y,&f,&s);
    if(shot->dx*forward_x[northern_power_direction]+
       shot->dy*forward_y[northern_power_direction]>=0)return 0;
    if(absolute(s)>12||(northern_power_kind==21?(f<8||f>40):(absolute(f-24)>6)))return 0;
    if(!origin_clear(ax,ay)||!clear_segment(ax,ay,shot->x,shot->y))return 0;
    nx=shot->x-shot->dy;ny=shot->y+shot->dx;
    return clear_segment(shot->x,shot->y,nx,ny);
}
static void metal_tick(void){
    unsigned i,limit=northern_power_kind==21?1u:2u;
    for(i=0;i<12&&redirect_count<limit;i++)if(can_turn(i)){
        Shot *shot=&shots[i];int dx=shot->dx;
        shot->dx=-shot->dy;shot->dy=dx;shot->owner=0;
        /* Keep its original shorter life. No indefinite refund or stale Fire
         * field permissions, and the friendly missile gets at most48 updates. */
        if(shot->life>48)shot->life=48;
        if(shot->life>60-northern_power_age)shot->life=60-northern_power_age;
        shot_effects[i]=SHOT_EFFECT_NONE;shot_phases[i]=CREATURE_METAL;
        turned_slots|=(unsigned short)(1u<<i);turned_serial[i]=shot_serial[i];
        friendly_slots|=(unsigned short)(1u<<i);friendly_serial[i]=shot_serial[i];
        redirect_count++;impact(shot->x,shot->y);
    }
}
static void weight_tick(void){
    unsigned i;
    if(!origin_clear(ax,ay))return;
    if(!pulse_age)for(i=0;i<12;i++)if(shots[i].life>0&&shots[i].owner&&
        near_point(ax,ay,shots[i].x,shots[i].y,10)&&
        clear_segment(ax,ay,shots[i].x,shots[i].y)){
        shots[i].life=0;shot_effects[i]=SHOT_EFFECT_NONE;
        shot_phases[i]=COMBAT_NEUTRAL_PHASE;pulse_age=northern_power_age;break;
    }
    if(pulse_age&&northern_power_age-pulse_age<6)radius_damage(ax,ay,22,32,CREATURE_EARTH);
}
int northern_powers_feedback(unsigned command){
    CreatureInstance *c=progression_selected();
    if(command<13||command>22||northern_power_time||!c||
       !creatures_instance_validate(c)||!creatures_form(c->form_id)||
       c->selected_command>1||c->equipped[c->selected_command]!=command||
       !creatures_command_learned(c->form_id,c->level,command)||
       !creatures_ability(command)||face<0||face>3)return 0;
    northern_power_kind=(int)command;northern_power_form=c->form_id;
    northern_power_direction=face;northern_power_origin_x=px;northern_power_origin_y=py;
    northern_power_cast_time=20;return 1;
}
void northern_powers_tick(void){
    if(northern_power_cast_time>0)northern_power_cast_time--;
    if(northern_power_time<=0)return;
    if(tile_owner!=NORTHERN_TILES_NORTHERN||cast_tile_generation!=tile_generation){
        finish_effect();return;
    }
    northern_power_age++;
    switch(northern_power_kind){
    case 14:span_damage();break;
    case 15:
        if(northern_power_age>=18&&northern_power_age<26&&origin_clear(ax,ay))
            radius_damage(ax,ay,14,24,CREATURE_FIRE);
        break;
    case 16:drawer_tick();break;
    case 17:if(northern_power_age<=8)washback();break;
    case 18:wake_tick();break;
    case 19:
        if(northern_power_age>=18&&northern_power_age<22&&origin_clear(ax,ay))
            radius_damage(ax,ay,14,24,CREATURE_EARTH);
        break;
    case 20:weight_tick();break;
    case 21:case 22:metal_tick();break;
    default:break;
    }
    if(northern_power_time>0&&--northern_power_time==0)finish_effect();
}
static void particle(int x,int y){
    if(!solid(x,y))obj_add(GFX_OBJ_WATER_DROP,x-4,y-4,8,8,1,y+2,0);
}
static void mark(int x,int y){
    if(!solid(x,y))obj_add(GFX_OBJ_POWER_PIN,x-8,y-8,16,16,1,y+1,0);
}
/* Sweep a visible prefix once, not once per particle. Sampling has no integer
 * division and never skips collision pixels or the two cells touching a
 * diagonal corner. The 48-pixel authored paths need at most nine samples; the
 * explicit ten-OBJ cap remains even if a later caller changes a segment. */
static void draw_line(int x,int y,int tx,int ty){
    int dx=absolute(tx-x),dy=-absolute(ty-y),sx=x<tx?1:-1;
    int sy=y<ty?1:-1,error=dx+dy,until_sample=6,samples=1;
    if(solid(x,y))return;
    obj_add(GFX_OBJ_WATER_DROP,x-4,y-4,8,8,1,y+2,0);
    while(x!=tx||y!=ty){
        int twice=error*2,nx=x,ny=y;
        if(twice>=dy){error+=dy;nx+=sx;}
        if(twice<=dx){error+=dx;ny+=sy;}
        if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return;
        x=nx;y=ny;
        if(solid(x,y))return;
        until_sample--;
        if(samples<10&&(!until_sample||(x==tx&&y==ty))){
            /* This exact center was checked above; particle() would repeat it. */
            obj_add(GFX_OBJ_WATER_DROP,x-4,y-4,8,8,1,y+2,0);
            samples++;until_sample=6;
        }
    }
}
void northern_powers_draw(void){
    int x,y;
    if(!northern_power_time||tile_owner!=NORTHERN_TILES_NORTHERN||
       cast_tile_generation!=tile_generation)return;
    switch(northern_power_kind){
    case 13:draw_line(northern_power_origin_x,northern_power_origin_y,ax,ay);mark(ax,ay);break;
    case 14:draw_line(ax,ay,bx,by);mark(ax,ay);mark(bx,by);break;
    case 15:case 19:mark(ax,ay);if(northern_power_age>=18){
        particle(ax-10,ay);particle(ax+10,ay);particle(ax,ay-10);particle(ax,ay+10);
        }break;
    case 16:particle(ax,ay);particle(bx,by);draw_line(ax,ay,bx,by);mark(effect_x,effect_y);break;
    case 17:point_at(8+northern_power_age,0,&x,&y);mark(x,y);
        point_at(8+northern_power_age,-10,&x,&y);particle(x,y);
        point_at(8+northern_power_age,10,&x,&y);particle(x,y);break;
    case 18:draw_line(northern_power_origin_x,northern_power_origin_y,ax,ay);
        draw_line(ax,ay,bx,by);particle(ax,ay);particle(bx,by);mark(effect_x,effect_y);break;
    case 20:mark(ax,ay);if(pulse_age){particle(ax-14,ay);particle(ax+14,ay);
        particle(ax,ay-14);particle(ax,ay+14);}break;
    case 21:case 22:
        /* A fixed crossbar and a visible elbow show the clockwise side exit. */
        point_at(northern_power_kind==21?20:24,-12,&x,&y);particle(x,y);
        point_at(northern_power_kind==21?20:24,12,&x,&y);particle(x,y);
        mark(ax,ay);point_at(northern_power_kind==21?20:24,-24,&x,&y);
        draw_line(ax,ay,x,y);break;
    default:break;
    }
}
