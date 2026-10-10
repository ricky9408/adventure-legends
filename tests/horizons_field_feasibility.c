/* Real command renderer/overlap with authored world solids, no reward callbacks. */
#define main horizons_base_power_tests
#include "horizons_powers_host.c"
#undef main
#include "horizons_art.h"
/* This helper models only Horizons geometry, where the legacy cache API is unsupported. */
int game_collision_rects(int x0,int y0,int x1,int y1,short out[][4],unsigned cap){(void)x0;(void)y0;(void)x1;(void)y1;(void)out;(void)cap;return -1;}
int underwater_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
int return_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
/* Returns beat/target bits: bit0 first beat target0,bit1 first target1,
 * bit2 second target0,bit3 second target1. */
unsigned field_feasible(unsigned command,unsigned area,int x,int y,int direction,int x0,int y0,int x1,int y1,int release_age){
 unsigned i,a,mask=0;const HorizonsArtRoom*r;if(area<62||area>69)return 0;r=&horizons_art_rooms[area-62];setup(command);room=area;px=x;py=y;face=direction;
 for(i=0;i<r->solid_count;i++){const HorizonsArtRect*s=&r->solids[i];if(s->x+s->w<x-90||s->x>x+90||s->y+s->h<y-90||s->y>y+90)continue;wall(s->x-5,s->y-5,s->w+10,s->h+10);}
 if(x<90)wall(0,0,5,r->height);if(x>r->width-90)wall(r->width-5,0,5,r->height);if(y<90)wall(0,0,r->width,5);if(y>r->height-90)wall(0,r->height-5,r->width,5);
 if(area==63&&y<150&&x>100&&x<380)wall(180,60,25,25);
 if(!horizons_power(command))return 0;
 for(a=1;a<=lifetime[command-106];a++){tick();unsigned b=horizons_powers_beat();if(b){if(horizons_powers_overlap(x0,y0,12))mask|=1u<<((b-1)*2);if(horizons_powers_overlap(x1,y1,12))mask|=2u<<((b-1)*2);}if(release_age>0&&(int)a==release_age)horizons_powers_input(256);}
 return mask;
}
int main(int argc,char**argv){int v[10],i;if(argc!=11)return 2;for(i=0;i<10;i++)v[i]=atoi(argv[i+1]);printf("%u\n",field_feasible((unsigned)v[0],(unsigned)v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8],v[9]));return 0;}
