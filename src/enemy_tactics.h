#ifndef ADVENTURE_ENEMY_TACTICS_H
#define ADVENTURE_ENEMY_TACTICS_H
#include "enemy_types.h"
/* Kind 1 also names the early cave chasers; only the court owns this behavior. */
static inline int enemy_is_court_sentry(int kind,int area){return kind==ENEMY_SENTRY&&area==53;}
enum { ENEMY_CHARGE_RANGE=64,
       ENEMY_CHARGE_WARNING=42, ENEMY_CHARGE_STEPS=18,
       ENEMY_CHARGE_SPEED=3, ENEMY_CHARGE_RECOVERY=90,
       ENEMY_POST_RANGE=56, ENEMY_POST_WARNING=20,
       ENEMY_POST_STEPS=6, ENEMY_POST_SPEED=2, ENEMY_POST_RECOVERY=36 };
/* Reuses the existing per-actor clock, warning and aim storage. Positive clock
 * is recovery; negative clock is a bounded rush or, for the court post, a
 * short shove. No save or shot ownership. The lane charger's warning and
 * recovery counts stay on the constants above. */
/* Returns contact eligibility for this update, including a rush which moved
 * before its final step or wall probe entered recovery. Interrupts and a wall
 * blocking the first microstep remain harmless; no per-actor state is added. */
int enemy_tactics_update(unsigned slot);
void enemy_tactics_draw(unsigned slot);
#endif
