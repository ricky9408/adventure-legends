/* Explicit absent-future-chapter/read-only-economy bridge for old isolated
 * combat component harnesses. The real engine links actual implementations. */
#include "save5.h"
int horizons_powers_busy(void){return 0;}
int covenants_powers_busy(void){return 0;}
void covenants_powers_selection_changed(void){}
void covenants_game_selection_changed(void){}
#ifndef FEEDBACK_REAL_ECONOMY
unsigned economy_heart_bonus(const Save5State*s){return !!(s->economy.relics&1u);}
unsigned economy_attack_bonus(const Save5State*s){return s->economy.upgrade+!!(s->economy.relics&4u);}
unsigned economy_power_reduction(const Save5State*s){return ((s->economy.relics&2u)?8u:0u)+((s->economy.later_claims&4u)?4u:0u);}

unsigned economy_speed_bonus(const Save5State*s){return s->economy.later_claims&1u?16u:0u;}
unsigned economy_defense_bonus(const Save5State*s){return s->economy.later_claims&2u?2u:0u;}
unsigned economy_later_heart_bonus(const Save5State*s){return !!(s->economy.later_claims&8u);}
#endif
