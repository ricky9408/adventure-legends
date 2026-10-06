/* Synthetic typed setup atop an authenticated native Magma fixture. This is
 * host/isolated-ARM proof only, never Underwater controller acquisition proof. */
#include "underwater_quests.h"
#include "underwater_magma_fixture.h"
int underwater_test_earned34(Save5State *s) {
 unsigned i;
#ifdef SAVE5_HOST_TEST
 save5_test_reset_writer();save5_test_fail_after(-1);
 for(i=0;i<32768;++i)save5_test_sram[i]=underwater_magma_fixture[i];
#else
 for(i=0;i<32768;++i)((volatile unsigned char*)0x0e000000)[i]=underwater_magma_fixture[i];
#endif
 return save5_load(s)?0:1;
}
int underwater_test_ready(Save5State *s,unsigned q) {
 unsigned bit;int result=underwater_quest_offer(s,q);
 if(result!=UNDERWATER_CHANGED&&result!=UNDERWATER_UNCHANGED)return 2;
 for(bit=1;bit<=8;bit<<=1)if(underwater_quest_mask(q)&bit){
  result=underwater_quest_objective(s,q,bit);
  if(result!=UNDERWATER_CHANGED&&result!=UNDERWATER_UNCHANGED&&result!=UNDERWATER_NOW_READY)return 3;
 }
 return 0;
}
static int claim(Save5State *s,unsigned q) {
 int result=underwater_test_ready(s,q);if(result)return result;
 return underwater_quest_claim(s,q)==UNDERWATER_REWARDED?0:4;
}
int underwater_test_recruits(Save5State *s) {
 unsigned i;int result=underwater_test_earned34(s);if(result)return result;
 for(i=46;i<=49;++i)if(underwater_visit(s,i)!=UNDERWATER_CHANGED)return 5;
 if(claim(s,38)||claim(s,39)||claim(s,40))return 6;
 for(i=50;i<=53;++i)if(underwater_visit(s,i)!=UNDERWATER_CHANGED)return 7;
 for(i=1;i<=4;i<<=1){if(i<4&&underwater_discover(s,23,i)<1)return 8;
  if(underwater_discover(s,24,i)<1)return 9;}
 for(i=3;i<=8;++i)if(underwater_field_recruit(s,i)!=UNDERWATER_REWARDED)return 10;
 return save5_validate(s)?0:11;
}
unsigned underwater_test_slot(const Save5State *s,unsigned form) {
 unsigned i;for(i=0;i<160;++i)if(s->roster.instances[i].form_id==form)return i;
 return 255;
}
int underwater_test_completed(Save5State *s,unsigned full) {
 unsigned i,key,slot;int result=underwater_test_recruits(s);if(result)return result;
 for(i=0;i<8;++i)for(key=1;key<=2;++key){
  if(key==2&&underwater_branch_recruit(s,i+1)!=UNDERWATER_REWARDED)return 12;
  slot=underwater_test_slot(s,49+3*i);if(slot==255)return 13;
  if(underwater_trial_complete(s,slot,s->roster.instances[slot].instance_id,17+i,key,i+1)!=UNDERWATER_REWARDED)return 14;
  if(creatures_evolve_to(&s->roster,slot,49+3*i+key,underwater_context(s),1,1)!=0)return 15;
 }
 for(i=41;i<46;++i)if(claim(s,i))return 16;
 if(full)while(creatures_roster_count(&s->roster)<160){
  /* Deliberately grandfathered synthetic stress. Not an admission bypass in
   * production and not evidence of obtaining 110 extra individuals in play. */
  if(creatures_grant(&s->roster,1,50,100,0,0)==255)return 17;
 }
 return save5_validate(s)?0:18;
}
