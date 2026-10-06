#ifndef EMBERBOND_REGIONAL_QUESTS_H
#define EMBERBOND_REGIONAL_QUESTS_H
#include "save5.h"
enum {
    REGION_QUEST_COUNT=11, REGION_FIRST_ROOM=16, REGION_LAST_ROOM=21,
    REGION_QUEST_PRACTICE=0, REGION_QUEST_DRY_ROAD=1,
    REGION_QUEST_WATER_BOND=2, REGION_QUEST_METAL_BOND=3,
    REGION_QUEST_TIDE_POOLS=4, REGION_QUEST_WEAVER=5,
    REGION_QUEST_FRIENDSHIPS=6, REGION_QUEST_LATCH=7,
    REGION_QUEST_MAIL=8, REGION_QUEST_GARDEN=9, REGION_QUEST_RING=10
};
enum RegionQuestResult { REGION_QUEST_INVALID=-1, REGION_QUEST_UNCHANGED=0,
    REGION_QUEST_CHANGED=1, REGION_QUEST_NOW_READY=2, REGION_QUEST_REWARDED=3,
    REGION_QUEST_LOCKED=4, REGION_QUEST_FULL=5, REGION_QUEST_RESERVED=6 };
/* These APIs operate on the engine's already validated live state. They never
 * access SRAM: caller autosaves after a nonzero successful change. Call only on
 * an interaction/event, not every frame. Eligibility does not award anything. */
int regional_can_enter(const Save5State *state,unsigned room);
int regional_visit(Save5State *state,unsigned room);
int regional_anchor(Save5State *state,unsigned room);
unsigned regional_quest_mask(unsigned quest);
int regional_quest_available(const Save5State *state,unsigned quest);
int regional_quest_offer(Save5State *state,unsigned quest);
/* Single authored objective bit. Repeated events are byte-for-byte no-ops.
 * Engine verifies the actual puzzle/combat condition before calling. */
int regional_quest_objective(Save5State *state,unsigned quest,unsigned bit);
int regional_quest_variable(Save5State *state,unsigned quest,unsigned value);
/* Reward+claim ledger is one synchronous in-memory transaction. Full inventory
 * or unavailable recruit leaves every byte unchanged and quest READY for retry.
 * No save or modal may intervene between reward and claim commit. */
int regional_quest_claim(Save5State *state,unsigned quest);
/* Practice racks are the only free non-starter equipment sources. */
int regional_claim_rack(Save5State *state,unsigned weapon_class);
/* RESERVED means physically free slots are needed for missing terminal paths;
 * FULL means160 occupied slots. Neither consumes rewards, source or quest state.
 * Imported over-budget rosters remain legal; only nonworsening grants proceed. */
#endif
