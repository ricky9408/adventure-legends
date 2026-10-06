#ifndef EMBERBOND_UNDERWATER_GAME_H
#define EMBERBOND_UNDERWATER_GAME_H
/* All implementation is ROM text. Room/transient proof is bounded and never
 * serialized. New resident OBJ allocation: zero; reuse regional streamed20. */
typedef struct { short x,y; unsigned char hp,kind,phase; } UnderwaterEnemySpawn;
typedef struct {
 unsigned char mode,rotation,ballast,baffle[2],echo,walk,aux;
} UnderwaterPuzzle;
typedef struct {
 unsigned instance_id,generation,party_signature;
 unsigned char index,slot,form,family,key,source,command,selected_party;
 unsigned char setting[4],casts,walk,order,failed;
} UnderwaterTrialProof;
extern UnderwaterPuzzle underwater_game_puzzle;
extern UnderwaterTrialProof underwater_game_trial;
extern unsigned underwater_game_revision,underwater_game_journal_selection;
extern unsigned char underwater_game_guardian_stage,underwater_game_guardian_ticks,underwater_game_guardian_hits;
int underwater_game_is_room(unsigned area);
unsigned underwater_game_spawn_count(unsigned area);
int underwater_game_spawn(unsigned area,unsigned spawn,int*x,int*y);
int underwater_game_can_enter(unsigned area);
int underwater_game_enter(unsigned area,unsigned spawn);
/* Call before any engine room/checkpoint mutation:0deny,1ready,2queued.
 * A new visit is committed while the old scene/checkpoint remains intact. */
int underwater_game_request_enter(unsigned area,unsigned spawn);
int underwater_game_take_transition(unsigned*area,unsigned*spawn);
int underwater_game_event_pending(void);
unsigned underwater_game_prepare_event(void); /* SAVE5_BUSY/DONE/FAILED */
void underwater_game_cancel_event(void);
unsigned underwater_game_enemy_spawns(unsigned area,const UnderwaterEnemySpawn**out);
int underwater_game_geometry_solid(unsigned area,int x,int y);
int underwater_game_solid(int x,int y);
/* Inclusive box is certified empty only in current Underwater geometry. */
int underwater_game_clear_box(int x0,int y0,int x1,int y1);
/* Exact endpoint-inclusive ray, bounded to0..1023 and Manhattan160. Returns
 * -1 outside Underwater so callers preserve other chapters' collision policy. */
int underwater_game_supercover(int x,int y,int tx,int ty);
void underwater_game_collision_inputs(unsigned out[3]);
void underwater_puzzle_reset(UnderwaterPuzzle*,unsigned area);
int underwater_puzzle_solid(const UnderwaterPuzzle*,unsigned area,int x,int y);
/* Reversible tagged toggle refuses changed-solid overlap, never shoves hero. */
int underwater_puzzle_toggle(UnderwaterPuzzle*,unsigned area,unsigned target,int px,int py);
int underwater_puzzle_solved(const UnderwaterPuzzle*,unsigned area);
int underwater_game_input(unsigned pressed,unsigned held);
int underwater_game_interact(void);
int underwater_game_power(unsigned command); /* feedback only, grants no proof */
void underwater_game_tick(void);
void underwater_game_reset(void);
void underwater_game_selection_changed(void);
int underwater_game_save_prepare_pending(void);
int underwater_game_prepare_save(void);
void underwater_game_draw_actors(void);
void underwater_game_draw_overlay(void);
int underwater_game_name(void);
int underwater_game_quest_text(void);
void underwater_game_draw_journal(void);
int underwater_game_menu_input(int pressed);
/* Cast owner iterates at most8 live20px field targets and tests its actual
 * active shape/LOS before hit. Passing proximity alone does not authorize it.
 * token is returned at cast begin. Any room/attempt/selection change fails. */
int underwater_game_field_target(unsigned index,int*x,int*y,int*radius);
int underwater_game_field_hit(unsigned index,unsigned command,unsigned caster_id,unsigned form_id,unsigned token);
unsigned underwater_game_action_begin(unsigned channel);
int underwater_game_target(int*x,int*y,int*radius);
int underwater_game_weapon_hit(unsigned weapon_class,int x,int y,unsigned damage_q4,unsigned channel,unsigned token);
int underwater_game_command_hit(int x,int y,unsigned damage_q4,unsigned token);
/* Engine bridges, shared with prior ROM-only chapter modules. */
void underwater_actor(unsigned sprite,int x,int y);
void region_form_actor(unsigned form,int x,int y);
void game_health_fill(void);
void game_north_hurt(unsigned damage_q4);
#endif
