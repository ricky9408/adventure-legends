/* Ending-only, read-only presentation. No save data, rewards or music ownership. */
#include "ending_credits.h"
#include "ending_credits_text.h"
#include "assets.h"
extern int keys,pressed,arrival_input_mask;
extern unsigned short *screen;
extern void rect(int,int,int,int,unsigned char),text_spans(const UiText*,int,int,int);
unsigned ending_credits_phase,ending_credits_scroll,ending_credits_revision,ending_credits_armed;
static unsigned clock_ticks;
#define BUTTONS (1u|2u|8u)
#define TOP 24
#define BOTTOM 138
#define ROW_HEIGHT 20
#define FIRST_Y 144
#define LINE_COUNT (EC_COUNT-EC_LINE_0)

ENDING_CODE void ending_credits_begin(void){
 ending_credits_phase=ending_credits_scroll=ending_credits_armed=clock_ticks=0;
 ending_credits_revision++;
}
static ENDING_CODE void roll_begin(void){
 ending_credits_phase=1;ending_credits_scroll=clock_ticks=ending_credits_armed=0;ending_credits_revision++;
}
ENDING_CODE int ending_credits_update(void){
 /* Input must be entirely released at every entry/phase boundary. A held
  * final-dialogue A, B or Start can neither skip nor leak into the field. */
 if(!ending_credits_armed){if(!((unsigned)keys&BUTTONS)){ending_credits_armed=1;ending_credits_revision++;}return 0;}
 if((unsigned)pressed&(2u|8u)){arrival_input_mask|=keys;pressed=0;return 1;}
 if(!ending_credits_phase){if(((unsigned)pressed&1u)||++clock_ticks>=180)roll_begin();return 0;}
 if(ending_credits_phase==2){if((unsigned)pressed&1u)roll_begin();return 0;}
 if(++clock_ticks<3)return 0;
 clock_ticks=0;ending_credits_scroll++;ending_credits_revision++;
 if(ending_credits_scroll>FIRST_Y+(LINE_COUNT-1)*ROW_HEIGHT+15-TOP){ending_credits_phase=2;ending_credits_armed=0;}
 return 0;
}
static ENDING_CODE void center(unsigned id,int y,int col){const UiText*t=&ending_credits_texts[id];text_spans(t,(240-t->width)/2,y,col);}
/* Spans are y-sorted. Keep a row cursor instead of per-span division and
 * reject clipped rows before constructing any VRAM pointer. Both odd/even
 * halfword masks retain their background bytes and never write offscreen. */
static ENDING_CODE void clipped(unsigned id,int y,int col){
 const UiText*t=&ending_credits_texts[id];int x=(240-t->width)/2;
 const UiRun*r=t->runs[x&1];unsigned n=t->count[x&1],row=0,next=120;
 unsigned short ink=(unsigned short)(col|(col<<8));
 while(n--){unsigned offset=r->offset,count=r->count,mask=r->mask;int yy;r++;
  while(offset>=next){row++;next+=120;}
  yy=y+(int)row;if(yy<TOP||yy>=BOTTOM)continue;
  {unsigned short*dst=screen+yy*120+(x>>1)+(offset-(next-120));
   if(mask==3)while(count--)*dst++=ink;
   else if(mask==1)while(count--){*dst=(*dst&0xff00)|(unsigned)col;dst++;}
   else while(count--){*dst=(*dst&255)|((unsigned)col<<8);dst++;}
  }
 }
}
ENDING_CODE void ending_credits_card_hint(void){center(ending_credits_armed?EC_CARD_HINT:EC_RELEASE_HINT,128,PAL_TEAL2);}
ENDING_CODE int ending_credits_draw(void){unsigned i;
 if(!ending_credits_phase)return 0;
 rect(0,0,240,160,PAL_INK);center(EC_TITLE,5,PAL_GOLD3);
 rect(12,20,216,1,PAL_TEAL2);rect(12,140,216,1,PAL_TEAL2);
 if(ending_credits_phase==2){center(EC_THANKS,64,PAL_GOLD4);center(ending_credits_armed?EC_DONE_HINT:EC_RELEASE_HINT,145,PAL_TEAL2);return 1;}
 for(i=0;i<LINE_COUNT;i++){int y=FIRST_Y+(int)i*ROW_HEIGHT-(int)ending_credits_scroll;if(y+15>TOP&&y<BOTTOM)clipped(EC_LINE_0+i,y,PAL_GOLD4);}
 center(ending_credits_armed?EC_ROLL_HINT:EC_RELEASE_HINT,145,PAL_TEAL2);return 1;
}
