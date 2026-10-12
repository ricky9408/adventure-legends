#ifndef ADVENTURE_ENEMY_TYPES_H
#define ADVENTURE_ENEMY_TYPES_H
enum { ENEMY_SLIME=0, ENEMY_SENTRY=1, ENEMY_RANGER=2, ENEMY_LANE_CHARGER=3 };
/* Bosses use their separate runtime. Negative/corrupt/unsupported pool kinds
 * remain excluded; the lane charger is an ordinary melee actor. */
static inline int enemy_kind_is_ordinary(int kind){return (unsigned)kind<=ENEMY_LANE_CHARGER;}
static inline int enemy_kind_is_melee(int kind){return enemy_kind_is_ordinary(kind)&&kind!=ENEMY_RANGER;}
#endif
