unsigned return_game_action_begin(unsigned channel){CreatureInstance*c;if(!return_game_is_room((unsigned)room)||channel!=3)return 0;if(++serial==0)++serial;cast_token=serial;c=active();cast_id=c?c->instance_id:0;cast_form=c?c->form_id:0;cast_command=progression_command();cast_slot=c?adventure_save.roster.party[adventure_save.roster.selected_party]:255;cast_selected=adventure_save.roster.selected_party;cast_party=party();cast_scene=scene;cast_attempt=attempt;cast_x=px;cast_y=py;cast_face=face;field_hits=0;return cast_token;}
int return_game_field_target(unsigned i,int*x,int*y,int*r){int xx=0,yy=0;if(!return_game_is_room((unsigned)room)||i>=8)return 0;
 if(return_game_trial.index<13){const TrialDef*d=&trials[return_game_trial.index];if(i>=d->count)return 0;xx=d->target[i][0];yy=d->target[i][1];}
 else if(repeat_active){if(i)return 0;xx=room==55?120:368;yy=room==55?80:240;}
 else if(room==54&&i<4){static const short p[4][2]={{240,72},{272,240},{320,240},{400,200}};xx=p[i][0];yy=p[i][1];}
 else if(room==55&&i<2){xx=i?176:64;yy=72;}
 else if(room==56&&i<4){static const short p[4][2]={{240,96},{240,208},{112,272},{368,144}};xx=p[i][0];yy=p[i][1];}
 else if(room==57&&i<4){static const short p[4][2]={{320,208},{400,240},{304,240},{80,176}};xx=p[i][0];yy=p[i][1];}
 else if(room==58&&i<3){static const short p[3][2]={{320,80},{80,224},{368,240}};xx=p[i][0];yy=p[i][1];}
 else if(room==59&&i==0){xx=64;yy=56;}
 else if(room==60&&i<5){static const short p[5][2]={{56,48},{96,40},{144,40},{184,48},{120,104}};xx=p[i][0];yy=p[i][1];}
 else if(room==61&&i<2){xx=i?176:64;yy=56;}
 else return 0;
 if(x)*x=xx;
 if(y)*y=yy;
 if(r)*r=12;
 return 1;
}
static int command_cap(unsigned command,unsigned key){const CreatureAbility*a=creatures_ability(command);return a&&key>=1&&key<=30&&(a->field_caps&(1u<<(key-1)));}
static COLD int wrong(int textid){toast(textid);return 2;}
COLD int return_game_field_hit(unsigned i,unsigned command,unsigned id,unsigned form,unsigned token){CreatureInstance*c=active();int x,y;if(event_count||!token||token!=cast_token||cast_scene!=scene||cast_attempt!=attempt||!c||id!=cast_id||form!=cast_form||c->instance_id!=id||c->form_id!=form||cast_slot>=160||c!=&adventure_save.roster.instances[cast_slot]||cast_selected!=adventure_save.roster.selected_party||cast_party!=party()||command!=cast_command||command!=progression_command()||!return_game_field_target(i,&x,&y,0))return 0;if(field_hits&(1u<<i))return 0;field_hits|=1u<<i;
 if(return_game_trial.index<13){if(!participant()||command!=return_game_trial.command){cancel_proof();return wrong(TX_RT_SAME);}if(cast_face!=1||cast_y<=y||ab(cast_x-x)>48)return wrong(TX_RT_WRONG_SIDE);return trial_cast(i);}
 if(repeat_active){if(!repeat_participant()){cancel_proof();return wrong(TX_RT_SAME);}if(command!=repeat_command)return wrong(TX_RT_WRONG);if(cast_face!=1||cast_y<=y)return wrong(TX_RT_WRONG_SIDE);if(repeat_setting!=(repeat_active==17?3:1))return wrong(TX_RT_FIT);repeat_stage=1;changed();toast(TX_RT_WALK);return 1;}
 /* Optional tagged roles remain useful after story completion and accept
  * inherited compatible commands. They never grant durable proof or rewards. */
 if((room==54&&i>=2)||room==55||(room==56&&i>=2)||(room==57&&i==3)||room==58){unsigned cap=room==54?(i==2?13:11):room==55?17:room==56?(i==2?14:22):room==57?23:i==0?11:i==1?19:14;if(!command_cap(command,cap))return wrong(TX_RT_WRONG);setting[3]|=(unsigned char)(1u<<i);changed();toast(TX_RT_TRACE);return 1;}
 if(room==54){if(i==0){if(!command_cap(command,11)&&command!=92)return wrong(TX_RT_ROOT);setting[0]=1;}else{if(!command_cap(command,13)&&command!=91)return wrong(TX_RT_HEARTH);setting[1]=1;}changed();toast(TX_RT_TRACE);return 1;}
 if(room==56){if(!command_cap(command,14))return wrong(TX_RT_FLOAT);if(!setting[0])return wrong(TX_RT_MANUAL);setting[1]|=1u<<i;if(setting[1]==3)objective(50,2);changed();toast(TX_RT_TRACE);return 1;}
 if(room==57){if(i==0){if(!command_cap(command,17))return wrong(TX_RT_HINGE);if(cast_face!=1||cast_y<=y)return wrong(TX_RT_WRONG_SIDE);objective(48,1);}else if(i==1){if(!command_cap(command,4))return wrong(TX_RT_BRAKE);if(!setting[0])return wrong(TX_RT_BRAKE);if(!set_mechanism(2,1))return 2;objective(48,2);}else{if(!setting[1])return wrong(TX_RT_MANUAL);if(!command_cap(command,13)&&!command_cap(command,23))return wrong(TX_RT_HEARTH);objective(52,2);}changed();toast(TX_RT_TRACE);return 1;}
 if(room==59){if(!command_cap(command,24))return wrong(TX_RT_FLOAT);if(!setting[0])return wrong(TX_RT_MANUAL);objective(50,1);changed();toast(TX_RT_TRACE);return 1;}
 if(room==60){static const unsigned char caps[5]={11,13,15,17,24};if(phase_step>=5){if(!command_cap(command,caps[i]))return wrong(TX_RT_PHASE_WRONG);toast(TX_RT_TRACE);return 1;}if(i!=phase_step||!command_cap(command,caps[phase_step]))return wrong(TX_RT_PHASE_WRONG);if(i==3||i==4){const CreatureForm*f=creatures_form(form);if(!f||f->phase!=(i==3?CREATURE_METAL:CREATURE_WATER)||f->polarity!=(i==3?CREATURE_YIN:CREATURE_YANG))return wrong(i==3?TX_RT_RECEPTIVE:TX_RT_IMPULSE);}phase_step++;if(phase_step==5)objective(51,2);changed();toast(TX_RT_TRACE);return 1;}
 if(room==61){if(i==0){if(!command_cap(command,17))return wrong(TX_RT_HINGE);if(cast_face!=1||cast_y<=y)return wrong(TX_RT_WRONG_SIDE);setting[0]=1;}else{if(!command_cap(command,24))return wrong(TX_RT_FLOAT);setting[1]=1;}if(setting[0]&&setting[1])objective(51,4);changed();toast(TX_RT_TRACE);return 1;}
 return 0;
}
int return_game_power(unsigned command){(void)command;if(return_game_trial.index<13&&progression_command()!=return_game_trial.command){cancel_proof();toast(TX_RT_WRONG);changed();return 1;}return 0;}
