typedef struct {
 FieldControlInput controls;
 int context_owned;
 int aim_holding;
} FieldUpdateInput;

static inline int field_update_input(FieldUpdateInput *input){
 int i;
 ticks++;
 for(i=0;i<6;i++)if(impacts[i].life)impacts[i].life--;
 if(hitstop){hitstop--;return 0;}
 if(pressed&KEY_START){journal_nav_open();game_state=PAUSE;return 0;}
 /* A contextual B belongs to its confirmation. Recall must also happen
  * before power ticks, otherwise hiding a held preview could release it. */
 input->context_owned=game_field_context_input();
 if(input->context_owned)game_power_preview_cancel();
 if(event_frame()||game_state!=PLAY)return 0;
 if(!input->context_owned&&(pressed&KEY_SELECT))field_goal_input((unsigned)pressed);
 input->controls=field_controls_read(&field_controls,(unsigned)keys,(unsigned)pressed);
 if(!input->context_owned&&input->controls.companion_pressed)game_field_companion_toggle();
 return 1;
}

static inline int field_update_powers(FieldUpdateInput *input){
 if(step_cd)step_cd--;
 if(area_ticks)area_ticks--;
 if(invuln)invuln--;
 if(ability_cd)ability_cd--;
 if(!ability_cd)covenants_cooldown_owned=0;
 if(heal_cd)heal_cd--;
 if(stone_guard)stone_guard--;
 input->aim_holding=game_power_aim_hold(summoned&&!input->context_owned&&
  !input->controls.companion_pressed?input->controls.power_held:0);
 advanced_tick();
 regional_powers_tick();
 northern_powers_tick();
 game_geometry_sync();
 southern_powers_tick();
 magma_powers_tick();
 if(underwater_power_time||underwater_power_cast_time)underwater_powers_tick();
 if(return_power_time||return_power_cast_time)return_powers_tick();
 if(horizons_power_time||horizons_power_cast_time)horizons_powers_tick();
 if(covenants_power_time||covenants_power_cast_time)covenants_powers_tick();
 if(event_frame())return 0;
 game_combat_tick();
 if(guard_invuln)guard_invuln--;
 if(power_effect)power_effect--;
 if(transition_lock)transition_lock--;
 return 1;
}

static inline int field_update_actions(const FieldUpdateInput *input){
 int dx=0,dy=0,return_input=0;
 if(input->context_owned){walk=0;game_attacks_suspend();return 1;}
 if(summoned){
  unsigned power=input->controls.power_pressed|(unsigned)(input->aim_holding&240);
  underwater_powers_input(power);
  if(return_power_time)return_input=return_powers_input(power);
  if(horizons_power_time)return_input|=horizons_powers_input(power);
  if(covenants_power_time)return_input|=covenants_powers_input(input->controls.power_pressed);
 }
 if(keys&KEY_LEFT){dx=-1;face=2;}
 if(keys&KEY_RIGHT){dx=1;face=3;}
 if(keys&KEY_UP){dy=-1;face=1;}
 if(keys&KEY_DOWN){dy=1;face=0;}
 if(swing||weapon_action.phase==WEAPON_WINDUP||weapon_action.phase==WEAPON_ACTIVE)
  face=weapon_action.direction;
 walk=(dx||dy)&&!input->aim_holding;
 if(walk)walk_phase++;
 if(input->aim_holding)walk=0;
 else{
  int speed=advanced_guard_charges?224:gear_stats.speed_q8;
  int diag=advanced_guard_charges?158:gear_stats.diagonal_q8;
  if(weapon_action.phase==WEAPON_CHARGING){speed=speed*3/4;diag=diag*3/4;}
  move_player(dx*(dx&&dy?diag:speed),dy*(dx&&dy?diag:speed));
 }
 if(game_road_step()||walk_entry())return 0;
 game_attack_update(keys,pressed);
 if(event_frame())return 0;
 /* Deferred rest cannot share another hostile tick; its save proof must
  * follow the first notice rather than the interaction's cold redraw. */
 if(save_requested&&(room==38||room==39)&&magma_game_save_prepare_pending()){
  save_frame();return 0;
 }
 /* An A interaction may own a new dialogue before a simultaneous B cast. */
 if(game_state!=PLAY)return 0;
 if((input->controls.power_pressed&FIELD_POWER_ACTION)&&!(return_input&2))game_field_ability();
 if(event_frame())return 0;
 return game_state==PLAY;
}

static inline int field_update_actors(void){
 /* These rooms can move collision props after the first synchronization.
  * The unconditional pre-tick and pre-draw checks still cover every room. */
 if(room==15||room==20||(unsigned)room-38u<40u)game_geometry_sync();
 game_companion_follow();
 update_shots();
 if((unsigned)room-54u<24u)return_legacy_tick();
 game_arrows_update();
 update_enemies();
 if(room==3||room==8||room==13)update_boss();
 region_game_tick();
 north_game_tick();
 south_game_tick();
 magma_game_tick();
 underwater_game_tick();
 if((unsigned)room-54u<8u)return_game_tick();
 if((unsigned)room-62u<8u)horizons_game_tick();
 if((unsigned)room-70u<8u)covenants_game_tick();
 if(room==0||room==62)covenants_game_tick_old();
 if(event_frame())return 0;
 return game_state==PLAY;
}

static inline void field_update_exits(void){
 if(room==6&&!(room_flags&CF_SKY_PATROL_CLEAR)){
  int i,alive=0;
  for(i=0;i<MAX_ENEMIES;i++)alive+=enemies[i].hp>0;
  if(!alive){room_flags|=CF_SKY_PATROL_CLEAR;save_game();show_scene(CD_PATROL_CLEAR,0,0);return;}
 }
 if(region_game_is_room((unsigned)room)||north_game_is_room((unsigned)room)||
    south_game_is_room((unsigned)room)||((unsigned)(room-38)<16u)){}
 else if(trials_is_room(room)){
  int dest=trials_exit(room,px,py);
  if(!transition_lock&&(keys&KEY_DOWN)&&dest>=0)enter_room(dest,0);
 }
 else if(room>=4&&room<14){
  const CampaignRoom *d=&campaign_rooms[room-4];
  if(!transition_lock&&px>=108&&px<=132){
   if(d->north_room!=0&&py<=39&&(keys&KEY_UP)&&
      (progress_bits()&d->north_flags)==d->north_flags)enter_room(d->north_room,d->north_spawn);
   else if(py>=140&&(keys&KEY_DOWN)&&!game_road_managed((unsigned)room,d->south_room))
    enter_room(d->south_room,d->south_spawn);
  }
 }
 else if(room==1){
  if(py<=31&&px>=WORLD_TEMPLE_GATE_X&&px<WORLD_TEMPLE_GATE_X+WORLD_TEMPLE_GATE_W)enter_room(2,0);
  else if(!game_road_managed(1,0)&&py>=WORLD_VILLAGE_EXIT_Y&&ab(px-WORLD_VILLAGE_EXIT_X)<18)enter_room(0,1);
 }
 else if(py<=31&&px>100&&px<140){
  if(room<3&&!game_road_managed((unsigned)room,(unsigned)room+1))enter_room(room+1,0);
 }
 else if(py>=149&&px>100&&px<140&&room>0&&room<=3)enter_room(room-1,1);
 camera_update(0);
}

static inline void field_update(void){
 FieldUpdateInput input;
 if(!field_update_input(&input))return;
 if(!field_update_powers(&input))return;
 if(!field_update_actions(&input))return;
 if(!field_update_actors())return;
 field_update_exits();
}
