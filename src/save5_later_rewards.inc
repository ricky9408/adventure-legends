/* Narrow durable report operation. Only the existing immutable raw snapshot
 * is staged; the cursor retains at most four changed participants, not another
 * roster or Save5 clone. This whole unit stays in the save5 ROM object. */
#include "later_rewards.h"
static struct {
 Save5State *live;
 LaterRewardContext context;
 Save4U32 token;
 EconomyState economy;
 CreatureInstance party[4];
 unsigned phase,treasure,source,error,gold,xp,fresh;
 Save4U8 slots[4],bond[4],quest_byte,reward_byte,event_byte;
} later_reward;
unsigned later_rewards_state_bytes(void){return sizeof later_reward;}
unsigned later_rewards_phase(void){return later_reward.phase;}
unsigned later_rewards_last_error(void){return later_reward.error;}
unsigned later_rewards_last_gold(void){return later_reward.gold;}
unsigned later_rewards_last_xp(void){return later_reward.xp;}
unsigned later_rewards_last_fresh(void){return later_reward.fresh;}
int later_rewards_pending(void){return later_reward.phase!=0;}
unsigned later_rewards_quest(unsigned treasure){static const Save4U8 q[4]={21,24,32,40};return treasure<4?q[treasure]:64;}
unsigned later_rewards_gold(unsigned treasure){static const Save4U16 gold[4]={80,100,120,160};return treasure<4?gold[treasure]:0;}
unsigned later_rewards_claimable(const Save5State*s){
 unsigned i,bits=0;
 if(!s||!economy_state_validate(&s->economy,s->campaign.chapter_flags)||
    !save5_later_claims_validate(&s->quests,&s->economy))return 0;
 for(i=0;i<4;++i)if(save5_quest_state(&s->quests,later_rewards_quest(i))==SAVE5_QUEST_CLAIMED)bits|=1u<<i;
 return bits&~s->economy.later_claims;
}
static int later_context_same(const LaterRewardContext*c){
 return c&&c->scene==later_reward.context.scene&&c->room==later_reward.context.room&&
 c->x==later_reward.context.x&&c->y==later_reward.context.y&&
 c->facing==later_reward.context.facing&&c->source_state==later_reward.context.source_state;
}
static unsigned later_source_error(const Save5State*s,unsigned treasure,unsigned source,const LaterRewardContext*c){
 static const Save4U8 areas[7]={29,22,37,30,38,46,0};
 static const Save4U16 xs[7]={120,312,120,400,160,120,56};
 static const Save4U16 ys[7]={108,192,112,192,176,72,100};
 static const Save4U8 owners[7]={0,0,1,1,2,3,255};
 int dx,dy,f,side,radius;
 if(!s||!c||treasure>=4||source>=7||!c->scene||c->facing<0||c->facing>3||
    c->x<0||c->x>511||c->y<0||c->y>511)return LATER_INVALID;
 if(c->room!=areas[source]||s->campaign.room!=(unsigned)c->room||
    (source!=LATER_SOURCE_VILLAGE_SHOP&&owners[source]!=treasure))return LATER_WRONG_SOURCE;
 if(c->source_state!=((source==LATER_SOURCE_NORTH_MACHINE||source==LATER_SOURCE_SOUTH_MACHINE)?5u:0u))return LATER_WRONG_SOURCE;
 dx=c->x-xs[source];dy=c->y-ys[source];
 f=c->facing==1?dy:c->facing==0?-dy:c->facing==2?dx:-dx;
 side=c->facing<2?(dx<0?-dx:dx):(dy<0?-dy:dy);
 if(source==LATER_SOURCE_UNDERWATER_KEEPER)
  return f>=6&&f<=26&&side<=10&&side<=f/2?LATER_OK:LATER_WRONG_SOURCE;
 if(dx<0)dx=-dx;
 if(dy<0)dy=-dy;
 radius=source<=1?24:source<=3?18:source==4?23:22;
 if(dx+dy>=radius)return LATER_WRONG_SOURCE;
 if(source>=2&&source<=4){
  if(f< -8)return LATER_WRONG_SOURCE;
  if(source!=LATER_SOURCE_SOUTH_MACHINE&&side>f+4)return LATER_WRONG_SOURCE;
 }
 return LATER_OK;
}
unsigned later_rewards_check(const Save5State*s,unsigned treasure,unsigned source,const LaterRewardContext*c){
 unsigned error=later_source_error(s,treasure,source,c),q,state;
 if(error)return error;
 if(!economy_state_validate(&s->economy,s->campaign.chapter_flags)||
    !save5_later_claims_validate(&s->quests,&s->economy))return LATER_INVALID;
 q=later_rewards_quest(treasure);state=save5_quest_state(&s->quests,q);
 if(s->economy.later_claims&(1u<<treasure))return LATER_ALREADY_OWNED;
 if((state!=SAVE5_QUEST_READY&&state!=SAVE5_QUEST_CLAIMED)||
    (source==LATER_SOURCE_VILLAGE_SHOP&&state!=SAVE5_QUEST_CLAIMED))return LATER_NOT_EARNED;
 /* All four exact authored masks are15. Full immutable preflight separately
  * checks canonical quest prerequisites, objective sequence, and provenance. */
 if(s->quests.objectives[q]!=15u)return LATER_NOT_EARNED;
 return LATER_OK;
}
static void later_release(unsigned error){
 if(later_reward.token&&save5_preflight_status(later_reward.token)!=SAVE5_FAILED)save5_preflight_cancel();
 later_reward.phase=0;later_reward.token=0;later_reward.live=0;later_reward.error=error;
 if(error){later_reward.gold=later_reward.xp=later_reward.fresh=0;}
}
int later_rewards_cancel(void){
 if(later_reward.phase==3)return 0;
 later_release(LATER_CANCELED);return 1;
}
int later_rewards_begin(Save5State*s,unsigned treasure,unsigned source,const LaterRewardContext*c){
 unsigned error;
 if(later_reward.phase){later_reward.error=LATER_BUSY;return 0;}
 error=later_rewards_check(s,treasure,source,c);later_reward.error=error;
 later_reward.gold=later_reward.xp=later_reward.fresh=0;
 if(error)return 0;
 later_reward.token=save5_preflight_begin(s);
 if(!later_reward.token){later_reward.error=LATER_BUSY;return 0;}
 later_reward.live=s;later_reward.context=*c;later_reward.treasure=treasure;
 later_reward.source=source;later_reward.phase=1;return 1;
}
static int later_stage(void){
 Save5State*s=&scratch.state;unsigned i,q=later_rewards_quest(later_reward.treasure),event=0,n;
 const Save5State*original=save5_preflight_snapshot(later_reward.token);
 if(!original||!save5_preflight_matches(later_reward.token,later_reward.live)){later_reward.error=LATER_STATE_CHANGED;return 0;}
 later_reward.error=later_rewards_check(original,later_reward.treasure,later_reward.source,&later_reward.context);
 if(later_reward.error)return 0;
 later_reward.fresh=save5_quest_state(&s->quests,q)==SAVE5_QUEST_READY;
 later_reward.xp=0;
 if(later_reward.fresh){
  save5_quest_set_state(&s->quests,q,SAVE5_QUEST_CLAIMED);
  s->quests.rewards[q>>3]|=(Save4U8)(1u<<(q&7));
  if(later_reward.treasure>=LATER_BELL){
   event=later_reward.treasure==LATER_BELL?242u:282u;
   for(i=0;i<4;++i){unsigned slot=s->roster.party[i];later_reward.slots[i]=(Save4U8)slot;
    if(slot<160)later_reward.xp+=s->roster.instances[slot].xp;
   }
   if(creatures_credit_event(&s->roster,event,160,CREATURE_CREDIT_PERSONAL_QUEST)<0)return 0;
   n=0;
   for(i=0;i<4;++i){unsigned slot=later_reward.slots[i];if(slot<160){
    later_reward.party[i]=s->roster.instances[slot];later_reward.bond[i]=s->roster.expedition_bond[slot];
    n+=s->roster.instances[slot].xp;
   }}
   later_reward.xp=n-later_reward.xp;
   later_reward.event_byte=s->roster.expedition_events[event>>3];
  }
  later_reward.quest_byte=s->quests.states[q>>2];later_reward.reward_byte=s->quests.rewards[q>>3];
 }
 n=later_rewards_gold(later_reward.treasure);
 if(n>9999u-s->economy.gold)n=9999u-s->economy.gold;
 s->economy.gold=(Save4U16)(s->economy.gold+n);s->economy.earned+=n;
 s->economy.later_claims|=(Save4U8)(1u<<later_reward.treasure);
 if(!economy_state_validate(&s->economy,s->campaign.chapter_flags)||!save5_later_claims_validate(&s->quests,&s->economy))return 0;
 later_reward.economy=s->economy;later_reward.gold=n;
 /* Mutation consumes the sole preflight token before writer admission.
  * Encoded snapshot validation still runs completely before the first write. */
 save5_preflight_cancel();later_reward.token=0;
 writer_status=SAVE5_BUSY;writer_phase=PHASE_META;writer_position=writer_progress=0;
 writer_preemptible=0;writer_economy=1;
 bank_valid[0]=bank_valid[1]=0;bank_sequence[0]=bank_sequence[1]=0;
 later_reward.phase=3;return 1;
}
static void later_publish(void){
 Save5State*s=later_reward.live;unsigned i,q=later_rewards_quest(later_reward.treasure);
 s->economy=later_reward.economy;
 if(!later_reward.fresh)return;
 s->quests.states[q>>2]=later_reward.quest_byte;s->quests.rewards[q>>3]=later_reward.reward_byte;
 if(later_reward.treasure<LATER_BELL)return;
 for(i=0;i<4;++i){unsigned slot=later_reward.slots[i];if(slot<160){
  s->roster.instances[slot]=later_reward.party[i];s->roster.expedition_bond[slot]=later_reward.bond[i];
 }}
 s->roster.expedition_events[(later_reward.treasure==LATER_BELL?242u:282u)>>3]=later_reward.event_byte;
}
unsigned later_rewards_step(const LaterRewardContext*c){
 unsigned status;
 if(!later_reward.phase)return later_reward.error?SAVE5_FAILED:SAVE5_DONE;
 if(later_reward.phase!=3&&!later_context_same(c)){later_release(LATER_STATE_CHANGED);return SAVE5_FAILED;}
 if(later_reward.phase==1){
  status=save5_preflight_step(later_reward.token,480);
  if(status==SAVE5_BUSY)return status;
  if(status!=SAVE5_DONE){later_release(LATER_INVALID);return SAVE5_FAILED;}
  later_reward.phase=2;return SAVE5_BUSY;
 }
 if(later_reward.phase==2){
  if(!later_stage()){later_release(later_reward.error?later_reward.error:LATER_STATE_CHANGED);return SAVE5_FAILED;}
  return SAVE5_BUSY;
 }
 status=save5_step(512);if(status==SAVE5_BUSY)return status;
 if(status==SAVE5_DONE){later_publish();later_release(LATER_OK);return SAVE5_DONE;}
 later_release(LATER_SAVE_FAILED);return SAVE5_FAILED;
}
