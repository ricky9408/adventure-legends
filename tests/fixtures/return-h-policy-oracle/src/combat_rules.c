#include "combat_rules.h"

typedef char CombatIntMustBe4Bytes[(sizeof(int) == 4) ? 1 : -1];

unsigned combat_phase_multiplier_q8(unsigned attacker, unsigned defender) {
    if ((attacker >= CREATURE_PHASE_COUNT && attacker != COMBAT_NEUTRAL_PHASE) ||
        (defender >= CREATURE_PHASE_COUNT && defender != COMBAT_NEUTRAL_PHASE)) return 0;
    if (attacker == COMBAT_NEUTRAL_PHASE || defender == COMBAT_NEUTRAL_PHASE) return 256;
    return creatures_phase_multiplier_q8(attacker, defender);
}
unsigned combat_damage_q4(unsigned base, unsigned attack, unsigned defense,
                          unsigned attacker, unsigned defender, int immune) {
    unsigned multiplier;
    int scaled;
    if (immune) return 0;
    if (!base || base > COMBAT_MAX_DAMAGE_Q4 || attack > EQUIPMENT_MAX_ATTACK_Q4 ||
        defense > COMBAT_MAX_DAMAGE_Q4) return 0;
    multiplier = combat_phase_multiplier_q8(attacker, defender);
    if (!multiplier) return 0;
    /* Maximum product + rounding is (255 + 24) * 320 + 128 = 89,408.
     * The explicit signed 32-bit intermediate is safe; 16-bit is not. */
    scaled = (((int)base + (int)attack) * (int)multiplier + 128) >> 8;
    scaled -= (int)defense;
    if (scaled < COMBAT_MIN_DAMAGE_Q4) return COMBAT_MIN_DAMAGE_Q4;
    if (scaled > COMBAT_MAX_DAMAGE_Q4) return COMBAT_MAX_DAMAGE_Q4;
    return (unsigned)scaled;
}
int combat_field_allows(CreatureU32 caps, CreatureU32 required) {
    return required && !(caps & ~COMBAT_FIELD_CAPS_MASK) &&
           !(required & ~COMBAT_FIELD_CAPS_MASK) && (caps & required) == required;
}
