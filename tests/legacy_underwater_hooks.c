/* Explicit absent-region bridge for isolated PRE-Underwater combat tests.
 * These suites use no Underwater rooms or powers; real current behavior is
 * linked by test_underwater_powers.py and the full native cartridge tests. */
#include "underwater_game.h"
#include "underwater_powers.h"
int underwater_game_target(int*x,int*y,int*r){(void)x;(void)y;(void)r;return 0;}
int underwater_game_weapon_hit(unsigned c,int x,int y,unsigned d,unsigned ch,unsigned token){(void)c;(void)x;(void)y;(void)d;(void)ch;(void)token;return 0;}
unsigned underwater_game_action_begin(unsigned ch){return ch<4?1:0;}
int underwater_powers_busy(void){return 0;}
