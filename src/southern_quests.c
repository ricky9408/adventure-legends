#include "southern_quests.h"
static const Save4U8 masks[8]={3,3,15,7,3,3,3,3};
/* First guaranteed sources, then byte8 bits0..7. Stable explicit rows. */
static const Save4U8 forms[10]={79,85,25,28,81,83,87,89,91,93};
static const Save4U8 families[10]={28,31,9,10,29,30,32,33,34,35};
static const Save4U8 levels[10]={20,20,20,22,22,22,24,22,24,22};
static const Save4U8 bonds[10]={40,40,40,45,45,45,45,45,45,45};
static int done(const Save5State *s,unsigned q) {
 return s && save5_quest_state(&s->quests,q)==SAVE5_QUEST_CLAIMED;
}
static int gate(const Save5State *s) {
 return s && (s->campaign.chapter_flags&SAVE4_SKY_CLEAR) &&
  (s->quests.region_flags[0]&1u) && (s->quests.region_flags[1]&1u) &&
  done(s,11) && done(s,13) && done(s,21);
}
static int town(const Save5State *s) { return gate(s)&&(s->quests.region_flags[2]&1u); }
static unsigned source_index(unsigned token) {
 if(token==SOUTH_SOURCE_WINDOW)return 0;
 if(token==SOUTH_SOURCE_HINGE)return 1;
 if(token>=SOUTH_SOURCE_TANGLEAPER&&token<=SOUTH_SOURCE_NEEDLETROT)return token-14;
 return 10;
}
unsigned southern_source_family(unsigned token) {
 unsigned i=source_index(token);return i<10?families[i]:0;
}
unsigned southern_source_token_for_family(unsigned family) {
 unsigned i;for(i=0;i<10;++i)if(families[i]==family)return i<2?i+1:i+14;
 return SOUTH_SOURCE_NONE;
}
int southern_source_claimed(const Save5State *s,unsigned token) {
 unsigned i=source_index(token);
 if(!s||i==10)return 0;
 if(i<2)return done(s,22+i);
 return (s->quests.region_flags[8]&(1u<<(i-2)))!=0;
}
unsigned southern_context(const Save5State *s) {
 unsigned context=0;
 if(done(s,22)&&done(s,23))context|=CREATURE_SOUTH_READY;
 if(done(s,24))context|=CREATURE_SUNWELL_OPEN;
 return context;
}
unsigned southern_quest_mask(unsigned q) { return q>=22&&q<30?masks[q-22]:0; }
int southern_can_enter(const Save5State *s,unsigned room) {
 unsigned prefix;
 if(!gate(s)||room<30||room>37)return 0;
 if(room==30)return 1;
 if(!town(s))return 0;
 if(room>=34&&(!done(s,22)||!done(s,23)))return 0;
 if(room>=35){prefix=(1u<<(room-34))-1u;if((s->quests.objectives[24]&prefix)!=prefix)return 0;}
 return 1;
}
int southern_visit(Save5State *s,unsigned room) {
 unsigned bit;
 if(!s||room<30||room>37)return SOUTH_INVALID;
 if(!save5_validate(s))return SOUTH_INVALID;
 if(!southern_can_enter(s,room))return SOUTH_LOCKED;
 bit=1u<<(room-30);if(s->quests.region_flags[2]&bit)return SOUTH_UNCHANGED;
 s->quests.region_flags[2]=(Save4U8)(s->quests.region_flags[2]|bit);return SOUTH_CHANGED;
}
int southern_anchor(Save5State *s,unsigned room) {
 unsigned bit;
 if(!s||(room!=30&&room!=31)||!save5_validate(s))return SOUTH_INVALID;
 bit=1u<<(room-30);if(!town(s)||!(s->quests.region_flags[2]&bit))return SOUTH_LOCKED;
 if(s->quests.anchors[2]&bit)return SOUTH_UNCHANGED;
 s->quests.anchors[2]=(Save4U8)(s->quests.anchors[2]|bit);return SOUTH_CHANGED;
}
int southern_quest_available(const Save5State *s,unsigned q) {
 if(!town(s)||!southern_quest_mask(q))return 0;
 return q!=24||(done(s,22)&&done(s,23));
}
int southern_quest_offer(Save5State *s,unsigned q) {
 if(!s||!southern_quest_mask(q)||!save5_validate(s))return SOUTH_INVALID;
 if(!southern_quest_available(s,q))return SOUTH_LOCKED;
 if(save5_quest_state(&s->quests,q))return SOUTH_UNCHANGED;
 save5_quest_set_state(&s->quests,q,SAVE5_QUEST_ACTIVE);return SOUTH_CHANGED;
}
int southern_quest_objective(Save5State *s,unsigned q,unsigned bit) {
 unsigned st,mask=southern_quest_mask(q);
 if(!s||!mask||!bit||(bit&(bit-1))||!(mask&bit)||!save5_validate(s))return SOUTH_INVALID;
 if(!southern_quest_available(s,q))return SOUTH_LOCKED;
 st=save5_quest_state(&s->quests,q);if(!st)return SOUTH_LOCKED;
 if(st>=SAVE5_QUEST_READY||(s->quests.objectives[q]&bit))return SOUTH_UNCHANGED;
 if(q==24&&(s->quests.objectives[q]&(bit-1))!=bit-1)return SOUTH_LOCKED;
 s->quests.objectives[q]=(Save4U16)(s->quests.objectives[q]|bit);
 if(s->quests.objectives[q]==mask){save5_quest_set_state(&s->quests,q,SAVE5_QUEST_READY);return SOUTH_NOW_READY;}
 return SOUTH_CHANGED;
}
unsigned southern_recruit_level(const CreatureRoster *r) {
 unsigned values[4],n=0,i,j,t;
 if(!r)return 18;
 for(i=0;i<4;++i){unsigned slot=r->party[i];
  if(slot>=CREATURE_ROSTER_CAPACITY||!(r->instances[slot].flags&CREATURE_OCCUPIED))continue;
  values[n++]=r->instances[slot].level;}
 for(i=1;i<n;++i)for(j=i;j&&values[j]<values[j-1];--j){t=values[j];values[j]=values[j-1];values[j-1]=t;}
 t=n?(n&1?values[n/2]:(values[n/2-1]+values[n/2])/2):18;
 return t<18?18:t>24?24:t;
}
static int admission_result(enum CreatureAdmissionStatus status) {
 if(creatures_admission_allowed(status))return SOUTH_CHANGED;
 if(status==CREATURE_ADMISSION_FULL)return SOUTH_FULL;
 if(status==CREATURE_ADMISSION_RESERVED)return SOUTH_RESERVED;
 return SOUTH_INVALID;
}
static int grant_preflight(const CreatureRoster *r,unsigned form) {
 if(r->next_instance_id==0xffffffffu)return SOUTH_INVALID;
 return admission_result(creatures_admission_query_grant(r,form,0));
}
int southern_quest_claim(Save5State *s,unsigned q) {
 static const Save4U8 gear[8]={19,255,255,21,23,22,24,20};
 EquipmentState staged;
 unsigned st,source,result;
 if(!s||!southern_quest_mask(q)||!save5_validate(s))return SOUTH_INVALID;
 if(!southern_quest_available(s,q))return SOUTH_LOCKED;
 st=save5_quest_state(&s->quests,q);if(st==SAVE5_QUEST_CLAIMED)return SOUTH_UNCHANGED;
 if(st!=SAVE5_QUEST_READY||s->quests.objectives[q]!=southern_quest_mask(q))return SOUTH_LOCKED;
 if(q<24){result=grant_preflight(&s->roster,forms[q-22]);if(result!=SOUTH_CHANGED)return (int)result;}
 source=gear[q-22];
 if(source!=255){
  staged=s->equipment;
  result=equipment_claim(&staged,equipment_reward_item(source),source,0);
  if(result==EQUIPMENT_FULL)return SOUTH_FULL;
  if(result!=EQUIPMENT_OK&&result!=EQUIPMENT_DUPLICATE&&result!=EQUIPMENT_ALREADY_CLAIMED)return SOUTH_INVALID;
 }
 /* grant has no failing mutations. Once it succeeds, only bounded infallible
  * copies/bit updates remain, so mixed Q22 cannot leave half a reward. */
 if(q<24){
  result=(unsigned)admission_result(creatures_grant_admitted(&s->roster,
   forms[q-22],southern_recruit_level(&s->roster),20,0,0,0));
  if(result!=SOUTH_CHANGED)return (int)result;
 }
 if(source!=255)s->equipment=staged;
 save5_quest_set_state(&s->quests,q,SAVE5_QUEST_CLAIMED);
 s->quests.rewards[q>>3]=(Save4U8)(s->quests.rewards[q>>3]|(1u<<(q&7)));
 return SOUTH_REWARDED;
}
int southern_discover(Save5State *s,unsigned discovery) {
 unsigned bit,q;
 if(!s||discovery>1||!save5_validate(s))return SOUTH_INVALID;
 bit=1u<<discovery;q=discovery?28:29;
 if(!town(s)||!(s->quests.region_flags[2]&4u)||save5_quest_state(&s->quests,q)<SAVE5_QUEST_READY)return SOUTH_LOCKED;
 if(s->quests.region_flags[18]&bit)return SOUTH_UNCHANGED;
 s->quests.region_flags[18]=(Save4U8)(s->quests.region_flags[18]|bit);return SOUTH_CHANGED;
}
int southern_field_recruit(Save5State *s,unsigned token) {
 static const Save4U8 visits[8]={2,2,8,2,2,2,4,8};
 unsigned i=source_index(token),field,result;
 if(!s||i<2||i>=10||!save5_validate(s))return SOUTH_INVALID;
 field=i-2;
 if(!town(s)||!(s->quests.region_flags[2]&visits[field])||
    (field==4&&!(s->quests.region_flags[18]&1u))||
    (field==6&&!(s->quests.region_flags[18]&2u)))return SOUTH_LOCKED;
 if(southern_source_claimed(s,token))return SOUTH_UNCHANGED;
 result=(unsigned)admission_result(creatures_grant_admitted(&s->roster,
  forms[i],southern_recruit_level(&s->roster),20,0,0,0));
 if(result!=SOUTH_CHANGED)return (int)result;
 s->quests.region_flags[8]=(Save4U8)(s->quests.region_flags[8]|(1u<<field));
 return SOUTH_REWARDED;
}
int southern_trial_complete(Save5State *s,unsigned slot,CreatureU32 expected_id,
 unsigned family,unsigned key,unsigned token) {
 CreatureInstance trained;const CreatureForm *form;CreatureU32 xp;
 unsigned i=source_index(token);
 if(!s||slot>=CREATURE_ROSTER_CAPACITY||!expected_id||i>=10||key!=1||
    family!=families[i]||!save5_validate(s))return SOUTH_INVALID;
 trained=s->roster.instances[slot];form=creatures_form(trained.form_id);
 if(!form||trained.instance_id!=expected_id||form->family!=family)return SOUTH_INVALID;
 if(!town(s)||!done(s,22)||!done(s,23)||!southern_source_claimed(s,token))return SOUTH_LOCKED;
 if(creatures_has_trial_qualified(&trained,family,key))return SOUTH_UNCHANGED;
 if(!creatures_mark_trial_qualified(&trained,family,key))return SOUTH_INVALID;
 xp=creatures_xp_threshold(levels[i]);
 if(trained.xp<xp&&!creatures_add_xp(&trained,xp-trained.xp))return SOUTH_INVALID;
 if(trained.bond<bonds[i])trained.bond=bonds[i];
 if(!creatures_instance_validate(&trained))return SOUTH_INVALID;
 s->roster.instances[slot]=trained;return SOUTH_REWARDED;
}
