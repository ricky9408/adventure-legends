#ifndef EMBERBOND_RETURN_POWERS_H
#define EMBERBOND_RETURN_POWERS_H
/* Commands91..105. ROM-only bounded cast. Engine owns shared cooldown.
 * Tick once only in active PLAY, after modal/save/picker/hitstop returns.
 * Reset on room/death/load/new game; never reset for selection/equipment edits. */
extern int return_power_kind,return_power_time,return_power_form;
extern int return_power_direction,return_power_origin_x,return_power_origin_y;
extern int return_power_age,return_power_cooldown,return_power_cast_time,return_power_phase;
int return_power(unsigned command);
int return_powers_busy(void);
int return_powers_cast_matches_selected(void);
/* Actual selection/party/form/command edits irreversibly invalidate field rights.
 * Combat, cast ages and cooldown continue from their immutable snapshot. */
void return_powers_selection_changed(void);
void return_powers_geometry_changed(void);
void return_powers_enemy_spawn(unsigned index);
void return_powers_shot_spawn(unsigned index);
void return_powers_reset(void);
void return_powers_tick(void);
void return_powers_draw(void);
/* One fresh cardinal edge in first8 updates selects facing or local turn side.
 * Fresh R(256) during a hinted live91/96/99 cast releases the CURRENT cast.
 * It never starts a second cast or changes expiry/cooldown. Parent must call
 * this before ability_cd rejects R and must not also start a cast that update. */
/* Result bit1(value1)=accepted direction; bit2(value2)=consumed fresh R. */
int return_powers_input(unsigned pressed);
int return_powers_can_aim(void);
int return_powers_can_release(void);
enum { RETURN_POWER_HINT_NONE,RETURN_POWER_HINT_FACE,RETURN_POWER_HINT_SIDE,
 RETURN_POWER_HINT_HEARTH_CHARGE,RETURN_POWER_HINT_HEARTH_RELEASE,
 RETURN_POWER_HINT_NOTCH_CATCH,RETURN_POWER_HINT_NOTCH_RELEASE,
 RETURN_POWER_HINT_CARRY_RELEASE,RETURN_POWER_HINT_QUIET_SIDE };
unsigned return_powers_hint(void);
/* -1 locomotion/recovery,0 anticipation,1 release,2 settle; simulation ages. */
int return_powers_companion_pose(void);
/* Invoke BEFORE shot movement, only with eligible=1 for explicit ordinary
 * hostile projectile provenance. Never pass boss/special/friendly shots as
 * eligible. Callback also independently verifies owner, life and coordinates.
 * Return1 consumes that exact current serial and caller skips its update. */
int return_powers_intercept_shot(unsigned index,int from_x,int from_y,
 int to_x,int to_y,int eligible);
/* Shared exact visible-pixel proof for native/host observation. Does not mutate
 * world/save or authorize a target. Targets use bevelled octagon radius<=16. */
int return_powers_overlap(int x,int y,int radius);
unsigned return_powers_cast_token(void);
unsigned return_powers_caster_id(void);
unsigned return_powers_moving_objects(void);
#endif
