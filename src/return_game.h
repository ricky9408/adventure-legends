#ifndef EMBERBOND_RETURN_GAME_H
#define EMBERBOND_RETURN_GAME_H
/* ROM-only Return chapter. No resident OBJ cache and no full-save snapshot. */
typedef struct {short x,y;unsigned char hp,kind,phase;} ReturnEnemySpawn;
typedef struct {unsigned instance_id,scene,attempt,party;unsigned char index,slot,form,command,selected,family,key,stage,setting,casts,walk,replay;} ReturnTrialProof;
extern ReturnTrialProof return_game_trial;
extern unsigned return_game_revision,return_game_journal_selection;
int return_game_is_room(unsigned area);
unsigned return_game_spawn_count(unsigned area);
int return_game_spawn(unsigned area,unsigned spawn,int*x,int*y);
int return_game_can_enter(unsigned area);
int return_game_request_enter(unsigned area,unsigned spawn);
int return_game_take_transition(unsigned*area,unsigned*spawn);
int return_game_enter(unsigned area,unsigned spawn);
unsigned return_game_enemy_spawns(unsigned area,const ReturnEnemySpawn**out);
int return_game_geometry_solid(unsigned area,int x,int y);
int return_game_solid(int x,int y);
int return_game_clear_box(int x0,int y0,int x1,int y1);
int return_game_supercover(int x,int y,int tx,int ty);
void return_game_collision_inputs(unsigned out[3]);
/* Inclusive player-foot rectangles from the same live private mechanism state
 * used by solid(). At most two; no mutation, cache or extra dilation. */
unsigned return_game_collision_rects(short out[2][4]);
int return_game_is_sanctuary(void);
int return_game_event_pending(void);
unsigned return_game_prepare_event(void);
void return_game_cancel_event(void);
void return_game_reset(void);
void return_game_selection_changed(void);
/* Explicitly abandon a personal/repeat attempt. Ordinary journal or picker
 * viewing freezes simulation and does NOT call this; real selection edits
 * invalidate through selection_changed. Confirmed map petals persist. */
void return_game_menu_abandoned(void);
int return_game_input(unsigned pressed,unsigned held);
int return_game_interact(void);
int return_game_old_interact(void);
void return_game_tick(void);
void return_game_draw_actors(void);
void return_game_draw_overlay(void);
void return_game_draw_old_overlay(void);
int return_game_name(void);
int return_game_quest_text(void);
void return_game_draw_journal(void);
int return_game_menu_input(int pressed);
/* Engine calls at actual cast begin, channel3 for commands. Same API is used
 * by both new and legacy learned commands; no proximity callback grants proof.
 * Field targets are exact visible radius12 octagons: abs(dx)<=12,abs(dy)<=12,
 * abs(dx)+abs(dy)<=15. Caller must prove a live command-shape overlap and LOS.
 * At most8 targets. field_hit validates immutable caster, party, scene/attempt,
 * selected command and cast token; returns0 stale,1accepted,2 readable refusal. */
unsigned return_game_action_begin(unsigned channel);
int return_game_field_target(unsigned index,int*x,int*y,int*radius);
int return_game_field_hit(unsigned index,unsigned command,unsigned caster_id,unsigned form_id,unsigned token);
int return_game_power(unsigned command); /* hint only; no proof */
void return_actor(unsigned sprite,int x,int y);
#endif
