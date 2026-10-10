/* Generated original The Roads That Stay pixels; no new RAM allocation. */
#ifndef EMBERBOND_COVENANTS_ART_H
#define EMBERBOND_COVENANTS_ART_H
#define COVENANTS_ART_FIRST_ROOM 70
#define COVENANTS_ART_ROOM_COUNT 8
#define COVENANTS_ART_FOOT_RADIUS 5
typedef struct { short x,y,w,h; } CovenantsArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const CovenantsArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } CovenantsArtRoom;
/* collision_rows[y] is an offset into half-open merged x intervals:
 * [count,lo0,hi0,...]. This already expands every static solid by radius5.
 * Dynamic objects must be tested separately with that identical foot rule.
 * bitmap_odd exists ONLY when width>240, no buffer or unpack step needed. */
extern const CovenantsArtRoom covenants_art_rooms[COVENANTS_ART_ROOM_COUNT];
/* Optional practice only: half-open allowed CENTER strips, indexed area-70.
 * Paint the visible plank five pixels beyond each edge for the full foot. */
extern const short covenants_practice_shortcuts[COVENANTS_ART_ROOM_COUNT][4];
enum {
 COVENANTS_SPR_STEWARD=0,
 COVENANTS_SPR_GROWER=1,
 COVENANTS_SPR_KILN_KEEPER=2,
 COVENANTS_SPR_WALKER=3,
 COVENANTS_SPR_REPAIRER=4,
 COVENANTS_SPR_SEED_KEEPER=5,
 COVENANTS_SPR_FERRY_KEEPER=6,
 COVENANTS_SPR_WATCHER=7,
 COVENANTS_SPR_NEIGHBOR=8,
 COVENANTS_SPR_PASSENGER=9,
 COVENANTS_SPR_REST=10,
 COVENANTS_SPR_REST_LIT=11,
 COVENANTS_SPR_RESET=12,
 COVENANTS_SPR_NOTICE=13,
 COVENANTS_SPR_MANUAL=14,
 COVENANTS_SPR_FULFILLED=15,
 COVENANTS_SPR_INVITE=16,
 COVENANTS_SPR_WAITING_PLACE=17,
 COVENANTS_SPR_STRAINER=18,
 COVENANTS_SPR_HOT_PLATE=19,
 COVENANTS_SPR_WARM_SEAM=20,
 COVENANTS_SPR_BALLAST=21,
 COVENANTS_SPR_QUIET_PIN=22,
 COVENANTS_SPR_WATER_INLET=23,
 COVENANTS_SPR_LENS=24,
 COVENANTS_SPR_SHADE_SCREEN=25,
 COVENANTS_SPR_FERRY=26,
 COVENANTS_SPR_VENT_OPEN=27,
 COVENANTS_SPR_VENT_CLOSED=28,
 COVENANTS_SPR_SHUTTER=29,
 COVENANTS_SPR_SHUTTER_LOOSE=30,
 COVENANTS_SPR_BOWL=31,
 COVENANTS_SPR_BOWL_COOL=32,
 COVENANTS_SPR_PORCH_LEFT=33,
 COVENANTS_SPR_PORCH_RIGHT=34,
 COVENANTS_SPR_PORCH_MARKS=35,
 COVENANTS_SPR_TRIAL=36,
 COVENANTS_SPR_PRACTICE=37,
 COVENANTS_SPR_WALKER_STEP_A=38,
 COVENANTS_SPR_WALKER_STEP_B=39,
 COVENANTS_SPR_SEED_KEEPER_STEP_A=40,
 COVENANTS_SPR_SEED_KEEPER_STEP_B=41,
 COVENANTS_SPR_PASSENGER_STEP_A=42,
 COVENANTS_SPR_PASSENGER_STEP_B=43,
 COVENANTS_SPR_COUNT=44
};
extern const unsigned char covenants_sprites[COVENANTS_SPR_COUNT][256];
#endif
