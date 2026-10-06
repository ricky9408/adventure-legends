# Immutable Save5 revision 1–4 policy

The immutable revision1–4 foundation is retained unchanged in the Magma
workspace. The current writer now declares content revision5, whose separate
policy rows append 24 forms, eight quests and six gear definitions. Wire
version5, 24-byte individuals,160 roster slots,5,056 used bytes,two6,144-byte
banks, offsets,CRC and commit-last protocol remain unchanged. New gameplay
admission never becomes a historical or current bank-validity predicate.

## Policy boundary

`src/save5_history_policy.h` is a data-only, explicitly versioned snapshot.
Its marked release-1–4 block is SHA-256-pinned by
`tests/test_save5_history.py`. Do not update the pin to accommodate a current
catalog edit. Add separately reviewed later-revision policy without rewriting
released rows. The `Save5HistoryVersion`, quest, item, room, visit-gate and
creature-source structures document the schema. Sparse item/form indexes resolve
only this snapshot; they never consult live catalog indexes.

The snapshot records:

- Exact per-revision enabled quest/item/room prefixes and every allowed region
  and anchor byte
- Quest objective masks, monotonic-prefix requirements, allowed variables,
  exact reward-bit relationships, regional entry and prerequisite quest gates
- Room/spawn masks, original campaign path/north-return prerequisites,
  anchor returns and permanent historical visit prerequisites
- Equipment ID, slot/category, flags, acquisition-source ID, source category
  (starter, free town rack, or quest), exact source-to-item and source-to-quest
  relationships, including the two-source Q6 and Q19 rewards
- Exact-family retained recruit and personal-trial evidence, generic reward
  links, per-individual training floors, Southern field/source/discovery links

Shared bounded history evaluators in `save5.c` implement these rows for both
streamed bank validation and the complete decoded-state validator. The creature
core supplies independent revision-qualified instance, collection, party,
identity, legacy-spirit and roster validation. No whole-save copy, mutable
validation cache, current-catalog fallback or trust-only load bypass was added.

Equipment combat statistics and weapon class are deliberately absent: the
released save record/reference validators did not validate those attributes.
Adding a new rejection based on them would alter historical acceptance. Slot
category, record flags, source ID and source relationships are frozen exactly.

## Blocking load, migration and writer behavior

Every SRAM bank is checked against its declared revision before bank selection.
`save5_load` decodes the selected bank, applies only the pre-existing resume
normalization and revision-1 starter migration, then calls
`save5_validate_revision` for a complete independent decoded-state check.
`save5_has_valid` follows the same path. Neither reads through live item,
quest or creature policy, and neither writes SRAM or changes caller output on
failure.

`save5_validate_revision(state, revision)` accepts revisions 1–5. For
revision 1 its input is explicitly **decoded** state: all quest bytes zero and
exactly the canonical migrated protected starter sword, equipped in slot 0,
with starter seen/source bits and all other equipment fields canonical. The
revision-1 **wire** reader still requires every reserved quest/equipment byte
to be zero. Starter migration is initialized from immutable values, so changing
or disabling today's starter definition cannot invalidate an old save.

Revisions 2–4 preserve the typed payload, including all legal generic reward
bits 5–128, event bytes and lifetime-aid bytes. No trial, source or reward history
is fabricated. Old evolved forms still permit every historically legal lack
of trial/bond evidence; new Southern same-individual causal checks retain their
original limited scope.

The public `save5_validate` and current gameplay helpers remain current-policy
APIs. A pending write is checked against both current policy and the exact
revision-5 wire policy before any SRAM writes. Thus a future live-policy edit
cannot silently produce incompatible bytes under a mismatched content revision.
An old valid save can load unchanged even when a deliberately incompatible
current policy rejects playing/re-saving that state; `save5_store` then fails
without writing, coercing equipped commands or changing historical evidence.
A future product migration for such incompatibility requires a separate reviewed
revision and explicit design. This refactor does not invent one.

## Verification

Run from this workspace:

    python3 tests/test_save5_history.py
    python3 tests/test_save5_history_differential.py
    python3 tests/test_save5.py
    python3 tests/test_southern_save.py

The new mutation suite proves the reported Q0 regression: changing only the
current mask from 7 to 15 makes current ACTIVE/objectives=8 legal, while every
released revision still rejects it. The test covers blocking load/has-valid,
zero-write incremental failure, old-bank selection, generation and
payload-exact revision-2-to-4 migration. It also covers current quest narrowing,
variable/room/source-quest changes, current command-1 removal, and canonical
revision-1 migration. Removed historical command 1 survives load/has-valid
unchanged across all four revisions; incompatible current re-save fails with
zero writes.

The independent differential suite SHA-pins frozen Southern C inputs and four
controller-earned SRAM images, snapshots both source trees in temporary build
directories and compares full CRC-valid banks. Its 166,699 comparisons contain
4,680 accepted and 162,019 rejected banks, including 69,688 single-byte mutants,
36,864 quest combinations, 14,364 catalog-drift mutants and 512 valid randomized
combinations. All load acceptance, decoded bytes, output atomicity and SRAM
immutability match. Seven temporary equipment variants cover source maps,
slots, flags, disabling ordinary/starter definitions and starter flags; class
change is a negative control. These synthetic cases are codec evidence, not
controller-earned gameplay or native cadence evidence.

The existing 41-test Save5 suite and 13-test Southern suite pass, including
147,504 Southern interrupted-write/success positions and all old fixture
preservation checks. Timing/resource measurements for the combined creature
and save refactor are recorded by the integration review, separately from these
host semantics results.

## Revision5 typed extension

New policy rows are outside the locked release1–4 block. New item source order
is25→20,26→37,27→53,28→67,29→85,30→5. Spawn masks15 for38/39 and1
for40–45 are verified against `assets/magma_region/validation.json`; only
spawn3 in38/39 requires their own recorded anchor. Normal spawn2 returns do not.
Source byte9, first-extra byte16 and discovery byte19 are independently typed.
Each retained new family is tied to its exact claimed source; each trial floor
is checked on the same individual. Branch receipts still require two distinct
retained IDs and an evolved retained branch after both companions evolve.

Revision5 adds13 bytes of bounded per-scan creature evidence plus alignment and
a deferred-causal-check flag. The semantic quest/source pass uses a fresh bounded
writer slice, preventing its cost from landing after an already full byte scan.
Budget0 remains no work; positive budgets retain progress and commit-last safety.
This changes scheduling only, never the wire representation or acceptance of old
banks. See `docs/MAGMA_SAVE_IMPLEMENTATION.md` for current evidence and limits.
