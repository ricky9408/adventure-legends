/* Only the base atlas copy skips pixels guaranteed to be hidden by an opaque
 * card. Every world overlay still runs; visible changed-world pixels stay fresh.
 * Evolution confirmation variants contain (12,42,216,105); evolution
 * animation paints (20,38,200,114) whenever its selected instance exists.
 * The opening journal card (tab zero) paints (8,31,224,119). Other pause
 * tabs retain their original path; the saved world strip at y153 stays fresh.
 * Save/event popups contain the
 * even-pixel interior (38,77,164,34) inside their original (37,77,166,34) card. */
#define COPY_OPAQUE_MODAL_BITMAP (game_state==EVOLVE_CONFIRM||game_state==EVOLVE_ANIM||game_state==SAVE_PENDING||game_state==EVENT_PENDING||(game_state==PAUSE&&journal_tab==0))
COLD int copy_modal_background(const u8 *bitmap,const u8 *odd,unsigned width){
 int y,left,first,last;const u8 *base;
 if(width!=480)return 0;
 if(game_state==PAUSE&&journal_tab==0){left=4;first=31;last=150;}
 else if(game_state==EVOLVE_CONFIRM){left=6;first=42;last=147;}
 else if(game_state==EVOLVE_ANIM){if(!progression_selected())return 0;left=10;first=38;last=152;}
 else if(game_state==SAVE_PENDING||game_state==EVENT_PENDING){left=19;first=77;last=111;}
 else return 0;
 base=((camera_x&1)?odd:bitmap)+camera_y*width+camera_x-(camera_x&1);
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
