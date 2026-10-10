#ifndef EMBERBOND_SAVE5_UNDERWATER_POLICY_H
#define EMBERBOND_SAVE5_UNDERWATER_POLICY_H
/* Appended revision6 only. The exact accepted revision5 policy header remains
 * byte-identical and is archived with its immutable source oracle. All wire
 * offsets, record widths, old quest/item/source/visit meanings are unchanged. */
static const Save5HistoryVersion save5_policy6_version = {
 46,37,53,{[0]=63,[1]=255,[2]=255,[3]=255,[4]=255,[8]=255,[9]=127,
 [10]=63,[16]=15,[17]=255,[18]=3,[19]=7,[20]=3,[21]=7},
 {[0]=3,[1]=3,[2]=3,[3]=3,[4]=3}
};
static const Save5HistoryQuest save5_policy6_quests[8] = {
 {3,0,0,4,33,0},{3,0,0,4,33,0},{15,1,0,4,39,40},
 {7,0,0,4,39,0},{3,0,0,4,40,0},{3,0,0,4,33,0},
 {3,0,0,4,33,0},{7,0,0,4,41,0}
};
static const Save5HistoryItem save5_policy6_items[6] = {
 {6,0,0,2,41},{13,0,0,2,42},{38,1,0,2,43},
 {54,2,0,2,44},{68,3,0,2,45},{86,4,0,2,45}
};
static const Save5HistoryRoom save5_policy6_rooms[8] = {
 {6,15,2,4,1,1,33,0,0},{6,7,2,4,2,2,33,0,0},
 {6,7,2,4,4,0,33,0,0},{6,3,2,4,8,0,33,0,0},
 {6,3,2,4,16,0,33,0,0},{6,7,2,4,32,0,33,0,0},
 {6,7,2,4,64,0,33,0,0},{6,3,2,4,128,0,33,0,0}
};
/* Current-r6 reciprocal shell-lift landing only. The inherited since5 keeps
 * old spawn3 anchor semantics; spawn4 additionally needs the Underwater visit.
 * Immutable r1..5 still resolve their exact original room38 row. */
static const Save5HistoryRoom save5_policy6_magma_return = {5,31,2,3,1,1,25,0,0};
/* Per-record evidence, not a roster clone. Counts saturate at2. A branch
 * receipt needs a retained terminal and two globally distinct identities. */
typedef struct UnderwaterEvidence {
 Save4U8 count[8], terminals, trained, invalid;
} UnderwaterEvidence;
static int underwater_quest_campaign_validate(const Save5Quests *);
static void underwater_instance_evidence(UnderwaterEvidence *,const CreatureInstance *);
static int underwater_sources_validate(const Save5Quests *,const Save4U8 *,const UnderwaterEvidence *);
static int underwater_roster_sources_validate(const Save5Quests *,const CreatureRoster *);
#endif
