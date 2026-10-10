#ifndef EMBERBOND_COVENANTS_GAME_H
#define EMBERBOND_COVENANTS_GAME_H
/* Final chapter world authority. All durable changes pass through the bounded
 * typed quest transaction. Cast/escort proofs are scene-local and never saved. */
typedef struct { short x,y; unsigned char hp,kind,phase; } CovenantsEnemySpawn;
extern unsigned covenants_game_revision,covenants_game_journal_selection;
int covenants_game_is_room(unsigned area);
unsigned covenants_game_spawn_count(unsigned area);
int covenants_game_spawn(unsigned area,unsigned spawn,int *x,int *y);
int covenants_game_can_enter(unsigned area);
/* Includes the preserved source-specific checkpoint and anchor gates. */
int covenants_game_route_allowed(unsigned area,unsigned spawn);
int covenants_game_request_enter(unsigned area,unsigned spawn);
int covenants_game_take_transition(unsigned *area,unsigned *spawn);
int covenants_game_enter(unsigned area,unsigned spawn);
unsigned covenants_game_enemy_spawns(unsigned area,const CovenantsEnemySpawn **out);
int covenants_game_geometry_solid(unsigned area,int x,int y);
int covenants_game_solid(int x,int y);
int covenants_game_clear_box(int x0,int y0,int x1,int y1);
int covenants_game_supercover(int x,int y,int tx,int ty);
void covenants_game_collision_inputs(unsigned out[3]);
int covenants_game_collision_rects(int x0,int y0,int x1,int y1,short out[][4],unsigned cap);
unsigned covenants_game_scene_generation(void);
unsigned covenants_game_attempt_generation(void);
unsigned covenants_game_geometry_revision(void);
int covenants_game_is_sanctuary(void);
int covenants_game_event_pending(void);
unsigned covenants_game_prepare_event(void);
void covenants_game_cancel_event(void);
void covenants_game_reset(void);
void covenants_game_prepare_old_scene(void);
void covenants_game_selection_changed(void);
void covenants_game_menu_abandoned(void);
int covenants_game_input(unsigned pressed,unsigned held);
int covenants_game_interact(void);
int covenants_game_old_interact(void);
void covenants_game_tick(void);
void covenants_game_tick_old(void);
void covenants_game_draw_actors(void);
void covenants_game_draw_overlay(void);
void covenants_game_draw_old_actors(void);
void covenants_game_draw_old_overlay(void);
int covenants_game_name(void);
int covenants_game_quest_text(void);
void covenants_game_draw_journal(void);
int covenants_game_menu_input(int pressed);
unsigned covenants_game_action_begin(unsigned channel);
void covenants_game_revoke_cast(unsigned token);
int covenants_game_field_target(unsigned index,int *x,int *y,int *radius);
int covenants_game_field_hit(unsigned index,unsigned command,unsigned caster,
                             unsigned form,unsigned token);
int covenants_game_power(unsigned command);
/* Engine-owned OAM upload/culling and ordinary wave spawn callbacks. */
void covenants_actor(unsigned sprite,int x,int y);
int game_covenants_spawn_wave(unsigned wave);
unsigned game_covenants_enemies_alive(void);
#endif
