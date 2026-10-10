#ifndef EMBERBOND_GEAR_MENU_H
#define EMBERBOND_GEAR_MENU_H
#include "equipment.h"
extern unsigned gear_menu_revision;
extern int gear_menu_slot,gear_menu_candidate;
void gear_menu_reset(void);
void gear_menu_draw(void);
int gear_menu_input(int pressed);
/* Engine bridge: HP is sixteenths of a heart; preview/commit never heals. */
unsigned game_gear_base_hp(void);
unsigned game_gear_hp(void);
unsigned game_gear_busy(void);
void game_gear_apply(unsigned clamped_hp_q4);
#endif
