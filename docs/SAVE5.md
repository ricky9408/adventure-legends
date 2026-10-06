# Save format 5, content revision 4

## Compatibility

The two 6,144-byte banks remain at SRAM `0x0200` and `0x1A00`, ending at
`0x3200`. No write touches `0x0000–0x01FF`, including legacy v2/v3 data and both
v4 banks. No offsets, creature records or credit-ledger positions moved.

New writes use **content revision 4**. Revision 1 is decoded explicitly, with
its original eight-form whitelist (1, 2, 4, 5, 7, 8, 10, 11), zero quest and
zero equipment allocations. Migration retains all creatures, identities, XP,
bond, evolutions, learned/equipped commands, selected command, collection,
party, expedition counters and event credits. It adds only the protected
Wayfarer Sword in bag slot 0; no quest, regional progress or rare item is
fabricated. Unknown future revisions and unknown content IDs reject that bank.
They are never normalized into placeholder creatures or equipment.

Revision 2 retains its exact eleven-form whitelist: the original eight plus
13, 14 and 16. Its original thirteen item IDs and equipment sources 0–12 remain
fixed even when the current catalog resolves more IDs. Northern forms, item
records, seen-item bits, sources 13+, quest IDs 11+, Northern visits/anchors,
and areas 22+ are rejected inside a revision-2 bank. Revision 3 enables exactly
21 forms: 1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 19, 20, 22, 23, 73, 74, 75, 76,
77, 78. Reserved IDs and legendary 121 remain invalid.

Revision 2/3→4 loading preserves every existing campaign, roster, command,
collection, credit, typed quest and equipment byte. It grants no recruit,
trial, quest, item, visit or reward. Only a later successful save changes the
header revision/generation/CRC. These are content revisions inside unchanged
wire version 5; an unknown content revision rejects the bank.

When neither v5 bank validates, the unchanged v4/v3/v2 reader is used. It
preserves every decoded campaign field and synthesizes the unlocked legacy
story families using the existing creature migration rules. Loading and
migration are read-only. A later successful transaction writes revision 4 in
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
| 12 | 2 | Content revision 4; exact readers for revisions 1, 2, 3 retained |
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
revisions 2, 3 and 4 retain an otherwise valid checkpoint rather than forcing every
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
retain their released revision-2 definitions. Northern IDs 11–21 are described
below; Southern IDs 22–29 follow;30–63 are zero. All regional quest activity requires Grove-clear
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
0–5 for visited rooms 16–21, with town bit 0 required for any visit; Northern byte 1 and Southern bytes 2, 8 and 18 are described below. Anchor byte 0 permits town-rest bit 0 and basin-rest bit 1,
each implying that room's visit; Northern anchors use byte 1 and Southern anchors byte 2.

Safe regional checkpoint rooms/spawns are16:0–5,17:0–2,18–21:0. All require
Grove-clear and the current room's visit bit. Rooms18/19 additionally require
quest 2 CLAIMED. Rest spawn 2 in 16/17 requires its matching discovered anchor.
Rooms14/15 remain separate personal trials, not regional save checkpoints;
38+ and all other holes remain rejected; Northern rooms 22–29 and Southern 30–37 are below. Exact world coordinates live in the
contract and are the region engine's responsibility.

A claimed creature quest requires the matching creature reward bit and obtained
history and a retained valid owned instance of its authored family, checked
against the actual enabled native catalog. If that form is unavailable, the claim is rejected. Evolution and
party/storage changes do not revoke earned collection history. Legacy creature
reward bits are preserved independently and never synthesize quest completion.

### Northern revision-3 contract

`assets/northern_region/contract.json` assigns quest IDs 11–21 with masks
`3,7,3,7,7,3,7,7,3,7,15`. Every Northern variable is zero: partial mechanism
arrangements reset on entry, while completed objectives persist. Northern data
requires Sky-clear, Reedhaven visited, and town-visited in region byte 1. The
original Stone/Wind conversation resume normalization and story ownership
rules are unchanged. Mandatory world puzzles must be solvable without selecting
or using an Earth companion; retaining earned story companions remains required
under the existing roster policy.

| Quest | Claim contract |
|---:|---|
| 11 | Creature reward 7; retained Wood form 19/20 |
| 12 | Reward 8; retained Fire 22/23 |
| 13 | Available after 11 CLAIMED; reward 11; retained Metal 77/78 |
| 14 | Reward 9; retained Water 73/74 |
| 15 | Reward 10; retained Earth 75/76 |
| 16 | Recruit 11 CLAIMED; trial 32 and level 16/bond 40; gear source 13 |
| 17 | Recruit 12 CLAIMED; trial 64 and level 17/bond 40; source 14 |
| 18 | Recruit 14 CLAIMED; trial 128 and level 18/bond 45; source 15 |
| 19 | Recruit 15 CLAIMED; trial 256 and level 18/bond 45; both sources 16/17 |
| 20 | Recruit 13 CLAIMED; trial 512 and level 20/bond 50; source 18 |
| 21 | Recruits 11/13 CLAIMED; monotonic objective prefixes 0,1,3,7,15 |

A claimed personal trial requires one valid retained instance of the correct
family to have **both** its trial flag and its level/bond floor. Evidence from
two different copies is not combined. READY has not yet earned those rewards.
The five Northern recruits are ordinary owned companions; they need not occupy
the active four slots, may evolve, and retain identity/commands in storage.
Generic creature reward bits 5–128 keep their existing independent semantics;
retention rules are scoped to the matching typed quest claim.

Region byte 1 bits 0–7 mark rooms 22–29. Bit 0 is required for every other visit;
revision-3 bytes 2–31 are zero. Anchor byte 1 bits 0/1 mark the rest points in rooms 22/23,
respectively, and imply that room's visit; revision-3 bytes 2–15 are zero. Current room
requires its visit bit. Safe spawns are 22:0–4, 23:0–2, 24–29:0; rest spawn 2 in 22/23
also requires its anchor. Both current checkpoint and historical visits to
26–29 require quests 11/13 CLAIMED; 27/28/29 additionally imply quest 21 objectives
1/2/4. Historical gates remain enforced after returning to town.

Evolution context is derived outside persistence: original chapter bits 0–2,
Reed-restored bit 8 from quest 2 CLAIMED, Harbor-ready bit 16 from **both** quests 11
and 13 CLAIMED, and Counterworks-stable bit 32 from quest 21 CLAIMED. These bits
must never be written into `CampaignSave.chapter_flags`; its bit 3 (value 0x08) remains
ENDING_SEEN. Use the explicit creature constants and masks, not family-index
shifts. Region visits do not use `1u << room`; room IDs 32+ need separate regional
storage, and the encounter-credit `room*6` scheme must be audited before 64 areas.

### Southern revision-4 contract

Only revisions 1, 2, 3 and 4 are accepted. Each bank's declared revision is
validated before migration, including immutable form identity, command/minimum
level pairs, family trial masks, incoming evolution minimum and polarity.
Current expanded policy cannot legalize an old record. In particular ability12,
Southern commands23–42 and Southern local trial bits on the wrong historical
family remain invalid. Historical evolved records with otherwise legal zero
trial/bond stay legal: Southern causal checks are never imposed retroactively.

Revision4 adds exactly forms25,26,28,29,79–94 (41 enabled), items4,12,36,52,66,84
(25 enabled), quests22–29, and these region allocations:

| Field | Meaning |
|---|---|
| region byte2 bits0–7 | Visits30–37; every visit requires town30 and Northern Q21 CLAIMED |
| anchors byte2 bits0/1 | Rest anchors30/31; each requires the matching visit |
| region byte8 bits0–7 | Typed field recruits25,28,81,83,87,89,91,93 |
| region byte18 bits0/1 | Loft/Q29 and awning/Q28 discoveries |

Bytes3–7,9–17,19–31 and unassigned anchor bits/bytes remain zero. Quests22–29
use masks3,3,15,7,3,3,3,3. Q24 accepts only prefixes0,1,3,7,15. Q22 CLAIMED
requires retained F028/obtained79 or80 and source19/item4 history; Q23 CLAIMED
requires retained F031/obtained85 or86. No Southern source consumes a generic
creature reward bit. The whole historical reward namespace5–128, event credits
and lifetime-aid bytes are preserved; old aid bits only suppress repeat event
credit and do not block new sources or explicit trial training floors.

All Southern content requires inherited Northern entry gates. Safe spawns are
30:0–4,31:0–3,32–37:0. Rest spawn2 in30/31 additionally requires its anchor.
Current checkpoint and permanent historical visits34–37 require Q22 and Q23
CLAIMED;35/36/37 require Q24 prefix1/3/7 respectively. Both guaranteed base
companions are required by the native Q24 interactions, independently of
command equipment. Scene/reset/escape correctness is the world caller's job.

Field source bit0/1/3/4/5 requires visit31, bit2/7 visit33, and bit6 visit32.
Bit4 additionally requires discovery0; bit6 requires discovery1. Discovery0
requires visit32 and Q29 READY or CLAIMED; discovery1 requires visit32 and Q28
READY or CLAIMED. A full gear bag therefore cannot hide either encounter.
Every claimed source retains its exact enabled family and obtained history,
including stored companions. Seen history alone does not establish a claim.

All ten new families map their own qualified trial key1 to wire mask1. Every
persisted Southern trial and evolved form requires Q22/Q23 CLAIMED, its matching
typed source, and that **same instance's** full trial/level/bond evidence. A
streamed per-individual check rejects undertrained copies before OR-combining
only already-validated source requirements. Old family masks remain unchanged.
Context SOUTH_READY=0x0040 derives from Q22/Q23 CLAIMED; SUNWELL_OPEN=0x0080
from Q24 CLAIMED. Neither is a campaign chapter flag.

`src/southern_quests.h` exposes synchronous event-only helpers. Source0 is
invalid;1=Q22,2=Q23,16–23=field bits0–7. Trial completion takes slot, expected
instance ID, explicit family/key and actual typed source token. It stages a
single24-byte instance, marks that family's trial and raises only missing
training to its floor. Greater values, identity and commands remain untouched.
Wrong identity/family/key/source fails without mutation. Generic credit history
cannot impersonate a typed source. The caller must prove environmental targets,
geometry, scene solution and the same participating identity; these helpers do
not fabricate gameplay-object evidence.

Q22 preflights free roster capacity and stages a512-byte equipment state before
its grant-zero inner recruit. Once grant succeeds, only infallible copies and
quest/source bits remain. Full160 roster, exhausted identity or full inventory
leaves the complete state unchanged and quest READY. No member is overwritten,
no party slot silently replaced, no release API invented. The outer save
transaction must publish that staged state only after DONE; retry retains the
same snapshot and identity.

`tests/fixtures/v5-revision3/northern-all21-town.sav` is the genuine N5 controller
fixture, SHA256 `f4e853c85445b8567263a1a875eba967e552e0dcae30958ca42f39bfec4e4479`,
source ROM `302316c53d6fb9dafa0ecbf9f679c9c39af3a150af3aa78398c368312e50399e`.
Its provenance records a locally frozen candidate with publication pending,
not a published release. Revision3→4 re-save preserves the entire payload from
32 onward, as does the existing revision2 fixture. No load writes SRAM or grants
new Southern content. Revision1 alone retains its original starter/resume
migration exception.

### Equipment block

Relative offsets:

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 384 | 48 non-compacting 8-byte bag records |
| 384 | 5 | Weapon/body/boots/belt/ring bag references |
| 389 | 11 | Zero settings reserve |
| 400 | 64 | Seen-item bitmap, bit equals exact item ID |
| 464 | 16 | Zero wallet/key reserve |
| 480 | 8 | Equipment-source claim bitmap |
| 488 | 24 | Zero reserved |

Each record encodes item ID16 at 0, rank at 2, flags at 3, quantity at 4, and zero
bytes 5–7. Empty records are all zero. Authored item IDs are
1,2,9,10,17,18,33,34,49,50,65,81,82,3,11,19,35,51,83,4,12,36,52,66,84 in stable acquisition
source order (not numeric sort). Revision 2 accepts only the first thirteen. Rank must be zero, quantity one, and flags
must match the definition. No derived HP/attack/defense/speed or affix statistic
is saved. Unique items cannot appear twice. Every owned item must be seen, but
seen history does not create an owned item after discard.

Bag0 always holds protected starter sword1. References are0–47 or255 empty,
match each slot's authored type, and cannot alias incompatible items. The
weapon cannot be empty; unequip falls back to bag0. Seen bit 0 is forbidden.

Equipment source IDs 0–24 map to the authored item list above;25–63 are reserved.
Sources 0–12 are byte-compatible with revision 2;13–18 append the Northern gear;19–24 append Southern.
A source claim requires the matching seen-item bit. Starter source 0 is marked
by initialization/migration. Free lance/bow rack sources 2/4 require town-visited;
every other source must exactly agree with its mapped claimed quest. Quests 6 and19
commit their two mapped equipment sources together. Quest reward IDs are a separate
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

## Revision-4 measured verification

Source-pinned results: `SOUTHERN_SAVE4_VERIFICATION.json`,
`evidence/southern-save-limits-arm-final.json`, and
`evidence/southern-save-limits-sanitizers.json`.

- Existing Save5 suite:41 tests; Southern ledger suite:13; unchanged Save4 suite:26
- Every6,146 durable cut/success position for24 Southern transactions,147,504 positions:
  mixed Q22, one field recruit, all ten trials, all ten evolutions, Crown claim and N5 migration
- Every legal historical generic reward5–128 individually under each revision1/2/3,
 372 collision cases; all old event/aid bytes preserved; new typed sources remain usable
- Actual full160 roster containing all41 forms, all30 quests and all25 authored items
- Synthetic48 unique gear records: Q22 is byte-unchanged FULL and remains READY;
  freeing one synthetic slot permits exactly one mixed claim. These extra IDs never ship
- Production historical stream rejects that synthetic catalog before any SRAM write
- ASan/UBSan:1,200 valid round-trips and1,200 invalid snapshots across79,491 randomized
 budget calls, including2,334 zero-budget and49,013 over-cap calls

ARM7TDMI/GBA timer measurement, WAITCNT0x4317, cap unchanged3072:

| Operation | Maximum cycles | 280,896-cycle frame |
|---|---:|---:|
| begin |21,657|7.71%|
| step1024 |60,321|21.47%|
| step3072, real25 gear |153,114|54.51%|
| step3072, synthetic48 gear |164,858|58.69%|
| requested4096, clamped3072, worst synthetic48 |164,854|58.69%|

The full160/all41/all30 states, both25 real and48 synthetic gear records, take
89/108/127 updates at1024 for two N5 banks, mixed N5/current banks, and two
full160 current banks respectively, or31/38/44 at3072.
These are isolated subsystem measurements, not full-game cadence claims.
The initial occupied-instance charge128 exceeded the1024 benchmark ceiling
(71,504 cycles); charging160 for exact revision checks and source evidence
restores the limit without weakening validation or raising the3072 cap. The
initial report is retained explicitly as an unsuccessful timing comparison.

Production `save5.o`:14,828 ROM bytes,7,248 BSS/EWRAM bytes, zero IWRAM code.
Compared with frozen Northern's13,464/7,244, that is +1,364 ROM and +4 mutable
bytes. Its single6,144-byte scratch allocation remains unchanged; with the
4,944-byte caller state, combined persistence storage is12,192 bytes.
`southern_quests.o`:2,662 ROM bytes and zero mutable globals. Its largest own
compiler frame is568 bytes (mixed claim, including512-byte equipment staging),
while trial completion uses64. `save5`'s largest own frame remains120
(`scan_run`); begin16 and step48. No whole SaveState is placed on the stack.
Reviewed ARM O2 direct-call frame sums are252 bytes for save5_step
(48+120+24+48+12) and788 bytes for southern_quest_claim
(568+72+40+48+48+12). These sums exclude interrupts, indirect calls and runtime
helper frames; they are not whole-program stack high-water measurements.

### Rest-entry validation optimization

The scene2 controller trace exposed two rest-entry updates at411,452 and398,657
cycles, with148 updates/flips over150 hardware frames. Steady save steps were
within budget; the synchronous anchor validation contributed244,641 cycles on
the11-individual N5-derived entry state.

`profile_southern_validation.py` builds only isolated profiling ROMs. Before
optimization, the11-instance cost comprised136,540 cycles for roster validation,
58,215 for Southern evidence,15,361 for quest validation,16,647 for equipment,
and the remaining campaign/ledger checks. Empty records were needlessly tested
against all ten Southern families and checked one byte at a time in the core.

The core now checks all24 bytes of an empty instance with six alias-safe aligned
word loads, with a portable fieldwise fallback; no field/padding check is lost.
Southern source rows use an explicit bounded lookup and an empty fast path.
These changes introduce no mutable cache, caller-trust shortcut or wire change.

| Isolated scenario | Anchor before | Anchor after | Full validation after |
|---|---:|---:|---:|
| N5-derived11 individuals |244,641|108,143|107,855|
| Ordinary Southern21, host fixture |256,598|126,725|126,435|
| Synthetic full160 |560,550|505,753|505,463|

Both zero-check implementations reject every24×255 single-byte nonzero case
under current and all four historical revisions.96,768 evidence cases cover
all256 form bytes and trial/training boundaries. Four genuine historical
fixtures and158,400 historical instance comparisons remain identical. Strict
ARM compilation adds no libc dependency. Core42, Save5 41, Southern13,
capacity/sanitizer4 and optimization3 suites pass. The full160 ASan/UBSan and
interrupted-write suites remain green; static stack-chain sums remain252/788.

See `evidence/southern-validation-optimization.json` for component measurements,
source hashes and scope. No frozen scene2 or main ROM was overwritten. The
numbers above do not prove whole-game rest cadence; the parent must rerun the
native controller gate using the optimized sources.

## Verification and reproducible measurements

Southern commands (host transactions do not establish native acquisition):

    python3 tests/test_southern_save.py
    python3 tests/test_southern_save_limits.py

Revision4 timing/resource evidence is recorded separately in the Southern save
limits report. The revision3 measurements below are historical comparisons, not
revision4 results.


    python3 tests/test_save5.py
    python3 tests/test_save4.py
    python3 tests/test_save5.py --arm-timing --mgba-tools <bridge-directory> --output build/save5-timing

The suite covers all 6,145 interruption positions in first migration and both
replacement directions, each individually corrupted write, every byte of
either bank corrupted, future/old revisions, CRC-valid malformed records,
duplicate item/creature references, immutable snapshots, tiny/huge budgets,
commit visibility, retries, full 160-creature rosters and all 19 authored items and 21 enabled form definitions.

`tests/fixtures/v5-revision1/all-evolved-village.sav` is an unchanged,
SHA256-pinned controller-only C4-final SRAM fixture. Its paired provenance
identifies the source ROM/report and confirms no game-RAM injection. Migration
asserts exact preservation of its full collection/creature/party wire span and
all creature-credit bytes, including its four evolved forms and commands.
Synthetic malformed-bank tests are codec tests, not gameplay evidence.

`tests/fixtures/v5-revision2/all-eleven-town.sav` is the unchanged controller-earned
R5 save, SHA256 `74f39c496a1e93eb47c5b50828513033899be0567a1391cf99869750defa9106`.
Its provenance pins the exact R5 ROM and native combat report, which has 2,761
passing checks, a saved/rebooted eleven-form collection, six live instances,
eleven claimed quests and thirteen items. The migration test compares the
entire bank payload from offset 32 onward byte-for-byte after revision 4 save.
No old-ROM machine state is imported. Northern API grants in host tests prove
codec behavior only; native Northern acquisition requires its controller suite.

ARM timing uses real emulated ARM7TDMI code, cascaded GBA timers and the engine's
WAITCNT 0x4317. It is an isolated subsystem benchmark, not proof of complete
engine frame cadence or physical hardware performance. Final numbers are
recorded beside exact source hashes and compiler stack usage in the JSON report.

Measured revision-3 Northern-policy build with N1 equipment validation optimization, 2026-10-05 (`-Wall -Wextra -Werror`):

| Operation | Maximum cycles | 280,896-cycle frame |
|---|---:|---:|
| begin, all tested roster sizes | 21,671 | 7.7% |
| step requested 1,024 | 65,459 | 23.3% |
| step requested 3,072 | 192,790 | 68.6% |
| step requested 4,096, clamped 3,072 | 192,786 | 68.6% |

Twenty-one scenarios cover empty/one/two valid banks, 2/4/160 creatures, mixed
and evolved rosters, all 19 equipment definitions, all 22 quests, and every
Northern retained family/trial. At 3072, four-creature/two-bank writes take 23
updates; full 160/all 19-item/all 22-quest/two-bank writes take 39. At 1024 they take 66
and 115. The maximum 3072 step leaves 88,106 cycles for the dedicated mode's other
work; whole-game cadence must be measured independently.

The save5 object contributes **13,464 bytes ROM**, **7,244 bytes EWRAM**, and
**zero IWRAM code**. Compared with frozen R5's 11,504 ROM/7,244 EWRAM, revision 3
adds 1,960 ROM bytes and no mutable RAM. EWRAM includes the single 6,144-byte
scratch union and 1,100 bytes of streaming state. The unchanged 4,944-byte caller
state is counted separately: 12,188 bytes combined. The maximum individual
compiler-reported stack frame remains 120 bytes (`scan_run`); this is not a
whole-program stack-high-water claim. No full bank/roster lives on the GBA stack.

N1's equipment validation uses a bounded 64-byte duplicate-ID bitmap. The
compiler reports a 96-byte `equipment_validate` frame and a 128-byte reviewed
validation subtree. The equipment branch beneath `save5_validate` totals 176
bytes, below its 200-byte creature-validation branch. Incremental `save5_step`
does not call the full equipment validator; its reviewed subtree totals 232
bytes. The larger existing batch-reward path is 712 bytes beneath
`equipment_claim_many` (544 + 40 + 96 + 24 + 8); equip's reviewed subtree is 312
bytes. These sums exclude caller and interrupt/exception overhead. Main SP
starts at `0x03007F00`, with code bounded below `0x03007000`, leaving 3,840 bytes
beneath the initial main SP. Whole-engine stack high-water still needs its own
measurement. Source hashes and the exact reviewed paths are recorded in
`NORTHERN_SAVE3_VERIFICATION.json`.

The 41-test host suite includes exact revision whitelists, 1,536 historical-visit
combinations, unknown revisions/IDs, all retained recruit/trial floors, split-copy
trial evidence, valid-CRC malformed banks, zero-write incremental failures, and
all 6,146 cut/success positions for each of three Northern transactions and
R5→revision 3 migration in addition to previous fault coverage. Original
revision 1 roster/commands and revision 2 complete typed payloads remain exact.

ASan/UBSan passes 1,000 full 160-creature/all 21-form/all 19-item/all 22-quest random-
budget save/load cycles, evolution and party changes, plus failed retention
snapshots with no durable writes. `tests/save5_sanitizer.c` is compiled and run
by `tests/test_save5.py`; leak detection is disabled for the ptrace sandbox,
while address and undefined-behavior checks remain active. These are subsystem
verification results, not a claim of 21 natively obtainable creatures.


## Southern queued save presentation

The engine now enters its frozen saving overlay for one update before calling
`progression_save_begin`. On the next frozen update, the unchanged public
`save5_begin` copies the snapshot, then later updates perform bounded writer
steps. No input or world progression can change the queued state. This avoids
combining a synchronous anchor validation, snapshot copy and cold bitmap redraw
in a single presentation interval. Codec wire bytes, snapshot semantics, CRC,
revision policy and transactional commit order are unchanged.

A rejected begin returns to the requesting state with the same persistent
failure notice. The queued entry itself writes no SRAM, and an interruption
there leaves the previous committed save intact. Host fault/freeze tests and
native full-collection cadence tests cover this additional engine phase.

The later core optimization and exact isolated timing sources are recorded in
`evidence/southern-validation-second.json`; older tables above remain historical
measurements and should not be relabeled as new runs.
