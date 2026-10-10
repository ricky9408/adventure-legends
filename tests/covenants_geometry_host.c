/* Calls the exact extracted production geometry, never a replacement exporter. */
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include "covenants_geometry_extract.inc"
#define MW 501
#define MH 341
static unsigned char raster[MH][MW];
static unsigned long pixels, queries, clipped_queries;
static unsigned whole_max[8], cast_max[8], states[8];
static unsigned rng=0x43ba7812u;
static unsigned random_word(void){rng=rng*1664525u+1013904223u;return rng;}
static void rasterize(short walls[][4],int n,int x0,int y0,int x1,int y1){
 int i,x,y;assert(x1-x0<MW&&y1-y0<MH);memset(raster,0,sizeof raster);
 for(i=0;i<n;i++){
  assert(walls[i][0]>=x0&&walls[i][1]>=y0&&walls[i][2]<=x1&&walls[i][3]<=y1);
  assert(walls[i][0]<=walls[i][2]&&walls[i][1]<=walls[i][3]);
  for(y=walls[i][1];y<=walls[i][3];y++)for(x=walls[i][0];x<=walls[i][2];x++)raster[y-y0][x-x0]=1;
 }
 for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++){
  int got=raster[y-y0][x-x0],want=covenants_game_solid(x,y);pixels++;
  if(got!=want){fprintf(stderr,"union mismatch room=%d moving=%d practice=%u xy=%d,%d got=%d want=%d\n",room,moving_x,practice_ticks,x,y,got,want);assert(got==want);}
 }
}
static void controls(int count){
 struct {short before[4];short walls[256][4];short after[4];} guard;
 unsigned cap,i;int n;
 for(cap=1;cap<=(unsigned)count+1;cap++){
  memset(&guard,0x5a,sizeof guard);
  n=covenants_game_collision_rects(-8,-8,488,328,guard.walls,cap);
  assert(n==(cap<(unsigned)count?-1:count));
  for(i=0;i<4;i++)assert(guard.before[i]==0x5a5a&&guard.after[i]==0x5a5a);
  for(i=cap;i<256;i++)for(unsigned k=0;k<4;k++)assert(guard.walls[i][k]==0x5a5a);
 }
 assert(covenants_game_collision_rects(0,0,20,20,guard.walls,0)==-1);
 assert(covenants_game_collision_rects(0,0,20,20,guard.walls,257)==-1);
 assert(covenants_game_collision_rects(0,0,20,20,0,48)==-1);
 assert(covenants_game_collision_rects(1,0,0,20,guard.walls,48)==-1);
 assert(covenants_game_collision_rects(0,1,20,0,guard.walls,48)==-1);
 assert(covenants_game_collision_rects(INT_MIN,0,20,20,guard.walls,48)==-1);
 assert(covenants_game_collision_rects(0,INT_MIN,20,20,guard.walls,48)==-1);
 assert(covenants_game_collision_rects(0,0,INT_MAX,20,guard.walls,48)==-1);
 assert(covenants_game_collision_rects(0,0,20,INT_MAX,guard.walls,48)==-1);
 n=covenants_game_collision_rects(-32768,-32768,32767,32767,guard.walls,256);
 assert(n==count);
 for(i=0;i<4;i++){
  int x=i&1?32767:-32768,y=i&2?32767:-32768;
  n=covenants_game_collision_rects(x,y,x,y,guard.walls,48);assert(n>0);rasterize(guard.walls,n,x,y,x,y);
 }
}
int main(void){
 short walls[256][4];unsigned a,practice;int mx,lo,hi,x,y,n;
 for(a=70;a<78;a++){
  const CovenantsArtRoom*r=&covenants_art_rooms[a-70];room=(int)a;
  lo=a==76?224:88;hi=a==71?152:a==73?136:a==76?272:lo;
  for(mx=lo;mx<=hi;mx++)for(practice=0;practice<2;practice++){
   moving_x=(short)mx;practice_ticks=(unsigned short)practice;states[a-70]++;
   n=covenants_game_collision_rects(-8,-8,r->width+8,r->height+8,walls,256);assert(n>=0&&n<=16);
   if((unsigned)n>whole_max[a-70])whole_max[a-70]=(unsigned)n;
   rasterize(walls,n,-8,-8,r->width+8,r->height+8);
   /* Full signed-short bounds cover the same complete rectangle set. */
   controls(n);
   for(y=0;y<r->height;y++)for(x=0;x<r->width;x++){
    n=covenants_game_collision_rects(x>64?x-64:0,y>64?y-64:0,x+64,y+64,walls,48);queries++;
    assert(n>=0&&n<=48);if((unsigned)n>cast_max[a-70])cast_max[a-70]=(unsigned)n;
   }
   /* Query clipping independently samples every state, including negative queries. */
   for(unsigned k=0;k<32;k++){
    int x0=(int)(random_word()%(r->width+40))-20,y0=(int)(random_word()%(r->height+40))-20;
    int x1=x0+(int)(random_word()%130),y1=y0+(int)(random_word()%130);
    n=covenants_game_collision_rects(x0,y0,x1,y1,walls,256);assert(n>=0);clipped_queries++;
    rasterize(walls,n,x0,y0,x1,y1);
   }
  }
 }
 room=69;assert(covenants_game_collision_rects(0,0,0,0,walls,256)==-1);
 room=78;assert(covenants_game_collision_rects(0,0,0,0,walls,256)==-1);
 printf("{\"occupied_union_pixel_comparisons\":%lu,\"cast_queries\":%lu,\"clipped_query_comparisons\":%lu,\"rooms\":[",pixels,queries,clipped_queries);
 for(a=0;a<8;a++)printf("%s{\"room\":%u,\"states\":%u,\"whole_room_max_rectangles\":%u,\"cast_max_rectangles\":%u}",a?",":"",a+70,states[a],whole_max[a],cast_max[a]);
 puts("]}");return 0;
}
