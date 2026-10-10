/* Synthetic geometry acceptance using the REAL support renderer and catalog.
 * This checks visible 7x7 target pixels at authored native origins/facings,
 * not gameplay rewards, controller input, native cadence or acquisition. */
#define main support_suite_main
#define solid inherited_host_solid
#define game_clear_box inherited_host_clear_box
#define return_game_supercover inherited_return_supercover
#define horizons_game_supercover inherited_horizons_supercover
#ifdef TEST_RETURN_SUPPORT
#include "return_powers_host.c"
#else
#include "horizons_powers_host.c"
#endif
#undef main
#undef solid
#undef game_clear_box
#undef return_game_supercover
#undef horizons_game_supercover
#include "covenants_art.h"
static const CovenantsArtRoom *art;
int solid(int x,int y){unsigned i;const unsigned short*b;if(x<0||y<0||x>=art->width||y>=art->height)return 1;b=art->collision_bands+art->collision_rows[y];for(i=0;i<b[0];i++)if(x>=b[1+i*2]&&x<b[2+i*2])return 1;return 0;}
int game_clear_box(int x0,int y0,int x1,int y1){int x,y;for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++)if(solid(x,y))return 0;return x0<=x1&&y0<=y1;}
int game_collision_rects(int x0,int y0,int x1,int y1,short out[][4],unsigned cap){unsigned i,n=0;for(i=0;i<(unsigned)art->solid_count+4u;i++){int l,t,r,b;if(i<art->solid_count){const CovenantsArtRect*s=&art->solids[i];l=s->x-5;t=s->y-5;r=s->x+s->w+4;b=s->y+s->h+4;}else{l=i==(unsigned)art->solid_count+1u?art->width-5:0;r=i==art->solid_count?4:art->width-1;t=i==(unsigned)art->solid_count+3u?art->height-5:0;b=i==(unsigned)art->solid_count+2u?4:art->height-1;}if(r<x0||l>x1||b<y0||t>y1)continue;if(n>=cap)return -1;out[n][0]=l;out[n][1]=t;out[n][2]=r;out[n++][3]=b;}return (int)n;}
int horizons_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
int return_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
int underwater_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
int return_game_clear_box(int x0,int y0,int x1,int y1){return game_clear_box(x0,y0,x1,y1);}
/* Current world bridge stubs issue a local token but NEVER grant rewards. */
int covenants_game_is_room(unsigned a){return a-70u<8u;}
int covenants_game_clear_box(int x0,int y0,int x1,int y1){return game_clear_box(x0,y0,x1,y1);}
int covenants_game_supercover(int x,int y,int tx,int ty){int dx=abs(tx-x),dy=-abs(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,e=dx+dy;if(solid(x,y)||solid(tx,ty))return 0;while(x!=tx||y!=ty){int q=e*2,nx=x,ny=y;if(q>=dy){e+=dy;nx+=sx;}if(q<=dx){e+=dx;ny+=sy;}if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return 0;x=nx;y=ny;if(solid(x,y))return 0;}return 1;}
unsigned covenants_game_action_begin(unsigned c){assert(c==3);return ++token;}
int covenants_game_field_target(unsigned i,int*x,int*y,int*r){(void)i;(void)x;(void)y;(void)r;return 0;}
int covenants_game_field_hit(unsigned i,unsigned c,unsigned id,unsigned f,unsigned t){(void)i;(void)c;(void)id;(void)f;(void)t;assert(0);return 0;}
void covenants_game_revoke_cast(unsigned t){(void)t;}
#ifndef TEST_RETURN_SUPPORT
unsigned return_game_action_begin(unsigned c){return horizons_game_action_begin(c);}
int return_game_field_target(unsigned i,int*x,int*y,int*r){return horizons_game_field_target(i,x,y,r);}
int return_game_field_hit(unsigned i,unsigned c,unsigned id,unsigned f,unsigned t){return horizons_game_field_hit(i,c,id,f,t);}
#endif
static unsigned visible_at(int tx,int ty){unsigned i;int x,y;for(i=0;i<draws;i++)for(y=0;y<draw_w[i];y++)for(x=0;x<draw_w[i];x++){int xx=draw_x[i]+x-tx,yy=draw_y[i]+y-ty;if(abs(xx)<=3&&abs(yy)<=3&&abs(xx)+abs(yy)<=3+3&&vram[draw_off[i]+y*draw_w[i]+x])return 1;}return 0;}
int main(int argc,char**argv){int v[10],i;unsigned age,mask=0,count=0;if(argc!=11)return 2;for(i=0;i<10;i++)v[i]=atoi(argv[i+1]);if(v[1]<70||v[1]>77)return 3;art=&covenants_art_rooms[v[1]-70];setup((unsigned)v[0]);room=v[1];px=v[2];py=v[3];face=v[4];assert(!solid(px,py));
#ifdef TEST_RETURN_SUPPORT
 assert(return_power((unsigned)v[0]));
 for(age=1;age<=lifetime[v[0]-91];age++){tick();if(return_powers_overlap(v[5],v[6],3)){assert(visible_at(v[5],v[6]));mask|=1;count++;printf("%u,",age);}}
#else
 assert(horizons_power((unsigned)v[0]));
 for(age=1;age<=lifetime[v[0]-106];age++){unsigned beat;tick();beat=horizons_powers_beat();if(beat){if(horizons_powers_overlap(v[5],v[6],3)){assert(visible_at(v[5],v[6]));mask|=1u<<((beat-1)*2);count++;printf("%u:%u:0,",age,beat);}if(v[0]==108&&horizons_powers_overlap(v[7],v[8],3)){assert(visible_at(v[7],v[8]));mask|=2u<<((beat-1)*2);count++;printf("%u:%u:1,",age,beat);}}if((int)age==v[9])assert(horizons_powers_input(256)==2);}
#endif
 printf(" %u %u\n",mask,count);return 0;}
