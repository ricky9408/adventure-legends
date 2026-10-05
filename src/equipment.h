#ifndef EMBERBOND_EQUIPMENT_H
#define EMBERBOND_EQUIPMENT_H
/* Freestanding C99. Cold ROM code; no allocation or implicit persistence.
 * Save codecs must encode each field explicitly, never memcpy this struct. */
typedef unsigned char EquipmentU8;
typedef unsigned short EquipmentU16;
typedef unsigned int EquipmentU32;
typedef signed short EquipmentS16;
typedef EquipmentU16 EquipmentItemId;

enum {
    EQUIPMENT_DEFINITION_CAPACITY = 512, EQUIPMENT_AUTHORED_COUNT = 13,
    EQUIPMENT_BAG_CAPACITY = 48, EQUIPMENT_SLOT_COUNT = 5,
    EQUIPMENT_EMPTY_REF = 255, EQUIPMENT_STARTER_ID = 1,
    EQUIPMENT_REWARD_CAPACITY = 64, EQUIPMENT_SAVE_BYTES = 512,
    EQUIPMENT_CLAIM_BATCH_MAX = 4,
    EQUIPMENT_PROTECTED = 1, EQUIPMENT_RECORD_FLAGS_MASK = 1,
    EQUIPMENT_NEUTRAL_PHASE = 255,
    EQUIPMENT_MIN_HP_Q4 = 96, EQUIPMENT_MAX_HP_Q4 = 192,
    EQUIPMENT_BASE_SPEED_Q8 = 320, EQUIPMENT_MIN_SPEED_Q8 = 288,
    EQUIPMENT_MAX_SPEED_Q8 = 352, EQUIPMENT_MAX_ATTACK_Q4 = 24,
    EQUIPMENT_MAX_DEFENSE_Q4 = 8, EQUIPMENT_BASE_ROLL_COOLDOWN = 42,
    EQUIPMENT_BASE_POWER_COOLDOWN = 75, EQUIPMENT_HEAL_COOLDOWN = 360
};
enum EquipmentSlot {
    EQUIPMENT_WEAPON = 0, EQUIPMENT_BODY, EQUIPMENT_BOOTS,
    EQUIPMENT_BELT, EQUIPMENT_RING
};
enum EquipmentWeaponClass {
    EQUIPMENT_NO_WEAPON = 0, EQUIPMENT_SWORD, EQUIPMENT_LANCE, EQUIPMENT_BOW
};
enum EquipmentBusy {
    EQUIPMENT_BUSY_CHARGING = 1, EQUIPMENT_BUSY_ATTACKING = 2,
    EQUIPMENT_BUSY_RECOVERING = 4, EQUIPMENT_BUSY_ROLLING = 8,
    EQUIPMENT_BUSY_PLAYER_PROJECTILE = 16, EQUIPMENT_BUSY_MASK = 31
};
enum EquipmentResult {
    EQUIPMENT_OK = 0, EQUIPMENT_INVALID, EQUIPMENT_BUSY,
    EQUIPMENT_INCOMPATIBLE, EQUIPMENT_FULL, EQUIPMENT_DUPLICATE,
    EQUIPMENT_ALREADY_CLAIMED, EQUIPMENT_CANNOT_DISCARD,
    EQUIPMENT_NEEDS_CONFIRMATION
};
/* Wire offsets are documented constants for the single shared v5 codec. */
enum {
    EQUIPMENT_SAVE_BAG_OFFSET = 0, EQUIPMENT_SAVE_REFS_OFFSET = 384,
    EQUIPMENT_SAVE_SETTINGS_OFFSET = 389, EQUIPMENT_SAVE_SEEN_OFFSET = 400,
    EQUIPMENT_SAVE_WALLET_OFFSET = 464, EQUIPMENT_SAVE_CLAIMS_OFFSET = 480,
    EQUIPMENT_SAVE_RESERVED_OFFSET = 488
};
typedef struct EquipmentRecord {
    EquipmentU16 item_id;
    EquipmentU8 rank, flags, quantity, reserved[3];
} EquipmentRecord;
/* Unique handcrafted items: at most one live bag record per definition. Bag
 * records never compact. A reference denotes that unique owned instance, not
 * another copy. Collection history is not proof of current ownership. */
typedef struct EquipmentState {
    EquipmentRecord bag[EQUIPMENT_BAG_CAPACITY];
    EquipmentU8 equipped[EQUIPMENT_SLOT_COUNT];
    EquipmentU8 settings_reserved[11];
    EquipmentU8 seen[64];
    EquipmentU8 wallet_key_reserved[16];
    EquipmentU8 reward_claims[8];
    EquipmentU8 reserved[24];
} EquipmentState;
typedef struct EquipmentBonuses {
    EquipmentS16 attack_q4, defense_q4, hp_q4, speed_q8_delta;
    EquipmentS16 roll_reduction, power_reduction, reach_px, stagger;
} EquipmentBonuses;
/* 24 bytes including explicit padding; zero entries are disabled IDs. */
typedef struct EquipmentDefinition {
    EquipmentU16 id;
    EquipmentU8 slot, weapon_class, flags, phase, reserved[2];
    EquipmentBonuses stats;
} EquipmentDefinition;
typedef struct EquipmentMove {
    EquipmentU8 windup, active, recovery, damage_q4, reach_px, half_width_px;
} EquipmentMove;
typedef struct EquipmentWeapon {
    EquipmentU8 id, move_count, combo_window, buffer;
    EquipmentU16 lunge_q8, projectile_speed_q8;
    EquipmentU8 charge_min_updates, charge_max_updates, max_live_arrows, reserved;
    EquipmentMove moves[3];
} EquipmentWeapon;
typedef struct EquipmentStats {
    EquipmentU16 max_hp_q4, speed_q8, diagonal_q8;
    EquipmentU8 attack_q4, defense_q4, roll_cooldown, power_cooldown;
    EquipmentU8 reach_px, stagger, weapon_class, phase;
} EquipmentStats;
typedef struct EquipmentComparison {
    EquipmentStats before, after;
    EquipmentU16 hp_before_q4, hp_after_q4;
    EquipmentU8 slot, old_ref, new_ref, reserved;
} EquipmentComparison;
extern const EquipmentDefinition equipment_definitions[EQUIPMENT_DEFINITION_CAPACITY];
extern const EquipmentWeapon equipment_weapons[4];
extern const EquipmentItemId equipment_authored_ids[EQUIPMENT_AUTHORED_COUNT];
const EquipmentDefinition *equipment_definition(unsigned item_id);
const EquipmentWeapon *equipment_weapon(unsigned weapon_class);
const char *equipment_name(unsigned item_id);
const char *equipment_description(unsigned item_id, unsigned line);
int equipment_catalog_validate(void);
int equipment_record_validate(const EquipmentRecord *record);
/* Bounded codec helpers: refs checks five refs; reserved checks padding and
 * the 512-bit seen namespace, without scanning bag ownership/duplicates. */
int equipment_refs_validate(const EquipmentState *state);
int equipment_reserved_validate(const EquipmentState *state);
int equipment_validate(const EquipmentState *state);
void equipment_init(EquipmentState *state);
unsigned equipment_count(const EquipmentState *state);
unsigned equipment_find(const EquipmentState *state, unsigned item_id);
int equipment_seen(const EquipmentState *state, unsigned item_id);
/* Fixed acquisition namespace: source0..12 maps authored item order.
 * Other source IDs are reserved; this is independent of quest IDs. */
unsigned equipment_reward_item(unsigned reward_id); /* 0 invalid */
unsigned equipment_reward_source(unsigned item_id); /* 255 invalid */
int equipment_reward_claimed(const EquipmentState *state, unsigned reward_id);
/* reward_id is an enabled acquisition source0..12, matching item_id.
 * It is ALWAYS one-time. A FULL result changes no byte:
 * leave the source READY and retry after a confirmed discard. A previously
 * owned unique item marks the source claimed without granting a second copy,
 * including after a discard; seen is collection history, never ownership. */
unsigned equipment_claim(EquipmentState *state, unsigned item_id,
                         unsigned reward_id, unsigned *out_ref);
/* Atomic small reward bundles. Sources must be distinct enabled IDs, count
 * 1..4. Stages one 512-byte temporary state; FULL/INVALID changes nothing.
 * OK means some new gear, DUPLICATE means only new history claims, and
 * ALREADY_CLAIMED means all sources were already claimed. */
unsigned equipment_claim_many(EquipmentState *state,
                              const EquipmentU8 *reward_sources, unsigned count);
/* Input base HP is 0..65535; it is never modified. Zero/low bases clamp to 96.
 * Corrupt state is rejected and output remains untouched. */
int equipment_derive(const EquipmentState *state, unsigned base_hp_q4,
                     EquipmentStats *out);
/* All busy bits lock mutation; unknown bits are invalid. Empty ref means
 * unequip, with weapon falling back to protected starter at bag[0]. Preview
 * has the same validation as commit but changes no state or current HP. */
unsigned equipment_preview(const EquipmentState *state, unsigned slot, unsigned ref,
                           unsigned base_hp_q4, unsigned current_hp_q4,
                           unsigned busy, EquipmentComparison *out);
unsigned equipment_equip(EquipmentState *state, unsigned slot, unsigned ref,
                         unsigned base_hp_q4, EquipmentU16 *current_hp_q4,
                         unsigned busy, EquipmentComparison *out);
unsigned equipment_unequip(EquipmentState *state, unsigned slot,
                           unsigned base_hp_q4, EquipmentU16 *current_hp_q4,
                           unsigned busy, EquipmentComparison *out);
unsigned equipment_discard(EquipmentState *state, unsigned ref,
                           unsigned base_hp_q4, EquipmentU16 *current_hp_q4,
                           unsigned busy, int confirmed);
/* Only current HP may be clamped; action clocks, cooldown remaining, attack
 * snapshots and projectile state are deliberately absent from mutation APIs. */
#endif
