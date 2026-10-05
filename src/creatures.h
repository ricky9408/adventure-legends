#ifndef ADVENTURE_LEGENDS_CREATURES_H
#define ADVENTURE_LEGENDS_CREATURES_H
/* Freestanding C99. Only explicit byte encoding in save5 may persist these
 * records. All definitions and lookups live in ROM; no malloc or hidden state. */
typedef unsigned char CreatureU8;
typedef unsigned short CreatureU16;
typedef unsigned int CreatureU32;
typedef CreatureU8 FormId;

enum {
    CREATURE_FORM_CAPACITY = 128, CREATURE_ENABLED_COUNT = 8,
    CREATURE_ROSTER_CAPACITY = 160, CREATURE_PARTY_CAPACITY = 4,
    CREATURE_EMPTY_SLOT = 255, CREATURE_MAX_LEVEL = 50,
    CREATURE_MAX_BOND = 100, CREATURE_EXPEDITION_BOND_CAP = 10,
    CREATURE_XP_CAP = 470596,
    CREATURE_OCCUPIED = 1, CREATURE_STORY_LOCKED = 2, CREATURE_FAVORITE = 4,
    CREATURE_FLAGS_MASK = 7,
    CREATURE_GROVE_CLEAR = 1, CREATURE_SKY_CLEAR = 2, CREATURE_CORE_CLEAR = 4,
    CREATURE_TRIAL_HEARTH = 1, CREATURE_TRIAL_CANOPY = 2,
    CREATURE_TRIAL_WIND_LOOM = 4, CREATURE_TRIAL_AMBER_ARCH = 8,
    CREATURE_TRIAL_MASK = 15,
    CREATURE_EVENT_CAPACITY = 512, CREATURE_FIELD_EVENT_BASE = 384,
    CREATURE_NICKNAME_MAX = 0 /* Named presets are not authored yet. */
};
/* Wuxing phases and polarity are independent axes. Wind is an ability. */
enum CreaturePhase {
    CREATURE_WOOD = 0, CREATURE_FIRE, CREATURE_EARTH,
    CREATURE_METAL, CREATURE_WATER, CREATURE_PHASE_COUNT
};
enum CreaturePolarity { CREATURE_YIN = 0, CREATURE_YANG = 1 };
enum FieldCapability {
    FIELD_BREAK_CRACK = 1u << 0, FIELD_BURN_THORNS = 1u << 1,
    FIELD_DRAW_ORE = 1u << 2, FIELD_DRIVE_SAIL = 1u << 3,
    FIELD_EARTH_SOCKET = 1u << 4, FIELD_EXPOSE_FIRE = 1u << 5,
    FIELD_EXPOSE_STONE = 1u << 6, FIELD_EXPOSE_WIND = 1u << 7,
    FIELD_FILL_BASIN = 1u << 8, FIELD_FIRE_SOCKET = 1u << 9,
    FIELD_GROW_BRIDGE = 1u << 10, FIELD_GROW_ROOTS = 1u << 11,
    FIELD_IGNITE = 1u << 12, FIELD_LINK_POOLS = 1u << 13,
    FIELD_PRESS_WEIGHT = 1u << 14, FIELD_REVEAL_CURRENT = 1u << 15,
    FIELD_TUNE_LATCH = 1u << 16, FIELD_TURN_VANE = 1u << 17,
    FIELD_UNCAP_WELL = 1u << 18, FIELD_WIND_SOCKET = 1u << 19,
    FIELD_WOOD_SOCKET = 1u << 20
};
#define FIELD_HOMURA (FIELD_IGNITE | FIELD_BURN_THORNS | FIELD_FIRE_SOCKET | FIELD_EXPOSE_FIRE)
#define FIELD_MIDORI (FIELD_GROW_BRIDGE | FIELD_GROW_ROOTS | FIELD_WOOD_SOCKET)
#define FIELD_FUURI (FIELD_TURN_VANE | FIELD_DRIVE_SAIL | FIELD_WIND_SOCKET | FIELD_EXPOSE_WIND)
#define FIELD_KOHAKU (FIELD_BREAK_CRACK | FIELD_PRESS_WEIGHT | FIELD_UNCAP_WELL | FIELD_EARTH_SOCKET | FIELD_EXPOSE_STONE)

typedef struct CreatureInstance {
    CreatureU8 form_id, flags, level, bond;
    CreatureU32 xp, instance_id;
    CreatureU16 nickname_id, trial_flags;
    CreatureU8 equipped[2], polarity, selected_command;
    CreatureU32 cosmetic_seed;
} CreatureInstance;

typedef struct CreatureRoster {
    CreatureInstance instances[CREATURE_ROSTER_CAPACITY];
    CreatureU8 party[CREATURE_PARTY_CAPACITY];
    CreatureU8 selected_party; /* party position, not roster index */
    CreatureU32 next_instance_id; /* never zero; UINT_MAX means exhausted */
    CreatureU8 seen[16], obtained[16], rewards[16];
    CreatureU8 expedition_bond[CREATURE_ROSTER_CAPACITY];
    CreatureU8 expedition_events[64];
    CreatureU8 lifetime_field_aid[16];
} CreatureRoster;

typedef struct CreatureLearn { CreatureU8 level, ability_id; } CreatureLearn;
/* Exactly 32 bytes, no pointers, no implicit catalog/encounter fallback. */
typedef struct CreatureForm {
    CreatureU8 id, family, phase, polarity, tier, rarity;
    CreatureU8 stats[5], signature_ability;
    CreatureU32 field_caps;
    CreatureU16 name_id, learnset_offset;
    CreatureU8 learnset_count, evolution_count;
    CreatureU16 evolution_offset;
    CreatureU32 sprite_offset;
    CreatureU16 portrait_id, flags;
} CreatureForm;
typedef struct CreatureEvolution {
    CreatureU8 from, to, min_level, min_bond;
    CreatureU16 trial_flag, chapter_flags;
} CreatureEvolution;
typedef struct CreatureAbility {
    CreatureU8 id, phase;
    CreatureU16 cooldown_updates;
    CreatureU32 field_caps;
} CreatureAbility;
extern const CreatureForm creature_forms[CREATURE_ENABLED_COUNT];
extern const CreatureLearn creature_learnsets[12];
extern const CreatureEvolution creature_evolutions[4];
extern const CreatureAbility creature_abilities[8];
extern const FormId creature_legacy_forms[4];

/* Valid identity is not enabled content. 3, 13, 121 and 128 remain disabled. */
int creatures_form_id_valid(unsigned form_id);
const CreatureForm *creatures_form(unsigned form_id);
const CreatureAbility *creatures_ability(unsigned ability_id);
const char *creatures_name(unsigned form_id);
const char *creatures_ability_name(unsigned ability_id);
unsigned creatures_legacy_spirit(unsigned form_id); /* 255 if unavailable */
CreatureU32 creatures_capabilities(unsigned form_id);
int creatures_has_capability(unsigned form_id, CreatureU32 needed);
unsigned creatures_phase_multiplier_q8(unsigned attacker, unsigned defender); /* 0 invalid */
unsigned creatures_generated_phase(unsigned phase); /* 255 invalid */
int creatures_catalog_validate(void);

CreatureU32 creatures_xp_threshold(unsigned level); /* UINT_MAX invalid */
unsigned creatures_level_for_xp(CreatureU32 xp); /* saturates at 50 */
int creatures_command_learned(unsigned form_id, unsigned level, unsigned ability_id);
int creatures_instance_validate(const CreatureInstance *instance);
int creatures_roster_validate(const CreatureRoster *roster);
int creatures_party_validate(const CreatureRoster *roster);
void creatures_roster_init(CreatureRoster *roster);
unsigned creatures_roster_count(const CreatureRoster *roster);
CreatureU32 creatures_party_capabilities(const CreatureRoster *roster);
int creatures_party_set(CreatureRoster *roster, const CreatureU8 party[4], CreatureU32 required_caps);
/* Adds an enabled form; callers author acquisition gates. Returns slot or 255.
 * reward_id 1..4 is reserved for matching story families; 5..128 is a
 * general one-time transaction; 0 means repeatable. At capacity
 * nothing changes, including the reward ledger. Story grants use the API below. */
unsigned creatures_grant(CreatureRoster *roster, unsigned form_id, unsigned level,
                         unsigned bond, unsigned flags, unsigned reward_id);
unsigned creatures_grant_story(CreatureRoster *roster, unsigned legacy_spirit,
                               unsigned chapter_flags); /* slot or 255 */
int creatures_migrate_legacy(CreatureRoster *roster, unsigned chapter_flags,
                             unsigned legacy_spirit);
/* Explicit chapter catch-up compensation; never decreases existing XP/bond. */
int creatures_apply_story_floors(CreatureRoster *roster, unsigned chapter_flags);
int creatures_add_xp(CreatureInstance *instance, CreatureU32 amount);
int creatures_equip(CreatureInstance *instance, unsigned command_slot, unsigned ability_id);
int creatures_select_command(CreatureInstance *instance, unsigned command_slot);

/* Caller persists these fields in the shared quest/bond reservation. Departing
 * sanctuary starts a new expedition; resting alone never grants bond. */
void creatures_begin_expedition(CreatureRoster *roster);
enum CreatureCreditKind { CREATURE_CREDIT_ENCOUNTER = 0, CREATURE_CREDIT_FIELD_AID = 1,
                           CREATURE_CREDIT_PERSONAL_QUEST = 2 };
/* Events are 0..511. Field aids exclusively use 384..511, mapped to lifetime
 * first-aid bits 0..127. XP and bond go once to every valid current party member.
 * Return 1 credited, 0 already credited/no party, -1 invalid. Shared event bits
 * prevent swapping members to re-credit. Encounter/quest IDs must be <384. */
int creatures_credit_event(CreatureRoster *roster, unsigned event_id,
                           CreatureU32 xp, unsigned kind);
int creatures_mark_trial(CreatureInstance *instance, unsigned trial_flag);

enum CreatureEvolutionStatus {
    CREATURE_EVOLVE_READY = 0, CREATURE_EVOLVE_INVALID,
    CREATURE_EVOLVE_NO_EDGE, CREATURE_EVOLVE_LEVEL,
    CREATURE_EVOLVE_BOND, CREATURE_EVOLVE_STORY,
    CREATURE_EVOLVE_TRIAL, CREATURE_EVOLVE_SANCTUARY,
    CREATURE_EVOLVE_DEFERRED
};
const CreatureEvolution *creatures_evolution(unsigned form_id);
/* READY ignores confirmation so UI can show eligibility; evolve requires it.
 * Deferring is explicit and leaves every roster byte unchanged. */
unsigned creatures_can_evolve(const CreatureInstance *instance, unsigned chapter_flags,
                              int at_sanctuary);
unsigned creatures_evolve(CreatureRoster *roster, unsigned roster_slot,
                          unsigned chapter_flags, int at_sanctuary, int confirmed);
unsigned creatures_defer_evolution(const CreatureInstance *instance);
#endif
