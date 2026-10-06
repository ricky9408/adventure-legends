#ifndef EMBERBOND_UNDERWATER_POWERS_H
#define EMBERBOND_UNDERWATER_POWERS_H
/* Commands67..90, ROM only; one bounded cast, no general projectile authority.
 * Invoke tick exactly once after modal/selector/save/hitstop early returns.
 * Reset on room/death/load/new game, NEVER on party/equipment/command changes.
 * ability_cd is engine-owned and must survive party/gear changes. */
extern int underwater_power_kind,underwater_power_time,underwater_power_form;
extern int underwater_power_direction,underwater_power_origin_x,underwater_power_origin_y;
extern int underwater_power_age,underwater_power_cooldown,underwater_power_cast_time,underwater_power_phase;
int underwater_power(unsigned command);
/* First8 gameplay updates only, one cardinal direction edge. Pass GBA pressed
 * keys (RIGHT16 LEFT32 UP64 DOWN128) BEFORE movement. Does not consume movement,
 * restart cast, change origin/identity or reset any lifetime/cooldown. */
int underwater_powers_input(unsigned pressed);
int underwater_powers_can_aim(void);
unsigned underwater_powers_hint(void); /*0 none,1 side,2 corner,3 axis*/
int underwater_powers_feedback(unsigned command); /*presentation only*/
int underwater_powers_busy(void);
int underwater_powers_cast_matches_selected(void);
/* Read-only selected-instance pose: -1 walking,0 anticipation,1 release,
 * 2 settle. Uses simulation age, so every paused engine mode freezes it. */
int underwater_powers_companion_pose(void);
void underwater_powers_tick(void);
void underwater_powers_draw(void);
void underwater_powers_reset(void);
/* Every actual collision mutation, before hit/draw hooks; preserves receipts. */
void underwater_powers_geometry_changed(void);
/* Every enemy pool identity assignment, including bulk room spawn/reuse. */
void underwater_powers_enemy_spawn(unsigned index);
/* Actual selection/party mapping/form/equipped-command edits, including edits
 * inside a frozen selector: invalidate field rights even if changed back before
 * the next tick. Does not end combat, reset ages, or refund cooldown. */
void underwater_powers_selection_changed(void);
/* No Underwater command reflects/intercepts shots, grants a guard, roots,
 * staggers, retimes windups, or changes bosses' vulnerability. Engine must NOT
 * route hostile/friendly shots or generic damage through this module. */
#endif
