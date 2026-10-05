#ifndef EMBERBOND_TRIALS_H
#define EMBERBOND_TRIALS_H
#include "creatures.h"
/* Optional personal trials. No save5 quest/equipment reservation is used.
 * Engine calls these before indexing campaign_rooms[room-4].
 * Coordinates: grove=480x320 WORLD coordinates; rooms14/15=240x160 SCREEN
 * coordinates. All points are object/player centers. Face: down,up,left,right.
 * Engine owns input cooldown/summoning, room changes, messages and save_game.
 * Every mutation increments trials_revision and progression_revision.
 */
enum { TRIAL_ROOM_WIND=14, TRIAL_ROOM_STONE=15, TRIAL_ROOM_COUNT=16 };
enum TrialEvent {
 TRIAL_NONE=0, TRIAL_INSPECT, TRIAL_RESTORED, TRIAL_ROTATED, TRIAL_PUSHED,
 TRIAL_RESET, TRIAL_WRONG_POWER, TRIAL_BLOCKED, TRIAL_NEED_PLATES,
 TRIAL_ALREADY_DONE, TRIAL_COMPLETE_HOMURA, TRIAL_COMPLETE_MIDORI,
 TRIAL_COMPLETE_FUURI, TRIAL_COMPLETE_KOHAKU, TRIAL_ENTER_WIND,
 TRIAL_ENTER_STONE, TRIAL_EXIT
};
typedef struct { short x,y; unsigned char family,event; } TrialAid;
extern const TrialAid trial_grove_aids[6];
extern const short trial_vane_centers[3][2];
extern const short trial_plate_centers[2][2];
extern unsigned trials_revision;
/* Exported state is transient and deliberately absent from the save codec. */
extern unsigned char trial_vanes[3]; /* 0 north,1 east,2 south,3 west */
extern short trial_parcels[2][2];
void trials_enter(unsigned room); /* Reset partial puzzle; completed state remains. */
int trials_is_room(unsigned room);
int trials_solid(unsigned room,int x,int y); /* includes +/-4 player foot */
int trials_interact(unsigned room,int x,int y,unsigned face);
int trials_power(unsigned room,int x,int y,unsigned spirit);
/* Returns 4/9 in optional south threshold, -1 elsewhere. Caller checks DOWN
 * plus its transition lock. Arrival=(120,132); return=(204,86)/(208,140). */
int trials_exit(unsigned room,int x,int y);
/* Entrance centers: room4=(204,64), room9=(208,120). A, radius <19. */
int trials_complete(unsigned family);
int trials_done(unsigned family);
int trials_event_needs_save(int event);
int trials_wind_solved(void);
unsigned trials_plate_mask(void);
int trials_try_push(int x,int y,unsigned face); /* 1 push,0 no adjacent,-1 blocked */
const unsigned char *trials_background(unsigned room); /* opaque 240x160 or NULL */
const char *trials_room_name(unsigned room); /* ASCII label; engine localizes HUD */
/* Draw onto engine's current screen after background copy, before HUD.
 * Grove floor details use x-cam_x,y-cam_y across the full240x160 view.
 * Call only when the cached background redraws (revision is a cache key). */
void trials_draw_background(unsigned room,int cam_x,int cam_y);
/* Uses hardware OBJ_PROP slots0..5 in grove/trial rooms; slot5 ONLY in room4/9.
 * Engine obj_add already transforms world coordinates in room1, so this passes
 * WORLD coordinates unchanged. Camera arguments are documentation, not a
 * second transform. Call once per draw_actors after generic campaign props.
 * Reuses engine OBJ_HINT for nearby A prompts. */
void trials_draw_actors(unsigned room,int cam_x,int cam_y);
#endif
