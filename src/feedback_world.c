#include "feedback_world.h"
/* Sparse original art is baked once. Runtime copies only opaque visible runs;
 * no scene construction, heap, resident OBJ tiles or full-screen RAM cache. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct {u16 x,y,count,reserved;u32 pixels[2];} FeedbackRun;
typedef struct {u16 first,count,x,y,width,height;} FeedbackRoom;
#include "feedback_world_data.inc"
extern u16 *screen;
extern int world_mask_active,game_world_rect_hidden(int,int,int,int);
void feedback_world_draw(unsigned room,int camera_x,int camera_y){
 unsigned i,end,first;const FeedbackRoom*scene;
 if(room>=78)return;
 scene=&feedback_rooms[room];if(!scene->count)return;
 {int l=(int)scene->x-camera_x,t=(int)scene->y-camera_y,r=l+scene->width,b=t+scene->height;
  if(l<0)l=0;
  if(t<0)t=0;
  if(r>240)r=240;
  if(b>160)b=160;
  if(l>=r||t>=b)return;
  /* A conservative visible bounding box can reject an entire covered town
   * construction before any individual row/table access. */
  if(world_mask_active&&game_world_rect_hidden(l,t,r-l,b-t))return;
 }
 end=scene->first+scene->count;first=scene->first;
 /* Generated runs are sorted by row. Skip the invisible prefix before any
  * pixel pointers/DMA work and stop at the first row below the viewport. */
 if(camera_y>0){unsigned lo=first,hi=end;
  while(lo<hi){unsigned mid=lo+(hi-lo)/2;if((int)feedback_runs[mid].y<camera_y)lo=mid+1;else hi=mid;}
  first=lo;
 }
 for(i=first;i<end;i++){
  if((int)feedback_runs[i].y-camera_y>=160)break;
  const FeedbackRun*r=&feedback_runs[i];const u8*src;u16*dst;
  int x=(int)r->x-camera_x,y=(int)r->y-camera_y,n=r->count,skip=0;unsigned pairs;
  if((unsigned)y>=160||x>=240||x+n<=0)continue;
  if(x<0){skip=-x;n+=x;x=0;}if(x+n>240)n=240-x;
  if(world_mask_active&&game_world_rect_hidden(x,y,n,1))continue;
  src=feedback_pixels+r->pixels[(x&1)^(skip&1)]+skip;dst=screen+y*120+(x>>1);
  if(x&1){*dst=(u16)((*dst&255)|((unsigned)*src++<<8));dst++;n--;}
  pairs=(unsigned)n>>1;
#if defined(__arm__) && !defined(GAME_HOST_TEST)
  if(pairs>=4){
   *(volatile u32*)0x040000D4=(u32)src;*(volatile u32*)0x040000D8=(u32)dst;
   *(volatile u32*)0x040000DC=0x80000000u|pairs;
   src+=pairs*2;dst+=pairs;
  }else
#endif
  {unsigned j;for(j=0;j<pairs;j++){*dst++=*(const u16*)src;src+=2;}}
  if(n&1)*dst=(u16)((*dst&65280)|*src);
 }
}
