#include "equipment.h"

typedef char EquipmentRecordMustBe8Bytes[(sizeof(EquipmentRecord) == 8) ? 1 : -1];
typedef char EquipmentStateMustBe512Bytes[(sizeof(EquipmentState) == 512) ? 1 : -1];
typedef char EquipmentDefinitionMustBe24Bytes[(sizeof(EquipmentDefinition) == 24) ? 1 : -1];
typedef char EquipmentIntMustBe4Bytes[(sizeof(int) == 4) ? 1 : -1];
typedef char EquipmentU16MustBe2Bytes[(sizeof(EquipmentU16) == 2) ? 1 : -1];
typedef char EquipmentU32MustBe4Bytes[(sizeof(EquipmentU32) == 4) ? 1 : -1];

static void clear_bytes(void *p, unsigned length) {
    EquipmentU8 *b = (EquipmentU8 *)p;
    while (length--) *b++ = 0;
}
static void copy_bytes(void *destination, const void *source, unsigned length) {
    EquipmentU8 *d = (EquipmentU8 *)destination;
    const EquipmentU8 *s = (const EquipmentU8 *)source;
    while (length--) *d++ = *s++;
}
static int zero_bytes(const EquipmentU8 *p, unsigned length) {
    while (length--) if (*p++) return 0;
    return 1;
}
static int bit_get(const EquipmentU8 *p, unsigned bit) {
    return (p[bit >> 3] >> (bit & 7)) & 1;
}
static void bit_set(EquipmentU8 *p, unsigned bit) {
    p[bit >> 3] |= (EquipmentU8)(1u << (bit & 7));
}
static unsigned clamp(int value, int low, int high) {
    return (unsigned)(value < low ? low : value > high ? high : value);
}
const EquipmentDefinition *equipment_definition(unsigned id) {
    if (!id || id >= EQUIPMENT_DEFINITION_CAPACITY || equipment_definitions[id].id != id)
        return 0;
    return &equipment_definitions[id];
}
const EquipmentWeapon *equipment_weapon(unsigned id) {
    if (!id || id > EQUIPMENT_BOW || equipment_weapons[id].id != id) return 0;
    return &equipment_weapons[id];
}
static int definition_validate(const EquipmentDefinition *d) {
    const EquipmentBonuses *s = &d->stats;
    if (d->slot >= EQUIPMENT_SLOT_COUNT || (d->flags & ~EQUIPMENT_RECORD_FLAGS_MASK) ||
        d->reserved[0] || d->reserved[1] || d->phase != EQUIPMENT_NEUTRAL_PHASE ||
        d->flags != (d->id == EQUIPMENT_STARTER_ID ? EQUIPMENT_PROTECTED : 0) ||
        (d->slot == EQUIPMENT_WEAPON ? !equipment_weapon(d->weapon_class) :
                                     d->weapon_class != EQUIPMENT_NO_WEAPON) ||
        s->attack_q4 < 0 || s->attack_q4 > 24 || s->defense_q4 < 0 || s->defense_q4 > 8 ||
        s->hp_q4 < 0 || s->hp_q4 > 32 || s->speed_q8_delta < -16 || s->speed_q8_delta > 16 ||
        s->roll_reduction < 0 || s->roll_reduction > 6 ||
        s->power_reduction < 0 || s->power_reduction > 8 ||
        s->reach_px < 0 || s->reach_px > EQUIPMENT_MAX_REACH_PX || s->stagger < 0 || s->stagger > 3 ||
        (d->slot != EQUIPMENT_WEAPON && s->reach_px)) return 0;
    return 1;
}
int equipment_catalog_validate(void) {
    unsigned i, count = 0;
    for (i = 0; i < EQUIPMENT_DEFINITION_CAPACITY; ++i) {
        const EquipmentDefinition *d = &equipment_definitions[i];
        if (!d->id) {
            if (!zero_bytes((const EquipmentU8 *)d, sizeof(*d))) return 0;
        } else {
            if (d->id != i || !definition_validate(d)) return 0;
            ++count;
        }
    }
    if (count != EQUIPMENT_AUTHORED_COUNT ||
        equipment_definitions[1].slot != EQUIPMENT_WEAPON ||
        equipment_definitions[1].weapon_class != EQUIPMENT_SWORD) return 0;
    /* This is a persistent acquisition-source mapping, not a sorted index.
     * Append new sources without renumbering any previously saved claim. */
    for (i = 0; i < EQUIPMENT_AUTHORED_COUNT; ++i) {
        unsigned j;
        if (!equipment_definition(equipment_authored_ids[i])) return 0;
        for (j = 0; j < i; ++j)
            if (equipment_authored_ids[j] == equipment_authored_ids[i]) return 0;
    }
    for (i = 1; i <= EQUIPMENT_BOW; ++i) {
        const EquipmentWeapon *w = equipment_weapon(i);
        unsigned n;
        if (!w || !w->move_count || w->move_count > 3 || w->reserved) return 0;
        for (n = 0; n < 3; ++n) {
            const EquipmentMove *m = &w->moves[n];
            if (n < w->move_count) {
                if (!m->windup || !m->active || !m->recovery || !m->damage_q4 ||
                    !m->reach_px || !m->half_width_px) return 0;
            } else if (!zero_bytes((const EquipmentU8 *)m, sizeof(*m))) return 0;
        }
    }
    return 1;
}
int equipment_record_validate(const EquipmentRecord *r) {
    const EquipmentDefinition *d;
    if (!r) return 0;
    if (!r->item_id) return !(r->rank|r->flags|r->quantity|r->reserved[0]|r->reserved[1]|r->reserved[2]);
    d = equipment_definition(r->item_id);
    return d && r->rank == 0 && r->flags == d->flags && r->quantity == 1 &&
           zero_bytes(r->reserved, sizeof(r->reserved));
}
int equipment_refs_validate(const EquipmentState *s) {
    unsigned i;
    if (!s || s->bag[0].item_id != EQUIPMENT_STARTER_ID ||
        !equipment_record_validate(&s->bag[0])) return 0;
    for (i = 0; i < EQUIPMENT_SLOT_COUNT; ++i) {
        unsigned r = s->equipped[i];
        const EquipmentDefinition *d;
        if (r == EQUIPMENT_EMPTY_REF) {
            if (i == EQUIPMENT_WEAPON) return 0;
            continue;
        }
        if (r >= EQUIPMENT_BAG_CAPACITY || !equipment_record_validate(&s->bag[r])) return 0;
        d = equipment_definition(s->bag[r].item_id);
        if (!d || d->slot != i) return 0;
    }
    return 1;
}
int equipment_reserved_validate(const EquipmentState *s) {
    unsigned i;
    if (!s || !zero_bytes(s->settings_reserved, sizeof(s->settings_reserved)) ||
        !zero_bytes(s->wallet_key_reserved, sizeof(s->wallet_key_reserved)) ||
        !zero_bytes(s->reserved, sizeof(s->reserved)) || bit_get(s->seen, 0)) return 0;
    /* Definitions occupy bits by exact ID, including sentinel bit zero. */
    for (i = 0; i < sizeof(s->seen); ++i) {
        unsigned bits=s->seen[i], bit=0;
        /* Empty history bytes dominate a real bag. Skip them as bytes, but
         * still validate every set identity, including malformed high bits. */
        while(bits){if((bits&1u)&&!equipment_definition(i*8u+bit))return 0;bits>>=1;bit++;}
    }
    for (i = 0; i < EQUIPMENT_REWARD_CAPACITY; ++i) {
        if (bit_get(s->reward_claims, i) &&
            (i >= EQUIPMENT_AUTHORED_COUNT || !bit_get(s->seen, equipment_authored_ids[i]))) return 0;
    }
    return 1;
}
int equipment_validate(const EquipmentState *s) {
    unsigned i;EquipmentU8 owned[64];
    if (!equipment_refs_validate(s) || !equipment_reserved_validate(s)) return 0;
    clear_bytes(owned,sizeof(owned));
    for (i = 0; i < EQUIPMENT_BAG_CAPACITY; ++i) {
        const EquipmentRecord *r = &s->bag[i];
        if (!equipment_record_validate(r)) return 0;
        if (!r->item_id) continue;
        if (!bit_get(s->seen, r->item_id)) return 0;
        if(bit_get(owned,r->item_id))return 0;
        bit_set(owned,r->item_id);
    }
    return 1;
}
void equipment_init(EquipmentState *s) {
    unsigned i;
    if (!s) return;
    clear_bytes(s, sizeof(*s));
    s->bag[0].item_id = EQUIPMENT_STARTER_ID;
    s->bag[0].flags = EQUIPMENT_PROTECTED;
    s->bag[0].quantity = 1;
    bit_set(s->seen, EQUIPMENT_STARTER_ID);
    bit_set(s->reward_claims, 0);
    for (i = 1; i < EQUIPMENT_SLOT_COUNT; ++i) s->equipped[i] = EQUIPMENT_EMPTY_REF;
}
unsigned equipment_count(const EquipmentState *s) {
    unsigned i, count = 0;
    if (!s) return 0;
    for (i = 0; i < EQUIPMENT_BAG_CAPACITY; ++i) if (s->bag[i].item_id) ++count;
    return count;
}
unsigned equipment_find(const EquipmentState *s, unsigned id) {
    unsigned i;
    if (!s || !equipment_definition(id)) return EQUIPMENT_EMPTY_REF;
    for (i = 0; i < EQUIPMENT_BAG_CAPACITY; ++i)
        if (s->bag[i].item_id == id && equipment_record_validate(&s->bag[i])) return i;
    return EQUIPMENT_EMPTY_REF;
}
int equipment_seen(const EquipmentState *s, unsigned id) {
    return s && equipment_definition(id) && bit_get(s->seen, id);
}
unsigned equipment_reward_item(unsigned reward) {
    return reward < EQUIPMENT_AUTHORED_COUNT ? equipment_authored_ids[reward] : 0;
}
unsigned equipment_reward_source(unsigned id) {
    unsigned i;
    for (i = 0; i < EQUIPMENT_AUTHORED_COUNT; ++i)
        if (equipment_authored_ids[i] == id) return i;
    return EQUIPMENT_EMPTY_REF;
}
int equipment_reward_claimed(const EquipmentState *s, unsigned reward) {
    return s && equipment_reward_item(reward) && bit_get(s->reward_claims, reward);
}
unsigned equipment_claim(EquipmentState *s, unsigned id, unsigned reward, unsigned *out_ref) {
    const EquipmentDefinition *d = equipment_definition(id);
    unsigned i;
    if (!d || equipment_reward_item(reward) != id || !equipment_validate(s)) return EQUIPMENT_INVALID;
    if (equipment_reward_claimed(s, reward)) return EQUIPMENT_ALREADY_CLAIMED;
    if (equipment_seen(s, id)) {
        bit_set(s->reward_claims, reward);
        if (out_ref) *out_ref = equipment_find(s, id);
        return EQUIPMENT_DUPLICATE;
    }
    for (i = 1; i < EQUIPMENT_BAG_CAPACITY; ++i) if (!s->bag[i].item_id) break;
    if (i == EQUIPMENT_BAG_CAPACITY) return EQUIPMENT_FULL;
    s->bag[i].item_id = (EquipmentU16)id;
    s->bag[i].flags = d->flags;
    s->bag[i].quantity = 1;
    bit_set(s->seen, id);
    bit_set(s->reward_claims, reward);
    if (out_ref) *out_ref = i;
    return EQUIPMENT_OK;
}
unsigned equipment_claim_many(EquipmentState *s, const EquipmentU8 *sources, unsigned count) {
    EquipmentState staged;
    unsigned i, j, result = EQUIPMENT_ALREADY_CLAIMED;
    if (!sources || !count || count > EQUIPMENT_CLAIM_BATCH_MAX || !equipment_validate(s))
        return EQUIPMENT_INVALID;
    /* Preflight the complete source list before attempting even a staged grant. */
    for (i = 0; i < count; ++i) {
        if (!equipment_reward_item(sources[i])) return EQUIPMENT_INVALID;
        for (j = 0; j < i; ++j) if (sources[i] == sources[j]) return EQUIPMENT_INVALID;
    }
    copy_bytes(&staged, s, sizeof(staged));
    for (i = 0; i < count; ++i) {
        unsigned status = equipment_claim(&staged, equipment_reward_item(sources[i]), sources[i], 0);
        if (status == EQUIPMENT_OK) result = EQUIPMENT_OK;
        else if (status == EQUIPMENT_DUPLICATE) {
            if (result != EQUIPMENT_OK) result = EQUIPMENT_DUPLICATE;
        } else if (status != EQUIPMENT_ALREADY_CLAIMED) return status;
    }
    copy_bytes(s, &staged, sizeof(staged));
    return result;
}
static void derive_refs(const EquipmentState *s, const EquipmentU8 *refs,
                        unsigned base_hp, EquipmentStats *out) {
    /* Signed 32-bit on host and ARM. Never accumulate back into base state. */
    int hp = (int)base_hp, speed = EQUIPMENT_BASE_SPEED_Q8;
    int attack = 0, defense = 0, roll = 0, power = 0, reach = 0, stagger = 0;
    unsigned i;
    clear_bytes(out, sizeof(*out));
    for (i = 0; i < EQUIPMENT_SLOT_COUNT; ++i) {
        const EquipmentDefinition *d;
        const EquipmentBonuses *b;
        if (refs[i] == EQUIPMENT_EMPTY_REF) continue;
        d = equipment_definition(s->bag[refs[i]].item_id);
        b = &d->stats;
        hp += b->hp_q4; speed += b->speed_q8_delta;
        attack += b->attack_q4; defense += b->defense_q4;
        roll += b->roll_reduction; power += b->power_reduction; stagger += b->stagger;
        /* Current-balance overlay: after dodge removal, Porchlight Ring (89)
         * trades more speed than Listening Ring for one more recovery point.
         * Keep the frozen catalog and saved item identity intact;
         * runtime still caps combined equipment recovery at eight. */
        if (d->id == 89) ++power;
        if (i == EQUIPMENT_WEAPON) {
            reach = b->reach_px;
            out->weapon_class = d->weapon_class;
            out->phase = d->phase;
        }
    }
    out->max_hp_q4 = (EquipmentU16)clamp(hp, EQUIPMENT_MIN_HP_Q4, EQUIPMENT_MAX_HP_Q4);
    out->speed_q8 = (EquipmentU16)clamp(speed, EQUIPMENT_MIN_SPEED_Q8, EQUIPMENT_MAX_SPEED_Q8);
    out->diagonal_q8 = (EquipmentU16)((out->speed_q8 * 181u + 128u) >> 8);
    out->attack_q4 = (EquipmentU8)clamp(attack, 0, EQUIPMENT_MAX_ATTACK_Q4);
    out->defense_q4 = (EquipmentU8)clamp(defense, 0, EQUIPMENT_MAX_DEFENSE_Q4);
    out->roll_cooldown = (EquipmentU8)(EQUIPMENT_BASE_ROLL_COOLDOWN - clamp(roll, 0, 6));
    out->power_cooldown = (EquipmentU8)(EQUIPMENT_BASE_POWER_COOLDOWN - clamp(power, 0, 8));
    out->reach_px = (EquipmentU8)clamp(reach, 0, EQUIPMENT_MAX_REACH_PX);
    out->stagger = (EquipmentU8)clamp(stagger, 0, 3);
}
int equipment_derive(const EquipmentState *s, unsigned base_hp, EquipmentStats *out) {
    if (!out || base_hp > 65535u || !equipment_validate(s)) return 0;
    derive_refs(s, s->equipped, base_hp, out);
    return 1;
}
unsigned equipment_preview(const EquipmentState *s, unsigned slot, unsigned ref,
                           unsigned base_hp, unsigned current_hp, unsigned busy,
                           EquipmentComparison *out) {
    EquipmentU8 refs[EQUIPMENT_SLOT_COUNT];
    EquipmentComparison c;
    const EquipmentDefinition *d;
    unsigned i;
    if (!out || slot >= EQUIPMENT_SLOT_COUNT || base_hp > 65535u || current_hp > 65535u ||
        (busy & ~EQUIPMENT_BUSY_MASK) || !equipment_validate(s)) return EQUIPMENT_INVALID;
    if (busy) return EQUIPMENT_BUSY;
    if (ref == EQUIPMENT_EMPTY_REF && slot == EQUIPMENT_WEAPON) ref = 0;
    if (ref != EQUIPMENT_EMPTY_REF) {
        if (ref >= EQUIPMENT_BAG_CAPACITY) return EQUIPMENT_INVALID;
        d = equipment_definition(s->bag[ref].item_id);
        if (!d) return EQUIPMENT_INVALID;
        if (d->slot != slot) return EQUIPMENT_INCOMPATIBLE;
    }
    for (i = 0; i < EQUIPMENT_SLOT_COUNT; ++i) refs[i] = s->equipped[i];
    refs[slot] = (EquipmentU8)ref;
    clear_bytes(&c, sizeof(c));
    derive_refs(s, s->equipped, base_hp, &c.before);
    derive_refs(s, refs, base_hp, &c.after);
    c.hp_before_q4 = (EquipmentU16)current_hp;
    c.hp_after_q4 = (EquipmentU16)(current_hp < c.after.max_hp_q4 ? current_hp : c.after.max_hp_q4);
    c.slot = (EquipmentU8)slot; c.old_ref = s->equipped[slot]; c.new_ref = (EquipmentU8)ref;
    copy_bytes(out, &c, sizeof(c));
    return EQUIPMENT_OK;
}
unsigned equipment_equip(EquipmentState *s, unsigned slot, unsigned ref,
                         unsigned base_hp, EquipmentU16 *hp, unsigned busy,
                         EquipmentComparison *out) {
    EquipmentComparison c;
    unsigned status;
    if (!hp) return EQUIPMENT_INVALID;
    status = equipment_preview(s, slot, ref, base_hp, *hp, busy, &c);
    if (status != EQUIPMENT_OK) return status;
    s->equipped[slot] = c.new_ref;
    *hp = c.hp_after_q4;
    if (out) copy_bytes(out, &c, sizeof(c));
    return EQUIPMENT_OK;
}
unsigned equipment_unequip(EquipmentState *s, unsigned slot, unsigned base_hp,
                           EquipmentU16 *hp, unsigned busy, EquipmentComparison *out) {
    return equipment_equip(s, slot, EQUIPMENT_EMPTY_REF, base_hp, hp, busy, out);
}
unsigned equipment_discard(EquipmentState *s, unsigned ref, unsigned base_hp,
                           EquipmentU16 *hp, unsigned busy, int confirmed) {
    EquipmentU8 refs[EQUIPMENT_SLOT_COUNT];
    EquipmentStats stats;
    unsigned i;
    if (!hp || base_hp > 65535u || ref >= EQUIPMENT_BAG_CAPACITY ||
        (busy & ~EQUIPMENT_BUSY_MASK) || !equipment_validate(s) || !s->bag[ref].item_id)
        return EQUIPMENT_INVALID;
    if (busy) return EQUIPMENT_BUSY;
    if (s->bag[ref].flags & EQUIPMENT_PROTECTED) return EQUIPMENT_CANNOT_DISCARD;
    if (!confirmed) return EQUIPMENT_NEEDS_CONFIRMATION;
    for (i = 0; i < EQUIPMENT_SLOT_COUNT; ++i) {
        refs[i] = s->equipped[i];
        if (refs[i] == ref) refs[i] = (EquipmentU8)(i == EQUIPMENT_WEAPON ? 0 : EQUIPMENT_EMPTY_REF);
    }
    derive_refs(s, refs, base_hp, &stats);
    for (i = 0; i < EQUIPMENT_SLOT_COUNT; ++i) s->equipped[i] = refs[i];
    clear_bytes(&s->bag[ref], sizeof(s->bag[ref]));
    if (*hp > stats.max_hp_q4) *hp = stats.max_hp_q4;
    return EQUIPMENT_OK;
}
