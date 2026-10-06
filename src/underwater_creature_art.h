/* Generated native art; edit assets/generate_underwater_creatures.py. */
#ifndef EMBERBOND_UNDERWATER_CREATURE_ART_H
#define EMBERBOND_UNDERWATER_CREATURE_ART_H
#define UNDERWATER_CREATURE_ART_COUNT 24
#define UNDERWATER_CREATURE_ART_FRAME_BYTES 256
#define UNDERWATER_CREATURE_ART_PORTRAIT_BYTES 1024
#define UNDERWATER_CREATURE_ART_DIRECTION_COUNT 4
#define UNDERWATER_CREATURE_ART_WALK_FRAME_COUNT 4
#define UNDERWATER_CREATURE_ART_ABILITY_FRAME_COUNT 3
#define UNDERWATER_CREATURE_ART_DATA_BYTES 196632
#define UNDERWATER_CREATURE_ART_ROM_BUDGET_BYTES 198656
enum { UNDERWATER_CREATURE_INKBUD, UNDERWATER_CREATURE_SCRIPTCUTTLE, UNDERWATER_CREATURE_FANFOLIO, UNDERWATER_CREATURE_BOBCLAM, UNDERWATER_CREATURE_KEELCASKET, UNDERWATER_CREATURE_CROWNFLOAT, UNDERWATER_CREATURE_FRONDFOAL, UNDERWATER_CREATURE_TRELLISSEER, UNDERWATER_CREATURE_BOWERCOIL, UNDERWATER_CREATURE_RIMLET, UNDERWATER_CREATURE_GATESHIELD, UNDERWATER_CREATURE_STENCILBACK, UNDERWATER_CREATURE_VENTPLUME, UNDERWATER_CREATURE_HALOWORM, UNDERWATER_CREATURE_TRAILWICK, UNDERWATER_CREATURE_PALMSTAR, UNDERWATER_CREATURE_CROSSBLOOM, UNDERWATER_CREATURE_FOLDRUNNER, UNDERWATER_CREATURE_LINKEEL, UNDERWATER_CREATURE_HINGEJAW, UNDERWATER_CREATURE_CLASPCOIL, UNDERWATER_CREATURE_COMBGLEAM, UNDERWATER_CREATURE_VEILGLASS, UNDERWATER_CREATURE_TRIADOME };
/* Stable form IDs: 49-72. No catalog or unlock changes.
 * Directions: down/up/left/right; four walk beats, three ability poses (anticipation/release/settle).
 * Native row-major 8bpp existing game_palette indices; zero is transparent.
 * Field anchor is (8,8). All pixel arrays and IDs are const ROM.
 * No heap, mutable RAM, BSS, IWRAM, palette upload, or persistent OBJ allocation.
 * These functions return pixels only. The caller's renderer owns signed
 * screen-coordinate clipping before any framebuffer or OBJ write.
 */
extern const unsigned char underwater_creature_form_ids[UNDERWATER_CREATURE_ART_COUNT];
extern const unsigned char underwater_creature_direction_frames[UNDERWATER_CREATURE_ART_COUNT][4][4][256];
extern const unsigned char underwater_creature_ability_frames[UNDERWATER_CREATURE_ART_COUNT][4][3][256];
extern const unsigned char underwater_creature_portraits[UNDERWATER_CREATURE_ART_COUNT][1024];
/* Unsupported IDs return -1/NULL. Invalid directions/frames return NULL.
 * Unsigned arguments deliberately reject wrapped negative int inputs too.
 * Returned pointers are immutable, with static ROM lifetime.
 */
int underwater_creature_art_index(unsigned int form_id);
const unsigned char *underwater_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame);
const unsigned char *underwater_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose);
const unsigned char *underwater_creature_art_portrait(unsigned int form_id);
#endif
