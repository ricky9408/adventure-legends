#ifndef EMBERBOND_FIELD_CONTROLS_H
#define EMBERBOND_FIELD_CONTROLS_H
/* Physical field controls meet the existing power modules at one boundary.
 * Their internal 256-bit action is semantic, rather than a physical R key.
 * A fresh R owns a B/R chord; B must be physically released before it can
 * start/hold a power again. Modal B cancellation never passes this boundary. */
enum { FIELD_POWER_B=2, FIELD_COMPANION_R=256, FIELD_POWER_ACTION=256 };
typedef struct { unsigned char power_blocked; } FieldControlState;
typedef struct { unsigned power_pressed,power_held,companion_pressed; } FieldControlInput;
static inline void field_controls_reset(FieldControlState *state,unsigned held) {
 state->power_blocked=(unsigned char)((held&FIELD_POWER_B)!=0);
}
static inline FieldControlInput field_controls_read(FieldControlState *state,
                                                    unsigned held,unsigned pressed) {
 FieldControlInput input;
 if(!(held&FIELD_POWER_B))state->power_blocked=0;
 if((held&(FIELD_COMPANION_R|FIELD_POWER_B))==(FIELD_COMPANION_R|FIELD_POWER_B))state->power_blocked=1;
 input.power_pressed=pressed&~(FIELD_POWER_B|FIELD_COMPANION_R);
 input.power_held=held&~(FIELD_POWER_B|FIELD_COMPANION_R);
 if(!state->power_blocked&&(held&FIELD_POWER_B)) {
  input.power_held|=FIELD_POWER_ACTION;
  if(pressed&FIELD_POWER_B)input.power_pressed|=FIELD_POWER_ACTION;
 }
 input.companion_pressed=pressed&FIELD_COMPANION_R;
 return input;
}
#endif
