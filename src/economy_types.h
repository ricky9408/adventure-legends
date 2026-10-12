#ifndef ADVENTURE_LEGENDS_ECONOMY_TYPES_H
#define ADVENTURE_LEGENDS_ECONOMY_TYPES_H
/* Content10 wallet; content11 adds later_claims at byte23 (wire5079).
 * Content12 uses reserved[0] for eight paid unique gear receipts and
 * reserved[1] for the inspected-story mask. Bank size/field offsets are stable. */
typedef struct EconomyState {
 unsigned int earned,spent;
 unsigned short gold,bought[2],used[2];
 unsigned char supplies[2],relics,upgrade,boss_claims,later_claims,reserved[8];
} EconomyState;
enum {
 ECONOMY_GOLD_CAP=9999,ECONOMY_SUPPLY_CAP=9,ECONOMY_STATE_BYTES=32,
 ECONOMY_HEART_TONIC=0,ECONOMY_SPIRIT_TONIC=1,ECONOMY_IRON_EDGE=2,
 ECONOMY_SHOP_ITEMS=3,ECONOMY_GROVE=0,ECONOMY_SKY=1,ECONOMY_CORE=2,
 ECONOMY_BOSS_COUNT=3,ECONOMY_HEART_PRICE=18,ECONOMY_SPIRIT_PRICE=24,
 ECONOMY_EDGE_PRICE=120,ECONOMY_GROVE_GOLD=60,ECONOMY_SKY_GOLD=100,
 ECONOMY_CORE_GOLD=160
};
enum {ECONOMY_GEAR_COUNT=8,ECONOMY_GEAR_MASK_BYTE=0,ECONOMY_STORY_MASK_BYTE=1,
      ECONOMY_STORY_WIND=1,ECONOMY_STORY_STONE=2};
/* Prices and identities are persistent content12 receipts. Never reorder. */
static inline unsigned economy_gear_item(unsigned index){
 static const unsigned char items[8]={2,49,67,85,54,68,86,6};return index<8?items[index]:0;
}
static inline unsigned economy_gear_price(unsigned index){
 static const unsigned short prices[8]={96,144,180,216,252,288,324,360};return index<8?prices[index]:0;
}
static inline unsigned economy_gear_spent(unsigned mask){
 unsigned i,total=0;for(i=0;i<8;++i)if(mask&(1u<<i))total+=economy_gear_price(i);return total;
}
static inline unsigned economy_story_inspected(const EconomyState*e){return e?e->reserved[ECONOMY_STORY_MASK_BYTE]:0;}
/* Header-local validation keeps existing standalone codec host builds valid. */
static inline int economy_state_validate(const EconomyState*e,unsigned chapters){
 unsigned i,spent;
 if(!e||e->gold>9999||e->upgrade>1||e->relics>7||e->later_claims>15||e->boss_claims!=e->relics||
    (e->relics&~chapters)||e->earned<e->spent||e->earned-e->spent!=e->gold)return 0;
 if(e->reserved[ECONOMY_STORY_MASK_BYTE]>3||
    ((e->reserved[ECONOMY_STORY_MASK_BYTE]&ECONOMY_STORY_WIND)&&!(chapters&1u))||
    ((e->reserved[ECONOMY_STORY_MASK_BYTE]&ECONOMY_STORY_STONE)&&!(chapters&2u)))return 0;
 for(i=2;i<8;++i)if(e->reserved[i])return 0;
 for(i=0;i<2;++i)if(e->used[i]>e->bought[i]||e->supplies[i]>9||
    (unsigned)(e->bought[i]-e->used[i])!=e->supplies[i])return 0;
 spent=(unsigned)e->bought[0]*18u+(unsigned)e->bought[1]*24u+(unsigned)e->upgrade*120u+
   economy_gear_spent(e->reserved[ECONOMY_GEAR_MASK_BYTE]);
 /* All authored boss awards total780, below the wallet cap. A clipped
  * payout implies earned>=9999, so this lower bound remains necessary. */
 return e->spent==spent&&e->earned>=((e->relics&1u)?60u:0u)+
   ((e->relics&2u)?100u:0u)+((e->relics&4u)?160u:0u)+
   ((e->later_claims&1u)?80u:0u)+((e->later_claims&2u)?100u:0u)+
   ((e->later_claims&4u)?120u:0u)+((e->later_claims&8u)?160u:0u);
}
/* Historical wallet semantics stay exact even after current rules expand. */
static inline int economy_state_validate_revision(const EconomyState*e,unsigned chapters,unsigned revision){
 unsigned i;if(revision<10||revision>12)return 0;
 if(revision<12){for(i=0;i<8;++i)if(e->reserved[i])return 0;if(revision==10&&e->later_claims)return 0;}
 return economy_state_validate(e,chapters);
}
#endif
