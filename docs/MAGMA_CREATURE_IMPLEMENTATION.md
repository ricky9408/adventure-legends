# Magma creature core and collection admission

Implementation scope: current creature catalog, generated tables, typed admission
queries/mutations and core tests. This is not a Magma playability/release claim.
The reviewed historical-policy foundation remains byte-exact in its frozen block.

## Data and policy

Current revision5 enables65 forms,102 learns,35 edges and65 abilities: append24
forms31–48/95–100,41 learns,15 edges and signatures43–66 to the delivered41 prefix.
No schema, identity-lock, wire layout, command12 or legendary enablement changes.
Current per-form trial masks prohibit key2 on31/34 before becoming32/35. This is
enforced by current/revision5 instance validation and qualified mark/query APIs;
historical masks are untouched.
Per-form current policy independently encodes exact polarity and field caps; only
39 and48 flip on evolution. Third tiers33/36 retain commands/caps and total285.

Frozen revision1–4 indexes, incoming minimums, commands, masks, polarity and story
mapping do not consult the live tables. API revision5 delegates current semantics.
Existing legal historical exceptions and over-budget rosters remain legal; trial
and source causality belongs to the typed save/quest layer, not an admission flag.

## Public interfaces

See src/creatures.h for exact signatures and stable result enumerations:

- creatures_collection_coverage returns occupied, viable, excess, free slots,
  missing opportunities and admission_safe; invalid output is zeroed
- creatures_terminal_family/mask expose immutable final128 reservation metadata
  without enabling any identity, command, acquisition or evolution
- creatures_admission_query_grant/evolution compute before/after coverage without
  mutation. The evolution query only accepts an explicit registered same-family
  edge; trial/context eligibility remains a separate check
- creatures_grant_admitted returns a typed admission result and a distinct new
  roster slot only on success. Use creatures_admission_allowed, not status==0:
  GRANDFATHERED_READY is successful too
- creatures_can_evolve_roster_to is the UI preconfirmation check. Instance-only
  eligibility queries cannot evaluate storage and must not substitute for it
- Both confirmed creatures_evolve and creatures_evolve_to enforce prospective
  admission. Ambiguous legacy branching never selects the first target. An
  unconfirmed eligible evolution returns DEFERRED before capacity checks and
  changes no bytes

The existing creatures_grant is intentionally retained as a legacy/staging
primitive so historical full160 test fixtures and internal transactions can be
constructed. Every gameplay wrapper must use admitted acquisition or an equivalent
preflight inside the same atomic transaction. Story joins now use admitted grants.
Legacy migration starts from a fresh<=4 roster and is inherently admission-safe.

One-time generic reward retries return ALREADY_CLAIMED before capacity admission.
Typed source receipts are outside the core: callers must check those receipts
first, then preflight admission and any equipment/quest constraints before writing
any reward, source, history, next ID or success state. The guard is not source
permission. Trial completion itself consumes no coverage and stays available.

## Why the scan is sufficient

The full immutable topology has60 families and72 distinct final opportunities.
Each family requires at most two representatives. A capped count and reachable
mask per family compute min(actual count, reachable target count), which is exact
maximum matching for this reviewed topology. One base with mask3 covers only one.

A query uses one160-record coverage scan and120 scratch count/mask bytes. Evolution
omits the chosen record, then inserts its actual and candidate forms virtually
from the same intermediate counts. No roster is copied, mutated or synthesized.
External entry points fully validate their roster once. Private already-validated
helpers avoid repeating that validation during the same synchronous mutation.

Safe states must retain excess<=88. Pre-existing excess>88 permits only physically
fitting, nonworsening-excess/nondecreasing-coverage actions. There is no universal
recovery guarantee for such an older collection. No integrity predicate rejects
it merely for excess, and there is no deletion/release/replacement feature.

## Verification

The checked-in tests are independent of the implementation's matching algorithm:

- tests/test_magma_catalog_policy.py:8 tests for exact current/historical manifests,
  immutable identity, per-form polarity, trial dependencies, generation bounds,
  full128 topology and released-semantic corruption
- tests/test_magma_creature_core.py:8 tests with strict native and ASan/UBSan runs;
  each native run covers35 edges,384 complete branch orders,2,078 matching checks
  and45,772 admission comparisons, including200 randomized220-action sequences
- tests/test_magma_history_core.py:4 tests;100,608 historical command/trial/level
  comparisons across current-table mutations plus48,000 corruption cases across
  three independently compiled current-data variants
- Immutable revision4 binary prefixes remain exact: forms1312 bytes, learns122,
  edges160 and abilities328. The new suite hash-pins each prefix independently
- Thirteen real distinct newly granted individuals obtain all24 new histories;
  refusals, decline, source retry, full160, missing-path rescue, wide IDs and
  corrupt future-topology metadata are tested without rewriting any old fixture

Catalog validation, deterministic generation/format and frozen-history generation
checks pass. Current-only count/context expectations and synthetic extension fixtures are
updated; all42 legacy core/sparse tests,4 branch tests and7 architecture tests
pass with historical hashes and assertions preserved. Native acquisition/art/power/UI/save-path integration remains separate.

## Bounded ARM evidence

See evidence/magma-creature-arm.json. Reproduce with:

    python3 tests/benchmark_magma_creatures.py --earned-sram PATH_TO_S3_08_COMPLETE41_INDEPENDENT_REBOOT_SAV --baseline-source PATH_TO_REVIEWED_FOUNDATION_SRC --output build/magma-creature-arm

The delivered S3 native-earned21 SRAM is hash-pinned to
0bd83c19eb0dee81b3cd9e2b48462f6362b559786e38fa119312fe05787b0bd3.
The34/full160/89 profiles are explicit host-constructed core states. Only the21
profile is an authentic native-earned collection; no authored Magma route is
implied by the34 fixture.

ARM7TDMI Thumb -O2, mGBA timer16777216Hz, WAITCNT0x4317, four samples per operation:

| Profile | Roster validation | Coverage query | Admitted grant transaction |
|---|---:|---:|---:|
|Native S3 earned21 |44,140|57,412|60,440|
|Host-staged34/all65 history |74,882|92,626|95,992|
|Grandfathered full160 |408,018|466,106|466,541|
|Safe duplicate limit89 |166,788|201,364|202,187|

Core object ROM sections total24,098 bytes versus18,198 for the reviewed foundation:
+5,900 bytes. Core mutable .data/.bss=0 and permanent IWRAM additions=0. The largest
compiler frame is232 bytes; isolated observed subcall stack below benchmark main
is at most340 bytes. These measurements do not establish whole-engine high-water
or physical-hardware performance. Catalog validation is636,795 cycles and belongs
at initialization, not a frame loop. Full160 admission exceeds one GBA frame
(280,896 cycles), so callers must use the existing paused/transactional UI and
still measure complete-engine cadence; never run all-roster queries every frame.
