/* Host-only ASan/UBSan exercise. Codec tests; no gameplay/ROM claim. */
#include "save5.h"
#include <assert.h>
#include <string.h>
static unsigned rng = 0x50560002u;
static unsigned next(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
int main(void) {
    Save5State state, out;
    unsigned cycle, i;
    memset(&state, 0, sizeof state);
    memset(save5_test_sram, 255, sizeof save5_test_sram);
    state.campaign.chapter_flags = 3; state.campaign.story_seen = 10;
    assert(creatures_migrate_legacy(&state.roster, 3, 0));
    equipment_init(&state.equipment);
    for (i = 4; i < 160; ++i)
        assert(creatures_grant(&state.roster, (unsigned[]){1,2,4,5,7,8,10,11}[i & 7u], 50, 100, 0, 0) == i);
    for (i = 1; i < EQUIPMENT_AUTHORED_COUNT; ++i)
        assert(equipment_claim(&state.equipment, equipment_authored_ids[i], i, 0) == EQUIPMENT_OK);
    state.quests.region_flags[0] = 1;
    for (i = 0; i < 11; ++i) if (i != 2 && i != 3) {
        save5_quest_set_state(&state.quests, i, SAVE5_QUEST_CLAIMED);
        state.quests.objectives[i] = (unsigned[]){7,3,7,7,3,1,1,1,3,7,1}[i];
        state.quests.rewards[i >> 3] |= (Save4U8)(1u << (i & 7u));
    }
    for (cycle = 0; cycle < 1000; ++cycle) {
        unsigned steps = 0;
        state.roster.instances[cycle % 160].cosmetic_seed = next();
        assert(save5_validate(&state));
        assert(save5_begin(&state));
        while (save5_status() == SAVE5_BUSY) {
            unsigned budget = next() % 4097u;
            (void)save5_step(budget);
            assert(save5_test_step_work() <= (budget > SAVE5_MAX_BUDGET ? SAVE5_MAX_BUDGET : budget));
            assert(++steps < 1000);
        }
        assert(save5_status() == SAVE5_DONE);
        assert(save5_load(&out));
        assert(memcmp(&state.roster, &out.roster, sizeof state.roster) == 0);
        assert(memcmp(&state.quests, &out.quests, sizeof state.quests) == 0);
        assert(memcmp(&state.equipment, &out.equipment, sizeof state.equipment) == 0);
        assert(save5_test_sram[0] == 255 && save5_test_sram[511] == 255);
    }
    return 0;
}
