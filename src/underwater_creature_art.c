#include "underwater_creature_art.h"
/* Original immutable native pixel arrays. */
#include "underwater_creature_art_data/part_000.inc"
#include "underwater_creature_art_data/part_001.inc"
#include "underwater_creature_art_data/part_002.inc"
#include "underwater_creature_art_data/part_003.inc"
#include "underwater_creature_art_data/part_004.inc"
#include "underwater_creature_art_data/part_005.inc"
#include "underwater_creature_art_data/part_006.inc"
#include "underwater_creature_art_data/part_007.inc"
#include "underwater_creature_art_data/part_008.inc"
#include "underwater_creature_art_data/part_009.inc"
#include "underwater_creature_art_data/part_010.inc"
#include "underwater_creature_art_data/part_011.inc"
#include "underwater_creature_art_data/part_012.inc"
#include "underwater_creature_art_data/part_013.inc"
#include "underwater_creature_art_data/part_014.inc"
#include "underwater_creature_art_data/part_015.inc"
#include "underwater_creature_art_data/part_016.inc"

int underwater_creature_art_index(unsigned int form_id) {
    switch (form_id) {
    case 49: return UNDERWATER_CREATURE_INKBUD;
    case 50: return UNDERWATER_CREATURE_SCRIPTCUTTLE;
    case 51: return UNDERWATER_CREATURE_FANFOLIO;
    case 52: return UNDERWATER_CREATURE_BOBCLAM;
    case 53: return UNDERWATER_CREATURE_KEELCASKET;
    case 54: return UNDERWATER_CREATURE_CROWNFLOAT;
    case 55: return UNDERWATER_CREATURE_FRONDFOAL;
    case 56: return UNDERWATER_CREATURE_TRELLISSEER;
    case 57: return UNDERWATER_CREATURE_BOWERCOIL;
    case 58: return UNDERWATER_CREATURE_RIMLET;
    case 59: return UNDERWATER_CREATURE_GATESHIELD;
    case 60: return UNDERWATER_CREATURE_STENCILBACK;
    case 61: return UNDERWATER_CREATURE_VENTPLUME;
    case 62: return UNDERWATER_CREATURE_HALOWORM;
    case 63: return UNDERWATER_CREATURE_TRAILWICK;
    case 64: return UNDERWATER_CREATURE_PALMSTAR;
    case 65: return UNDERWATER_CREATURE_CROSSBLOOM;
    case 66: return UNDERWATER_CREATURE_FOLDRUNNER;
    case 67: return UNDERWATER_CREATURE_LINKEEL;
    case 68: return UNDERWATER_CREATURE_HINGEJAW;
    case 69: return UNDERWATER_CREATURE_CLASPCOIL;
    case 70: return UNDERWATER_CREATURE_COMBGLEAM;
    case 71: return UNDERWATER_CREATURE_VEILGLASS;
    case 72: return UNDERWATER_CREATURE_TRIADOME;
    default: return -1;
    }
}
const unsigned char *underwater_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame) {
    int i = underwater_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || frame >= 4) return (const unsigned char *)0;
    return underwater_creature_direction_frames[i][direction][frame];
}
const unsigned char *underwater_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose) {
    int i = underwater_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || pose >= 3) return (const unsigned char *)0;
    return underwater_creature_ability_frames[i][direction][pose];
}
const unsigned char *underwater_creature_art_portrait(unsigned int form_id) {
    int i = underwater_creature_art_index(form_id);
    return i < 0 ? (const unsigned char *)0 : underwater_creature_portraits[i];
}
