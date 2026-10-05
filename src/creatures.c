#include "creatures.h"

/* Natural layout is deliberately checked, never used as a save wire format. */
typedef char CreatureInstanceMustBe24Bytes[(sizeof(CreatureInstance) == 24) ? 1 : -1];
typedef char CreatureFormMustBe32Bytes[(sizeof(CreatureForm) == 32) ? 1 : -1];
typedef char CreatureU32MustBe4Bytes[(sizeof(CreatureU32) == 4) ? 1 : -1];
#define U32_MAX_VALUE 0xffffffffu

static void clear_bytes(void *p, unsigned n) {
    CreatureU8 *b = (CreatureU8 *)p;
    while (n--) *b++ = 0;
}
static int bit_get(const CreatureU8 *bits, unsigned n) {
    return (bits[n >> 3] >> (n & 7)) & 1;
}
static void bit_set(CreatureU8 *bits, unsigned n) {
    bits[n >> 3] |= (CreatureU8)(1u << (n & 7));
}
/* Reviewed identity policy is separate from generated authored data. It keeps
 * malformed historical rows invalid and does not assume alternating pairs. */
typedef struct CreatureFormPolicy {
    CreatureU8 id, family, tier, signature;
    CreatureU8 learn_offset, learn_count, edge_offset, edge_count;
} CreatureFormPolicy;
typedef struct CreatureFamilyPolicy {
    CreatureU8 phase, polarity, trial, reserved;
    CreatureU32 base_caps, added_caps;
} CreatureFamilyPolicy;
static const CreatureFormPolicy form_policy[CREATURE_ENABLED_COUNT] = {
    {1, 1, 1, 1, 0, 1, 0, 1}, {2, 1, 2, 5, 1, 2, 0, 0},
    {4, 2, 1, 2, 3, 1, 1, 1}, {5, 2, 2, 6, 4, 2, 0, 0},
    {7, 3, 1, 3, 6, 1, 2, 1}, {8, 3, 2, 7, 7, 2, 0, 0},
    {10, 4, 1, 4, 9, 1, 3, 1}, {11, 4, 2, 8, 10, 2, 0, 0},
    {13, 5, 1, 9, 12, 1, 4, 1}, {14, 5, 2, 10, 13, 2, 0, 0},
    {16, 6, 1, 11, 15, 1, 0, 0}
};
static const CreatureFamilyPolicy family_policy[] = {
    {CREATURE_FIRE, CREATURE_YANG, CREATURE_TRIAL_HEARTH, 0, FIELD_HOMURA, 0},
    {CREATURE_WOOD, CREATURE_YIN, CREATURE_TRIAL_CANOPY, 0, FIELD_MIDORI, 0},
    {CREATURE_WOOD, CREATURE_YANG, CREATURE_TRIAL_WIND_LOOM, 0, FIELD_FUURI, 0},
    {CREATURE_EARTH, CREATURE_YIN, CREATURE_TRIAL_AMBER_ARCH, 0, FIELD_KOHAKU, 0},
    {CREATURE_WATER, CREATURE_YIN, CREATURE_TRIAL_PAIRED_POOLS, 0, FIELD_DEWSPINDLE, FIELD_LINK_POOLS},
    {CREATURE_METAL, CREATURE_YANG, 0, 0, FIELD_CHIMECLASP, 0}
};
static unsigned family_trial(const CreatureForm *f) {
    if (!f || f->family < 1 || f->family > sizeof(family_policy) / sizeof(family_policy[0])) return 0;
    return family_policy[f->family - 1].trial;
}
static const CreatureEvolution *incoming_evolution(unsigned id) {
    unsigned i;
    for (i = 0; i < CREATURE_EVOLUTION_COUNT; ++i)
        if (creature_evolutions[i].to == id) return &creature_evolutions[i];
    return 0;
}

int creatures_form_id_valid(unsigned id) { return id >= 1 && id <= 128; }
const CreatureForm *creatures_form(unsigned id) {
    unsigned i;
    for (i = 0; i < CREATURE_ENABLED_COUNT; ++i)
        if (creature_forms[i].id == id) return &creature_forms[i];
    return 0;
}
const CreatureAbility *creatures_ability(unsigned id) {
    if (id < 1 || id > CREATURE_ABILITY_COUNT || creature_abilities[id - 1].id != id) return 0;
    return &creature_abilities[id - 1];
}
unsigned creatures_legacy_spirit(unsigned id) {
    unsigned i;
    for (i = 0; i < CREATURE_LEGACY_COUNT; ++i)
        if (id == creature_legacy_forms[i] || id == creature_legacy_forms[i] + 1u)
            return i;
    return CREATURE_EMPTY_SLOT;
}
CreatureU32 creatures_capabilities(unsigned id) {
    const CreatureForm *f = creatures_form(id);
    return f ? f->field_caps : 0;
}
int creatures_has_capability(unsigned id, CreatureU32 needed) {
    const CreatureForm *f = creatures_form(id);
    return f && (f->field_caps & needed) == needed;
}
unsigned creatures_phase_multiplier_q8(unsigned a, unsigned d) {
    /* Order: Wood -> Earth -> Water -> Fire -> Metal -> Wood. */
    static const CreatureU8 controls[5] = {2, 3, 4, 0, 1};
    if (a >= 5 || d >= 5) return 0;
    if (controls[a] == d) return 320;
    if (controls[d] == a) return 224;
    return 256;
}
unsigned creatures_generated_phase(unsigned p) {
    if (p >= 5) return CREATURE_EMPTY_SLOT;
    return p == 4 ? 0 : p + 1;
}
CreatureU32 creatures_xp_threshold(unsigned level) {
    CreatureU32 n;
    if (level < 1 || level > 50) return U32_MAX_VALUE;
    n = level - 1;
    return 4u * n * n * n;
}
unsigned creatures_level_for_xp(CreatureU32 xp) {
    unsigned lo = 1, hi = 50;
    while (lo < hi) {
        unsigned mid = (lo + hi + 1) >> 1;
        if (creatures_xp_threshold(mid) <= xp) lo = mid;
        else hi = mid - 1;
    }
    return lo;
}
int creatures_command_learned(unsigned id, unsigned level, unsigned ability) {
    const CreatureForm *f = creatures_form(id);
    unsigned j;
    if (!f || level < 1 || level > 50 || !creatures_ability(ability) ||
        f->learnset_offset + f->learnset_count > CREATURE_LEARNSET_COUNT) return 0;
    for (j = 0; j < f->learnset_count; ++j) {
        const CreatureLearn *l = &creature_learnsets[f->learnset_offset + j];
        if (l->ability_id == ability && l->level <= level) return 1;
    }
    return 0;
}
const CreatureEvolution *creatures_evolution(unsigned id) {
    unsigned i;
    for (i = 0; i < CREATURE_EVOLUTION_COUNT; ++i)
        if (creature_evolutions[i].from == id) return &creature_evolutions[i];
    return 0;
}
int creatures_catalog_validate(void) {
    static const CreatureEvolution expected_edges[CREATURE_EVOLUTION_COUNT] = {
        {1, 2, 12, 40, CREATURE_TRIAL_HEARTH, CREATURE_GROVE_CLEAR},
        {4, 5, 12, 40, CREATURE_TRIAL_CANOPY, CREATURE_GROVE_CLEAR},
        {7, 8, 16, 55, CREATURE_TRIAL_WIND_LOOM, CREATURE_SKY_CLEAR},
        {10, 11, 20, 60, CREATURE_TRIAL_AMBER_ARCH, CREATURE_CORE_CLEAR},
        {13, 14, 15, 45, CREATURE_TRIAL_PAIRED_POOLS, CREATURE_REED_RESTORED}
    };
    static const CreatureU16 cooldowns[CREATURE_ABILITY_COUNT] = {75,75,75,75,105,120,105,120,90,120,90};
    static const FormId legacy_ids[CREATURE_LEGACY_COUNT] = {1,4,7,10};
    unsigned i, j, k;
    for (i = 0; i < CREATURE_LEGACY_COUNT; ++i)
        if (creature_legacy_forms[i] != legacy_ids[i]) return 0;
    for (i = 0; i < CREATURE_ENABLED_COUNT; ++i) {
        const CreatureForm *f = &creature_forms[i];
        const CreatureFormPolicy *p = &form_policy[i];
        const CreatureFamilyPolicy *family = &family_policy[p->family - 1];
        CreatureU32 caps = family->base_caps | (p->tier > 1 ? family->added_caps : 0);
        unsigned total = 0;
        if (f->id != p->id || f->family != p->family ||
            f->phase != family->phase || f->polarity != family->polarity ||
            f->tier != p->tier || f->rarity != 0 || f->field_caps != caps ||
            f->flags != 1 || f->name_id != f->id || f->portrait_id != f->id ||
            f->sprite_offset || f->signature_ability != p->signature ||
            f->learnset_count != p->learn_count || f->learnset_offset != p->learn_offset ||
            f->learnset_offset + f->learnset_count > CREATURE_LEARNSET_COUNT ||
            f->evolution_count != p->edge_count || f->evolution_offset != p->edge_offset ||
            f->evolution_offset + f->evolution_count > CREATURE_EVOLUTION_COUNT ||
            (f->evolution_count && creature_evolutions[f->evolution_offset].from != f->id)) return 0;
        for (j = 0; j < CREATURE_PHASE_COUNT; ++j) {
            if (!f->stats[j] || f->stats[j] > 100) return 0;
            total += f->stats[j];
        }
        if (total != (f->tier == 1 ? 180u : 240u)) return 0;
        if (creature_learnsets[f->learnset_offset].level != 1 ||
            !creatures_command_learned(f->id, CREATURE_MAX_LEVEL, f->signature_ability)) return 0;
        for (j = 0; j < f->learnset_count; ++j) {
            const CreatureLearn *l = &creature_learnsets[f->learnset_offset + j];
            const CreatureAbility *a = creatures_ability(l->ability_id);
            if (!a || a->phase != f->phase || (a->field_caps & caps) != a->field_caps ||
                (a->id == f->signature_ability && a->field_caps != caps) ||
                l->level < 1 || l->level > CREATURE_MAX_LEVEL ||
                (j && l->level < creature_learnsets[f->learnset_offset + j - 1].level)) return 0;
            for (k = 0; k < j; ++k)
                if (creature_learnsets[f->learnset_offset + k].ability_id == l->ability_id) return 0;
        }
    }
    for (i = 0; i < CREATURE_ABILITY_COUNT; ++i) {
        const CreatureAbility *a = &creature_abilities[i];
        if (a->id != i + 1 || a->phase >= CREATURE_PHASE_COUNT ||
            a->cooldown_updates != cooldowns[i]) return 0;
    }
    for (i = 0; i < CREATURE_EVOLUTION_COUNT; ++i) {
        const CreatureEvolution *e = &creature_evolutions[i], *expected = &expected_edges[i];
        const CreatureForm *a = creatures_form(e->from), *b = creatures_form(e->to);
        unsigned id = e->to;
        if (e->from != expected->from || e->to != expected->to ||
            e->min_level != expected->min_level || e->min_bond != expected->min_bond ||
            e->trial_flag != expected->trial_flag || e->chapter_flags != expected->chapter_flags ||
            !a || !b || e->from == e->to || a->family != b->family ||
            b->tier <= a->tier || e->min_level < 1 || e->min_level > CREATURE_MAX_LEVEL ||
            e->min_bond > CREATURE_MAX_BOND || !e->chapter_flags ||
            (e->chapter_flags & ~CREATURE_EVOLUTION_CONTEXT_MASK) ||
            e->trial_flag != family_trial(a) ||
            (a->field_caps & b->field_caps) != a->field_caps ||
            !creatures_command_learned(b->id, e->min_level, b->signature_ability)) return 0;
        for (j = 0; j < a->learnset_count; ++j) {
            const CreatureLearn *l = &creature_learnsets[a->learnset_offset + j];
            if (!creatures_command_learned(b->id, l->level, l->ability_id)) return 0;
        }
        for (j = 0; j < CREATURE_ENABLED_COUNT; ++j) {
            const CreatureEvolution *next = creatures_evolution(id);
            if (id == e->from) return 0;
            if (!next) break;
            id = next->to;
        }
        if (j == CREATURE_ENABLED_COUNT) return 0;
        for (j = 0; j < i; ++j)
            if (creature_evolutions[j].from == e->from || creature_evolutions[j].to == e->to) return 0;
    }
    return 1;
}
int creatures_instance_validate(const CreatureInstance *c) {
    const CreatureForm *f;
    unsigned j, legacy;
    if (!c) return 0;
    if (!c->form_id) {
        const CreatureU8 *bytes = (const CreatureU8 *)c;
        for (j = 0; j < sizeof(*c); ++j) if (bytes[j]) return 0;
        return 1;
    }
    f = creatures_form(c->form_id);
    legacy = creatures_legacy_spirit(c->form_id);
    if (!f || !(c->flags & CREATURE_OCCUPIED) || (c->flags & ~CREATURE_FLAGS_MASK) ||
        c->level < 1 || c->level > 50 || c->bond > 100 || c->xp > CREATURE_XP_CAP ||
        c->level != creatures_level_for_xp(c->xp) || !c->instance_id ||
        c->instance_id == U32_MAX_VALUE || c->nickname_id > CREATURE_NICKNAME_MAX ||
        (c->trial_flags & ~family_trial(f)) ||
        ((c->flags & CREATURE_STORY_LOCKED) && legacy >= CREATURE_LEGACY_COUNT) || c->polarity != f->polarity ||
        c->selected_command > 1 || !c->equipped[c->selected_command] ||
        (c->equipped[0] && c->equipped[0] == c->equipped[1])) return 0;
    for (j = 0; j < 2; ++j)
        if (c->equipped[j] && !creatures_command_learned(c->form_id, c->level, c->equipped[j])) return 0;
    if (f->tier > 1) {
        const CreatureEvolution *e = incoming_evolution(c->form_id);
        if (!e || c->level < e->min_level) return 0;
    }
    return 1;
}
int creatures_party_validate(const CreatureRoster *r) {
    unsigned i, j, members = 0, legendary = 0;
    if (!r) return 0;
    for (i = 0; i < 4; ++i) {
        unsigned slot = r->party[i];
        const CreatureInstance *c;
        if (slot == CREATURE_EMPTY_SLOT) continue;
        if (slot >= 160) return 0;
        c = &r->instances[slot];
        if (!c->form_id || !creatures_instance_validate(c)) return 0;
        for (j = 0; j < i; ++j) if (slot == r->party[j]) return 0;
        ++members;
        legendary += creatures_form(c->form_id)->rarity != 0;
    }
    if (legendary > 1) return 0;
    if (!members) return r->selected_party == CREATURE_EMPTY_SLOT;
    return r->selected_party < 4 && r->party[r->selected_party] != CREATURE_EMPTY_SLOT;
}
int creatures_roster_validate(const CreatureRoster *r) {
    unsigned i, j, stories = 0;
    if (!r || !r->next_instance_id || !creatures_party_validate(r)) return 0;
    for (i = 0; i < 128; ++i) {
        if ((bit_get(r->seen, i) || bit_get(r->obtained, i)) && !creatures_form(i + 1)) return 0;
        if (bit_get(r->obtained, i) && !bit_get(r->seen, i)) return 0;
    }
    for (i = 0; i < 160; ++i) {
        const CreatureInstance *c = &r->instances[i];
        unsigned legacy;
        if (!creatures_instance_validate(c) || r->expedition_bond[i] > 10) return 0;
        if (!c->form_id) { if (r->expedition_bond[i]) return 0; continue; }
        if (c->instance_id >= r->next_instance_id || !bit_get(r->obtained, c->form_id - 1)) return 0;
        for (j = 0; j < i; ++j)
            if (c->instance_id == r->instances[j].instance_id) return 0;
        if (c->flags & CREATURE_STORY_LOCKED) {
            legacy = creatures_legacy_spirit(c->form_id);
            if (legacy >= 4 || (stories & (1u << legacy)) || !bit_get(r->rewards, legacy)) return 0;
            stories |= 1u << legacy;
        }
    }
    return stories == (r->rewards[0] & 15u);
}
void creatures_roster_init(CreatureRoster *r) {
    unsigned i;
    if (!r) return;
    clear_bytes(r, sizeof(*r));
    for (i = 0; i < 4; ++i) r->party[i] = CREATURE_EMPTY_SLOT;
    r->selected_party = CREATURE_EMPTY_SLOT;
    r->next_instance_id = 1;
}
unsigned creatures_roster_count(const CreatureRoster *r) {
    unsigned i, n = 0;
    if (!r) return 0;
    for (i = 0; i < 160; ++i) n += r->instances[i].form_id != 0;
    return n;
}
CreatureU32 creatures_party_capabilities(const CreatureRoster *r) {
    CreatureU32 caps = 0;
    unsigned i;
    if (!creatures_party_validate(r)) return 0;
    for (i = 0; i < 4; ++i)
        if (r->party[i] != CREATURE_EMPTY_SLOT)
            caps |= creatures_capabilities(r->instances[r->party[i]].form_id);
    return caps;
}
int creatures_party_set(CreatureRoster *r, const CreatureU8 party[4], CreatureU32 required) {
    CreatureU8 old[4];
    unsigned i, selected;
    if (!r || !party || !creatures_party_validate(r)) return 0;
    selected = r->selected_party;
    for (i = 0; i < 4; ++i) old[i] = r->party[i];
    for (i = 0; i < 4; ++i) r->party[i] = party[i];
    /* Keep active creature identity across party sorting when possible. */
    r->selected_party = CREATURE_EMPTY_SLOT;
    if (selected < 4)
        for (i = 0; i < 4; ++i)
            if (r->party[i] == old[selected]) r->selected_party = (CreatureU8)i;
    if (r->selected_party == CREATURE_EMPTY_SLOT)
        for (i = 0; i < 4; ++i)
            if (r->party[i] != CREATURE_EMPTY_SLOT) { r->selected_party = (CreatureU8)i; break; }
    if (creatures_party_validate(r) && (creatures_party_capabilities(r) & required) == required) return 1;
    for (i = 0; i < 4; ++i) r->party[i] = old[i];
    r->selected_party = (CreatureU8)selected;
    return 0;
}
unsigned creatures_grant(CreatureRoster *r, unsigned id, unsigned level,
                         unsigned bond, unsigned flags, unsigned reward) {
    const CreatureForm *f = creatures_form(id);
    CreatureInstance c;
    unsigned i, j, legacy;
    if (!r || !f || level < 1 || level > 50 || bond > 100 ||
        (flags & ~(CREATURE_STORY_LOCKED | CREATURE_FAVORITE)) || reward > 128 ||
        !creatures_roster_validate(r) || r->next_instance_id == U32_MAX_VALUE ||
        (reward && bit_get(r->rewards, reward - 1))) return CREATURE_EMPTY_SLOT;
    legacy = creatures_legacy_spirit(id);
    if (flags & CREATURE_STORY_LOCKED) {
        if (legacy >= 4 || reward != legacy + 1) return CREATURE_EMPTY_SLOT;
    } else if (reward && reward <= 4) return CREATURE_EMPTY_SLOT;
    for (i = 0; i < 160; ++i) if (!r->instances[i].form_id) break;
    if (i == 160) return CREATURE_EMPTY_SLOT;
    clear_bytes(&c, sizeof(c));
    c.form_id = (CreatureU8)id; c.flags = (CreatureU8)(flags | CREATURE_OCCUPIED);
    c.level = (CreatureU8)level; c.bond = (CreatureU8)bond;
    c.xp = creatures_xp_threshold(level); c.instance_id = r->next_instance_id;
    c.polarity = f->polarity;
    c.equipped[0] = creature_learnsets[f->learnset_offset].ability_id;
    c.cosmetic_seed = c.instance_id * 2654435761u;
    if (!creatures_instance_validate(&c)) return CREATURE_EMPTY_SLOT;
    r->instances[i] = c; ++r->next_instance_id;
    bit_set(r->seen, id - 1); bit_set(r->obtained, id - 1);
    if (reward) bit_set(r->rewards, reward - 1);
    r->expedition_bond[i] = 0;
    for (j = 0; j < 4; ++j) {
        if (r->party[j] == CREATURE_EMPTY_SLOT) {
            r->party[j] = (CreatureU8)i;
            if (r->selected_party == CREATURE_EMPTY_SLOT) r->selected_party = (CreatureU8)j;
            break;
        }
    }
    return i;
}
static unsigned party_median_level(const CreatureRoster *r) {
    unsigned levels[4], n = 0, i, j;
    for (i = 0; i < 4; ++i) if (r->party[i] < 160) {
        unsigned value = r->instances[r->party[i]].level;
        j = n;
        while (j && levels[j - 1] > value) { levels[j] = levels[j - 1]; --j; }
        levels[j] = value; ++n;
    }
    if (!n) return 1;
    return n & 1 ? levels[n >> 1] : (levels[(n >> 1) - 1] + levels[n >> 1]) / 2;
}
unsigned creatures_grant_story(CreatureRoster *r, unsigned legacy, unsigned chapters) {
    static const CreatureU8 floor[4] = {1, 1, 8, 14};
    unsigned i, level;
    if (!r || legacy >= 4 || (legacy == 2 && !(chapters & CREATURE_GROVE_CLEAR)) ||
        (legacy == 3 && !(chapters & CREATURE_SKY_CLEAR)) || !creatures_roster_validate(r))
        return CREATURE_EMPTY_SLOT;
    if (bit_get(r->rewards, legacy)) {
        for (i = 0; i < 160; ++i)
            if ((r->instances[i].flags & CREATURE_STORY_LOCKED) &&
                creatures_legacy_spirit(r->instances[i].form_id) == legacy) return i;
        return CREATURE_EMPTY_SLOT;
    }
    level = party_median_level(r);
    if (level < floor[legacy]) level = floor[legacy];
    return creatures_grant(r, creature_legacy_forms[legacy], level, 20, CREATURE_STORY_LOCKED, legacy + 1);
}
int creatures_apply_story_floors(CreatureRoster *r, unsigned chapters) {
    unsigned i, changed = 0;
    if (!r || !creatures_roster_validate(r)) return 0;
    for (i = 0; i < 160; ++i) {
        CreatureInstance *c = &r->instances[i];
        unsigned legacy, level = 0, bond = 0;
        if (!(c->flags & CREATURE_STORY_LOCKED)) continue;
        legacy = creatures_legacy_spirit(c->form_id);
        if (chapters & CREATURE_CORE_CLEAR) { level = 20; bond = legacy == 2 ? 55 : 50; }
        else if (chapters & CREATURE_SKY_CLEAR) {
            if (legacy < 3) { level = 16; bond = legacy == 2 ? 45 : 40; }
        } else if ((chapters & CREATURE_GROVE_CLEAR) && legacy < 2) { level = 12; bond = 30; }
        /* A completed one-time trial stays additive to story compensation. */
        if (bond && (c->trial_flags & (1u << legacy))) bond += 10;
        if (c->level < level) { c->level = (CreatureU8)level; c->xp = creatures_xp_threshold(level); changed = 1; }
        if (c->bond < bond) { c->bond = (CreatureU8)bond; changed = 1; }
    }
    return (int)changed;
}
int creatures_migrate_legacy(CreatureRoster *r, unsigned chapters, unsigned selected) {
    static const CreatureU8 floors[4] = {1, 1, 8, 14};
    unsigned i, count = 2;
    if (!r || (chapters & ~15u) ||
        ((chapters & CREATURE_SKY_CLEAR) && !(chapters & CREATURE_GROVE_CLEAR)) ||
        ((chapters & CREATURE_CORE_CLEAR) && !(chapters & CREATURE_SKY_CLEAR)) ||
        ((chapters & 8u) && !(chapters & CREATURE_CORE_CLEAR))) return 0;
    if (chapters & CREATURE_GROVE_CLEAR) count = 3;
    if (chapters & CREATURE_SKY_CLEAR) count = 4;
    if (selected >= count) return 0;
    creatures_roster_init(r);
    for (i = 0; i < count; ++i)
        if (creatures_grant(r, creature_legacy_forms[i], floors[i], 20, CREATURE_STORY_LOCKED, i + 1) == CREATURE_EMPTY_SLOT) return 0;
    r->selected_party = (CreatureU8)selected;
    creatures_apply_story_floors(r, chapters);
    return creatures_roster_validate(r);
}
int creatures_add_xp(CreatureInstance *c, CreatureU32 amount) {
    if (!c || !c->form_id || !creatures_instance_validate(c)) return 0;
    if (amount > CREATURE_XP_CAP - c->xp) c->xp = CREATURE_XP_CAP;
    else c->xp += amount;
    c->level = (CreatureU8)creatures_level_for_xp(c->xp);
    return 1;
}
int creatures_equip(CreatureInstance *c, unsigned slot, unsigned ability) {
    if (!c || !c->form_id || !creatures_instance_validate(c) || slot > 1 ||
        (ability && !creatures_command_learned(c->form_id, c->level, ability)) ||
        (ability && c->equipped[slot ^ 1] == ability) ||
        (!ability && c->selected_command == slot)) return 0;
    c->equipped[slot] = (CreatureU8)ability;
    return 1;
}
int creatures_select_command(CreatureInstance *c, unsigned slot) {
    if (!c || !c->form_id || !creatures_instance_validate(c) || slot > 1 || !c->equipped[slot]) return 0;
    c->selected_command = (CreatureU8)slot;
    return 1;
}
void creatures_begin_expedition(CreatureRoster *r) {
    if (!r) return;
    clear_bytes(r->expedition_bond, sizeof(r->expedition_bond));
    clear_bytes(r->expedition_events, sizeof(r->expedition_events));
}
int creatures_credit_event(CreatureRoster *r, unsigned event, CreatureU32 xp, unsigned kind) {
    unsigned i, members = 0, bond;
    if (!r || !creatures_party_validate(r) || event >= 512 || kind > CREATURE_CREDIT_PERSONAL_QUEST ||
        (kind == CREATURE_CREDIT_FIELD_AID ? event < 384 : event >= 384)) return -1;
    if (bit_get(r->expedition_events, event)) return 0;
    for (i = 0; i < 4; ++i) if (r->party[i] < 160) {
        ++members;
        if (r->expedition_bond[r->party[i]] > 10) return -1;
    }
    if (!members) return 0;
    bond = kind == CREATURE_CREDIT_ENCOUNTER ? 1 : (kind == CREATURE_CREDIT_FIELD_AID ? 3 : 10);
    if (kind == CREATURE_CREDIT_FIELD_AID && bit_get(r->lifetime_field_aid, event - 384)) bond = 0;
    bit_set(r->expedition_events, event);
    if (kind == CREATURE_CREDIT_FIELD_AID) bit_set(r->lifetime_field_aid, event - 384);
    for (i = 0; i < 4; ++i) if (r->party[i] < 160) {
        unsigned slot = r->party[i], gain = bond;
        CreatureInstance *c = &r->instances[slot];
        creatures_add_xp(c, xp);
        if (gain > 10u - r->expedition_bond[slot]) gain = 10u - r->expedition_bond[slot];
        if (gain > 100u - c->bond) gain = 100u - c->bond;
        c->bond += (CreatureU8)gain; r->expedition_bond[slot] += (CreatureU8)gain;
    }
    return 1;
}
int creatures_mark_trial(CreatureInstance *c, unsigned flag) {
    unsigned required;
    if (!c || !c->form_id || !creatures_instance_validate(c)) return 0;
    required = family_trial(creatures_form(c->form_id));
    if (!required || flag != required) return 0;
    c->trial_flags |= (CreatureU16)flag;
    return 1;
}
unsigned creatures_can_evolve(const CreatureInstance *c, unsigned context, int sanctuary) {
    const CreatureEvolution *e;
    if (!c || !c->form_id || !creatures_instance_validate(c) ||
        (context & ~CREATURE_EVOLUTION_CONTEXT_MASK)) return CREATURE_EVOLVE_INVALID;
    e = creatures_evolution(c->form_id);
    if (!e) return CREATURE_EVOLVE_NO_EDGE;
    if (c->level < e->min_level) return CREATURE_EVOLVE_LEVEL;
    if (c->bond < e->min_bond) return CREATURE_EVOLVE_BOND;
    if ((context & e->chapter_flags) != e->chapter_flags) return CREATURE_EVOLVE_STORY;
    if ((c->trial_flags & e->trial_flag) != e->trial_flag) return CREATURE_EVOLVE_TRIAL;
    if (!sanctuary) return CREATURE_EVOLVE_SANCTUARY;
    return CREATURE_EVOLVE_READY;
}
unsigned creatures_evolve(CreatureRoster *r, unsigned slot, unsigned context, int sanctuary, int confirmed) {
    CreatureInstance *c, candidate;
    const CreatureEvolution *e;
    const CreatureForm *target;
    unsigned result;
    if (!r || slot >= 160 || !creatures_roster_validate(r)) return CREATURE_EVOLVE_INVALID;
    c = &r->instances[slot];
    result = creatures_can_evolve(c, context, sanctuary);
    if (result != CREATURE_EVOLVE_READY) return result;
    if (!confirmed) return CREATURE_EVOLVE_DEFERRED;
    e = creatures_evolution(c->form_id); target = creatures_form(e->to);
    if (!target || (creatures_capabilities(c->form_id) & target->field_caps) != creatures_capabilities(c->form_id))
        return CREATURE_EVOLVE_INVALID;
    candidate = *c; candidate.form_id = target->id; candidate.polarity = target->polarity;
    if (!creatures_instance_validate(&candidate)) return CREATURE_EVOLVE_INVALID;
    *c = candidate;
    bit_set(r->seen, c->form_id - 1); bit_set(r->obtained, c->form_id - 1);
    return CREATURE_EVOLVE_READY;
}
unsigned creatures_defer_evolution(const CreatureInstance *c) {
    if (!c || !c->form_id || !creatures_instance_validate(c)) return CREATURE_EVOLVE_INVALID;
    return CREATURE_EVOLVE_DEFERRED;
}
