#include "magma_quests.h"
static const Save4U8 masks[8]={3,3,15,7,3,3,3,7};
static const Save4U8 forms[9]={31,34,37,40,43,46,95,97,99};
static const Save4U8 families[9]={11,12,13,14,15,16,36,37,38};
static const Save4U8 visits[7]={2,8,4,2,2,4,8};
static int done(const Save5State *s,unsigned q) {
 return s && save5_quest_state(&s->quests,q)==SAVE5_QUEST_CLAIMED;
}
static int gate(const Save5State *s) { return done(s,24); }
static int town(const Save5State *s) { return gate(s)&&(s->quests.region_flags[3]&1u); }
static unsigned source_index(unsigned token) {
 if(token==MAGMA_SOURCE_HEARTH)return 0;
 if(token==MAGMA_SOURCE_FOOTPATH)return 1;
 if(token>=MAGMA_SOURCE_FIELD_0&&token<=MAGMA_SOURCE_FIELD_6)return token-14;
 return 9;
}
static int admission_result(enum CreatureAdmissionStatus result) {
 if(creatures_admission_allowed(result))return MAGMA_CHANGED;
 if(result==CREATURE_ADMISSION_FULL)return MAGMA_FULL;
 if(result==CREATURE_ADMISSION_RESERVED||result==CREATURE_ADMISSION_COVERAGE_LOSS)return MAGMA_SPACE_RESERVED;
 if(result==CREATURE_ADMISSION_ID_EXHAUSTED)return MAGMA_ID_EXHAUSTED;
 return MAGMA_INVALID;
}
/* Capacity queries deliberately model terminal opportunities only. Mirror
 * admitted grant identity exhaustion here so every typed denial is visible
 * before an invitation/teaching confirmation. A claimed receipt still wins. */
static int grant_status(const CreatureRoster *r,unsigned form) {
 enum CreatureAdmissionStatus status=creatures_admission_query_grant(r,form,0);
 if(creatures_admission_allowed(status) && r->next_instance_id==0xffffffffu)return MAGMA_ID_EXHAUSTED;
 return admission_result(status);
}
unsigned magma_source_family(unsigned token) {
 unsigned i=source_index(token);return i<9?families[i]:0;
}
unsigned magma_source_form(unsigned token) {
 unsigned i=source_index(token);return i<9?forms[i]:0;
}
unsigned magma_source_token_for_family(unsigned family) {
 unsigned i;for(i=0;i<9;++i)if(families[i]==family)return i<2?i+1:i+14;
 return MAGMA_SOURCE_NONE;
}
unsigned magma_source_aid(unsigned token) {
 unsigned i=source_index(token);return i>=2&&i<9?i+53:255;
}
int magma_source_claimed(const Save5State *s,unsigned token) {
 unsigned i=source_index(token);
 if(!s||i==9)return 0;
 if(i<2)return done(s,30+i);
 return (s->quests.region_flags[9]&(1u<<(i-2)))!=0;
}
unsigned magma_context(const Save5State *s) {
 unsigned context=0;
 if(done(s,30)&&done(s,31))context|=CREATURE_MAGMA_READY;
 if(done(s,32))context|=CREATURE_CALDERA_OPEN;
 return context;
}
unsigned magma_quest_mask(unsigned q) { return q>=30&&q<38?masks[q-30]:0; }
int magma_can_enter(const Save5State *s,unsigned room) {
 unsigned prefix;
 if(!gate(s)||room<38||room>45)return 0;
 if(room==38)return 1;
 if(!town(s))return 0;
 if(room>=42&&(!done(s,30)||!done(s,31)))return 0;
 if(room>=43){prefix=(1u<<(room-42))-1u;if((s->quests.objectives[32]&prefix)!=prefix)return 0;}
 return 1;
}
int magma_visit(Save5State *s,unsigned room) {
 unsigned bit;
 if(!s||room<38||room>45||!save5_validate(s))return MAGMA_INVALID;
 if(!magma_can_enter(s,room))return MAGMA_LOCKED;
 bit=1u<<(room-38);if(s->quests.region_flags[3]&bit)return MAGMA_UNCHANGED;
 s->quests.region_flags[3]=(Save4U8)(s->quests.region_flags[3]|bit);return MAGMA_CHANGED;
}
int magma_anchor(Save5State *s,unsigned room) {
 unsigned bit;
 if(!s||(room!=38&&room!=39)||!save5_validate(s))return MAGMA_INVALID;
 bit=1u<<(room-38);if(!town(s)||!(s->quests.region_flags[3]&bit))return MAGMA_LOCKED;
 if(s->quests.anchors[3]&bit)return MAGMA_UNCHANGED;
 s->quests.anchors[3]=(Save4U8)(s->quests.anchors[3]|bit);return MAGMA_CHANGED;
}
int magma_quest_available(const Save5State *s,unsigned q) {
 if(!town(s)||!magma_quest_mask(q))return 0;
 if(q==32)return done(s,30)&&done(s,31);
 if(q==33)return done(s,30);
 if(q==37)return (s->quests.objectives[32]&3u)==3u;
 return 1;
}
int magma_quest_offer(Save5State *s,unsigned q) {
 if(!s||!magma_quest_mask(q)||!save5_validate(s))return MAGMA_INVALID;
 if(!magma_quest_available(s,q))return MAGMA_LOCKED;
 if(save5_quest_state(&s->quests,q))return MAGMA_UNCHANGED;
 save5_quest_set_state(&s->quests,q,SAVE5_QUEST_ACTIVE);return MAGMA_CHANGED;
}
int magma_quest_objective(Save5State *s,unsigned q,unsigned bit) {
 unsigned st,mask=magma_quest_mask(q);
 if(!s||!mask||!bit||(bit&(bit-1))||!(mask&bit)||!save5_validate(s))return MAGMA_INVALID;
 if(!magma_quest_available(s,q))return MAGMA_LOCKED;
 st=save5_quest_state(&s->quests,q);if(!st)return MAGMA_LOCKED;
 if(st>=SAVE5_QUEST_READY||(s->quests.objectives[q]&bit))return MAGMA_UNCHANGED;
 if(q==32&&(s->quests.objectives[q]&(bit-1))!=bit-1)return MAGMA_LOCKED;
 s->quests.objectives[q]=(Save4U16)(s->quests.objectives[q]|bit);
 if(s->quests.objectives[q]==mask){save5_quest_set_state(&s->quests,q,SAVE5_QUEST_READY);return MAGMA_NOW_READY;}
 return MAGMA_CHANGED;
}
unsigned magma_recruit_level(const CreatureRoster *r) {
 unsigned values[4],n=0,i,j,t;
 if(!r)return 24;
 for(i=0;i<4;++i){unsigned slot=r->party[i];
  if(slot>=CREATURE_ROSTER_CAPACITY||!(r->instances[slot].flags&CREATURE_OCCUPIED))continue;
  values[n++]=r->instances[slot].level;}
 for(i=1;i<n;++i)for(j=i;j&&values[j]<values[j-1];--j){t=values[j];values[j]=values[j-1];values[j-1]=t;}
 t=n?(n&1?values[n/2]:(values[n/2-1]+values[n/2])/2):24;
 return t<24?24:t>30?30:t;
}
int magma_quest_claim(Save5State *s,unsigned q) {
 static const Save4U8 gear[8]={25,255,255,26,27,28,29,30};
 EquipmentState staged;unsigned st,source,result,slot;int admission;
 if(!s||!magma_quest_mask(q)||!save5_validate(s))return MAGMA_INVALID;
 if(!magma_quest_available(s,q))return MAGMA_LOCKED;
 st=save5_quest_state(&s->quests,q);if(st==SAVE5_QUEST_CLAIMED)return MAGMA_UNCHANGED;
 if(st!=SAVE5_QUEST_READY||s->quests.objectives[q]!=magma_quest_mask(q))return MAGMA_LOCKED;
 if(q<32){admission=grant_status(&s->roster,forms[q-30]);
  if(admission!=MAGMA_CHANGED)return admission;}
 source=gear[q-30];
 if(source!=255){
  staged=s->equipment;result=equipment_claim(&staged,equipment_reward_item(source),source,0);
  if(result==EQUIPMENT_FULL)return MAGMA_FULL;
  if(result!=EQUIPMENT_OK&&result!=EQUIPMENT_DUPLICATE&&result!=EQUIPMENT_ALREADY_CLAIMED)return MAGMA_INVALID;
 }
 /* The 512-byte gear stage precedes every roster mutation. grant_admitted has
  * mutation-free failure. Afterwards only infallible copies/bit updates remain. */
 if(q<32){admission=admission_result(creatures_grant_admitted(&s->roster,forms[q-30],
   magma_recruit_level(&s->roster),20,0,0,&slot));if(admission!=MAGMA_CHANGED)return admission;}
 if(source!=255)s->equipment=staged;
 save5_quest_set_state(&s->quests,q,SAVE5_QUEST_CLAIMED);
 s->quests.rewards[q>>3]=(Save4U8)(s->quests.rewards[q>>3]|(1u<<(q&7)));
 return MAGMA_REWARDED;
}
unsigned magma_discovery_state(const Save5State *s) {
 if(!s||!s->quests.region_flags[19])return SAVE5_QUEST_INACTIVE;
 if(magma_source_claimed(s,MAGMA_SOURCE_FIELD_6))return SAVE5_QUEST_CLAIMED;
 return s->quests.region_flags[19]==7?SAVE5_QUEST_READY:SAVE5_QUEST_ACTIVE;
}
int magma_discover(Save5State *s,unsigned bit) {
 if(!s||(bit!=1&&bit!=2&&bit!=4)||!save5_validate(s))return MAGMA_INVALID;
 if(!town(s)||!(s->quests.region_flags[3]&8u))return MAGMA_LOCKED;
 if(s->quests.region_flags[19]&bit)return MAGMA_UNCHANGED;
 if((s->quests.region_flags[19]&(bit-1))!=bit-1)return MAGMA_LOCKED;
 s->quests.region_flags[19]=(Save4U8)(s->quests.region_flags[19]|bit);
 return s->quests.region_flags[19]==7?MAGMA_NOW_READY:MAGMA_CHANGED;
}
static int teaching_gear_status(const EquipmentState *e) {
 EquipmentState staged=*e;
 unsigned r=equipment_claim(&staged,equipment_reward_item(25),25,0);
 if(r==EQUIPMENT_FULL)return MAGMA_FULL;
 return r==EQUIPMENT_OK||r==EQUIPMENT_DUPLICATE||r==EQUIPMENT_ALREADY_CLAIMED?MAGMA_CHANGED:MAGMA_INVALID;
}
int magma_source_status(const Save5State *s,unsigned token) {
 unsigned i=source_index(token);
 if(!s||i>=9||!save5_validate(s))return MAGMA_INVALID;
 if(magma_source_claimed(s,token))return MAGMA_UNCHANGED;
 if(!town(s))return MAGMA_LOCKED;
 if(i<2){if(save5_quest_state(&s->quests,30+i)!=SAVE5_QUEST_READY)return MAGMA_LOCKED;}
 else if(!(s->quests.region_flags[3]&visits[i-2])||(i==8&&s->quests.region_flags[19]!=7))return MAGMA_LOCKED;
 {int result=grant_status(&s->roster,forms[i]);
  if(result!=MAGMA_CHANGED)return result;
  return i==0?teaching_gear_status(&s->equipment):MAGMA_CHANGED;}
}
int magma_field_recruit(Save5State *s,unsigned token) {
 unsigned i=source_index(token),slot;int result;
 if(i<2||i>=9)return MAGMA_INVALID;
 result=magma_source_status(s,token);if(result!=MAGMA_CHANGED)return result;
 result=admission_result(creatures_grant_admitted(&s->roster,forms[i],magma_recruit_level(&s->roster),20,0,0,&slot));
 if(result!=MAGMA_CHANGED)return result;
 s->quests.region_flags[9]=(Save4U8)(s->quests.region_flags[9]|(1u<<(i-2)));
 return MAGMA_REWARDED;
}
int magma_branch_status(const Save5State *s,unsigned token) {
 unsigned i=source_index(token),n;int evolved=0;
 if(!s||i<2||i>=6||!save5_validate(s))return MAGMA_INVALID;
 if(!magma_source_claimed(s,token)||!town(s)||!(s->quests.region_flags[3]&visits[i-2]))return MAGMA_LOCKED;
 for(n=0;n<CREATURE_ROSTER_CAPACITY;++n) {
  unsigned f=s->roster.instances[n].form_id;
  if(f==forms[i]+1u||f==forms[i]+2u){evolved=1;break;}
 }
 if(!evolved)return MAGMA_LOCKED;
 return grant_status(&s->roster,forms[i]);
}
int magma_branch_recruit(Save5State *s,unsigned token) {
 unsigned i=source_index(token),slot;int result=magma_branch_status(s,token);
 if(result!=MAGMA_CHANGED)return result;
 result=admission_result(creatures_grant_admitted(&s->roster,forms[i],magma_recruit_level(&s->roster),20,0,0,&slot));
 if(result!=MAGMA_CHANGED)return result;
 s->quests.region_flags[16]=(Save4U8)(s->quests.region_flags[16]|(1u<<(i-2)));
 return MAGMA_REWARDED;
}
unsigned magma_trial_aid(unsigned family,unsigned key) {
 unsigned token=magma_source_token_for_family(family),i=source_index(token);
 if(i>=9||!key||key>(i<6?2u:1u))return 255;
 return i<6?40+i*2+key-1:52+i-6;
}
int magma_trial_status(const Save5State *s,unsigned slot,CreatureU32 expected_id,
 unsigned family,unsigned key,unsigned token) {
 const CreatureInstance *c;const CreatureForm *form;unsigned i=source_index(token),from;
 if(!s||slot>=CREATURE_ROSTER_CAPACITY||!expected_id||i>=9||family!=families[i]||
    magma_trial_aid(family,key)==255||!save5_validate(s))return MAGMA_INVALID;
 c=&s->roster.instances[slot];form=creatures_form(c->form_id);
 if(!form||c->instance_id!=expected_id||form->family!=family)return MAGMA_INVALID;
 if(!town(s)||!done(s,30)||!done(s,31)||!magma_source_claimed(s,token))return MAGMA_LOCKED;
 if(creatures_has_trial_qualified(c,family,key))return MAGMA_UNCHANGED;
 if(i<2&&key==2&&(!done(s,32)||!(c->trial_flags&1u)))return MAGMA_LOCKED;
 from=forms[i]+(i<2&&key==2?1u:0u);
 if(c->form_id!=from)return MAGMA_LOCKED;
 return MAGMA_CHANGED;
}
int magma_trial_complete(Save5State *s,unsigned slot,CreatureU32 expected_id,
 unsigned family,unsigned key,unsigned token) {
 CreatureInstance trained;CreatureU32 xp;unsigned tier3,level,bond;
 int result=magma_trial_status(s,slot,expected_id,family,key,token);
 if(result!=MAGMA_CHANGED)return result;
 trained=s->roster.instances[slot];tier3=(family==11||family==12)&&key==2;
 level=tier3?32:26;bond=tier3?60:45;
 if(!creatures_mark_trial_qualified(&trained,family,key))return MAGMA_INVALID;
 xp=creatures_xp_threshold(level);
 if(trained.xp<xp&&!creatures_add_xp(&trained,xp-trained.xp))return MAGMA_INVALID;
 if(trained.bond<bond)trained.bond=(CreatureU8)bond;
 if(!creatures_instance_validate(&trained))return MAGMA_INVALID;
 s->roster.instances[slot]=trained;return MAGMA_REWARDED;
}
const char *magma_result_message(int result) {
 switch(result){
 case MAGMA_FULL:return "Storage is full. Your invitation is still ready.";
 case MAGMA_SPACE_RESERVED:return "Keep room for a missing family or evolution path.";
 case MAGMA_ID_EXHAUSTED:return "This collection cannot assign another identity.";
 case MAGMA_LOCKED:return "Complete the marked steps first.";
 case MAGMA_UNCHANGED:return "Already recorded.";
 case MAGMA_INVALID:return "That action could not be recorded.";
 default:return "Ready.";
 }
}
