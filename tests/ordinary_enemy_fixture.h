#ifndef ADVENTURE_ORDINARY_ENEMY_FIXTURE_H
#define ADVENTURE_ORDINARY_ENEMY_FIXTURE_H
#include "enemy_types.h"
/* Run the real power suites against both the established ordinary actor and
 * the charger. Explicit ranger and unsupported-kind fixtures keep their role. */
static inline int test_ordinary_enemy_kind(int kind){
#ifdef CHARGER_POWER_REGRESSION
 return kind==ENEMY_SLIME?ENEMY_LANE_CHARGER:kind;
#else
 return kind;
#endif
}
#endif
