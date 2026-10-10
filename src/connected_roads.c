#include "connected_roads.h"
#include "connected_roads_data.inc"
void connected_road_range(unsigned room,unsigned *first,unsigned *end){
 unsigned a=0,b=0;if(room<78u){a=connected_road_ranges[room][0];b=connected_road_ranges[room][1];}
 if(first)*first=a;
 if(end)*end=b;
}
int connected_road_managed(unsigned room,unsigned target){unsigned i,end;/* Retired return shortcuts must not revive via old A/rectangle paths. */if((room==53&&target==46)||(room==45&&target==38))return 1;connected_road_range(room,&i,&end);for(;i<end;i++)if(connected_roads[i].target==target&&!(connected_roads[i].reserved&ROAD_ARRIVAL_ONLY))return 1;for(i=0;i<connected_door_count;i++)if(connected_doors[i].room==room&&connected_doors[i].target==target)return 1;return 0;}
int connected_road_distance(const ConnectedRoad*r,int x,int y){
 if(r->edge==ROAD_NORTH)return y;
 if(r->edge==ROAD_EAST)return (int)r->width-1-x;
 if(r->edge==ROAD_SOUTH)return (int)r->height-1-y;
 return x;
}
int connected_road_contains(const ConnectedRoad*r,int x,int y,int margin){
 int v=(r->edge==ROAD_NORTH||r->edge==ROAD_SOUTH)?x:y;
 return v>=r->low-margin&&v<r->high+margin;
}
int connected_road_outward(const ConnectedRoad*r,unsigned held){
 static const unsigned short bit[4]={64,16,128,32},opposite[4]={128,32,64,16};
 return (held&bit[r->edge])&&!(held&opposite[r->edge]);
}
int connected_road_point(const ConnectedRoad*r,int x,int y,int open){int d;
 if((unsigned)x>=r->width||(unsigned)y>=r->height||!connected_road_contains(r,x,y,0))return -1;
 d=connected_road_distance(r,x,y);if(d>=ROAD_EDGE_STRIP)return -1;
 if(d<ROAD_FOOT)return 1;
 return !open&&d<=(int)r->barrier_inset+ROAD_FOOT;
}
int connected_road_box(const ConnectedRoad*r,int x0,int y0,int x1,int y1){int l=0,t=0,rr=r->width-1,b=r->height-1;
 if(r->edge==ROAD_NORTH||r->edge==ROAD_SOUTH){l=r->low;rr=r->high-1;if(r->edge==ROAD_NORTH)b=ROAD_EDGE_STRIP-1;else t=r->height-ROAD_EDGE_STRIP;}
 else{t=r->low;b=r->high-1;if(r->edge==ROAD_WEST)rr=ROAD_EDGE_STRIP-1;else l=r->width-ROAD_EDGE_STRIP;}
 return x1>=l&&x0<=rr&&y1>=t&&y0<=b;
}
void connected_road_arrival(const ConnectedRoad*r,int x,int y,int*ax,int*ay){
 int v=(r->edge==ROAD_NORTH||r->edge==ROAD_SOUTH)?x:y,offset=v-r->center;
 if(offset<r->low-r->center)offset=r->low-r->center;
 if(offset>=r->high-r->center)offset=r->high-r->center-1;
 *ax=r->arrival_x;*ay=r->arrival_y;
 if(r->edge==ROAD_NORTH||r->edge==ROAD_SOUTH)*ax+=offset;else *ay+=offset;
}
