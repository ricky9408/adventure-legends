#ifndef EMBERBOND_NORTH_GAME_H
#define EMBERBOND_NORTH_GAME_H
/* Native chapter: stationary interiors and full240x160 cropped exteriors.
 * enter validates gates/spawns and records visits; call before Q8/camera setup.
 * solid includes the five-pixel player foot. Actor centers are world pixels.
 * No physics, heap, private framebuffer, save snapshot or OBJ allocation. */
extern unsigned north_game_revision,north_game_journal_selection;
typedef struct NorthPuzzle { unsigned char rail,cart[2],weight; } NorthPuzzle;
enum { NORTH_ACTION_TURN=1,NORTH_ACTION_REEL,NORTH_ACTION_WEIGHT,NORTH_ACTION_RESET };
extern NorthPuzzle north_game_puzzle;
extern unsigned char north_game_machine_stage,north_game_machine_ticks,north_game_machine_hp;
/* Pure bounded mechanism transition. player position is swept for cargo safety.
 * -1 blocked/invalid,0 no change,1 changed. No saved objectives are touched. */
int north_puzzle_step(NorthPuzzle*,unsigned area,unsigned action,int player_x,int player_y);
int north_puzzle_solved(const NorthPuzzle*,unsigned area);
int north_game_is_room(unsigned area);
int north_game_enter(unsigned area,unsigned spawn);
int north_game_solid(int x,int y);
int north_game_interact(void);
int north_game_power(unsigned command);
void north_game_tick(void);
void north_game_reset(void);
void north_game_draw_actors(void);
void north_game_draw_overlay(void);
int north_game_name(void);
int north_game_quest_text(void);
void north_game_draw_journal(void);
int north_game_menu_input(int pressed);
/* One target, reserved attack-ledger bit8. Parent calls hit ONLY on a confirmed
 * melee/arrow overlap and deduplicates per attack. Coordinates/radius are the
 * exposed weak point, never a static wall. All damage uses Q4 heart units. */
int north_game_target(int*x,int*y,int*radius);
int north_game_weapon_hit(unsigned weapon_class,int x,int y,unsigned damage_q4);
/* Parent bridge: reuse its bounded20-slot regional OBJ cache, with a distinct
 * sprite-key namespace; do not allocate a second cache. */
void north_actor(unsigned sprite_index,int x,int y);
void region_form_actor(unsigned form,int x,int y);
int game_region_entry_safe(void);
void game_health_fill(void);
unsigned game_weapon_class(void);
void game_north_hurt(unsigned damage_q4);
#endif
