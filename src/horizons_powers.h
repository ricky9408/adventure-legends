#ifndef EMBERBOND_HORIZONS_POWERS_H
#define EMBERBOND_HORIZONS_POWERS_H
/* Sixteen finite commands106..121. ROM-only; shared cooldown belongs to engine.
 * Tick/input only in active PLAY after modal, journal, held-L and hitstop gates.
 * Merely viewing a picker/journal must never call selection_changed/reset. */
extern int horizons_power_kind,horizons_power_time,horizons_power_form;
extern int horizons_power_direction,horizons_power_origin_x,horizons_power_origin_y;
extern int horizons_power_age,horizons_power_cooldown,horizons_power_cast_time,horizons_power_phase;
int horizons_power(unsigned command);
int horizons_powers_busy(void);
int horizons_powers_cast_matches_selected(void);
void horizons_powers_selection_changed(void);
void horizons_powers_geometry_changed(void);
void horizons_powers_enemy_spawn(unsigned index);
void horizons_powers_shot_spawn(unsigned index);
void horizons_powers_reset(void);
void horizons_powers_tick(void);
void horizons_powers_draw(void);
/* Result1 accepts one fresh cardinal edge, result2 consumes fresh R for the
 * current cast. Call before shared cooldown rejects R; never also start a cast.
 * Direction/side can change once in first8 updates. Identity, command, origin,
 * expiry and action token remain the initial snapshot. */
int horizons_powers_input(unsigned pressed);
int horizons_powers_can_aim(void);
int horizons_powers_can_release(void);
enum { HORIZONS_POWER_HINT_NONE,HORIZONS_POWER_HINT_FACE,HORIZONS_POWER_HINT_SIDE,
 HORIZONS_POWER_HINT_GATHER,HORIZONS_POWER_HINT_RELEASE,HORIZONS_POWER_HINT_CATCH,
 HORIZONS_POWER_HINT_HOLD,HORIZONS_POWER_HINT_TWO_BEATS };
unsigned horizons_powers_hint(void);
int horizons_powers_companion_pose(void);
/* Explicit ordinary hostile provenance only, BEFORE projectile movement.
 * Independently validates owner, serial, life, exact segment and one-use guard. */
int horizons_powers_intercept_shot(unsigned index,int from_x,int from_y,
 int to_x,int to_y,int eligible);
/* Exact live drawn pixels intersecting target octagon, with supercover LOS.
 * This read-only observation never authorizes a reward on its own. */
int horizons_powers_overlap(int x,int y,int radius);
unsigned horizons_powers_cast_token(void);
unsigned horizons_powers_caster_id(void);
unsigned horizons_powers_moving_objects(void);
/* 0 outside collision window,1 first leg/pulse/gather,2 second/return/release.
 * Field-target dispatch is once per target per beat, always the same token. */
unsigned horizons_powers_beat(void);
unsigned horizons_powers_release_phase(void);
#endif
