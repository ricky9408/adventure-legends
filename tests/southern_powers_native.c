/* Host-compiled native C harness, NOT an emulator/controller acceptance route.
 * Links the real gear damage runtime, catalog, old and new power handlers.
 * Only world collision, pool spawning, feedback and OBJ hardware are synthetic. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "northern_powers.h"
#include "southern_powers.h"
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
static const unsigned forms[20]={25,26,28,29,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94};
int solid(int x,int y){
    int i;solid_calls++;if(x<0||y<0||x>=480||y>=320)return 1;
    for(i=0;i<wall_count;i++)if(x>=walls[i].x&&x<walls[i].x+walls[i].w&&
       y>=walls[i].y&&y<walls[i].y+walls[i].h)return 1;
    return 0;
}
static void wall(int x,int y,int w,int h){assert(wall_count<8);walls[wall_count].x=x;
    walls[wall_count].y=y;walls[wall_count].w=w;walls[wall_count++].h=h;southern_powers_geometry_changed();}
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
    const CreatureForm *f=creatures_form(forms[command-23]);assert(f);
    memset(&caster,0,sizeof caster);caster.form_id=f->id;caster.flags=CREATURE_OCCUPIED;
    caster.level=30;caster.xp=creatures_xp_threshold(30);caster.bond=50;
    caster.instance_id=1;caster.polarity=f->polarity;caster.equipped[0]=(CreatureU8)command;
    assert(creatures_instance_validate(&caster));
}
static void setup(unsigned command){
    southern_powers_reset();regional_powers_reset();northern_powers_reset();advanced_reset();
    northern_powers_tiles_release(NORTHERN_TILES_REGIONAL);
    memset(enemies,0,sizeof enemies);memset(shots,0,sizeof shots);memset(kills,0,sizeof kills);
    memset(enemy_clocks,0,sizeof enemy_clocks);memset(enemy_windups,0,sizeof enemy_windups);
    memset(shot_effects,0,sizeof shot_effects);memset(shot_phases,255,sizeof shot_phases);
    wall_count=absent=ability_cd=hitstop=0;px=py=cx=cy=100;face=3;boss_live=0;
    stone_guard=guard_invuln=0;max_hp=6;equipment_init(&adventure_save.equipment);
    game_health_refresh(1);game_attacks_reset();select_command(command);
}
static void enemy(unsigned i,int x,int y,int hearts){
    enemies[i]=(Enemy){x,y,hearts,0,0};enemy_hp_q4[i]=hearts*16;enemy_phases[i]=255;southern_powers_enemy_spawn(i);
}
static void shot(unsigned i,int x,int y,int dx,int dy,int life,int owner){
    shots[i]=(Shot){x,y,dx,dy,life,owner};shot_phases[i]=CREATURE_FIRE;
    shot_effects[i]=SHOT_EFFECT_FIRE;northern_powers_shot_spawn(i);
}
static void updates(unsigned n){while(n--){southern_powers_tick();regional_powers_tick();if(ability_cd&&!hitstop)ability_cd--;}}
static void expect_damage(unsigned i,unsigned q4){if(enemy_hp_q4[i]!=160-(int)q4)fprintf(stderr,"command%d age%d enemy%u actual%d expected%d\n",southern_power_kind,southern_power_age,i,enemy_hp_q4[i],160-(int)q4);assert(enemy_hp_q4[i]==160-(int)q4);}
static void test_every_command(void){
    unsigned c;
    for(c=23;c<=42;c++){
        int x=124,y=100,old_draws;
        setup(c);
        if(c==23){x=112;y=92;}if(c==24){x=116;y=84;}
        if(c==28){x=124;y=112;}if(c==30){x=120;y=100;}
        if(c==31||c==32){x=100;y=90;}if(c==33){x=110;y=100;}
        if(c==34)x=122;if(c==37)y=112;if(c==38){x=112;y=76;}
        enemy(0,x,y,10);if(c==29)enemies[0].kind=2;
        if(c==40)enemy(1,100,130,10);
        assert(southern_power(c));assert(southern_power_form==(int)forms[c-23]);
        assert(southern_power_time>0&&southern_power_time<=60);
        assert(southern_power_cooldown==(c&1?90:120));assert(southern_powers_busy());
        assert(northern_powers_tiles_owner()==NORTHERN_TILES_SOUTHERN);
        assert(game_gear_busy()&EQUIPMENT_BUSY_PLAYER_PROJECTILE);
        assert(!southern_power(c));updates(8);
        if(c==28){shot(0,126,100,-4,0,40,1);assert(southern_powers_intercept_shot(0,126,100,122,100,1));}
        if(c==29)assert(southern_powers_windup(0,30)==42);
        if(c>=31&&c<=33)assert(southern_powers_melee_guard(0,x,y));
        if(c==34)enemies[0].x=126;
        if(c==26||c==35||c==36){int tx=100,ty=100;assert(southern_powers_approach(0,&tx,&ty));assert(tx!=100||ty!=100);}
        if(c==39)southern_powers_weapon_hit(0);
        if(c==40){face=0;assert(southern_powers_can_aim());assert(southern_powers_aim());southern_powers_weapon_hit(0);}
        updates(25);old_draws=draws;southern_powers_draw();assert(draws-old_draws<=24);
        if(c!=35&&c!=40)expect_damage(0,c==23||c==29||c==31||c==36||c==39?16:c==25||c==26||c==41?20:c==27?16:c==37?12:24);
        if(c==35)expect_damage(0,0);if(c==40){expect_damage(0,0);expect_damage(1,24);}
        updates(70);assert(!southern_powers_busy());assert(northern_powers_tiles_owner()==0);
    }
}
static void test_snapshot_pause_and_invalid(void){
    unsigned c;int up,draw0,t,cd;
    setup(23);up=uploads;assert(!southern_power(22)&&!southern_power(43)&&!southern_power(12));
    assert(!southern_power(24));caster.selected_command=2;assert(!southern_power(23));
    select_command(23);caster.level=0;assert(!southern_power(23));
    select_command(23);caster.form_id=121;assert(!southern_power(23));
    select_command(23);face=4;assert(!southern_power(23));face=3;absent=1;assert(!southern_power(23));absent=0;
    assert(up==uploads&&!ability_cd);
    /* Hostile forged stat is bounded by gear8 + Feather8 + Bell4. */
    setup(24);gear_stats.power_cooldown=1;assert(GAME_MAX_POWER_RECOVERY==20);assert(southern_power(24));assert(ability_cd==100);
    t=southern_power_time;cd=ability_cd;select_command(42);px=220;py=200;face=0;
    assert(southern_power_form==26&&southern_power_direction==3&&southern_power_phase==CREATURE_WOOD);
    assert(southern_power_origin_x==100&&southern_power_origin_y==100&&!southern_powers_feedback(42));
    for(c=0;c<20;c++){draw0=draws;southern_powers_draw();assert(draws-draw0<=24);}
    assert(southern_power_time==t&&ability_cd==cd);
    hitstop=3;updates(20);assert(southern_power_time==t&&southern_power_age==0&&ability_cd==cd);
    hitstop=0;updates(1);assert(southern_power_time==t-1&&southern_power_cooldown==100);
    for(c=23;c<=42;c++){setup(c);enemy(0,124,100,10);if(c==29)enemies[0].kind=2;assert(southern_power(c));t=enemy_hp_q4[0];
        southern_powers_reset();updates(90);expect_damage(0,(unsigned)(160-t));assert(!southern_powers_busy());}
}
static void test_guards_and_aim(void){unsigned c;int t,cd;
    for(c=31;c<=33;c++){
        setup(c);enemy(0,c==33?110:100,c==33?100:90,10);assert(southern_power(c));
        assert(!southern_powers_melee_guard(0,enemies[0].x,enemies[0].y));updates(8);
        assert(!southern_powers_melee_guard(0,90,100));assert(!southern_powers_melee_guard(0,100,110));
        enemies[0].kind=3;assert(!southern_powers_melee_guard(0,enemies[0].x,enemies[0].y));enemies[0].kind=0;
        enemies[0].kind=2;assert(!southern_powers_melee_guard(0,enemies[0].x,enemies[0].y));enemies[0].kind=0;
        px=110;assert(!southern_powers_melee_guard(0,enemies[0].x,enemies[0].y));px=100;
        assert(southern_powers_melee_guard(0,enemies[0].x,enemies[0].y));
        assert(southern_powers_melee_guard(0,enemies[0].x,enemies[0].y));
        updates(12);assert(!southern_powers_melee_guard(0,enemies[0].x,enemies[0].y));
    }
    setup(31);enemy(0,100,90,10);enemy(1,100,90,10);assert(southern_power(31));updates(8);
    assert(southern_powers_melee_guard(0,100,90));assert(!southern_powers_melee_guard(1,100,90));
    enemy(0,100,90,10);assert(!southern_powers_melee_guard(0,100,90));
    setup(33);enemy(0,110,100,10);assert(southern_power(33));updates(17);assert(!southern_powers_melee_guard(0,110,100));
    setup(32);enemy(0,100,110,10);assert(southern_power(32));updates(8);
    assert(southern_powers_hint()==SOUTHERN_HINT_OTHER_SIDE);t=southern_power_time;cd=ability_cd;
    caster.instance_id=2;assert(!southern_powers_aim());caster.instance_id=1;
    assert(southern_powers_aim());assert(southern_power_time==t&&ability_cd==cd);
    assert(!southern_powers_can_aim());assert(!southern_powers_melee_guard(0,100,110));updates(6);
    assert(southern_powers_melee_guard(0,100,110));assert(!southern_powers_aim());
    setup(32);assert(southern_power(32));wall(100,110,1,1);assert(!southern_powers_aim());
}
static void test_windup_and_echo(void){
    int flash;
    setup(29);enemy(0,124,100,10);assert(!southern_power(29)&&!ability_cd);
    enemies[0].kind=3;assert(!southern_power(29)&&!ability_cd);
    enemies[0].kind=2;assert(southern_power(29));
    assert(southern_powers_windup(1,30)==30);enemies[0].kind=3;assert(southern_powers_windup(0,30)==30);
    enemies[0].kind=2;assert(southern_powers_windup(0,30)==42);assert(southern_powers_windup(0,30)==30);
    updates(11);expect_damage(0,0);flash=enemies[0].flash;updates(1);expect_damage(0,16);assert(enemies[0].flash==flash);
    setup(39);enemy(0,124,100,10);assert(southern_power(39));game_enemy_hurt(0,8,0,255);updates(10);expect_damage(0,8);
    southern_powers_weapon_hit(0);updates(7);expect_damage(0,8);updates(1);expect_damage(0,24);
    southern_powers_weapon_hit(0);updates(20);expect_damage(0,24);
    setup(39);enemy(0,124,100,10);assert(southern_power(39));southern_powers_weapon_hit(0);
    enemy(0,124,100,10);updates(20);expect_damage(0,0);
    setup(40);enemy(0,124,100,10);enemy(1,100,132,10);assert(southern_power(40));
    assert(southern_powers_hint()==SOUTHERN_HINT_SECOND_TARGET);southern_powers_weapon_hit(0);updates(1);expect_damage(0,0);
    face=0;assert(southern_powers_aim());assert(!southern_powers_can_aim());
    game_enemy_hurt(0,255,0,255);assert(enemies[0].hp==0);southern_powers_weapon_hit(0);updates(8);expect_damage(1,24);
    setup(40);enemy(0,124,100,10);enemy(1,100,132,10);assert(southern_power(40));face=0;
    wall(112,110,1,20);assert(!southern_powers_aim());
    setup(40);enemy(0,124,100,10);enemy(1,100,132,10);assert(southern_power(40));face=0;assert(southern_powers_aim());
    southern_powers_weapon_hit(0);wall(112,110,1,20);updates(9);expect_damage(1,0);
    setup(39);enemy(0,124,100,10);assert(southern_power(39));updates(60);southern_powers_weapon_hit(0);updates(10);expect_damage(0,0);
}
static void test_windup_cast_boundaries(void){int up;
    setup(29);enemy(0,124,100,10);enemies[0].kind=2;enemy_clocks[0]=41;up=uploads;
    assert(!southern_power(29)&&!ability_cd&&!southern_power_time&&up==uploads&&enemy_clocks[0]==41);
    enemy_clocks[0]=100;assert(!southern_power(29)&&!ability_cd&&enemy_clocks[0]==100);
    enemy_clocks[0]=40;assert(southern_power(29));assert(enemy_clocks[0]==40&&!enemy_windups[0]);
    assert(southern_powers_windup(0,30)==42);updates(12);expect_damage(0,16);
    setup(29);enemy(0,124,100,10);enemies[0].kind=2;enemy_clocks[0]=100;enemy_windups[0]=15;
    assert(southern_power(29));assert(enemy_windups[0]==27&&southern_power_time==60&&ability_cd==90);
    assert(!southern_power(29)&&enemy_windups[0]==27);assert(southern_powers_windup(0,27)==27);
    updates(12);expect_damage(0,16);assert(enemy_windups[0]==27&&!enemies[0].flash);
    setup(29);enemy(0,124,100,10);enemies[0].kind=3;enemy_windups[0]=15;
    assert(!southern_power(29)&&enemy_windups[0]==15&&!ability_cd);
}
static void test_projectiles_and_interceptions(void){
    setup(27);enemy(0,116,100,10);enemy(1,126,110,10);enemy(2,126,90,10);
    assert(southern_power(27));updates(30);expect_damage(0,16);expect_damage(1,8);expect_damage(2,8);
    setup(27);enemy(0,126,110,10);assert(southern_power(27));updates(30);expect_damage(0,0); /* no impact, no split */
    setup(28);enemy(0,124,112,10);assert(southern_power(28));updates(6);
    shot(0,126,100,-4,0,30,1);assert(!southern_powers_intercept_shot(0,126,100,122,100,0));
    assert(!southern_powers_intercept_shot(0,122,100,126,100,1));
    assert(southern_powers_intercept_shot(0,126,100,122,100,1));assert(shots[0].life==0);expect_damage(0,24);
    shot(0,126,100,-4,0,30,1);assert(!southern_powers_intercept_shot(0,126,100,122,100,1));assert(shots[0].life==30);
    updates(10);expect_damage(0,24);southern_powers_reset();assert(shots[0].life==30);
    setup(41);enemy(0,85,100,10);wall(120,90,1,20);assert(southern_power(41));updates(26);expect_damage(0,20);
    setup(41);enemy(0,135,100,10);wall(120,90,1,20);assert(southern_power(41));updates(40);expect_damage(0,0);
    setup(42);enemy(0,120,100,10);enemy(1,115,115,10);enemy(2,115,85,10);assert(southern_power(42));updates(44);
    expect_damage(0,24);expect_damage(1,24);expect_damage(2,24);
    setup(42);enemy(0,80,100,10);assert(southern_power(42));updates(18);cx=60;cy=100;wall(99,0,1,320);updates(30);expect_damage(0,0);
}
static void test_geometry_once_and_walls(void){unsigned c,d,i;static const int dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};
    for(d=0;d<4;d++){
        setup(25);face=(int)d;for(i=0;i<6;i++)enemy(i,100+dx[d]*20-dy[d]*(int)i,100+dy[d]*20+dx[d]*(int)i,10);
        assert(southern_power(25));updates(24);for(i=0;i<6;i++)expect_damage(i,20);
        setup(25);face=(int)d;enemy(0,100-dx[d]*20,100-dy[d]*20,10);assert(southern_power(25));updates(24);expect_damage(0,0);
        setup(25);face=(int)d;enemy(0,100+dx[d]*20,100+dy[d]*20,10);
        wall(100+dx[d]*10,100+dy[d]*10,1,1);assert(southern_power(25));updates(24);expect_damage(0,0);
    }
    setup(30);enemy(0,100,100,10);enemy(1,120,100,10);enemy(2,98,100,10);assert(southern_power(30));updates(40);
    expect_damage(0,0);expect_damage(1,24);expect_damage(2,0);
    setup(34);enemy(0,124,100,10);assert(southern_power(34));updates(10);expect_damage(0,0);
    enemies[0].x=122;updates(1);enemies[0].x=126;updates(1);expect_damage(0,24);
    enemies[0].x=122;updates(1);enemies[0].x=126;updates(1);expect_damage(0,24);
    setup(38);enemy(0,100,100,10);enemy(1,112,76,10);assert(southern_power(38));updates(30);expect_damage(0,0);expect_damage(1,24);
    for(c=23;c<=42;c++){
        setup(c);enemy(0,124,100,10);if(c==29||c==39||c==40){wall(112,0,1,320);assert(!southern_power(c));continue;}
        assert(southern_power(c));wall(112,0,1,320);updates(61);expect_damage(0,0);
    }
    setup(24);enemy(0,140,100,10);wall(120,88,1,1);assert(southern_power(24));updates(40);expect_damage(0,24);
    setup(24);enemy(0,116,84,10);wall(101,100,1,1);assert(!southern_power(24));
    setup(24);enemy(0,116,84,10);wall(100,99,1,1);assert(!southern_power(24));
    setup(37);enemy(0,124,112,10);assert(southern_power(37));updates(15);assert(slowed_enemies[0]);southern_powers_reset();assert(!slowed_enemies[0]);
    setup(25);enemy(0,124,100,10);enemies[0].kind=3;assert(southern_power(25));updates(24);assert(enemies[0].x==124);
}
static void test_decoys_and_lease(void){int tx,ty,up;unsigned owner;
    setup(35);enemy(0,124,100,10);enemy(1,126,100,10);assert(southern_power(35));updates(6);
    tx=ty=100;assert(southern_powers_approach(0,&tx,&ty));assert(tx==120&&ty==84);
    assert(enemies[0].x==124&&enemies[0].y==100);assert(!southern_powers_approach(1,&tx,&ty));
    updates(12);assert(!southern_powers_approach(0,&tx,&ty));expect_damage(0,0);
    setup(36);enemy(0,120,100,10);enemies[0].kind=3;assert(southern_power(36));updates(6);
    assert(!southern_powers_approach(0,&tx,&ty));enemies[0].kind=0;wall(120,90,1,1);assert(!southern_powers_approach(0,&tx,&ty));
    for(owner=1;owner<=3;owner++){
        setup(23);assert(northern_powers_tiles_claim(owner));up=uploads;
        assert(!northern_powers_tiles_claim(owner)&&!southern_power(23)&&!ability_cd&&uploads==up);
        assert(northern_powers_tiles_release(owner));assert(southern_power(23));
        assert(!northern_powers_tiles_claim(owner));assert(!northern_powers_tiles_release(3));
        updates(24);assert(northern_powers_tiles_owner()==0);
    }
    setup(23);ability_cd=70;up=uploads;assert(southern_powers_feedback(23));
    assert(!southern_powers_busy()&&ability_cd==70&&uploads==up&&northern_powers_tiles_owner()==0);
    assert(southern_powers_cast_matches_selected());caster.instance_id=2;assert(!southern_powers_cast_matches_selected());caster.instance_id=1;
    updates(20);assert(!southern_power_cast_time);
}
static void test_render_stress(void){unsigned c,d,n;int max_draw=0,max_solid=0;unsigned char before[16384];
    for(c=23;c<=42;c++)for(d=0;d<4;d++){
        setup(c);face=(int)d;enemy(0,100+(d==3?24:d==2?-24:0),100+(d==0?24:d==1?-24:0),10);
        if(c==29)enemies[0].kind=2;memcpy(before,vram,sizeof before);assert(southern_power(c));
        for(n=0;n<16384;n++)if(!(n>=GFX_OBJ_POWER_PIN&&n<GFX_OBJ_POWER_PIN+256)&&!(n>=GFX_OBJ_WATER_DROP&&n<GFX_OBJ_WATER_DROP+64))assert(vram[n]==before[n]);
        for(n=0;n<60;n++){int old=draws;solid_calls=0;southern_powers_draw();if(draws-old>max_draw)max_draw=draws-old;
            if(solid_calls>max_solid)max_solid=solid_calls;assert(draws-old<=24&&solid_calls<2000);updates(1);}
    }
    printf("Bounded render: 4800 draws; max OBJ=%d; max solid calls=%d\n",max_draw,max_solid);
}

static void test_real_weapons_and_gear(void){unsigned i,w;EquipmentComparison compare;EquipmentU16 hero;
    for(w=EQUIPMENT_SWORD;w<=EQUIPMENT_LANCE;w++){
        setup(39);enemy(0,120,100,10);assert(southern_power(39));
        gear_stats.weapon_class=(EquipmentU8)w;gear_stats.phase=255;gear_stats.attack_q4=0;
        assert(weapon_action_tick(&weapon_action,&gear_stats,3,1,1,0)&WEAPON_EVENT_START);
        for(i=0;i<20&&weapon_action.phase!=WEAPON_ACTIVE;i++)weapon_action_tick(&weapon_action,&gear_stats,3,0,0,0);
        assert(weapon_action.phase==WEAPON_ACTIVE);assert(game_melee_hit(0,120,100,0));
        game_enemy_hurt(0,weapon_action.damage_q4,weapon_action.attack_q4,weapon_action.element);
        southern_powers_weapon_hit(0);assert(!game_melee_hit(0,120,100,0));updates(8);
        expect_damage(0,weapon_action.damage_q4+16);
    }
    setup(39);enemy(0,132,100,10);assert(southern_power(39));
    gear_stats.weapon_class=EQUIPMENT_BOW;gear_stats.phase=255;gear_stats.attack_q4=0;
    assert(weapon_action_tick(&weapon_action,&gear_stats,3,1,1,0)&WEAPON_EVENT_START);
    for(i=0;i<10&&!weapon_action.arrow_pending;i++)weapon_action_tick(&weapon_action,&gear_stats,3,0,0,0);
    assert(weapon_arrow_spawn(&player_arrows[0],&weapon_action,100,100));
    for(i=0;i<20&&player_arrows[0].active;i++)game_arrows_update();
    assert(!player_arrows[0].active);updates(8);expect_damage(0,weapon_action.damage_q4+16);
    setup(25);assert(southern_power(25));hero=(EquipmentU16)hero_hp_q4;
    assert(equipment_equip(&adventure_save.equipment,0,0,96,&hero,game_gear_busy(),&compare)==EQUIPMENT_BUSY);
    updates(24);assert(!game_gear_busy());
    assert(equipment_equip(&adventure_save.equipment,0,0,96,&hero,game_gear_busy(),&compare)==EQUIPMENT_OK);
    setup(39);enemy(0,124,100,10);enemy_phases[0]=CREATURE_METAL;assert(southern_power(39));
    southern_powers_weapon_hit(0);updates(8);
    expect_damage(0,combat_damage_q4(16,0,0,CREATURE_FIRE,CREATURE_METAL,0));
}
static void test_pose_and_dynamic_geometry(void){int x,y,step,old,px0,py0;
    setup(23);cx=92;cy=104;assert(southern_power(23));px0=px;py0=py;
    assert(southern_powers_companion_pose(&x,&y)&&x==92&&y==104);
    assert(southern_powers_cast_matches_selected());caster.instance_id=2;
    assert(!southern_powers_cast_matches_selected()&&!southern_powers_companion_pose(&x,&y));caster.instance_id=1;
    assert(southern_powers_cast_matches_selected());
    updates(4);assert(southern_powers_companion_pose(&x,&y)&&x==92&&y==96);
    updates(8);assert(southern_powers_companion_pose(&x,&y)&&x==92&&y==104);
    assert(px==px0&&py==py0&&cx==92&&cy==104);updates(1);assert(!southern_powers_companion_pose(&x,&y));
    for(step=1;step<=16;step++){
        setup(24);wall(100+step,101-step,1,1);assert(!southern_power(24));
        setup(24);assert(southern_power(24));wall(100+step,101-step,1,1);
        old=draws;record_draws=1;capture_count=0;southern_powers_draw();record_draws=0;assert(draws-old<=24);
        for(x=0;x<capture_count;x++)assert(capture_x[x]<100+step);
    }
    setup(38);assert(southern_power(38));wall(100,92,1,1);old=draws;southern_powers_draw();assert(draws==old);
    setup(30);assert(southern_power(30));updates(20);wall(105,0,1,320);capture_count=0;record_draws=1;
    southern_powers_draw();record_draws=0;for(x=0;x<capture_count;x++)assert(capture_x[x]<105);
    setup(38);enemy(0,112,76,10);assert(southern_power(38));updates(6);assert(slowed_enemies[0]);
    /* Parent orders regional decay before Southern tick. Every slow is gone by expiry. */
    while(southern_power_time){regional_powers_tick();southern_powers_tick();}assert(!slowed_enemies[0]);
}


static int reference_clear(int x,int y,int tx,int ty){int dx=abs(tx-x),dy=-abs(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,err=dx+dy;
    if(solid(x,y)||solid(tx,ty))return 0;
    while(x!=tx||y!=ty){int twice=err*2,nx=x,ny=y;if(twice>=dy){err+=dy;nx+=sx;}if(twice<=dx){err+=dx;ny+=sy;}
        if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return 0;x=nx;y=ny;if(solid(x,y))return 0;}return 1;
}
static void reference_point(int d,int f,int s,int*x,int*y){static const int dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};
    *x=100+f*dx[d]-s*dy[d];*y=100+f*dy[d]+s*dx[d];
}
static int reference_crescent(int d,int qx,int qy){static const int f[5]={0,16,36,16,0},s[5]={-18,-24,0,24,18};int p;
    for(p=0;p<4;p++){int x,y,tx,ty,dx,dy,sx,sy,err;reference_point(d,f[p],s[p],&x,&y);reference_point(d,f[p+1],s[p+1],&tx,&ty);
        if((p==0&&!reference_clear(100,100,x,y))||!reference_clear(x,y,tx,ty))break;
        dx=abs(tx-x);dy=-abs(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;err=dx+dy;
        for(;;){int twice;if(abs(x-qx)+abs(y-qy)<=4&&reference_clear(x,y,qx,qy))return 1;
            if(x==tx&&y==ty)break;twice=err*2;if(twice>=dy){err+=dy;x+=sx;}if(twice<=dx){err+=dx;y+=sy;}}
    }return 0;
}
static void test_cached_crescent_equivalence(void){int d,barrier,batch,cases=0;
    for(d=0;d<4;d++)for(barrier=0;barrier<=34;barrier++)for(batch=0;batch<17;batch++){
        int i,expected[6],x,y;setup(38);face=d;
        for(i=0;i<6;i++){int index=batch*6+i;reference_point(d,-6+(index%9)*6,-30+(index/9)*6,&x,&y);enemy((unsigned)i,x,y,10);}
        assert(southern_power(38));southern_powers_draw(); /* warm the unobstructed cache */
        if(barrier>0){if(barrier<=18)reference_point(d,0,-barrier,&x,&y);
            else reference_point(d,barrier-18,-18-(barrier-18)*6/16,&x,&y);wall(x,y,1,1);}
        for(i=0;i<6;i++)expected[i]=reference_crescent(d,enemies[i].x,enemies[i].y);
        updates(6);for(i=0;i<6;i++)expect_damage((unsigned)i,expected[i]?24:0);
        updates(8);for(i=0;i<6;i++)expect_damage((unsigned)i,expected[i]?24:0);
        cases++;
    }
    setup(38);enemy(0,112,76,10);assert(southern_power(38));wall(100,92,1,1);updates(6);expect_damage(0,0);
    wall_count=0;southern_powers_geometry_changed();updates(1);expect_damage(0,24); /* removal reopens same live field */
    setup(38);enemy(0,100,100,10);assert(southern_power(38));updates(6);expect_damage(0,0);
    enemies[0].x=112;enemies[0].y=76;updates(1);expect_damage(0,24); /* current moving target, no stale hit cache */
    solid_calls=0;southern_powers_draw();assert(solid_calls==0); /* rendering reuses the checked raster */
    southern_powers_reset();assert(!southern_powers_busy());setup(38);wall(100,92,1,1);enemy(0,112,76,10);
    assert(southern_power(38));updates(6);expect_damage(0,0); /* reset/room cannot retain valid spans */
    printf("Cached crescent matches uncached geometry: %d cases, four facings, thin walls, invalidation/removal, moving targets and reset\n",cases);
}

static void paired_long_setup(void){
    setup(40);px=296;py=96;face=3;enemy(0,320,96,10);enemy(1,272,48,10);
    assert(southern_power(40));px=272;py=80;face=1;assert(southern_powers_aim());
}
static void test_mark_sight_cache(void){int before,i;
    paired_long_setup();solid_calls=0;before=draws;southern_powers_draw();assert(draws>before&&solid_calls==0);
    solid_calls=0;for(i=0;i<20;i++)southern_powers_draw();assert(!solid_calls);
    wall(290,0,1,61);southern_powers_draw();solid_calls=0;southern_powers_draw();assert(!solid_calls);
    /* A moving endpoint invalidates LOS even without a scenery mutation. */
    enemies[1].y=32;before=draws;southern_powers_draw();assert(draws-before==1);
    southern_powers_weapon_hit(0);updates(8);expect_damage(1,0);
    enemies[1].y=48;before=draws;southern_powers_draw();assert(draws-before>1);
    solid_calls=0;southern_powers_weapon_hit(0);assert(!solid_calls);updates(8);expect_damage(1,24);
    paired_long_setup();southern_powers_draw();wall(296,70,1,8);before=draws;southern_powers_draw();assert(draws-before==1);
    wall_count=0;southern_powers_geometry_changed();before=draws;southern_powers_draw();assert(draws-before>1);
    southern_powers_weapon_hit(0);wall(296,70,1,8);updates(8);expect_damage(1,0);
    paired_long_setup();wall(290,0,1,61);southern_powers_draw();southern_powers_weapon_hit(0);
    enemies[1].y=32;updates(8);expect_damage(1,0); /* delayed endpoint checked anew */
    paired_long_setup();southern_powers_draw();enemy(1,272,48,10);southern_powers_weapon_hit(0);updates(8);expect_damage(1,0);
    paired_long_setup();southern_powers_draw();southern_powers_reset();solid_calls=0;before=draws;southern_powers_draw();
    assert(draws==before&&!solid_calls&&!southern_powers_busy());
}
int main(void){assert(creatures_catalog_validate());test_every_command();test_snapshot_pause_and_invalid();
    test_guards_and_aim();test_windup_and_echo();test_windup_cast_boundaries();test_projectiles_and_interceptions();test_geometry_once_and_walls();
    test_decoys_and_lease();test_real_weapons_and_gear();test_pose_and_dynamic_geometry();test_cached_crescent_equivalence();test_mark_sight_cache();test_render_stress();
    puts("PASS Southern host integration: all20 real roles, directional and spent guards, explicit delayed weapon echoes, split/return/ricochet, LOS/corners, recycled identities, one-hit ledgers, snapshot/freeze/reset, field-only feedback, shared tile lease, bounded drawing. Not cartridge controller proof.");return 0;}
