COLD unsigned horizons_game_action_begin(unsigned channel){CreatureInstance*c;if(!horizons_game_is_room((unsigned)room)||channel!=3)return 0;if(++serial==0)++serial;invalidate_cast();cast.token=serial;c=active();cast.id=c?c->instance_id:0;cast.form=c?c->form_id:0;cast.command=progression_command();cast.slot=c?adventure_save.roster.party[adventure_save.roster.selected_party]:255;cast.selected=adventure_save.roster.selected_party;cast.party=party();cast.scene=scene;cast.attempt=attempt;cast.x=px;cast.y=py;cast.face=face;return cast.token;}
/* Startup aiming belongs to the live effect snapshot, never the player's
 * mutable face. Token/id/form/command/origin must all belong to this action. */
static COLD unsigned cast_direction(void){
 if(cast.command>=106&&cast.command<=121){if(!horizons_powers_busy()||horizons_powers_cast_token()!=cast.token||horizons_powers_caster_id()!=cast.id||horizons_power_kind!=cast.command||horizons_power_form!=cast.form||horizons_power_origin_x!=cast.x||horizons_power_origin_y!=cast.y||(unsigned)horizons_power_direction>3u)return 4;return(unsigned)horizons_power_direction;}
 if(cast.command>=91&&cast.command<=105){if(!return_powers_busy()||return_powers_cast_token()!=cast.token||return_powers_caster_id()!=cast.id||return_power_kind!=cast.command||return_power_form!=cast.form||return_power_origin_x!=cast.x||return_power_origin_y!=cast.y||(unsigned)return_power_direction>3u)return 4;return(unsigned)return_power_direction;}
 return cast.face;
}
COLD int horizons_game_field_target(unsigned i,int*x,int*y,int*r){int xx=0,yy=0;if(!horizons_game_is_room((unsigned)room)||i>=8)return 0;
 if(proof.mode==MODE_TRIAL||proof.mode==MODE_PRACTICE){const TrialDef*d=work_trial();if(i>=2)return 0;xx=d->target[i][0];yy=d->target[i][1];if(proof.mode==MODE_PRACTICE&&proof.index==0&&room==63){xx=i?368:336;yy=i?96:64;}}
 else if(proof.mode==MODE_INITIAL||proof.mode==MODE_REPEAT){const SourceDef*d=&sources[proof.index];unsigned count=proof.mode==MODE_REPEAT&&(proof.index==1||proof.index==8||proof.index==9)?2:1;if(i>=count)return 0;xx=d->target[0]+(i?24:0);yy=d->target[1];}
 else if(room==62&&i==0){xx=352;yy=176;}
 else if(room==63&&i==0){xx=carriage_x;yy=90;}
 else if(room==64&&i<4){xx=i==3?208:64+i*56;yy=i==3?88:(setting[0]&(1u<<i))?80:56;}
 else if(room==65&&i==0){xx=336;yy=160;}
 else if(room==66&&i<4){if(i==0){xx=144+setting[0]*32;yy=248;}else {xx=112+i*32;yy=80;}}
 else if(room==67&&i<3){xx=i==0?80+setting[0]*32:i==1?288:312;yy=i==0?224:208;}
 else if(room==68&&i<3){xx=48+i*72;yy=64;}
 else return 0;
 if(x)*x=xx;
 if(y)*y=yy;
 if(r)*r=12;
 return 1;
}
static COLD int rail_open(unsigned from,unsigned to){unsigned edge=from<to?from:to;if(from>3||to>3||ab((int)from-(int)to)!=1)return 0;return edge==0?setting[1]==1:edge==1?setting[2]==0:setting[2]==1;}
static COLD int load_clear(int cx){int x,y;if(game_region_actor_overlap(cx-7,65,cx+7,79))return 0;for(y=65;y<80;y+=7)for(x=cx-7;x<cx+8;x+=7)if(horizons_game_geometry_solid(63,x,y))return 0;return 1;}
static COLD int pull_carriage(unsigned facing){unsigned next;int direction;if(setting[3])return wrong(TX_HZ_CLEAR);if(facing!=2&&facing!=3)return wrong(TX_HZ_SIDE);direction=cast.x>carriage_x?1:-1;if((direction>0&&facing!=2)||(direction<0&&facing!=3))return wrong(TX_HZ_SIDE);if((direction<0&&!setting[0])||(direction>0&&setting[0]>=3))return wrong(TX_HZ_FIT);next=setting[0]+direction;if(!rail_open(setting[0],next))return wrong(TX_HZ_FIT);for(int xx=carriage_x;xx!=192+(int)next*32;xx+=direction*2)if(!load_clear(xx))return wrong(TX_HZ_CLEAR);setting[4]=next;setting[3]=1;invalidate_cast();horizons_powers_geometry_changed();return_powers_geometry_changed();changed();return 1;}
COLD int horizons_game_field_hit(unsigned i,unsigned command,unsigned id,unsigned form,unsigned token){CreatureInstance*c=active();unsigned beat=command>=106?horizons_powers_beat():1,mask,facing;int x,y;if(!beat||beat>2)return 0;if(event_count||!token||token!=cast.token||cast.scene!=scene||cast.attempt!=attempt||!c||id!=cast.id||form!=cast.form||c->instance_id!=id||c->form_id!=form||cast.slot>=160||c!=&adventure_save.roster.instances[cast.slot]||cast.selected!=adventure_save.roster.selected_party||cast.party!=party()||command!=cast.command||command!=progression_command()||!horizons_game_field_target(i,&x,&y,0)||!creatures_command_learned(form,c->level,command))return 0;facing=cast_direction();if(facing>3)return 0;mask=1u<<i;if(!proof.mode&&i==0&&(room==63||room==66)&&((cast.hits[0]|cast.hits[1])&mask))return 0;if(cast.hits[beat-1]&mask)return 0;cast.hits[beat-1]|=mask;
 if(proof.mode)return attempt_hit(i,command,token,beat,facing);
 if(room==62){if(command!=106)return wrong(TX_HZ_WRONG);toast(TX_HZ_TRACE);return 1;}
 if(room==63){if(command!=106)return wrong(TX_HZ_WRONG);if(!(bits(55)&1))return wrong(TX_HZ_FIT);return pull_carriage(facing);}
 if(room==64){if(i<3){if(command!=106)return wrong(TX_HZ_WRONG);if(facing!=0&&facing!=1)return wrong(TX_HZ_SIDE);if(cast.y>y){setting[0]|=1u<<i;}else setting[0]&=~(1u<<i);setting[2]|=1u<<i;}else{if(command!=102)return wrong(TX_HZ_WRONG);if(facing!=1||cast.y<=y)return wrong(TX_HZ_SIDE);setting[1]=1;}if(setting[0]==5&&setting[1]&&(setting[2]&5)==5)objective(55,4);}
 else if(room==65){if(command!=104)return wrong(TX_HZ_WRONG);if(setting[0]!=1)return wrong(TX_HZ_FIT);setting[1]=3;objective(56,2);}
 else if(room==66){if(!(bits(56)&2))return wrong(TX_HZ_FIT);if(i==0){if(command!=106)return wrong(TX_HZ_WRONG);if(facing!=2&&facing!=3)return wrong(TX_HZ_SIDE);if(cast.x>x&&setting[0]<2)setting[0]++;else if(cast.x<x&&setting[0])setting[0]--;else return wrong(TX_HZ_FIT);}else{if(command!=104)return wrong(TX_HZ_WRONG);if(i==1){setting[1]=0;return wrong(TX_HZ_DRY);}setting[1]|=1u<<(i-1);}if(setting[0]==1&&setting[1]==6)objective(56,4);}
 else if(room==67){if(i==0){if(command!=110)return wrong(TX_HZ_WRONG);if(facing!=2&&facing!=3)return wrong(TX_HZ_SIDE);if(cast.x<x&&setting[0]<2)setting[0]++;else if(cast.x>x&&setting[0])setting[0]--;else return wrong(TX_HZ_FIT);if(setting[0]==1)objective(57,1);}else{if(command!=108)return wrong(TX_HZ_WRONG);if(i==1&&horizons_powers_release_phase())return 0;if(i==1&&!horizons_powers_release_phase()){wax_token=token;}else if(i==2&&horizons_powers_release_phase()&&wax_token==token&&setting[1]&&setting[2]){objective(57,2);wax_token=0;}else return wrong(TX_HZ_CAST);}}
 else if(room==68){static const unsigned char commands[3]={106,102,104};unsigned want=i==0?0:i==1?1:3;if(command!=commands[i])return wrong(TX_HZ_WRONG);if((bits(57)&4)){toast(TX_HZ_NO_REWARD);return 1;}if(setting[0]!=want||!(bits(57)&2))return wrong(TX_HZ_FIT);setting[0]|=1u<<i;if(setting[0]==7)objective(57,4);}
 else return 0;
 changed();toast(TX_HZ_TRACE);return 1;
}
COLD int horizons_game_power(unsigned command){(void)command;if((proof.mode==MODE_REPEAT||proof.mode==MODE_TRIAL||proof.mode==MODE_PRACTICE)&&progression_command()!=proof.command){cancel_proof();toast(TX_HZ_SAME);changed();return 1;}return 0;}
