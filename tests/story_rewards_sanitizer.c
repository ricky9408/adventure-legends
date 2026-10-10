#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "story_rewards.h"
static CreatureRoster base,snapshot,live,expected;
static Save5State state,save_before;
static void reference(CreatureRoster*r,unsigned chapters){unsigned i;for(i=0;i<4;i++)creatures_grant_story(r,i,chapters);creatures_apply_story_floors(r,chapters);}
int main(void){unsigned n,chapter,k,token,status,cases=0;static const unsigned chapters[]={0,1,2,3,7,15,0xffffffffu};
 creatures_roster_init(&base);
 for(n=0;n<=160;n++){
  assert(creatures_roster_validate(&base));
  for(chapter=0;chapter<sizeof chapters/sizeof chapters[0];chapter++){
   snapshot=live=expected=base;reference(&expected,chapters[chapter]);token=creatures_story_job_begin(&snapshot,chapters[chapter]);assert(token);
   for(k=0;k<40;k++){status=(unsigned)creatures_admission_job_step(token,4);assert(status<=1);assert(!memcmp(&live,&base,sizeof live));assert(!memcmp(&snapshot,&base,sizeof snapshot));}
   assert(status==1&&creatures_story_job_commit(token,&live));assert(!memcmp(&live,&expected,sizeof live));assert(creatures_roster_validate(&live));assert(!creatures_story_job_commit(token,&live));cases++;
  }
  if(n<160)assert(creatures_grant(&base,1,1+n%50,n%101,0,0)<160);
 }
 memset(&state,0,sizeof state);equipment_init(&state.equipment);assert(creatures_migrate_legacy(&state.roster,0,0));assert(save5_validate(&state));
 for(n=2;n<160;n++)assert(creatures_grant(&state.roster,1,1+n%50,n%101,0,0)<160);
 assert(save5_validate(&state));save_before=state;expected=state.roster;reference(&expected,7);memset(save5_test_sram,0xa7,32768);
 assert(story_rewards_begin(&state,7));
 for(k=0;k<200;k++){
  status=story_rewards_step();
  if(status!=SAVE5_BUSY)break;
  assert(!memcmp(&state,&save_before,sizeof state));
 }
 assert(status==SAVE5_DONE&&!memcmp(&state.roster,&expected,sizeof expected));assert(save5_validate(&state));
 for(k=0;k<32768;k++)assert(save5_test_sram[k]==0xa7);
 /* Purpose separation and stale exact-source authority remain fail closed. */
 snapshot=live=base;token=creatures_story_job_begin(&snapshot,7);for(k=0;k<40;k++)creatures_admission_job_step(token,4);
 live.instances[159].bond^=1;expected=live;assert(!creatures_story_job_commit(token,&live));assert(!memcmp(&live,&expected,sizeof live));
 token=creatures_story_job_begin(&snapshot,7);for(k=0;k<40;k++)creatures_admission_job_step(token,4);creatures_story_job_cancel(token);assert(!creatures_story_job_commit(token,&live));
 printf("PASS: %u differential bounded story cases + legal160 full-save atomic transaction and no SRAM writes\n",cases);return 0;
}
