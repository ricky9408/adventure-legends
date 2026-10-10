/* Exact row-band supercover tests only; not controller gameplay evidence. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#ifndef POWER_SOURCE
#define POWER_SOURCE "../src/horizons_powers.c"
#endif
#include POWER_SOURCE
volatile int room;
static unsigned state=812459u,checks;
static unsigned rng(void){state=state*1664525u+1013904223u;return state;}
#ifndef REAL_ART
static unsigned short test_rows[256],test_bands[256*3];
const NorthArtRoom north_art_rooms[8]={{256,256,0,0,0,0,test_rows,test_bands}};
const SouthArtRoom south_art_rooms[8]={{256,256,0,0,0,0,test_rows,test_bands}};
#endif
static int oracle_solid(int x,int y){const unsigned short *rows,*b;unsigned w,h,n;
 if(room<30){const NorthArtRoom*r=north_art_rooms+room-22;w=r->width;h=r->height;rows=r->collision_rows;b=r->collision_bands;}
 else{const SouthArtRoom*r=south_art_rooms+room-30;w=r->width;h=r->height;rows=r->collision_rows;b=r->collision_bands;}
 if((unsigned)x>=w||(unsigned)y>=h)return 1;
 b+=rows[y];n=*b++;while(n--){if((unsigned)x>=b[0]&&(unsigned)x<b[1])return 1;b+=2;}return 0;
}
static int original(int x,int y,int tx,int ty){int ax,ay,sx,sy,e;
 if(oracle_solid(x,y)||oracle_solid(tx,ty))return 0;
 ax=ab(tx-x);ay=-ab(ty-y);sx=x<tx?1:-1;sy=y<ty?1:-1;e=ax+ay;
 while(x!=tx||y!=ty){int q=e*2,nx=x,ny=y;
  if(q>=ay){e+=ay;nx+=sx;}if(q<=ax){e+=ax;ny+=sy;}
  if(nx!=x&&ny!=y&&(oracle_solid(nx,y)||oracle_solid(x,ny)))return 0;
  x=nx;y=ny;if(oracle_solid(x,y))return 0;
 }return 1;
}
static void compare(int x,int y,int tx,int ty){int a=original(x,y,tx,ty),b=old_rows_clear(x,y,tx,ty);assert(a==b);checks++;}
int main(void){int x,y,dx,dy;
#ifndef REAL_ART
 for(y=0;y<256;y++)test_rows[y]=(unsigned short)(y*3);
 for(room=22;room<=30;room+=8)for(dy=-20;dy<=20;dy++)for(dx=-20;dx<=20;dx++){
  compare(64,64,64+dx,64+dy);
  for(y=42;y<=86;y++)for(x=42;x<=86;x++){test_bands[y*3]=1;test_bands[y*3+1]=(unsigned short)x;test_bands[y*3+2]=(unsigned short)(x+1);compare(64,64,64+dx,64+dy);test_bands[y*3]=0;}
 }
#else
 for(room=22;room<38;room++){
  unsigned i,w=room<30?north_art_rooms[room-22].width:south_art_rooms[room-30].width,h=room<30?north_art_rooms[room-22].height:south_art_rooms[room-30].height;
  for(y=-1;y<=(int)h;y++)for(x=-1;x<=(int)w;x++){
   compare(x,y,x,y);
   for(dy=-1;dy<=1;dy++)for(dx=-1;dx<=1;dx++)compare(x,y,x+dx,y+dy);
  }
  for(i=0;i<60000;i++){x=(int)(rng()%(w+16))-8;y=(int)(rng()%(h+16))-8;dx=(int)(rng()%129)-64;dy=(int)(rng()%129)-64;compare(x,y,x+dx,y+dy);}
 }
#endif
 printf("%u original supercover equivalence checks passed\n",checks);return 0;
}
