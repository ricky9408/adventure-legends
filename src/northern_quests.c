#include "northern_quests.h"
static const unsigned char masks[11]={3,7,3,7,7,3,7,7,3,7,15};
static int done(const Save5State*s,unsigned q){return save5_quest_state(&s->quests,q)==SAVE5_QUEST_CLAIMED;}
static int gate(const Save5State*s){return s&&(s->campaign.chapter_flags&SAVE4_SKY_CLEAR)&&(s->quests.region_flags[0]&1u);}
static int town(const Save5State*s){return gate(s)&&(s->quests.region_flags[1]&1u);}
unsigned northern_quest_mask(unsigned q){return q>=11&&q<=21?masks[q-11]:0;}
int northern_can_enter(const Save5State*s,unsigned room){
 if(!gate(s)||room<22||room>29)return 0;
 if(room==22)return 1;
 if(!town(s))return 0;
 if(room>=26&&(!done(s,11)||!done(s,13)))return 0;
 if(room>=27&&!(s->quests.objectives[21]&(1u<<(room-27))))return 0;
 return 1;
}
int northern_visit(Save5State*s,unsigned room){unsigned bit;if(!northern_can_enter(s,room))return NORTH_LOCKED;
 bit=1u<<(room-22);if(s->quests.region_flags[1]&bit)return NORTH_UNCHANGED;
 s->quests.region_flags[1]=(Save4U8)(s->quests.region_flags[1]|bit);return NORTH_CHANGED;
}
int northern_anchor(Save5State*s,unsigned room){unsigned bit;if(!s||(room!=22&&room!=23))return NORTH_INVALID;
 bit=1u<<(room-22);if(!town(s)||!(s->quests.region_flags[1]&bit))return NORTH_LOCKED;
 if(s->quests.anchors[1]&bit)return NORTH_UNCHANGED;
 s->quests.anchors[1]=(Save4U8)(s->quests.anchors[1]|bit);return NORTH_CHANGED;
}
int northern_quest_available(const Save5State*s,unsigned q){static const unsigned char req[5]={11,12,14,15,13};
 if(!town(s)||!northern_quest_mask(q))return 0;
 if(q==13)return done(s,11);
 if(q>=16&&q<=20)return done(s,req[q-16]);
 if(q==21)return done(s,11)&&done(s,13);
 return 1;
}
int northern_quest_offer(Save5State*s,unsigned q){
 if(!s||!northern_quest_mask(q))return NORTH_INVALID;
 if(!northern_quest_available(s,q))return NORTH_LOCKED;
 if(save5_quest_state(&s->quests,q))return NORTH_UNCHANGED;
 save5_quest_set_state(&s->quests,q,SAVE5_QUEST_ACTIVE);return NORTH_CHANGED;
}
int northern_quest_objective(Save5State*s,unsigned q,unsigned bit){unsigned st,mask=northern_quest_mask(q);
 if(!s||!mask||!bit||(bit&(bit-1))||!(mask&bit))return NORTH_INVALID;
 if(!northern_quest_available(s,q))return NORTH_LOCKED;
 st=save5_quest_state(&s->quests,q);if(!st)return NORTH_LOCKED;
 if(st>=SAVE5_QUEST_READY||(s->quests.objectives[q]&bit))return NORTH_UNCHANGED;
 if(q==21&&(s->quests.objectives[q]&(bit-1))!=bit-1)return NORTH_LOCKED;
 s->quests.objectives[q]=(Save4U16)(s->quests.objectives[q]|bit);
 if(s->quests.objectives[q]==mask){save5_quest_set_state(&s->quests,q,SAVE5_QUEST_READY);return NORTH_NOW_READY;}
 return NORTH_CHANGED;
}
unsigned northern_recruit_level(const CreatureRoster*r){unsigned levels[4],n=0,i,j,t;
 if(!r)return 14;
 for(i=0;i<4;i++){unsigned s=r->party[i];if(s>=CREATURE_ROSTER_CAPACITY||!(r->instances[s].flags&CREATURE_OCCUPIED))continue;levels[n++]=r->instances[s].level;}
 for(i=1;i<n;i++)for(j=i;j&&levels[j]<levels[j-1];j--){t=levels[j];levels[j]=levels[j-1];levels[j-1]=t;}
 /* Integer median: average the middle pair for an even valid party, rounded
  * down. The bounded catch-up never falls below14 or exceeds20. */
 t=n?(n&1?levels[n/2]:(levels[n/2-1]+levels[n/2])/2):14;return t<14?14:t>20?20:t;
}
int northern_quest_claim(Save5State*s,unsigned q){
 static const unsigned char forms[5]={19,22,77,73,75},rewards[5]={7,8,11,9,10};
 static const unsigned char trial_forms[5]={19,22,73,75,77},trial_levels[5]={16,17,18,18,20},trial_bonds[5]={40,40,45,45,50};
 static const EquipmentU8 gear[5][2]={{13,255},{14,255},{15,255},{16,17},{18,255}};
 CreatureInstance trained;unsigned slot=CREATURE_EMPTY_SLOT,result,i,st,idx;
 if(!s||!northern_quest_mask(q))return NORTH_INVALID;
 if(!northern_quest_available(s,q))return NORTH_LOCKED;
 st=save5_quest_state(&s->quests,q);if(st==SAVE5_QUEST_CLAIMED)return NORTH_UNCHANGED;
 if(st!=SAVE5_QUEST_READY||s->quests.objectives[q]!=northern_quest_mask(q))return NORTH_LOCKED;
 if(q<=15){
  idx=q-11;i=rewards[idx]-1;
  if(s->roster.rewards[i>>3]&(1u<<(i&7)))return NORTH_INVALID;
  if(!creatures_form(forms[idx]))return NORTH_LOCKED;
  result=creatures_grant(&s->roster,forms[idx],northern_recruit_level(&s->roster),20,0,rewards[idx]);
  if(result==CREATURE_EMPTY_SLOT)return NORTH_FULL;
 }else if(q<=20){
  const CreatureForm*base;CreatureU32 xp;
  idx=q-16;base=creatures_form(trial_forms[idx]);if(!base)return NORTH_LOCKED;
  for(i=0;i<CREATURE_ROSTER_CAPACITY;i++){const CreatureForm*f=creatures_form(s->roster.instances[i].form_id);
   if((s->roster.instances[i].flags&CREATURE_OCCUPIED)&&f&&f->family==base->family){slot=i;break;}}
  if(slot==CREATURE_EMPTY_SLOT)return NORTH_LOCKED;
  trained=s->roster.instances[slot];
  if(!creatures_mark_trial(&trained,1u<<(idx+5)))return NORTH_INVALID;
  xp=creatures_xp_threshold(trial_levels[idx]);if(trained.xp<xp&&!creatures_add_xp(&trained,xp-trained.xp))return NORTH_INVALID;
  if(trained.bond<trial_bonds[idx])trained.bond=trial_bonds[idx];
  result=equipment_claim_many(&s->equipment,gear[idx],gear[idx][1]==255?1:2);
  if(result==EQUIPMENT_FULL)return NORTH_FULL;
  if(result!=EQUIPMENT_OK&&result!=EQUIPMENT_DUPLICATE&&result!=EQUIPMENT_ALREADY_CLAIMED)return NORTH_INVALID;
  s->roster.instances[slot]=trained;
 }
 save5_quest_set_state(&s->quests,q,SAVE5_QUEST_CLAIMED);
 s->quests.rewards[q>>3]=(Save4U8)(s->quests.rewards[q>>3]|(1u<<(q&7)));
 return NORTH_REWARDED;
}
