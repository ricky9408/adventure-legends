/* Synthetic actual-module pixel snapshots and sampled cumulative hit maps.
 * No emulator, no player-acquisition claim, no engine/controller affordance proof. */
#define main underwater_host_test_main
#include "underwater_powers_native.c"
#undef main
#include "assets.h"
static unsigned char picture[240*160],hit_map[240*160];
static void render(void){int i,x,y;memset(picture,0,sizeof picture);record_draws=1;capture_count=0;underwater_powers_draw();record_draws=0;
 for(i=0;i<capture_count;i++)for(y=0;y<capture_width[i];y++)for(x=0;x<capture_width[i];x++){
  int sx=capture_x[i]+x,sy=capture_y[i]+y,w=capture_width[i];
  unsigned tile=(unsigned)((y/8)*(w/8)+x/8),off=tile*64+(unsigned)(y%8)*8+(unsigned)(x%8);
  unsigned char color=vram[capture_off[i]+off];if(color&&sx>=0&&sx<240&&sy>=0&&sy<160)picture[sy*240+sx]=color;
 }
}
int main(void){unsigned c,n,i,j;fwrite(game_palette,2,256,stdout);
 for(c=67;c<=90;c++){
  unsigned ages[3]={start[c-67]-2,start[c-67]+active_len[c-67]/2,start[c-67]+active_len[c-67]-1};
  for(j=0;j<3;j++){setup(c);enemy(0,positions[c-67][0],positions[c-67][1],10);assert(underwater_power(c));
   for(n=0;n<ages[j];n++)scenario_update(c);render();fwrite(picture,1,sizeof picture,stdout);}
  memset(hit_map,0,sizeof hit_map);
  /* A2px sample grid is explicitly labelled, not a continuous exact boundary. */
  for(n=0;n<46*31;n+=6){setup(c);for(i=0;i<6&&n+i<46*31;i++){int f=(int)((n+i)/31)*2-28,s=(int)((n+i)%31)*2-30;enemy(i,100+f,100+s,10);}
   assert(underwater_power(c));updates(life[c-67]);for(i=0;i<6&&n+i<46*31;i++)if(enemy_hp_q4[i]<160){int f=(int)((n+i)/31)*2-28,s=(int)((n+i)%31)*2-30;hit_map[(100+s)*240+100+f]=1;}}
  fwrite(hit_map,1,sizeof hit_map,stdout);
 }
 return 0;
}
