/* Generated original Northern chapter art. */
#ifndef EMBERBOND_NORTH_ART_H
#define EMBERBOND_NORTH_ART_H
#define NORTH_ART_FIRST_ROOM 22
#define NORTH_ART_ROOM_COUNT 8
#define NORTH_ART_FOOT_RADIUS 5
typedef struct { short x,y,w,h; } NorthArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const NorthArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } NorthArtRoom;
extern const NorthArtRoom north_art_rooms[NORTH_ART_ROOM_COUNT];
/* Exact five-pixel-foot collision. collision_rows[y] indexes a u16 stream
 * record [count,lo0,hi0,...] of sorted merged half-open x intervals.
 * Bounds-check x/y first. No RAM unpacking or additional expansion. */
/* Row-major native 16px actors; zero transparent. Existing OBJ cache only. */
enum {
 NORTH_SPR_EDDA = 0,
 NORTH_SPR_TOVE = 1,
 NORTH_SPR_NERI = 2,
 NORTH_SPR_PELL = 3,
 NORTH_SPR_IVEN = 4,
 NORTH_SPR_RESET = 5,
 NORTH_SPR_HANDLE = 6,
 NORTH_SPR_HANDLE_DONE = 7,
 NORTH_SPR_CART_LIGHT = 8,
 NORTH_SPR_CART_HEAVY = 9,
 NORTH_SPR_JUNCTION_NS = 10,
 NORTH_SPR_JUNCTION_EW = 11,
 NORTH_SPR_WEIGHT_UP = 12,
 NORTH_SPR_WEIGHT_DOWN = 13,
 NORTH_SPR_REEL = 14,
 NORTH_SPR_REEL_HELD = 15,
 NORTH_SPR_BEARING = 16,
 NORTH_SPR_TENDER = 17,
 NORTH_SPR_MARKER = 18,
 NORTH_SPR_HEAT_COLD = 19,
 NORTH_SPR_HEAT_WARM = 20,
 NORTH_SPR_CHART_DAMP = 21,
 NORTH_SPR_CHART_DRY = 22,
 NORTH_SPR_REST = 23,
 NORTH_SPR_REST_LIT = 24,
 NORTH_SPR_FERRY_SIGN = 25,
 NORTH_SPR_MACHINE_IDLE = 26,
 NORTH_SPR_MACHINE_WARN = 27,
 NORTH_SPR_MACHINE_OPEN = 28,
 NORTH_SPR_BEACON_LIT = 29,
 NORTH_SPR_FORECAST = 30,
 NORTH_SPR_SOCKET = 31,
 NORTH_SPR_COUNT = 32
};
extern const unsigned char north_sprites[NORTH_SPR_COUNT][256];
extern const unsigned char north_background_hearthwake_quay[153600];
extern const unsigned char north_background_hearthwake_quay_odd[153600];
extern const unsigned char north_background_headland_roads[153600];
extern const unsigned char north_background_headland_roads_odd[153600];
extern const unsigned char north_background_boathouse_gallery[38400];
extern const unsigned char north_background_kiln_chart_store[38400];
extern const unsigned char north_background_loading_hall[38400];
extern const unsigned char north_background_crossbeam_chamber[38400];
extern const unsigned char north_background_relay_gallery[38400];
extern const unsigned char north_background_beacon_crown[38400];
#endif
