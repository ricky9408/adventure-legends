/* Generated original evolved companion art; edit assets/generate_evolutions.py. */
#ifndef EMBERBOND_EVOLUTION_ART_H
#define EMBERBOND_EVOLUTION_ART_H
#define EVOLUTION_ART_COUNT 4
#define EVOLUTION_ART_FRAME_BYTES 256
#define EVOLUTION_ART_PORTRAIT_BYTES 1024
enum { EVOLUTION_HOMURA_HEARTHKEEPER, EVOLUTION_MIDORI_CANOPYKEEPER,
       EVOLUTION_FUURI_WINDWEAVER, EVOLUTION_KOHAKU_ARCHWARDEN };
/* Order is stable IDs 2,5,8,11. Directions: down, up, left, right.
 * Four frames: idle, first motion beat, raised/turning beat, second beat.
 * Row-major palette indices into existing game_palette; zero is transparent.
 * 16x16 field anchor is center (x-8,y-8); 32x32 portrait is top-left blitted.
 * All arrays are immutable ROM data. No new palette, buffers or BSS.
 * These sheets do not themselves enable evolution or change collision boxes.
 */
extern const unsigned char evolution_form_ids[EVOLUTION_ART_COUNT];
extern const unsigned char evolution_companion_direction_frames[EVOLUTION_ART_COUNT][4][4][EVOLUTION_ART_FRAME_BYTES];
extern const unsigned char evolution_portraits[EVOLUTION_ART_COUNT][EVOLUTION_ART_PORTRAIT_BYTES];
/* Fail closed: unknown stable ID returns -1/null; invalid direction/frame null. */
int evolution_art_index(unsigned int form_id);
const unsigned char *evolution_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame);
const unsigned char *evolution_art_portrait(unsigned int form_id);
#endif
