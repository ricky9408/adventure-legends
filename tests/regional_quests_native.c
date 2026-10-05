#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "regional_quests.h"
static unsigned checks;
#define CHECK(x) do{assert(x);++checks;}while(0)
static Save5State state,copy,loaded;
static void fresh(unsigned chapter){
    memset(&state,0,sizeof state);state.campaign.chapter_flags=chapter;
    state.campaign.story_seen=(chapter&1?2:0)|(chapter&2?8:0);
    CHECK(creatures_migrate_legacy(&state.roster,chapter,0));equipment_init(&state.equipment);
    CHECK(save5_validate(&state));
}
static void complete(unsigned q){unsigned bit,mask=regional_quest_mask(q);
    CHECK(regional_quest_offer(&state,q)==REGION_QUEST_CHANGED);
    for(bit=1;bit<=4;bit<<=1)if(mask&bit){int result=regional_quest_objective(&state,q,bit);CHECK(result==REGION_QUEST_CHANGED||result==REGION_QUEST_NOW_READY);}
    CHECK(save5_quest_state(&state.quests,q)==SAVE5_QUEST_READY);CHECK(save5_validate(&state));
}
static void roundtrip(void){
    CHECK(save5_validate(&state));CHECK(save5_store(&state));memset(&loaded,0xcc,sizeof loaded);
    CHECK(save5_load(&loaded));CHECK(!memcmp(&state.roster,&loaded.roster,sizeof state.roster));
    CHECK(!memcmp(&state.equipment,&loaded.equipment,sizeof state.equipment));
    CHECK(!memcmp(&state.quests,&loaded.quests,sizeof state.quests));
}
int main(void){unsigned q,i,n,slot;int enabled;
    fresh(0);copy=state;CHECK(regional_visit(&state,16)==REGION_QUEST_LOCKED);CHECK(!memcmp(&copy,&state,sizeof state));
    fresh(7);CHECK(regional_visit(&state,17)==REGION_QUEST_LOCKED);CHECK(regional_anchor(&state,16)==REGION_QUEST_LOCKED);
    CHECK(regional_visit(&state,16)==REGION_QUEST_CHANGED);CHECK(regional_visit(&state,16)==REGION_QUEST_UNCHANGED);
    CHECK(regional_visit(&state,17)==REGION_QUEST_CHANGED);CHECK(regional_anchor(&state,16)==REGION_QUEST_CHANGED);
    CHECK(regional_anchor(&state,17)==REGION_QUEST_CHANGED);CHECK(!regional_can_enter(&state,18));CHECK(!regional_can_enter(&state,19));
    CHECK(regional_claim_rack(&state,EQUIPMENT_LANCE)==REGION_QUEST_REWARDED);
    CHECK(regional_claim_rack(&state,EQUIPMENT_BOW)==REGION_QUEST_REWARDED);copy=state;
    CHECK(regional_claim_rack(&state,EQUIPMENT_LANCE)==REGION_QUEST_UNCHANGED);CHECK(!memcmp(&copy,&state,sizeof state));
    for(q=0;q<128;q++){
        copy=state;CHECK(regional_quest_objective(&state,q,8)==REGION_QUEST_INVALID);CHECK(!memcmp(&copy,&state,sizeof state));
    }
    for(q=0;q<REGION_QUEST_COUNT;q++)if(q!=2&&q!=3&&q!=4&&q!=7&&q!=10){
        complete(q);CHECK(regional_quest_claim(&state,q)==REGION_QUEST_REWARDED);CHECK(save5_validate(&state));copy=state;
        CHECK(regional_quest_claim(&state,q)==REGION_QUEST_UNCHANGED);CHECK(!memcmp(&copy,&state,sizeof state));
        CHECK(regional_quest_objective(&state,q,1)==REGION_QUEST_UNCHANGED);CHECK(!memcmp(&copy,&state,sizeof state));
    }
    complete(2);enabled=creatures_form(13)!=0;copy=state;
    if(!enabled){CHECK(regional_quest_claim(&state,2)==REGION_QUEST_LOCKED);CHECK(!memcmp(&copy,&state,sizeof state));}
    else{
        n=creatures_roster_count(&state.roster);CHECK(regional_quest_claim(&state,2)==REGION_QUEST_REWARDED);
        CHECK(creatures_roster_count(&state.roster)==n+1);CHECK(regional_can_enter(&state,18)&&regional_can_enter(&state,19));
        CHECK(regional_visit(&state,18)==REGION_QUEST_CHANGED);CHECK(regional_visit(&state,19)==REGION_QUEST_CHANGED);roundtrip();
        complete(3);CHECK(regional_quest_claim(&state,3)==REGION_QUEST_REWARDED);roundtrip();
        complete(4);CHECK(regional_quest_claim(&state,4)==REGION_QUEST_REWARDED);roundtrip();
        for(slot=0;slot<160&&state.roster.instances[slot].form_id!=13;slot++){}
        CHECK(slot<160);
        CHECK(state.roster.instances[slot].level==15&&state.roster.instances[slot].bond==45&&state.roster.instances[slot].trial_flags==16);
        copy=state;CHECK(regional_quest_claim(&state,4)==REGION_QUEST_UNCHANGED);CHECK(!memcmp(&copy,&state,sizeof state));
        complete(7);CHECK(regional_quest_claim(&state,7)==REGION_QUEST_REWARDED);
        complete(10);CHECK(regional_quest_claim(&state,10)==REGION_QUEST_REWARDED);CHECK(equipment_count(&state.equipment)==13);roundtrip();
    }
    fresh(7);regional_visit(&state,16);complete(2);
    if(enabled){
        for(i=creatures_roster_count(&state.roster);i<160;i++)CHECK(creatures_grant(&state.roster,1,1,0,0,0)!=255);
        copy=state;CHECK(regional_quest_claim(&state,2)==REGION_QUEST_FULL);CHECK(!memcmp(&copy,&state,sizeof state));CHECK(save5_validate(&state));
    }
    printf("regional quest checks: %u; native Water/Metal catalog %s\n",checks,enabled?"enabled":"pending (no gameplay claim)");return 0;
}
