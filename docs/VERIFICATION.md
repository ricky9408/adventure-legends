# Three-lantern campaign foundation — verification

## Save-feedback follow-up — 2026-10-05

The current source includes a focused fix after frozen campaign commit `5de9e978fd9c01ae8a2c24e3797d5f131ebc7749`: failed checkpoint writes now keep their failure notification instead of being overwritten by a success toast on resume or no-dialogue puzzle completion. The new host integration regression confirms the previous bank survives a failed relay save, the failure remains visible, and a later successful checkpoint persists that relay.

- Current ROM: **1,583,628 bytes**, SHA-256 `b2bb22b39a9da5173c02da1f8a3447a038ef52d0e6ae04f94c53630db07de4aa`
- Clean ARM rebuild, complete `make test`, bridge smoke and the focused save-feedback regression pass
- The aggregate now runs both routes exhaustively and measures their cadence separately: **7,090 gameplay assertions** (3,425 minimal, 3,481 optional, 24 first-chapter, 20 review and 140 exploration), plus 26 save-host groups
- Each route passes 60 steady scenes / 20,460 frames and 28 cold transitions / 1,680 frames with exactly one update and presentation per hardware frame
- Worst sampled current cold work: **228,540 cycles**; steady work: **119,221 cycles**

The original source ZIP and the checked-in `docs/campaign` capture/evidence remain unchanged and describe the original ROM below. They are not new captures of this follow-up ROM. Current raw reports regenerate under `build/campaign-performance-minimal` and `build/campaign-performance-optional`; the next player release will include this fix.

## Original frozen campaign verification

Verified 2026-10-05. This is a coherent story foundation within the larger requested project, not completion of evolution, equipment, regional cities or 128 monster forms.

- ROM: **1,583,620 bytes**
- SHA-256: `0ded4a979de99fa32e152ca0b541189df330f8c3ca8dcae14988d181c027f1d7`
- GNU ARM GCC 14.2.1, valid native GBA header, no `-Wall -Wextra` warnings
- Full asset regeneration changes no source bytes and rebuilds the exact tested ROM
- mGBA 0.10.5 native core with HLE BIOS; normal gameplay uses only GBA buttons and read-only state inspection

## Gameplay and persistence

**3,978 assertions pass:** 3,425 exhaustive campaign, 369 optional route, 24 preserved first-chapter, 20 independent review and 140 scrolling/exploration regressions. Another 26 host save-test groups cover serialization faults independently of the emulator.

Coverage includes all 14 areas, four companions, three bosses and the elder ending/postgame. The six-heart route uses ordinary one-damage sword strikes without the optional relic/chime or a required combat-healing wait loop. The optional route collects the permanent eight-heart relic and flower chime.

- All 6 wind-relay orders and 24 four-socket orders
- Wrong, absent and repeated powers; intended prerequisite chains; safe reentry and reload
- Closed exits, cracked arch, root gap and thorns resist straight/diagonal movement and swept dodge
- Natural deaths/retries in seven threat rooms; every Kazane state and every core phase/transition can retreat safely
- Reward/ending page interruptions, replay interruptions and postgame visits; earned companions and clear flags never duplicate or disappear
- Authentic prior-ROM formats 2/3 migrate to dual-bank format 4, preserving optional upgrades; sequence wrap, latest-record selection and corruption fallback
- Every journal tab and all unlocked companion selections render distinct, stable content
- Original camera boundaries, all four viewport alignments, ranged warnings, combo/damage and camp semantics remain tested

The camp regression found and fixed a real integration bug: resting after arriving from the north now records the camp spawn, while ordinary north-side reentry still preserves its physical entrance.

## Frame pacing

Both minimal and optional-eight-heart fixture runs pass strict cold and steady cadence:

- Per run: **60 steady scenes, 20,460 updates and 20,460 presentations in 20,460 hardware frames**
- Per run: **28 cold transitions, 1,680 updates and 1,680 presentations in 1,680 hardware frames**
- All 14 rooms, four powers, three journal tabs, all selected-companion panels, every boss phase and a genuine six-projectile enraged Kazane window are covered
- Worst sampled cold update/render: **229,908 cycles**, leaving **18.15%** of the 280,896-cycle display-frame budget
- Worst sampled steady update/render: **120,501 cycles**

These are actual emulated GBA frames at 16,777,216/280,896≈59.7275 Hz, not host FPS. Timings exclude VBlank waiting/OAM commit; independent page-flip cadence verifies final presentation. This is representative measured coverage, not an exhaustive all-frame proof or physical-hardware certification.

The initially measured cold journal could take two frames. Fixed-source panel DMA, precompiled paired-pixel text spans and a paired-pixel static sprite renderer remove that overrun. Both text alignments reconstruct exact original glyph pixels. Seven complete journal/companion screens match the pre-optimization renderer pixel-for-pixel.

## Capture and evidence

The full video is a continuous **254.74-second** controller-only run through the optional route, all bosses, ending and peaceful village, with actual emulator audio. It uses no RAM injection, save reload or savestate rewind. This scripted route duration is not an estimated human play length.

[Summary](campaign/summary.json), [minimal gameplay](campaign/gameplay-minimal.json), [optional gameplay](campaign/gameplay-optional.json), [minimal cadence](campaign/performance-minimal.json), [optional cadence](campaign/performance-optional.json), [capture](campaign/capture.json), and bounded assertion-audit files are checked in. Raw controller traces/state fixtures regenerate under ignored `build/`. Older `docs/milestone1`, `docs/perf` and polish evidence are historical tests of prior ROMs, not this release's timing report.

## Reproduce

```sh
make
./tools/build_mgba_bridge.sh
make test
make test-tools
make assets
make
make gameplay-video  # ffmpeg required
```

Save-host tests include explicit corruption/interruption fixtures; those are distinguished from ordinary controller-only progression. Test save states are paired with their authentic SRAM to prevent accidental cross-branch progress.

## Limits

Physical GBA hardware, flash cartridges, other emulator/compiler releases and the macOS native bridge path remain untested. There is no hosted CI configured. Current puzzles are largely persistent companion mechanisms; movable-object/clue quests, richer regional interactivity and hidden discoveries are upcoming work. Current roster: 4 implemented/obtainable companion forms; evolution and equipment inventory are not yet implemented.
