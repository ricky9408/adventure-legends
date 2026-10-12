#ifndef EMBER_GROWTH_GOALS_H
#define EMBER_GROWTH_GOALS_H
#include "creatures.h"
/* Read-only display model. Every gate is reported independently, never just
 * the first denial. No roster, save, command or evolution token is changed. */
enum { GROWTH_LEVEL=1,GROWTH_BOND=2,GROWTH_STORY=4,GROWTH_TRIAL=8,GROWTH_REST=16,GROWTH_ALL=31 };
typedef struct { unsigned target,min_level,min_bond,met; CreatureU32 next_xp; } GrowthGoal;
int growth_goals_query(const CreatureInstance*,unsigned target,unsigned context,int sanctuary,GrowthGoal*);
unsigned growth_goals_trial_text(unsigned from,unsigned target,unsigned line);
void growth_goals_text(unsigned label,int x,int y,int color);
void growth_goals_center(unsigned label,int y,int color);
int growth_goals_number(unsigned value,unsigned places,int x,int y,int color);
/* pages:0 all goals,1 authored personal-trial clues,2 new technique/role.
 * confirm=0 is inspection,1 single-edge confirmation,2 branch confirmation. */
void growth_goals_draw(const CreatureInstance*,unsigned target,unsigned context,int sanctuary,unsigned page,int confirm,int preparing);
#endif
