#ifndef ADVENTURE_CONNECTED_ROAD_REGION_H
#define ADVENTURE_CONNECTED_ROAD_REGION_H
#include "connected_roads.h"

/* The full engine supplies road seams. Historical standalone chapter harnesses
 * have no bridge and retain their original geometry and local door dispatch. */
static inline int road_region_managed(unsigned source,unsigned target){
 return game_road_managed&&game_road_managed(source,target);
}
static inline int road_region_point(unsigned area,int x,int y){
 return game_road_collision?game_road_collision(area,x,y):-1;
}
static inline int road_region_box(unsigned area,int x0,int y0,int x1,int y1){
 return game_road_box_touched&&game_road_box_touched(area,x0,y0,x1,y1);
}
/* A positive original chapter clearance certificate remains valid if the
 * roads add no solid point to this box. Unlike touched(), this does not discard
 * certificates merely because an open seam subtracts authored geometry. */
static inline int road_region_box_added(unsigned area,int x0,int y0,int x1,int y1){
 return game_road_box_added&&game_road_box_added(area,x0,y0,x1,y1);
}
/* Legacy interval rays know the authored map, while a road may open a border
 * or close its gate. Only seam-touching rays use exact point supercover. No
 * intermediate cell or diagonal side cell may borrow an open endpoint. */
static inline int road_region_ray(unsigned area,int x,int y,int tx,int ty,
                                 int (*blocked)(int,int)){
 int dx,dy,sx,sy,e;
 if(!road_region_box(area,x<tx?x:tx,y<ty?y:ty,x>tx?x:tx,y>ty?y:ty))return -1;
 if((unsigned)x>1023u||(unsigned)y>1023u||(unsigned)tx>1023u||(unsigned)ty>1023u)return 0;
 dx=tx-x;dy=ty-y;sx=dx<0?-1:1;sy=dy<0?-1:1;
 if(dx<0)dx=-dx;
 if(dy<0)dy=-dy;
 if(dx+dy>160||blocked(x,y)||blocked(tx,ty))return 0;
 dy=-dy;e=dx+dy;
 while(x!=tx||y!=ty){
  int twice=e*2,nx=x,ny=y;
  if(twice>=dy){e+=dy;nx+=sx;}
  if(twice<=dx){e+=dx;ny+=sy;}
  if((nx!=x&&blocked(nx,y))||(ny!=y&&blocked(x,ny))||blocked(nx,ny))return 0;
  x=nx;y=ny;
 }
 return 1;
}
#endif
