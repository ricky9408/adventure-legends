# Magma release verification

Developer evidence contains progression spoilers. The default player teaser and guide
remain spoiler-free. Measurements were made on 5 October 2026 UTC.

## Exact cartridge and compatibility

- ROM: **7,495,920 bytes**, SHA-256 `90ba47f30a0c94c28f073d26cc31ac5f5c736eb4d6e704d090892d2776f1ffb2`
- Symbols: `add52be1a5d23d2e8df8fd616f4ef1c7fde8d3e1906e1d789925d68476cf50f6`
- Runtime-source manifest: `a72fd93eddb0a39322b22e45caf0f4ac49496d962776ee616dfd83642342ef3f`, **893 inputs**
- Save wire 5, content revision 5; exact revision 1–4 policy, 24-byte records,
  160 slots and two 6,144-byte banks remain compatible
- Linked IWRAM code **28,120 / 28,672 bytes**, 552 bytes before the reserved-stack boundary
- Data **92 bytes**, BSS **48,568 bytes**; no new permanent OBJ allocation
- mGBA 0.10.5, GNU ARM GCC 14.2.1, native 240×160 Mode4/OBJ output

A clean independent rebuild reproduces the exact ROM and symbol bytes. ELF debug paths
may differ between directories; both ELF load images are independently paired with the
same cartridge. A separate source-export review verifies a clean extracted build and deterministic
asset regeneration. All 2,740 files in its reviewed archive remained byte-identical;
only the four documented excluded River overview PNGs were regenerated. Repackaging
that untouched extraction reproduced its exact ZIP bytes. The final package adds
verification notes/receipts and redirects a host-test output into build/, with runtime
inputs unchanged. The sealed receipt is in `magma/source-export-review.json`.

## Controller-earned content

The final exact-D acquisition route passes **26,884 checks**, with no failures or game
RAM writes. It earns all **65 historical forms while retaining 34 actual individuals**,
all **31 gear items** and **38 quest claims**. All nine new families, 15 new personal
trial/evolution edges, two third tiers and four alternate branches are exercised.
Four extra bases are real repeated encounters with distinct identities; collection
history never clones or replaces an individual.

The separate minimal route passes **1,837 checks** from the authenticated delivered
Southern eight-base town save. It requires no optional earlier quest, trial, evolution,
gear or Core ending. Only the two guaranteed teaching companions and starter sword are
needed for the new main route. The eight prior individuals stay unchanged.

Independent native controls pass **1,162 checks**: movement, diagonal camera, movable
objects, reset/reentry, modal ownership, journal/selector input, actual death/retry,
all eight full-view scenes and the moving hazard's pixel/collision alignment. Twelve
whole-viewport oracles and twenty damaging-sweep position oracles are included.

The final **647-check retained lifecycle** authenticates the exact-D acquisition SRAM,
then uses cold SRAM boots only, never producer machine states. It checks all 34 storage
candidates, four genuinely earned same-family selector pairs, save/reload, ordinary
hazard death/retry, a second reboot and old-region return. Every identity, history and
claimed quest remains intact.

Seven named new native suites pass **50,149 overlapping assertions**, with zero
failures. The teaching-encounter exception suite contributes 427 checks; it is not
counted as obtaining an additional form. All native reports pin exact ROM/symbol/ELF, runtime manifest, emulator bridge and test
sources. The original producer reports are preserved byte-for-byte in bounded text
parts with the generated fixtures. See [magma/index.json](magma/index.json) and
`tests/fixtures/v5-revision5/provenance.json`. Individual checks overlap; their sum is
not a count of unique behaviors.

## Combat and actual frame presentation

The final same-target combat continuation passes **13,986 checks** and the performance
continuation passes **5,206 checks**, both with zero failures. They cover all 24 new
commands, real damage/control behavior, personal
identity, cooldown/recovery, inherited commands, one-hit rules, connected wall-clipped
paths, shared tile ownership, modal/hit-stop freezes and same-family switching.
Five-phase complete modifier tables, adversarial serial wrap and forged projectile
provenance are separate host tests, not falsely claimed as native input cases.
Normal R dispatch uses the authored default side; the alternate-side internal API is
not another player button.

Tests sample the main-loop update counter and displayed bitmap page after every
emulated hardware frame. Host execution speed is never the frame-rate metric. Timer
cycles exclude final VBlank wait/OAM commit, so a value below 280,896 alone does not
prove frame pacing. The target hardware cadence is approximately 59.7275 Hz.

Confirmed final-D windows include:

| Window | Updates / page flips | Peak measured cycles |
|---|---:|---:|
| All 34 real storage candidates and empty wrap |148/148 each|272,595|
| Full 34-individual repeated rest/save |180/180 each|219,356|
| Independent performance full-roster save |45/45 each|218,891|
| Final same-target combat windows, combined |3,837/3,837 each|246,444|
| Final same-target performance windows, combined |2,187/2,187 each|270,525|
| Spoiler-free native town stroll |1,200/1,200 each|137,414|

Six crowded windows combine five visible enemy bodies, a hostile shot, two arrows and
a Magma effect for nine actual frames each. Native cold journal coverage opens all nine
pages. Save, storage and cold-menu windows have limited remaining margins and must be
remeasured after future content/audio changes. A measured window is not proof of all
possible 160-instance/48-item engine states.

## Correctness fixes established during testing

- Damaging regulator sweep pixels now refresh with each collision position rather
  than the slower ambient animation clock
- The deliberate diversion remains latched through undamaged cycles, allowing ordinary
  walking to the coupling; it clears after a successful window
- A durable repaired-screen objective restores the repaired position after travel/load
- An inline chapter check and removal of an unrelated redundant geometry scan recover
  older crowded Southern command cadence without changing collision semantics
- Authentic full-roster rest exposed a cold-render plus anchor-validation overrun.
  Exact anchor validation is now queued inside frozen saving mode after both bitmap
  pages warm, before the unchanged snapshot/writer. No validation was removed

Earlier failed candidate reports remain preserved as development evidence. Test-only
route corrections moved away from the public rest interaction before sword attacks
and used a four-pixel path endpoint tolerance for Q8 motion, while independently
asserting real interaction range. No health, creature, reward or gameplay-memory
injection was used to turn those routes into passes.

## Core, saves and independent reviews

- Frozen-policy comparison covers **166,703** CRC-valid historical images/banks
- New typed transactions cover **344,176** interrupted/success write positions across
  **56** transitions; failed final commits preserve the previous bank
- Revision-5 direct/API and sanitizer tests cover same-instance trial causality,
  third-tier eligibility, alternate branches, source receipts, wrong identities,
  grandfathered capacity, mixed quest/gear atomicity and all unassigned bytes
- Collection admission preserves 72 planned terminal opportunities within 160 slots;
  old legal over-budget rosters remain loadable/saveable, without promising recovery
- The branch UI review covers 22 host scenarios, 896 cancellation masks and 60
  direction/A combinations; any direction consumes confirmation before mutation
- Deferred-anchor full-engine host review covers 27 scenarios in strict/UBSan builds,
  including the packaged earned-34 fixture, wrong mode/room/state, A+R, cancellation,
  failures at begin/mid-write/final commit, persistent feedback and successful retry
- Exact quarter-heart gear text is pixel-tested over 97 Q4 values and 2,500 comparisons

Host/synthetic evidence is distinct from controller acquisition and native pacing.
Isolated ARM save measurements and compiler stack frames do not establish full-engine
stack high-water. Reviews: [MAGMA_POLICY_REVIEW.md](MAGMA_POLICY_REVIEW.md),
[MAGMA_LEGACY_ADMISSION.md](MAGMA_LEGACY_ADMISSION.md),
[MAGMA_SAVE_IMPLEMENTATION.md](MAGMA_SAVE_IMPLEMENTATION.md),
[evidence/deferred-anchor/REVIEW.md](evidence/deferred-anchor/REVIEW.md).

## Whole-game regression and reproduction

A clean final-D `make test test-tools` passed with **exit 0** in **1,733.82 seconds**.
It includes all prior story/exploration/save/evolution/party/equipment, River, Northern
and Southern acquisition/combat/control/cadence/render suites plus the bridge smoke.
The full log SHA-256 is `46596948fcea3810393578c27133ebf6aeb0dd959c4b5c8ff97cfa0381c295a1`.
The source-pinned receipt is in `magma/aggregate.json`; earlier C aggregate success is
not substituted for this exact-D run. All nine retained Southern suites pass 33,010
overlapping assertions; their strict windows reach a maximum 273,845 measured cycles
with one update/page flip per hardware frame. Magma host contracts and the seven new native
suites are separately recorded rather than added to a misleading aggregate count.
The final live `make test-magma-host` also passes with exit 0; its complete log hash is
`6dd03c9608e8e80f7759002df1223d7c1e6c2d45ce8a48bd979f913d4eaf07ec`,
with bounded details in `magma/host-aggregate.json`.

Run `make test test-tools` for the retained whole-game suite and `make test-magma` for
the new host plus complete native milestone. `make test-magma-native` earns a fresh
exact-ROM collection, archives its exact producer scripts, then runs minimal, controls,
retained lifecycle, combat, performance and teaching-encounter checks. Source reports
are generated outputs, not hard-coded success fixtures. `make gameplay-video` captures
the spoiler-free town stroll; `make developer-video` is spoiler-bearing older campaign
media. Every capture/test requires the ROM/symbol pair it actually observes.

Legacy observation fixes use ROM-paired ELF/STT_FILE private-symbol scopes instead of
ambiguous global nm names. Northern facing-sensitive range tests measure after the
ordinary facing input, retaining their original band geometry, hit timing and damage
assertions. Historical fixture bytes and their source pins remain unchanged. The frozen Southern
policy oracle is included in `tests/fixtures/southern-policy-oracle`; both normal and
isolated no-sibling source runs pass all 166,703 differential comparisons. This test
now fails if its packaged oracle is absent rather than silently skipping it.

The independently extracted host aggregate passed every preceding suite, including
all 344,176 interrupted-write positions, then exited 2 at the deferred-anchor probe's
synthetic fixed-address memory setup, before any game assertions in that probe.
The exact script's one standalone rerun passed all 27 scenarios, and a separate mapping
diagnostic succeeded. The failed call's errno was not captured. A later disposable diagnostic independently
reproduced errno 17 (EEXIST): Python heap 0x04d48000–0x051a2000 overlapped the requested
0x05000000–0x05020000 synthetic palette range. This establishes a possible host-address
collision, not the unrecorded cause of the first failure or a game assertion failure.
This extracted aggregate is **not** reported as exit 0. The separate complete live
aggregate above did pass, as did earlier strict/UBSan extracted fixture checks.
No assertion was weakened and no mapping was forcibly overwritten.

The source package excludes toolchains, shared emulator libraries, live runtime saves,
machine states and diagnostic smoke screenshots. It contains original editable assets,
chunked generated arrays, generated QA SRAM fixtures and their exact provenance.
Prior release reports remain at [VERIFICATION-SOUTHERN.md](VERIFICATION-SOUTHERN.md)
and [VERIFICATION-NORTHERN.md](VERIFICATION-NORTHERN.md).

## Visual review, media and limits

All eight native scenes were visually inspected. Pale paths contrast with foliage,
ceramic water channels and foreground edges. Town terraces, workshop and spring grotto
supply distinct landmarks. Three industrial mechanism rooms deliberately share stone
materials and remain sparse; commercial-game environmental density is not claimed.
Developer-only native stills are under [magma/native](magma/native/index.json).

The default teaser is an unbroken **20.091-second** opening-town stroll with an already
available companion. It has no new creature reveal, puzzle solution, secret route,
boss or ending; no cuts, resets, RAM writes or ownership/quest changes during capture.
Its audio is actual original PSG samples with zero endpoint drift. The preview is an
actual 240×160 frame; delivered 4× media uses nearest-neighbor scaling. No orchestral
or voice integration is included. See [magma/media.json](magma/media.json).

Physical GBA/flash cartridges, other emulator/compiler releases and runtime stack
high-water remain untested. Cold checkpoint decoding is a blocking transition,
separate from steady gameplay and incremental saving. The 128-form game, underwater
chapter, return journeys and legendary acquisition remain unfinished. No unmeasured
playtime or commercial-game parity is claimed.
