/* Actual effective gear cooldown, with no engine state mutation or fake formula. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "progression.h"
#include "gear_runtime.h"
#include "economy.h"
#include "companion_guide.h"
Save5State adventure_save;
static void check(void){unsigned command;EquipmentStats before=gear_stats;Save5State saved=adventure_save;
 for(command=1;command<=128;command++){const CreatureAbility*a=creatures_ability(command);unsigned base=command<=4?75:a->cooldown_updates;assert(companion_guide_recovery(command)==game_power_cooldown(base));}
 assert(!memcmp(&before,&gear_stats,sizeof before)&&!memcmp(&saved,&adventure_save,sizeof saved));
}
int main(void){unsigned item,ref;equipment_init(&adventure_save.equipment);assert(equipment_derive(&adventure_save.equipment,96,&gear_stats));game_gear_bonus_stats(&gear_stats);check();assert(companion_guide_recovery(1)==75);
 for(item=0;item<EQUIPMENT_AUTHORED_COUNT;item++){
  unsigned id=equipment_authored_ids[item];const EquipmentDefinition*d=equipment_definition(id);
  equipment_init(&adventure_save.equipment);if(id!=EQUIPMENT_STARTER_ID)assert(equipment_claim(&adventure_save.equipment,id,equipment_reward_source(id),&ref)==EQUIPMENT_OK);else ref=0;
  adventure_save.equipment.equipped[d->slot]=(EquipmentU8)ref;assert(equipment_derive(&adventure_save.equipment,96,&gear_stats));game_gear_bonus_stats(&gear_stats);check();
 }
 /* Effective gear cap plus earned feather: eight+eight, not raw-item totals. */
 memset(&gear_stats,0,sizeof gear_stats);gear_stats.power_cooldown=EQUIPMENT_BASE_POWER_COOLDOWN-8;gear_stats.roll_cooldown=EQUIPMENT_BASE_ROLL_COOLDOWN-8;adventure_save.economy.relics=2;game_gear_bonus_stats(&gear_stats);assert(EQUIPMENT_BASE_POWER_COOLDOWN-gear_stats.power_cooldown==16);check();assert(companion_guide_recovery(1)==59);
 puts("PASS actual recovery: all128 commands ×48 shipped gear items, base75 legacy dispatch, gear cap+earned feather, no data mutation");return 0;
}
