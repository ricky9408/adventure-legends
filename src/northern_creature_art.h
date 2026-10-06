/* Generated original art; edit assets/generate_northern_creatures.py. */
#ifndef EMBERBOND_NORTHERN_CREATURE_ART_H
#define EMBERBOND_NORTHERN_CREATURE_ART_H
#define NORTHERN_CREATURE_ART_COUNT 10
#define NORTHERN_CREATURE_ART_FRAME_BYTES 256
#define NORTHERN_CREATURE_ART_PORTRAIT_BYTES 1024
#define NORTHERN_CREATURE_ART_DIRECTION_COUNT 4
#define NORTHERN_CREATURE_ART_WALK_FRAME_COUNT 4
#define NORTHERN_CREATURE_ART_ABILITY_FRAME_COUNT 2
enum { NORTHERN_CREATURE_SPOOLBUD, NORTHERN_CREATURE_LOOMCROWN, NORTHERN_CREATURE_CINDERTRAY, NORTHERN_CREATURE_KILNBARROW, NORTHERN_CREATURE_KEELKIP, NORTHERN_CREATURE_WAKECRADLE, NORTHERN_CREATURE_CAIRNCRICKET, NORTHERN_CREATURE_ARCHSPRING, NORTHERN_CREATURE_RIVETFOIL, NORTHERN_CREATURE_GIMBALCLOAK };
/* Stable, noncontiguous form IDs: 19,20,22,23,73,74,75,76,77,78.
 * Directions: down/up/left/right. Four walk beats, two cast poses per direction.
 * Native row-major 8bpp palette indices. Transparent zero. Field anchor (8,8).
 * Existing 178-entry game_palette, no runtime palette mutation or buffers.
 * All art lives in const ROM: no mutable data/BSS. No gameplay unlocks.
 */
extern const unsigned char northern_creature_form_ids[NORTHERN_CREATURE_ART_COUNT];
extern const unsigned char northern_creature_direction_frames[NORTHERN_CREATURE_ART_COUNT][4][4][256];
extern const unsigned char northern_creature_ability_frames[NORTHERN_CREATURE_ART_COUNT][4][2][256];
extern const unsigned char northern_creature_portraits[NORTHERN_CREATURE_ART_COUNT][1024];
/* Unsupported IDs return -1/NULL. Invalid direction or pose returns NULL. */
int northern_creature_art_index(unsigned int form_id);
const unsigned char *northern_creature_art_frame(unsigned int form_id,unsigned int direction,unsigned int frame);
const unsigned char *northern_creature_art_ability_frame(unsigned int form_id,unsigned int direction,unsigned int pose);
const unsigned char *northern_creature_art_portrait(unsigned int form_id);
#endif
