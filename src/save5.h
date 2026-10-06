#ifndef EMBERBOND_SAVE5_H
#define EMBERBOND_SAVE5_H
#include "save4.h"
#include "creatures.h"
#include "equipment.h"

/* v5 never writes SRAM 0..0x1ff, including every v2/v3 byte and both v4 banks.
 * Every multibyte wire field is explicitly little endian.
 * Content revisions are distinct from wire version5: readers accept exactly
 * revision1 (8 forms, reserved quests/gear), revision2 (11 forms/13 items),
 * revision3 (21 forms/19 items, Northern quests11..21/areas22..29), and
 * revision4 (41 forms/25 items, Southern quests22..29/areas30..37). Revision1
 * installs only starter equipment; revision2/3->4 preserves existing typed bytes
 * and adds no recruit, trial, quest, gear, visit or reward on load. All writes
 * use revision4. Unknown revisions and cross-revision content are rejected. */
enum {
    SAVE5_BANK_A = 0x0200, SAVE5_BANK_B = 0x1A00,
    SAVE5_BANK_SIZE = 6144, SAVE5_USED_SIZE = 5056,
    SAVE5_CONTENT_REVISION = 4, SAVE5_COMMIT = 0xA5,
    SAVE5_HEADER_OFFSET = 0, SAVE5_CAMPAIGN_OFFSET = 32,
    SAVE5_COLLECTION_OFFSET = 96, SAVE5_INSTANCES_OFFSET = 160,
    SAVE5_PARTY_OFFSET = 4000, SAVE5_QUEST_OFFSET = 4032,
    SAVE5_EQUIPMENT_OFFSET = 4544, SAVE5_RESERVED_OFFSET = 5056,
    SAVE5_CRC_OFFSET = 16, SAVE5_COMMIT_OFFSET = 20,
    SAVE5_RECOMMENDED_BUDGET = 1024, SAVE5_MAX_BUDGET = 3072,
    SAVE5_IDLE = 0, SAVE5_BUSY = 1, SAVE5_DONE = 2, SAVE5_FAILED = 3
};
enum {
    SAVE5_QUEST_CAPACITY = 64, SAVE5_QUEST_BYTES = 264,
    SAVE5_QUEST_INACTIVE = 0, SAVE5_QUEST_ACTIVE = 1,
    SAVE5_QUEST_READY = 2, SAVE5_QUEST_CLAIMED = 3
};
/* Fixed quest allocation; objectives are explicitly little-endian on wire.
 * State uses two bits per quest. Only authored IDs/masks are accepted. */
typedef struct Save5Quests {
    Save4U8 states[16];
    Save4U16 objectives[64];
    Save4U8 rewards[8], variables[64], region_flags[32], anchors[16];
} Save5Quests;
unsigned save5_quest_state(const Save5Quests *quests, unsigned quest_id);
int save5_quest_set_state(Save5Quests *quests, unsigned quest_id, unsigned state);
int save5_quests_validate(const Save5Quests *quests);

typedef struct Save5State {
    CampaignSave campaign;
    CreatureRoster roster;
    Save5Quests quests;
    EquipmentState equipment;
} Save5State;

/* Read-only, blocking startup/transition operation. Failure leaves out intact.
 * Refuses while a writer owns the static scratch space. If neither v5 bank
 * validates, uses the unchanged v4/v3/v2 decoder and synthesizes only unlocked
 * story creatures. No implicit migration write. Metadata is in campaign. */
int save5_load(Save5State *out);
int save5_has_valid(void);
/* Full blocking validator for host tools/transitions, not active-game ticks. */
int save5_validate(const Save5State *state);
int save5_campaign_validate(const CampaignSave *campaign);

/* begin snapshots the complete state; caller may change it immediately after
 * success. begin performs no SRAM read/write and no CRC. Busy begin is refused
 * without altering the current transaction. Basic validation may reject begin;
 * Roster, quest and equipment validation is incremental and may later return
 * FAILED, before any SRAM write. step counts bytes and conservative semantic-work charges against
 * budget, capped at 3072 (zero does no work), plus bounded record-end checks.
 * Call once per display update, preferably not on the same heavy frame as begin. */
int save5_begin(const Save5State *state);
unsigned save5_step(unsigned byte_budget);
unsigned save5_status(void);
/* Monotonic byte work count, conservative total 6*6144+3. Invalid old banks
 * short-circuit scans, so DONE is authoritative rather than total equality. */
unsigned save5_progress(void);
unsigned save5_progress_total(void);
/* Blocking adapter ONLY for host tests or explicitly paused transitions. */
int save5_store(const Save5State *state);
Save4U32 save5_crc32(const Save4U8 *bytes, unsigned length);

#ifdef SAVE5_HOST_TEST
extern Save4U8 save5_test_sram[32768];
void save5_test_reset_writer(void);
void save5_test_fail_after(int count);
unsigned save5_test_write_count(void);
void save5_test_corrupt_write(int index, Save4U8 xor_mask);
/* Last step's byte work, so host tests verify every requested bound. */
unsigned save5_test_step_work(void);
#endif
#endif
