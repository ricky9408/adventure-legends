#ifndef EMBERBOND_SOUTHERN_POWERS_H
#define EMBERBOND_SOUTHERN_POWERS_H
/* Commands23..42. One cast, <=3 internal projectiles, <=6 target ledger entries.
 * Tick once only on active gameplay, AFTER modal/hitstop/selector early returns.
 * Reset at room/death/new/load. Global ability_cd is not reset on party swap. */
extern int southern_power_kind,southern_power_time,southern_power_form;
extern int southern_power_direction,southern_power_origin_x,southern_power_origin_y;
extern int southern_power_age,southern_power_cooldown,southern_power_cast_time;
extern int southern_power_phase;
int southern_power(unsigned command);
/* Explicit -1=left / +1=right relative to the snapshotted facing, for command32. */
int southern_power_side(unsigned command,int side);
int southern_powers_can_aim(void);
int southern_powers_aim(void);
enum { SOUTHERN_HINT_NONE, SOUTHERN_HINT_OTHER_SIDE, SOUTHERN_HINT_SECOND_TARGET };
unsigned southern_powers_hint(void);
int southern_powers_feedback(unsigned command);
void southern_powers_tick(void);
void southern_powers_draw(void);
void southern_powers_reset(void);
/* REQUIRED after any collision/topology mutation, before subsequent power
 * damage or rendering. Include field/manual interactions, doors and bridges
 * in all old/new rooms. Room/reset and new casts invalidate internally.
 * Does not alter lifetime, hit ledger, cooldown or lease. */
void southern_powers_geometry_changed(void);
int southern_powers_busy(void);
/* Render-only Leafbound sidestep/recovery; never mutate player/follower state. */
int southern_powers_companion_pose(int *x,int *y);
int southern_powers_cast_matches_selected(void);
/* Call on EVERY new pool-slot identity, including bulk room spawning. */
void southern_powers_enemy_spawn(unsigned enemy_index);
/* ONLY eligible ordinary melee attacks may ask to consume a directional guard.
 * attack_x/y is the attacker's world position. Never call from generic damage. */
int southern_powers_melee_guard(unsigned enemy_index,int attack_x,int attack_y);
/* ONLY ordinary AI windup starts. Bosses must never pass through this hook. */
unsigned southern_powers_windup(unsigned enemy_index,unsigned base_updates);
/* Ordinary walking AI asks for a temporary approach target. No teleport/push. */
int southern_powers_approach(unsigned enemy_index,int *target_x,int *target_y);
/* ONLY after actual ordinary sword/lance/arrow damage has been confirmed.
 * Spell/status/echo damage must not notify this hook. */
void southern_powers_weapon_hit(unsigned enemy_index);
/* Before moving a hostile shot. eligible=1 only for a normal enemy projectile,
 * never a boss/special shot. Return1 means consumed; caller skips its update. */
int southern_powers_intercept_shot(unsigned shot_index,int from_x,int from_y,
                                  int to_x,int to_y,int eligible);
#endif
