#include "southern_creature_art.h"
/* Generated original ROM pixels. */
#include "southern_creature_art_data/part_000.inc"
#include "southern_creature_art_data/part_001.inc"
#include "southern_creature_art_data/part_002.inc"
#include "southern_creature_art_data/part_003.inc"
#include "southern_creature_art_data/part_004.inc"
#include "southern_creature_art_data/part_005.inc"
#include "southern_creature_art_data/part_006.inc"
#include "southern_creature_art_data/part_007.inc"
#include "southern_creature_art_data/part_008.inc"
#include "southern_creature_art_data/part_009.inc"
#include "southern_creature_art_data/part_010.inc"
#include "southern_creature_art_data/part_011.inc"

int southern_creature_art_index(unsigned int form_id) {
    switch(form_id) {
    case 25: return SOUTHERN_CREATURE_TANGLEAPER;
    case 26: return SOUTHERN_CREATURE_BOUGHVAULT;
    case 28: return SOUTHERN_CREATURE_DUNEROLL;
    case 29: return SOUTHERN_CREATURE_DUNESCOOP;
    case 79: return SOUTHERN_CREATURE_SKIMKIP;
    case 80: return SOUTHERN_CREATURE_SAILSKIP;
    case 81: return SOUTHERN_CREATURE_WARMCROAK;
    case 82: return SOUTHERN_CREATURE_BELLOWSWELL;
    case 83: return SOUTHERN_CREATURE_SHELLWADDLE;
    case 84: return SOUTHERN_CREATURE_VAULTBACK;
    case 85: return SOUTHERN_CREATURE_CLIPMANTIS;
    case 86: return SOUTHERN_CREATURE_FOILSCYTHE;
    case 87: return SOUTHERN_CREATURE_SWAYLEMUR;
    case 88: return SOUTHERN_CREATURE_CANOPETAIL;
    case 89: return SOUTHERN_CREATURE_RILLNEWT;
    case 90: return SOUTHERN_CREATURE_VEILCREST;
    case 91: return SOUTHERN_CREATURE_GLIMMERBAT;
    case 92: return SOUTHERN_CREATURE_FLAREFAN;
    case 93: return SOUTHERN_CREATURE_NEEDLETROT;
    case 94: return SOUTHERN_CREATURE_QUILLSTRIDE;
    default: return -1;
    }
}
const unsigned char *southern_creature_art_frame(unsigned int form_id,unsigned int direction,unsigned int frame) {
    int i=southern_creature_art_index(form_id);
    if(i<0 || direction>=4 || frame>=4) return (const unsigned char *)0;
    return southern_creature_direction_frames[i][direction][frame];
}
const unsigned char *southern_creature_art_ability_frame(unsigned int form_id,unsigned int direction,unsigned int pose) {
    int i=southern_creature_art_index(form_id);
    if(i<0 || direction>=4 || pose>=2) return (const unsigned char *)0;
    return southern_creature_ability_frames[i][direction][pose];
}
const unsigned char *southern_creature_art_portrait(unsigned int form_id) {
    int i=southern_creature_art_index(form_id);
    return i<0 ? (const unsigned char *)0 : southern_creature_portraits[i];
}
