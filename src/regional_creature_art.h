/* Generated original art; edit assets/generate_regional_creatures.py. */
#ifndef EMBERBOND_REGIONAL_CREATURE_ART_H
#define EMBERBOND_REGIONAL_CREATURE_ART_H
#define REGIONAL_CREATURE_ART_COUNT 3
#define REGIONAL_CREATURE_ART_FRAME_BYTES 256
#define REGIONAL_CREATURE_ART_PORTRAIT_BYTES 1024
#define REGIONAL_CREATURE_ART_DIRECTION_COUNT 4
#define REGIONAL_CREATURE_ART_WALK_FRAME_COUNT 4
#define REGIONAL_CREATURE_ART_ABILITY_FRAME_COUNT 2
enum { REGIONAL_CREATURE_DEWSPINDLE, REGIONAL_CREATURE_TIDEWHEEL, REGIONAL_CREATURE_CHIMECLASP };
/* Stable form IDs 13,14,16. Directions down/up/left/right. Walk cycle 0..3;
 * ability 0 gathers/coils, 1 releases. Art only, no gameplay unlocks.
 * Native row-major 8bpp indices into game_palette; zero is transparent.
 * 16x16 field anchor (8,8); 32x32 portrait blits at top-left.
 * Immutable ROM data, no new palette, runtime buffers, data or BSS.
 */
extern const unsigned char regional_creature_form_ids[REGIONAL_CREATURE_ART_COUNT];
extern const unsigned char regional_creature_direction_frames[REGIONAL_CREATURE_ART_COUNT][4][4][REGIONAL_CREATURE_ART_FRAME_BYTES];
extern const unsigned char regional_creature_ability_frames[REGIONAL_CREATURE_ART_COUNT][4][2][REGIONAL_CREATURE_ART_FRAME_BYTES];
extern const unsigned char regional_creature_portraits[REGIONAL_CREATURE_ART_COUNT][REGIONAL_CREATURE_ART_PORTRAIT_BYTES];
/* Fail closed: unsupported stable IDs return -1/NULL. Out-of-range direction,
 * walk frame or ability pose also returns NULL; there is no implicit fallback.
 */
int regional_creature_art_index(unsigned int form_id);
const unsigned char *regional_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame);
const unsigned char *regional_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose);
const unsigned char *regional_creature_art_portrait(unsigned int form_id);
#endif
