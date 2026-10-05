# Full-screen companion-growth milestone — verification

## Reviewed correction build (2026-10-05)

The corrected ROM is **1,823,228 bytes**, SHA-256 `63a1161f35ad728f2d72134f0d3183ee5d6449389dbc46e375bd0ebcc236261d`. It includes three focused review corrections:

- Real departures from the village start a new expedition for every available route; checkpoint reloads preserve the existing expedition
- Save-write failures remain clearly visible on paused/modal panels until acknowledgement or a new save attempt; acknowledging the notice does not claim the write succeeded
- Six malformed-save native tests now recompute and assert full-bank v5 CRC32 before testing semantic rejection

A fresh `make test` and `make test-tools` passed for this exact ROM. There are **10,724 native-emulator assertions**, including the 115-assertion expedition regression, with zero failures. Controller journeys and explicitly labelled malformed SRAM inputs are distinct from supplemental host fault-injection tests. Paused wait/close/retry and rendered-notice/OBJ occlusion checks are host tests using the actual C implementation, not controller progression claims.

IWRAM code is **26,712 bytes** within the 28-KiB code cap; initialized EWRAM/BSS is **44,984 bytes**. Both full campaign cadence routes passed their strict native-frame checks. [Exact corrected-ROM evidence and report hashes](systems/review-fixes.json) identify this run.

The original delivered ROM, source ZIP, player preview, and earlier `docs/systems` reports remain unchanged historical artifacts. Their original-ROM measurements follow below. The corrected-ROM report above supersedes their artifact identity for the reviewed source. No hosted CI or physical-hardware certification is claimed; the blocking cold checkpoint decode remains an explicit limitation.

## Original delivered milestone

Verified 2026-10-05 against the merged campaign baseline `cda9ccd8ecc30778ba46ff9c5c3bbf96d77c6de0`. Technical evidence below contains progression spoilers; player media does not.

- ROM: **1,822,892 bytes**
- SHA-256: `d19e9b93df294e0d54de277ab90e3d2571c402adc68e82d8adb0a4a6114e6a45`
- GNU ARM GCC 14.2.1, valid native GBA header, warning-free build
- Deterministic regeneration changes **zero source bytes** and produces the exact tested ROM
- IWRAM code: **26,528 bytes**, within the 28-KiB code cap and 4-KiB stack reserve
- EWRAM initialized data/BSS: **44,968 bytes**, below 256 KiB

### Actual playability

**10,609 native-controller assertions pass**, with zero failures: preserved first-chapter/review/exploration checks, exhaustive minimal and optional campaign routes, fresh six/eight-heart evolution routes, an authentic format-4 migration route, full-screen pixel/OAM tests and advanced-command behavior.

The routes obtain exactly **eight enabled forms** through ordinary controller play. They test all four personal trials, declined then accepted evolution, original/new command selection, interrupted commits, reloads, field-capability preservation, ending/replay sprite identity and postgame traversal. Reserved or merely designed forms never enter the roster.

The wind puzzle covers all 64 states/192 rotations in source-backed solver tests. The movable-parcel puzzle covers 756 reachable labeled placements, 4,544 push edges and 672,606 integer-pixel push stances; reset and exit remain reachable. Permanent rewards cannot repeat, and completed arrangements cannot be disturbed into a broken state.

### Full-screen world and HUD

All **160 displayed rows** match the original grove source atlas at all four camera-word alignments. Native screenshots also match outside explicitly reconstructed nonzero OBJ and authored decoration pixels. No old HUD strip is stretched or painted over. World art/collision source fingerprints remain unchanged; camera range and screen transforms are deliberately updated.

Tests cover six/eight floating hearts, upper-right companion/action icons, top-edge clipping, native 240×160 output and journal visibility. The first four companions' actual evolved sprite bytes are verified in final/replay OAM and VRAM.

### Frame cadence and honest loading boundary

Native clock: 16,777,216 Hz; display frame: 280,896 cycles, approximately 59.7275 Hz. Host emulator throughput is not used as a frame-rate claim.

- Each independent full campaign route: **60 steady scenes, 20,460/20,460 updates and presentations**, plus **28 cold UI windows, 1,680/1,680**
- Largest sampled original-campaign/UI update+render: **217,237 cycles**
- Ten eight-heart advanced-effect windows: **2,400/2,400 updates and presentations**, including active final-boss projectiles/hazards; largest sample **203,689 cycles**
- Evolution animation: **936/936 updates and presentations** across fresh/minimal/migrated routes
- **476 incremental save windows** satisfy strict steady writer cadence; largest measured writer+render sample **262,188 cycles**, about 93.34% of budget

The cold Continue operation intentionally performs a blocking checkpoint decode before entering the incremental writer. Its overlapping old-frame sample is **reported separately**, not counted as smooth gameplay or a steady writer frame. The short saving state freezes world actions while still rendering/updating; four-companion writes ordinarily take about 18 updates. This explicit loading boundary is a known limit, not a claim that every startup/transition is single-frame.

Timings exclude VBlank waiting and OAM commit; independent bitmap-page checks verify presentation. These are representative emulator measurements, not exhaustive all-frame or physical-hardware certification.

### Persistence, failure and portability

Host verification includes 26 save4 groups, 16 save5 groups, 23 creature groups, 12 trial groups, 39 supplemental advanced-power contracts and an actual-game-function asynchronous failure-feedback regression. Host-injected state/fault cases are explicitly separated from native controller progression.

Save5 tests include every write interruption position, corrupted write/readback cases, every byte in both banks, malformed creature/party/content fields, sequence wrap and older-save conversion. Authentic earlier saves and their hashes/provenance ship under `tests/fixtures`; no sibling workspace is required. The v5 writer leaves original save bytes untouched.

The prior review's misleading-success-toast issue is fixed. This milestone also fixes reload incorrectly starting a new expedition, and ensures final-card portrait uploads occur after saving rather than being overwritten by village props. Successful retries clear stale failure feedback.

### Reproduction and evidence

```sh
make
./tools/build_mgba_bridge.sh
make test
make test-tools
make assets
make
make gameplay-video
```

[Compact summary](systems/summary.json), bounded assertion audit files, independent [minimal cadence](systems/cadence-minimal.json) and [optional cadence](systems/cadence-optional.json) are checked in. Raw traces and paired machine-state/SRAM snapshots regenerate under ignored `build/`. `tests/test_save5.py --arm-timing` reproduces isolated ARM writer benchmarks.

The default video is a **22.75-second spoiler-free opening teaser**, captured frame-by-frame with real emulator audio and controls. Full story/trial/evolution recordings and QA screenshots are developer evidence. Older `docs/campaign`, `docs/milestone1`, `docs/perf` and polish reports describe earlier ROMs and are not this release's timing evidence.

### Remaining scope

Physical GBA hardware, flash cartridges, other emulator/compiler releases and the macOS bridge path are not verified. Hosted CI is not configured. Numerical five-phase battle modifiers, exposed storage management, equipment, regional cities and the full 128-form roster remain later work. Current counts: **12 designed, 8 implemented/obtainable/verified, 128 reserved capacity**.
