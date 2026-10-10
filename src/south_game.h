#ifndef EMBERBOND_SOUTH_GAME_H
#define EMBERBOND_SOUTH_GAME_H
/* Original Sunlace chapter. No new OBJ cache, heap, framebuffer or IWRAM code.
 * Field actions bind selected active form capability, never equipped command.
 * Main route needs guaranteed base79 + base85, both before the intake gate. */
extern unsigned south_game_revision,south_game_journal_selection;
typedef struct SouthPuzzle { unsigned char mirror[2],shade; } SouthPuzzle;
typedef struct SouthBeam { short x1,y1,x2,y2; unsigned char end_kind; } SouthBeam;
enum { SOUTH_ACTION_MIRROR0=1,SOUTH_ACTION_MIRROR1,SOUTH_ACTION_SHADE,SOUTH_ACTION_RESET };
enum { SOUTH_BEAM_WALL=0,SOUTH_BEAM_MIRROR=1,SOUTH_BEAM_RECEIVER=2,SOUTH_BEAM_SHADE=3,SOUTH_BEAM_LOOP=4 };
extern SouthPuzzle south_game_puzzle;
extern unsigned char south_game_machine_stage,south_game_machine_ticks,south_game_machine_hp;
/* Pure finite optical state. Four segments/two mirrors maximum, repeated
 * node/direction detection, no movement/collision or saved objective mutation.
 * beam returns segment count; receivers returns shape-tagged two-bit mask. */
int south_puzzle_step(SouthPuzzle*,unsigned area,unsigned action);
unsigned south_puzzle_beam(const SouthPuzzle*,unsigned area,SouthBeam out[4]);
unsigned south_puzzle_receivers(const SouthPuzzle*,unsigned area);
int south_puzzle_solved(const SouthPuzzle*,unsigned area);
typedef struct SouthEnemySpawn { short x,y; unsigned char hp,kind,phase; } SouthEnemySpawn;
/* Returns0 outside rooms31/33. HP is existing whole-heart enemy HP. */
unsigned south_game_enemy_spawns(unsigned area,const SouthEnemySpawn **spawns);
int south_game_is_room(unsigned area);
int south_game_enter(unsigned area,unsigned spawn);
/* Engine entry: sync chapter and perform any expedition reset first; request
 * before changing room/scene. 0=reject,2=queued,1=one-use ready token armed.
 * Warm EVENT_PENDING pages, prepare fixed bounded slices, restore source state,
 * commit through the job's own synchronous engine call. The adapter consumes an exact
 * full-state proof after only idempotent engine setup. Direct entry stays strict. */
int south_game_request_enter(unsigned area,unsigned spawn);
int south_game_enter_pending(void);
unsigned south_game_prepare_enter(void);
int south_game_commit_enter(void);
void south_game_cancel_enter(void);
int south_game_solid(int x,int y);
int south_game_interact(void);
/* 0: no field target; 1: success; 2: rejected target, no cooldown/resource. */
int south_game_power(unsigned command);
void south_game_tick(void);
/* Explicit reset clears transient trial proofs, never completed save bits.
 * Ordinary entry resets room mechanisms but preserves pinned cross-room trial
 * evidence. Call reset after death/load/new game, before accepting input. */
void south_game_reset(void);
/* Exact old-state Southern rest validation. Anchor interaction requests first;
 * engine warms both EVENT_PENDING pages, prepares one bounded slice/update,
 * restores PLAY, then commits once. Commit performs the anchor/heal/checkpoint
 * and existing dialogue/save request. Cancel on selection or any room entry.
 * There is no caller-supplied validated flag or additional Save5 copy. */
int south_game_request_rest(void);
int south_game_rest_pending(void);
unsigned south_game_prepare_rest(void);
int south_game_commit_rest(void);
void south_game_cancel_rest(void);
void south_game_draw_actors(void);
void south_game_draw_overlay(void);
int south_game_name(void);
int south_game_quest_text(void);
void south_game_draw_journal(void);
int south_game_menu_input(int pressed); /* journal tab7 */
int south_game_target(int*x,int*y,int*radius);
int south_game_weapon_hit(unsigned weapon_class,int x,int y,unsigned damage_q4);
/* Shared parent bridges; sprite keys4096+id, existing20 visible region slots. */
void south_actor(unsigned sprite_index,int x,int y);
void region_form_actor(unsigned form,int x,int y);
void game_health_fill(void);
unsigned game_weapon_class(void);
void game_north_hurt(unsigned damage_q4);
/* Engine-private typed quest action queue. Seal once after the action, freeze
 * input, prepare bounded frames, restore PLAY and commit once. */
int south_game_quest_pending(void);
int south_game_quest_seal(void);
unsigned south_game_quest_prepare(void);
int south_game_quest_commit(void);
void south_game_quest_cancel(void);
#endif
