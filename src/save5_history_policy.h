#ifndef EMBERBOND_SAVE5_HISTORY_POLICY_H
#define EMBERBOND_SAVE5_HISTORY_POLICY_H

/* Immutable RELEASED wire policy, schema 1. Never regenerate these rows from
 * current equipment/quest catalogs. Append a new reviewed revision instead.
 * tests/test_save5_history.py pins the release1..4 block byte-for-byte.
 * Numeric values here are saved identities/bit meanings, not current enums.
 * This header is data-only so every existing build still links save5.c alone. */
typedef struct Save5HistoryVersion {
    Save4U8 quest_count, item_count, last_room;
    Save4U8 regions[32], anchors[16];
} Save5HistoryVersion;
typedef struct Save5HistoryQuest {
    Save4U8 mask, prefix, variable_max, region, prior_a, prior_b;
} Save5HistoryQuest;
typedef struct Save5HistoryItem {
    Save4U8 id, slot, flags, category;
    signed char quest;
} Save5HistoryItem;
typedef struct Save5HistoryRoom {
    Save4U8 since, spawns, chapter, region, visit, anchor, quest;
    Save4U16 entry, north;
} Save5HistoryRoom;
typedef struct Save5HistoryFlagGate {
    Save4U16 trigger, required;
    Save4U8 chapter;
} Save5HistoryFlagGate;
typedef struct Save5HistoryVisitGate {
    Save4U8 region, trigger, quest_a, quest_b, objective_quest, objectives;
} Save5HistoryVisitGate;
typedef struct Save5HistoryCreature {
    Save4U8 base, evolved, level, bond, source_quest, reward;
    Save4U16 trial, owner, trained;
} Save5HistoryCreature;

/* BEGIN LOCKED RELEASES 1-4 */
static const Save5HistoryVersion save5_history_versions[5] = {
    {0,0,0,{0},{0}},
    {0,0,13,{0},{0}},
    {11,13,21,{[0]=63},{[0]=3}},
    {22,19,29,{[0]=63,[1]=255},{[0]=3,[1]=3}},
    {30,25,37,{[0]=63,[1]=255,[2]=255,[8]=255,[18]=3},
              {[0]=3,[1]=3,[2]=3}}
};
/* prior_* is quest ID + 1; zero means no prerequisite. Each row's reward
 * ledger bit has exactly its own quest ID. Variables3/9 alone allow0..3. */
static const Save5HistoryQuest save5_history_quests[30] = {
    {7,0,0,0,0,0}, {3,0,0,0,0,0}, {7,0,0,0,0,0},
    {7,0,3,0,0,0}, {3,0,0,0,0,0}, {1,0,0,0,0,0},
    {1,0,0,0,0,0}, {1,0,0,0,0,0}, {3,0,0,0,0,0},
    {7,0,3,0,0,0}, {1,0,0,0,0,0},
    {3,0,0,1,0,0}, {7,0,0,1,0,0}, {3,0,0,1,12,0},
    {7,0,0,1,0,0}, {7,0,0,1,0,0},
    {3,0,0,1,12,0}, {7,0,0,1,13,0}, {7,0,0,1,15,0},
    {3,0,0,1,16,0}, {7,0,0,1,14,0}, {15,1,0,1,12,14},
    {3,0,0,2,22,0}, {3,0,0,2,22,0}, {15,1,0,2,23,24},
    {7,0,0,2,22,0}, {3,0,0,2,22,0}, {3,0,0,2,22,0},
    {3,0,0,2,22,0}, {3,0,0,2,22,0}
};
/* Each persisted quest-reward bit is tied to this exact quest state,
 * including reserved slots (whose state must remain INACTIVE). */
static const Save4U8 save5_history_reward_quests[64] = {
    0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,
    16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,
    32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,
    48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63
};
/* Indexed by acquisition source, NOT item ID. Category0=starter (claim may
 * be absent historically),1=free town rack,2=exact claimed quest equivalence.
 * Quest6 and quest19 each deliberately own two distinct source rows. */
static const Save5HistoryItem save5_history_items[25] = {
    {1,0,1,0,-1}, {2,0,0,2,7}, {9,0,0,1,-1}, {10,0,0,2,6},
    {17,0,0,1,-1}, {18,0,0,2,4}, {33,1,0,2,0}, {34,1,0,2,8},
    {49,2,0,2,1}, {50,2,0,2,9}, {65,3,0,2,5}, {81,4,0,2,10},
    {82,4,0,2,6}, {3,0,0,2,16}, {11,0,0,2,17}, {19,0,0,2,18},
    {35,1,0,2,19}, {51,2,0,2,19}, {83,4,0,2,20},
    {4,0,0,2,22}, {12,0,0,2,29}, {36,1,0,2,25},
    {52,2,0,2,27}, {66,3,0,2,26}, {84,4,0,2,28}
};
/* Exact sparse ID -> source row + 1. Zero is reserved. */
static const Save4U8 save5_history_item_source[85] = {
    [1]=1,[2]=2,[9]=3,[10]=4,[17]=5,[18]=6,[33]=7,[34]=8,
    [49]=9,[50]=10,[65]=11,[81]=12,[82]=13,[3]=14,[11]=15,
    [19]=16,[35]=17,[51]=18,[83]=19,[4]=20,[12]=21,[36]=22,
    [52]=23,[66]=24,[84]=25
};
/* region255 means original campaign. quest is ID+1. Spawn bit2 in a
 * regional anchor room requires the recorded matching anchor. */
static const Save5HistoryRoom save5_history_rooms[38] = {
    {1,57,0,255,0,0,0,0,0}, {1,7,0,255,0,0,0,0,0},
    {1,3,0,255,0,0,0,0,0}, {1,3,0,255,0,0,0,0,0},
    {1,3,1,255,0,0,0,0,0}, {1,3,1,255,0,0,0,0,3},
    {1,3,1,255,0,0,0,3,7}, {1,3,1,255,0,0,0,7,63},
    {1,3,1,255,0,0,0,63,0}, {1,3,2,255,0,0,0,0,64},
    {1,3,2,255,0,0,0,64,448}, {1,3,2,255,0,0,0,448,4032},
    {1,3,2,255,0,0,0,4032,65472}, {1,3,2,255,0,0,0,65472,0},
    {0,0,0,0,0,0,0,0,0}, {0,0,0,0,0,0,0,0,0},
    {2,63,1,0,1,1,0,0,0}, {2,7,1,0,2,2,0,0,0},
    {2,1,1,0,4,0,3,0,0}, {2,1,1,0,8,0,3,0,0},
    {2,1,1,0,16,0,0,0,0}, {2,1,1,0,32,0,0,0,0},
    {3,31,2,1,1,1,0,0,0}, {3,7,2,1,2,2,0,0,0},
    {3,1,2,1,4,0,0,0,0}, {3,1,2,1,8,0,0,0,0},
    {3,1,2,1,16,0,0,0,0}, {3,1,2,1,32,0,0,0,0},
    {3,1,2,1,64,0,0,0,0}, {3,1,2,1,128,0,0,0,0},
    {4,31,2,2,1,1,0,0,0}, {4,15,2,2,2,2,0,0,0},
    {4,1,2,2,4,0,0,0,0}, {4,1,2,2,8,0,0,0,0},
    {4,1,2,2,16,0,0,0,0}, {4,1,2,2,32,0,0,0,0},
    {4,1,2,2,64,0,0,0,0}, {4,1,2,2,128,0,0,0,0}
};
static const Save5HistoryFlagGate save5_history_flag_gates[10] = {
    {63,0,1}, {65472,0,2}, {2,1,0}, {4,3,0}, {56,7,0},
    {384,64,0}, {3584,448,0}, {1024,512,0}, {61440,4032,0},
    {0,0,0}
};
/* quest IDs+1. Visits remain prerequisites even after returning to town. */
static const Save5HistoryVisitGate save5_history_visit_gates[8] = {
    {1,240,12,14,0,0}, {1,32,0,0,22,1},
    {1,64,0,0,22,2}, {1,128,0,0,22,4},
    {2,240,23,24,0,0}, {2,32,0,0,25,1},
    {2,64,0,0,25,3}, {2,128,0,0,25,7}
};
/* Region byte, required chapter mask, required previous town-byte mask.
 * Every nonempty region also requires its own town visit bit0. */
static const Save4U8 save5_history_regions[3][3] = {{0,1,0},{1,2,1},{2,2,3}};
static const Save4U8 save5_history_field_visit[8] = {2,2,8,2,2,2,4,8};
static const Save4U8 save5_history_field_discovery[8] = {0,0,0,0,1,0,2,0};
static const Save4U8 save5_history_discovery_quest[2] = {29,28};
/* Exact-family retention, reward bit IDs and same-copy training floors. The
 * old evolved-form validator deliberately imposes no extra causal history. */
static const Save5HistoryCreature save5_history_creatures[7] = {
    {13,14,0,0,2,5,0,1,0}, {16,0,0,0,3,6,0,2,0},
    {19,20,16,40,11,7,32,4,256}, {22,23,17,40,12,8,64,8,512},
    {73,74,18,45,14,9,128,16,1024}, {75,76,18,45,15,10,256,32,2048},
    {77,78,20,50,13,11,512,64,4096}
};
static const Save4U8 save5_history_creature_row[79] = {
    [13]=1,[14]=1,[16]=2,[19]=3,[20]=3,[22]=4,[23]=4,
    [73]=5,[74]=5,[75]=6,[76]=6,[77]=7,[78]=7
};
static const Save4U8 save5_history_trial_quests[5] = {16,17,18,19,20};
/* Southern source order is two quest rewards followed by field bits0..7. */
static const Save5HistoryCreature save5_history_southern[10] = {
    {79,80,20,40,22,0,1,1,0}, {85,86,20,40,23,0,1,2,0},
    {25,26,20,40,0,0,1,4,0}, {28,29,22,45,0,0,1,8,0},
    {81,82,22,45,0,0,1,16,0}, {83,84,22,45,0,0,1,32,0},
    {87,88,24,45,0,0,1,64,0}, {89,90,22,45,0,0,1,128,0},
    {91,92,24,45,0,0,1,256,0}, {93,94,22,45,0,0,1,512,0}
};
static const Save4U8 save5_history_southern_row[128] = {
    [79]=1,[80]=1,[85]=2,[86]=2,[25]=3,[26]=3,[28]=4,[29]=4,
    [81]=5,[82]=5,[83]=6,[84]=6,[87]=7,[88]=7,[89]=8,[90]=8,
    [91]=9,[92]=9,[93]=10,[94]=10
};
/* END LOCKED RELEASES 1-4 */
/* Current revision5 additions. Never append into or reinterpret released rows.
 * A later revision must snapshot these values before changing their policy. */
static const Save5HistoryVersion save5_policy5_version = {
    38,31,45,{[0]=63,[1]=255,[2]=255,[3]=255,[8]=255,[9]=127,
             [16]=15,[18]=3,[19]=7},{[0]=3,[1]=3,[2]=3,[3]=3}
};
static const Save5HistoryQuest save5_policy5_quests[8] = {
    {3,0,0,3,25,0},{3,0,0,3,25,0},{15,1,0,3,31,32},
    {7,0,0,3,31,0},{3,0,0,3,25,0},{3,0,0,3,25,0},
    {3,0,0,3,25,0},{7,0,0,3,25,0}
};
static const Save5HistoryItem save5_policy5_items[6] = {
    {20,0,0,2,30},{37,1,0,2,33},{53,2,0,2,34},
    {67,3,0,2,35},{85,4,0,2,36},{5,0,0,2,37}
};
static const Save5HistoryRoom save5_policy5_rooms[8] = {
    {5,15,2,3,1,1,25,0,0},{5,15,2,3,2,2,25,0,0},
    {5,1,2,3,4,0,25,0,0},{5,1,2,3,8,0,25,0,0},
    {5,1,2,3,16,0,25,0,0},{5,1,2,3,32,0,25,0,0},
    {5,1,2,3,64,0,25,0,0},{5,1,2,3,128,0,25,0,0}
};
#endif
