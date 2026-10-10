#ifndef EMBER_JOURNEY_MAP_H
#define EMBER_JOURNEY_MAP_H
/* Read-only journal view. No new visits, travel, saves or puzzle actions. */
enum { JOURNEY_ROAD, JOURNEY_DOOR, JOURNEY_STAIRS, JOURNEY_FERRY,
       JOURNEY_LIFT, JOURNEY_DIVE, JOURNEY_PASSAGE };
enum { JOURNEY_N, JOURNEY_E, JOURNEY_S, JOURNEY_W, JOURNEY_NE,
       JOURNEY_SE, JOURNEY_SW, JOURNEY_NW, JOURNEY_CENTER,
       JOURNEY_N_LEFT, JOURNEY_N_RIGHT, JOURNEY_E_TOP, JOURNEY_E_BOTTOM,
       JOURNEY_S_LEFT, JOURNEY_S_RIGHT, JOURNEY_W_TOP, JOURNEY_W_BOTTOM };
typedef struct JourneyMapExit {
 unsigned char target,kind,direction,open,named;
} JourneyMapExit;
int journey_map_exit(unsigned area,unsigned index,JourneyMapExit *out);
int journey_map_is_known(unsigned area);
unsigned journey_map_selected_place(void);
unsigned journey_map_selected_exit(void);
unsigned journey_map_overview(void);
void journey_map_reset(void);
/* Begin invalidates one paused-session snapshot; open resets only the view. */
void journey_map_begin(void);
void journey_map_open(void);
/* Returns zero only when B should leave Map for the journal hub. */
int journey_map_input(int input);
void journey_map_draw(void);
#endif
