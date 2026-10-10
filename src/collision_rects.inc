/* Exact rectangle view of solid() in rooms0..45,54..61 and62..77. No persistent
 * storage and no changes to the authoritative point predicate. Rectangles are
 * clipped before narrowing to short. Unsupported rooms fail closed. */
#include "collision_rects.h"
#include "connected_roads.h"
extern int covenants_game_collision_rects(int,int,int,int,short[][4],unsigned) __attribute__((weak));
typedef struct {
 int x0,y0,x1,y1;
 short (*out)[4];
 unsigned count,cap,carve;
} CollisionRectBuilder;
#ifdef ADVENTURE_CONNECTED_ROAD_RUNTIME
/* Subtract the same source-road strips that override the authored point
 * predicate. Each recursive branch advances its road index; output is bounded
 * by the caller's cap and discarded on overflow. */
static COLD int collision_rect_carve(CollisionRectBuilder*b,unsigned index,int l,int t,int r,int d){
 unsigned i;short*v;
 for(i=index;b->carve&&i<road_cached_count;i++){
  const RoadCollisionBand*s=&road_collision_bands[i];int mt,md;
  if(r<s->l||l>s->r||d<s->t||t>s->b)continue;
  mt=t>s->t?t:s->t;md=d<s->b?d:s->b;
  if(t<s->t&&!collision_rect_carve(b,i+1,l,t,r,s->t-1))return 0;
  if(d>s->b&&!collision_rect_carve(b,i+1,l,s->b+1,r,d))return 0;
  if(l<s->l&&!collision_rect_carve(b,i+1,l,mt,s->l-1,md))return 0;
  if(r>s->r&&!collision_rect_carve(b,i+1,s->r+1,mt,r,md))return 0;
  return 1;
 }
 if(b->count==b->cap)return 0;
 v=b->out[b->count++];v[0]=(short)l;v[1]=(short)t;v[2]=(short)r;v[3]=(short)d;
 return 1;
}
#endif
static COLD int collision_rect_add(CollisionRectBuilder *b,int l,int t,int r,int d){
 if(l<b->x0)l=b->x0;
 if(t<b->y0)t=b->y0;
 if(r>b->x1)r=b->x1;
 if(d>b->y1)d=b->y1;
 if(l>r||t>d)return 1;
#ifdef ADVENTURE_CONNECTED_ROAD_RUNTIME
 return collision_rect_carve(b,0,l,t,r,d);
#else
 {short*v;if(b->count==b->cap)return 0;
  v=b->out[b->count++];v[0]=(short)l;v[1]=(short)t;v[2]=(short)r;v[3]=(short)d;return 1;}
#endif
}
#ifdef ADVENTURE_CONNECTED_ROAD_RUNTIME
/* Add exactly the road-owned foot bounds/fences after the static subtraction.
 * Dynamic chapter props are emitted afterward and keep their original OR. */
static COLD int collision_rect_roads(CollisionRectBuilder*b){unsigned i;
 if(!b->carve)return 1;
 b->carve=0;
 for(i=0;i<road_cached_count;i++){
  const RoadCollisionBand*s=&road_collision_bands[i];
  if(!(road_open_bits&(1u<<i))){if(!collision_rect_add(b,s->bl,s->bt,s->br,s->bb))return 0;}
  else{
   int n=s->b<ROAD_FOOT?s->b:ROAD_FOOT-1;
   if(s->t<=n&&!collision_rect_add(b,s->l,s->t,s->r,n))return 0;
   n=s->t>road_cached_height-ROAD_FOOT?s->t:road_cached_height-ROAD_FOOT;
   if(n<=s->b&&!collision_rect_add(b,s->l,n,s->r,s->b))return 0;
   n=s->r<ROAD_FOOT?s->r:ROAD_FOOT-1;
   if(s->l<=n&&!collision_rect_add(b,s->l,s->t,n,s->b))return 0;
   n=s->l>road_cached_width-ROAD_FOOT?s->l:road_cached_width-ROAD_FOOT;
   if(n<=s->r&&!collision_rect_add(b,n,s->t,s->r,s->b))return 0;
  }
 }
 return 1;
}
#else
/* Historical isolated chapter harnesses have no main-engine road bridge. */
#define collision_rect_roads(b) 1
#endif
/* Equal consecutive generated rows share exactly the same occupied union. */
static COLD int collision_rect_rows(CollisionRectBuilder *b,unsigned height,
 const unsigned short *rows,const unsigned short *bands){
 int y=b->y0<0?0:b->y0,last=b->y1,end;unsigned offset,count;
 const unsigned short *band;
 if(last>=(int)height)last=(int)height-1;
 while(y<=last){
  offset=rows[y];end=y;
  while(end<last&&rows[end+1]==offset)end++;
  band=bands+offset;count=*band++;
  while(count--){
   if(!collision_rect_add(b,band[0],y,band[1]-1,end))return 0;
   band+=2;
  }
  y=end+1;
 }
 return 1;
}
#ifdef ADVENTURE_CONNECTED_ROAD_RUNTIME
/* Horizons uses the same exact road subtraction/fence union as legacy maps.
 * The carriage is appended after road carving because the authoritative
 * Horizons point predicate ORs it with the road-adjusted static geometry. */
static inline __attribute__((always_inline)) int collision_rect_horizons(CollisionRectBuilder*b){
 const HorizonsArtRoom*r=&horizons_art_rooms[(unsigned)room-62u];unsigned inputs[3];
 if(!collision_rect_add(b,b->x0,b->y0,4,b->y1)||
    !collision_rect_add(b,r->width-5,b->y0,b->x1,b->y1)||
    !collision_rect_add(b,b->x0,b->y0,b->x1,4)||
    !collision_rect_add(b,b->x0,r->height-5,b->x1,b->y1)||
    !collision_rect_rows(b,r->height,r->collision_rows,r->collision_bands)||
    !collision_rect_roads(b))return 0;
 if(room==63){horizons_game_collision_inputs(inputs);
  if(!collision_rect_add(b,(short)inputs[0]-12,60,(short)inputs[0]+12,84))return 0;
 }
 return 1;
}
#endif
#define COLLISION_RECT(l,t,r,d) do{if(!collision_rect_add(&b,(l),(t),(r),(d)))return -1;}while(0)
#define COLLISION_BOUNDS(l,t,r,d) do{ \
 COLLISION_RECT(x0,y0,(l)-1,y1);COLLISION_RECT((r)+1,y0,x1,y1); \
 COLLISION_RECT(x0,y0,x1,(t)-1);COLLISION_RECT(x0,(d)+1,x1,y1); \
}while(0)
COLD int game_collision_rects(int x0,int y0,int x1,int y1,short out[][4],unsigned cap){
 CollisionRectBuilder b;unsigned area=(unsigned)room,i;int seams;
 seams=game_road_box_touched&&game_road_box_touched(area,x0,y0,x1,y1);
 if(seams){
#ifdef ADVENTURE_CONNECTED_ROAD_RUNTIME
  if((area<22u||area>=46u)&&(area<62u||area>=70u))return -1;
  if(road_cached_room!=room)game_roads_sync();
  if(road_cached_count>8u)return -1;
#else
  return -1;
#endif
 }
 if(!out||!cap||cap>256u||x0<-32768||y0<-32768||
    x1>32767||y1>32767||x1<x0||y1<y0)return -1;
#ifdef ADVENTURE_CONNECTED_ROAD_RUNTIME
 if(area-62u<8u){
  b.x0=x0;b.y0=y0;b.x1=x1;b.y1=y1;b.out=out;b.count=0;b.cap=cap;b.carve=(unsigned)seams;
  return collision_rect_horizons(&b)?(int)b.count:-1;
 }
#endif
 if(area-70u<8u)return covenants_game_collision_rects?covenants_game_collision_rects(x0,y0,x1,y1,out,cap):-1;
 if(area>=62u||(area>=46u&&area<54u))return -1;
 b.x0=x0;b.y0=y0;b.x1=x1;b.y1=y1;b.out=out;b.count=0;b.cap=cap;b.carve=(unsigned)seams;
 if(area>=54u){const ReturnArtRoom *r=&return_art_rooms[area-54u];short dynamic[2][4];unsigned count;
  COLLISION_BOUNDS(5,5,r->width-6,r->height-6);
  if(!collision_rect_rows(&b,r->height,r->collision_rows,r->collision_bands))return -1;
  count=return_game_collision_rects(dynamic);
  for(i=0;i<count;i++)COLLISION_RECT(dynamic[i][0],dynamic[i][1],dynamic[i][2],dynamic[i][3]);
 }else if(area>=38u){const MagmaArtRoom *r=&magma_art_rooms[area-38u];
  unsigned inputs[3];int x,y;
  COLLISION_BOUNDS(0,0,r->width-1,r->height-1);
  if(!collision_rect_rows(&b,r->height,r->collision_rows,r->collision_bands)||!collision_rect_roads(&b))return -1;
  magma_game_collision_inputs(inputs);
  if((area>=42u&&area<=44u)||(area==40u&&inputs[2])){
   for(i=0;i<magma_puzzle_count(area);i++)
    if(magma_puzzle_position(&magma_game_puzzle,area,i,&x,&y))
     COLLISION_RECT(x-11,y-11,x+10,y+10);
  }else if(area==38u||area==39u){
   x=(int)inputs[0];y=area==38u?232:264;
   COLLISION_RECT(x-11,y-11,x+10,y+10);
  }
 }else if(area>=22u){const unsigned short *rows,*bands;unsigned width,height;
  if(area>=30u){const SouthArtRoom *r=&south_art_rooms[area-30u];
   rows=r->collision_rows;bands=r->collision_bands;width=r->width;height=r->height;
  }else{const NorthArtRoom *r=&north_art_rooms[area-22u];
   rows=r->collision_rows;bands=r->collision_bands;width=r->width;height=r->height;
  }
  COLLISION_BOUNDS(0,0,(int)width-1,(int)height-1);
  if(!collision_rect_rows(&b,height,rows,bands)||!collision_rect_roads(&b))return -1;
 }else if(area>=16u){const RegionArtRoom *r=&region_art_rooms[area-16u];
  COLLISION_BOUNDS(5,5,r->width-6,r->height-6);
  for(i=0;i<r->solid_count;i++){const RegionArtRect *s=&r->solids[i];
   COLLISION_RECT(s->x-5,s->y-5,s->x+s->w+4,s->y+s->h+4);
  }
  if(area==17u&&!(adventure_save.quests.objectives[REGION_QUEST_DRY_ROAD]&2u))
   COLLISION_RECT(219,147,260,188);
  if(area==19u){COLLISION_RECT(45,43,82,78);COLLISION_RECT(157,43,194,78);}
  if(area==20u)for(i=0;i<2;i++){
   int x=region_game_crates[i][0],y=region_game_crates[i][1];
   COLLISION_RECT(x-12,y-12,x+11,y+11);
  }
 }else if(area>=14u){
  COLLISION_BOUNDS(12,44,227,147);
  if(area==TRIAL_ROOM_STONE)for(i=0;i<2;i++){
   int x=trial_parcels[i][0],y=trial_parcels[i][1];
   COLLISION_RECT(x-10,y-10,x+10,y+10);
  }
 }else if(area>=4u){const CampaignRoom *r=&campaign_rooms[area-4u];
  unsigned pr=progress_bits();int k;
  COLLISION_BOUNDS(12,32,227,147);
  /* Original five sampled foot points, not a filled-square dilation. */
  for(k=0;k<5;k++){
   int dx=k?(k&1?-4:4):0,dy=k?(k&2?-4:4):0;
   for(i=0;i<r->solid_count;i++){const CampaignBlock *s=&r->solids[i];
    COLLISION_RECT(s->x-dx,s->y-dy,s->x+s->w-dx-1,s->y+s->h-dy-1);
   }
   for(i=0;i<r->block_count;i++){const CampaignBlock *s=&r->blocks[i];
    if((pr&s->flags)!=s->flags)
     COLLISION_RECT(s->x-dx,s->y-dy,s->x+s->w-dx-1,s->y+s->h-dy-1);
   }
  }
 }else if(area==1u){
  COLLISION_BOUNDS(12,24,WORLD_W-13,WORLD_H-13);
  for(i=0;i<OVERWORLD_SOLID_COUNT;i++){const WorldRect *s=&overworld_solids[i];
   COLLISION_RECT(s->x,s->y,s->x+s->w-1,s->y+s->h-1);
  }
  if(!bridge_open)COLLISION_RECT(x0,WORLD_RIVER_Y,x1,WORLD_RIVER_Y+WORLD_RIVER_H-1);
  else{COLLISION_RECT(x0,WORLD_RIVER_Y,WORLD_BRIDGE_X-1,WORLD_RIVER_Y+WORLD_RIVER_H-1);
   COLLISION_RECT(WORLD_BRIDGE_X+WORLD_BRIDGE_W,WORLD_RIVER_Y,x1,WORLD_RIVER_Y+WORLD_RIVER_H-1);}
 }else{
  COLLISION_BOUNDS(12,28,227,152);
  for(i=0;i<asset_solids_count[area];i++){const AssetRect *s=&asset_solids[area][i];
   COLLISION_RECT(s->x,s->y,s->x+s->w-1,s->y+s->h-1);
  }
  if(area==2u){
   if(torches!=3)COLLISION_RECT(89,y0,151,43);
   COLLISION_RECT(52,55,76,73);COLLISION_RECT(164,55,188,73);
  }
  if(area==3u)COLLISION_RECT(x0,y0,x1,38);
 }
 return (int)b.count;
}
#undef COLLISION_BOUNDS
#undef COLLISION_RECT
