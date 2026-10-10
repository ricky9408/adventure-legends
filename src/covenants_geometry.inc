#include "connected_road_region.h"
/* Collision bands already expand artwork to the engine's radius-five foot.
 * An optional shortcut subtracts only its authored, visibly painted strip. */
static COLD int practice_strip(int y,int *left,int *right){
 const short *p;unsigned i=(unsigned)room-70;
 if(i>=8||!practice_ticks)return 0;
 p=covenants_practice_shortcuts[i];
 if(p[2]<=0||y<p[1]||y>=p[1]+p[3])return 0;
 *left=p[0];*right=p[0]+p[2];return 1;
}
static COLD int dynamic_rect(int *x0,int *y0,int *x1,int *y1){
 if(room==71){*x0=moving_x;*y0=104;*x1=moving_x+24;*y1=120;}
 else if(room==73){*x0=moving_x;*y0=96;*x1=moving_x+16;*y1=108;}
 else if(room==76){*x0=moving_x;*y0=48;*x1=moving_x+24;*y1=60;}
 else return 0;
 return 1;
}
static COLD int dynamic_solid(int x,int y){
 int x0,y0,x1,y1,l,h;
 if(practice_strip(y,&l,&h)&&x>=l&&x<h)return 0;
 return dynamic_rect(&x0,&y0,&x1,&y1)&&x+5>=x0&&x-5<x1&&y+5>=y0&&y-5<y1;
}
COLD int covenants_game_geometry_solid(unsigned a,int x,int y){
 const CovenantsArtRoom*r;const unsigned short*b;unsigned n,i;
 if(!covenants_game_is_room(a))return 1;
 {int seam=road_region_point(a,x,y);if(seam>=0)return seam;}
 r=&covenants_art_rooms[a-70];
 if(x<5||y<5||x>r->width-6||y>r->height-6)return 1;
 b=r->collision_bands+r->collision_rows[y];n=*b++;
 for(i=0;i<n;i++,b+=2)if(x>=b[0]&&x<b[1])return 1;
 return 0;
}
COLD int covenants_game_solid(int x,int y){
 const CovenantsArtRoom*r;int l,h;
 if(!covenants_game_is_room((unsigned)room))return 0;
 {int seam=road_region_point((unsigned)room,x,y);if(seam>=0)return seam;}
 r=&covenants_art_rooms[room-70];
 if(x<5||y<5||x>r->width-6||y>r->height-6)return 1;
 if(practice_strip(y,&l,&h)&&x>=l&&x<h)return 0;
 return covenants_game_geometry_solid((unsigned)room,x,y)||dynamic_solid(x,y);
}
static COLD int interval_span(int x,int a,int b,int *lo,int *hi){
 if(a>=b)return 1;
 if(x>=a&&x<b)return 0;
 if(b<=x){if(b>*lo)*lo=b;}else if(a-1<*hi)*hi=a-1;
 return 1;
}
static COLD unsigned free_span(int x,int y){
 const CovenantsArtRoom*r=&covenants_art_rooms[room-70];
 const unsigned short*b=r->collision_bands+r->collision_rows[y];
 unsigned n=*b++,i;int lo=5,hi=r->width-6,l=0,h=0,cut=practice_strip(y,&l,&h),x0,y0,x1,y1;
 for(i=0;i<n;i++,b+=2){
  if(cut){if(!interval_span(x,b[0],b[1]<l?b[1]:l,&lo,&hi)||!interval_span(x,b[0]>h?b[0]:h,b[1],&lo,&hi))return 0;}
  else if(!interval_span(x,b[0],b[1],&lo,&hi))return 0;
 }
 if(dynamic_rect(&x0,&y0,&x1,&y1)&&y>=y0-5&&y<y1+5){
  x0-=5;x1+=5;
  if(cut){if(!interval_span(x,x0,x1<l?x1:l,&lo,&hi)||!interval_span(x,x0>h?x0:h,x1,&lo,&hi))return 0;}
  else if(!interval_span(x,x0,x1,&lo,&hi))return 0;
 }
 return (unsigned)lo<<16|(unsigned)hi;
}
/* Generated collision bands are the radius-five union of these authored
 * rectangles, as in the exporter below. Test their intersections with the
 * query directly, subtracting the exact practice opening. This avoids
 * reconstructing identical free row spans for every power pixel. */
COLD int covenants_game_clear_box(int x0,int y0,int x1,int y1){
 const CovenantsArtRoom*r;const short*p;int pl=0,pr=0,pt=0,pb=0,l,t,h,d;unsigned i;
 if(!covenants_game_is_room((unsigned)room)||x0>x1||y0>y1)return 0;
 if(road_region_box_added((unsigned)room,x0,y0,x1,y1))return 0;
 r=&covenants_art_rooms[room-70];
 if(x0<5||y0<5||x1>r->width-6||y1>r->height-6)return 0;
 p=covenants_practice_shortcuts[(unsigned)room-70];
 if(practice_ticks&&p[2]>0){pl=p[0];pr=pl+p[2];pt=p[1];pb=pt+p[3];}
 for(i=0;i<=r->solid_count;i++){
  if(i<r->solid_count){const CovenantsArtRect*s=&r->solids[i];l=s->x;t=s->y;h=l+s->w;d=t+s->h;}
  else if(!dynamic_rect(&l,&t,&h,&d))break;
  l=l-5>x0?l-5:x0;h=h+4<x1?h+4:x1;
  t=t-5>y0?t-5:y0;d=d+4<y1?d+4:y1;
  if(l<=h&&t<=d&&(l<pl||h>=pr||t<pt||d>=pb))return 0;
 }
 return 1;
}
COLD int covenants_game_supercover(int x,int y,int tx,int ty){
 unsigned s;int dx,dy,sx,sy,e;
 if(!covenants_game_is_room((unsigned)room))return -1;
 {int seam=road_region_ray((unsigned)room,x,y,tx,ty,covenants_game_solid);if(seam>=0)return seam;}
 if((unsigned)x>1023u||(unsigned)y>1023u||(unsigned)tx>1023u||(unsigned)ty>1023u)return 0;
 dx=ab(tx-x);dy=ab(ty-y);
 if(dx+dy>160||covenants_game_solid(x,y)||covenants_game_solid(tx,ty))return 0;
 sx=x<tx?1:-1;sy=y<ty?1:-1;dy=-dy;e=dx+dy;s=free_span(x,y);if(!s)return 0;
 while(x!=tx||y!=ty){
  int twice=e*2,nx=x,ny=y;
  if(twice>=dy){e+=dy;nx+=sx;}if(twice<=dx){e+=dx;ny+=sy;}
  if(nx!=x&&((unsigned)nx<(s>>16)||(unsigned)nx>(s&65535u)))return 0;
  if(ny!=y){s=free_span(x,ny);if(!s||(unsigned)nx<(s>>16)||(unsigned)nx>(s&65535u))return 0;}
  x=nx;y=ny;
 }
 return 1;
}
COLD void covenants_game_collision_inputs(unsigned out[3]){
 if(out){out[0]=geometry;out[1]=(unsigned)(unsigned short)moving_x;out[2]=practice_ticks!=0;}
}
/* Exact rectangle export for the same point predicate. Consumers own storage;
 * overflow/invalid input grants no certificate and partial output is discarded. */
typedef struct {int x0,y0,x1,y1;short(*out)[4];unsigned count,cap;} CovenantRectBuild;
static COLD int export_rect(CovenantRectBuild*b,int l,int t,int r,int d){
 short*p;
 if(l<b->x0)l=b->x0;
 if(t<b->y0)t=b->y0;
 if(r>b->x1)r=b->x1;
 if(d>b->y1)d=b->y1;
 if(l>r||t>d)return 1;
 if(b->count==b->cap)return 0;
 p=b->out[b->count++];p[0]=(short)l;p[1]=(short)t;p[2]=(short)r;p[3]=(short)d;return 1;
}
static COLD int export_occupied(CovenantRectBuild*b,int l,int t,int r,int d){
 const short*p=covenants_practice_shortcuts[(unsigned)room-70];int pl,pt,pr,pb,mt,md;
 if(!practice_ticks||p[2]<=0)return export_rect(b,l,t,r,d);
 pl=p[0];pt=p[1];pr=p[0]+p[2]-1;pb=p[1]+p[3]-1;
 if(r<pl||l>pr||d<pt||t>pb)return export_rect(b,l,t,r,d);
 mt=t>pt?t:pt;md=d<pb?d:pb;
 return export_rect(b,l,t,r,pt-1)&&export_rect(b,l,pb+1,r,d)&&
        export_rect(b,l,mt,pl-1,md)&&export_rect(b,pr+1,mt,r,md);
}
COLD int covenants_game_collision_rects(int x0,int y0,int x1,int y1,short out[][4],unsigned cap){
 CovenantRectBuild b;const CovenantsArtRoom*r;unsigned i;int l,t,h,d;
 if(!covenants_game_is_room((unsigned)room)||!out||!cap||cap>256||x0<-32768||y0<-32768||x1>32767||y1>32767||x0>x1||y0>y1)return -1;
 if(road_region_box((unsigned)room,x0,y0,x1,y1))return -1;
 b.x0=x0;b.y0=y0;b.x1=x1;b.y1=y1;b.out=out;b.cap=cap;b.count=0;r=&covenants_art_rooms[room-70];
 if(!export_rect(&b,x0,y0,4,y1)||!export_rect(&b,r->width-5,y0,x1,y1)||
    !export_rect(&b,x0,y0,x1,4)||!export_rect(&b,x0,r->height-5,x1,y1))return -1;
 for(i=0;i<r->solid_count;i++){
  const CovenantsArtRect*s=&r->solids[i];
  if(!export_occupied(&b,s->x-5,s->y-5,s->x+s->w+4,s->y+s->h+4))return -1;
 }
 if(dynamic_rect(&l,&t,&h,&d)&&!export_occupied(&b,l-5,t-5,h+4,d+4))return -1;
 return (int)b.count;
}
