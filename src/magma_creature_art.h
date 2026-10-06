/* Generated native art; edit assets/generate_magma_creatures.py. */
#ifndef EMBERBOND_MAGMA_CREATURE_ART_H
#define EMBERBOND_MAGMA_CREATURE_ART_H
#define MAGMA_CREATURE_ART_COUNT 24
#define MAGMA_CREATURE_ART_FRAME_BYTES 256
#define MAGMA_CREATURE_ART_PORTRAIT_BYTES 1024
#define MAGMA_CREATURE_ART_DIRECTION_COUNT 4
#define MAGMA_CREATURE_ART_WALK_FRAME_COUNT 4
#define MAGMA_CREATURE_ART_ABILITY_FRAME_COUNT 2
#define MAGMA_CREATURE_ART_DATA_BYTES 172056
#define MAGMA_CREATURE_ART_ROM_BUDGET_BYTES 174080
enum { MAGMA_CREATURE_COALCOIL, MAGMA_CREATURE_EMBERHELIX, MAGMA_CREATURE_HEARTHCROWN, MAGMA_CREATURE_SHARDIBEX, MAGMA_CREATURE_BRACEHORN, MAGMA_CREATURE_SPANRAM, MAGMA_CREATURE_TUFTPIKA, MAGMA_CREATURE_ROOTMUFFLE, MAGMA_CREATURE_SPOREVAULT, MAGMA_CREATURE_CHALKLUNG, MAGMA_CREATURE_BELLCUP, MAGMA_CREATURE_RUNNELRIBBON, MAGMA_CREATURE_ORELET, MAGMA_CREATURE_AUGERMOLE, MAGMA_CREATURE_PENDULUMOLE, MAGMA_CREATURE_ASHKITE, MAGMA_CREATURE_PLUMEHOPPER, MAGMA_CREATURE_HUSKDRIFTER, MAGMA_CREATURE_SCREEPEEK, MAGMA_CREATURE_STAIRTRUNK, MAGMA_CREATURE_MOSSMARCH, MAGMA_CREATURE_TRELLISLONG, MAGMA_CREATURE_DRIPURCHIN, MAGMA_CREATURE_DEWMEDUSA };
/* Stable form IDs: 31-48,95-100. No catalog or unlock changes.
 * Directions: down/up/left/right; four walk beats, two ability poses.
 * Native row-major 8bpp existing game_palette indices; zero is transparent.
 * Field anchor is (8,8). All pixel arrays and IDs are const ROM.
 * No heap, mutable RAM, BSS, IWRAM, palette upload, or persistent OBJ allocation.
 * These functions return pixels only. The caller's renderer owns signed
 * screen-coordinate clipping before any framebuffer or OBJ write.
 */
extern const unsigned char magma_creature_form_ids[MAGMA_CREATURE_ART_COUNT];
extern const unsigned char magma_creature_direction_frames[MAGMA_CREATURE_ART_COUNT][4][4][256];
extern const unsigned char magma_creature_ability_frames[MAGMA_CREATURE_ART_COUNT][4][2][256];
extern const unsigned char magma_creature_portraits[MAGMA_CREATURE_ART_COUNT][1024];
/* Unsupported IDs return -1/NULL. Invalid directions/frames return NULL.
 * Unsigned arguments deliberately reject wrapped negative int inputs too.
 * Returned pointers are immutable, with static ROM lifetime.
 */
int magma_creature_art_index(unsigned int form_id);
const unsigned char *magma_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame);
const unsigned char *magma_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose);
const unsigned char *magma_creature_art_portrait(unsigned int form_id);
#endif
