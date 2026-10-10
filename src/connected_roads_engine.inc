/* Main-engine road ownership. New routines stay in ROM; no saved coordinates. */
#define ADVENTURE_CONNECTED_ROAD_RUNTIME 1
volatile int connected_road_pending=-1,connected_road_current=-1;
volatile int connected_door_pending=-1;
unsigned connected_road_revision,connected_road_arrivals,connected_road_refusals;
static int road_cached_room=-1,road_notice=-1,road_source_x,road_source_y,door_notice_index=-1;
static unsigned road_open_bits;
/* Query-local shape cache. Authored rooms currently have at most five exits.
 * An unexpected larger room keeps the original exact table fallback. */
typedef struct { short l,t,r,b,bl,bt,br,bb; } RoadCollisionBand;
static RoadCollisionBand road_collision_bands[8];
static unsigned road_cached_first,road_cached_end,road_cached_count;
static int road_cached_width,road_cached_height;
static COLD void game_roads_cache(unsigned first,unsigned end){unsigned i;
 road_cached_first=first;road_cached_end=end;road_cached_count=end-first;
 road_cached_width=road_cached_count?connected_roads[first].width:0;
 road_cached_height=road_cached_count?connected_roads[first].height:0;
 if(road_cached_count>8u)return;
 for(i=first;i<end;i++){const ConnectedRoad*r=&connected_roads[i];RoadCollisionBand*b=&road_collision_bands[i-first];
  b->l=0;b->t=0;b->r=r->width-1;b->b=r->height-1;
  if(r->edge==ROAD_NORTH||r->edge==ROAD_SOUTH){b->l=r->low;b->r=r->high-1;if(r->edge==ROAD_NORTH)b->b=ROAD_EDGE_STRIP-1;else b->t=r->height-ROAD_EDGE_STRIP;}
  else{b->t=r->low;b->b=r->high-1;if(r->edge==ROAD_WEST)b->r=ROAD_EDGE_STRIP-1;else b->l=r->width-ROAD_EDGE_STRIP;}
  b->bl=b->l;b->bt=b->t;b->br=b->r;b->bb=b->b;
  if(r->edge==ROAD_NORTH)b->bb=r->barrier_inset+ROAD_FOOT;
  else if(r->edge==ROAD_EAST)b->bl=r->width-1-r->barrier_inset-ROAD_FOOT;
  else if(r->edge==ROAD_SOUTH)b->bt=r->height-1-r->barrier_inset-ROAD_FOOT;
  else b->br=r->barrier_inset+ROAD_FOOT;
 }
}
extern int horizons_game_route_allowed(unsigned,unsigned) __attribute__((weak));
extern int covenants_game_route_allowed(unsigned,unsigned) __attribute__((weak));
extern int underwater_game_road_departure(unsigned,unsigned) __attribute__((weak));
static COLD int game_route_allowed(unsigned gate,unsigned target,unsigned spawn){
 switch(gate){
 case ROAD_GATE_NONE:return 1;
 case ROAD_GATE_GROVE:return !!(chapter_flags&SAVE4_GROVE_CLEAR);
 case ROAD_GATE_SKY:return !!(chapter_flags&SAVE4_SKY_CLEAR);
 case ROAD_GATE_REGION:return regional_can_enter(&adventure_save,target);
 case ROAD_GATE_NORTH:return northern_can_enter(&adventure_save,target);
 case ROAD_GATE_SOUTH:return southern_can_enter(&adventure_save,target);
 case ROAD_GATE_MAGMA:return magma_game_can_enter(target);
 case ROAD_GATE_UNDERWATER:return underwater_game_can_enter(target);
 case ROAD_GATE_RETURN:return return_game_can_enter(target);
 case ROAD_GATE_HORIZONS:return horizons_game_route_allowed?horizons_game_route_allowed(target,spawn):horizons_game_can_enter(target);
 case ROAD_GATE_COVENANTS:return covenants_game_route_allowed?covenants_game_route_allowed(target,spawn):covenants_game_can_enter(target);
 }return 0;
}
static COLD int game_road_allowed(const ConnectedRoad*r){
 if(r->reserved&ROAD_ARRIVAL_ONLY)return 1;
 return game_route_allowed(r->gate,r->target,r->spawn);
}
static COLD int game_roads_sync(void){unsigned first,end,i,bits=0;int changed;
 connected_road_range((unsigned)room,&first,&end);
 for(i=first;i<end;i++)if(game_road_allowed(&connected_roads[i]))bits|=1u<<(i-first);
 changed=road_cached_room!=room||road_open_bits!=bits;
 if(changed){game_roads_cache(first,end);road_cached_room=room;road_open_bits=bits;connected_road_revision++;cache_valid[0]=cache_valid[1]=0;}
 return changed;
}
COLD int game_road_managed(unsigned source,unsigned target){return connected_road_managed(source,target);}
COLD int game_road_collision(unsigned area,int x,int y){unsigned i;int value;
 if(area!=(unsigned)room)return -1;
 if(road_cached_room!=room)game_roads_sync();
 if(!road_cached_count||(unsigned)x>=(unsigned)road_cached_width||(unsigned)y>=(unsigned)road_cached_height)return -1;
 if(x>=ROAD_EDGE_STRIP&&y>=ROAD_EDGE_STRIP&&x<road_cached_width-ROAD_EDGE_STRIP&&y<road_cached_height-ROAD_EDGE_STRIP)return -1;
 if(road_cached_count<=8u){
  for(i=0;i<road_cached_count;i++){const RoadCollisionBand*b=&road_collision_bands[i];
   if(x<b->l||x>b->r||y<b->t||y>b->b)continue;
   if(x<ROAD_FOOT||y<ROAD_FOOT||x>=road_cached_width-ROAD_FOOT||y>=road_cached_height-ROAD_FOOT)return 1;
   return !(road_open_bits&(1u<<i))&&x>=b->bl&&x<=b->br&&y>=b->bt&&y<=b->bb;
  }
 }else for(i=road_cached_first;i<road_cached_end;i++){value=connected_road_point(&connected_roads[i],x,y,(road_open_bits>>(i-road_cached_first))&1u);if(value>=0)return value;}
 return -1;
}
/* An open seam only removes authored geometry. Keep the chapter's original
 * static and dynamic clearance proof after rejecting the only new solids:
 * the five-pixel outer foot bound and overlapping closed road fences. */
COLD int game_road_box_added(unsigned area,int x0,int y0,int x1,int y1){unsigned i;
 if(area!=(unsigned)room||x0>x1||y0>y1)return 1;
 if(road_cached_room!=room)game_roads_sync();
 if(road_cached_count&&(x0<ROAD_FOOT||y0<ROAD_FOOT||x1>=road_cached_width-ROAD_FOOT||y1>=road_cached_height-ROAD_FOOT))return 1;
 if(road_cached_count>8u)return game_road_box_touched((unsigned)room,x0,y0,x1,y1);
 if(road_open_bits==((1u<<road_cached_count)-1u))return 0;
 for(i=0;i<road_cached_count;i++){const RoadCollisionBand*b=&road_collision_bands[i];
  if(!(road_open_bits&(1u<<i))&&x1>=b->bl&&x0<=b->br&&y1>=b->bt&&y0<=b->bb)return 1;
 }return 0;
}
COLD int game_road_box_touched(unsigned area,int x0,int y0,int x1,int y1){unsigned first,end,i;
 connected_road_range(area,&first,&end);for(i=first;i<end;i++)if(connected_road_box(&connected_roads[i],x0,y0,x1,y1))return 1;return 0;
}
COLD void game_road_cancel(void){connected_road_pending=connected_door_pending=-1;}
COLD void game_road_interrupt(void){
 if(connected_road_pending>=0||connected_door_pending>=0){
  south_game_cancel_enter();magma_game_cancel_enter();underwater_game_cancel_event();
  return_game_cancel_event();horizons_game_cancel_event();covenants_game_cancel_event();
  if(game_state==EVENT_PENDING)game_state=event_resume_state;
 }
 game_road_cancel();
}
static COLD void game_roads_reset(void){game_road_cancel();connected_road_current=-1;road_cached_room=road_notice=door_notice_index=-1;road_open_bits=0;}
static COLD void game_road_validate_request(int target,int spawn){
 if(connected_road_pending>=0){const ConnectedRoad*r=&connected_roads[connected_road_pending];
  if(restoring_checkpoint||room!=r->room||target!=r->target||spawn!=r->spawn||px!=road_source_x||py!=road_source_y)game_road_cancel();
 }
 if(connected_door_pending>=0){const ConnectedDoor*d=&connected_doors[connected_door_pending];
  if(restoring_checkpoint||room!=d->room||target!=d->target||spawn!=d->spawn||px!=road_source_x||py!=road_source_y)game_road_cancel();
 }
}
static COLD void game_road_arrive(int oldroom,int target,int spawn){int ax,ay,index=connected_road_pending;
 if(connected_door_pending>=0){const ConnectedDoor*d=&connected_doors[connected_door_pending];
  game_road_cancel();
  if(oldroom==d->room&&target==d->target&&spawn==d->spawn&&room==target){game_roads_sync();if(!solid(d->arrival_x,d->arrival_y)){px=d->arrival_x;py=d->arrival_y;door_notice_index=-1;}else connected_road_refusals++;}
  return;
 }
 if(index<0)return;
 game_road_cancel();
 {const ConnectedRoad*r=&connected_roads[index];
  if(oldroom!=r->room||target!=r->target||spawn!=r->spawn||room!=target)return;
  connected_road_arrival(r,road_source_x,road_source_y,&ax,&ay);
  game_roads_sync();
  /* The retained checkpoint is the safe fallback if edited scenery rejects a
   * landing. Tests require every route landing to succeed. */
  if(solid(ax,ay)){connected_road_refusals++;return;}
  px=ax;py=ay;connected_road_current=index;connected_road_arrivals++;road_notice=-1;
 }
}
/* Descending a real interior stair returns beside that same stair on the
 * lower floor. Retry/Continue keep their historical checkpoint0 positions. */
static COLD void game_stair_arrive(int oldroom,int target,int spawn){int x;
 if(restoring_checkpoint||spawn!=0||oldroom!=target+1||room!=target||checkpoint_spawn!=0||
    adventure_save.campaign.room!=target||adventure_save.campaign.spawn!=0)return;
 if(!((target>=26&&target<=28)||(target>=34&&target<=36)||(target>=42&&target<=44)))return;
 x=target>=42?216:208;
 if(solid(x,80)){connected_road_refusals++;return;}
 px=x;py=80;
}
static COLD int game_road_hint(const ConnectedRoad*r){
 if(room==0)return TX_PF_ROUTE_LATER;
 switch(r->gate){case ROAD_GATE_NORTH:return TX_NT_LOCKED_A;case ROAD_GATE_SOUTH:return TX_ST_LOCKED_A;case ROAD_GATE_MAGMA:return TX_MG_LOCKED;case ROAD_GATE_UNDERWATER:return TX_UW_LOCKED;case ROAD_GATE_RETURN:return TX_RT_LOCKED;case ROAD_GATE_HORIZONS:return TX_HZ_LOCKED;case ROAD_GATE_COVENANTS:return TX_CV_LOCKED;default:return TX_RG_LOCKED_A;}
}
static COLD int game_door_step(void){unsigned i;int old=room;
 if(door_notice_index>=0){const ConnectedDoor*d=&connected_doors[door_notice_index];if(room!=d->room||px<d->x-10||px>=d->x+d->w+10||py<d->y-10||py>=d->y+d->h+10)door_notice_index=-1;}
 for(i=0;i<connected_door_count;i++){const ConnectedDoor*d=&connected_doors[i];unsigned bit=d->edge==ROAD_NORTH?KEY_UP:KEY_DOWN;
  if(room!=d->room||!(keys&bit)||px<d->x||px>=d->x+d->w||py<d->y||py>=d->y+d->h)continue;
  if(!game_route_allowed(d->gate,d->target,d->spawn)){if(door_notice_index!=(int)i){door_notice_index=(int)i;toast(room==0?TX_PF_ROUTE_LATER:TX_RT_LOCKED);}return 0;}
  connected_door_pending=(int)i;road_source_x=px;road_source_y=py;enter_room(d->target,d->spawn);
  if(room==old&&game_state!=EVENT_PENDING)game_road_cancel();
  if(room!=old||game_state==EVENT_PENDING){game_attacks_suspend();pressed=0;return 1;}return 0;
 }return 0;
}
COLD int game_road_step(void){unsigned first,end,i;int old=room;
 game_roads_sync();connected_road_range((unsigned)room,&first,&end);
 if(road_notice>=0){const ConnectedRoad*r=&connected_roads[road_notice];if(r->room!=room||!connected_road_contains(r,px,py,10)||connected_road_distance(r,px,py)>40)road_notice=-1;}
 if(transition_lock||game_state!=PLAY||connected_road_pending>=0||connected_door_pending>=0)return 0;
 for(i=first;i<end;i++){const ConnectedRoad*r=&connected_roads[i];int distance,open=(road_open_bits>>(i-first))&1u;
  if(r->reserved&ROAD_ARRIVAL_ONLY)continue;
  if(!connected_road_contains(r,px,py,0)||!connected_road_outward(r,(unsigned)keys))continue;
  distance=connected_road_distance(r,px,py);if(distance<0)continue;
  if(!open){if(distance<=(int)r->barrier_inset+ROAD_FOOT+2&&road_notice!=(int)i){road_notice=(int)i;toast(game_road_hint(r));}continue;}
  if(distance>ROAD_FOOT)continue;
  if(r->entry_safe&&!game_region_entry_safe())continue;
  connected_road_pending=(int)i;road_source_x=px;road_source_y=py;
  if(underwater_game_road_departure&&underwater_game_road_departure(r->target,r->spawn))event_frame();
  else enter_room(r->target,r->spawn);
  if(room==old&&game_state!=EVENT_PENDING)game_road_cancel();
  if(room!=old||game_state==EVENT_PENDING){game_attacks_suspend();pressed=0;return 1;}
  return 0;
 }return game_door_step();
}
static COLD void game_roads_draw(void){unsigned first,end,i;game_roads_sync();connected_road_range((unsigned)room,&first,&end);
 for(i=first;i<end;i++){const ConnectedRoad*r=&connected_roads[i];int x,y,k;
  if(road_open_bits&(1u<<(i-first)))continue;
  if(r->edge==ROAD_NORTH||r->edge==ROAD_SOUTH){
   x=r->low-5-camera_x;y=(r->edge==ROAD_NORTH?r->barrier_inset:r->height-1-r->barrier_inset)-camera_y;
   rect(x,y-4,r->high-r->low+10,3,PAL_WOOD1);rect(x,y-3,r->high-r->low+10,1,PAL_WOOD4);
   for(k=0;k<r->high-r->low+10;k+=8){rect(x+k,y-10,3,13,PAL_WOOD1);rect(x+k+1,y-9,1,11,PAL_WOOD4);}
  }else{
   x=(r->edge==ROAD_WEST?r->barrier_inset:r->width-1-r->barrier_inset)-camera_x;y=r->low-5-camera_y;
   rect(x-3,y,7,r->high-r->low+10,PAL_WOOD1);rect(x-2,y+1,2,r->high-r->low+8,PAL_WOOD4);
   for(k=0;k<r->high-r->low+10;k+=8){rect(x-5,y+k,11,3,PAL_WOOD1);rect(x-4,y+k,9,1,PAL_WOOD4);}
  }
 }
}
