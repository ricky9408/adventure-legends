#include "regional_quests.h"
static const unsigned char masks[REGION_QUEST_COUNT]={7,3,7,7,3,1,1,1,3,7,1};
static int town_open(const Save5State*s){
    return s && (s->campaign.chapter_flags&SAVE4_GROVE_CLEAR) && (s->quests.region_flags[0]&1u);
}
static int claimed(const Save5State*s,unsigned q){return save5_quest_state(&s->quests,q)==SAVE5_QUEST_CLAIMED;}
unsigned regional_quest_mask(unsigned q){return q<REGION_QUEST_COUNT?masks[q]:0;}
int regional_can_enter(const Save5State*s,unsigned room){
    if(!s||room<REGION_FIRST_ROOM||room>REGION_LAST_ROOM||!(s->campaign.chapter_flags&SAVE4_GROVE_CLEAR))return 0;
    if(room==REGION_FIRST_ROOM)return 1;
    if(!town_open(s))return 0;
    return (room!=18&&room!=19)||claimed(s,REGION_QUEST_WATER_BOND);
}
int regional_visit(Save5State*s,unsigned room){
    unsigned bit;if(!regional_can_enter(s,room))return REGION_QUEST_LOCKED;
    bit=1u<<(room-REGION_FIRST_ROOM);
    if(s->quests.region_flags[0]&bit)return REGION_QUEST_UNCHANGED;
    s->quests.region_flags[0]=(Save4U8)(s->quests.region_flags[0]|bit);return REGION_QUEST_CHANGED;
}
int regional_anchor(Save5State*s,unsigned room){
    unsigned bit;if(!s||(room!=16&&room!=17))return REGION_QUEST_INVALID;
    if(!town_open(s)||!(s->quests.region_flags[0]&(1u<<(room-16))))return REGION_QUEST_LOCKED;
    bit=1u<<(room-16);if(s->quests.anchors[0]&bit)return REGION_QUEST_UNCHANGED;
    s->quests.anchors[0]=(Save4U8)(s->quests.anchors[0]|bit);return REGION_QUEST_CHANGED;
}
int regional_quest_available(const Save5State*s,unsigned q){
    if(!town_open(s)||q>=REGION_QUEST_COUNT)return 0;
    if(q==REGION_QUEST_METAL_BOND||q==REGION_QUEST_TIDE_POOLS)return claimed(s,REGION_QUEST_WATER_BOND);
    if(q==REGION_QUEST_LATCH||q==REGION_QUEST_RING)return claimed(s,REGION_QUEST_METAL_BOND);
    if(q==REGION_QUEST_FRIENDSHIPS)return (s->campaign.chapter_flags&SAVE4_CORE_CLEAR)!=0;
    if(q==REGION_QUEST_MAIL)return (s->campaign.chapter_flags&SAVE4_SKY_CLEAR)!=0;
    return 1;
}
int regional_quest_offer(Save5State*s,unsigned q){
    if(q>=REGION_QUEST_COUNT||!s)return REGION_QUEST_INVALID;
    if(!regional_quest_available(s,q))return REGION_QUEST_LOCKED;
    if(save5_quest_state(&s->quests,q))return REGION_QUEST_UNCHANGED;
    save5_quest_set_state(&s->quests,q,SAVE5_QUEST_ACTIVE);return REGION_QUEST_CHANGED;
}
int regional_quest_objective(Save5State*s,unsigned q,unsigned bit){
    unsigned state;if(!s||q>=REGION_QUEST_COUNT||!bit||(bit&(bit-1))||!(masks[q]&bit))return REGION_QUEST_INVALID;
    if(!regional_quest_available(s,q))return REGION_QUEST_LOCKED;
    state=save5_quest_state(&s->quests,q);
    if(state==SAVE5_QUEST_INACTIVE)return REGION_QUEST_LOCKED;
    if(state>=SAVE5_QUEST_READY||(s->quests.objectives[q]&bit))return REGION_QUEST_UNCHANGED;
    s->quests.objectives[q]=(Save4U16)(s->quests.objectives[q]|bit);
    if(s->quests.objectives[q]==masks[q]){save5_quest_set_state(&s->quests,q,SAVE5_QUEST_READY);return REGION_QUEST_NOW_READY;}
    return REGION_QUEST_CHANGED;
}
int regional_quest_variable(Save5State*s,unsigned q,unsigned value){
    if(!s||(q!=REGION_QUEST_METAL_BOND&&q!=REGION_QUEST_GARDEN)||value>3)return REGION_QUEST_INVALID;
    if(save5_quest_state(&s->quests,q)!=SAVE5_QUEST_ACTIVE)return REGION_QUEST_LOCKED;
    if(s->quests.variables[q]==value)return REGION_QUEST_UNCHANGED;
    s->quests.variables[q]=(Save4U8)value;return REGION_QUEST_CHANGED;
}
static void reward_commit(Save5Quests*q,unsigned id){
    save5_quest_set_state(q,id,SAVE5_QUEST_CLAIMED);
    q->rewards[id>>3]=(Save4U8)(q->rewards[id>>3]|(1u<<(id&7)));
}
int regional_quest_claim(Save5State*s,unsigned q){
    static const EquipmentU8 rewards[REGION_QUEST_COUNT][2]={{6,255},{8,255},{255,255},{255,255},{5,255},{10,255},{3,12},{1,255},{7,255},{9,255},{11,255}};
    CreatureInstance trained;unsigned trained_slot=CREATURE_EMPTY_SLOT;
    unsigned state,result;if(!s||q>=REGION_QUEST_COUNT)return REGION_QUEST_INVALID;
    if(!regional_quest_available(s,q))return REGION_QUEST_LOCKED;
    state=save5_quest_state(&s->quests,q);
    if(state==SAVE5_QUEST_CLAIMED)return REGION_QUEST_UNCHANGED;
    if(state!=SAVE5_QUEST_READY||s->quests.objectives[q]!=masks[q])return REGION_QUEST_LOCKED;
    if(q==REGION_QUEST_TIDE_POOLS){
        unsigned i;CreatureU32 target=creatures_xp_threshold(15);
        for(i=0;i<CREATURE_ROSTER_CAPACITY;i++)if(s->roster.instances[i].form_id==13||s->roster.instances[i].form_id==14){trained_slot=i;break;}
        if(trained_slot==CREATURE_EMPTY_SLOT)return REGION_QUEST_LOCKED;
        trained=s->roster.instances[trained_slot];
        if(!creatures_mark_trial(&trained,CREATURE_TRIAL_PAIRED_POOLS))return REGION_QUEST_INVALID;
        if(trained.xp<target&&!creatures_add_xp(&trained,target-trained.xp))return REGION_QUEST_INVALID;
        if(trained.bond<45)trained.bond=45;
    }
    if(q==REGION_QUEST_WATER_BOND||q==REGION_QUEST_METAL_BOND){
        unsigned form=q==REGION_QUEST_WATER_BOND?13:16,reward=q==REGION_QUEST_WATER_BOND?5:6;
        if(!creatures_form(form))return REGION_QUEST_LOCKED;
        /* A reward already granted without its quest ledger is inconsistent;
         * never repair it by creating a second creature. */
        if(s->roster.rewards[(reward-1)>>3]&(1u<<((reward-1)&7)))return REGION_QUEST_INVALID;
        enum CreatureAdmissionStatus admission=creatures_grant_admitted(&s->roster,form,10,20,0,reward,0);
        if(!creatures_admission_allowed(admission))
            return admission==CREATURE_ADMISSION_FULL?REGION_QUEST_FULL:
                   admission==CREATURE_ADMISSION_RESERVED?REGION_QUEST_RESERVED:REGION_QUEST_INVALID;
    }else{
        result=equipment_claim_many(&s->equipment,rewards[q],rewards[q][1]==255?1:2);
        if(result==EQUIPMENT_FULL)return REGION_QUEST_FULL;
        if(result!=EQUIPMENT_OK&&result!=EQUIPMENT_DUPLICATE&&result!=EQUIPMENT_ALREADY_CLAIMED)return REGION_QUEST_INVALID;
    }
    if(trained_slot!=CREATURE_EMPTY_SLOT)s->roster.instances[trained_slot]=trained;
    reward_commit(&s->quests,q);return REGION_QUEST_REWARDED;
}
int regional_claim_rack(Save5State*s,unsigned cls){
    unsigned source,result;if(!s||(cls!=EQUIPMENT_LANCE&&cls!=EQUIPMENT_BOW))return REGION_QUEST_INVALID;
    if(!town_open(s))return REGION_QUEST_LOCKED;
    source=cls==EQUIPMENT_LANCE?2:4;
    result=equipment_claim(&s->equipment,equipment_reward_item(source),source,0);
    if(result==EQUIPMENT_FULL)return REGION_QUEST_FULL;
    if(result==EQUIPMENT_OK||result==EQUIPMENT_DUPLICATE)return REGION_QUEST_REWARDED;
    if(result==EQUIPMENT_ALREADY_CLAIMED)return REGION_QUEST_UNCHANGED;
    return REGION_QUEST_INVALID;
}
