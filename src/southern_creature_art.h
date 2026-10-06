/* Generated original art; edit assets/generate_southern_creatures.py. */
#ifndef EMBERBOND_SOUTHERN_CREATURE_ART_H
#define EMBERBOND_SOUTHERN_CREATURE_ART_H
#define SOUTHERN_CREATURE_ART_COUNT 20
#define SOUTHERN_CREATURE_ART_FRAME_BYTES 256
#define SOUTHERN_CREATURE_ART_PORTRAIT_BYTES 1024
#define SOUTHERN_CREATURE_ART_DIRECTION_COUNT 4
#define SOUTHERN_CREATURE_ART_WALK_FRAME_COUNT 4
#define SOUTHERN_CREATURE_ART_ABILITY_FRAME_COUNT 2
enum { SOUTHERN_CREATURE_TANGLEAPER, SOUTHERN_CREATURE_BOUGHVAULT, SOUTHERN_CREATURE_DUNEROLL, SOUTHERN_CREATURE_DUNESCOOP, SOUTHERN_CREATURE_SKIMKIP, SOUTHERN_CREATURE_SAILSKIP, SOUTHERN_CREATURE_WARMCROAK, SOUTHERN_CREATURE_BELLOWSWELL, SOUTHERN_CREATURE_SHELLWADDLE, SOUTHERN_CREATURE_VAULTBACK, SOUTHERN_CREATURE_CLIPMANTIS, SOUTHERN_CREATURE_FOILSCYTHE, SOUTHERN_CREATURE_SWAYLEMUR, SOUTHERN_CREATURE_CANOPETAIL, SOUTHERN_CREATURE_RILLNEWT, SOUTHERN_CREATURE_VEILCREST, SOUTHERN_CREATURE_GLIMMERBAT, SOUTHERN_CREATURE_FLAREFAN, SOUTHERN_CREATURE_NEEDLETROT, SOUTHERN_CREATURE_QUILLSTRIDE };
/* Stable, noncontiguous form IDs: 25,26,28,29,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94.
 * Directions: down/up/left/right. Four walk beats, two cast poses per direction.
 * Native row-major 8bpp palette indices. Transparent zero. Field anchor (8,8).
 * Existing 178-entry game_palette, no runtime palette mutation or buffers.
 * All art lives in const ROM: no mutable data/BSS. No gameplay unlocks.
 */
extern const unsigned char southern_creature_form_ids[SOUTHERN_CREATURE_ART_COUNT];
extern const unsigned char southern_creature_direction_frames[SOUTHERN_CREATURE_ART_COUNT][4][4][256];
extern const unsigned char southern_creature_ability_frames[SOUTHERN_CREATURE_ART_COUNT][4][2][256];
extern const unsigned char southern_creature_portraits[SOUTHERN_CREATURE_ART_COUNT][1024];
/* Unsupported IDs return -1/NULL. Invalid direction or pose returns NULL. */
int southern_creature_art_index(unsigned int form_id);
const unsigned char *southern_creature_art_frame(unsigned int form_id,unsigned int direction,unsigned int frame);
const unsigned char *southern_creature_art_ability_frame(unsigned int form_id,unsigned int direction,unsigned int pose);
const unsigned char *southern_creature_art_portrait(unsigned int form_id);
#endif
