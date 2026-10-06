# Candidate D final full legacy acceptance

PASS for the assigned final legacy scope. `make test test-tools` exited0 after1,733.820s, with82 Python invocations. Additional strict+ASan/UBSan gear-heart tests passed. This is exact candidate D acceptance for the legacy scope; Magma-specific native acquisition/combat/save-performance acceptance is owned separately.

## Exact target and reproducibility
- ROM SHA-256: 90ba47f30a0c94c28f073d26cc31ac5f5c736eb4d6e704d090892d2776f1ffb2 (7,495,920 bytes)
- Symbols SHA-256: add52be1a5d23d2e8df8fd616f4ef1c7fde8d3e1906e1d789925d68476cf50f6
- Independently rebuilt ELF SHA-256: 0b56a0a525ef59d36b14a89a2786e5811f29fd9a54c386093fa06528f3afcc99
- Runtime manifest SHA-256: a72fd93eddb0a39322b22e45caf0f4ac49496d962776ee616dfd83642342ef3f
- Initial archive SHA-256: 206e8522744774d9fa45539fe8dc697bf04a127ebec841abdfbd222dd55df576
- Clean official-toolchain rebuild: no warnings; exact ROM, symbols and runtime manifest reproduced. Original/rebuilt ELF differs only in debug paths; stripped-debug bytes identical
- All893 runtime inputs verified after completion; all initial production/asset/tool inputs and203 historical fixture files remain unchanged

## D source reconciliation
Only game.c, magma_game.c and magma_game.h differ from accepted legacy candidate C, implementing deferred Magma anchor preparation on warmed SAVING pages. Save5 codec, creature/catalog/art runtime files and all203 historical fixtures remain unchanged. Full D legacy aggregate was rerun rather than inheriting C results. See candidate-c-to-d-runtime.patch and candidate-c-to-d-reconciliation.json.

## Coverage
- First-chapter playthrough, review, exploration and prior-save migration
- Save4/Save5/Southern persistence, corruptions, byte cuts, retries, capacity, sanitizer and source-admission contracts
- Creature/current65 and immutable historical1–4 policies; personal trials; actual host UI/save failure integration
- Equipment, weapon actions, exact number/heart pixels, gear runtime, all phase matchups, regional adapters/art/game
- Native new-game replacement confirmation, quickparty migration, expedition, full-screen/OAM, three evolution routes, advanced powers and source contracts
- Normal, evolved and separately labeled synthetic quickparty tests
- Mandatory and optional full original campaigns plus both strict-cold hardware performance suites
- Full River journey, collection, combat and equipment behavior
- Full Northern host/journey/alternate route/source-provenance denials/stress/boss/modal/combat suites
- All nine Southern controller suites: minimal1889; full journey15732; targeting188; optics4708; controls448; selector42; combat8176; hardware performance1484; render343. These are overlapping assertion counts, not unique gameplay events
- Full Southern route earns41 histories in21 retained real individuals and independently reboots; it does not assert Magma acquisition
- Bridge smoke tool and additional gear-heart strict+ASan/UBSan tests

## Resolved blockers retained as evidence
- A's stale current-catalog expectations and colliding South/Magma locals were repaired only in tests; historical digests, source/SRAM pins and earned Southern41 scenario counts are unchanged
- South locals are resolved through the exact ROM-paired ELF, STT_FILE owner south_game.c, with type/width/address and load-image checks. No last-nm-entry choice
- Host adapter/source-contract linkage now includes real new dependencies, preserving all old assertions
- Northern delayed-span fixture measures exclusion after facing; the full D Northern aggregate verifies34px initial distance, first hit at age28, one24Q4 hit. Its strict damage/geometry assertions were strengthened
- B's returning-fan/fire-annulus pacing regressions reproduce in independent native runs. C and D restore180/180 update/page-flip windows without relaxing assertions or changing old effect algorithms

## Hardware pacing
Final full Southern suite has zero failures and one update/displayed-page flip per measured hardware frame. Crowded command42 peak259,451 render cycles, command30 peak251,667. Worst cold window273,845 render cycles. Render timing excludes final VBlank/OAM work; actual hardware-frame/page-flip assertions also pass. These are sampled gameplay/UI/save windows, not a claim that cold checkpoint decoding has no blocking transition. Headroom remains limited for future content/music changes.

## Receipts and raw evidence
- make-test-test-tools.log: full aggregate log, SHA-256 46596948fcea3810393578c27133ebf6aeb0dd959c4b5c8ff97cfa0381c295a1
- aggregate-command-result.json and executed-commands.json: exact completion, elapsed duration and executed command lines
- initial-receipt.json / candidate-d-initial-source-build.tar.gz: original files and hashes
- clean-rebuild-receipt.json / clean-build.log: reproducibility
- aggregate-test-hashes-before.json / aggregate-test-hashes-after.json: exact tests
- final-code-receipt.json: source/fixture preservation and transparent unrelated Magma-combat test change
- report-index.json:39 canonical reports with hashes and coverage markers
- legacy-artifact-hashes.json:5,011 legacy artifacts with byte sizes/hashes; raw files remain in candidate-D/build
- southern-final-cadence-summary.json: complete final hardware windows
- environment-receipt.json: compiler/Python/Pillow and bridge/toolchain library hashes

## Honest limits
No Magma-specific native acquisition/combat or full34 save-performance acceptance is claimed here; other workers own that scope. Physical GBA hardware, flash carts, alternative compilers/emulators and platforms remain untested. Native journeys use controller input and real earned SRAM; no game-RAM injection. Host synthetic/fault cases are separate. The explicitly labeled synthetic quickparty run uses three game_state writes and controller_only=false; bridge smoke writes its own trivial test ROM's memory. Neither is counted as controller gameplay. No GitHub writes, uploads or publication performed.
