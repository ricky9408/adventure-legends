/* Generated native art; edit assets/generate_horizons_creatures.py. */
#ifndef EMBERBOND_HORIZONS_CREATURE_ART_H
#define EMBERBOND_HORIZONS_CREATURE_ART_H
#define HORIZONS_CREATURE_ART_COUNT 16
#define HORIZONS_CREATURE_ART_FRAME_BYTES 256
#define HORIZONS_CREATURE_ART_PORTRAIT_BYTES 1024
#define HORIZONS_CREATURE_ART_DIRECTION_COUNT 4
#define HORIZONS_CREATURE_ART_WALK_FRAME_COUNT 4
#define HORIZONS_CREATURE_ART_ABILITY_FRAME_COUNT 3
#define HORIZONS_CREATURE_ART_DATA_BYTES 131088
#define HORIZONS_CREATURE_ART_ROM_BUDGET_BYTES 134144
enum { HORIZONS_CREATURE_LINTAIL, HORIZONS_CREATURE_LOOMARTEN, HORIZONS_CREATURE_CINDERCUP, HORIZONS_CREATURE_MANTLEWICK, HORIZONS_CREATURE_TALUSNIP, HORIZONS_CREATURE_STRATODILLO, HORIZONS_CREATURE_GLEAMRAY, HORIZONS_CREATURE_FOLDCURRENT, HORIZONS_CREATURE_RIVETUSK, HORIZONS_CREATURE_FURLACE, HORIZONS_CREATURE_KILNSPOKE, HORIZONS_CREATURE_CHALKOX, HORIZONS_CREATURE_TINSHEAR, HORIZONS_CREATURE_RIPPLEBACK, HORIZONS_CREATURE_TETHERASP, HORIZONS_CREATURE_CYMBALOP };
/* Stable form IDs: 105-120. No catalog or unlock changes.
 * Directions: down/up/left/right; four walk beats, three ability poses (anticipation/release/settle).
 * Native row-major 8bpp existing game_palette indices; zero is transparent.
 * Field anchor is (8,8). All pixel arrays and IDs are const ROM.
 * No heap, mutable RAM, BSS, IWRAM, palette upload, or persistent OBJ allocation.
 * These functions return pixels only. The caller's renderer owns signed
 * screen-coordinate clipping before any framebuffer or OBJ write.
 */
extern const unsigned char horizons_creature_form_ids[HORIZONS_CREATURE_ART_COUNT];
extern const unsigned char horizons_creature_direction_frames[HORIZONS_CREATURE_ART_COUNT][4][4][256];
extern const unsigned char horizons_creature_ability_frames[HORIZONS_CREATURE_ART_COUNT][4][3][256];
extern const unsigned char horizons_creature_portraits[HORIZONS_CREATURE_ART_COUNT][1024];
/* Unsupported IDs return -1/NULL. Invalid directions/frames return NULL.
 * Unsigned arguments deliberately reject wrapped negative int inputs too.
 * Returned pointers are immutable, with static ROM lifetime.
 */
int horizons_creature_art_index(unsigned int form_id);
const unsigned char *horizons_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame);
const unsigned char *horizons_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose);
const unsigned char *horizons_creature_art_portrait(unsigned int form_id);
#endif
