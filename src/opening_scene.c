/* Original village morning. No campaign flags, codec fields or SRAM writes
 * exist here. Only completing/skipping requests the ordinary initial save. */
#include "opening_scene.h"
#include "opening_scene_data.h"
#include "assets.h"
#include "progression.h"
extern volatile int game_state;
extern int keys,pressed,frame,page,arrival_input_mask,world_mask_active,obj_count;
extern int cache_valid[2],save_begin_pending,save_completion_pending;
extern unsigned short *screen;
extern void copy_bg(int);
extern void box(int,int,int,int);
extern void sprite(const unsigned char*,int,int,int,int,int);
extern void obj_sprite(int,int,int,int);
extern void obj_add(int,int,int,int,int,int,int,int);
extern void toast(int);
#if defined(__arm__)
extern void save_game(void) __attribute__((long_call));
#else
extern void save_game(void);
#endif
unsigned char opening_page,opening_clock,opening_armed;
static unsigned char painted[2];

static OPENING_CODE void opening_text(unsigned id,int x,int y,int col){
 const UiText*t=&opening_scene_texts[id];const UiRun*r=t->runs[x&1];
 unsigned n=t->count[x&1];unsigned short*base=screen+y*120+(x>>1),color=(unsigned short)(col|(col<<8));
 while(n--){unsigned short*dst=base+r->offset;unsigned count=r->count,mask=r->mask;r++;
  if(mask==3)while(count--)*dst++=color;
  else if(mask==1)while(count--){*dst=(*dst&0xff00)|col;dst++;}
  else while(count--){*dst=(*dst&255)|(col<<8);dst++;}
 }
}
OPENING_CODE void opening_scene_begin(void){
 opening_page=opening_clock=opening_armed=0;painted[0]=painted[1]=255;
 cache_valid[0]=cache_valid[1]=0;save_requested=0;save_begin_pending=save_completion_pending=0;
 game_state=OPENING_SCENE;
}
static OPENING_CODE void opening_finish(void){
 /* Preserve every existing SRAM byte until this exact boundary. Normal
  * transactional save semantics then protect interruption of the first save. */
 game_state=1;arrival_input_mask|=keys;pressed=0;
 cache_valid[0]=cache_valid[1]=0;toast(TX_EXPLORE1);save_game();
}
OPENING_CODE void opening_scene_update(void){
 if(opening_clock<240)opening_clock++;
 /* Both title/confirmation controls must be released before either can act.
  * Later pages use hardware pressed edges, never held-key auto-advance. */
 if(!opening_armed){if(!(keys&(1|8)))opening_armed=1;return;}
 if(pressed&8){opening_finish();return;}
 if(pressed&1){if(++opening_page>=OPENING_SCENE_PAGES){opening_page=OPENING_SCENE_PAGES-1;opening_finish();}else opening_clock=0;}
}
OPENING_CODE void opening_scene_render(void){
 unsigned beat=opening_page,light,step=opening_clock<28?opening_clock:28;
 int homura_x=94,homura_y=77,midori_x=156,midori_y=81;
 screen=(unsigned short*)(page?0x0600a000:0x06000000);world_mask_active=0;obj_count=0;
 /* The title activation already spends a frame on new-game initialization.
  * Leave the already-painted title back page intact and do no extra copy;
  * paint the opening on the next update, inside its own frame budget. */
 if(!opening_clock&&!opening_armed)return;
 if(painted[page]!=beat){
  copy_bg(BACK_VILLAGE);
  box(30,1,180,17);opening_text(OS_TITLE,(240-opening_scene_texts[OS_TITLE].width)/2,2,PAL_GOLD4);
  sprite(opening_chore_props,158,77,32,16,0);
  box(4,96,232,63);
  opening_text(OS_SPEAKER0+beat*3,12,98,PAL_GOLD3);
  opening_text(OS_LINE0_0+beat*3,12,114,PAL_GOLD4);
  opening_text(OS_LINE0_1+beat*3,12,130,PAL_GOLD4);
  opening_text(OS_CONTROLS,(240-opening_scene_texts[OS_CONTROLS].width)/2,145,PAL_TEAL2);
  painted[page]=(unsigned char)beat;
 }
 /* The native 16x24 prop includes its exact village underlay, so each pulse
  * erases the previous one without re-rendering the world or moving actors. */
 light=beat<2?(unsigned)(frame/18)&1u:2u;
 if(beat==2&&opening_clock<72)light=(opening_clock/6)%3;
 sprite(opening_lantern[light],112,44,16,24,0);
 if(beat>=4){homura_x+=beat==4?(int)step/2:14;homura_y+=beat==4?(int)step/4:7;}
 if(beat>=5){midori_x-=beat==5?(int)step/2:14;midori_y+=beat==5?(int)step/7:4;}
 obj_add(6656,112,80,16,16,2,85,0);obj_sprite(SPR_HERO_UP_0,120,86,86);
 obj_add(6656,123,62,16,16,2,66,0);obj_sprite(SPR_ELDER,131,68,68);
 obj_add(6656,homura_x-8,homura_y-6,16,16,2,homura_y-1,0);
 obj_sprite(SPR_FOX_0+((frame/16)&1),homura_x,homura_y,homura_y);
 obj_add(6656,midori_x-8,midori_y-6,16,16,2,midori_y-1,0);
 obj_sprite(SPR_LEAF_0+((frame/20)&1),midori_x,midori_y,midori_y);
 /* A tiny glint marks the choice to help; the light itself stays weak. */
 if((beat==4||beat==5)&&opening_clock<40&&(opening_clock&8))
  obj_add(10560,(beat==4?homura_x:midori_x)-4,59,8,8,1,99,0);
}
