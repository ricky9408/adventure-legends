#ifndef EMBERBOND_STORY_REWARDS_H
#define EMBERBOND_STORY_REWARDS_H
#include "save5.h"
/* Original campaign rewards, scheduled behind EVENT_PENDING. No SRAM writes,
 * extra save copy, heap or IWRAM. The existing immutable preflight scratch and
 * bounded admission cursor own all validation until an exact atomic commit. */
int story_rewards_begin(Save5State *live,unsigned chapters);
int story_rewards_pending(void);
unsigned story_rewards_step(void);
void story_rewards_cancel(void);
unsigned story_rewards_state_bytes(void);
#endif
