#include "return_creature_art.h"
/* Original immutable native pixel arrays. */
#include "return_creature_art_data/part_000.inc"
#include "return_creature_art_data/part_001.inc"
#include "return_creature_art_data/part_002.inc"
#include "return_creature_art_data/part_003.inc"
#include "return_creature_art_data/part_004.inc"
#include "return_creature_art_data/part_005.inc"
#include "return_creature_art_data/part_006.inc"
#include "return_creature_art_data/part_007.inc"
#include "return_creature_art_data/part_008.inc"
#include "return_creature_art_data/part_009.inc"
#include "return_creature_art_data/part_010.inc"

int return_creature_art_index(unsigned int form_id) {
    switch (form_id) {
    case 3: return RETURN_CREATURE_HOMURA_WAYHEARTH;
    case 6: return RETURN_CREATURE_MIDORI_ORCHARDKEEPER;
    case 9: return RETURN_CREATURE_FUURI_SKYHEM;
    case 12: return RETURN_CREATURE_KOHAKU_WAYSTONE;
    case 15: return RETURN_CREATURE_RIVERTURN;
    case 17: return RETURN_CREATURE_BELLSTRIDE;
    case 18: return RETURN_CREATURE_PEALWARDEN;
    case 21: return RETURN_CREATURE_ARBOURLOOM;
    case 24: return RETURN_CREATURE_HEARTHROVER;
    case 27: return RETURN_CREATURE_CROWNLEAP;
    case 30: return RETURN_CREATURE_TERRASHAPER;
    case 101: return RETURN_CREATURE_HINGELET;
    case 102: return RETURN_CREATURE_HUSHHINGE;
    case 103: return RETURN_CREATURE_RILLKITE;
    case 104: return RETURN_CREATURE_WAKEBRAID;
    default: return -1;
    }
}
const unsigned char *return_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame) {
    int i = return_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || frame >= 4) return (const unsigned char *)0;
    return return_creature_direction_frames[i][direction][frame];
}
const unsigned char *return_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose) {
    int i = return_creature_art_index(form_id);
    if (i < 0 || direction >= 4 || pose >= 3) return (const unsigned char *)0;
    return return_creature_ability_frames[i][direction][pose];
}
const unsigned char *return_creature_art_portrait(unsigned int form_id) {
    int i = return_creature_art_index(form_id);
    return i < 0 ? (const unsigned char *)0 : return_creature_portraits[i];
}
