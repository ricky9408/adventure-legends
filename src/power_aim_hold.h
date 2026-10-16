#ifndef EMBERBOND_POWER_AIM_HOLD_H
#define EMBERBOND_POWER_AIM_HOLD_H
/* Optional anticipation only: holding the semantic power action buys input time,
 * never more live damage/field frames. Engine calls input before the PLAY-only tick.
 * Cooldown remains engine-owned and continues; no save/OBJ/IWRAM allocation. */
enum { POWER_AIM_HOLD_UPDATES = 90, POWER_AIM_ACTION = 256 };
typedef struct { unsigned char held,updates; } PowerAimHold;
static inline void power_aim_hold_reset(PowerAimHold *hold) {
 hold->held=hold->updates=0;
}
static inline int power_aim_hold_input(PowerAimHold *hold,unsigned keys,int eligible) {
 hold->held=(unsigned char)(eligible&&(keys&POWER_AIM_ACTION)&&hold->updates<POWER_AIM_HOLD_UPDATES);
 return hold->held;
}
static inline int power_aim_hold_tick(PowerAimHold *hold) {
 if(hold->held&&hold->updates<POWER_AIM_HOLD_UPDATES){hold->updates++;return 1;}
 hold->held=0;return 0;
}
#endif
