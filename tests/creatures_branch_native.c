/* Current reviewed F013 branch; synthetic capability variants remain host-only. */
#include "creatures.h"
#include <assert.h>
#include <string.h>
#ifndef EXPECT_INVALID_CATALOG
static CreatureRoster roster, before;
#endif
int main(void) {
#ifdef EXPECT_INVALID_CATALOG
    assert(!creatures_catalog_validate());
#else
    unsigned target;
    assert(creatures_catalog_validate());
    assert(creatures_evolution_count(37) == 2);
    assert(creatures_evolution(37) == 0);
    assert(creatures_evolution_at(37, 0)->to == 38);
    assert(creatures_evolution_at(37, 1)->to == 39);
    assert(!creatures_evolution_at(37, 2));
    assert(!creatures_evolution_at(37, 0xffffffffu));
    assert(creatures_evolution_to(37, 38)->to == 38);
    assert(creatures_evolution_to(37, 39)->to == 39);
    assert(!creatures_evolution_to(37, 1));
    for (target = 38; target <= 39; ++target) {
        CreatureInstance expected;
        creatures_roster_init(&roster);
        assert(creatures_grant(&roster, 37, 26, 45, 0, 0) == 0);
        assert(!creatures_mark_trial(&roster.instances[0], 1));
        assert(!creatures_mark_trial_qualified(&roster.instances[0], 9, 1));
        assert(creatures_mark_trial_qualified(&roster.instances[0], 13, target-37));
        before = roster;
        assert(creatures_can_evolve(&roster.instances[0], 256, 1) == CREATURE_EVOLVE_AMBIGUOUS);
        assert(creatures_evolve(&roster, 0, 256, 1, 1) == CREATURE_EVOLVE_AMBIGUOUS);
        assert(!memcmp(&roster, &before, sizeof(roster)));
        assert(creatures_evolve_to(&roster, 0, target, 256, 1, 0) == CREATURE_EVOLVE_DEFERRED);
        assert(!memcmp(&roster, &before, sizeof(roster)));
        assert(creatures_evolve_to(&roster, 0, 38 + 256u, 256, 1, 1) == CREATURE_EVOLVE_INVALID);
        assert(creatures_evolve_to(&roster, 0, 25, 256, 1, 1) == CREATURE_EVOLVE_NO_EDGE);
        assert(!memcmp(&roster, &before, sizeof(roster)));
        expected = roster.instances[0]; expected.form_id = (CreatureU8)target; expected.polarity = creatures_form(target)->polarity;
        assert(creatures_evolve_to(&roster, 0, target, 256, 1, 1) == CREATURE_EVOLVE_READY);
        assert(!memcmp(&roster.instances[0], &expected, sizeof(expected)));
        assert(creatures_roster_count(&roster) == 1);
        assert(creatures_roster_validate(&roster));
        assert(creatures_command_learned(target, 1, 49));
        assert(creatures_supports_capability(target, 12));
        assert(!creatures_evolution(target));
    }
#ifdef EXTENDED_CAPABILITY
    assert(!creatures_supports_capability(37, 32));
    assert(creatures_supports_capability(37, 33));
    assert(creatures_supports_capability(38, 33));
    assert(creatures_supports_capability(39, 33));
    assert(creatures_capabilities(37) == FIELD_GROW_ROOTS);
    assert(!creatures_supports_capability(1, 33));
    assert(!creatures_supports_capability(37, 65569));
    assert(creatures_party_supports_capability(&roster, 33));
#endif
#endif
    return 0;
}
