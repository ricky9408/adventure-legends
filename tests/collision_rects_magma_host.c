/* Compile the actual production module. Wrappers only configure its real
 * private scalar state; no copied puzzle representation or predicate. */
#include "../src/magma_game.c"
void collision_magma_state(unsigned trial,unsigned lesson,unsigned screen){
 trial_index=(unsigned char)trial;lesson_x=(unsigned char)lesson;screen_x=(unsigned char)screen;
}
unsigned collision_magma_digest(void){
 return (unsigned)trial_index|((unsigned)lesson_x<<8)|((unsigned)screen_x<<16);
}
