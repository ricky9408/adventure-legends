/* Isolated host/ARM typed ledger fixture; direct APIs, never world acquisition. */
#include "magma_quests.h"
#include "magma_s3_fixture.h"
#define REQUIRE(x) do { if (!(x)) return __LINE__; } while (0)
static const unsigned char forms[9]={31,34,37,40,43,46,95,97,99};
static const unsigned char tokens[9]={1,2,16,17,18,19,20,21,22};
static const unsigned char families[9]={11,12,13,14,15,16,36,37,38};
unsigned magma_test_slot(const Save5State *s,unsigned form) {
 unsigned i;for(i=0;i<160;++i)if(s->roster.instances[i].form_id==form)return i;return 160;
}
int magma_test_southern(Save5State *s) {
 unsigned i;
#ifdef SAVE5_HOST_TEST
 save5_test_reset_writer();save5_test_fail_after(-1);save5_test_corrupt_write(-1,0);
 for(i=0;i<32768;++i)save5_test_sram[i]=magma_s3_fixture[i];
#else
 for(i=0;i<32768;++i)((volatile unsigned char*)0x0E000000)[i]=magma_s3_fixture[i];
#endif
 REQUIRE(save5_load(s));REQUIRE(save5_validate(s));return 0;
}
int magma_test_ready(Save5State *s,unsigned q) {
 unsigned bit,mask=magma_quest_mask(q);int result=magma_quest_offer(s,q);
 REQUIRE(result==MAGMA_CHANGED||result==MAGMA_UNCHANGED);
 for(bit=1;bit<=8;bit<<=1)if(mask&bit){result=magma_quest_objective(s,q,bit);REQUIRE(result>=0&&result<=2);}
 REQUIRE(save5_quest_state(&s->quests,q)==SAVE5_QUEST_READY);return 0;
}
int magma_test_completed(Save5State *s,unsigned full) {
 unsigned i,q,slot;REQUIRE(!magma_test_southern(s));
 for(i=38;i<=41;++i)REQUIRE(magma_visit(s,i)==MAGMA_CHANGED);
 for(q=30;q<=31;++q){REQUIRE(!magma_test_ready(s,q));REQUIRE(magma_quest_claim(s,q)==MAGMA_REWARDED);}
 for(i=1;i<=4;i<<=1)REQUIRE(magma_discover(s,i)==(i==4?MAGMA_NOW_READY:MAGMA_CHANGED));
 for(i=2;i<9;++i)REQUIRE(magma_field_recruit(s,tokens[i])==MAGMA_REWARDED);
 REQUIRE(!magma_test_ready(s,32));REQUIRE(magma_quest_claim(s,32)==MAGMA_REWARDED);
 for(i=0;i<9;++i){
  slot=magma_test_slot(s,forms[i]);REQUIRE(slot<160);
  REQUIRE(magma_trial_complete(s,slot,s->roster.instances[slot].instance_id,families[i],1,tokens[i])==MAGMA_REWARDED);
  REQUIRE(creatures_evolve_to(&s->roster,slot,forms[i]+1,0x300,1,1)==CREATURE_EVOLVE_READY);
  if(i<2){
   REQUIRE(magma_trial_complete(s,slot,s->roster.instances[slot].instance_id,families[i],2,tokens[i])==MAGMA_REWARDED);
   REQUIRE(creatures_evolve_to(&s->roster,slot,forms[i]+2,0x300,1,1)==CREATURE_EVOLVE_READY);
  } else if(i<6){
   REQUIRE(magma_branch_recruit(s,tokens[i])==MAGMA_REWARDED);
   slot=magma_test_slot(s,forms[i]);REQUIRE(slot<160);
   REQUIRE(magma_trial_complete(s,slot,s->roster.instances[slot].instance_id,families[i],2,tokens[i])==MAGMA_REWARDED);
   REQUIRE(creatures_evolve_to(&s->roster,slot,forms[i]+2,0x300,1,1)==CREATURE_EVOLVE_READY);
  }
  REQUIRE(save5_validate(s));
 }
 for(q=33;q<38;++q){REQUIRE(!magma_test_ready(s,q));REQUIRE(magma_quest_claim(s,q)==MAGMA_REWARDED);}
 for(i=42;i<=45;++i)REQUIRE(magma_visit(s,i)==MAGMA_CHANGED);
 REQUIRE(magma_anchor(s,38)==MAGMA_CHANGED);REQUIRE(magma_anchor(s,39)==MAGMA_CHANGED);
 REQUIRE(creatures_roster_count(&s->roster)==34);
 if(full)while(creatures_roster_count(&s->roster)<160)REQUIRE(creatures_grant(&s->roster,1,50,100,0,0)<160);
 REQUIRE(save5_validate(s));return 0;
}
int magma_test_full48(Save5State *s) {
 unsigned i,j;for(i=1;i<48;++i){
  unsigned char *p=(unsigned char*)&s->equipment.bag[i];for(j=0;j<sizeof(EquipmentRecord);++j)p[j]=0;
  s->equipment.bag[i].item_id=(unsigned short)(99+i);s->equipment.bag[i].quantity=1;
  s->equipment.seen[(99+i)>>3]|=(unsigned char)(1u<<((99+i)&7));
 }
 s->equipment.equipped[0]=0;for(i=1;i<5;++i)s->equipment.equipped[i]=255;
 REQUIRE(equipment_validate(&s->equipment));REQUIRE(!equipment_catalog_validate());REQUIRE(save5_validate(s));return 0;
}
#ifndef MAGMA_SETUP_ONLY
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stddef.h>
static Save5State state,loaded,bad;
static unsigned char saved[32768];
static unsigned rng=0x4d41474d;
static unsigned next_random(void){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
int main(void){unsigned i,n,invalid=0,valid=0;
 assert(!magma_test_completed(&state,1));assert(save5_store(&state));assert(save5_load(&loaded));
 /* A second linear trial belongs to the intermediate form, never the base. */
 for(n=0;n<2;++n){CreatureInstance *c;unsigned form=n?34:31,slot=magma_test_slot(&state,form+2);
  assert(slot<160);bad=state;c=&bad.roster.instances[slot];c->form_id=(CreatureU8)form;
  c->equipped[0]=(CreatureU8)(n?46:43);c->equipped[1]=0;c->selected_command=0;
  assert(c->trial_flags==3);assert(!creatures_instance_validate(c));
  assert(!creatures_instance_validate_revision(c,5));assert(!save5_validate(&bad));assert(!save5_validate_revision(&bad,5));
  assert(!creatures_has_trial_qualified(c,n?12:11,2));
  memcpy(saved,save5_test_sram,sizeof saved);save5_test_fail_after(-1);
  if(save5_begin(&bad))while(save5_status()==SAVE5_BUSY)save5_step(3072);
  assert(save5_status()==SAVE5_FAILED);assert(!save5_test_write_count());assert(!memcmp(saved,save5_test_sram,sizeof saved));
 }

 assert(!memcmp(&state.roster,&loaded.roster,sizeof state.roster));
 assert(!memcmp(&state.quests,&loaded.quests,sizeof state.quests));
 assert(!memcmp(&state.equipment,&loaded.equipment,sizeof state.equipment));
 for(i=0;i<160;++i){unsigned key;CreatureInstance *c=&state.roster.instances[i];
  for(key=0;key<4;++key)(void)magma_trial_status(&state,i,c->instance_id,creatures_form(c->form_id)->family,key,magma_source_token_for_family(creatures_form(c->form_id)->family));}
 for(n=0;n<1200;++n){unsigned index=next_random()%sizeof state,budget;
  bad=state;((unsigned char*)&bad)[index]^=(unsigned char)(1u<<(next_random()%8));
  memcpy(saved,save5_test_sram,sizeof saved);save5_test_fail_after(-1);
  if(save5_begin(&bad)){for(i=0;save5_status()==SAVE5_BUSY&&i<100000;++i){budget=next_random()%5000;save5_step(budget);assert(save5_test_step_work()<=(budget>3072?3072:budget));}}
  if(save5_status()==SAVE5_DONE){++valid;assert(save5_load(&loaded));assert(save5_validate(&loaded));}
  else{++invalid;assert(!save5_test_write_count());assert(!memcmp(saved,save5_test_sram,sizeof saved));}
 }
 printf("{\"result\":\"PASS\",\"randomized_snapshots\":1200,\"accepted\":%u,\"rejected\":%u,\"roster\":160,\"forms_obtained\":65}\n",valid,invalid);return 0;
}
#endif
