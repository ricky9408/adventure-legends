/* Exact rectangle/raster oracle; synthetic geometry, not controller evidence. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#ifndef POWER_SOURCE
#define POWER_SOURCE "../src/horizons_powers.c"
#endif
#include POWER_SOURCE
volatile int room;
static unsigned state=7193527u,checks;
static unsigned rng(void){state=state*1664525u+1013904223u;return state;}
static int oracle_solid(int x,int y){unsigned i;for(i=0;i<collision.count;i++){const short*r=collision.walls[i];if(x>=r[0]&&x<=r[2]&&y>=r[1]&&y<=r[3])return 1;}return 0;}
static int original(int x,int y,int tx,int ty){int ax=ab(tx-x),ay=-ab(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,e=ax+ay;
 if(oracle_solid(x,y)||oracle_solid(tx,ty))return 0;
 while(x!=tx||y!=ty){int q=e*2,nx=x,ny=y;if(q>=ay){e+=ay;nx+=sx;}if(q<=ax){e+=ax;ny+=sy;}if(nx!=x&&ny!=y&&(oracle_solid(nx,y)||oracle_solid(x,ny)))return 0;x=nx;y=ny;if(oracle_solid(x,y))return 0;}return 1;
}
static void compare(int x,int y,int tx,int ty){assert(original(x,y,tx,ty)==rectangle_ray(x,y,tx,ty));checks++;}
int main(void){int x,y,dx,dy;unsigned i,j;
 collision.count=1;
 for(dy=-20;dy<=20;dy++)for(dx=-20;dx<=20;dx++)for(y=42;y<=86;y++)for(x=42;x<=86;x++){
  collision.walls[0][0]=collision.walls[0][2]=(short)x;collision.walls[0][1]=collision.walls[0][3]=(short)y;compare(64,64,64+dx,64+dy);
 }
 for(i=0;i<100;i++){
  collision.count=(unsigned char)(1+rng()%48);
  for(j=0;j<collision.count;j++){short*r=collision.walls[j];r[0]=(short)(rng()%256);r[1]=(short)(rng()%256);r[2]=(short)(r[0]+rng()%65);r[3]=(short)(r[1]+rng()%65);}
  for(j=0;j<12000;j++){x=(int)(rng()%256);y=(int)(rng()%256);dx=(int)(rng()%257)-128;dy=(int)(rng()%257)-128;compare(x,y,x+dx,y+dy);}
 }
 printf("%u exact rectangle/supercover comparisons passed\n",checks);return 0;
}
