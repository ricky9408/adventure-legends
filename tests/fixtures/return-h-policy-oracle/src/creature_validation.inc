#define CHECK_KEY_INDEX(map, bound, records, key) do { \
    for (i = 0; i <= (bound); ++i) { \
        j = (map)[i]; \
        if (j > sizeof(records) / sizeof((records)[0]) || \
            (j && (records)[j - 1].key != i)) return 0; \
    } \
    for (i = 0; i < sizeof(records) / sizeof((records)[0]); ++i) \
        if ((records)[i].key > (bound) || (map)[(records)[i].key] != i + 1) return 0; \
} while (0)
int creatures_catalog_validate(void) {
        static const CreatureEvolution expected_edges[CREATURE_EVOLUTION_COUNT] = {
        {1, 2, 12, 40, 1, 1},
        {4, 5, 12, 40, 2, 1},
        {7, 8, 16, 55, 4, 2},
        {10, 11, 20, 60, 8, 4},
        {13, 14, 15, 45, 16, 8},
        {19, 20, 16, 40, 32, 16},
        {22, 23, 17, 40, 64, 16},
        {73, 74, 18, 45, 128, 16},
        {75, 76, 18, 45, 256, 16},
        {77, 78, 20, 50, 512, 16},
        {25, 26, 20, 40, 1, 64},
        {28, 29, 22, 45, 1, 64},
        {79, 80, 20, 40, 1, 64},
        {81, 82, 22, 45, 1, 64},
        {83, 84, 22, 45, 1, 64},
        {85, 86, 20, 40, 1, 64},
        {87, 88, 24, 45, 1, 64},
        {89, 90, 22, 45, 1, 64},
        {91, 92, 24, 45, 1, 64},
        {93, 94, 22, 45, 1, 64},
        {31, 32, 26, 45, 1, 256},
        {32, 33, 32, 60, 3, 512},
        {34, 35, 26, 45, 1, 256},
        {35, 36, 32, 60, 3, 512},
        {37, 38, 26, 45, 1, 256},
        {37, 39, 26, 45, 2, 256},
        {40, 41, 26, 45, 1, 256},
        {40, 42, 26, 45, 2, 256},
        {43, 44, 26, 45, 1, 256},
        {43, 45, 26, 45, 2, 256},
        {46, 47, 26, 45, 1, 256},
        {46, 48, 26, 45, 2, 256},
        {95, 96, 26, 45, 1, 256},
        {97, 98, 26, 45, 1, 256},
        {99, 100, 26, 45, 1, 256},
        {49, 50, 28, 45, 1, 1024},
        {49, 51, 28, 45, 2, 1024},
        {52, 53, 28, 45, 1, 1024},
        {52, 54, 28, 45, 2, 1024},
        {55, 56, 28, 45, 1, 1024},
        {55, 57, 28, 45, 2, 1024},
        {58, 59, 28, 45, 1, 1024},
        {58, 60, 28, 45, 2, 1024},
        {61, 62, 28, 45, 1, 1024},
        {61, 63, 28, 45, 2, 1024},
        {64, 65, 28, 45, 1, 1024},
        {64, 66, 28, 45, 2, 1024},
        {67, 68, 28, 45, 1, 1024},
        {67, 69, 28, 45, 2, 1024},
        {70, 71, 28, 45, 1, 1024},
        {70, 72, 28, 45, 2, 1024},
        {2, 3, 32, 60, 1025, 4096},
        {5, 6, 32, 60, 1026, 4096},
        {8, 9, 32, 60, 1028, 4096},
        {11, 12, 32, 60, 1032, 4096},
        {14, 15, 32, 60, 1040, 4096},
        {16, 17, 28, 45, 1024, 4096},
        {17, 18, 32, 60, 3072, 4096},
        {20, 21, 32, 60, 1056, 4096},
        {23, 24, 32, 60, 1088, 4096},
        {26, 27, 32, 60, 1025, 4096},
        {29, 30, 32, 60, 1025, 4096},
        {101, 102, 28, 45, 1024, 4096},
        {103, 104, 28, 45, 1024, 4096},
    };
    static const FormId legacy_ids[CREATURE_LEGACY_COUNT] = {1,4,7,10};
    unsigned i, j, k, trials = 0;
    if (creature_terminal_policy[0].family || creature_terminal_policy[0].terminal_mask) return 0;
    for (i = 1; i <= CREATURE_FORM_CAPACITY; ++i)
        if (!creatures_terminal_family(i)) return 0;
    CHECK_KEY_INDEX(creature_form_index, CREATURE_FORM_CAPACITY, creature_forms, id);
    CHECK_KEY_INDEX(creature_ability_index, 255, creature_abilities, id);
    CHECK_KEY_INDEX(creature_incoming_evolution_index, CREATURE_FORM_CAPACITY, creature_evolutions, to);
    CHECK_KEY_INDEX(form_policy_index, CREATURE_FORM_CAPACITY, form_policy, id);
    CHECK_KEY_INDEX(family_policy_index, CREATURE_FAMILY_CAPACITY, family_policy, id);
    CHECK_KEY_INDEX(ability_policy_index, 255, ability_policy, id);
    CHECK_KEY_INDEX(revision5_policy_index, CREATURE_FORM_CAPACITY, revision5_policy, id);
    CHECK_KEY_INDEX(revision6_policy_index, CREATURE_FORM_CAPACITY, revision6_policy, id);
    for (k = 0; k < 4; ++k) {
        for (i = 0; i <= CREATURE_FORM_CAPACITY; ++i) {
            j = revision_policy_index[k][i];
            if (j > sizeof(revision_policy) / sizeof(revision_policy[0]) ||
                (j && (revision_policy[j - 1].id != i ||
                       !(revision_policy[j - 1].revision_bits & (1u << k))))) return 0;
        }
        for (i = 0; i < sizeof(revision_policy) / sizeof(revision_policy[0]); ++i)
            if (revision_policy[i].id > CREATURE_FORM_CAPACITY ||
                ((revision_policy[i].revision_bits & (1u << k)) &&
                 revision_policy_index[k][revision_policy[i].id] != i + 1)) return 0;
    }
    for (i = 0; i < sizeof(capability_policy) / sizeof(capability_policy[0]); ++i) {
        const CreatureCapabilityPolicy *p = &capability_policy[i];
        if (!p->id || (p->legacy_mask & (p->legacy_mask - 1u))) return 0;
        for (j = 0; j < i; ++j)
            if (capability_policy[j].id == p->id ||
                (p->legacy_mask && capability_policy[j].legacy_mask == p->legacy_mask)) return 0;
    }
    for (i = 0; i < sizeof(capability_memberships) / sizeof(capability_memberships[0]); ++i) {
        const CreatureCapabilityMembership *m = &capability_memberships[i];
        if (!m->form && !m->capability) continue;
        if (!creatures_form(m->form) || !capability_policy_for_id(m->capability)) return 0;
        for (j = 0; j < i; ++j)
            if (capability_memberships[j].form == m->form &&
                capability_memberships[j].capability == m->capability) return 0;
    }
    for (i = 0; i < sizeof(trial_policy) / sizeof(trial_policy[0]); ++i) {
        const CreatureTrialPolicy *p = &trial_policy[i];
        const CreatureFamilyPolicy *f = family_policy_for_id(p->family);
        if (!f || !p->key || !p->mask || (p->mask & (p->mask - 1u)) ||
            (p->mask & ~f->trial) || (p->prerequisite & ~f->trial) ||
            (p->prerequisite & p->mask) || !p->introduced_revision ||
            p->introduced_revision > CREATURE_CONTENT_REVISION) return 0;
        for (j = 0; j < i; ++j)
            if (trial_policy[j].family == p->family &&
                (trial_policy[j].key == p->key || trial_policy[j].mask == p->mask)) return 0;
        for (j = 0; j < sizeof(trial_policy) / sizeof(trial_policy[0]); ++j)
            if (trial_policy[j].family == p->family &&
                (p->prerequisite & trial_policy[j].mask) &&
                trial_policy[j].introduced_revision > p->introduced_revision) return 0;
    }
    for (i = 0; i < sizeof(family_policy) / sizeof(family_policy[0]); ++i) {
        const CreatureFamilyPolicy *p = &family_policy[i];
        if (!p->id || p->id > CREATURE_FAMILY_CAPACITY ||
            p->phase >= CREATURE_PHASE_COUNT || p->polarity > CREATURE_YANG ||
            (legacy_trial_scalars[p->id] & ~p->trial) ||
            (legacy_family(p->id) && (trials & legacy_trial_scalars[p->id]))) return 0;
        if (legacy_family(p->id)) trials |= legacy_trial_scalars[p->id];
        for (j = 0; j < i; ++j) if (family_policy[j].id == p->id) return 0;
        for (j = 0; j < CREATURE_ENABLED_COUNT; ++j)
            if (creature_forms[j].family == p->id) break;
        if (j == CREATURE_ENABLED_COUNT) return 0;
        {
            unsigned allowed = 0, reachable = 0, pass;
            for (j = 0; j < sizeof(trial_policy) / sizeof(trial_policy[0]); ++j)
                if (trial_policy[j].family == p->id) allowed |= trial_policy[j].mask;
            if (allowed != p->trial) return 0;
            /* At most16 one-hot keys fit in the wire mask. A bounded fixed
             * point rejects cycles and every unsatisfiable dependency chain. */
            for (pass = 0; pass < 16 && reachable != allowed; ++pass)
                for (j = 0; j < sizeof(trial_policy) / sizeof(trial_policy[0]); ++j) {
                    const CreatureTrialPolicy *t = &trial_policy[j];
                    if (t->family == p->id && (reachable & t->prerequisite) == t->prerequisite)
                        reachable |= t->mask;
                }
            if (reachable != allowed) return 0;
        }
    }
    if (trials != CREATURE_TRIAL_MASK) return 0;
    for (i = 0; i < CREATURE_LEGACY_COUNT; ++i)
        if (creature_legacy_forms[i] != legacy_ids[i]) return 0;
    for (i = 0; i < CREATURE_ENABLED_COUNT; ++i) {
        const CreatureForm *f = &creature_forms[i];
        const CreatureFormPolicy *p = form_policy_for_id(f->id);
        const CreatureFamilyPolicy *family = family_policy_for_id(f->family);
        CreatureU32 caps;
        unsigned total = 0;
        if (!p || !family || !creatures_form_id_valid(f->id)) return 0;
        for (j = 0; j < i; ++j) if (creature_forms[j].id == f->id) return 0;
        caps = p->field_caps;
        if (f->id != p->id || f->family != p->family ||
            (p->trial_mask & ~family->trial) ||
            f->phase != family->phase || f->polarity != p->polarity ||
            f->tier != p->tier || f->rarity != 0 || f->field_caps != caps ||
            f->flags != 1 || f->name_id != f->id || f->portrait_id != f->id ||
            f->sprite_offset || f->signature_ability != p->signature ||
            f->learnset_count != p->learn_count || f->learnset_offset != p->learn_offset ||
            f->learnset_offset + f->learnset_count > CREATURE_LEARNSET_COUNT ||
            f->evolution_count != p->edge_count || f->evolution_offset != p->edge_offset ||
            f->evolution_offset + f->evolution_count > CREATURE_EVOLUTION_COUNT ||
            (f->evolution_count && creature_evolutions[f->evolution_offset].from != f->id)) return 0;
        for (j = 0; j < f->evolution_count; ++j)
            if (creature_evolutions[f->evolution_offset + j].from != f->id) return 0;
        if (creatures_evolution_count(f->id) != f->evolution_count) return 0;
        for (j = 0; j < CREATURE_PHASE_COUNT; ++j) {
            if (!f->stats[j] || f->stats[j] > 100) return 0;
            total += f->stats[j];
        }
        if (f->tier < 1 || f->tier > 3 ||
            total != (f->tier == 1 ? 180u : f->tier == 2 ? 240u : 285u)) return 0;
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
        const CreatureAbilityPolicy *p = ability_policy_for_id(a->id);
        if (!a->id || !p || a->phase >= CREATURE_PHASE_COUNT ||
            a->cooldown_updates != p->cooldown) return 0;
        for (j = 0; j < i; ++j) if (creature_abilities[j].id == a->id) return 0;
    }
    for (i = 0; i < CREATURE_EVOLUTION_COUNT; ++i) {
        const CreatureEvolution *e = &creature_evolutions[i], *expected = &expected_edges[i];
        const CreatureForm *a = creatures_form(e->from), *b = creatures_form(e->to);
        if (e->from != expected->from || e->to != expected->to ||
            e->min_level != expected->min_level || e->min_bond != expected->min_bond ||
            e->trial_flag != expected->trial_flag || e->chapter_flags != expected->chapter_flags ||
            !a || !b || e->from == e->to || a->family != b->family ||
            b->tier <= a->tier || e->min_level < 1 || e->min_level > CREATURE_MAX_LEVEL ||
            e->min_bond > CREATURE_MAX_BOND || !e->chapter_flags ||
            (e->chapter_flags & ~CREATURE_EVOLUTION_CONTEXT_MASK) ||
            !e->trial_flag || !trial_subset_valid(family_policy_for_id(a->family), e->trial_flag) ||
            (a->field_caps & b->field_caps) != a->field_caps ||
            !extended_capabilities_inherited(a->id, b->id) ||
            !creatures_command_learned(b->id, e->min_level, b->signature_ability)) return 0;
        for (j = 0; j < a->learnset_count; ++j) {
            const CreatureLearn *l = &creature_learnsets[a->learnset_offset + j];
            if (!creatures_command_learned(b->id, l->level, l->ability_id)) return 0;
        }
        /* Strictly increasing tiers prove acyclicity across every branch.
         * Unique destinations prohibit merges. Exact reviewed edge comparison
         * above is the allowlist for any repeated source. */
        for (j = 0; j < i; ++j)
            if (creature_evolutions[j].to == e->to ||
                (creature_evolutions[j].from == e->from &&
                 creature_evolutions[j].to == e->to)) return 0;
    }
    return 1;
}
/* Persistent scalar rules are frozen across revisions1-5. No current form,
 * ability, incoming edge, nickname table or legacy-story map is consulted. */
CREATURE_INLINE int instance_shape_valid(const CreatureInstance *c, unsigned legacy) {
    CreatureU32 n;
    if (!(c->flags & 1u) || (c->flags & ~7u) ||
        c->level < 1 || c->level > 50 || c->bond > 100 || c->xp > 470596u ||
        !c->instance_id || c->instance_id == U32_MAX_VALUE || c->nickname_id ||
        ((c->flags & 2u) && legacy >= 4) ||
        c->selected_command > 1 || !c->equipped[c->selected_command] ||
        (c->equipped[0] && c->equipped[0] == c->equipped[1])) return 0;
    n = c->level - 1u;
    if (c->xp < 4u*n*n*n) return 0;
    ++n;
    return c->level == 50 || c->xp < 4u*n*n*n;
}
int creatures_instance_validate(const CreatureInstance *c) {
    const CreatureForm *f;
    const CreatureFormPolicy *current;
    const CreatureFamilyPolicy *family;
    unsigned j;
    if (!c) return 0;
    if (!c->form_id) return instance_is_zero(c);
    f = creatures_form(c->form_id);
    family = f ? family_policy_for_id(f->family) : 0;
    current = f ? form_policy_for_id(f->id) : 0;
    if (!f || !family || !current || !(c->flags & CREATURE_OCCUPIED) || (c->flags & ~CREATURE_FLAGS_MASK) ||
        c->level < 1 || c->level > 50 || c->bond > 100 || c->xp > CREATURE_XP_CAP ||
        /* The authored thresholds are strictly increasing. Validate the known
         * level's exact interval instead of rediscovering it by binary search. */
        (c->xp < creatures_xp_threshold(c->level) ||
         (c->level < CREATURE_MAX_LEVEL && c->xp >= creatures_xp_threshold(c->level + 1u))) || !c->instance_id ||
        c->instance_id == U32_MAX_VALUE || c->nickname_id > CREATURE_NICKNAME_MAX ||
        (c->trial_flags & ~current->trial_mask) ||
        ((c->flags & CREATURE_STORY_LOCKED) && (f->family < 1 || f->family > 4)) || c->polarity != f->polarity ||
        c->selected_command > 1 || !c->equipped[c->selected_command] ||
        (c->equipped[0] && c->equipped[0] == c->equipped[1])) return 0;
    if ((family->trial & (family->trial - 1u)) && !trial_subset_valid(family, c->trial_flags)) return 0;
    for (j = 0; j < 2; ++j)
        if (c->equipped[j] && !creatures_command_learned(c->form_id, c->level, c->equipped[j])) return 0;
    if (f->tier > 1) {
        const CreatureEvolution *e = incoming_evolution(c->form_id);
        if (!e || c->level < e->min_level) return 0;
        /* New branch receipts never tighten a released family's acceptance. */
        if (((f->family >= 17 && f->family <= 24) ||
             (e->chapter_flags & (CREATURE_RETURN_READY | CREATURE_RETURN_COMPLETE))) &&
            (c->bond < e->min_bond || (c->trial_flags & e->trial_flag) != e->trial_flag)) return 0;
    }
    return 1;
}
int creatures_instance_validate_revision(const CreatureInstance *c, unsigned revision) {
    const CreatureRevisionPolicy *p;
    unsigned i;
    if (revision == CREATURE_CONTENT_REVISION) return creatures_instance_validate(c);
    if (!c || revision < 1 || revision > 6) return 0;
    if (!c->form_id) return instance_is_zero(c);
    p = revision_policy_for_id(c->form_id, revision);
    if (!p || !instance_shape_valid(c, p->family >= 1 && p->family <= 4 ? p->family - 1u : 255u) ||
        c->polarity != p->polarity || c->level < p->min_level ||
        (c->trial_flags & ~p->trial_mask)) return 0;
    if (revision == 6) {
        const CreatureRevision6Constraint *limit = &revision6_constraints[revision6_policy_index[c->form_id]-1u];
        if (c->bond < limit->min_bond || (c->trial_flags & limit->required_trial) != limit->required_trial) return 0;
        for (i = 0; i < sizeof(revision6_trial_dependencies) / sizeof(revision6_trial_dependencies[0]); ++i) {
            const CreatureRevisionTrialDependency *d = &revision6_trial_dependencies[i];
            if (p->family == d->family && (c->trial_flags & d->mask) &&
                (c->trial_flags & d->prerequisite) != d->prerequisite) return 0;
        }
    }
    if (revision == 5) {
        for (i = 0; i < sizeof(revision5_trial_dependencies) / sizeof(revision5_trial_dependencies[0]); ++i) {
            const CreatureRevisionTrialDependency *d = &revision5_trial_dependencies[i];
            if (p->family == d->family && (c->trial_flags & d->mask) &&
                (c->trial_flags & d->prerequisite) != d->prerequisite) return 0;
        }
    }
    for (i = 0; i < 2; ++i)
        if (c->equipped[i] && !creatures_command_learned_revision(c->form_id, c->level, c->equipped[i], revision)) return 0;
    return 1;
}
