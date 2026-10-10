/* Test-only exported wrappers around the actual integrated production helpers. */
#include "progression.h"
#include "gear_runtime.h"
#include "gear_menu.h"
Save5State adventure_save;
volatile int max_hp;
#define EXPORT __attribute__((visibility("default")))
EXPORT int gear_treasure_valid(const Save5State *s){return save5_validate(s);}
EXPORT unsigned gear_treasure_expected(const Save5State *s,unsigned base,unsigned current,unsigned slot,unsigned ref,EquipmentComparison *out){
 unsigned result;adventure_save=*s;max_hp=(int)base;
 result=equipment_preview(&adventure_save.equipment,slot,ref,game_gear_base_hp(),current,0,out);
 if(result==EQUIPMENT_OK){game_gear_bonus_stats(&out->before);game_gear_bonus_stats(&out->after);}
 return result;
}
