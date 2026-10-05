#include "creatures.h"
#include <assert.h>
#include <stddef.h>
static CreatureRoster roster;
static unsigned rng = 314159u;
static unsigned roll(void) { rng = rng * 1664525u + 1013904223u; return rng; }
int main(void) {
    unsigned i;
    assert(creatures_catalog_validate());
    assert(creatures_migrate_legacy(&roster, 7, 3));
    assert(offsetof(CreatureInstance, cosmetic_seed) == 20);
    for (i = 0; i < 12000; ++i) {
        unsigned n = roll(), slot = (n >> 8) & 3;
        CreatureInstance *c = &roster.instances[slot];
        switch (n & 7) {
        case 0: creatures_credit_event(&roster, n % 384, n >> 23, CREATURE_CREDIT_ENCOUNTER); break;
        case 1: creatures_credit_event(&roster, 384 + n % 128, n >> 24, CREATURE_CREDIT_FIELD_AID); break;
        case 2: creatures_mark_trial(c, 1u << slot); break;
        case 3: creatures_evolve(&roster, slot, 7, 1, (n >> 7) & 1); break;
        case 4: creatures_begin_expedition(&roster); break;
        case 5: creatures_add_xp(c, n); break;
        case 6: creatures_equip(c, 1, slot + 5); break;
        default: creatures_select_command(c, (n >> 6) & 1); break;
        }
        assert(creatures_roster_validate(&roster));
    }
    return 0;
}
