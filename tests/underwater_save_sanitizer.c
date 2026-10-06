/* ASan/UBSan host adversaries. No native acquisition assertion. */
#include "underwater_quests.h"
#include <stdio.h>
#include <string.h>
int underwater_test_earned34(Save5State*);int underwater_test_completed(Save5State*,unsigned);
static Save5State base,state,before;
static unsigned char sram_before[32768];
static unsigned random_state=0x554e4436;
static unsigned random_next(void){random_state=random_state*1664525u+1013904223u;return random_state;}
#define CHECK(x) do{if(!(x)){fprintf(stderr,"failed line %u\n",(unsigned)__LINE__);return 1;}}while(0)
int main(void){unsigned i,j,token,result,expected,phase,checks=0;UnderwaterRequest r;
 CHECK(!underwater_test_completed(&base,0));memcpy(sram_before,save5_test_sram,sizeof sram_before);
 for(i=0;i<4000;++i){state=base;
  if(i)for(j=0;j<1+i%3;++j)((unsigned char*)&state)[random_next()%sizeof state]=(unsigned char)random_next();
  before=state;expected=(unsigned)save5_validate(&state);token=save5_preflight_begin(&state);CHECK(token);
  do{result=save5_preflight_step(token,(i%3)?1024:1);}while(result==SAVE5_BUSY);
  CHECK(result==(expected?SAVE5_DONE:SAVE5_FAILED));CHECK(!memcmp(&state,&before,sizeof state));
  CHECK(!memcmp(save5_test_sram,sram_before,sizeof sram_before));save5_preflight_cancel();++checks;
 }
 for(i=0;i<2000;++i){state=base;memset(&r,0,sizeof r);r.operation=UW_REQUEST_REPEAT_RECRUIT;r.source=1;
  token=underwater_job_begin(&state,&r,17);CHECK(token);before=state;
  j=0;do{phase=underwater_job_phase(token);
   if(i%2&&phase==6){state.roster.instances[0].cosmetic_seed^=1;before=state;}
   result=underwater_job_step(token,1024,17);CHECK(++j<200);
   if(phase!=6)CHECK(!memcmp(&state,&before,sizeof state));
  }while(result==SAVE5_BUSY);
  if(i%2){CHECK(result==SAVE5_FAILED);CHECK(!memcmp(&state,&before,sizeof state));}
  else {CHECK(result==SAVE5_DONE);CHECK(underwater_job_result(token)==UNDERWATER_REWARDED);CHECK(save5_validate(&state));}
  CHECK(!memcmp(save5_test_sram,sram_before,sizeof sram_before));underwater_job_cancel();++checks;
 }
 printf("{\"result\":\"PASS\",\"checks\":%u,\"snapshot_mutations\":4000,\"staged_jobs\":2000}\n",checks);return 0;
}
