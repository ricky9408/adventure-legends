static COLD int wrong(int id){toast(id);return 2;}
static COLD int command_cap(unsigned command,unsigned mask){const CreatureAbility*a=creatures_ability(command);return a&&!!(a->field_caps&mask);}
static COLD int attempt_solved(void){if(!proof.mode)return 0;if(proof.mode==MODE_INITIAL||proof.mode==MODE_REPEAT)return proof.stage==3;return proof.stage==3&&proof.walk==3;}
static COLD int invite_source(unsigned i){HorizonsRequest r={0};if(i>=12)return 0;
 if(source_owned(i))return 0;
 if(i<4){if(state(54+i)!=1||bits(54+i)!=(i?7u:3u)){say(qclues[i][0],qclues[i][1]);return 1;}}
 else if(proof.mode!=MODE_INITIAL||proof.index!=i||!attempt_solved()){say(sources[i].clue[0],sources[i].clue[1]);return 1;}
 if(invite_confirm!=i+1){invite_confirm=i+1;toast(TX_HZ_BEGIN);return 1;}
 if(i<4){cancel_proof();}
 r.operation=HORIZONS_REQUEST_INITIAL_RECRUIT;r.room=room;r.source=i+1;r.family=41+i;enqueue(r);return 1;
}
static COLD int begin_source(unsigned i){CreatureInstance*c=active();const SourceDef*d=&sources[i];const CreatureForm*f=c?creatures_form(c->form_id):0;
 if(i>=12||room!=d->area)return 0;
 if(!source_owned(i)){if(i<4)return invite_source(i);if(!done(54)){toast(TX_HZ_LOCKED);return 1;}if(proof.mode==MODE_INITIAL&&proof.index==i)return invite_source(i);bind(MODE_INITIAL,i,0,0);}
 else {if(proof.mode==MODE_REPEAT&&proof.index==i){HorizonsRequest r={0};if(!participant()){cancel_proof();return wrong(TX_HZ_SAME);}if(!attempt_solved()){say(d->clue[0],d->clue[1]);return 1;}if(invite_confirm!=i+1){invite_confirm=i+1;toast(TX_HZ_BEGIN);return 1;}r.operation=HORIZONS_REQUEST_REPEAT_RECRUIT;r.room=room;r.source=33+i;r.family=41+i;r.slot=proof.slot;r.instance_id=proof.id;r.form=proof.form;r.command=proof.command;enqueue(r);return 1;}
  if(!c||!f||f->family!=41+i||progression_command()!=d->command||!done(d->claim)){say(TX_HZ_TRIAL_PICK,d->clue[0]);return 1;}bind(MODE_REPEAT,i,c,d->command);
 }
 changed();say(d->clue[0],d->clue[1]);return 1;
}
static COLD int begin_trial(unsigned i){CreatureInstance*c=active();const TrialDef*d=&trials[i];int result;if(!c||c->form_id!=d->form||progression_command()!=d->command){say(TX_HZ_TRIAL_PICK,d->clue[0]);return 1;}result=horizons_trial_status(&adventure_save,adventure_save.roster.party[adventure_save.roster.selected_party],c->instance_id,41+i,1,c->form_id,progression_command());if(result!=HORIZONS_CHANGED&&result!=HORIZONS_UNCHANGED){say(TX_HZ_TRIAL_PICK,d->clue[0]);return 1;}bind(MODE_TRIAL,i,c,d->command);proof.replay=result==HORIZONS_UNCHANGED;changed();say(d->clue[0],d->clue[1]);return 1;}
static COLD int begin_practice(unsigned i){CreatureInstance*c=active();if(room!=practice_trials[i].area||!c||c->form_id!=trials[i].form+1u||progression_command()!=trials[i].command+1u||!creatures_has_trial_qualified(c,41+i,1))return 0;bind(MODE_PRACTICE,i,c,progression_command());changed();say(practice_trials[i].clue[0],practice_trials[i].clue[1]);return 1;}
static COLD void trial_finish(void){HorizonsRequest r={0};if((proof.mode!=MODE_TRIAL&&proof.mode!=MODE_PRACTICE)||!participant()||!attempt_solved())return;if(proof.replay||proof.mode==MODE_PRACTICE){cancel_proof();changed();toast(TX_HZ_PRACTICE);return;}r.operation=HORIZONS_REQUEST_TRIAL_COMPLETE;r.room=room;r.slot=proof.slot;r.instance_id=proof.id;r.family=41+proof.index;r.key=1;r.form=proof.form;r.command=proof.command;enqueue(r);}
static COLD int attempt_manual(unsigned second){unsigned i=proof.index;if(proof.mode==MODE_INITIAL||proof.mode==MODE_REPEAT){const SourceDef*d=&sources[i];if(proof.mode==MODE_REPEAT&&!participant()){cancel_proof();return wrong(TX_HZ_SAME);}
  if(i==4){proof.setting=(proof.setting+1)%3;proof.stage=proof.mode==MODE_INITIAL&&proof.setting==2?2:0;}
  else if(i==7){if(proof.mode==MODE_INITIAL){proof.setting^=second?2:1;proof.stage=proof.setting==3?2:0;}else if(proof.hits&&proof.cast_token==cast.token&&horizons_power_kind==117&&horizons_powers_busy()){proof.stage=2;}else return wrong(TX_HZ_CAST);}
  else if(i==8&&proof.mode==MODE_INITIAL){if(!second){proof.setting=1;proof.stage=0;}else if(proof.setting==1){proof.setting=2;proof.stage=2;}else return wrong(TX_HZ_FIT);}
  else {proof.setting^=1;if(i==5&&proof.mode==MODE_INITIAL)proof.stage=proof.setting?2:0;else {proof.stage=0;proof.hits=0;proof.cast_token=0;}}
  (void)d;invite_confirm=0;changed();toast(TX_HZ_ADJUST);return 1;
 }
 if(proof.mode==MODE_TRIAL||proof.mode==MODE_PRACTICE){if(!participant()){cancel_proof();return wrong(TX_HZ_SAME);}
  if(i==2&&proof.stage==1){proof.setting=1;proof.stage=3;}
  else if(i==1&&proof.stage==1){proof.setting=1;} /* Same cast may retain gathered warmth through a hand action. */
  else {proof.setting^=1;proof.hits=proof.walk=proof.stage=0;proof.cast_token=0;}
  changed();toast(TX_HZ_ADJUST);return 1;
 }return 0;
}
static COLD int attempt_hit(unsigned n,unsigned command,unsigned token,unsigned beat,unsigned facing){unsigned i=proof.index;
 if(proof.mode!=MODE_INITIAL&&!participant()){cancel_proof();return wrong(TX_HZ_SAME);}
 if(proof.mode==MODE_REPEAT&&command!=sources[i].command)return wrong(TX_HZ_WRONG);
 if(proof.mode==MODE_TRIAL||proof.mode==MODE_PRACTICE){if(command!=proof.command)return wrong(TX_HZ_WRONG);
  if(proof.mode==MODE_PRACTICE){if(!proof.setting)return wrong(TX_HZ_FIT);if((beat==1&&n!=0)||(beat==2&&n!=1))return 0;if(beat==1&&n==0){proof.cast_token=token;proof.hits|=1;}else if(beat==2&&n==1&&proof.cast_token==token&&(proof.hits&1)){proof.hits|=2;proof.stage=3;}else return wrong(TX_HZ_CAST);}
  else if(i==0){if(facing!=1||cast.y<=trials[i].target[n][1])return wrong(TX_HZ_SIDE);if(n>=2)return 0;proof.hits|=1u<<n;if(proof.hits==3)proof.stage=3;}
  else if(i==1){if(n==0&&horizons_powers_release_phase())return 0;if(n==0&&!horizons_powers_release_phase()){proof.cast_token=token;proof.stage=1;}else if(n==1&&horizons_powers_release_phase()&&proof.cast_token==token&&proof.stage==1&&proof.setting){proof.stage=3;}else return wrong(TX_HZ_CAST);}
  else if(i==2){if(facing!=3||cast.x>=144||n!=0)return wrong(TX_HZ_SIDE);proof.hits=1;proof.stage=1;}
  else {if(!proof.setting||facing!=3)return wrong(TX_HZ_SIDE);proof.hits|=1u<<n;if(proof.hits==3)proof.stage=3;}
  changed();toast(TX_HZ_TRACE);trial_finish();return 1;
 }
 if(proof.mode==MODE_INITIAL){
  if(i==6){if(!command_cap(command,FIELD_IGNITE)||!proof.setting)return wrong(TX_HZ_WRONG);proof.stage=2;}
  else if(i==8){if(!command_cap(command,FIELD_ECHO_OUTLINE))return wrong(TX_HZ_WRONG);toast(TX_HZ_SOURCE9A);return 1;}
  else if(i==7){if(!command_cap(command,FIELD_PRESS_WEIGHT|FIELD_SHIFT_BALLAST))return wrong(TX_HZ_WRONG);toast(TX_HZ_SOURCE8A);return 1;}
  else if(i==9){if(command!=104||!proof.setting)return wrong(TX_HZ_WRONG);proof.stage=2;}
  else if(i==10){if(!command_cap(command,FIELD_GROW_ROOTS|FIELD_GROW_BRIDGE))return wrong(TX_HZ_WRONG);proof.stage=2;}
  else if(i==11){if(!proof.setting)return wrong(TX_HZ_FIT);if(proof.stage==0&&command_cap(command,FIELD_TURN_VANE)){proof.stage=1;}else if(proof.stage==1&&command==102){proof.stage=2;}else return wrong(TX_HZ_WRONG);}
  else return wrong(TX_HZ_FIT);
 } else if(proof.mode==MODE_REPEAT){
  if(i==1){if(!proof.setting)return wrong(TX_HZ_FIT);if(n==0&&horizons_powers_release_phase())return 0;if(n==0&&!horizons_powers_release_phase()){proof.cast_token=token;proof.hits=1;}else if(n==1&&horizons_powers_release_phase()&&proof.cast_token==token&&proof.hits==1){proof.stage=2;}else return wrong(TX_HZ_CAST);}
  else if(i==2){if(facing!=3||cast.x>=sources[i].target[0])return wrong(TX_HZ_SIDE);proof.stage=2;}
  else if(i==4){if(!proof.setting)return wrong(TX_HZ_FIT);proof.setting=2;proof.stage=2;}
  else if(i==7){if(facing!=1)return wrong(TX_HZ_SIDE);proof.hits=1;proof.cast_token=token;}
  else if(i==8||i==9){if(!proof.setting)return wrong(TX_HZ_FIT);if((beat==1&&n!=0)||(beat==2&&n!=1))return 0;if(beat==1&&n==0){proof.cast_token=token;proof.hits=1;}else if(beat==2&&n==1&&proof.cast_token==token&&proof.hits==1){proof.hits=3;proof.stage=2;}else return wrong(TX_HZ_CAST);}
  else {if(i!=10&&!proof.setting)return wrong(TX_HZ_FIT);if(i==0&&(facing!=2&&facing!=3))return wrong(TX_HZ_SIDE);proof.stage=2;}
 }
 changed();toast(TX_HZ_TRACE);return 1;
}
static COLD void attempt_walk(void){unsigned i=proof.index;if(!proof.mode)return;if(proof.mode!=MODE_INITIAL&&!participant()){cancel_proof();changed();return;}
 if(proof.mode==MODE_INITIAL||proof.mode==MODE_REPEAT){const SourceDef*d=&sources[i];if(proof.stage==2&&near(px,py,d->walk[0],d->walk[1],8)){proof.stage=3;changed();toast(TX_HZ_BEGIN);if(proof.mode==MODE_INITIAL&&i==5)objective(58,1);}return;}
 if(proof.stage==3){const TrialDef*d=work_trial();if(!(proof.walk&1)&&near(px,py,d->walk[0][0],d->walk[0][1],8)){proof.walk=1;changed();toast(TX_HZ_WALK);}else if(proof.walk==1&&near(px,py,d->walk[1][0],d->walk[1][1],8)){proof.walk=3;changed();trial_finish();}}
}
