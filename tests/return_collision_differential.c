/* B-versus-patched full-raster/cast trace. Included historical host harness
 * supplies actual catalog, procedural tiles, handlers and observable state. */
#define main original_host_main
#include "return_legacy_powers_host.c"
#undef main
extern int collision_test_clear(int,int,int,int);
extern void collision_test_draw(int,int,int,int);
extern void collision_test_field(int,int,int,int,ReturnLegacyEmit,void*);
static void word(unsigned n){unsigned char b[4]={(unsigned char)n,(unsigned char)(n>>8),(unsigned char)(n>>16),(unsigned char)(n>>24)};assert(fwrite(b,1,4,stdout)==4);}
static void draw_trace(void){unsigned i;word(draws);for(i=0;i<draws;i++){word((unsigned)draw[i].x);word((unsigned)draw[i].y);word((unsigned)draw[i].size);word((unsigned)draw[i].off);assert(fwrite(vram+draw[i].off,1,(size_t)(draw[i].size*draw[i].size),stdout)==(size_t)(draw[i].size*draw[i].size));}}
static void piece_trace(void*ctx,const ReturnLegacyPiece*p){int x,y;(void)ctx;word((unsigned)p->x);word((unsigned)p->y);word(p->size);word(p->kind);for(y=0;y<p->size;y++)for(x=0;x<p->size;x++)word((unsigned)opaque(p,x,y));}
static void walls_case(unsigned n){wall_count=0;if(n==1){walls[0].x=100;walls[0].y=100;walls[0].w=1;walls[0].h=1;wall_count=1;}if(n==2||n==3){walls[0].x=100;walls[0].y=65;walls[0].w=1;walls[0].h=70;wall_count=1;if(n==3){walls[1].x=65;walls[1].y=100;walls[1].w=70;walls[1].h=1;wall_count=2;}}if(n==4){walls[0].x=101;walls[0].y=100;walls[0].w=1;walls[0].h=1;walls[1].x=100;walls[1].y=101;walls[1].w=1;walls[1].h=1;wall_count=2;}if(n==5){walls[0].x=85;walls[0].y=85;walls[0].w=7;walls[0].h=11;walls[1].x=107;walls[1].y=102;walls[1].w=13;walls[1].h=5;wall_count=2;}}
int main(void){unsigned scenario,area,dir,j,age;int dx,dy;
 /* Full direct raster semantics: blocked start/end, zero length, every slope,
  * touching corners, clipping at thin dynamic walls, exact six-pixel samples
  * and ten-OBJ bound. Room22 proves the Return-only guard falls back. */
 for(area=0;area<2;area++)for(scenario=0;scenario<6;scenario++){
  setup(13);assert(cast_power(13));room=area?22:54;walls_case(scenario);
  for(dx=-32;dx<=32;dx++)for(dy=-32;dy<=32;dy++){
   word((unsigned)collision_test_clear(100,100,100+dx,100+dy));draws=0;collision_test_draw(100,100,100+dx,100+dy);draw_trace();collision_test_field(100,100,100+dx,100+dy,piece_trace,0);word(0xffffffffu);
  }
 }
 /* Real effect geometry/pixels/gameplay before and after dynamic blockers
  * change during active casts, in every facing and every old field command. */
 for(j=0;j<sizeof commands/sizeof commands[0];j++)for(dir=0;dir<4;dir++)for(scenario=0;scenario<4;scenario++){
  unsigned c=commands[j];setup(c);face=(int)dir;enemies[0]=(Enemy){100,80,1000,0,0};enemies[1]=(Enemy){120,90,1000,0,0};assert(cast_power(c));
  for(age=0;age<96;age++){
   if(scenario&&age==10)walls_case(scenario);if(age==24)walls_case(0);if(scenario&&age==35)walls_case(4);if(age==50)walls_case(0);
   effects_draw(c);draw_trace();export(c,piece_trace);word(0xffffffffu);word(checksum());
   word((unsigned)return_legacy_overlap(100,76,12));word((unsigned)return_legacy_overlap(113,85,0));word((unsigned)return_legacy_overlap(100,100,0));
   effects_tick();return_legacy_tick();
  }
 }
 return 0;
}
