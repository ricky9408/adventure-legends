#include "save4.h"

/* These width requirements hold for ARM7TDMI and the supported host harness. */
typedef char save4_u16_must_be_16_bits[(sizeof(Save4U16) == 2) ? 1 : -1];
typedef char save4_u32_must_be_32_bits[(sizeof(Save4U32) == 4) ? 1 : -1];

#define COMMIT 0xA5u
#define SKY_PATH (SAVE4_SKY_BRIDGE | SAVE4_SKY_VANE)
#define SKY_PATROL (SKY_PATH | SAVE4_SKY_PATROL_CLEAR)
#define SKY_ALL (SKY_PATROL | SAVE4_RELAY_LEFT | SAVE4_RELAY_RIGHT | SAVE4_RELAY_FIRE)
#define CORE_WEIGHTS (SAVE4_CORE_PATH_OPEN | SAVE4_WEIGHT_WEST | SAVE4_WEIGHT_EAST)
#define CORE_ROOTS (CORE_WEIGHTS | SAVE4_WELL_UNCAPPED | SAVE4_ROOT_CHANNEL | SAVE4_THORNS_BURNED)
#define ALL_LAMPS (SAVE4_LAMP_FIRE | SAVE4_LAMP_NATURE | SAVE4_LAMP_WIND | SAVE4_LAMP_STONE)

#ifdef SAVE4_HOST_TEST
Save4U8 save4_test_sram[256];
static int test_limit = -1, test_corrupt_index = -1;
static unsigned test_writes;
static Save4U8 test_corrupt_mask;
#define SRAM save4_test_sram
void save4_test_fail_after(int count) { test_limit = count; test_writes = 0; }
unsigned save4_test_write_count(void) { return test_writes; }
void save4_test_corrupt_write(int index, Save4U8 xor_mask) {
    test_corrupt_index = index;
    test_corrupt_mask = xor_mask;
}
#else
#define SRAM ((volatile Save4U8 *)0x0E000000)
#endif

static int write_byte(unsigned offset, Save4U8 value) {
#ifdef SAVE4_HOST_TEST
    if (test_limit >= 0 && test_writes >= (unsigned)test_limit) return 0;
    if (test_corrupt_index >= 0 && test_writes == (unsigned)test_corrupt_index)
        value ^= test_corrupt_mask;
    ++test_writes;
#endif
    SRAM[offset] = value;
    return 1;
}

static void read_bytes(Save4U8 *dst, unsigned offset, unsigned size) {
    unsigned i;
    for (i = 0; i < size; ++i) dst[i] = SRAM[offset + i];
}

static Save4U16 read_u16(const Save4U8 *p) {
    return (Save4U16)((Save4U16)p[0] | ((Save4U16)p[1] << 8));
}

static Save4U32 read_u32(const Save4U8 *p) {
    return (Save4U32)p[0] | ((Save4U32)p[1] << 8) |
           ((Save4U32)p[2] << 16) | ((Save4U32)p[3] << 24);
}

static void put_u32(Save4U8 *p, Save4U32 value) {
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (Save4U8)(value >> (8 * i));
}

Save4U16 save4_crc16(const Save4U8 *bytes, unsigned length) {
    unsigned bit;
    Save4U16 crc = 0xFFFFu;
    while (length--) {
        crc ^= (Save4U16)*bytes++ << 8;
        for (bit = 0; bit < 8; ++bit)
            crc = (Save4U16)((crc << 1) ^ ((crc & 0x8000u) ? 0x1021u : 0));
    }
    return crc;
}

unsigned save4_unlock_mask(unsigned chapter_flags) {
    unsigned mask = 3;
    if (chapter_flags & SAVE4_GROVE_CLEAR) mask |= 4;
    if ((chapter_flags & (SAVE4_GROVE_CLEAR | SAVE4_SKY_CLEAR)) ==
        (SAVE4_GROVE_CLEAR | SAVE4_SKY_CLEAR)) mask |= 8;
    return mask;
}

unsigned save4_max_hp(const CampaignSave *data) { return data->relic ? 8u : 6u; }

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

static int validate_fields(const CampaignSave *s) {
    Save4U32 f = s->room_flags;
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
        s->room = 0;
        s->spawn = SAVE4_SPAWN_ELDER;
    }
}

static int decode_bank(unsigned offset, CampaignSave *s) {
    Save4U8 b[SAVE4_BANK_SIZE];
    unsigned i;
    read_bytes(b, offset, SAVE4_BANK_SIZE);
    if (b[0] != 0x45 || b[1] != 0x42 || b[2] != 4 || b[3] != SAVE4_BANK_SIZE ||
        b[4] != COMMIT || save4_crc16(b, 30) != read_u16(b + 30)) return 0;
    for (i = 24; i < 30; ++i) if (b[i]) return 0;
    s->sequence = read_u32(b + 5);
    s->room = b[9]; s->spawn = b[10]; s->chapter_flags = b[11];
    s->bridge = b[12]; s->torches = b[13]; s->relic = b[14]; s->camp = b[15];
    s->room_flags = read_u32(b + 16); s->optional_flags = b[20];
    s->story_seen = read_u16(b + 21); s->spirit = b[23]; s->loaded_version = 4;
    return validate_fields(s);
}

static int decode_legacy(CampaignSave *s) {
    Save4U8 b[13];
    unsigned i, sum;
    /* Snapshot ALL bytes first, including both legacy checksum locations. */
    read_bytes(b, 0, sizeof b);
    if (b[0] != 0x45 || b[1] != 0x42 || b[3] > 3 || b[4] > 1 || b[5] > 3 ||
        b[6] > 1 || b[7] > 1) return 0;
    if (b[2] == 2) {
        sum = 0;
        for (i = 0; i < 8; ++i) sum += b[i];
        if ((Save4U8)sum != b[8]) return 0;
    } else if (b[2] == 3) {
        if (b[8] > 1 || b[9] > 1 || b[10] != (b[8] ? 8 : 6) || b[11]) return 0;
        sum = 0x3D;
        for (i = 0; i < 12; ++i) sum += b[i];
        if ((Save4U8)sum != b[12]) return 0;
    } else return 0;
    s->room = b[3]; s->spawn = SAVE4_SPAWN_SOUTH;
    s->chapter_flags = b[6] ? SAVE4_GROVE_CLEAR : 0;
    s->bridge = b[4]; s->torches = b[5];
    s->relic = b[2] == 3 ? b[8] : 0; s->camp = b[2] == 3 ? b[9] : 0;
    if (s->room == 1 && s->camp) s->spawn = SAVE4_SPAWN_CAMP;
    s->room_flags = 0; s->optional_flags = 0; s->story_seen = 0; s->spirit = 0;
    s->sequence = 0; s->loaded_version = b[2];
    normalize_resume(s);
    return 1;
}

/* Equal and exactly-half-range ambiguous sequences deterministically select A.
 * An ordinary new generation differs by one, including FFFFFFFF -> 00000000. */
static int current_bank(CampaignSave *s) {
    CampaignSave a, b;
    int good_a = decode_bank(SAVE4_BANK_A, &a), good_b = decode_bank(SAVE4_BANK_B, &b);
    if (good_a && good_b) {
        Save4U32 delta = b.sequence - a.sequence;
        if (delta && delta < 0x80000000u) { *s = b; return 1; }
        *s = a; return 0;
    }
    if (good_a) { *s = a; return 0; }
    if (good_b) { *s = b; return 1; }
    return -1;
}

int save4_load(CampaignSave *out) {
    CampaignSave state;
    if (!out) return 0;
    if (current_bank(&state) < 0 && !decode_legacy(&state)) return 0;
    normalize_resume(&state);
    *out = state;
    return 1;
}

int save4_has_valid(void) {
    CampaignSave state;
    return save4_load(&state);
}

static void encode_bank(Save4U8 *b, const CampaignSave *s, Save4U32 sequence) {
    unsigned i;
    Save4U16 crc;
    for (i = 0; i < SAVE4_BANK_SIZE; ++i) b[i] = 0;
    b[0] = 0x45; b[1] = 0x42; b[2] = 4; b[3] = SAVE4_BANK_SIZE; b[4] = COMMIT;
    put_u32(b + 5, sequence);
    b[9] = s->room; b[10] = s->spawn; b[11] = s->chapter_flags;
    b[12] = s->bridge; b[13] = s->torches; b[14] = s->relic; b[15] = s->camp;
    put_u32(b + 16, s->room_flags); b[20] = s->optional_flags;
    b[21] = (Save4U8)s->story_seen; b[22] = (Save4U8)(s->story_seen >> 8); b[23] = s->spirit;
    crc = save4_crc16(b, 30); b[30] = (Save4U8)crc; b[31] = (Save4U8)(crc >> 8);
}

int save4_store(const CampaignSave *data) {
    CampaignSave current, verified;
    Save4U8 b[SAVE4_BANK_SIZE];
    Save4U32 sequence;
    unsigned i, destination;
    int active;
    if (!data || !validate_fields(data)) return 0;
    active = current_bank(&current);
    if (active < 0) {
        /* Read complete legacy state before ANY write, including new games. */
        (void)decode_legacy(&current);
        sequence = 1;
        destination = SAVE4_BANK_A;
    } else {
        sequence = current.sequence + 1u;
        destination = active == 0 ? SAVE4_BANK_B : SAVE4_BANK_A;
    }
    encode_bank(b, data, sequence);
    if (!write_byte(destination + 4, 0)) return 0;
    /* Verify invalidation before replacing a formerly committed bank. */
    if (SRAM[destination + 4] != 0) return 0;
    for (i = 0; i < SAVE4_BANK_SIZE; ++i)
        if (i != 4 && !write_byte(destination + i, b[i])) return 0;
    for (i = 0; i < SAVE4_BANK_SIZE; ++i)
        if (i != 4 && SRAM[destination + i] != b[i]) return 0;
    if (!write_byte(destination + 4, COMMIT)) return 0;
    for (i = 0; i < SAVE4_BANK_SIZE; ++i)
        if (SRAM[destination + i] != b[i]) return 0;
    return decode_bank(destination, &verified) && verified.sequence == sequence;
}
