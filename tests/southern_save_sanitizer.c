/* Southern host/ARM codec fixtures. This is not native acquisition evidence.
 * The pinned Northern controller save is loaded, then Southern event helpers
 * are called directly. Every trial trains and evolves its same instance. */
#include "southern_quests.h"
#include "southern_n5_fixture.h"
#define REQUIRE(x) do { if (!(x)) return __LINE__; } while (0)
static const unsigned char south_forms[10]={79,85,25,28,81,83,87,89,91,93};
static const unsigned char south_tokens[10]={1,2,16,17,18,19,20,21,22,23};
static const unsigned char south_families[10]={28,31,9,10,29,30,32,33,34,35};
static const unsigned char south_levels[10]={20,20,20,22,22,22,24,22,24,22};
static const unsigned char south_bonds[10]={40,40,40,45,45,45,45,45,45,45};
unsigned southern_test_slot(const Save5State *s,unsigned form) {
    unsigned i;
    for(i=0;i<160;++i)if(s->roster.instances[i].form_id==form)return i;
    return 160;
}
int southern_test_northern(Save5State *s) {
    unsigned i;
#ifdef SAVE5_HOST_TEST
    save5_test_reset_writer();save5_test_fail_after(-1);save5_test_corrupt_write(-1,0);
    for(i=0;i<32768;++i)save5_test_sram[i]=southern_n5_fixture[i];
#else
    for(i=0;i<32768;++i)((volatile unsigned char *)0x0E000000)[i]=southern_n5_fixture[i];
#endif
    REQUIRE(save5_load(s));
    REQUIRE(southern_visit(s,30)==SOUTH_CHANGED);
    return 0;
}
int southern_test_ready(Save5State *s,unsigned q) {
    unsigned bit,mask=southern_quest_mask(q);
    int result=southern_quest_offer(s,q);
    REQUIRE(result==SOUTH_CHANGED||result==SOUTH_UNCHANGED);
    for(bit=1;bit<=8;bit<<=1)if(mask&bit) {
        result=southern_quest_objective(s,q,bit);
        REQUIRE(result>=SOUTH_UNCHANGED&&result<=SOUTH_NOW_READY);
    }
    REQUIRE(save5_quest_state(&s->quests,q)==SAVE5_QUEST_READY);
    return 0;
}
int southern_test_completed(Save5State *s,unsigned full) {
    static const unsigned char old_forms[21]={1,2,4,5,7,8,10,11,13,14,16,19,20,22,23,73,74,75,76,77,78};
    unsigned i,q,slot,filled;
    REQUIRE(!southern_test_northern(s));
    for(i=31;i<=33;++i)REQUIRE(southern_visit(s,i)==SOUTH_CHANGED);
    for(q=22;q<24;++q) {
        REQUIRE(!southern_test_ready(s,q));
        REQUIRE(southern_quest_claim(s,q)==SOUTH_REWARDED);
    }
    REQUIRE(!southern_test_ready(s,29));REQUIRE(southern_discover(s,0)==SOUTH_CHANGED);
    REQUIRE(!southern_test_ready(s,28));REQUIRE(southern_discover(s,1)==SOUTH_CHANGED);
    for(i=2;i<10;++i)REQUIRE(southern_field_recruit(s,south_tokens[i])==SOUTH_REWARDED);
    for(i=0;i<10;++i) {
        CreatureInstance *c;
        slot=southern_test_slot(s,south_forms[i]);REQUIRE(slot<160);
        c=&s->roster.instances[slot];
        REQUIRE(southern_trial_complete(s,slot,c->instance_id,south_families[i],1,south_tokens[i])==SOUTH_REWARDED);
        REQUIRE(c->trial_flags==1&&c->level>=south_levels[i]&&c->bond>=south_bonds[i]);
        REQUIRE(creatures_evolve(&s->roster,slot,CREATURE_SOUTH_READY,1,1)==CREATURE_EVOLVE_READY);
        REQUIRE(save5_validate(s));
    }
    for(q=24;q<30;++q) {
        REQUIRE(!southern_test_ready(s,q));REQUIRE(southern_quest_claim(s,q)==SOUTH_REWARDED);
    }
    for(i=34;i<=37;++i)REQUIRE(southern_visit(s,i)==SOUTH_CHANGED);
    REQUIRE(southern_anchor(s,30)==SOUTH_CHANGED);REQUIRE(southern_anchor(s,31)==SOUTH_CHANGED);
    s->campaign.room=37;s->campaign.spawn=0;
    if(full) {
        /* Retain physical copies of every form, not only collection bits. */
        for(i=0;i<21;++i)if(southern_test_slot(s,old_forms[i])==160)
            REQUIRE(creatures_grant(&s->roster,old_forms[i],50,100,0,0)<160);
        for(i=0;i<10;++i)REQUIRE(creatures_grant(&s->roster,south_forms[i],50,100,0,0)<160);
        for(filled=0;filled<160;++filled)if(!s->roster.instances[filled].form_id)break;
        for(i=filled;i<160;++i)REQUIRE(creatures_grant(&s->roster,old_forms[i%21],50,100,0,0)==i);
    }
    REQUIRE(save5_validate(s));
    return 0;
}
int southern_test_full48(Save5State *s) {
    unsigned i,j;
    /* Keep authored collection/reward history; replace only live bag entries. */
    for(i=1;i<48;++i) {
        unsigned char *p=(unsigned char *)&s->equipment.bag[i];
        for(j=0;j<sizeof(EquipmentRecord);++j)p[j]=0;
        s->equipment.bag[i].item_id=(unsigned short)(99+i);
        s->equipment.bag[i].quantity=1;
        s->equipment.seen[(99+i)>>3]|=(unsigned char)(1u<<((99+i)&7));
    }
    s->equipment.equipped[0]=0;
    for(i=1;i<5;++i)s->equipment.equipped[i]=EQUIPMENT_EMPTY_REF;
    REQUIRE(equipment_validate(&s->equipment));
    REQUIRE(!equipment_catalog_validate());
    REQUIRE(save5_validate(s));
    return 0;
}
#ifndef SOUTHERN_SETUP_ONLY
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
static Save5State state,out,broken;
static unsigned char previous[32768];
static unsigned rng=0x504F5554u,steps_total,zero_budgets,capped_budgets;
static void verify_roundtrip(void) {
    /* Sequence/version are output-only metadata, not caller-save payload. */
    assert(!memcmp(&state.campaign,&out.campaign,offsetof(CampaignSave,sequence)));
    assert(!memcmp(&state.roster,&out.roster,sizeof state.roster));
    assert(!memcmp(&state.quests,&out.quests,sizeof state.quests));
    assert(!memcmp(&state.equipment,&out.equipment,sizeof state.equipment));
}
static unsigned next_random(void) { rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng; }
static void finish(unsigned expected) {
    unsigned steps=0;
    while(save5_status()==SAVE5_BUSY) {
        unsigned budget=steps==0?0:steps==1?4096:next_random()%8193u;
        unsigned cap=budget>3072?3072:budget;
        save5_step(budget);assert(save5_test_step_work()<=cap);
        zero_budgets+=budget==0;capped_budgets+=budget>3072;
        assert(++steps<2000);
    }
    steps_total+=steps;assert(save5_status()==expected);
}
int main(void) {
    unsigned cycle,i,j,writes,invalid_count=0;
    assert(!southern_test_completed(&state,1));
    assert(equipment_catalog_validate());
    for(cycle=0;cycle<1200;++cycle) {
        if(cycle%50==0) {
            const CreatureU8 party[4]={11,12,13,14};
            assert(creatures_party_set(&state.roster,party,0));
        } else if(cycle%50==25) {
            const CreatureU8 party[4]={0,1,2,3};
            assert(creatures_party_set(&state.roster,party,0));
        }
        state.roster.instances[cycle%160].cosmetic_seed=next_random();
        state.roster.expedition_events[(cycle/8)%64]^=(unsigned char)(1u<<(cycle%8));
        assert(save5_validate(&state));assert(save5_begin(&state));finish(SAVE5_DONE);
        assert(save5_load(&out));verify_roundtrip();
    }
    /* Wrong floors, trial keys, identities and typed source history never write.
     * A high-floor second copy cannot compensate for the invalid first copy. */
    for(cycle=0;cycle<1200;++cycle) {
        unsigned which=cycle%16,form_index=(cycle/16)%10;
        unsigned slot=southern_test_slot(&state,south_forms[form_index]+1u);
        assert(slot<160);broken=state;
        switch(which) {
        case 0:broken.roster.instances[slot].bond=(unsigned char)(south_bonds[form_index]-1);break;
        case 1:broken.roster.instances[slot].level=(unsigned char)(south_levels[form_index]-1);
               broken.roster.instances[slot].xp=creatures_xp_threshold(broken.roster.instances[slot].level);break;
        case 2:broken.roster.instances[slot].trial_flags=0;break;
        case 3:broken.roster.instances[slot].trial_flags=2;break;
        case 4:broken.roster.instances[slot].instance_id=broken.roster.instances[0].instance_id;break;
        case 5:broken.roster.instances[slot].selected_command=255;break;
        case 6:broken.quests.region_flags[8]&=(unsigned char)~(1u<<(form_index%8));break;
        case 7:broken.quests.region_flags[18]&=(unsigned char)~(1u<<(form_index%2));break;
        case 8:broken.quests.region_flags[2]&=(unsigned char)~1u;break;
        case 9:broken.quests.objectives[24]=5;break;
        case 10:broken.quests.anchors[2]|=128;break;
        case 11:broken.campaign.spawn=1;break;
        case 12:broken.equipment.bag[1].item_id=broken.equipment.bag[0].item_id;
                broken.equipment.bag[1].flags=broken.equipment.bag[0].flags;break;
        case 13:broken.equipment.reserved[cycle%24]=1;break;
        case 14:broken.quests.rewards[3]^=1;break;
        default:
            for(i=0;i<160;++i) {
                if(broken.roster.instances[i].form_id==south_forms[form_index]||
                   broken.roster.instances[i].form_id==south_forms[form_index]+1u)
                    memset(&broken.roster.instances[i],0,sizeof(CreatureInstance));
            }
            break;
        }
        assert(!save5_validate(&broken));writes=save5_test_write_count();
        for(j=0;j<32768;++j)previous[j]=save5_test_sram[j];
        if(save5_begin(&broken))finish(SAVE5_FAILED);
        assert(save5_status()==SAVE5_FAILED);assert(save5_test_write_count()==writes);
        for(j=0;j<32768;++j)assert(previous[j]==save5_test_sram[j]);
        assert(save5_load(&out));verify_roundtrip();++invalid_count;
    }
    printf("{\"valid_roundtrips\":1200,\"invalid_snapshots\":%u,\"random_budget_steps\":%u,"
           "\"zero_budget_calls\":%u,\"above_cap_budget_calls\":%u,\"seed\":1347376468}\n",
           invalid_count,steps_total,zero_budgets,capped_budgets);
    return 0;
}
#endif
