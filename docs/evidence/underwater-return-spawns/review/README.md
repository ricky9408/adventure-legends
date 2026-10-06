# Independent current-r6 return-boundary review

PASS: no blocking defect found in this two-file codec delta.

Reversed `codec.diff` in an isolated temporary directory and verified that both reconstructed files exactly match the prior independent review's SHA256 hashes. All other files in the 23-file runtime include closure remained unchanged.

## Result

Compared all 65,536 room/spawn byte pairs before and after the delta. Exactly five additional current-r6 landings are accepted on otherwise valid fully progressed state:

- 38:4
- 46:3
- 48:2
- 51:2
- 52:2

No other pair changed acceptance. Current validation and revision6 validation agree.

Also passed:

- 1,536 room/spawn/old-anchor/new-anchor combinations
- 57,351 bounded preflight checks
- 3,086 independently CRC-repaired raw-bank loads across both destinations, including refusal preserving the output and SRAM bytes
- 10,240 before/after historical revision1..5 Magma typed cases; the native-r5 fixture supplies legal old Magma state, while earlier revisions correctly reject that newer content
- An isolated native34-derived 38:4 test: rejected without Underwater town visit, accepted immediately after the visit with both Magma/Underwater anchors absent; no later Underwater teaching or quest progression required
- 55,808 exact room/spawn mask checks under ASan/UBSan, including current validation, revision6 validation, and bounded preflight

## Source review

The current campaign validator bounds room and spawn before indexing the new row or shifting the mask. The new revision-aware history lookup substitutes room38 only for revision6. All other historical lookups remain the original rows. The replacement retains `since5`, preserving Magma spawn3 anchor semantics; spawn4 requires the separate Underwater town-visit gate in both current and historical-r6 causal validation.

Only46/47 spawn2 are Underwater anchor landings. The added46:3 and48/51/52:2 landings do not borrow anchor permission. Existing source, visit, teaching, and main-route-prefix checks are still called. The existing game spawn counts inspected during review agree with the codec's new Underwater masks; this is not collision or native route proof.

The old Save5 historical header remains unchanged at `69dba67ea332f03bab26246b5739662aef7177ff1cabe43bed8b444940d40a13`.

## Exact source identity

- `src/save5.c`: `a637429f7e016b3d108b2c526917ab58768fc996a99b35355270114ad27237b1`
- `src/save5_underwater_policy.h`: `3f78289d79484df9223cc8593166df0c9bfd53a147f9d2347c7a9b9181bb4200`
- SHA256 of the compact, sorted 23-file runtime source-hash map: `54b40d2f51053a1392b10e4fba1ee3335707b308b2de18c52eaa57233ea02ce1`

Complete hashes and counts are in `result.json` and `sanitizers.json`. All runtime sources remained stable during the checks. The authenticated Magma fixture was verified and unchanged.

This receipt supplements the earlier bounded-transaction review for these two changed files only. It does not claim another run of unrelated long suites, native acquisition, geometry reachability, or full-frame timing acceptance. ASan/UBSan ran with leak detection disabled because LeakSanitizer is unavailable under the executor's ptrace runtime.

## Reproduce

```
python3 docs/evidence/underwater-return-spawns/review/check_boundary.py
python3 docs/evidence/underwater-return-spawns/review/check_sanitizers.py
```
