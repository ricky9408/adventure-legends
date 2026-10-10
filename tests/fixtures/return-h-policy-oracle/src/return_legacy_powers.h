#ifndef EMBERBOND_RETURN_LEGACY_POWERS_H
#define EMBERBOND_RETURN_LEGACY_POWERS_H
/* ROM-only Return-room bridge. No historical damage, timing, tile ownership or
 * cooldown is changed. Before an actual old cast call begin(command), then
 * confirm(handler_succeeded, exact_fire_shot_return_or_minus_one). A failed
 * begin/confirm can never rebind an already-live effect. The Fire1 index MUST
 * come directly from this cast's ordinary engine fire_shot call, not a search.
 * Call cancel on every actual selection/form/command/party edit, summon recall,
 * and personal-proof menu abandonment; reset on room/death/new/load. */
unsigned return_legacy_begin(unsigned command);
void return_legacy_confirm(int success,int shot_index);
void return_legacy_cancel(void);
void return_legacy_reset(void);
/* Exactly once after old effect/shot movement during active PLAY; no modal,
 * picker, save, hitstop or render-only invocations. Defensive guards freeze
 * modal/hitstop calls, but the engine must still revoke abandoned proof. */
void return_legacy_tick(void);
/* Only the explicit finite Return-only base2..4 field stroke is drawn here.
 * Existing powers keep their original renderer. No simulation in callbacks. */
void return_legacy_draw(void);
/* Observational exact opaque-pixel overlap against the field octagon, with
 * live wall/LOS checks. Does not call world proof or mutate state. */
int return_legacy_overlap(int x,int y,int radius);
unsigned return_legacy_cast_token(void);
unsigned return_legacy_caster_id(void);
#endif
