#ifndef EMBERBOND_REGIONAL_SHOP_H
#define EMBERBOND_REGIONAL_SHOP_H
#include "save5.h"
/* Traveling suppliers stand beside the arrival road, away from authored
 * quest actors, reset props, anchors and exits. No solid or route is added. */
static inline unsigned regional_shop_region(unsigned room){
 static const unsigned char rooms[8]={16,22,30,38,46,54,62,70};unsigned i;
 for(i=0;i<8;++i)if(room==rooms[i])return i;
 return 8;
}
static inline int regional_shop_position(unsigned room,int*x,int*y){
 static const short xs[8]={208,240,160,304,304,208,208,208};
 static const short ys[8]={284,272,272,284,284,284,284,284};
 unsigned region=regional_shop_region(room);if(region>=8)return 0;
 if(x)*x=xs[region];
 if(y)*y=ys[region];
 return 1;
}
static inline int regional_shop_available(const Save5State*s,unsigned item){
 unsigned region;if(!s)return 0;if(s->campaign.room==0)return item<3;
 region=regional_shop_region(s->campaign.room);
 return region<8&&(s->quests.region_flags[region]&1u)&&item<4u+region;
}
#endif
