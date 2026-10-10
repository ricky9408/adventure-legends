typedef struct {unsigned char area,to,spawn,key;short x,y;} CovenantDoor;
static const CovenantDoor doors[]={
 {70,62,5,DOWN,240,304},{70,71,0,RIGHT,464,160},{71,70,1,LEFT,8,272},
 {71,72,0,RIGHT,224,32},{72,71,1,LEFT,8,128},{72,73,0,RIGHT,464,128},
 {73,72,1,RIGHT,224,128},{73,70,2,LEFT,8,128},{70,73,1,LEFT,16,160},
 {70,74,0,UP,240,16},{74,70,3,DOWN,240,304},{74,75,0,RIGHT,464,160},
 {75,74,1,LEFT,8,272},{75,76,0,RIGHT,224,32},{76,75,1,LEFT,8,128},
 {76,77,0,RIGHT,464,128},{77,76,1,RIGHT,224,128},{77,74,2,LEFT,8,128},
 {74,77,1,LEFT,16,160}
};
static COLD void new_attempt(void){
 invalidate_cast();next_generation(&attempt);invite_confirm=porch_confirm=0;
 setting[10]=setting[11]=0;practice_mode=0;
}
static COLD int door(unsigned a,unsigned s){
 if(event_count)return 1;
 if(covenants_game_is_room(a)&&!spawn_allowed(a,s)){say(TX_CV_LOCKED,TX_CV_CLUE61B);return 1;}
 persist();enter_room((int)a,(int)s);return 1;
}
static COLD void clear_prompts(void){
 unsigned i=(unsigned)room-70;
 if(invite_confirm&&(i>=8||invite_confirm!=i+1||!close(invitations[i][0],invitations[i][1])))invite_confirm=0;
 if(reset_confirm&&(i>=8||!close(resets[i][0],resets[i][1])))reset_confirm=0;
 if(porch_confirm&&(room!=70||!close(128,272)))porch_confirm=0;
}
COLD int covenants_game_input(unsigned pressed,unsigned held){
 (void)held;if(game_state!=PLAY)return 0;clear_prompts();
 if((pressed&B)&&(reset_confirm||invite_confirm||porch_confirm)){
  reset_confirm=invite_confirm=porch_confirm=0;toast(TX_CV_STILL_OPEN);return 1;
 }
 return 0;
}
static COLD int invitation(unsigned i){
 if(owned(i)){say(after_lines[i][0],after_lines[i][1]);return 1;}
 if(!fulfilled(i)){say(trial_clues[i][0],trial_clues[i][1]);return 1;}
 if(invite_confirm!=i+1){new_attempt();invite_confirm=(unsigned char)(i+1);say(invite_lines[i][0],invite_lines[i][1]);toast(TX_CV_INVITE_ASK);return 1;}
 invite_confirm=0;
 simple(COVENANTS_REQUEST_UNIQUE_INVITE,(unsigned)room,0,0,i+1);return 1;
}
static COLD int practice_begin(unsigned i){
 CreatureInstance*c=active();
 if(!c||c->form_id!=121+i||!owned(i)||!fulfilled(i)){say(TX_CV_PRACTICE_NEED,TX_CV_INVITE_LATER);return 1;}
 if(progression_command()!=practices[i].command){toast(TX_CV_CHOOSE_POWER);return 1;}
 new_attempt();practice_mode=1;toast(TX_CV_PRACTICE);changed();return 1;
}
static COLD int report(unsigned q,int a,int b){
 if(state(q)==SAVE5_QUEST_READY)claim(q);else{if(!state(q))offer(q);say(a,b);}return 1;
}
static COLD int resident_dialogue(unsigned i,unsigned j){
 static const int lines[8][2]={{TX_CV_STEWARD_A,TX_CV_STEWARD_B},{TX_CV_GROWER_A,TX_CV_GROWER_B},
 {TX_CV_KILN_KEEPER_A,TX_CV_KILN_KEEPER_B},{TX_CV_WALKER_A,TX_CV_WALKER_B},
 {TX_CV_REPAIRER_A,TX_CV_REPAIRER_B},{TX_CV_SEED_KEEPER_A,TX_CV_SEED_KEEPER_B},
 {TX_CV_FERRY_KEEPER_A,TX_CV_FERRY_KEEPER_B},{TX_CV_WATCHER_A,TX_CV_WATCHER_B}};
 if(i==0&&j==0){
  if(!done(60)){
   if(state(60)==SAVE5_QUEST_READY)return report(60,TX_CV_WELCOME_A,TX_CV_WELCOME_B);
   setting[5]|=1;say(TX_CV_WELCOME_A,TX_CV_WELCOME_B);return 1;
  }
  if(!done(61))return report(61,TX_CV_LOWER_REPORT_A,TX_CV_LOWER_REPORT_B);
  if(done(62)&&!done(63)){
   if(!state(63)){offer(63);say(TX_CV_PORCH_A,TX_CV_PORCH_B);return 1;}
   if(!(bits(63)&1)){
    if(!porch_confirm){new_attempt();porch_confirm=1;say(TX_CV_PORCH_ASK_A,TX_CV_PORCH_ASK_B);return 1;}
    porch_confirm=0;objective(63,1);say(TX_CV_PORCH_YES_A,TX_CV_PORCH_YES_B);return 1;
   }
   say(TX_CV_CLUE63A,TX_CV_CLUE63B);return 1;
  }
 }
 if(i==0&&j==1&&!done(60)){setting[5]|=2;say(TX_CV_STEWARD_A,TX_CV_STEWARD_B);return 1;}
 if(i==4&&j==0&&!done(62))return report(62,TX_CV_UPPER_REPORT_A,TX_CV_UPPER_REPORT_B);
 if(!fulfilled(i)&&i==1&&j==0&&setting[0]==3&&moving_x==120&&!moving_state&&setting[3]==3){npc_stage=1;toast(TX_CV_WAIT);return 1;}
 if(!fulfilled(i)&&i==3&&j==0&&setting[0]==3){npc_stage=1;movement_ticks=0;toast(TX_CV_WAIT);return 1;}
 if(!fulfilled(i)&&i==5&&j==0&&setting[0]==3&&shade_geometry()){npc_stage=1;toast(TX_CV_WAIT);return 1;}
 if(!fulfilled(i)&&i==6&&j==0&&(setting[0]&1)&&npc_stage==0){npc_stage=1;toast(TX_CV_WAIT);return 1;}
 say(fulfilled(i)?after_lines[i][0]:lines[i][0],fulfilled(i)?after_lines[i][1]:lines[i][1]);return 1;
}
static COLD int manual_work(unsigned i,unsigned j){
 if(fulfilled(i))return practice_begin(i);
 if(i==0){
  if(!done(60)){
   if(j==0&&setting[5]==3){objective(60,4);say(TX_CV_WELCOME_A,TX_CV_WELCOME_B);}
   else say(TX_CV_CLUE60A,TX_CV_WELCOME_A);
  }else setting[1+j]=(setting[1+j]+1)%3;
 }else if(i==1){
  if(!(setting[0]&1))return wrong(TX_CV_WRONG);
  if(moving_state)return wrong(TX_CV_CLEAR);
  setting[1]=(setting[1]+1)%3;setting[3]=0;
  begin_motion(88+setting[1]*32);
 }else if(i==2){setting[1]^=1;if(!setting[1]){movement_ticks=0;setting[3]=0;}}
 else if(i==3){say(TX_CV_WALKER_A,TX_CV_TRIAL4B);return 1;}
 else if(i==4){
  if(!(setting[0]&1))return wrong(TX_CV_WRONG);
  setting[1+j]=(setting[1+j]+1)%3;setting[0]&=1;setting[3]=0;
 }else if(i==5){setting[1]=(setting[1]+1)%3;setting[0]&=1;npc_stage=0;}
 else if(i==6){if(!(setting[0]&4)||moving_x!=272||moving_state)return wrong(TX_CV_WAIT);setting[1]=1;}
 else if(i==7){
  if(!setting[1]){setting[1]=1;toast(TX_CV_STILL_OPEN);changed();return 1;}
  if(setting[0]!=7)return wrong(TX_CV_WRONG);
  if(game_covenants_enemies_alive())return wrong(TX_CV_WAIT);
  if(setting[4]<3){
   if(!game_covenants_spawn_wave(setting[4]+1))return wrong(TX_CV_CLEAR);
   setting[4]++;toast(TX_CV_WAVE_ASK);
  }else{complete_covenant();say(TX_CV_AFTER8A,TX_CV_AFTER8B);return 1;}
 }
 changed();toast(TX_CV_ADJUST);return 1;
}
static COLD int inspect_work(void){
 if(room==70){
  if(close(144,240)){if(setting[0]==31&&setting[1]==2)setting[3]|=1;else {wrong(TX_CV_FIT);return 1;}}
  else if(close(336,272)){if(setting[0]==31&&setting[2]==1)setting[3]|=2;else {wrong(TX_CV_FIT);return 1;}}
  else return 0;
 }else if(room==71){
  if(close(96,192)){if(moving_x==120&&!moving_state)setting[3]|=1;else {wrong(TX_CV_FIT);return 1;}}
  else if(close(160,192)){if(moving_x==120&&!moving_state)setting[3]|=2;else {wrong(TX_CV_FIT);return 1;}}
  else return 0;
 }else if(room==72){
  unsigned k;if(close(144,104))k=0;else if(close(272,104))k=1;else if(close(384,104))k=2;else return 0;
  if(movement_ticks<24*(k+1)){wrong(TX_CV_WAIT);return 1;}setting[3]|=1u<<k;
 }else if(room==74){
  unsigned k;if(close(120,216))k=0;else if(close(360,240))k=1;else if(close(240,168))k=2;else return 0;
  if((setting[0]&2)&&(sound_observation()&(1u<<k)))setting[3]|=1u<<k;else {wrong(TX_CV_FIT);return 1;}
 }else return 0;
 changed();toast(TX_CV_TRACE);return 1;
}
COLD int covenants_game_interact(void){
 unsigned i=(unsigned)room-70,j;int x,y;
 if(i>=8||game_state!=PLAY||event_count)return 0;
 clear_prompts();
 if(close(resets[i][0],resets[i][1])){
  if(!reset_confirm){reset_confirm=1;toast(TX_CV_RESET_ASK);return 1;}
  if(!covenants_game_spawn((unsigned)room,0,&x,&y)){toast(TX_CV_FIT);return 1;}covenants_game_reset();game_region_warp(x,y);toast(TX_CV_RESET_DONE);return 1;
 }
 for(j=0;j<sizeof doors/sizeof doors[0];j++)if(doors[j].area==room&&!road_region_managed((unsigned)room,doors[j].to)&&close(doors[j].x,doors[j].y))return door(doors[j].to,doors[j].spawn);
 if((i==0||i==4)&&close(80,272)){simple(COVENANTS_REQUEST_ANCHOR,(unsigned)room,0,0,0);return 1;}
 if(close(invitations[i][0],invitations[i][1]))return invitation(i);
 for(j=0;j<manual_counts[i];j++)if(close(manual_points[i][j][0],manual_points[i][j][1])){manual_work(i,j);return 1;}
 if(!fulfilled(i)&&inspect_work())return 1;
 for(j=0;j<resident_counts[i];j++){
  int xx=residents[i][j].x,yy=residents[i][j].y;
  if(!j&&(i==1||i==3||i==5||i==6)){xx=npc_x;yy=npc_y;}
  if(close(xx,yy))return resident_dialogue(i,j);
 }
 return 0;
}
COLD int covenants_game_old_interact(void){
 if(game_state!=PLAY||event_count||!done(57)||!(adventure_save.campaign.chapter_flags&SAVE4_ENDING_SEEN))return 0;
 if(room==0&&close(120,94)){
  if(!state(60)){offer(60);objective(60,1);say(TX_CV_HOME_A,TX_CV_HOME_B);return 1;}
  if(!done(63)&&state(63)&&((bits(63)&3)==3)){
   if(state(63)==SAVE5_QUEST_READY)claim(63);else{objective(63,4);say(TX_CV_HOME_RETURN_A,TX_CV_HOME_RETURN_B);}return 1;
  }
  if(done(63)){say(TX_CV_END_A,TX_CV_END_B);return 1;}
  say(TX_CV_CLUE60A,TX_CV_CLUE60B);return 1;
 }
 if(room==62&&close(120,208)){
  if((bits(60)&1)&&!(bits(60)&2)){objective(60,2);say(TX_CV_LETTER_A,TX_CV_LETTER_B);return 1;}
  if(!(bits(60)&1)){say(TX_CV_CLUE60A,TX_CV_HOME_B);return 1;}
  /* Other completed-Horizons conversations retain their normal priority. */
  if(!done(60)){say(TX_CV_LETTER_A,TX_CV_LETTER_B);return 1;}
 }
 if(room==62&&!road_region_managed(62,70)&&close(416,16))return door(70,0);
 if(room==62&&state(63)&&(bits(63)&1)&&!(bits(63)&2)&&close(npc_x,npc_y)){
  if(!escort_stage){new_attempt();escort_stage=1;toast(TX_CV_WAIT);say(TX_CV_FAIR_RETURN_A,TX_CV_FAIR_RETURN_B);}return 1;
 }
 return 0;
}
static COLD void old_escort_tick(void){
 static const short route[8][2]={{416,32},{336,24},{336,112},{384,112},{384,192},{272,192},{272,208},{120,240}};
 if(room!=62||!state(63)||!(bits(63)&1)||(bits(63)&2)||!escort_stage||event_count)return;
 if(escort_stage>8)return;
 if(near(px,py,npc_x,npc_y,38)&&ambient%3==0){
  int tx=route[escort_stage-1][0],ty=route[escort_stage-1][1],nx=npc_x,ny=npc_y;
  if(nx!=tx)nx+=nx<tx?1:-1;else if(ny!=ty)ny+=ny<ty?1:-1;
  if(nx!=npc_x||ny!=npc_y){
   extern int solid(int,int);
   if(game_region_actor_overlap(nx-4,ny-4,nx+4,ny+4))npc_wait_for_space();
   else if(!solid(nx,ny)){npc_blocked_ticks=0;npc_x=nx;npc_y=ny;}
  }
  if(npc_x==tx&&npc_y==ty){escort_stage++;if(escort_stage==9)objective(63,2);}
 }
}
COLD void covenants_game_tick_old(void){
 int old_x=npc_x,old_y=npc_y;
 if((room!=0&&room!=62)||game_state!=PLAY)return;
 covenants_game_prepare_old_scene();
 ambient++;clear_prompts();old_escort_tick();
 if(npc_x!=old_x||npc_y!=old_y){npc_walk_recent=4;npc_walk_phase++;}else if(npc_walk_recent)npc_walk_recent--;
 if(room==62&&!road_region_managed(62,70)&&!transition_lock&&(keys&UP)&&near(px,py,416,16,10)&&done(57)&&(bits(60)&3)==3)door(70,0);
 if(room==0&&setting[23]){
  if(setting[23]==1){setting[23]=2;say(TX_CV_END_A,TX_CV_END_B);}
  else if(setting[23]==2){setting[23]=3;say(adventure_save.quests.region_flags[23]?TX_CV_END_INVITED_A:TX_CV_END_WAITING_A,adventure_save.quests.region_flags[23]?TX_CV_END_INVITED_B:TX_CV_END_WAITING_B);}
  else{setting[23]=0;if(adventure_save.quests.region_flags[23]&&adventure_save.quests.region_flags[23]!=255)say(TX_CV_END_WAITING_A,TX_CV_END_WAITING_B);}
 }
}
static COLD void held_practice_tick(void){
 if(room!=73||!practice_mode||setting[10]!=1)return;
 if(!cast.token||cast.command!=124||cast.scene!=scene||cast.attempt!=attempt||cast.geometry!=geometry||
    !members_match()||live_direction()>3||!covenants_powers_overlap(practices[3].target[0][0],practices[3].target[0][1],3)){
  setting[11]=0;return;
 }
 if(++setting[11]>=12){practice_ticks=360;practice_mode=0;setting[10]=setting[11]=0;geometry_changed();toast(TX_CV_PRACTICE_DONE);}
}
COLD void covenants_game_tick(void){
 unsigned i;int old_x=npc_x,old_y=npc_y;if(!covenants_game_is_room((unsigned)room)||game_state!=PLAY)return;
 if(work_area!=room)covenants_game_reset();
 ambient++;
 clear_prompts();
 if(event_count)return;
 if(moving_state)motion_tick();
 practice_expiry();
 held_practice_tick();
 work_tick();
 if(npc_x!=old_x||npc_y!=old_y){npc_walk_recent=4;npc_walk_phase++;}else if(npc_walk_recent)npc_walk_recent--;
 if(event_count||transition_lock)return;
 for(i=0;i<sizeof doors/sizeof doors[0];i++)if(doors[i].area==room&&!road_region_managed((unsigned)room,doors[i].to)&&(keys&doors[i].key)&&near(px,py,doors[i].x,doors[i].y,10)){door(doors[i].to,doors[i].spawn);return;}
}
COLD int covenants_game_name(void){return covenants_game_is_room((unsigned)room)?room_names[room-70]:TX_CV_JOURNAL;}
COLD int covenants_game_quest_text(void){
 unsigned q=!done(60)?60:!done(61)?61:!done(62)?62:63;return quest_names[q-60];
}
