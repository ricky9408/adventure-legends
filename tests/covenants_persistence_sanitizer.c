/* Host adversarial save/transaction harness; never native gameplay evidence. */
#include "covenants_quests.h"
#include <assert.h>
#include <string.h>
#include "covenants-seeds.h"
static Save5State state,before;
static unsigned random_state=0x9128u;
static unsigned random_next(void){random_state^=random_state<<13;random_state^=random_state>>17;random_state^=random_state<<5;return random_state;}
static unsigned preflight(Save5State*s){unsigned token=save5_preflight_begin(s),status=SAVE5_BUSY,k=0;assert(token);
 while(status==SAVE5_BUSY){unsigned phase=save5_preflight_phase(token);assert(++k<3000);assert(save5_preflight_step(token,0)==SAVE5_BUSY);assert(save5_preflight_phase(token)==phase);status=save5_preflight_step(token,1u<<(k%12));}
 save5_preflight_cancel();return status;
}
int main(void){unsigned n,i;
 assert(sizeof state==sizeof covenants_old);assert(sizeof state==sizeof covenants_full);
 for(n=0;n<12000;++n){unsigned valid;memcpy(&state,n&1?covenants_full:covenants_old,sizeof state);
  if(n%7)for(i=0;i<1+n%4;++i)((unsigned char*)&state)[random_next()%sizeof state]=(unsigned char)random_next();
  before=state;valid=save5_validate(&state);assert(preflight(&state)==(valid?SAVE5_DONE:SAVE5_FAILED));assert(!memcmp(&state,&before,sizeof state));
 }
 for(n=0;n<8192;++n){CovenantsRequest r={0};unsigned token,status,step=0;
  memcpy(&state,covenants_old,sizeof state);before=state;
  r.operation=random_next()%12;r.source=random_next()%512;r.room=random_next()%512;r.quest=random_next()%512;r.bit=random_next();
  token=covenants_job_begin(&state,&r,n+1,1);
  if(token){status=SAVE5_BUSY;while(status==SAVE5_BUSY){assert(++step<3000);status=covenants_job_step(token,1024,n+1,1);}covenants_job_cancel();}
  assert(!memcmp(&state,&before,sizeof state));
 }
 /* Whole-width APIs must fail closed before shifts and table access. */
 for(n=0;n<8192;++n){unsigned key=random_next();memcpy(&state,covenants_full,sizeof state);
  (void)covenants_source_form(key);(void)covenants_source_family(key);(void)covenants_source_room(key);
  (void)covenants_can_enter(&state,key);(void)covenants_quest_mask(key);(void)covenants_quest_available(&state,key);
  (void)covenants_fulfilled(&state,key);(void)covenants_source_claimed(&state,key);
 }
 memcpy(&state,covenants_full,sizeof state);assert(save5_validate(&state));
 save5_test_fail_after(-1);memset(save5_test_sram,255,sizeof save5_test_sram);assert(save5_store(&state));
 memset(&before,0,sizeof before);assert(save5_load(&before));assert(!memcmp(&state.roster,&before.roster,sizeof state.roster));
 return 0;
}
