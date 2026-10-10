#ifndef EMBERBOND_COMBAT_RULES_H
#define EMBERBOND_COMBAT_RULES_H
#include "equipment.h"
#include "creatures.h"
enum { COMBAT_NEUTRAL_PHASE = 255, COMBAT_MIN_DAMAGE_Q4 = 4,
       COMBAT_MAX_DAMAGE_Q4 = 255, COMBAT_FIELD_CAPS_MASK = (1u << 21) - 1u };
/* 0 invalid. Neutral on either side is exactly 256; all elemental pairs call
 * the creature resolver so there is one authoritative five-phase relation. */
unsigned combat_phase_multiplier_q8(unsigned attacker_phase, unsigned defender_phase);
/* 0 for immunity OR invalid/non-damaging inputs. base=1..255, attack=0..24,
 * defense=0..255. The player defense cap of 8 is imposed by equipment_derive.
 * Round product half-up, subtract defense, then clamp [4,255]. Immunity is
 * handled before that minimum. No polarity or owner-derived bonuses. */
unsigned combat_damage_q4(unsigned base_damage_q4, unsigned attack_bonus_q4,
                          unsigned target_defense_q4, unsigned attacker_phase,
                          unsigned defender_phase, int immune);
/* A field event requires explicit capabilities. Neither friendly ownership
 * nor a fire phase implies ignite. Mundane arrows pass tags=0. */
int combat_field_allows(CreatureU32 field_caps, CreatureU32 required_caps);
#endif
