#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <limits.h>
#define COLD
#define GAME_HOST_TEST 1
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
int world_mask_active,world_mask_left,world_mask_right,world_mask_top,world_mask_bottom,room;
struct Art{unsigned short width,height;} horizons_art_rooms[8],covenants_art_rooms[8];

u16 *before_screen;
#define ab before_ab
#define sign before_sign
#define game_world_rect_hidden before_game_world_rect_hidden
#define pix before_pix
#define rect before_rect
#define line before_line
#define scrolling_room before_scrolling_room
#define screen before_screen
int ab(int n){return n<0?-n:n;}
int sign(int n){return(n>0)-(n<0);}
COLD int game_world_rect_hidden(int x,int y,int w,int h){return world_mask_active&&x>=world_mask_left&&y>=world_mask_top&&x+w<=world_mask_right&&y+h<=world_mask_bottom;}
void pix(int x,int y,u8 c){if((unsigned)x>=240||(unsigned)y>=160)return;u16 *p=screen+y*120+(x>>1);u16 v=*p;*p=(x&1)?((v&255)|(c<<8)):((v&0xFF00)|c);}
void rect(int x,int y,int w,int h,u8 c){int yy,xx;if(world_mask_active&&game_world_rect_hidden(x,y,w,h))return;u32 fill=(u32)c*0x01010101u;if(x<0){w+=x;x=0;}if(y<0){h+=y;y=0;}if(x+w>240)w=240-x;if(y+h>160)h=160-y;if(w<1||h<1)return;
 for(yy=y;yy<y+h;yy++){int left=x,right=x+w;if(left&1)pix(left++,yy,c);if(right&1)pix(--right,yy,c);u16 *p=screen+yy*120+(left>>1);
  /* Host pixel tests use the same CPU fill without accessing DMA registers. */
#ifndef GAME_HOST_TEST
  if(right-left>=32){if(left&2){*p++=(u16)fill;left+=2;}if((right-left)&2){screen[yy*120+(right>>1)-1]=(u16)fill;right-=2;}REG32(0x040000D4)=(u32)&fill;REG32(0x040000D8)=(u32)p;REG32(0x040000DC)=0x85000000|((right-left)>>2);}
  else
#endif
  for(xx=left;xx<right;xx+=2)*p++=(u16)fill;
 }}
void line(int x,int y,int x2,int y2,int col){if(world_mask_active&&game_world_rect_hidden(x<x2?x:x2,y<y2?y:y2,ab(x-x2)+1,ab(y-y2)+1))return;int dx=ab(x2-x),sx=sign(x2-x),dy=-ab(y2-y),sy=sign(y2-y),e=dx+dy,e2;while(1){pix(x,y,col);if(x==x2&&y==y2)break;e2=2*e;if(e2>=dy){e+=dy;x+=sx;}if(e2<=dx){e+=dx;y+=sy;}}}
int scrolling_room(void){return room==1||room==16||room==17||room==22||room==23||room==30||room==31||room==38||room==39||room==46||room==47||room==48||room==51||room==54||room==56||room==57||room==58||((unsigned)room-62u<8u&&(horizons_art_rooms[room-62].width>240||horizons_art_rooms[room-62].height>160))||((unsigned)room-70u<8u&&(covenants_art_rooms[room-70].width>240||covenants_art_rooms[room-70].height>160));}
#undef ab
#undef sign
#undef game_world_rect_hidden
#undef pix
#undef rect
#undef line
#undef scrolling_room
#undef screen

u16 *after_screen;
#define ab after_ab
#define sign after_sign
#define game_world_rect_hidden after_game_world_rect_hidden
#define pix after_pix
#define rect after_rect
#define line after_line
#define scrolling_room after_scrolling_room
#define screen after_screen
int ab(int n){return n<0?-n:n;}
int sign(int n){return(n>0)-(n<0);}
COLD int game_world_rect_hidden(int x,int y,int w,int h){return world_mask_active&&x>=world_mask_left&&y>=world_mask_top&&x+w<=world_mask_right&&y+h<=world_mask_bottom;}
void pix(int x,int y,u8 c){if((unsigned)x>=240||(unsigned)y>=160)return;u16 *p=screen+y*120+(x>>1);u16 v=*p;*p=(x&1)?((v&255)|(c<<8)):((v&0xFF00)|c);}
void rect(int x,int y,int w,int h,u8 c){
 int left,right,odd_left,odd_right,words,row;__UINTPTR_TYPE__ dst;u32 fill=(u32)c*0x01010101u;
 if(world_mask_active&&game_world_rect_hidden(x,y,w,h))return;
 if(x<0){w+=x;x=0;}if(y<0){h+=y;y=0;}
 if(x+w>240)w=240-x;if(y+h>160)h=160-y;if(w<1||h<1)return;
 left=x;right=x+w;odd_left=left&1;odd_right=right&1;
 dst=(__UINTPTR_TYPE__)(screen+y*120+(left>>1));
 if(odd_left)left++;if(odd_right)right--;
 words=(right-left)>>1;
 /* Advance a byte address, avoiding a dead pointer beyond the final row
  * when screen names a smaller cached notice surface. */
 for(row=0;row<h;row++,dst+=240){u16*p=(u16*)dst;int n=words;
  if(odd_left){*p=(*p&255)|((u16)c<<8);p++;}
  if(odd_right){u16*q=p+n;*q=(*q&0xff00)|c;}
#ifndef GAME_HOST_TEST
  if(right-left>=32){
   if(left&2){*p++=(u16)fill;n--;}
   if(n&1){p[n-1]=(u16)fill;n--;}
   REG32(0x040000D4)=(u32)&fill;REG32(0x040000D8)=(u32)p;REG32(0x040000DC)=0x85000000|(n>>1);
  }else
#endif
  while(n--)*p++=(u16)fill;
 }
}
void line(int x,int y,int x2,int y2,int col){if(y==y2){rect(x<x2?x:x2,y,ab(x2-x)+1,1,col);return;}if(x==x2){rect(x,y<y2?y:y2,1,ab(y2-y)+1,col);return;}if(world_mask_active&&game_world_rect_hidden(x<x2?x:x2,y<y2?y:y2,ab(x-x2)+1,ab(y-y2)+1))return;int dx=ab(x2-x),sx=sign(x2-x),dy=-ab(y2-y),sy=sign(y2-y),e=dx+dy,e2;while(1){pix(x,y,col);if(x==x2&&y==y2)break;e2=2*e;if(e2>=dy){e+=dy;x+=sx;}if(e2<=dx){e+=dx;y+=sy;}}}
int scrolling_room(void){
 unsigned current=(unsigned)room;
 /* Snapshot once: the room does not change during one query. Preserve the
  * legacy set exactly; mixed-size chapters use their authored dimensions. */
 if(current-70u<8u)return covenants_art_rooms[current-70u].width>240||covenants_art_rooms[current-70u].height>160;
 if(current-62u<8u)return horizons_art_rooms[current-62u].width>240||horizons_art_rooms[current-62u].height>160;
 if(current<32u)return (0xC0C30002u>>current)&1u;
 if(current<64u)return (0x0749C0C0u>>(current-32u))&1u;
 return 0;
}
#undef ab
#undef sign
#undef game_world_rect_hidden
#undef pix
#undef rect
#undef line
#undef scrolling_room
#undef screen

#define BYTES 38400
#define GUARD 256
static union { uint32_t align; uint8_t v[BYTES+2*GUARD]; } aa,bb;
static uint8_t seed[BYTES+2*GUARD];
static unsigned long long rectangles,lines,scrolls;
static uint32_t rnd=0x185f39b1u;
static uint32_t random32(void){rnd=rnd*1664525u+1013904223u;return rnd;}
static const int masks[][5]={
 {0,0,0,240,160},{1,0,0,240,160},{1,8,31,232,153},
 {1,8,31,232,150},{1,26,29,214,160},{1,12,42,228,147},
 {1,20,38,220,152},{1,6,99,234,155},{1,-12,-8,252,168},
 {1,0,0,0,0},{1,240,160,260,180},{1,80,80,40,40}
};
static void setmask(int m){world_mask_active=masks[m][0];world_mask_left=masks[m][1];world_mask_top=masks[m][2];world_mask_right=masks[m][3];world_mask_bottom=masks[m][4];}
static void check(int kind,int x,int y,int a,int b,int col,int mask){
 setmask(mask);memcpy(aa.v,seed,sizeof(seed));memcpy(bb.v,seed,sizeof(seed));
 if(kind){before_line(x,y,a,b,col);after_line(x,y,a,b,col);lines++;}
 else{before_rect(x,y,a,b,col);after_rect(x,y,a,b,col);rectangles++;}
 if(memcmp(aa.v,bb.v,sizeof(seed))||memcmp(aa.v,seed,GUARD)||memcmp(bb.v,seed,GUARD)||memcmp(aa.v+BYTES+GUARD,seed+BYTES+GUARD,GUARD)||memcmp(bb.v+BYTES+GUARD,seed+BYTES+GUARD,GUARD)){
  unsigned i;for(i=0;i<sizeof(seed)&&aa.v[i]==bb.v[i];i++);
  fprintf(stderr,"FAIL kind=%d x=%d y=%d a=%d b=%d col=%d mask=%d pixel=%d old=%u new=%u\n",kind,x,y,a,b,col,mask,(int)i-GUARD,i<sizeof(seed)?aa.v[i]:0,i<sizeof(seed)?bb.v[i]:0);exit(1);
 }
}
static void checkscroll(int r){room=r;int b=before_scrolling_room(),a=after_scrolling_room();scrolls++;if(a!=b){fprintf(stderr,"FAIL scrolling room=%d old=%d new=%d\n",r,b,a);exit(1);}}
int main(void){
 unsigned i;int x,y,a,b,c,m,k;for(i=0;i<sizeof(seed);i++)seed[i]=(uint8_t)random32();before_screen=(u16*)(aa.v+GUARD);after_screen=(u16*)(bb.v+GUARD);
horizons_art_rooms[0]=(struct Art){480,320};
horizons_art_rooms[1]=(struct Art){480,160};
horizons_art_rooms[2]=(struct Art){240,160};
horizons_art_rooms[3]=(struct Art){480,320};
horizons_art_rooms[4]=(struct Art){240,320};
horizons_art_rooms[5]=(struct Art){480,320};
horizons_art_rooms[6]=(struct Art){240,160};
horizons_art_rooms[7]=(struct Art){240,160};
covenants_art_rooms[0]=(struct Art){480,320};
covenants_art_rooms[1]=(struct Art){240,320};
covenants_art_rooms[2]=(struct Art){480,160};
covenants_art_rooms[3]=(struct Art){240,160};
covenants_art_rooms[4]=(struct Art){480,320};
covenants_art_rooms[5]=(struct Art){240,320};
covenants_art_rooms[6]=(struct Art){480,160};
covenants_art_rooms[7]=(struct Art){240,160};
 // Dense valid and invalid room domain, integer extremes and random full words.
 for(x=-65536;x<=65536;x++)checkscroll(x);
 const int edge_rooms[]={INT_MIN,INT_MIN+1,-1000000,-1,0,1,31,32,61,62,63,64,69,70,77,78,255,256,INT_MAX-1,INT_MAX};
 for(i=0;i<sizeof(edge_rooms)/sizeof(*edge_rooms);i++)checkscroll(edge_rooms[i]);
 for(i=0;i<1000000;i++)checkscroll((int)random32());
 // Dynamic authored dimensions, independently for every mixed-size room.
 const int dimensions[]={0,1,159,160,161,239,240,241,319,320,480,65535};
 for(k=62;k<78;k++)for(a=0;a<12;a++)for(b=0;b<12;b++){
  struct Art *p=k<70?&horizons_art_rooms[k-62]:&covenants_art_rooms[k-70];*p=(struct Art){dimensions[a],dimensions[b]};checkscroll(k);
 }
 printf("PASS scrolling %llu comparisons\n",scrolls);fflush(stdout);
 // Every viewport-adjacent x endpoint pair, both axis directions and parity.
 const int ys[]={-161,-4,-1,0,1,2,29,30,31,79,80,98,99,146,149,150,152,153,154,155,158,159,160,161,320};
 const int xs[]={-241,-4,-1,0,1,2,3,6,8,12,20,26,119,120,213,214,227,228,231,232,233,234,237,238,239,240,241,480};
 for(x=-4;x<=244;x++)for(a=-4;a<=244;a++)for(k=0;k<25;k++){
  y=ys[k];m=(x+a+k+1000)%12;c=(x*11+a*7+k)&255;check(1,x,y,a,y,c,m);
 }
 for(y=-4;y<=164;y++)for(b=-4;b<=164;b++)for(k=0;k<28;k++){
  x=xs[k];m=(y+b+k+1000)%12;c=(y*11+b*7+k)&255;check(1,x,y,x,b,c,m);
 }
 printf("PASS axis lines %llu comparisons\n",lines);fflush(stdout);
 // All colors across clipping, full spans, single pixels and modal boundaries.
 const int endpoints[][4]={{-300,80,540,80},{540,80,-300,80},{120,-200,120,360},{120,360,120,-200},{0,0,239,0},{239,159,0,159},{239,0,239,159},{0,159,0,0},{-1,-1,240,160},{240,160,-1,-1},{0,159,239,0},{8,31,231,31},{8,152,231,152},{8,153,231,153},{8,31,8,152},{8,31,8,153},{7,31,8,31},{231,152,232,152},{-1,0,0,0},{239,159,240,159},{1,1,1,1},{0,0,0,0},{239,159,239,159},{240,160,240,160},{26,29,213,29},{20,38,219,151}};
 for(c=0;c<256;c++)for(m=0;m<12;m++)for(i=0;i<sizeof(endpoints)/sizeof(*endpoints);i++){
  const int*p=endpoints[i];check(1,p[0],p[1],p[2],p[3],c,m);
 }
 const int colors[]={INT_MIN,-257,-256,-1,256,257,511,INT_MAX};
 for(k=0;k<8;k++)for(m=0;m<12;m++)for(i=0;i<sizeof(endpoints)/sizeof(*endpoints);i++){const int*p=endpoints[i];check(1,p[0],p[1],p[2],p[3],colors[k],m);}
 // Non-axis lines preserve exact Bresenham pixels in every octant.
 for(i=0;i<100000;i++){
  x=(int)(random32()%1281)-520;y=(int)(random32()%1121)-480;a=(int)(random32()%1281)-520;b=(int)(random32()%1121)-480;
  check(1,x,y,a,b,(int)random32(),i%12);
 }
 printf("PASS all lines %llu comparisons\n",lines);fflush(stdout);
 const int heights[]={-4,-1,0,1,2,3,4,31,32,33,159,160,161,320};
 const int widths[]={-4,-1,0,1,2,3,4,29,30,31,32,33,34,35,63,64,239,240,241,480};
 // Horizontal and vertical clipping/parity sweep with zero/negative sizes.
 for(x=-4;x<=244;x++)for(a=-4;a<=244;a++)for(k=0;k<14;k++){
  y=ys[(x+a+k+1000)%25];b=heights[k];m=(x+a+k+1000)%12;check(0,x,y,a,b,(x*11+a*7+k)&255,m);
 }
 for(y=-4;y<=164;y++)for(b=-4;b<=164;b++)for(k=0;k<20;k++){
  x=xs[(y+b+k+1000)%28];a=widths[k];m=(y+b+k+1000)%12;check(0,x,y,a,b,(y*11+b*7+k)&255,m);
 }
 // All colors and masks with aligned/odd endpoints at DMA threshold.
 for(c=0;c<256;c++)for(m=0;m<12;m++)for(k=0;k<20;k++)for(x=0;x<4;x++){
  check(0,x,0,widths[k],3,c,m);check(0,7+x,30,widths[k],124,c,m);check(0,237+x,158,widths[k],3,c,m);
 }
 for(i=0;i<100000;i++){
  x=(int)(random32()%1281)-520;y=(int)(random32()%1121)-480;a=(int)(random32()%1101)-300;b=(int)(random32()%1101)-300;
  check(0,x,y,a,b,(int)random32(),i%12);
 }
 printf("{\"rectangles\":%llu,\"lines\":%llu,\"scrolling\":%llu,\"all_equal\":true,\"guards_unchanged\":true}\n",rectangles,lines,scrolls);return 0;
}
