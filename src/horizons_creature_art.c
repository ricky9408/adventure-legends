#include "horizons_creature_art.h"
/* Original immutable native pixel arrays. */
#include "horizons_creature_art_data/part_000.inc"
#include "horizons_creature_art_data/part_001.inc"
#include "horizons_creature_art_data/part_002.inc"
#include "horizons_creature_art_data/part_003.inc"
#include "horizons_creature_art_data/part_004.inc"
#include "horizons_creature_art_data/part_005.inc"
#include "horizons_creature_art_data/part_006.inc"
#include "horizons_creature_art_data/part_007.inc"
#include "horizons_creature_art_data/part_008.inc"
#include "horizons_creature_art_data/part_009.inc"
#include "horizons_creature_art_data/part_010.inc"

int horizons_creature_art_index(unsigned int form_id) {
    switch (form_id) {
    case 105: return HORIZONS_CREATURE_LINTAIL;
    case 106: return HORIZONS_CREATURE_LOOMARTEN;
    case 107: return HORIZONS_CREATURE_CINDERCUP;
    case 108: return HORIZONS_CREATURE_MANTLEWICK;
    case 109: return HORIZONS_CREATURE_TALUSNIP;
    case 110: return HORIZONS_CREATURE_STRATODILLO;
    case 111: return HORIZONS_CREATURE_GLEAMRAY;
    case 112: return HORIZONS_CREATURE_FOLDCURRENT;
    case 113: return HORIZONS_CREATURE_RIVETUSK;
    case 114: return HORIZONS_CREATURE_FURLACE;
    case 115: return HORIZONS_CREATURE_KILNSPOKE;
    case 116: return HORIZONS_CREATURE_CHALKOX;
    case 117: return HORIZONS_CREATURE_TINSHEAR;
    case 118: return HORIZONS_CREATURE_RIPPLEBACK;
    case 119: return HORIZONS_CREATURE_TETHERASP;
    case 120: return HORIZONS_CREATURE_CYMBALOP;
    default: return -1;
    }
}
const unsigned char *horizons_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame) {
    int i = horizons_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || frame >= 4) return (const unsigned char *)0;
    return horizons_creature_direction_frames[i][direction][frame];
}
const unsigned char *horizons_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose) {
    int i = horizons_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || pose >= 3) return (const unsigned char *)0;
    return horizons_creature_ability_frames[i][direction][pose];
}
const unsigned char *horizons_creature_art_portrait(unsigned int form_id) {
    int i = horizons_creature_art_index(form_id);
    return i < 0 ? (const unsigned char *)0 : horizons_creature_portraits[i];
}
