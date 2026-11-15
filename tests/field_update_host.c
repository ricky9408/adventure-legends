#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "field_controls.h"
#include "weapon_actions.h"
#include "campaign_rules.h"
#include "world.h"

enum {PLAY=1,DIALOG=2,PAUSE=3,KEY_A=1,KEY_B=2,KEY_SELECT=4,KEY_START=8,
 KEY_RIGHT=16,KEY_LEFT=32,KEY_UP=64,KEY_DOWN=128,KEY_R=256,MAX_ENEMIES=6};
static int ticks,hitstop,pressed,keys,game_state,room,walk,walk_phase,face,swing;
static int step_cd,area_ticks,invuln,ability_cd,heal_cd,stone_guard,guard_invuln;
static int power_effect,transition_lock,covenants_cooldown_owned,summoned;
static int advanced_guard_charges,save_requested,px,py;
static int underwater_power_time,underwater_power_cast_time,return_power_time;
static int return_power_cast_time,horizons_power_time,horizons_power_cast_time;
static int covenants_power_time,covenants_power_cast_time;
static unsigned room_flags;
static struct {int life;} impacts[6];
static struct {int hp;} enemies[6];
static FieldControlState field_controls;
static WeaponAttack weapon_action;
static EquipmentStats gear_stats;
const CampaignRoom campaign_rooms[10]={{0}};

static int context,context_modal,aim,road,entry,attack_modal,ability_modal,rest_pending;
static int stop_event,event_calls,return_flags;
static unsigned calls,checks,move_calls,attack_calls,ability_calls,actor_calls;
static unsigned goal_calls,toggle_calls,cancel_calls,suspend_calls,save_calls,camera_calls;
static unsigned advanced_at,geometry_at,move_at,attack_at,follow_at,shots_at,enemies_at;
static unsigned consumed_held,power_input;
static int moved_x,moved_y,entered_room,entered_spawn;
#define CHECK(condition) do{checks++;assert(condition);}while(0)
#define NOTE() (++calls)

static int event_frame(void){event_calls++;NOTE();return event_calls==stop_event;}
static void journal_nav_open(void){NOTE();}
static int game_field_context_input(void){NOTE();if(context_modal)game_state=DIALOG;return context;}
static void game_power_preview_cancel(void){NOTE();cancel_calls++;}
static void field_goal_input(unsigned input){CHECK(input&KEY_SELECT);NOTE();goal_calls++;}
static void game_field_companion_toggle(void){NOTE();toggle_calls++;summoned=!summoned;}
static int game_power_aim_hold(unsigned held){consumed_held=held;NOTE();return aim;}
static void advanced_tick(void){advanced_at=NOTE();}
static void regional_powers_tick(void){NOTE();}
static void northern_powers_tick(void){NOTE();}
static void game_geometry_sync(void){geometry_at=NOTE();}
static void southern_powers_tick(void){NOTE();}
static void magma_powers_tick(void){NOTE();}
static void underwater_powers_tick(void){NOTE();}
static void return_powers_tick(void){NOTE();}
static void horizons_powers_tick(void){NOTE();}
static void covenants_powers_tick(void){NOTE();}
static void game_combat_tick(void){NOTE();}
static void game_attacks_suspend(void){NOTE();suspend_calls++;weapon_action_suspend(&weapon_action);}
static void underwater_powers_input(unsigned power){NOTE();power_input=power;}
static int return_powers_input(unsigned power){NOTE();power_input=power;return return_flags;}
static int horizons_powers_input(unsigned power){NOTE();power_input=power;return return_flags;}
static int covenants_powers_input(unsigned power){NOTE();power_input=power;return return_flags;}
static void move_player(int dx,int dy){move_at=NOTE();move_calls++;moved_x=dx;moved_y=dy;}
static int game_road_step(void){NOTE();return road;}
static int walk_entry(void){NOTE();return entry;}
static void game_attack_update(int held,int edge){
 attack_at=NOTE();attack_calls++;
 weapon_action_tick(&weapon_action,&gear_stats,(unsigned)face,!!(held&KEY_A),!!(edge&KEY_A),0);
 if(attack_modal)game_state=DIALOG;
}
static int magma_game_save_prepare_pending(void){NOTE();return rest_pending;}
static void save_frame(void){NOTE();save_calls++;}
static void game_field_ability(void){NOTE();ability_calls++;if(ability_modal)game_state=DIALOG;}
static void game_companion_follow(void){follow_at=NOTE();}
static void update_shots(void){shots_at=NOTE();actor_calls++;}
static void return_legacy_tick(void){NOTE();}
static void game_arrows_update(void){NOTE();}
static void update_enemies(void){enemies_at=NOTE();}
static void update_boss(void){NOTE();}
static void region_game_tick(void){NOTE();}
static void north_game_tick(void){NOTE();}
static void south_game_tick(void){NOTE();}
static void magma_game_tick(void){NOTE();}
static void underwater_game_tick(void){NOTE();}
static void return_game_tick(void){NOTE();}
static void horizons_game_tick(void){NOTE();}
static void covenants_game_tick(void){NOTE();}
static void covenants_game_tick_old(void){NOTE();}
static void save_game(void){NOTE();save_calls++;}
static void show_scene(int scene,int a,int b){CHECK(scene==CD_PATROL_CLEAR);(void)a;(void)b;game_state=DIALOG;}
static int region_game_is_room(unsigned area){return area>=16&&area<22;}
static int north_game_is_room(unsigned area){return area>=22&&area<30;}
static int south_game_is_room(unsigned area){return area>=30&&area<38;}
static int trials_is_room(int area){return area==14||area==15;}
static int trials_exit(int area,int x,int y){(void)area;(void)x;(void)y;return 1;}
static void enter_room(int area,int spawn){NOTE();entered_room=area;entered_spawn=spawn;}
static unsigned progress_bits(void){return room_flags;}
static int game_road_managed(unsigned from,unsigned to){(void)from;(void)to;return 0;}
static int ab(int value){return value<0?-value:value;}
static void camera_update(int force){CHECK(!force);NOTE();camera_calls++;}

#include "field_update.inc"

static void reset(void){
 ticks=hitstop=pressed=keys=room=walk=walk_phase=face=swing=0;game_state=PLAY;
 step_cd=area_ticks=invuln=ability_cd=heal_cd=stone_guard=guard_invuln=0;
 power_effect=transition_lock=covenants_cooldown_owned=summoned=0;
 advanced_guard_charges=save_requested=0;px=100;py=100;
 underwater_power_time=underwater_power_cast_time=return_power_time=0;
 return_power_cast_time=horizons_power_time=horizons_power_cast_time=0;
 covenants_power_time=covenants_power_cast_time=0;room_flags=0;
 memset(impacts,0,sizeof impacts);memset(enemies,0,sizeof enemies);
 memset(&weapon_action,0,sizeof weapon_action);memset(&field_controls,0,sizeof field_controls);
 memset(&gear_stats,0,sizeof gear_stats);
 gear_stats.weapon_class=EQUIPMENT_SWORD;gear_stats.phase=EQUIPMENT_NEUTRAL_PHASE;
 gear_stats.speed_q8=256;gear_stats.diagonal_q8=181;
 context=context_modal=aim=road=entry=attack_modal=ability_modal=rest_pending=0;
 stop_event=event_calls=return_flags=0;
 calls=move_calls=attack_calls=ability_calls=actor_calls=goal_calls=toggle_calls=0;
 cancel_calls=suspend_calls=save_calls=camera_calls=0;
 advanced_at=geometry_at=move_at=attack_at=follow_at=shots_at=enemies_at=0;
 consumed_held=power_input=0;moved_x=moved_y=0;entered_room=entered_spawn=-1;
}

static void modal_and_hitstop_freeze_field(void){
 reset();hitstop=2;impacts[0].life=3;ability_cd=7;pressed=KEY_START;
 field_update();CHECK(ticks==1&&hitstop==1&&impacts[0].life==2);
 CHECK(game_state==PLAY&&ability_cd==7&&!move_calls&&!attack_calls&&!actor_calls);
 reset();pressed=KEY_START|KEY_B|KEY_SELECT;ability_cd=7;
 field_update();CHECK(game_state==PAUSE&&ability_cd==7&&!goal_calls&&!ability_calls&&!actor_calls);
 reset();context=1;context_modal=1;pressed=KEY_B|KEY_SELECT;
 field_update();CHECK(game_state==DIALOG&&cancel_calls==1&&!goal_calls&&!advanced_at&&!actor_calls);
}

static void context_owns_buttons_while_world_advances(void){
 reset();context=1;summoned=1;keys=pressed=KEY_A|KEY_B|KEY_R|KEY_SELECT|KEY_RIGHT;
 ability_cd=3;walk=1;weapon_action.phase=WEAPON_CHARGING;weapon_action.weapon_class=EQUIPMENT_BOW;
 field_update();CHECK(cancel_calls==1&&suspend_calls==1&&!toggle_calls&&!goal_calls);
 CHECK(ability_cd==2&&consumed_held==0&&!walk&&!move_calls&&!attack_calls&&!ability_calls);
 CHECK(actor_calls==1&&camera_calls==1&&weapon_action.phase==WEAPON_IDLE);
}

static void recall_precedes_aim_and_one_timer_tick(void){
 reset();summoned=1;keys=pressed=KEY_R|KEY_B;
 step_cd=area_ticks=invuln=ability_cd=heal_cd=stone_guard=guard_invuln=2;
 power_effect=transition_lock=2;
 field_update();CHECK(toggle_calls==1&&!summoned&&consumed_held==0&&!ability_calls);
 CHECK(step_cd==1&&area_ticks==1&&invuln==1&&ability_cd==1&&heal_cd==1);
 CHECK(stone_guard==1&&guard_invuln==1&&power_effect==1&&transition_lock==1);
 CHECK(field_controls.power_blocked);
 keys=KEY_B;pressed=0;field_update();CHECK(!ability_calls);
 keys=pressed=0;field_update();keys=pressed=KEY_B;field_update();CHECK(ability_calls==1);
}

static void movement_and_attack_keep_order(void){
 reset();keys=pressed=KEY_RIGHT|KEY_UP|KEY_A|KEY_B|KEY_SELECT;
 field_update();CHECK(goal_calls==1&&moved_x==181&&moved_y==-181&&walk_phase==1);
 CHECK(advanced_at<geometry_at&&geometry_at<move_at&&move_at<attack_at);
 CHECK(attack_at<follow_at&&follow_at<shots_at&&shots_at<enemies_at);
 CHECK(weapon_action.phase==WEAPON_WINDUP&&face==1&&ability_calls==1&&actor_calls==1);
 reset();aim=KEY_RIGHT;summoned=1;keys=pressed=KEY_RIGHT|KEY_B;
 field_update();CHECK(!walk&&!move_calls&&power_input==(FIELD_POWER_ACTION|KEY_RIGHT));
 reset();weapon_action.phase=WEAPON_CHARGING;weapon_action.weapon_class=EQUIPMENT_BOW;
 keys=KEY_RIGHT|KEY_A;field_update();CHECK(moved_x==192&&moved_y==0);
}

static void transition_or_dialogue_prevents_late_attacks(void){
 reset();road=1;keys=pressed=KEY_A|KEY_B;field_update();
 CHECK(move_calls==1&&!attack_calls&&!ability_calls&&!actor_calls);
 reset();entry=1;keys=pressed=KEY_A|KEY_B;field_update();CHECK(!attack_calls&&!actor_calls);
 reset();attack_modal=1;keys=pressed=KEY_A|KEY_B;field_update();
 CHECK(attack_calls==1&&game_state==DIALOG&&!ability_calls&&!actor_calls);
 reset();ability_modal=1;keys=pressed=KEY_B;field_update();
 CHECK(ability_calls==1&&game_state==DIALOG&&!actor_calls);
 reset();room=38;save_requested=rest_pending=1;keys=pressed=KEY_B;field_update();
 CHECK(save_calls==1&&attack_calls==1&&!ability_calls&&!actor_calls);
 reset();summoned=return_power_time=1;return_flags=2;keys=pressed=KEY_B;field_update();
 CHECK(power_input==FIELD_POWER_ACTION&&!ability_calls&&actor_calls==1);
}

static void event_boundaries_stop_the_next_stage(void){
 int boundary;
 for(boundary=1;boundary<=5;boundary++){
  reset();stop_event=boundary;keys=pressed=KEY_A|KEY_B;field_update();
  CHECK(event_calls==boundary&&!camera_calls);
  CHECK(attack_calls==(unsigned)(boundary>=3));
  CHECK(ability_calls==(unsigned)(boundary>=4));
  CHECK(actor_calls==(unsigned)(boundary>=5));
 }
 reset();room=6;field_update();CHECK(room_flags&CF_SKY_PATROL_CLEAR);
 CHECK(save_calls==1&&game_state==DIALOG&&!camera_calls);
 reset();room=15;keys=KEY_DOWN;field_update();CHECK(entered_room==1&&entered_spawn==0&&camera_calls==1);
}

int main(void){
 modal_and_hitstop_freeze_field();context_owns_buttons_while_world_advances();
 recall_precedes_aim_and_one_timer_tick();movement_and_attack_keep_order();
 transition_or_dialogue_prevents_late_attacks();event_boundaries_stop_the_next_stage();
 printf("PASS %u field stage checks: input ownership, timer order, real weapon dispatch, travel/dialogue/save barriers\n",checks);
 return 0;
}
