#ifndef ADVENTURE_RECRUIT_NOTICE_H
#define ADVENTURE_RECRUIT_NOTICE_H
#include "creatures.h"
/* Content12 economy reserved[1] records explicit inspection of the two
 * automatic post-boss story recruits. No party/individual/reward is awarded. */
int recruit_notice_pending(const CreatureInstance *creature);
int recruit_notice_acknowledge(const CreatureInstance *creature);
int recruit_notice_world(unsigned form);
void recruit_notice_badge(int x,int y);
#endif
