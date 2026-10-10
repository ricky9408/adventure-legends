/* Bounded balance probe: actual equipment derive/preview/commit, runtime bonus,
 * refresh/apply, and economy functions. Only absent chapter invalidation hooks
 * are stubs. This is synthetic gear ownership, not acquisition-route evidence. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gear_runtime.h"
#include "gear_menu.h"
#include "progression.h"
#include "economy.h"

Save5State adventure_save;
volatile int hp, max_hp;
int gfx_slash_frame, ability_cd, ability_max, sword_cd;
static unsigned invalidations;
void covenants_powers_selection_changed(void) { ++invalidations; }
void covenants_game_selection_changed(void) { ++invalidations; }

static unsigned ref(unsigned id) {
    unsigned r = equipment_find(&adventure_save.equipment, id);
    assert(r != EQUIPMENT_EMPTY_REF);
    return r;
}

static void reset(void) {
    unsigned i;
    memset(&adventure_save, 0, sizeof adventure_save);
    equipment_init(&adventure_save.equipment);
    for (i = 1; i < EQUIPMENT_AUTHORED_COUNT; ++i)
        assert(equipment_claim(&adventure_save.equipment,
               equipment_reward_item(i), i, 0) == EQUIPMENT_OK);
    max_hp = 6;
    hero_hp_q4 = 63;
    ability_cd = 37;
    ability_max = 71;
    sword_cd = 19;
    /* Nonzero transient state makes accidental attack resets visible. */
    memset(&weapon_action, 0, sizeof weapon_action);
    weapon_action.weapon_class = EQUIPMENT_SWORD;
    weapon_action.combo_clock = 17;
    weapon_action.hit_mask = 0x12;
    memset(player_arrows, 0, sizeof player_arrows);
    player_arrows[0].x_q8 = 0x1234;
    game_health_refresh(0);
}

static void commit(unsigned slot, unsigned item) {
    EquipmentComparison preview, applied;
    EquipmentStats effective_before, effective_after, derived;
    EquipmentState before = adventure_save.equipment, expected;
    WeaponAttack action = weapon_action;
    WeaponArrow arrows[WEAPON_ARROW_CAPACITY];
    EquipmentU16 current_hp = (EquipmentU16)hero_hp_q4;
    unsigned r = item ? ref(item) : EQUIPMENT_EMPTY_REF;
    unsigned hooks = invalidations;
    unsigned i;
    memcpy(arrows, player_arrows, sizeof arrows);
    assert(equipment_preview(&adventure_save.equipment, slot, r,
           game_gear_base_hp(), current_hp, 0, &preview) == EQUIPMENT_OK);
    assert(!memcmp(&before, &adventure_save.equipment, sizeof before));
    effective_before = preview.before;
    effective_after = preview.after;
    game_gear_bonus_stats(&effective_before);
    game_gear_bonus_stats(&effective_after);
    assert(!memcmp(&gear_stats, &effective_before, sizeof gear_stats));
    assert(equipment_equip(&adventure_save.equipment, slot, r,
           game_gear_base_hp(), &current_hp, 0, &applied) == EQUIPMENT_OK);
    assert(!memcmp(&preview, &applied, sizeof preview));
    expected = before;
    expected.equipped[slot] = (EquipmentU8)r;
    assert(!memcmp(&expected, &adventure_save.equipment, sizeof expected));
    assert(equipment_derive(&adventure_save.equipment, game_gear_base_hp(), &derived));
    assert(!memcmp(&derived, &preview.after, sizeof derived));
    game_gear_apply_stats(current_hp, &applied.after);
    assert(invalidations == hooks + 2);
    assert(!memcmp(&gear_stats, &effective_after, sizeof gear_stats));
    assert(hero_hp_q4 == 63 && current_hp == 63 && preview.hp_after_q4 == 63);
    assert(ability_cd == 37 && ability_max == 71 && sword_cd == 19);
    assert(!memcmp(&action, &weapon_action, sizeof action));
    assert(!memcmp(arrows, player_arrows, sizeof arrows));
    for (i = 0; i < 8; ++i) {
        game_health_refresh(0);
        assert(!memcmp(&gear_stats, &effective_after, sizeof gear_stats));
        assert(hero_hp_q4 == 63 && ability_cd == 37 && ability_max == 71 && sword_cd == 19);
    }
    game_gear_apply(current_hp);
    assert(!memcmp(&gear_stats, &effective_after, sizeof gear_stats));
    assert(hero_hp_q4 == 63 && ability_cd == 37 && ability_max == 71 && sword_cd == 19);
    assert(!memcmp(&action, &weapon_action, sizeof action));
    assert(!memcmp(arrows, player_arrows, sizeof arrows));
}

static void frozen_identity_and_other_items(void) {
    const EquipmentDefinition *porchlight = equipment_definition(89);
    const EquipmentDefinition *listening = equipment_definition(88);
    EquipmentDefinition snapshot[EQUIPMENT_DEFINITION_CAPACITY];
    unsigned i;
    assert(sizeof(EquipmentState) == 512 && sizeof(EquipmentRecord) == 8);
    assert(sizeof(EquipmentDefinition) == 24 && equipment_catalog_validate());
    assert(porchlight->stats.power_reduction == 4 && porchlight->stats.roll_reduction == 1);
    assert(porchlight->stats.speed_q8_delta == -4);
    assert(listening->stats.power_reduction == 5 && listening->stats.roll_reduction == 0);
    assert(listening->stats.speed_q8_delta == -2);
    assert(equipment_reward_source(89) == 47 && equipment_reward_item(47) == 89);
    memcpy(snapshot, equipment_definitions, sizeof snapshot);
    for (i = 0; i < EQUIPMENT_AUTHORED_COUNT; ++i) {
        unsigned id = equipment_reward_item(i);
        const EquipmentDefinition *d = equipment_definition(id);
        EquipmentStats raw;
        unsigned extra = id == 89 ? 1u : 0u;
        reset();
        commit(d->slot, id);
        assert(equipment_derive(&adventure_save.equipment, 96, &raw));
        assert(raw.power_cooldown == 75u - d->stats.power_reduction - extra);
        assert(raw.roll_cooldown == 42u - d->stats.roll_reduction);
        assert(raw.speed_q8 == 320 + d->stats.speed_q8_delta);
        assert(raw.diagonal_q8 == ((raw.speed_q8 * 181u + 128u) >> 8));
        assert(raw.max_hp_q4 == 96 + d->stats.hp_q4);
        assert(raw.attack_q4 == d->stats.attack_q4);
        assert(raw.defense_q4 == d->stats.defense_q4);
        assert(raw.reach_px == d->stats.reach_px && raw.stagger == d->stats.stagger);
    }
    assert(!memcmp(snapshot, equipment_definitions, sizeof snapshot));
    puts("PASS all48 authored items: only89 receives +1 recovery; catalog/history/save layout unchanged");
}

static void tradeoff(unsigned boots, unsigned belt, unsigned listening_recovery,
                     unsigned porchlight_recovery, const char *label) {
    unsigned claims, relic;
    for (claims = 0; claims < 16; ++claims) for (relic = 0; relic < 2; ++relic) {
        EquipmentStats listening, porchlight;
        unsigned economy_recovery = 8u * relic + ((claims & 4u) ? 4u : 0u);
        reset();
        adventure_save.economy.later_claims = (unsigned char)claims;
        adventure_save.economy.relics = (unsigned char)(4u | (relic ? 2u : 0u));
        adventure_save.economy.upgrade = 1;
        game_health_refresh(0);
        commit(EQUIPMENT_BOOTS, boots);
        commit(EQUIPMENT_BELT, belt);
        commit(EQUIPMENT_RING, 88);
        listening = gear_stats;
        assert(listening.power_cooldown == 75u - listening_recovery - economy_recovery);
        commit(EQUIPMENT_RING, 89);
        porchlight = gear_stats;
        assert(porchlight.power_cooldown == 75u - porchlight_recovery - economy_recovery);
        assert(75u - porchlight.power_cooldown - economy_recovery <= 8u);
        assert(porchlight.speed_q8 + 2u == listening.speed_q8);
        assert(porchlight.attack_q4 == listening.attack_q4 && porchlight.attack_q4 == 8);
        assert(porchlight.max_hp_q4 == listening.max_hp_q4);
        assert(porchlight.defense_q4 == listening.defense_q4);
        assert(porchlight.reach_px == listening.reach_px && porchlight.stagger == listening.stagger);
        assert(game_power_cooldown(75) == porchlight.power_cooldown);
        assert(game_power_cooldown(120) == 120u - porchlight_recovery - economy_recovery);
        assert(game_power_cooldown(1) == 1 && game_power_cooldown(0) == 1);
        commit(EQUIPMENT_RING, 88);
        assert(!memcmp(&gear_stats, &listening, sizeof listening));
        commit(EQUIPMENT_RING, 89);
        assert(!memcmp(&gear_stats, &porchlight, sizeof porchlight));
        commit(EQUIPMENT_RING, 89); /* Re-equip never stacks the overlay. */
        assert(!memcmp(&gear_stats, &porchlight, sizeof porchlight));
        commit(EQUIPMENT_RING, 0);
        assert(gear_stats.attack_q4 == 8 && hero_hp_q4 == 63 && ability_cd == 37);
    }
    printf("PASS %s: Listening%u/Porchlight%u equipment recovery, speed tradeoff2; all32 passive/relic states\n",
           label, listening_recovery, porchlight_recovery);
}

int main(void) {
    frozen_identity_and_other_items();
    tradeoff(0, 0, 5, 6, "alone");
    tradeoff(55, 0, 7, 8, "near cap, Walkway Boots");
    tradeoff(50, 0, 8, 8, "already capped, Surestep Boots");
    tradeoff(52, 69, 8, 8, "over cap, Softsand Boots + Reedcourier Belt");
    puts("PASS production derive/preview/commit/bonus/apply/refresh parity; no attack, HP, or current cooldown reset");
    return 0;
}
