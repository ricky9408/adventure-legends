#include "save5.h"
#include "save5_history_policy.h"

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
    if ((s->room > 13 && (s->room < 16 || s->room > 45)) ||
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
    if (s->room >= 38) {
        /* assets/magma_region/validation.json verifies radius-five paths. */
        return (chapter & SAVE4_SKY_CLEAR) && (s->room<=39?s->spawn<=3:s->spawn==0);
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
static const Save4U8 quest_masks[38] = {7,3,7,7,3,1,1,1,3,7,1,3,7,3,7,7,3,7,7,3,7,15,3,3,15,7,3,3,3,3,3,3,15,7,3,3,3,7};
static const signed char equipment_source_quest[31] = {-1,7,-1,6,-1,4,0,8,1,9,5,10,6,16,17,18,19,19,20,22,29,25,27,26,28,30,33,34,35,36,37};
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
    if ((id == 21 || id == 24 || id == 32) && (objectives & (objectives + 1u))) return 0;
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
        (q->region_flags[2] && !(q->region_flags[2] & 1u)) ||
        (q->region_flags[3] && !(q->region_flags[3] & 1u)) ||
        !zero_bytes(q->region_flags + 4, 4) || (q->region_flags[9] & ~127u) ||
        !zero_bytes(q->region_flags + 10, 6) || (q->region_flags[16] & ~15u) ||
        q->region_flags[17] || (q->region_flags[18] & ~3u) ||
        (q->region_flags[19] & ~7u) || (q->region_flags[19] & (q->region_flags[19]+1u)) ||
        !zero_bytes(q->region_flags + 20, 12) ||
        (q->anchors[0] & ~3u) || (q->anchors[1] & ~3u) ||
        (q->anchors[2] & ~3u) || (q->anchors[3] & ~3u) ||
        !zero_bytes(q->anchors + 4, 12)) return 0;
    if (q->anchors[3] & ~q->region_flags[3]) return 0;
    if ((q->anchors[2] & 1u) && !(q->region_flags[2] & 1u)) return 0;
    if ((q->anchors[2] & 2u) && !(q->region_flags[2] & 2u)) return 0;
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
static int magma_quest_campaign_validate(const Save5Quests *q) {
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
    if(!magma_quest_campaign_validate(q))return 0;
    if (room >= 38) {
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
/* Southern source order: two guaranteed, then eight typed field encounters.
 * A record with any trial or an evolved Southern form is checked locally for
 * its complete floor. OR summaries never combine one copy's trial with another
 * copy's training. High bits mean that a checked individual requires a source. */
static unsigned southern_instance_evidence(const CreatureInstance *c) {
    static const Save4U8 forms[10]={79,85,25,28,81,83,87,89,91,93};
    static const Save4U8 levels[10]={20,20,20,22,22,22,24,22,24,22};
    static const Save4U8 bonds[10]={40,40,40,45,45,45,45,45,45,45};
    /* Explicit form-byte -> source-row+1. Zero means no Southern evidence;
     * bounds are checked before indexing. This preserves all256 byte inputs. */
    static const Save4U8 source_row[128]={
        [79]=1,[80]=1,[85]=2,[86]=2,[25]=3,[26]=3,[28]=4,[29]=4,
        [81]=5,[82]=5,[83]=6,[84]=6,[87]=7,[88]=7,[89]=8,[90]=8,
        [91]=9,[92]=9,[93]=10,[94]=10
    };
    unsigned i, result;
    /* Empty records still receive the complete zero-byte instance validation. */
    if (!c->form_id || c->form_id>=sizeof source_row) return 0;
    i=source_row[c->form_id];
    if (!i) return 0;
    --i;result=1u<<i;
    if (c->trial_flags || c->form_id==forms[i]+1u) {
        if (c->trial_flags!=1 || c->level<levels[i] || c->bond<bonds[i]) return 0x80000000u;
        result|=1u<<(i+10);
    }
    return result;
}
static unsigned southern_roster_evidence(const CreatureRoster *r) {
    unsigned i, evidence=0;
    for(i=0;i<CREATURE_ROSTER_CAPACITY;++i) evidence|=southern_instance_evidence(&r->instances[i]);
    return evidence;
}
static int southern_sources_validate(const Save5Quests *q, const Save4U8 *obtained,
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
            !(obtained[(base+1)>>3]&(1u<<((base+1)&7)))) return 0;
    }
    return 1;
}
/* Bounded per-record accumulation for both streaming and blocking checks.
 * Count caps at2 because branch receipt evidence needs two distinct retained
 * identities; the roster/stream identity validator proves global uniqueness. */
typedef struct MagmaEvidence {
    Save4U8 count[9], evolved_branches, ready, caldera, invalid;
} MagmaEvidence;
static const Save4U8 magma_bases[9]={31,34,37,40,43,46,95,97,99};
static unsigned magma_form_row(unsigned form) {
    if(form>=31 && form<=48)return (form-31)/3;
    if(form>=95 && form<=100)return 6+(form-95)/2;
    return 9;
}
static void magma_instance_evidence(MagmaEvidence *e,const CreatureInstance *c) {
    unsigned i=magma_form_row(c->form_id),delta;
    if(i==9)return;
    if(e->count[i]<2)++e->count[i];
    delta=c->form_id-magma_bases[i];
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
static int magma_sources_validate(const Save5Quests *q,const Save4U8 *obtained,
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
            unsigned f=magma_bases[i]+j-1;
            history|=(obtained[f>>3]>>(f&7))&1u;
        }
        if(!history)return 0;
    }
    for(i=0;i<4;++i)if(q->region_flags[16]&(1u<<i)) {
        unsigned a=magma_bases[i+2],history;
        history=((obtained[a>>3]>>(a&7))|(obtained[(a+1)>>3]>>((a+1)&7)))&1u;
        if(e->count[i+2]<2 || !(e->evolved_branches&(1u<<i)) || !history)return 0;
    }
    return 1;
}
static int magma_roster_sources_validate(const Save5Quests *q,const CreatureRoster *r) {
    MagmaEvidence e;unsigned i;clear_bytes(&e,sizeof e);
    for(i=0;i<CREATURE_ROSTER_CAPACITY;++i)magma_instance_evidence(&e,&r->instances[i]);
    return magma_sources_validate(q,r->obtained,&e);
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
/* Released-policy evaluators are bounded and shared by blocking decoded-state
 * validation and streaming bank scans. They never resolve a historical row
 * through current quest, equipment, region or creature source catalogs. */
static const Save5HistoryVersion *history_version(unsigned revision) {
    if(revision==5)return &save5_policy5_version;
    return revision >= 1 && revision <= 4 ? &save5_history_versions[revision] : 0;
}
static const Save5HistoryItem *history_item(unsigned id, unsigned revision) {
    const Save5HistoryVersion *v = history_version(revision);
    unsigned row;
    if(revision==5)for(row=0;row<6;++row)if(save5_policy5_items[row].id==id)return &save5_policy5_items[row];
    if (!v || id >= sizeof save5_history_item_source) return 0;
    row = save5_history_item_source[id];
    return row && row <= v->item_count ? &save5_history_items[row - 1u] : 0;
}
static const Save5HistoryQuest *history_quest(unsigned id) {
    return id<30?&save5_history_quests[id]:&save5_policy5_quests[id-30];
}
static const Save5HistoryRoom *history_room(unsigned id) {
    return id<38?&save5_history_rooms[id]:&save5_policy5_rooms[id-38];
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
    room = history_room(c->room);
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
        if (i < (revision==5?4u:3u) && (q->anchors[i] & ~q->region_flags[i])) return 0;
    }
    for (i = 0; i < (revision==5?4u:3u); ++i)
        if (q->region_flags[i] && !(q->region_flags[i] & 1u)) return 0;
    if(revision==5 && (q->region_flags[19] & (q->region_flags[19]+1u)))return 0;
    return 1;
}
static int history_quest_campaign_validate(const CampaignSave *c, const Save5Quests *q,
                                           unsigned revision) {
    const Save5HistoryVersion *v = history_version(revision);
    const Save5HistoryRoom *room;
    unsigned i, j;
    if (!v || c->room > v->last_room) return 0;
    room = history_room(c->room);
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
    if(revision==5 && !magma_quest_campaign_validate(q))return 0;
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
        p = i<25?&save5_history_items[i]:&save5_policy5_items[i-25];
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
        (revision!=5 || magma_roster_sources_validate(&s->quests,&s->roster)) &&
        (revision == 1 ? history_starter_validate(&s->equipment) :
         history_equipment_validate(&s->quests, &s->equipment, revision));
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
        southern_sources_validate(&s->quests, s->roster.obtained, southern_roster_evidence(&s->roster)) &&
        magma_roster_sources_validate(&s->quests,&s->roster) &&
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
    unsigned retained_creatures, southern_evidence; /* checked per-individual evidence */
    MagmaEvidence magma;
    unsigned pending_quest_check;
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
        (get16(b + 12) < 1 || get16(b + 12) > SAVE5_CONTENT_REVISION) ||
        b[20] != (scan.memory ? 0 : SAVE5_COMMIT) ||
        !zero_bytes(b + 14, 2) || !zero_bytes(b + 21, 11)) return 0;
    scan.expected_crc = get32(b + 16); scan.sequence = get32(b + 8);
    scan.revision = get16(b + 12);
    return 1;
}
static int revision_form_allowed(unsigned id) {
    return creatures_form_allowed_revision(id, scan.revision);
}
static int revision_equipment_allowed(unsigned id) {
    return history_item(id, scan.revision) && (!scan.memory || equipment_definition(id));
}
static int scan_collection(void) {
    unsigned i;
    /* Collection discovery is revisioned content, not permission to use a
     * reserved form. Reward bits remain an explicit 128-bit authored ledger. */
    for (i = 0; i < 128; ++i) {
        if (bit(scan.collection, i) && (!revision_form_allowed(i + 1) ||
            (scan.memory && !creatures_form(i + 1)))) return 0;
        if (bit(scan.collection + 16, i) && !bit(scan.collection, i)) return 0;
    }
    return 1;
}
static int scan_instance(unsigned slot) {
    CreatureInstance c;
    unsigned i, legacy;
    Save4U8 *ids = scratch.bytes + SAVE5_RESERVED_OFFSET;
    decode_instance(&c, scan.block);
    if (!creatures_instance_validate_revision(&c, scan.revision) ||
        (scan.memory && !creatures_instance_validate(&c))) return 0;
    if (!(c.flags & CREATURE_OCCUPIED)) return 1;
    if (!bit(scan.collection + 16, c.form_id - 1)) return 0;
    for (i = 0; i < slot; ++i)
        if (get32(ids + i * 4) == c.instance_id) return 0;
    put32(ids + slot * 4, c.instance_id);
    set_bit(scan.occupied, slot);
    scan.retained_creatures |= history_retained_evidence(&c);
    scan.southern_evidence |= history_southern_evidence(&c);
    if(scan.revision==5)magma_instance_evidence(&scan.magma,&c);
    if (c.instance_id > scan.max_id) scan.max_id = c.instance_id;
    legacy = creatures_legacy_spirit_revision(c.form_id, scan.revision);
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
    if (!history_equipment_record_validate(r, scan.revision) ||
        (scan.memory && !equipment_record_validate(r))) return 0;
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
    if(scan.pending_quest_check && budget) {
        scan.pending_quest_check=0;
        if (!history_quest_fields_validate(&scan.quests, scan.revision) ||
                    !history_quest_campaign_validate(&scan.campaign, &scan.quests, scan.revision) ||
                    !history_creatures_validate(&scan.quests, scan.collection + 16, scan.collection + 32,
                                               scan.retained_creatures, scan.southern_evidence) ||
                    (scan.revision==5 && !magma_sources_validate(&scan.quests,scan.collection+16,&scan.magma)) ||
                    (scan.memory && (!quest_fields_validate(&scan.quests) ||
                     !quest_campaign_validate(&scan.campaign, &scan.quests) ||
                     !quest_creatures_validate(&scan.quests, scan.collection + 16, scan.collection + 32,
                                               scan.retained_creatures) ||
                     !southern_sources_validate(&scan.quests, scan.collection + 16, scan.southern_evidence)))) scan.valid = 0;
        /* Exactly one bounded semantic pass; never a full-roster scan. */
        return budget;
    }
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
                if (!history_campaign_validate(&c, scan.revision) ||
                    (scan.memory && !save5_campaign_validate(&c)) ||
                    !zero_bytes(scan.block+15, 49)) scan.valid = 0;
                scan_next(SCAN_COLLECTION, 48); charge = 32; break;
            }
            case SCAN_COLLECTION:
                if (!scan_collection()) scan.valid = 0;
                scan_next(SCAN_COLLECTION_RESERVED, 16); charge = 128; break;
            case SCAN_COLLECTION_RESERVED:
                scan.slot = 0; scan_next(SCAN_INSTANCE, 24); break;
            case SCAN_INSTANCE:
                /* Revision-qualified policy and Southern per-copy evidence add
                 * semantic work. Charge it explicitly without raising the cap. */
                charge = scan.block[0] ? 160 : 16;
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
                if (!history_objective_validate(&scan.quests, scan.slot, scan.revision) ||
                    (scan.memory && !quest_objective_validate(&scan.quests, scan.slot))) scan.valid = 0;
                ++scan.slot;
                scan_next(scan.slot == 64 ? SCAN_QUEST_REWARDS : SCAN_QUEST_OBJECTIVE,
                          scan.slot == 64 ? 8 : 2); charge = 16; break;
            case SCAN_QUEST_REWARDS:
                copy_bytes(scan.quests.rewards, scan.block, 8);
                for (i = 0; i < 8; ++i)
                    if (!history_reward_validate(&scan.quests, i) ||
                        (scan.memory && !quest_reward_validate(&scan.quests, i))) scan.valid = 0;
                scan_next(SCAN_QUEST_VARIABLES, 64); charge = 128; break;
            case SCAN_QUEST_VARIABLES:
                copy_bytes(scan.quests.variables, scan.block, 64);
                scan_next(SCAN_QUEST_FLAGS, 32); break;
            case SCAN_QUEST_FLAGS:
                copy_bytes(scan.quests.region_flags, scan.block, 32);
                scan_next(SCAN_QUEST_ANCHORS, 16); break;
            case SCAN_QUEST_ANCHORS:
                copy_bytes(scan.quests.anchors, scan.block, 16);
                /* Defer the bounded causal pass to a fresh update. Copying
                 * the final anchor byte must not append a chapter-wide check
                 * to an otherwise full byte-work slice. The conservative
                 * charge exhausts this call without pretending bytes moved. */
                scan.pending_quest_check=1;
                scan_next(SCAN_BOND,160);charge=budget-used;break;
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
                if (!history_equipment_refs_validate(&scan.equipment, scan.revision) ||
                    (scan.memory && !equipment_refs_validate(&scan.equipment))) scan.valid = 0;
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
                if (!history_equipment_claims_validate(&scan.quests, &scan.equipment, scan.revision) ||
                    (scan.memory && !quest_equipment_validate(&scan.quests, &scan.equipment))) scan.valid = 0;
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
static unsigned decode_valid_bank(Save5State *s, unsigned offset, Save4U32 sequence) {
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
    if (revision == 1) history_starter_init(&s->equipment);
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
    return revision;
}
static int load_internal(Save5State *out) {
    CampaignSave legacy;
    int active;
    bank_valid[0] = (unsigned)scan_bank(SAVE5_BANK_A, &bank_sequence[0]);
    bank_valid[1] = (unsigned)scan_bank(SAVE5_BANK_B, &bank_sequence[1]);
    active = newest_bank();
    if (active >= 0) {
        unsigned revision = decode_valid_bank(&scratch.state,
            active ? SAVE5_BANK_B : SAVE5_BANK_A, bank_sequence[active]);
        if (!save5_validate_revision(&scratch.state, revision)) return 0;
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
