/* Independent cache boundary/lifetime checks. Synthetic geometry only; the
 * actual room snapshot is proved separately by collision_rects_host.c. */
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#ifndef POWER_SOURCE
#define POWER_SOURCE "../src/horizons_powers.c"
#endif
#include POWER_SOURCE
volatile int room,px,py;
int face,ability_cd,ability_max,hitstop;
static unsigned fills,point_fallbacks,box_fallbacks,revocations;
static int result_mode;
int game_collision_rects(int x0,int y0,int x1,int y1,short out[][4],unsigned cap){
 fills++;assert(cap==48);
 if(result_mode){out[0][0]=out[0][1]=out[0][2]=out[0][3]=100;return result_mode;}
 if(x0<=120&&x1>=120&&y0<=100&&y1>=100){out[0][0]=out[0][2]=120;out[0][1]=out[0][3]=100;return 1;}
 return 0;
}
int solid(int x,int y){point_fallbacks++;return y==100&&(x==120||x==170);}
int game_clear_box(int x0,int y0,int x1,int y1){(void)x0;(void)y0;(void)x1;(void)y1;box_fallbacks++;return 0;}
int horizons_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
int underwater_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
int return_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
void horizons_game_revoke_cast(unsigned value){assert(value==77);revocations++;}
int northern_powers_tiles_release(unsigned owner){assert(owner==NORTHERN_TILES_HORIZONS);return 1;}
static void prepare(void){horizons_power_time=0;horizons_powers_reset();room=0;horizons_power_origin_x=horizons_power_origin_y=100;result_mode=0;}
int main(void){
 unsigned before,i;static const int malformed[]={-1,-2,49,256,INT_MIN,INT_MAX};
 prepare();before=fills;
 assert(geometry_snapshot(36,36,164,164));assert(fills==before+1&&collision.valid==1&&collision.count==1);
 assert(!clear(100,100,120,100));assert(clear(100,99,120,99));
 assert(!geometry_snapshot(35,36,164,164));assert(!geometry_snapshot(36,35,164,164));
 assert(!geometry_snapshot(36,36,165,164));assert(!geometry_snapshot(36,36,164,165));
 assert(fills==before+1);before=point_fallbacks;assert(blocked(170,100));assert(point_fallbacks==before+1);
 before=box_fallbacks;assert(!clear_box(169,99,171,101));assert(box_fallbacks==before+1);
 before=fills;room=1;assert(geometry_snapshot(100,100,101,101));assert(fills==before+1);
 for(i=0;i<sizeof malformed/sizeof *malformed;i++){
  prepare();result_mode=malformed[i];before=fills;
  assert(!geometry_snapshot(100,100,101,101));assert(collision.valid==2&&collision.count==0);
  assert(!blocked(100,100));assert(clear(100,100,110,100)); /* Ignore the poisoned partial rectangle. */
  assert(!clear(100,100,120,100));assert(fills==before+1);
  horizons_powers_geometry_changed();assert(!geometry_snapshot(100,100,101,101));assert(fills==before+2);
 }
 prepare();assert(geometry_snapshot(100,100,101,101));ability_cd=45;horizons_power_time=10;cast.token=77;
 horizons_powers_selection_changed();assert(!collision.valid&&cast.revoked&&cast.aimed&&ability_cd==45&&revocations==1);
 assert(geometry_snapshot(100,100,101,101));cast.field_valid=1;cast.dirty=0;
 horizons_powers_geometry_changed();assert(!collision.valid&&cast.revoked&&cast.dirty&&!cast.field_valid&&ability_cd==45&&revocations==2);
 assert(geometry_snapshot(100,100,101,101));assert(cast.revoked&&cast.dirty&&ability_cd==45);
 horizons_powers_reset();assert(!collision.valid&&!horizons_power_time&&ability_cd==45&&revocations==3);
 prepare();horizons_power_origin_x=horizons_power_origin_y=0;assert(geometry_snapshot(0,0,64,64));assert(!geometry_snapshot(-1,0,64,64));
 prepare();horizons_power_origin_x=horizons_power_origin_y=1023;assert(geometry_snapshot(959,959,1023,1023));assert(!geometry_snapshot(959,959,1024,1023));
 puts("Envelope edges, room guard, poisoned partial/invalid counts, failed-fill retention, reset/selection/geometry invalidation, permanent revocation, and no cooldown refund passed");
 return 0;
}
