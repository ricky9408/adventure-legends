#ifndef ADVENTURE_LEGENDS_ECONOMY_H
#define ADVENTURE_LEGENDS_ECONOMY_H
#include "save5.h"
enum {
 ECONOMY_OK=0,ECONOMY_INVALID=1,ECONOMY_BUSY=2,ECONOMY_NO_GOLD=3,
 ECONOMY_FULL=4,ECONOMY_ALREADY_OWNED=5,ECONOMY_NOT_EARNED=6,
 ECONOMY_EMPTY=7,ECONOMY_SAVE_FAILED=8,ECONOMY_STATE_CHANGED=9,
 ECONOMY_NOT_IN_VILLAGE=10
};
/* Once per actual normal-enemy defeat; engine owns per-spawn death identity.
 * Repeat encounters intentionally earn again. Returns capped actual credit. */
unsigned economy_award_combat(Save5State*,unsigned amount);
unsigned economy_gold(const Save5State*);
unsigned economy_supply_count(const Save5State*,unsigned supply);
unsigned economy_heart_bonus(const Save5State*);
/* Ownership count0..2: runtime adds4Q4 displayed attack per owned buff. */
unsigned economy_attack_bonus(const Save5State*);
unsigned economy_power_reduction(const Save5State*);
unsigned economy_speed_bonus(const Save5State*);
unsigned economy_defense_bonus(const Save5State*);
unsigned economy_later_heart_bonus(const Save5State*);
unsigned economy_claimable(const Save5State*);
unsigned economy_price(unsigned item);
unsigned economy_boss_gold(unsigned boss);
/* Owned immutable preflight followed by nonpreemptible dual-bank save.
 * Freeze gameplay/input; no live money/item change or tonic effect before DONE.
 * Purchases are village-only; claims require earned clear and village/boss room. */
int economy_begin_purchase(Save5State*,unsigned item);
int economy_begin_use(Save5State*,unsigned supply);
int economy_begin_claim(Save5State*,unsigned boss);
unsigned economy_step(void);
int economy_pending(void);
/* Returns0 after writer admission; continue stepping until DONE/FAILED. */
int economy_cancel(void);
unsigned economy_last_error(void);
unsigned economy_last_gold(void);
unsigned economy_state_bytes(void);
#endif
