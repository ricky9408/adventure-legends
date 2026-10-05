#ifndef EMBERBOND_REGION_GAME_H
#define EMBERBOND_REGION_GAME_H
/* Native six-room runtime. Persistence belongs only to regional_quests/save5.
 * Engine bridge contract:
 * - Call enter after validating the target, before final Q8/camera initialization.
 *   This function also assigns room, px, py, checkpoint_spawn and visits the room.
 * - solid already tests a +/-5px square foot: never expand it a second time.
 * - interact is A only; power is an actual selected/summoned command use.
 * - tick is active PLAY only; it handles directional exits and real roll sensors.
 * - Call draw_overlay after base bitmap, draw_actors from the native OBJ pass.
 * - region_game_revision must participate in the bitmap cache key.
 * - Grove return enter_room(1,3) is transient: engine places (168,264), then
 *   normalizes checkpoint_spawn to the supported Grove spawn0 before saving.
 */
extern unsigned region_game_revision;
/* Stable, volatile-only QA symbols; no positions enter the save codec. */
extern short region_game_crates[2][2];
extern unsigned char region_game_foundry_step,region_game_pool_levels[2],region_game_valves[2];
extern unsigned char region_game_garden_step;
extern unsigned region_game_journal_selection;
int region_game_is_room(unsigned area);
int region_game_enter(unsigned area,unsigned spawn);
int region_game_solid(int x,int y);
int region_game_interact(void);
int region_game_power(unsigned command);
void region_game_tick(void);
void region_game_draw_actors(void);
void region_game_draw_overlay(void);
int region_game_name(void);
int region_game_quest_text(void);
void region_game_draw_journal(void);
int region_game_menu_input(int pressed);
/* Pure hit-test target query; false outside town. Hit callback is permitted
 * ONLY after engine-confirmed active melee/arrow collision, never on A press.
 * x/y are the collision point on the target. class must match current gear. */
int region_game_target(int *x,int *y,int *radius);
int region_game_practice_hit(unsigned weapon_class,int x,int y);
/* Geometry/puzzle queries also used by finite-state host verification. */
unsigned region_game_plate_mask(void);
int region_game_try_push(int x,int y,unsigned facing);
void region_game_reset(void);
/* Parent-provided bridge functions. All actor coordinates are world centers.
 * Cache native 16px pixels in OBJ; clipping is parent-owned. */
void region_actor(unsigned sprite_index,int x,int y);
void region_form_actor(unsigned form,int x,int y);
int game_region_entry_safe(void);
void game_health_fill(void);
unsigned game_weapon_class(void);
void game_region_warp(int x,int y);
#endif
