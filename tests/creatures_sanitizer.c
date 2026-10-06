/* Host-only deterministic state-machine and byte-mutation safety test.
 * This grants core data directly; native acquisition routes are tested elsewhere. */
#include "creatures.h"
#include <assert.h>
#include <stddef.h>
#include <string.h>
static CreatureRoster roster, snapshot, mutated;
static unsigned rng = 314159u;
static unsigned roll(void) { rng = rng * 1664525u + 1013904223u; return rng; }

int main(void) {
    unsigned i, j, b;
    static const unsigned enabled[] = {1,2,4,5,7,8,10,11,13,14,16,19,20,22,23,73,74,75,76,77,78};
    static const CreatureU8 parties[][4] = {{0,1,2,3},{4,5,0,1},{2,3,4,5},{255,255,255,255}};
    assert(creatures_catalog_validate());
    assert(creatures_migrate_legacy(&roster, 7, 3));
    assert(offsetof(CreatureInstance, cosmetic_seed) == 20);
    assert(creatures_grant(&roster, 13, 10, 20, 0, 5) == 4);
    assert(creatures_grant(&roster, 16, 10, 20, 0, 6) == 5);
    assert(roster.instances[4].flags == CREATURE_OCCUPIED);
    assert(roster.instances[5].flags == CREATURE_OCCUPIED);
    for (i = 0; i < 5; ++i)
        assert(creatures_grant(&roster, (unsigned[]){19,22,73,75,77}[i], 10, 20, 0, 0) == i + 6);
    for (i = 0; i < 24000; ++i) {
        unsigned n = roll(), slot = (n >> 8) % 11;
        CreatureInstance *c = &roster.instances[slot];
        switch (n & 15) {
        case 0: creatures_credit_event(&roster, n % 384, n >> 23, CREATURE_CREDIT_ENCOUNTER); break;
        case 1: creatures_credit_event(&roster, 384 + n % 128, n >> 24, CREATURE_CREDIT_FIELD_AID); break;
        case 2: creatures_mark_trial(c, creatures_family_trial(c->form_id)); break;
        case 3: creatures_evolve(&roster, slot, 63, 1, (n >> 7) & 1); break;
        case 4: creatures_begin_expedition(&roster); break;
        case 5: creatures_add_xp(c, n); break;
        case 6: creatures_equip(c, 1, creatures_form(c->form_id)->signature_ability); break;
        case 7: creatures_select_command(c, (n >> 6) & 1); break;
        case 8: assert(creatures_party_set(&roster, parties[(n >> 9) & 3], 0)); break;
        case 9:
            snapshot = roster;
            assert(creatures_grant(&roster, 13, 10, 20, 0, 5) == CREATURE_EMPTY_SLOT);
            assert(!memcmp(&snapshot, &roster, sizeof(roster)));
            break;
        case 10: creatures_equip(c, (n >> 16) & 3, (n >> 24) & 31); break;
        case 11: creatures_mark_trial(c, (n >> 19) & 63); break;
        case 12: creatures_grant(&roster, enabled[(n >> 12) % 21], 50, 100, 0, 0); break;
        case 13: creatures_evolve(&roster, (n >> 24), n & 31, 1, 1); break;
        case 14: creatures_party_capabilities(&roster); break;
        default: creatures_apply_story_floors(&roster, n & 7); break;
        }
        assert(creatures_roster_validate(&roster));
    }
    creatures_add_xp(&roster.instances[4], CREATURE_XP_CAP);
    roster.instances[4].bond = 100;
    assert(creatures_mark_trial(&roster.instances[4], CREATURE_TRIAL_PAIRED_POOLS));
    if (roster.instances[4].form_id == 13)
        assert(creatures_evolve(&roster, 4, CREATURE_REED_RESTORED, 1, 1) == CREATURE_EVOLVE_READY);
    assert(roster.instances[4].form_id == 14);
    assert(roster.instances[4].flags == CREATURE_OCCUPIED);
    assert(creatures_roster_validate(&roster));
    /* Mutation probes include evolved nonlegacy instances, invalid form/family
     * paths, flags, command slots, collection, party and instance identities. */
    snapshot = roster;
    for (i = 0; i < sizeof(roster); ++i) for (b = 0; b < 8; ++b) {
        unsigned slot = (i / sizeof(CreatureInstance)) % CREATURE_ROSTER_CAPACITY;
        int valid;
        mutated = snapshot;
        ((unsigned char *)&mutated)[i] ^= (unsigned char)(1u << b);
        valid = creatures_roster_validate(&mutated);
        creatures_party_validate(&mutated);
        creatures_party_capabilities(&mutated);
        if (!valid) assert(creatures_evolve(&mutated, slot, 63, 1, 1) == CREATURE_EVOLVE_INVALID);
    }
    for (i = 0; i < sizeof(enabled) / sizeof(enabled[0]); ++i) {
        CreatureInstance good, probe;
        creatures_roster_init(&roster);
        assert(creatures_grant(&roster, enabled[i], 50, 100, 0, 0) == 0);
        good = roster.instances[0];
        for (j = 0; j < sizeof(good); ++j) for (b = 0; b < 256; ++b) {
            probe = good;
            ((unsigned char *)&probe)[j] = (unsigned char)b;
            creatures_instance_validate(&probe);
            creatures_can_evolve(&probe, 63, 1);
            creatures_mark_trial(&probe, creatures_family_trial(enabled[i]));
            creatures_add_xp(&probe, 0xffffffffu);
            creatures_equip(&probe, 1, 10);
            creatures_select_command(&probe, 1);
        }
    }
    return 0;
}
