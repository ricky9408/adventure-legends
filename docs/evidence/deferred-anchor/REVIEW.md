# Independent deferred-rest anchor review

## Result

No blocking correctness defect found in the reviewed deferred-anchor implementation. The production engine performs the anchor proof only on its dedicated frozen frame, after both Mode4 bitmap cache pages are warm. The original exact `magma_anchor` validator and the bounded Save5 codec/writer remain in use.

This review's evidence is **synthetic host integration**, not controller-earned gameplay, a native-ROM screenshot, hardware timing, or an emulator acquisition claim. The separate parent-owned native D timing reproduction is required for presentation-budget acceptance.

## Reviewed sources

- `src/game.c`: SHA256 `6c7872c036672678127ba0b71c2b9e4a7c3ea3dd0cecc90f84143396276e6421`
- `src/magma_game.c`: SHA256 `9074017c7c25fe39f4a66c5054018fb98efa2cd547ba4e653363a5751016625c`
- `src/magma_quests.c`: SHA256 `a4aaaaec7a301d8dee1b6316a8fd7feed42d2297a58d4e2ae5da60120a05d617`
- `src/save5.c`: SHA256 `93c42b198a22914d1de853c4fd54093acf05a14c9705eca15b0ac14e2757d2b9`
- `src/progression.c`: SHA256 `62a18d3ca5875fb89f39eaac3bfa43825a4f7534427d4c3dccdb76f60717e6e3`

Contracts read: `docs/magma-runtime/HANDOFF.md`, `src/magma_game.h`, `tests/test_magma_game.py`, `tests/test_save_feedback.py`, the production rest/prepare/reset/entry paths, Save5 bank state machine, attack dispatch, quick-party input, and bitmap/OBJ rendering.

No production file or existing test was changed by this reviewer. All new review files are confined to this directory.

## Observed scheduling

The independently instrumented full production engine gave the following sequence for both room38 and room39, with both a newly lit and an already-lit rest anchor:

1. Real host `update(A|R)` enters the authored A interaction and immediately freezes in `SAVE_PENDING`; pending stage is3. No anchor validator, snapshot, writer step, enemy update, projectile update, Magma world tick, or R ability runs after the rest. The prior legal campaign spawn remains in the in-memory save, while the requested checkpoint is3. The first real `render()` calls `render_static` once.
2. The next frozen update reduces3→2 without validation. The other real render page calls `render_static` once. Both page caches now contain the saving notice.
3. The next frozen update reduces2→1 and calls the real `magma_anchor` exactly once in state6. On success, campaign.spawn becomes3. Neither Magma nor progression bitmap revision changes. Real render reuses its cache page.
4. The next frozen update reduces1→0 and calls the existing `save5_begin` exactly once. No writer step or SRAM write occurs on that update. The other render page remains cached.
5. Subsequent frozen updates run the existing incremental writer. Normal play resumes only at its terminal result.

Cumulative `render_static` calls across those four displayed stages were exactly `[1, 2, 2, 2]`. The test executes the real render cache; its inert mapped backing memory does not emulate DMA or prove final display pixels/timing. The changed REST visual is a streamed OBJ asset, not bitmap overlay content, so it does not require an additional bitmap revision.

## Atomicity and boundary coverage

The new harness passed27 focused scenarios:

- Both anchor rooms, unlit/lit, through actual production A dispatch, prepare, snapshot, incremental write, and readback
- A+R cannot start a cast after rest; imminent synthetic hostile projectile/enemy state stays unchanged through save completion
- START+ A opens pause before rest; L+A belongs to quick-party; SELECT+A starts rolling and cannot also rest
- Repeated direct rest calls while one request is queued do not duplicate healing, revisions, or validation
- Repeated prepare after successful consumption returns0 without revalidation
- Wrong room, wrong campaign room, restamped campaign spawn, changed checkpoint, cancellation/reset, and invalid roster all fail closed before snapshot or writer work
- Wrong-mode prepare consumes the request without invoking the validator
- Cancellation restores each exact prior checkpoint0/1/2/3; an already changed checkpoint is preserved, and cancellation does not overwrite a different current room's checkpoint
- Production `start_game(0)` and `start_game(1)` cancel an uncommitted anchor before new-game/load work; their ensuing ordinary saves finish validly
- Production death/reset cancels an uncommitted request and restores its prior checkpoint when called at an explicitly synthetic pre-freeze boundary. Real post-rest gameplay cannot reach this boundary because the new engine gate has already frozen it
- Failure before any bank write, during writes, and on the final commit byte, using fail-after0/50/3000/6144. The previously committed bank remains byte-identical and loadable
- After the typed anchor proof succeeds, a later writer failure intentionally retains the valid live anchor/checkpoint3. It displays persistent save failure, and a retry saves the live result without re-running the proof. This matches other unsaved progression; it is not an anchor rollback
- Full controller-earned C SRAM was also decoded and deliberately altered into an unlit/current-room host setup for a large-roster regression. Its roster remains unchanged, but this derivative test is explicitly synthetic and does not claim D gameplay acquisition

The proof-stage full validator is unchanged; no bypass, weakened predicate, second save snapshot, or synchronous SRAM side route was introduced. Rosters/equipment and reward-related data are unchanged by rest. The codec remains responsible for safe bank selection, validation, byte budgeting, verification, and commit.

## Files and reproduction

- `engine_probe.c`: observation hooks and inert host address mapping; does not replace engine functions
- `test_engine_probe.py`: full-engine synthetic test runner
- `engine-probe-results.json`: machine-readable27-scenario result and source hashes
- `engine-probe.log`: default compiler run
- `engine-probe-ubsan-results.json` and `engine-probe-ubsan.log`: the same cases with UndefinedBehaviorSanitizer
- `existing-runtime.log`: existing Magma runtime suite,16/16 pass
- `existing-save-feedback.log`: existing production save-feedback suite, pass

Run from repository root:

```
python docs/evidence/deferred-anchor/test_engine_probe.py
HOST_CC='cc -fsanitize=undefined -fno-sanitize-recover=all' PROBE_RESULT_NAME=engine-probe-ubsan-results.json python docs/evidence/deferred-anchor/test_engine_probe.py
python tests/test_magma_game.py
python tests/test_save_feedback.py
```

The harness must be rerun if reviewed source hashes change. Host function instrumentation and synthetic state do not establish native performance; use the parent-owned candidate-D ROM/native report for that acceptance.
