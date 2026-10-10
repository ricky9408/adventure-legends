typedef struct {unsigned char area,to,spawn,key;short x,y;} DoorDef;
static const DoorDef doors[]={
 {62,61,1,DOWN,240,304},{62,63,0,RIGHT,464,160},{62,66,1,LEFT,16,160},{62,64,1,UP,240,16},
 {63,62,1,LEFT,8,128},{63,65,0,RIGHT,472,128},{63,64,0,UP,208,16},{63,67,0,UP,400,16},
 {64,63,2,DOWN,120,150},{64,62,3,LEFT,8,112},
 {65,63,1,LEFT,16,160},{65,66,0,RIGHT,464,160},{65,67,1,UP,240,16},
 {66,65,1,DOWN,120,304},{66,62,2,UP,48,8},{66,69,0,RIGHT,224,272},
 {67,63,3,DOWN,80,288},{67,65,2,DOWN,400,288},{67,68,0,UP,240,16},{67,69,1,LEFT,16,144},
 {68,67,2,DOWN,120,150},{69,66,2,DOWN,120,150},{69,67,3,RIGHT,224,112}
};
static COLD void reset_point(int*x,int*y){*x=24;*y=horizons_art_rooms[room-62].height-28;}
static COLD int door(unsigned a,unsigned s){if(event_count)return 1;if((a==69&&room==67)||(a==67&&room==69)){if(!done(57)){say(TX_HZ_LOCKED_FINAL,TX_HZ_HUD_REPORT);return 1;}}
 if(horizons_game_is_room(a)&&!spawn_allowed(a,s)){say(a==67||a==68?TX_HZ_LOCKED_FINAL:TX_HZ_LOCKED,TX_HZ_HUD_WORK);return 1;}persist();enter_room(a,s);return 1;}
static COLD void clear_prompt(void){if(invite_confirm&&(!horizons_game_is_room((unsigned)room)||invite_confirm>12||!close(sources[invite_confirm-1].invite[0],sources[invite_confirm-1].invite[1])))invite_confirm=0;}
COLD int horizons_game_input(unsigned pressed,unsigned held){(void)held;if(game_state!=PLAY)return 0;clear_prompt();if(!horizons_game_is_room((unsigned)room))return 0;if(pressed&B){if(reset_confirm||invite_confirm){reset_confirm=invite_confirm=0;toast(TX_HZ_WAIT);return 1;}}return 0;}
static COLD int reset_interact(void){int x,y,xx=120,yy=140;reset_point(&x,&y);if(!close(x,y))return 0;if(!reset_confirm){reset_confirm=1;toast(TX_HZ_RESET_ASK);return 1;}horizons_game_spawn((unsigned)room,0,&xx,&yy);horizons_game_reset();game_region_warp(xx,yy);toast(TX_HZ_RESET_DONE);return 1;}
COLD int horizons_game_old_interact(void){if(game_state!=PLAY||!done(51)||event_count)return 0;
 if(room==60&&close(64,112)){if(!done(54)){objective(54,1);say(TX_HZ_INVITATION_A,TX_HZ_INVITATION_B);}else if(state(59)==2){claim(59);}else if((bits(59)&7)==7){objective(59,8);toast(TX_HZ_RECORD);}else say(TX_HZ_CLUE59A,TX_HZ_CLUE59B);return 1;}
 if(room==61&&!road_region_managed(61,62)&&close(120,32))return door(62,0);
 return 0;
}
static COLD int main_report(unsigned q,int a,int b){if(state(q)==2)claim(q);else {if(!state(q))offer(q);say(a,b);}return 1;}
COLD int horizons_game_interact(void){unsigned i;CreatureInstance*c=active();if(!horizons_game_is_room((unsigned)room)||game_state!=PLAY||event_count)return 0;clear_prompt();if(reset_interact())return 1;
 for(i=0;i<sizeof doors/sizeof doors[0];i++)if(doors[i].area==room&&!road_region_managed((unsigned)room,doors[i].to)&&close(doors[i].x,doors[i].y))return door(doors[i].to,doors[i].spawn);
 if(proof.mode){unsigned j=proof.index;if(proof.mode==MODE_INITIAL||proof.mode==MODE_REPEAT){const SourceDef*d=&sources[j];if(close(d->invite[0],d->invite[1]))return begin_source(j);if(close(d->manual[0],d->manual[1]))return attempt_manual(0);if((j==7&&close(80,144))||(j==8&&close(192,32)))return attempt_manual(1);}else {const TrialDef*d=work_trial();if(close(d->manual[0],d->manual[1]))return attempt_manual(0);if(close(d->lectern[0],d->lectern[1])){say(d->clue[0],d->clue[1]);return 1;}}}
 else {
  /* Explicit trial and evolved exhibit share only their own named lectern. */
  for(i=0;i<4;i++)if(trials[i].area==room&&close(trials[i].lectern[0],trials[i].lectern[1])&&c&&(c->form_id==trials[i].form||c->form_id==trials[i].form+1u)){if(begin_practice(i))return 1;return begin_trial(i);}
  if(room==63&&close(336,128)&&begin_practice(0))return 1;
  for(i=0;i<12;i++)if(sources[i].area==room&&close(sources[i].invite[0],sources[i].invite[1])){if(i==0&&state(54)==2)return main_report(54,TX_HZ_FAIR_A,TX_HZ_FAIR_B);if(i==1&&state(55)==2)return main_report(55,TX_HZ_STAGE_A,TX_HZ_STAGE_B);return begin_source(i);}
 }
 if(room==62){
  if(close(88,80)){say(TX_HZ_PROMISE_FAIR_A,TX_HZ_PROMISE_FAIR_B);return 1;}
  if(close(384,80)){say(TX_HZ_PROMISE_YARD_A,TX_HZ_PROMISE_YARD_B);return 1;}
  if(close(72,256)){simple(HORIZONS_REQUEST_ANCHOR,62,0,0,0);return 1;}
  if(close(208,208)||close(272,208)){setting[0]^=close(208,208)?1:2;changed();toast(TX_HZ_ADJUST);return 1;}
  if(close(120,208)){if(!(bits(54)&1)){say(TX_HZ_CLUE54A,TX_HZ_INVITATION_B);return 1;}if(state(57)==2)return main_report(57,TX_HZ_CLOSE_A,TX_HZ_CLOSE_B);if(state(54)==2)return main_report(54,TX_HZ_FAIR_A,TX_HZ_FAIR_B);say(done(57)?TX_HZ_PROMISE_HOME_A:TX_HZ_FAIR_A,done(57)?TX_HZ_PROMISE_HOME_B:TX_HZ_FAIR_B);return 1;}
 }
 else if(room==63){if(close(80,96)||close(352,96)){if(setting[3])return wrong(TX_HZ_CLEAR);setting[close(80,96)?1:2]^=1;changed();toast(TX_HZ_ADJUST);return 1;}if(close(136,80)){objective(55,1);objective(59,1);say(TX_HZ_YARD_A,TX_HZ_YARD_B);return 1;}}
 else if(room==64){if(close(32,96)){say(TX_HZ_PROMISE_STAGE_A,TX_HZ_PROMISE_STAGE_B);return 1;}if(close(56,104)||close(120,104)||close(176,104)){i=close(56,104)?0:close(120,104)?1:2;setting[0]^=1u<<i;setting[2]&=~(1u<<i);changed();toast(TX_HZ_ADJUST);return 1;}if(close(120,40)){say(TX_HZ_STAGE_A,TX_HZ_STAGE_B);return 1;}if(!proof.mode&&close(176,120)){setting[8]^=1;if(setting[8])objective(58,1);changed();toast(TX_HZ_DISCOVERY);return 1;}}
 else if(room==65){
  if(close(80,256)){simple(HORIZONS_REQUEST_ANCHOR,65,0,0,0);return 1;}
  if(close(96,176)){objective(56,1);say(TX_HZ_COURT_A,TX_HZ_COURT_B);return 1;}
  if(close(336,208)){setting[0]=(setting[0]+1)%3;setting[1]=0;changed();toast(TX_HZ_ADJUST);return 1;}
  if(close(352,272)){if(state(56)==2)return main_report(56,TX_HZ_COURT_A,TX_HZ_COURT_B);if(state(58)==2)return main_report(58,TX_HZ_DISCOVERY,TX_HZ_CLOSE_B);if((bits(58)&3)==3){objective(58,4);toast(TX_HZ_RECORD);return 1;}say(TX_HZ_GALLERY_A,TX_HZ_GALLERY_B);return 1;}
 }
 else if(room==66){if(close(48,96)){say(TX_HZ_PROMISE_PRINT_A,TX_HZ_PROMISE_PRINT_B);return 1;}if(close(176,80)){objective(59,2);say(TX_HZ_GALLERY_A,TX_HZ_GALLERY_B);return 1;}if(close(48,288)){say(TX_HZ_SOURCE9A,TX_HZ_SOURCE9B);return 1;}}
 else if(room==67){if(close(368,176)){say(TX_HZ_PROMISE_WAX_A,TX_HZ_PROMISE_WAX_B);return 1;}if(close(352,224)){setting[1]^=1;changed();toast(TX_HZ_ADJUST);return 1;}if(close(352,256)){setting[2]^=1;changed();toast(TX_HZ_ADJUST);return 1;}if(close(112,256)){say(TX_HZ_TRANSFER_A,TX_HZ_TRANSFER_B);return 1;}if(close(288,240)){say(TX_HZ_WAX_A,TX_HZ_WAX_B);return 1;}}
 else if(room==68){if(close(72,136)&&(bits(57)&4)){say(TX_HZ_PROMISE_SHOW_A,TX_HZ_PROMISE_SHOW_B);return 1;}if(close(120,96)){if(bits(57)&4){performance_ticks=180;game_horizons_performance_start();toast(TX_HZ_NO_REWARD);}else say(TX_HZ_SHOW_A,TX_HZ_SHOW_B);return 1;}}
 else if(room==69){if(close(40,80)){objective(59,4);say(TX_HZ_SOURCE9A,TX_HZ_SOURCE9B);return 1;}if(close(48,104)||close(80,104)){setting[8]^=close(48,104)?1:2;if(setting[8]==3)objective(58,2);changed();toast(TX_HZ_ADJUST);return 1;}}
 return 0;
}
COLD void horizons_game_tick(void){unsigned i;int x,y;if(!horizons_game_is_room((unsigned)room)||game_state!=PLAY)return;clear_prompt();ambient++;reset_point(&x,&y);if(reset_confirm&&!close(x,y))reset_confirm=0;if(event_count)return;
 if(performance_ticks)performance_ticks--;
 horizons_audio_tick();
 if(room==63&&setting[3]){int goal=192+(setting[3]==2?setting[0]:setting[4])*32,next=carriage_x+(carriage_x<goal?2:-2);if(carriage_x==goal){if(setting[3]==1)setting[0]=setting[4];setting[3]=0;}else if(!load_clear(next)){if(setting[3]==1){setting[3]=2;toast(TX_HZ_CLEAR);}}else{carriage_x=next;if(carriage_x==goal){if(setting[3]==1)setting[0]=setting[4];setting[3]=0;toast(TX_HZ_TRACE);}horizons_powers_geometry_changed();return_powers_geometry_changed();changed();}}
 attempt_walk();if(event_count)return;
 if(!proof.mode){if(room==62&&(bits(54)&1)&&setting[0]==3&&near(px,py,240,240,9)&&!(bits(54)&2))objective(54,2);if(room==63&&(bits(55)&1)&&!setting[3]&&setting[0]==2&&setting[1]==1&&setting[2]==0&&near(px,py,256,128,9)&&!(bits(55)&2))objective(55,2);}
 if(event_count||transition_lock)return;
 for(i=0;i<sizeof doors/sizeof doors[0];i++)if(doors[i].area==room&&!road_region_managed((unsigned)room,doors[i].to)&&(keys&doors[i].key)&&near(px,py,doors[i].x,doors[i].y,10)){door(doors[i].to,doors[i].spawn);return;}
}
COLD int horizons_game_name(void){return horizons_game_is_room((unsigned)room)?room_names[room-62]:TX_HZ_JOURNAL;}
COLD int horizons_game_quest_text(void){if(!done(54))return TX_HZ_HUD_FAIR;if(!done(55)||!done(56))return TX_HZ_HUD_WORK;if(state(57)==2)return TX_HZ_HUD_REPORT;if(!done(57))return TX_HZ_HUD_FINAL;return TX_HZ_HUD_DONE;}
