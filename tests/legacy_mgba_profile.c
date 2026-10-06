/* Read-only PC/timing observer for the existing mGBA test session ABI.
 * No cartridge instrumentation, memory writes, or emulated timing changes. */
#include <mgba/core/core.h>
#include <mgba/core/timing.h>
#include <mgba/internal/arm/arm.h>
#include <stdint.h>
#include <string.h>
struct SessionPrefix { struct mCore *core; };
struct ProfileRow { uint64_t begin,end;uint32_t probe,entry_frame,exit_frame,entry_pc,return_pc; };
struct Probe { uint32_t address,return_pc,sp,frame;uint64_t start;int active; };
static struct Probe probes[64];
static struct ProfileRow rows[131072];
static unsigned count,nprobes,overflow,reentered;
void legacy_profile_reset(const uint32_t *addresses,unsigned n){unsigned i;memset(probes,0,sizeof probes);count=overflow=reentered=0;nprobes=n>64?64:n;for(i=0;i<nprobes;i++)probes[i].address=addresses[i]&~1u;}
unsigned legacy_profile_count(void){return count;}
unsigned legacy_profile_overflow(void){return overflow;}
unsigned legacy_profile_reentered(void){return reentered;}
const struct ProfileRow *legacy_profile_rows(void){return rows;}
void legacy_profile_frames(void *v,unsigned frames,unsigned keys){
 struct mCore *core=((struct SessionPrefix*)v)->core;struct ARMCore *cpu=core->cpu;
 uint32_t target=core->frameCounter(core)+frames;core->setKeys(core,keys&1023);
 while(core->frameCounter(core)!=target){
  /* runFrame stops at the video event before the next instruction.
   * Drain due events before single-stepping to preserve that boundary. */
  if(cpu->cycles>=cpu->nextEvent){cpu->irqh.processEvents(cpu);if(core->frameCounter(core)==target)break;}
  uint32_t pc=(uint32_t)cpu->gprs[ARM_PC]-(cpu->executionMode==MODE_THUMB?2u:4u);
  uint32_t sp=(uint32_t)cpu->gprs[ARM_SP];uint64_t now=mTimingGlobalTime(core->timing);unsigned i;
  for(i=0;i<nprobes;i++){
   struct Probe *p=probes+i;
   if(p->active&&pc==p->return_pc&&sp==p->sp){
    if(count<sizeof rows/sizeof rows[0])rows[count++]=(struct ProfileRow){p->start,now,i,p->frame,core->frameCounter(core),p->address,p->return_pc};else overflow++;
    p->active=0;
   }
   if(pc==p->address){
    if(p->active)reentered++;
    p->active=1;p->return_pc=(uint32_t)cpu->gprs[ARM_LR]&~1u;p->sp=sp;p->start=now;p->frame=core->frameCounter(core);
   }
  }
  core->step(core);
 }
}
