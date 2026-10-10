/* Synthetic component geometry, not legacy-room or controller evidence.
 * Run the existing real-catalog assertions with an exact snapshot, then with
 * unsupported/overflow snapshots so neither cache nor fallback loses coverage. */
#define main original_power_host_main
#include "horizons_powers_host.c"
#undef main
static unsigned snapshot_calls;
static int snapshot_refuse;
static int test_rect(short out[][4],unsigned cap,int*n,int x0,int y0,int x1,int y1,int l,int t,int r,int b){
 if(l<x0)l=x0;if(t<y0)t=y0;if(r>x1)r=x1;if(b>y1)b=y1;if(l>r||t>b)return 1;
 if((unsigned)*n>=cap)return 0;out[*n][0]=(short)l;out[*n][1]=(short)t;out[*n][2]=(short)r;out[*n][3]=(short)b;(*n)++;return 1;
}
int game_collision_rects(int x0,int y0,int x1,int y1,short out[][4],unsigned cap){int n=0,i;snapshot_calls++;
 if(snapshot_refuse){if(cap)out[0][0]=out[0][1]=out[0][2]=out[0][3]=100;return-1;}
 for(i=0;i<wall_count;i++)if(!test_rect(out,cap,&n,x0,y0,x1,y1,walls[i].x,walls[i].y,walls[i].x+walls[i].w-1,walls[i].y+walls[i].h-1))return-1;
 if(!test_rect(out,cap,&n,x0,y0,x1,y1,-32768,-32768,-1,32767)||!test_rect(out,cap,&n,x0,y0,x1,y1,480,-32768,32767,32767)||!test_rect(out,cap,&n,x0,y0,x1,y1,-32768,-32768,32767,-1)||!test_rect(out,cap,&n,x0,y0,x1,y1,-32768,320,32767,32767))return-1;
 return n;
}
int underwater_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return-1;}
int return_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return-1;}
static void cache_lifetime(void){unsigned n;
 snapshot_refuse=0;setup(121);assert(horizons_power(121));n=snapshot_calls;updates(12);assert(snapshot_calls==n);
 horizons_powers_selection_changed();tick();assert(snapshot_calls==n+1);n=snapshot_calls;
 wall(112,100,1,1);tick();assert(snapshot_calls==n+1);n=snapshot_calls;
 room=63;tick();assert(snapshot_calls==n+1);
 setup(121);snapshot_refuse=1;assert(horizons_power(121));n=snapshot_calls;updates(12);assert(snapshot_calls==n); /* failed snapshot cached, no repeated fill */
 puts("snapshot lifetime: cast/reset, geometry, selection, room guard and failed-fill boundedness passed");
}
int main(void){int r;snapshot_refuse=0;r=original_power_host_main();assert(!r);snapshot_refuse=1;r=original_power_host_main();assert(!r);cache_lifetime();printf("Exact synthetic snapshots plus unsupported/partial-overflow fallback passed; %u fills\n",snapshot_calls);return 0;}
