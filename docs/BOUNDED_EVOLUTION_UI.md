# Bounded evolution confirmation

This integrates the generic Save5 preflight and independent creature admission
cursor into the existing `EVOLVE_CONFIRM` state. It applies to all 51 currently
authored edges, including the original story and regional families before the
Underwater unlock. There is no Q32 or Underwater-only gate in this adapter.

## Transaction and input contract

- SELECT binds the actual selected roster slot, instance ID, source form, party
  index, both equipped commands and selected-command index
- Opening prepares frozen display reasons for both authored branches. It prefers
  the first admitted branch, unless the player explicitly chooses a branch while
  preparation is running. Both portraits stay visible throughout preparation
- A starts a fresh generic full-save preflight for the selected target. A during
  opening preparation does not queue a commit; release and press A again
- The existing Save5 scratch is the only full snapshot. It is immutable, exposed
  only after DONE, and exclusively owned until release. No heap, second save copy,
  caller validity flag, hash authorization or cached-reason authorization is used
- Each input update runs an explicit bounded batch of at most three cheap
  preparation slices. Each Save preflight slice uses a640-byte budget (at most
  four roster records); each core cursor slice uses four records. The batch stops
  before final exact comparison/commit or any terminal/cancelled state. Warmup
  and the final exact comparison/commit each occupy a separate update
- Commit requires the exact live participant and request, unchanged room/position,
  chapter/context and sanctuary, then an exact comparison of all 4,944 live save
  bytes. The core immediately compares all 4,140 roster bytes independently,
  consumes its token once and performs the small evolution mutation
- B, START and SELECT cancel before all other inputs. Any direction consumes a
  simultaneous A and cancels a pending confirmation. Only a single exact LEFT or
  RIGHT direction toggles the branch; mixed directions do not toggle
- Public cancellation invalidates the frozen menu binding. It revokes only its own
  scratch/cursor ownership, never a replacement operation's ownership
- New, load and save-begin call cancellation internally. Engine scene/death/menu
  abandonment and changed-selection notifications should call
  `progression_evolution_cancel()` as well
- Successful commit releases ownership before the existing animation, selection
  refresh, sounds and one save request at animation tick80

The renderer performs no validation, mutation or job steps. Frozen display reasons
are informational only. Missing local requirements can be displayed immediately;
a locally eligible target always needs both authoritative proofs before evolving.

## Verification

`python3 tests/test_magma_evolution_ui.py` runs 38 production-linked strict-C99
host tests. Engine presentation, sound and save requests are explicit host bridges;
Save5, creature core, admission, context, generated text and portraits are real.
The previous 22 tests and their predicates remain, with asynchronous waits and
valid typed source scaffolding replacing roster-only ready-state fixtures.

Coverage includes all15 Magma edges, all16 Underwater edges, all20 earlier edges
before Q32; selected individuals rather than family caches; both branch layouts;
all cancellation chords; every pending-frame cancellation; stale selected commands,
identity, form, target and branch; each of4,944 live-save byte mutations; foreign
ownership and revoked tokens; grandfathered160-slot admission; rendering without
validation; repeated A; animation art, timing and exactly one save request.

The frozen Southern fixture is unchanged:
`tests/fixtures/v5-revision4/southern-minimal8-town.sav`, SHA256
`968066ed983bd48fc2af0d7ffeb79f635624037ef2099809fd00c97aaa04cc0c`.
No previous fixture or historical hash was edited.

Sanitizers:

```sh
ASAN=$(cc -print-file-name=libasan.so)
ASAN_OPTIONS=detect_leaks=0 LD_PRELOAD="$ASAN" \
  MAGMA_EVOLUTION_SANITIZERS=address,undefined \
  python3 tests/test_magma_evolution_ui.py
```

## Isolated ARM evidence and limits

`python3 tests/profile_evolution_ui.py` builds the actual progression/save/core
translation units for ARM7TDMI with WAITCNT0x4317. The34-retained case loads the
authenticated native Magma fixture;50/160 use the existing completed Underwater
setup helpers. Only the chosen evolution participant is synthetically reset to
its base form, with a valid selected command and personal trial proof. Evidence:
`docs/evidence/bounded-evolution-ui-arm.json`.

Measured snapshot: opening begin39,661 /39,928 /39,928 cycles; fresh-A
begin33,022 /33,200 /33,200 at34/50/160. Largest batched noncommit update is
41,082 /56,146 /68,761 cycles respectively, below the90,000-cycle preparation
target. Final commit+refresh is isolated on its own update:
79,943 /84,954 /122,574 cycles. The private job is72 bytes on ARM, allocated
outside IWRAM. Compiler static frames are not interrupt-inclusive stack high-water
measurements.

Two-branch opening takes50 input updates including two warmup frames; fresh-A
confirmation takes37 updates. At the nominal59.73Hz GBA cadence this is about
0.84s opening and0.62s confirmation, before the unchanged80-tick animation.
Cancellation remains available between every batch. Instrumented production
Save5/core tests assert at most three combined slices per update, zero slices in
each warmup update, and no preparation slice sharing the final exact-check/commit
update.

Prior unbatched144/103-tick evidence and documentation are preserved under
`docs/evidence/bounded-evolution-ui-unbatched/`.

This evidence excludes final-engine drawing, native audio/interrupts and real
controller acquisition. The final update-plus-draw frame, cold pages, resource
budgets, native old-save upgrade, collection progression and all128-form milestone
still require the parent integration's exact final-ROM tests. No native Underwater
completion claim is made here. Re-run the profiler after final integration edits.
