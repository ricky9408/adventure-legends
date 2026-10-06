# Underwater typed progress and Save5 revision6

Implementation and host/isolated-ARM evidence only. This is not an Underwater release or native collection claim. Native controller-only journeys, final render/cadence/OAM/stack/resource review, and a frozen final ROM remain separate acceptance gates.

## Persistent contract

- Wire version5, 24-byte records, 160 individuals, 6144-byte banks at 0x0200/0x1A00, 5056-byte used payload, and every offset remain unchanged
- Current writes advertise content revision6; revisions1–5 remain independently decoded with their exact released acceptance policies
- The accepted Magma Save5 history header remains byte-identical at SHA256 `69dba67ea332f03bab26246b5739662aef7177ff1cabe43bed8b444940d40a13`
- `tests/fixtures/magma-policy-oracle` is a self-contained 15-file exact source closure copied with `git show` from accepted commit `0a8b05c3e24d02bd350a11c32289fb5686641535`. Its pinned provenance manifest is `9ba6c261b8a45525ecbe5d75a2a9ee858f11709074875105a9560dc855689d54`. No frozen sibling is needed to run the differential
- Original authentic Magma 34 SRAM and provenance are unchanged, SHA256 `a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858`
- Only byte4 visits, byte10 six first-field receipts, byte17 eight first-extra receipts, byte20 F023 prefix0/1/3, byte21 F024 prefix0/1/3/7, and anchor byte4 bits1/2 are new regional state
- Rooms46–53, quests38–45, items6/13/38/54/68/86, equipment sources31–36, forms49–72 and commands67–90 are separate namespaces
- Nacreway and every new source require claimed Magma quest32. Rooms50–53 require both teaching quests, and rooms51/52/53 require objective prefixes1/3/7. Both entrance and return spawns enforce these gates
- Anchor spawn2 exists at46/47 only with the corresponding permanent visit and anchor. Ordinary reciprocal returns use46 spawn3 and48/51/52 spawn2, preserving each room's full quest/prefix gate. Other new rooms retain only spawns0/1. Current-r6 room38 spawn4 is the shell-lift return and additionally requires the Underwater town visit; revisions1–5 keep their exact old rejection
- Every first-source receipt requires retained exact-family ownership and appropriate history. Every current new-family individual requires that receipt. First-extra receipts require two retained distinct identities plus a retained authored terminal
- Admission is prospective, not save validity. The same72 terminal opportunities and88-copy reserve apply. Grandfathered unsafe saves remain loadable/saveable

## Typed APIs

`underwater_quests.h` exposes synchronous cold transaction APIs for host regression and explicit paused tools. They must not be used on native idle/draw/tick paths: representative 50 synchronous repeat grant costs over550,000 ARM cycles.

First source tokens are exactly `UW_SOURCE_17..24` =1..8. The repeat transaction accepts the corresponding first-source token, not the separate room interaction ID17..24. The world owns a solved attempt generation and consumes it only on a successful invitation. The durable first-extra bit is provenance and never blocks a new, explicit repeat encounter.

Trials bind exact slot, monotonic instance ID, family, local key and source. Both keys1/2 may be completed independently on the same base. Completion stages one 24-byte instance and raises only it to level28/bond45. An already recorded key returns unchanged before training or credit. No quest/source/trial API awards ordinary XP, lifetime field-aid credit, or party bond; those are separate idempotent runtime event calls.

Quest45 stages both equipment rewards into a single 512-byte temporary before any live reward/state byte changes. No nested equipment batch stage or fullSave stack copy is used. A full bag leaves READY and every byte untouched, including when the first item would fit but the second would not. Previously seen/discarded unique items settle the source without generating duplicates. Teaching/main quests grant no equipment.

## Bounded native transaction protocol

`underwater_job_begin` copies a zero-initialized `UnderwaterRequest` and requires a nonzero scene generation. It returns an opaque token. Each `underwater_job_step(token, budget, scene_generation)` runs at most one bounded phase. `UW_REQUEST_QUEST_PROGRESS` offers and records one objective atomically. `UW_REQUEST_TRIAL_STATUS` is read-only.

1. `save5_preflight_begin` exclusively borrows the existing 6144-byte codec scratch and stores the raw snapshot. There is no second fullSave or roster snapshot
2. Preflight validates campaign/party/discovery, capped roster slices including identity uniqueness, quest fields and causal gates, item records, equipment references/seen/claims, and exact per-family source/trial evidence
3. The immutable validated snapshot feeds the independent incremental core admission cursor. No caller-controlled trusted flag exists
4. Gear reuses the existing 512-byte codec scan equipment stage after validation; a trained individual uses one private 24-byte stage
5. Immediately before commit, the live Save5State is compared word-for-word with the immutable snapshot. Core grant commit also compares the entire roster and consumes its admission token once
6. Only then are the small staged patch and infallible typed receipts applied. Scratch is released before ordinary save writing starts

Cancel, scene mismatch, load, request/participant mismatch, failed validation, or any live-state byte difference prevents durable mutation. Cancel revokes the preflight generation before scratch can be reused. Load cancels preflight; ordinary writer begin refuses while it owns scratch; a preflight begin refuses while the writer is busy. A copied request cannot be redirected by editing the caller's original request.

The parent engine must freeze movement/input, timers, casts, enemies, room attempts and selection while a job is pending; retain its source/trial geometry proof; and explicitly cancel on death, load/new game or scene reset. An input-generation receipt is still required even though the durable job is one-use. No phase reads or writes SRAM. Ordinary saving begins only after the live transaction finishes.

## Evidence

Reproduce with:

- `python3 tests/test_underwater_save.py`
- `python3 tests/test_underwater_transactions.py`
- `python3 tests/test_underwater_history_differential.py`
- `python3 tests/test_underwater_powerloss.py`
- `python3 tests/profile_underwater_save.py`
- `python3 tests/profile_underwater_transactions.py`

The host synthetic collection reaches 89 history forms and 50 independently identified retained individuals, plus all 37 equipment definitions. This does not prove controller obtainability.

Initial isolated ARM7TDMI measurements at WAITCNT0x4317, before whole-engine integration:

- Current blocking validation:171,411 authentic 34;235,585 synthetic 50;544,575 synthetic 160 cycles
- Synchronous repeat status/grant at50:393,241/554,810 cycles, too long for a hardware frame
- Bounded job begin: at most24,836 cycles
- Bounded job worst phase: approximately56,100 cycles including exact full-state/roster comparison and successful grant commit
- Bounded full 160 preflight record slice: approximately30,200 cycles
- Two-item equipment commit: approximately36,200 cycles

Mutable-memory delta is 32 bytes in Save5 plus 104 bytes in the typed job and 164 bytes in the core admission cursor (300 total), reusing the existing raw save scratch and equipment stage. No new IWRAM allocation is used.

Full per-phase data, source include-closure hashes, test labels and operation results live in `docs/evidence/underwater-transactions-arm.json`. Writer measurements are in `underwater-save-arm.json` and optional lower-budget profiles. These are isolated costs, never a claim of native frame cadence or final hardware acceptance.
