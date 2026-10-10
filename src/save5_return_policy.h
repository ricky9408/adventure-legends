#ifndef EMBERBOND_SAVE5_RETURN_POLICY_H
#define EMBERBOND_SAVE5_RETURN_POLICY_H
/* Append-only content7. wire5 offsets and immutable r1..6 rows are unchanged. */
static const Save5HistoryVersion save5_policy7_version = {
 54,42,61,{[0]=63,[1]=255,[2]=255,[3]=255,[4]=255,[5]=255,[8]=255,[9]=127,
 [10]=63,[11]=3,[16]=15,[17]=255,[18]=3,[19]=7,[20]=3,[21]=7},
 {[0]=3,[1]=3,[2]=3,[3]=3,[4]=3,[5]=3}
};
/* Return quests start in old towns. Region0 here preserves those visits; new
 * room objective evidence and prerequisites are checked separately below. */
static const Save5HistoryQuest save5_policy7_quests[8] = {
 {3,0,0,0,41,0},
 {7,0,0,0,47,0},
 {7,0,0,0,48,0},
 {7,0,0,0,47,0},
 {7,0,0,0,50,0},
 {15,0,0,0,49,51},
 {7,0,0,0,47,0},
 {15,0,0,0,48,50},
};
static const Save5HistoryItem save5_policy7_items[5] = {
 {21,0,0,2,52},{39,1,0,2,51},{55,2,0,2,48},{69,3,0,2,50},{87,4,0,2,53}
};
static const Save5HistoryRoom save5_policy7_rooms[8] = {
 {7,7,2,5,1,1,47,0,0},
 {7,7,2,5,2,2,47,0,0},
 {7,3,2,5,4,0,47,0,0},
 {7,3,2,5,8,0,47,0,0},
 {7,3,2,5,16,0,47,0,0},
 {7,3,2,5,32,0,47,0,0},
 {7,3,2,5,64,0,47,0,0},
 {7,3,2,5,128,0,47,0,0},
};
typedef struct ReturnEvidence { Save4U8 count[2], trained, invalid; } ReturnEvidence;
static int return_quest_campaign_validate(const Save5Quests *);
static void return_instance_evidence(ReturnEvidence *,const CreatureInstance *);
static int return_sources_validate(const Save5Quests *,const Save4U8 *,const ReturnEvidence *);
static int return_roster_sources_validate(const Save5Quests *,const CreatureRoster *);
#endif
