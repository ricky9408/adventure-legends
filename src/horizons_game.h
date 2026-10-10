#ifndef EMBERBOND_HORIZONS_GAME_H
#define EMBERBOND_HORIZONS_GAME_H
/* ROM-only chapter orchestration. No roster scan or save clone in PLAY. */
typedef struct {short x,y;unsigned char hp,kind,phase;} HorizonsEnemySpawn;
extern unsigned horizons_game_revision,horizons_game_journal_selection;
int horizons_game_is_room(unsigned area);
unsigned horizons_game_spawn_count(unsigned area);
int horizons_game_spawn(unsigned area,unsigned spawn,int*x,int*y);
int horizons_game_can_enter(unsigned area);
/* Includes the preserved source-specific checkpoint and anchor gates. */
int horizons_game_route_allowed(unsigned area,unsigned spawn);
int horizons_game_request_enter(unsigned area,unsigned spawn);
int horizons_game_take_transition(unsigned*area,unsigned*spawn);
int horizons_game_enter(unsigned area,unsigned spawn);
unsigned horizons_game_enemy_spawns(unsigned area,const HorizonsEnemySpawn**out);
int horizons_game_geometry_solid(unsigned area,int x,int y);
int horizons_game_solid(int x,int y);
int horizons_game_clear_box(int x0,int y0,int x1,int y1);
int horizons_game_supercover(int x,int y,int tx,int ty);
void horizons_game_collision_inputs(unsigned out[3]);
int horizons_game_is_sanctuary(void);
int horizons_game_event_pending(void);
unsigned horizons_game_prepare_event(void);
void horizons_game_cancel_event(void);
void horizons_game_reset(void);
void horizons_game_selection_changed(void);
void horizons_game_menu_abandoned(void);
int horizons_game_input(unsigned pressed,unsigned held);
int horizons_game_interact(void);
int horizons_game_old_interact(void);
void horizons_game_tick(void);
void horizons_game_draw_actors(void);
void horizons_game_draw_overlay(void);
void horizons_game_draw_old_overlay(void);
int horizons_game_name(void);
int horizons_game_quest_text(void);
void horizons_game_draw_journal(void);
int horizons_game_menu_input(int pressed);
unsigned horizons_game_action_begin(unsigned channel);
void horizons_game_revoke_cast(unsigned token);
int horizons_game_field_target(unsigned index,int*x,int*y,int*radius);
int horizons_game_field_hit(unsigned index,unsigned command,unsigned caster_id,unsigned form_id,unsigned token);
int horizons_game_power(unsigned command);
void horizons_actor(unsigned sprite,int x,int y);
#endif
