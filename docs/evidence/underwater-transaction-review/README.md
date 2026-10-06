# Independent bounded transaction review

Outcome: no blocking defect found in the reviewed Save5 preflight, bounded creature admission, or Underwater durable transaction implementations. This is a source-locked host semantic review, not native gameplay, controller acquisition, or full-frame timing acceptance.

## Reviewed identity

- Delivered Magma authority: commit `0a8b05c3e24d02bd350a11c32289fb5686641535`; reported delivered ROM `90ba47f30a0c94c28f073d26cc31ac5f5c736eb4d6e704d090892d2776f1ffb2`
- Authenticated input: `tests/fixtures/v5-revision5/magma-all65-town.sav`, SHA256 `a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858`
- Save5: `dbeef77a1e478c33e3c1405f5ea6b6e6ac7f7f7eb48acb4855d6b04671267682`
- Preflight include: `14d05e2ff8943f8effa093ba9350e11b2d615bd46951d713bbf1c016f2356eb4`
- Underwater transaction include: `3122483bbd99be0a43dd15bf5e26fd83e51c4e74e5e29d649a9acbf70305d0d9`
- Core admission include: `a971e84833a63ccea93c72d4b01859d965c765bcc95abd7884e33ea544a75cd1`
- Creature core: `b6d892f4b0f5969101b35b541aa07a8e923ad41be593a6f398c89363a6d56175`
- The full 23-file quoted-include runtime closure appears in each JSON result. SHA256 of the compact sorted JSON source-hash map is `a97b189d7d2c4f250cdb2c5d8a664df2c3d8fccf96207043ec809aea988a152a`

The save owner confirmed this source freeze before final testing. Before/after hashes match for all test runs. No production edits, GitHub writes, delivered-sibling edits, or fixture changes were made by this review.

## Independent checks

`review.c` and `admission_review.c` are independent test harnesses. The existing fixture setup is used only as a seed/stress constructor; the transaction route used for the 97-state grid is built in the review harness and compared operation by operation. `QUEST_PROGRESS` has no synchronous twin, so its reference is a staged offer plus the original synchronous objective, with publication only on success. Synthetic typed states and generated SRAM are never represented as controller-earned progress.

Both strict optimized (`-O2 -Wall -Wextra -Werror -Wstrict-aliasing=2 -fstrict-aliasing`) and ASan/UBSan versions passed:

| Check | Cases per build |
| --- | ---: |
| Underwater request result and exact output bytes vs synchronous reference | 59,254 |
| Full-state single-bit mutation: bounded preflight vs complete validator | 158,208 |
| Exact stale-state denial: every Save5 byte before visit/recruit/gear commit | 14,832 |
| Reached-phase cancellation, scene change, and load invalidation | 15 |
| Both-bank every-write-cut recovery plus injected write corruptions | 12,306 |
| Independent core admission query/detail and grant/evolution commit parity | 14,652 |

Additional checks include copied request mutation, writer/preflight exclusion, zero and oversized budgets, distinct live-pointer identity, no SRAM writes before explicit save, no durable changes before phase6, once-only commit tokens, failed/incomplete attempts, and fail-closed 32-bit token exhaustion. Test-only wrappers seed otherwise private serials near UINT32_MAX in temporary compilation; production files remain unchanged.

The exact `Save5State` size is 4,944 bytes in these builds. Each byte was independently changed in the final stale-state checks, including C padding, campaign metadata, party/history/credits, quests, and equipment. This exercises full-state equality rather than a checksum or roster-only gate.

Both destinations were tested at every permitted write cut 0..6,145. Loads selected the complete old state until the new commit was complete, then the complete new state. The old bank and SRAM before 0x0200 stayed unchanged. CRC was independently recomputed over the finished bank with CRC/commit bytes zeroed. Selected corruption at invalidate, header, instance, quest, payload-end, and commit writes failed readback and retained the old loadable state.

## Historical acceptance

- Independently compared all 15 oracle source files to `git show` of the delivered Magma commit. All are identical
- The generated revision1..4 creature history block is unchanged
- `src/save5_history_policy.h` is unchanged at SHA256 `69dba67ea332f03bab26246b5739662aef7177ff1cabe43bed8b444940d40a13`
- Independently reran the existing historical differential suite: 61,216 comparisons, 441 accepted and 60,775 rejected, with exact decoded/failure-byte equality. The complete log is `historical-differential.log`
- Separately generated legal revision5 states with 89, 90, 159, and 160 retained individuals using the delivered Magma core. Current load, current bounded preflight, revision6 resave, and reload all preserved the typed payload. These include genuinely over-budget rosters and demonstrate that admission reservation remains separate from save validity. See `old-overbudget.json`

The fixed wire version5 layout, 24-byte instances, 160 slots, 6,144-byte banks, and 0x0200/0x1A00 bank offsets are unchanged.

## Predicate and commit review

The preflight phase map preserves the synchronous current validator's checks:

1. Campaign scalar, chapter, room, and spawn validation
2. Nonzero next identity; party structure and members; exact seen/obtained subset and enabled identities
3. Every 24-byte instance, including all empty bytes; empty expedition credit; bond cap; identity ordering and uniqueness; retained obtained evidence; unique story-locked receipts
4. Every quest objective/state and reward byte; all reserved fields; anchors and region flags; campaign/quest causality
5. Retained creature, Southern, Magma, and Underwater source evidence accumulated during the record walk, then checked against the original helpers
6. Every equipment record; unique ownership and seen bits; equipped references; reserved/history/reward validation; quest/equipment receipt correspondence

No coverage/admission limit was added to Save5 validity. Current and historical policy paths remain distinct. New Underwater trial/bond requirements apply only to new families; the old trial/bond acceptance was exercised by the historical differential.

The raw snapshot lives in the existing Save5 scratch allocation. Its accessor is const; mutable equipment staging is in the separate existing `BankScan.equipment`, not the raw snapshot. The word-copy/equality paths use the existing GNU may-alias type and naturally word-aligned structs; the static state-size assertion covers the final whole word. Strict-aliasing and sanitizer builds passed.

Writer begin is refused while preflight is BUSY/DONE. Preflight begin is refused while the writer is BUSY. Load/has-valid cancel preflight before reusing scratch. Tokens do not wrap back to old identities; exhaustion refuses new work. Copied request fields are validated at full unsigned width before narrowing. Stale tokens cannot complete a newer operation.

The final commit first checks the exact original full-state pointer and all 4,944 bytes. Recruitment then performs the core's distinct-live-roster exact comparison and once-only admission commit, followed by infallible, already-validated quest/source receipt changes without a yield or callback. Gear claims stage both items before publishing equipment and quest receipts. Trial changes stage only the exact selected individual. Failure paths do not publish partial receipts or gear. The final phase is the only durable mutation point.

Repeated invitations require a currently retained terminal individual and the corresponding source. Obtained history is not counted as a retained copy or a selected trial participant. The exact source/family/identity checks and synchronous field/context semantics match in the request grid. Evolution checks retain the same context, sanctuary, confirmation, trial, bond, and prospective-admission ordering as the synchronous core.

## Limits and integration requirements

- This is a cooperative in-process C API, not a memory-isolation boundary. The core accepts a caller-owned immutable snapshot pointer and requires that ownership contract. A cast that writes the const raw snapshot, or a retained equipment-stage pointer used after cancellation/reuse, violates the borrowing contract and is not prevented by token checks. Current reviewed job code exposes no mutable raw-snapshot path and does not retain a stage pointer across calls
- Exact comparison detects the current byte state; an external mutation that changes and restores bytes between calls is not a history log. Runtime scene/attempt generation, participant cancellation, and ordinary-world freezing remain necessary
- Parent-owned engine integration is still changing. This review does not approve its update/draw scheduling, event queue, death/load/new-game wiring, attempt lifecycle, renderer, or native input routes
- No native Underwater89/50 acquisition or complete 280,896-cycle frame acceptance was established here. The owner's isolated ARM phase timing is useful component evidence only
- The historical differential is an independently rerun existing suite, not a second independently designed historical model. The new host transaction/core harnesses are independent, but synchronous parity alone cannot prove game-design intent
- LeakSanitizer cannot initialize under this executor's ptrace runtime. ASan/UBSan passed with `ASAN_OPTIONS=detect_leaks=0`; no claim of LSan coverage is made. These production paths allocate no heap

## Reproduce

From repository root:

```
python3 docs/evidence/underwater-transaction-review/run_review.py
ASAN_OPTIONS=detect_leaks=0 python3 docs/evidence/underwater-transaction-review/run_review.py --sanitize
python3 docs/evidence/underwater-transaction-review/run_admission_review.py
ASAN_OPTIONS=detect_leaks=0 python3 docs/evidence/underwater-transaction-review/run_admission_review.py --sanitize
python3 docs/evidence/underwater-transaction-review/check_old_overbudget.py
python3 tests/test_underwater_history_differential.py
```

Results are evidence for the exact source hashes above. Rerun affected checks if that closure changes.
