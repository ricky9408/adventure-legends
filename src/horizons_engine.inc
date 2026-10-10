/* Mixed-width/height Horizons maps and cold engine helpers. */
COLD void copy_horizons(void){
 const HorizonsArtRoom*r=&horizons_art_rooms[room-62];u32 src,dst,mode;int y,width=r->width;
 if(COPY_OPAQUE_MODAL_BITMAP&&copy_modal_background(r->bitmap,r->bitmap_odd,width))return;
 if(width==240){REG32(0x040000D4)=(u32)(r->bitmap+camera_y*240);REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;return;}
 src=(u32)(((camera_x&1)?r->bitmap_odd:r->bitmap)+camera_y*width+(camera_x&~1));dst=(u32)screen;
 /* Retain halfword DMA when either pointer or the authored stride is not
  * word aligned. Integer MMIO addresses also avoid forming an unused
  * pointer beyond the bitmap after the final row. */
 mode=((src|dst|(u32)width)&3u)?0x80000000u|120u:0x84000000u|60u;
 for(y=0;y<160;y++){REG32(0x040000D4)=src;REG32(0x040000D8)=dst;REG32(0x040000DC)=mode;src+=width;dst+=240;}
}
COLD void draw_horizons_map(void){
 int i,mx=20,my=62;box(8,31,224,123);centered(horizons_game_name(),35,GOLD);
 rect(mx,my,120,80,PAL_GOLD4);rect(mx+10,my+12,100,56,PAL_PINE3);
 line(mx+18,my+55,mx+94,my+16,PAL_TEAL2);
 for(i=0;i<8;i++){int x=168+(i&1)*30,y=62+(i/2)*19;
  rect(x,y,10,10,(adventure_save.quests.region_flags[6]&(1u<<i))?GOLD:PAL_STONE2);
  if(room==62+i)rect(x-2,y-2,14,2,TEAL);
 }
 rect(mx+px*120/world_width()-1,my+py*80/world_height()-1,3,3,PAL_HEART);
 centered(TX_G_NEXT_TAB,140,TEAL);
}
COLD int horizons_hint_text(void){
 static const int hints[]={0,TX_HP_FACE,TX_HP_SIDE,TX_HP_GATHER,TX_HP_RELEASE,
  TX_HP_CATCH,TX_HP_HOLD,TX_HP_TWO_BEATS};
 unsigned h=horizons_powers_hint();return h<sizeof(hints)/sizeof(hints[0])?hints[h]:0;
}
COLD int game_region_actor_overlap(int x0,int y0,int x1,int y1){
 unsigned i;if(x0>x1||y0>y1)return 1;
 if(px+6>=x0&&px-6<=x1&&py+6>=y0&&py-6<=y1)return 1;
 if(summoned&&cx+6>=x0&&cx-6<=x1&&cy+6>=y0&&cy-6<=y1)return 1;
 for(i=0;i<MAX_ENEMIES;i++)if(enemies[i].hp>0&&enemies[i].x+7>=x0&&
   enemies[i].x-7<=x1&&enemies[i].y+7>=y0&&enemies[i].y-7<=y1)return 1;
 return 0;
}
