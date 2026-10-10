#include "covenants_creature_art.h"
#include "covenants_creature_art_data/part_000.inc"
#include "covenants_creature_art_data/part_001.inc"
#include "covenants_creature_art_data/part_002.inc"
#include "covenants_creature_art_data/part_003.inc"
#include "covenants_creature_art_data/part_004.inc"
#include "covenants_creature_art_data/part_005.inc"

const struct CovenantsCreatureArtEntry covenants_creature_art_entries[8] = {
    {121,8,8,8,13,{8,6,9,7},{10,18,12}}, /* Stilltide Orrery */
    {122,8,8,8,13,{7,6,8,6},{9,14,11}}, /* Vowbough */
    {123,8,8,8,13,{12,9,12,10},{18,8,12}}, /* Kilnwhorl */
    {124,8,8,8,13,{11,9,12,9},{14,12,14}}, /* Cairnward */
    {125,8,8,8,13,{8,6,9,7},{10,15,12}}, /* Bellmantle */
    {126,8,8,8,13,{10,8,11,9},{12,14,13}}, /* Shadeweaver */
    {127,8,8,8,13,{8,8,5,7},{10,9,12}}, /* Tideplume */
    {128,8,8,8,13,{10,8,11,8},{15,18,14}}, /* Hearthmoth */
};
int covenants_creature_art_index(unsigned int form_id) {
    return form_id >= 121 && form_id <= 128 ? (int)(form_id - 121) : -1;
}
const unsigned char *covenants_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame) {
    int i=covenants_creature_art_index(form_id);
    return i < 0 || direction >= 4 || frame >= 4 ? (const unsigned char *)0 : covenants_creature_art_walk[i][direction][frame];
}
const unsigned char *covenants_creature_art_cast_frame(unsigned int form_id, unsigned int direction, unsigned int pose) {
    int i=covenants_creature_art_index(form_id);
    return i < 0 || direction >= 4 || pose >= 3 ? (const unsigned char *)0 : covenants_creature_art_cast[i][direction][pose];
}
const unsigned char *covenants_creature_art_portrait(unsigned int form_id) {
    int i=covenants_creature_art_index(form_id);
    return i < 0 ? (const unsigned char *)0 : covenants_creature_art_portraits[i];
}

unsigned covenants_creature_art_walk_index(unsigned form_id, unsigned active_ticks) {
    int i = covenants_creature_art_index(form_id);
    unsigned frame, total = 0;
    if (i < 0) return 0;
    for (frame = 0; frame < 4; frame++) total += covenants_creature_art_entries[i].walk_ticks[frame];
    active_ticks %= total;
    for (frame = 0; frame < 3; frame++) {
        unsigned duration = covenants_creature_art_entries[i].walk_ticks[frame];
        if (active_ticks < duration) break;
        active_ticks -= duration;
    }
    return frame;
}
