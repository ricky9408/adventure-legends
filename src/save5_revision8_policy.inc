/* Immutable exact Horizons C content8 validator. Frozen before content9 expansion.
 * Preserve these numeric checks and their fixed historical dependencies.
 * Source: tests/fixtures/horizons-c-policy-oracle/manifest.json. */
static const Save4U8 history8_quest_masks[60] = {7,3,7,7,3,1,1,1,3,7,1,3,7,3,7,7,3,7,7,3,7,15,3,3,15,7,3,3,3,3,3,3,15,7,3,3,3,7,3,3,15,7,3,3,3,7,3,7,7,7,7,15,7,15,7,15,15,15,7,15};
static int history8_save5_campaign_validate(const CampaignSave *s) {
    Save4U32 f;
    if (!s) return 0;
    f = s->room_flags;
    unsigned chapter = s->chapter_flags, seen = s->story_seen;
    if ((s->room > 13 && (s->room < 16 || s->room > 69)) ||
        s->spawn > SAVE4_SPAWN_WEST_TRAIL ||
        s->bridge > 1 || s->torches > 3 || s->relic > 1 || s->camp > 1 ||
        s->optional_flags > 1 || (seen & ~0x7Fu) || (f & ~0xFFFFu)) return 0;
    if (chapter != 0 && chapter != 1 && chapter != 3 && chapter != 7 && chapter != 15)
        return 0;
    if (s->spirit > 3 || !(save4_unlock_mask(chapter) & (1u << s->spirit))) return 0;
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
    if (s->room >= 62) {
        static const Save4U8 spawns[8]={31,15,3,15,7,15,1,3};
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
    if (!has_all(f, entry_requirements(s->room))) return 0;
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
        if (!has_all(f, north_requirements(s->room))) return 0;
    }
    return 1;
}
static unsigned history8_quest_objective_mask(unsigned id) {
    return id < sizeof history8_quest_masks ? history8_quest_masks[id] : 0;
}
static int history8_quest_objective_validate(const Save5Quests *q, unsigned id) {
    unsigned state = save5_quest_state(q, id), mask = history8_quest_objective_mask(id);
    unsigned objectives = q->objectives[id];
    if(id>=54&&id<60)return history8_horizons_objective_validate(q,id);
    if (!mask) return !state && !objectives;
    if (objectives & ~mask) return 0;
    /* Beacon stages are monotonic prefixes: 0,1,3,7,15 only. */
    if ((id == 21 || id == 24 || id == 32 || id == 40) && (objectives & (objectives + 1u))) return 0;
    if (state == SAVE5_QUEST_INACTIVE) return !objectives;
    if (state == SAVE5_QUEST_ACTIVE) return objectives != mask;
    return objectives == mask;
}
static int history8_quest_fields_validate(const Save5Quests *q) {
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
        (q->region_flags[6] && !(q->region_flags[6]&1u)) || q->region_flags[7] || (q->region_flags[9] & ~127u) ||
        (q->region_flags[10] & ~63u) || (q->region_flags[11] & ~3u) || (q->region_flags[13]&~15u) || (q->region_flags[15]&~15u) ||
        (q->region_flags[16] & ~15u) || (q->region_flags[18] & ~3u) ||
        (q->region_flags[19] & ~7u) || (q->region_flags[19] & (q->region_flags[19]+1u)) ||
        (q->region_flags[20] & ~3u) || (q->region_flags[20] & (q->region_flags[20]+1u)) ||
        (q->region_flags[21] & ~7u) || (q->region_flags[21] & (q->region_flags[21]+1u)) ||
        !zero_bytes(q->region_flags + 22, 10) ||
        (q->anchors[0] & ~3u) || (q->anchors[1] & ~3u) ||
        (q->anchors[2] & ~3u) || (q->anchors[3] & ~3u) ||
        (q->anchors[4] & ~3u) || (q->anchors[5] & ~3u) || (q->anchors[6]&~3u) || !zero_bytes(q->anchors + 7, 9)) return 0;
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
static int history8_quest_campaign_validate(const CampaignSave *c, const Save5Quests *q) {
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
    if(!magma_quest_campaign_validate(q)||!underwater_quest_campaign_validate(q)||!return_quest_campaign_validate(q)||!history8_horizons_quest_campaign_validate(q))return 0;
    if (room >= 62)return history8_horizons_campaign_validate(c,q);
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
static int history8_quest_creatures_validate(const Save5Quests *q, const Save4U8 *obtained,
                                    const Save4U8 *rewards, unsigned retained) {
    static const Save4U8 recruit_rewards[5]={7,8,11,9,10};
    static const Save4U8 recruit_masks[5]={4,8,64,16,32};
    unsigned i;
    if (save5_quest_state(q, 2) == SAVE5_QUEST_CLAIMED) {
        unsigned water = (creatures_form_allowed_revision(13,8) && (obtained[1] & 16u)) ||
                         (creatures_form_allowed_revision(14,8) && (obtained[1] & 32u)) ||
                         (creatures_form_allowed_revision(15,8) && (obtained[1] & 64u));
        if (!(rewards[0] & 16u) || !water || !(retained & 1u)) return 0;
    }
    if (save5_quest_state(q, 3) == SAVE5_QUEST_CLAIMED &&
        (!(rewards[0] & 32u) || (!creatures_form_allowed_revision(16,8) || (!(obtained[1] & 128u) && !(obtained[2] & 3u))) ||
         !(retained & 2u))) return 0;
    for (i=0; i<5; ++i) {
        unsigned reward=recruit_rewards[i]-1u;
        if (save5_quest_state(q,11+i)==SAVE5_QUEST_CLAIMED &&
            (!(retained & recruit_masks[i]) || !(rewards[reward>>3] & (1u<<(reward&7))))) return 0;
        if (save5_quest_state(q,16+i)==SAVE5_QUEST_CLAIMED && !(retained & (256u<<i))) return 0;
    }
    return 1;
}
