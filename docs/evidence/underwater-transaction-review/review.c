/* Independent host-only semantic review. No controller acquisition or timing claim. */
#include "underwater_quests.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
extern int underwater_test_earned34(Save5State *);
extern int underwater_test_recruits(Save5State *);
extern int underwater_test_completed(Save5State *, unsigned);
extern void review_preflight_serial(unsigned);
extern void review_admission_serial(unsigned);
static Save5State seeds[128], a, b, original;
static unsigned seed_count, parity_count, mutant_count, stale_count, commit_count;
static unsigned char old_sram[32768];
static void snapshot(const Save5State *s) {assert(seed_count<128);assert(save5_validate(s));seeds[seed_count++]=*s;}
static int sync_request(Save5State *s,const UnderwaterRequest *r) {
 int result;
 switch(r->operation){
 case UW_REQUEST_VISIT:return underwater_visit(s,r->room);
 case UW_REQUEST_ANCHOR:return underwater_anchor(s,r->room);
 case UW_REQUEST_QUEST_OFFER:return underwater_quest_offer(s,r->quest);
 case UW_REQUEST_QUEST_OBJECTIVE:return underwater_quest_objective(s,r->quest,r->bit);
 case UW_REQUEST_QUEST_PROGRESS:
  /* Define implicit-offer semantics independently from job internals. */
  if(!r->bit||(r->bit&(r->bit-1))||!(r->bit&underwater_quest_mask(r->quest)))return UNDERWATER_INVALID;
  if(!save5_validate(s))return UNDERWATER_INVALID;
  if(!underwater_quest_available(s,r->quest))return UNDERWATER_LOCKED;
  {Save5State staged=*s;
   if(!save5_quest_state(&staged.quests,r->quest)){
    result=underwater_quest_offer(&staged,r->quest);assert(result==UNDERWATER_CHANGED);
   }
   result=underwater_quest_objective(&staged,r->quest,r->bit);
   if(result==UNDERWATER_CHANGED||result==UNDERWATER_NOW_READY)*s=staged;
   return result;
  }
 case UW_REQUEST_QUEST_CLAIM:return underwater_quest_claim(s,r->quest);
 case UW_REQUEST_FIELD_RECRUIT:return underwater_field_recruit(s,r->source);
 case UW_REQUEST_REPEAT_RECRUIT:return underwater_branch_recruit(s,r->source);
 case UW_REQUEST_DISCOVER:return underwater_discover(s,r->family,r->bit);
 case UW_REQUEST_TRIAL_STATUS:return underwater_trial_status(s,r->slot,r->instance_id,r->family,r->key,r->source);
 case UW_REQUEST_TRIAL_COMPLETE:return underwater_trial_complete(s,r->slot,r->instance_id,r->family,r->key,r->source);
 default:return UNDERWATER_INVALID;
 }
}
static void check(const Save5State *base,UnderwaterRequest request) {
 Save4U32 token;unsigned steps=0,phase,state;int wanted,got;
 a=*base;b=*base;original=*base;memcpy(old_sram,save5_test_sram,sizeof old_sram);
 wanted=sync_request(&a,&request);
 token=underwater_job_begin(&b,&request,19);
 if(!token){got=UNDERWATER_INVALID;assert(!memcmp(&b,&original,sizeof b));}
 else{
  /* Original request is no longer owned by caller; mutation cannot redirect. */
  memset(&request,0xA5,sizeof request);
  assert(underwater_job_step(token,0,19)==SAVE5_BUSY);
  assert(!save5_begin(&a));assert(!save5_preflight_begin(&a));
  do{
   phase=underwater_job_phase(token);
   state=underwater_job_step(token,(steps&1)?1024:0xffffffffu,19);
   assert(++steps<400);
   if(phase!=6)assert(!memcmp(&b,&original,sizeof b));
   assert(!memcmp(old_sram,save5_test_sram,sizeof old_sram));
  }while(state==SAVE5_BUSY);
  got=underwater_job_result(token);
  if(state==SAVE5_DONE){
   assert(!save5_preflight_active());original=b;
   assert(underwater_job_step(token,1024,19)==SAVE5_DONE);
   assert(!memcmp(&b,&original,sizeof b));
  }else assert(state==SAVE5_FAILED && got==UNDERWATER_INVALID);
 }
 if(wanted!=got||memcmp(&a,&b,sizeof a)){
  fprintf(stderr,"parity failure case %u wanted %d got %d token %u\n",parity_count,wanted,got,token);abort();
 }
 underwater_job_cancel();++parity_count;
}
static void enact(UnderwaterRequest request) {
 check(&b,request);assert(underwater_job_status(0)==SAVE5_FAILED);snapshot(&b);
}
static UnderwaterRequest req(unsigned op){UnderwaterRequest r;memset(&r,0,sizeof r);r.operation=op;return r;}
static void build_seeds(void) {
 UnderwaterRequest r;unsigned room,q,bit,i,key,slot;
 assert(!underwater_test_earned34(&b));snapshot(&b);
 for(room=46;room<=49;++room){r=req(UW_REQUEST_VISIT);r.room=room;enact(r);}
 for(room=46;room<=47;++room){r=req(UW_REQUEST_ANCHOR);r.room=room;enact(r);}
 for(q=38;q<=40;++q){
  for(bit=1;bit<=8;bit<<=1)if(underwater_quest_mask(q)&bit){r=req(UW_REQUEST_QUEST_PROGRESS);r.quest=q;r.bit=bit;enact(r);}
  r=req(UW_REQUEST_QUEST_CLAIM);r.quest=q;enact(r);
 }
 for(room=50;room<=53;++room){r=req(UW_REQUEST_VISIT);r.room=room;enact(r);}
 for(i=23;i<=24;++i)for(bit=1;bit<=(i==23?2u:4u);bit<<=1){r=req(UW_REQUEST_DISCOVER);r.family=i;r.bit=bit;enact(r);}
 for(i=3;i<=8;++i){r=req(UW_REQUEST_FIELD_RECRUIT);r.source=i;enact(r);}
 for(i=0;i<8;++i)for(key=1;key<=2;++key){
  if(key==2){r=req(UW_REQUEST_REPEAT_RECRUIT);r.source=i+1;enact(r);}
  for(slot=0;slot<160;++slot)if(b.roster.instances[slot].form_id==49+3*i)break;
  assert(slot<160);r=req(UW_REQUEST_TRIAL_COMPLETE);r.source=i+1;r.slot=slot;r.instance_id=b.roster.instances[slot].instance_id;r.family=17+i;r.key=key;enact(r);
  assert(creatures_evolve_to(&b.roster,slot,49+3*i+key,underwater_context(&b),1,1)==CREATURE_EVOLVE_READY);snapshot(&b);
 }
 for(q=41;q<=45;++q){
  r=req(UW_REQUEST_QUEST_OFFER);r.quest=q;enact(r);
  for(bit=1;bit<=8;bit<<=1)if(underwater_quest_mask(q)&bit){r=req(UW_REQUEST_QUEST_OBJECTIVE);r.quest=q;r.bit=bit;enact(r);}
  r=req(UW_REQUEST_QUEST_CLAIM);r.quest=q;enact(r);
 }
 assert(creatures_roster_count(&b.roster)==50);
 assert(!underwater_test_completed(&b,1));snapshot(&b);
 b.roster.next_instance_id=0xffffffffu;snapshot(&b);
}
static void request_grid(void) {
 unsigned si,op,v,bit,slot;UnderwaterRequest r;
 for(si=0;si<seed_count;++si){
  for(op=1;op<=2;++op)for(v=45;v<=54;++v){r=req(op);r.room=v;check(&seeds[si],r);}
  for(op=3;op<=6;++op)for(v=37;v<=46;++v){
   r=req(op);r.quest=v;
   if(op==4||op==5){for(bit=0;bit<=17;++bit){r.bit=bit;check(&seeds[si],r);}}
   else check(&seeds[si],r);
  }
  for(op=7;op<=8;++op)for(v=0;v<=9;++v){r=req(op);r.source=v;check(&seeds[si],r);}
  for(v=22;v<=25;++v)for(bit=0;bit<=8;++bit){r=req(9);r.family=v;r.bit=bit;check(&seeds[si],r);}
  for(slot=0;slot<160;++slot)if(seeds[si].roster.instances[slot].form_id>=49&&seeds[si].roster.instances[slot].form_id<=72){
   for(op=10;op<=11;++op)for(v=0;v<=3;++v){
    r=req(op);r.slot=slot;r.instance_id=seeds[si].roster.instances[slot].instance_id;
    r.family=creatures_form(seeds[si].roster.instances[slot].form_id)->family;r.source=r.family-16;r.key=v;check(&seeds[si],r);
    ++r.instance_id;check(&seeds[si],r);
   }
  }
 }
}
static void preflight_parity(void) {
 unsigned si,offset,mask,state,step,want;Save4U32 token;const Save5State *snap;
 static const unsigned variants[]={0,30,90,0xffffffffu};
 for(si=0;si<4;++si){unsigned seed=variants[si]==0xffffffffu?seed_count-2:variants[si];assert(seed<seed_count);
  for(offset=0;offset<sizeof a;++offset)for(mask=1;mask<=128;mask<<=1){
   a=seeds[seed];((unsigned char*)&a)[offset]^=(unsigned char)mask;original=a;want=(unsigned)save5_validate(&a);
   token=save5_preflight_begin(&a);assert(token);assert(save5_preflight_step(token,0)==SAVE5_BUSY);
   step=0;do{state=save5_preflight_step(token,(step%3==0)?1:(step%3==1)?1024:0xffffffffu);assert(++step<400);}while(state==SAVE5_BUSY);
   assert(state==(want?SAVE5_DONE:SAVE5_FAILED));assert(!memcmp(&a,&original,sizeof a));
   snap=save5_preflight_snapshot(token);assert(!!snap==!!want);
   if(want){assert(!memcmp(snap,&a,sizeof a));assert(save5_preflight_matches(token,&a));b=a;assert(!save5_preflight_matches(token,&b));}
   save5_preflight_cancel();assert(!save5_preflight_snapshot(token));++mutant_count;
  }
 }
}
static void stale_full_state(void) {
 unsigned offset,state,steps,op;UnderwaterRequest r;Save4U32 token;
 for(op=0;op<3;++op)for(offset=0;offset<sizeof a;++offset){
  if(op==0){a=seeds[seed_count-3];r=req(UW_REQUEST_REPEAT_RECRUIT);r.source=1;}
  else if(op==1){a=seeds[0];r=req(UW_REQUEST_VISIT);r.room=46;}
  else{a=seeds[seed_count-4];r=req(UW_REQUEST_QUEST_CLAIM);r.quest=45;}
  token=underwater_job_begin(&a,&r,29);assert(token);steps=0;
  while(underwater_job_phase(token)!=6){assert(underwater_job_step(token,1024,29)==SAVE5_BUSY);assert(++steps<400);}
  ((unsigned char*)&a)[offset]^=1;original=a;memcpy(old_sram,save5_test_sram,sizeof old_sram);
  state=underwater_job_step(token,1024,29);assert(state==SAVE5_FAILED);
  assert(!memcmp(&a,&original,sizeof a));assert(!memcmp(old_sram,save5_test_sram,sizeof old_sram));++stale_count;
 }
}
static int same_payload(const Save5State *x,const Save5State *y){
 return x->campaign.room==y->campaign.room&&x->campaign.spawn==y->campaign.spawn&&
  x->campaign.chapter_flags==y->campaign.chapter_flags&&x->campaign.bridge==y->campaign.bridge&&
  x->campaign.torches==y->campaign.torches&&x->campaign.relic==y->campaign.relic&&x->campaign.camp==y->campaign.camp&&
  x->campaign.room_flags==y->campaign.room_flags&&x->campaign.optional_flags==y->campaign.optional_flags&&
  x->campaign.story_seen==y->campaign.story_seen&&x->campaign.spirit==y->campaign.spirit&&
  !memcmp(&x->roster,&y->roster,sizeof x->roster)&&!memcmp(&x->quests,&y->quests,sizeof x->quests)&&
  !memcmp(&x->equipment,&y->equipment,sizeof x->equipment);
}
static unsigned bank_checks;
static void bank_roundtrip(void){
 static unsigned char initial[32768],bank[SAVE5_BANK_SIZE];
 static Save5State old,newer,out;
 unsigned dest,cut,i,budget,step;Save4U32 token,expected_crc;UnderwaterRequest r;
 old=seeds[0];newer=old;r=req(UW_REQUEST_VISIT);r.room=46;
 token=underwater_job_begin(&newer,&r,33);assert(token);
 while(underwater_job_step(token,1024,33)==SAVE5_BUSY){}
 assert(underwater_job_result(token)==UNDERWATER_CHANGED);underwater_job_cancel();assert(save5_validate(&newer));
 for(dest=0;dest<2;++dest){
  save5_test_reset_writer();save5_test_fail_after(-1);memset(save5_test_sram,255,32768);assert(save5_store(&old));
  if(dest)assert(save5_store(&old));
  memcpy(initial,save5_test_sram,32768);
  assert(save5_begin(&newer));step=0;
  while(save5_status()==SAVE5_BUSY){
   budget=step%4==0?1:step%4==1?64:step%4==2?1024:0xffffffffu;
   assert(!save5_preflight_begin(&old));assert(!underwater_job_begin(&old,&r,33));
   assert(!save5_load(&out));save5_step(budget);assert(save5_test_step_work()<=(budget<3072?budget:3072));assert(++step<1000);
  }
  assert(save5_status()==SAVE5_DONE);assert(save5_load(&out));assert(same_payload(&out,&newer));
  memcpy(bank,save5_test_sram+(dest?SAVE5_BANK_A:SAVE5_BANK_B),sizeof bank);
  expected_crc=(Save4U32)bank[16]|((Save4U32)bank[17]<<8)|((Save4U32)bank[18]<<16)|((Save4U32)bank[19]<<24);
  assert(bank[20]==SAVE5_COMMIT);memset(bank+16,0,5);assert(save5_crc32(bank,sizeof bank)==expected_crc);
  for(cut=0;cut<SAVE5_BANK_SIZE+2;++cut){
   save5_test_reset_writer();save5_test_fail_after((int)cut);memcpy(save5_test_sram,initial,32768);
   assert(save5_store(&newer)==(cut>=SAVE5_BANK_SIZE+1));assert(save5_load(&out));
   assert(same_payload(&out,cut>=SAVE5_BANK_SIZE+1?&newer:&old));
   assert(!memcmp(save5_test_sram,initial,SAVE5_BANK_A));
   i=dest?SAVE5_BANK_B:SAVE5_BANK_A;assert(!memcmp(save5_test_sram+i,initial+i,SAVE5_BANK_SIZE));++bank_checks;
  }
  for(i=0;i<7;++i){static const int corrupt[]={0,1,16,160,4000,6143,6144};
   save5_test_reset_writer();save5_test_fail_after(-1);memcpy(save5_test_sram,initial,32768);save5_test_corrupt_write(corrupt[i],1);
   assert(!save5_store(&newer));assert(save5_load(&out));assert(same_payload(&out,&old));save5_test_corrupt_write(-1,0);++bank_checks;
  }
 }
 save5_test_fail_after(-1);
}
static void token_interleavings(void) {
 UnderwaterRequest r;Save4U32 token,old;unsigned phase,steps,st;
 r=req(UW_REQUEST_REPEAT_RECRUIT);r.source=1;
 for(phase=0;phase<=6;++phase){
  for(st=0;st<3;++st){
   a=seeds[seed_count-3];original=a;token=underwater_job_begin(&a,&r,7);assert(token);steps=0;
   while(underwater_job_phase(token)<phase){assert(underwater_job_step(token,1024,7)==SAVE5_BUSY);assert(++steps<400);}
   if(underwater_job_phase(token)!=phase){underwater_job_cancel();continue;}
   if(st==0){underwater_job_cancel();assert(underwater_job_step(token,1024,7)!=SAVE5_DONE);}
   else if(st==1)assert(underwater_job_step(token,1024,8)==SAVE5_FAILED);
   else {assert(save5_load(&b));assert(underwater_job_step(token,1024,7)==SAVE5_FAILED);}
   assert(!memcmp(&a,&original,sizeof a));++commit_count;
  }
 }
 a=seeds[seed_count-3];token=underwater_job_begin(&a,&r,7);assert(token);old=token;underwater_job_cancel();
 token=underwater_job_begin(&a,&r,7);assert(token&&token!=old);assert(underwater_job_step(old,1024,7)==SAVE5_FAILED);
 while(underwater_job_step(token,1024,7)==SAVE5_BUSY){}assert(underwater_job_result(token)==UNDERWATER_REWARDED);underwater_job_cancel();
 /* Test-only wrappers set private counters in isolated compilation only. */
 review_preflight_serial(0xfffffffeu);token=save5_preflight_begin(&a);assert(token==0xffffffffu);save5_preflight_cancel();assert(!save5_preflight_begin(&a));assert(save5_preflight_status(token)==SAVE5_IDLE);
 review_admission_serial(0xfffffffeu);token=creatures_admission_job_begin(&a.roster,49,255);assert(token==0xffffffffu);creatures_admission_job_cancel();assert(!creatures_admission_job_begin(&a.roster,49,255));
}
int main(void){build_seeds();request_grid();preflight_parity();stale_full_state();bank_roundtrip();token_interleavings();printf("{\"seed_states\":%u,\"transaction_parity\":%u,\"preflight_bit_mutants\":%u,\"full_state_stale_denials\":%u,\"phase_interleavings\":%u,\"bank_atomic_checks\":%u,\"save_bytes\":%u,\"status\":\"pass\"}\n",seed_count,parity_count,mutant_count,stale_count,commit_count,bank_checks,(unsigned)sizeof a);return 0;}
