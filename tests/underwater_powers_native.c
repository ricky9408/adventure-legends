/* Synthetic host integration, NOT a controller/acquisition acceptance route.
 * Links the real gear damage runtime, catalog, old and new power handlers.
 * World collision, selection, pool spawning, feedback and OBJ hardware are synthetic. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "northern_powers.h"
#include "southern_powers.h"
#include "magma_powers.h"
#include "underwater_powers.h"
#include "underwater_game.h"
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
static int solid_calls,record_draws,capture_count,capture_x[32],capture_y[32],capture_off[32],capture_width[32];
static unsigned char vram[16384];
static struct {int x,y,w,h;} walls[8];
static int field_enabled,field_x,field_y,field_calls,field_accepted,boss_vulnerable,field_radius,field_mutates;
static unsigned underwater_serial,underwater_used;
unsigned underwater_game_action_begin(unsigned channel){assert(channel<4);underwater_used=0;return ++underwater_serial;}
int underwater_game_field_target(unsigned i,int*x,int*y,int*r){if(!field_enabled||i>=(unsigned)field_enabled)return 0;*x=field_x;*y=field_y;*r=field_radius;return 1;}
int underwater_game_field_hit(unsigned i,unsigned c,unsigned id,unsigned f,unsigned token){
 field_calls++;if(i>=8||token!=underwater_serial||id!=caster.instance_id||f!=caster.form_id||c!=caster.equipped[caster.selected_command]||(underwater_used&(1u<<i)))return 0;
 underwater_used|=1u<<i;field_accepted++;
 if(field_mutates){field_mutates=0;walls[wall_count].x=103;walls[wall_count].y=0;walls[wall_count].w=1;walls[wall_count++].h=320;underwater_powers_geometry_changed();}
 return 1;
}
int underwater_game_target(int*x,int*y,int*r){if(!chapter_enabled)return 0;*x=chapter_x;*y=chapter_y;*r=10;return 1;}
int underwater_game_command_hit(int x,int y,unsigned q,unsigned token){if(!chapter_enabled||!boss_vulnerable||x!=chapter_x||y!=chapter_y||token!=underwater_serial||(underwater_used&256))return 0;
 underwater_used|=256;chapter_hp-=(int)q;return 1;}
int underwater_game_weapon_hit(unsigned w,int x,int y,unsigned q,unsigned ch,unsigned token){(void)w;(void)x;(void)y;(void)q;(void)ch;(void)token;return 0;}
static const unsigned forms[24]={49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72};
int solid(int x,int y){
    int i;solid_calls++;if(x<0||y<0||x>=480||y>=320)return 1;
    for(i=0;i<wall_count;i++)if(x>=walls[i].x&&x<walls[i].x+walls[i].w&&
       y>=walls[i].y&&y<walls[i].y+walls[i].h)return 1;
    return 0;
}
int underwater_game_clear_box(int x0,int y0,int x1,int y1){int i;
 if(x0<0||y0<0||x1>=480||y1>=320||x0>x1||y0>y1)return 0;
 for(i=0;i<wall_count;i++)if(x0<walls[i].x+walls[i].w&&x1>=walls[i].x&&y0<walls[i].y+walls[i].h&&y1>=walls[i].y)return 0;
 return 1;
}
int game_clear_box(int x0,int y0,int x1,int y1){return underwater_game_clear_box(x0,y0,x1,y1);}
/* Synthetic world keeps the original generic fallback; the real-world helper
 * has its own differential against solid() in the chapter integration suite. */
int underwater_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
static void wall(int x,int y,int w,int h){assert(wall_count<8);walls[wall_count].x=x;
    walls[wall_count].y=y;walls[wall_count].w=w;walls[wall_count++].h=h;southern_powers_geometry_changed();magma_powers_geometry_changed();underwater_powers_geometry_changed();}
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
    if(record_draws){assert(capture_count<32);
        capture_x[capture_count]=x;capture_y[capture_count]=y;capture_off[capture_count]=off;capture_width[capture_count++]=w;}
}
static void select_command(unsigned command){
    const CreatureForm *f=creatures_form(forms[command-67]);assert(f);
    memset(&caster,0,sizeof caster);caster.form_id=f->id;caster.flags=CREATURE_OCCUPIED;
    caster.level=40;caster.xp=creatures_xp_threshold(40);caster.bond=80;
    caster.instance_id=1;caster.polarity=f->polarity;caster.trial_flags=(command-67)%3?1u<<(((command-67)%3)-1):0;caster.equipped[0]=(CreatureU8)command;
    assert(creatures_instance_validate(&caster));
}
static void setup(unsigned command){
    underwater_powers_reset();magma_powers_reset();southern_powers_reset();regional_powers_reset();northern_powers_reset();advanced_reset();
    northern_powers_tiles_release(NORTHERN_TILES_REGIONAL);
    memset(enemies,0,sizeof enemies);memset(shots,0,sizeof shots);memset(kills,0,sizeof kills);
    memset(enemy_clocks,0,sizeof enemy_clocks);memset(enemy_windups,0,sizeof enemy_windups);
    memset(shot_effects,0,sizeof shot_effects);memset(shot_phases,255,sizeof shot_phases);
    field_enabled=field_calls=field_accepted=underwater_used=0;boss_vulnerable=1;chapter_enabled=chapter_used=0;chapter_hp=160;
    field_mutates=0;field_radius=10;wall_count=absent=ability_cd=hitstop=0;px=py=cx=cy=100;face=3;boss_live=0;
    stone_guard=guard_invuln=0;max_hp=6;equipment_init(&adventure_save.equipment);
    game_health_refresh(1);game_attacks_reset();select_command(command);
}
static void enemy(unsigned i,int x,int y,int hearts){
    enemies[i]=(Enemy){x,y,hearts,0,0};enemy_hp_q4[i]=hearts*16;enemy_phases[i]=255;southern_powers_enemy_spawn(i);magma_powers_enemy_spawn(i);underwater_powers_enemy_spawn(i);
}
static void shot(unsigned i,int x,int y,int dx,int dy,int life,int owner){
    shots[i]=(Shot){x,y,dx,dy,life,owner};shot_phases[i]=CREATURE_FIRE;
    shot_effects[i]=SHOT_EFFECT_FIRE;northern_powers_shot_spawn(i);
}
static void updates(unsigned n){while(n--){underwater_powers_tick();if(!hitstop){regional_powers_tick();advanced_tick();game_combat_tick();if(ability_cd)ability_cd--;}}}
/* These vectors were authored independently from ability_contracts, rather
 * than sampled from the implementation's hit predicates. Motion-only catches
 * have a scripted honest entry/exit, not a stationary target shortcut. */
static const unsigned start[24]={12,14,16,12,14,16,12,16,16,12,14,18,12,16,12,12,16,16,12,16,18,12,18,20};
static const unsigned life[24]={36,38,48,28,54,48,40,44,48,44,154,34,36,50,56,38,44,46,44,42,52,36,52,38};
static const unsigned active_len[24]={18,12,24,6,32,20,20,18,24,28,132,4,16,24,24,15,16,18,24,14,24,16,24,4};
static const int positions[24][2]={{124,100},{128,100},{104,88},{124,100},{112,100},{124,89},
 {112,100},{130,100},{112,90},{108,100},{136,100},{124,100},{108,100},{112,100},{100,100},{116,100},
 {116,110},{111,100},{106,100},{138,100},{124,100},{112,89},{132,100},{128,108}};
static unsigned assertions,max_draws,max_tick_solid;
/* Five-phase reference, explicit complete matrix, independent of resolver. */
static unsigned reference_damage(unsigned c,unsigned defender){static const unsigned short multiplier[5][6]={
 {256,256,320,224,256,256},{256,256,256,320,224,256},{224,256,256,256,320,256},{320,224,256,256,256,256},{256,320,224,256,256,256}};
 static const unsigned phases[8]={4,2,0,3,1,0,3,4};unsigned q=(c-67)%3?24:16;
 return (q*multiplier[phases[(c-67)/3]][defender]+128)/256;}
static void expected(unsigned i,unsigned damage){if(enemy_hp_q4[i]!=160-(int)damage){fprintf(stderr,"command%d age%d target%u hp%d expected%d\n",underwater_power_kind,underwater_power_age,i,enemy_hp_q4[i],160-(int)damage);abort();}assertions++;}
static void set_motion_position(int f){static const int vx[4]={0,0,-1,1},vy[4]={1,-1,0,0};int d=underwater_power_direction;
 enemies[0].x=100+f*vx[d];enemies[0].y=100+f*vy[d];}
static void scenario_update(unsigned c){int t=underwater_power_age-(int)start[c-67];
 if(c==71&&t==0)set_motion_position(16);
 if(c==77){if(t==0)set_motion_position(30);if(t==3)set_motion_position(12);}
 solid_calls=0;updates(1);if((unsigned)solid_calls>max_tick_solid)max_tick_solid=(unsigned)solid_calls;
 draws=solid_calls=0;underwater_powers_draw();assert(solid_calls==0);assert(draws<=25);if((unsigned)draws>max_draws)max_draws=(unsigned)draws;
}
static void finish_case(unsigned c){unsigned i;for(i=0;i<180;i++)scenario_update(c);}
static void test_all_commands(void){unsigned c,p,d;
 for(c=67;c<=90;c++)for(p=0;p<6;p++){
  setup(c);enemy(0,positions[c-67][0],positions[c-67][1],10);enemy_phases[0]=p==5?255:(unsigned char)p;
  assert(underwater_power(c));assert(underwater_power_time==(int)life[c-67]);assert(underwater_power_form==(int)c-18);
  assert(underwater_power_cooldown==(c==77?180:(c-67)%3?120:90));assert(northern_powers_tiles_owner()==NORTHERN_TILES_UNDERWATER);
  updates(start[c-67]-1);expected(0,0);finish_case(c);expected(0,reference_damage(c,p));
  assert(!underwater_powers_busy()&&!northern_powers_tiles_owner());assert(underwater_power_age==(int)life[c-67]);assert(underwater_powers_companion_pose()==-1);
 }
 for(c=67;c<=90;c++)for(d=0;d<4;d++){
  static const int vx[4]={0,0,-1,1},vy[4]={1,-1,0,0};int f=positions[c-67][0]-100,l=positions[c-67][1]-100;
  setup(c);face=(int)d;enemy(0,100+f*vx[d]-l*vy[d],100+f*vy[d]+l*vx[d],10);assert(underwater_power(c));finish_case(c);expected(0,(c-67)%3?24:16);
 }
}
static void test_identity_windows(void){unsigned c,n;int time,cd;unsigned token;
 for(c=67;c<=90;c++){
  setup(c);enemy(0,positions[c-67][0],positions[c-67][1],10);assert(underwater_power(c));time=underwater_power_time;cd=ability_cd;token=underwater_serial;assert(underwater_powers_companion_pose()==0);
  hitstop=3;for(n=0;n<12;n++){updates(1);underwater_powers_draw();}assert(underwater_power_time==time&&ability_cd==cd&&!underwater_power_age);
  assert(underwater_powers_companion_pose()==0);hitstop=0;caster.instance_id=2;assert(underwater_powers_companion_pose()==-1);assert(!underwater_powers_cast_matches_selected());assert(!underwater_powers_input(16));assert(!underwater_power(c));
  finish_case(c);assert(underwater_serial==token);assert(!underwater_power_time);
  setup(c);assert(underwater_power(c));updates(start[c-67]+active_len[c-67]);enemy(0,positions[c-67][0],positions[c-67][1],10);finish_case(c);expected(0,0);
  setup(c);assert(underwater_power(c));underwater_powers_reset();updates(90);assert(!underwater_power_time&&!underwater_power_age&&!northern_powers_tiles_owner());
 }
 setup(67);assert(!underwater_power(UINT_MAX)&&!underwater_power(66)&&!underwater_power(91)&&!underwater_power(68));
 caster.instance_id=0;assert(!underwater_power(67));select_command(67);caster.selected_command=2;assert(!underwater_power(67));
 select_command(67);face=-1;assert(!underwater_power(67));face=4;assert(!underwater_power(67));face=3;px=INT_MAX;assert(!underwater_power(67));px=100;
 caster.level=0;assert(!underwater_power(67));select_command(67);absent=1;assert(!underwater_power(67));absent=0;
 assert(underwater_powers_feedback(67));assert(!underwater_power_time&&!ability_cd&&!northern_powers_tiles_owner());
}
static void test_controls_inheritance(void){unsigned c;int time,cd;
 for(c=67;c<=90;c++){
  setup(c);assert(underwater_power(c));time=underwater_power_time;cd=ability_cd;
  if(c==67||c==71||c==77||c==81){assert(!underwater_powers_can_aim()&&!underwater_powers_input(16));continue;}
  assert(underwater_powers_can_aim());assert(!underwater_powers_input(16|32));
  assert(underwater_powers_input(c==69||c==83||c==90?64:16));assert(!underwater_powers_input(32));
  assert(underwater_power_time==time&&ability_cd==cd&&!underwater_power_age);updates(9);assert(!underwater_powers_can_aim());
 }
 /* Each terminal actually casts its retained base using the selected instance. */
 for(c=67;c<=88;c+=3){unsigned branch;for(branch=1;branch<=2;branch++){
  setup(c+branch);caster.equipped[0]=(CreatureU8)c;assert(creatures_instance_validate(&caster));assert(underwater_power(c));
  assert(underwater_power_form==(int)(c+branch-18));assert(underwater_powers_cast_matches_selected());}}
 /* An expired startup direction cannot reverse an already travelling shape. */
 setup(73);assert(underwater_power(73));updates(8);assert(!underwater_powers_input(16));
}
static void test_walls_and_holes(void){unsigned c;
 for(c=67;c<=90;c++)if(c!=81){
  setup(c);enemy(0,positions[c-67][0],positions[c-67][1],10);wall(103,0,1,320);assert(underwater_power(c));finish_case(c);expected(0,0);
 }
 /* Endpoint-inclusive diagonal corner clipping. */
 setup(79);enemy(0,108,100,10);wall(101,100,1,1);wall(100,99,1,1);assert(underwater_power(79));finish_case(79);expected(0,0);
 /* Safe gaps are true non-damaging pixels, not just transparent artwork. */
 {static const unsigned commands[]={69,72,74,75,78,80,82,83,84,88,89,90};
  static const int safe[][2]={{124,100},{124,100},{120,100},{118,100},{124,108},{100,100},{100,100},{116,100},{100,100},{112,92},{124,100},{124,100}};
  for(c=0;c<sizeof commands/sizeof commands[0];c++){setup(commands[c]);enemy(0,safe[c][0],safe[c][1],10);assert(underwater_power(commands[c]));finish_case(commands[c]);expected(0,0);}}
 /* Moving collision changes clip before any later damage and do not reset. */
 setup(67);enemy(0,124,100,10);assert(underwater_power(67));updates(13);wall(110,0,1,320);underwater_powers_draw();assert(underwater_power_age==13);finish_case(67);expected(0,0);
 setup(73);wall(108,0,1,320);assert(underwater_power(73));updates(18);wall_count=0;underwater_powers_geometry_changed();enemy(0,120,100,10);finish_case(73);expected(0,0);
}
static void test_catch_push_and_slots(void){unsigned n;int oldx,oldy;
 setup(70);enemy(0,124,100,10);assert(underwater_power(70));updates(12);expected(0,16);assert(enemies[0].x==124&&enemies[0].y==94);
 setup(70);enemy(0,124,100,10);wall(120,92,9,1);assert(underwater_power(70));updates(12);assert(enemies[0].y>=97);expected(0,16);
 setup(71);enemy(0,112,100,10);assert(underwater_power(71));updates(14);enemies[0].x=116;updates(1);updates(7);expected(0,0);updates(1);expected(0,24);assert(enemies[0].x==114);
 setup(71);enemy(0,112,100,10);assert(underwater_power(71));updates(14);enemies[0].x=116;updates(1);enemy(0,116,100,10);finish_case(71);expected(0,0);
 setup(77);enemy(0,136,100,10);assert(underwater_power(77));updates(14);enemies[0].x=130;updates(1);enemies[0].x=136;updates(1);enemies[0].x=112;finish_case(77);expected(0,0);
 setup(77);enemy(0,130,100,10);assert(underwater_power(77));updates(14);enemies[0].x=112;finish_case(77);expected(0,0); /* No real front entry. */
 setup(78);enemy(0,124,100,10);assert(underwater_power(78));updates(18);expected(0,24);enemy(0,124,100,10);
 for(n=0;n<65536;n++)underwater_powers_enemy_spawn(0);finish_case(78);expected(0,0);
 setup(70);enemy(0,124,100,10);enemies[0].kind=3;oldx=enemies[0].x;oldy=enemies[0].y;assert(underwater_power(70));finish_case(70);expected(0,0);assert(enemies[0].x==oldx&&enemies[0].y==oldy);
 setup(78);enemy(0,INT_MAX,INT_MIN,10);assert(underwater_power(78));finish_case(78);expected(0,0);underwater_powers_enemy_spawn(UINT_MAX);
}
static void test_field_boss_and_provenance(void){unsigned c,n;
 for(c=67;c<=90;c++)if(c!=71&&c!=77){
  setup(c);field_enabled=1;field_x=positions[c-67][0];field_y=positions[c-67][1];assert(underwater_power(c));finish_case(c);assert(field_accepted==1);assert(field_calls==1);
  setup(c);field_enabled=1;field_x=positions[c-67][0];field_y=positions[c-67][1];assert(underwater_power(c));caster.instance_id=2;finish_case(c);assert(!field_accepted&&!field_calls);
  setup(c);chapter_enabled=1;chapter_x=positions[c-67][0];chapter_y=positions[c-67][1];boss_vulnerable=0;assert(underwater_power(c));finish_case(c);assert(chapter_hp==160);
  setup(c);chapter_enabled=1;chapter_x=positions[c-67][0];chapter_y=positions[c-67][1];assert(underwater_power(c));finish_case(c);assert(chapter_hp==160-(int)((c-67)%3?24:16));
 }
 setup(67);field_enabled=1;field_x=124;field_y=100;assert(underwater_power(67));underwater_serial++;finish_case(67);assert(!field_accepted);
 setup(67);field_enabled=1;field_x=124;field_y=100;assert(underwater_power(67));
 caster.instance_id=2;underwater_powers_selection_changed();caster.instance_id=1;finish_case(67);assert(!field_calls&&!field_accepted);
 /* Root/stagger timers and genuine hostile/friendly shot identities untouched
  * by every new module tick, draw, reset, or startup orientation. */
 for(c=67;c<=90;c++){
  setup(c);enemy(0,positions[c-67][0],positions[c-67][1],10);rooted_enemies[0]=23;slowed_enemies[0]=29;enemy_stagger_ticks[0]=31;enemy_windups[0]=27;
  shot(0,124,100,-2,0,30,1);shot(1,124,100,2,0,30,0);assert(underwater_power(c));
  for(n=0;n<life[c-67];n++){underwater_powers_tick();underwater_powers_draw();}
  underwater_powers_reset();assert(rooted_enemies[0]==23&&slowed_enemies[0]==29&&enemy_stagger_ticks[0]==31&&enemy_windups[0]==27);
  assert(shots[0].life==30&&shots[0].owner==1&&shots[1].life==30&&shots[1].owner==0);
 }
}
static void test_visible_field_overlap(void){unsigned c;
 /* Every base teaching command accepts a natural three-pixel lateral offset. */
 for(c=67;c<=88;c+=3){setup(c);field_enabled=1;field_x=positions[c-67][0];field_y=positions[c-67][1]+3;
  assert(underwater_power(c));finish_case(c);assert(field_accepted==1&&field_calls==1);}
 /* Visible ring edge intersects the one-pixel hook; enemy center still misses. */
 setup(73);enemy(0,112,103,10);field_enabled=1;field_x=112;field_y=103;
 assert(underwater_power(73));finish_case(73);assert(field_accepted==1);expected(0,0);
 /* A ring completely inside empty space remains empty. */
 setup(82);field_enabled=1;field_x=field_y=100;assert(underwater_power(82));finish_case(82);assert(!field_accepted);
 setup(78);field_enabled=1;field_x=124;field_y=108;field_radius=1;assert(underwater_power(78));finish_case(78);assert(!field_accepted);
 setup(90);field_enabled=1;field_x=124;field_y=100;field_radius=1;assert(underwater_power(90));finish_case(90);assert(!field_accepted);
 /* Overlap cannot carry a field receipt through a wall from its visible edge. */
 setup(73);field_enabled=1;field_x=120;field_y=103;wall(115,0,1,320);assert(underwater_power(73));finish_case(73);assert(!field_accepted);
 setup(70);field_enabled=1;field_x=128;field_y=100;wall(124,0,1,320);assert(underwater_power(70));finish_case(70);assert(!field_accepted);
}
static void test_field_mutation_invalidates_cache(void){
 setup(70);field_enabled=8;field_x=124;field_y=100;field_mutates=1;
 assert(underwater_power(70));updates(12);assert(field_accepted==1&&field_calls==1);
 finish_case(70);assert(field_accepted==1&&field_calls==1);
}
static void test_gate_natural_pursuit(void){unsigned n;
 /* Native ordinary enemy pacing: one pixel each six simulation updates. */
 setup(77);enemy(0,138,100,10);assert(underwater_power(77));
 for(n=1;n<=154;n++){if(n%6==0)enemies[0].x--;updates(1);if(n<144)expected(0,0);}
 expected(0,24);assert(!underwater_powers_busy()&&ability_cd==26);
 setup(77);enemy(0,138,100,10);assert(underwater_power(77));
 for(n=1;n<=154;n++){if(n%6==0)enemies[0].x--;if(n==60)enemies[0].y=107;updates(1);}expected(0,0);
 setup(77);enemy(0,138,100,10);assert(underwater_power(77));
 for(n=1;n<=154;n++){if(n%6==0)enemies[0].x+=n<60?-1:1;updates(1);}expected(0,0);
}
static void test_shared_lease_and_trail(void){unsigned owner,n;int before;
 for(owner=NORTHERN_TILES_REGIONAL;owner<=NORTHERN_TILES_MAGMA;owner++){
  setup(67);assert(northern_powers_tiles_claim(owner));before=uploads;assert(!underwater_power(67));assert(uploads==before);assert(northern_powers_tiles_release(owner));
  assert(underwater_power(67));assert(!northern_powers_tiles_claim(owner));assert(!northern_powers_tiles_release(NORTHERN_TILES_UNDERWATER));
 }
 setup(81);enemy(0,108,100,10);assert(underwater_power(81));
 for(n=0;n<12;n++){if(n<8)px++;updates(1);}assert(px==108&&py==100);updates(11);expected(0,0);finish_case(81);expected(0,24);assert(px==108&&py==100);
 setup(81);enemy(0,108,100,10);assert(underwater_power(81));px=200;updates(4);px=108;finish_case(81);expected(0,0);
 setup(76);wall(110,70,1,61);enemy(0,109,80,10);assert(underwater_power(76));finish_case(76);expected(0,16);
 setup(76);wall(110,90,1,11);enemy(0,109,80,10);assert(underwater_power(76));finish_case(76);expected(0,0); /* Convex corner stops crawl. */
}

/* Independent integer set oracle for nine nonconvex/static signatures. Every
 * point in the51x49 domain is tested, in fresh six-identity batches. Expected
 * membership does not call the production shape/phase/collision helpers. */
static int reference_union(unsigned c,int f,int s){int q=f-24,z=-s;
 switch(c){
 case 69:return ((f>=0&&f<=7)||(f>=40&&f<=47))&&((s>=-16&&s<=-9)||(s>=8&&s<=15));
 case 70:return f>=18&&f<=29&&s>=-8&&s<=7;
 case 72:return f>=18&&f<=29&&((s>=-18&&s<=-5)||(s>=4&&s<=17));
 case 75:return (((f>=10&&f<=13)||(f>=34&&f<=37))&&s>=-16&&s<=-5)||(f>=22&&f<=25&&s>=4&&s<=15);
 case 78:return f>=12&&f<36&&s>=-14&&s<14&&!(z>=-11&&z<-5&&f>=17&&f<27)&&!(z>=4&&z<10&&f>=21&&f<31);
 case 83:return (f>=14&&f<=17&&((s>=-24&&s<=-5)||(s>=4&&s<=23)))||(s>=-2&&s<=1&&((f>=4&&f<=11)||(f>=20&&f<=27)));
 case 88:return f>=0&&f<=24&&((s>=-12&&s<=-10)||(s>=-6&&s<=-4)||(s>=0&&s<=2)||(s>=6&&s<=8));
 case 89:return f>=10&&f<=38&&s>=-14&&s<=14&&abs(q+s)>3;
 case 90:return f>=0&&f<=34&&abs(s)*34<=18*f&&(abs(q)>=3||abs(s)>=3);
 default:assert(0);return 0;
 }
}
static void test_independent_geometry_grid(void){static const unsigned commands[9]={69,70,72,75,78,83,88,89,90};unsigned ci,n,i,count;
 for(ci=0;ci<9;ci++)for(n=0;n<51*49;n+=6){unsigned c=commands[ci];int wanted[6];setup(c);count=0;
  for(i=0;i<6&&n+i<51*49;i++){int f=(int)((n+i)/49),s=(int)((n+i)%49)-24;enemy(i,100+f,100+s,10);wanted[i]=reference_union(c,f,s);count++;}
  assert(underwater_power(c));updates(life[c-67]);for(i=0;i<count;i++)expected(i,wanted[i]?((c-67)%3?24:16):0);
 }
}
static void test_every_slot_and_ordinary_kind(void){unsigned c,k;
 for(c=67;c<=90;c++){
  setup(c);enemy(0,positions[c-67][0],positions[c-67][1],10);assert(underwater_power(c));enemy(0,positions[c-67][0],positions[c-67][1],10);finish_case(c);expected(0,0);
  for(k=1;k<=2;k++){setup(c);enemy(0,positions[c-67][0],positions[c-67][1],10);enemies[0].kind=(int)k;assert(underwater_power(c));finish_case(c);expected(0,(c-67)%3?24:16);}
 }
 setup(81);enemy(0,100,100,10);assert(underwater_power(81));for(k=0;k<12;k++){if(k<8)px++;updates(1);}wall(104,80,1,40);finish_case(81);expected(0,0);
}
static void test_startup_choices_change_geometry(void){
 setup(78);assert(underwater_power(78));assert(underwater_powers_companion_pose()==0);updates(18);assert(underwater_powers_companion_pose()==1);
 updates(4);assert(underwater_powers_companion_pose()==2);updates(6);assert(underwater_powers_companion_pose()==-1);
 setup(83);enemy(0,116,120,10);assert(underwater_power(83));updates(44);expected(0,24);
 setup(83);enemy(0,116,120,10);enemy(1,136,100,10);assert(underwater_power(83));assert(underwater_powers_input(64));updates(44);expected(0,0);expected(1,24);
 setup(69);enemy(0,104,88,10);enemy(1,144,112,10);assert(underwater_power(69));assert(underwater_powers_input(128));updates(16);expected(0,0);expected(1,24);
 setup(73);enemy(0,120,112,10);assert(underwater_power(73));assert(underwater_powers_input(16));updates(40);expected(0,16);
 setup(73);enemy(0,120,112,10);assert(underwater_power(73));updates(40);expected(0,0);
 setup(77);enemy(0,136,100,10);assert(underwater_power(77));updates(14);enemies[0].x=112;updates(1);expected(0,24);
}
int main(void){assert(creatures_catalog_validate());test_all_commands();test_identity_windows();test_controls_inheritance();test_walls_and_holes();test_catch_push_and_slots();test_field_boss_and_provenance();test_shared_lease_and_trail();test_visible_field_overlap();test_gate_natural_pursuit();test_field_mutation_invalidates_cache();test_independent_geometry_grid();test_startup_choices_change_geometry();test_every_slot_and_ordinary_kind();
 printf("Underwater24 synthetic strict integration: %u damage assertions; max draw objects%u; max tick scenery probes%u\n",assertions,max_draws,max_tick_solid);return 0;}
