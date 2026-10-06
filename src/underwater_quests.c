#include "underwater_quests.h"
static const Save4U8 masks[8]={3,3,15,7,3,3,3,7};
static const Save4U8 visits[8]={1,1,4,2,8,4,32,8};
static int done(const Save5State *s,unsigned q) {
 return s && save5_quest_state(&s->quests,q)==SAVE5_QUEST_CLAIMED;
}
static int gate(const Save5State *s) { return done(s,32); }
static int town(const Save5State *s) { return gate(s)&&(s->quests.region_flags[4]&1u); }
static unsigned source_index(unsigned token) { return token>=1&&token<=8?token-1:8; }
static unsigned base_form(unsigned index) { return 49+3*index; }
static int admission_result(enum CreatureAdmissionStatus result) {
 if(creatures_admission_allowed(result))return UNDERWATER_CHANGED;
 if(result==CREATURE_ADMISSION_FULL)return UNDERWATER_FULL;
 if(result==CREATURE_ADMISSION_RESERVED||result==CREATURE_ADMISSION_COVERAGE_LOSS)return UNDERWATER_SPACE_RESERVED;
 if(result==CREATURE_ADMISSION_ID_EXHAUSTED)return UNDERWATER_ID_EXHAUSTED;
 return UNDERWATER_INVALID;
}
static int grant_status(const CreatureRoster *r,unsigned form) {
 enum CreatureAdmissionStatus result=creatures_admission_query_grant(r,form,0);
 if(creatures_admission_allowed(result)&&r->next_instance_id==0xffffffffu)return UNDERWATER_ID_EXHAUSTED;
 return admission_result(result);
}
unsigned underwater_source_family(unsigned token) {
 unsigned i=source_index(token);return i<8?17+i:0;
}
unsigned underwater_source_form(unsigned token) {
 unsigned i=source_index(token);return i<8?base_form(i):0;
}
unsigned underwater_source_token_for_family(unsigned family) {
 return family>=17&&family<=24?family-16:UW_SOURCE_NONE;
}
unsigned underwater_source_aid(unsigned token) {
 unsigned i=source_index(token);return i>=2&&i<8?76+i:255;
}
int underwater_source_claimed(const Save5State *s,unsigned token) {
 unsigned i=source_index(token);
 if(!s||i>=8)return 0;
 return i<2?done(s,38+i):(s->quests.region_flags[10]&(1u<<(i-2)))!=0;
}
unsigned underwater_context(const Save5State *s) {
 unsigned context=0;
 if(done(s,38)&&done(s,39))context|=CREATURE_UNDERWATER_READY;
 if(done(s,40))context|=CREATURE_PALINODE_OPEN;
 return context;
}
unsigned underwater_quest_mask(unsigned q) { return q>=38&&q<46?masks[q-38]:0; }
int underwater_can_enter(const Save5State *s,unsigned room) {
 unsigned prefix;
 if(!gate(s)||room<46||room>53)return 0;
 if(room==46)return 1;
 if(!town(s))return 0;
 if(room>=50&&(!done(s,38)||!done(s,39)))return 0;
 if(room>=51){prefix=(1u<<(room-50))-1u;if((s->quests.objectives[40]&prefix)!=prefix)return 0;}
 return 1;
}
int underwater_visit(Save5State *s,unsigned room) {
 unsigned bit;
 if(!s||room<46||room>53||!save5_validate(s))return UNDERWATER_INVALID;
 if(!underwater_can_enter(s,room))return UNDERWATER_LOCKED;
 bit=1u<<(room-46);if(s->quests.region_flags[4]&bit)return UNDERWATER_UNCHANGED;
 s->quests.region_flags[4]=(Save4U8)(s->quests.region_flags[4]|bit);return UNDERWATER_CHANGED;
}
int underwater_anchor(Save5State *s,unsigned room) {
 unsigned bit;
 if(!s||(room!=46&&room!=47)||!save5_validate(s))return UNDERWATER_INVALID;
 bit=1u<<(room-46);
 if(!town(s)||!(s->quests.region_flags[4]&bit))return UNDERWATER_LOCKED;
 if(s->quests.anchors[4]&bit)return UNDERWATER_UNCHANGED;
 s->quests.anchors[4]=(Save4U8)(s->quests.anchors[4]|bit);return UNDERWATER_CHANGED;
}
int underwater_quest_available(const Save5State *s,unsigned q) {
 if(!town(s)||!underwater_quest_mask(q))return 0;
 if(q==40)return done(s,38)&&done(s,39);
 if(q==41)return done(s,38);
 if(q==42)return done(s,39);
 if(q==45)return done(s,40);
 return 1;
}
int underwater_quest_offer(Save5State *s,unsigned q) {
 if(!s||!underwater_quest_mask(q)||!save5_validate(s))return UNDERWATER_INVALID;
 if(!underwater_quest_available(s,q))return UNDERWATER_LOCKED;
 if(save5_quest_state(&s->quests,q))return UNDERWATER_UNCHANGED;
 save5_quest_set_state(&s->quests,q,SAVE5_QUEST_ACTIVE);return UNDERWATER_CHANGED;
}
int underwater_quest_objective(Save5State *s,unsigned q,unsigned bit) {
 unsigned st,mask=underwater_quest_mask(q);
 if(!s||!mask||!bit||(bit&(bit-1))||!(mask&bit)||!save5_validate(s))return UNDERWATER_INVALID;
 if(!underwater_quest_available(s,q))return UNDERWATER_LOCKED;
 st=save5_quest_state(&s->quests,q);if(!st)return UNDERWATER_LOCKED;
 if(st>=SAVE5_QUEST_READY||(s->quests.objectives[q]&bit))return UNDERWATER_UNCHANGED;
 if(q==40&&(s->quests.objectives[q]&(bit-1))!=bit-1)return UNDERWATER_LOCKED;
 s->quests.objectives[q]=(Save4U16)(s->quests.objectives[q]|bit);
 if(s->quests.objectives[q]==mask){save5_quest_set_state(&s->quests,q,SAVE5_QUEST_READY);return UNDERWATER_NOW_READY;}
 return UNDERWATER_CHANGED;
}
unsigned underwater_recruit_level(const CreatureRoster *r) {
 unsigned values[4],n=0,i,j,t;
 if(!r)return 26;
 for(i=0;i<4;++i){unsigned slot=r->party[i];
  if(slot>=CREATURE_ROSTER_CAPACITY||!(r->instances[slot].flags&CREATURE_OCCUPIED))continue;
  values[n++]=r->instances[slot].level;}
 for(i=1;i<n;++i)for(j=i;j&&values[j]<values[j-1];--j){t=values[j];values[j]=values[j-1];values[j-1]=t;}
 t=n?(n&1?values[n/2]:(values[n/2-1]+values[n/2])/2):26;
 return t<26?26:t>32?32:t;
}
int underwater_quest_claim(Save5State *s,unsigned q) {
 EquipmentState staged;unsigned st,source,result,slot;int admission;
 if(!s||!underwater_quest_mask(q)||!save5_validate(s))return UNDERWATER_INVALID;
 if(!underwater_quest_available(s,q))return UNDERWATER_LOCKED;
 st=save5_quest_state(&s->quests,q);if(st==SAVE5_QUEST_CLAIMED)return UNDERWATER_UNCHANGED;
 if(st!=SAVE5_QUEST_READY||s->quests.objectives[q]!=underwater_quest_mask(q))return UNDERWATER_LOCKED;
 if(q<40){admission=grant_status(&s->roster,base_form(q-38));if(admission!=UNDERWATER_CHANGED)return admission;}
 /* Stage once; do not nest equipment_claim_many's second 512-byte stage.
  * A failed second item never leaks the first reward or a quest receipt. */
 if(q>=41){
  staged=s->equipment;
  for(source=q==45?35:q-10;source<=(q==45?36:q-10);++source){
   result=equipment_claim(&staged,equipment_reward_item(source),source,0);
   if(result==EQUIPMENT_FULL)return UNDERWATER_FULL;
   if(result!=EQUIPMENT_OK&&result!=EQUIPMENT_DUPLICATE&&result!=EQUIPMENT_ALREADY_CLAIMED)return UNDERWATER_INVALID;
  }
 }
 if(q<40){admission=admission_result(creatures_grant_admitted(&s->roster,base_form(q-38),
   underwater_recruit_level(&s->roster),20,0,0,&slot));if(admission!=UNDERWATER_CHANGED)return admission;}
 if(q>=41)s->equipment=staged;
 save5_quest_set_state(&s->quests,q,SAVE5_QUEST_CLAIMED);
 s->quests.rewards[q>>3]=(Save4U8)(s->quests.rewards[q>>3]|(1u<<(q&7)));
 return UNDERWATER_REWARDED;
}
unsigned underwater_discovery_state(const Save5State *s,unsigned family) {
 unsigned byte,mask;
 if(!s||(family!=23&&family!=24))return SAVE5_QUEST_INACTIVE;
 byte=family-3;mask=family==23?3:7;
 if(underwater_source_claimed(s,family-16))return SAVE5_QUEST_CLAIMED;
 if(!s->quests.region_flags[byte])return SAVE5_QUEST_INACTIVE;
 return s->quests.region_flags[byte]==mask?SAVE5_QUEST_READY:SAVE5_QUEST_ACTIVE;
}
int underwater_discover(Save5State *s,unsigned family,unsigned bit) {
 unsigned byte,mask,visit;
 if(!s||(family!=23&&family!=24))return UNDERWATER_INVALID;
 byte=family-3;mask=family==23?3:7;visit=family==23?32:8;
 if(!bit||(bit&(bit-1))||!(mask&bit)||!save5_validate(s))return UNDERWATER_INVALID;
 if(!town(s)||!(s->quests.region_flags[4]&visit))return UNDERWATER_LOCKED;
 if(s->quests.region_flags[byte]&bit)return UNDERWATER_UNCHANGED;
 if((s->quests.region_flags[byte]&(bit-1))!=bit-1)return UNDERWATER_LOCKED;
 s->quests.region_flags[byte]=(Save4U8)(s->quests.region_flags[byte]|bit);
 return s->quests.region_flags[byte]==mask?UNDERWATER_NOW_READY:UNDERWATER_CHANGED;
}
int underwater_source_status(const Save5State *s,unsigned token) {
 unsigned i=source_index(token);
 if(!s||i>=8||!save5_validate(s))return UNDERWATER_INVALID;
 if(underwater_source_claimed(s,token))return UNDERWATER_UNCHANGED;
 if(!town(s))return UNDERWATER_LOCKED;
 if(i<2){if(save5_quest_state(&s->quests,38+i)!=SAVE5_QUEST_READY)return UNDERWATER_LOCKED;}
 else if(!(s->quests.region_flags[4]&visits[i])||
  (i==6&&s->quests.region_flags[20]!=3)||(i==7&&s->quests.region_flags[21]!=7))return UNDERWATER_LOCKED;
 return grant_status(&s->roster,base_form(i));
}
int underwater_field_recruit(Save5State *s,unsigned token) {
 unsigned i=source_index(token),slot;int result;
 if(i<2||i>=8)return UNDERWATER_INVALID;
 result=underwater_source_status(s,token);if(result!=UNDERWATER_CHANGED)return result;
 result=admission_result(creatures_grant_admitted(&s->roster,base_form(i),underwater_recruit_level(&s->roster),20,0,0,&slot));
 if(result!=UNDERWATER_CHANGED)return result;
 s->quests.region_flags[10]=(Save4U8)(s->quests.region_flags[10]|(1u<<(i-2)));
 return UNDERWATER_REWARDED;
}
int underwater_branch_status(const Save5State *s,unsigned token) {
 unsigned i=source_index(token),n;int terminal=0;
 if(!s||i>=8||!save5_validate(s))return UNDERWATER_INVALID;
 if(!underwater_source_claimed(s,token)||!town(s)||!(s->quests.region_flags[4]&visits[i]))return UNDERWATER_LOCKED;
 for(n=0;n<CREATURE_ROSTER_CAPACITY;++n){unsigned f=s->roster.instances[n].form_id;
  if(f==base_form(i)+1u||f==base_form(i)+2u){terminal=1;break;}}
 return terminal?grant_status(&s->roster,base_form(i)):UNDERWATER_LOCKED;
}
int underwater_branch_recruit(Save5State *s,unsigned token) {
 unsigned i=source_index(token),slot;int result=underwater_branch_status(s,token);
 if(result!=UNDERWATER_CHANGED)return result;
 result=admission_result(creatures_grant_admitted(&s->roster,base_form(i),underwater_recruit_level(&s->roster),20,0,0,&slot));
 if(result!=UNDERWATER_CHANGED)return result;
 s->quests.region_flags[17]=(Save4U8)(s->quests.region_flags[17]|(1u<<i));
 return UNDERWATER_REWARDED;
}
unsigned underwater_trial_aid(unsigned family,unsigned key) {
 return family>=17&&family<=24&&key>=1&&key<=2?62+(family-17)*2+key-1:255;
}
int underwater_trial_status(const Save5State *s,unsigned slot,CreatureU32 expected_id,
 unsigned family,unsigned key,unsigned token) {
 const CreatureInstance *c;const CreatureForm *form;unsigned i=source_index(token);
 if(!s||slot>=CREATURE_ROSTER_CAPACITY||!expected_id||i>=8||family!=17+i||
  underwater_trial_aid(family,key)==255||!save5_validate(s))return UNDERWATER_INVALID;
 c=&s->roster.instances[slot];form=creatures_form(c->form_id);
 if(!form||c->instance_id!=expected_id||form->family!=family)return UNDERWATER_INVALID;
 if(!town(s)||!done(s,38)||!done(s,39)||!underwater_source_claimed(s,token))return UNDERWATER_LOCKED;
 if(creatures_has_trial_qualified(c,family,key))return UNDERWATER_UNCHANGED;
 if(c->form_id!=base_form(i))return UNDERWATER_LOCKED;
 return UNDERWATER_CHANGED;
}
int underwater_trial_complete(Save5State *s,unsigned slot,CreatureU32 expected_id,
 unsigned family,unsigned key,unsigned token) {
 CreatureInstance trained;CreatureU32 xp;
 int result=underwater_trial_status(s,slot,expected_id,family,key,token);
 if(result!=UNDERWATER_CHANGED)return result;
 trained=s->roster.instances[slot];
 if(!creatures_mark_trial_qualified(&trained,family,key))return UNDERWATER_INVALID;
 xp=creatures_xp_threshold(28);
 if(trained.xp<xp&&!creatures_add_xp(&trained,xp-trained.xp))return UNDERWATER_INVALID;
 if(trained.bond<45)trained.bond=45;
 if(!creatures_instance_validate(&trained))return UNDERWATER_INVALID;
 s->roster.instances[slot]=trained;return UNDERWATER_REWARDED;
}
const char *underwater_result_message(int result) {
 switch(result){
 case UNDERWATER_FULL:return "Storage is full. Your invitation is still ready.";
 case UNDERWATER_SPACE_RESERVED:return "Keep room for a missing family or evolution path.";
 case UNDERWATER_ID_EXHAUSTED:return "This collection cannot assign another identity.";
 case UNDERWATER_LOCKED:return "Complete the marked steps first.";
 case UNDERWATER_UNCHANGED:return "Already recorded.";
 case UNDERWATER_INVALID:return "That action could not be recorded.";
 default:return "Ready.";
 }
}

#include "underwater_transactions.inc"
