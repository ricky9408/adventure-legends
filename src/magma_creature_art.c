#include "magma_creature_art.h"
/* Original immutable native pixel arrays. */
#include "magma_creature_art_data/part_000.inc"
#include "magma_creature_art_data/part_001.inc"
#include "magma_creature_art_data/part_002.inc"
#include "magma_creature_art_data/part_003.inc"
#include "magma_creature_art_data/part_004.inc"
#include "magma_creature_art_data/part_005.inc"
#include "magma_creature_art_data/part_006.inc"
#include "magma_creature_art_data/part_007.inc"
#include "magma_creature_art_data/part_008.inc"
#include "magma_creature_art_data/part_009.inc"
#include "magma_creature_art_data/part_010.inc"
#include "magma_creature_art_data/part_011.inc"
#include "magma_creature_art_data/part_012.inc"
#include "magma_creature_art_data/part_013.inc"
#include "magma_creature_art_data/part_014.inc"

int magma_creature_art_index(unsigned int form_id) {
    switch (form_id) {
    case 31: return MAGMA_CREATURE_COALCOIL;
    case 32: return MAGMA_CREATURE_EMBERHELIX;
    case 33: return MAGMA_CREATURE_HEARTHCROWN;
    case 34: return MAGMA_CREATURE_SHARDIBEX;
    case 35: return MAGMA_CREATURE_BRACEHORN;
    case 36: return MAGMA_CREATURE_SPANRAM;
    case 37: return MAGMA_CREATURE_TUFTPIKA;
    case 38: return MAGMA_CREATURE_ROOTMUFFLE;
    case 39: return MAGMA_CREATURE_SPOREVAULT;
    case 40: return MAGMA_CREATURE_CHALKLUNG;
    case 41: return MAGMA_CREATURE_BELLCUP;
    case 42: return MAGMA_CREATURE_RUNNELRIBBON;
    case 43: return MAGMA_CREATURE_ORELET;
    case 44: return MAGMA_CREATURE_AUGERMOLE;
    case 45: return MAGMA_CREATURE_PENDULUMOLE;
    case 46: return MAGMA_CREATURE_ASHKITE;
    case 47: return MAGMA_CREATURE_PLUMEHOPPER;
    case 48: return MAGMA_CREATURE_HUSKDRIFTER;
    case 95: return MAGMA_CREATURE_SCREEPEEK;
    case 96: return MAGMA_CREATURE_STAIRTRUNK;
    case 97: return MAGMA_CREATURE_MOSSMARCH;
    case 98: return MAGMA_CREATURE_TRELLISLONG;
    case 99: return MAGMA_CREATURE_DRIPURCHIN;
    case 100: return MAGMA_CREATURE_DEWMEDUSA;
    default: return -1;
    }
}
const unsigned char *magma_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame) {
    int i = magma_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || frame >= 4) return (const unsigned char *)0;
    return magma_creature_direction_frames[i][direction][frame];
}
const unsigned char *magma_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose) {
    int i = magma_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || pose >= 2) return (const unsigned char *)0;
    return magma_creature_ability_frames[i][direction][pose];
}
const unsigned char *magma_creature_art_portrait(unsigned int form_id) {
    int i = magma_creature_art_index(form_id);
    return i < 0 ? (const unsigned char *)0 : magma_creature_portraits[i];
}
