#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
typedef struct{u16 a0,a1,a2,pad;}ObjEntry;
#define PLAY 1
#define DIALOG 2
#define PAUSE 3
#define DEAD 4
#define EVOLVE_CONFIRM 7
#define EVOLVE_ANIM 8
#define SAVE_NOTICE_Y 8
#define SAVE_NOTICE_H 19
#define WHITE 7
#define INK 1
#define TEAL 80
#define OBJ_HUD_COMPANION 14400
#define OBJ_HUD_ACTION 14656
#define OBJ_HUD_COOLDOWN 14720
int camera_x,camera_y,game_state,quickparty_open,display_state,scrolling,save_visible,save_left,badge_left,reward_visible;
int summoned,ability_cd,ability_max,current_form;
int scrolling_room(void){return scrolling;}
int save_notice_visible(void){return save_visible;}
int save_notice_left(void){return save_left;}
int game_save_badge_left(void){return badge_left;}
int game_shop_reward_visible(void){return reward_visible;}
int game_display_state(void){return display_state;}
int progression_current_form(void){return current_form;}
static u8 companion[256];
const u8 *companion_form_pixels(int a,int b,int c){(void)a;(void)b;(void)c;return companion;}
typedef struct {int w,h,off;u8 bytes[256];}Upload;
#define obj_entries before_obj_entries
#define obj_depth before_obj_depth
#define obj_count before_obj_count
#define gfx_hud_code before_gfx_hud_code
#define gfx_hud_bar before_gfx_hud_bar
#define obj_upload before_obj_upload
#define obj_add before_obj_add
#define draw_floating_hud before_draw_floating_hud
#define uploads before_uploads
#define upload_count before_upload_count
ObjEntry obj_entries[128];int obj_depth[128],obj_count,gfx_hud_code,gfx_hud_bar,upload_count;Upload uploads[4];
void obj_upload(const u8*p,int w,int h,int off){if(upload_count>=4||w*h>256)abort();Upload*u=&uploads[upload_count++];u->w=w;u->h=h;u->off=off;memcpy(u->bytes,p,w*h);}
void obj_add(int off,int x,int y,int w,int h,int priority,int depth,int flip){int shape=0,size=0;ObjEntry o;
 if(scrolling_room()&&(priority==1||priority==2)){x-=camera_x;y-=camera_y;}

 if(obj_count>=120||x<=-w||x>=240||y<=-h||y>=160)return;
 /* Even corner HUD OBJ must not obscure the exceptional modal notice. */
 if(save_notice_visible()){int left=save_notice_left();if(x+w>left&&x<240-left&&y+h>SAVE_NOTICE_Y&&y<SAVE_NOTICE_Y+SAVE_NOTICE_H)return;}
 if(x+w>136&&x<200&&y+h>3&&y<20){int left=game_save_badge_left();if(left<200&&x+w>left)return;}
 if(game_state==PLAY&&game_shop_reward_visible()&&x+w>5&&x<121&&y+h>122&&y<139)return;
 /* Menus are background pixels: hide actors where a panel covers them. */
 if(priority==1||priority==2){if(quickparty_open&&x+w>26&&x<214&&y+h>29&&y<160)return;if(game_display_state()==PAUSE||game_display_state()==11||game_state==13||game_state==DEAD||game_state==EVOLVE_CONFIRM||game_state==EVOLVE_ANIM)return;if(game_display_state()==DIALOG&&y+h>99)return;}
 if(w==16&&h==16)size=1;else if(w==32&&h==32)size=2;else if(w==32&&h==16){shape=1;size=2;}else if(w==32&&h==8){shape=1;size=1;}else if(w==16&&h==8){shape=1;size=0;}
 o.a0=(y&255)|0x2000|(shape<<14);o.a1=(x&511)|(size<<14)|(flip?0x1000:0);o.a2=(512+off/32)|(priority<<10);o.pad=0;
 obj_entries[obj_count]=o;obj_depth[obj_count]=depth;obj_count++;
}
void draw_floating_hud(void){int code=(int)progression_current_form()*2+summoned;int width=ability_cd?(ability_max-ability_cd)*16/ability_max:16;
 if(code!=gfx_hud_code){u8 pixels[64];int x,y;const u8 rr[7]={30,17,17,30,20,18,17},bb[7]={30,17,17,30,17,17,30};const u8*rows=summoned?rr:bb;obj_upload(companion_form_pixels(progression_current_form(),0,0),16,16,OBJ_HUD_COMPANION);for(y=0;y<8;y++)for(x=0;x<8;x++)pixels[y*8+x]=(x>=1&&x<=5&&y<7&&(rows[y]&(1<<(5-x))))?WHITE:INK;obj_upload(pixels,8,8,OBJ_HUD_ACTION);gfx_hud_code=code;}
 if(width!=gfx_hud_bar){u8 pixels[256];int x,y;for(y=0;y<8;y++)for(x=0;x<32;x++)pixels[y*32+x]=(x<18&&y>=2&&y<=5)?((x>0&&x<=width&&y==3)?TEAL:INK):0;obj_upload(pixels,32,8,OBJ_HUD_COOLDOWN);gfx_hud_bar=width;}
 obj_add(OBJ_HUD_COMPANION,216,3,16,16,0,9999,0);obj_add(OBJ_HUD_ACTION,204,8,8,8,0,9999,0);obj_add(OBJ_HUD_COOLDOWN,215,18,32,8,0,9999,0);
}
#undef obj_entries
#undef obj_depth
#undef obj_count
#undef gfx_hud_code
#undef gfx_hud_bar
#undef obj_upload
#undef obj_add
#undef draw_floating_hud
#undef uploads
#undef upload_count
#define obj_entries after_obj_entries
#define obj_depth after_obj_depth
#define obj_count after_obj_count
#define gfx_hud_code after_gfx_hud_code
#define gfx_hud_bar after_gfx_hud_bar
#define obj_upload after_obj_upload
#define obj_add after_obj_add
#define draw_floating_hud after_draw_floating_hud
#define uploads after_uploads
#define upload_count after_upload_count
ObjEntry obj_entries[128];int obj_depth[128],obj_count,gfx_hud_code,gfx_hud_bar,upload_count;Upload uploads[4];
void obj_upload(const u8*p,int w,int h,int off){if(upload_count>=4||w*h>256)abort();Upload*u=&uploads[upload_count++];u->w=w;u->h=h;u->off=off;memcpy(u->bytes,p,w*h);}
void obj_add(int off,int x,int y,int w,int h,int priority,int depth,int flip){int shape=0,size=0;ObjEntry o;
 if((priority==1||priority==2)&&scrolling_room()){x-=camera_x;y-=camera_y;}

 if(obj_count>=120||x<=-w||x>=240||y<=-h||y>=160)return;
 /* Even corner HUD OBJ must not obscure the exceptional modal notice. */
 if(save_notice_visible()){int left=save_notice_left();if(x+w>left&&x<240-left&&y+h>SAVE_NOTICE_Y&&y<SAVE_NOTICE_Y+SAVE_NOTICE_H)return;}
 if(x+w>136&&x<200&&y+h>3&&y<20){int left=game_save_badge_left();if(left<200&&x+w>left)return;}
 if(game_state==PLAY&&x+w>5&&x<121&&y+h>122&&y<139&&game_shop_reward_visible())return;
 /* Menus are background pixels: hide actors where a panel covers them. */
 if(priority==1||priority==2){int display=game_display_state();if(quickparty_open&&x+w>26&&x<214&&y+h>29&&y<160)return;if(display==PAUSE||display==11||game_state==13||game_state==DEAD||game_state==EVOLVE_CONFIRM||game_state==EVOLVE_ANIM)return;if(display==DIALOG&&y+h>99)return;}
 if(w==16&&h==16)size=1;else if(w==32&&h==32)size=2;else if(w==32&&h==16){shape=1;size=2;}else if(w==32&&h==8){shape=1;size=1;}else if(w==16&&h==8){shape=1;size=0;}
 o.a0=(y&255)|0x2000|(shape<<14);o.a1=(x&511)|(size<<14)|(flip?0x1000:0);o.a2=(512+off/32)|(priority<<10);o.pad=0;
 obj_entries[obj_count]=o;obj_depth[obj_count]=depth;obj_count++;
}
void draw_floating_hud(void){int code=(int)progression_current_form()*2+summoned;int width=ability_cd?(ability_max-ability_cd)*16/ability_max:16;
 if(code!=gfx_hud_code){u8 pixels[64];int x,y;const u8 rr[7]={30,17,17,30,20,18,17},bb[7]={30,17,17,30,17,17,30};const u8*rows=summoned?rr:bb;obj_upload(companion_form_pixels(progression_current_form(),0,0),16,16,OBJ_HUD_COMPANION);for(y=0;y<8;y++)for(x=0;x<8;x++)pixels[y*8+x]=(x>=1&&x<=5&&y<7&&(rows[y]&(1<<(5-x))))?WHITE:INK;obj_upload(pixels,8,8,OBJ_HUD_ACTION);gfx_hud_code=code;}
 if(width!=gfx_hud_bar){u32 pixels[64];u8*bytes=(u8*)pixels;u32 ink=(u32)INK*0x01010101u;int x,y;
  /* Exact same 32x8 tile: only rows2..5 and columns0..17 are opaque. */
  for(x=0;x<64;x++)pixels[x]=0;
  for(y=2;y<=5;y++){for(x=0;x<4;x++)pixels[y*8+x]=ink;pixels[y*8+4]=ink&0xffffu;}
  for(x=1;x<18&&x<=width;x++)bytes[3*32+x]=TEAL;
  obj_upload(bytes,32,8,OBJ_HUD_COOLDOWN);gfx_hud_bar=width;}
 obj_add(OBJ_HUD_COMPANION,216,3,16,16,0,9999,0);obj_add(OBJ_HUD_ACTION,204,8,8,8,0,9999,0);obj_add(OBJ_HUD_COOLDOWN,215,18,32,8,0,9999,0);
}
#undef obj_entries
#undef obj_depth
#undef obj_count
#undef gfx_hud_code
#undef gfx_hud_bar
#undef obj_upload
#undef obj_add
#undef draw_floating_hud
#undef uploads
#undef upload_count

static unsigned long long objects,huds;
static uint32_t rng=0xaf618542;
static unsigned random32(void){rng=rng*1664525u+1013904223u;return rng;}
static void init(int count){
 memset(before_obj_entries,0x51,sizeof before_obj_entries);memcpy(after_obj_entries,before_obj_entries,sizeof before_obj_entries);
 memset(before_obj_depth,0xc7,sizeof before_obj_depth);memcpy(after_obj_depth,before_obj_depth,sizeof before_obj_depth);
 before_obj_count=after_obj_count=count;
 memset(before_uploads,0xb3,sizeof before_uploads);memcpy(after_uploads,before_uploads,sizeof before_uploads);before_upload_count=after_upload_count=0;
}
static void same(int x,int y,int w,int h,int priority){
 if(before_obj_count!=after_obj_count||memcmp(before_obj_entries,after_obj_entries,sizeof before_obj_entries)||memcmp(before_obj_depth,after_obj_depth,sizeof before_obj_depth)){
  fprintf(stderr,"OBJ FAIL x=%d y=%d w=%d h=%d p=%d raw=%d display=%d quick=%d save=%d left=%d badge=%d reward=%d scroll=%d\n",x,y,w,h,priority,game_state,display_state,quickparty_open,save_visible,save_left,badge_left,reward_visible,scrolling);exit(1);
 }
}
static void objcase(int x,int y,int w,int h,int priority,int count,int flip,int off,int depth){
 init(count);before_obj_add(off,x,y,w,h,priority,depth,flip);after_obj_add(off,x,y,w,h,priority,depth,flip);same(x,y,w,h,priority);objects++;
}
static void hudcase(int cd,int max,int bar,int code,int summon,int form){
 ability_cd=cd;ability_max=max;summoned=summon;current_form=form;init(0);
 before_gfx_hud_bar=after_gfx_hud_bar=bar;before_gfx_hud_code=after_gfx_hud_code=code;
 before_draw_floating_hud();after_draw_floating_hud();same(0,0,0,0,0);huds++;
 if(before_gfx_hud_bar!=after_gfx_hud_bar||before_gfx_hud_code!=after_gfx_hud_code||before_upload_count!=after_upload_count||memcmp(before_uploads,after_uploads,sizeof before_uploads)){
  fprintf(stderr,"HUD FAIL cd=%d max=%d bar=%d code=%d summoned=%d form=%d\n",cd,max,bar,code,summon,form);exit(1);
 }
}
int main(void){
 int raw,display,q,s,r,bl,sl,pr,sc,g,x,y,w,h,k;unsigned i;
 const int badge[]={0,120,136,150,199,200,240};const int left[]={0,13,80,119,120};
 const int geometry[][4]={{0,0,8,8},{-16,0,16,16},{-15,-15,16,16},{239,159,16,16},{240,160,16,16},{5,122,32,16},{121,139,32,16},{136,3,32,8},{199,19,16,8},{26,29,32,32},{214,160,16,16},{120,98,16,16},{120,99,16,16},{120,100,16,16},{120,8,16,16},{120,27,16,16}};
 for(raw=0;raw<14;raw++)for(display=0;display<14;display++)for(q=0;q<2;q++)for(s=0;s<2;s++)for(r=0;r<2;r++)for(bl=0;bl<7;bl++)for(sl=0;sl<5;sl++)for(pr=0;pr<4;pr++)for(sc=0;sc<2;sc++)for(g=0;g<16;g++){
  game_state=raw;display_state=display;quickparty_open=q;save_visible=s;reward_visible=r;badge_left=badge[bl];save_left=left[sl];scrolling=sc;camera_x=sc?1:0;camera_y=sc?3:0;
  objcase(geometry[g][0],geometry[g][1],geometry[g][2],geometry[g][3],pr,raw%3?0:119,g&1,14720,(g-8)*1000);
 }
 printf("PASS OBJ mode matrix %llu\n",objects);fflush(stdout);
 const int xx[]={-481,-33,-32,-31,-17,-16,-15,-9,-8,-7,-1,0,1,4,5,6,7,8,12,13,20,25,26,27,119,120,121,135,136,137,198,199,200,213,214,215,238,239,240,241,479,480};
 const int yy[]={-321,-33,-32,-31,-17,-16,-15,-9,-8,-7,-1,0,1,2,3,4,7,8,9,19,20,21,26,27,28,29,30,31,98,99,100,121,122,123,138,139,140,158,159,160,161,319,320};
 const int sizes[][2]={{8,8},{16,16},{32,32},{32,16},{32,8},{16,8},{64,64},{0,0},{-1,-1},{1,1}};
 for(g=0;g<10;g++)for(x=0;x<42;x++)for(y=0;y<43;y++)for(pr=0;pr<4;pr++)for(sc=0;sc<2;sc++){
  game_state=(x+y)%14;display_state=(x*3+y)%14;quickparty_open=x&1;save_visible=y&1;reward_visible=(x+y)&1;badge_left=badge[x%7];save_left=left[y%5];scrolling=sc;camera_x=sc?240:0;camera_y=sc?160:0;
  objcase(xx[x],yy[y],sizes[g][0],sizes[g][1],pr,(x+y)%3==0?120:(x+y)%3==1?119:0,x&1,(x-20)*32,y-20);
 }
 for(i=0;i<100000;i++){
  game_state=random32()%14;display_state=random32()%14;quickparty_open=random32()%2;save_visible=random32()%2;save_left=random32()%241;badge_left=random32()%241;reward_visible=random32()%2;scrolling=random32()%2;camera_x=random32()%241;camera_y=random32()%161;
  x=(int)(random32()%1201)-480;y=(int)(random32()%801)-320;w=(int)(random32()%130)-1;h=(int)(random32()%130)-1;pr=random32()%32;
  objcase(x,y,w,h,pr,random32()%125,random32()%2,(int)(random32()%16000),(int)random32());
 }
 printf("PASS all OBJ %llu\n",objects);fflush(stdout);
 for(i=0;i<sizeof companion;i++)companion[i]=(u8)(i*17+39);
 game_state=display_state=1;quickparty_open=save_visible=reward_visible=scrolling=0;badge_left=240;save_left=80;camera_x=camera_y=0;
 // Every generated width -4096..4096 plus no-upload cache path and signed color-independent bounds.
 for(k=-4096;k<=4096;k++)for(s=0;s<2;s++){
  hudcase(16-k,16,k^0x55,-1,s,128);hudcase(16-k,16,k,256+s,s,128);
 }
 // Real cooldown intervals including division rounding and pre-existing mixed upload/cache paths.
 for(w=1;w<=512;w++)for(h=0;h<=w;h++)hudcase(h,w,-1,-1,h&1,h%129);
 // Signed out-of-range cooldowns remain representable; division by zero / overflow excluded as UB in original.
 for(i=0;i<100000;i++){
  x=(int)(random32()%2000001)-1000000;y=(int)(random32()%2001)-1000;if(!y)y=1;
  hudcase(x,y,(int)random32(),(int)(random32()%258),random32()%2,random32()%129);
 }
 printf("{\"object_comparisons\":%llu,\"hud_comparisons\":%llu,\"all_equal\":true,\"full_obj_entries_depth_count_and_upload_bytes_equal\":true}\n",objects,huds);
 return 0;
}
