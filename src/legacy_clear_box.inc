/* Exact, read-only certificate for an inclusive box of solid() coordinates.
 * Included by game.c after its types, headers, globals and progress_bits().
 * A false result never grants a collision shortcut. All supported rooms are
 * exact; rooms outside 0..37 and invalid boxes deliberately fail closed.
 * The arithmetic below occurs only after rejecting full signed input bounds.
 * Every obstacle endpoint comes from short coordinates or bounded ROM data.
 */
static inline int legacy_box_hits(int x0,int y0,int x1,int y1,
                                 int left,int top,int right,int bottom){
 return x1>=left&&x0<right&&y1>=top&&y0<bottom;
}

/* North/South already store the exact player-foot geometry. A local previous
 * offset avoids rescanning repeated consecutive rows; nothing is cached
 * between calls and no radius is added to these intervals. */
static COLD int legacy_rows_clear(int x0,int y0,int x1,int y1,
 unsigned width,unsigned height,const unsigned short *rows,
 const unsigned short *bands){
 int y;unsigned previous=~0u;
 if((unsigned)x1>=width||(unsigned)y1>=height)return 0;
 for(y=y0;y<=y1;y++){
  unsigned offset=rows[y],count;const unsigned short *band;
  if(offset==previous)continue;
  previous=offset;band=bands+offset;count=*band++;
  while(count--){
   if((unsigned)x1<band[0])break;
   if((unsigned)x0<band[1])return 0;
   band+=2;
  }
 }
 return 1;
}

COLD int legacy_game_clear_box(int x0,int y0,int x1,int y1){
 unsigned area=(unsigned)room,i;
 if(area>=38u||x0<0||y0<0||x1<x0||y1<y0)return 0;
 if(area>=22u){
  if(area>=30u){const SouthArtRoom *r=&south_art_rooms[area-30u];
   return legacy_rows_clear(x0,y0,x1,y1,r->width,r->height,
                            r->collision_rows,r->collision_bands);
  }else{const NorthArtRoom *r=&north_art_rooms[area-22u];
   return legacy_rows_clear(x0,y0,x1,y1,r->width,r->height,
                            r->collision_rows,r->collision_bands);
  }
 }
 if(area>=16u){const RegionArtRoom *r=&region_art_rooms[area-16u];
  if(x0<5||y0<5||x1>=r->width-5||y1>=r->height-5)return 0;
  for(i=0;i<r->solid_count;i++){const RegionArtRect *s=&r->solids[i];
   if(legacy_box_hits(x0,y0,x1,y1,s->x-5,s->y-5,
                      s->x+s->w+5,s->y+s->h+5))return 0;
  }
  if(area==17u&&!(adventure_save.quests.objectives[REGION_QUEST_DRY_ROAD]&2u)
     &&legacy_box_hits(x0,y0,x1,y1,219,147,261,189))return 0;
  if(area==19u&&(legacy_box_hits(x0,y0,x1,y1,45,43,83,79)
                 ||legacy_box_hits(x0,y0,x1,y1,157,43,195,79)))return 0;
  if(area==20u)for(i=0;i<2;i++){
   int x=region_game_crates[i][0],y=region_game_crates[i][1];
   if(legacy_box_hits(x0,y0,x1,y1,x-12,y-12,x+12,y+12))return 0;
  }
  return 1;
 }
 if(area>=14u){
  if(x0<12||x1>=228||y0<44||y1>=148)return 0;
  if(area==TRIAL_ROOM_STONE)for(i=0;i<2;i++){
   int x=trial_parcels[i][0],y=trial_parcels[i][1];
   if(legacy_box_hits(x0,y0,x1,y1,x-10,y-10,x+11,y+11))return 0;
  }
  return 1;
 }
 if(area>=4u){const CampaignRoom *r=&campaign_rooms[area-4u];
  unsigned pr;int k;
  if(x0<12||x1>=228||y0<32||y1>=148)return 0;
  pr=progress_bits();
  /* This is the original five-point foot, not a filled square dilation. */
  for(k=0;k<5;k++){
   int dx=k?(k&1?-4:4):0,dy=k?(k&2?-4:4):0;
   for(i=0;i<r->solid_count;i++){const CampaignBlock *s=&r->solids[i];
    if(legacy_box_hits(x0,y0,x1,y1,s->x-dx,s->y-dy,
                       s->x+s->w-dx,s->y+s->h-dy))return 0;
   }
   for(i=0;i<r->block_count;i++){const CampaignBlock *s=&r->blocks[i];
    if((pr&s->flags)!=s->flags&&
       legacy_box_hits(x0,y0,x1,y1,s->x-dx,s->y-dy,
                        s->x+s->w-dx,s->y+s->h-dy))return 0;
   }
  }
  return 1;
 }
 if(area==1u){
  if(x0<12||x1>=WORLD_W-12||y0<24||y1>=WORLD_H-12)return 0;
  for(i=0;i<OVERWORLD_SOLID_COUNT;i++){const WorldRect *s=&overworld_solids[i];
   if(legacy_box_hits(x0,y0,x1,y1,s->x,s->y,s->x+s->w,s->y+s->h))return 0;
  }
  if(y1>=WORLD_RIVER_Y&&y0<WORLD_RIVER_Y+WORLD_RIVER_H&&
     (!bridge_open||x0<WORLD_BRIDGE_X||x1>=WORLD_BRIDGE_X+WORLD_BRIDGE_W))return 0;
  return 1;
 }
 if(x0<12||x1>227||y0<28||y1>152)return 0;
 for(i=0;i<asset_solids_count[area];i++){const AssetRect *s=&asset_solids[area][i];
  if(legacy_box_hits(x0,y0,x1,y1,s->x,s->y,s->x+s->w,s->y+s->h))return 0;
 }
 if(area==2u){
  if(torches!=3&&legacy_box_hits(x0,y0,x1,y1,89,28,152,44))return 0;
  if(legacy_box_hits(x0,y0,x1,y1,52,55,77,74)
     ||legacy_box_hits(x0,y0,x1,y1,164,55,189,74))return 0;
 }
 if(area==3u&&y0<39)return 0;
 return 1;
}
