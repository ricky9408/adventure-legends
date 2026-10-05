#ifndef EMBERBOND_WEAPON_ACTIONS_H
#define EMBERBOND_WEAPON_ACTIONS_H
#include "equipment.h"
/* Transient combat state. Never persisted. Call once per PLAY update only:
 * pause, picker, dialogue, save and hit-stop must not advance these clocks. */
enum WeaponPhase { WEAPON_IDLE, WEAPON_WINDUP, WEAPON_ACTIVE,
                   WEAPON_RECOVERY, WEAPON_CHARGING };
enum WeaponEvent { WEAPON_EVENT_START=1, WEAPON_EVENT_ACTIVE=2,
                   WEAPON_EVENT_ARROW=4, WEAPON_EVENT_FINISH=8,
                   WEAPON_EVENT_BLOCKED=16 };
enum { WEAPON_ARROW_CAPACITY=2, WEAPON_TARGET_CAPACITY=16,
       WEAPON_COORDINATE_MAX=1023 };
typedef struct WeaponAttack {
    EquipmentU16 hit_mask;
    EquipmentU8 weapon_class, phase, direction, move, age, charge;
    EquipmentU8 combo, combo_clock, buffer, suppress_until_release;
    EquipmentU8 damage_q4, attack_q4, reach_px, half_width_px;
    EquipmentU8 stagger, element, arrow_pending, reserved;
} WeaponAttack;
typedef struct WeaponArrow {
    int x_q8, y_q8;
    EquipmentU16 remaining_q8, speed_q8;
    EquipmentU8 active, direction, damage_q4, attack_q4;
    EquipmentU8 stagger, element, reserved[2];
} WeaponArrow;
/* Direction follows the engine: down0/up1/left2/right3. Stats are already
 * derived/cached. Invalid input is a no-op, never an implicit cancellation.
 * held/pressed are normalized booleans. live_arrows includes every still-live
 * player arrow. Emitted ARROW must be spawned by the caller in the same update.
 * A short tap is latched until the four-update bow draw finishes. */
void weapon_action_init(WeaponAttack *action);
unsigned weapon_action_tick(WeaponAttack *action,const EquipmentStats *stats,
                            unsigned direction,int held,int pressed,
                            unsigned live_arrows);
/* Before entering a modal or a rolling/transition state, clear queued attacks
 * and cancel an un-fired bow draw. Already committed melee/recovery clocks and
 * combo remain unchanged. No surprise shot or held-A attack after returning. */
void weapon_action_suspend(WeaponAttack *action);
unsigned weapon_action_busy(const WeaponAttack *action,unsigned live_arrows);
/* Pure geometry plus per-swing hit ledger. Caller checks line of sight before
 * marking a hit. False/blocked targets must not consume their ledger bit. */
int weapon_action_contains(const WeaponAttack *action,int origin_x,int origin_y,
                           int target_x,int target_y);
int weapon_action_can_hit(const WeaponAttack *action,unsigned target_id);
int weapon_action_mark_hit(WeaponAttack *action,unsigned target_id);
/* Mundane arrows have no field capability tags. Spawn snapshots attack damage;
 * a release at the live-arrow cap consumes normal recovery with BLOCKED, never
 * overwrites an existing arrow. Coordinates are world pixels. */
int weapon_arrow_spawn(WeaponArrow *arrow,WeaponAttack *action,int x,int y);
/* Each pixel of travel is visited, wall first then target. Return nonzero from
 * either callback to stop. Target callback may apply one hit using this arrow's
 * immutable stats. It is never called behind a blocking pixel. */
typedef int (*WeaponPointTest)(void *context,int x,int y);
void weapon_arrow_tick(WeaponArrow *arrow,WeaponPointTest solid,
                       WeaponPointTest target,void *context);
#endif
