/* Host-only revision3 codec checks; not native obtainability evidence. */
#include "save5.h"
#include <assert.h>
#include <string.h>
static Save5State state, out, broken;
static unsigned rng=0xC0DE5052u;
static unsigned next(void) { rng^=rng<<13; rng^=rng>>17; rng^=rng<<5; return rng; }
static void finish(unsigned expected) {
    unsigned steps=0;
    while(save5_status()==SAVE5_BUSY) {
        unsigned budget=next()%4097u;
        save5_step(budget);
        assert(save5_test_step_work()<=(budget>3072?3072:budget));
        assert(++steps<1000);
    }
    assert(save5_status()==expected);
}
int main(void) {
    unsigned i,cycle;
    static const unsigned forms[21]={1,2,4,5,7,8,10,11,13,14,16,19,20,22,23,73,74,75,76,77,78};
    static const unsigned masks[22]={7,3,7,7,3,1,1,1,3,7,1,3,7,3,7,7,3,7,7,3,7,15};
    memset(save5_test_sram,255,sizeof save5_test_sram);
    state.campaign.chapter_flags=3;state.campaign.story_seen=10;
    assert(creatures_migrate_legacy(&state.roster,3,0));
    equipment_init(&state.equipment);
    assert(creatures_grant(&state.roster,13,50,100,0,5)==4);
    assert(creatures_grant(&state.roster,16,50,100,0,6)==5);
    for(i=0;i<5;++i) {
        static const unsigned newforms[5]={19,22,73,75,77};
        assert(creatures_grant(&state.roster,newforms[i],50,100,0,7+i)==6+i);
        assert(creatures_mark_trial(&state.roster.instances[6+i],32u<<i));
    }
    for(i=11;i<160;++i)assert(creatures_grant(&state.roster,forms[i%21],50,100,0,0)==i);
    for(i=1;i<EQUIPMENT_AUTHORED_COUNT;++i)
        assert(equipment_claim(&state.equipment,equipment_authored_ids[i],i,0)==EQUIPMENT_OK);
    state.quests.region_flags[0]=1;state.quests.region_flags[1]=255;state.campaign.room=29;
    for(i=0;i<22;++i) {
        assert(save5_quest_set_state(&state.quests,i,SAVE5_QUEST_CLAIMED));
        state.quests.objectives[i]=masks[i];state.quests.rewards[i>>3]|=1u<<(i&7);
    }
    for(cycle=0;cycle<1000;++cycle) {
        if(cycle==400) {
            assert(creatures_mark_trial(&state.roster.instances[4],CREATURE_TRIAL_PAIRED_POOLS));
            assert(creatures_evolve(&state.roster,4,CREATURE_REED_RESTORED,1,1)==CREATURE_EVOLVE_READY);
        }
        if(cycle==500) for(i=6;i<11;++i)
            assert(creatures_evolve(&state.roster,i,CREATURE_NORTH_HARBOR_READY,1,1)==CREATURE_EVOLVE_READY);
        if(cycle%50==0) {
            const CreatureU8 party[4]={4,5,2,3};
            assert(creatures_party_set(&state.roster,party,0));
        } else if(cycle%50==25) {
            const CreatureU8 party[4]={0,1,2,3};
            assert(creatures_party_set(&state.roster,party,0));
        }
        state.roster.instances[cycle%160].cosmetic_seed=next();
        assert(save5_validate(&state));assert(save5_begin(&state));finish(SAVE5_DONE);
        assert(save5_load(&out));
        assert(!memcmp(&state.roster,&out.roster,sizeof state.roster));
        assert(!memcmp(&state.quests,&out.quests,sizeof state.quests));
        assert(!memcmp(&state.equipment,&out.equipment,sizeof state.equipment));
    }
    for(i=4;i<=10;++i) {
        unsigned writes=save5_test_write_count();
        broken=state;
        {unsigned j,family=creatures_form(state.roster.instances[i].form_id)->family;
         for(j=4;j<160;++j)if(creatures_form(broken.roster.instances[j].form_id)->family==family)
             memset(&broken.roster.instances[j],0,sizeof(CreatureInstance));}
        assert(creatures_roster_validate(&broken.roster));
        assert(!save5_validate(&broken));assert(save5_begin(&broken));finish(SAVE5_FAILED);
        assert(save5_test_write_count()==writes);
        assert(save5_load(&out));assert(!memcmp(&state.roster,&out.roster,sizeof state.roster));
    }
    return 0;
}
