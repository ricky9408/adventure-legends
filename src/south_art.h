/* Generated original Southern chapter art. */
#ifndef EMBERBOND_SOUTH_ART_H
#define EMBERBOND_SOUTH_ART_H
#define SOUTH_ART_FIRST_ROOM 30
#define SOUTH_ART_ROOM_COUNT 8
#define SOUTH_ART_FOOT_RADIUS 5
typedef struct { short x,y,w,h; } SouthArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const SouthArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } SouthArtRoom;
extern const SouthArtRoom south_art_rooms[SOUTH_ART_ROOM_COUNT];
/* Exact radius-five collision: rows[y] is a u16 offset into records
 * [count,lo0,hi0,...], with sorted merged half-open x intervals. */
enum {
 SOUTH_SPR_GUIDE = 0,
 SOUTH_SPR_TAILOR = 1,
 SOUTH_SPR_MARKET = 2,
 SOUTH_SPR_RAIN = 3,
 SOUTH_SPR_PORTER = 4,
 SOUTH_SPR_CURATOR = 5,
 SOUTH_SPR_REST = 6,
 SOUTH_SPR_FERRY = 7,
 SOUTH_SPR_MIRROR_SLASH = 8,
 SOUTH_SPR_MIRROR_BACK = 9,
 SOUTH_SPR_HOOD = 10,
 SOUTH_SPR_SOCKET = 11,
 SOUTH_SPR_CLOCK = 12,
 SOUTH_SPR_SHADE_CLOSED = 13,
 SOUTH_SPR_SHADE_OPEN = 14,
 SOUTH_SPR_RAIN_PIPE = 15,
 SOUTH_SPR_HANDLE = 16,
 SOUTH_SPR_TRIAL = 17,
 SOUTH_SPR_CATCH = 18,
 SOUTH_SPR_ROOT = 19,
 SOUTH_SPR_DRAIN = 20,
 SOUTH_SPR_RIPPLE = 21,
 SOUTH_SPR_RESET = 22,
 SOUTH_SPR_TORN = 23,
 SOUTH_SPR_AWNING = 24,
 SOUTH_SPR_GATE = 25,
 SOUTH_SPR_WATER_LENS = 26,
 SOUTH_SPR_NOTICE = 27,
 SOUTH_SPR_RECEIVER = 28,
 SOUTH_SPR_CLOTH = 29,
 SOUTH_SPR_PLATE = 30,
 SOUTH_SPR_CORD = 31,
 SOUTH_SPR_BEACON = 32,
 SOUTH_SPR_MACHINE_IDLE = 33,
 SOUTH_SPR_MACHINE_WARN = 34,
 SOUTH_SPR_MACHINE_OPEN = 35,
 SOUTH_SPR_DONE = 36,
 SOUTH_SPR_REST_LIT = 37,
 SOUTH_SPR_COUNT = 38
};
extern const unsigned char south_sprites[SOUTH_SPR_COUNT][256];
extern const unsigned char south_background_sunlace_anchorage[153600];
extern const unsigned char south_background_sunlace_anchorage_odd[153600];
extern const unsigned char south_background_frondshore_commons[153600];
extern const unsigned char south_background_frondshore_commons_odd[153600];
extern const unsigned char south_background_awning_loft[38400];
extern const unsigned char south_background_chalkspring_hollow[38400];
extern const unsigned char south_background_light_intake[38400];
extern const unsigned char south_background_split_shade_walk[38400];
extern const unsigned char south_background_turning_bough_gallery[38400];
extern const unsigned char south_background_sunwell_crown[38400];
#endif
