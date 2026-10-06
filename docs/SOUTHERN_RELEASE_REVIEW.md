# Southern S3 independent release-candidate review

## Verdict

No current release-blocking state, persistence, selection, collision-cache, ownership, cooldown or tile-lease defect was found in this review. All independently executed targeted checks passed. This is approval of the reviewed core/integration scope, conditional on the separate exact-ROM native controller/combat/performance acceptance. It is not a physical-hardware or whole-game cadence certification.

No production/runtime files, existing tests or external state were changed. All new deliverables are in `build/release-independent-review/`; temporary test variants remained temporary.

## Identity and reproducibility

Candidate: `adventure-legends-southern-s3`, 5,858,700-byte ROM.

- ROM SHA-256: `87d16a0fc513d7e8a491e0b5ac5929f7951e1e44e18b7f534f1e5e0cc794d4de`
- ELF: `b51c73b85837f228a0b334482bdc74b9cbc8173ac9d15f0ae122cd336ba632e9`
- Symbols: `ceedba1a6052fe450f17c91375eef6ddd5200d1a7bb01394c1eb95d2bc4f1305`
- Source manifest: `build/source-hashes.json`, SHA-256 `609104f75fa341bb67d0d1e2a362db7b03ed655ecb6eed41c101b0c799b2f089`
- All 707 manifest entries matched before and after the checks
- A separate clean ARM rebuild in `rebuild/` reproduced all three artifacts byte-for-byte, including ELF debug content and symbols

Rebuild used the repository compiler/flags and `make -j2 BUILD=build/release-independent-review/rebuild build/release-independent-review/rebuild/emberbond.elf`, followed by objcopy and the normal header fixer on the independent ROM. It intentionally did not invoke the manifest-writing ROM recipe. See `rebuild.log` and `summary.json`.

## Independently executed checks

`targeted-checks.json` and `targeted-checks.log` record 34 passing unittest cases: Southern core (8), branch/capability contracts (4), Southern persistence (13), capacity/sanitizers (4), validation optimization (4), and exact-source geometry fingerprint (1). `run_checks.py` reproduces them with isolated outputs.

Additional passing checks, not added to the unittest count:

- Quick-party scan: 265,216 reference-equivalent cases, both strict and ASan/UBSan builds; roster bytes unchanged
- Actual Southern power handlers linked with actual gear/weapon/core code: strict and ASan/UBSan passes; all 20 commands, ownership, shared lease, cooldown/snapshot behavior, guards, echoes, generations, wall/corner behavior and 4,800 drawing calls (maximum 12 objects)
- Exact-source save-feedback host integration: frozen queued-begin input, unchanged previous SRAM, invalid snapshot rejection, six modal notices, retry, and party ownership preservation; `save-feedback.log`
- Validator differential rerun under ASan/UBSan: 23,531,642 XP/level pairs, 301,510 party-reference pairs, 1,048,576 collection-byte pairs and 36,720 instance corruptions; `validation-differential-sanitized.log`
- Added randomized crescent stress using the explicit uncached reference: 16,000 scenes / 192,000 target comparisons across all facings, warmed caches and added/removed rectangles, under ASan/UBSan; `crescent_random_review.c` and `crescent-random.log`
- Save ASan/UBSan: 1,200 valid roundtrips, 1,200 invalid snapshots and 79,491 randomized-budget steps, including full160 / all41 / all30 / authored25 state; `southern-save-limits-sanitizers.json`

These are host/synthetic fixtures, including temporary augmented branch/catalog/capacity variants where explicitly labeled. They are not native acquisition or controller evidence.

## Source findings

- `src/creatures.c:17–27, 796–891`: zero records still examine every byte; known-level XP intervals are equivalent to the previous monotonic lookup; standalone party validation remains full, while roster validation validates every record once. Collection subset/identity checks and instance uniqueness remain enforced
- `src/save5.c:465–520` and `src/southern_quests.c:104–180`: keyed source evidence stays bounded and family-specific. Trial/level/bond evidence is local to one instance. Mixed rewards stage equipment before granting; failed capacity preflight remains atomic and retryable
- `src/game.c:308–312, 470–478, 648` and `src/progression.c:116–117`: entry freezes before snapshot work; the next frozen update calls the unchanged snapshot API. No gameplay/input path runs between those phases. Failed begin and failed stepping restore the requesting state with failure feedback
- `src/quickparty.c:49–58`: bounded wrap is called only with +/-1 and preserves the 160-slot plus empty-sentinel traversal
- `src/game.c:378–386, 451–467, 478, 549`: fingerprint covers every current mutable collision input: room, bridge, torches, campaign flags, Dry Road bit, trial parcels and regional crates. Northern and Southern collision bands are static. Synchronization precedes effect ticking and rendering; room/death/new-game resets invalidate effects
- `src/southern_powers.c`: only scenery proofs are cached; endpoints/generations key mark LOS, targets remain live, complete crescent spans preserve raster/diagonal rules, and hit ledgers survive invalidation. Aim requires the same selected instance/form/command. Selection cannot renew lifetime/cooldown. `src/northern_powers.c:78–94` rejects overlapping leases and premature release. `src/gear_runtime.c:41` retains the active-effect gear lock

## Timing and remaining limits

Reviewed archived timing sources and harnesses, without presenting them as independently rerun native timing. The second validation evidence matches current sources and reports the actual21 anchor microbenchmark falling from 127,256 to 105,891 cycles. Its current-source isolated save report has a 153,114-cycle maximum authored25 step at budget3072; synthetic48 reaches 164,858. Module timing explicitly uses synthetic world/OBJ callbacks. These numbers do not establish full-frame cadence.

The rebuilt ELF places IWRAM end at `0x03006d28`, below the linker reserve boundary `0x03007000`; this is not runtime stack high-water measurement. Physical GBA, alternate compiler/emulator releases, full native acquisition and final native cadence were not independently exercised here.

The legacy-trial-union and historical-policy items in `docs/SOUTHERN_CORE_REVIEW.md` remain future expansion gates. No corresponding authored-policy change is enabled now; they are not current S3 failures. Any future collision-changing system must extend the explicit invalidation contract.
