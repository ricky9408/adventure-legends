#ifndef EMBER_GEAR_PREVIEW_H
#define EMBER_GEAR_PREVIEW_H
#include "equipment.h"
/* Display projection only: input has already received runtime bonuses once.
 * Hearts are exact Q4; walking is a baseline-100 index in tenths. */
typedef struct GearPreview {
 unsigned attack,defense,hearts,walk_tenths,recovery_updates,recovery_hundredths,distance,stagger,weapon_class;
} GearPreview;
void gear_preview_project(const EquipmentStats *effective,unsigned command,GearPreview *out);
/* Approximate active-play seconds, rounded to hundredths at the GBA cadence.
 * Menus/hitstop do not advance recovery. Input is bounded to unsigned16. */
unsigned gear_preview_hundredths(unsigned updates);
#endif
