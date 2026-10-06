#include "northern_creature_art.h"
/* Generated original ROM pixels. */
#include "northern_creature_art_data/part_000.inc"
#include "northern_creature_art_data/part_001.inc"
#include "northern_creature_art_data/part_002.inc"
#include "northern_creature_art_data/part_003.inc"
#include "northern_creature_art_data/part_004.inc"
#include "northern_creature_art_data/part_005.inc"
#include "northern_creature_art_data/part_006.inc"

int northern_creature_art_index(unsigned int form_id) {
    switch(form_id) {
    case 19: return NORTHERN_CREATURE_SPOOLBUD;
    case 20: return NORTHERN_CREATURE_LOOMCROWN;
    case 22: return NORTHERN_CREATURE_CINDERTRAY;
    case 23: return NORTHERN_CREATURE_KILNBARROW;
    case 73: return NORTHERN_CREATURE_KEELKIP;
    case 74: return NORTHERN_CREATURE_WAKECRADLE;
    case 75: return NORTHERN_CREATURE_CAIRNCRICKET;
    case 76: return NORTHERN_CREATURE_ARCHSPRING;
    case 77: return NORTHERN_CREATURE_RIVETFOIL;
    case 78: return NORTHERN_CREATURE_GIMBALCLOAK;
    default: return -1;
    }
}
const unsigned char *northern_creature_art_frame(unsigned int form_id,unsigned int direction,unsigned int frame) {
    int i=northern_creature_art_index(form_id);
    if(i<0 || direction>=4 || frame>=4) return (const unsigned char *)0;
    return northern_creature_direction_frames[i][direction][frame];
}
const unsigned char *northern_creature_art_ability_frame(unsigned int form_id,unsigned int direction,unsigned int pose) {
    int i=northern_creature_art_index(form_id);
    if(i<0 || direction>=4 || pose>=2) return (const unsigned char *)0;
    return northern_creature_ability_frames[i][direction][pose];
}
const unsigned char *northern_creature_art_portrait(unsigned int form_id) {
    int i=northern_creature_art_index(form_id);
    return i<0 ? (const unsigned char *)0 : northern_creature_portraits[i];
}
