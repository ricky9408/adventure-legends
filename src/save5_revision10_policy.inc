/* Immutable revision10 acceptance, reproduced from the pinned G7 source closure.
 * Source: tests/fixtures/v5-revision10-policy-oracle/manifest.json. */
static Save4U32 history10_entry_requirements(unsigned room);
static Save4U32 history10_north_requirements(unsigned room);
static int history10_save5_campaign_validate(const CampaignSave *s);
static unsigned history10_quest_objective_mask(unsigned id);
static int history10_quest_objective_validate(const Save5Quests *q, unsigned id);
static int history10_quest_reward_validate(const Save5Quests *q, unsigned index);
static int history10_quest_fields_validate(const Save5Quests *q);
static int history10_save5_quests_validate(const Save5Quests *q);
static int history10_magma_quest_campaign_validate(const Save5Quests *q);
static int history10_quest_campaign_validate(const CampaignSave *c, const Save5Quests *q);
static unsigned history10_retained_creature_bits(const CreatureInstance *c);
static unsigned history10_retained_creatures(const CreatureRoster *r);
static int history10_quest_creatures_validate(const Save5Quests *q, const Save4U8 *obtained,
                                    const Save4U8 *rewards, unsigned retained);
static unsigned history10_southern_instance_evidence(const CreatureInstance *c);
static unsigned history10_southern_roster_evidence(const CreatureRoster *r);
static int history10_southern_sources_validate(const Save5Quests *q, const Save4U8 *obtained,
                                      unsigned evidence);
static unsigned history10_magma_form_row(unsigned form);
static void history10_magma_instance_evidence(MagmaEvidence *e,const CreatureInstance *c);
static int history10_magma_sources_validate(const Save5Quests *q,const Save4U8 *obtained,
                                 const MagmaEvidence *e);
static int history10_magma_roster_sources_validate(const Save5Quests *q,const CreatureRoster *r);
static int history10_underwater_quest_campaign_validate(const Save5Quests *q);
static void history10_underwater_instance_evidence(UnderwaterEvidence *e,const CreatureInstance *c);
static int history10_underwater_sources_validate(const Save5Quests *q,const Save4U8 *obtained,
 const UnderwaterEvidence *e);
static int history10_underwater_roster_sources_validate(const Save5Quests *q,const CreatureRoster *r);
static int history10_return_quest_campaign_validate(const Save5Quests *q);
static void history10_return_instance_evidence(ReturnEvidence *e,const CreatureInstance *c);
static int history10_return_sources_validate(const Save5Quests *q,const Save4U8 *obtained,const ReturnEvidence *e);
static int history10_return_roster_sources_validate(const Save5Quests *q,const CreatureRoster *r);
static int history10_horizons_visit(const Save5Quests*q,unsigned room);
static int history10_horizons_done(const Save5Quests*q,unsigned id);
static unsigned history10_horizons_receipt(const Save5Quests*q,unsigned index,unsigned repeat);
static int history10_horizons_objective_validate(const Save5Quests*q,unsigned id);
static int history10_horizons_quest_campaign_validate(const Save5Quests*q);
static int history10_horizons_campaign_validate(const CampaignSave*c,const Save5Quests*q);
static void history10_horizons_instance_evidence(HorizonsEvidence*e,const CreatureInstance*c);
static int history10_horizons_sources_validate(const Save5Quests*q,const Save4U8*obtained,const HorizonsEvidence*e);
static int history10_horizons_roster_sources_validate(const Save5Quests*q,const CreatureRoster*r);
static int history10_covenant_done(const Save5Quests*q,unsigned quest);
static int history10_covenant_visit(const Save5Quests*q,unsigned room);
static int history10_covenant_entry(const CampaignSave*c,const Save5Quests*q);
static int history10_covenants_objective_validate(const Save5Quests*q,unsigned quest);
static int history10_covenants_quest_campaign_validate(const CampaignSave*c,const Save5Quests*q);
static int history10_covenants_campaign_validate(const CampaignSave*c,const Save5Quests*q);
static void history10_covenants_instance_evidence(CovenantsEvidence*e,const CreatureInstance*c);
static int history10_covenants_sources_validate(const Save5Quests*q,const Save4U8*obtained,const CovenantsEvidence*e);
static int history10_covenants_roster_sources_validate(const Save5Quests*q,const CreatureRoster*r);
static const Save4U8 history10_quest_masks[64] = {7,3,7,7,3,1,1,1,3,7,1,3,7,3,7,7,3,7,7,3,7,15,3,3,15,7,3,3,3,3,3,3,15,7,3,3,3,7,3,3,15,7,3,3,3,7,3,7,7,7,7,15,7,15,7,15,15,15,7,15,7,15,15,7};
static const Save4U8 history10_magma_bases[9]={31,34,37,40,43,46,95,97,99};
static Save4U32 history10_entry_requirements(unsigned room) {
    switch (room) {
    case 6: return SKY_PATH;
    case 7: return SKY_PATROL;
    case 8: return SKY_ALL;
    case 10: return SAVE4_CORE_PATH_OPEN;
    case 11: return CORE_WEIGHTS;
    case 12: return CORE_ROOTS;
    case 13: return CORE_ROOTS | ALL_LAMPS;
    default: return 0;
    }
}
static Save4U32 history10_north_requirements(unsigned room) {
    switch (room) {
    case 5: return SKY_PATH;
    case 6: return SKY_PATROL;
    case 7: return SKY_ALL;
    case 9: return SAVE4_CORE_PATH_OPEN;
    case 10: return CORE_WEIGHTS;
    case 11: return CORE_ROOTS;
    case 12: return CORE_ROOTS | ALL_LAMPS;
    default: return 0;
    }
}
static int history10_save5_campaign_validate(const CampaignSave *s) {
    Save4U32 f;
    if (!s) return 0;
    f = s->room_flags;
    unsigned chapter = s->chapter_flags, seen = s->story_seen;
    if ((s->room > 13 && (s->room < 16 || s->room > 77)) ||
        s->spawn > SAVE4_SPAWN_WEST_TRAIL ||
        s->bridge > 1 || s->torches > 3 || s->relic > 1 || s->camp > 1 ||
        s->optional_flags > 1 || (seen & ~0x7Fu) || (f & ~0xFFFFu)) return 0;
    if (chapter != 0 && chapter != 1 && chapter != 3 && chapter != 7 && chapter != 15)
        return 0;
    if (s->spirit > 3 || !((chapter>=3?15u:chapter?7u:3u) & (1u << s->spirit))) return 0;
    if ((f & 0x3Fu) && !(chapter & SAVE4_GROVE_CLEAR)) return 0;
    if ((f & 0xFFC0u) && !(chapter & SAVE4_SKY_CLEAR)) return 0;
    if (s->optional_flags && !(chapter & SAVE4_GROVE_CLEAR)) return 0;
    if ((seen & (SAVE4_SEEN_LEGACY_RECAP | SAVE4_SEEN_WIND_JOIN | SAVE4_SEEN_SKY_INTRO)) &&
        !(chapter & SAVE4_GROVE_CLEAR)) return 0;
    if ((seen & (SAVE4_SEEN_STONE_JOIN | SAVE4_SEEN_CORE_INTRO)) &&
        !(chapter & SAVE4_SKY_CLEAR)) return 0;
    if ((seen & SAVE4_SEEN_CORE_RELEASE) && !(chapter & SAVE4_CORE_CLEAR)) return 0;
    if ((seen & SAVE4_SEEN_CHIME) && !(s->optional_flags & SAVE4_RIDGE_CHIME)) return 0;

    if ((f & SAVE4_SKY_VANE) && !(f & SAVE4_SKY_BRIDGE)) return 0;
    if ((f & SAVE4_SKY_PATROL_CLEAR) && !has_all(f, SKY_PATH)) return 0;
    if ((f & (SAVE4_RELAY_LEFT | SAVE4_RELAY_RIGHT | SAVE4_RELAY_FIRE)) &&
        !has_all(f, SKY_PATROL)) return 0;
    if ((f & (SAVE4_WEIGHT_WEST | SAVE4_WEIGHT_EAST)) && !(f & SAVE4_CORE_PATH_OPEN)) return 0;
    if ((f & (SAVE4_WELL_UNCAPPED | SAVE4_ROOT_CHANNEL | SAVE4_THORNS_BURNED)) &&
        !has_all(f, CORE_WEIGHTS)) return 0;
    if ((f & SAVE4_ROOT_CHANNEL) && !(f & SAVE4_WELL_UNCAPPED)) return 0;
    /* Burning thorns before growing roots is valid; do not demand the reverse. */
    if ((f & ALL_LAMPS) && !has_all(f, CORE_ROOTS)) return 0;

    if (s->room >= 4 && s->room <= 8 && !(chapter & SAVE4_GROVE_CLEAR)) return 0;
    if (s->room >= 9 && s->room <= 13 && !(chapter & SAVE4_SKY_CLEAR)) return 0;
    if (s->room >= 70) {
        static const Save4U8 spawns[8]={31,3,3,3,15,3,3,3};
        return (chapter & SAVE4_SKY_CLEAR) && (spawns[s->room-70] & (1u<<s->spawn));
    }
    if (s->room >= 62) {
        static const Save4U8 spawns[8]={63,15,3,15,7,15,1,3};
        return (chapter & SAVE4_SKY_CLEAR) && (spawns[s->room-62] & (1u<<s->spawn));
    }
    if (s->room >= 54) {
        return (chapter & SAVE4_SKY_CLEAR) &&
            (save5_policy7_rooms[s->room-54].spawns & (1u<<s->spawn));
    }
    if (s->room >= 46) {
        return (chapter & SAVE4_SKY_CLEAR) &&
            (save5_policy6_rooms[s->room-46].spawns & (1u<<s->spawn));
    }
    if (s->room >= 38) {
        /* assets/magma_region/validation.json verifies radius-five paths. */
        return (chapter & SAVE4_SKY_CLEAR) &&
            (s->room==38?s->spawn<=4:s->room==39?s->spawn<=3:s->spawn==0);
    }
    if (s->room >= 30) {
        if (!(chapter & SAVE4_SKY_CLEAR)) return 0;
        if (s->room == 30) return s->spawn <= 4;
        if (s->room == 31) return s->spawn <= 3;
        return s->spawn == 0;
    }
    if (s->room >= 22) {
        if (!(chapter & SAVE4_SKY_CLEAR)) return 0;
        if (s->room == 22) return s->spawn <= 4;
        if (s->room == 23) return s->spawn <= 2;
        return s->spawn == 0;
    }
    if (s->room >= 16) {
        if (!(chapter & SAVE4_GROVE_CLEAR)) return 0;
        if (s->room == 16) return s->spawn <= 5;
        if (s->room == 17) return s->spawn <= 2;
        return s->spawn == 0;
    }
    if (!has_all(f, history10_entry_requirements(s->room))) return 0;
    if (s->room == 0) {
        if (s->spawn != SAVE4_SPAWN_SOUTH && s->spawn != SAVE4_SPAWN_ELDER &&
            s->spawn != SAVE4_SPAWN_EAST_TRAIL && s->spawn != SAVE4_SPAWN_WEST_TRAIL)
            return 0;
        if (s->spawn == SAVE4_SPAWN_EAST_TRAIL && !(chapter & SAVE4_GROVE_CLEAR)) return 0;
        if (s->spawn == SAVE4_SPAWN_WEST_TRAIL && !(chapter & SAVE4_SKY_CLEAR)) return 0;
    } else if (s->room == 1) {
        if (s->spawn > SAVE4_SPAWN_CAMP || (s->spawn == SAVE4_SPAWN_CAMP && !s->camp)) return 0;
        if (s->spawn == SAVE4_SPAWN_NORTH && !s->bridge) return 0;
    } else if (s->spawn > SAVE4_SPAWN_NORTH) return 0;
    if (s->spawn == SAVE4_SPAWN_NORTH) {
        if (s->room == 2 && s->torches != 3) return 0;
        if (!has_all(f, history10_north_requirements(s->room))) return 0;
    }
    return 1;
}
static unsigned history10_quest_objective_mask(unsigned id) {
    return id < sizeof history10_quest_masks ? history10_quest_masks[id] : 0;
}
static int history10_quest_objective_validate(const Save5Quests *q, unsigned id) {
    if(!q||id>=64)return 0;
    unsigned state = save5_quest_state(q, id), mask = history10_quest_objective_mask(id);
    unsigned objectives = q->objectives[id];
    if(id>=60&&id<64)return history10_covenants_objective_validate(q,id);
    if(id>=54&&id<60)return history10_horizons_objective_validate(q,id);
    if (!mask) return !state && !objectives;
    if (objectives & ~mask) return 0;
    /* Beacon stages are monotonic prefixes: 0,1,3,7,15 only. */
    if ((id == 21 || id == 24 || id == 32 || id == 40) && (objectives & (objectives + 1u))) return 0;
    if (state == SAVE5_QUEST_INACTIVE) return !objectives;
    if (state == SAVE5_QUEST_ACTIVE) return objectives != mask;
    return objectives == mask;
}
static int history10_quest_reward_validate(const Save5Quests *q, unsigned index) {
    unsigned i;
    for (i = 0; i < 8; ++i)
        if (((q->rewards[index] >> i) & 1u) !=
            (save5_quest_state(q, index * 8u + i) == SAVE5_QUEST_CLAIMED)) return 0;
    return 1;
}
static int history10_quest_fields_validate(const Save5Quests *q) {
    unsigned i;
    for (i = 0; i < 64; ++i) {
        if (i == 3 || i == 9) {
            if (q->variables[i] > 3 ||
                (q->variables[i] && !save5_quest_state(q, i))) return 0;
        } else if (q->variables[i]) return 0;
    }
    if ((q->region_flags[0] & ~63u) ||
        (q->region_flags[0] && !(q->region_flags[0] & 1u)) ||
        (q->region_flags[1] && !(q->region_flags[1] & 1u)) ||
        (q->region_flags[2] && !(q->region_flags[2] & 1u)) ||
        (q->region_flags[3] && !(q->region_flags[3] & 1u)) ||
        (q->region_flags[4] && !(q->region_flags[4] & 1u)) ||
        (q->region_flags[5] && !(q->region_flags[5] & 1u)) ||
        (q->region_flags[6] && !(q->region_flags[6]&1u)) || (q->region_flags[7] && !(q->region_flags[7]&1u)) || (q->region_flags[9] & ~127u) ||
        (q->region_flags[10] & ~63u) || (q->region_flags[11] & ~3u) || (q->region_flags[13]&~15u) || (q->region_flags[15]&~15u) ||
        (q->region_flags[16] & ~15u) || (q->region_flags[18] & ~3u) ||
        (q->region_flags[19] & ~7u) || (q->region_flags[19] & (q->region_flags[19]+1u)) ||
        (q->region_flags[20] & ~3u) || (q->region_flags[20] & (q->region_flags[20]+1u)) ||
        (q->region_flags[21] & ~7u) || (q->region_flags[21] & (q->region_flags[21]+1u)) ||
        !zero_bytes(q->region_flags + 24, 8) ||
        (q->anchors[0] & ~3u) || (q->anchors[1] & ~3u) ||
        (q->anchors[2] & ~3u) || (q->anchors[3] & ~3u) ||
        (q->anchors[4] & ~3u) || (q->anchors[5] & ~3u) || (q->anchors[6]&~3u) || (q->anchors[7]&~3u) || !zero_bytes(q->anchors + 8, 8)) return 0;
    if (q->anchors[5] & ~q->region_flags[5]) return 0;
    if (q->anchors[4] & ~q->region_flags[4]) return 0;
    if (q->anchors[3] & ~q->region_flags[3]) return 0;
    if ((q->anchors[2] & 1u) && !(q->region_flags[2] & 1u)) return 0;
    if ((q->anchors[2] & 2u) && !(q->region_flags[2] & 2u)) return 0;
    if ((q->anchors[0] & 1u) && !(q->region_flags[0] & 1u)) return 0;
    if ((q->anchors[0] & 2u) && !(q->region_flags[0] & 2u)) return 0;
    if ((q->anchors[1] & 1u) && !(q->region_flags[1] & 1u)) return 0;
    if ((q->anchors[1] & 2u) && !(q->region_flags[1] & 2u)) return 0;
    return 1;
}
static int history10_save5_quests_validate(const Save5Quests *q) {
    unsigned i;
    if (!q || !history10_quest_fields_validate(q)) return 0;
    for (i = 0; i < SAVE5_QUEST_CAPACITY; ++i)
        if (!history10_quest_objective_validate(q, i)) return 0;
    for (i = 0; i < 8; ++i) if (!history10_quest_reward_validate(q, i)) return 0;
    return 1;
}
static int history10_magma_quest_campaign_validate(const Save5Quests *q) {
    unsigned i;
    /* Revision5 owns separate room/source/repeat/discovery bytes. Every
     * durable step retains its entry and exact permanent visit prerequisites. */
    if (q->region_flags[3] || q->region_flags[9] || q->region_flags[16] || q->region_flags[19]) {
        if (save5_quest_state(q,24) != SAVE5_QUEST_CLAIMED || !(q->region_flags[3]&1u)) return 0;
    }
    for (i=30;i<38;++i) if (save5_quest_state(q,i) &&
        (!(q->region_flags[3]&1u) || save5_quest_state(q,24)!=SAVE5_QUEST_CLAIMED)) return 0;
    if (save5_quest_state(q,33) && save5_quest_state(q,30)!=SAVE5_QUEST_CLAIMED) return 0;
    if (save5_quest_state(q,37) && !has_all(q->objectives[32],3)) return 0;
    if (save5_quest_state(q,32) || (q->region_flags[3]&240u)) {
        if (save5_quest_state(q,30)!=SAVE5_QUEST_CLAIMED ||
            save5_quest_state(q,31)!=SAVE5_QUEST_CLAIMED) return 0;
    }
    for (i=5;i<8;++i) if ((q->region_flags[3]&(1u<<i)) &&
        !has_all(q->objectives[32],(1u<<(i-4))-1u)) return 0;
    { static const Save4U8 visits[7]={2,8,4,2,2,4,8};
      for(i=0;i<7;++i) if((q->region_flags[9]&(1u<<i)) && !(q->region_flags[3]&visits[i])) return 0; }
    if (q->region_flags[19] && !(q->region_flags[3]&8u)) return 0;
    if ((q->region_flags[9]&64u) && q->region_flags[19]!=7) return 0;
    if (q->region_flags[16] & ~q->region_flags[9]) return 0;
    return 1;
}
static int history10_quest_campaign_validate(const CampaignSave *c, const Save5Quests *q) {
    static const Save4U8 trial_recruit[5] = {11,12,14,15,13};
    unsigned room = c->room, i;
    unsigned harbor = save5_quest_state(q,11) == SAVE5_QUEST_CLAIMED &&
                      save5_quest_state(q,13) == SAVE5_QUEST_CLAIMED;
    if (q->region_flags[0] && !(c->chapter_flags & SAVE4_GROVE_CLEAR)) return 0;
    for (i = 0; i < 16; ++i)
        if (q->states[i] && (!(c->chapter_flags & SAVE4_GROVE_CLEAR) ||
                             !(q->region_flags[0] & 1u))) return 0;
    if (q->region_flags[1] && (!(c->chapter_flags & SAVE4_SKY_CLEAR) ||
                               !(q->region_flags[0] & 1u))) return 0;
    for (i = 11; i <= 21; ++i)
        if (save5_quest_state(q,i) && (!(c->chapter_flags & SAVE4_SKY_CLEAR) ||
                                      !(q->region_flags[1] & 1u))) return 0;
    if (save5_quest_state(q,13) && save5_quest_state(q,11) != SAVE5_QUEST_CLAIMED) return 0;
    for (i = 0; i < 5; ++i)
        if (save5_quest_state(q,16+i) &&
            save5_quest_state(q,trial_recruit[i]) != SAVE5_QUEST_CLAIMED) return 0;
    if (save5_quest_state(q,21) && !harbor) return 0;
    /* Visits are permanent proof of passing the same gates even when the
     * current checkpoint has returned to town. No objective or claim resets. */
    if ((q->region_flags[1] & 240u) && !harbor) return 0;
    if (((q->region_flags[1] >> 5) & 7u) & ~q->objectives[21]) return 0;
    /* Southern claims/visits never borrow legacy generic creature rewards. */
    if (q->region_flags[2] || q->region_flags[8] || q->region_flags[18]) {
        if (!(c->chapter_flags & SAVE4_SKY_CLEAR) || !(q->region_flags[0] & 1u) ||
            !(q->region_flags[1] & 1u) || save5_quest_state(q,21) != SAVE5_QUEST_CLAIMED ||
            !(q->region_flags[2] & 1u)) return 0;
    }
    for (i = 22; i < 30; ++i)
        if (save5_quest_state(q,i) && (!(q->region_flags[2] & 1u) ||
            save5_quest_state(q,21) != SAVE5_QUEST_CLAIMED)) return 0;
    {
        unsigned ready = save5_quest_state(q,22) == SAVE5_QUEST_CLAIMED &&
                         save5_quest_state(q,23) == SAVE5_QUEST_CLAIMED;
        if ((save5_quest_state(q,24) || (q->region_flags[2] & 240u)) && !ready) return 0;
        /* All required earlier objectives, not merely the last prefix bit. */
        for (i=5; i<8; ++i)
            if ((q->region_flags[2] & (1u<<i)) &&
                (q->objectives[24] & ((1u<<(i-4))-1u)) != ((1u<<(i-4))-1u)) return 0;
    }
    if (q->region_flags[18]) {
        if (!(q->region_flags[2] & 4u)) return 0;
        if ((q->region_flags[18] & 1u) && save5_quest_state(q,29) < SAVE5_QUEST_READY) return 0;
        if ((q->region_flags[18] & 2u) && save5_quest_state(q,28) < SAVE5_QUEST_READY) return 0;
    }
    {
        static const Save4U8 visit[8]={2,2,8,2,2,2,4,8};
        for (i=0;i<8;++i)
            if ((q->region_flags[8] & (1u<<i)) && !(q->region_flags[2] & visit[i])) return 0;
        if ((q->region_flags[8]&16u) && !(q->region_flags[18]&1u)) return 0;
        if ((q->region_flags[8]&64u) && !(q->region_flags[18]&2u)) return 0;
    }
    if(!history10_magma_quest_campaign_validate(q)||!history10_underwater_quest_campaign_validate(q)||!history10_return_quest_campaign_validate(q)||!history10_horizons_quest_campaign_validate(q)||!history10_covenants_quest_campaign_validate(c,q))return 0;
    if (room >=70 || (room==62&&c->spawn==5))return history10_covenants_campaign_validate(c,q);
    if (room >= 62)return history10_horizons_campaign_validate(c,q);
    if (room >= 54) {
        if(c->spawn==2 && room<=55 && !(q->anchors[5]&(1u<<(room-54))))return 0;
        return (q->region_flags[5]&(1u<<(room-54)))!=0;
    }
    if (room >= 46) {
        if(c->spawn==2 && room<=47 && !(q->anchors[4]&(1u<<(room-46))))return 0;
        return (q->region_flags[4]&(1u<<(room-46)))!=0;
    }
    if (room >= 38) {
        if(room==38 && c->spawn==4 && !(q->region_flags[4]&1u))return 0;
        if(c->spawn==3 && room<=39 && !(q->anchors[3]&(1u<<(room-38))))return 0;
        return (q->region_flags[3] & (1u << (room-38))) != 0;
    }
    if (room >= 30) {
        if (!(q->region_flags[2] & (1u << (room - 30)))) return 0;
        if (c->spawn == 2 && ((room == 30 && !(q->anchors[2] & 1u)) ||
                             (room == 31 && !(q->anchors[2] & 2u)))) return 0;
        return 1;
    }
    if (room >= 22) {
        /* Separate regional byte: never shift a campaign mask by room ID. */
        if (!(q->region_flags[1] & (1u << (room - 22)))) return 0;
        if (room >= 26 && !harbor) return 0;
        if (room >= 27 && !(q->objectives[21] & (1u << (room - 27)))) return 0;
        if (c->spawn == 2 && ((room == 22 && !(q->anchors[1] & 1u)) ||
                             (room == 23 && !(q->anchors[1] & 2u)))) return 0;
        return 1;
    }
    if (room < 16) return 1;
    if (!(q->region_flags[0] & (1u << (room - 16)))) return 0;
    if ((room == 18 || room == 19) && save5_quest_state(q, 2) != SAVE5_QUEST_CLAIMED) return 0;
    if (c->spawn == 2 && ((room == 16 && !(q->anchors[0] & 1u)) ||
                         (room == 17 && !(q->anchors[0] & 2u)))) return 0;
    return 1;
}
static unsigned history10_retained_creature_bits(const CreatureInstance *c) {
    unsigned owner, trial, level, bond, trained;
    switch (c->form_id) {
    case 13: case 14: case 15: return 1u;
    case 16: case 17: case 18: return 2u;
    case 19: case 20: case 21: owner=4; trial=32; level=16; bond=40; trained=256; break;
    case 22: case 23: case 24: owner=8; trial=64; level=17; bond=40; trained=512; break;
    case 73: case 74: owner=16; trial=128; level=18; bond=45; trained=1024; break;
    case 75: case 76: owner=32; trial=256; level=18; bond=45; trained=2048; break;
    case 77: case 78: owner=64; trial=512; level=20; bond=50; trained=4096; break;
    default: return 0;
    }
    if ((c->trial_flags & trial) && c->level >= level && c->bond >= bond) owner |= trained;
    return owner;
}
static unsigned history10_retained_creatures(const CreatureRoster *r) {
    unsigned i, mask = 0;
    for (i = 0; i < CREATURE_ROSTER_CAPACITY; ++i)
        mask |= history10_retained_creature_bits(&r->instances[i]);
    return mask;
}
static int history10_quest_creatures_validate(const Save5Quests *q, const Save4U8 *obtained,
                                    const Save4U8 *rewards, unsigned retained) {
    static const Save4U8 recruit_rewards[5]={7,8,11,9,10};
    static const Save4U8 recruit_masks[5]={4,8,64,16,32};
    unsigned i;
    if (save5_quest_state(q, 2) == SAVE5_QUEST_CLAIMED) {
        unsigned water = (history10_form_allowed(13) && (obtained[1] & 16u)) ||
                         (history10_form_allowed(14) && (obtained[1] & 32u)) ||
                         (history10_form_allowed(15) && (obtained[1] & 64u));
        if (!(rewards[0] & 16u) || !water || !(retained & 1u)) return 0;
    }
    if (save5_quest_state(q, 3) == SAVE5_QUEST_CLAIMED &&
        (!(rewards[0] & 32u) || (!history10_form_allowed(16) || (!(obtained[1] & 128u) && !(obtained[2] & 3u))) ||
         !(retained & 2u))) return 0;
    for (i=0; i<5; ++i) {
        unsigned reward=recruit_rewards[i]-1u;
        if (save5_quest_state(q,11+i)==SAVE5_QUEST_CLAIMED &&
            (!(retained & recruit_masks[i]) || !(rewards[reward>>3] & (1u<<(reward&7))))) return 0;
        if (save5_quest_state(q,16+i)==SAVE5_QUEST_CLAIMED && !(retained & (256u<<i))) return 0;
    }
    return 1;
}
static unsigned history10_southern_instance_evidence(const CreatureInstance *c) {
    static const Save4U8 forms[10]={79,85,25,28,81,83,87,89,91,93};
    static const Save4U8 levels[10]={20,20,20,22,22,22,24,22,24,22};
    static const Save4U8 bonds[10]={40,40,40,45,45,45,45,45,45,45};
    /* Explicit form-byte -> source-row+1. Zero means no Southern evidence;
     * bounds are checked before indexing. This preserves all256 byte inputs. */
    static const Save4U8 source_row[128]={
        [79]=1,[80]=1,[85]=2,[86]=2,[25]=3,[26]=3,[27]=3,[28]=4,[29]=4,[30]=4,
        [81]=5,[82]=5,[83]=6,[84]=6,[87]=7,[88]=7,[89]=8,[90]=8,
        [91]=9,[92]=9,[93]=10,[94]=10
    };
    unsigned i, result;
    /* Empty records still receive the complete zero-byte instance validation. */
    if (!c->form_id || c->form_id>=sizeof source_row) return 0;
    i=source_row[c->form_id];
    if (!i) return 0;
    --i;result=1u<<i;
    if (c->trial_flags || c->form_id!=forms[i]) {
        if (!(c->trial_flags&1u) || (c->trial_flags & ~(i==2||i==3?1025u:1u)) || c->level<levels[i] || c->bond<bonds[i]) return 0x80000000u;
        result|=1u<<(i+10);
    }
    return result;
}
static unsigned history10_southern_roster_evidence(const CreatureRoster *r) {
    unsigned i, evidence=0;
    for(i=0;i<CREATURE_ROSTER_CAPACITY;++i) evidence|=history10_southern_instance_evidence(&r->instances[i]);
    return evidence;
}
static int history10_southern_sources_validate(const Save5Quests *q, const Save4U8 *obtained,
                                      unsigned evidence) {
    static const Save4U8 forms[10]={79,85,25,28,81,83,87,89,91,93};
    unsigned i, sources=(unsigned)q->region_flags[8]<<2;
    if (evidence&0x80000000u) return 0;
    if (save5_quest_state(q,22)==SAVE5_QUEST_CLAIMED) sources|=1u;
    if (save5_quest_state(q,23)==SAVE5_QUEST_CLAIMED) sources|=2u;
    if ((sources & evidence)!=sources || ((evidence>>10)&~sources)) return 0;
    if ((evidence>>10) && (sources&3u)!=3u) return 0;
    for(i=0;i<10;++i) if(sources&(1u<<i)) {
        unsigned base=forms[i]-1u;
        if (!(obtained[base>>3]&(1u<<(base&7))) &&
            !(obtained[(base+1)>>3]&(1u<<((base+1)&7))) &&
            !((i==2||i==3) && (obtained[(base+2)>>3]&(1u<<((base+2)&7))))) return 0;
    }
    return 1;
}
static unsigned history10_magma_form_row(unsigned form) {
    if(form>=31 && form<=48)return (form-31)/3;
    if(form>=95 && form<=100)return 6+(form-95)/2;
    return 9;
}
static void history10_magma_instance_evidence(MagmaEvidence *e,const CreatureInstance *c) {
    unsigned i=history10_magma_form_row(c->form_id),delta;
    if(i==9)return;
    if(e->count[i]<2)++e->count[i];
    delta=c->form_id-history10_magma_bases[i];
    if(i>=2 && i<6 && delta)e->evolved_branches|=(Save4U8)(1u<<(i-2));
    if(c->trial_flags || delta) {
        e->ready=1;
        if(c->level<26 || c->bond<45)e->invalid=1;
    }
    if(i<2 && (c->trial_flags&2u)) {
        e->caldera=1;
        if(c->level<32 || c->bond<60 || !(c->trial_flags&1u))e->invalid=1;
    }
    if(delta) {
        unsigned required=i<2?(delta==2?3u:1u):i<6?(delta==2?2u:1u):1u;
        if(!has_all(c->trial_flags,required))e->invalid=1;
    }
}
static int history10_magma_sources_validate(const Save5Quests *q,const Save4U8 *obtained,
                                 const MagmaEvidence *e) {
    unsigned sources=(unsigned)q->region_flags[9]<<2,i,j;
    if(e->invalid)return 0;
    if(save5_quest_state(q,30)==SAVE5_QUEST_CLAIMED)sources|=1u;
    if(save5_quest_state(q,31)==SAVE5_QUEST_CLAIMED)sources|=2u;
    if(e->ready && (sources&3u)!=3u)return 0;
    if(e->caldera && save5_quest_state(q,32)!=SAVE5_QUEST_CLAIMED)return 0;
    for(i=0;i<9;++i) {
        unsigned history=0;
        if(!!e->count[i] != !!(sources&(1u<<i)))return 0;
        if(!(sources&(1u<<i)))continue;
        for(j=0;j<(i<6?3u:2u);++j) {
            unsigned f=history10_magma_bases[i]+j-1;
            history|=(obtained[f>>3]>>(f&7))&1u;
        }
        if(!history)return 0;
    }
    for(i=0;i<4;++i)if(q->region_flags[16]&(1u<<i)) {
        unsigned a=history10_magma_bases[i+2],history;
        history=((obtained[a>>3]>>(a&7))|(obtained[(a+1)>>3]>>((a+1)&7)))&1u;
        if(e->count[i+2]<2 || !(e->evolved_branches&(1u<<i)) || !history)return 0;
    }
    return 1;
}
static int history10_magma_roster_sources_validate(const Save5Quests *q,const CreatureRoster *r) {
    MagmaEvidence e;unsigned i;clear_bytes(&e,sizeof e);
    for(i=0;i<CREATURE_ROSTER_CAPACITY;++i)history10_magma_instance_evidence(&e,&r->instances[i]);
    return history10_magma_sources_validate(q,r->obtained,&e);
}
/* Revision6 causal rules are deliberately isolated from immutable r1..5.
 * None of these functions are used to reinterpret old bank fields. */
static int history10_underwater_quest_campaign_validate(const Save5Quests *q) {
 static const Save4U8 visits[6]={4,2,8,4,32,8};
 unsigned i;
 if(q->region_flags[4]||q->region_flags[10]||q->region_flags[17]||
    q->region_flags[20]||q->region_flags[21]){
  if(save5_quest_state(q,32)!=SAVE5_QUEST_CLAIMED||!(q->region_flags[4]&1u))return 0;
 }
 for(i=38;i<46;++i)if(save5_quest_state(q,i)&&
  (!(q->region_flags[4]&1u)||save5_quest_state(q,32)!=SAVE5_QUEST_CLAIMED))return 0;
 if(save5_quest_state(q,41)&&save5_quest_state(q,38)!=SAVE5_QUEST_CLAIMED)return 0;
 if(save5_quest_state(q,42)&&save5_quest_state(q,39)!=SAVE5_QUEST_CLAIMED)return 0;
 if(save5_quest_state(q,45)&&save5_quest_state(q,40)!=SAVE5_QUEST_CLAIMED)return 0;
 if(save5_quest_state(q,40)||(q->region_flags[4]&240u)){
  if(save5_quest_state(q,38)!=SAVE5_QUEST_CLAIMED||save5_quest_state(q,39)!=SAVE5_QUEST_CLAIMED)return 0;
 }
 for(i=5;i<8;++i)if((q->region_flags[4]&(1u<<i))&&
  !has_all(q->objectives[40],(1u<<(i-4))-1u))return 0;
 for(i=0;i<6;++i)if((q->region_flags[10]&(1u<<i))&&!(q->region_flags[4]&visits[i]))return 0;
 if(q->region_flags[20]&&!(q->region_flags[4]&32u))return 0;
 if(q->region_flags[21]&&!(q->region_flags[4]&8u))return 0;
 if((q->region_flags[10]&16u)&&q->region_flags[20]!=3)return 0;
 if((q->region_flags[10]&32u)&&q->region_flags[21]!=7)return 0;
 return 1;
}
static void history10_underwater_instance_evidence(UnderwaterEvidence *e,const CreatureInstance *c) {
 unsigned i,delta;
 if(c->form_id<49||c->form_id>72)return;
 i=(c->form_id-49)/3;delta=(c->form_id-49)%3;
 if(e->count[i]<2)++e->count[i];
 if(delta)e->terminals|=(Save4U8)(1u<<i);
 if(c->trial_flags||delta){
  e->trained=1;
  if(c->level<28||c->bond<45||(c->trial_flags&~3u)||
   (delta&&!(c->trial_flags&(1u<<(delta-1)))))e->invalid=1;
 }
}
static int history10_underwater_sources_validate(const Save5Quests *q,const Save4U8 *obtained,
 const UnderwaterEvidence *e) {
 unsigned sources=(unsigned)q->region_flags[10]<<2,i,j;
 if(e->invalid)return 0;
 if(save5_quest_state(q,38)==SAVE5_QUEST_CLAIMED)sources|=1u;
 if(save5_quest_state(q,39)==SAVE5_QUEST_CLAIMED)sources|=2u;
 if(e->trained&&(sources&3u)!=3u)return 0;
 for(i=0;i<8;++i){
  unsigned history=0,terminal_history=0;
  if(!!e->count[i]!=!!(sources&(1u<<i)))return 0;
  for(j=0;j<3;++j){unsigned f=48+3*i+j,seen=(obtained[f>>3]>>(f&7))&1u;
   history|=seen;if(j)terminal_history|=seen;}
  if((sources&(1u<<i))&&!history)return 0;
  if(q->region_flags[17]&(1u<<i)){
   if(e->count[i]<2||!(e->terminals&(1u<<i))||!terminal_history)return 0;
  }
 }
 return 1;
}
static int history10_underwater_roster_sources_validate(const Save5Quests *q,const CreatureRoster *r) {
 UnderwaterEvidence e;unsigned i;clear_bytes(&e,sizeof e);
 for(i=0;i<CREATURE_ROSTER_CAPACITY;++i)history10_underwater_instance_evidence(&e,&r->instances[i]);
 return history10_underwater_sources_validate(q,r->obtained,&e);
}

/* Current Return causal policy. Never called for revisions1..6. */
static int history10_return_quest_campaign_validate(const Save5Quests *q) {
 static const Save4U8 prerequisites[8][2]={{41,0},{47,0},{48,0},{47,0},{50,0},{49,51},{47,0},{48,50}};
 static const Save4U8 objective_visits[][3]={
  {47,2,2},
  {48,1,8},
  {48,2,8},
  {49,1,16},
  {49,2,16},
  {50,1,32},
  {50,2,4},
  {51,1,64},
  {51,2,64},
  {51,4,128},
  {52,2,8},
  {53,1,1},
  {53,2,4},
  {53,4,8},
  {53,8,16},
 };
 unsigned i,j;
 for(i=46;i<54;++i)if(save5_quest_state(q,i)){
  for(j=0;j<2;++j)if(prerequisites[i-46][j]&&save5_quest_state(q,prerequisites[i-46][j]-1u)!=SAVE5_QUEST_CLAIMED)return 0;
 }
 if(q->region_flags[5]||q->region_flags[11]||q->anchors[5]){
  if(save5_quest_state(q,46)!=SAVE5_QUEST_CLAIMED||!(q->region_flags[5]&1u))return 0;
 }
 if((q->region_flags[5]&36u)&&save5_quest_state(q,49)!=SAVE5_QUEST_CLAIMED)return 0;
 if((q->region_flags[5]&8u)&&save5_quest_state(q,47)!=SAVE5_QUEST_CLAIMED)return 0;
 if((q->region_flags[5]&192u)&&(save5_quest_state(q,48)!=SAVE5_QUEST_CLAIMED||save5_quest_state(q,50)!=SAVE5_QUEST_CLAIMED))return 0;
 for(i=0;i<sizeof objective_visits/sizeof objective_visits[0];++i)
  if((q->objectives[objective_visits[i][0]]&objective_visits[i][1])&&!(q->region_flags[5]&objective_visits[i][2]))return 0;
 return 1;
}
static void history10_return_instance_evidence(ReturnEvidence *e,const CreatureInstance *c) {
 unsigned family=history10_family(c->form_id),level=32,bond=60;
 if(family==39||family==40){
  unsigned i=family-39;
  if(e->count[i]<2)++e->count[i];
 }
 if((family>=1&&family<=10)||(family==39||family==40)){
  unsigned mask=c->trial_flags&3072u;
  if(!mask)return;
  e->trained=1;
  if((family==6&&!(mask&2048u))||family>=39){level=28;bond=45;}
  if(c->level<level||c->bond<bond)e->invalid=1;
 }
}
static int history10_return_sources_validate(const Save5Quests *q,const Save4U8 *obtained,const ReturnEvidence *e) {
 unsigned i;
 if(e->invalid||(e->trained&&save5_quest_state(q,46)!=SAVE5_QUEST_CLAIMED))return 0;
 for(i=0;i<2;++i){
  unsigned claimed=save5_quest_state(q,47+2*i)==SAVE5_QUEST_CLAIMED;
  unsigned base=100+2*i;
  unsigned history=((obtained[base>>3]>>(base&7))|(obtained[(base+1)>>3]>>((base+1)&7)))&1u;
  if(!!e->count[i]!=!!claimed||(claimed&&!history))return 0;
  /* The initial quest authorizes one real copy; additional retained copies
   * have exactly the repeat provenance. Counts never use history bits. */
  if(!!(q->region_flags[11]&(1u<<i))!=(e->count[i]>=2))return 0;
 }
 return 1;
}
static int history10_return_roster_sources_validate(const Save5Quests *q,const CreatureRoster *r) {
 ReturnEvidence e;unsigned i;clear_bytes(&e,sizeof e);
 for(i=0;i<CREATURE_ROSTER_CAPACITY;++i)history10_return_instance_evidence(&e,&r->instances[i]);
 return history10_return_sources_validate(q,r->obtained,&e);
}

/* Numeric content8 source policy. Every listed receipt owns retained identities;
 * nonauthoritative credit/history never authorizes an invitation or trial. */
static const Save4U8 history10_horizons_base_forms[12]={105,107,109,111,113,114,115,116,117,118,119,120};
static const Save4U8 history10_horizons_source_rooms[12]={62,63,66,68,63,64,65,67,69,66,62,68};
static const Save4U8 history10_horizons_quest_masks[6]={7,15,15,15,7,15};
static const Save4U8 history10_horizons_priors[6][2]={{52,0},{55,0},{55,0},{56,57},{55,0},{55,0}};
/* quest,bit,predecessors,area. Ordered invitation bits are included here, but
 * only the typed initial-source transaction can create those four bits. */
static const Save4U8 history10_horizons_objectives[][4]={
 {54,1,0,60},{54,2,1,62},{54,4,3,62},
 {55,1,0,63},{55,2,1,63},{55,4,3,64},{55,8,7,63},
 {56,1,0,65},{56,2,1,65},{56,4,3,66},{56,8,7,66},
 {57,1,0,67},{57,2,1,67},{57,4,3,68},{57,8,7,68},
 {58,1,0,64},{58,2,0,69},{58,4,3,65},
 {59,1,0,63},{59,2,0,66},{59,4,0,69},{59,8,7,60}
};
static int history10_horizons_visit(const Save5Quests*q,unsigned room){
 return room==60?!!(q->region_flags[5]&64u):room==61?!!(q->region_flags[5]&128u):
  room>=62&&room<=69?!!(q->region_flags[6]&(1u<<(room-62))):0;
}
static int history10_horizons_done(const Save5Quests*q,unsigned id){return save5_quest_state(q,id)==3;}
static unsigned history10_horizons_receipt(const Save5Quests*q,unsigned index,unsigned repeat){
 return (q->region_flags[(repeat?14:12)+(index>>3)]>>(index&7))&1u;
}
static int history10_horizons_objective_validate(const Save5Quests*q,unsigned id){
 unsigned state,mask,bits,i;if(id<54||id>59)return 0;
 state=save5_quest_state(q,id);mask=history10_horizons_quest_masks[id-54];bits=q->objectives[id];
 if(bits&~mask||(!state&&bits)||(state==1&&bits==mask)||(state>=2&&bits!=mask))return 0;
 for(i=0;i<sizeof history10_horizons_objectives/sizeof history10_horizons_objectives[0];++i){
  const Save4U8*p=history10_horizons_objectives[i];
  if(p[0]==id&&(bits&p[1])&&(bits&p[2])!=p[2])return 0;
 }
 return 1;
}
static int history10_horizons_quest_campaign_validate(const Save5Quests*q){
 unsigned i,j,v=q->region_flags[6];
 for(i=54;i<60;++i)if(save5_quest_state(q,i)){
  for(j=0;j<2;++j)if(history10_horizons_priors[i-54][j]&&!history10_horizons_done(q,history10_horizons_priors[i-54][j]-1u))return 0;
 }
 if(v||q->anchors[6]||q->region_flags[12]||q->region_flags[13]||q->region_flags[14]||q->region_flags[15]){
  if(!history10_horizons_done(q,51)||!(v&1u))return 0;
 }
 if((v&254u)&&!history10_horizons_done(q,54))return 0;
 if((v&96u)&&(!history10_horizons_done(q,55)||!history10_horizons_done(q,56)))return 0;
 if((q->anchors[6]&1u)&&!(v&1u))return 0;
 if((q->anchors[6]&2u)&&(!(v&8u)||!history10_horizons_done(q,54)))return 0;
 for(i=0;i<sizeof history10_horizons_objectives/sizeof history10_horizons_objectives[0];++i){
  const Save4U8*p=history10_horizons_objectives[i];
  if((q->objectives[p[0]]&p[1])&&!history10_horizons_visit(q,p[3]))return 0;
 }
 for(i=0;i<12;++i){
  unsigned initial=history10_horizons_receipt(q,i,0);
  if(i<4&&initial!=!!(q->objectives[54+i]&(i?8u:4u)))return 0;
  if(initial&&(!history10_horizons_visit(q,history10_horizons_source_rooms[i])||(i>=4&&!history10_horizons_done(q,54))))return 0;
  if(history10_horizons_receipt(q,i,1)&&(!initial||!history10_horizons_done(q,i<4?54+i:54)))return 0;
 }
 return 1;
}
static int history10_horizons_campaign_validate(const CampaignSave*c,const Save5Quests*q){
 static const Save4U8 counts[8]={5,4,2,4,3,4,1,2};
 static const Save4U8 inbound[8][5]={{61,63,66,64,62},{62,65,64,67,0},{63,62,0,0,0},
  {63,66,67,65,0},{65,62,69,0,0},{63,65,68,69,0},{67,0,0,0,0},{66,67,0,0,0}};
 unsigned r=c->room,s=c->spawn;if(r<62||r>69||s>=counts[r-62]||!history10_horizons_visit(q,r)||!history10_horizons_visit(q,inbound[r-62][s]))return 0;
 if(!history10_horizons_done(q,51))return 0;
 if((r!=62||(s>=1&&s<=3))&&!history10_horizons_done(q,54))return 0;
 if((r==67||r==68||(r==63&&s==3)||(r==65&&s==2)||(r==69&&s==1))&&
  (!history10_horizons_done(q,55)||!history10_horizons_done(q,56)))return 0;
 if(((r==67&&s==3)||(r==69&&s==1))&&!history10_horizons_done(q,57))return 0;
 if(r==62&&s==4&&!(q->anchors[6]&1u))return 0;
 if(r==65&&s==3&&!(q->anchors[6]&2u))return 0;
 return 1;
}
static void history10_horizons_instance_evidence(HorizonsEvidence*e,const CreatureInstance*c){
 unsigned family=history10_family(c->form_id),i;
 if(family<41||family>52)return;
 i=family-41;
 if(e->count[i]<2)++e->count[i];
 if(c->trial_flags){e->trained=1;if(family>44||c->trial_flags!=1024||c->level<34||c->bond<60)e->invalid=1;}
}
static int history10_horizons_sources_validate(const Save5Quests*q,const Save4U8*obtained,const HorizonsEvidence*e){
 unsigned i;if(e->invalid||(e->trained&&!history10_horizons_done(q,54)))return 0;
 for(i=0;i<12;++i){
  unsigned base=history10_horizons_base_forms[i]-1u,initial=history10_horizons_receipt(q,i,0),repeat=history10_horizons_receipt(q,i,1);
  if(initial!=!!e->count[i]||repeat!=(e->count[i]>=2))return 0;
  if(initial&&!(obtained[base>>3]&(1u<<(base&7))))return 0;
  /* New families have no release path: acquired history cannot exist without
   * their first real invitation. Seen-only encounter history remains legal. */
  if(!initial&&((obtained[base>>3]&(1u<<(base&7)))||
    (i<4&&(obtained[(base+1)>>3]&(1u<<((base+1)&7))))))return 0;
 }
 return 1;
}
static int history10_horizons_roster_sources_validate(const Save5Quests*q,const CreatureRoster*r){
 HorizonsEvidence e;unsigned i;clear_bytes(&e,sizeof e);
 for(i=0;i<160;++i)history10_horizons_instance_evidence(&e,&r->instances[i]);
 return history10_horizons_sources_validate(q,r->obtained,&e);
}

/* Unique covenant rights and invitation receipts are separate causal facts.
 * Seen-only discovery is legal; obtained always has exactly one retained owner. */
static int history10_covenant_done(const Save5Quests*q,unsigned quest){return save5_quest_state(q,quest)==3;}
static int history10_covenant_visit(const Save5Quests*q,unsigned room){
 return room==0?1:room==62?!!(q->region_flags[6]&1u):room>=70&&room<=77?!!(q->region_flags[7]&(1u<<(room-70))):0;
}
static int history10_covenant_entry(const CampaignSave*c,const Save5Quests*q){
 return (c->chapter_flags&SAVE4_ENDING_SEEN)&&history10_covenant_done(q,57)&&(q->objectives[60]&3u)==3u;
}
static int history10_covenants_objective_validate(const Save5Quests*q,unsigned quest){
 unsigned state,mask,bits;if(quest<60||quest>63)return 0;
 state=save5_quest_state(q,quest);bits=q->objectives[quest];mask=(quest==60||quest==63)?7u:15u;
 if(bits&~mask||(!state&&bits)||(state==1&&bits==mask)||(state>=2&&bits!=mask))return 0;
 return (quest==61||quest==62)||!(bits&(bits+1u));
}
static int history10_covenants_quest_campaign_validate(const CampaignSave*c,const Save5Quests*q){
 unsigned i,v=q->region_flags[7],rights=q->region_flags[22],receipts=q->region_flags[23];
 if(save5_quest_state(q,60)&&(!(c->chapter_flags&SAVE4_ENDING_SEEN)||!history10_covenant_done(q,57)))return 0;
 if((q->objectives[60]&2u)&&!history10_covenant_visit(q,62))return 0;
 if((q->objectives[60]&4u)&&!(v&1u))return 0;
 if((v||q->anchors[7]||rights||receipts)&&(!(v&1u)||!history10_covenant_entry(c,q)))return 0;
 if((v&14u)&&!history10_covenant_done(q,60))return 0;
 if((v&240u)&&(!(v&16u)||!history10_covenant_done(q,61)))return 0;
 if((q->anchors[7]&1u)&&!(v&1u))return 0;
 if((q->anchors[7]&2u)&&(!(v&16u)||!history10_covenant_done(q,61)))return 0;
 if(save5_quest_state(q,61)&&(!history10_covenant_done(q,60)||!(v&1u)))return 0;
 if(save5_quest_state(q,62)&&(!history10_covenant_done(q,61)||!(v&16u)))return 0;
 if(save5_quest_state(q,63)&&(!history10_covenant_done(q,61)||!history10_covenant_done(q,62)||!(v&1u)))return 0;
 if((q->objectives[63]&2u)&&!history10_covenant_visit(q,62))return 0;
 if(rights!=((unsigned)q->objectives[61]|((unsigned)q->objectives[62]<<4))||(receipts&~rights))return 0;
 for(i=0;i<8;++i)if((rights&(1u<<i))&&(!(v&(1u<<i))||!history10_covenant_done(q,i<4?60:61)))return 0;
 return 1;
}
static int history10_covenants_campaign_validate(const CampaignSave*c,const Save5Quests*q){
 static const Save4U8 counts[8]={5,2,2,2,4,2,2,2};
 static const Save4U8 inbound[8][5]={{62,71,73,74,70},{70,72,0,0,0},{71,73,0,0,0},{72,70,0,0,0},
  {70,75,77,74,0},{74,76,0,0,0},{75,77,0,0,0},{76,74,0,0,0}};
 unsigned r=c->room,s=c->spawn;
 if(r==62&&s==5)return history10_covenant_entry(c,q)&&history10_covenant_visit(q,62)&&history10_covenant_visit(q,70);
 if(r<70||r>77||s>=counts[r-70]||!history10_covenant_entry(c,q)||!history10_covenant_visit(q,r)||!history10_covenant_visit(q,inbound[r-70][s]))return 0;
 if(r>=71&&r<=73&&!history10_covenant_done(q,60))return 0;
 if((r>=74||(r==70&&s==3))&&!history10_covenant_done(q,61))return 0;
 if(r==70&&s==4&&!(q->anchors[7]&1u))return 0;
 if(r==74&&s==3&&!(q->anchors[7]&2u))return 0;
 return 1;
}
static void history10_covenants_instance_evidence(CovenantsEvidence*e,const CreatureInstance*c){
 unsigned i;if(c->form_id<121||c->form_id>128)return;i=c->form_id-121;
 if(e->count[i]<2)++e->count[i];
}
static int history10_covenants_sources_validate(const Save5Quests*q,const Save4U8*obtained,const CovenantsEvidence*e){
 unsigned i;for(i=0;i<8;++i){unsigned receipt=(q->region_flags[23]>>i)&1u;
  if(e->count[i]!=receipt||!!(obtained[15]&(1u<<i))!=receipt)return 0;
 }return 1;
}
static int history10_covenants_roster_sources_validate(const Save5Quests*q,const CreatureRoster*r){
 CovenantsEvidence e;unsigned i;clear_bytes(&e,sizeof e);
 for(i=0;i<160;++i)history10_covenants_instance_evidence(&e,&r->instances[i]);
 return history10_covenants_sources_validate(q,r->obtained,&e);
}

static int history10_economy_validate(const EconomyState*e,unsigned chapters){
 unsigned i,spent;
 if(!e||e->gold>9999||e->upgrade>1||e->relics>7||e->boss_claims!=e->relics||
    (e->relics&~chapters)||e->earned<e->spent||e->earned-e->spent!=e->gold)return 0;
 if(e->later_claims||!zero_bytes(e->reserved,8))return 0;
 for(i=0;i<2;++i)if(e->used[i]>e->bought[i]||e->supplies[i]>9||
    (unsigned)(e->bought[i]-e->used[i])!=e->supplies[i])return 0;
 spent=(unsigned)e->bought[0]*18u+(unsigned)e->bought[1]*24u+(unsigned)e->upgrade*120u;
 return e->spent==spent&&e->earned>=((e->relics&1u)?60u:0u)+
   ((e->relics&2u)?100u:0u)+((e->relics&4u)?160u:0u);
}
