#include "save5.h"

typedef char save5_u32_width[(sizeof(Save4U32) == 4) ? 1 : -1];
typedef char save5_instance_width[(sizeof(CreatureInstance) == 24) ? 1 : -1];
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
    if (s->room > 13 || s->spawn > SAVE4_SPAWN_WEST_TRAIL ||
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
    if (s->room >= 9 && !(chapter & SAVE4_SKY_CLEAR)) return 0;
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

static void normalize_resume(CampaignSave *s) {
    if ((s->chapter_flags & SAVE4_CORE_CLEAR) ||
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
int save5_validate(const Save5State *s) {
    if (!s || !save5_campaign_validate(&s->campaign) ||
        !creatures_roster_validate(&s->roster) ||
        !zero_bytes(s->quest_reserved, sizeof s->quest_reserved) ||
        !zero_bytes(s->equipment_reserved, sizeof s->equipment_reserved)) return 0;
    return 1;
}
/* Preserve small metadata above the used wire allocation, then move each
 * explicit 24-byte instance backwards into its wire position. This transforms
 * the immutable runtime snapshot in place without a second roster buffer. */
static void snapshot_metadata(void) {
    Save5State *s = &scratch.state;
    Save4U8 *b = scratch.bytes + SAVE5_RESERVED_OFFSET;
    clear_bytes(b, 320);
    encode_campaign(b, &s->campaign);
    copy_bytes(b + 16, s->roster.party, 4);
    b[20] = s->roster.selected_party;
    put32(b + 24, s->roster.next_instance_id);
    copy_bytes(b + 32, s->roster.seen, 16);
    copy_bytes(b + 48, s->roster.obtained, 16);
    copy_bytes(b + 64, s->roster.rewards, 16);
    copy_bytes(b + 80, s->roster.expedition_bond, 160);
    copy_bytes(b + 240, s->roster.expedition_events, 64);
    copy_bytes(b + 304, s->roster.lifetime_field_aid, 16);
}
static void snapshot_finish(void) {
    Save4U8 *b = scratch.bytes, *m = b + SAVE5_RESERVED_OFFSET;
    clear_bytes(b, 160);
    b[0] = 0x45; b[1] = 0x42; b[2] = 5; b[3] = 32;
    put16(b + 4, SAVE5_BANK_SIZE); put16(b + 6, SAVE5_USED_SIZE);
    put16(b + 12, SAVE5_CONTENT_REVISION);
    copy_bytes(b + 32, m, 15);
    copy_bytes(b + 96, m + 32, 48);
    clear_bytes(b + 4000, 1056);
    copy_bytes(b + 4000, m + 16, 12);
    copy_bytes(b + 4296, m + 80, 160);
    copy_bytes(b + 4456, m + 240, 64);
    copy_bytes(b + 4520, m + 304, 16);
}

/* Streaming validation is shared by loader and writer. There is never a
 * second full bank/roster allocation or a full-bank CRC hidden in begin(). */
typedef struct BankScan {
    Save4U8 block[64], collection[48], occupied[20];
    Save4U32 crc, expected_crc, sequence, max_id;
    unsigned offset, position, valid, story_mask, stage, boundary, base, slot, memory;
} BankScan;
static BankScan scan;
static unsigned writer_status, writer_phase, writer_position, writer_progress;
static unsigned writer_destination, bank_valid[2];
static Save4U32 bank_sequence[2], writer_crc;
enum { PHASE_META, PHASE_ENCODE, PHASE_FINISH, PHASE_CHECK_SNAPSHOT, PHASE_SCAN_A, PHASE_SCAN_B, PHASE_PREPARE, PHASE_CRC,
       PHASE_INVALIDATE, PHASE_CHECK_INVALIDATE, PHASE_WRITE, PHASE_VERIFY, PHASE_COMMIT, PHASE_FINAL };

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
        get16(b + 12) != SAVE5_CONTENT_REVISION ||
        b[20] != (scan.memory ? 0 : SAVE5_COMMIT) ||
        !zero_bytes(b + 14, 2) || !zero_bytes(b + 21, 11)) return 0;
    scan.expected_crc = get32(b + 16); scan.sequence = get32(b + 8);
    return 1;
}
static int scan_collection(void) {
    unsigned i;
    /* Collection discovery is revisioned content, not permission to use a
     * reserved form. Reward bits remain an explicit 128-bit authored ledger. */
    for (i = 0; i < 128; ++i) {
        if (bit(scan.collection, i) && !creatures_form(i + 1)) return 0;
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
    if (!(c.flags & CREATURE_OCCUPIED)) return 1;
    if (!bit(scan.collection + 16, c.form_id - 1)) return 0;
    for (i = 0; i < slot; ++i)
        if (get32(ids + i * 4) == c.instance_id) return 0;
    put32(ids + slot * 4, c.instance_id);
    set_bit(scan.occupied, slot);
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
/* Chunk loops avoid per-byte division and phase dispatch on ARM7TDMI.
 * Record checks are charged conservative byte-equivalent work as well. This
 * prevents a full roster from concentrating all validation in one update. */
static unsigned scan_run(unsigned budget) {
    unsigned used = 0;
    while (scan.valid && scan.position < SAVE5_BANK_SIZE && used < budget) {
        unsigned p = scan.position, n = scan.boundary - p, i, any = 0;
        Save4U32 crc = scan.crc;
        unsigned zero = scan.stage == 3 || scan.stage == 6 || scan.stage == 9;
        const volatile Save4U8 *src;
        if (n > budget - used) n = budget - used;
        if (scan.memory && zero && p < SAVE5_RESERVED_OFFSET &&
            p + n > SAVE5_RESERVED_OFFSET) n = SAVE5_RESERVED_OFFSET - p;
        src = scan.memory ? scratch.bytes + p : SRAM + scan.offset + p;
        if (scan.stage == 0) {
            for (i = 0; i < n; ++i) {
                Save4U8 v = src[i];
                scan.block[p + i] = v;
                if (!scan.memory) crc = crc_byte(crc, p+i >= 16 && p+i <= 20 ? 0 : v);
            }
        } else if (scan.stage == 1 || scan.stage == 4 || scan.stage == 5) {
            Save4U8 *dst = scan.block + p - scan.base;
            if (scan.memory) for (i = 0; i < n; ++i) dst[i] = src[i];
            else for (i = 0; i < n; ++i) { Save4U8 v = src[i]; dst[i] = v; crc = crc_byte(crc, v); }
        } else if (scan.stage == 2) {
            Save4U8 *dst = scan.collection + p - 96;
            if (scan.memory) for (i = 0; i < n; ++i) dst[i] = src[i];
            else for (i = 0; i < n; ++i) { Save4U8 v = src[i]; dst[i] = v; crc = crc_byte(crc, v); }
        } else if (scan.stage == 7) {
            for (i = 0; i < n; ++i) {
                Save4U8 v = src[i];
                if (!scan.memory) crc = crc_byte(crc, v);
                if (v > 10 || (v && !bit(scan.occupied, p + i - 4296))) scan.valid = 0;
            }
        } else if (zero) {
            /* Scanner's temporary IDs overlap the memory snapshot's trailing
             * reserve. Those bytes are zeroed before CRC/writes, and never
             * originate in user-controlled persisted fields. */
            if (scan.memory && p >= SAVE5_RESERVED_OFFSET) {
                i = n;
            } else {
                for (i = 0; i < n; ++i) { Save4U8 v = src[i]; any |= v; if (!scan.memory) crc = crc_byte(crc, v); }
                if (any) scan.valid = 0;
            }
        } else if (!scan.memory) {
            for (i = 0; i < n; ++i) crc = crc_byte(crc, src[i]);
        }
        scan.crc = crc; scan.position += n; used += n;
        if (scan.position == scan.boundary) {
            unsigned charge = 0;
            if (scan.stage == 0) {
                if (!scan_header()) scan.valid = 0;
                scan.stage = 1; scan.base = 32; scan.boundary = 96;
            } else if (scan.stage == 1) {
                CampaignSave c;
                decode_campaign(&c, scan.block);
                if (!save5_campaign_validate(&c) || !zero_bytes(scan.block+15, 49)) scan.valid = 0;
                scan.stage = 2; scan.boundary = 144; charge = 32;
            } else if (scan.stage == 2) {
                if (!scan_collection()) scan.valid = 0;
                scan.stage = 3; scan.boundary = 160; charge = 128;
            } else if (scan.stage == 3) {
                scan.stage = 4; scan.base = 160; scan.boundary = 184;
            } else if (scan.stage == 4) {
                charge = scan.block[0] ? 128 : 16;
                if (!scan_instance(scan.slot++)) scan.valid = 0;
                scan.base += 24; scan.boundary += 24;
                if (scan.slot == 160) { scan.stage = 5; scan.base = 4000; scan.boundary = 4032; }
            } else if (scan.stage == 5) {
                if (!scan_party()) scan.valid = 0;
                scan.stage = 6; scan.boundary = 4296; charge = 32;
            } else if (scan.stage == 6) { scan.stage = 7; scan.boundary = 4456; }
            else if (scan.stage == 7) { scan.stage = 8; scan.boundary = 4536; }
            else if (scan.stage == 8) { scan.stage = 9; scan.boundary = SAVE5_BANK_SIZE; }
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
    unsigned i;
    clear_bytes(s, sizeof *s);
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
    normalize_resume(&s->campaign);
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
    if (!s || !save5_campaign_validate(&s->campaign) ||
        !zero_bytes(s->quest_reserved, sizeof s->quest_reserved) ||
        !zero_bytes(s->equipment_reserved, sizeof s->equipment_reserved)) {
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
            snapshot_metadata(); writer_position = 160; writer_phase = PHASE_ENCODE;
            used += available < 64 ? available : 64;
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
            used += available < 256 ? available : 256;
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
