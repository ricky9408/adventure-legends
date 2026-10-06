/* Synthetic host hardware/clock bridge. World, casts, LOS, target geometry and
 * quest transactions are real. No controller/native acquisition claim. */
#include "underwater_powers.h"
#include "underwater_game.h"
#include "northern_powers.h"
#include "progression.h"
#include "gear_runtime.h"
typedef struct{int x,y,hp,flash,kind;}Enemy;
Enemy enemies[6];
int ability_cd,ability_max,hitstop;
static unsigned owner,generation;
extern int settle_events(void);
extern volatile int game_state;
int solid(int x,int y){return underwater_game_solid(x,y);}
void kill_enemy(Enemy*e){e->hp=0;}
void impact(int x,int y){(void)x;(void)y;}
void sfx(int x){(void)x;}
void obj_upload(const unsigned char*p,int w,int h,int off){(void)p;(void)w;(void)h;(void)off;}
void obj_add(int off,int x,int y,int w,int h,int p,int d,int f){(void)off;(void)x;(void)y;(void)w;(void)h;(void)p;(void)d;(void)f;}
unsigned game_power_cooldown(unsigned n){return n;}
void game_enemy_hurt(unsigned i,unsigned d,unsigned a,unsigned p){(void)i;(void)d;(void)a;(void)p;}
unsigned northern_powers_tiles_owner(void){return owner;}
unsigned northern_powers_tiles_generation(void){return generation;}
int northern_powers_tiles_claim(unsigned o){if(owner)return 0;owner=o;generation++;return 1;}
int northern_powers_tiles_release(unsigned o){if(owner!=o)return 0;owner=0;return 1;}
int real_cast(void){unsigned n=0;game_state=1;while(underwater_power_time||ability_cd){if(ability_cd)ability_cd--;underwater_powers_tick();if(!settle_events()||++n>1000)return-1;}if(!underwater_power(progression_command()))return-2;n=0;while(underwater_power_time){underwater_powers_tick();if(ability_cd)ability_cd--;if(!settle_events()||++n>1000)return-3;}return 1;}
