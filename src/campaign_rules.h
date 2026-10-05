#ifndef EMBER_CAMPAIGN_RULES_H
#define EMBER_CAMPAIGN_RULES_H
#include "ui.h"
typedef struct {short x,y,w,h;unsigned int flags;} CampaignBlock;
typedef struct {short x,y;unsigned char kind,power,range,input;unsigned int set,requires,lit,visible;short dialogue;unsigned char optional,hide_done;} CampaignObject;
typedef struct {short x,y;unsigned char kind,hp;} CampaignEnemy;
typedef struct {short name;unsigned char solid_count,block_count,object_count,enemy_count;const CampaignBlock *solids,*blocks;const CampaignObject *objects;const CampaignEnemy *enemies;unsigned int north_flags;unsigned char north_room,south_room,north_spawn,south_spawn,boss;} CampaignRoom;
typedef struct {short speaker;short lines[12];unsigned char pages;} CampaignDialogue;
enum {
 CD_ACT1_OPEN,
 CD_ELDER_ACT1,
 CD_GROVE_CLEAR,
 CD_WIND_JOIN,
 CD_LEGACY_RECAP,
 CD_ELDER_ACT2,
 CD_SKY_PATH_SIGN,
 CD_OPTIONAL_CHIME,
 CD_SKY_INTRO,
 CD_SAIL_BRIDGE,
 CD_SKY_VANE_OPEN,
 CD_PATROL_HINT,
 CD_PATROL_CLEAR,
 CD_RELAY_HINT,
 CD_RELAY_COMPLETE,
 CD_SKY_PREBOSS,
 CD_SKY_BOSS_INTRO,
 CD_SKY_BOSS_CLEAR,
 CD_STONE_JOIN,
 CD_ELDER_ACT3,
 CD_CORE_PATH_SIGN,
 CD_CORE_ARCH,
 CD_WEIGHTS_HINT,
 CD_ROOT_HINT,
 CD_ROOTS_GROWN,
 CD_FOUR_LIGHTS_HINT,
 CD_FOUR_LIGHTS,
 CD_LAST_REST,
 CD_CORE_INTRO,
 CD_CORE_STONE_HINT,
 CD_CORE_WIND_HINT,
 CD_CORE_FIRE_HINT,
 CD_CORE_RELEASE,
 CD_ELDER_FINAL,
 CD_ENDING_FRIENDS,
 CD_ELDER_POSTGAME,
 CD_ELDER_CHIME,
 CD_GROVE_POSTCLEAR,
 CD_COUNT};
#define CF_SKY_BRIDGE (1u<<0)
#define CF_SKY_VANE (1u<<1)
#define CF_SKY_PATROL_CLEAR (1u<<2)
#define CF_RELAY_LEFT (1u<<3)
#define CF_RELAY_RIGHT (1u<<4)
#define CF_RELAY_FIRE (1u<<5)
#define CF_CORE_PATH_OPEN (1u<<6)
#define CF_WEIGHT_WEST (1u<<7)
#define CF_WEIGHT_EAST (1u<<8)
#define CF_WELL_UNCAPPED (1u<<9)
#define CF_ROOT_CHANNEL (1u<<10)
#define CF_THORNS_BURNED (1u<<11)
#define CF_LAMP_FIRE (1u<<12)
#define CF_LAMP_NATURE (1u<<13)
#define CF_LAMP_WIND (1u<<14)
#define CF_LAMP_STONE (1u<<15)
extern const CampaignRoom campaign_rooms[10];
extern const CampaignDialogue campaign_dialogues[CD_COUNT];
#endif
