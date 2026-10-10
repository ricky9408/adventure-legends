#ifndef EMBER_ADVANCED_POWERS_H
#define EMBER_ADVANCED_POWERS_H
extern int advanced_kind,advanced_time_left,advanced_origin_x,advanced_origin_y,advanced_direction,advanced_hit_mask,advanced_shield_left;
extern int rooted_enemies[6],advanced_guard_charges;
extern unsigned char shot_effects[12],shot_phases[12];
enum { SHOT_EFFECT_NONE=0,SHOT_EFFECT_FIRE=1,SHOT_EFFECT_WIND=2 };
int advanced_power(unsigned command);
void advanced_tick(void);
void advanced_reset(void);
void advanced_draw(void);

#include "return_legacy_geometry.h"
/* Additive read-only export; no field side effects or inferred hit radius. */
void advanced_powers_field_geometry(unsigned command,ReturnLegacyEmit emit,void *context);
#endif
