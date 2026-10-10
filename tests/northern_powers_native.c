/* Host-compiled native C harness, NOT an emulator/controller acceptance route.
 * Links the real gear damage runtime, catalog, old and new power handlers.
 * Only world collision, pool spawning, feedback and OBJ hardware are synthetic. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "northern_powers.h"
#include "regional_powers.h"
#include "advanced_powers.h"
#include "gear_runtime.h"
#include "gear_menu.h"
#include "progression.h"
#include "combat_rules.h"
#include "north_game.h"
#include "obj_layout.h"

typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
Enemy enemies[6];Shot shots[12];Save5State adventure_save;
volatile int hp,max_hp,px,py,boss_hp,boss_x,boss_y,room;
volatile int spirit,stone_guard,guard_invuln;
int cx,cy;
int keys,gfx_slash_frame,face,roll_ticks,swing,sword_cd,combo_step,combo_timer;
int attack_buffer,swing_damage,slash_id,hitstop,boss_flash,boss_armor;
int ability_cd,ability_max,enemy_windups[6],enemy_clocks[6],frame,power_effect;
static CreatureInstance caster;
static int absent,kills[6],uploads,draws,wall_count,boss_live;
static int solid_calls,record_draws,capture_count,capture_x[32],capture_y[32];
static unsigned char vram[16384];
static struct {int x,y,w,h;} walls[8];
static const unsigned forms[10]={19,20,22,23,73,74,75,76,77,78};
int solid(int x,int y){
    int i;solid_calls++;if(x<0||y<0||x>=480||y>=320)return 1;
    for(i=0;i<wall_count;i++)if(x>=walls[i].x&&x<walls[i].x+walls[i].w&&
       y>=walls[i].y&&y<walls[i].y+walls[i].h)return 1;
    return 0;
}
static void wall(int x,int y,int w,int h){assert(wall_count<8);walls[wall_count].x=x;
    walls[wall_count].y=y;walls[wall_count].w=w;walls[wall_count++].h=h;}
int near(int x,int y,int tx,int ty,int radius){return abs(x-tx)+abs(y-ty)<radius;}
int boss_active(void){return boss_live;}
int try_interaction(void){return 0;}
void move_player(int x,int y){px+=x/256;py+=y/256;}
CreatureInstance *progression_selected(void){return absent?0:&caster;}
void impact(int x,int y){(void)x;(void)y;}
void sfx(int n){(void)n;}
void kill_enemy(Enemy *e){unsigned i=(unsigned)(e-enemies);assert(i<6);assert(++kills[i]==1);e->hp=0;}
int north_game_target(int *x,int *y,int *radius){(void)x;(void)y;(void)radius;return 0;}
int north_game_weapon_hit(unsigned weapon_class,int x,int y,unsigned damage_q4){
    (void)weapon_class;(void)x;(void)y;(void)damage_q4;return 0;}
int south_game_target(int*x,int*y,int*r){(void)x;(void)y;(void)r;return 0;}
int south_game_weapon_hit(unsigned c,int x,int y,unsigned d){(void)c;(void)x;(void)y;(void)d;return 0;}
int region_game_practice_hit(unsigned c,int x,int y){(void)c;(void)x;(void)y;return 0;}
void obj_upload(const unsigned char *p,int w,int h,int off){
    assert(off>=0&&off+w*h<=16384);memcpy(vram+off,p,(size_t)(w*h));uploads++;
}
void obj_add(int off,int x,int y,int w,int h,int priority,int depth,int flip){
    (void)x;(void)y;(void)priority;(void)depth;(void)flip;
    assert(off>=0&&off+w*h<=16384);draws++;
    if(record_draws&&off==GFX_OBJ_WATER_DROP){assert(capture_count<32);
        capture_x[capture_count]=x+4;capture_y[capture_count++]=y+4;}
}
static void select_command(unsigned command){
    const CreatureForm *f=creatures_form(forms[command-13]);assert(f);
    memset(&caster,0,sizeof caster);caster.form_id=f->id;caster.flags=CREATURE_OCCUPIED;
    caster.level=30;caster.xp=creatures_xp_threshold(30);caster.bond=50;
    caster.instance_id=1;caster.polarity=f->polarity;caster.equipped[0]=(CreatureU8)command;
    assert(creatures_instance_validate(&caster));
}
static void setup(unsigned command){
    regional_powers_reset();northern_powers_reset();advanced_reset();
    northern_powers_tiles_release(NORTHERN_TILES_REGIONAL);
    memset(enemies,0,sizeof enemies);memset(shots,0,sizeof shots);memset(kills,0,sizeof kills);
    memset(shot_effects,0,sizeof shot_effects);memset(shot_phases,255,sizeof shot_phases);
    wall_count=absent=ability_cd=0;px=py=100;face=3;boss_live=0;
    stone_guard=guard_invuln=0;max_hp=6;equipment_init(&adventure_save.equipment);
    game_health_refresh(1);game_attacks_reset();select_command(command);
}
static void enemy(unsigned i,int x,int y,int hearts){
    enemies[i]=(Enemy){x,y,hearts,0,0};enemy_hp_q4[i]=hearts*16;enemy_phases[i]=255;
}
static void shot(unsigned i,int x,int y,int dx,int dy,int life,int owner){
    shots[i]=(Shot){x,y,dx,dy,life,owner};shot_phases[i]=CREATURE_FIRE;
    shot_effects[i]=SHOT_EFFECT_FIRE;northern_powers_shot_spawn(i);
}
static void updates(unsigned n){while(n--){northern_powers_tick();if(ability_cd)ability_cd--;}}
static void expect_damage(unsigned i,unsigned q4){assert(enemy_hp_q4[i]==160-(int)q4);}
static void test_every_command(void){
    unsigned c;
    for(c=13;c<=22;c++){
        setup(c);enemy(0,c==16?140:c==13?136:124,100,10);
        if(c==20)shot(0,120,100,-2,0,90,1);
        if(c>=21)shot(0,124,100,-2,0,90,1);
        assert(northern_power(c));assert(northern_power_kind==(int)c);
        assert(northern_power_form==(int)forms[c-13]);assert(northern_power_cast_time==20);
        assert(northern_power_time>0&&northern_power_time<=60);
        assert(northern_power_cooldown==(c&1?90:120));assert(northern_powers_busy());
        assert(game_gear_busy()&EQUIPMENT_BUSY_PLAYER_PROJECTILE);
        assert(!northern_power(c));
        updates(c==18?35:32);{int before=draws;northern_powers_draw();assert(draws-before<=20);}
        if(c<21)expect_damage(0,c==13?16:c==20?32:24);
        else {assert(!shots[0].owner);assert(shots[0].dx==0&&shots[0].dy==-2);
            assert(shot_effects[0]==SHOT_EFFECT_NONE&&shot_phases[0]==CREATURE_METAL);}
        updates(61);assert(!northern_power_time&&!northern_power_cast_time);
        assert(northern_powers_tiles_owner()==NORTHERN_TILES_NONE);
    }
}
static void test_selection_and_snapshot(void){
    unsigned i;int old_cd,old_uploads;
    setup(13);old_uploads=uploads;
    assert(!northern_power(12)&&!northern_power(0)&&!northern_power(23));
    assert(!northern_power(14));absent=1;assert(!northern_power(13));absent=0;
    caster.form_id=121;assert(!northern_power(13));caster.form_id=21;assert(!northern_power(13));
    select_command(14);caster.level=1;caster.xp=0;assert(!northern_power(14));
    select_command(13);caster.equipped[0]=14;assert(!northern_power(14));
    select_command(13);caster.flags=0;assert(!northern_power(13));
    select_command(13);caster.selected_command=2;assert(!northern_power(13));
    select_command(13);ability_cd=1;assert(!northern_power(13));ability_cd=0;
    face=4;assert(!northern_power(13));face=3;
    assert(uploads==old_uploads&&!ability_cd&&!northern_power_time);
    gear_stats.power_cooldown=EQUIPMENT_BASE_POWER_COOLDOWN-8;
    enemy(0,136,100,10);assert(northern_power(13));old_cd=ability_cd;
    assert(old_cd==82&&ability_max==82&&northern_power_cooldown==82);
    select_command(22);px=300;py=200;face=0;gear_stats.power_cooldown=1;
    for(i=0;i<100;i++)northern_powers_draw();
    assert(northern_power_time==18&&northern_power_age==0&&ability_cd==old_cd);
    assert(northern_power_form==19&&northern_power_direction==3);
    assert(northern_power_origin_x==100&&northern_power_origin_y==100);
    assert(!northern_powers_feedback(22));updates(1);
    assert(northern_power_time==17&&northern_power_cooldown==82&&northern_power_form==19);
    /* Hostile forged stat is bounded by gear8 + Feather8 + Bell4. */
    setup(13);gear_stats.power_cooldown=1;assert(GAME_MAX_POWER_RECOVERY==20);assert(northern_power(13));assert(ability_cd==70);
    setup(13);gear_stats.power_cooldown=EQUIPMENT_BASE_POWER_COOLDOWN+1;
    assert(northern_power(13));assert(ability_cd>=70&&ability_cd<=90);
}
static void test_delays_and_ledgers(void){
    unsigned c,i;
    for(c=15;c<=19;c+=4){
        setup(c);enemy(0,124,100,10);assert(northern_power(c));updates(17);expect_damage(0,0);
        updates(1);expect_damage(0,24);updates(60);expect_damage(0,24);
    }
    setup(16);enemy(0,116,100,10);enemy(1,140,100,10);assert(northern_power(16));
    updates(29);expect_damage(0,0);expect_damage(1,0);updates(1);expect_damage(1,24);expect_damage(0,0);
    setup(14);for(i=0;i<6;i++)enemy(i,124,88+(int)i*4,10);
    assert(northern_power(14));updates(1);for(i=0;i<6;i++)expect_damage(i,24);
    updates(59);for(i=0;i<6;i++)expect_damage(i,24);
    setup(14);enemy(0,110,100,10);assert(northern_power(14));updates(5);expect_damage(0,0);
    enemies[0].x=124;updates(1);expect_damage(0,24);enemies[0].x=110;updates(1);
    enemies[0].x=124;updates(1);expect_damage(0,24);
    setup(15);enemy(0,124,100,1);assert(northern_power(15));updates(60);
    assert(kills[0]==1&&enemies[0].hp==0&&enemy_hp_q4[0]==0);
    setup(20);enemy(0,124,100,10);assert(northern_power(20));updates(10);expect_damage(0,0);
    shot(0,120,100,-2,0,90,0);updates(1);assert(shots[0].life);expect_damage(0,0);
    shot(1,120,100,-2,0,90,1);shot(2,120,100,-2,0,90,1);updates(1);
    assert(shots[1].life==0&&shots[2].life==90);expect_damage(0,32);updates(40);expect_damage(0,32);
}
static void test_walls_displacement_and_phase(void){
    unsigned d;static const int dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};
    for(d=0;d<4;d++){
        setup(13);face=(int)d;enemy(0,100+dx[d]*36,100+dy[d]*36,10);
        assert(northern_power(13));assert(enemies[0].x==100+dx[d]*28&&enemies[0].y==100+dy[d]*28);
        setup(17);face=(int)d;enemy(0,100+dx[d]*20,100+dy[d]*20,10);
        wall(100+dx[d]*25,100+dy[d]*25,1,1);assert(northern_power(17));
        assert(enemies[0].x==100+dx[d]*24&&enemies[0].y==100+dy[d]*24);expect_damage(0,24);
        updates(10);assert(enemies[0].x==100+dx[d]*24&&enemies[0].y==100+dy[d]*24);
        setup(13);face=(int)d;enemy(0,100+dx[d]*36,100+dy[d]*36,10);
        wall(100+dx[d]*30,100+dy[d]*30,1,1);assert(northern_power(13));expect_damage(0,0);
        setup(15);face=(int)d;wall(100+dx[d]*24,100+dy[d]*24,1,1);
        assert(!northern_power(15)&&!ability_cd);
    }
    setup(13);enemy(0,136,105,10);assert(northern_power(13));
    assert(abs(enemies[0].x-136)+abs(enemies[0].y-105)<=8);
    setup(17);enemy(0,124,100,10);enemies[0].kind=3;boss_x=124;boss_y=100;boss_live=1;
    assert(northern_power(17));assert(enemies[0].x==124&&boss_x==124&&boss_y==100);
    setup(17);enemy(0,124,100,10);enemy_phases[0]=CREATURE_FIRE;assert(northern_power(17));
    assert(enemy_hp_q4[0]==160-(int)combat_damage_q4(24,0,0,CREATURE_WATER,CREATURE_FIRE,0));
    assert(enemy_hp_q4[0]%16!=0);assert(enemies[0].hp==(enemy_hp_q4[0]+15)/16);
    setup(14);wall(124,86,1,1);assert(!northern_power(14)&&!ability_cd);
    setup(14);wall(124,100,1,1);assert(!northern_power(14)&&!ability_cd);
    setup(15);enemy(0,129,100,10);assert(northern_power(15));wall(127,99,1,3);
    updates(25);expect_damage(0,0);
    setup(16);wall(130,100,1,1);assert(!northern_power(16));
    setup(16);enemy(0,140,100,10);assert(northern_power(16));wall(130,100,1,1);
    updates(35);assert(!northern_power_time);expect_damage(0,0);
    setup(18);wall(124,112,1,1);assert(!northern_power(18));
    setup(18);wall(124,124,1,1);assert(!northern_power(18));
    setup(18);enemy(0,124,124,10);enemy(1,146,124,10);assert(northern_power(18));
    updates(12);expect_damage(0,0);updates(24);expect_damage(0,24);expect_damage(1,0);
    setup(18);enemy(0,124,124,10);assert(northern_power(18));updates(23);
    wall(124,111,1,1);updates(20);assert(!northern_power_time);expect_damage(0,0);
    setup(18);enemy(0,130,106,10);assert(northern_power(18));wall(127,100,1,12);
    updates(48);expect_damage(0,0);
}
static void test_reflection_generation_and_reset(void){
    unsigned i;
    setup(21);shot(0,124,100,-2,0,80,1);shot(1,126,100,-2,0,80,1);
    assert(northern_power(21));updates(1);assert(!shots[0].owner&&shots[1].owner);
    assert(shots[0].dx==0&&shots[0].dy==-2&&shots[0].life==48);
    assert(northern_powers_shot_is_reflected(0));assert(northern_powers_busy());
    updates(20);assert(!northern_power_time&&northern_powers_busy());
    shots[0].life=0;assert(!northern_powers_busy());
    setup(21);shot(0,124,100,-2,1,5,1);assert(northern_power(21));updates(1);
    assert(shots[0].dx==-1&&shots[0].dy==-2&&shots[0].life==5);
    setup(21);shot(0,124,100,2,0,90,1);assert(northern_power(21));updates(1);assert(shots[0].owner);
    setup(21);shot(0,124,100,-2,0,90,1);assert(northern_power(21));wall(124,99,1,1);
    updates(1);assert(shots[0].owner);
    setup(22);for(i=0;i<3;i++)shot(i,124,100,-2,0,90,1);
    assert(northern_power(22));updates(1);assert(!shots[0].owner&&!shots[1].owner&&shots[2].owner);
    updates(10);assert(shots[2].owner);
    setup(22);shot(0,124,100,-2,0,90,1);assert(northern_power(22));updates(1);
    /* Ownership changes alone do not create a new projectile identity. */
    shots[0].owner=1;shots[0].dx=-2;shots[0].dy=0;updates(1);assert(shots[0].owner);
    /* A newly spawned projectile in that same slot is distinct and eligible. */
    shot(0,124,100,-2,0,90,1);updates(1);assert(!shots[0].owner);
    shot(0,124,100,-2,0,90,1);updates(1);assert(shots[0].owner); /* limit two */
    setup(22);assert(northern_power(22));updates(46);shot(0,124,100,-2,0,90,1);
    updates(1);assert(!shots[0].owner&&shots[0].life==13);
    northern_powers_reset();assert(!shots[0].life&&!northern_powers_busy());
    assert(!northern_power_time&&!northern_power_cast_time&&!northern_power_form);
    setup(22);shot(0,124,100,-2,0,90,1);assert(northern_power(22));updates(1);
    shot(0,124,100,-2,0,90,1);northern_powers_reset();assert(shots[0].life==90&&shots[0].owner);
    assert(!northern_powers_shot_is_reflected(12));northern_powers_shot_spawn(12);
}
/* Rendering must retain its conservative visible prefix when a mechanism
 * inserts a wall after the cast. Exercise all29 pixels, including endpoints,
 * in each direction, not just static cast-placement checks. */
static void test_render_sweep(void){
    unsigned d;int barrier,i;
    static const int dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};
    for(d=0;d<4;d++)for(barrier=0;barrier<=29;barrier++){
        int x,y,sx=-dy[d],sy=dx[d];
        setup(14);face=(int)d;assert(northern_power(14));
        x=100+dx[d]*24+dy[d]*14;y=100+dy[d]*24-dx[d]*14;
        if(barrier<=28)wall(x+sx*barrier,y+sy*barrier,1,1);
        capture_count=0;solid_calls=0;record_draws=1;northern_powers_draw();record_draws=0;
        assert(capture_count<=10&&solid_calls<=31);
        for(i=0;i<capture_count;i++){
            int along=(capture_x[i]-x)*sx+(capture_y[i]-y)*sy;
            assert(along>=0&&along<=28&&along<barrier);
        }
        if(barrier==0)assert(!capture_count);
        if(barrier==29){assert(capture_count==6);assert(solid_calls==31);
            assert(capture_x[0]==x&&capture_y[0]==y);
            assert(capture_x[5]==x+sx*28&&capture_y[5]==y+sy*28);}
    }
    /* A diagonal tether must also stop at a touching corner obstacle. */
    setup(13);enemy(0,136,105,10);assert(northern_power(13));wall(103,100,1,1);
    capture_count=0;record_draws=1;northern_powers_draw();record_draws=0;
    assert(capture_count==1&&capture_x[0]==100&&capture_y[0]==100);
    setup(13);enemy(0,136,105,10);assert(northern_power(13));wall(102,101,1,1);
    capture_count=0;record_draws=1;northern_powers_draw();record_draws=0;
    assert(capture_count==1&&capture_x[0]==100&&capture_y[0]==100);
    /* The bent surge remains within the previous20-OBJ draw budget. */
    setup(18);assert(northern_power(18));i=draws;northern_powers_draw();assert(draws-i<=20);
}
static void test_cancelled_effects(void){
    unsigned c;
    for(c=13;c<=22;c++){
        int before;setup(c);enemy(0,c==16?140:124,100,10);
        assert(northern_power(c));before=enemy_hp_q4[0];
        northern_powers_reset();updates(90);assert(enemy_hp_q4[0]==before);
        assert(!northern_powers_busy()&&!northern_power_cast_time);
        assert(northern_powers_tiles_owner()==NORTHERN_TILES_NONE);
    }
}
static void test_feedback_and_tiles_concurrency(void){
    int old_uploads,old_draws,i;unsigned generation;unsigned char saved[16384];
    setup(15);assert(northern_powers_tiles_claim(NORTHERN_TILES_SOUTHERN));
    assert(!northern_powers_tiles_claim(NORTHERN_TILES_SOUTHERN));
    assert(!northern_power(15)&&!regional_power(11));
    assert(northern_powers_tiles_release(NORTHERN_TILES_SOUTHERN));
    setup(15);old_uploads=uploads;ability_cd=71;
    assert(northern_powers_feedback(15));assert(northern_power_cast_time==20);
    assert(!northern_powers_busy()&&!northern_power_time&&ability_cd==71&&uploads==old_uploads);
    assert(northern_powers_tiles_owner()==NORTHERN_TILES_NONE);assert(!game_gear_busy());
    updates(19);assert(northern_power_cast_time==1);updates(1);assert(!northern_power_cast_time);
    setup(15);assert(regional_power(11));old_uploads=uploads;ability_cd=0;
    assert(!northern_power(15)&&uploads==old_uploads);
    regional_powers_reset();northern_powers_tiles_release(NORTHERN_TILES_REGIONAL);
    assert(northern_power(15));old_uploads=uploads;assert(!regional_power(11)&&uploads==old_uploads);
    updates(36);assert(regional_power(11));regional_powers_reset();
    northern_powers_tiles_release(NORTHERN_TILES_REGIONAL);
    setup(15);assert(northern_powers_tiles_claim(NORTHERN_TILES_REGIONAL));
    regional_power_time=12;old_uploads=uploads;generation=northern_powers_tiles_generation();
    assert(!northern_power(15)&&uploads==old_uploads&&!ability_cd);
    assert(!northern_powers_tiles_release(NORTHERN_TILES_REGIONAL));regional_power_time=0;
    assert(northern_powers_tiles_release(NORTHERN_TILES_REGIONAL));
    assert(northern_power(15));assert(northern_powers_tiles_generation()!=generation);
    assert(!northern_powers_tiles_claim(NORTHERN_TILES_REGIONAL));
    assert(!northern_powers_tiles_claim(NORTHERN_TILES_NORTHERN));
    assert(!northern_powers_tiles_release(NORTHERN_TILES_NORTHERN));
    updates(36);assert(northern_powers_tiles_claim(NORTHERN_TILES_REGIONAL));
    old_draws=draws;northern_powers_draw();assert(draws==old_draws);
    northern_powers_tiles_release(NORTHERN_TILES_REGIONAL);
    /* Real legacy advanced Fire visuals plus two real gear arrows/new Northern
     * tiles. Guard every unrelated OBJ byte, including phase/heart/arrow caches. */
    setup(18);assert(advanced_power(5));ability_cd=0;
    player_arrows[0]=(WeaponArrow){100*256,100*256,120*256,1024,1,0,32,0,0,255,{0,0}};
    player_arrows[1]=player_arrows[0];player_arrows[1].direction=3;game_draw_weapon();
    memcpy(saved,vram,sizeof saved);assert(northern_power(18));
    for(i=0;i<16384;i++)if(!(i>=GFX_OBJ_POWER_PIN&&i<GFX_OBJ_POWER_PIN+256)&&
       !(i>=GFX_OBJ_WATER_DROP&&i<GFX_OBJ_WATER_DROP+64))assert(saved[i]==vram[i]);
    memcpy(saved,vram,sizeof saved);
    for(i=0;i<10;i++){advanced_tick();northern_powers_tick();advanced_draw();northern_powers_draw();game_draw_weapon();}
    assert(advanced_time_left>0&&northern_power_time>0);
    assert(!memcmp(saved+GFX_OBJ_POWER_PIN,vram+GFX_OBJ_POWER_PIN,256));
    assert(!memcmp(saved+GFX_OBJ_WATER_DROP,vram+GFX_OBJ_WATER_DROP,64));
    assert(!memcmp(saved+GFX_OBJ_PLAYER_ARROW,vram+GFX_OBJ_PLAYER_ARROW,128));
    assert(!memcmp(saved+GFX_OBJ_PHASE_ICONS,vram+GFX_OBJ_PHASE_ICONS,320));
    assert(!northern_powers_tiles_claim(99));northern_powers_reset();advanced_reset();
}
int main(void){
    assert(creatures_catalog_validate());test_every_command();test_selection_and_snapshot();
    test_delays_and_ledgers();test_walls_displacement_and_phase();
    test_reflection_generation_and_reset();test_render_sweep();test_cancelled_effects();test_feedback_and_tiles_concurrency();
    puts("PASS Northern host C: ten commands, sparse validation, Q4/phase damage, delays, hit ledgers, swept displacement/LOS, bent wake, 90-degree generation-safe reflection, reset/freeze/snapshots, feedback, bounded lifetimes, shared OBJ lease, legacy advanced effect + two arrows");
    setup(14);assert(northern_power(14));solid_calls=0;northern_powers_draw();
    printf("Command14 draw solid() calls: %d\n",solid_calls);
    puts("This is host C integration coverage; native controller/gameplay acceptance remains separate.");return 0;
}
