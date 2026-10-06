# Northern N5: detailed developer verification

**Spoilers:** this is engineering evidence, not a player walkthrough. Native test reports and acquisition identifiers expose progression. See [the player guide](PLAY_JA.md) for spoiler-free help.

## Scope and immutable candidate

The accepted Northern candidate is **N5**, dated 2026-10-05:

- Cartridge: `build/northern-n5/emberbond.gba`, **4,351,688 bytes**
- ROM SHA-256: `302316c53d6fb9dafa0ecbf9f679c9c39af3a150af3aa78398c368312e50399e`
- Symbols SHA-256: `7110402451d7bea92ebd1d83dfddbf2f389468028e8842ef6afa22f043595018`
- Frozen source-manifest SHA-256: `0effd60dc5e3d255e54269e862033b3a3eac1829cc1245c205db4a4acc6df792`

[summary.json](northern/summary.json) records the exact target, memory allocations, content counts, native-versus-host distinction and limits. [suites.json](northern/suites.json) preserves the original full-report SHA-256, byte size, assertion count and recorded harness hashes for each native suite. The controller-acceptance source and the separately completed combat report are both included; the acceptance source by itself covered only five of those suites.

The packager checks frozen ROM/symbol bytes, full report hashes, every recorded native check/case outcome, report lineage, the final earned SRAM hash and compiled source hashes. Compiled source guards cover `src/` C/header/assembly/include files and `linker.ld`, not mutable Markdown or Makefile edits. The original broader manifest's byte hash is retained as provenance; it is not misrepresented as a current documentation lock. No public output contains the full raw traces, machine states, save bytes or machine-local paths.

## Controller acquisition and main-route acceptance

The full journey passes **9,978 checks**. It begins with authentic, prior-release R5 SRAM, SHA-256 `74f39c496a1e93eb47c5b50828513033899be0567a1391cf99869750defa9106`, preserved at `tests/fixtures/v5-revision2/all-eleven-town.sav`. That save was actually earned on the prior cartridge, has six owned families and eleven historical forms, and contains no Northern progress. It is forward-loaded by the new cartridge. No prior-ROM machine state is imported.

All gameplay acquisition uses controller input. Symbols, OAM, VRAM, palette and SRAM are observations; gameplay RAM writes are zero. Branches authenticate the current cartridge, symbols and paired state/SRAM hashes. Repeated events from alternate branches are not counted as additional companions.

The independent final reboot verifies:

- Historical forms: `1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 19, 20, 22, 23, 73, 74, 75, 76, 77, 78`
- Eleven real owned instances, retaining all six older instance identities; evolution changes each existing instance
- All 22 regional quest states CLAIMED, all 19 equipment items retained and all eight Northern areas visited
- All five new evolutions deliberately declined and then confirmed, with the base command retained
- Repeat reward idempotence, return to the previous region, ordinary enemy death/retry and independent save reload
- Final collection SRAM SHA-256: `f4e853c85445b8567263a1a875eba967e552e0dcae30958ca42f39bfec4e4479`

The separate **4,668-check Sky-clear route** cold-loads a real older Sky-clear save. It proves the Northern main route does not require the Core-clear/ending, optional Reedhaven quests, an evolved command or Earth selection. Existing Kohaku ownership is retained rather than deleted to fabricate this route. The main path selects the base Wood and Metal recruits and uses reachable manual weights. Wrong powers, wrong manual rail, reset, leave/reentry and preservation of completed stages are exercised. Acquisition detail is in [acquisition.json](northern/acquisition.json).

## Combat, gear and controls

The separately pinned combat suite passes **8,837 checks across 85 functional cases** from a cold SRAM-only import of the same N5 controller-earned collection. The producer report, original R5 ancestry, ROM/symbol hashes, source harness, completion records, recruit events, CRC-valid SRAM metadata and final snapshot are authenticated before import.

Coverage includes all ten new commands, unobstructed/blocked endpoints, two-leg Water corner visibility, wrong positions and Metal facing, retained hit ledgers through pause/picker/switch/recall and hitstop, persistent late enemy crossing, moving after casting, room reset, shared OBJ effect-tile lease in both directions, reflected-shot locks and natural slot reuse. All five controlling phase relationships are hit-tested on native Northern targets, including reflected Metal against Wood.

All six sidegrades are checked, including movement/roll/reach, bow range, three real weapon damage comparisons, fractional-health preview, no equipment-heal behavior and cooldown capture that cannot be evaded by later gear changes. Short and held bow draws cancel correctly through picker, journal and roll. Live effects and reflected shots keep gear changes locked until their action has ended. [combat.json](northern/combat.json) retains bounded case outcomes and measured scalar values without raw simulation snapshots.

The dedicated boss-control suite adds **221 checks** for actual stage timing, paused-journal freeze, active-handle A priority, reachable manual reset, leave/reentry and genuine sweep death/retry. All three player weapon classes are tested at the exposed machine through actual collisions. The observed stage timers are telegraph 60, sweep 24, exposure 90 and recovery 30 active updates. Movement/control summaries are in [controls.json](northern/controls.json).

## Native pixels, modal transitions and timing

The stress suite passes **314 checks**, including all four viewport source alignments. Each alignment compares all 38,400 source pixels and 160 rows with zero index mismatches. Native RGB is compared outside actual nonzero OAM pixels, with zero background mismatches; sprites are not erased from the capture to force equality. Cardinal and diagonal controller travel is measured in fixed-point world positions.

Modal setup/resume contributes **162 native checks**. An independent before/after boot comparison covers **25 scenes**: seven journal tabs, confirmation, declined evolution, active evolution, natural death, retry and the first presented resume frames. All native RGB and visible OAM entries are identical to the pre-optimization candidate. Both candidates boot authenticated SRAM independently; foreign machine states are never loaded. The evolved current-form sprite cache is checked after resuming. [pixels-and-modal.json](northern/pixels-and-modal.json) includes scene pixel hashes, bounded OAM digests and resume observations.

The hardware clock ratio is **16,777,216 / 280,896 = approximately 59.7275 Hz**. Host execution speed is not game FPS. The timer measures update/render before the final VBlank wait and OAM commit; independent per-hardware-frame update and page-flip observations catch missed presentations.

| Exact-N5 native window | Updates / flips / frames | Peak cycles |
| --- | --- | ---: |
| Active scrolling | 240 / 240 / 240 | 126,413 |
| Mixed camera, three visible enemies, hostile shots, two arrows and new effect | 600 / 600 / 600 | 194,941 |
| Combat with three visible enemy bodies | 420 / 420 / 420 | 174,705 |
| Gathered combat with five visible enemy bodies | 420 / 420 / 420 | 208,128 |
| Cold seven-tab journal, combat suite | 80 / 80 / 80 | 266,153 |
| Cold journal over field enemies, stress suite | 80 / 80 / 80 | 266,428 |
| Cold rest/autosave/dialogue, stress suite | 140 / 140 / 140 | 207,552 |
| Cold rest/save, combat suite | 150 / 150 / 150 | 207,575 |

The stronger gathered combat scene has **five visible enemies, two visible hostile shots, two player arrows and an active Wood span simultaneously for 12 frames**, with camera movement in the window. It is not merely a five-enemy pool with only two sprites on screen. All 420 frames update and present exactly once, and the peak is about 74.1% of the native frame budget. The cold journal maximum is about 94.8%. Full bounded window metrics are in [timing.json](northern/timing.json).

These representative authored scenes do not certify every theoretical maximum enemy/projectile/effect combination. Cold Continue checkpoint decoding remains a separate blocking load transition. No physical-hardware timing or total stack-high-water claim is made.

## Save integrity and synthetic evidence

Save5 writes content revision **3**. Revision 1 and revision 2 retain their exact form/item/quest whitelists; a CRC-valid older bank containing future content is rejected. Revision 2→3 retains existing campaign, roster, party, command, instance identity and reward state, and grants no new progress. Explicit readers also retain older format-2/3/4 compatibility. Back up saves before upgrading; older ROMs do not understand new content.

The **78 synthetic host cases** exercise objective permutations, sequential dungeon stages, full roster/equipment capacity, atomic rejection and retry. The reproducible producer-validation harness passes **15 checks: one valid current producer accepted and 14 malformed producers rejected**. The rejection cases mutate source JSON only, never gameplay SRAM or native state, and run no emulator. They reject foreign ROMs/symbols, RAM-writing/non-controller/failed producers, unverified ancestry, wrong harness/content, incomplete lifecycle/recruitment, wrong SRAM hashes, false ownership and wrong snapshot targets. They are excluded from native-controller check totals. See [synthetic-host.json](northern/synthetic-host.json).

[NORTHERN_SAVE3_VERIFICATION.json](NORTHERN_SAVE3_VERIFICATION.json) separately records the host save-codec tests, sanitizer runs, exact prior fixture, 6,146 cut/success positions per listed transaction, semantic corruption coverage and isolated ARM save-step measurements. Those subsystem ROMs have their own hashes and are not N5 whole-frame results. [SAVE5.md](SAVE5.md) defines the wire format and compatibility rules.

## Player-facing capture

The public teaser was recorded from this exact ROM after a controller-driven arrival at the northern harbor. It shows ordinary walking, base Homura and one harmless initial Fire cast, with no recruits, evolution, hidden routes, puzzle solutions, boss or ending. All 110 capture checks pass separately from the six gameplay suites.

The continuous recording contains **1,200 actual hardware frames, updates and page flips**, lasts **20.09124755859375 seconds**, and has no cuts, capture reloads, resets or machine-state loads. Start/end SRAM bytes have the same hash. The native lossless video decodes to the exact captured RGB stream; the MP4 enlarges 240×160 to 960×640 with nearest-neighbor scaling and no invented/interpolated frames. The emulator's real PSG stereo audio contains 658,350 samples per channel at 32,768 Hz, with **zero native audio/video duration drift**; the MP4 resamples audio to 48 kHz AAC. Its strongest observed update/render is 136,058 cycles.

[The bounded capture summary](northern/player-teaser.json) retains exact video/audio/preview hashes. MP4 SHA-256: `12fbcad81b61d9dfc1f7d09fe59aaa023e22a280cc520f4361623bd05b081ad0`. The native harbor preview is 240×160; diagnostic screenshots from other suites remain developer spoilers.

## Fresh whole-game regression

The clean exact-N5 aggregate `make test test-tools` completed with exit code 0. [aggregate.json](northern/aggregate.json) preserves bounded per-report hashes, byte sizes and outcomes. It records **44,707 checks in 21 native-controller suites** and a separately classified **20-check review suite** whose copied-save corruption case is deliberately synthetic. Both strict campaign cadence routes pass, each covering 60 scenes and 28 transitions. All host targets and native bridge smoke tests completed in the pinned final log.

The fresh Northern subset includes 161 modal setup checks rather than the archived 162, because this invocation has no before/after comparison argument. Its other core Northern counts agree with the frozen acceptance. The earlier 25-scene comparison remains its own evidence. Synthetic quick-party interruption writes and repeated normal checks, the 39 advanced-source host checks, 78 order/capacity cases and 15 provenance checks remain outside the normal native-controller total. Neither overlapping reruns nor copied intermediate campaign manifests are added as unique coverage.

An obsolete host shim failed during the initial aggregate attempt; it was corrected and the complete aggregate restarted with no runtime/art edits. Final successful log SHA-256: `821f5eb5e8cb955f329eb10902dd5e5a445b059bd796a8a810245c2ade1ab6bf`. The raw log stays out of the source package. Executed harnesses are identified by the original reports' recorded hashes, not by assuming every subsequently edited tool was part of that invocation.

The clean rebuild reproduces the exact cartridge and symbols. Independent `make assets` regeneration preserves all 859 existing source/art files; only four documented excluded River overview images are recreated. The regeneration report hash and those filenames are retained in the aggregate summary.

## Reproduction and completion limits

`make test test-tools` is the full current regression entry point; `make test-northern` runs the Northern subset. Individual commands and provenance requirements are in [tests/NORTHERN_QA.md](../tests/NORTHERN_QA.md). Full raw reports remain generated under ignored `build/`. The archive-specific `python3 tools/package_northern_evidence.py` produces deterministic, hash-checked summaries, each below 32,000 bytes, and fails if a frozen candidate or source report differs. It does not rerun gameplay or turn a partial test run into an aggregate pass. By default it preserves the hash-pinned public aggregate summary. To independently rebuild that summary from the completed raw evidence, pass `--aggregate-build QA_BUILD_DIRECTORY --art-regeneration-report ART_REGENERATION_REPORT.json`; the exact successful aggregate log and regeneration report hashes must match.

There are **21 obtainable forms**, not 128, and **11 retained family instances**, not 21 simultaneous independent companions. The authored legendary is disabled. Additional southern-island, magma-mountain and underwater regions, the full roster and final campaign scope remain unfinished. See [VERIFICATION.md](VERIFICATION.md) for the completed whole-game aggregate summary and [the chapter design](NORTHERN_CHAPTER_DESIGN.md) for design detail, which is not itself proof of implemented behavior.
