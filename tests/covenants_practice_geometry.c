/* Real legendary renderer + exact generated room collision. Synthetic casting
 * does not establish controller reachability, progression or native cadence. */
#define main inherited_component_suite
#define solid inherited_solid
#define game_clear_box inherited_clear_box
#define game_collision_rects inherited_collision_rects
#define covenants_game_supercover inherited_covenants_supercover
#include "covenants_powers_host.c"
#undef main
#undef solid
#undef game_clear_box
#undef game_collision_rects
#undef covenants_game_supercover
#include "covenants_art.h"
static const CovenantsArtRoom *art;
int solid(int x,int y) {
    unsigned i;const unsigned short *b;
    if(x<0||y<0||x>=art->width||y>=art->height)return 1;
    b=art->collision_bands+art->collision_rows[y];
    for(i=0;i<b[0];i++)if(x>=b[1+i*2]&&x<b[2+i*2])return 1;
    return 0;
}
int game_clear_box(int x0,int y0,int x1,int y1) {
    int y;unsigned i,offset;const unsigned short *b;
    if(x0<0||y0<0||x1>=art->width||y1>=art->height||x0>x1||y0>y1)return 0;
    y=y0;
    while(y<=y1) {
        offset=art->collision_rows[y];b=art->collision_bands+offset;
        for(i=0;i<b[0];i++)if(x0<b[2+i*2]&&x1>=b[1+i*2])return 0;
        do { y++; }while(y<=y1&&art->collision_rows[y]==offset);
    }
    return 1;
}
int game_collision_rects(int x0,int y0,int x1,int y1,short out[][4],unsigned cap) {
    unsigned i,n=0,offset;int y,end,last;const unsigned short *b;
    if(snapshot_refuse)return -1;
    y=y0<0?0:y0;last=y1>=art->height?art->height-1:y1;
    while(y<=last) {
        offset=art->collision_rows[y];end=y;
        while(end<last&&art->collision_rows[end+1]==offset)end++;
        b=art->collision_bands+offset;
        for(i=0;i<b[0];i++) {
            int l=b[1+i*2],r=b[2+i*2]-1;
            if(l>x1||r<x0)continue;
            if(n>=cap)return -1;
            out[n][0]=(short)(l<x0?x0:l);out[n][1]=(short)y;
            out[n][2]=(short)(r>x1?x1:r);out[n++][3]=(short)end;
        }
        y=end+1;
    }
    return (int)n;
}
int covenants_game_supercover(int x,int y,int tx,int ty) {
    int ax=abs(tx-x),ay=-abs(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,e=ax+ay;
    if(solid(x,y)||solid(tx,ty))return 0;
    while(x!=tx||y!=ty) {
        int q=e*2,nx=x,ny=y;
        if(q>=ay) { e+=ay;nx+=sx; }if(q<=ax) { e+=ax;ny+=sy; }
        if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return 0;
        x=nx;y=ny;if(solid(x,y))return 0;
    }
    return 1;
}
static int visible(int tx,int ty,int radius) {
    unsigned i;int x,y;
    for(i=0;i<draws;i++) {
        if(draw_w[i]!=8)continue;
        for(y=0;y<8;y++)for(x=0;x<8;x++) {
            int xx=abs(draw_x[i]+x-tx),yy=abs(draw_y[i]+y-ty);
            if(xx<=radius&&yy<=radius&&xx+yy<=radius+3&&vram[draw_off[i]+y*8+x])return 1;
        }
    }
    return 0;
}
int main(int argc,char **argv) {
    int v[12],i,index;unsigned age,hits[2]={0,0},mask=0;const CovenantsPowerProof *proof;
    if(argc!=10&&argc!=13)return 2;
    for(i=0;i<argc-1;i++)v[i]=atoi(argv[i+1]);
    index=v[0]==12?0:v[0]-121;
    if(index<0||index>7||v[1]<70||v[1]>77)return 3;
    art=&covenants_art_rooms[v[1]-70];snapshot_refuse=(unsigned)v[5];
    setup((unsigned)v[0]);room=v[1];px=v[2];py=v[3];face=v[4];assert(!solid(px,py));
    assert(covenants_power((unsigned)v[0]));proof=covenants_powers_proof();assert(proof);
    for(age=1;age<lifetime[index];age++) {
        unsigned beat;tick();beat=covenants_powers_beat();
        for(i=0;i<(argc==13?2:1);i++)if(covenants_powers_overlap(v[6+i*3],v[7+i*3],v[8+i*3])) {
            assert(visible(v[6+i*3],v[7+i*3],v[8+i*3]));assert(beat==1||beat==2);
            assert(proof->origin_x==px&&proof->origin_y==py&&proof->direction==face);
            hits[i]++;mask|=1u<<(i*2+beat-1);printf("%u:%u:%d,",age,beat,i);
        }
    }
    assert(hits[0]&&(argc!=13||hits[1]));
    if(v[0]==123)assert((mask&9u)==9u);
    printf(" %u %u %u\n",mask,hits[0],hits[1]);return 0;
}
