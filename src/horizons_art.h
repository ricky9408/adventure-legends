/* Generated Shared Horizons original pixels. */
#ifndef EMBERBOND_HORIZONS_ART_H
#define EMBERBOND_HORIZONS_ART_H
typedef struct { short x,y,w,h; } HorizonsArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const HorizonsArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } HorizonsArtRoom;
extern const HorizonsArtRoom horizons_art_rooms[8];
enum {
 HORIZONS_SPR_HOST=0,
 HORIZONS_SPR_PORTER=1,
 HORIZONS_SPR_STORYTELLER=2,
 HORIZONS_SPR_SCRIBE=3,
 HORIZONS_SPR_JOINER=4,
 HORIZONS_SPR_HOST_WORK=5,
 HORIZONS_SPR_PORTER_WORK=6,
 HORIZONS_SPR_REST=7,
 HORIZONS_SPR_REST_LIT=8,
 HORIZONS_SPR_RESET=9,
 HORIZONS_SPR_TRIAL=10,
 HORIZONS_SPR_NOTICE=11,
 HORIZONS_SPR_HANDLE=12,
 HORIZONS_SPR_CUP=13,
 HORIZONS_SPR_CARRIAGE=14,
 HORIZONS_SPR_PANEL=15,
 HORIZONS_SPR_WAX=16,
 HORIZONS_SPR_BOWL=17,
 HORIZONS_SPR_LATCH=18,
 HORIZONS_SPR_DONE=19,
 HORIZONS_SPR_COUNT=20 };
extern const unsigned char horizons_sprites[20][256];
#endif
