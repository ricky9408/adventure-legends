/* Generated original Return world. Immutable shared palette. */
#ifndef EMBERBOND_RETURN_ART_H
#define EMBERBOND_RETURN_ART_H
#define RETURN_ART_FIRST_ROOM 54
#define RETURN_ART_ROOM_COUNT 8
#define RETURN_ART_FOOT_RADIUS 5
typedef struct { short x,y,w,h; } ReturnArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const ReturnArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } ReturnArtRoom;
extern const ReturnArtRoom return_art_rooms[8];
enum {
 RETURN_SPR_GARDENER=0,
 RETURN_SPR_BELLMAKER=1,
 RETURN_SPR_PORTER=2,
 RETURN_SPR_WEAVER=3,
 RETURN_SPR_GUIDE=4,
 RETURN_SPR_GARDENER_WORK=5,
 RETURN_SPR_PORTER_WORK=6,
 RETURN_SPR_REST=7,
 RETURN_SPR_REST_LIT=8,
 RETURN_SPR_RESET=9,
 RETURN_SPR_TRIAL=10,
 RETURN_SPR_NOTICE=11,
 RETURN_SPR_HANDLE=12,
 RETURN_SPR_RECEIVER=13,
 RETURN_SPR_SAIL=14,
 RETURN_SPR_SKIFF=15,
 RETURN_SPR_HEARTH=16,
 RETURN_SPR_ROOT=17,
 RETURN_SPR_LATCH=18,
 RETURN_SPR_DONE=19,
 RETURN_SPR_COUNT=20 };
extern const unsigned char return_sprites[20][256];
extern const unsigned char return_background_greenwake_common[153600];
extern const unsigned char return_background_greenwake_common_odd[153600];
extern const unsigned char return_background_bellfoundry_attic[38400];
extern const unsigned char return_background_overflow_gardens[153600];
extern const unsigned char return_background_overflow_gardens_odd[153600];
extern const unsigned char return_background_hearthwake_sailwalk[153600];
extern const unsigned char return_background_hearthwake_sailwalk_odd[153600];
extern const unsigned char return_background_sunlace_shade_terraces[153600];
extern const unsigned char return_background_sunlace_shade_terraces_odd[153600];
extern const unsigned char return_background_riverglass_landing[38400];
extern const unsigned char return_background_lampkeepers_maproom[38400];
extern const unsigned char return_background_tideglass_causeway[38400];
#endif
