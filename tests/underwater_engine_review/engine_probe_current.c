/* Synthetic host-only observation. No engine behavior is replaced.
 * Mapped addresses are inert backing memory, NOT emulated GBA hardware/DMA. */
#define _GNU_SOURCE
#include <sys/mman.h>
#include <stdint.h>
#include <errno.h>
#include "magma_quests.h"
#include "magma_game.h"
#include "underwater_game.h"
#include "underwater_quests.h"
#include "progression.h"
extern volatile int game_state;
extern void render_static(void),update_enemies(void),update_shots(void),ability(void);
unsigned probe_anchor,probe_begin,probe_step,probe_render,probe_enemies,probe_shots,probe_tick,probe_ability;
unsigned probe_anchor_modes,probe_copy,probe_copy_pages;
extern void render(void),draw_actors(void);
extern int page;
unsigned probe_event,probe_job,probe_preflight,probe_admission,probe_grant,probe_evolve,probe_validate,probe_heal,probe_uwtick;
extern void game_health_fill(void);
#define NI __attribute__((no_instrument_function))
void NI __cyg_profile_func_enter(void *fn,void *caller){
 (void)caller;
 /* Inert host registers never execute DMA. Clear a stale enable request at
  * render entry, then observe exactly the full-page command before actors
  * may reuse DMA3. This counts requests, not hardware pixels or DMA timing. */
 if(fn==(void*)render)*(volatile uint32_t*)0x040000DC=0;
 if(fn==(void*)draw_actors&&*(volatile uint32_t*)0x040000DC==(0x84000000u|9600u)&&
    *(volatile uint32_t*)0x040000D4==(page?0x06000000u:0x0600A000u)&&
    *(volatile uint32_t*)0x040000D8==(page?0x0600A000u:0x06000000u)){
  probe_copy++;probe_copy_pages|=1u<<(unsigned)page;
 }

 if(fn==(void*)underwater_game_prepare_event)probe_event++;
 if(fn==(void*)underwater_job_step)probe_job++;
 if(fn==(void*)save5_preflight_step)probe_preflight++;
 if(fn==(void*)creatures_admission_job_step)probe_admission++;
 if(fn==(void*)creatures_admission_job_commit_grant)probe_grant++;
 if(fn==(void*)creatures_admission_job_commit_evolution)probe_evolve++;
 if(fn==(void*)save5_validate)probe_validate++;
 if(fn==(void*)game_health_fill)probe_heal++;
 if(fn==(void*)underwater_game_tick)probe_uwtick++;
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
void NI probe_reset(void){probe_copy=probe_copy_pages=0;probe_event=probe_job=probe_preflight=probe_admission=probe_grant=probe_evolve=probe_validate=probe_heal=probe_uwtick=0;probe_anchor=probe_begin=probe_step=probe_render=probe_enemies=probe_shots=probe_tick=probe_ability=probe_anchor_modes=0;}
/* Diagnostics never replace or overwrite a pre-existing host mapping. */
uintptr_t probe_map_error_address;
int probe_map_error_number;
unsigned probe_map_success_count;
int NI probe_map(void){
 const uintptr_t addresses[]={0x04000000,0x05000000,0x06000000,0x07000000};
 unsigned i,j;
 probe_map_error_address=0;probe_map_error_number=0;probe_map_success_count=0;
 for(i=0;i<4;i++){
  void *mapped=mmap((void*)addresses[i],0x20000,PROT_READ|PROT_WRITE,
                   MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
  if(mapped==MAP_FAILED || mapped!=(void*)addresses[i]){
   probe_map_error_address=addresses[i];
   probe_map_error_number=mapped==MAP_FAILED?errno:ENOTSUP;
   if(mapped!=MAP_FAILED)munmap(mapped,0x20000);
   for(j=0;j<i;j++)munmap((void*)addresses[j],0x20000);
   return 0;
  }
  probe_map_success_count++;
 }
 return 1;
}
