#ifndef EMBERBOND_MAGMA_GAME_H
#define EMBERBOND_MAGMA_GAME_H
/* ROM-only chapter implementation. Actual engine foot is radius5. All props
 * occupy12x12 raw pixels; slide rests use24x18 steps and never boundary lanes.
 * New permanent OBJ and IWRAM allocation:0. The parent streams16px actors. */
typedef struct MagmaPuzzle { unsigned char cell[2],heat,brace; } MagmaPuzzle;
typedef struct MagmaEnemySpawn { short x,y; unsigned char hp,kind,phase; } MagmaEnemySpawn;
extern MagmaPuzzle magma_game_puzzle;
extern unsigned magma_game_revision,magma_game_journal_selection;
extern unsigned char magma_game_machine_stage,magma_game_machine_ticks,magma_game_machine_hp;
int magma_game_is_room(unsigned area);
unsigned magma_game_spawn_count(unsigned area);
int magma_game_spawn(unsigned area,unsigned index,int *x,int *y);
int magma_game_can_enter(unsigned area);
int magma_game_enter(unsigned area,unsigned spawn);
/* Active general entry only; cold restoration and the shell-lift retain
 * their existing exact paths. Request after deterministic source sync and
 * expedition reset but before scene/pose mutation. 0 denied,2 queued,1 only
 * inside the adapter-owned synchronous commit callback. */
int magma_game_request_enter(unsigned area,unsigned spawn);
int magma_game_enter_pending(void);
unsigned magma_game_prepare_enter(void);
int magma_game_commit_enter(void);
void magma_game_cancel_enter(void);
/* Engine-only bounded room46 -> room38:4 shell-lift orchestration. Request
 * BEFORE any transition mutation: 0 denied, 1 scoped commit, 2 queued.
 * Freeze in EVENT_PENDING(10), warm both pages, then prepare one slice/update.
 * DONE still owns scratch: restore original mode and call commit immediately.
 * Commit performs the exact comparison and invokes enter_room itself; do not
 * issue a second transition. Cancel on a different entry, selection, reset,
 * death or load. No API grants an arbitrary trusted/validated flag. */
int magma_game_request_return(void);
int magma_game_return_pending(void);
unsigned magma_game_prepare_return(void);
int magma_game_commit_return(void);
void magma_game_cancel_return(void);
/* Branch-invitation queue, advanced once per frozen EVENT_PENDING update.
 * DONE: restore PLAY and call commit_event immediately for presentation/save.
 * B, a redirected transition, scene reset, death or load cancels the request. */
int magma_game_event_pending(void);
unsigned magma_game_prepare_event(void);
int magma_game_commit_event(void);
void magma_game_cancel_event(void);
unsigned magma_game_enemy_spawns(unsigned area,const MagmaEnemySpawn **out);
/* Exact baked static collision; same radius-five intervals as production.
 * Dynamic fingerprint exposes every prop position changing the predicate,
 * independent of decorative animation, power cooldown or quest text. */
int magma_game_geometry_solid(unsigned area,int x,int y);
int magma_game_solid(int x,int y);
/* Inclusive exact empty-box proof in large rooms38/39. False elsewhere keeps
 * callers on their original pixel collision path, including small puzzles. */
int magma_game_clear_box(int x0,int y0,int x1,int y1);
void magma_game_collision_inputs(unsigned out[3]);
void magma_puzzle_reset(MagmaPuzzle *,unsigned area);
unsigned magma_puzzle_count(unsigned area);
int magma_puzzle_position(const MagmaPuzzle *,unsigned area,unsigned prop,int*x,int*y);
int magma_puzzle_solid(const MagmaPuzzle *,unsigned area,int x,int y);
/* Direction0 down,1 up,2 left,3 right; player endpoints optional. Move checks
 * every pixel of both swept footprints and permits pulling without crushing.
 * Returns1 changed,0 blocked,-1 invalid, never mutates on failure. */
int magma_puzzle_move(MagmaPuzzle *,unsigned area,unsigned prop,unsigned direction,
 int player_x,int player_y,int *out_x,int *out_y);
int magma_puzzle_charge(MagmaPuzzle *,unsigned area); /* brick at input only */
int magma_puzzle_brace(MagmaPuzzle *,unsigned area); /* exact baffle/shoe rests */
int magma_puzzle_solved(const MagmaPuzzle *,unsigned area);
/* PLAY-only before movement/roll/weapon input.1 owns input while grabbing.
 * A/B release; arrow pressed performs one slide; held arrows are not repeated.
 * Parent must warp fractional player coordinates to the new px/py on success. */
int magma_game_input(unsigned pressed,unsigned held);
int magma_game_grabbed(void);
int magma_game_interact(void);
int magma_game_power(unsigned command); /*0 no target,1 success,2 rejected*/
void magma_game_tick(void);
/* Death/load/new game: clears incomplete participant-bound trial evidence.
 * Ordinary enter resets arrangements but preserves chosen multiroom proof. */
void magma_game_reset(void);
/* Rest queues an exact typed anchor validation for a cached SAVE_PENDING(6)
 * update. The requested checkpoint is3; campaign.spawn retains its prior legal
 * value until preparation succeeds. The synchronous prepare helper preserves
 * the original direct contract; active engines warm both saving-notice pages
 * and use the bounded step API below before the ordinary snapshot/write.
 * Return1 only after real magma_anchor CHANGED/UNCHANGED; failure0 consumes the
 * queue and must surface save failure. Never bump a bitmap/UI revision here.
 * No queue: pending returns0 and prepare returns0. Death/load/new reset cancels. */
int magma_game_save_prepare_pending(void);
/* Pre-writer entry redirection only: revoke the owned proof/queue and restore
 * the old runtime checkpoint. Engine restores its old caller mode separately. */
void magma_game_cancel_save_prepare(void);
int magma_game_prepare_save(void);
/* Engine SAVE_PENDING stage2 holds on BUSY; DONE advances to the ordinary
 * save writer; FAILED consumes/revokes the queue and shows save failure.
 * The synchronous API above remains the exact direct/oracle path. */
unsigned magma_game_prepare_save_step(void);
void magma_game_draw_actors(void);
void magma_game_draw_overlay(void);
int magma_game_name(void);
int magma_game_quest_text(void);
void magma_game_draw_journal(void);
int magma_game_menu_input(int pressed); /* journal tab8,24 cards */
int magma_game_target(int*x,int*y,int*radius);
int magma_game_weapon_hit(unsigned weapon_class,int x,int y,unsigned damage_q4,
 unsigned channel,unsigned token);
/* Each fresh action owns a nonzero serial in its independent channel:
 * 0 melee,1 arrow slot0,2 arrow slot1,3 companion cast. Store the returned
 * token with that action. Retargeting never calls begin; another action in
 * another channel cannot erase the hit. Death/load/entry invalidate tokens. */
unsigned magma_game_action_begin(unsigned channel);
int magma_game_command_hit(int x,int y,unsigned damage_q4,unsigned token);
/* Existing bounded bridges plus live enemy overlap check. No allocator. */
void magma_actor(unsigned sprite_index,int x,int y);
void region_form_actor(unsigned form,int x,int y);
void game_health_fill(void);
unsigned game_weapon_class(void);
void game_north_hurt(unsigned damage_q4);
int game_magma_actor_overlap(int x,int y,int radius);
#endif
