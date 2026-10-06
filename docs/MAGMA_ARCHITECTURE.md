# Magma preparation: historical policy and multi-trial gates

This isolated core workspace resolves the two **future expansion gates** in
`SOUTHERN_CORE_REVIEW.md`. They were not current Southern S3 saved-game defects.
No active Southern or frozen S3 runtime was modified. S3 remains pinned to ROM
`87d16a0fc513d7e8a491e0b5ac5929f7951e1e44e18b7f534f1e5e0cc794d4de`.

This work enables **zero additional forms**. The ROM still has 41 forms, 41
commands, 20 evolution edges and content revision 4. Magma's separately designed
24 forms remain disabled: 31–48 in F011–F016 and 95–100 in F036–F038. Third tiers
33/36 and alternate branches 39/42/45/48 are not gameplay in this deliverable.
The original generated creature data, all instance/wire layouts, Save4 source,
old fixture files and their hash pins remain unchanged.

## 1. Current qualified trials versus immutable legacy scalars

`CreatureFamilyPolicy.trial` is now explicitly the current family-qualified
union. `legacy_trial_scalars` is a separate immutable mapping, preserving
F001=1, F002=2, F003=4, F004=8, F005=16, F006=0, F007=32, F008=64,
F025=128, F026=256, F027=512. New families still return zero from the old query.
Adding a key to F001 cannot change the legacy query to 1025 or stop legacy
`creatures_mark_trial(instance, 1)` working.

Each qualified `(family, key)` has an explicit one-hot u16 bit and prerequisite
mask. Catalog validation enforces unique local keys and bits, exact union,
known prerequisite bits, no self-dependencies, no cycles and no prerequisite
introduced later than its dependent. At most 16 distinct bits can exist in one
family. Full-width input guards precede conversion. Wrong-family collisions,
unknown keys and unmet prerequisites fail without changing the individual.

An edge requires its reviewed subset, not the family's entire union. Required
subsets are closed under prerequisites. Old first-tier edges retain their
original scalar even when a later trial is added. A branch can have independent
keys 1/2 with masks 1/2; a linear key2 can require key1, producing edge mask3.
`build_trial_masks` resolves the same bounded prerequisite closure for generated
ROM edges. Production revision-4 enablement remains exact and rejects additions.

Current validation enforces dependencies on persisted multi-trial records.
Historical validation keeps the old exact mask and does not retroactively add
bond/trial causality to old evolved forms. Trial bits are retained on evolution;
none is consumed, auto-earned, or copied from another individual.

## 2. Target queries and future third tiers

The existing target APIs remain authoritative:

- `creatures_evolution_count(from)`, `creatures_evolution_at(from, ordinal)` and
  `creatures_evolution_to(from, target)` expose explicit candidate edges
- `creatures_can_evolve_to(instance, target, context, sanctuary)` evaluates
  that target with unchanged LEVEL → BOND → STORY → TRIAL → SANCTUARY precedence
- `creatures_evolve_to` requires explicit confirmation, stages one individual,
  preserves identity/evidence/inherited commands and changes only authored fields
- Legacy lookup returns no edge for a branching source; legacy can/evolve returns
  AMBIGUOUS after validating its input and never chooses the first edge

The ordinary tier-three stat budget is 285, matching the existing authoring
contract. Current story-family lookup follows the reviewed current lineage, so
an F001 third tier preserves STORY_LOCKED identity instead of becoming invalid.
Historical story-family lookup is separately frozen.

Synthetic tests append F001 form3 and an edge from released form2, using qualified
key2=1024 with prerequisite1 and edge mask1025. They preserve the original
1→2 edge, legacy scalar1 and every historical revision. Another fixture tests
both F013 targets independently, both trials together, ambiguity, invalid
requests, decline and evidence preservation. A context0x100 test proves the
core target path retains u16 context when an explicitly test-only policy admits
that bit. These are host/sanitizer fixtures, never enabled cartridge content.

## 3. Immutable released policy and safe future extension

`assets/history/creatures-v1-v4.json` contains the exact historical form,
family, polarity, minimum-level, trial and command/minimum-level relationships.
`tools/generate_creature_history.py` verifies its reviewed SHA-256 and emits the
marked immutable section in `creatures.c`. It never reads today's catalog.
Historical form, command, trial, legacy-story, instance, collection, party and
roster validation consult that section exclusively.

`assets/history/released-creature-relations-v4.json` and
`assets/creatures/released_policy.py` separately protect released *current*
semantic relations. Generation rejects removed/changed original learn pairs,
evolution edges, signatures, identity-related phase/polarity, ability behavior
and trial assignments. It permits reviewed additions. Derived offsets, sparse
indexes, counts and outgoing counts are not frozen: an existing evolved form
may gain a new outgoing edge, and layouts may be regenerated. Old revision
snapshots do not change when that happens.

The Save5 half is documented in `HISTORICAL_SAVE_POLICY.md`: immutable quest
masks/variables, gates, rooms/spawns, source and equipment relationships drive
both old-bank scanning and full decoded-state validation. Current gameplay
validation remains a separate API. The writer validates both current policy and
the exact declared revision before any SRAM write. A deliberately incompatible
live edit cannot rewrite an old bank, silently change its command or broaden
its allowed objective bits.

For a later content revision:

1. Keep both released snapshot files and the locked Save5 release1–4 block intact
2. Add reviewed new-revision rows/routing, enablement and current family/key/edge
   rows; retain every released semantic relationship
3. Regenerate indexes/counts and allow new learns/edges without changing old pairs
4. Add exact source, quest, equipment and same-individual causal policies for new
   content; keep old generic reward/event/aid namespaces intact
5. Re-run historical differential, malformed-CRC, zero-write, interrupted-save,
   branch/decline and capacity tests before enabling the new revision

A semantic removal/replacement is intentionally not an automatic migration.
Under a forced command1→23 live mutation, valid old banks still load unchanged;
current re-save fails with zero writes. Designing a playable incompatible
migration needs separate explicit policy. Pre-v5 migration remains the existing
Save4/legacy synthesis path; released current relation locks prevent changing
its source semantics. No legacy history is cloned into new companions.

## 4. Verification and reproducible commands

    make all
    make test-magma-architecture
    python3 tests/test_creatures.py
    python3 tests/test_southern_validation_optimization.py
    python3 tests/test_save4.py
    python3 tests/test_save5.py
    python3 tests/test_southern_save.py
    python3 tests/test_southern_save_limits.py

The independent whole-bank differential requires a SHA-pinned Southern oracle.
It defaults to the sibling checkout; set `SAVE5_HISTORY_BASELINE` to the supplied
frozen Southern source if replaying elsewhere. Neither tree is modified.

Final host evidence includes 166,699 whole-bank comparisons; 100,608 historical
form/level/command/trial matrix comparisons plus 144,000 deterministic corruption
comparisons across ordinary, command-removed and live-index-removed variants;
all 65,536 u16 trial values in the synthetic released-family extension; the old
23,531,642 XP/level, 301,510 party/reference, 1,048,576 collection-byte and 36,720
instance-corruption differential cases; and all 147,504 Southern interrupted
write/success positions. Existing old suites/fixture pins pass. ASan/UBSan run
both new synthetic architectures and full160/48-gear persistence tests.

The synthetic48 harness now extends an explicit temporary historical item policy
as well as temporary live item rows. Production still rejects those IDs before
writing and on loading. No test-only bypass was added to production C.

## 5. Isolated ARM resource and timing results

Final development-only ROM:
`f083dcb13e5cb40f4e0d7bf47cf2060775a7291a1bee7f7b68f0766ba25b5c4e`.
This is not a release/gameplay acceptance ROM.

- Full ROM: 5,865,092 bytes, +6,392 versus S3
- ELF mutable storage: data84 + BSS48,008 bytes, unchanged
- `creatures.o`: ROM14,078, zero mutable bytes; +1,412 ROM
- `save5.o`: ROM19,803, BSS7,248; +4,975 ROM and zero extra RAM
- The single6,144-byte scratch bank and4,944-byte caller save state are unchanged
- Maximum save5 own compiler frame128 bytes; reviewed conservative direct-C sums
  are236 for save-step,396 for load,172 for current full validation,284 for
  historical full validation and788 for mixed Southern claim

The sums are control-flow-insensitive and may include parameter-infeasible call
branches. They exclude interrupts, indirect calls and runtime stack high-water.
No physical-hardware or whole-engine stack high-water claim is made.

At WAITCNT0x4317, real ARM7TDMI code with emulated hardware timers:

| Scenario | S3 anchor cycles | New anchor cycles | New full historical validation |
|---|---:|---:|---:|
| N5-derived11 |91,405|82,593|110,882|
| Controller-earned21 |105,891|99,121|129,218|
| Synthetic30 |not measured|110,002|139,523|
| Synthetic full160 |427,000|445,250|464,072|

The empty-slot fast path checks all24 bytes and its expedition credit in the
roster traversal, avoiding a large validator frame for empty records. Every
occupied record still receives complete validation. It recovers ordinary-state
headroom without a mutable cache or trust shortcut. Full160 is explicitly
**18,250 cycles / 4.27% slower** than S3's isolated anchor result. That operation
already exceeds one GBA frame at full capacity; its growth is not concealed.
The30-instance case is host-constructed Southern content, not a Magma cadence
prediction.

Incremental save maxima across full160/all41/all30 and real25/synthetic48 gear:

- begin21,657 cycles
- budget1024 step60,315 cycles
- budget3072 real25 step153,158 cycles; synthetic48 step160,876
- requested4096 remains clamped3072, worst160,872 cycles

All existing isolated writer limits pass. These are subsystem measurements, not
whole-game cadence. The final raw source-pinned reports are in
`docs/evidence/magma-architecture-final.json` and its referenced evidence files.

## Remaining gates and design choices

- Proposed Magma forms39 and48 explicitly change polarity relative to their
  base families. The evolution mutation already assigns target-authored
  polarity, and historical polarity is frozen per form, but current catalog
  validation still requires the family's single polarity. Before those forms
  are enabled, add a separately bounded explicit per-form current polarity
  policy/override. Preserve every released polarity and the identity-lock tuple
  (ID/key/family/tier/rarity); do not infer flips from phase or branch position

- No Magma art, handlers, acquisition, quest transactions, UI target picker,
  branch encounter receipts or map integration is implemented here
- New families, trial rows, content revision5 and context0x100/0x200 must receive
  explicit current+historical policies before enablement; the synthetic core
  context test does not prove the engine's full u16 context path
- Before30+ real companions are enabled, independently measure cold menus,
  synchronous anchor entry and complete presented-frame cadence. A separately
  reviewed bounded engine transaction stage may be needed; no game.c/UI change
  was made in this architecture task
- Runtime stack high-water and physical hardware behavior remain unmeasured
- Deterministic repeatable base encounters must produce distinct retained
  individuals under the separately designed branch-source contract; this work
  does not fabricate or clone collection history
