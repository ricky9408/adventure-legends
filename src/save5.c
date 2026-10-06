#include "save5.h"

typedef char save5_u32_width[(sizeof(Save4U32) == 4) ? 1 : -1];
typedef char save5_instance_width[(sizeof(CreatureInstance) == 24) ? 1 : -1];
typedef char save5_quest_width[(sizeof(Save5Quests) == 264) ? 1 : -1];
typedef char save5_equipment_width[(sizeof(EquipmentState) == 512) ? 1 : -1];
typedef char save5_state_fits[(sizeof(Save5State) <= SAVE5_RESERVED_OFFSET) ? 1 : -1];
typedef char save5_state_word_size[(sizeof(Save5State) % 4 == 0) ? 1 : -1];
typedef Save4U32 Save5AliasU32 __attribute__((__may_alias__));

/* Exactly one full-size static EWRAM scratch allocation. While scanning old
 * banks, its always-zero trailing reserve temporarily holds 160 instance IDs.
 * That region is cleared before the snapshot CRC or first SRAM write. */
static union { Save4U8 bytes[SAVE5_BANK_SIZE]; Save5State state; } scratch;
static const Save4U32 crc_table[256] = {
    0x00000000u, 0x77073096u, 0xEE0E612Cu, 0x990951BAu, 0x076DC419u, 0x706AF48Fu, 0xE963A535u, 0x9E6495A3u,
    0x0EDB8832u, 0x79DCB8A4u, 0xE0D5E91Eu, 0x97D2D988u, 0x09B64C2Bu, 0x7EB17CBDu, 0xE7B82D07u, 0x90BF1D91u,
    0x1DB71064u, 0x6AB020F2u, 0xF3B97148u, 0x84BE41DEu, 0x1ADAD47Du, 0x6DDDE4EBu, 0xF4D4B551u, 0x83D385C7u,
    0x136C9856u, 0x646BA8C0u, 0xFD62F97Au, 0x8A65C9ECu, 0x14015C4Fu, 0x63066CD9u, 0xFA0F3D63u, 0x8D080DF5u,
    0x3B6E20C8u, 0x4C69105Eu, 0xD56041E4u, 0xA2677172u, 0x3C03E4D1u, 0x4B04D447u, 0xD20D85FDu, 0xA50AB56Bu,
    0x35B5A8FAu, 0x42B2986Cu, 0xDBBBC9D6u, 0xACBCF940u, 0x32D86CE3u, 0x45DF5C75u, 0xDCD60DCFu, 0xABD13D59u,
    0x26D930ACu, 0x51DE003Au, 0xC8D75180u, 0xBFD06116u, 0x21B4F4B5u, 0x56B3C423u, 0xCFBA9599u, 0xB8BDA50Fu,
    0x2802B89Eu, 0x5F058808u, 0xC60CD9B2u, 0xB10BE924u, 0x2F6F7C87u, 0x58684C11u, 0xC1611DABu, 0xB6662D3Du,
    0x76DC4190u, 0x01DB7106u, 0x98D220BCu, 0xEFD5102Au, 0x71B18589u, 0x06B6B51Fu, 0x9FBFE4A5u, 0xE8B8D433u,
    0x7807C9A2u, 0x0F00F934u, 0x9609A88Eu, 0xE10E9818u, 0x7F6A0DBBu, 0x086D3D2Du, 0x91646C97u, 0xE6635C01u,
    0x6B6B51F4u, 0x1C6C6162u, 0x856530D8u, 0xF262004Eu, 0x6C0695EDu, 0x1B01A57Bu, 0x8208F4C1u, 0xF50FC457u,
    0x65B0D9C6u, 0x12B7E950u, 0x8BBEB8EAu, 0xFCB9887Cu, 0x62DD1DDFu, 0x15DA2D49u, 0x8CD37CF3u, 0xFBD44C65u,
    0x4DB26158u, 0x3AB551CEu, 0xA3BC0074u, 0xD4BB30E2u, 0x4ADFA541u, 0x3DD895D7u, 0xA4D1C46Du, 0xD3D6F4FBu,
    0x4369E96Au, 0x346ED9FCu, 0xAD678846u, 0xDA60B8D0u, 0x44042D73u, 0x33031DE5u, 0xAA0A4C5Fu, 0xDD0D7CC9u,
    0x5005713Cu, 0x270241AAu, 0xBE0B1010u, 0xC90C2086u, 0x5768B525u, 0x206F85B3u, 0xB966D409u, 0xCE61E49Fu,
    0x5EDEF90Eu, 0x29D9C998u, 0xB0D09822u, 0xC7D7A8B4u, 0x59B33D17u, 0x2EB40D81u, 0xB7BD5C3Bu, 0xC0BA6CADu,
    0xEDB88320u, 0x9ABFB3B6u, 0x03B6E20Cu, 0x74B1D29Au, 0xEAD54739u, 0x9DD277AFu, 0x04DB2615u, 0x73DC1683u,
    0xE3630B12u, 0x94643B84u, 0x0D6D6A3Eu, 0x7A6A5AA8u, 0xE40ECF0Bu, 0x9309FF9Du, 0x0A00AE27u, 0x7D079EB1u,
    0xF00F9344u, 0x8708A3D2u, 0x1E01F268u, 0x6906C2FEu, 0xF762575Du, 0x806567CBu, 0x196C3671u, 0x6E6B06E7u,
    0xFED41B76u, 0x89D32BE0u, 0x10DA7A5Au, 0x67DD4ACCu, 0xF9B9DF6Fu, 0x8EBEEFF9u, 0x17B7BE43u, 0x60B08ED5u,
    0xD6D6A3E8u, 0xA1D1937Eu, 0x38D8C2C4u, 0x4FDFF252u, 0xD1BB67F1u, 0xA6BC5767u, 0x3FB506DDu, 0x48B2364Bu,
    0xD80D2BDAu, 0xAF0A1B4Cu, 0x36034AF6u, 0x41047A60u, 0xDF60EFC3u, 0xA867DF55u, 0x316E8EEFu, 0x4669BE79u,
    0xCB61B38Cu, 0xBC66831Au, 0x256FD2A0u, 0x5268E236u, 0xCC0C7795u, 0xBB0B4703u, 0x220216B9u, 0x5505262Fu,
    0xC5BA3BBEu, 0xB2BD0B28u, 0x2BB45A92u, 0x5CB36A04u, 0xC2D7FFA7u, 0xB5D0CF31u, 0x2CD99E8Bu, 0x5BDEAE1Du,
    0x9B64C2B0u, 0xEC63F226u, 0x756AA39Cu, 0x026D930Au, 0x9C0906A9u, 0xEB0E363Fu, 0x72076785u, 0x05005713u,
    0x95BF4A82u, 0xE2B87A14u, 0x7BB12BAEu, 0x0CB61B38u, 0x92D28E9Bu, 0xE5D5BE0Du, 0x7CDCEFB7u, 0x0BDBDF21u,
    0x86D3D2D4u, 0xF1D4E242u, 0x68DDB3F8u, 0x1FDA836Eu, 0x81BE16CDu, 0xF6B9265Bu, 0x6FB077E1u, 0x18B74777u,
    0x88085AE6u, 0xFF0F6A70u, 0x66063BCAu, 0x11010B5Cu, 0x8F659EFFu, 0xF862AE69u, 0x616BFFD3u, 0x166CCF45u,
    0xA00AE278u, 0xD70DD2EEu, 0x4E048354u, 0x3903B3C2u, 0xA7672661u, 0xD06016F7u, 0x4969474Du, 0x3E6E77DBu,
    0xAED16A4Au, 0xD9D65ADCu, 0x40DF0B66u, 0x37D83BF0u, 0xA9BCAE53u, 0xDEBB9EC5u, 0x47B2CF7Fu, 0x30B5FFE9u,
    0xBDBDF21Cu, 0xCABAC28Au, 0x53B39330u, 0x24B4A3A6u, 0xBAD03605u, 0xCDD70693u, 0x54DE5729u, 0x23D967BFu,
    0xB3667A2Eu, 0xC4614AB8u, 0x5D681B02u, 0x2A6F2B94u, 0xB40BBE37u, 0xC30C8EA1u, 0x5A05DF1Bu, 0x2D02EF8Du,
};
#define SKY_PATH (SAVE4_SKY_BRIDGE | SAVE4_SKY_VANE)
#define SKY_PATROL (SKY_PATH | SAVE4_SKY_PATROL_CLEAR)
#define SKY_ALL (SKY_PATROL | SAVE4_RELAY_LEFT | SAVE4_RELAY_RIGHT | SAVE4_RELAY_FIRE)
#define CORE_WEIGHTS (SAVE4_CORE_PATH_OPEN | SAVE4_WEIGHT_WEST | SAVE4_WEIGHT_EAST)
#define CORE_ROOTS (CORE_WEIGHTS | SAVE4_WELL_UNCAPPED | SAVE4_ROOT_CHANNEL | SAVE4_THORNS_BURNED)
#define ALL_LAMPS (SAVE4_LAMP_FIRE | SAVE4_LAMP_NATURE | SAVE4_LAMP_WIND | SAVE4_LAMP_STONE)


#ifdef SAVE5_HOST_TEST
Save4U8 save5_test_sram[32768];
static int test_limit = -1, test_corrupt_index = -1;
static unsigned test_writes, test_step_work;
static Save4U8 test_corrupt_mask;
#define SRAM save5_test_sram
void save5_test_fail_after(int count) { test_limit = count; test_writes = 0; }
unsigned save5_test_write_count(void) { return test_writes; }
void save5_test_corrupt_write(int index, Save4U8 mask) {
    test_corrupt_index = index; test_corrupt_mask = mask;
}
unsigned save5_test_step_work(void) { return test_step_work; }
#else
#define SRAM ((volatile Save4U8 *)0x0E000000)
#endif
static int write_byte(unsigned offset, Save4U8 value) {
#ifdef SAVE5_HOST_TEST
    if (test_limit >= 0 && test_writes >= (unsigned)test_limit) return 0;
    if (test_corrupt_index >= 0 && test_writes == (unsigned)test_corrupt_index)
        value ^= test_corrupt_mask;
    ++test_writes;
#endif
    SRAM[offset] = value;
    return 1;
}
static void clear_bytes(void *dst, unsigned length) {
    Save4U8 *p = (Save4U8 *)dst;
    while (length--) *p++ = 0;
}
static void copy_state(Save5State *dst, const Save5State *src) {
    unsigned i;
    /* Runtime snapshot only: never writes a raw struct to SRAM. Both pointers
     * are naturally word aligned; all wire output still uses encode_*(). */
    for (i = 0; i < sizeof(*dst) / 4; ++i)
        ((Save5AliasU32 *)dst)[i] = ((const Save5AliasU32 *)src)[i];
}
static void copy_bytes(void *dst, const void *src, unsigned length) {
    Save4U8 *d = (Save4U8 *)dst;
    const Save4U8 *s = (const Save4U8 *)src;
    while (length--) *d++ = *s++;
}
static int zero_bytes(const Save4U8 *p, unsigned length) {
    while (length--) if (*p++) return 0;
    return 1;
}
static Save4U16 get16(const Save4U8 *p) {
    return (Save4U16)((unsigned)p[0] | ((unsigned)p[1] << 8));
}
static Save4U32 get32(const Save4U8 *p) {
    return (Save4U32)p[0] | ((Save4U32)p[1] << 8) |
           ((Save4U32)p[2] << 16) | ((Save4U32)p[3] << 24);
}
static void put16(Save4U8 *p, unsigned value) {
    p[0] = (Save4U8)value; p[1] = (Save4U8)(value >> 8);
}
static void put32(Save4U8 *p, Save4U32 value) {
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (Save4U8)(value >> (8 * i));
}
static Save4U32 crc_byte(Save4U32 crc, Save4U8 value) {
    return crc_table[(crc ^ value) & 255u] ^ (crc >> 8);
}
Save4U32 save5_crc32(const Save4U8 *bytes, unsigned length) {
    Save4U32 crc = 0xFFFFFFFFu;
    while (length--) crc = crc_byte(crc, *bytes++);
    return ~crc;
}
static int has_all(Save4U32 flags, Save4U32 required) {
    return (flags & required) == required;
}

/* Access to each new room is cumulative. The first chapter remains compatible
 * with every state accepted by the exact v2/v3 validators: old completed saves
 * may legitimately contain odd-looking bridge/torch bytes, and remain earned. */
static Save4U32 entry_requirements(unsigned room) {
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

/* A north-side spawn records a return from beyond this room's north gate.
 * Require the same permanent prerequisites as that trip, rather than letting
 * a malformed checkpoint resume past a closed bridge or root gap. */
static Save4U32 north_requirements(unsigned room) {
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

int save5_campaign_validate(const CampaignSave *s) {
    Save4U32 f;
    if (!s) return 0;
    f = s->room_flags;
    unsigned chapter = s->chapter_flags, seen = s->story_seen;
    if ((s->room > 13 && (s->room < 16 || s->room > 29)) ||
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

static void normalize_resume(CampaignSave *s, unsigned revision) {
    if (((s->chapter_flags & SAVE4_CORE_CLEAR) &&
         (revision == 1 || !(s->chapter_flags & SAVE4_ENDING_SEEN))) ||
        ((s->chapter_flags & SAVE4_SKY_CLEAR) && !(s->story_seen & SAVE4_SEEN_STONE_JOIN)) ||
        ((s->chapter_flags & SAVE4_GROVE_CLEAR) && !(s->story_seen & SAVE4_SEEN_WIND_JOIN))) {
        s->room = 0; s->spawn = SAVE4_SPAWN_ELDER;
    }
}
static void encode_campaign(Save4U8 *b, const CampaignSave *s) {
    b[0] = s->room; b[1] = s->spawn; b[2] = s->chapter_flags;
    b[3] = s->bridge; b[4] = s->torches; b[5] = s->relic;
    b[6] = s->camp; b[7] = s->optional_flags; put32(b + 8, s->room_flags);
    put16(b + 12, s->story_seen); b[14] = s->spirit;
}
static void decode_campaign(CampaignSave *s, const Save4U8 *b) {
    clear_bytes(s, sizeof *s);
    s->room = b[0]; s->spawn = b[1]; s->chapter_flags = b[2];
    s->bridge = b[3]; s->torches = b[4]; s->relic = b[5];
    s->camp = b[6]; s->optional_flags = b[7]; s->room_flags = get32(b + 8);
    s->story_seen = get16(b + 12); s->spirit = b[14]; s->loaded_version = 5;
}
static void encode_instance(Save4U8 *b, const CreatureInstance *s) {
    b[0] = s->form_id; b[1] = s->flags; b[2] = s->level; b[3] = s->bond;
    put32(b + 4, s->xp); put32(b + 8, s->instance_id);
    put16(b + 12, s->nickname_id); put16(b + 14, s->trial_flags);
    b[16] = s->equipped[0]; b[17] = s->equipped[1];
    b[18] = s->polarity; b[19] = s->selected_command;
    put32(b + 20, s->cosmetic_seed);
}
static void decode_instance(CreatureInstance *s, const Save4U8 *b) {
    s->form_id = b[0]; s->flags = b[1]; s->level = b[2]; s->bond = b[3];
    s->xp = get32(b + 4); s->instance_id = get32(b + 8);
    s->nickname_id = get16(b + 12); s->trial_flags = get16(b + 14);
    s->equipped[0] = b[16]; s->equipped[1] = b[17];
    s->polarity = b[18]; s->selected_command = b[19];
    s->cosmetic_seed = get32(b + 20);
}
/* Authored quest policy. Disabled IDs and all unassigned fields stay zero;
 * room/event handlers cannot turn reserved bits into implicit content. */
/* assets/region/contract.json schema1. Keep identities stable; rooms14/15
 * remain the separate personal trials and are not regional checkpoints. */
static const Save4U8 quest_masks[22] = {7,3,7,7,3,1,1,1,3,7,1,3,7,3,7,7,3,7,7,3,7,15};
static const signed char equipment_source_quest[19] = {-1,7,-1,6,-1,4,0,8,1,9,5,10,6,16,17,18,19,19,20};
static unsigned quest_objective_mask(unsigned id) {
    return id < sizeof quest_masks ? quest_masks[id] : 0;
}
unsigned save5_quest_state(const Save5Quests *q, unsigned id) {
    if (!q || id >= SAVE5_QUEST_CAPACITY) return SAVE5_QUEST_INACTIVE;
    return (q->states[id >> 2] >> ((id & 3u) * 2u)) & 3u;
}
int save5_quest_set_state(Save5Quests *q, unsigned id, unsigned state) {
    unsigned shift;
    if (!q || id >= SAVE5_QUEST_CAPACITY || state > SAVE5_QUEST_CLAIMED) return 0;
    shift = (id & 3u) * 2u;
    q->states[id >> 2] = (Save4U8)((q->states[id >> 2] & ~(3u << shift)) | (state << shift));
    return 1;
}
static int quest_objective_validate(const Save5Quests *q, unsigned id) {
    unsigned state = save5_quest_state(q, id), mask = quest_objective_mask(id);
    unsigned objectives = q->objectives[id];
    if (!mask) return !state && !objectives;
    if (objectives & ~mask) return 0;
    /* Beacon stages are monotonic prefixes: 0,1,3,7,15 only. */
    if (id == 21 && (objectives & (objectives + 1u))) return 0;
    if (state == SAVE5_QUEST_INACTIVE) return !objectives;
    if (state == SAVE5_QUEST_ACTIVE) return objectives != mask;
    return objectives == mask;
}
static int quest_reward_validate(const Save5Quests *q, unsigned index) {
    unsigned i;
    for (i = 0; i < 8; ++i)
        if (((q->rewards[index] >> i) & 1u) !=
            (save5_quest_state(q, index * 8u + i) == SAVE5_QUEST_CLAIMED)) return 0;
    return 1;
}
static int quest_fields_validate(const Save5Quests *q) {
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
        !zero_bytes(q->region_flags + 2, 30) || (q->anchors[0] & ~3u) ||
        (q->anchors[1] & ~3u) || !zero_bytes(q->anchors + 2, 14)) return 0;
    if ((q->anchors[0] & 1u) && !(q->region_flags[0] & 1u)) return 0;
    if ((q->anchors[0] & 2u) && !(q->region_flags[0] & 2u)) return 0;
    if ((q->anchors[1] & 1u) && !(q->region_flags[1] & 1u)) return 0;
    if ((q->anchors[1] & 2u) && !(q->region_flags[1] & 2u)) return 0;
    return 1;
}
int save5_quests_validate(const Save5Quests *q) {
    unsigned i;
    if (!q || !quest_fields_validate(q)) return 0;
    for (i = 0; i < SAVE5_QUEST_CAPACITY; ++i)
        if (!quest_objective_validate(q, i)) return 0;
    for (i = 0; i < 8; ++i) if (!quest_reward_validate(q, i)) return 0;
    return 1;
}
static int quest_campaign_validate(const CampaignSave *c, const Save5Quests *q) {
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
/* Call only after instance validation. Low bits prove retained family ownership;
 * bits8..12 additionally prove a single same-family instance owns its personal
 * trial AND the one-time training floor. Never combine evidence across copies. */
static unsigned retained_creature_bits(const CreatureInstance *c) {
    unsigned owner, trial, level, bond, trained;
    switch (c->form_id) {
    case 13: case 14: return 1u;
    case 16: return 2u;
    case 19: case 20: owner=4; trial=32; level=16; bond=40; trained=256; break;
    case 22: case 23: owner=8; trial=64; level=17; bond=40; trained=512; break;
    case 73: case 74: owner=16; trial=128; level=18; bond=45; trained=1024; break;
    case 75: case 76: owner=32; trial=256; level=18; bond=45; trained=2048; break;
    case 77: case 78: owner=64; trial=512; level=20; bond=50; trained=4096; break;
    default: return 0;
    }
    if ((c->trial_flags & trial) && c->level >= level && c->bond >= bond) owner |= trained;
    return owner;
}
static unsigned retained_creatures(const CreatureRoster *r) {
    unsigned i, mask = 0;
    for (i = 0; i < CREATURE_ROSTER_CAPACITY; ++i)
        mask |= retained_creature_bits(&r->instances[i]);
    return mask;
}
static int quest_creatures_validate(const Save5Quests *q, const Save4U8 *obtained,
                                    const Save4U8 *rewards, unsigned retained) {
    static const Save4U8 recruit_rewards[5]={7,8,11,9,10};
    static const Save4U8 recruit_masks[5]={4,8,64,16,32};
    unsigned i;
    if (save5_quest_state(q, 2) == SAVE5_QUEST_CLAIMED) {
        unsigned water = (creatures_form(13) && (obtained[1] & 16u)) ||
                         (creatures_form(14) && (obtained[1] & 32u));
        if (!(rewards[0] & 16u) || !water || !(retained & 1u)) return 0;
    }
    if (save5_quest_state(q, 3) == SAVE5_QUEST_CLAIMED &&
        (!(rewards[0] & 32u) || !creatures_form(16) || !(obtained[1] & 128u) ||
         !(retained & 2u))) return 0;
    for (i=0; i<5; ++i) {
        unsigned reward=recruit_rewards[i]-1u;
        if (save5_quest_state(q,11+i)==SAVE5_QUEST_CLAIMED &&
            (!(retained & recruit_masks[i]) || !(rewards[reward>>3] & (1u<<(reward&7))))) return 0;
        if (save5_quest_state(q,16+i)==SAVE5_QUEST_CLAIMED && !(retained & (256u<<i))) return 0;
    }
    return 1;
}
/* Revision2 cannot acquire Northern state merely because today's catalog can
 * resolve it. Revision1 already uses its all-zero legacy reservation reader. */
static int quest_revision_validate(const Save5Quests *q, unsigned revision) {
    unsigned i;
    if (revision >= 3) return 1;
    if (q->region_flags[1] || q->anchors[1]) return 0;
    for (i=11; i<22; ++i)
        if (save5_quest_state(q,i) || q->objectives[i]) return 0;
    return 1;
}
static int quest_equipment_validate(const Save5Quests *q, const EquipmentState *e) {
    unsigned source;
    if ((e->reward_claims[0] & 20u) && !(q->region_flags[0] & 1u)) return 0;
    /* Seen/record/reserved checks are already streamed. This bounded source
     * ledger check does not call the whole-inventory validator. */
    for (source = 0; source < EQUIPMENT_REWARD_CAPACITY; ++source) {
        unsigned claimed = (e->reward_claims[source >> 3] >> (source & 7u)) & 1u;
        unsigned id = equipment_reward_item(source);
        if (claimed && (!id || !equipment_seen(e, id))) return 0;
        if (source < sizeof equipment_source_quest && equipment_source_quest[source] >= 0 && claimed !=
            (save5_quest_state(q, (unsigned)equipment_source_quest[source]) == SAVE5_QUEST_CLAIMED)) return 0;
    }
    return 1;
}
static void encode_equipment_record(Save4U8 *b, const EquipmentRecord *r) {
    put16(b, r->item_id); b[2] = r->rank; b[3] = r->flags; b[4] = r->quantity;
    b[5] = r->reserved[0]; b[6] = r->reserved[1]; b[7] = r->reserved[2];
}
static void decode_equipment_record(EquipmentRecord *r, const Save4U8 *b) {
    r->item_id = get16(b); r->rank = b[2]; r->flags = b[3]; r->quantity = b[4];
    r->reserved[0] = b[5]; r->reserved[1] = b[6]; r->reserved[2] = b[7];
}
static Save4U8 quest_wire_byte(const Save5Quests *q, unsigned p) {
    if (p < 16) return q->states[p];
    if (p < 144) return (Save4U8)(q->objectives[(p - 16) >> 1] >> ((p & 1u) * 8u));
    if (p < 152) return q->rewards[p - 144];
    if (p < 216) return q->variables[p - 152];
    if (p < 248) return q->region_flags[p - 216];
    return q->anchors[p - 248];
}
static Save4U8 equipment_tail_byte(const EquipmentState *e, unsigned p) {
    if (p < 389) return e->equipped[p - 384];
    if (p < 400) return e->settings_reserved[p - 389];
    if (p < 464) return e->seen[p - 400];
    if (p < 480) return e->wallet_key_reserved[p - 464];
    if (p < 488) return e->reward_claims[p - 480];
    return e->reserved[p - 488];
}
int save5_validate(const Save5State *s) {
    return s && save5_campaign_validate(&s->campaign) &&
        creatures_roster_validate(&s->roster) && save5_quests_validate(&s->quests) &&
        quest_campaign_validate(&s->campaign, &s->quests) &&
        quest_creatures_validate(&s->quests, s->roster.obtained, s->roster.rewards,
                                 retained_creatures(&s->roster)) &&
        equipment_validate(&s->equipment) && quest_equipment_validate(&s->quests, &s->equipment);
}
/* Tight metadata packing uses all 1088 canonical-padding bytes temporarily:
 * campaign15 + party5 + next4 + collection48 + credits240 + quests264 + gear512.
 * No second full roster or bank exists. Every typed field is explicitly encoded. */
enum { META_QUEST = 312, META_EQUIPMENT = 576 };
static void snapshot_metadata(void) {
    Save5State *s = &scratch.state;
    Save4U8 *b = scratch.bytes + SAVE5_RESERVED_OFFSET;
    encode_campaign(b, &s->campaign);
    copy_bytes(b + 15, s->roster.party, 4); b[19] = s->roster.selected_party;
    put32(b + 20, s->roster.next_instance_id);
    copy_bytes(b + 24, s->roster.seen, 16);
    copy_bytes(b + 40, s->roster.obtained, 16);
    copy_bytes(b + 56, s->roster.rewards, 16);
    copy_bytes(b + 72, s->roster.expedition_bond, 160);
    copy_bytes(b + 232, s->roster.expedition_events, 64);
    copy_bytes(b + 296, s->roster.lifetime_field_aid, 16);
}
static void snapshot_finish(void) {
    Save4U8 *b = scratch.bytes, *m = b + SAVE5_RESERVED_OFFSET;
    clear_bytes(b, 160);
    b[0] = 0x45; b[1] = 0x42; b[2] = 5; b[3] = 32;
    put16(b + 4, SAVE5_BANK_SIZE); put16(b + 6, SAVE5_USED_SIZE);
    put16(b + 12, SAVE5_CONTENT_REVISION);
    copy_bytes(b + 32, m, 15); copy_bytes(b + 96, m + 24, 48);
    clear_bytes(b + 4000, 1056);
    copy_bytes(b + 4000, m + 15, 5); copy_bytes(b + 4008, m + 20, 4);
    copy_bytes(b + 4032, m + META_QUEST, 264);
    copy_bytes(b + 4296, m + 72, 160);
    copy_bytes(b + 4456, m + 232, 64);
    copy_bytes(b + 4520, m + 296, 16);
    copy_bytes(b + 4544, m + META_EQUIPMENT, 512);
}

/* Streaming checks never call the whole-inventory validator. Quest objectives
 * and equipment records are checked one at a time, with conservative charges. */
typedef struct BankScan {
    Save4U8 block[64], collection[48], occupied[20], item_owned[64];
    Save5Quests quests;
    EquipmentState equipment;
    CampaignSave campaign;
    Save4U32 crc, expected_crc, sequence, max_id;
    unsigned offset, position, valid, story_mask, stage, boundary, base, slot, memory, revision;
    unsigned retained_creatures; /* streamed, validated owned Water/Metal bits */
} BankScan;
static BankScan scan;
static unsigned writer_status, writer_phase, writer_position, writer_progress;
static unsigned writer_destination, bank_valid[2];
static Save4U32 bank_sequence[2], writer_crc;
enum { PHASE_META, PHASE_QUEST, PHASE_EQUIPMENT, PHASE_ENCODE, PHASE_FINISH,
       PHASE_CHECK_SNAPSHOT, PHASE_SCAN_A, PHASE_SCAN_B, PHASE_PREPARE, PHASE_CRC,
       PHASE_INVALIDATE, PHASE_CHECK_INVALIDATE, PHASE_WRITE, PHASE_VERIFY, PHASE_COMMIT, PHASE_FINAL };
enum { SCAN_HEADER, SCAN_CAMPAIGN, SCAN_COLLECTION, SCAN_COLLECTION_RESERVED,
       SCAN_INSTANCE, SCAN_PARTY, SCAN_QUEST_LEGACY, SCAN_QUEST_STATES,
       SCAN_QUEST_OBJECTIVE, SCAN_QUEST_REWARDS, SCAN_QUEST_VARIABLES,
       SCAN_QUEST_FLAGS, SCAN_QUEST_ANCHORS, SCAN_BOND, SCAN_EVENTS,
       SCAN_CREDIT_RESERVED, SCAN_EQUIPMENT_RECORD, SCAN_EQUIPMENT_REFS,
       SCAN_EQUIPMENT_SETTINGS, SCAN_EQUIPMENT_SEEN, SCAN_EQUIPMENT_WALLET,
       SCAN_EQUIPMENT_CLAIMS, SCAN_EQUIPMENT_RESERVED, SCAN_PADDING };

static int bit(const Save4U8 *p, unsigned n) { return (p[n >> 3] >> (n & 7)) & 1; }
static void set_bit(Save4U8 *p, unsigned n) { p[n >> 3] |= (Save4U8)(1u << (n & 7)); }
static void scan_start(unsigned offset, unsigned memory) {
    clear_bytes(&scan, sizeof scan);
    scan.offset = offset; scan.crc = 0xFFFFFFFFu; scan.valid = 1;
    scan.memory = memory; scan.boundary = 32;
    clear_bytes(scratch.bytes + SAVE5_RESERVED_OFFSET, 640);
}
static int scan_header(void) {
    const Save4U8 *b = scan.block;
    if (b[0] != 0x45 || b[1] != 0x42 || b[2] != 5 || b[3] != 32 ||
        get16(b + 4) != SAVE5_BANK_SIZE || get16(b + 6) != SAVE5_USED_SIZE ||
        (get16(b + 12) != 1 && get16(b + 12) != 2 && get16(b + 12) != SAVE5_CONTENT_REVISION) ||
        b[20] != (scan.memory ? 0 : SAVE5_COMMIT) ||
        !zero_bytes(b + 14, 2) || !zero_bytes(b + 21, 11)) return 0;
    scan.expected_crc = get32(b + 16); scan.sequence = get32(b + 8);
    scan.revision = get16(b + 12);
    return 1;
}
static int revision_form_allowed(unsigned id) {
    /* Identity lists are fixed for each released content revision. */
    if (id==1 || id==2 || id==4 || id==5 || id==7 || id==8 || id==10 || id==11)
        return creatures_form(id)!=0;
    if (scan.revision>=2 && (id==13 || id==14 || id==16)) return creatures_form(id)!=0;
    if (scan.revision==3 && (id==19 || id==20 || id==22 || id==23 ||
        id==73 || id==74 || id==75 || id==76 || id==77 || id==78)) return creatures_form(id)!=0;
    return 0;
}
static int revision_equipment_allowed(unsigned id) {
    if (id==1 || id==2 || id==9 || id==10 || id==17 || id==18 ||
        id==33 || id==34 || id==49 || id==50 || id==65 || id==81 || id==82)
        return equipment_definition(id)!=0;
    return scan.revision==3 && (id==3 || id==11 || id==19 || id==35 || id==51 || id==83) &&
           equipment_definition(id)!=0;
}
static int scan_collection(void) {
    unsigned i;
    /* Collection discovery is revisioned content, not permission to use a
     * reserved form. Reward bits remain an explicit 128-bit authored ledger. */
    for (i = 0; i < 128; ++i) {
        if (bit(scan.collection, i) && !revision_form_allowed(i + 1)) return 0;
        if (bit(scan.collection + 16, i) && !bit(scan.collection, i)) return 0;
    }
    return 1;
}
static int scan_instance(unsigned slot) {
    CreatureInstance c;
    unsigned i, legacy;
    Save4U8 *ids = scratch.bytes + SAVE5_RESERVED_OFFSET;
    decode_instance(&c, scan.block);
    if (!creatures_instance_validate(&c)) return 0;
    if (c.form_id && !revision_form_allowed(c.form_id)) return 0;
    if (!(c.flags & CREATURE_OCCUPIED)) return 1;
    if (!bit(scan.collection + 16, c.form_id - 1)) return 0;
    for (i = 0; i < slot; ++i)
        if (get32(ids + i * 4) == c.instance_id) return 0;
    put32(ids + slot * 4, c.instance_id);
    set_bit(scan.occupied, slot);
    scan.retained_creatures |= retained_creature_bits(&c);
    if (c.instance_id > scan.max_id) scan.max_id = c.instance_id;
    legacy = creatures_legacy_spirit(c.form_id);
    if (c.flags & CREATURE_STORY_LOCKED) {
        if (legacy > 3 || (scan.story_mask & (1u << legacy)) ||
            !bit(scan.collection + 32, legacy)) return 0;
        scan.story_mask |= 1u << legacy;
    }
    return 1;
}
static int scan_party(void) {
    const Save4U8 *b = scan.block;
    unsigned i, j, count = 0;
    Save4U32 next_id = get32(b + 8);
    if (!zero_bytes(b + 5, 3) || !zero_bytes(b + 12, 20) ||
        !next_id || next_id <= scan.max_id ||
        (scan.collection[32] & 15u) != scan.story_mask) return 0;
    for (i = 0; i < 4; ++i) {
        if (b[i] == CREATURE_EMPTY_SLOT) continue;
        if (b[i] >= 160 || !bit(scan.occupied, b[i])) return 0;
        for (j = 0; j < i; ++j) if (b[i] == b[j]) return 0;
        ++count;
    }
    if (!count) return b[4] == CREATURE_EMPTY_SLOT;
    return b[4] < 4 && b[b[4]] != CREATURE_EMPTY_SLOT;
}
static int scan_equipment_record(unsigned slot) {
    EquipmentRecord *r = &scan.equipment.bag[slot];
    decode_equipment_record(r, scan.block);
    if (!equipment_record_validate(r) || (r->item_id && !revision_equipment_allowed(r->item_id))) return 0;
    if (!slot && (r->item_id != EQUIPMENT_STARTER_ID || r->flags != EQUIPMENT_PROTECTED)) return 0;
    if (r->item_id) {
        if (bit(scan.item_owned, r->item_id)) return 0;
        set_bit(scan.item_owned, r->item_id);
    }
    return 1;
}
static int equipment_seen_byte(unsigned index, unsigned value) {
    unsigned i;
    if ((value & scan.item_owned[index]) != scan.item_owned[index]) return 0;
    for (i = 0; i < 8; ++i)
        if ((value & (1u << i)) && !revision_equipment_allowed(index * 8u + i)) return 0;
    return 1;
}
static void scan_next(unsigned stage, unsigned size) {
    scan.stage = stage; scan.base = scan.position; scan.boundary = scan.position + size;
}
/* Byte loops avoid divisions and expensive checks. Record-end semantic work
 * is bounded independently of bag/roster occupancy and charged to the budget. */
static unsigned scan_run(unsigned budget) {
    unsigned used = 0;
    while (scan.valid && scan.position < SAVE5_BANK_SIZE && used < budget) {
        unsigned p = scan.position, n = scan.boundary - p, i, any = 0;
        Save4U32 crc = scan.crc;
        unsigned zero = scan.stage == SCAN_COLLECTION_RESERVED ||
            scan.stage == SCAN_QUEST_LEGACY || scan.stage == SCAN_CREDIT_RESERVED ||
            scan.stage == SCAN_EQUIPMENT_SETTINGS || scan.stage == SCAN_EQUIPMENT_WALLET ||
            scan.stage == SCAN_EQUIPMENT_RESERVED || scan.stage == SCAN_PADDING;
        const volatile Save4U8 *src;
        if (n > budget - used) n = budget - used;
        if (scan.memory && zero && p < SAVE5_RESERVED_OFFSET &&
            p + n > SAVE5_RESERVED_OFFSET) n = SAVE5_RESERVED_OFFSET - p;
        src = scan.memory ? scratch.bytes + p : SRAM + scan.offset + p;
        if (scan.stage == SCAN_HEADER) {
            for (i = 0; i < n; ++i) {
                Save4U8 v = src[i]; scan.block[p + i] = v;
                if (!scan.memory) crc = crc_byte(crc, p+i >= 16 && p+i <= 20 ? 0 : v);
            }
        } else if (scan.stage == SCAN_COLLECTION) {
            Save4U8 *dst = scan.collection + p - 96;
            if (scan.memory) for (i = 0; i < n; ++i) dst[i] = src[i];
            else for (i = 0; i < n; ++i) { Save4U8 v = src[i]; dst[i] = v; crc = crc_byte(crc, v); }
        } else if (scan.stage == SCAN_BOND) {
            for (i = 0; i < n; ++i) {
                Save4U8 v = src[i];
                if (!scan.memory) crc = crc_byte(crc, v);
                if (v > 10 || (v && !bit(scan.occupied, p + i - 4296))) scan.valid = 0;
            }
        } else if (zero) {
            /* ID scratch overlaps only canonical trailing padding. */
            if (!(scan.memory && p >= SAVE5_RESERVED_OFFSET)) {
                for (i = 0; i < n; ++i) { Save4U8 v = src[i]; any |= v; if (!scan.memory) crc = crc_byte(crc, v); }
                if (any) scan.valid = 0;
            }
        } else if (scan.stage == SCAN_EVENTS) {
            if (!scan.memory) for (i = 0; i < n; ++i) crc = crc_byte(crc, src[i]);
        } else {
            Save4U8 *dst = scan.block + p - scan.base;
            if (scan.memory) for (i = 0; i < n; ++i) dst[i] = src[i];
            else for (i = 0; i < n; ++i) { Save4U8 v = src[i]; dst[i] = v; crc = crc_byte(crc, v); }
        }
        scan.crc = crc; scan.position += n; used += n;
        if (scan.position == scan.boundary) {
            unsigned charge = 0;
            switch (scan.stage) {
            case SCAN_HEADER:
                if (!scan_header()) scan.valid = 0;
                scan_next(SCAN_CAMPAIGN, 64); break;
            case SCAN_CAMPAIGN: {
                CampaignSave c;
                decode_campaign(&c, scan.block);
                scan.campaign = c;
                if (!save5_campaign_validate(&c) || (scan.revision == 1 && c.room > 13) ||
                    (scan.revision == 2 && c.room > 21) ||
                    !zero_bytes(scan.block+15, 49)) scan.valid = 0;
                scan_next(SCAN_COLLECTION, 48); charge = 32; break;
            }
            case SCAN_COLLECTION:
                if (!scan_collection()) scan.valid = 0;
                scan_next(SCAN_COLLECTION_RESERVED, 16); charge = 128; break;
            case SCAN_COLLECTION_RESERVED:
                scan.slot = 0; scan_next(SCAN_INSTANCE, 24); break;
            case SCAN_INSTANCE:
                charge = scan.block[0] ? 128 : 16;
                if (!scan_instance(scan.slot++)) scan.valid = 0;
                scan_next(scan.slot == 160 ? SCAN_PARTY : SCAN_INSTANCE, scan.slot == 160 ? 32 : 24); break;
            case SCAN_PARTY:
                if (!scan_party()) scan.valid = 0;
                scan_next(scan.revision == 1 ? SCAN_QUEST_LEGACY : SCAN_QUEST_STATES,
                          scan.revision == 1 ? 264 : 16); charge = 32; break;
            case SCAN_QUEST_LEGACY: scan_next(SCAN_BOND, 160); break;
            case SCAN_QUEST_STATES:
                copy_bytes(scan.quests.states, scan.block, 16);
                scan.slot = 0; scan_next(SCAN_QUEST_OBJECTIVE, 2); break;
            case SCAN_QUEST_OBJECTIVE:
                scan.quests.objectives[scan.slot] = get16(scan.block);
                if (!quest_objective_validate(&scan.quests, scan.slot)) scan.valid = 0;
                ++scan.slot;
                scan_next(scan.slot == 64 ? SCAN_QUEST_REWARDS : SCAN_QUEST_OBJECTIVE,
                          scan.slot == 64 ? 8 : 2); charge = 16; break;
            case SCAN_QUEST_REWARDS:
                copy_bytes(scan.quests.rewards, scan.block, 8);
                for (i = 0; i < 8; ++i) if (!quest_reward_validate(&scan.quests, i)) scan.valid = 0;
                scan_next(SCAN_QUEST_VARIABLES, 64); charge = 128; break;
            case SCAN_QUEST_VARIABLES:
                copy_bytes(scan.quests.variables, scan.block, 64);
                scan_next(SCAN_QUEST_FLAGS, 32); break;
            case SCAN_QUEST_FLAGS:
                copy_bytes(scan.quests.region_flags, scan.block, 32);
                scan_next(SCAN_QUEST_ANCHORS, 16); break;
            case SCAN_QUEST_ANCHORS:
                copy_bytes(scan.quests.anchors, scan.block, 16);
                if (!quest_fields_validate(&scan.quests) || !quest_revision_validate(&scan.quests,scan.revision) ||
                    !quest_campaign_validate(&scan.campaign, &scan.quests) ||
                    !quest_creatures_validate(&scan.quests, scan.collection + 16, scan.collection + 32,
                                              scan.retained_creatures)) scan.valid = 0;
                scan_next(SCAN_BOND, 160); charge = 128; break;
            case SCAN_BOND: scan_next(SCAN_EVENTS, 80); break;
            case SCAN_EVENTS: scan_next(SCAN_CREDIT_RESERVED, 8); break;
            case SCAN_CREDIT_RESERVED:
                scan.slot = 0;
                scan_next(scan.revision == 1 ? SCAN_PADDING : SCAN_EQUIPMENT_RECORD,
                          scan.revision == 1 ? 1600 : 8); break;
            case SCAN_EQUIPMENT_RECORD:
                if (!scan_equipment_record(scan.slot++)) scan.valid = 0;
                scan_next(scan.slot == 48 ? SCAN_EQUIPMENT_REFS : SCAN_EQUIPMENT_RECORD,
                          scan.slot == 48 ? 5 : 8); charge = 32; break;
            case SCAN_EQUIPMENT_REFS:
                copy_bytes(scan.equipment.equipped, scan.block, 5);
                if (!equipment_refs_validate(&scan.equipment)) scan.valid = 0;
                scan_next(SCAN_EQUIPMENT_SETTINGS, 11); charge = 64; break;
            case SCAN_EQUIPMENT_SETTINGS: scan.slot = 0; scan_next(SCAN_EQUIPMENT_SEEN, 1); break;
            case SCAN_EQUIPMENT_SEEN:
                scan.equipment.seen[scan.slot] = scan.block[0];
                if (!equipment_seen_byte(scan.slot, scan.block[0])) scan.valid = 0;
                ++scan.slot;
                scan_next(scan.slot == 64 ? SCAN_EQUIPMENT_WALLET : SCAN_EQUIPMENT_SEEN,
                          scan.slot == 64 ? 16 : 1); charge = 16; break;
            case SCAN_EQUIPMENT_WALLET: scan_next(SCAN_EQUIPMENT_CLAIMS, 8); break;
            case SCAN_EQUIPMENT_CLAIMS:
                copy_bytes(scan.equipment.reward_claims, scan.block, 8);
                if (!quest_equipment_validate(&scan.quests, &scan.equipment) ||
                    (scan.revision == 2 && ((scan.equipment.reward_claims[1] & 0xe0u) ||
                     !zero_bytes(scan.equipment.reward_claims+2,6)))) scan.valid = 0;
                scan_next(SCAN_EQUIPMENT_RESERVED, 24); charge = 128; break;
            case SCAN_EQUIPMENT_RESERVED: scan_next(SCAN_PADDING, 1088); break;
            default: break;
            }
            if (charge > budget - used) charge = budget - used;
            used += charge;
        }
    }
    if (scan.position == SAVE5_BANK_SIZE && !scan.memory && ~scan.crc != scan.expected_crc) scan.valid = 0;
    return used;
}
static int scan_bank(unsigned offset, Save4U32 *sequence) {
    scan_start(offset, 0);
    while (scan.valid && scan.position < SAVE5_BANK_SIZE) (void)scan_run(1024);
    if (!scan.valid) return 0;
    *sequence = scan.sequence;
    return 1;
}
static int newest_bank(void) {
    if (bank_valid[0] && bank_valid[1]) {
        Save4U32 delta = bank_sequence[1] - bank_sequence[0];
        return delta && delta < 0x80000000u ? 1 : 0;
    }
    if (bank_valid[0]) return 0;
    if (bank_valid[1]) return 1;
    return -1;
}
static void read_bytes(Save4U8 *out, unsigned offset, unsigned size) {
    while (size--) *out++ = SRAM[offset++];
}
static void decode_valid_bank(Save5State *s, unsigned offset, Save4U32 sequence) {
    Save4U8 b[32];
    unsigned i, revision;
    clear_bytes(s, sizeof *s);
    read_bytes(b, offset + 12, 2); revision = get16(b);
    read_bytes(b, offset + 32, 15); decode_campaign(&s->campaign, b);
    s->campaign.sequence = sequence;
    read_bytes(s->roster.seen, offset + 96, 16);
    read_bytes(s->roster.obtained, offset + 112, 16);
    read_bytes(s->roster.rewards, offset + 128, 16);
    for (i = 0; i < 160; ++i) {
        read_bytes(b, offset + 160 + i * 24, 24);
        decode_instance(&s->roster.instances[i], b);
    }
    read_bytes(b, offset + 4000, 12);
    copy_bytes(s->roster.party, b, 4); s->roster.selected_party = b[4];
    s->roster.next_instance_id = get32(b + 8);
    read_bytes(s->roster.expedition_bond, offset + 4296, 160);
    read_bytes(s->roster.expedition_events, offset + 4456, 64);
    read_bytes(s->roster.lifetime_field_aid, offset + 4520, 16);
    if (revision == 1) equipment_init(&s->equipment);
    else {
        read_bytes(s->quests.states, offset + 4032, 16);
        for (i = 0; i < 64; ++i) {
            read_bytes(b, offset + 4048 + i * 2, 2);
            s->quests.objectives[i] = get16(b);
        }
        read_bytes(s->quests.rewards, offset + 4176, 8);
        read_bytes(s->quests.variables, offset + 4184, 64);
        read_bytes(s->quests.region_flags, offset + 4248, 32);
        read_bytes(s->quests.anchors, offset + 4280, 16);
        for (i = 0; i < 48; ++i) {
            read_bytes(b, offset + 4544 + i * 8, 8);
            decode_equipment_record(&s->equipment.bag[i], b);
        }
        read_bytes(s->equipment.equipped, offset + 4928, 5);
        read_bytes(s->equipment.seen, offset + 4944, 64);
        read_bytes(s->equipment.reward_claims, offset + 5024, 8);
    }
    normalize_resume(&s->campaign, revision);
}
static int load_internal(Save5State *out) {
    CampaignSave legacy;
    int active;
    bank_valid[0] = (unsigned)scan_bank(SAVE5_BANK_A, &bank_sequence[0]);
    bank_valid[1] = (unsigned)scan_bank(SAVE5_BANK_B, &bank_sequence[1]);
    active = newest_bank();
    if (active >= 0) {
        decode_valid_bank(&scratch.state, active ? SAVE5_BANK_B : SAVE5_BANK_A, bank_sequence[active]);
        if (!save5_validate(&scratch.state)) return 0;
    } else {
#ifdef SAVE5_HOST_TEST
        /* save4.c remains byte-for-byte unchanged. Its host-only 256-byte SRAM
         * shim is synchronized only for reads; target builds share hardware. */
        read_bytes(save4_test_sram, 0, 256);
#endif
        if (!save4_load(&legacy)) return 0;
        clear_bytes(&scratch.state, sizeof scratch.state);
        scratch.state.campaign = legacy;
        equipment_init(&scratch.state.equipment);
        if (!creatures_migrate_legacy(&scratch.state.roster, legacy.chapter_flags, legacy.spirit) ||
            !save5_validate(&scratch.state)) return 0;
    }
    if (out) copy_bytes(out, &scratch.state, sizeof *out);
    return 1;
}
int save5_load(Save5State *out) {
    if (!out || writer_status == SAVE5_BUSY) return 0;
    return load_internal(out);
}
int save5_has_valid(void) {
    if (writer_status == SAVE5_BUSY) return 0;
    return load_internal(0);
}
int save5_begin(const Save5State *s) {
    if (writer_status == SAVE5_BUSY) return 0;
    if (!s || !save5_campaign_validate(&s->campaign)) {
        writer_status = SAVE5_FAILED; return 0;
    }
    copy_state(&scratch.state, s);
    writer_status = SAVE5_BUSY; writer_phase = PHASE_META;
    writer_position = writer_progress = 0;
    bank_valid[0] = bank_valid[1] = 0;
    bank_sequence[0] = bank_sequence[1] = 0;
    return 1;
}
unsigned save5_status(void) { return writer_status; }
unsigned save5_progress(void) { return writer_progress; }
unsigned save5_progress_total(void) { return SAVE5_BANK_SIZE * 6u + 3u; }
unsigned save5_step(unsigned budget) {
    unsigned used = 0;
    /* Cap even accidentally enormous caller budgets. Bounded work is part of
     * this API, not a convention that the engine can accidentally defeat. */
    if (budget > SAVE5_MAX_BUDGET) budget = SAVE5_MAX_BUDGET;
    while (writer_status == SAVE5_BUSY && used < budget) {
        unsigned available = budget - used;
        if (writer_phase == PHASE_META) {
            snapshot_metadata(); writer_position = 0; writer_phase = PHASE_QUEST;
            used += available < 312 ? available : 312;
        } else if (writer_phase == PHASE_QUEST) {
            unsigned n = 264 - writer_position, i;
            if (n > available) n = available;
            for (i = 0; i < n; ++i)
                scratch.bytes[SAVE5_RESERVED_OFFSET + META_QUEST + writer_position + i] =
                    quest_wire_byte(&scratch.state.quests, writer_position + i);
            writer_position += n; used += n;
            if (writer_position == 264) { writer_position = 0; writer_phase = PHASE_EQUIPMENT; }
        } else if (writer_phase == PHASE_EQUIPMENT) {
            if (writer_position < 384) {
                encode_equipment_record(scratch.bytes + SAVE5_RESERVED_OFFSET + META_EQUIPMENT + writer_position,
                    &scratch.state.equipment.bag[writer_position / 8]);
                writer_position += 8; used += available < 8 ? available : 8;
            } else {
                unsigned n = 512 - writer_position, i;
                if (n > available) n = available;
                for (i = 0; i < n; ++i)
                    scratch.bytes[SAVE5_RESERVED_OFFSET + META_EQUIPMENT + writer_position + i] =
                        equipment_tail_byte(&scratch.state.equipment, writer_position + i);
                writer_position += n; used += n;
            }
            if (writer_position == 512) { writer_position = 160; writer_phase = PHASE_ENCODE; }
        } else if (writer_phase == PHASE_ENCODE) {
            unsigned n = available / 4u, i;
            if (!n) n = 1;
            if (n > writer_position) n = writer_position;
            for (i = 0; i < n; ++i) {
                unsigned slot = --writer_position;
                encode_instance(scratch.bytes + 160 + slot * 24, &scratch.state.roster.instances[slot]);
            }
            used += n * 4u > available ? available : n * 4u;
            if (!writer_position) writer_phase = PHASE_FINISH;
        } else if (writer_phase == PHASE_FINISH) {
            snapshot_finish(); scan_start(0, 1); writer_phase = PHASE_CHECK_SNAPSHOT;
            used += available < 1088 ? available : 1088;
        } else if (writer_phase == PHASE_CHECK_SNAPSHOT) {
            used += scan_run(available);
            if (!scan.valid) writer_status = SAVE5_FAILED;
            else if (scan.position == SAVE5_BANK_SIZE) { writer_phase = PHASE_SCAN_A; scan_start(SAVE5_BANK_A, 0); }
        } else if (writer_phase == PHASE_SCAN_A || writer_phase == PHASE_SCAN_B) {
            unsigned bank = writer_phase == PHASE_SCAN_B;
            unsigned before = scan.position;
            used += scan_run(available); writer_progress += scan.position - before;
            if (!scan.valid || scan.position == SAVE5_BANK_SIZE) {
                bank_valid[bank] = scan.valid; bank_sequence[bank] = scan.sequence;
                if (!bank) { writer_phase = PHASE_SCAN_B; scan_start(SAVE5_BANK_B, 0); }
                else { writer_phase = PHASE_PREPARE; writer_position = SAVE5_RESERVED_OFFSET; }
            }
        } else if (writer_phase == PHASE_PREPARE) {
            unsigned n = SAVE5_BANK_SIZE - writer_position, i;
            if (n > available) n = available;
            for (i = 0; i < n; ++i) scratch.bytes[writer_position + i] = 0;
            writer_position += n; used += n;
            if (writer_position == SAVE5_BANK_SIZE) {
                int active = newest_bank();
                Save4U32 sequence = active < 0 ? 1u : bank_sequence[active] + 1u;
                writer_destination = active == 0 ? SAVE5_BANK_B : SAVE5_BANK_A;
                put32(scratch.bytes + 8, sequence);
                writer_crc = 0xFFFFFFFFu; writer_position = 0; writer_phase = PHASE_CRC;
            }
        } else if (writer_phase == PHASE_CRC) {
            unsigned n = SAVE5_BANK_SIZE - writer_position, i;
            Save4U32 crc = writer_crc;
            if (n > available) n = available;
            for (i = 0; i < n; ++i) crc = crc_byte(crc, scratch.bytes[writer_position + i]);
            writer_crc = crc; writer_position += n; used += n; writer_progress += n;
            if (writer_position == SAVE5_BANK_SIZE) {
                put32(scratch.bytes + SAVE5_CRC_OFFSET, ~writer_crc); writer_phase = PHASE_INVALIDATE;
            }
        } else if (writer_phase == PHASE_INVALIDATE) {
            ++used; ++writer_progress;
            if (!write_byte(writer_destination + SAVE5_COMMIT_OFFSET, 0)) writer_status = SAVE5_FAILED;
            else writer_phase = PHASE_CHECK_INVALIDATE;
        } else if (writer_phase == PHASE_CHECK_INVALIDATE) {
            ++used; ++writer_progress;
            if (SRAM[writer_destination + SAVE5_COMMIT_OFFSET] != 0) writer_status = SAVE5_FAILED;
            else { writer_phase = PHASE_WRITE; writer_position = 0; }
        } else if (writer_phase == PHASE_WRITE) {
            unsigned n = SAVE5_BANK_SIZE - writer_position, i;
            if (n > available) n = available;
            for (i = 0; i < n; ++i) {
                unsigned p = writer_position + i;
                if (p != SAVE5_COMMIT_OFFSET && !write_byte(writer_destination + p, scratch.bytes[p])) {
                    writer_status = SAVE5_FAILED; break;
                }
            }
            writer_position += n; used += n; writer_progress += n;
            if (writer_position == SAVE5_BANK_SIZE) { writer_phase = PHASE_VERIFY; writer_position = 0; }
        } else if (writer_phase == PHASE_VERIFY || writer_phase == PHASE_FINAL) {
            unsigned n = SAVE5_BANK_SIZE - writer_position, i;
            if (n > available) n = available;
            for (i = 0; i < n; ++i)
                if (SRAM[writer_destination + writer_position + i] != scratch.bytes[writer_position + i]) {
                    writer_status = SAVE5_FAILED; break;
                }
            writer_position += n; used += n; writer_progress += n;
            if (writer_status == SAVE5_BUSY && writer_position == SAVE5_BANK_SIZE) {
                if (writer_phase == PHASE_FINAL) writer_status = SAVE5_DONE;
                else writer_phase = PHASE_COMMIT;
            }
        } else if (writer_phase == PHASE_COMMIT) {
            ++used; ++writer_progress;
            if (!write_byte(writer_destination + SAVE5_COMMIT_OFFSET, SAVE5_COMMIT)) writer_status = SAVE5_FAILED;
            else {
                scratch.bytes[SAVE5_COMMIT_OFFSET] = SAVE5_COMMIT;
                writer_position = 0; writer_phase = PHASE_FINAL;
            }
        } else writer_status = SAVE5_FAILED;
    }
#ifdef SAVE5_HOST_TEST
    test_step_work = used;
#endif
    return writer_status;
}
int save5_store(const Save5State *s) {
    if (!save5_begin(s)) return 0;
    while (save5_step(SAVE5_RECOMMENDED_BUDGET) == SAVE5_BUSY) { }
    return save5_status() == SAVE5_DONE;
}
#ifdef SAVE5_HOST_TEST
void save5_test_reset_writer(void) {
    writer_status = SAVE5_IDLE; writer_progress = 0; test_step_work = 0;
}
#endif
