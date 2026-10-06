/* Isolated pre-Magma combat harness bridge: these tests exercise old chapters.
 * Full Magma behavior is linked and tested in test_magma_powers.py instead. */
#include "magma_game.h"
#include "magma_powers.h"
int magma_game_target(int*x,int*y,int*r){(void)x;(void)y;(void)r;return 0;}
int magma_game_weapon_hit(unsigned c,int x,int y,unsigned d,unsigned ch,unsigned token){(void)c;(void)x;(void)y;(void)d;(void)ch;(void)token;return 0;}
unsigned magma_game_action_begin(unsigned ch){return ch<4?1:0;}
int magma_powers_busy(void){return 0;}

/* No Magma world return job exists in these pre-Magma combat harnesses. */
void magma_game_cancel_return(void){}
