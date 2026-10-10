/* Synthetic direct-API regression of the real bounded branch transaction.
 * SRAM inputs below are authenticated controller-earned histories; direct
 * transaction calls and malformed/full stress here are not controller proof. */
#include "magma_quests.h"
#include "magma_recruit_fixtures.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static Save5State base,live,expected,before,loaded;
static unsigned char original_sram[32768],saved_sram[32768];
static unsigned checks,scene=1;
static void fixture(unsigned n){
 magma_recruit_job_cancel();save5_test_reset_writer();save5_test_fail_after(-1);
 memcpy((void*)save5_test_sram,n?recruit_104_fixture:recruit_65_fixture,32768);
 assert(save5_load(&base));assert(save5_validate(&base));
 assert(creatures_roster_count(&base.roster)==(n?52:34));
}
static unsigned begin(void){unsigned token=magma_recruit_job_begin(&live,16,++scene);assert(token);return token;}
static unsigned run(unsigned source){
 unsigned token=magma_recruit_job_begin(&live,source,++scene),status=SAVE5_BUSY,n=0;
 assert(token);before=live;memcpy(original_sram,(const void*)save5_test_sram,32768);
 while(status==SAVE5_BUSY){unsigned phase=magma_recruit_job_phase(token);
  status=magma_recruit_job_step(token,640,scene);assert(++n<150);
  if(phase!=3)assert(!memcmp(&live,&before,sizeof live));
  assert(!memcmp(original_sram,(const void*)save5_test_sram,32768));
 }
 assert(status==SAVE5_DONE);expected=live;
 assert(magma_recruit_job_step(token,640,scene)==SAVE5_DONE);
 assert(!memcmp(&live,&expected,sizeof live));assert(!save5_preflight_active());
 ++checks;return (unsigned)magma_recruit_job_result(token);
}
static void parity(void){
 unsigned n,source;int result;Save5State synchronous;
 for(n=0;n<2;++n){fixture(n);
  for(source=16;source<=19;++source){
   live=base;synchronous=base;result=magma_branch_recruit(&synchronous,source);
   assert(run(source)==(unsigned)result);assert(!memcmp(&live,&synchronous,sizeof live));
   assert(save5_validate(&live));
  }
  live=base;live.roster.next_instance_id=0xffffffffu;synchronous=live;
  result=magma_branch_recruit(&synchronous,16);assert(result==MAGMA_ID_EXHAUSTED);
  assert(run(16)==(unsigned)result);assert(!memcmp(&live,&synchronous,sizeof live));
  live=base;while(creatures_roster_count(&live.roster)<160)assert(creatures_grant(&live.roster,1,50,100,0,0)!=255);
  synchronous=live;assert(magma_branch_recruit(&synchronous,16)==MAGMA_FULL);
  assert(run(16)==MAGMA_FULL);assert(!memcmp(&live,&synchronous,sizeof live));
 }
}
static void stale_and_cancel(void){
 unsigned offset,phase,mode,token,status,foreign;fixture(1);
 for(offset=0;offset<sizeof(live);++offset){
  live=base;token=begin();while(magma_recruit_job_phase(token)!=3)assert(magma_recruit_job_step(token,640,scene)==SAVE5_BUSY);
  ((unsigned char*)&live)[offset]^=1;before=live;
  assert(magma_recruit_job_step(token,640,scene)==SAVE5_FAILED);assert(!memcmp(&live,&before,sizeof live));++checks;
 }
 for(phase=0;phase<4;++phase)for(mode=0;mode<5;++mode){
  live=base;token=begin();while(magma_recruit_job_phase(token)<phase)assert(magma_recruit_job_step(token,640,scene)==SAVE5_BUSY);
  assert(!save5_begin(&live));assert(!save5_preflight_begin(&live));before=live;
  if(!mode)magma_recruit_job_cancel();
  else if(mode==1)++scene;
  else if(mode==2){assert(save5_load(&loaded));}
  else if(mode==3){live.roster.selected_party=(live.roster.selected_party+1)%4;before=live;}
  else {save5_preflight_cancel();foreign=save5_preflight_begin(&base);assert(foreign);}
  do{status=magma_recruit_job_step(token,640,scene);}while(status==SAVE5_BUSY);
  assert(status==SAVE5_FAILED);assert(!memcmp(&live,&before,sizeof live));
  if(mode==4){assert(save5_preflight_status(foreign)==SAVE5_BUSY);magma_recruit_job_cancel();assert(save5_preflight_status(foreign)==SAVE5_BUSY);save5_preflight_cancel();}
  ++checks;
 }
 live=base;for(offset=0;offset<65536;offset+=257)if(offset<16||offset>19)assert(!magma_recruit_job_begin(&live,offset,scene));
 assert(!magma_recruit_job_begin(&live,16,0));assert(!magma_recruit_job_begin(0,16,scene));
 live=base;token=begin();before=live;assert(magma_recruit_job_step(token,0,scene)==SAVE5_BUSY);assert(!memcmp(&live,&before,sizeof live));magma_recruit_job_cancel();
 /* Invalid source saves are rejected by bounded proof just as synchronous. */
 live=base;live.roster.instances[0].level=0;before=live;token=begin();do{status=magma_recruit_job_step(token,0xffffffffu,scene);}while(status==SAVE5_BUSY);
 assert(status==SAVE5_FAILED);assert(!memcmp(&live,&before,sizeof live));++checks;
}
static void powercuts(void){
 unsigned cut;fixture(1);live=base;assert(save5_store(&live));memcpy(saved_sram,(const void*)save5_test_sram,32768);
 assert(run(16)==MAGMA_REWARDED);expected=live;
 /* Early/late marker and payload interruptions; transaction preparation itself
  * was byte-identical SRAM at every phase above. Existing writer owns codec. */
 for(cut=0;cut<17000;cut+=127){
  memcpy((void*)save5_test_sram,saved_sram,32768);save5_test_reset_writer();save5_test_fail_after((int)cut);
  (void)save5_store(&live);save5_test_fail_after(-1);save5_test_reset_writer();assert(save5_load(&loaded));
  assert(!memcmp(&loaded.roster,&base.roster,sizeof base.roster)||!memcmp(&loaded.roster,&expected.roster,sizeof expected.roster));
  assert(save5_validate(&loaded));++checks;
 }
}
int main(void){parity();stale_and_cancel();powercuts();printf("PASS %u Magma branch parity, exact-byte stale, cancellation, ownership and interrupted-save checks\n",checks);return 0;}
