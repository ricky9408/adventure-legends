# Underwater authoring schema2, development content revision6

The current catalog has90 authored designs and128 immutable reserved identities.
The development core manifest selects89 forms,142 learned-command pairs,51 edges
and89 commands. This append is forms49–72 and signatures67–90 in families17–24.
Ability12, legends121–128 and every unlisted form remain disabled. Table enablement
is not evidence of acquisition, artwork, handlers, controller routes or delivery.

## Bounded source fragments

catalog.json is a strict source descriptor, not the assembled schema2 document.
Use catalog_source.load_catalog(path), or validate_catalog.load_json(path), for
all consumers. The loader also accepts archived monolithic JSON. It preserves
row order, rejects duplicate keys/paths, unsafe relative paths, nested descriptor
fragments and files reaching90,000 bytes.31 source files each stay below90KB;
metadata is separate and row arrays use stable24-record chunks. format_catalog.py
checks deterministic formatting without changing parsed values. No assembled
oversize JSON needs to be published or committed.

The old65-form catalog can be reconstructed by removing only revision6 rows,
capabilities and proposed slot statuses49–72. Its canonical SHA256 remains
 ebe05e3fa2b35c7fcd3e32d5235b95fc0010e003acb8439b23eef58fa9b16ec0.

## Immutable history and current policy

- The released65 form rows,102 learns,35 edges and65 command rows remain byte-exact
  prefixes. IDs, names, phases, polarities, existing stat weights, trial meanings
  and learn relationships are preserved
- identity-lock.json SHA256 is
  fe553a9d963de059e7d6c0f8647ab6a3fe736c5fdf7ca8d3b18c6dedd3292969
- assets/history/creatures-v1-v4.json and released-creature-relations-v4.json
  independently freeze historical reader and authoring semantics. Never regenerate
  those snapshots from expanded current data. Separate creatures-v5.json and
  released-creature-relations-v5.json freeze finally delivered Magma commit
  0a8b05c3e24d02bd350a11c32289fb5686641535 before revision6 expansion
- Revision APIs dispatch1–5 to frozen policies and6 to current policy. Admission is
  absent from all revision/current instance and roster legality predicates
- Current per-form policy specifies each polarity and field-capability set. Only
  individually approved branch polarities may differ. The old39/48 exceptions
  remain unchanged. Every new form49–72 has explicit polarity; no family-wide
  exception is accepted. Historical polarity remains per-form frozen
- Original21, Southern20, Magma24 and Underwater24 use append-only ROM order. Authored
  JSON is ID-sorted separately. Offsets/counts are checked before narrowing;
  source-grouped multi-edge rows must be contiguous
- Schema2 retains the8-command authoring bound and byte command IDs. Generated
  ROM indexes store row+1 and fail closed for missing, stale or out-of-range maps

## Trials, evolution and capability policy

Legacy unqualified trial scalars retain exact original ownership. New families
never become HEARTH owners merely because their local bit is1. Qualified trials
bind family plus local key; all keys and masks are validated at full integer width.

Magma families11/12 have key1→bit1 and key2→bit2 with key1 prerequisite. Their
third-tier edges require both bits. Base31/34 permit only bit1; current/revision5
instance validation and qualified trial APIs reject premature bit2 even with high
level/bond. Forms32/35 and33/36 may retain bits1+2. Branch families13–16 have independent keys1/2,
requiring only the selected edge's bit. Families36–38 have key1 only. World quest
code must separately prove source, from-form, context and same-individual floors.

MAGMA_READY=256 and CALDERA_OPEN=512 belong to the u16 evolution-context namespace,
not CampaignSave chapter flags. The current context mask is4095. Magma context derives
from claimed quests30/31 and32 respectively. Every evolution requires its exact
level, bond, trial, context, sanctuary and explicit target confirmation. Third
forms33/36 total285 stat points and retain all earlier field actions/commands.

Underwater families17–24 have independent local keys1/2, masks1/2 and no mutual
prerequisite. Both terminals inherit the base command at level1. New terminals
require their own branch receipt and level28/bond45. UNDERWATER_READY=1024 derives
from quests38/39; PALINODE_OPEN=2048 derives from quest40. Old evolved forms keep
exact historical acceptance, including legal zero bond or missing trial receipts.

Branch enumeration never silently selects its first edge. Legacy ambiguous calls
return AMBIGUOUS. The roster-aware preconfirmation query checks both eligibility
and capacity; confirmed evolve/evolve_to enforce the same guard. Decline preserves
every roster byte. Evolution retains ID, XP, bond, trial evidence, cosmetic seed
and equipped commands; a new signature is learnable, never auto-equipped.

## Terminal-opportunity admission

terminal-topology.json freezes all128 final-form family/mask rows. Disabled targets
participate only in capacity reservation. Maximum matching uses actual retained
individuals, never history/source flags. One flexible branch base covers one
opportunity; two bases or a base plus one terminal can cover two.

Safe forward actions preserve occupied−viable≤88, reserving all72 terminal
opportunities within160 slots. Missing-family/missing-branch bases remain admissible
at the boundary. Coverage-losing branch choices and redundant acquisitions refuse
without mutation. The scan uses120 scratch count/mask bytes, a single bounded160-
record coverage pass, no heap and no whole-roster stack copy.

Legal over-budget historical collections remain loadable and saveable, including
revision6 re-saves. New actions may only preserve/reduce excess and preserve/increase
coverage while respecting physical capacity. Admission cannot guarantee recovery
of all future opportunities from an already over-budget collection. No deletion,
replacement, release or history cloning is introduced.

Gameplay uses creatures_grant_admitted and creatures_admission_allowed(status):
READY and GRANDFATHERED_READY are both successful. Raw creatures_grant remains an
internal staging/compatibility primitive and does not authorize bypassing the
forward guard. Typed source wrappers return existing receipt status before
admission; mixed transactions preflight all rewards before any mutation.

## Verification and scope

Run from the repository root:

    python3 assets/creatures/validate_catalog.py
    python3 assets/creatures/generate_data.py --check
    python3 assets/creatures/format_catalog.py --check
    python3 tools/generate_creature_history.py --check
    python3 tests/test_underwater_creature_core.py
    python3 tests/test_magma_catalog_policy.py
    python3 tests/test_magma_creature_core.py
    python3 tests/test_magma_history_core.py

The core suite uses strict C99, ASan/UBSan, immutable prefix hashes, all35 edges,
branch orders, full/over-budget rosters, independent current/historical references,
malformed metadata and randomized admission sequences. The isolated ARM benchmark
is tests/benchmark_magma_creatures.py; docs/MAGMA_CREATURE_IMPLEMENTATION.md records
its invocation, bounds and limitations. Whole-engine cadence, save interruption,
source receipt integration and native controller routes are separate required gates.

See docs/UNDERWATER_CORE_FOUNDATION.md for exact new host coverage and isolated
ARM object resource deltas. Integration acceptance remains the parent milestone.

## Frame-bounded transactions

New gameplay can use creatures_admission_job_begin/step/result and once-only
commit_grant/commit_evolution against a caller-owned immutable snapshot. Four
records per step cap the full validation/admission workload; commits compare
all4140 live roster bytes exactly. The private ARM cursor is164 bytes. The
caller proves fullSave and typed source/attempt state and cancels on every
load/death/scene/confirmation invalidation. Existing synchronous APIs remain
available with unchanged behavior. See the foundation report for measured
cycle limits and the remaining combined-frame cadence gate.
