/* 5x7 letterforms for an exact-pixel wordmark. */
const u8 alphabet[26][7]={{14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{14,17,16,16,16,17,14},{30,17,17,17,17,17,30},{31,16,16,30,16,16,31},{31,16,16,30,16,16,16},{14,17,16,23,17,17,15},{17,17,17,31,17,17,17},{31,4,4,4,4,4,31},{7,2,2,2,18,18,12},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},{17,27,21,21,17,17,17},{17,25,25,21,19,19,17},{14,17,17,17,17,17,14},{30,17,17,30,16,16,16},{14,17,17,17,21,18,13},{30,17,17,30,20,18,17},{15,16,16,14,1,1,30},{31,4,4,4,4,4,4},{17,17,17,17,17,17,14},{17,17,17,17,17,10,4},{17,17,17,21,21,27,17},{17,17,10,4,10,17,17},{17,17,10,4,4,4,4},{31,1,2,4,8,16,31}};
#include "feedback_title_data.inc"
COLD void wordmark(void){int y;
 /* Called only after BACK_TITLE: this generated patch includes the exact
  * background between glyphs and preserves the original shadow order. */
 for(y=0;y<23;y++){
#ifndef GAME_HOST_TEST
  REG32(0x040000D4)=(u32)feedback_title_wordmark[y];REG32(0x040000D8)=(u32)(screen+(35+y)*120+20);REG32(0x040000DC)=0x84000000|41;
#else
  int x;for(x=0;x<82;x++)screen[(35+y)*120+20+x]=(u16)(feedback_title_wordmark[y][x*2]|((u16)feedback_title_wordmark[y][x*2+1]<<8));
#endif
 }
}
COLD void draw_route_map(void){int i;const int names[]={TX_C_MAP_GROVE,TX_C_MAP_SKY,TX_C_MAP_CORE};int selected=room==14?1:room>=9?2:room>=4?1:0;box(8,31,224,122);centered(TX_C_MAP_ROUTE,35,GOLD);line(48,78,192,78,PAL_GOLD2);for(i=0;i<3;i++){int x=48+i*72;rect(x-9,66,18,22,(chapter_flags&(1u<<i))?PAL_GOLD3:PAL_STONE1);rect(x-5,70,10,14,(chapter_flags&(1u<<i))?PAL_FIRE2:PAL_STONE3);if(selected==i){rect(x-12,62,24,2,TEAL);rect(x-12,92,24,2,TEAL);}text(names[i],x-ui_texts[names[i]].width/2,100,CREAM);}centered(TX_C_MAP_RETURN,120,CREAM);centered(TX_C_MAP_NEXT,136,TEAL);}
COLD void draw_companion_journal(void){quickparty_draw_journal();}
