#include "economy.h"
/* One small owner; reuse existing immutable preflight and bank scratch. */
static struct {
 Save5State*live;Save4U32 token;EconomyState next;
 unsigned phase,operation,item,error,gold;
} transaction;
enum {BUY=1,USE=2,CLAIM=3};
unsigned economy_state_bytes(void){return sizeof transaction;}
unsigned economy_last_error(void){return transaction.error;}
unsigned economy_last_gold(void){return transaction.gold;}
unsigned economy_gold(const Save5State*s){return s?s->economy.gold:0;}
unsigned economy_supply_count(const Save5State*s,unsigned i){return s&&i<2?s->economy.supplies[i]:0;}
unsigned economy_heart_bonus(const Save5State*s){return s&&!!(s->economy.relics&1u);}
unsigned economy_attack_bonus(const Save5State*s){return s?(unsigned)s->economy.upgrade+!!(s->economy.relics&4u):0;}
unsigned economy_power_reduction(const Save5State*s){return s?((s->economy.relics&2u)?8u:0u)+((s->economy.later_claims&4u)?4u:0u):0;}
unsigned economy_speed_bonus(const Save5State*s){return s&&(s->economy.later_claims&1u)?16u:0u;}
unsigned economy_defense_bonus(const Save5State*s){return s&&(s->economy.later_claims&2u)?2u:0u;}
unsigned economy_later_heart_bonus(const Save5State*s){return s&&!!(s->economy.later_claims&8u);}
unsigned economy_claimable(const Save5State*s){return s&&economy_state_validate(&s->economy,s->campaign.chapter_flags)?(s->campaign.chapter_flags&7u)&~s->economy.boss_claims:0;}
unsigned economy_price(unsigned i){static const unsigned short p[3]={18,24,120};return i<3?p[i]:0;}
unsigned economy_boss_gold(unsigned i){static const unsigned short p[3]={60,100,160};return i<3?p[i]:0;}
static unsigned add_gold(EconomyState*e,unsigned n){unsigned room=9999u-e->gold;if(n>room)n=room;e->gold=(unsigned short)(e->gold+n);e->earned+=n;return n;}
unsigned economy_award_combat(Save5State*s,unsigned n){if(!s||transaction.phase||save5_preflight_active()||(!economy_state_validate(&s->economy,s->campaign.chapter_flags)||!save5_later_claims_validate(&s->quests,&s->economy)))return 0;return add_gold(&s->economy,n);}
int economy_pending(void){return transaction.phase!=0;}
int economy_cancel(void){
 if(transaction.phase==3)return 0;
 if(transaction.token&&save5_preflight_status(transaction.token)!=SAVE5_FAILED)save5_preflight_cancel();
 transaction.phase=0;transaction.token=0;transaction.live=0;transaction.gold=0;return 1;
}
static unsigned prepare(const Save5State*s,unsigned operation,unsigned item,EconomyState*next){
 unsigned price;
 if(!s||!economy_state_validate(&s->economy,s->campaign.chapter_flags)||!save5_later_claims_validate(&s->quests,&s->economy))return ECONOMY_INVALID;
 *next=s->economy;
 if(operation==BUY){
  if(s->campaign.room!=0)return ECONOMY_NOT_IN_VILLAGE;
  price=economy_price(item);if(!price)return ECONOMY_INVALID;
  if(item==2&&next->upgrade)return ECONOMY_ALREADY_OWNED;
  if(item<2&&(next->supplies[item]>=9||next->bought[item]==65535u))return ECONOMY_FULL;
  if(next->gold<price)return ECONOMY_NO_GOLD;
  next->gold=(unsigned short)(next->gold-price);next->spent+=price;
  if(item<2){++next->supplies[item];++next->bought[item];}else next->upgrade=1;
 }else if(operation==USE){
  if(item>=2)return ECONOMY_INVALID;
  if(!next->supplies[item])return ECONOMY_EMPTY;
  --next->supplies[item];++next->used[item];
 }else if(operation==CLAIM){
  static const unsigned char rooms[3]={3,8,13};unsigned mask;
  if(item>=3)return ECONOMY_INVALID;
  mask=1u<<item;
  if(!(s->campaign.chapter_flags&mask))return ECONOMY_NOT_EARNED;
  if(next->boss_claims&mask)return ECONOMY_ALREADY_OWNED;
  if(s->campaign.room&&s->campaign.room!=rooms[item])return ECONOMY_NOT_IN_VILLAGE;
  next->boss_claims|=(unsigned char)mask;next->relics|=(unsigned char)mask;
  add_gold(next,economy_boss_gold(item));
 }else return ECONOMY_INVALID;
 return economy_state_validate(next,s->campaign.chapter_flags)?ECONOMY_OK:ECONOMY_INVALID;
}
static int begin(Save5State*s,unsigned operation,unsigned item){
 unsigned error;
 if(transaction.phase){transaction.error=ECONOMY_BUSY;return 0;}
 error=prepare(s,operation,item,&transaction.next);transaction.error=error;transaction.gold=0;if(error)return 0;
 transaction.token=save5_preflight_begin(s);if(!transaction.token){transaction.error=ECONOMY_BUSY;return 0;}
 transaction.live=s;transaction.operation=operation;transaction.item=item;transaction.phase=1;return 1;
}
int economy_begin_purchase(Save5State*s,unsigned item){return begin(s,BUY,item);}
int economy_begin_use(Save5State*s,unsigned item){return begin(s,USE,item);}
int economy_begin_claim(Save5State*s,unsigned item){return begin(s,CLAIM,item);}
unsigned economy_step(void){
 unsigned status;const Save5State*s;
 if(!transaction.phase)return transaction.error?SAVE5_FAILED:SAVE5_DONE;
 if(transaction.phase==1){
  status=save5_preflight_step(transaction.token,480);if(status==SAVE5_BUSY)return status;
  if(status!=SAVE5_DONE){transaction.error=ECONOMY_INVALID;economy_cancel();return SAVE5_FAILED;}
  transaction.phase=2;return SAVE5_BUSY;
 }
 if(transaction.phase==2){
  s=save5_preflight_snapshot(transaction.token);
  if(!s||!save5_preflight_matches(transaction.token,transaction.live)){transaction.error=ECONOMY_STATE_CHANGED;economy_cancel();return SAVE5_FAILED;}
  transaction.error=prepare(s,transaction.operation,transaction.item,&transaction.next);
  if(transaction.error){economy_cancel();return SAVE5_FAILED;}
  transaction.gold=transaction.operation==CLAIM?transaction.next.gold-s->economy.gold:0;
  if(!save5_preflight_store_economy(transaction.token,transaction.live,&transaction.next)){transaction.error=ECONOMY_STATE_CHANGED;economy_cancel();return SAVE5_FAILED;}
  transaction.token=0;transaction.phase=3;return SAVE5_BUSY;
 }
 status=save5_step(512);if(status==SAVE5_BUSY)return status;
 if(status==SAVE5_DONE){transaction.live->economy=transaction.next;transaction.error=ECONOMY_OK;}
 else{transaction.error=ECONOMY_SAVE_FAILED;transaction.gold=0;}
 transaction.phase=0;transaction.live=0;return status==SAVE5_DONE?SAVE5_DONE:SAVE5_FAILED;
}
