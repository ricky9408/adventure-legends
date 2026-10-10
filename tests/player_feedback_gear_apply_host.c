/* Actual fresh-stats runtime helper versus a full validated derive. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gear_runtime.h"
#include "gear_menu.h"
#include "progression.h"
Save5State adventure_save;
volatile int hp,max_hp=6;
int gfx_slash_frame;
static unsigned selections;
void covenants_powers_selection_changed(void){selections++;}
void covenants_game_selection_changed(void){selections++;}
int main(void){unsigned i,bits,upgrade,ref,cases=0;EquipmentComparison cmp;EquipmentStats expected;EquipmentU16 current;
 for(i=0;i<EQUIPMENT_AUTHORED_COUNT;i++)for(bits=0;bits<128;bits++)for(upgrade=0;upgrade<2;upgrade++){
  memset(&adventure_save,0,sizeof adventure_save);equipment_init(&adventure_save.equipment);adventure_save.economy.relics=(unsigned char)(bits&7u);adventure_save.economy.later_claims=(unsigned char)(bits>>3);adventure_save.economy.upgrade=(unsigned char)upgrade;
  if(equipment_authored_ids[i]!=EQUIPMENT_STARTER_ID)assert(equipment_claim(&adventure_save.equipment,equipment_authored_ids[i],i,&ref)==EQUIPMENT_OK);else ref=0;
  current=80;assert(equipment_equip(&adventure_save.equipment,equipment_definition(equipment_authored_ids[i])->slot,ref,game_gear_base_hp(),&current,0,&cmp)==EQUIPMENT_OK);
  assert(equipment_derive(&adventure_save.equipment,game_gear_base_hp(),&expected));game_gear_bonus_stats(&expected);
  hero_hp_q4=80;selections=0;game_gear_apply_stats(current,&cmp.after);assert(selections==2);assert(!memcmp(&expected,&gear_stats,sizeof expected));assert(hero_hp_q4==(int)current&&hero_hp_q4<=80&&hp==(hero_hp_q4+15)/16&&gfx_slash_frame==-1);
  game_gear_apply_stats(current,&cmp.after);assert(!memcmp(&expected,&gear_stats,sizeof expected)&&hero_hp_q4<=80);cases++;
 }
 printf("PASS fresh Gear apply: %u actual item/passive combinations match validated derive, no healing or repeated bonus accumulation\n",cases);return 0;
}
