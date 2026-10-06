/* Production collision and swept prop moves, exhaustive pixel-space proof.
 * No abstract lattice occupancy substitutes for actual radius-five geometry. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "magma_art.h"
#include "magma_game.h"
int magma_game_is_room(unsigned a){return a>=38&&a<=45;}
#include "magma_puzzle.inc"
#define W 240
#define H 160
#define N (35*35)
static unsigned char seen[W*H],edges[N][N],valid[N],reachable[N],solvable[N];
static int queue[W*H],todo[N],qx[N],qy[N];
static int flood(MagmaPuzzle*p,unsigned area,int sx,int sy){int head=0,tail=0,i,v,x,y;static const int dx[4]={1,-1,0,0},dy[4]={0,0,1,-1};memset(seen,0,sizeof seen);if(magma_puzzle_solid(p,area,sx,sy))return 0;seen[sy*W+sx]=1;queue[tail++]=sy*W+sx;while(head<tail){v=queue[head++];x=v%W;y=v/W;for(i=0;i<4;i++){int nx=x+dx[i],ny=y+dy[i],j=ny*W+nx;if(nx>=0&&nx<W&&ny>=0&&ny<H&&!seen[j]&&!magma_puzzle_solid(p,area,nx,ny)){seen[j]=1;queue[tail++]=j;}}}return tail;}
static int checked(unsigned a){MagmaPuzzle p,q;unsigned count=magma_puzzle_count(a),i,j,d;int s,v,n,head,tail,cases=0,links=0,x,y,px,py,nx,ny,tx,ty,ox,oy,goal;
 memset(valid,0,sizeof valid);memset(edges,0,sizeof edges);memset(reachable,0,sizeof reachable);memset(solvable,0,sizeof solvable);
 for(i=0;i<35;i++)for(j=0;j<(count==2?35u:1u);j++){
  p=(MagmaPuzzle){{(unsigned char)i,(unsigned char)j},0,0};magma_puzzle_position(&p,a,0,&x,&y);if(raw_prop_wall(a,x,y))continue;if(count==2){magma_puzzle_position(&p,a,1,&ox,&oy);if(raw_prop_wall(a,ox,oy)||(ab(x-ox)<12&&ab(y-oy)<12))continue;}s=i*35+j;valid[s]=1;cases++;flood(&p,a,120,136);
  if(!seen[148*W+120]||!seen[120*W+24]||!seen[128*W+216]){fprintf(stderr,"Boundary lost:%u/%d\n",a,s);return 0;}
  for(v=0;v<(int)count;v++){magma_puzzle_position(&p,a,(unsigned)v,&x,&y);for(py=y-24;py<=y+24;py++)for(px=x-24;px<=x+24;px++){if(px<0||py<0||px>=W||py>=H||ab(px-x)+ab(py-y)>24||!seen[py*W+px])continue;for(d=0;d<4;d++){q=p;if(magma_puzzle_move(&q,a,(unsigned)v,d,px,py,&nx,&ny)!=1)continue;n=q.cell[0]*35+(count==2?q.cell[1]:0);edges[s][n]=1;/* A simultaneous pull must retain its final clear footprint. */if(magma_puzzle_solid(&q,a,nx,ny)){fprintf(stderr,"Invalid endpoint\n");return 0;}qx[n]=nx;qy[n]=ny;}}}
 }
 magma_puzzle_reset(&p,a);s=p.cell[0]*35+(count==2?p.cell[1]:0);if(!valid[s]){fprintf(stderr,"Invalid reset%u\n",a);return 0;}reachable[s]=1;todo[0]=s;tail=1;head=0;
 while(head<tail){s=todo[head++];for(n=0;n<N;n++)if(edges[s][n]&&!reachable[n]){reachable[n]=1;todo[tail++]=n;}}
 /* For every actually reachable spatial arrangement, every free player pixel
  * must retain the walking-only exit. This is stronger than source-cell BFS. */
 for(s=0;s<N;s++)if(reachable[s]){p=(MagmaPuzzle){{(unsigned char)(s/35),(unsigned char)(s%35)},0,0};flood(&p,a,120,136);for(y=5;y<155;y++)for(x=5;x<235;x++)if(!magma_puzzle_solid(&p,a,x,y)&&!seen[y*W+x]){fprintf(stderr,"Stranded pixel:%u state%d px%d,%d\n",a,s,x,y);return 0;}for(n=0;n<N;n++)if(edges[s][n])links++;}
 goal=(a==40?23:a==42?20:a==43?4:20)*35+(a==43?18:a==44?4:0);if(!valid[goal]){fprintf(stderr,"Invalid goal%u\n",a);return 0;}
 solvable[goal]=1;todo[0]=goal;tail=1;head=0;while(head<tail){n=todo[head++];for(s=0;s<N;s++)if(edges[s][n]&&!solvable[s]){solvable[s]=1;todo[tail++]=s;}}
 for(s=0;s<N;s++)if(reachable[s]&&!solvable[s]){fprintf(stderr,"Cannot solve:%u/%d\n",a,s);return 0;}
 /* Every input/source, brace, receiver, forward-door approach is reachable
  * in goal geometry; charge source approach is reachable in reset geometry. */
 p=(MagmaPuzzle){{(unsigned char)(goal/35),(unsigned char)(goal%35)},1,1};flood(&p,a,120,136);tx=216;ty=72;if(!seen[ty*W+tx]||!seen[120*W+168]||!seen[104*W+208])return 0;
 magma_puzzle_reset(&p,a);flood(&p,a,120,136);if(!seen[68*W+32])return 0;
 printf("room%u: %d legal arrangements, %d actual swept transitions, all reachable pixels exit and all arrangements solve\n",a,cases,links);return 1;
}
int main(void){return checked(40)&&checked(42)&&checked(43)&&checked(44)?0:1;}
