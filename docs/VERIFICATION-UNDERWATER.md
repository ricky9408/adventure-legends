# Underwater milestone verification: build K

Developer-facing evidence index; progression spoilers may appear in linked reports.

**Status: tested Underwater runtime milestone.** Full controller acquisition,
minimal-save lifecycle, independent combat/control/stress, real-module host
integration, qualified stack observations, visual/media review, the fresh native
recipe and retained whole-game regression targets pass on K within the scopes
below. Final source-package identity and clean-export results belong in the
separately accompanying sealed export receipt, not a self-referential hash inside
the archive. This is not completion of the whole project or physical-hardware QA.
Underwater repository publication is paused; no PR, push, merge or hosted CI result
is claimed.

## Exact runtime pairing

- ROM: 9,777,176 bytes, SHA-256
  `df3733446cda3d41c2e78da134b25cd446846d6283e4ac5dc47b3fcaa3f98607`
- ELF SHA-256:
  `1fc2082a8cdc7cb56ca8e8ded59a7a322a4beacbb0adebad47d5169e9ea5dbe3`
- Symbols SHA-256:
  `3839900cde0cbbfae5f3883bfda7e726f2f85ee92d736f60381e95cc3899a797`
- Runtime manifest: 1,163 inputs (`src/**` and `linker.ld`), SHA-256
  `458a276750c5f677123a5905d4214af585db5ad6787a07d5a5135f565eb03929`
- mGBA bridge SHA-256 used by the two passing routes:
  `c158ceef817ffaed570acb8ecc0c8a5f2c237767dad4a5fd388239d3f5ae47a3`

The runtime manifest is a build receipt, not a whole-source/export manifest or
clean-build proof. Documentation and test observers can change without changing
that runtime hash; each evidence producer must retain its separate source pins.
Raw reports below live under ignored `build/`; they are not silently included in a
source-only archive. Bounded public summaries are linked below; the separately
accompanying sealed export receipt records the final archive audit.

## Content accounting

The assembled authoring catalog has 90 designed forms and 128 stable identity slots.
The generated runtime enables 89 forms in 38 families; the remaining authored
legendary is disabled. Reserved rows do not count as designed or playable forms.
The Underwater delta is eight families / 24 forms (49–72), 24 commands (67–90),
16 individual-bound trial/evolution edges, eight areas (46–53), eight quests (38–45)
and six gear items. Total runtime content is 54 areas, 46 quests and 37 gear items.

“89 forms” counts historical forms including evolution. The full native route
retains 50 independently identified creatures; it does not retain 89 simultaneous
individuals. Eight repeat encounters provide the genuine additional bases needed
for the new alternate branches. No duplicate individual or fabricated history bit
is accepted as an acquisition.

## Passed candidate-K controller routes

### Full collection

- [Bounded full-route summary](evidence/underwater-native-k/full.json)
- Raw report: `build/underwater-k-full01/underwater-journey.json`
- Report SHA-256:
  `8e8c9f749f7f78aa043fd985a05c7d06c2ff6dec95effa1639f8f6520954cc6d`
- **10,940 checks, zero failures**; controller-only; zero game RAM writes
- Begins with authenticated, delivered Magma SRAM containing 34 individuals and
  65 historical forms; no cross-ROM machine state is imported
- Ends with 50 real individuals, all 89 form histories, all 46 quests and 37 gear
- Covers all 16 new personal trial/evolution paths and eight genuine repeat encounters
- Nine explicitly measured field windows each record 120 updates and 120 displayed
  page flips over 120 hardware frames; these windows are a subset of overall acceptance
- Final town SRAM SHA-256:
  `41cf371618208e0097fe6ee10393e3185b4bffb2af9dad9e5f81e2663d6673a0`

Source SRAM: `tests/fixtures/v5-revision5/magma-all65-town.sav`, SHA-256
`a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858`.
Its delivered source ROM is
`90ba47f30a0c94c28f073d26cc31ac5f5c736eb4d6e704d090892d2776f1ffb2`.

### Minimal main route

- [Bounded minimal-route summary](evidence/underwater-native-k/minimal-main.json)
- Raw report: `build/underwater-k-minimal-main/underwater-journey.json`
- Report SHA-256:
  `cc9428a0e905ad8e3f10f3a259cd5a3662e91ab0b00d6285a3bd4e303c6d46c9`
- **761 checks, zero failures**; controller-only; zero game RAM writes
- Begins with ten genuine prior-route individuals; ends with twelve, retaining all
  original ten and using the two new unevolved teaching companions
- Main completion does not require optional training, evolution or armor
- Eight measured field windows each record 120 updates and 120 page flips over
  120 hardware frames
- Final town SRAM SHA-256:
  `3f5bbccab022f86b38f4d180e8cf66b04c055791fe4804ddbebbdefb5406aeda`

Source SRAM: `tests/fixtures/v5-revision5-minimal/magma-minimal10-town.sav`, SHA-256
`f584de3b29cb77731148b31b99dc40e0c7e4ec05f1aac42e0d38dd5b44612eeb`.
It comes from the same delivered Magma ROM above. The independent lifecycle review below cold-imports SRAM into new emulator
instances, rather than loading machine states.

Both journey reports retain their `development_bringup=true` and
`player_facing=false` labels. Their passing assertions are route evidence, not a
release acceptance flag. Earlier segmented/debug routes remain diagnostic evidence
with their original failures and cannot replace either final route.

## Additional completed candidate-K reviews

### Independent combat, controls, pixels and stress

Five same-K suites pass **138/138 top-level case outcomes**, zero failures:

| Suite | Top-level cases | Passing checks | Bounded evidence |
| --- | ---: | ---: | --- |
| Precision combat/control/art | 77 | 8,383 | [Combat](evidence/underwater-native-k/combat.json) |
| Dense scenery | 24 | 1,773 | [Scenery](evidence/underwater-native-k/scenery.json) |
| Moving powers | 4 | 703 | [Dynamic](evidence/underwater-native-k/dynamic.json) |
| Critical alternate aim | 1 | 76 | [Alternate aim](evidence/underwater-native-k/critical-aim.json) |
| Natural phase timing | 32 | 385 | [Phase](evidence/underwater-native-k/phase.json) |

The main suite accepts all 24 commands both equipped/cast and doing measured actual
enemy damage; cooldown/no-double-hit, alternates/diagonals, facing, safe apertures,
wall clipping, field-target overlap, selector freezing and all 50 stored identities
are covered. Its dedicated form sweep records 96 actual creature body/pose-state pixel
comparisons across 24 forms. Its top-level case count is distinct from nested placement/pixel records.

These suites use actual controller movement and read-only observations. Fine combat
probes use a planner to reach exact test positions and facings with ordinary D-pad
inputs; this validates authored collision/control contracts, not easy or forgiving
player aim. The separate full journey uses ordinary route navigation and establishes
acquisition/play progression. Neither predicted positions nor synthetic host fixtures
count as native movement or damage evidence. Consumers load only exact-K,
hash-paired machine state and SRAM from the successful full producer.

All 164 sampled windows across these five suites preserve one update and one page
flip per hardware frame (8,935 frames). Peak update/render cost is **270,733 cycles**
in the phase suite, below 280,896 cycles per frame. The cycle timer excludes final
VBlank waiting/OAM commit, so actual update/page-flip traces remain required. This
is sampled emulator cadence, not an exhaustive workload or physical-hardware claim.
The [independent combat acceptance index](evidence/underwater-native-combat/acceptance-k.json)
adds 240 storage frames to these windows for **9,175 total hardware-frame
observations**, all passing update/page gates. Peak observed OAM is 52 entries;
the busiest observed scanline has 26 sprites and 232 summed source pixels. These
counts are observations, not hardware render-time certification. The index verifies
1,723 native 240×160 screenshot records and pins the five exact full reports.

The [native evidence index](evidence/underwater-native-k/index.json) currently pins
eight reports with **24,208 overlapping checks**, including full/minimal routes and
lifecycle. The sum is bookkeeping, not a count of unique behaviors. Supplemental
stress reports intentionally do not claim the main suite's complete command coverage.

### Independent minimal-save lifecycle

- [Bounded independent lifecycle summary](evidence/underwater-native-k/minimal-lifecycle.json)
- Raw report: `build/underwater-k-minimal-review/lifecycle/underwater-minimal-review.json`
- Report SHA-256:
  `f9c6816cb9d149fbedab37d35f155a42937836380cf2ba89ae935d6fa25bde32`
- **1,187 checks, zero failures**, controller-only, zero game RAM writes and zero
  machine-state loads; eight fresh-emulator cold boots
- All 21 unique directed exits, surface return/re-entry, native save/reboot,
  ordinary death/retry, cold dialogue and ineligible evolution preview/cancel
- 33 active cadence windows total 6,487 hardware frames, each with matching update
  and page flip; peak observed update/render cost 268,951 cycles
- Eight separately labeled Continue-loading windows each take 52 hardware frames,
  with 44 ordinary counter increments, 45 flips and one counter reset; these are
  not counted as passing active-play cadence
- Optional quests, eligible evolution preparation and trial completion are outside
  this minimal-roster review; no eligibility or progress was fabricated

### Real-module synthetic engine integration

The [candidate-K engine index](evidence/underwater-engine-review/candidate-k-index.json)
records **147 checks and 14,832 full-state mutation-rejection cases** across the
current renderer, event/evolution lifecycle, Magma return and Southern rest probes.
All four passed on their first attempt, with all frozen runtime and shared-observer
sources unchanged. Fixed-address test mappings use `MAP_FIXED_NOREPLACE`; no existing
mapping, permission or ASLR setting is changed. These are synthetic host probes
against real production modules, not native acquisition, pixel/DMA or timing proof.
Large report bytes are preserved through deterministic gzip with raw/compressed
hash receipts rather than silently truncated or replaced.

### Qualified native stack observation

The [candidate-K memory report](underwater-memory/candidate-k/README.md) records
388 functional checks with zero failures over three separately instrumented
native runs: authentic 34-person migration, a real evolution at 50 retained
individuals and actual casts of all 16 retained Underwater evolved forms.
The observed cumulative canary-overwrite extent is 948 bytes; the lower 2,892-byte
prefix and bottom 64-byte guard remain unchanged. This is not true minimum SP,
an exhaustive maximum-stack bound, production-K cadence or physical-hardware proof.
The exact control/diagnostic distinction and resource accounting are below.

### Spoiler-free player teaser

- [Bounded media receipt](underwater/media.json), [native preview](underwater/preview-native.png)
  and [4× preview](underwater/preview-4x.png)
- Raw capture report: `build/underwater-k-teaser02/capture.json`
- Report SHA-256:
  `69cd2bc05da1657973aeb52b85e536569d5a5e3f0b0d9250600d8deeb00464fb`
- **176 checks, zero failures**, controller-only, zero RAM writes, machine-state
  loads, capture cuts, capture resets or capture SRAM reloads
- 1,200 continuous 240×160 hardware frames, each with one update and one displayed
  page flip; peak update/render cost 174,660 cycles, peak 24 OAM objects
- 20.091 seconds at the GBA clock ratio; MP4 is nearest-neighbor 4× (960×640)
- Real emulator PSG audio; no added orchestral track
- Ordinary opening-town exploration with an already-owned companion; no new
  recruitment/evolution, puzzle interactions, secrets, boss or ending
- Native stills and the 4× preview were visually reviewed

The teaser demonstrates only the recorded town window. It cannot clear full-region
visual, combat, resource or complete-campaign acceptance by itself.

### All-eight-area native visual review

The [visual review](evidence/underwater-native-k/visual-review.json) pins actual
candidate-K screenshots for all eight scenes. Review covers the full-world viewport,
floating HUD, player/companion outlines, walkable paths, contrasting boundaries,
interactive-target spacing and different town/archive/garden landmarks at native size.
The rooms intentionally leave open floor around mechanisms; environmental density
is modest. Some pale command details have less contrast against cream backgrounds.
These are finite captured views, not exhaustive coverage of every camera coordinate
or a physical handheld panel/color-response test.

### Shipped native recipe replay

The [eight-stage recipe receipt](evidence/underwater-native-k/recipe/receipt.json),
SHA-256 `71f97ff182b35cc2335c69050e33414a50b7a024fa4017f2b537cb4d10745a6c`,
records exit 0 for full collection, minimal main, minimal lifecycle, precision
combat/control/art, scenery, dynamic powers, natural phase sweep and alternate-aim
scenery. This is a fresh sequential run of the shipped native driver, with new
producers and consumers on K rather than reused earlier route states. Its observer
source closure and runtime inputs remain pinned throughout. It is separate from
the independent eight-report evidence set above and is not added to that check sum.

Eight unit tests for the evidence-summary packager also pass, including rejection
of failed, mismatched, diagnostic-only and invalid-cadence reports. A superseded
draft recipe stopped at its observer-source change guard; its raw evidence remains
separate and is not relabeled as this successful replay.

### Complete retained regression and host targets

The [isolated final-K aggregate index](evidence/underwater-legacy/final-k-aggregate.json)
records **`make test-tools test`**, **`make test-underwater-host test-magma-host`**
and **`make test-magma-native`** all at exit 0. The latter earns fresh same-K Magma full and
minimal routes, then runs controls, retained-save lifecycle, combat, performance
and teaching encounter checks. Its seven reports have zero failures. The isolated
copy keeps 1,163 runtime inputs and 295 observer inputs unchanged.
[K-specific host receipt provenance](evidence/underwater-host-k/provenance.json)
keeps new host results separate from restored historical evidence. Two reporters
changed output paths only; their nine-test rerun passed with the same measurements.

The complete `make test` run reaches and passes the final Southern combat,
performance and rendering suites, alongside the earlier retained campaign/system,
regional, Northern and Southern checks. Prior-candidate failures remain separate
evidence and are not relabeled as the final aggregate.

### Source-export preflight

The [source-only ZIP preflight receipt](evidence/underwater-source-preflight/receipt.json)
pins 3,977 shipped files and a 14,434,553-byte initial archive, SHA-256
`2a3e935b946176ab3c041d51244d675e37615dd6a5191242903229266e922be0`.
Its extraction clean-built to the exact K ROM and symbols. Bridge setup and smoke tests passed. `make assets` reproduced the shipped
files with zero changes. This establishes that preflight snapshot's reproducibility;
the final delivered ZIP has a separately accompanying sealed export receipt.
Do not substitute this preflight identity for the final package.

## Final source-package verification contract

The source archive is sealed only after runtime evidence and these documents are
frozen. Its separately accompanying export receipt identifies the final ZIP and
manifest hashes, file count, source-only allowlist and text-size audit, then records
clean extraction/build, exact K ROM/symbol reproduction, bridge/smoke checks and
asset-generator roundtrip with shipped-file comparisons. The receipt is outside the
ZIP so recording its final hash does not alter the archive being identified.

Do not infer a final-package pass from the earlier preflight or from this document.
Use the matching sealed receipt delivered with the archive. A passed isolated,
synthetic or prior-candidate test cannot substitute for an exact-source native gate.
Earlier failures retain their original evidence and the separately recorded fixes
and reruns; no failed diagnostic is counted as a final pass.

## Save compatibility and loading boundary

The wire format remains Save5, with unchanged 24-byte individual records,
160 roster slots, 6,144-byte banks and existing offsets. Current writes use
**content revision 6**. Previously published formats 2–4 and Save5 revisions 1–5
migrate forward using frozen historical rules, not the expanded current catalog.
Read [the revision-6 persistence contract](UNDERWATER_PROGRESS_SAVE6.md) and
[historical policy](HISTORICAL_SAVE_POLICY.md) for implementation-level constraints.

Players must back up `.sav` before upgrading and use matching ROM/save basenames.
Do not downgrade an upgraded save into an older ROM; use the untouched prior backup.
A loaded history does not award new quests, items, companions or trial completion.

Cold Continue can take **52 emulated hardware frames** before normal play. This is
an explicitly blocking decode/initial-checkpoint transition, not a steady gameplay
or 59.73 Hz claim. Its loading trace and frame-counter reset must be reported
separately. It is excluded only from active cadence; active PLAY, dialogue, menus,
evolution, transitions and incremental saving still require one game update and
one displayed bitmap flip per hardware frame in every measured acceptance window.
Host throughput/FPS and raw modulo arithmetic across a counter reset are not cadence.

## Resource accounting and limits

Candidate-K static accounting is in
[`underwater-memory/candidate-k/memory-budget.json`](underwater-memory/candidate-k/memory-budget.json).

- ROM: 9,777,176 / 33,554,432 bytes; 23,777,256 bytes below the hardware limit
- Growth from delivered Magma: 2,281,256 bytes
- Original 2 MiB growth target: exceeded by 184,104 bytes
- Revised engineering growth budget: **2.5 MiB = 2,621,440 bytes**, with 340,184
  bytes remaining; this is an explicit adjustment, not a retroactive 2 MiB pass
- EWRAM data plus BSS: 49,856 / 262,144 bytes
- IWRAM code: 28,432 bytes (`0x6f10`), ending at `0x03006f10`
- Gap to SYSTEM stack floor `0x03007000`: **240 bytes**
- SYSTEM stack reserve: `[0x03007000, 0x03007f00)`, **3,840 bytes**; keep it intact
- GCC stack-usage record count: 919, all static; individual frames are not a
  transitive maximum-call-chain proof

The separately instrumented startup canary ROM is not the release ROM. Its
[control rebuild receipt](underwater-memory/candidate-k/diagnostic-build-receipt.json)
shows an uninstrumented control byte-identical to K. Observations must report their
own diagnostic hash and measure only the overwrite extent of exercised paths.
Unwritten slots, writes equal to the canary, unexercised paths, assembly/library
calls and interrupt stacks limit the result. Do not label an unchanged lower guard
as true minimum SP, guaranteed free stack or a physical-hardware safety proof.
The completed K observation is separately paired in its linked memory report.
Existing A/B/G reports remain historical; their measurements are not relabeled K.

## Reproduction and export requirements

Build requirements and compiler setup remain in [the README](../README.md) and
[tools guide](../tools/README.md). Generated source ships in bounded chunks.
`make assets` requires Pillow and the documented Noto CJK font; plain `make` does not.

- `make test`: retained whole-game regression through Southern
- `make test-magma`: retained Magma host/native regression
- `make test-underwater`: new chapter host checks and the sequenced native target
- `make test-underwater-host`: new chapter host contracts, not native route acceptance
- `make test-underwater-native`: fresh full/minimal producers, cold lifecycle,
  precision combat/control/art, scenery, dynamic, phase and alternate-aim consumers
  through `tools/run_underwater_native.py`
- `make gameplay-video`: spoiler-free Underwater town capture with native PSG audio
- `tests/underwater_journey.py`: pinned full/minimal controller producers
- `tests/underwater_precision_native.py`: precision/control/field/art consumer,
  using `tests/underwater_combat_native.py` as its shared native foundation
- `tests/underwater_geometry_stress_native.py`, `underwater_dynamic_stress_native.py`
  and `underwater_phase_stress_native.py`: scenery, moving and phase/cadence stress
- `tests/underwater_minimal_review.py`: independent cold-SRAM lifecycle consumer

The native runners require the exact ROM/symbol/ELF pairing and runtime-source
manifest. The full producer uses the delivered full Magma fixture; the minimal
producer explicitly uses the minimal fixture and `--scope main`. Consumers must
receive the hash of the successful source report and its immutable observer sources.
See each runner's `--help`; do not substitute a newer source snapshot for its pin.

A final source-only archive must contain editable sources, original assets, tests,
small documented fixtures and bounded evidence. It must exclude toolchains,
shared emulator libraries, generated build trees, live saves and machine states.
Every allowlisted text file must be below 90,000 bytes; large raw traces belong in
separately authenticated compressed evidence or bounded summaries. Oversized
archived engine/canary JSON is shipped as deterministic gzip with raw/compressed
hash receipts; its uncompressed original is excluded by an explicit allowlist.
A ZIP manifest is an integrity inventory, not test execution. The preflight
rebuild and generator roundtrip passed; the final package is identified and checked
by its separately accompanying sealed export receipt.

## Scope limits and preserved history

This is native mGBA emulator evidence. Physical GBA hardware, flash cartridges,
other emulator/compiler versions and the macOS native bridge-build path are not
verified. Existing original PSG music/effects are included; no orchestral or
voice synthesis integration is claimed. The game remains in development, with
104-form, 120-form, eight-legendary and integrated-release milestones ahead.
No measured campaign playtime is claimed.

[VERIFICATION.md](VERIFICATION.md) remains the delivered Magma record.
[UNDERWATER_ACCEPTANCE_PLAN.md](UNDERWATER_ACCEPTANCE_PLAN.md), foundation/design
notes and A/B/D/G diagnostic reports preserve their original development context,
including failed runs. This document is the current tested-milestone index and does not
rewrite those historical results.
