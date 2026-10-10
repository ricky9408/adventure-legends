/* Return-only cold drawing bridges. Shared event scheduling stays ROM-only. */
COLD void copy_return(void){
 const ReturnArtRoom*r=&return_art_rooms[room-54];u32 src,dst,mode;int y,width=r->width;
 if(COPY_OPAQUE_MODAL_BITMAP&&copy_modal_background(r->bitmap,r->bitmap_odd,width))return;
 if(width==240){REG32(0x040000D4)=(u32)(r->bitmap);REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;return;}
 src=(u32)(((camera_x&1)?r->bitmap_odd:r->bitmap)+camera_y*width+(camera_x&~1));dst=(u32)screen;
 /* Retain halfword DMA when either pointer or the authored stride is not
  * word aligned. Integer MMIO addresses also avoid forming an unused
  * pointer beyond the bitmap after the final row. */
 mode=((src|dst|(u32)width)&3u)?0x80000000u|120u:0x84000000u|60u;
 for(y=0;y<160;y++){REG32(0x040000D4)=src;REG32(0x040000D8)=dst;REG32(0x040000DC)=mode;src+=width;dst+=240;}
}
COLD void draw_return_map(void){int i,mx=20,my=62;box(8,31,224,123);centered(return_game_name(),35,GOLD);rect(mx,my,120,80,PAL_PINE4);rect(mx+8,my+12,104,56,PAL_GOLD4);line(mx+12,my+50,mx+108,my+20,PAL_WATER3);for(i=0;i<8;i++){int x=168+(i&1)*30,y=62+(i/2)*19;rect(x,y,10,10,(adventure_save.quests.region_flags[5]&(1u<<i))?GOLD:PAL_STONE2);if(room==54+i)rect(x-2,y-2,14,2,TEAL);}if(scrolling_room())rect(mx+px/4-1,my+py/4-1,3,3,PAL_HEART);centered(TX_G_NEXT_TAB,140,TEAL);}
COLD int return_hint_text(void){static const int hints[]={0,TX_RP_FACE,TX_RP_SIDE,TX_RP_HEARTH_CHARGE,TX_RP_HEARTH_RELEASE,TX_RP_NOTCH_CATCH,TX_RP_NOTCH_RELEASE,TX_RP_CARRY_RELEASE,TX_RP_QUIET_SIDE};unsigned h=return_powers_hint();return h<sizeof(hints)/sizeof(hints[0])?hints[h]:0;}
