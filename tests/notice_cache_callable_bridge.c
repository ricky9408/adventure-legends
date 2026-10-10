/* Test-only native function invocation. Each branch restores a same-ROM
 * snapshot first. It intentionally suspends gameplay and IRQ dispatch; after
 * return the CPU idles, so two complete scanouts observe a fixed framebuffer.
 * This is a raster oracle, never active gameplay or pacing evidence. */
#include "player_feedback_mgba_bridge.c"
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/arm/isa-inlines.h>
unsigned eb_notice_call(void *v,uint32_t address){
 struct Session*s=v;struct ARMCore*cpu=((struct GBA*)s->core->board)->cpu;
 const uint32_t stop=0x0203fff0;unsigned count;
 s->core->busWrite16(s->core,stop,0xe7fe);
 cpu->cpsr.priv=MODE_SYSTEM;cpu->cpsr.i=1;cpu->cpsr.t=1;_ARMReadCPSR(cpu);
 cpu->gprs[0]=1;cpu->gprs[ARM_SP]=0x03007e00;cpu->gprs[ARM_LR]=stop|1;cpu->gprs[ARM_PC]=address;
 cpu->cycles+=ThumbWritePC(cpu);
 for(count=0;count<1000000;count++){
  if((uint32_t)cpu->gprs[ARM_PC]==stop+2&&cpu->executionMode==MODE_THUMB)return count+1;
  s->core->step(s->core);
 }
 return 0;
}
void eb_notice_fill(void*v,uint32_t address,unsigned seed){
 struct Session*s=v;unsigned i;
 for(i=0;i<38400;i+=4){seed=seed*1664525u+1013904223u;s->core->busWrite32(s->core,address+i,seed);}
}
