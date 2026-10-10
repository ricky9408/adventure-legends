/* Production pure spatial model, shared unchanged by the focused host proof. */
static int ab(int n){return n<0?-n:n;}
int magma_game_geometry_solid(unsigned area,int x,int y){const MagmaArtRoom*r;const unsigned short*b;unsigned n;
 if(!magma_game_is_room(area))return 0;
r=&magma_art_rooms[area-38];
 if((unsigned)x>=r->width||(unsigned)y>=r->height)return 1;
 b=r->collision_bands+r->collision_rows[y];n=*b++;
 while(n--){if(x<b[0])return 0;if(x<b[1])return 1;b+=2;}return 0;
}
unsigned magma_puzzle_count(unsigned a){return a==40||a==42?1:(a==43||a==44)?2:0;}
void magma_puzzle_reset(MagmaPuzzle*p,unsigned a){if(!p)return;p->cell[0]=(unsigned char)(a==40?21:a==43?23:14);p->cell[1]=26;p->heat=p->brace=0;}
int magma_puzzle_position(const MagmaPuzzle*p,unsigned a,unsigned i,int*x,int*y){if(!p||i>=magma_puzzle_count(a)||p->cell[i]>=35)return 0;if(x)*x=48+(p->cell[i]%7)*24;if(y)*y=32+(p->cell[i]/7)*18;return 1;}
static int prop_hit(int x,int y,int ox,int oy){return x>=ox-11&&x<ox+11&&y>=oy-11&&y<oy+11;}
int magma_puzzle_solid(const MagmaPuzzle*p,unsigned a,int x,int y){unsigned i;int ox,oy;if(magma_game_geometry_solid(a,x,y))return 1;for(i=0;i<magma_puzzle_count(a);i++)if(magma_puzzle_position(p,a,i,&ox,&oy)&&prop_hit(x,y,ox,oy))return 1;return 0;}
static int raw_prop_wall(unsigned a,int x,int y){return magma_game_geometry_solid(a,x-1,y-1)||magma_game_geometry_solid(a,x+1,y-1)||magma_game_geometry_solid(a,x-1,y+1)||magma_game_geometry_solid(a,x+1,y+1);}
int magma_puzzle_move(MagmaPuzzle*p,unsigned a,unsigned prop,unsigned d,int px0,int py0,int*outx,int*outy){
 static const signed char dc[4]={0,0,-1,1},dr[4]={1,-1,0,0};
 int x,y,nx,ny,c,r,i,n,xx,yy,tx,ty,movep=0,pdx=0,pdy=0,ox,oy;unsigned j;
 if(!p||d>3||!magma_puzzle_position(p,a,prop,&x,&y))return -1;
 if(ab(px0-x)+ab(py0-y)>24||magma_puzzle_solid(p,a,px0,py0))return 0;
 c=p->cell[prop]%7+dc[d];r=p->cell[prop]/7+dr[d];if(c<0||c>=7||r<0||r>=5)return 0;
 nx=48+c*24;ny=32+r*18;n=dc[d]?24:18;
 /* A grab keeps its relative offset throughout the slide. This supports
  * pushing, pulling away from walls and side-sliding without releasing. */
 movep=1;pdx=nx-x;pdy=ny-y;
 for(i=1;i<=n;i++){
  xx=x+(nx-x)*i/n;yy=y+(ny-y)*i/n;
  if(raw_prop_wall(a,xx,yy))return 0;
  tx=px0+pdx*i/n;ty=py0+pdy*i/n;
  if(magma_game_geometry_solid(a,tx,ty)||prop_hit(tx,ty,xx,yy))return 0;
  for(j=0;j<magma_puzzle_count(a);j++)if(j!=prop&&magma_puzzle_position(p,a,j,&ox,&oy)){
   if(ab(xx-ox)<12&&ab(yy-oy)<12)return 0;
if(prop_hit(tx,ty,ox,oy))return 0;
  }
 }
 p->cell[prop]=(unsigned char)(r*7+c);p->brace=0;
 if(outx)*outx=px0+(movep?pdx:0);
if(outy)*outy=py0+(movep?pdy:0);
return 1;
}
int magma_puzzle_charge(MagmaPuzzle*p,unsigned a){if(!p||(a!=40&&a!=42&&a!=44)||p->cell[0]!=(a==40?21:14))return 0;p->heat=1;return 1;}
int magma_puzzle_brace(MagmaPuzzle*p,unsigned a){if(!p)return 0;if(a==43&&p->cell[0]==4&&p->cell[1]==18){p->brace=1;return 1;}if(a==44&&p->cell[0]==20&&p->cell[1]==4&&p->heat){p->brace=1;return 1;}return 0;}
int magma_puzzle_solved(const MagmaPuzzle*p,unsigned a){if(!p)return 0;return a==42?p->cell[0]==20&&p->heat:a==43?p->cell[0]==4&&p->cell[1]==18&&p->brace:a==44?p->cell[0]==20&&p->cell[1]==4&&p->heat&&p->brace:0;}
