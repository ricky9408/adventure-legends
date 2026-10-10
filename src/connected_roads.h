#ifndef EMBERBOND_CONNECTED_ROADS_H
#define EMBERBOND_CONNECTED_ROADS_H
/* World-space seams, generated from the same manifest as the authored roads.
 * Saved room/spawn values remain unchanged; arrival pixels are volatile. */
enum { ROAD_NORTH,ROAD_EAST,ROAD_SOUTH,ROAD_WEST };
enum { ROAD_GATE_NONE,ROAD_GATE_GROVE,ROAD_GATE_SKY,ROAD_GATE_REGION,
 ROAD_GATE_NORTH,ROAD_GATE_SOUTH,ROAD_GATE_MAGMA,ROAD_GATE_UNDERWATER,
 ROAD_GATE_RETURN,ROAD_GATE_HORIZONS,ROAD_GATE_COVENANTS };
enum { ROAD_FOOT=5,ROAD_EDGE_STRIP=32 };
enum { ROAD_ARRIVAL_ONLY=1 };
typedef struct {
 unsigned char room,target,spawn,edge,gate,entry_safe;
 unsigned short width,height;
 short low,high,center,target_center,arrival_x,arrival_y;
 unsigned char barrier_inset,reserved;
} ConnectedRoad;
typedef struct {
 unsigned char room,target,spawn,edge,gate,reserved;
 short x,y,w,h,arrival_x,arrival_y;
} ConnectedDoor;
extern const ConnectedRoad connected_roads[];
extern const unsigned connected_road_count;
extern const ConnectedDoor connected_doors[];
extern const unsigned connected_door_count;
/* Returned range is [first,end), or empty for an invalid/unmanaged room. */
void connected_road_range(unsigned room,unsigned *first,unsigned *end);
int connected_road_managed(unsigned room,unsigned target);
int connected_road_distance(const ConnectedRoad *r,int x,int y);
int connected_road_contains(const ConnectedRoad *r,int x,int y,int margin);
int connected_road_outward(const ConnectedRoad *r,unsigned held);
/* -1 means the original chapter geometry remains authoritative. */
int connected_road_point(const ConnectedRoad *r,int x,int y,int open);
int connected_road_box(const ConnectedRoad *r,int x0,int y0,int x1,int y1);
void connected_road_arrival(const ConnectedRoad *r,int x,int y,int *ax,int *ay);
/* Weak bridge hooks preserve historical standalone chapter test linkage. */
extern int game_road_collision(unsigned area,int x,int y) __attribute__((weak));
extern int game_road_box_added(unsigned area,int x0,int y0,int x1,int y1) __attribute__((weak));
extern int game_road_box_touched(unsigned area,int x0,int y0,int x1,int y1) __attribute__((weak));
extern int game_road_managed(unsigned source,unsigned target) __attribute__((weak));
#endif
