/* Retained pre-feedback optical semantics: pixel-step ray traversal against
 * authored SouthArtRoom solids, before finite ROM table optimization. */
#include "south_game.h"
#include "south_art.h"
static int puzzle_valid(const SouthPuzzle*p,unsigned a){return p&&a>=34&&a<=36&&p->mirror[0]<2&&p->mirror[1]<2&&p->shade<2;
}
static int optical_wall(unsigned area,int x,int y){const SouthArtRoom*r=&south_art_rooms[area-30];
unsigned i;
if((unsigned)x>=r->width||(unsigned)y>=r->height)return 1;
for(i=0;i<r->solid_count;i++){const SouthArtRect*b=&r->solids[i];
if(x>=b->x&&x<b->x+b->w&&y>=b->y&&y<b->y+b->h)return 1;
}return 0;
}
unsigned reference_south_puzzle_beam(const SouthPuzzle*p,unsigned a,SouthBeam out[4]){static const int dx[4]={1,0,-1,0},dy[4]={0,1,0,-1};
int mx[2],my[2],rx,ry,x,y,d=0,nx,ny,k,kind,hit;
unsigned n=0,seen=0,bit;
if(!out||!puzzle_valid(p,a))return 0;
mx[0]=a==36?80:112;
my[0]=a==36?104:56;
mx[1]=a==36?80:112;
my[1]=a==36?48:104;
rx=a==34?112:192;
ry=a==36?48:104;
x=32;
y=a==36?104:56;
while(n<4){nx=x;
ny=y;
hit=-1;
kind=SOUTH_BEAM_WALL;
for(k=0;k<240;k++){nx+=dx[d];
ny+=dy[d];
if(optical_wall(a,nx,ny))break;
if(a!=34&&nx==152&&ny==(p->shade?(a==35?104:48):(a==35?56:104))){kind=SOUTH_BEAM_SHADE;
break;
}
if(nx==rx&&ny==ry){kind=SOUTH_BEAM_RECEIVER;
break;
}
if(nx==mx[0]&&ny==my[0]){hit=0;
kind=SOUTH_BEAM_MIRROR;
break;
}
if(a!=34&&nx==mx[1]&&ny==my[1]){hit=1;
kind=SOUTH_BEAM_MIRROR;
break;
}
}
out[n].x1=(short)x;
out[n].y1=(short)y;
out[n].x2=(short)nx;
out[n].y2=(short)ny;
out[n].end_kind=(unsigned char)kind;
n++;
if(hit<0){break;
}bit=1u<<((unsigned)hit*4+(unsigned)d);
if(seen&bit){out[n-1].end_kind=SOUTH_BEAM_LOOP;
break;
}seen|=bit;
d=p->mirror[hit]?(d^1):3-d;
x=nx;
y=ny;
}return n;
}
