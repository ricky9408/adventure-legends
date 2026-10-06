# Independent engine lifecycle review

These are synthetic host checks, not native controller acquisition, GBA frame
cadence, DMA execution, hardware pixels, or save provenance evidence. They link
real production modules. Intentional host fixture/state edits are declared in
the tests; they must never be relabeled as controller-earned progress.

## Reproduction

Run from the repository root:

- `python3 tests/underwater_engine_review/run_probe.py test_legacy_deferred_anchor_linked.py` (candidate A renderer)
- `python3 tests/underwater_engine_review/run_probe.py test_legacy_deferred_anchor_current.py` (optimized current renderer)
- `UNDERWATER_REVIEW_SOURCE="$PWD/build/underwater-candidate-a/source" python3 tests/underwater_engine_review/run_probe.py test_engine_lifecycle.py`
- `python3 tests/underwater_engine_review/run_probe.py test_bounded_magma_return.py`

The first probe is source-distributable and uses packaged fixtures. It adds all
six real Underwater modules to the archived deferred-anchor probe, retains all
27 original game assertions, and uses the current 32-field framebuffer cache
shape. The archived scripts/evidence are not replaced.

The second probe pins candidate A by default. Its source closure can be selected
with `UNDERWATER_REVIEW_SOURCE`, and another frozen manifest with
`UNDERWATER_REVIEW_MANIFEST`. Candidate A manifest SHA-256:
`f75b5b9924bda3e9118e64f80f12f5905d1d72cef166980c3d8a94d407484580`.
The full compiled source closure is checked against that manifest, including at
the end of the suite.

The third probe tests the bounded Magma shell-lift return on current development
sources, or an explicit source closure. It hashes sources before compilation,
checks they did not change during compilation/tests, and records that closure.

## Launcher safety

The launcher imports the original strict `collision_detail` / `run_attempts`
policy. All four GBA-style backing ranges use `MAP_FIXED_NOREPLACE`. No mapping
is overwritten and no ASLR or protection setting is changed. Only a proved
Python-heap overlap, with EEXIST before any game assertion, permits a fresh
process retry, at most three attempts total. Assertion failures, denied mappings,
unknown failures, and malformed diagnostics are never retried. Each attempt's
stdout, stderr, report (if generated), and a launcher receipt remain under
`build/underwater-engine-review`. Exact expected suite counts are enforced.

## Candidate A results

- Linked legacy deferred-anchor probe: 27/27
- Full-engine lifecycle: 30/30
- Last A lifecycle receipt: `build/underwater-engine-review/test_engine_lifecycle-u29mrz6g/launcher-result.json`
- Source closure verified unchanged
- No source lifecycle bug found within this review's scope

Coverage includes delayed new-room visits, rest/anchor/healing, two-page notice
warmup, no later hostile/ability input after queuing, invalid-state rejection,
world cancellation/death/load/new-game, queued quest rewards once only, trial and
old-cast revocation for party/command away-and-back changes, real evolution update
dispatch and cancellation, foreign preflight ownership, and return-arch/entry
intents completing before transition/save. Injected SRAM failures preserve the
old bank, retain the valid live anchor, and retry without rehealing or re-award.

Observed host work bounds: one world-job slice per EVENT_PENDING update; at most
three evolution preparation slices per update; evolution commit separate from
preparation; longest sampled event run 141 updates, writer 36 updates. These
counts are not cycle/frame-cadence guarantees.

## Bounded Magma return review

The new return job owns only the existing Save5 preflight scratch. It binds the
exact source room46/pose/checkpoint, chapter mirror, and progression revision.
The return source must be canonical and the Magma town already visited. It does
not treat a visit bit as validation authority.

After bounded full validation, an exact all-state comparison immediately precedes
a synchronous ordinary `enter_room(38,4)` under a private, one-use, call-scoped
lease. Only that matching wrapper call skips redundant `magma_visit`; direct
`magma_game_enter` calls retain complete validation. The lease cannot survive
returning from the callback. No public trusted flag or extra Save5 copy exists.

Current integrated result: 39/39 checks, including changing each of all 4,944
live Save5 bytes after successful validation and rejecting every commit. Other
checks cover before/after-validation field mutations, invalid/canonical-source
gates, multiple queue attempts, writer exclusion, foreign scratch after token
revocation, direct-wrapper rejection before/after the lease, and explicit,
world-reset, Magma-reset, selection, new-game, load, and replacement-entry
cancellation. First complete receipt:
`build/underwater-engine-review/test_bounded_magma_return-y3orkbp1/launcher-result.json`.

`tests/test_magma_game.py` also passed all 16 existing standalone world tests
with the new return-job implementation. Final native cartridge timing remains a
separate acceptance gate.

## Current renderer observation

`test_legacy_deferred_anchor_current.py` preserves all 27 gameplay assertions
and exact two-page warmup accounting. Its separate diagnostic C observer clears
a stale request in inert host DMA3 control at render entry, then samples DMA3
at `draw_actors` entry, before actor uploads can reuse it. A copy counts only if
source is the opposite framebuffer, destination is the current framebuffer, and
control is exactly the full-page 9,600-word transfer. Static paints plus these
exact copy requests must still total `[1,2,2,2]` across the original warmup checks.

This observes a requested transfer; DMA execution, pixel identity, hardware
correctness, and timing remain native acceptance gates. The archived candidate-A
probe/evidence is unchanged. The current-renderer probe passed 27/27; receipt:
`build/underwater-engine-review/test_legacy_deferred_anchor_current-joa5i3qu/launcher-result.json`.

## Bounded Southern rest review

`python3 tests/underwater_engine_review/run_probe.py test_bounded_southern_rest.py`
checks the current-source Southern rest scheduler (51 assertions). The two
actual rest targets now enqueue before synchronizing/mutating live campaign
state, anchor bits, health, or checkpoint. The job binds exact source room,
position, facing, checkpoint, chapter, progression revision, and full Save5
snapshot in the existing scratch. Preparation is bounded. A final exact compare
adjoins the equivalent typed anchor bit operation, followed by one heal,
checkpoint2, and the existing rest dialogue/save request. Public
`southern_anchor` remains fully validating.

51/51 integrated host checks passed, including pre-existing invalid input and all 4,944 Save5 bytes independently
mutated in each room30/31 after successful preflight; every commit was rejected.
Both lit/unlit anchors, early and ready-phase stale state, cancellation/death/load,
foreign scratch, writer exclusion/failure/retry, repeated queue/commit, and
unchanged public transaction rejection are covered. Receipt:
`build/underwater-engine-review/test_bounded_southern_rest-won96g84/launcher-result.json`.
This is synthetic host evidence only; final native timing is separate.

## Frozen candidate D replay

All four suites passed against `build/underwater-candidate-d/runtime-source`:
current renderer27 + lifecycle30 + bounded Magma return39 + Southern rest51 =147.
The full 1,163-input frozen manifest is
`e9b5eb4cfe1a26f8337c54956621d34403e73bd27bb85e9cd6b14ac75a8c786f`.
Reference ROM SHA-256 is
`0ce33fac654559563853c4a342b855357cc61c4dd52cdeb247c22293079afd82`.

Portable reports, launcher receipts, per-artifact hashes, and the check index
are in `docs/evidence/underwater-engine-review/candidate-d-index.json`. Every
reported production source hash was matched back to the frozen D manifest.
Set `UNDERWATER_REVIEW_SOURCE` to D's runtime-source directory; for lifecycle
and current-renderer probes also set `UNDERWATER_REVIEW_MANIFEST` to D's
source-hashes.json. Return/rest tests record and verify their complete selected
source closure directly.

The current renderer probe explicitly requires terminal save failure to remain
in SAVE_PENDING with no write/visible failure mutation, then checks the next
cheap update resumes and publishes the notice. This is the current scheduling
contract; the original A probe retains its original immediate-resume assertions.
D writer sampling is37 updates including deferred resume. No native timing
claim follows from these host checks.
