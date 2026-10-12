#include "enemy_tactics.h"
#include "assets.h"
#if defined(__arm__)
#define COLD __attribute__((section(".text.rom"),long_call,noinline))
#else
#define COLD
#endif
typedef struct {int x,y,hp,flash,kind;} Enemy;
extern Enemy enemies[6];
extern volatile int px,py,game_state;
extern int frame,enemy_clocks[6],enemy_windups[6],enemy_aimx[6],enemy_aimy[6];
extern int rooted_enemies[6];
extern unsigned char slowed_enemies[6],enemy_stagger_ticks[6];
extern int solid(int,int);
extern unsigned southern_powers_windup(unsigned,unsigned);
extern void region_pixels_actor(unsigned,const unsigned char*,int,int);
#include "enemy_tactics_art.inc"
static COLD int magnitude(int x){return x<0?-x:x;}
static COLD void recover(unsigned i){
 enemy_windups[i]=0;enemy_clocks[i]=ENEMY_CHARGE_RECOVERY;
 enemy_aimx[i]=enemy_aimy[i]=0;
}
COLD void enemy_tactics_update(unsigned i){
 Enemy*e;int dx,dy,n;
 if(i>=6||game_state!=1)return;
 e=&enemies[i];if(e->kind!=ENEMY_LANE_CHARGER||e->hp<=0)return;
 /* All existing attacks/roots can interrupt the warning or rush. Releasing a
  * root never resumes a stale aimed attack. The engine owns hitstop/modal freeze. */
 if(e->flash||enemy_stagger_ticks[i]||rooted_enemies[i]){recover(i);return;}
 if(enemy_clocks[i]>0){enemy_clocks[i]--;return;}
 if(enemy_windups[i]>0){
  if(--enemy_windups[i]==0)enemy_clocks[i]=-ENEMY_CHARGE_STEPS;
  return;
 }
 if(enemy_clocks[i]<0){
  if(slowed_enemies[i]&&(frame&1))return;
  /* Probe every radius-five foot position: never jump over a thin wall. */
  for(n=0;n<ENEMY_CHARGE_SPEED;n++){
   int x=e->x+enemy_aimx[i],y=e->y+enemy_aimy[i];
   if(solid(x,y)){recover(i);return;}e->x=x;e->y=y;
  }
  if(++enemy_clocks[i]==0)recover(i);
  return;
 }
 dx=px-e->x;dy=py-e->y;
 if(magnitude(dx)+magnitude(dy)>ENEMY_CHARGE_RANGE)return;
 /* Cardinal lane is locked now, not homed during the rush. A side-step can
  * avoid contact and leaves a long, vulnerable recovery at the endpoint. */
 enemy_aimx[i]=enemy_aimy[i]=0;
 if(magnitude(dx)>magnitude(dy))enemy_aimx[i]=dx<0?-1:1;
 else enemy_aimy[i]=dy<0?-1:1;
 enemy_windups[i]=(int)southern_powers_windup(i,ENEMY_CHARGE_WARNING);
}
COLD void enemy_tactics_draw(unsigned i){
 unsigned direction=0,pose,index;
 if(i>=6||enemies[i].kind!=ENEMY_LANE_CHARGER)return;
 if(enemy_windups[i]||enemy_clocks[i]<0){
  direction=enemy_aimy[i]<0?1u:enemy_aimx[i]<0?2u:enemy_aimx[i]>0?3u:0u;
 }
 pose=enemy_windups[i]>0;index=pose*4+direction;
 /* Same single 16x16 regional cache entry as a ranger. No resident OBJ growth,
  * extra actor slot, or new effect object; the existing spark marks warning. */
 region_pixels_actor(20480u+index,charger_pixels[index],enemies[i].x,enemies[i].y);
}
