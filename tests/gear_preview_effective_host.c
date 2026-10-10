/* Exercise the actual cached menu, live commit, and effective runtime bonuses.
 * Only world/UI/save bridges are bounded here; equipment, bonus math, recovery,
 * weapon busy detection and the projection under test are production code. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "progression.h"
#include "gear_runtime.h"
#include "gear_preview.h"
#include "companion_guide.h"

static unsigned preview_calls;
static unsigned counted_preview(const EquipmentState *state, unsigned slot,
                                unsigned ref, unsigned base, unsigned current,
                                unsigned busy, EquipmentComparison *out) {
    ++preview_calls;
    return equipment_preview(state, slot, ref, base, current, busy, out);
}
#define equipment_preview counted_preview
#include "../src/gear_menu.c"
#undef equipment_preview

typedef struct { int x, y, dx, dy, life, owner; } Shot;
Save5State adventure_save;
Shot shots[12];
volatile int hp, max_hp;
int journal_tab = 4, gfx_slash_frame, roll_ticks;
int regional_power_kind, regional_power_time;
int ability_cd, ability_max, northern_power_cooldown, southern_power_cooldown;
int magma_power_cooldown, underwater_power_cooldown, return_power_cooldown;
int horizons_power_cooldown, covenants_power_cooldown;
static unsigned chapter_busy, saves, sounds, selections;

/* These hooks do no gear arithmetic and cannot substitute for runtime apply. */
int northern_powers_busy(void) { return !!(chapter_busy & 1u); }
int southern_powers_busy(void) { return !!(chapter_busy & 2u); }
int magma_powers_busy(void) { return !!(chapter_busy & 4u); }
int underwater_powers_busy(void) { return !!(chapter_busy & 8u); }
int return_powers_busy(void) { return !!(chapter_busy & 16u); }
int horizons_powers_busy(void) { return !!(chapter_busy & 32u); }
int covenants_powers_busy(void) { return !!(chapter_busy & 64u); }
void covenants_powers_selection_changed(void) { ++selections; }
void covenants_game_selection_changed(void) { ++selections; }
void save_game(void) { ++saves; }
void toast(int id) { (void)id; }
void sfx(int id) { (void)id; ++sounds; }

typedef struct {
    Save5State save;
    EquipmentStats stats;
    WeaponAttack action;
    WeaponArrow arrows[2];
    Shot projectiles[12];
    int hearts, legacy_hp, base, slash, roll, regional_kind, regional_time;
    int cooldowns[9];
    unsigned chapter, save_calls, sound_calls, selection_calls;
} RuntimeSnapshot;

static void snapshot(RuntimeSnapshot *out) {
    memset(out, 0, sizeof *out);
    out->save = adventure_save;
    out->stats = gear_stats;
    out->action = weapon_action;
    memcpy(out->arrows, player_arrows, sizeof out->arrows);
    memcpy(out->projectiles, shots, sizeof shots);
    out->hearts = hero_hp_q4;
    out->legacy_hp = hp;
    out->base = max_hp;
    out->slash = gfx_slash_frame;
    out->roll = roll_ticks;
    out->regional_kind = regional_power_kind;
    out->regional_time = regional_power_time;
    out->cooldowns[0] = ability_cd;
    out->cooldowns[1] = ability_max;
    out->cooldowns[2] = northern_power_cooldown;
    out->cooldowns[3] = southern_power_cooldown;
    out->cooldowns[4] = magma_power_cooldown;
    out->cooldowns[5] = underwater_power_cooldown;
    out->cooldowns[6] = return_power_cooldown;
    out->cooldowns[7] = horizons_power_cooldown;
    out->cooldowns[8] = covenants_power_cooldown;
    out->chapter = chapter_busy;
    out->save_calls = saves;
    out->sound_calls = sounds;
    out->selection_calls = selections;
}

static void unchanged(const RuntimeSnapshot *before) {
    RuntimeSnapshot after;
    snapshot(&after);
    assert(!memcmp(before, &after, sizeof after));
}

static void combat_unchanged(const RuntimeSnapshot *before) {
    RuntimeSnapshot after;
    snapshot(&after);
    assert(!memcmp(&before->action, &after.action, sizeof after.action));
    assert(!memcmp(before->arrows, after.arrows, sizeof after.arrows));
    assert(!memcmp(before->projectiles, after.projectiles, sizeof after.projectiles));
    assert(!memcmp(before->cooldowns, after.cooldowns, sizeof after.cooldowns));
    assert(before->roll == after.roll && before->chapter == after.chapter);
    assert(before->regional_kind == after.regional_kind);
    assert(before->regional_time == after.regional_time);
}

static void seed_combat(void) {
    memset(&weapon_action, 0x35, sizeof weapon_action);
    weapon_action.phase = WEAPON_IDLE;
    weapon_action.weapon_class = EQUIPMENT_SWORD;
    memset(player_arrows, 0x46, sizeof player_arrows);
    player_arrows[0].active = player_arrows[1].active = 0;
    memset(shots, 0, sizeof shots);
    shots[0] = (Shot){81, 93, 1, -1, 29, 1}; /* An enemy shot is not a lock. */
    roll_ticks = regional_power_kind = regional_power_time = 0;
    chapter_busy = 0;
    ability_cd = 37; ability_max = 105;
    northern_power_cooldown = 31; southern_power_cooldown = 43;
    magma_power_cooldown = 59; underwater_power_cooldown = 67;
    return_power_cooldown = 73; horizons_power_cooldown = 83;
    covenants_power_cooldown = 97;
    gfx_slash_frame = 19;
    assert(game_gear_busy() == 0);
}

static void fresh(unsigned story_hearts, unsigned relics, unsigned upgrade) {
    memset(&adventure_save, 0, sizeof adventure_save);
    equipment_init(&adventure_save.equipment);
    adventure_save.economy.relics = (unsigned char)relics;
    adventure_save.economy.upgrade = (unsigned char)upgrade;
    max_hp = (int)story_hearts;
    hero_hp_q4 = 80;
    assert(equipment_derive(&adventure_save.equipment, game_gear_base_hp(), &gear_stats));
    game_gear_bonus_stats(&gear_stats);
    hp = (hero_hp_q4 + 15) / 16;
    seed_combat();
    saves = sounds = selections = preview_calls = 0;
    gear_menu_reset();
    journal_tab = 4;
}

static unsigned claim(unsigned id) {
    unsigned ref;
    EquipmentU8 equipped[EQUIPMENT_SLOT_COUNT];
    EquipmentStats stats = gear_stats;
    int current = hero_hp_q4;
    memcpy(equipped, adventure_save.equipment.equipped, sizeof equipped);
    if (id == EQUIPMENT_STARTER_ID) return 0;
    assert(equipment_claim(&adventure_save.equipment, id,
                           equipment_reward_source(id), &ref) == EQUIPMENT_OK);
    assert(!memcmp(equipped, adventure_save.equipment.equipped, sizeof equipped));
    assert(!memcmp(&stats, &gear_stats, sizeof stats) && current == hero_hp_q4);
    return ref;
}

static void own_all(void) {
    unsigned i;
    for (i = 1; i < EQUIPMENT_AUTHORED_COUNT; ++i) claim(equipment_authored_ids[i]);
    assert(equipment_count(&adventure_save.equipment) == EQUIPMENT_BAG_CAPACITY);
}

static void live_equip(unsigned slot, unsigned ref) {
    EquipmentU16 current = (EquipmentU16)hero_hp_q4;
    EquipmentComparison committed;
    assert(equipment_equip(&adventure_save.equipment, slot, ref,
                           game_gear_base_hp(), &current, game_gear_busy(),
                           &committed) == EQUIPMENT_OK);
    game_gear_apply_stats(current, &committed.after);
}

static void equip_id(unsigned id) {
    unsigned ref = equipment_find(&adventure_save.equipment, id);
    assert(ref != EQUIPMENT_EMPTY_REF);
    live_equip(equipment_definition(id)->slot, ref);
}

static unsigned reference_hundredths(unsigned updates) {
    /* GBA update: 280896 / 16777216 seconds. Reduce the rational independently
     * of the implementation's shift to pin rounding as well as the unit. */
    return (unsigned)(((uint64_t)updates * 28089600u + 8388608u) / 16777216u);
}

static void projection_exact(const EquipmentStats *effective, unsigned command,
                             GearPreview *out) {
    const CreatureAbility *ability = creatures_ability(command);
    EquipmentStats original = *effective;
    unsigned base = command <= 4 ? 75u : ability->cooldown_updates;
    unsigned reduction = EQUIPMENT_BASE_POWER_COOLDOWN - effective->power_cooldown;
    unsigned expected_recovery = base > reduction ? base - reduction : 1u;
    unsigned expected_walk = (unsigned)(((uint64_t)effective->speed_q8 * 1000u + 160u) / 320u);
    gear_preview_project(effective, command, out);
    assert(!memcmp(&original, effective, sizeof original));
    assert(out->weapon_class == effective->weapon_class);
    assert(out->attack == (unsigned)equipment_weapons[effective->weapon_class].moves[0].damage_q4 + effective->attack_q4);
    assert(out->defense == effective->defense_q4);
    assert(out->hearts == effective->max_hp_q4);
    assert(out->walk_tenths == expected_walk);
    assert(out->recovery_updates == expected_recovery);
    assert(out->recovery_updates == companion_guide_recovery_stats(command, effective));
    assert(out->recovery_hundredths == reference_hundredths(expected_recovery));
    assert(out->distance == (unsigned)equipment_weapons[effective->weapon_class].moves[0].reach_px + effective->reach_px);
    assert(out->stagger == effective->stagger);
}

static void project_all(const EquipmentStats *before, const EquipmentStats *after) {
    unsigned command;
    GearPreview first, second;
    for (command = 1; command <= 128; ++command) {
        projection_exact(before, command, &first);
        projection_exact(after, command, &second);
    }
}

static void compare_commit(unsigned slot, unsigned candidate) {
    RuntimeSnapshot frozen;
    EquipmentComparison display, again, post, raw;
    EquipmentStats actual_before = gear_stats, derived;
    EquipmentState expected_equipment = adventure_save.equipment;
    EquipmentU16 expected_hp = (EquipmentU16)hero_hp_q4;
    Save5State expected_save;
    GearPreview promised, actual;
    unsigned command, old_previews;

    gear_menu_slot = (int)slot;
    gear_menu_candidate = (int)candidate;
    snapshot(&frozen);
    assert(preview_display(&display) == EQUIPMENT_OK);
    unchanged(&frozen);
    assert(!memcmp(&display.before, &actual_before, sizeof actual_before));
    old_previews = preview_calls;
    assert(preview_display(&again) == EQUIPMENT_OK);
    assert(preview_calls == old_previews && !memcmp(&display, &again, sizeof again));
    project_all(&display.before, &display.after);
    unchanged(&frozen);
    assert(gear_menu_input(2) == 0); /* B cancels through the parent menu. */
    assert(gear_menu_input(8) == 0); /* START closes through the parent menu. */
    unchanged(&frozen);

    assert(equipment_equip(&expected_equipment, slot, candidate,
                           game_gear_base_hp(), &expected_hp, 0, &raw) == EQUIPMENT_OK);
    assert(equipment_derive(&expected_equipment, game_gear_base_hp(), &derived));
    game_gear_bonus_stats(&derived);
    assert(!memcmp(&display.after, &derived, sizeof derived));
    assert(display.hp_before_q4 == (unsigned)frozen.hearts);
    assert(display.hp_after_q4 == expected_hp && expected_hp <= frozen.hearts);
    expected_save = adventure_save;
    expected_save.equipment = expected_equipment;

    assert(gear_menu_input(1) == 1);
    assert(saves == frozen.save_calls + 1 && sounds == frozen.sound_calls + 1);
    assert(selections == frozen.selection_calls + 2);
    assert(!memcmp(&expected_save, &adventure_save, sizeof expected_save));
    assert(!memcmp(&display.after, &gear_stats, sizeof gear_stats));
    assert(hero_hp_q4 == expected_hp && hp == (hero_hp_q4 + 15) / 16);
    combat_unchanged(&frozen);
    for (command = 1; command <= 128; ++command) {
        projection_exact(&display.after, command, &promised);
        projection_exact(&gear_stats, command, &actual);
        assert(!memcmp(&promised, &actual, sizeof actual));
        assert(actual.recovery_updates == companion_guide_recovery(command));
        assert(actual.recovery_updates == game_power_cooldown(command <= 4 ? 75u : creatures_ability(command)->cooldown_updates));
    }
    snapshot(&frozen);
    assert(preview_display(&post) == EQUIPMENT_OK);
    assert(preview_calls == old_previews); /* The commit seeds raw cache data. */
    assert(!memcmp(&post.before, &gear_stats, sizeof gear_stats));
    assert(!memcmp(&post.after, &gear_stats, sizeof gear_stats));
    assert(post.hp_before_q4 == expected_hp && post.hp_after_q4 == expected_hp);
    project_all(&post.before, &post.after);
    unchanged(&frozen);
}

static unsigned matrix(void) {
    unsigned bag, base, bits, upgrade, item, cases = 0;
    static const unsigned weapons[] = {1, 9, 17, 4, 10, 19, 7, 14};
    for (bag = 0; bag < 2; ++bag)
    for (base = 6; base <= 8; base += 2)
    for (bits = 0; bits < 8; ++bits)
    for (upgrade = 0; upgrade < 2; ++upgrade)
    for (item = 0; item < EQUIPMENT_AUTHORED_COUNT; ++item) {
        unsigned i, id = equipment_authored_ids[item], ref;
        fresh(base, bits, upgrade);
        own_all();
        ref = equipment_find(&adventure_save.equipment, id);
        if (bag) {
            /* Obtain real stable sparse refs by discarding a previously full bag. */
            for (i = 1; i < EQUIPMENT_BAG_CAPACITY; ++i) if (i != ref) {
                EquipmentU16 current = (EquipmentU16)hero_hp_q4;
                assert(equipment_discard(&adventure_save.equipment, i,
                           game_gear_base_hp(), &current, 0, 1) == EQUIPMENT_OK);
                assert(current == hero_hp_q4);
            }
            assert(equipment_count(&adventure_save.equipment) == (id == 1 ? 1u : 2u));
        } else {
            equip_id(weapons[(item + bits) % 8]);
            equip_id(34); equip_id(50); equip_id(69); equip_id(88);
        }
        assert(equipment_validate(&adventure_save.equipment));
        hero_hp_q4 = item % 3 == 0 ? 0 : item % 3 == 1 ? 80 : gear_stats.max_hp_q4;
        hp = (hero_hp_q4 + 15) / 16;
        seed_combat();
        saves = sounds = selections = 0;
        compare_commit(equipment_definition(id)->slot, ref);
        ++cases;
        compare_commit(equipment_definition(id)->slot, EQUIPMENT_EMPTY_REF);
        ++cases;
    }
    return cases;
}

static void starter_and_browsing(void) {
    unsigned slot, i;
    RuntimeSnapshot before;
    EquipmentComparison comparison;
    fresh(6, 0, 0);
    snapshot(&before);
    for (i = 0; i < 12; ++i) {
        assert(gear_menu_input(i & 1u ? 64 : 128) == 1);
        assert(preview_display(&comparison) == EQUIPMENT_OK);
        unchanged(&before);
    }
    for (slot = 0; slot < EQUIPMENT_SLOT_COUNT; ++slot)
        compare_commit(slot, EQUIPMENT_EMPTY_REF);
    assert(adventure_save.equipment.equipped[0] == 0);
    assert(gear_stats.weapon_class == EQUIPMENT_SWORD);
    assert(equipment_count(&adventure_save.equipment) == 1);
    fresh(8, 7, 1);
    own_all();
    snapshot(&before);
    for (slot = 0; slot < EQUIPMENT_SLOT_COUNT; ++slot) {
        gear_menu_slot = (int)slot;
        gear_menu_candidate = adventure_save.equipment.equipped[slot];
        for (i = 0; i < 50; ++i) {
            assert(gear_menu_input(128) == 1);
            assert(preview_display(&comparison) == EQUIPMENT_OK);
            unchanged(&before);
        }
    }
}

static void live_locks_and_ownership(void) {
    unsigned mode;
    EquipmentComparison comparison;
    RuntimeSnapshot before;
    fresh(8, 7, 1);
    gear_menu_slot = EQUIPMENT_BODY;
    gear_menu_candidate = (int)claim(34);
    assert(preview_display(&comparison) == EQUIPMENT_OK);
    for (mode = 0; mode < 16; ++mode) {
        seed_combat();
        if (mode < 4) weapon_action.phase = (unsigned char)(mode + 1u);
        else if (mode == 4) roll_ticks = 6;
        else if (mode == 5) player_arrows[0].active = 1;
        else if (mode == 6) player_arrows[1].active = 1;
        else if (mode == 7) shots[4] = (Shot){31, 17, 2, 0, 8, 0};
        else if (mode == 8) { regional_power_kind = 11; regional_power_time = 9; }
        else chapter_busy = 1u << (mode - 9u);
        assert(game_gear_busy());
        snapshot(&before);
        assert(preview_display(&comparison) == EQUIPMENT_OK);
        project_all(&comparison.before, &comparison.after);
        assert(gear_menu_input(2) == 0 && gear_menu_input(8) == 0);
        unchanged(&before);
        assert(gear_menu_input(1) == 1); /* A must re-read the current live lock. */
        unchanged(&before);
    }
    seed_combat();
    assert(preview_display(&comparison) == EQUIPMENT_OK);
    adventure_save.equipment.bag[gear_menu_candidate].quantity = 0;
    snapshot(&before);
    assert(gear_menu_input(1) == 1);
    unchanged(&before);
    assert(preview_display(&comparison) == EQUIPMENT_INVALID);
    unchanged(&before);

    /* A valid discard leaves seen/history bits set, but is no longer ownership. */
    adventure_save.equipment.bag[gear_menu_candidate].quantity = 1;
    assert(preview_display(&comparison) == EQUIPMENT_OK);
    { EquipmentU16 current = (EquipmentU16)hero_hp_q4;
      assert(equipment_discard(&adventure_save.equipment, (unsigned)gear_menu_candidate,
                   game_gear_base_hp(), &current, 0, 1) == EQUIPMENT_OK); }
    assert(equipment_seen(&adventure_save.equipment, 34));
    snapshot(&before);
    assert(gear_menu_input(1) == 1);
    unchanged(&before);
    assert(preview_display(&comparison) == EQUIPMENT_INVALID);
    unchanged(&before);
}

static void reachable_caps_and_equal_rings(void) {
    unsigned bits, weapon;
    EquipmentComparison cmp;
    GearPreview before, after;
    for (bits = 0; bits < 8; ++bits) {
        fresh(8, bits, 1);
        own_all();
        equip_id(50); equip_id(69); equip_id(88);
        gear_menu_slot = EQUIPMENT_BOOTS;
        gear_menu_candidate = (int)equipment_find(&adventure_save.equipment, 52);
        assert(preview_display(&cmp) == EQUIPMENT_OK);
        projection_exact(&cmp.before, 1, &before);
        projection_exact(&cmp.after, 1, &after);
        assert(before.recovery_updates == (bits & 2u ? 59u : 67u));
        assert(after.recovery_updates == before.recovery_updates);
        assert(after.recovery_hundredths == before.recovery_hundredths);
        assert(after.walk_tenths < before.walk_tenths);
        assert(context_label(&cmp, &before, &after, 1) == GP_RECOVERY_CAP);
        compare_commit(EQUIPMENT_BOOTS, (unsigned)gear_menu_candidate);
        for (weapon = 0; weapon < 2; ++weapon) {
            equip_id(weapon ? 10u : 4u); equip_id(67); equip_id(84);
            gear_menu_slot = EQUIPMENT_BELT;
            gear_menu_candidate = EQUIPMENT_EMPTY_REF;
            assert(preview_display(&cmp) == EQUIPMENT_OK);
            assert(cmp.before.stagger == 3 && cmp.after.stagger == 3);
            projection_exact(&cmp.before, 128, &before);
            projection_exact(&cmp.after, 128, &after);
            assert(before.stagger == after.stagger);
            assert(context_label(&cmp, &before, &after, 128) == GP_STAGGER_CAP);
            compare_commit(EQUIPMENT_BELT, EQUIPMENT_EMPTY_REF);
        }
        equip_id(83);
        gear_menu_slot = EQUIPMENT_RING;
        gear_menu_candidate = (int)equipment_find(&adventure_save.equipment, 86);
        assert(preview_display(&cmp) == EQUIPMENT_OK);
        assert(!memcmp(&cmp.before, &cmp.after, sizeof cmp.before));
        for (weapon = 1; weapon <= 128; ++weapon) {
            projection_exact(&cmp.before, weapon, &before);
            projection_exact(&cmp.after, weapon, &after);
            assert(!memcmp(&before, &after, sizeof after));
            assert(context_label(&cmp, &before, &after, weapon) == GP_SAME);
        }
        compare_commit(EQUIPMENT_RING, (unsigned)gear_menu_candidate);
    }
}

static void cache_keys(void) {
    EquipmentComparison display, reference;
    EquipmentState good;
    RuntimeSnapshot before;
    unsigned i, count;
    unsigned char *bytes;
    fresh(6, 0, 0);
    assert(preview_display(&display) == EQUIPMENT_OK);
    good = adventure_save.equipment;
    bytes = (unsigned char *)&adventure_save.equipment;
    for (i = 0; i < sizeof good; ++i) {
        unsigned expected;
        bytes[i] ^= 1;
        snapshot(&before);
        count = preview_calls;
        expected = equipment_preview(&adventure_save.equipment,
                   (unsigned)gear_menu_slot, (unsigned)gear_menu_candidate,
                   game_gear_base_hp(), game_gear_hp(), 0, &reference);
        assert(preview_display(&display) == expected && preview_calls == count + 1);
        if (expected == EQUIPMENT_OK) {
            game_gear_bonus_stats(&reference.before);
            game_gear_bonus_stats(&reference.after);
            assert(!memcmp(&display, &reference, sizeof display));
        }
        unchanged(&before);
        bytes[i] ^= 1;
        count = preview_calls;
        assert(preview_display(&display) == EQUIPMENT_OK && preview_calls == count + 1);
    }
    assert(!memcmp(&good, &adventure_save.equipment, sizeof good));
    count = preview_calls; max_hp = 8;
    assert(preview_display(&display) == EQUIPMENT_OK && preview_calls == count + 1);
    assert(display.after.max_hp_q4 == 128);
    count = preview_calls; --hero_hp_q4;
    assert(preview_display(&display) == EQUIPMENT_OK && preview_calls == count + 1);
    count = preview_calls; adventure_save.economy.relics = 7;
    assert(preview_display(&display) == EQUIPMENT_OK && preview_calls == count + 1);
    assert(display.after.max_hp_q4 == 144 && display.after.attack_q4 == 4);
    assert(display.after.power_cooldown == 67);
    count = preview_calls; adventure_save.economy.upgrade = 1;
    assert(preview_display(&display) == EQUIPMENT_OK && preview_calls == count + 1);
    assert(display.after.attack_q4 == 8);
    count = preview_calls; gear_menu_slot = EQUIPMENT_BODY; gear_menu_candidate = EQUIPMENT_EMPTY_REF;
    assert(preview_display(&display) == EQUIPMENT_OK && preview_calls == count + 1);
    count = preview_calls; gear_menu_reset();
    assert(preview_display(&display) == EQUIPMENT_OK && preview_calls == count + 1);
}

static void conversion_domain(void) {
    unsigned updates, reduction, command, speed;
    EquipmentStats stats;
    GearPreview projected;
    for (updates = 0; updates <= 65535; ++updates)
        assert(gear_preview_hundredths(updates) == reference_hundredths(updates));
    fresh(6, 0, 0);
    stats = gear_stats;
    for (reduction = 0; reduction <= GAME_MAX_POWER_RECOVERY; ++reduction) {
        stats.power_cooldown = (unsigned char)(EQUIPMENT_BASE_POWER_COOLDOWN - reduction);
        for (command = 1; command <= 128; ++command) projection_exact(&stats, command, &projected);
    }
    for (speed = EQUIPMENT_MIN_SPEED_Q8; speed <= EQUIPMENT_MAX_SPEED_Q8; ++speed) {
        stats.speed_q8 = (EquipmentU16)speed;
        projection_exact(&stats, 1, &projected);
    }
    stats = gear_stats;
    projection_exact(&stats, 1, &projected);
    assert(projected.walk_tenths == 1000 && projected.recovery_updates == 75);
    assert(projected.recovery_hundredths == 126);
}

int main(void) {
    unsigned cases;
    assert(equipment_catalog_validate());
    conversion_domain();
    starter_and_browsing();
    live_locks_and_ownership();
    cache_keys();
    reachable_caps_and_equal_rings();
    cases = matrix();
    printf("PASS Gear preview: %u item/removal commits across 48 items, 8 passive combinations, "
           "2 shop states, story bases 6/8 and full/sparse bags; all 128 commands, "
           "actual effective runtime stats, cap/duplicate ties, full save/combat preservation, "
           "fresh busy/ownership rejection, no auto-equip or healing\n", cases);
    return 0;
}
