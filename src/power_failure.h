#ifndef EMBERBOND_POWER_FAILURE_H
#define EMBERBOND_POWER_FAILURE_H
#include "ui.h"
enum PowerFailure { POWER_FAILURE_NONE, POWER_FAILURE_WAIT, POWER_FAILURE_BLOCKED,
                    POWER_FAILURE_MISMATCH, POWER_FAILURE_AIM };
static inline int power_failure_text(enum PowerFailure reason){
    if(reason==POWER_FAILURE_WAIT)return TX_COOLDOWN;
    if(reason==POWER_FAILURE_BLOCKED)return TX_MG_BLOCKED;
    if(reason==POWER_FAILURE_MISMATCH)return TX_C_POWER_MISMATCH;
    return TX_SP_AIM_CLEAR;
}
#endif
