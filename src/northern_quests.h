#ifndef EMBERBOND_NORTHERN_QUESTS_H
#define EMBERBOND_NORTHERN_QUESTS_H
#include "save5.h"
enum { NORTH_FIRST_ROOM=22,NORTH_LAST_ROOM=29,NORTH_FIRST_QUEST=11,NORTH_QUEST_COUNT=11,
 NORTH_Q_LINES=11,NORTH_Q_KILN,NORTH_Q_BEARING,NORTH_Q_TENDER,NORTH_Q_MARKERS,
 NORTH_Q_ROOF,NORTH_Q_LEDGER,NORTH_Q_FRAGILE,NORTH_Q_BALANCE,NORTH_Q_COMPASS,NORTH_Q_BEACON };
enum NorthQuestResult { NORTH_INVALID=-1,NORTH_UNCHANGED=0,NORTH_CHANGED=1,NORTH_NOW_READY=2,NORTH_REWARDED=3,NORTH_LOCKED=4,NORTH_FULL=5,NORTH_RESERVED=6 };
/* Event-only helpers. No SRAM, no whole-save scratch, no automatic equip or
 * evolution. Claim is an atomic synchronous ledger transaction. */
int northern_can_enter(const Save5State*,unsigned room);
int northern_visit(Save5State*,unsigned room);
int northern_anchor(Save5State*,unsigned room);
unsigned northern_quest_mask(unsigned quest);
int northern_quest_available(const Save5State*,unsigned quest);
int northern_quest_offer(Save5State*,unsigned quest);
int northern_quest_objective(Save5State*,unsigned quest,unsigned bit);
int northern_quest_claim(Save5State*,unsigned quest);
unsigned northern_recruit_level(const CreatureRoster*);
/* RESERVED means physically free slots are needed for missing terminal paths;
 * FULL means160 occupied slots. Neither consumes rewards, source or quest state.
 * Imported over-budget rosters remain legal; only nonworsening grants proceed. */
#endif
