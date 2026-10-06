#ifndef EMBERBOND_MAGMA_POWERS_H
#define EMBERBOND_MAGMA_POWERS_H
/* Commands43..66: one snapshotted cast, <=3 moving objects, six target bits.
 * Tick ONLY after dialogue/menu/picker/hitstop early returns. Draw never ticks.
 * Reset on room/death/load/new-game, never on a selection change. */
extern int magma_power_kind,magma_power_time,magma_power_form;
extern int magma_power_direction,magma_power_origin_x,magma_power_origin_y;
extern int magma_power_age,magma_power_cooldown,magma_power_cast_time,magma_power_phase;
int magma_power(unsigned command);
/* -1/+1 chooses Cinder Tilt side and Trellis Bend turn. */
int magma_power_side(unsigned command,int side);
/* One startup-only retarget of Cone Drop; exact original expiration/cooldown. */
int magma_powers_can_aim(void);
int magma_powers_aim(void);
enum { MAGMA_HINT_NONE, MAGMA_HINT_LANDING };
unsigned magma_powers_hint(void);
int magma_powers_feedback(unsigned command);
void magma_powers_tick(void);
void magma_powers_draw(void);
void magma_powers_reset(void);
int magma_powers_busy(void);
int magma_powers_cast_matches_selected(void);
/* REQUIRED whenever actual solid inputs change, before tick/draw/hit hooks.
 * Invalidates exact scenery geometry only, preserving age/cooldown/hit ledger. */
void magma_powers_geometry_changed(void);
/* Every new identity in enemy pool, including room bulk-spawn and reuse. */
void magma_powers_enemy_spawn(unsigned enemy_index);
/* Ordinary melee contact only: do not route boss, ranged, or generic damage. */
int magma_powers_melee_guard(unsigned enemy_index,int attack_x,int attack_y);
/* Before a hostile shot moves. eligible=1 ONLY for ordinary hostile shots,
 * never boss/special shots. Return1 consumes the shot; caller skips its update. */
int magma_powers_intercept_shot(unsigned shot_index,int from_x,int from_y,
                               int to_x,int to_y,int eligible);
#endif
