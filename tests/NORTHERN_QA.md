# Northern native acceptance

Developer evidence only. These reports and screenshots reveal chapter progression and must not be used as player-facing guides or teaser images.

## Safety and provenance

- `northern_journey.py` requires explicit frozen ROM and symbol SHA256 values and refuses the prior R5 ROM as a Northern candidate
- All gameplay changes use real controller input. Symbols, OAM, palette, VRAM and SRAM are read-only observations. No player positions, health, flags, instances or command state are injected
- Source R5 SRAM is authenticated against `74f39c496a1e93eb47c5b50828513033899be0567a1391cf99869750defa9106`. It contains six genuine family instances and eleven historical forms, with no Northern content
- Prior-cartridge machine states are never imported. Every current-cartridge branch checks the ROM, symbol, machine-state and paired SRAM hashes before loading
- Test sources are copied and hashed at run initialization. Collision navigation reads the tested ROM's actual room descriptors, rather than assuming the mutable checkout still matches the candidate
- Native screenshots are 240×160. Performance counts actual emulated hardware frames, game update increments and displayed page flips, never host wall-clock FPS
- `northern_host_cases.py` is explicitly synthetic host-only evidence. Capacity faults and exhaustive objective order tests do not establish native obtainability

## Suites

For a quick performance regression across candidates, `northern_stress.py --forward-sram` can import only the authenticated source report’s earned SRAM into a fresh target boot. It creates new target-ROM machine states and makes no new acquisition claim.

Supply `--rom ROM --symbols SYMBOLS --expected-rom-sha SHA --expected-symbols-sha SHA --output DIRECTORY` to each native suite.

1. `python3 tests/northern_journey.py ...`
   - Exact revision2→3 migration, all eight areas, guaranteed base-command main route with manual weights and no Earth selection
   - Wrong powers, wrong manual rail, reset, leaving and reentry, completed-stage preservation
   - Actual sword/lance/bow machine collisions, all eleven Northern quests, five recruits, five declined/confirmed evolutions and six item sidegrades
   - Twenty-one historical forms with eleven retained instances in one real save, independent reboot, repeat reward idempotence, old-region return and ordinary enemy death/retry
2. `python3 tests/northern_sky_route.py ...`
   - Hash-authenticated prior Sky-clear SRAM, normal Kohaku ownership retained
   - No Core-clear, ending, optional Reedhaven quest, Earth selection or evolved command required for the entire Northern main route
3. `python3 tests/northern_stress.py ... --journey-report SUCCESSFUL_SAME_ROM_REPORT`
   - All four viewport source alignments, exact full-frame source indices and native RGB outside actual nonzero OAM pixels, corner HUD
   - Normalized cardinal/diagonal controller travel
   - Active scrolling, cold seven-tab journal traversal, ordinary rest/save/dialogue cadence, plus cold journal rendering over actual field enemies
   - Combined camera motion, typed enemies, hostile shots, two arrows and a new effect; representative native screenshots and full frame traces
   - `--scope pixels`, `field`, `save` or `field-journal` can isolate a diagnostic branch
4. `python3 tests/northern_boss_controls.py ... --journey-report SUCCESSFUL_SAME_ROM_REPORT`
   - Actual telegraph/sweep/exposure/recovery stage durations and paused-journal freeze
   - Active handle A priority, reachable manual reset, leave/reentry and genuine sweep death/retry
5. `python3 tests/northern_modal_pixels.py ... --source-report AUTHENTICATED_REPORT`
   - Independently boots the report’s pre-evolution SRAM on each candidate, never a prior machine state
   - Captures paused tabs, confirmation, active evolution, natural death and first presented resume frames
   - Verifies current-form companion tile cache on resume; `--compare PRIOR_MODAL_SCENES.json` checks native RGB and all visible OAM entries exactly
6. `python3 tests/northern_host_cases.py --output REPORT.json`
   - All objective permutations, enforced sequential dungeon stages, roster/equipment capacity failure atomicity and retry

## Release reading

A passing journey establishes acquisition and persistence. It does not supersede a failing performance or control report. Header-enabled rows and authored images are not acquisition evidence. Every release claim must cite the final frozen candidate's report; success on an earlier ROM cannot be carried forward without rerunning.
