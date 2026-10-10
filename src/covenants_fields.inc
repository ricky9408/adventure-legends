/* Full bounded party/equipment comparison, not a hash or public progress bit. */
static COLD void capture_members(void){
 CreatureRoster*r=&adventure_save.roster;EquipmentState*e=&adventure_save.equipment;unsigned i;
 for(i=0;i<4;i++){
  unsigned s=r->party[i];PartyMemberProof*p=&cast.members[i];cast.refs[i]=(unsigned char)s;zero_bytes(p,sizeof *p);
  if(s<CREATURE_ROSTER_CAPACITY){CreatureInstance*c=&r->instances[s];p->id=c->instance_id;p->form=c->form_id;p->command_slot=c->selected_command;p->commands[0]=c->equipped[0];p->commands[1]=c->equipped[1];p->flags=c->flags;}
 }
 for(i=0;i<5;i++){unsigned s=e->equipped[i];cast.gear_refs[i]=(unsigned char)s;zero_bytes(&cast.gear[i],sizeof cast.gear[i]);if(s<EQUIPMENT_BAG_CAPACITY)cast.gear[i]=e->bag[s];}
}
static COLD int members_match(void){
 CreatureRoster*r=&adventure_save.roster;EquipmentState*e=&adventure_save.equipment;unsigned i;
 for(i=0;i<4;i++){
  unsigned s=r->party[i];PartyMemberProof*p=&cast.members[i];CreatureInstance*c;
  if(s!=cast.refs[i])return 0;
  if(s>=CREATURE_ROSTER_CAPACITY)continue;
  c=&r->instances[s];
  if(c->instance_id!=p->id||c->form_id!=p->form||c->selected_command!=p->command_slot||c->equipped[0]!=p->commands[0]||c->equipped[1]!=p->commands[1]||c->flags!=p->flags)return 0;
 }
 for(i=0;i<5;i++){unsigned s=e->equipped[i];if(s!=cast.gear_refs[i]||(s<EQUIPMENT_BAG_CAPACITY&&!equal_bytes(&e->bag[s],&cast.gear[i],sizeof cast.gear[i])))return 0;}
 return 1;
}
COLD unsigned covenants_game_action_begin(unsigned channel){
 CreatureInstance*c;
 if(!covenants_game_is_room((unsigned)room)||channel!=3||game_state!=PLAY||event_count||face<0||face>3)return 0;
 c=active();if(!c)return 0;
 invalidate_cast();if(practice_mode)setting[10]=setting[11]=0;next_generation(&serial);cast.token=serial;cast.id=c->instance_id;
 cast.form=c->form_id;cast.command=progression_command();cast.slot=adventure_save.roster.party[adventure_save.roster.selected_party];
 cast.selected=adventure_save.roster.selected_party;cast.scene=scene;cast.attempt=attempt;cast.geometry=geometry;
 cast.x=(short)px;cast.y=(short)py;cast.face=(unsigned char)face;capture_members();return cast.token;
}
static COLD unsigned live_direction(void){
 if(cast.command==12||cast.command>=122){
  const CovenantsPowerProof*p=covenants_powers_proof();
  if(!p||p->token!=cast.token||p->caster!=cast.id||p->form!=cast.form||p->command!=cast.command||p->origin_x!=cast.x||p->origin_y!=cast.y||p->scene!=scene||p->attempt!=attempt||p->geometry!=geometry)return 4;
  return p->direction;
 }
 if(cast.command>=106&&cast.command<=121){
  if(!horizons_powers_busy()||horizons_powers_cast_token()!=cast.token||horizons_powers_caster_id()!=cast.id||horizons_power_kind!=cast.command||horizons_power_form!=cast.form||horizons_power_origin_x!=cast.x||horizons_power_origin_y!=cast.y)return 4;
  return (unsigned)horizons_power_direction;
 }
 if(cast.command>=91&&cast.command<=105){
  if(!return_powers_busy()||return_powers_cast_token()!=cast.token||return_powers_caster_id()!=cast.id||return_power_kind!=cast.command||return_power_form!=cast.form||return_power_origin_x!=cast.x||return_power_origin_y!=cast.y)return 4;
  return (unsigned)return_power_direction;
 }
 return 4; /* No generic phase/capability fallback can solve this chapter. */
}
COLD int covenants_game_field_target(unsigned index,int*x,int*y,int*radius){
 unsigned i=(unsigned)room-70;
 if(i>=8||index>=8)return 0;
 if(practice_mode){const PracticeDef*p=&practices[i];if(index>=p->count)return 0;if(x)*x=p->target[index][0];if(y)*y=p->target[index][1];if(radius)*radius=3;return 1;}
 if(fulfilled(i)||!state(i<4?61:62)||index>=station_counts[i])return 0;
 if(x)*x=station_targets[i][index].x;
 if(y)*y=station_targets[i][index].y;
 if(radius)*radius=station_targets[i][index].radius;
 return 1;
}
static COLD unsigned effect_beat(unsigned command){
 if(command==12||command>=122)return covenants_powers_beat();
 return command>=106?horizons_powers_beat():1;
}
static COLD int effect_overlap(unsigned command,int x,int y,int radius){
 if(command==12||command>=122)return covenants_powers_overlap(x,y,radius)!=0;
 if(command>=106)return horizons_powers_overlap(x,y,radius)!=0;
 return return_powers_overlap(x,y,radius)!=0;
}
static COLD int practice_hit(unsigned i,unsigned command,unsigned token,unsigned beat){
 const PracticeDef*p=&practices[(unsigned)room-70];unsigned need=(1u<<p->count)-1;
 if(command!=p->command||cast.form!=(unsigned)room+51u||!owned((unsigned)room-70)||!fulfilled((unsigned)room-70))return 0;
 if(command==12&&!covenants_powers_release_phase())return 0;
 if(command==123){
  if(i==0&&beat==1)heat_token=token;
  else if(i!=1||beat!=2||heat_token!=token)return 0;
 }
 setting[10]|=1u<<i;
 if(setting[10]==need&&command!=124){
  /* Temporary convenience only; no quest, history, source or healing credit. */
  practice_ticks=360;practice_mode=0;setting[10]=0;geometry_changed();toast(TX_CV_PRACTICE_DONE);
 }
 return 1;
}
static COLD int station_hit(const StationTarget*t,unsigned token,unsigned beat){
 unsigned bit=1u<<t->station;
 if(t->beat!=beat)return 0;
 if(t->command==108){
  if(beat==1){heat_token=token;toast(TX_CV_GATHER);return 1;}
  if(heat_token!=token||!horizons_powers_release_phase())return 0;
  heat_token=0;
 }
 if(setting[0]&bit)return 1;
 /* Mechanical prerequisites are local ordinary settings. No old cast token
  * or completed different covenant substitutes for these visible states. */
 if(room==72&&t->station==0&&!setting[1])return wrong(TX_CV_FIT);
 if(room==74&&t->station==1&&sound_observation()!=7)return wrong(TX_CV_FIT);
 if(room==75&&t->station==1&&setting[1]!=1)return wrong(TX_CV_FIT);
 if(room==76&&t->station==1){
  if(!(setting[0]&1)||npc_stage!=3||moving_x!=224||moving_state)return wrong(TX_CV_WAIT);
  if(!begin_motion(272))return 0;
 }
 if(room==76&&t->station==2&&(moving_x!=272||moving_state||npc_stage!=3))return wrong(TX_CV_WAIT);
 if(room==77&&t->station==0&&!setting[1])return wrong(TX_CV_FIT);
 setting[0]|=bit;changed();toast(TX_CV_TRACE);return 1;
}
COLD int covenants_game_field_hit(unsigned index,unsigned command,unsigned id,unsigned form,unsigned token){
 CreatureInstance*c=active();unsigned beat,i=(unsigned)room-70;int x,y,radius;
 if(i>=8||game_state!=PLAY||event_count||!token||token!=cast.token||cast.scene!=scene||cast.attempt!=attempt||cast.geometry!=geometry||!c||
    id!=cast.id||form!=cast.form||c->instance_id!=id||c->form_id!=form||cast.slot>=160||c!=&adventure_save.roster.instances[cast.slot]||
    cast.selected!=adventure_save.roster.selected_party||command!=cast.command||command!=progression_command()||!members_match()||
    !creatures_command_learned(form,c->level,command)||live_direction()>3||!covenants_game_field_target(index,&x,&y,&radius))return 0;
 beat=effect_beat(command);if(!beat||beat>2||cast.hits[beat-1]&(1u<<index)||!effect_overlap(command,x,y,radius))return 0;
 if(practice_mode){if(command!=practices[i].command)return 0;}
 else if(command!=station_targets[i][index].command)return 0;
 cast.hits[beat-1]|=1u<<index;
 return practice_mode?practice_hit(index,command,token,beat):station_hit(&station_targets[i][index],token,beat);
}
COLD int covenants_game_power(unsigned command){
 if(covenants_game_is_room((unsigned)room)&&practice_mode&&command!=practices[(unsigned)room-70].command){practice_mode=0;setting[10]=0;invalidate_cast();next_generation(&attempt);toast(TX_CV_WRONG);return 1;}
 return 0;
}
