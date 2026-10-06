# Independent historical-policy / third-tier foundation review

Result: PASS for the two scoped historical-policy and multi-trial expansion gates. No blocker found in this core-only refactor. This does not approve Magma content enablement or all proposed design cards.

## Scope and provenance

- Reviewed isolated `adventure-legends-magma-core`, without modifying production source, authored content, enablement, or Southern/S3 files. Every review artifact is under `build/policy-independent-review`; host compiles also used unique temporary directories.
- Authoritative baseline ROM: frozen `adventure-legends-southern-s3/build/emberbond.gba`, SHA-256 `87d16a0fc513d7e8a491e0b5ac5929f7951e1e44e18b7f534f1e5e0cc794d4de`. The initially referenced live Southern build was stale S2; parent clarified the exact S3 path, independently verified here.
- Reviewed `src/creatures.c`: `3495ca3d141b6162452b64e0f5f38a6aa88f46e2fe3cd7352db1825d15a1c350`
- Reviewed `src/save5.c`: `379080d8b16364f9dbae552835caf34daec4d210a2e250d0e74f7055cdab0216`
- Frozen inputs and evidence hashes in `docs/evidence/magma-architecture-final.json` all verified. Production src/assets/tools/tests did not change during this review; the policy worker updated documentation/evidence concurrently.
- Current 41 forms, 41 abilities, 61 learns, 20 edges, content revision4, generated C data, identity lock, Save4 and equipment runtime remain unchanged. The authored catalog is semantically identical JSON to S3; its pre-existing compact formatting differs.

## Independent findings

1. Revision1–4 bank acceptance no longer depends on current creature form/index/learn/trial/edge or equipment/quest relationships. The streamed scan and post-decode full validator use frozen policy. Historical command1 survives forced current removal; broader current Q0 cannot authorize old objectives8. Current writes remain checked against both policies before any SRAM write.
2. The separate legacy trial scalar retains its old meaning when the current same-family union grows. Qualified keys, distinct masks, closed prerequisites, independent branch subsets, wrong-family rejection and explicit target selection work. Original evolved forms still permit historically legal absent trial/bond evidence; neither loading nor evolution fabricates rewards/trials.
3. Immutable semantic snapshots are pinned independently of live authoring. Released learn relationships/edges/trial assignments remain locked; derived offsets/counts can change for an added edge on released evolved form2. The F001 test-only 2→3 extension preserves story identity, inherited commands, original1→2 semantics and every old revision.
4. No new mutable validation cache, trust-only load shortcut, whole-save stack copy, or SRAM mutation during read/failure was found. All empty-instance bytes remain checked. Accepted decoded results and rejection/output atomicity match the frozen oracle.

## Additional tests written for this review

`independent_targeted_tests.py` and `targeted-results.json`:

- Synthetic F011–F016 tables use the actual planned graph IDs: linear31→32→33 and34→35→36; branch targets39/42/45/48. These are structural fixtures, not designed gameplay/stat/polarity approval.
- All393,216 u16 trial patterns across six families passed under ASan/UBSan. Covered prerequisite-only rejection, distinct branch keys, same-bit cross-family rejection, all branch target choices, legacy ambiguity, decline atomicity, retained instance identity/equipped commands, and historical revision1–4 rejection of every new form.
- Removed every current form, ability, learn, edge and sparse-index row; removed all current equipment definitions and acquisition-source IDs; zeroed current quest masks, equipment source→quest relationships and trial recruitment relationships. Historical snapshots remained intact.
- Against the SHA-pinned frozen S3 oracle,12,753 CRC-valid whole-bank comparisons matched exactly:558 accepted,12,195 rejected. Includes12,600 deterministic mutants across collection, instance, party, quest, credit/event, equipment and reserved bytes, plus independent reward/event/aid ledgers.
- All four original historical SRAM images still load byte-identically. Each of nine original/completed bank seeds fails incompatible current re-save with zero writes and unchanged caller state/SRAM. Every probe checks `load == has_valid`, output atomicity, and SRAM immutability.

Reproduce from the isolated workspace:

    SAVE5_HISTORY_BASELINE=../adventure-legends-southern-s3 python3 build/policy-independent-review/independent_targeted_tests.py

## Supplied tests independently rerun

All81 tests passed:

- `tests/test_magma_architecture.py`:7
- `tests/test_magma_history_core.py`:4;100,608 policy matrix plus144,000 corruption comparisons
- `tests/test_save5_history.py`:7
- `tests/test_save5_history_differential.py`:9;166,699 whole-bank comparisons,4,680 accepted and162,019 rejected
- `tests/test_save5.py`:41
- `tests/test_southern_save.py`:13, including147,504 durable interruption/success positions

Both generated-data/history `--check` commands also passed. Logs are beside this report.

## Performance / stack

Independently recompiled and ran `profile_magma_validation.py` in `arm-validation`, with the frozen controller-earned21 fixture. The entire source-pinned JSON report and every measured cycle exactly reproduce the worker's final report:

- Earned21 anchor105,891→99,121 cycles (6.39% better); historical full validation129,218
- Synthetic30 anchor110,002; historical full validation139,523
- Full160 anchor427,000→445,250 (18,250 cycles,4.27% worse); historical full validation464,072

Full160 synchronous work already exceeds one frame and remains a future engine integration concern. This is not a new save-corruption blocker. The separately source-verified writer report remains within its limits:21,657 begin;60,315 step at budget1024; worst160,876 at budget3072 with synthetic48 gear. No extra mutable RAM is reported; own stack frames from independent ARM compile match the evidence (scan128, current instance48, historical instance32, historical full validator128). Reviewed direct-C sums are static bounds only, not runtime high-water or interrupt-inclusive measurements.

## Explicit remaining integration gates

- Proposed polarity-flipping forms39/48 are not supported by the current family-wide catalog polarity guard (`creatures.c:782`). An independent temporary flip reproducer in `polarity-flip/` confirms catalog rejection; direct isolated evolution correctly copies the target polarity. A separately reviewed current per-form polarity policy is required before those design cards can be enabled. This is outside the two gates resolved here.
- Magma art/handlers/quests/acquisition, branch encounter receipts, UI target picker and full-engine u16 context integration are not implemented or accepted by this review.
- Pre-v5 Save4 synthesis intentionally remains the existing current-policy migration path; the revision1–4 isolation claim is Save5 content revisions1–4.
- Future content requires explicit new-revision routing/policies and revalidation; current incompatible semantics are deliberately rejected on re-save rather than silently migrated.
- Cold menus, native full-engine cadence at30+ companions, runtime stack high-water and physical hardware remain unmeasured.
