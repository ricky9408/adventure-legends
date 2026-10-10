/* A repeat invitation confirmation is scoped to this exact facing cone.
 * Leaving it clears only the prompt, never the solved encounter or its token. */
static void clear_departed_repeat_prompt(void){if(invite_confirm==1&&!((repeat_active==17&&room==55&&close(208,80))||(repeat_active==18&&room==58&&close(400,240))))invite_confirm=0;}
static void reset_point(int*x,int*y){int big=room==54||room==56||room==57||room==58;*x=big?40:24;*y=big?276:132;}
static COLD int door(unsigned a,unsigned s){if(event_count){transition_area=a;transition_spawn=s;transition_ready=2;return 1;}if(return_game_is_room(a)&&!return_can_enter(&adventure_save,a)){say(TX_RT_LOCKED,TX_RT_LOCKEDB);return 1;}persist();enter_room(a,s);return 1;}
static COLD int reset_interact(void){int x,y,xx=120,yy=140;reset_point(&x,&y);if(!close(x,y))return 0;if(!reset_confirm){reset_confirm=1;toast(TX_RT_RESET_CONFIRM);return 1;}return_game_spawn((unsigned)room,0,&xx,&yy);return_game_reset();game_region_warp(xx,yy);toast(TX_RT_RESET_DONE);return 1;}
int return_game_input(unsigned pressed,unsigned held){(void)held;if(game_state!=PLAY)return 0;clear_departed_repeat_prompt();if(invite_confirm>=46){int here=(invite_confirm==47&&room==16&&close(368,152))||(invite_confirm==49&&room==30&&close(448,192));if(!here)invite_confirm=0;else if(pressed&B){invite_confirm=0;toast(TX_RT_WAIT);return 1;}}if(!return_game_is_room((unsigned)room))return 0;if(pressed&B){reset_confirm=0;if(invite_confirm){invite_confirm=0;toast(TX_RT_WAIT);return 1;}}return 0;}
/* Separate explicit tables/notices keep every original NPC, shop and quest
 * reachable. Parent dispatches only for these selected old rooms. */
COLD int return_game_old_interact(void){if(game_state!=PLAY||!done(40))return 0;
 if(room==46&&close(200,272)){if(!done(46))objective(46,1);say(TX_RT_ARCHIVE_A,TX_RT_ARCHIVE_B);return 1;}
 if(room==0){
  if(close(152,112)){if(!done(46)){if(adventure_save.quests.objectives[46]&1)return report(46,2,TX_RT_VILLAGE_A,TX_RT_VILLAGE_B);say(TX_RT_ARCHIVE_A,TX_RT_ARCHIVE_B);return 1;}if(!done(51)&&return_quest_available(&adventure_save,51)&&(adventure_save.quests.objectives[51]&7)==7)return report(51,8,TX_RT_VILLAGE_DONE,TX_RT_VILLAGE_DONE_B);say(done(51)?TX_RT_VILLAGE_DONE:TX_RT_VILLAGE_A,done(51)?TX_RT_VILLAGE_DONE_B:TX_RT_VILLAGE_B);return 1;}
  if(close(176,112)&&!road_region_managed((unsigned)room,54))return door(54,0);
  if(close(104,112)&&!road_region_managed((unsigned)room,60))return door(60,0);
 }
 if(!done(46))return 0;
 if(room==16){
  if(close(368,152)){if(!done(47)&&(adventure_save.quests.objectives[47]&3)==3&&state(47)!=2){if(invite_confirm!=47){invite_confirm=47;toast(TX_RT_INVITE);return 1;}invite_confirm=0;}if(!done(47))return report(47,!(adventure_save.quests.objectives[47]&1)?1:(adventure_save.quests.objectives[47]&2)?4:0,TX_RT_SMITH_A,TX_RT_SMITH_B);say(TX_RT_SMITH_DONE,TX_RT_OLD_ACCESS);return 1;}
  if(close(424,144)&&!road_region_managed((unsigned)room,55))return door(55,0);
  if(close(112,144)){if(state(50)==2)return report(50,0,TX_RT_MIRA_DONE,TX_RT_OLD_ACCESS);if(!done(50)&&(adventure_save.quests.objectives[50]&3)==3)return report(50,4,TX_RT_MIRA_DONE,TX_RT_OLD_ACCESS);if(state(52)==2)return report(52,0,TX_RT_MIRA_DONE,TX_RT_OLD_ACCESS);if(!done(52)&&(adventure_save.quests.objectives[52]&3)==3)return report(52,4,TX_RT_MIRA_DONE,TX_RT_OLD_ACCESS);say(done(50)?TX_RT_MIRA_DONE:TX_RT_MIRA_A,TX_RT_OLD_ACCESS);return 1;}
 }
 if(room==17&&close(264,284)&&!road_region_managed((unsigned)room,56))return door(56,0);
 if(room==22){if(close(416,144)&&!road_region_managed((unsigned)room,57))return door(57,0);if(close(192,192)){if((adventure_save.quests.objectives[48]&3)==3||state(48)==2)return report(48,4,TX_RT_EDDA_DONE,TX_RT_OLD_ACCESS);offer(48);say(TX_RT_EDDA_A,TX_RT_BRAKE);return 1;}if(close(352,176))return report(52,1,TX_RT_TOVE_A,TX_RT_HOME);}
 if(room==30){if(close(432,256)&&!road_region_managed((unsigned)room,58))return door(58,0);if(close(448,192)){if(!done(49)&&(adventure_save.quests.objectives[49]&3)==3&&state(49)!=2){if(invite_confirm!=49){invite_confirm=49;toast(TX_RT_INVITE);return 1;}invite_confirm=0;}if(!done(49))return report(49,(adventure_save.quests.objectives[49]&3)==3?4:0,TX_RT_CURATOR_A,TX_RT_HOME);if(state(53)==2)return report(53,0,TX_RT_SURVEY_DONE,TX_RT_OLD_ACCESS);offer(53);say(done(53)?TX_RT_SURVEY_DONE:TX_RT_CURATOR_DONE,TX_RT_OLD_ACCESS);return 1;}}
 if((room==18&&close(208,112))||(room==20&&close(208,112))){say(done(47)?TX_RT_SMITH_DONE:TX_RT_SMITH_A,TX_RT_OLD_ACCESS);return 1;}
 if(room==38&&close(208,272)&&done(52)){say(TX_RT_RESSA_DONE,TX_RT_OLD_ACCESS);return 1;}
 return 0;
}
COLD int return_game_interact(void){unsigned i;if(!return_game_is_room((unsigned)room)||game_state!=PLAY||event_count)return 0;clear_departed_repeat_prompt();if(reset_interact())return 1;
 if(return_game_trial.index<13)return trial_interact();
 /* Multiple nearby lessons share no invisible activation; exact lectern wins
  * only when the selected predecessor matches that visibly named lesson. */
 for(i=0;i<13;i++)if(trials[i].area==room&&close(trials[i].lectern[0],trials[i].lectern[1]))return begin_trial(i);
 if(room==54){if(close(72,256)){simple(RETURN_REQUEST_ANCHOR,54,0,0,0);return 1;}if(close(240,240)){if(setting[0]&&setting[1]){objective(53,1);toast(TX_RT_RECORD);}else say(TX_RT_HEARTH,TX_RT_USE_COMMAND);return 1;}if(close(240,72)){say(TX_RT_ROOT,TX_RT_HOME);return 1;}if(close(272,240)){say(TX_RT_HEARTH,TX_RT_HOME);return 1;}}
 else if(room==55){
  if(close(40,116)){simple(RETURN_REQUEST_ANCHOR,55,0,0,0);return 1;}
  if(repeat_active){if(close(64,112)||close(176,112)){repeat_setting^=close(64,112)?1:2;repeat_stage=0;changed();toast(TX_RT_ADJUSTED);return 1;}if(close(208,80))return invite_repeat();return 0;}
  if(close(64,112)||close(176,112)){unsigned n=close(64,112)?0:1;if(!set_mechanism(n,setting[n]^1))return 1;if(setting[0]&&setting[1])objective(47,2);changed();toast(TX_RT_ADJUSTED);return 1;}
  if(close(208,80)){if(done(47))return begin_repeat(17);say(TX_RT_SMITH_A,TX_RT_SMITH_B);return 1;}
 }
 else if(room==56){if(close(288,256)){setting[0]^=1;changed();toast(TX_RT_ADJUSTED);return 1;}if(close(432,256)){objective(53,2);toast(TX_RT_RECORD);return 1;}if(close(240,96)||close(240,208)){say(TX_RT_FLOAT,TX_RT_WALK);return 1;}}
 else if(room==57){if(close(352,272)){setting[0]^=1;changed();toast(TX_RT_BRAKE);return 1;}if(close(304,272)){setting[1]^=1;changed();toast(TX_RT_ADJUSTED);return 1;}if(close(432,272)){objective(53,4);toast(TX_RT_RECORD);return 1;}if(close(320,208)){say(TX_RT_HINGE,TX_RT_WRONG_SIDE);return 1;}if(close(400,240)){say(TX_RT_BRAKE,TX_RT_USE_COMMAND);return 1;}if(close(304,240)){say(TX_RT_TOVE_A,TX_RT_MANUAL);return 1;}}
 else if(room==58){
  if(repeat_active){if(close(368,272)){repeat_setting^=1;repeat_stage=0;changed();toast(TX_RT_ADJUSTED);return 1;}if(close(400,240))return invite_repeat();}
  if(close(80,80)||close(160,80)){unsigned n=close(80,80)?0:1;setting[n]^=1;if(setting[0]&&setting[1])objective(49,1);changed();toast(TX_RT_ADJUSTED);return 1;}
  if(close(128,144)){setting[2]^=1;if(setting[2])objective(49,2);changed();toast(TX_RT_ADJUSTED);return 1;}
  if(close(400,240)){if(done(49))return begin_repeat(18);say(TX_RT_CURATOR_A,TX_RT_HOME);return 1;}
  if(close(432,256)&&!road_region_managed((unsigned)room,59))return door(59,0);
  if(close(240,240)){objective(53,8);toast(TX_RT_RECORD);return 1;}
 }
 else if(room==59){if(close(120,104)){setting[0]^=1;changed();toast(TX_RT_ADJUSTED);return 1;}if(close(64,56)||close(192,56)){say(TX_RT_FLOAT,TX_RT_HOME);return 1;}}
 else if(room==60){if(close(120,104)){objective(51,1);say(TX_RT_PHASE,TX_RT_PHASE_SWAP);return 1;}if(close(208,112)&&!road_region_managed((unsigned)room,61))return door(61,0);}
 else if(room==61){if(close(64,56)||close(176,56)){say(TX_RT_HINGE,TX_RT_FLOAT);return 1;}}
 return 0;
}
COLD void return_game_tick(void){int x,y;if(!return_game_is_room((unsigned)room)||game_state!=PLAY)return;clear_departed_repeat_prompt();ambient_clock++;reset_point(&x,&y);if(reset_confirm&&!close(x,y))reset_confirm=0;if(event_count)return;
 if(return_game_trial.index<13)trial_walk();
 else if(repeat_active){if(!repeat_participant()){cancel_proof();changed();}else if(repeat_stage==1&&near(px,py,room==55?208:400,room==55?112:272,9)){repeat_stage=2;changed();toast(TX_RT_TRACE);}}
 if(transition_lock)return;
 {const ReturnArtRoom*r=&return_art_rooms[room-54];if(!road_region_managed((unsigned)room,parents[room-54])&&py>=r->height-16&&ab(px-r->width/2)<=16&&(keys&DOWN)){door(parents[room-54],parent_spawns[room-54]);return;}}
}
int return_game_name(void){return return_game_is_room((unsigned)room)?room_names[room-54]:TX_RT_JOURNAL;}
int return_game_quest_text(void){if(!done(46))return TX_RT_HUD_HOME;if(!(adventure_save.quests.region_flags[5]&1))return TX_RT_HUD_COMMON;if(!done(48)||!done(50))return TX_RT_HUD_ARMS;if(!done(51))return(adventure_save.quests.objectives[51]&7)==7?TX_RT_HUD_RETURN:TX_RT_HUD_MAP;return TX_RT_HUD_DONE;}
