# Northern N5 release verification

Developer evidence; contains progression spoilers. Verified reports are dated 2026-10-05. Player instructions remain in the spoiler-free [README](../README.md) and [Japanese guide](PLAY_JA.md).

## Exact cartridge

- ROM: **4,351,688 bytes**
- ROM SHA-256: `302316c53d6fb9dafa0ecbf9f679c9c39af3a150af3aa78398c368312e50399e`
- Symbols SHA-256: `7110402451d7bea92ebd1d83dfddbf2f389468028e8842ef6afa22f043595018`
- Save wire version **5**, content revision **3**; exact revision-1/revision-2 whitelists and older format readers remain supported
- IWRAM code **28,120 / 28,672 bytes**; initialized data plus BSS **47,548 bytes** in EWRAM
- Native evidence uses mGBA 0.10.5 and GNU ARM GCC 14.2.1

A clean isolated rebuild reproduced both the frozen ROM and symbols byte-for-byte. Isolated asset regeneration checked 859 existing source/art files with no changes or missing inputs; only four documented, source-package-excluded River overview images were recreated. These are reproducibility results, not extra gameplay assertions.

## Completed Northern checks

The six named native-controller reports pass **24,180 checks, zero failures**:

| Suite | Passed checks |
| --- | ---: |
| Full Northern journey and retained collection | 9,978 |
| Sky-clear main route | 4,668 |
| Pixel, movement and performance stress | 314 |
| Boss controls, stage timing and retry | 221 |
| Modal scene controller setup/resume | 162 |
| Northern combat and equipment, 85 functional cases | 8,837 |

The 25-scene modal pixel/OAM comparison passes separately. The 78 host objective-order/capacity cases and 15 source-provenance checks (one accepted producer and 14 malformed-producer rejections) are **synthetic host evidence** and are excluded from the native assertion total. Assertions repeat across frames and branches; their sum is not a count of unique behaviors.

One independently rebooted, controller-earned save records **21 obtained historical forms, 11 retained family instances, all 22 regional quests and 19 equipment items**. The project contains **30 areas**, including eight Northern areas. Enabled rows, host grants and archived prior-ROM machine states are not substituted for acquisition proof.

The five-visible-enemy combat window includes two visible hostile shots, two player arrows and a new persistent effect simultaneously for 12 frames. It preserves **420/420 updates and page flips**, with a **208,128-cycle** peak. Cold journal windows preserve **80/80**, with the highest Northern journal peak **266,428 cycles**. The native frame budget is 280,896 cycles at approximately 59.7275 Hz. These are representative authored emulator windows, not physical-hardware or every-possible-crowd certification.

## Spoiler-free player capture

The exact-N5 northern harbor teaser passes 110 separate capture checks: **1,200 native frames / updates / page flips**, **20.091 seconds**, no cuts, resets, machine-state loads or saved-progress changes. It shows ordinary walking with base Homura and one harmless initial Fire cast. Original emulator PSG is retained, with zero native audio/video duration drift. The MP4 uses 4× nearest-neighbor enlargement with one encoded frame per hardware frame. [Media hashes and measurements](northern/player-teaser.json) are separate from gameplay acceptance totals.

## Fresh whole-game aggregate

A clean N5 checkout completed **`make test test-tools` with exit code 0**. The exact per-suite report hashes and outcomes are in [aggregate.json](northern/aggregate.json): **44,707 checks across 21 native-controller suites**, plus a separate **20-check mixed review suite** that deliberately corrupts a copied SRAM file. These are fresh rerun results, not older-ROM successes carried forward.

Both minimal and optional campaign cadence suites pass strict cold and steady checks, each with 60 scenes and 28 transitions. Host save/core/equipment/art contracts, Northern host tests and native bridge smoke tests also completed. The structured host evidence separately records 39 advanced-source checks, 78 Northern order/capacity cases and 15 provenance checks. The synthetic quick-party run contains three deliberate RAM writes and six added synthetic checks; its 573 repeated normal checks are not added again to the controller total.

This fresh modal setup has 161 checks because it does not run the archived before/after comparison. The earlier exact-N5 acceptance has 162 and retains that independent comparison. The 24,180-check Northern archive, 25 modal scene comparisons and 110 player-capture checks stay separately labeled; do not add overlapping runs as unique coverage.

An initial aggregate attempt caught an obsolete advanced-power host test shim. Its missing dispatch symbols were corrected and the fresh full aggregate was restarted; the cartridge/runtime/art did not change. The successful final log SHA-256 is `821f5eb5e8cb955f329eb10902dd5e5a445b059bd796a8a810245c2ade1ab6bf`. Recorded report/harness hashes identify what executed; later capture/documentation changes are not substituted for test evidence.

## Evidence and reproduction

See [detailed Northern verification](NORTHERN_VERIFICATION.md), [bounded summary](northern/summary.json), [exact report hashes and counts](northern/suites.json), [native timing](northern/timing.json), [save revision-3 verification](NORTHERN_SAVE3_VERIFICATION.json), and [the QA commands](../tests/NORTHERN_QA.md).

Run `make`, `./tools/build_mgba_bridge.sh`, then `make test test-tools` for a new whole-game run. `make test-northern` runs the focused Northern suites. Reports are generated under ignored `build/`; do not mix different cartridges' machine states. `python3 tools/package_northern_evidence.py` validates and summarizes the exact archived N5 reports. It keeps each public JSON below 32,000 bytes and omits raw traces, SRAM, machine states and local filesystem paths.

## Limits and historical releases

The full 128-form roster, legendary progression and southern-island, magma-mountain and underwater regions remain unfinished. No final campaign-length claim is made. Physical GBA/flash cartridges, other emulator/compiler releases, the macOS bridge path and hosted CI remain unverified. Cold Continue decoding remains a blocking load transition. Whole-program stack high-water is not measured.

[Reedhaven verification](VERIFICATION-REEDHAVEN.md) is preserved unchanged for the prior ROM. [Quick-party verification](VERIFICATION-QUICKPARTY.md) and [full-screen verification](VERIFICATION-FULLSCREEN.md) are also historical. Their successes are not counted as fresh N5 evidence.
