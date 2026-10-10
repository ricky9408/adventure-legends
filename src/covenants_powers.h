#ifndef EMBERBOND_COVENANTS_POWERS_H
#define EMBERBOND_COVENANTS_POWERS_H
/* One finite original legendary effect, commands12 and122..128. Shared engine
 * cooldown is never refunded. Tick/input only in active PLAY, after held-L,
 * menu, dialogue and hitstop gates. Viewing a menu must NOT revoke the cast. */
extern int covenants_power_kind,covenants_power_time,covenants_power_form;
extern int covenants_power_direction,covenants_power_origin_x,covenants_power_origin_y;
extern int covenants_power_age,covenants_power_cooldown,covenants_power_cast_time,covenants_power_phase;
typedef struct {
    unsigned instance;
    unsigned char slot,form,equipped[2],selected_command,polarity;
} CovenantsPowerMember;
typedef struct {
    unsigned caster,token,scene,attempt,geometry,action_serial;
    CovenantsPowerMember party[4];
    short origin_x,origin_y,area;
    unsigned char form,command,direction,selected_party,owner_slot;
} CovenantsPowerProof;
/* Read-only exact live proof. NULL after revocation, expiry or identity change.
 * Neither this pointer nor overlap alone authorizes a durable world reward. */
const CovenantsPowerProof *covenants_powers_proof(void);
int covenants_power(unsigned command);
int covenants_powers_busy(void);
int covenants_powers_cast_matches_selected(void);
void covenants_powers_selection_changed(void);
void covenants_powers_geometry_changed(void);
void covenants_powers_enemy_spawn(unsigned index);
void covenants_powers_shot_spawn(unsigned index);
void covenants_powers_reset(void);
void covenants_powers_tick(void);
void covenants_powers_draw(void);
/* Deliberate placement/facing at cast is immutable; no post-cast aim override.
 * R may release the Orrery after30 ward updates. Surviving drops only become
 * counter-shots. Kilnwhorl automatically releases after36 active updates. */
int covenants_powers_input(unsigned pressed);
int covenants_powers_can_release(void);
enum { COVENANTS_POWER_HINT_NONE,COVENANTS_POWER_HINT_WARD,
       COVENANTS_POWER_HINT_BANK,COVENANTS_POWER_HINT_HOLD,
       COVENANTS_POWER_HINT_GAP,COVENANTS_POWER_HINT_WAIT };
unsigned covenants_powers_hint(void);
int covenants_powers_companion_pose(void);
int covenants_powers_intercept_shot(unsigned index,int from_x,int from_y,
                                  int to_x,int to_y,int ordinary_hostile);
/* Exact visible nontransparent diamond pixels vs target octagon, bounded LOS.
 * Geometry edits revoke field rights for the entire lifetime of this cast. */
int covenants_powers_overlap(int x,int y,int radius);
unsigned covenants_powers_cast_token(void);
unsigned covenants_powers_caster_id(void);
unsigned covenants_powers_moving_objects(void);
unsigned covenants_powers_beat(void);
unsigned covenants_powers_release_phase(void);
/* Engine must pass its CURRENT authored boss exposure/immunity result. A
 * successful query consumes at most one boss contact/cast, returns base Q4,
 * and caller uses its existing boss damage resolver. No exposure/state writes. */
unsigned covenants_powers_boss_damage(int x,int y,int radius,int eligible);
unsigned covenants_powers_state_bytes(void);
#endif
