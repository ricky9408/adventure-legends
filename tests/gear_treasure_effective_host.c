/* Content11 treasure/gear integration. Reuse the real menu/cache/commit test
 * bridges, but import an authenticated late save for valid quest provenance.
 * Prepared wallet/loadout/HP combinations are synthetic host boundaries, not
 * a claim that a controller earned them. No gameplay source is replaced. */
#define main gear_preview_foundation_main
#include "gear_preview_effective_host.c"
#undef main

static Save5State treasure_template;
static unsigned treasure_comparisons, treasure_states, treasure_cache_changes;

static unsigned bounded(unsigned n, unsigned limit) {
    return n < limit ? n : limit;
}

static void load_treasure_template(const char *path) {
    static const unsigned quests[] = {21, 24, 32, 40};
    unsigned i;
    FILE *stream = fopen(path, "rb");
    assert(stream);
    assert(fread(save5_test_sram, 1, sizeof save5_test_sram, stream) == sizeof save5_test_sram);
    assert(fgetc(stream) == EOF);
    assert(fclose(stream) == 0);
    save5_test_reset_writer();
    save5_test_fail_after(-1);
    save5_test_corrupt_write(-1, 0);
    assert(save5_load(&treasure_template));
    assert(save5_validate(&treasure_template));
    assert(equipment_count(&treasure_template.equipment) == EQUIPMENT_AUTHORED_COUNT);
    assert(treasure_template.economy.later_claims == 0);
    for (i = 0; i < 4; ++i) {
        assert(save5_quest_state(&treasure_template.quests, quests[i]) == SAVE5_QUEST_CLAIMED);
        assert(treasure_template.quests.objectives[quests[i]] == 15);
    }
}

static void prepared_wallet(unsigned old, unsigned later, unsigned upgrade) {
    EconomyState *e = &adventure_save.economy;
    memset(e, 0, sizeof *e);
    e->relics = e->boss_claims = (unsigned char)old;
    e->later_claims = (unsigned char)later;
    e->upgrade = (unsigned char)upgrade;
    /* Includes enough legitimate combat income for every reward lower bound,
     * while retaining the exact purchase ledger for the optional upgrade. */
    e->earned = 1000;
    e->spent = upgrade * 120u;
    e->gold = (unsigned short)(e->earned - e->spent);
    assert(economy_state_validate(e, adventure_save.campaign.chapter_flags));
    assert(save5_later_claims_validate(&adventure_save.quests, e));
}

/* Independent arithmetic: apply the documented bonus amounts to raw equipment
 * data once; compare all fields with production's effective conversion. */
static EquipmentStats reference_bonus(EquipmentStats raw) {
    unsigned old = adventure_save.economy.relics;
    unsigned later = adventure_save.economy.later_claims;
    unsigned reduction = bounded(75u - raw.power_cooldown + 42u - raw.roll_cooldown, 8);
    raw.attack_q4 = (EquipmentU8)bounded(raw.attack_q4 +
        4u * (adventure_save.economy.upgrade + !!(old & 4u)), 32);
    raw.speed_q8 = (EquipmentU16)bounded(raw.speed_q8 + ((later & 1u) ? 16u : 0u), 352);
    raw.diagonal_q8 = (EquipmentU16)(((uint64_t)raw.speed_q8 * 181u + 128u) / 256u);
    raw.defense_q4 = (EquipmentU8)bounded(raw.defense_q4 + ((later & 2u) ? 2u : 0u), 8);
    raw.power_cooldown = (EquipmentU8)(75u - reduction - ((old & 2u) ? 8u : 0u) - ((later & 4u) ? 4u : 0u));
    return raw;
}

static void check_effective(const EquipmentStats *raw, const EquipmentStats *actual) {
    EquipmentStats expected = reference_bonus(*raw);
    assert(!memcmp(&expected, actual, sizeof expected));
    assert(actual->speed_q8 <= 352 && actual->defense_q4 <= 8);
    assert(actual->power_cooldown >= 55);
    assert(actual->diagonal_q8 == ((actual->speed_q8 * 181u + 128u) / 256u));
}

static void treasure_fresh(unsigned story, unsigned old, unsigned later,
                           unsigned upgrade, unsigned loadout) {
    static const unsigned items[4][5] = {
        {1, 0, 0, 0, 0},       /* Starter and empty optional slots. */
        {2, 34, 49, 67, 82},   /* Real raw DEF7 -> effective DEF8 with seal. */
        {19, 40, 50, 69, 88},  /* Reach plus saturated gear recovery. */
        {21, 35, 49, 0, 85}    /* Fastest current authored gear: raw334. */
    };
    unsigned slot;
    EquipmentStats raw;
    adventure_save = treasure_template;
    prepared_wallet(old, later, upgrade);
    for (slot = 0; slot < EQUIPMENT_SLOT_COUNT; ++slot)
        adventure_save.equipment.equipped[slot] = slot ? EQUIPMENT_EMPTY_REF : 0;
    max_hp = (int)story;
    hero_hp_q4 = 80;
    hp = 5;
    seed_combat();
    assert(game_gear_base_hp() == (story + !!(old & 1u) + !!(later & 8u)) * 16u);
    assert(economy_heart_bonus(&adventure_save) == !!(old & 1u));
    assert(economy_later_heart_bonus(&adventure_save) == !!(later & 8u));
    assert(economy_speed_bonus(&adventure_save) == ((later & 1u) ? 16u : 0u));
    assert(economy_defense_bonus(&adventure_save) == ((later & 2u) ? 2u : 0u));
    assert(economy_power_reduction(&adventure_save) == ((old & 2u) ? 8u : 0u) + ((later & 4u) ? 4u : 0u));
    game_health_refresh(0);
    for (slot = 0; slot < EQUIPMENT_SLOT_COUNT; ++slot)
        if (items[loadout][slot]) equip_id(items[loadout][slot]);
    assert(equipment_derive(&adventure_save.equipment, game_gear_base_hp(), &raw));
    check_effective(&raw, &gear_stats);
    assert(save5_validate(&adventure_save));
    saves = sounds = selections = preview_calls = 0;
    gear_menu_reset();
    journal_tab = 4;
}

static void treasure_display(EquipmentComparison *shown) {
    EquipmentComparison raw;
    RuntimeSnapshot frozen;
    snapshot(&frozen);
    assert(equipment_preview(&adventure_save.equipment, (unsigned)gear_menu_slot,
        (unsigned)gear_menu_candidate, game_gear_base_hp(), game_gear_hp(), 0, &raw) == EQUIPMENT_OK);
    assert(preview_display(shown) == EQUIPMENT_OK);
    check_effective(&raw.before, &shown->before);
    check_effective(&raw.after, &shown->after);
    assert(shown->hp_before_q4 == raw.hp_before_q4 && shown->hp_after_q4 == raw.hp_after_q4);
    /* The cache must retain raw stats even after returning effective output. */
    assert(!memcmp(&preview_cache.comparison, &raw, sizeof raw));
    unchanged(&frozen);
}

static void treasure_commit(unsigned slot, unsigned ref) {
    EquipmentComparison shown;
    gear_menu_slot = (int)slot;
    gear_menu_candidate = (int)ref;
    treasure_display(&shown);
    compare_commit(slot, ref);
    treasure_display(&shown);
    ++treasure_comparisons;
}

static void treasure_matrix(void) {
    unsigned later, old, upgrade, story, loadout, item;
    for (later = 0; later < 16; ++later)
    for (old = 0; old < 8; ++old)
    for (upgrade = 0; upgrade < 2; ++upgrade)
    for (story = 6; story <= 8; story += 2)
    for (loadout = 0; loadout < 4; ++loadout) {
        Save5State prepared;
        EquipmentStats stats;
        treasure_fresh(story, old, later, upgrade, loadout);
        prepared = adventure_save;
        stats = gear_stats;
        ++treasure_states;
        for (item = 0; item < EQUIPMENT_AUTHORED_COUNT; ++item) {
            unsigned id = equipment_authored_ids[item];
            unsigned slot = equipment_definition(id)->slot;
            adventure_save = prepared;
            gear_stats = stats;
            hero_hp_q4 = item % 3 == 0 ? 0 : item % 3 == 1 ? 83 : stats.max_hp_q4;
            hp = (hero_hp_q4 + 15) / 16;
            seed_combat();
            saves = sounds = selections = 0;
            gear_menu_reset();
            treasure_commit(slot, equipment_find(&adventure_save.equipment, id));
            treasure_commit(slot, EQUIPMENT_EMPTY_REF);
        }
        assert(save5_validate(&adventure_save));
    }
}

static void every_later_cache_transition(void) {
    unsigned old, upgrade, later, bit, repeat;
    for (old = 0; old < 8; ++old)
    for (upgrade = 0; upgrade < 2; ++upgrade)
    for (later = 0; later < 16; ++later)
    for (bit = 1; bit <= 8; bit <<= 1) {
        EquipmentComparison first, changed, again, raw_before;
        unsigned count;
        treasure_fresh(8, old, later, upgrade, 2);
        gear_menu_slot = EQUIPMENT_BODY;
        gear_menu_candidate = (int)equipment_find(&adventure_save.equipment, 34);
        treasure_display(&first);
        raw_before = preview_cache.comparison;
        count = preview_calls;
        prepared_wallet(old, later ^ bit, upgrade);
        game_health_refresh(0);
        treasure_display(&changed);
        /* Pearl belongs in raw base HP. Other later treasures deliberately do
         * not invalidate the raw cache; each read reapplies current bonuses. */
        assert(preview_calls == count + (bit == 8));
        if (bit != 8) assert(!memcmp(&raw_before, &preview_cache.comparison, sizeof raw_before));
        if (bit == 1) assert(first.after.speed_q8 != changed.after.speed_q8);
        if (bit == 2) assert(first.after.defense_q4 != changed.after.defense_q4);
        if (bit == 4) assert(first.after.power_cooldown != changed.after.power_cooldown);
        if (bit == 8) assert(first.after.max_hp_q4 != changed.after.max_hp_q4);
        count = preview_calls;
        for (repeat = 0; repeat < 12; ++repeat) {
            treasure_display(&again);
            assert(preview_calls == count && !memcmp(&again, &changed, sizeof again));
        }
        project_all(&changed.before, &changed.after);
        treasure_commit(EQUIPMENT_BODY, (unsigned)gear_menu_candidate);
        assert(save5_validate(&adventure_save));
        ++treasure_cache_changes;
    }
}

static void pearl_full_health_and_removal(void) {
    unsigned old, later, story, slot;
    for (old = 0; old < 8; ++old)
    for (later = 8; later < 16; ++later)
    for (story = 6; story <= 8; story += 2) {
        unsigned base = (story + !!(old & 1u) + 1u) * 16u;
        treasure_fresh(story, old, later, 1, 0);
        game_health_fill();
        assert(hero_hp_q4 == (int)base);
        treasure_commit(EQUIPMENT_WEAPON, 0);
        assert(hero_hp_q4 == (int)base); /* Full Pearl must survive no-op A. */
        equip_id(14); equip_id(34); equip_id(56); equip_id(65);
        assert(hero_hp_q4 == (int)base); /* Adding capacity does not heal. */
        game_health_fill();
        for (slot = 0; slot < EQUIPMENT_SLOT_COUNT; ++slot) {
            int full = hero_hp_q4;
            treasure_commit(slot, adventure_save.equipment.equipped[slot]);
            assert(hero_hp_q4 == full);
        }
        for (slot = 0; slot < EQUIPMENT_SLOT_COUNT; ++slot) {
            treasure_commit(slot, EQUIPMENT_EMPTY_REF);
            assert(hero_hp_q4 == gear_stats.max_hp_q4);
        }
        assert(hero_hp_q4 == (int)base && gear_stats.max_hp_q4 == base);
        assert(save5_validate(&adventure_save));
    }
}

static void treasure_caps_and_equal_values(void) {
    unsigned old, later, command, repeat;
    for (old = 0; old < 8; ++old)
    for (later = 0; later < 16; ++later) {
        EquipmentComparison cmp;
        GearPreview before, after;
        treasure_fresh(8, old, later, 1, 2);
        gear_menu_slot = EQUIPMENT_BOOTS;
        gear_menu_candidate = (int)equipment_find(&adventure_save.equipment, 52);
        treasure_display(&cmp);
        for (command = 1; command <= 128; ++command) {
            projection_exact(&cmp.before, command, &before);
            projection_exact(&cmp.after, command, &after);
            assert(before.recovery_updates == after.recovery_updates);
            assert(before.walk_tenths > after.walk_tenths);
            assert(context_label(&cmp, &before, &after, command) == GP_RECOVERY_CAP);
        }
        treasure_commit(EQUIPMENT_BOOTS, (unsigned)gear_menu_candidate);
        for (repeat = 0; repeat < 12; ++repeat) {
            treasure_commit(EQUIPMENT_BOOTS, (unsigned)gear_menu_candidate);
            assert(gear_stats.power_cooldown == 75u - 8u - ((old & 2u) ? 8u : 0u) - ((later & 4u) ? 4u : 0u));
        }
        if ((old & 2u) && (later & 4u)) {
            assert(gear_stats.power_cooldown == 55);
            assert(game_power_cooldown(75) == 55);
            assert(game_power_cooldown(20) == 1 && game_power_cooldown(0) == 1);
        }

        treasure_fresh(8, old, later, 1, 1);
        gear_menu_slot = EQUIPMENT_RING;
        gear_menu_candidate = (int)equipment_find(&adventure_save.equipment, 81);
        treasure_display(&cmp);
        assert(cmp.before.defense_q4 == ((later & 2u) ? 8u : 7u));
        assert(cmp.after.defense_q4 == ((later & 2u) ? 8u : 6u));
        for (command = 1; command <= 128; ++command) {
            projection_exact(&cmp.before, command, &before);
            projection_exact(&cmp.after, command, &after);
            assert((before.defense == after.defense) == !!(later & 2u));
            assert(before.walk_tenths == after.walk_tenths);
        }
        treasure_commit(EQUIPMENT_RING, (unsigned)gear_menu_candidate);

        equip_id(83);
        gear_menu_slot = EQUIPMENT_RING;
        gear_menu_candidate = (int)equipment_find(&adventure_save.equipment, 86);
        treasure_display(&cmp);
        for (command = 1; command <= 128; ++command) {
            projection_exact(&cmp.before, command, &before);
            projection_exact(&cmp.after, command, &after);
            assert(!memcmp(&before, &after, sizeof before));
            assert(context_label(&cmp, &before, &after, command) == GP_SAME);
        }
        treasure_commit(EQUIPMENT_RING, (unsigned)gear_menu_candidate);
        assert(save5_validate(&adventure_save));
    }
}

static void synthetic_speed_cap_domain(void) {
    unsigned old, later, speed;
    for (old = 0; old < 8; ++old)
    for (later = 0; later < 16; ++later) {
        EquipmentStats raw;
        treasure_fresh(8, old, later, 1, 3);
        assert(gear_stats.speed_q8 == ((later & 1u) ? 350u : 334u));
        assert(equipment_derive(&adventure_save.equipment, game_gear_base_hp(), &raw));
        /* No currently authored loadout reaches speed352 with Compass; these
         * raw input probes separately pin the bounded production converter. */
        for (speed = EQUIPMENT_MIN_SPEED_Q8; speed <= EQUIPMENT_MAX_SPEED_Q8; ++speed) {
            EquipmentStats effective = raw;
            GearPreview shown;
            effective.speed_q8 = (EquipmentU16)speed;
            raw.speed_q8 = (EquipmentU16)speed;
            game_gear_bonus_stats(&effective);
            check_effective(&raw, &effective);
            projection_exact(&effective, 128, &shown);
            if ((later & 1u) && speed >= 336) {
                assert(effective.speed_q8 == 352 && effective.diagonal_q8 == 249);
                assert(shown.walk_tenths == 1100);
            }
        }
    }
}

int main(int argc, char **argv) {
    assert(argc == 2);
    assert(equipment_catalog_validate());
    load_treasure_template(argv[1]);
    every_later_cache_transition();
    pearl_full_health_and_removal();
    treasure_caps_and_equal_values();
    synthetic_speed_cap_domain();
    treasure_matrix();
    assert(treasure_states == 2048 && treasure_cache_changes == 1024);
    printf("PASS treasure Gear: %u prepared valid loadouts; 16 later x 8 old x 2 shop x 2 story x 4 loadouts; "
           "all48 items/removals, all128 commands; %u actual menu commits; %u later-bit cache transitions; "
           "Pearl full-HP/no-op/removal, DEF8/recovery20, raw cache/no accumulation, "
           "synthetic speed352/diagonal249/walk110.0 cap\n",
           treasure_states, treasure_comparisons, treasure_cache_changes);
    return 0;
}
