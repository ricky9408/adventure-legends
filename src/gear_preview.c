#include "gear_preview.h"
#include "companion_guide.h"
unsigned gear_preview_hundredths(unsigned updates){
 /* round(updates * 438900 / 262144) = round(updates * 109725 / 65536).
  * Split at eight bits so even65535 cannot overflow32-bit unsigned math.
  * The intermediate maximum is28089299; shipped commands top out at240. */
 if(updates>65535u)updates=65535u;
 return (((updates>>8)*109725u)+(((updates&255u)*109725u+32768u)>>8))>>8;
}
void gear_preview_project(const EquipmentStats*s,unsigned command,GearPreview*out){
 const EquipmentMove*m=&equipment_weapons[s->weapon_class].moves[0];
 out->attack=m->damage_q4+s->attack_q4;out->defense=s->defense_q4;out->hearts=s->max_hp_q4;
 out->walk_tenths=(s->speed_q8*25u+4u)>>3;
 out->recovery_updates=companion_guide_recovery_stats(command,s);
 out->recovery_hundredths=gear_preview_hundredths(out->recovery_updates);
 out->distance=m->reach_px+s->reach_px;out->stagger=s->stagger;out->weapon_class=s->weapon_class;
}
