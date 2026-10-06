/* Synthetic host-only observation. No engine behavior is replaced.
 * Mapped addresses are inert backing memory, NOT emulated GBA hardware/DMA. */
#define _GNU_SOURCE
#include <sys/mman.h>
#include <stdint.h>
#include "magma_quests.h"
#include "magma_game.h"
#include "progression.h"
extern volatile int game_state;
extern void render_static(void),update_enemies(void),update_shots(void),ability(void);
unsigned probe_anchor,probe_begin,probe_step,probe_render,probe_enemies,probe_shots,probe_tick,probe_ability;
unsigned probe_anchor_modes;
#define NI __attribute__((no_instrument_function))
void NI __cyg_profile_func_enter(void *fn,void *caller){
 (void)caller;
 if(fn==(void*)magma_anchor){probe_anchor++;probe_anchor_modes|=1u<<game_state;}
 else if(fn==(void*)save5_begin)probe_begin++;
 else if(fn==(void*)save5_step)probe_step++;
 else if(fn==(void*)render_static)probe_render++;
 else if(fn==(void*)update_enemies)probe_enemies++;
 else if(fn==(void*)update_shots)probe_shots++;
 else if(fn==(void*)magma_game_tick)probe_tick++;
 else if(fn==(void*)ability)probe_ability++;
}
void NI __cyg_profile_func_exit(void *fn,void *caller){(void)fn;(void)caller;}
void NI probe_reset(void){probe_anchor=probe_begin=probe_step=probe_render=probe_enemies=probe_shots=probe_tick=probe_ability=probe_anchor_modes=0;}
int NI probe_map(void){
 const uintptr_t addresses[]={0x04000000,0x05000000,0x06000000,0x07000000};
 unsigned i;
 for(i=0;i<4;i++)if(mmap((void*)addresses[i],0x20000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==MAP_FAILED)return 0;
 return 1;
}
