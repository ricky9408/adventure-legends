#include "save5.h"
#include <assert.h>
#include <stdio.h>
int underwater_test_completed(Save5State *,unsigned);
static Save5State state;
int main(void){unsigned room,spawn,status,token,n,expected,checked=0;static const unsigned masks[]={31,15,1,1,1,1,1,1,15,7,7,3,3,7,7,3};
 assert(!underwater_test_completed(&state,0));state.quests.anchors[3]=3;state.quests.anchors[4]=3;
 for(room=38;room<256;++room)for(spawn=0;spawn<256;++spawn){state.campaign.room=(Save4U8)room;state.campaign.spawn=(Save4U8)spawn;expected=room<54&&spawn<8&&!!(masks[room-38]&(1u<<spawn));
  assert(save5_validate(&state)==(int)expected);assert(save5_validate_revision(&state,6)==(int)expected);
  token=save5_preflight_begin(&state);assert(token);n=0;do{status=save5_preflight_step(token,640);assert(++n<300);}while(status==SAVE5_BUSY);
  assert(status==(expected?SAVE5_DONE:SAVE5_FAILED));save5_preflight_cancel();++checked;
 }
 printf("sanitized exact spawn-mask/current/revision6/preflight cases: %u passed\n",checked);return 0;}
