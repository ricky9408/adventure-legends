/* Host-only synthetic sparse-catalog contract. No cartridge/content claim. */
#include "creatures.h"
#include <assert.h>
#include <stddef.h>
#include <string.h>

#if !defined(EXPECT_INVALID_CATALOG) || defined(EXPECT_UNKNOWN_FAMILY)
static CreatureRoster roster;
#endif
#ifndef EXPECT_INVALID_CATALOG
static const unsigned old_forms[] = {1,2,4,5,7,8,10,11,13,14,16};
static const unsigned old_trials[] = {1,1,2,2,4,4,8,8,16,16,0};
static const unsigned southern_forms[] = {25,26,28,29,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94};
static const unsigned new_forms[] = {19,20,22,23,73,74,75,76,77,78};
static void check_trials(CreatureInstance *c, unsigned trial) {
    static const unsigned flags[] = {0,1,2,4,8,16,32,64,128,256,512,1024,
                                     32768,65535,65536,0xffffffffu};
    CreatureInstance original = *c, probe;
    unsigned i;
    assert(creatures_family_trial(c->form_id) == trial);
    for (i = 0; i < sizeof(flags) / sizeof(flags[0]); ++i) {
        probe = original;
        assert(creatures_mark_trial(&probe, flags[i]) == (int)(trial && flags[i] == trial));
        if (!trial || flags[i] != trial) assert(!memcmp(&original, &probe, sizeof(probe)));
        if (flags[i] <= 65535) {
            probe = original;
            probe.trial_flags = (CreatureU16)flags[i];
            assert(creatures_instance_validate(&probe) == (int)(!flags[i] || flags[i] == trial));
        }
    }
    if (trial) {
        probe = original;
        assert(!creatures_mark_trial(&probe, trial | (trial == 1u ? 2u : 1u)));
        assert(!memcmp(&original, &probe, sizeof(probe)));
    }
}
#endif
#ifndef LAST_TRIAL
#define LAST_TRIAL 512
#endif
int main(void) {
#ifdef EXPECT_INVALID_CATALOG
    assert(!creatures_catalog_validate());
#ifdef EXPECT_UNKNOWN_FAMILY
    assert(creatures_family_trial(16) == 0);
    creatures_roster_init(&roster);
    assert(creatures_grant(&roster, 16, 50, 100, 0, 0) == CREATURE_EMPTY_SLOT);
    assert(creatures_roster_count(&roster) == 0);
#endif
#else
    unsigned i, j;
    assert(creatures_catalog_validate());
    assert(sizeof(CreatureInstance) == 24 && sizeof(CreatureRoster) == 4140);
    assert(offsetof(CreatureInstance, trial_flags) == 14);
    assert(offsetof(CreatureInstance, equipped) == 16);
    assert(!creatures_ability(0) && !creatures_ability(12));
    assert(!creatures_ability(256) && !creatures_ability(0xffffffffu));
    assert(!creatures_family_trial(0) && !creatures_family_trial(128));
    assert(!creatures_family_trial(256) && !creatures_family_trial(0xffffffffu));
    for (i = 1; i <= 11; ++i) assert(creatures_ability(i)->id == i);
    for (i = 0; i < sizeof(old_forms) / sizeof(old_forms[0]); ++i) {
        creatures_roster_init(&roster);
        assert(creatures_grant(&roster, old_forms[i], 50, 100, 0, 0) == 0);
        check_trials(&roster.instances[0], old_trials[i]);
    }
#ifdef SPARSE_FIXTURE
    for (i = 13; i <= 22; ++i) assert(creatures_ability(i)->id == i);
    for (i = 23; i <= 42; ++i) assert(creatures_ability(i)->id == i);
    assert(!creatures_ability(43) && !creatures_ability(255));
    for (i = 0; i < sizeof(new_forms) / sizeof(new_forms[0]); ++i) {
        unsigned trial = i < 8 ? 32u << (i / 2) : LAST_TRIAL;
        CreatureInstance before;
        creatures_roster_init(&roster);
        assert(creatures_grant(&roster, new_forms[i], 50, 100, 0, 0) == 0);
        assert(creatures_roster_validate(&roster));
        check_trials(&roster.instances[0], trial);
        assert(creatures_mark_trial(&roster.instances[0], trial));
        before = roster.instances[0];
        assert(!creatures_equip(&roster.instances[0], 1, 12));
        assert(!memcmp(&before, &roster.instances[0], sizeof(before)));
        if (!(i & 1u)) {
            const CreatureEvolution *e = creatures_evolution(new_forms[i]);
            unsigned context = e->chapter_flags;
            assert(creatures_can_evolve(&roster.instances[0], 0, 1) == CREATURE_EVOLVE_STORY);
            assert(creatures_evolve(&roster, 0, context, 1, 0) == CREATURE_EVOLVE_DEFERRED);
            assert(!memcmp(&before, &roster.instances[0], sizeof(before)));
            assert(creatures_evolve(&roster, 0, context, 1, 1) == CREATURE_EVOLVE_READY);
            before.form_id++;
            assert(!memcmp(&before, &roster.instances[0], sizeof(before)));
            assert(creatures_equip(&roster.instances[0], 1, 14 + i));
            assert(creatures_roster_validate(&roster));
        }
    }
#else
    for (i = 12; i <= 255; ++i) assert(!creatures_ability(i));
    for (i = 0; i < sizeof(new_forms) / sizeof(new_forms[0]); ++i) {
        creatures_roster_init(&roster);
        assert(!creatures_form(new_forms[i]) && !creatures_family_trial(new_forms[i]));
        assert(creatures_grant(&roster, new_forms[i], 50, 100, 0, 0) == CREATURE_EMPTY_SLOT);
    }
#endif
    for (i = 1; i <= 128; ++i) {
        unsigned enabled = 0;
        for (j = 0; j < sizeof(old_forms) / sizeof(old_forms[0]); ++j) enabled |= old_forms[j] == i;
#ifdef SPARSE_FIXTURE
        for (j = 0; j < sizeof(new_forms) / sizeof(new_forms[0]); ++j) enabled |= new_forms[j] == i;
        for (j = 0; j < sizeof(southern_forms) / sizeof(southern_forms[0]); ++j) enabled |= southern_forms[j] == i;
#endif
        assert((creatures_form(i) != 0) == (int)enabled);
    }
#endif
    return 0;
}
