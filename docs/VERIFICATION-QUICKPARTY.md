# Quick companion picker — verification

Verified 2026-10-05 on the full-screen/evolution release foundation. Technical evidence can contain progression spoilers; the player demo and opening screenshots do not.

- ROM: **1,837,636 bytes**
- SHA-256: `1e76b1d5f3a65557b47f7445710d448b0a316fdd9e810a2d1dcc49ea4f7a45aa`
- GNU ARM GCC 14.2.1, valid native GBA header, warning-free full rebuild
- Full rebuild is byte-identical; UI regeneration changes zero bytes across 67 generated files
- IWRAM code: **26,968 bytes**, below the 28-KiB cap and preserving the stack reserve
- Initialized data plus BSS: **45,020 bytes**, below 256 KiB
- Real village departures into all three routes start a new expedition; checkpoint reload retains its existing credit ledger. Malformed-save tests now retain valid full-bank CRC32 before checking semantic rejection.
- Failed assignment saves retain a visible modal warning through long waits and page changes. Explicit return to play acknowledges it without marking the write successful; a later successful retry clears the failure.
- Save5 content revision remains **1**; legacy migration and serialized party layout are unchanged

## Preserved behavior

**11,657 native-emulator assertions pass with zero failures.** The complete `make test` aggregate passes: original first-chapter/review/exploration checks; exhaustive minimal and optional campaign routes; their strict cold/steady frame-cadence checks; full-screen source pixels and OAM; fresh six/eight-heart and authentic format4-migrated evolution routes; advanced powers; host save4/save5/creature/trial suites; asynchronous save-failure feedback; and the quick-party controller suite. `make test-tools` also passes.

No original behavioral assertion was removed. The advanced-effect recall/switch case was intentionally adapted from immediate L-press selection to preview/release selection. It now verifies that both picker updates freeze the complete effect state and that subsequent effect duration excludes those two paused updates. The host save-feedback build now links the new module.

Eight forms remain implemented, obtainable and verified. These are four actual owned story instances after evolution, with eight historical obtained-form bits. Party assignment never manufactures an unevolved copy from the historical collection.

## Picker and journal coverage

Controller-only native checks cover simultaneous L+direction, latest direction, all diagonals and opposite pairs, held/repeated inputs, B cancellation, invalid/empty slots, 12-update taps versus 13-update/long inspection, summoned and uncalled companions, duplicate OBJ prevention, and frozen movement/enemies/projectiles/cooldowns/effect timers. A release consumes its own action update. Native Start interruption and subsequent L-release cleanup are covered.

Journal checks assign, swap, reorder and empty slots, reject removal of the last assigned member, verify that only occupied roster records appear, retain every story instance, and reload assignments from unchanged save5 revision1. Fifteen SRAM samples from a controller-started assignment transaction independently reboot to either the prior complete party or the new complete party. No partial assignment is accepted.

The supplemental journey uses the exact-ROM controller-earned evolution snapshots. It moves a pending companion to another quick slot before declining and accepting its evolution, reverses all four evolved assignments, verifies that growth-command edits target the intended owned instance, reloads, and checks all four advanced effects across picker freeze/replacement.

Synthetic forced pause/dialogue/death interruption tests are separately labeled. They are fault tests, not normal controller progression, and their RAM writes are never counted as gameplay evidence. Host persistence corruption/fault tests retain the same separation.

## Native cadence and remaining limits

Timing uses emulated GBA updates, displayed bitmap-page flips and hardware cycle counters: 16,777,216Hz / 280,896 cycles, approximately 59.7275Hz. Host emulator throughput is not used as a frame-rate claim. Cold open, directional redraw, cancel and release are measured, including immediate movement-to-L at all four grove camera-word alignments. The evolved stress maximum is **208,555 cycles**, about 74.25% of budget, with every hardware update and presentation retained. Outside-panel source pixels verify stale-page recovery. Measurements also include held-picker frames and incremental assignment saves. Detailed per-scene measurements and exact assertion counts are in [the candidate summary](quickparty/summary.json).

The normal 240×160 viewport and corner HUD remain unchanged. The selector covers part of the world only while L is held. Native source-pixel/full-screen tests still pass after dismissal. World art and collision tables are unchanged.

Cold Continue still performs a blocking checkpoint decode; that documented load transition is separate from smooth gameplay and incremental-save cadence. Measurements are representative, not physical-hardware certification. Physical GBA/flash cartridges, other emulator/compiler releases, macOS bridge builds and hosted CI remain unverified.

## Reproduce

```sh
make
./tools/build_mgba_bridge.sh
make test
make test-tools
python3 tests/quickparty_tests.py --rom build/emberbond.gba --symbols build/emberbond.sym --journey build/evolution-qa/evolution-report.json --output build/quickparty-evolved-qa
python3 tests/quickparty_tests.py --rom build/emberbond.gba --symbols build/emberbond.sym --synthetic-interruptions --output build/quickparty-synthetic-qa
make quickparty-video
```

The player input demo is **15.17 seconds**, opening village only, captured from native frames and native PSG audio. Its separate caption margin shows the actual inputs; the underlying 240×160 game image is unaltered. It includes no evolved forms, secret locations, bosses or endings.

[Prior full-screen/evolution verification](VERIFICATION-FULLSCREEN.md) includes the merged-main review corrections on `63a1161f…`; `docs/systems/review-fixes.json` retains their exact evidence. The other `docs/systems/` files describe the earlier `d19e9b93…` build. Older campaign/milestone/performance evidence describes still earlier versions. These are historical records, not substituted evidence for this candidate.
