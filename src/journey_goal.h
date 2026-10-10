#ifndef EMBER_JOURNEY_GOAL_H
#define EMBER_JOURNEY_GOAL_H
#include "save5.h"
/* Read-only guidance. Names become available with their existing story gate;
 * no visit, quest, reward, party, or save field is changed by inspection. */
typedef struct JourneyGoal { int title, detail; unsigned target, stage; } JourneyGoal;
enum { JOURNEY_LIGHTS, JOURNEY_RIVER, JOURNEY_NORTH, JOURNEY_SOUTH,
 JOURNEY_MAGMA, JOURNEY_UNDERWATER, JOURNEY_RETURN, JOURNEY_HORIZONS,
 JOURNEY_COVENANTS, JOURNEY_HOME };
JourneyGoal journey_goal_read(const Save5State *save,unsigned chapter_flags,unsigned current_room);
#endif
