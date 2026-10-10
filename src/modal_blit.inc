/* Guaranteed opaque interiors only. Journal row153 remains true world. */
COLD int modal_coverage(int*out_left,int*out_first,int*out_last){int mode=game_display_state(),left,first,last;
 if(world_mask_disabled)return 0;
 if(quickparty_open){left=13;first=29;last=160;}
 else if(mode==PAUSE){left=4;first=31;last=journal_tab==JOURNAL_GOAL?150:153;}
 else if(mode==11||game_state==13){left=4;first=31;last=153;}
 else if(mode==EVOLVE_CONFIRM){left=6;first=42;last=147;}
 else if(mode==EVOLVE_ANIM){if(!progression_selected())return 0;left=10;first=38;last=152;}
 else if(mode==DIALOG){left=3;first=99;last=155;}
 else return 0;
 if(out_left)*out_left=left;
 if(out_first)*out_first=first;
 if(out_last)*out_last=last;
 return 1;
}
#define COPY_OPAQUE_MODAL_BITMAP modal_coverage(0,0,0)
COLD int copy_modal_background(const u8 *bitmap,const u8 *odd,unsigned width){
 int y,left,first,last;const u8 *base;
 if((width!=480&&width!=240)||!modal_coverage(&left,&first,&last))return 0;
 base=((camera_x&1)&&odd?odd:bitmap)+camera_y*width+camera_x-(camera_x&1);
#ifdef GAME_HOST_TEST
 /* Mirror the DMA effect for full-engine host framebuffer comparisons. The
  * separate camera oracle also executes the native register path below. */
 for(y=0;y<160;y++){int x;const u8*src=base+y*width;
  for(x=0;x<120;x++)if(y<first||y>=last||x<left||x>=120-left)screen[y*120+x]=(u16)(src[x*2]|((u16)src[x*2+1]<<8));
 }
 return 1;
#endif
 /* A fixed-width scene has contiguous uncovered top/bottom bands. Copy
  * those in two aligned word transfers instead of160 row setup sequences.
  * The narrow side bands keep the exact halfword geometry below. */
 if(width==240&&camera_x==0){
  REG32(0x040000D4)=(u32)base;REG32(0x040000D8)=(u32)screen;
  REG32(0x040000DC)=0x84000000|(first*60);
  if(last<160){REG32(0x040000D4)=(u32)(base+last*240);REG32(0x040000D8)=(u32)(screen+last*120);REG32(0x040000DC)=0x84000000|((160-last)*60);}
  for(y=first;y<last;y++){
   const u8 *src=base+y*240;u16 *dst=screen+y*120;
   REG32(0x040000D4)=(u32)src;REG32(0x040000D8)=(u32)dst;REG32(0x040000DC)=0x80000000|left;
   REG32(0x040000D4)=(u32)(src+240-left*2);REG32(0x040000D8)=(u32)(dst+120-left);REG32(0x040000DC)=0x80000000|left;
  }
  return 1;
 }
 for(y=0;y<160;y++){
  const u8 *src=base+y*width;u16 *dst=screen+y*120;
  REG32(0x040000D4)=(u32)src;REG32(0x040000D8)=(u32)dst;
  if(y>=first&&y<last){
   REG32(0x040000DC)=0x80000000|left;
   REG32(0x040000D4)=(u32)(src+240-left*2);REG32(0x040000D8)=(u32)(dst+120-left);
   REG32(0x040000DC)=0x80000000|left;
  }else REG32(0x040000DC)=0x80000000|120;
 }
 return 1;
}
