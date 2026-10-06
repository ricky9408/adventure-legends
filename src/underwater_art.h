/* Generated original Underwater art. Frozen RGB555 palette; shared OBJ cache. */
#ifndef EMBERBOND_UNDERWATER_ART_H
#define EMBERBOND_UNDERWATER_ART_H
#define UNDERWATER_ART_FIRST_ROOM 46
#define UNDERWATER_ART_ROOM_COUNT 8
#define UNDERWATER_ART_FOOT_RADIUS 5
typedef struct { short x,y,w,h; } UnderwaterArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const UnderwaterArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } UnderwaterArtRoom;
extern const UnderwaterArtRoom underwater_art_rooms[UNDERWATER_ART_ROOM_COUNT];
/* Half-open solids. collision_rows[y] indexes [count,x0,x1,...] in
 * collision_bands. Entries already include the exact radius-five foot. */
/* Native row-major 16px glyphs, zero transparent. Stream existing OBJ slots. */
enum {
 UNDERWATER_SPR_KEEPER=0,
 UNDERWATER_SPR_SHELLWRIGHT=1,
 UNDERWATER_SPR_COOK=2,
 UNDERWATER_SPR_FRAMER=3,
 UNDERWATER_SPR_DANCER=4,
 UNDERWATER_SPR_KEEPER_WORK=5,
 UNDERWATER_SPR_WORKER_WORK=6,
 UNDERWATER_SPR_REST=7,
 UNDERWATER_SPR_REST_LIT=8,
 UNDERWATER_SPR_RESET=9,
 UNDERWATER_SPR_TRIAL=10,
 UNDERWATER_SPR_NOTICE=11,
 UNDERWATER_SPR_LEAF=12,
 UNDERWATER_SPR_SHELF=13,
 UNDERWATER_SPR_BAFFLE=14,
 UNDERWATER_SPR_GATE=15,
 UNDERWATER_SPR_DONE=16,
 UNDERWATER_SPR_GUARDIAN=17,
 UNDERWATER_SPR_GUARDIAN_WARN=18,
 UNDERWATER_SPR_GUARDIAN_OPEN=19,
 UNDERWATER_SPR_COUNT=20
};
extern const unsigned char underwater_sprites[UNDERWATER_SPR_COUNT][256];
extern const unsigned char underwater_background_nacreway[153600];
extern const unsigned char underwater_background_nacreway_odd[153600];
extern const unsigned char underwater_background_siltglass_commons[153600];
extern const unsigned char underwater_background_siltglass_commons_odd[153600];
extern const unsigned char underwater_background_kelp_promenade[153600];
extern const unsigned char underwater_background_kelp_promenade_odd[153600];
extern const unsigned char underwater_background_hollow_oyster_garden[38400];
extern const unsigned char underwater_background_palinode_vestibule[38400];
extern const unsigned char underwater_background_countercurrent_stacks[153600];
extern const unsigned char underwater_background_countercurrent_stacks_odd[153600];
extern const unsigned char underwater_background_listening_chamber[38400];
extern const unsigned char underwater_background_vestige_court[38400];
#endif
