#ifndef ADVENTURE_ENEMY_TACTICS_H
#define ADVENTURE_ENEMY_TACTICS_H
#include "enemy_types.h"
enum { ENEMY_CHARGE_RANGE=64,
       ENEMY_CHARGE_WARNING=42, ENEMY_CHARGE_STEPS=18,
       ENEMY_CHARGE_SPEED=3, ENEMY_CHARGE_RECOVERY=90 };
/* Reuses the existing per-actor clock, warning and aim storage. Positive clock
 * is recovery; negative clock is a bounded rush. No save or shot ownership. */
/* Returns contact eligibility for this update, including a rush which moved
 * before its final step or wall probe entered recovery. Interrupts and a wall
 * blocking the first microstep remain harmless; no per-actor state is added. */
int enemy_tactics_update(unsigned slot);
void enemy_tactics_draw(unsigned slot);
#endif
