COLD void copy_region(void){
 const RegionArtRoom*r=&region_art_rooms[room-16];u32 src,dst,mode;int y,width=r->width;
 if(COPY_OPAQUE_MODAL_BITMAP&&copy_modal_background(r->bitmap,r->bitmap_odd,width))return;
 if(width==240){REG32(0x040000D4)=(u32)r->bitmap;REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;return;}
 src=(u32)(((camera_x&1)?r->bitmap_odd:r->bitmap)+camera_y*width+(camera_x&~1));dst=(u32)screen;
 /* Both authored rows and bitmap pages are halfword aligned. Word DMA is
  * safe only when the whole row stride and both pointers are word aligned.
  * Integer MMIO cursors avoid forming an unused pointer past the last row. */
 mode=((src|dst|(u32)width)&3u)?0x80000000u|120u:0x84000000u|60u;
 for(y=0;y<160;y++){REG32(0x040000D4)=src;REG32(0x040000D8)=dst;REG32(0x040000DC)=mode;src+=width;dst+=240;}
}
COLD void copy_south(void){
 const SouthArtRoom*r=&south_art_rooms[room-30];u32 src,dst,mode;int y,width=r->width;
 if(COPY_OPAQUE_MODAL_BITMAP&&copy_modal_background(r->bitmap,r->bitmap_odd,width))return;
 if(width==240){REG32(0x040000D4)=(u32)r->bitmap;REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;return;}
 src=(u32)(((camera_x&1)?r->bitmap_odd:r->bitmap)+camera_y*width+(camera_x&~1));dst=(u32)screen;
 /* Both authored rows and bitmap pages are halfword aligned. Word DMA is
  * safe only when the whole row stride and both pointers are word aligned.
  * Integer MMIO cursors avoid forming an unused pointer past the last row. */
 mode=((src|dst|(u32)width)&3u)?0x80000000u|120u:0x84000000u|60u;
 for(y=0;y<160;y++){REG32(0x040000D4)=src;REG32(0x040000D8)=dst;REG32(0x040000DC)=mode;src+=width;dst+=240;}
}
COLD void copy_magma(void){
 const MagmaArtRoom*r=&magma_art_rooms[room-38];u32 src,dst,mode;int y,width=r->width;
 if(COPY_OPAQUE_MODAL_BITMAP&&copy_modal_background(r->bitmap,r->bitmap_odd,width))return;
 if(width==240){REG32(0x040000D4)=(u32)r->bitmap;REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;return;}
 src=(u32)(((camera_x&1)?r->bitmap_odd:r->bitmap)+camera_y*width+(camera_x&~1));dst=(u32)screen;
 /* Both authored rows and bitmap pages are halfword aligned. Word DMA is
  * safe only when the whole row stride and both pointers are word aligned.
  * Integer MMIO cursors avoid forming an unused pointer past the last row. */
 mode=((src|dst|(u32)width)&3u)?0x80000000u|120u:0x84000000u|60u;
 for(y=0;y<160;y++){REG32(0x040000D4)=src;REG32(0x040000D8)=dst;REG32(0x040000DC)=mode;src+=width;dst+=240;}
}
COLD void copy_north(void){
 const NorthArtRoom*r=&north_art_rooms[room-22];u32 src,dst,mode;int y,width=r->width;
 if(COPY_OPAQUE_MODAL_BITMAP&&copy_modal_background(r->bitmap,r->bitmap_odd,width))return;
 if(width==240){REG32(0x040000D4)=(u32)r->bitmap;REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;return;}
 src=(u32)(((camera_x&1)?r->bitmap_odd:r->bitmap)+camera_y*width+(camera_x&~1));dst=(u32)screen;
 /* Both authored rows and bitmap pages are halfword aligned. Word DMA is
  * safe only when the whole row stride and both pointers are word aligned.
  * Integer MMIO cursors avoid forming an unused pointer past the last row. */
 mode=((src|dst|(u32)width)&3u)?0x80000000u|120u:0x84000000u|60u;
 for(y=0;y<160;y++){REG32(0x040000D4)=src;REG32(0x040000D8)=dst;REG32(0x040000DC)=mode;src+=width;dst+=240;}
}
COLD void draw_south_map(void){int i,mx=20,my=62;box(8,31,224,123);centered(south_game_name(),35,GOLD);rect(mx,my,120,80,PAL_GOLD2);rect(mx,my+58,120,22,PAL_WATER3);for(i=0;i<8;i++){int x=168+(i&1)*30,y=62+(i/2)*19;rect(x,y,10,10,(adventure_save.quests.region_flags[2]&(1u<<i))?GOLD:PAL_STONE2);if(room==30+i)rect(x-2,y-2,14,2,TEAL);}if(scrolling_room())rect(mx+px/4-1,my+py/4-1,3,3,PAL_HEART);centered(TX_G_NEXT_TAB,140,TEAL);}
COLD void draw_magma_map(void){int i,mx=20,my=62;box(8,31,224,123);centered(magma_game_name(),35,GOLD);rect(mx,my,120,80,PAL_GOLD2);rect(mx,my+58,120,22,PAL_STONE3);for(i=0;i<8;i++){int x=168+(i&1)*30,y=62+(i/2)*19;rect(x,y,10,10,(adventure_save.quests.region_flags[3]&(1u<<i))?GOLD:PAL_STONE2);if(room==38+i)rect(x-2,y-2,14,2,TEAL);}if(scrolling_room())rect(mx+px/4-1,my+py/4-1,3,3,PAL_HEART);centered(TX_G_NEXT_TAB,140,TEAL);}
COLD void draw_north_map(void){int i,mx=20,my=62;box(8,31,224,123);centered(north_game_name(),35,GOLD);rect(mx,my,120,80,PAL_PINE3);rect(mx,my+58,120,22,PAL_WATER3);for(i=0;i<8;i++){int x=168+(i&1)*30,y=62+(i/2)*19;rect(x,y,10,10,(adventure_save.quests.region_flags[1]&(1u<<i))?GOLD:PAL_STONE2);if(room==22+i)rect(x-2,y-2,14,2,TEAL);}if(scrolling_room())rect(mx+px/4-1,my+py/4-1,3,3,PAL_HEART);centered(TX_G_NEXT_TAB,140,TEAL);}
COLD void draw_region_map(void){int i,mx=20,my=62;box(8,31,224,123);centered(region_game_name(),35,GOLD);rect(mx,my,120,80,PAL_PINE3);rect(mx,my+36,120,8,PAL_WATER3);for(i=0;i<6;i++){int x=170+(i&1)*30,y=67+(i/2)*24;rect(x,y,10,10,(adventure_save.quests.region_flags[0]&(1u<<i))?GOLD:PAL_STONE2);if(room==16+i)rect(x-2,y-2,14,2,TEAL);}if(scrolling_room())rect(mx+px/4-1,my+py/4-1,3,3,PAL_HEART);centered(TX_G_NEXT_TAB,140,TEAL);}
