#include "campaign_rules.h"
static const CampaignBlock solids_4[]={{8,28,96,16,0},{136,28,96,16,0},{64,72,32,24,0},{152,96,32,24,0}};
static const CampaignBlock blocks_4[]={{0,0,0,0,0}};
static const CampaignObject objects_4[]={{48,120,9,255,26,1,0,0,0,0,-1,0,0},{184,64,11,1,28,2,0,0,0,0,CD_OPTIONAL_CHIME,1,0},{48,56,10,255,26,1,0,0,0,0,CD_SKY_PATH_SIGN,0,0}};
static const CampaignEnemy enemies_4[]={{176,128,2,4},{56,64,0,2}};
static const CampaignBlock solids_5[]={{8,28,96,16,0},{136,28,96,16,0},{8,88,88,16,0},{144,88,88,16,0}};
static const CampaignBlock blocks_5[]={{96,88,48,16,1},{104,28,32,16,2}};
static const CampaignObject objects_5[]={{64,120,0,2,28,2,1,0,1,0,CD_SAIL_BRIDGE,0,0},{176,64,0,2,28,2,2,0,2,0,CD_SKY_VANE_OPEN,0,0}};
static const CampaignEnemy enemies_5[]={{0}};
static const CampaignBlock solids_6[]={{8,28,96,16,0},{136,28,96,16,0},{72,76,16,32,0},{152,76,16,32,0}};
static const CampaignBlock blocks_6[]={{104,28,32,16,4}};
static const CampaignObject objects_6[]={{120,112,10,255,26,1,0,0,0,0,CD_PATROL_HINT,0,0}};
static const CampaignEnemy enemies_6[]={{48,64,2,4},{192,64,2,4},{112,80,0,2},{128,80,0,2}};
static const CampaignBlock solids_7[]={{8,28,96,16,0},{136,28,96,16,0},{104,72,32,16,0}};
static const CampaignBlock blocks_7[]={{104,28,32,16,56}};
static const CampaignObject objects_7[]={{56,112,0,2,28,2,8,0,8,0,-1,0,0},{184,112,0,2,28,2,16,0,16,0,-1,0,0},{120,112,7,0,28,2,32,0,32,0,-1,0,0},{56,56,8,255,26,0,0,0,40,0,-1,0,0},{184,56,8,255,26,0,0,0,48,0,-1,0,0},{120,56,9,255,26,1,0,0,0,0,CD_SKY_PREBOSS,0,0}};
static const CampaignEnemy enemies_7[]={{0}};
static const CampaignBlock solids_8[]={{8,28,96,16,0},{136,28,96,16,0}};
static const CampaignBlock blocks_8[]={{104,28,32,16,131072}};
static const CampaignObject objects_8[]={{120,36,8,255,26,0,0,0,0,131072,-1,0,0}};
static const CampaignEnemy enemies_8[]={{0}};
static const CampaignBlock solids_9[]={{8,28,96,16,0},{136,28,96,16,0},{8,80,96,16,0},{136,80,96,16,0}};
static const CampaignBlock blocks_9[]={{104,80,32,16,64}};
static const CampaignObject objects_9[]={{120,88,1,3,32,2,64,0,64,0,CD_CORE_ARCH,0,1},{56,120,9,255,26,1,0,0,0,0,-1,0,0},{184,120,10,255,26,1,0,0,0,0,CD_CORE_PATH_SIGN,0,0}};
static const CampaignEnemy enemies_9[]={{0}};
static const CampaignBlock solids_10[]={{8,28,96,16,0},{136,28,96,16,0},{104,60,32,56,0}};
static const CampaignBlock blocks_10[]={{104,28,32,16,384}};
static const CampaignObject objects_10[]={{56,80,1,3,24,2,128,0,128,0,-1,0,0},{184,80,1,3,24,2,256,0,256,0,-1,0,0},{120,128,10,255,26,1,0,0,0,0,CD_WEIGHTS_HINT,0,0}};
static const CampaignEnemy enemies_10[]={{0}};
static const CampaignBlock solids_11[]={{8,28,96,16,0},{136,28,96,16,0},{8,84,96,20,0},{136,84,96,20,0},{8,56,88,12,0},{144,56,88,12,0}};
static const CampaignBlock blocks_11[]={{40,104,24,24,512},{104,84,32,20,1024},{96,56,48,12,2048}};
static const CampaignObject objects_11[]={{52,116,2,3,32,2,512,0,512,0,-1,0,1},{52,116,4,1,28,2,1024,512,1024,0,CD_ROOTS_GROWN,0,0},{120,62,3,0,32,2,2048,0,2048,0,-1,0,1}};
static const CampaignEnemy enemies_11[]={{0}};
static const CampaignBlock solids_12[]={{8,28,96,16,0},{136,28,96,16,0},{104,72,32,24,0}};
static const CampaignBlock blocks_12[]={{104,28,32,16,61440}};
static const CampaignObject objects_12[]={{56,64,3,0,24,2,4096,0,4096,0,-1,0,0},{184,64,4,1,24,2,8192,0,8192,0,-1,0,0},{56,112,5,2,24,2,16384,0,16384,0,-1,0,0},{184,112,6,3,24,2,32768,0,32768,0,-1,0,0},{120,124,9,255,26,1,0,0,0,0,CD_LAST_REST,0,0}};
static const CampaignEnemy enemies_12[]={{0}};
static const CampaignBlock solids_13[]={{8,28,96,16,0},{136,28,96,16,0}};
static const CampaignBlock blocks_13[]={{104,28,32,16,262144}};
static const CampaignObject objects_13[]={{0}};
static const CampaignEnemy enemies_13[]={{0}};
const CampaignRoom campaign_rooms[10]={
{TX_C_ROOM_4,4,0,3,2,solids_4,blocks_4,objects_4,enemies_4,0,5,0,0,4,0},
{TX_C_ROOM_5,4,2,2,0,solids_5,blocks_5,objects_5,enemies_5,2,6,4,0,1,0},
{TX_C_ROOM_6,4,1,1,4,solids_6,blocks_6,objects_6,enemies_6,4,7,5,0,1,0},
{TX_C_ROOM_7,3,1,6,0,solids_7,blocks_7,objects_7,enemies_7,56,8,6,0,1,0},
{TX_C_ROOM_8,2,1,1,0,solids_8,blocks_8,objects_8,enemies_8,131072,0,7,3,1,1},
{TX_C_ROOM_9,4,1,3,0,solids_9,blocks_9,objects_9,enemies_9,0,10,0,0,5,0},
{TX_C_ROOM_10,3,1,3,0,solids_10,blocks_10,objects_10,enemies_10,384,11,9,0,1,0},
{TX_C_ROOM_11,6,3,3,0,solids_11,blocks_11,objects_11,enemies_11,3072,12,10,0,1,0},
{TX_C_ROOM_12,3,1,5,0,solids_12,blocks_12,objects_12,enemies_12,61440,13,11,0,1,0},
{TX_C_ROOM_13,2,1,0,0,solids_13,blocks_13,objects_13,enemies_13,262144,0,12,3,1,2},
};
const CampaignDialogue campaign_dialogues[CD_COUNT]={
{TX_C_ACT1_OPEN_SPEAKER,{TX_C_ACT1_OPEN_0_0,TX_C_ACT1_OPEN_0_1,TX_C_ACT1_OPEN_1_0,TX_C_ACT1_OPEN_1_1},2},
{TX_C_ELDER_ACT1_SPEAKER,{TX_C_ELDER_ACT1_0_0,TX_C_ELDER_ACT1_0_1},1},
{TX_C_GROVE_CLEAR_SPEAKER,{TX_C_GROVE_CLEAR_0_0,TX_C_GROVE_CLEAR_0_1},1},
{TX_C_WIND_JOIN_SPEAKER,{TX_C_WIND_JOIN_0_0,TX_C_WIND_JOIN_0_1,TX_C_WIND_JOIN_1_0,TX_C_WIND_JOIN_1_1,TX_C_WIND_JOIN_2_0,TX_C_WIND_JOIN_2_1},3},
{TX_C_LEGACY_RECAP_SPEAKER,{TX_C_LEGACY_RECAP_0_0,TX_C_LEGACY_RECAP_0_1,TX_C_LEGACY_RECAP_1_0,TX_C_LEGACY_RECAP_1_1},2},
{TX_C_ELDER_ACT2_SPEAKER,{TX_C_ELDER_ACT2_0_0,TX_C_ELDER_ACT2_0_1,TX_C_ELDER_ACT2_1_0,TX_C_ELDER_ACT2_1_1},2},
{TX_C_SKY_PATH_SIGN_SPEAKER,{TX_C_SKY_PATH_SIGN_0_0,TX_C_SKY_PATH_SIGN_0_1},1},
{TX_C_OPTIONAL_CHIME_SPEAKER,{TX_C_OPTIONAL_CHIME_0_0,TX_C_OPTIONAL_CHIME_0_1},1},
{TX_C_SKY_INTRO_SPEAKER,{TX_C_SKY_INTRO_0_0,TX_C_SKY_INTRO_0_1},1},
{TX_C_SAIL_BRIDGE_SPEAKER,{TX_C_SAIL_BRIDGE_0_0,TX_C_SAIL_BRIDGE_0_1},1},
{TX_C_SKY_VANE_OPEN_SPEAKER,{TX_C_SKY_VANE_OPEN_0_0,TX_C_SKY_VANE_OPEN_0_1},1},
{TX_C_PATROL_HINT_SPEAKER,{TX_C_PATROL_HINT_0_0,TX_C_PATROL_HINT_0_1},1},
{TX_C_PATROL_CLEAR_SPEAKER,{TX_C_PATROL_CLEAR_0_0,TX_C_PATROL_CLEAR_0_1},1},
{TX_C_RELAY_HINT_SPEAKER,{TX_C_RELAY_HINT_0_0,TX_C_RELAY_HINT_0_1},1},
{TX_C_RELAY_COMPLETE_SPEAKER,{TX_C_RELAY_COMPLETE_0_0,TX_C_RELAY_COMPLETE_0_1},1},
{TX_C_SKY_PREBOSS_SPEAKER,{TX_C_SKY_PREBOSS_0_0,TX_C_SKY_PREBOSS_0_1},1},
{TX_C_SKY_BOSS_INTRO_SPEAKER,{TX_C_SKY_BOSS_INTRO_0_0,TX_C_SKY_BOSS_INTRO_0_1},1},
{TX_C_SKY_BOSS_CLEAR_SPEAKER,{TX_C_SKY_BOSS_CLEAR_0_0,TX_C_SKY_BOSS_CLEAR_0_1},1},
{TX_C_STONE_JOIN_SPEAKER,{TX_C_STONE_JOIN_0_0,TX_C_STONE_JOIN_0_1,TX_C_STONE_JOIN_1_0,TX_C_STONE_JOIN_1_1,TX_C_STONE_JOIN_2_0,TX_C_STONE_JOIN_2_1},3},
{TX_C_ELDER_ACT3_SPEAKER,{TX_C_ELDER_ACT3_0_0,TX_C_ELDER_ACT3_0_1,TX_C_ELDER_ACT3_1_0,TX_C_ELDER_ACT3_1_1},2},
{TX_C_CORE_PATH_SIGN_SPEAKER,{TX_C_CORE_PATH_SIGN_0_0,TX_C_CORE_PATH_SIGN_0_1},1},
{TX_C_CORE_ARCH_SPEAKER,{TX_C_CORE_ARCH_0_0,TX_C_CORE_ARCH_0_1},1},
{TX_C_WEIGHTS_HINT_SPEAKER,{TX_C_WEIGHTS_HINT_0_0,TX_C_WEIGHTS_HINT_0_1},1},
{TX_C_ROOT_HINT_SPEAKER,{TX_C_ROOT_HINT_0_0,TX_C_ROOT_HINT_0_1},1},
{TX_C_ROOTS_GROWN_SPEAKER,{TX_C_ROOTS_GROWN_0_0,TX_C_ROOTS_GROWN_0_1},1},
{TX_C_FOUR_LIGHTS_HINT_SPEAKER,{TX_C_FOUR_LIGHTS_HINT_0_0,TX_C_FOUR_LIGHTS_HINT_0_1},1},
{TX_C_FOUR_LIGHTS_SPEAKER,{TX_C_FOUR_LIGHTS_0_0,TX_C_FOUR_LIGHTS_0_1},1},
{TX_C_LAST_REST_SPEAKER,{TX_C_LAST_REST_0_0,TX_C_LAST_REST_0_1},1},
{TX_C_CORE_INTRO_SPEAKER,{TX_C_CORE_INTRO_0_0,TX_C_CORE_INTRO_0_1},1},
{TX_C_CORE_STONE_HINT_SPEAKER,{TX_C_CORE_STONE_HINT_0_0,TX_C_CORE_STONE_HINT_0_1},1},
{TX_C_CORE_WIND_HINT_SPEAKER,{TX_C_CORE_WIND_HINT_0_0,TX_C_CORE_WIND_HINT_0_1},1},
{TX_C_CORE_FIRE_HINT_SPEAKER,{TX_C_CORE_FIRE_HINT_0_0,TX_C_CORE_FIRE_HINT_0_1},1},
{TX_C_CORE_RELEASE_SPEAKER,{TX_C_CORE_RELEASE_0_0,TX_C_CORE_RELEASE_0_1,TX_C_CORE_RELEASE_1_0,TX_C_CORE_RELEASE_1_1},2},
{TX_C_ELDER_FINAL_SPEAKER,{TX_C_ELDER_FINAL_0_0,TX_C_ELDER_FINAL_0_1,TX_C_ELDER_FINAL_1_0,TX_C_ELDER_FINAL_1_1,TX_C_ELDER_FINAL_2_0,TX_C_ELDER_FINAL_2_1},3},
{TX_C_ENDING_FRIENDS_SPEAKER,{TX_C_ENDING_FRIENDS_0_0,TX_C_ENDING_FRIENDS_0_1,TX_C_ENDING_FRIENDS_1_0,TX_C_ENDING_FRIENDS_1_1},2},
{TX_C_ELDER_POSTGAME_SPEAKER,{TX_C_ELDER_POSTGAME_0_0,TX_C_ELDER_POSTGAME_0_1},1},
{TX_C_ELDER_CHIME_SPEAKER,{TX_C_ELDER_CHIME_0_0,TX_C_ELDER_CHIME_0_1},1},
{TX_C_GROVE_POSTCLEAR_SPEAKER,{TX_C_GROVE_POSTCLEAR_0_0,TX_C_GROVE_POSTCLEAR_0_1},1},
};
