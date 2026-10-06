# Underwater candidate A: targeted legacy native regression

**Not accepted. Three production cadence regressions are reproduced.**

ROM SHA-256: `0d7fd78733405a6fc8ec6eeca68ad207dfb11b91dcfe44a8d67f312552b46675`

Exact report hashes, windows, misses and ELF provenance: [bounded JSON](../evidence/underwater-legacy/candidate-a.json). Full raw controller inputs, paired native states/SRAM, screenshots and reports are retained under `build/underwater-legacy-a/`.

## Required fixes

| Native case | Hardware frames | Updates / flips | Peak recorded cycles | Missing frame indices |
| --- | ---: | ---: | ---: | --- |
| Southern command42, five visible enemies + real shots/arrows | 180 | 179 / 179 | 266,828 | 73 |
| Southern cold rest/save, summoned companion | 160 | 157 / 157 | 279,769 | 36, 81, 117 |
| Earned21 storage candidates | 120 | 115 / 115 | 276,122 | 26, 33, 35, 62, 114 |

Command42 was repeated independently from its authenticated same-ROM controller snapshot and matching SRAM. It reproduces the exact miss at index73 with the same266,828-cycle observation. No cross-ROM state was imported.

Recorded render cycles exclude the final VBlank/OAM commit. All three failures remain below280,896 recorded cycles; that is insufficient for acceptance. Tests require both one game update and one displayed page flip on **every** actual hardware frame. Host FPS is never used.

## Passed targeted coverage

- Southern complete controller producer:16,430 checks,41 historical forms,21 actual retained individuals,30 completed quests, preserved earlier identities, independent cold SRAM reboot and ordinary death/retry
- Ten Southern declined/confirmed evolutions;20 authenticated bounded prep/commit waits, no missed hardware frame; worst observed257,242 cycles
- Southern commands30/38/24/32:180 updates and flips per180-frame window; peaks258,642 /160,494 /213,817 /192,582 cycles. All five tested commands, including failing42, actually combine five visible bodies, two player arrows, hostile shots and active effect for9 frames
- Cold town/field journals:95/95 each; all eight pages reached. Unsummoned earned21 rest/save:180/180. Four-slot selector:96/96
- Southern early controls448 checks; exact tile resume, body/shadow and selected-instance render controls343 checks
- Old evolution routes: normal1709, six-heart1678 and v4-migrated1270 checks
- Advanced powers540 checks, including six240-frame live final-boss stress windows, plus unchanged production-module host contracts with new chapter reset bridges
- Quick-party643 normal and461 evolved/reordered checks; both use controller-only actual roster state and retain old power-cut/selection assertions
- PR5 revision1 migration91 checks; Northern revision2 migration; old v2/v3 valid, invalid, corruption and independent reboot cases; new-game53 checks; fullscreen96 checks

## Harness adaptation only

`RegionJourney.wait_evolution` now authenticates the exact ROM/ELF image and the unique `progression.c:evolution_job` local object through ELF STT_FILE ownership. It checks the72-byte object ABI and phase at offset8, waits with neutral controller input for idle phase plus prepared confirmation, then requires a fresh A and actual animation. Decline tests remain unchanged. It also measures hardware updates/page flips throughout observed preparation and commit.

The Regional/Northern/Southern/Magma evolution helpers, old four-family evolution route and reordered quick-party evolution use this observer. Current producer content revision expectations move to6; historical source revision1–5 fixtures and archive pins remain unchanged. The advanced-power host shim links the real Underwater power module and preserves its old source-contract checks, adding an explicit death reset/evolution-cancel observation. Runtime, core, save and art files were not edited by this reviewer.

Early harness-development attempts and their logs are not acceptance evidence. No original historical fixture or published evidence archive was modified. The parent must repeat affected native gates on the next frozen candidate and run the final aggregate after integration stabilizes. This report does not accept all89 forms/50 individuals or complete Underwater content.
