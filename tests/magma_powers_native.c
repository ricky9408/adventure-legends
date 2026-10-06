/* Host-compiled native C harness, NOT an emulator/controller acceptance route.
 * Links the real gear damage runtime, catalog, old and new power handlers.
 * World collision, selection, pool spawning, feedback and OBJ hardware are synthetic. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "northern_powers.h"
#include "southern_powers.h"
#include "magma_powers.h"
#include "magma_game.h"
#include <limits.h>
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
static int chapter_enabled,chapter_x,chapter_y,chapter_hp;
static unsigned chapter_tokens[4],chapter_used;
static int solid_calls,record_draws,capture_count,capture_x[32],capture_y[32];
static unsigned char vram[16384];
static struct {int x,y,w,h;} walls[8];
static const unsigned forms[24]={31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,95,96,97,98,99,100};
int solid(int x,int y){
    int i;solid_calls++;if(x<0||y<0||x>=480||y>=320)return 1;
    for(i=0;i<wall_count;i++)if(x>=walls[i].x&&x<walls[i].x+walls[i].w&&
       y>=walls[i].y&&y<walls[i].y+walls[i].h)return 1;
    return 0;
}
int game_clear_box(int x0,int y0,int x1,int y1){int i;
 if(x0<0||y0<0||x1>=480||y1>=320||x0>x1||y0>y1)return 0;
 for(i=0;i<wall_count;i++)if(x0<walls[i].x+walls[i].w&&x1>=walls[i].x&&y0<walls[i].y+walls[i].h&&y1>=walls[i].y)return 0;
 return 1;
}
static void wall(int x,int y,int w,int h){assert(wall_count<8);walls[wall_count].x=x;
    walls[wall_count].y=y;walls[wall_count].w=w;walls[wall_count++].h=h;southern_powers_geometry_changed();magma_powers_geometry_changed();}
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
/* Synthetic authored-scene bridge. Full chapter implementation is tested
 * separately; here we verify the power supplies stable per-cast identity. */
unsigned magma_game_action_begin(unsigned channel){assert(channel<4);chapter_tokens[channel]++;chapter_used&=~(1u<<channel);return chapter_tokens[channel];}
int magma_game_target(int*x,int*y,int*r){if(!chapter_enabled)return 0;if(x)*x=chapter_x;if(y)*y=chapter_y;if(r)*r=13;return 1;}
int magma_game_weapon_hit(unsigned cls,int x,int y,unsigned q4,unsigned channel,unsigned token){
 (void)cls;(void)x;(void)y;(void)q4;(void)channel;(void)token;return 0;}
int magma_game_command_hit(int x,int y,unsigned q4,unsigned token){
 if(!chapter_enabled||x!=chapter_x||y!=chapter_y||token!=chapter_tokens[3]||(chapter_used&8))return 0;
 chapter_used|=8;chapter_hp-=(int)q4;return 1;}
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
    const CreatureForm *f=creatures_form(forms[command-43]);assert(f);
    memset(&caster,0,sizeof caster);caster.form_id=f->id;caster.flags=CREATURE_OCCUPIED;
    caster.level=40;caster.xp=creatures_xp_threshold(40);caster.bond=80;
    caster.instance_id=1;caster.polarity=f->polarity;caster.equipped[0]=(CreatureU8)command;
    assert(creatures_instance_validate(&caster));
}
static void setup(unsigned command){
    magma_powers_reset();southern_powers_reset();regional_powers_reset();northern_powers_reset();advanced_reset();
    northern_powers_tiles_release(NORTHERN_TILES_REGIONAL);
    memset(enemies,0,sizeof enemies);memset(shots,0,sizeof shots);memset(kills,0,sizeof kills);
    memset(enemy_clocks,0,sizeof enemy_clocks);memset(enemy_windups,0,sizeof enemy_windups);
    memset(shot_effects,0,sizeof shot_effects);memset(shot_phases,255,sizeof shot_phases);
    chapter_enabled=chapter_used=0;chapter_hp=160;
    wall_count=absent=ability_cd=hitstop=0;px=py=cx=cy=100;face=3;boss_live=0;
    stone_guard=guard_invuln=0;max_hp=6;equipment_init(&adventure_save.equipment);
    game_health_refresh(1);game_attacks_reset();select_command(command);
}
static void enemy(unsigned i,int x,int y,int hearts){
    enemies[i]=(Enemy){x,y,hearts,0,0};enemy_hp_q4[i]=hearts*16;enemy_phases[i]=255;southern_powers_enemy_spawn(i);magma_powers_enemy_spawn(i);
}
static void shot(unsigned i,int x,int y,int dx,int dy,int life,int owner){
    shots[i]=(Shot){x,y,dx,dy,life,owner};shot_phases[i]=CREATURE_FIRE;
    shot_effects[i]=SHOT_EFFECT_FIRE;northern_powers_shot_spawn(i);
}
static void updates(unsigned n){while(n--){magma_powers_tick();if(!hitstop){regional_powers_tick();advanced_tick();game_combat_tick();if(ability_cd)ability_cd--;}}}
static const unsigned start[24]={8,12,18,6,12,20,8,14,16,8,12,10,6,14,16,8,12,14,10,16,10,14,10,18};
static const unsigned act[24]={36,16,30,8,24,10,18,36,6,12,30,20,12,8,20,10,18,40,12,20,24,30,14,24};
static const unsigned recover[24]={12,16,20,16,18,22,12,14,18,14,18,20,16,22,16,12,18,18,12,20,12,16,12,18};
static const unsigned damage[24]={16,24,32,20,24,32,16,20,24,16,24,24,20,28,24,16,24,16,20,24,16,24,16,24};
static const int positions[24][2]={{108,100},{112,84},{122,100},{118,100},{114,100},{130,100},
 {120,100},{124,88},{140,100},{128,100},{140,100},{118,100},{118,95},{124,100},{112,96},{114,89},
 {116,100},{132,100},{121,100},{120,86},{122,100},{124,88},{124,100},{125,100}};
static unsigned assertions,max_draws,max_solid;
static void expect_damage(unsigned i,unsigned q4){if(enemy_hp_q4[i]!=160-(int)q4)fprintf(stderr,
 "command%d age%d enemy%u actual%d expected%d\n",magma_power_kind,magma_power_age,i,enemy_hp_q4[i],160-(int)q4);
 assert(enemy_hp_q4[i]==160-(int)q4);assertions++;}
static void complete(unsigned command){unsigned n;for(n=0;n<100;n++){
 if(command==47&&magma_power_age==(int)start[command-43])assert(magma_powers_melee_guard(0,enemies[0].x,enemies[0].y));
 updates(1);if(magma_power_time)assert(game_gear_busy()&EQUIPMENT_BUSY_PLAYER_PROJECTILE);draws=solid_calls=0;magma_powers_draw();if((unsigned)draws>max_draws)max_draws=(unsigned)draws;
 if((unsigned)solid_calls>max_solid)max_solid=(unsigned)solid_calls;assert(draws<=24);
 }}
static void test_every_command(void){unsigned c,i;
 for(c=43;c<=66;c++)for(i=0;i<6;i++){unsigned expected;
  setup(c);enemy(0,positions[c-43][0],positions[c-43][1],10);enemy_phases[0]=i==5?255:(unsigned char)i;
  assert(magma_power(c));assert(magma_power_form==(int)forms[c-43]);
  assert(magma_power_time==(int)(start[c-43]+act[c-43]+recover[c-43]));
  assert(magma_power_cooldown==(c==45||c==48?150:(c==43||c==46||c==49||c==52||c==55||c==58||c==61||c==63||c==65?90:120)));
  assert(northern_powers_tiles_owner()==NORTHERN_TILES_MAGMA);assert(magma_powers_busy());
  assert(game_gear_busy()&EQUIPMENT_BUSY_PLAYER_PROJECTILE);assert(!magma_power(c));
  expected=combat_damage_q4(damage[c-43],0,0,(unsigned)magma_power_phase,enemy_phases[0],0);
  complete(c);expect_damage(0,expected);assert(!magma_powers_busy());assert(northern_powers_tiles_owner()==0);
 }
}
static void test_rotations_and_exact_windows(void){unsigned c,d;static const int dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};
 for(c=43;c<=66;c++)for(d=0;d<4;d++){
  int f=positions[c-43][0]-100,l=positions[c-43][1]-100;
  setup(c);face=(int)d;enemy(0,100+f*dx[d]-l*dy[d],100+f*dy[d]+l*dx[d],10);
  assert(magma_power(c));updates(start[c-43]-1);expect_damage(0,0);
  assert(magma_power_age==(int)start[c-43]-1);complete(c);expect_damage(0,damage[c-43]);
  assert(px==100&&py==100&&cx==100&&cy==100);
 }
 /* Swept crossing between observations cannot hop over the thread. */
 setup(43);enemy(0,100,100,10);assert(magma_power(43));updates(8);enemies[0].x=120;updates(1);expect_damage(0,16);
 /* At active end, recovery cannot hit an entrant. */
 setup(50);enemy(0,100,100,10);assert(magma_power(50));updates(50);enemies[0].x=124;enemies[0].y=88;
 updates(14);expect_damage(0,0);
 /* Reset clears only the bounded status this cast supplied. */
 setup(50);enemy(0,124,88,10);assert(magma_power(50));updates(14);assert(rooted_enemies[0]>0);
 magma_powers_reset();assert(rooted_enemies[0]==0);
 setup(49);enemy(0,110,100,10);assert(magma_power(49));updates(14);assert(slowed_enemies[0]>0);
 magma_powers_reset();assert(slowed_enemies[0]==0);
}
static void test_freeze_identity_and_validation(void){unsigned c,i;int time,cd,up;
 setup(43);up=uploads;assert(!magma_power(42)&&!magma_power(67)&&!magma_power(UINT_MAX));assert(!magma_power(44));
 caster.selected_command=2;assert(!magma_power(43));select_command(43);caster.level=0;assert(!magma_power(43));
 select_command(43);caster.instance_id=0;assert(!magma_power(43));select_command(43);
 face=-1;assert(!magma_power(43));face=4;assert(!magma_power(43));face=3;assert(!magma_power_side(43,0));
 absent=1;assert(!magma_power(43));absent=0;px=INT_MAX;assert(!magma_power(43));px=100;assert(up==uploads&&!ability_cd);
 for(c=43;c<=66;c++){setup(c);assert(magma_power(c));time=magma_power_time;cd=ability_cd;
  hitstop=3;for(i=0;i<10;i++){updates(1);magma_powers_draw();}assert(time==magma_power_time&&cd==ability_cd&&!magma_power_age);
  hitstop=0;caster.instance_id=2;assert(!magma_powers_cast_matches_selected());assert(!magma_powers_aim());
  assert(magma_power_form==(int)forms[c-43]);assert(!magma_powers_feedback(c));
  magma_powers_reset();updates(80);assert(!magma_powers_busy()&&northern_powers_tiles_owner()==0);
 }
 setup(51);enemy(0,140,100,10);assert(magma_power(51));time=magma_power_time;cd=ability_cd;
 assert(magma_powers_can_aim());face=0;assert(magma_powers_aim());assert(!magma_powers_can_aim());
 assert(time==magma_power_time&&cd==ability_cd);complete(51);expect_damage(0,0);
 setup(51);assert(magma_power(51));updates(12);assert(!magma_powers_aim());
 setup(43);up=uploads;assert(magma_powers_feedback(43));assert(!magma_powers_busy()&&!ability_cd&&up==uploads);
 assert(!northern_powers_tiles_owner());updates(30);assert(!magma_power_cast_time);
 setup(43);gear_stats.power_cooldown=1;assert(magma_power(43));assert(magma_power_cooldown==82);
}
static void test_geometry_and_exclusions(void){unsigned c;int old;
 for(c=43;c<=66;c++){
  setup(c);enemy(0,positions[c-43][0],positions[c-43][1],10);enemies[0].kind=3;
  assert(magma_power(c));updates(90);expect_damage(0,0);
  setup(c);enemy(0,positions[c-43][0],positions[c-43][1],10);wall(103,0,1,320);
  old=magma_power(c);if(old)updates(90);expect_damage(0,0);
 }
 /* One target bit across multi-part casts; a recycled pool slot is new identity
  * but cannot acquire another hit in the old cast. */
 setup(64);enemy(0,120,100,10);assert(magma_power(64));updates(14);expect_damage(0,24);
 enemy(0,124,90,10);for(c=0;c<65536;c++)magma_powers_enemy_spawn(0);updates(30);expect_damage(0,0);
 /* Cached scenery invalidates before native movers change a baffle/brick. */
 setup(64);enemy(0,124,84,10);assert(magma_power(64));magma_powers_draw();
 solid_calls=0;magma_powers_draw();assert(solid_calls==0);wall(124,90,1,1);updates(50);expect_damage(0,0);
 setup(64);wall(124,90,1,1);enemy(0,124,84,10);assert(magma_power(64));magma_powers_draw();
 wall_count=0;magma_powers_geometry_changed();updates(50);expect_damage(0,24);
 /* Diagonal side-cell blocking: no crossing the corner between two solids. */
 setup(58);enemy(0,114,89,10);wall(101,100,1,1);wall(100,99,1,1);assert(magma_power(58));updates(50);expect_damage(0,0);
 /* Safe central lane remains safe between roots and wedge lanes. */
 for(c=50;c<=62;c+=12){setup(c);enemy(0,124,100,10);assert(magma_power(c));updates(80);expect_damage(0,0);}
 setup(66);enemy(0,100,100,10);assert(magma_power(66));updates(80);expect_damage(0,0);
 setup(43);enemy(0,108,80,10);enemy(1,108,120,10);assert(magma_power(43));updates(80);
 assert(enemy_hp_q4[0]+enemy_hp_q4[1]==304);
 setup(55);enemy(0,118,95,10);enemy(1,118,105,10);assert(magma_power(55));updates(80);
 expect_damage(0,20);expect_damage(1,0);
 /* Invalid pool coordinates do not produce arithmetic overflow. */
 setup(66);enemy(0,INT_MAX,INT_MIN,10);assert(magma_power(66));updates(90);expect_damage(0,0);
 magma_powers_enemy_spawn(UINT_MAX);
}
static void test_guard_and_screen(void){unsigned i;
 setup(47);enemy(0,114,100,10);assert(magma_power(47));assert(!magma_powers_melee_guard(0,114,100));updates(12);
 assert(!magma_powers_melee_guard(0,90,100));enemies[0].kind=2;assert(!magma_powers_melee_guard(0,114,100));enemies[0].kind=0;
 px=110;assert(!magma_powers_melee_guard(0,114,100));px=100;assert(magma_powers_melee_guard(0,114,100));
 assert(magma_powers_melee_guard(0,114,100));expect_damage(0,24);enemy(0,114,100,10);assert(!magma_powers_melee_guard(0,114,100));
 setup(47);enemy(0,114,100,10);assert(magma_power(47));updates(60);expect_damage(0,0);
 setup(60);enemy(0,132,100,10);assert(magma_power(60));shot(0,124,100,-8,0,30,1);
 assert(!magma_powers_intercept_shot(0,124,100,116,100,1));updates(14);
 assert(!magma_powers_intercept_shot(0,124,100,116,100,0));assert(shots[0].life);
 assert(!magma_powers_intercept_shot(0,124,100,116,100,2));
 assert(!magma_powers_intercept_shot(0,124,100,115,100,1));
 shots[0].life=-1;assert(!magma_powers_intercept_shot(0,124,100,116,100,1));shots[0].life=30;
 shots[0].owner=0;assert(!magma_powers_intercept_shot(0,124,100,116,100,1));shots[0].owner=1;
 assert(magma_powers_intercept_shot(0,124,100,116,100,1));assert(!shots[0].life);
 shot(0,124,100,-8,0,30,1);assert(!magma_powers_intercept_shot(0,124,100,116,100,1));
 for(i=0;i<40;i++)updates(1);expect_damage(0,16);
 setup(60);assert(magma_power(60));updates(14);shot(0,124,100,-8,0,30,1);wall(122,100,1,1);
 assert(!magma_powers_intercept_shot(0,124,100,116,100,1));
 assert(!magma_powers_intercept_shot(UINT_MAX,0,0,0,0,1));
}
static void test_shared_lease(void){unsigned owner;
 for(owner=1;owner<=NORTHERN_TILES_UNDERWATER;owner++){
  setup(43);assert(northern_powers_tiles_claim(owner));assert(!magma_power(43));assert(!ability_cd);
  assert(!northern_powers_tiles_claim(owner));assert(northern_powers_tiles_release(owner));
 }
 setup(43);assert(!northern_powers_tiles_claim(NORTHERN_TILES_UNDERWATER+1));assert(magma_power(43));
 for(owner=1;owner<=NORTHERN_TILES_UNDERWATER;owner++){assert(!northern_powers_tiles_claim(owner));assert(!northern_powers_tiles_release(owner));}
 magma_powers_reset();assert(northern_powers_tiles_owner()==0);
 setup(43);regional_power_time=3;assert(!magma_power(43));regional_power_time=0;
 northern_power_time=3;assert(!magma_power(43));northern_power_time=0;
 southern_power_time=3;assert(!magma_power(43));southern_power_time=0;
 assert(magma_power(43));
}
static void test_equipment_lock(void){EquipmentComparison compare;EquipmentU16 hero;
 setup(61);assert(magma_power(61));hero=(EquipmentU16)hero_hp_q4;
 assert(equipment_equip(&adventure_save.equipment,0,0,96,&hero,game_gear_busy(),&compare)==EQUIPMENT_BUSY);
 updates(33);assert(magma_powers_busy());
 assert(equipment_equip(&adventure_save.equipment,0,0,96,&hero,game_gear_busy(),&compare)==EQUIPMENT_BUSY);
 updates(1);assert(!magma_powers_busy());
 assert(equipment_equip(&adventure_save.equipment,0,0,96,&hero,game_gear_busy(),&compare)==EQUIPMENT_OK);
}
static void test_chapter_cast_tokens(void){unsigned c,i,token;
 for(c=43;c<=66;c++){setup(c);chapter_enabled=1;chapter_x=positions[c-43][0];chapter_y=positions[c-43][1];
  assert(magma_power(c));token=chapter_tokens[3];
  for(i=0;i<100;i++){magma_game_action_begin(0);magma_game_action_begin(1);magma_game_action_begin(2);updates(1);}
  assert(chapter_tokens[3]==token);assert(chapter_hp==160-(c==47?0:(int)damage[c-43]));
 }
 setup(51);chapter_enabled=1;chapter_x=140;chapter_y=100;assert(magma_power(51));token=chapter_tokens[3];
 assert(magma_powers_aim());assert(chapter_tokens[3]==token);updates(80);assert(chapter_hp==136);
 setup(64);chapter_enabled=1;chapter_x=124;chapter_y=88;assert(magma_power(64));updates(14);assert(chapter_hp==136);
 chapter_used=0; /* Even a faulty external ledger reset cannot duplicate our cast. */
 updates(30);assert(chapter_hp==136);
 setup(43);token=chapter_tokens[3];assert(magma_powers_feedback(43));assert(chapter_tokens[3]==token);
}
static void test_weapon_sources_unchanged(void){unsigned w,n;
 /* Magma adds no weapon-triggered follow-up. These real sword/lance/arrow
  * paths must keep their own hit and lethal behavior without recursing. */
 for(w=EQUIPMENT_SWORD;w<=EQUIPMENT_BOW;w++){
  setup(43);enemy(0,120,100,10);gear_stats.weapon_class=(unsigned char)w;game_attacks_reset();
  game_attack_update(1,1);for(n=0;n<12;n++){game_attack_update(0,0);if(w==EQUIPMENT_BOW)game_arrows_update();
   else if(game_melee_hit(0,enemies[0].x,enemies[0].y,0))game_enemy_hurt(0,weapon_action.damage_q4,weapon_action.attack_q4,weapon_action.element);}
  assert(enemy_hp_q4[0]<160);assert(!magma_power_time&&!magma_power_age);
 }
 setup(49);enemy(0,120,100,1);assert(magma_power(49));updates(60);assert(kills[0]==1);
}
int main(void){test_every_command();test_rotations_and_exact_windows();test_freeze_identity_and_validation();test_geometry_and_exclusions();
 test_guard_and_screen();test_shared_lease();test_equipment_lock();test_chapter_cast_tokens();test_weapon_sources_unchanged();
 printf("Magma24 strict C integration: %u damage assertions; max draw objects %u; max draw solid probes %u\n",assertions,max_draws,max_solid);return 0;}
