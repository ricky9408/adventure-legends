#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "save5.h"
#include "economy.h"
#include "story_rewards.h"
#include "progression_events.h"

#define CHECK(condition) do { if (!(condition)) { fprintf(stderr, "%s:%d: %s\n", __func__, __LINE__, #condition); exit(1); } } while (0)

static unsigned assertions;
static unsigned char baseline_sram[32768], committed_sram[32768];

static void clean_runtime(void) {
    save5_test_reset_writer();
    CHECK(economy_cancel());
    story_rewards_cancel();
    creatures_admission_job_cancel();
    save5_test_fail_after(-1);
    save5_test_corrupt_write(-1, 0);
    save4_test_fail_after(-1);
    save4_test_corrupt_write(-1, 0);
}

static void new_state(Save5State *state) {
    memset(state, 0, sizeof *state);
    CHECK(creatures_migrate_legacy(&state->roster, 0, 0));
    equipment_init(&state->equipment);
    state->economy.gold = 100;
    state->economy.earned = 100;
    CHECK(save5_validate(state));
}

static void equal_payload(const Save5State *actual, const Save5State *expected) {
    Save5State a = *actual, b = *expected;
    a.campaign.sequence = b.campaign.sequence = 0;
    a.campaign.loaded_version = b.campaign.loaded_version = 0;
    CHECK(!memcmp(&a, &b, sizeof a));
}

static unsigned finish_writer(unsigned budget) {
    unsigned status = SAVE5_BUSY, steps = 0;
    while (status == SAVE5_BUSY && steps++ < 100000) status = save5_step(budget);
    CHECK(steps < 100000);
    return status;
}

static unsigned finish_economy(void) {
    unsigned status = SAVE5_BUSY, steps = 0;
    while (status == SAVE5_BUSY && steps++ < 100000) status = economy_step();
    CHECK(steps < 100000);
    return status;
}

static void prepare_disk(Save5State *old, Save5State *next) {
    clean_runtime();
    memset(save5_test_sram, 0x6D, sizeof save5_test_sram);
    new_state(old);
    CHECK(save5_store(old));
    memcpy(baseline_sram, save5_test_sram, sizeof baseline_sram);
    *next = *old;
    next->economy.gold += 7;
    next->economy.earned += 7;
}

static void interrupted_save5(void) {
    Save5State old, next, loaded;
    unsigned count, cut;
    prepare_disk(&old, &next);
    save5_test_fail_after(-1);
    CHECK(save5_store(&next));
    count = save5_test_write_count();
    CHECK(count == 6145);
    for (cut = 0; cut <= count; ++cut) {
        int committed;
        clean_runtime();
        memcpy(save5_test_sram, baseline_sram, sizeof baseline_sram);
        save5_test_fail_after((int)cut);
        committed = save5_store(&next);
        CHECK(committed == (cut == count));
        CHECK(save5_test_write_count() <= cut);
        CHECK(!memcmp(save5_test_sram, baseline_sram, 512));
        CHECK(!memcmp(save5_test_sram + SAVE5_BANK_A, baseline_sram + SAVE5_BANK_A, SAVE5_BANK_SIZE));
        save5_test_reset_writer();
        CHECK(save5_load(&loaded));
        equal_payload(&loaded, committed ? &next : &old);
        ++assertions;
    }
}

static void atomic_save5_smoke(void) {
    Save5State old, next, loaded;
    prepare_disk(&old, &next);
    save5_test_fail_after(100);
    CHECK(!save5_store(&next));
    save5_test_reset_writer();
    CHECK(save5_load(&loaded));
    equal_payload(&loaded, &old);
    CHECK(!memcmp(save5_test_sram + SAVE5_BANK_A, baseline_sram + SAVE5_BANK_A, SAVE5_BANK_SIZE));
    ++assertions;
}

static void interrupted_save4(void) {
    CampaignSave old = {0}, next = {0}, loaded;
    unsigned char disk[256];
    unsigned cut, count;
    clean_runtime();
    memset(save4_test_sram, 0x7B, sizeof save4_test_sram);
    old.bridge = 1;
    CHECK(save4_store(&old));
    memcpy(disk, save4_test_sram, sizeof disk);
    next = old;
    next.torches = 3;
    save4_test_fail_after(-1);
    CHECK(save4_store(&next));
    count = save4_test_write_count();
    CHECK(count == 33);
    for (cut = 0; cut <= count; ++cut) {
        int committed;
        memcpy(save4_test_sram, disk, sizeof disk);
        save4_test_fail_after((int)cut);
        committed = save4_store(&next);
        CHECK(committed == (cut == count));
        CHECK(save4_load(&loaded));
        CHECK(loaded.bridge == 1);
        CHECK(loaded.torches == (committed ? 3 : 0));
        CHECK(!memcmp(save4_test_sram, disk, SAVE4_BANK_A));
        CHECK(!memcmp(save4_test_sram + SAVE4_BANK_A, disk + SAVE4_BANK_A, SAVE4_BANK_SIZE));
        ++assertions;
    }
}

static void corruption_save5(void) {
    Save5State old, next, loaded;
    unsigned byte;
    prepare_disk(&old, &next);
    CHECK(save5_store(&next));
    memcpy(committed_sram, save5_test_sram, sizeof committed_sram);
    for (byte = 0; byte < SAVE5_BANK_SIZE; ++byte) {
        clean_runtime();
        memcpy(save5_test_sram, committed_sram, sizeof committed_sram);
        save5_test_sram[SAVE5_BANK_B + byte] ^= 1u;
        CHECK(save5_load(&loaded));
        equal_payload(&loaded, &old);
        ++assertions;
    }
    for (byte = 0; byte < 6145; byte += 97) {
        clean_runtime();
        memcpy(save5_test_sram, baseline_sram, sizeof baseline_sram);
        save5_test_corrupt_write((int)byte, 1);
        CHECK(!save5_store(&next));
        save5_test_reset_writer();
        CHECK(save5_load(&loaded));
        equal_payload(&loaded, &old);
        ++assertions;
    }
}

static unsigned independent_crc32(const unsigned char *data, unsigned size) {
    unsigned crc = 0xFFFFFFFFu, i, bit;
    for (i = 0; i < size; ++i) {
        unsigned value = i >= 16 && i <= 20 ? 0 : data[i];
        crc ^= value;
        for (bit = 0; bit < 8; ++bit) crc = (crc >> 1) ^ ((crc & 1u) ? 0xEDB88320u : 0);
    }
    return ~crc;
}

static void authenticate_bank(unsigned char *bank) {
    unsigned crc = independent_crc32(bank, SAVE5_BANK_SIZE), i;
    for (i = 0; i < 4; ++i) bank[16 + i] = (unsigned char)(crc >> (8 * i));
}

static void put_word(unsigned char *bytes, unsigned value, unsigned count) {
    unsigned i;
    for (i = 0; i < count; ++i) bytes[i] = (unsigned char)(value >> (8 * i));
}

static void independent_starter_bank(unsigned revision) {
    unsigned char *bank;
    unsigned i;
    memset(save5_test_sram, 0, sizeof save5_test_sram);
    bank = save5_test_sram + SAVE5_BANK_A;
    bank[0] = 'E'; bank[1] = 'B'; bank[2] = 5; bank[3] = 32;
    put_word(bank + 4, 6144, 2);
    put_word(bank + 6, revision >= 13 ? 5092 : revision >= 10 ? 5088 : 5056, 2);
    put_word(bank + 8, 1, 4);
    put_word(bank + 12, revision, 2);
    bank[20] = 0xA5;
    bank[96] = bank[112] = 9;
    bank[128] = 3;
    for (i = 0; i < 2; ++i) {
        unsigned char *record = bank + 160 + 24 * i;
        record[0] = i ? 4 : 1;
        record[1] = 3;
        record[2] = 1;
        record[3] = 20;
        put_word(record + 8, i + 1, 4);
        record[16] = (unsigned char)(i + 1);
        record[18] = (unsigned char)!i;
    }
    bank[4000] = 0; bank[4001] = 1; bank[4002] = bank[4003] = 255;
    put_word(bank + 4008, 3, 4);
    if (revision >= 2) {
        bank[4544] = 1; bank[4547] = 1; bank[4548] = 1;
        for (i = 1; i < 5; ++i) bank[4928 + i] = 255;
        bank[4944] = 2; bank[5024] = 1;
    }
    authenticate_bank(bank);
}

static void historical_starter_migration(void) {
    unsigned revision;
    for (revision = 1; revision <= 13; ++revision) {
        Save5State loaded, asynchronous, migrated;
        unsigned status = SAVE5_BUSY, steps = 0;
        clean_runtime();
        independent_starter_bank(revision);
        memcpy(baseline_sram, save5_test_sram, sizeof baseline_sram);
        CHECK(save5_load(&loaded));
        CHECK(creatures_roster_count(&loaded.roster) == 2);
        CHECK(loaded.roster.instances[0].form_id == 1 && loaded.roster.instances[1].form_id == 4);
        CHECK(loaded.roster.instances[0].xp == 0 && loaded.roster.instances[1].xp == 0);
        CHECK(loaded.roster.instances[0].bond == 20 && loaded.roster.instances[1].bond == 20);
        CHECK(loaded.roster.rewards[0] == 3);
        CHECK(equipment_count(&loaded.equipment) == 1 && loaded.equipment.bag[0].item_id == 1);
        CHECK(loaded.economy.gold == 0 && loaded.economy.earned == 0 && loaded.economy.spent == 0);
        CHECK(!memcmp(save5_test_sram, baseline_sram, sizeof baseline_sram));
        CHECK(save5_load_begin(&asynchronous));
        while (status == SAVE5_BUSY && steps++ < 1000) status = save5_load_step(511);
        CHECK(status == SAVE5_DONE);
        equal_payload(&asynchronous, &loaded);
        CHECK(!memcmp(save5_test_sram, baseline_sram, sizeof baseline_sram));
        CHECK(save5_store(&loaded));
        CHECK(save5_test_sram[SAVE5_BANK_B + 12] == 13);
        CHECK(save5_load(&migrated));
        equal_payload(&migrated, &loaded);
        ++assertions;
    }
}

static void reject_authenticated_malformed_banks(void) {
    Save5State old, next, loaded, sentinel;
    unsigned offsets[] = {32, 33, 34, 35, 36, 37, 38, 160, 162, 163, 164,
        168, 176, 178, 179, 4000, 4004, 4032, 4048, 4176, 4544, 4546,
        4547, 4548, 4928, 4944, 5024, 5056, 5060, 5064, 5088, 5092};
    unsigned i;
    prepare_disk(&old, &next);
    memcpy(committed_sram, baseline_sram, sizeof committed_sram);
    memset(&sentinel, 0xA6, sizeof sentinel);
    for (i = 0; i < sizeof offsets / sizeof offsets[0]; ++i) {
        unsigned char *bank;
        clean_runtime();
        memcpy(save5_test_sram, committed_sram, sizeof committed_sram);
        bank = save5_test_sram + SAVE5_BANK_A;
        bank[offsets[i]] = 255;
        authenticate_bank(bank);
        loaded = sentinel;
        if (save5_load(&loaded)) {
            fprintf(stderr, "accepted malformed offset %u\n", offsets[i]);
            CHECK(0);
        }
        CHECK(!memcmp(&loaded, &sentinel, sizeof loaded));
        CHECK(save5_load_begin(&loaded));
        {
            unsigned status = SAVE5_BUSY, steps = 0;
            while (status == SAVE5_BUSY && steps++ < 1000) status = save5_load_step(511);
            CHECK(status == SAVE5_FAILED);
            CHECK(!memcmp(&loaded, &sentinel, sizeof loaded));
        }
        ++assertions;
    }
    for (i = 0; i < 24; ++i) {
        unsigned char *bank;
        clean_runtime();
        memcpy(save5_test_sram, committed_sram, sizeof committed_sram);
        bank = save5_test_sram + SAVE5_BANK_A;
        bank[160 + 2 * 24 + i] = 1;
        authenticate_bank(bank);
        loaded = sentinel;
        CHECK(!save5_load(&loaded));
        CHECK(!memcmp(&loaded, &sentinel, sizeof loaded));
        ++assertions;
    }
}

static void snapshot_and_loader(void) {
    Save5State original, changed, loaded, sentinel;
    unsigned budget;
    prepare_disk(&original, &changed);
    CHECK(save5_begin(&changed));
    original = changed;
    changed.economy.gold += 1;
    changed.economy.earned += 1;
    CHECK(!save5_begin(&changed));
    CHECK(save5_step(0) == SAVE5_BUSY);
    CHECK(save5_test_write_count() == 6145);
    CHECK(finish_writer(113) == SAVE5_DONE);
    CHECK(save5_load(&loaded));
    equal_payload(&loaded, &original);
    memcpy(committed_sram, save5_test_sram, sizeof committed_sram);
    memset(&sentinel, 0xA5, sizeof sentinel);
    for (budget = 1; budget <= 1024; budget *= 4) {
        unsigned status = SAVE5_BUSY, steps = 0;
        clean_runtime();
        loaded = sentinel;
        CHECK(save5_load_begin(&loaded));
        CHECK(!save5_begin(&changed));
        CHECK(save5_load_step(0) == SAVE5_BUSY);
        CHECK(!memcmp(&loaded, &sentinel, sizeof loaded));
        while (status == SAVE5_BUSY && steps++ < 20000) {
            CHECK(!memcmp(&loaded, &sentinel, sizeof loaded));
            status = save5_load_step(budget);
        }
        CHECK(status == SAVE5_DONE);
        equal_payload(&loaded, &original);
        CHECK(!memcmp(save5_test_sram, committed_sram, sizeof committed_sram));
        ++assertions;
    }
    clean_runtime();
    loaded = sentinel;
    CHECK(save5_load_begin(&loaded));
    CHECK(save5_load_step(1024) == SAVE5_BUSY);
    save5_load_cancel();
    CHECK(!memcmp(&loaded, &sentinel, sizeof loaded));
}

static void malformed_ram_never_reaches_sram(void) {
    Save5State original, next, invalid;
    unsigned slot, byte;
    prepare_disk(&original, &next);
    for (slot = 2; slot < CREATURE_ROSTER_CAPACITY; ++slot) {
        for (byte = 0; byte < sizeof(CreatureInstance); ++byte) {
            unsigned status = SAVE5_BUSY, steps = 0;
            Save4U32 token;
            clean_runtime();
            invalid = original;
            ((unsigned char *)&invalid.roster.instances[slot])[byte] = 1;
            token = save5_preflight_begin(&invalid);
            CHECK(token);
            while (status == SAVE5_BUSY && steps++ < 1000) status = save5_preflight_step(token, 480);
            CHECK(status == SAVE5_FAILED);
            CHECK(!save5_preflight_snapshot(token));
            save5_preflight_cancel();
            save5_test_fail_after(-1);
            CHECK(save5_begin(&invalid));
            CHECK(finish_writer(511) == SAVE5_FAILED);
            CHECK(save5_test_write_count() == 0);
            CHECK(!memcmp(save5_test_sram, baseline_sram, sizeof baseline_sram));
            ++assertions;
        }
    }
}

static void economy_transactions(void) {
    Save5State original, next, loaded, before;
    unsigned cut, status, steps;
    static const unsigned cuts[] = {0, 1, 20, 512, 4096, 6144};
    for (cut = 0; cut < sizeof cuts / sizeof cuts[0]; ++cut) {
        prepare_disk(&original, &next);
        before = original;
        save5_test_fail_after((int)cuts[cut]);
        CHECK(economy_begin_purchase(&original, ECONOMY_HEART_TONIC));
        CHECK(!economy_begin_purchase(&original, ECONOMY_HEART_TONIC));
        CHECK(economy_award_combat(&original, 100) == 0);
        status = SAVE5_BUSY;
        steps = 0;
        while (status == SAVE5_BUSY && steps++ < 1000) {
            CHECK(!memcmp(&original, &before, sizeof before));
            status = economy_step();
        }
        CHECK(status == SAVE5_FAILED);
        CHECK(economy_last_error() == ECONOMY_SAVE_FAILED);
        CHECK(!memcmp(&original, &before, sizeof before));
        save5_test_reset_writer();
        CHECK(save5_load(&loaded));
        equal_payload(&loaded, &before);
        ++assertions;
    }
    prepare_disk(&original, &next);
    before = original;
    CHECK(economy_begin_purchase(&original, ECONOMY_HEART_TONIC));
    CHECK(finish_economy() == SAVE5_DONE);
    CHECK(original.economy.gold == 82 && original.economy.earned == 100 && original.economy.spent == 18);
    CHECK(original.economy.supplies[0] == 1 && original.economy.bought[0] == 1 && original.economy.used[0] == 0);
    CHECK(save5_load(&loaded));
    equal_payload(&loaded, &original);
    CHECK(economy_begin_use(&original, ECONOMY_HEART_TONIC));
    CHECK(finish_economy() == SAVE5_DONE);
    CHECK(original.economy.supplies[0] == 0 && original.economy.bought[0] == 1 && original.economy.used[0] == 1);
    before = original;
    CHECK(!economy_begin_use(&original, ECONOMY_HEART_TONIC));
    CHECK(economy_last_error() == ECONOMY_EMPTY);
    CHECK(!memcmp(&original, &before, sizeof before));
    CHECK(economy_begin_purchase(&original, ECONOMY_HEART_TONIC));
    original.roster.instances[0].bond += 1;
    before = original;
    CHECK(finish_economy() == SAVE5_FAILED);
    CHECK(economy_last_error() == ECONOMY_STATE_CHANGED);
    CHECK(!memcmp(&original, &before, sizeof before));
    CHECK(economy_award_combat(&original, UINT_MAX) == 9999u - 82u);
    CHECK(original.economy.gold == 9999);
    CHECK(original.economy.earned - original.economy.spent == original.economy.gold);
    before = original;
    CHECK(economy_award_combat(&original, UINT_MAX) == 0);
    CHECK(!memcmp(&original, &before, sizeof before));
    ++assertions;
}

static void creature_credits(void) {
    CreatureRoster roster, before;
    unsigned member, event;
    CHECK(creatures_migrate_legacy(&roster, 0, 0));
    for (event = 0; event < 384; ++event) {
        CHECK(creatures_credit_event(&roster, event, 13, CREATURE_CREDIT_ENCOUNTER) == 1);
        before = roster;
        CHECK(creatures_credit_event(&roster, event, UINT_MAX, CREATURE_CREDIT_ENCOUNTER) == 0);
        CHECK(!memcmp(&roster, &before, sizeof roster));
        CHECK(creatures_roster_validate(&roster));
        ++assertions;
    }
    for (member = 0; member < 2; ++member) {
        CHECK(roster.instances[member].xp == 13u * 384u);
        CHECK(roster.instances[member].bond == 30);
        CHECK(roster.expedition_bond[member] == 10);
    }
    before = roster;
    CHECK(creatures_credit_event(&roster, 512, 5, CREATURE_CREDIT_ENCOUNTER) == -1);
    CHECK(creatures_credit_event(&roster, 0, 5, CREATURE_CREDIT_FIELD_AID) == -1);
    CHECK(!memcmp(&roster, &before, sizeof roster));
    creatures_begin_expedition(&roster);
    CHECK(creatures_credit_event(&roster, 384, 1, CREATURE_CREDIT_FIELD_AID) == 1);
    CHECK(roster.instances[0].bond == 33);
    creatures_begin_expedition(&roster);
    CHECK(creatures_credit_event(&roster, 384, 1, CREATURE_CREDIT_FIELD_AID) == 1);
    CHECK(roster.instances[0].bond == 33);
    CHECK(creatures_add_xp(&roster.instances[0], UINT_MAX));
    CHECK(roster.instances[0].xp == CREATURE_XP_CAP && roster.instances[0].level == 50);
    before = roster;
    CHECK(creatures_grant(&roster, 129, 1, 0, 0, 0) == CREATURE_EMPTY_SLOT);
    CHECK(creatures_grant(&roster, UINT_MAX, 1, 0, 0, 0) == CREATURE_EMPTY_SLOT);
    CHECK(!memcmp(&roster, &before, sizeof roster));
    roster.next_instance_id = UINT_MAX;
    before = roster;
    CHECK(creatures_grant(&roster, 1, 1, 0, 0, 0) == CREATURE_EMPTY_SLOT);
    CHECK(!memcmp(&roster, &before, sizeof roster));
}

static void party_and_gear(void) {
    CreatureRoster roster, before;
    EquipmentState gear, old;
    EquipmentU16 hp = 96;
    unsigned first, result, id, reward;
    CreatureU8 mapping[4];
    CHECK(creatures_migrate_legacy(&roster, 0, 0));
    memcpy(mapping, roster.party, sizeof mapping);
    mapping[0] = 1; mapping[1] = 0;
    CHECK(creatures_party_set(&roster, mapping, 0));
    CHECK(roster.selected_party == 1);
    before = roster;
    mapping[0] = mapping[1];
    CHECK(!creatures_party_set(&roster, mapping, 0));
    CHECK(!memcmp(&roster, &before, sizeof roster));
    mapping[0] = 160;
    CHECK(!creatures_party_set(&roster, mapping, 0));
    CHECK(!memcmp(&roster, &before, sizeof roster));
    equipment_init(&gear);
    CHECK(equipment_purchase(&gear, 2, &first) == EQUIPMENT_OK);
    old = gear;
    CHECK(equipment_purchase(&gear, 2, 0) == EQUIPMENT_DUPLICATE);
    CHECK(!memcmp(&gear, &old, sizeof gear));
    CHECK(equipment_discard(&gear, first, 96, &hp, 0, 1) == EQUIPMENT_OK);
    CHECK(equipment_seen(&gear, 2));
    CHECK(equipment_find(&gear, 2) == EQUIPMENT_EMPTY_REF);
    old = gear;
    CHECK(equipment_purchase(&gear, 2, 0) == EQUIPMENT_DUPLICATE);
    CHECK(!memcmp(&gear, &old, sizeof gear));
    CHECK(equipment_claim(&gear, 2, 1, 0) == EQUIPMENT_DUPLICATE);
    CHECK(equipment_count(&gear) == 1);
    old = gear;
    CHECK(equipment_claim(&gear, 2, 1, 0) == EQUIPMENT_ALREADY_CLAIMED);
    CHECK(!memcmp(&gear, &old, sizeof gear));
    for (id = 0; id <= 65536; ++id) {
        const EquipmentDefinition *definition = equipment_definition(id);
        if (definition) {
            CHECK(definition->id == id);
            CHECK(definition->stats.attack_q4 <= (definition->slot == EQUIPMENT_WEAPON ? 4 : 0));
        }
        ++assertions;
    }
    for (reward = 0; reward < EQUIPMENT_AUTHORED_COUNT; ++reward) {
        EquipmentStats stats;
        equipment_init(&gear);
        id = equipment_reward_item(reward);
        result = equipment_claim(&gear, id, reward, &first);
        CHECK(result == (reward ? EQUIPMENT_OK : EQUIPMENT_ALREADY_CLAIMED));
        if (reward) {
            CHECK(equipment_equip(&gear, equipment_definition(id)->slot, first, 96, &hp, 0, 0) == EQUIPMENT_OK);
            CHECK(equipment_derive(&gear, 96, &stats));
            CHECK(stats.attack_q4 + 8 <= 24);
        }
        CHECK(equipment_validate(&gear));
    }
}

static void story_and_quest_identities(void) {
    Save5State state, before;
    unsigned status, loops = 0, id, other;
    Save5Quests quests, saved;
    clean_runtime();
    new_state(&state);
    before = state;
    CHECK(story_rewards_begin(&state, 1));
    state.economy.gold += 1;
    state.economy.earned += 1;
    before = state;
    status = SAVE5_BUSY;
    while (status == SAVE5_BUSY && loops++ < 1000) status = story_rewards_step();
    CHECK(status == SAVE5_DONE);
    CHECK(creatures_roster_count(&state.roster) == 3);
    CHECK(state.roster.rewards[0] == 7);
    CHECK(state.economy.gold == before.economy.gold);
    before = state;
    state.campaign.chapter_flags = 1;
    CHECK(story_rewards_begin(&state, 1));
    status = SAVE5_BUSY; loops = 0;
    while (status == SAVE5_BUSY && loops++ < 1000) status = story_rewards_step();
    CHECK(status == SAVE5_DONE);
    CHECK(!memcmp(&state.roster, &before.roster, sizeof state.roster));
    clean_runtime();
    new_state(&state);
    CHECK(story_rewards_begin(&state, 1));
    CHECK(story_rewards_step() == SAVE5_BUSY);
    state.economy.gold += 1;
    state.economy.earned += 1;
    before = state;
    status = SAVE5_BUSY; loops = 0;
    while (status == SAVE5_BUSY && loops++ < 1000) status = story_rewards_step();
    CHECK(status == SAVE5_FAILED);
    CHECK(!memcmp(&state, &before, sizeof state));
    memset(&quests, 0, sizeof quests);
    for (id = 0; id < 64; ++id) {
        CHECK(save5_quest_set_state(&quests, id, SAVE5_QUEST_ACTIVE));
        CHECK(save5_quest_state(&quests, id) == SAVE5_QUEST_ACTIVE);
        for (other = 0; other < 64; ++other) CHECK(save5_quest_state(&quests, other) == (other <= id ? 1u : 0u));
    }
    saved = quests;
    CHECK(!save5_quest_set_state(&quests, 64, 1));
    CHECK(!save5_quest_set_state(&quests, UINT_MAX, 1));
    CHECK(!save5_quest_set_state(&quests, 0, 4));
    CHECK(!memcmp(&saved, &quests, sizeof saved));
    for (id = 0; id < 256; ++id) {
        unsigned event = progression_encounter_event(id, 0);
        CHECK(event == CREATURE_EVENT_CAPACITY || event < 384);
        CHECK(progression_encounter_event(id, 6) == CREATURE_EVENT_CAPACITY);
    }
    ++assertions;
}

int main(int argc, char **argv) {
    const char *name = argc == 2 ? argv[1] : "all";
    if (!strcmp(name, "all") || !strcmp(name, "powerfail")) { interrupted_save4(); interrupted_save5(); }
    if (!strcmp(name, "all") || !strcmp(name, "atomic")) atomic_save5_smoke();
    if (!strcmp(name, "all") || !strcmp(name, "corruption")) corruption_save5();
    if (!strcmp(name, "all") || !strcmp(name, "malformed")) reject_authenticated_malformed_banks();
    if (!strcmp(name, "all") || !strcmp(name, "history")) historical_starter_migration();
    if (!strcmp(name, "all") || !strcmp(name, "snapshot")) snapshot_and_loader();
    if (!strcmp(name, "all") || !strcmp(name, "invalid-ram")) malformed_ram_never_reaches_sram();
    if (!strcmp(name, "all") || !strcmp(name, "economy")) economy_transactions();
    if (!strcmp(name, "all") || !strcmp(name, "credits")) creature_credits();
    if (!strcmp(name, "all") || !strcmp(name, "gear")) party_and_gear();
    if (!strcmp(name, "all") || !strcmp(name, "story")) story_and_quest_identities();
    CHECK(assertions > 0);
    printf("{\"case\":\"%s\",\"status\":\"passed\",\"iterations\":%u}\n", name, assertions);
    return 0;
}
