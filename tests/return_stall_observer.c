/* Read-only emulator-side native Return stall observer. No ROM/RAM writes.
 * Entry/return observer adapted from legacy_mgba_profile.c. Host-side exact
 * per-instruction cycle attribution is diagnostic, validated against runFrame. */
#include <mgba/core/core.h>
#include <mgba/core/timing.h>
#include <mgba/internal/arm/arm.h>
#include <stdint.h>
#include <string.h>
struct SessionPrefix { struct mCore *core; };
struct ProfileRow { uint64_t begin,end;uint32_t probe,entry_frame,exit_frame,entry_pc,return_pc; };
struct Probe { uint32_t address,return_pc,sp,frame;uint64_t start;int active; };
static struct Probe probes[128];
static struct ProfileRow rows[262144];
static unsigned count,nprobes,overflow,reentered;
static uint32_t starts[2048],ends[2048],nfunctions;
static uint64_t cycles[2049],instructions[2049];
struct LoopRow {uint64_t begin,end;uint32_t entry_frame,exit_frame;};
static struct LoopRow loops[128];
static uint64_t loop_cycles[128][2049];
static unsigned loop_count,loop_active,last_index;
static uint32_t update_address,render_address;
void return_loop_config(uint32_t update,uint32_t render){update_address=update&~1u;render_address=render&~1u;loop_count=loop_active=last_index=0;memset(loops,0,sizeof loops);memset(loop_cycles,0,sizeof loop_cycles);}
unsigned return_loop_count(void){return loop_count;}
const struct LoopRow *return_loops(void){return loops;}
const uint64_t *return_loop_cycles(unsigned n){return loop_cycles[n];}
static void charge(unsigned i,uint64_t delta){cycles[i]+=delta;if(loop_active&&loop_count<=128)loop_cycles[loop_count-1][i]+=delta;}

void return_profile_reset(const uint32_t *addresses,unsigned n,const uint32_t *fs,const uint32_t *fe,unsigned fn){unsigned i;memset(probes,0,sizeof probes);count=overflow=reentered=0;nprobes=n>128?128:n;for(i=0;i<nprobes;i++)probes[i].address=addresses[i]&~1u;nfunctions=fn>2048?2048:fn;memcpy(starts,fs,nfunctions*4);memcpy(ends,fe,nfunctions*4);}
void return_hist_reset(void){memset(cycles,0,sizeof cycles);memset(instructions,0,sizeof instructions);}
const uint64_t *return_hist_cycles(void){return cycles;}
const uint64_t *return_hist_instructions(void){return instructions;}
unsigned return_profile_count(void){return count;}
unsigned return_profile_overflow(void){return overflow;}
unsigned return_profile_reentered(void){return reentered;}
const struct ProfileRow *return_profile_rows(void){return rows;}
static unsigned resolve(uint32_t pc){unsigned lo=0,hi=nfunctions;while(lo<hi){unsigned m=(lo+hi)/2;if(starts[m]<=pc)lo=m+1;else hi=m;}return lo&&pc<ends[lo-1]?lo-1:nfunctions;}
void return_profile_frames(void *v,unsigned frames,unsigned keys){
 struct mCore *core=((struct SessionPrefix*)v)->core;struct ARMCore *cpu=core->cpu;
 uint32_t target=core->frameCounter(core)+frames;core->setKeys(core,keys&1023);
 while(core->frameCounter(core)!=target){
  if(cpu->cycles>=cpu->nextEvent){uint64_t before=mTimingGlobalTime(core->timing);cpu->irqh.processEvents(cpu);charge(last_index,mTimingGlobalTime(core->timing)-before);if(core->frameCounter(core)==target)break;}
  uint32_t pc=(uint32_t)cpu->gprs[ARM_PC]-(cpu->executionMode==MODE_THUMB?2u:4u);
  uint32_t sp=(uint32_t)cpu->gprs[ARM_SP];uint64_t now=mTimingGlobalTime(core->timing);unsigned i;
  for(i=0;i<nprobes;i++){
   struct Probe *p=probes+i;
   if(p->active&&pc==p->return_pc&&sp==p->sp){
    if(count<sizeof rows/sizeof rows[0])rows[count++]=(struct ProfileRow){p->start,now,i,p->frame,core->frameCounter(core),p->address,p->return_pc};else overflow++;
    p->active=0;
    if(p->address==render_address&&loop_active){loops[loop_count-1].end=now;loops[loop_count-1].exit_frame=core->frameCounter(core);loop_active=0;}
   }
   if(pc==p->address){
    if(p->address==update_address&&loop_count<128){loop_count++;loop_active=1;loops[loop_count-1].begin=now;loops[loop_count-1].entry_frame=core->frameCounter(core);}
    if(p->active)reentered++;p->active=1;p->return_pc=(uint32_t)cpu->gprs[ARM_LR]&~1u;p->sp=sp;p->start=now;p->frame=core->frameCounter(core);}
  }
  i=resolve(pc);core->step(core);charge(i,mTimingGlobalTime(core->timing)-now);instructions[i]++;last_index=i;
 }
}
/* mCore saveState intentionally leaves reserved bytes untouched. The ordinary
 * bridge uses malloc, so unrelated host allocations leak into those bytes.
 * Zero only the host output buffer for byte-exact deterministic comparison. */
#include <stdio.h>
#include <stdlib.h>
int return_state_save(void *v,const char *path){struct mCore *core=((struct SessionPrefix*)v)->core;size_t n=core->stateSize(core);void *p=calloc(1,n);if(!p)return 0;FILE *f=fopen(path,"wb");if(!f){free(p);return 0;}int ok=core->saveState(core,p)&&fwrite(p,1,n,f)==n;fclose(f);free(p);return ok;}
