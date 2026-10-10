/* Generated native art; edit assets/generate_return_creatures.py. */
#ifndef EMBERBOND_RETURN_CREATURE_ART_H
#define EMBERBOND_RETURN_CREATURE_ART_H
#define RETURN_CREATURE_ART_COUNT 15
#define RETURN_CREATURE_ART_FRAME_BYTES 256
#define RETURN_CREATURE_ART_PORTRAIT_BYTES 1024
#define RETURN_CREATURE_ART_DIRECTION_COUNT 4
#define RETURN_CREATURE_ART_WALK_FRAME_COUNT 4
#define RETURN_CREATURE_ART_ABILITY_FRAME_COUNT 3
#define RETURN_CREATURE_ART_DATA_BYTES 122895
#define RETURN_CREATURE_ART_ROM_BUDGET_BYTES 131072
enum { RETURN_CREATURE_HOMURA_WAYHEARTH, RETURN_CREATURE_MIDORI_ORCHARDKEEPER, RETURN_CREATURE_FUURI_SKYHEM, RETURN_CREATURE_KOHAKU_WAYSTONE, RETURN_CREATURE_RIVERTURN, RETURN_CREATURE_BELLSTRIDE, RETURN_CREATURE_PEALWARDEN, RETURN_CREATURE_ARBOURLOOM, RETURN_CREATURE_HEARTHROVER, RETURN_CREATURE_CROWNLEAP, RETURN_CREATURE_TERRASHAPER, RETURN_CREATURE_HINGELET, RETURN_CREATURE_HUSHHINGE, RETURN_CREATURE_RILLKITE, RETURN_CREATURE_WAKEBRAID };
/* Stable form IDs: 3,6,9,12,15,17,18,21,24,27,30,101-104. No catalog or unlock changes.
 * Directions: down/up/left/right; four walk beats, three ability poses (anticipation/release/settle).
 * Native row-major 8bpp existing game_palette indices; zero is transparent.
 * Field anchor is (8,8). All pixel arrays and IDs are const ROM.
 * No heap, mutable RAM, BSS, IWRAM, palette upload, or persistent OBJ allocation.
 * These functions return pixels only. The caller's renderer owns signed
 * screen-coordinate clipping before any framebuffer or OBJ write.
 */
extern const unsigned char return_creature_form_ids[RETURN_CREATURE_ART_COUNT];
extern const unsigned char return_creature_direction_frames[RETURN_CREATURE_ART_COUNT][4][4][256];
extern const unsigned char return_creature_ability_frames[RETURN_CREATURE_ART_COUNT][4][3][256];
extern const unsigned char return_creature_portraits[RETURN_CREATURE_ART_COUNT][1024];
/* Unsupported IDs return -1/NULL. Invalid directions/frames return NULL.
 * Unsigned arguments deliberately reject wrapped negative int inputs too.
 * Returned pointers are immutable, with static ROM lifetime.
 */
int return_creature_art_index(unsigned int form_id);
const unsigned char *return_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame);
const unsigned char *return_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose);
const unsigned char *return_creature_art_portrait(unsigned int form_id);
#endif
