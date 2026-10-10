#ifndef ADVENTURE_LEGENDS_ECONOMY_TYPES_H
#define ADVENTURE_LEGENDS_ECONOMY_TYPES_H
/* Content10 only; explicitly encoded at5056. Migration starts entirely zero. */
typedef struct EconomyState {
 unsigned int earned,spent;
 unsigned short gold,bought[2],used[2];
 unsigned char supplies[2],relics,upgrade,boss_claims,reserved[9];
} EconomyState;
enum {
 ECONOMY_GOLD_CAP=9999,ECONOMY_SUPPLY_CAP=9,ECONOMY_STATE_BYTES=32,
 ECONOMY_HEART_TONIC=0,ECONOMY_SPIRIT_TONIC=1,ECONOMY_IRON_EDGE=2,
 ECONOMY_SHOP_ITEMS=3,ECONOMY_GROVE=0,ECONOMY_SKY=1,ECONOMY_CORE=2,
 ECONOMY_BOSS_COUNT=3,ECONOMY_HEART_PRICE=18,ECONOMY_SPIRIT_PRICE=24,
 ECONOMY_EDGE_PRICE=120,ECONOMY_GROVE_GOLD=60,ECONOMY_SKY_GOLD=100,
 ECONOMY_CORE_GOLD=160
};
/* Header-local validation keeps existing standalone codec host builds valid. */
static inline int economy_state_validate(const EconomyState*e,unsigned chapters){
 unsigned i,spent;
 if(!e||e->gold>9999||e->upgrade>1||e->relics>7||e->boss_claims!=e->relics||
    (e->relics&~chapters)||e->earned<e->spent||e->earned-e->spent!=e->gold)return 0;
 for(i=0;i<9;++i)if(e->reserved[i])return 0;
 for(i=0;i<2;++i)if(e->used[i]>e->bought[i]||e->supplies[i]>9||
    (unsigned)(e->bought[i]-e->used[i])!=e->supplies[i])return 0;
 spent=(unsigned)e->bought[0]*18u+(unsigned)e->bought[1]*24u+(unsigned)e->upgrade*120u;
 return e->spent==spent&&e->earned>=((e->relics&1u)?60u:0u)+
   ((e->relics&2u)?100u:0u)+((e->relics&4u)?160u:0u);
}
#endif
