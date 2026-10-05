# Save format 5, content revision 2

## Compatibility

The two 6,144-byte banks remain at SRAM `0x0200` and `0x1A00`, ending at
`0x3200`. No write touches `0x0000–0x01FF`, including legacy v2/v3 data and both
v4 banks. No offsets, creature records or credit-ledger positions moved.

New writes use **content revision 2**. Revision 1 is decoded explicitly, with
its original eight-form whitelist (1, 2, 4, 5, 7, 8, 10, 11), zero quest and
zero equipment allocations. Migration retains all creatures, identities, XP,
bond, evolutions, learned/equipped commands, selected command, collection,
party, expedition counters and event credits. It adds only the protected
Wayfarer Sword in bag slot 0; no quest, regional progress or rare item is
fabricated. Unknown future revisions and unknown content IDs reject that bank.
They are never normalized into placeholder creatures or equipment.

When neither v5 bank validates, the unchanged v4/v3/v2 reader is used. It
preserves every decoded campaign field and synthesizes the unlocked legacy
story families using the existing creature migration rules. Loading and
migration are read-only. A later successful transaction writes revision 2 in
the new address range, leaving the previous active bank and all legacy bytes
intact. Older ROMs can see only their untouched old checkpoint, not newer
progress; downgrade synchronization is unsupported.

## Wire layout

All multibyte fields are explicitly little endian. Runtime structs, padding,
pointers and derived statistics are never the serialization format.

| Offset | Bytes | Meaning |
|---:|---:|---|
| 0 | 2 | `45 42` magic |
| 2 | 1 | Format version 5 |
| 3 | 1 | Header size 32 |
| 4 | 2 | Bank size 6,144 |
| 6 | 2 | Used allocation 5,056 |
| 8 | 4 | Unsigned generation |
| 12 | 2 | Content revision 2; explicit revision-1 reader retained |
| 14 | 2 | Zero reserved |
| 16 | 4 | IEEE CRC32 |
| 20 | 1 | Commit marker `A5`, zero while constructing |
| 21 | 11 | Zero reserved |
| 32 | 64 | Campaign |
| 96 | 64 | Seen16, obtained 16, creature-reward 16, reserved 16 |
| 160 | 3,840 | 160 explicit 24-byte creature instances |
| 4,000 | 32 | Party/settings |
| 4,032 | 512 | Typed quests 264 + creature credits 240 + reserved 8 |
| 4,544 | 512 | Typed equipment |
| 5,056 | 1,088 | Zero padding, covered by CRC |

CRC polynomial is `0xEDB88320`, initial state and final XOR `FFFFFFFF`.
`123456789` produces `CBF43926`. Bytes16–20 (CRC and commit) are treated as zero
for CRC calculation, including committed banks. The 1-KiB CRC table is ROM.

### Campaign

Relative offsets: room 0, spawn 1, chapter 2, bridge 3, torches 4, relic 5, camp 6,
optional flags 7, room flags 32 at 8, story-seen 16 at 12, legacy companion 14;
bytes 15–63 are zero. Every old progression flag is retained.

Pending Core ending resumes at village/elder. Once `ENDING_SEEN` is set,
revision 2 retains an otherwise valid checkpoint rather than forcing every
postgame resume back to the elder. Missing Wind/Stone story conversations still
normalize safely. Revision-1 and older migrations retain conservative original
resume behavior. Room/spawn validation is explicit; holes do not become valid
merely because a larger room ID exists.

### Creatures and party

Each 24-byte creature has form 0, flags 1, level2, bond 3, XP32 at 4, instance ID32
at 8, nickname16 at 12, personal trial16 at 14, commands 16/17, polarity 18, selected
command 19 and cosmetic seed32 at 20. Empty records are entirely zero. Content
validation checks XP-derived level, learned commands, family trial bits,
evolution level and polarity; no arbitrary combat stat is persisted.

Roster IDs are unique and nonzero, below next-instance ID. Obtained must be a
subset of seen, owned forms must be obtained, and the first four story-reward
bits exactly match story-locked families. Only enabled revision-specific forms
may appear in seen/obtained. Existing 128-bit creature reward history remains
unchanged.

Party bytes 0–3 are roster indices (255 empty), byte 4 selects a party position
(255 only if party empty), bytes 5–7 are zero, next-instance ID32 is at 8, and
bytes 12–31 are zero. References are unique and occupied. IDs never wrap/reuse;
`FFFFFFFF` is the exhausted sentinel.

### Quest block

Relative offsets inside the shared block:

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 16 | Two-bit quest states for 64 IDs |
| 16 | 128 | 64 little-endian objective masks16 |
| 144 | 8 | Claimed quest reward ledger |
| 152 | 64 | Authored quest variables |
| 216 | 32 | Authored region flags |
| 248 | 16 | Discovered anchors |
| 264 | 160 | Per-instance expedition bond, each0–10 |
| 424 | 64 | Shared512-event expedition credit bitmap |
| 488 | 16 | Permanent128-event first-field-aid bitmap |
| 504 | 8 | Zero reserved |

`Save5Quests` is exactly 264 bytes. `save5_quest_state` and
`save5_quest_set_state` read/write the two-bit state. Values are INACTIVE 0,
ACTIVE 1, READY 2, CLAIMED 3. Disabled IDs and unassigned bits are rejected.
INACTIVE has no objectives; ACTIVE is incomplete; READY/CLAIMED have the exact
authored objective mask. The quest reward bit must match CLAIMED. Empty
creature slots must have zero expedition bond counters.

### Authored regional contract

`assets/region/contract.json` is the schema-1 authoring contract. Quest IDs 0–10
are enabled;11–63 are zero. All regional quest activity requires Grove-clear
and town-visited. The authored objective masks and rewards are:

| Quest | Mask | Reward link |
|---:|---:|---|
| 0, workshop practice | 7 | Equipment source 6, Patchwork Mail33 |
| 1, dry road home | 3 | Source 8, Trail Boots49 |
| 2, reed basin bond | 7 | Creature reward 5, Water form 13/evolved14 |
| 3, bell foundry bond | 7 | Creature reward 6, Metal form 16 |
| 4, paired tide pools | 3 | Source 5, Tidewood Bow18 |
| 5, hidden nook | 1 | Source 10, Woven Belt65 |
| 6, four friendships | 1 | Both source 3 Copperleaf Lance10 and source 12 Steady Ring82 |
| 7, tuning latch | 1 | Source 1, Reedguard Sword2 |
| 8, hearthplate craft | 3 | Source 7, Hearthscale Mail34 |
| 9, surestep garden | 7 | Source 9, Surestep Boots50 |
| 10, resonance repair | 1 | Source 11, Resonance Ring81 |

Only variables 3 and9 are assigned, each0–3 while its matching quest is active,
ready or claimed; both must be zero while unseen. Full objective masks determine
READY/CLAIMED; variable 3 is not additionally required. Region byte 0 permits bits
0–5 for visited rooms 16–21, with town bit 0 required for any visit; all other
region bytes are zero. Anchor byte 0 permits town-rest bit 0 and basin-rest bit 1,
each implying that room's visit; other anchor bytes are zero.

Safe regional checkpoint rooms/spawns are16:0–5,17:0–2,18–21:0. All require
Grove-clear and the current room's visit bit. Rooms18/19 additionally require
quest 2 CLAIMED. Rest spawn 2 in 16/17 requires its matching discovered anchor.
Rooms14/15 remain separate personal trials, not regional save checkpoints;
22+ and all other holes remain rejected. Exact world coordinates live in the
contract and are the region engine's responsibility.

A claimed creature quest requires the matching creature reward bit and obtained
history for its authored family, checked against the actual enabled native
catalog. If that form is unavailable, the claim is rejected. Evolution and
party/storage changes do not revoke earned collection history. Legacy creature
reward bits are preserved independently and never synthesize quest completion.

### Equipment block

Relative offsets:

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 384 | 48 non-compacting8-byte bag records |
| 384 | 5 | Weapon/body/boots/belt/ring bag references |
| 389 | 11 | Zero settings reserve |
| 400 | 64 | Seen-item bitmap, bit equals exact item ID |
| 464 | 16 | Zero wallet/key reserve |
| 480 | 8 | Equipment-source claim bitmap |
| 488 | 24 | Zero reserved |

Each record encodes item ID16 at 0, rank at 2, flags at 3, quantity at 4, and zero
bytes 5–7. Empty records are all zero. Authored item IDs are
1,2,9,10,17,18,33,34,49,50,65,81,82. Rank must be zero, quantity one, and flags
must match the definition. No derived HP/attack/defense/speed or affix statistic
is saved. Unique items cannot appear twice. Every owned item must be seen, but
seen history does not create an owned item after discard.

Bag0 always holds protected starter sword1. References are0–47 or255 empty,
match each slot's authored type, and cannot alias incompatible items. The
weapon cannot be empty; unequip falls back to bag0. Seen bit 0 is forbidden.

Equipment source IDs 0–12 map to the authored item list above;13–63 are reserved.
A source claim requires the matching seen-item bit. Starter source 0 is marked
by initialization/migration. Free lance/bow rack sources 2/4 require town-visited;
every other source must exactly agree with its mapped claimed quest. Quest 6
commits both mapped equipment sources together. Quest reward IDs are a separate
namespace. These are consistency checks, not cryptographic authentication.
Quest completion and all mapped equipment claims must be staged/saved together.

## Bounded transaction

`save5_begin` snapshots the complete **4,944-byte** runtime state. It checks the
small campaign contract only, performs no SRAM I/O or CRC, and retains no caller
pointer. A busy begin is refused without replacing the pending transaction.
The caller may change its copy immediately after success.

Semantic validation is incremental and may report FAILED after begin. No SRAM
write occurs until the entire snapshot is valid. Quest objectives are checked
one at a time; equipment records and seen bytes are checked individually. The
streaming pass never calls the full inventory validator. Cheap slot checks,
bounded ledger checks and conservative work charges distribute validation
across updates instead of making one inventory-sized spike.

One static 6-KiB union holds the immutable snapshot and canonical wire bank.
The 1,088-byte trailing reserve temporarily packs exactly campaign 15 + party 5 +
next-ID 4 + collection 48 + creature credits 240 + quest 264 + equipment 512. Typed
quest/objective and item fields are encoded explicitly and incrementally;
creatures then encode backwards in place. Old-bank scans temporarily reuse
canonical padding for an instance-ID index. All padding is zeroed before CRC
and SRAM writes. There is no second full-bank/roster snapshot on the stack.

Call `save5_step` once per display update. Zero is quiet; budgets are capped at
**3,072 byte/work units**. The engine's dedicated light-rendering SAVE_PENDING
mode uses 3,072. The lower 1,024 helper budget remains available. Avoid combining
begin and a large step in one heavy frame.

1. Encode and semantically validate the snapshot incrementally
2. Read, CRC-check and semantically validate both old banks incrementally
3. Select the older/inactive bank; generation is current+1, or 1
4. Zero padding and calculate snapshot CRC incrementally
5. Invalidate only destination commit; read back invalidation
6. Write 6,143 content bytes in bounded chunks
7. Compare every destination byte with the snapshot before committing
8. Write commit marker last
9. Compare all 6,144 bytes again; only then report DONE

There are exactly 6,145 durable writes. The prior active bank remains unchanged.
Before commit a power cut selects the old bank; after commit it selects the
complete new bank even if final acknowledgment/readback has not occurred.
FAILED never means the old bank was erased. A failed reward commit must leave
authoritative game RAM and quest READY unchanged; publish staged reward state
and its success dialogue only after DONE. Retry uses the same complete staged
state and cannot grant another copy.

Unsigned generation wrap is deterministic: `FFFFFFFF -> 00000000` is newer;
equal generations and exact half-range gaps choose bank A. Invalid banks can
short-circuit scans; completion status, not progress percentage, is decisive.
Caller version/generation metadata is not mutated; reload if needed.

`save5_store`, `save5_load`, `save5_has_valid` and full `save5_validate` are
blocking host/startup/transition helpers, not active-play tick operations.
Load/has-valid refuse while the writer owns the shared scratch space.

## Verification and reproducible measurements

    python3 tests/test_save5.py
    python3 tests/test_save4.py
    python3 tests/test_save5.py --arm-timing --mgba-tools <bridge-directory> --output build/save5-timing

The suite covers all 6,145 interruption positions in first migration and both
replacement directions, each individually corrupted write, every byte of
either bank corrupted, future/old revisions, CRC-valid malformed records,
duplicate item/creature references, immutable snapshots, tiny/huge budgets,
commit visibility, retries, full 160-creature rosters and all 13 authored items.

`tests/fixtures/v5-revision1/all-evolved-village.sav` is an unchanged,
SHA256-pinned controller-only C4-final SRAM fixture. Its paired provenance
identifies the source ROM/report and confirms no game-RAM injection. Migration
asserts exact preservation of its full collection/creature/party wire span and
all creature-credit bytes, including its four evolved forms and commands.
Synthetic malformed-bank tests are codec tests, not gameplay evidence.

ARM timing uses real emulated ARM7TDMI code, cascaded GBA timers and the engine's
WAITCNT 0x4317. It is an isolated subsystem benchmark, not proof of complete
engine frame cadence or physical hardware performance. Final numbers are
recorded beside exact source hashes and compiler stack usage in the JSON report.

Measured revision-2 regional-policy build, 2026-10-05 (`-Wall -Wextra -Werror`):

| Operation | Maximum cycles | 280,896-cycle frame |
|---|---:|---:|
| begin, all tested roster sizes | 21,627 | 7.7% |
| step requested 1,024 | 64,636 | 23.0% |
| step requested 3,072 | 190,386 | 67.8% |
| step requested 4,096, clamped 3,072 | 190,382 | 67.8% |

Fifteen scenarios cover empty/one/two valid old banks, 2/4/160 creatures, mixed
and evolved rosters, and all 13 authored equipment items with their nine mapped
gear quests claimed. At 3,072, four-creature/two-bank writes take 23 updates;
full 160-creature/all 13-item/two-bank writes take 39. At 1,024 they take 66 and 115.
The 3,072 maximum leaves 90,510 cycles for the dedicated mode's other work; the
complete game still requires its own integration cadence measurement.

The save5 object contributes **11,380 bytes ROM**, **7,240 bytes EWRAM**, and
**zero IWRAM code**. EWRAM includes the single 6,144-byte scratch union and 1,096
bytes of streaming state. The unchanged 4,944-byte caller state is counted
separately: 12,184 bytes combined. Maximum compiler-reported individual stack
frame is 120 bytes (`scan_run`), not a claim about whole-engine stack high-water.
No full bank/roster lives on the GBA stack.

The 25-test host save5 suite and unchanged 26-test save4 suite pass. Native
ASan/UBSan also passes 1,000 full 160-creature/all 13-item/claimed-gear-quest
asynchronous save/load cycles with random 0–4,096 requested budgets and no memory
or undefined-behavior finding (sandbox leak detection disabled). Reproduce via
`tests/save5_sanitizer.c` with the save4/save5/creature/equipment modules and
`SAVE4_HOST_TEST`, `SAVE5_HOST_TEST`, `-fsanitize=address,undefined`.

These measurements precede future Water/Metal catalog enablement. Quest 2/3
CLAIMED and gated rooms 18/19 intentionally remain rejected until the matching
native form definitions exist. Repeat the same suite/timing after catalog
changes; adding a form row is not evidence that its gameplay/art is complete.
