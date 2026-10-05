#ifndef EMBERBOND_SAVE4_H
#define EMBERBOND_SAVE4_H

/* Freestanding ARM7TDMI and host-test API. No pointer or C struct layout is
 * persisted. New games use a zero-initialized CampaignSave; save4_store chooses
 * the next generation from SRAM, never from the caller's metadata. */
typedef unsigned char Save4U8;
typedef unsigned short Save4U16;
typedef unsigned int Save4U32;

enum {
    SAVE4_GROVE_CLEAR = 1u, SAVE4_SKY_CLEAR = 2u,
    SAVE4_CORE_CLEAR = 4u, SAVE4_ENDING_SEEN = 8u,
    SAVE4_SPAWN_SOUTH = 0, SAVE4_SPAWN_NORTH = 1,
    SAVE4_SPAWN_CAMP = 2, SAVE4_SPAWN_ELDER = 3,
    SAVE4_SPAWN_EAST_TRAIL = 4, SAVE4_SPAWN_WEST_TRAIL = 5,
    SAVE4_SKY_BRIDGE = 1u << 0, SAVE4_SKY_VANE = 1u << 1,
    SAVE4_SKY_PATROL_CLEAR = 1u << 2, SAVE4_RELAY_LEFT = 1u << 3,
    SAVE4_RELAY_RIGHT = 1u << 4, SAVE4_RELAY_FIRE = 1u << 5,
    SAVE4_CORE_PATH_OPEN = 1u << 6, SAVE4_WEIGHT_WEST = 1u << 7,
    SAVE4_WEIGHT_EAST = 1u << 8, SAVE4_WELL_UNCAPPED = 1u << 9,
    SAVE4_ROOT_CHANNEL = 1u << 10, SAVE4_THORNS_BURNED = 1u << 11,
    SAVE4_LAMP_FIRE = 1u << 12, SAVE4_LAMP_NATURE = 1u << 13,
    SAVE4_LAMP_WIND = 1u << 14, SAVE4_LAMP_STONE = 1u << 15,
    SAVE4_RIDGE_CHIME = 1u,
    SAVE4_SEEN_LEGACY_RECAP = 1u << 0, SAVE4_SEEN_WIND_JOIN = 1u << 1,
    SAVE4_SEEN_SKY_INTRO = 1u << 2, SAVE4_SEEN_STONE_JOIN = 1u << 3,
    SAVE4_SEEN_CORE_INTRO = 1u << 4, SAVE4_SEEN_CORE_RELEASE = 1u << 5,
    SAVE4_SEEN_CHIME = 1u << 6,
    SAVE4_BANK_A = 0x40, SAVE4_BANK_B = 0x80, SAVE4_BANK_SIZE = 32
};

typedef struct CampaignSave {
    Save4U8 room, spawn, chapter_flags, bridge, torches, relic, camp;
    Save4U32 room_flags;
    Save4U8 optional_flags;
    Save4U16 story_seen;
    Save4U8 spirit;
    /* Output-only metadata; sequence is zero for legacy, version is 2/3/4.
     * A successful store does not mutate the caller; reload if needed. */
    Save4U32 sequence;
    Save4U8 loaded_version;
} CampaignSave;

/* Read-only. Failure leaves *out unchanged. Reward scenes pending on load and
 * every CORE_CLEAR resume use village/elder; no completion bit is revoked.
 * A valid legacy payload is decoded in full before the caller can enter rooms.
 * Set quest_started=1 in the game for ANY valid load (not stored in v4). */
int save4_load(CampaignSave *out);
int save4_has_valid(void);

/* Returns 1 only after a complete readback validates. Writes only the older or
 * inactive 32-byte bank; legacy bytes 0..12 and the current bank are untouched.
 * SRAM hardware can lose power after any individual byte write. */
int save4_store(const CampaignSave *data);

/* Bitmask of Homura/Midori/Fuuri/Kohaku: 3, 7, or 15 for valid chapters.
 * Unlocks never depend on whether a reward conversation has finished. */
unsigned save4_unlock_mask(unsigned chapter_flags);
unsigned save4_max_hp(const CampaignSave *data);
Save4U16 save4_crc16(const Save4U8 *bytes, unsigned length);

#ifdef SAVE4_HOST_TEST
/* Host-simulated SRAM ONLY. These symbols do not exist in a cartridge build.
 * Copy .sav fixtures into this array; never inject game RAM for these tests. */
extern Save4U8 save4_test_sram[256];
/* Permit exactly count writes, then fail; -1 permits all writes. Reset count. */
void save4_test_fail_after(int count);
unsigned save4_test_write_count(void);
/* Corrupt one zero-based write, including the final commit, for readback QA.
 * Use index=-1 to disable. This setting does not reset the write counter. */
void save4_test_corrupt_write(int index, Save4U8 xor_mask);
#endif
#endif
