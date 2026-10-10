/* Actual menu cache and fresh live equipment commits; engine bridge is explicit. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "progression.h"
#include "equipment.h"
static unsigned previews,hp=96,base=96,busy,saves,applies;
static unsigned tracked_preview(const EquipmentState*s,unsigned slot,unsigned ref,unsigned b,unsigned h,unsigned flags,EquipmentComparison*out){previews++;return equipment_preview(s,slot,ref,b,h,flags,out);}
#define equipment_preview tracked_preview
#include "../src/gear_menu.c"
#undef equipment_preview
Save5State adventure_save;
int journal_tab=4;
unsigned game_gear_base_hp(void){return base+(adventure_save.economy.relics&1u?16u:0u);}
unsigned game_gear_hp(void){return hp;}
unsigned game_gear_busy(void){return busy;}
void game_gear_bonus_stats(EquipmentStats*s){unsigned recovery=(EQUIPMENT_BASE_POWER_COOLDOWN-s->power_cooldown)+(EQUIPMENT_BASE_ROLL_COOLDOWN-s->roll_cooldown);if(recovery>8u)recovery=8u;s->power_cooldown=(unsigned char)(EQUIPMENT_BASE_POWER_COOLDOWN-recovery);s->attack_q4+=(unsigned char)(4u*(adventure_save.economy.upgrade+!!(adventure_save.economy.relics&4u)));if(adventure_save.economy.relics&2u)s->power_cooldown-=8;}
void game_gear_apply_stats(unsigned h,const EquipmentStats*s){assert(s);assert(h<=hp);hp=h;applies++;}
void save_game(void){saves++;}
void toast(int id){(void)id;}
void sfx(int id){(void)id;}
static void fresh(void){memset(&adventure_save,0,sizeof adventure_save);equipment_init(&adventure_save.equipment);gear_menu_reset();previews=saves=applies=busy=0;base=hp=96;}
static void exact(EquipmentComparison*cached){EquipmentComparison oracle;unsigned want=equipment_preview(&adventure_save.equipment,(unsigned)gear_menu_slot,(unsigned)gear_menu_candidate,game_gear_base_hp(),hp,0,&oracle);assert(preview_display(cached)==want);if(want==EQUIPMENT_OK){game_gear_bonus_stats(&oracle.before);game_gear_bonus_stats(&oracle.after);assert(!memcmp(cached,&oracle,sizeof oracle));}}
int main(void){EquipmentComparison cmp;EquipmentState good,before;unsigned i,n,ref;unsigned char*bytes;
 fresh();exact(&cmp);assert(previews==1);exact(&cmp);assert(previews==1);good=adventure_save.equipment;
 /* Every equipment byte, including reserved/history/ownership bytes, is keyed. */
 bytes=(unsigned char*)&adventure_save.equipment;
 for(i=0;i<sizeof good;i++){n=previews;bytes[i]^=1;exact(&cmp);assert(previews==n+1);bytes[i]^=1;exact(&cmp);assert(previews==n+2);}
 assert(!memcmp(&good,&adventure_save.equipment,sizeof good));
 n=previews;base+=16;exact(&cmp);assert(previews==n+1);n=previews;hp--;exact(&cmp);assert(previews==n+1);
 n=previews;gear_menu_slot=1;gear_menu_candidate=255;exact(&cmp);assert(previews==n+1);n=previews;gear_menu_candidate=0;exact(&cmp);assert(previews==n+1);gear_menu_slot=0;
 n=previews;adventure_save.economy.relics=7;exact(&cmp);assert(previews==n+1&&cmp.after.attack_q4==4&&cmp.after.max_hp_q4==128&&cmp.after.power_cooldown==67);n=previews;adventure_save.economy.upgrade=1;exact(&cmp);assert(previews==n+1&&cmp.after.attack_q4==8);exact(&cmp);assert(cmp.after.attack_q4==8&&previews==n+1);
 fresh();assert(equipment_claim(&adventure_save.equipment,33,equipment_reward_source(33),&ref)==EQUIPMENT_OK);gear_menu_slot=1;gear_menu_candidate=(int)ref;hp=80;adventure_save.economy.relics=7;adventure_save.economy.upgrade=1;exact(&cmp);n=previews;
 assert(gear_menu_input(1)&&applies==1&&saves==1&&hp==80);exact(&cmp);assert(previews==n);assert(!memcmp(&cmp.before,&cmp.after,sizeof cmp.before)&&cmp.hp_before_q4==80&&cmp.hp_after_q4==80&&cmp.after.attack_q4==8);
 /* A does not trust a cached preview: live busy and mutated ownership win. */
 before=adventure_save.equipment;busy=EQUIPMENT_BUSY_ATTACKING;assert(gear_menu_input(1)&&applies==1&&saves==1&&!memcmp(&before,&adventure_save.equipment,sizeof before)&&hp==80);busy=0;
 adventure_save.equipment.bag[ref].quantity=0;assert(gear_menu_input(1)&&applies==1&&saves==1&&hp==80);n=previews;assert(preview_display(&cmp)==EQUIPMENT_INVALID&&previews==n+1);adventure_save.equipment=before;exact(&cmp);
 gear_menu_reset();n=previews;exact(&cmp);assert(previews==n+1);
 puts("PASS Gear display cache: every512 equipment byte, HP/base/slot/candidate/passive keys, fresh commit seed, live busy/ownership rejection and nonaccumulating bonuses");return 0;
}
