#ifndef EMBERBOND_NORTHERN_POWERS_H
#define EMBERBOND_NORTHERN_POWERS_H
/* Combat-only commands 13..22. These never dispatch field capabilities.
 * Call tick exactly once per active gameplay update, after pause/hitstop/picker
 * returns. Reset on room change, death and new/load game. All code stays in ROM. */
extern int northern_power_kind, northern_power_time, northern_power_form;
extern int northern_power_direction, northern_power_origin_x, northern_power_origin_y;
extern int northern_power_age, northern_power_cooldown, northern_power_cast_time;
int northern_power(unsigned command);
/* Field-only success feedback. Does not start combat, touch the shared lease,
 * change cooldown, or block gear. Refuses to overwrite a live combat snapshot. */
int northern_powers_feedback(unsigned command);
void northern_powers_tick(void);
void northern_powers_draw(void);
void northern_powers_reset(void);
/* Active effects OR still-live redirected friendly shots block equipment edits. */
int northern_powers_busy(void);

/* PIN (256 bytes) and WATER_DROP (64 bytes) are one mutually exclusive lease.
 * Regional command 9..11 must claim before changing state/uploading either tile;
 * release after expiry/reset. Neither claimant may overwrite a live effect,
 * including an earlier effect of its own. Draw only while its lease is held.
 * Generation changes on successful ownership changes; renderer caches may use
 * it to invalidate stale tile assumptions. No additional resident OBJ bytes. */
enum { NORTHERN_TILES_NONE, NORTHERN_TILES_REGIONAL, NORTHERN_TILES_NORTHERN, NORTHERN_TILES_SOUTHERN };
int northern_powers_tiles_claim(unsigned owner);
int northern_powers_tiles_release(unsigned owner);
unsigned northern_powers_tiles_owner(void);
unsigned northern_powers_tiles_generation(void);

/* REQUIRED after every new assignment to a Shot pool slot. A recycled slot is
 * a new projectile; merely changing ownership is not. A per-slot generation
 * plus cast ledger prevents repeat turns of the same live projectile. */
void northern_powers_shot_spawn(unsigned index);
int northern_powers_shot_is_reflected(unsigned index);
#endif
