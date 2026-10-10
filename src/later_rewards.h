#ifndef ADVENTURE_LEGENDS_LATER_REWARDS_H
#define ADVENTURE_LEGENDS_LATER_REWARDS_H
#include "save5.h"
/* Permanent item ownership and first-collection gold share one persisted bit.
 * Values below are stable authored IDs, independent of equipment sources. */
enum {
 LATER_COMPASS=0,LATER_LENS=1,LATER_BELL=2,LATER_PEARL=3,LATER_REWARD_COUNT=4,
 LATER_SOURCE_NORTH_MACHINE=0,LATER_SOURCE_NORTH_HARBOR=1,
 LATER_SOURCE_SOUTH_MACHINE=2,LATER_SOURCE_SOUTH_TOWN=3,
 LATER_SOURCE_MAGMA_RESSA=4,LATER_SOURCE_UNDERWATER_KEEPER=5,
 LATER_SOURCE_VILLAGE_SHOP=6,LATER_SOURCE_COUNT=7
};
enum {
 LATER_OK=0,LATER_INVALID=1,LATER_BUSY=2,LATER_NOT_EARNED=3,
 LATER_ALREADY_OWNED=4,LATER_WRONG_SOURCE=5,LATER_STATE_CHANGED=6,
 LATER_SAVE_FAILED=7,LATER_CANCELED=8
};
/* Sample actual runtime context at begin and every step. scene is a nonzero
 * generation revoked on load/death/scene changes. source_state is the actual
 * machine stage (5) at either machine and zero elsewhere. No validated flag.
 * Coordinates/facing obey the original report interaction geometry. */
typedef struct LaterRewardContext {
 Save4U32 scene;
 int room,x,y,facing;
 unsigned source_state;
} LaterRewardContext;
unsigned later_rewards_quest(unsigned treasure);
unsigned later_rewards_gold(unsigned treasure);
unsigned later_rewards_claimable(const Save5State*);
/* Read-only interaction eligibility; no token, SRAM, mutation or full scan.
 * This is a UI routing check only. begin/step still perform owned preflight. */
unsigned later_rewards_check(const Save5State*,unsigned treasure,unsigned source,const LaterRewardContext*);
/* READY -> atomic quest/EXP/bond/event receipt + treasure + clipped gold.
 * CLAIMED -> explicit missing-treasure recovery only, without EXP/bond replay.
 * Village shop is recovery-only. No roster/gear capacity or selection changes.
 * Owns immutable preflight/writer scratch; all live fields stay unchanged until
 * DONE. After writer admission freeze gameplay and continue nonpreemptibly. */
int later_rewards_begin(Save5State*,unsigned treasure,unsigned source,const LaterRewardContext*);
unsigned later_rewards_step(const LaterRewardContext*);
int later_rewards_pending(void);
/* Returns zero after writer admission; keep stepping to DONE/FAILED. */
int later_rewards_cancel(void);
unsigned later_rewards_last_error(void);
unsigned later_rewards_last_gold(void);
unsigned later_rewards_last_xp(void); /* actual summed party XP, not nominal */
unsigned later_rewards_last_fresh(void);
unsigned later_rewards_phase(void);
unsigned later_rewards_state_bytes(void);
#endif
