#ifndef EMBER_COMPANION_GUIDE_H
#define EMBER_COMPANION_GUIDE_H
#include "creatures.h"
#include "equipment.h"
/* Read-only companion display. No selection/save/cast hooks in this module. */
enum { COMPANION_GUIDE_GROWTH=4 };
extern unsigned companion_guide_page;
unsigned companion_guide_command_next(const CreatureInstance*,unsigned,int);
/* Shared command base for both the companion guide and effective gear preview. */
unsigned companion_guide_recovery_stats(unsigned command,const EquipmentStats *effective);
unsigned companion_guide_recovery(unsigned command);
void companion_guide_draw(const CreatureInstance*,unsigned command,unsigned destination);
void companion_guide_axes(unsigned form,unsigned polarity,int y);
void companion_guide_combat(unsigned command,int y);
void companion_guide_text(unsigned label,int x,int y,int color);
int companion_guide_number(unsigned value,unsigned places,int x,int y,int color);
void companion_guide_center(unsigned label,int y,int color);
#endif
