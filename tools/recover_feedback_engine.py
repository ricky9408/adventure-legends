"""Replay owned engine edits on the verified immutable Covenants E baseline.

Retained as reconstruction provenance after the execution workspace rollback.
It is not a save migration or release-publishing tool.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'src/game.c';s=p.read_text()
if '#include "save_feedback.h"' in s:raise SystemExit('Engine feedback already applied')
s=s.replace('#include "combat_rules.h"','#include "combat_rules.h"\n#include "travel_feedback.h"\n#include "feedback_world.h"\n#include "save_feedback.h"\n#include "journal_nav.h"\n#include "economy.h"\n#include "game_shop.h"')
s=s.replace('int save_begin_pending,save_completion_pending;','''int save_begin_pending,save_completion_pending;
int save_ordinary_scope,arrival_input_mask,title_option,save_ordinary_defer;
static int locked_notice_room=-1,locked_notice_x,locked_notice_y,locked_notice_text;
volatile unsigned save_step_cycles,save_step_max_cycles,save_begin_cycles,save_begin_max_cycles;
volatile unsigned render_world_cycles,render_card_cycles,render_actors_cycles;
int world_mask_active,world_mask_left,world_mask_top,world_mask_right,world_mask_bottom,world_mask_disabled;
volatile unsigned render_profile_serial,render_profile_frame,render_profile_state,render_profile_room,render_profile_world,render_profile_card,render_profile_actors,render_profile_save_begin,render_profile_save_step;''')
s=s.replace('static unsigned short covenants_wave_shots;','static unsigned short covenants_wave_shots;\nstatic unsigned char defeated_enemy_mask;')
s=s.replace('COLD void save_game(void);','COLD void save_game(void);\nCOLD void save_game_ordinary(void);\nCOLD int walk_entry(void);\nint game_display_state(void);\nint game_save_badge_id(void);\nu32 cycle_now(void);')
s=s.replace('#define CACHE_FIELDS 38','#define CACHE_FIELDS 45')
s=s.replace('void pix(int x,int y,u8 c){','COLD int game_world_rect_hidden(int x,int y,int w,int h){return world_mask_active&&x>=world_mask_left&&y>=world_mask_top&&x+w<=world_mask_right&&y+h<=world_mask_bottom;}\nvoid pix(int x,int y,u8 c){')
s=s.replace('void rect(int x,int y,int w,int h,u8 c){int yy,xx;','void rect(int x,int y,int w,int h,u8 c){int yy,xx;if(world_mask_active&&game_world_rect_hidden(x,y,w,h))return;')
s=s.replace('void sprite(const u8 *data,int x,int y,int w,int h,int flash){int xx,yy;','void sprite(const u8 *data,int x,int y,int w,int h,int flash){int xx,yy;if(world_mask_active&&game_world_rect_hidden(x,y,w,h))return;')
s=s.replace('void line(int x,int y,int x2,int y2,int col){int dx=','void line(int x,int y,int x2,int y2,int col){if(world_mask_active&&game_world_rect_hidden(x<x2?x:x2,y<y2?y:y2,ab(x-x2)+1,ab(y-y2)+1))return;int dx=')
s=s.replace('void copy_bg(int id){REG32','void copy_bg(int id){if(COPY_OPAQUE_MODAL_BITMAP&&copy_modal_background(backgrounds[id],0,240))return;REG32')
s=s.replace(' /* Menus are background pixels: hide actors where a panel covers them. */',' if(x+w>146&&x<238&&y+h>29&&y<46&&game_save_badge_id())return;\n if(game_state==PLAY&&game_shop_reward_visible()&&x+w>5&&x<121&&y+h>122&&y<139)return;\n /* Menus are background pixels: hide actors where a panel covers them. */')
s=s.replace('if(game_state==PAUSE||game_state==DEAD||','if(game_display_state()==PAUSE||game_display_state()==11||game_state==13||game_state==DEAD||')
s=s.replace('if(game_state==DIALOG&&y+h>99)','if(game_display_state()==DIALOG&&y+h>99)')
s=s.replace('if((game_state==SAVE_PENDING||game_state==EVENT_PENDING)&&x+w>37&&x<203&&y+h>77&&y<111)return;','')
s=s.replace('int i,anim=roll_ticks?(roll_ticks/3)&3:(swing','int i,anim=(swing').replace('py-11+(roll_ticks?2:0)','py-11')
s=s.replace(' if(roll_ticks){obj_add(OBJ_SPARK,px-sign(roll_dx)*12-4,py-sign(roll_dy)*12,8,8,1,py-1,0);}\n','')
s=s.replace(' if(room==22)south_actor(SOUTH_SPR_FERRY,208,208);\n','').replace(' if(room==30)magma_actor(MAGMA_SPR_LIFT,288,248);\n','').replace(' if(room==38)underwater_actor(UNDERWATER_SPR_GATE,416,224);\n','')
a=s.index('COLD void game_region_warp(');b=s.index('\n',a);s=s[:a]+s[a:b].replace('game_attacks_suspend();camera_update(1);','game_attacks_suspend();travel_feedback_arrive((unsigned)room,x,y);camera_update(1);')+s[b:]
s=s.replace('COLD void dialogue(int a,int b,int next){dialog_lines[0]=a;','''COLD void dialogue(int a,int b,int next){
 if(a==TX_RG_LOCKED_A||a==TX_NT_LOCKED_A||a==TX_ST_LOCKED_A||a==TX_MG_LOCKED||a==TX_UW_LOCKED||a==TX_RT_LOCKED||a==TX_HZ_LOCKED||a==TX_HZ_LOCKED_FINAL||a==TX_CV_LOCKED){
  if(locked_notice_room==room&&locked_notice_text==a&&near(px,py,locked_notice_x,locked_notice_y,24))return;
  locked_notice_room=room;locked_notice_text=a;locked_notice_x=px;locked_notice_y=py;
 }
 dialog_lines[0]=a;''')
s=s.replace('make_save(&adventure_save.campaign,r,spawn);acknowledge_save_failure();save_failed=0;save_requested=1;saved_room=r;','make_save(&adventure_save.campaign,r,spawn);/* Only verified DONE clears failure. */if(!save_requested){save_feedback_ordinary=save_ordinary_scope!=0;save_ordinary_defer=save_feedback_ordinary?2:0;}else if(!save_ordinary_scope)save_feedback_ordinary=0;save_requested=1;save_feedback_requests++;saved_room=r;')
s=s.replace('COLD void save_game(void){save_at(room,checkpoint_spawn);}','COLD void save_game(void){save_at(room,checkpoint_spawn);}\nCOLD void save_game_ordinary(void){int prior=save_ordinary_scope;save_ordinary_scope=1;save_game();save_ordinary_scope=prior;}')
s=s.replace('#include "covenants_engine.inc"','#include "covenants_engine.inc"\nint game_display_state(void){if(game_state==SAVE_PENDING)return save_resume_state;if(game_state==EVENT_PENDING)return event_resume_state;return game_shop_display_state();}')
a=s.index('COLD void save_frame(void){');b=s.index('\nCOLD void show_scene(',a)
s=s[:a]+'''COLD void save_frame(void){unsigned status;
 if(save5_take_preempted()){save_feedback_background=0;save_feedback_preemptions++;save_feedback_invalidate();if(!save_requested){save_requested=1;save_feedback_ordinary=1;}}
 if(economy_pending()||event_frame()||game_state==EVENT_PENDING)return;
 if(save5_preflight_active())return;
 if(save_feedback_background){
  if(save_requested&&!save_feedback_ordinary){save5_cancel_background();save5_take_preempted();save_feedback_background=0;save_feedback_preemptions++;save_feedback_invalidate();}
  else{
#ifndef GAME_HOST_TEST
   unsigned started=cycle_now();
#endif
   status=save5_step(512);save_feedback_background_frames++;
#ifndef GAME_HOST_TEST
   save_step_cycles=cycle_now()-started;if(save_step_cycles>save_step_max_cycles)save_step_max_cycles=save_step_cycles;
#endif
   if(status==SAVE5_BUSY)return;
   save_feedback_background=0;save5_set_preemptible(0);save_feedback_complete(status==SAVE5_DONE);
   if(status==SAVE5_DONE){has_save=1;save_failed=0;acknowledge_save_failure();}else{save_failed=save_failure_notice=1;toast(TX_C_SAVE_FAILED);}return;
  }
 }
 if(save_requested&&game_state!=SAVE_PENDING){
  if(!magma_game_save_prepare_pending()&&save_feedback_same(&adventure_save)){save_requested=0;save_feedback_skipped++;return;}
  if(save_feedback_ordinary&&!magma_game_save_prepare_pending()){
   if(save_ordinary_defer){save_ordinary_defer--;return;}
#ifndef GAME_HOST_TEST
   unsigned started=cycle_now();
#endif
   save_requested=0;save_feedback_capture(&adventure_save);
   if(save5_begin(&adventure_save)){save_feedback_background=1;save5_set_preemptible(1);}
   else{save_feedback_complete(0);save_failed=save_failure_notice=1;toast(TX_C_SAVE_FAILED);}
#ifndef GAME_HOST_TEST
   save_begin_cycles=cycle_now()-started;if(save_begin_cycles>save_begin_max_cycles)save_begin_max_cycles=save_begin_cycles;
#endif
   return;
  }
  save_requested=0;save_completion_pending=0;save_resume_state=game_state;game_attacks_suspend();save_begin_pending=magma_game_save_prepare_pending()?3:1;game_state=SAVE_PENDING;
 }
}'''+s[b:]
s=s.replace('else if(dialogue_seen)save_game();','else if(dialogue_seen)save_game_ordinary();')
s=s.replace('COLD void spawn_enemies(void){covenants_wave_enemies=0;','COLD void spawn_enemies(void){defeated_enemy_mask=0;covenants_wave_enemies=0;')
s=s.replace('if(r>=70)covenants_game_enter','save_ordinary_scope=1;\n if(r>=70)covenants_game_enter',1)
s=s.replace(' if(r==3||r==8||r==13){boss_x=120;',' save_ordinary_scope=0;\n if(r==3||r==8||r==13){boss_x=120;',1)
s=s.replace(' save_game();if(r==5',' travel_feedback_arrive((unsigned)room,px,py);arrival_input_mask|=keys&(KEY_A|KEY_B|KEY_R|KEY_START|KEY_L|KEY_SELECT);\n save_game_ordinary();if(r==5',1)
s=s.replace('COLD void start_game(int resume){int oldsave=has_save;','COLD void start_game(int resume){int oldsave=has_save;save5_cancel_background();save5_take_preempted();save_feedback_reset();travel_feedback_reset();locked_notice_room=-1;game_shop_reset();arrival_input_mask=0;title_option=0;save_ordinary_defer=0;save_begin_cycles=save_begin_max_cycles=save_step_cycles=save_step_max_cycles=0;')
s=s.replace('if(game_state==PLAY&&!save_failed)toast(TX_SAVED);','if(game_state==PLAY&&!save_failed)save_feedback_complete(1);')
s=s.replace('if(pressed&(KEY_B|KEY_START|KEY_SELECT)){game_state=TITLE;return;}','if(pressed&(KEY_B|KEY_START)){game_state=TITLE;return;}')
s=s.replace(' if(pressed&KEY_START)start_game(has_save);\n else if(pressed&KEY_SELECT){if(has_save)game_state=NEW_GAME_CONFIRM;else start_game(0);}',' if(has_save&&(pressed&(KEY_UP|KEY_DOWN)))title_option^=1;\n if(pressed&KEY_START)start_game(has_save);\n else if(pressed&KEY_A){if(has_save&&title_option)game_state=NEW_GAME_CONFIRM;else start_game(has_save);}')
s=s.replace('invuln||guard_invuln||roll_ticks||game_state!=PLAY','invuln||guard_invuln||game_state!=PLAY').replace('&&!guard_invuln&&!roll_ticks&&game_state==PLAY','&&!guard_invuln&&game_state==PLAY')
a=s.index('COLD int try_interaction(void)');s=s[:a]+'''COLD int walk_entry(void){int n=travel_feedback_step((unsigned)room,px,py,(unsigned)keys,(unsigned)transition_lock),allowed=0,old=room,wait_a=TX_RG_LOCKED_A,wait_b=TX_RG_LOCKED_B;const TravelEntry*e;if(n<0)return 0;e=&travel_entries[n];
 if((e->action==TRAVEL_REGION||(e->action==TRAVEL_NORTH&&room==16)||e->action==TRAVEL_FERRY||e->action==TRAVEL_LIFT||e->action==TRAVEL_DIVE)&&!game_region_entry_safe()){travel_feedback_release((unsigned)n);return 0;}
 adventure_save.campaign.chapter_flags=chapter_flags;
 switch(e->action){
 case TRAVEL_CAMPAIGN:allowed=e->target==4?!!(chapter_flags&SAVE4_GROVE_CLEAR):!!(chapter_flags&SAVE4_SKY_CLEAR);break;
 case TRAVEL_REGION:allowed=regional_can_enter(&adventure_save,e->target);wait_a=TX_RG_ENTRY_A;wait_b=TX_RG_ENTRY_B;break;
 case TRAVEL_NORTH:allowed=e->target==16?regional_can_enter(&adventure_save,16):northern_can_enter(&adventure_save,e->target);wait_a=TX_NT_LOCKED_A;wait_b=TX_NT_LOCKED_B;break;
 case TRAVEL_SOUTH:allowed=e->target==22?northern_can_enter(&adventure_save,22):southern_can_enter(&adventure_save,e->target);if(room==32&&e->target==30)allowed&=save5_quest_state(&adventure_save.quests,29)>=SAVE5_QUEST_READY;if(room==36&&e->target==31)allowed&=!!(adventure_save.quests.objectives[24]&4);wait_a=TX_ST_LOCKED_A;wait_b=TX_ST_FERRY_WAIT_B;break;
 case TRAVEL_MAGMA:allowed=e->target==30?southern_can_enter(&adventure_save,30):magma_game_can_enter(e->target);if((room==39&&e->target==40)||(room==40&&e->target==39))allowed&=!!(adventure_save.quests.objectives[35]&2);if(room==44&&e->target==39)allowed&=!!(adventure_save.quests.objectives[32]&4);if(room==45&&e->target==38)allowed&=magma_game_machine_stage==5;wait_a=TX_MG_LOCKED;wait_b=TX_MG_LOCKEDB;break;
 case TRAVEL_UNDERWATER:if(underwater_game_guardian_stage==4){underwater_game_interact();game_attacks_suspend();pressed=0;return 1;}wait_a=TX_UW_RETURN_LATER;wait_b=TX_UW_HOME;break;
 case TRAVEL_TRIAL:enter_room(e->target,e->spawn);dialogue(e->target==14?TX_T_WIND_HINT1:TX_T_STONE_HINT1,e->target==14?TX_T_WIND_HINT2:TX_T_STONE_HINT2,PLAY);game_attacks_suspend();pressed=0;return 1;
 case TRAVEL_RETURN:allowed=return_game_can_enter(e->target);wait_a=TX_RT_LOCKED;wait_b=TX_RT_LOCKEDB;break;
 case TRAVEL_HORIZONS:allowed=horizons_game_can_enter(e->target);wait_a=TX_HZ_LOCKED;wait_b=TX_HZ_HUD_WORK;break;
 case TRAVEL_FERRY:allowed=southern_can_enter(&adventure_save,e->target);wait_a=TX_ST_FERRY_WAIT_A;wait_b=TX_ST_FERRY_WAIT_B;break;
 case TRAVEL_LIFT:allowed=magma_game_can_enter(e->target);wait_a=TX_MG_LIFT_WAIT_A;wait_b=TX_MG_LIFT_WAIT_B;break;
 case TRAVEL_DIVE:allowed=underwater_game_can_enter(e->target);wait_a=TX_UW_PORTAL_WAIT_A;wait_b=TX_UW_PORTAL_WAIT_B;break;
 }
 if(allowed){enter_room(e->target,e->spawn);if(old==30&&room==22){game_region_warp(208,224);travel_feedback_arrive((unsigned)room,px,py);}}
 else dialogue(wait_a,wait_b,PLAY);
 game_attacks_suspend();pressed=0;return 1;
}
'''+s[a:]
s=s.replace('COLD int try_interaction(void){if(','COLD int try_interaction(void){if(game_shop_interact())return 1;if(',1)
a=s.index('void kill_enemy(Enemy*e){');b=s.index('\nvoid update_enemies(',a)
s=s[:a]+'''void kill_enemy(Enemy*e){unsigned slot=(unsigned)(e-enemies),i,xp=0,gold;CreatureU32 before[4];if(slot>=MAX_ENEMIES||(defeated_enemy_mask&(1u<<slot)))return;defeated_enemy_mask|=(unsigned char)(1u<<slot);impact(e->x,e->y);e->hp=0;kills++;
 for(i=0;i<4;i++){unsigned member=adventure_save.roster.party[i];before[i]=member<CREATURE_ROSTER_CAPACITY?adventure_save.roster.instances[member].xp:0;}
 progression_encounter(room,slot);
 for(i=0;i<4;i++){unsigned member=adventure_save.roster.party[i];if(member<CREATURE_ROSTER_CAPACITY&&adventure_save.roster.instances[member].xp>before[i])xp+=(unsigned)(adventure_save.roster.instances[member].xp-before[i]);}
 gold=economy_award_combat(&adventure_save,e->kind==2?10u:6u);game_shop_reward(xp,gold);save_game_ordinary();if(hero_hp_q4<gear_stats.max_hp_q4&&kills%3==0)game_health_heal(16);
}'''+s[b:]
s=s.replace('void update(void){int dx=0,dy=0,return_input=0;frame++;','void update(void){int dx=0,dy=0,return_input=0;frame++;if(locked_notice_room!=room||!near(px,py,locked_notice_x,locked_notice_y,24))locked_notice_room=-1;roll_ticks=roll_cd=roll_dx=roll_dy=0;save_feedback_tick();game_shop_tick();arrival_input_mask&=keys;keys&=~arrival_input_mask;pressed&=~arrival_input_mask;')
s=s.replace(' if(game_state==EVENT_PENDING){event_step();return;}',' if(game_shop_update())return;\n if(game_state==EVENT_PENDING){event_step();return;}',1)
s=s.replace(' if(game_state==SAVE_PENDING){int status;',' if(game_state==SAVE_PENDING){int status;save_feedback_blocked_frames++;')
s=s.replace('has_save=1;}else{save_failed=save_failure_notice=1;toast(TX_C_SAVE_FAILED);}game_state=save_resume_state;return;}','has_save=1;save_feedback_complete(1);}else{save_feedback_complete(0);save_failed=save_failure_notice=1;toast(TX_C_SAVE_FAILED);}game_state=save_resume_state;return;}',1)
s=s.replace('if(save_begin_pending){save_begin_pending=0;if(!progression_save_begin())','if(save_begin_pending){save_begin_pending=0;save5_set_preemptible(0);save_feedback_capture(&adventure_save);if(!progression_save_begin())')
a=s.index(' if(game_state==PAUSE){if(quickparty_menu_input');b=s.index('\n if(game_state==DEAD)',a)
s=s[:a]+''' if(game_state==PAUSE){int input=journal_nav_keys(keys,pressed),nav;if(journal_tab==JOURNAL_ITEMS&&game_shop_confirm&&(input&KEY_B)){game_shop_items_input(input);return;}nav=journal_nav_input(input);if(nav==JOURNAL_CLOSE){game_shop_cancel_items();acknowledge_save_failure();game_state=PLAY;return;}if(nav==JOURNAL_CONSUMED)return;if(game_shop_items_input(input)||quickparty_menu_input(input)||progression_menu_input(input)||gear_menu_input(input)||region_game_menu_input(input)||north_game_menu_input(input)||south_game_menu_input(input)||magma_game_menu_input(input)||underwater_game_menu_input(input)||return_game_menu_input(input)||horizons_game_menu_input(input)||covenants_game_menu_input(input))return;if((input&KEY_A)&&journal_tab==0&&(chapter_flags&SAVE4_ENDING_SEEN)){show_scene(CD_ELDER_FINAL,2,0);append_scene(CD_ENDING_FRIENDS);}return;}'''+s[b:]
s=s.replace('journal_tab=room==1?1:0;game_state=PAUSE;','journal_nav_open();game_state=PAUSE;')
a=s.index(' if((pressed&KEY_SELECT)&&!roll_cd');b=s.index('\n game_attack_update',a)
s=s[:a]+''' /* Select has no field action and no input grants dodge invulnerability. */
 {int speed=advanced_guard_charges?224:gear_stats.speed_q8,diag=advanced_guard_charges?158:gear_stats.diagonal_q8;if(weapon_action.phase==WEAPON_CHARGING){speed=speed*3/4;diag=diag*3/4;}move_player(dx*(dx&&dy?diag:speed),dy*(dx&&dy?diag:speed));}
 if(walk_entry())return;'''+s[b:]
s=s.replace('(pressed&KEY_R)&&!roll_ticks&&','(pressed&KEY_R)&&').replace('if(roll_cd)roll_cd--;','').replace('if(roll_ticks)roll_ticks--;','')
s=s.replace(' else show_scene(CD_CORE_RELEASE,1,SAVE4_SEEN_CORE_RELEASE);',' else show_scene(CD_CORE_RELEASE,1,SAVE4_SEEN_CORE_RELEASE);\n game_shop_begin_boss(cleared==3?0u:cleared==8?1u:2u);')
s=s.replace('if(room==0){if(chapter_flags&SAVE4_GROVE_CLEAR){obj_add(OBJ_PROP,188,120,16,16,1,128,0);if(game_state==PLAY&&near(px,py,196,128,24))obj_add(OBJ_HINT,192,107,8,8,1,999,0);}if(chapter_flags&SAVE4_SKY_CLEAR){obj_add(OBJ_PROP+256,72,120,16,16,1,128,0);if(game_state==PLAY&&near(px,py,80,128,24))obj_add(OBJ_HINT,76,107,8,8,1,999,0);}if(optional_flags&SAVE4_RIDGE_CHIME)','if(room==0){if(optional_flags&SAVE4_RIDGE_CHIME)')
# Rendering: exact visible badge key, retained panes and bounded world clipping.
pos=s.index('COLD void draw_save_failure_notice(void)')
s=s[:pos]+'''int game_save_badge_id(void){if(save_failed)return TX_FB_SAVE_ERROR;if(game_state==EVENT_PENDING)return TX_FB_WORKING;if(game_state==SAVE_PENDING||economy_pending()||save_feedback_badge()==1||(save_requested&&save_feedback_ordinary&&!save5_preflight_active()))return TX_FB_SAVING;return save_feedback_badge()==2?TX_FB_SAVED:0;}
COLD void game_draw_save_badge(void){int id=game_save_badge_id();if(id){int w=ui_texts[id].width+8;box(238-w,29,w,17);text(id,242-w,29,TEAL);}}
'''+s[pos:]
s=s.replace('COLD void render_static(void){screen=','COLD void render_static(void){int display_state=game_display_state();\n#ifndef GAME_HOST_TEST\n unsigned profile_started;\n#endif\n screen=')
s=s.replace('centered(TX_TAGLINE,84,CREAM);box(43,112','centered(TX_TAGLINE,78,CREAM);centered(TX_FB_TITLE_KEYS,96,TEAL);box(43,112')
s=s.replace('centered(has_save?TX_CONTINUE:TX_START,114,GOLD);if(has_save)centered(TX_NEW,130,CREAM);','centered(has_save?TX_CONTINUE:TX_START,114,title_option?CREAM:GOLD);if(has_save)centered(TX_NEW,130,title_option?GOLD:CREAM);')
s=s.replace(' draw_world();if(game_state==PAUSE){','''#ifndef GAME_HOST_TEST
 profile_started=cycle_now();
#endif
 world_mask_active=0;{int left,top,bottom;if(modal_coverage(&left,&top,&bottom)){world_mask_left=left*2;world_mask_right=240-left*2;world_mask_top=top;world_mask_bottom=bottom;world_mask_active=1;}}
 draw_world();world_mask_active=0;
#ifndef GAME_HOST_TEST
 render_world_cycles=cycle_now()-profile_started;profile_started=cycle_now();
#endif
 if(display_state==PAUSE){''')
a=s.index('COLD void render_static(void)');b=s.index('COLD int boss_banner',a);part=s[a:b].replace('if(game_state==DIALOG)','if(display_state==DIALOG)').replace('game_state==PAUSE','display_state==PAUSE')
part=part.replace(' if(game_state==SAVE_PENDING||game_state==EVENT_PENDING){box(37,77,166,34);centered(game_state==EVENT_PENDING?TX_UW_PREPARING:TX_E_SAVING,85,GOLD);}','')
part=part.replace('if(game_state==EVOLVE_CONFIRM)','if(display_state==EVOLVE_CONFIRM)').replace('if(game_state==EVOLVE_ANIM)','if(display_state==EVOLVE_ANIM)')
part=part.replace('centered((chapter_flags&SAVE4_ENDING_SEEN)?TX_C_ENDING_REPLAY:TX_ROLL_CONTROL,127,TEAL);','centered((chapter_flags&SAVE4_ENDING_SEEN)?TX_C_ENDING_REPLAY:TX_FB_BACK,127,TEAL);')
part=part.replace(' draw_save_failure_notice();}',' game_shop_draw_reward();game_draw_save_badge();draw_save_failure_notice();\n#ifndef GAME_HOST_TEST\n render_card_cycles=cycle_now()-profile_started;\n#endif\n}')
s=s[:a]+part+s[b:]
a=s.index(' if(display_state==PAUSE&&journal_tab==1){');b=s.index('\n if(quickparty_open)quickparty_draw();',a)
chain=s[a:b].strip().replace('if(display_state==PAUSE&&','else if(',1).replace('else if(display_state==PAUSE&&','else if(').replace('else if(display_state==PAUSE){','else{')
helper='COLD void draw_journal_panel(void){if(journal_nav_draw()){}\n else if(journal_tab==JOURNAL_ITEMS){game_shop_draw_items();}\n '+chain+'}\n'
s=s[:a]+' if(!game_shop_draw()&&display_state==PAUSE)draw_journal_panel();'+s[b:]
pos=s.index('COLD void render_static(void)');s=s[:pos]+helper+s[pos:]
a=s.index('COLD int reuse_modal_bitmap(');b=s.index('\nvoid render(void)',a)
s=s[:a]+'''COLD int reuse_modal_bitmap(const u32*key){
 int i,other=page^1,same=cache_valid[other];
 int pause_repaint=game_display_state()==PAUSE&&journal_tab!=JOURNAL_GOAL&&cache_fields[page][44]==PAUSE;
 int shop_card=game_display_state()==11||game_state==13;
 int old_shop_card=cache_fields[page][44]==11||cache_fields[page][1]==13;
 int shop_repaint=shop_card&&old_shop_card;
 int overlay=cache_valid[page]&&(game_state==EVOLVE_CONFIRM||(game_state==EVOLVE_ANIM&&cache_fields[page][1]==EVOLVE_ANIM&&progression_selected())||pause_repaint||shop_repaint);
 for(i=0;i<CACHE_FIELDS;i++){
  if(cache_fields[other][i]!=key[i])same=0;
  if(i!=19&&i!=21&&i!=23&&!(pause_repaint&&(i==1||i==10||i==38||i==40||i==44))&&!(shop_repaint&&(i==1||i==40||i==44))&&cache_fields[page][i]!=key[i])overlay=0;
 }
 if(same){REG32(0x040000D4)=other?0x0600A000:0x06000000;REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;for(i=0;i<112;i++)modal_world_row[page][i]=modal_world_row[other][i];return 1;}
 if(!overlay)return 0;
 if(pause_repaint){for(i=0;i<112;i++)screen[153*120+4+i]=modal_world_row[page][i];draw_journal_panel();}
 else if(shop_repaint)game_shop_draw();
 else if(game_state==EVOLVE_ANIM)progression_draw_evolution();
 else progression_draw_confirm();
 game_draw_save_badge();draw_save_failure_notice();return 1;
}'''+s[b:]
s=s.replace('void render(void){game_geometry_sync();','void render(void){render_world_cycles=render_card_cycles=render_actors_cycles=0;game_geometry_sync();')
s=s.replace('game_state==PLAY?covenants_powers_hint():0};','game_state==PLAY?covenants_powers_hint():0,journal_nav_revision,game_save_badge_id(),game_shop_revision,title_option,game_shop_reward_visible(),save_failed,game_display_state()};')
s=s.replace('quickparty_draw();}else render_static();','quickparty_draw();game_draw_save_badge();draw_save_failure_notice();}else render_static();')
s=s.replace(' draw_actors();\n}','''#ifndef GAME_HOST_TEST
 {unsigned profile_started=cycle_now();draw_actors();render_actors_cycles=cycle_now()-profile_started;}
#else
 draw_actors();
#endif
}''',1)
s=s.replace('while(1){u32 started=cycle_now();keys=','while(1){u32 started=cycle_now();save_begin_cycles=save_step_cycles=0;keys=')
s=s.replace('horizons_audio_poll();render_cycles=cycle_now()-started;','horizons_audio_poll();render_profile_serial++;render_profile_world=render_world_cycles;render_profile_card=render_card_cycles;render_profile_actors=render_actors_cycles;render_profile_save_begin=save_begin_cycles;render_profile_save_step=save_step_cycles;render_profile_state=(unsigned)game_state;render_profile_room=(unsigned)room;render_cycles=cycle_now()-started;render_profile_frame=(unsigned)frame;render_profile_serial++;')
p.write_text(s)
# Scene/animation integrations and removal of obsolete travel notice art.
p=ROOT/'src/covenants_engine.inc';s=p.read_text().replace('static COLD void covenants_enemy_generation(unsigned i){','static COLD void covenants_enemy_generation(unsigned i){\n defeated_enemy_mask&=(unsigned char)~(1u<<i);');p.write_text(s)
p=ROOT/'src/world_drawing.inc';s=p.read_text().replace(' trials_draw_background(room,camera_x,camera_y);',' trials_draw_background(room,camera_x,camera_y);\n feedback_world_draw((unsigned)room,camera_x,camera_y);');p.write_text(s)
p=ROOT/'src/region_game.c';s=p.read_text().replace('roll_serial,last_garden_roll','garden_sensor_previous').replace('static int was_rolling;','').replace('field_pool_mask=0;was_rolling=0;roll_serial=0;last_garden_roll=~0u;','field_pool_mask=0;garden_sensor_previous=~0u;').replace('  if(roll_ticks&&!was_rolling)roll_serial++;\n  was_rolling=roll_ticks!=0;\n','').replace('if(roll_ticks&&sensor>=0&&roll_serial!=last_garden_roll){\n    last_garden_roll=roll_serial;event_dirty=0;','if(sensor>=0&&(unsigned)sensor!=garden_sensor_previous){\n    garden_sensor_previous=(unsigned)sensor;event_dirty=0;').replace(' if(transition_lock||game_state!=PLAY)return;',' if(sensor<0)garden_sensor_previous=~0u;\n if(transition_lock||game_state!=PLAY)return;',1).replace('region_actor(REGION_SPR_SIGN_WORKSHOP,168,248);','');p.write_text(s)
p=ROOT/'src/region_game.h';p.write_text(p.read_text().replace('real roll sensors','ordered walking-pad sensors'))
p=ROOT/'src/north_game.c';s=p.read_text().replace('if(northern_can_enter(&adventure_save,22))north_actor(NORTH_SPR_FERRY_SIGN,400,280);','').replace('north_actor(NORTH_SPR_FERRY_SIGN,240,264);','');p.write_text(s)
p=ROOT/'src/trials.c';s=p.read_text().replace('else if(room==4||room==9){int x=room==4?204:208,y=room==4?64:120;actor(5,x,y);hint(x,y,22);}','else if(room==4||room==9){/* feedback_world draws the walking entries. */}');p.write_text(s)
p=ROOT/'src/return_game_draw.inc';s=p.read_text()
for call in ['old_notice(176,112,PAL_PINE3);','old_notice(104,112,PAL_GOLD1);','old_notice(424,144,PAL_GOLD1);','old_notice(264,284,PAL_WATER2);','old_notice(416,144,PAL_GOLD1);','old_notice(432,256,PAL_WATER2);']:s=s.replace(call,'')
s=s.replace('ra(RETURN_SPR_GUIDE,done(49)?176:128,112);ra(RETURN_SPR_NOTICE,432,256);','ra(RETURN_SPR_GUIDE,done(49)?176:128,112);').replace('ra(RETURN_SPR_NOTICE,120,104);ra(RETURN_SPR_NOTICE,208,112);','ra(RETURN_SPR_NOTICE,120,104);');p.write_text(s)
p=ROOT/'src/horizons_game_draw.inc';s=p.read_text().replace('else if(room==61){notice(120,32,2);arrow(120,52,0,-12,PAL_WATER2);}','');p.write_text(s)
print('Restored engine/world integration through approved F changes')
