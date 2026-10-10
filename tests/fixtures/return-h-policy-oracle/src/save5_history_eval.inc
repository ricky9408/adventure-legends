/* Released-policy evaluators are bounded and shared by blocking decoded-state
 * validation and streaming bank scans. They never resolve a historical row
 * through current quest, equipment, region or creature source catalogs. */
static const Save5HistoryVersion *history_version(unsigned revision) {
    if(revision==7)return &save5_policy7_version;
    if(revision==6)return &save5_policy6_version;
    if(revision==5)return &save5_policy5_version;
    return revision >= 1 && revision <= 4 ? &save5_history_versions[revision] : 0;
}
static const Save5HistoryItem *history_item(unsigned id, unsigned revision) {
    const Save5HistoryVersion *v = history_version(revision);
    unsigned row;
    if(revision>=7)for(row=0;row<5;++row)if(save5_policy7_items[row].id==id)return &save5_policy7_items[row];
    if(revision>=6)for(row=0;row<6;++row)if(save5_policy6_items[row].id==id)return &save5_policy6_items[row];
    if(revision>=5)for(row=0;row<6;++row)if(save5_policy5_items[row].id==id)return &save5_policy5_items[row];
    if (!v || id >= sizeof save5_history_item_source) return 0;
    row = save5_history_item_source[id];
    return row && row <= v->item_count && row <= 25 ? &save5_history_items[row - 1u] : 0;
}
static const Save5HistoryQuest *history_quest(unsigned id) {
    return id<30?&save5_history_quests[id]:id<38?&save5_policy5_quests[id-30]:id<46?&save5_policy6_quests[id-38]:&save5_policy7_quests[id-46];
}
static const Save5HistoryRoom *history_room(unsigned id,unsigned revision) {
    if(revision>=6 && id==38)return &save5_policy6_magma_return;
    return id<38?&save5_history_rooms[id]:id<46?&save5_policy5_rooms[id-38]:id<54?&save5_policy6_rooms[id-46]:&save5_policy7_rooms[id-54];
}
static int history_claimed(const Save5Quests *q, unsigned quest_plus_one) {
    return !quest_plus_one || save5_quest_state(q, quest_plus_one - 1u) == 3;
}
static int history_campaign_validate(const CampaignSave *c, unsigned revision) {
    const Save5HistoryVersion *v = history_version(revision);
    const Save5HistoryRoom *room;
    unsigned i, chapter, seen, spirits;
    Save4U32 flags;
    if (!c || !v || c->room > v->last_room || c->spawn > 5) return 0;
    room = history_room(c->room,revision);
    chapter = c->chapter_flags; seen = c->story_seen; flags = c->room_flags;
    if (!room->since || room->since > revision || !(room->spawns & (1u << c->spawn)) ||
        c->bridge > 1 || c->torches > 3 || c->relic > 1 || c->camp > 1 ||
        c->optional_flags > 1 || seen > 127 || (flags & ~65535u) ||
        (chapter != 0 && chapter != 1 && chapter != 3 && chapter != 7 && chapter != 15)) return 0;
    spirits = chapter >= 3 ? 15u : chapter ? 7u : 3u;
    if (c->spirit > 3 || !(spirits & (1u << c->spirit)) ||
        !has_all(chapter, room->chapter) || !has_all(flags, room->entry)) return 0;
    for (i = 0; i < sizeof save5_history_flag_gates / sizeof save5_history_flag_gates[0]; ++i) {
        const Save5HistoryFlagGate *g = &save5_history_flag_gates[i];
        if ((flags & g->trigger) && (!has_all(flags, g->required) || !has_all(chapter, g->chapter))) return 0;
    }
    if ((c->optional_flags && !(chapter & 1u)) ||
        ((seen & 7u) && !(chapter & 1u)) || ((seen & 24u) && !(chapter & 2u)) ||
        ((seen & 32u) && !(chapter & 4u)) || ((seen & 64u) && !(c->optional_flags & 1u))) return 0;
    if (!c->room && ((c->spawn == 4 && !(chapter & 1u)) ||
                     (c->spawn == 5 && !(chapter & 2u)))) return 0;
    if (c->room == 1 && ((c->spawn == 2 && !c->camp) ||
                        (c->spawn == 1 && !c->bridge))) return 0;
    if (c->spawn == 1 && ((c->room == 2 && c->torches != 3) ||
                         !has_all(flags, room->north))) return 0;
    return 1;
}
static int history_objective_validate(const Save5Quests *q, unsigned id, unsigned revision) {
    const Save5HistoryVersion *v = history_version(revision);
    unsigned state, objectives;
    const Save5HistoryQuest *p;
    if (!q || id >= 64 || !v) return 0;
    state = save5_quest_state(q, id); objectives = q->objectives[id];
    if (id >= v->quest_count) return !state && !objectives;
    p = history_quest(id);
    if (objectives & ~p->mask) return 0;
    if (p->prefix && (objectives & (objectives + 1u))) return 0;
    if (!state) return !objectives;
    return state == 1 ? objectives != p->mask : objectives == p->mask;
}
static int history_reward_validate(const Save5Quests *q, unsigned index) {
    unsigned i;
    for (i = 0; i < 8; ++i)
        if (((q->rewards[index] >> i) & 1u) !=
            (save5_quest_state(q, save5_history_reward_quests[index * 8u + i]) == 3)) return 0;
    return 1;
}
static int history_quest_fields_validate(const Save5Quests *q, unsigned revision) {
    const Save5HistoryVersion *v = history_version(revision);
    unsigned i;
    if (!q || !v) return 0;
    for (i = 0; i < 64; ++i) {
        unsigned limit = i < v->quest_count ? history_quest(i)->variable_max : 0;
        if (q->variables[i] > limit || (q->variables[i] && !save5_quest_state(q, i))) return 0;
    }
    for (i = 0; i < 32; ++i) if (q->region_flags[i] & ~v->regions[i]) return 0;
    for (i = 0; i < 16; ++i) {
        if (q->anchors[i] & ~v->anchors[i]) return 0;
        if (i < (revision>=7?6u:revision>=6?5u:revision==5?4u:3u) && (q->anchors[i] & ~q->region_flags[i])) return 0;
    }
    for (i = 0; i < (revision>=7?6u:revision>=6?5u:revision==5?4u:3u); ++i)
        if (q->region_flags[i] && !(q->region_flags[i] & 1u)) return 0;
    if(revision>=5 && (q->region_flags[19] & (q->region_flags[19]+1u)))return 0;
    if(revision>=6 && ((q->region_flags[20] & (q->region_flags[20]+1u)) ||
        (q->region_flags[21] & (q->region_flags[21]+1u))))return 0;
    return 1;
}
static int history_quest_campaign_validate(const CampaignSave *c, const Save5Quests *q,
                                           unsigned revision) {
    const Save5HistoryVersion *v = history_version(revision);
    const Save5HistoryRoom *room;
    unsigned i, j;
    if (!v || c->room > v->last_room) return 0;
    room = history_room(c->room,revision);
    for (i = 0; i < 3; ++i) if (q->region_flags[i]) {
        const Save4U8 *p = save5_history_regions[i];
        if (!has_all(c->chapter_flags, p[1])) return 0;
        for (j = 0; j < 3; ++j)
            if ((p[2] & (1u << j)) && !(q->region_flags[j] & 1u)) return 0;
    }
    for (i = 0; i < v->quest_count; ++i) if (save5_quest_state(q, i)) {
        const Save5HistoryQuest *p = history_quest(i);
        if (!(c->chapter_flags & 1u) || !(q->region_flags[0] & 1u) ||
            !(q->region_flags[p->region] & 1u) ||
            (p->region == 1 && !(c->chapter_flags & 2u)) ||
            !history_claimed(q, p->prior_a) || !history_claimed(q, p->prior_b)) return 0;
    }
    for (i = 0; i < sizeof save5_history_visit_gates / sizeof save5_history_visit_gates[0]; ++i) {
        const Save5HistoryVisitGate *g = &save5_history_visit_gates[i];
        if ((q->region_flags[g->region] & g->trigger) &&
            (!history_claimed(q, g->quest_a) || !history_claimed(q, g->quest_b) ||
             (g->objective_quest && !has_all(q->objectives[g->objective_quest - 1u], g->objectives)))) return 0;
    }
    if (q->region_flags[2] || q->region_flags[8] || q->region_flags[18]) {
        if (!(c->chapter_flags & 2u) || !(q->region_flags[0] & 1u) ||
            !(q->region_flags[1] & 1u) || !(q->region_flags[2] & 1u) || !history_claimed(q, 22)) return 0;
    }
    if (q->region_flags[18]) {
        if (!(q->region_flags[2] & 4u)) return 0;
        for (i = 0; i < 2; ++i)
            if ((q->region_flags[18] & (1u << i)) &&
                save5_quest_state(q, save5_history_discovery_quest[i]) < 2) return 0;
    }
    for (i = 0; i < 8; ++i) if (q->region_flags[8] & (1u << i)) {
        if (!(q->region_flags[2] & save5_history_field_visit[i]) ||
            !has_all(q->region_flags[18], save5_history_field_discovery[i])) return 0;
    }
    if(revision>=5 && !magma_quest_campaign_validate(q))return 0;
    if(revision>=6 && !underwater_quest_campaign_validate(q))return 0;
    if(revision>=7 && !return_quest_campaign_validate(q))return 0;
    if(revision>=6 && c->room==38 && c->spawn==4 && !(q->region_flags[4]&1u))return 0;
    if (room->region != 255) {
        if (!(q->region_flags[room->region] & room->visit) || !history_claimed(q, room->quest)) return 0;
        if (c->spawn == (room->since==5?3u:2u) && room->anchor && !(q->anchors[room->region] & room->anchor)) return 0;
    }
    return 1;
}
static unsigned history_retained_evidence(const CreatureInstance *c) {
    const Save5HistoryCreature *p;
    unsigned row;
    if (c->form_id >= sizeof save5_history_creature_row) return 0;
    row = save5_history_creature_row[c->form_id];
    if (!row) return 0;
    p = &save5_history_creatures[row - 1u];
    return p->owner | ((c->trial_flags & p->trial) && c->level >= p->level && c->bond >= p->bond ? p->trained : 0);
}
static unsigned history_southern_evidence(const CreatureInstance *c) {
    const Save5HistoryCreature *p;
    unsigned row, result;
    if (!c->form_id || c->form_id >= sizeof save5_history_southern_row) return 0;
    row = save5_history_southern_row[c->form_id];
    if (!row) return 0;
    p = &save5_history_southern[row - 1u]; result = p->owner;
    if (c->trial_flags || c->form_id == p->evolved) {
        if (c->trial_flags != p->trial || c->level < p->level || c->bond < p->bond) return 0x80000000u;
        result |= (unsigned)p->owner << 10;
    }
    return result;
}
static int history_obtained(const Save4U8 *obtained, unsigned id) {
    return id && ((obtained[(id - 1u) >> 3] >> ((id - 1u) & 7u)) & 1u);
}
static int history_creatures_validate(const Save5Quests *q, const Save4U8 *obtained,
                                      const Save4U8 *rewards, unsigned retained, unsigned southern) {
    unsigned i, sources = (unsigned)q->region_flags[8] << 2;
    for (i = 0; i < sizeof save5_history_creatures / sizeof save5_history_creatures[0]; ++i) {
        const Save5HistoryCreature *p = &save5_history_creatures[i];
        if (save5_quest_state(q, p->source_quest) == 3 &&
            (!(retained & p->owner) || !((rewards[(p->reward - 1u) >> 3] >> ((p->reward - 1u) & 7u)) & 1u) ||
             (i < 2 && !history_obtained(obtained, p->base) && !history_obtained(obtained, p->evolved)))) return 0;
        if (i >= 2 && save5_quest_state(q, save5_history_trial_quests[i - 2u]) == 3 &&
            !(retained & p->trained)) return 0;
    }
    if (southern & 0x80000000u) return 0;
    for (i = 0; i < 2; ++i)
        if (save5_quest_state(q, save5_history_southern[i].source_quest) == 3) sources |= 1u << i;
    if ((sources & southern) != sources || ((southern >> 10) & ~sources) ||
        ((southern >> 10) && (sources & 3u) != 3u)) return 0;
    for (i = 0; i < 10; ++i) if (sources & (1u << i)) {
        const Save5HistoryCreature *p = &save5_history_southern[i];
        if (!history_obtained(obtained, p->base) && !history_obtained(obtained, p->evolved)) return 0;
    }
    return 1;
}
static int history_equipment_record_validate(const EquipmentRecord *r, unsigned revision) {
    const Save5HistoryItem *p;
    if (!r->item_id) return !(r->rank | r->flags | r->quantity | r->reserved[0] | r->reserved[1] | r->reserved[2]);
    p = history_item(r->item_id, revision);
    return p && !r->rank && r->flags == p->flags && r->quantity == 1 &&
        !r->reserved[0] && !r->reserved[1] && !r->reserved[2];
}
static int history_equipment_refs_validate(const EquipmentState *e, unsigned revision) {
    unsigned i;
    if (e->bag[0].item_id != 1 || !history_equipment_record_validate(&e->bag[0], revision)) return 0;
    for (i = 0; i < 5; ++i) {
        unsigned ref = e->equipped[i];
        const Save5HistoryItem *p;
        if (ref == 255) { if (!i) return 0; continue; }
        if (ref >= 48 || !history_equipment_record_validate(&e->bag[ref], revision)) return 0;
        p = history_item(e->bag[ref].item_id, revision);
        if (!p || p->slot != i) return 0;
    }
    return 1;
}
static int history_equipment_claims_validate(const Save5Quests *q, const EquipmentState *e,
                                             unsigned revision) {
    const Save5HistoryVersion *v = history_version(revision);
    unsigned i;
    if (!v) return 0;
    for (i = 0; i < 64; ++i) {
        unsigned claimed = (e->reward_claims[i >> 3] >> (i & 7u)) & 1u;
        const Save5HistoryItem *p;
        if (i >= v->item_count) { if (claimed) return 0; continue; }
        p = i<25?&save5_history_items[i]:i<31?&save5_policy5_items[i-25]:i<37?&save5_policy6_items[i-31]:&save5_policy7_items[i-37];
        if (claimed && !(e->seen[p->id >> 3] & (1u << (p->id & 7u)))) return 0;
        if (p->category == 1 && claimed && !(q->region_flags[0] & 1u)) return 0;
        if (p->category == 2 && claimed != (save5_quest_state(q, (unsigned)p->quest) == 3)) return 0;
    }
    return 1;
}
static int history_equipment_validate(const Save5Quests *q, const EquipmentState *e, unsigned revision) {
    Save4U8 owned[64];
    unsigned i, j;
    if (!history_equipment_refs_validate(e, revision) ||
        !zero_bytes(e->settings_reserved, 11) || !zero_bytes(e->wallet_key_reserved, 16) ||
        !zero_bytes(e->reserved, 24) || !history_equipment_claims_validate(q, e, revision)) return 0;
    clear_bytes(owned, sizeof owned);
    for (i = 0; i < 48; ++i) {
        const EquipmentRecord *r = &e->bag[i];
        unsigned mask;
        if (!history_equipment_record_validate(r, revision)) return 0;
        if (!r->item_id) continue;
        mask = 1u << (r->item_id & 7u);
        if (!(e->seen[r->item_id >> 3] & mask) || (owned[r->item_id >> 3] & mask)) return 0;
        owned[r->item_id >> 3] |= (Save4U8)mask;
    }
    for (i = 0; i < 64; ++i) for (j = 0; j < 8; ++j)
        if ((e->seen[i] & (1u << j)) && !history_item(i * 8u + j, revision)) return 0;
    return 1;
}
/* Revision1 wire gear was all-zero reserved. Only after verified decode is
 * its canonical starter materialized, with no dependency on live item data. */
static void history_starter_init(EquipmentState *e) {
    unsigned i;
    clear_bytes(e, sizeof *e);
    e->bag[0].item_id = 1; e->bag[0].flags = 1; e->bag[0].quantity = 1;
    e->seen[0] = 2; e->reward_claims[0] = 1;
    for (i = 1; i < 5; ++i) e->equipped[i] = 255;
}
static int history_starter_validate(const EquipmentState *e) {
    unsigned i;
    if (e->bag[0].item_id != 1 || e->bag[0].rank || e->bag[0].flags != 1 || e->bag[0].quantity != 1 ||
        !zero_bytes(e->bag[0].reserved, 3) || !zero_bytes((const Save4U8 *)(e->bag + 1), 47u * 8u) ||
        e->equipped[0] || !zero_bytes(e->settings_reserved, 11) || e->seen[0] != 2 ||
        !zero_bytes(e->seen + 1, 63) || !zero_bytes(e->wallet_key_reserved, 16) ||
        e->reward_claims[0] != 1 || !zero_bytes(e->reward_claims + 1, 7) || !zero_bytes(e->reserved, 24)) return 0;
    for (i = 1; i < 5; ++i) if (e->equipped[i] != 255) return 0;
    return 1;
}
int save5_validate_revision(const Save5State *s, unsigned revision) {
    if(revision==7)return save5_validate(s);
    unsigned i, retained = 0, southern = 0;
    if (!s || !history_campaign_validate(&s->campaign, revision) ||
        !creatures_roster_validate_revision(&s->roster, revision) ||
        !history_quest_fields_validate(&s->quests, revision)) return 0;
    for (i = 0; i < 64; ++i)
        if (!history_objective_validate(&s->quests, i, revision)) return 0;
    for (i = 0; i < 8; ++i) if (!history_reward_validate(&s->quests, i)) return 0;
    for (i = 0; i < 160; ++i) {
        retained |= history_retained_evidence(&s->roster.instances[i]);
        southern |= history_southern_evidence(&s->roster.instances[i]);
    }
    return history_quest_campaign_validate(&s->campaign, &s->quests, revision) &&
        history_creatures_validate(&s->quests, s->roster.obtained, s->roster.rewards, retained, southern) &&
        (revision<5 || magma_roster_sources_validate(&s->quests,&s->roster)) &&
        (revision<6 || underwater_roster_sources_validate(&s->quests,&s->roster)) &&
        (revision == 1 ? history_starter_validate(&s->equipment) :
         history_equipment_validate(&s->quests, &s->equipment, revision));
}

