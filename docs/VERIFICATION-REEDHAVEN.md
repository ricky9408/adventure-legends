# Reedhaven equipment and elemental companions — verification

Verified 2026-10-05 on merged PR5 (`b54f8fa8e91a7097d989b9c22f5edf0c15493938`). Developer evidence can reveal progression; the player teaser and town preview do not reveal puzzles, recruits or endings.

## Exact native build

- ROM: **3,085,056 bytes**, SHA-256 `0ba77d82ce15619784c35a67be83950f924265b604a47495a8987afb21963e90`
- Symbols SHA-256: `2e44714072837c06db32f7b019afbdd0555f82904166da6d980bf8394ccfb2ac`
- GNU ARM GCC 14.2.1; valid GBA header; warning-free build
- IWRAM code: **27,664 bytes**, below the 28-KiB code cap; the top 4 KiB remains reserved for stack
- Initialized data plus BSS: **47,320 bytes**, below 256 KiB EWRAM
- Authored OBJ allocation ends at byte **16,256** of its 16,384-byte bitmap-mode allocation
- Full asset regeneration and rebuild reproduce the same ROM. Generated source chunks remain below 32 KB.
- Save5 content revision **2**; explicit forward readers retain v2/v3/v4 and revision-1 progress. Backup the `.sav` before upgrading; old ROMs do not synchronize newer progress backward.

## Playable content and native acceptance

This milestone has 22 areas in total, including six new regional areas, 11 regional quests, 13 earnable equipment pieces across five slots, three player weapon classes, six owned companion families and 11 obtainable forms. The single-file collection journey obtained all 11 historical forms, retained six real owned instances, saved all 11 regional quests, and rebooted successfully. No historical form was cloned into an extra companion.

The region journey passes **5,684 native checks**. It uses controller input from a hash-pinned prior-ROM story save, with no gameplay RAM writes. It covers real entrances and exits, clue/companion/crate activities, repeat rewards, puzzle resets and reentry, equipment training, regional recruitment, deliberate evolution decline/confirmation, retained Water commands, a taught shortcut, death/retry and independent save reload.

The native combat/collection suite passes **2,761 checks** across 18 functional cases and one measured combat window. It verifies all five controlling phase relationships through real companion hits, fractional health and armor, no equip/heal exploit, sword equipment differences, attack hit ledgers, live-projectile gear locks, and short/held bow cancellation by pause, picker and roll. Its additional collection case obtains and reloads all 11 enabled forms in one file.

Across the shipped controller/native suites, **20,547 assertions pass with zero failures**. The complete aggregate also preserves the first chapter, scrolling exploration, both minimal/optional story routes, full-screen pixel/OAM checks, all prior evolutions and personal trials, quick-party assignment and interrupted saves. Exact counts, candidate hashes and bounded assertion records are in [the release summary](reedhaven/summary.json). Host sanitizers, malformed-save probes and synthetic interruption tests are kept separate from normal native-controller assertions.

The exact merged PR5 reordered/evolved-party save also passes **91 controller-only migration checks**: all roster bytes, instance IDs, assignments, selected member, learned commands and credit ledgers survive Continue, a real checkpoint and independent reboot. Only starter equipment is added; regional quests remain unearned. No prior-ROM machine state is imported.

## Important fixes caught before release

- Arrow proximity and Metal-pin hits now require an unobstructed path; nearby targets cannot be hit through a wall just before projectile collision.
- Sword art and hit direction use the same captured facing. Gear changes cannot alter an active attack, projectile or cooldown.
- Stagger is a separate timer rather than longer damage immunity, so stagger gear does not accidentally break the sword combo.
- Armor uses fractional health consistently. Changing or browsing equipment never fills health; reducing capacity only clamps excess health.
- Regional return restores the original world sprite atlas, and death retries use the actual regional checkpoint spawn.
- Cached partial-heart glyphs removed a scrolling update hitch. Cached health capacity and conditional sprite setup removed a cold legacy transition hitch.
- A short bow tap waiting to fire can now be canceled by rolling, matching held-draw cancellation.
- Quest rewards, traversal-critical recruits and equipment are validated together; malformed but CRC-valid banks fail safely without losing the prior committed bank.

## Frame cadence

Measurements use actual emulated GBA hardware frames, game-update counters and bitmap-page flips. The hardware ratio is 16,777,216 / 280,896, approximately **59.7275 Hz**. Emulator host throughput is not a frame-rate measurement.

- Town: 180/180 updates and flips, maximum measured update/render cost **94,101 cycles**
- Basin: 180/180 updates and flips, maximum **136,860 cycles**
- Fractional-health/two-arrow combat: 200/200 updates and flips, maximum **118,095 cycles**; two arrows are simultaneously active for 16 frames
- Four 360-frame scrolling windows preserve one update and presentation per frame, including the formerly expensive fractional-heart case
- The explicit PR5 migration/checkpoint test preserves all 63 incremental-save updates/flips; its highest measured save update is **249,821 cycles**, about 88.9% of the frame budget
- Both inherited campaign cadence suites pass strict cold and steady checks; picker/modal/incremental-save checks remain part of the aggregate

The combat window has five live enemies but only two visible at once and no hostile shots. It is a representative mixed-workload measurement, not a claim that every possible maximal crowd has been measured. The cycle timer observes update/render before VBlank wait and OAM commit; update/page-flip checks separately catch missed display frames.

Cold Continue still performs a blocking checkpoint decode before normal gameplay. Tests explicitly distinguish this load from active play and incremental saves rather than silently excusing dropped gameplay frames.

## Persistence and core checks

The host suites include atomic multi-item rewards, full-inventory rejection, reference validity, no-heal equipment changes, bounded weapon timing and wall-first projectile collision. They run strict compiler checks and ASan/UBSan where applicable. Save tests cover revision-1 migration, valid-CRC semantic corruption, retained regional recruits, every interrupted write position and repeated full-roster transactions. The isolated ARM save benchmark is distinct from whole-frame evidence.

Runtime health is measured in sixteenths of a heart. Legacy whole-heart symbols remain read-only observation caches, not a second health authority. Save files contain explicit fields and owned references, never runtime struct padding or derived combat stats.

## Reproduce

```sh
make
./tools/build_mgba_bridge.sh
make test test-tools
make gameplay-video
python3 tools/package_reedhaven_evidence.py
python3 tools/package_source.py
```

The default player teaser is **18.517 seconds / 1,106 native frames**, including all 23 visible save frames. It uses actual PSG audio, nearest-neighbor enlargement and no invented/interpolated frames. Preparation is controller-driven; the clip stays in the opening town with the starting companion and one lance practice hit.

## Remaining scope and limits

Eleven forms are implemented, obtainable and tested, not 128. The full roster, legendary progression and Northern-European, southern-island, magma-mountain and underwater regions remain ongoing. No commercial-game parity or campaign-length claim is made.

Physical GBA/flash cartridges, alternate emulator/compiler versions, macOS bridge builds and hosted CI remain unverified. Earlier folders under `docs/` retain their own historical ROM hashes; they are not substituted as evidence for this build. [Prior quick-party verification](VERIFICATION-QUICKPARTY.md) records the preceding release.
