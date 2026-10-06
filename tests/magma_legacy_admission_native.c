/* Actual legacy-region wrappers, current core and real save codec. Synthetic
 * duplicate fixtures are deliberately legal historical collections, not routes. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "regional_quests.h"
#include "northern_quests.h"
#include "southern_quests.h"
static Save5State state,before,loaded;
static unsigned checks,sources_checked;
#define CHECK(x) do { if(!(x)){fprintf(stderr,"check failed line %u: %s\n",__LINE__,#x);assert(x);}++checks; } while(0)
int southern_test_northern(Save5State*);
int southern_test_ready(Save5State*,unsigned);
static const unsigned forms[17]={13,16,19,22,77,73,75,79,85,25,28,81,83,87,89,91,93};
static void fresh(void){
 memset(&state,0,sizeof state);state.campaign.chapter_flags=7;state.campaign.story_seen=10;
 CHECK(creatures_migrate_legacy(&state.roster,7,0));equipment_init(&state.equipment);
 CHECK(save5_validate(&state));CHECK(regional_visit(&state,16)==REGION_QUEST_CHANGED);
}
static void ready_regional(unsigned q){unsigned bit,mask=regional_quest_mask(q);
 CHECK(regional_quest_offer(&state,q)==REGION_QUEST_CHANGED);
 for(bit=1;bit<=4;bit<<=1)if(mask&bit){int r=regional_quest_objective(&state,q,bit);CHECK(r==REGION_QUEST_CHANGED||r==REGION_QUEST_NOW_READY);}
 CHECK(save5_quest_state(&state.quests,q)==SAVE5_QUEST_READY);
}
static void ready_north(unsigned q){unsigned bit,mask=northern_quest_mask(q);
 CHECK(northern_quest_offer(&state,q)==NORTH_CHANGED);
 for(bit=1;bit<=8;bit<<=1)if(mask&bit){int r=northern_quest_objective(&state,q,bit);CHECK(r==NORTH_CHANGED||r==NORTH_NOW_READY);}
 CHECK(save5_quest_state(&state.quests,q)==SAVE5_QUEST_READY);
}
static void setup(unsigned source){
 if(source<7){
  fresh();
  if(source<2){
   if(source==1){ready_regional(2);CHECK(regional_quest_claim(&state,2)==REGION_QUEST_REWARDED);}
   ready_regional(source+2);
  }else{
   CHECK(northern_visit(&state,22)==NORTH_CHANGED);
   if(source==4){ready_north(11);CHECK(northern_quest_claim(&state,11)==NORTH_REWARDED);}
   ready_north(source+9);
  }
 }else{
  CHECK(!southern_test_northern(&state));
  if(source<9)CHECK(!southern_test_ready(&state,source+15));
  else{
   CHECK(southern_visit(&state,31)==SOUTH_CHANGED);
   CHECK(southern_visit(&state,32)==SOUTH_CHANGED);
   CHECK(southern_visit(&state,33)==SOUTH_CHANGED);
   if(source==13){CHECK(!southern_test_ready(&state,29));CHECK(southern_discover(&state,0)==SOUTH_CHANGED);}
   if(source==15){CHECK(!southern_test_ready(&state,28));CHECK(southern_discover(&state,1)==SOUTH_CHANGED);}
  }
 }
 CHECK(save5_validate(&state));CHECK(save5_validate_revision(&state,4));
}
static int claim(unsigned source){
 if(source<2)return regional_quest_claim(&state,source+2);
 if(source<7)return northern_quest_claim(&state,source+9);
 if(source<9)return southern_quest_claim(&state,source+15);
 return southern_field_recruit(&state,source+7);
}
static CreatureCoverage coverage(void){CreatureCoverage c;CHECK(creatures_collection_coverage(&state.roster,&c));return c;}
static void fill_excess(unsigned wanted){CreatureCoverage c=coverage();
 while(c.excess<wanted){CHECK(creatures_grant(&state.roster,1,50,100,0,0)<160);c=coverage();}
 CHECK(c.excess==wanted);CHECK(save5_validate(&state));CHECK(save5_validate_revision(&state,4));
}
static void fill_full(void){
 while(creatures_roster_count(&state.roster)<160)CHECK(creatures_grant(&state.roster,1,50,100,0,0)<160);
 CHECK(save5_validate(&state));CHECK(save5_validate_revision(&state,4));
}
static void unchanged(int got,int expected){CHECK(got==expected);CHECK(!memcmp(&state,&before,sizeof state));}
static void roundtrip(void){
 CHECK(save5_validate(&state));CHECK(save5_store(&state));CHECK(save5_load(&loaded));
 CHECK(!memcmp(&state.roster,&loaded.roster,sizeof state.roster));
 CHECK(!memcmp(&state.quests,&loaded.quests,sizeof state.quests));
 CHECK(!memcmp(&state.equipment,&loaded.equipment,sizeof state.equipment));
}
static void test_source(unsigned source){unsigned budget,slot;CreatureCoverage old,after;
 for(budget=88;budget<=89;++budget){
  /* Missing-family capture improves coverage and remains available at the
   * safe boundary and in a grandfathered over-budget state with physical room. */
  setup(source);fill_excess(budget);old=coverage();before=state;
  CHECK(claim(source)==3);after=coverage();CHECK(after.excess==budget);
  CHECK(after.occupied==old.occupied+1&&after.viable==old.viable+1);
  CHECK(state.roster.next_instance_id==before.roster.next_instance_id+1);
  for(slot=0;slot<160;++slot)if(before.roster.instances[slot].form_id)
   CHECK(!memcmp(&state.roster.instances[slot],&before.roster.instances[slot],sizeof(CreatureInstance)));
  CHECK(save5_validate(&state));CHECK(save5_validate_revision(&state,4));roundtrip();
  /* A spent receipt remains an idempotent success at full capacity. */
  fill_full();before=state;unchanged(claim(source),0);roundtrip();
  /* An unclaimed old source may encounter an already retained ordinary copy.
   * The new redundant reward must refuse before gear/quest/source/ID writes. */
  setup(source);CHECK(creatures_grant(&state.roster,forms[source],50,100,0,0)<160);
  fill_excess(budget);before=state;unchanged(claim(source),6);
  CHECK(save5_validate(&state));CHECK(save5_validate_revision(&state,4));roundtrip();
 }
 setup(source);fill_full();before=state;unchanged(claim(source),5);roundtrip();
 setup(source);state.roster.next_instance_id=0xffffffffu;CHECK(save5_validate(&state));before=state;unchanged(claim(source),-1);
 setup(source);state.roster.instances[1].instance_id=state.roster.instances[0].instance_id;before=state;unchanged(claim(source),-1);
 ++sources_checked;
}
static void mixed_south_gear_tests(void){
 unsigned q=22;
 setup(7);CHECK(creatures_grant(&state.roster,79,50,100,0,0)<160);fill_excess(88);
 CHECK(!equipment_seen(&state.equipment,equipment_reward_item(19)));
 before=state;unchanged(southern_quest_claim(&state,q),SOUTH_RESERVED);
 CHECK(!memcmp(&state.equipment,&before.equipment,sizeof state.equipment));
 /* Below the budget, the same mixed transaction grants exactly one companion
  * plus its authored gear, and then commits the one-time quest receipt. */
 setup(7);CHECK(creatures_grant(&state.roster,79,50,100,0,0)<160);fill_excess(87);
 before=state;CHECK(southern_quest_claim(&state,q)==SOUTH_REWARDED);
 CHECK(coverage().excess==88);CHECK(equipment_seen(&state.equipment,equipment_reward_item(19)));
 CHECK(creatures_roster_count(&state.roster)==creatures_roster_count(&before.roster)+1);
 CHECK(save5_validate(&state));roundtrip();
}
int main(void){unsigned source;
 CHECK(REGION_QUEST_RESERVED==6&&NORTH_RESERVED==6&&SOUTH_RESERVED==6);
 CHECK(REGION_QUEST_FULL==5&&NORTH_FULL==5&&SOUTH_FULL==5);
 for(source=0;source<17;++source)test_source(source);
 mixed_south_gear_tests();
 printf("Legacy admission: %u source routes, %u exact-state checks passed\n",sources_checked,checks);
 return 0;
}
