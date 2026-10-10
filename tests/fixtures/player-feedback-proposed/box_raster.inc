/* Common opaque cards need one pass over each interior row. The original
 * five-rectangle behavior remains authoritative for clipped/small/unaligned
 * boxes and while a world cover is active. Keep this routine in ROM. */
COLD void proposal_box(int x,int y,int w,int h){
 if(!world_mask_active&&x>=0&&y>=0&&x+w<=240&&y+h<=160&&!(x&3)&&!(w&3)&&w>=32&&h>=3){
  /* DMA reads through MMIO addresses; volatile keeps source initialization
   * observable to the compiler even though no C pointer reads these words. */
  volatile u32 fill=(u32)UI_BG*0x01010101u,border=(u32)UI_BORDER*0x01010101u;
  u32 left=(fill&0xffffff00u)|UI_BORDER,right=(fill&0x00ffffffu)|((u32)UI_BORDER<<24);
  int row,words=w>>2;
#ifndef GAME_HOST_TEST
  REG32(0x040000D4)=(u32)&border;REG32(0x040000D8)=(u32)(screen+y*120+(x>>1));REG32(0x040000DC)=0x85000000|words;
  REG32(0x040000D8)=(u32)(screen+(y+h-1)*120+(x>>1));REG32(0x040000DC)=0x85000000|words;
  REG32(0x040000D4)=(u32)&fill;
#else
  {int col;for(col=x;col<x+w;col+=2){screen[y*120+(col>>1)]=(u16)border;screen[(y+h-1)*120+(col>>1)]=(u16)border;}}
#endif
  for(row=y+1;row<y+h-1;row++){
   u32 *dst=(u32*)(screen+row*120+(x>>1));dst[0]=left;dst[words-1]=right;
#ifndef GAME_HOST_TEST
   REG32(0x040000D8)=(u32)(dst+1);REG32(0x040000DC)=0x85000000|(words-2);
#else
   {int col;for(col=1;col<words-1;col++)dst[col]=fill;}
#endif
  }
  return;
 }
 rect(x,y,w,h,UI_BG);rect(x,y,w,1,UI_BORDER);rect(x,y+h-1,w,1,UI_BORDER);rect(x,y,1,h,UI_BORDER);rect(x+w-1,y,1,h,UI_BORDER);
}
