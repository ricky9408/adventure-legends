# Explicit evolution UI host review

## Result

22 focused tests pass against the production `src/progression.c`, both normally
and with AddressSanitizer plus UndefinedBehaviorSanitizer. No production code or
Save5 implementation was edited by this review.

Two review findings were reported and fixed by the integration owner before the
final passing runs:

1. `A+LEFT+RIGHT` and `A+UP/DOWN` could previously reach the commit path. Every
   directional chord now consumes the frame; only exactly LEFT or RIGHT changes
   a two-branch choice. A simultaneous A never commits that frame.
2. Initial branch preference checked local requirements without collection
   admission. It now prefers the first genuinely admitted choice, so a reserved
   duplicate branch does not displace an available missing branch.

## Evidence boundaries

- This is a **synthetic host test**, not emulator/controller acquisition evidence,
  a native gameplay journey, ARM performance measurement, or hardware proof
- Actual linked modules include progression, creature core/catalog/admission,
  quest context, Save5 reader, generated UI text, and generated creature portraits
- Explicit stubs provide engine globals, save/sound requests, and framebuffer
  drawing. Text pixels use the shipped `UiRun` data and its 120-pair scanline
  addressing contract; sprites use actual shipped pixels
- Synthetic setups are valid creature rosters. Direct quest-state changes and
  deliberate stale/invalid-state fault injection do not claim valid completed
  acquisition, quest, or whole-save histories
- One separate smoke case loads and validates the actual delivered Southern
  revision 4 fixture `tests/fixtures/v5-revision4/southern-minimal8-town.sav`, then
  checks that drawing the Growth tab leaves its loaded save byte-identical
- Commit tests count a save request at animation completion. They do not exercise
  SRAM writer timing or power-loss behavior

## Covered behavior

- All 15 authored Magma evolution edges: both 31/34 three-stage lines, all four
  two-choice families, and the 95/97/99 single-step families
- Actual selected roster individual remains authoritative even with two copies
  of one family and a higher-tier same-family form in the compatibility cache
- Each locally eligible branch is preferred, locked alternatives remain visible
  and selectable, and both-locked choices remain inspectable
- All 896 ten-bit GBA input masks containing B, START, or SELECT cancel before
  confirm/direction/stale-participant logic, without save mutation or core commit
- All 30 direction/A combinations for each of a single-edge and two-edge source
  avoid committing; only exactly LEFT/RIGHT toggle a two-choice selection
- Cancel and reopen reset the choice and bind the current actual individual
- Different selected copy, replacement instance ID, changed source form, invalid
  selection, and unoccupied source abort before any core commit
- Level, bond, story context, trial, sanctuary, and malformed roster are rechecked
  on A; every failure leaves `Save5State` byte-identical
- A newly earned trial is respected even if the cached display still says locked
- At excess 88, a locally ready duplicate branch is reserved and the missing
  alternative is admitted. At excess 87 the first target can be displayed ready;
  one intervening added copy raises excess to 88 and commit correctly refuses
- First admitted second-branch selection performs exactly two admission/roster
  queries, without a redundant third refresh
- Old/target animation art changes at tick 36, preserves individual identity,
  returns to pause and requests one save at tick 80
- Core function instrumentation observes no full roster/catalog/admission/commit
  calls across 180 repeated Growth/confirmation draws and idle inputs, or 79
  animation draw/tick iterations. The same counters increment on event-time
  selection, proving that the instrumentation is active
- Every branch's two names, real 32×32 portraits, selected highlight, status and
  controls fit the 240×160 framebuffer. Names fit their 96-pixel cards, do not
  overlap portraits, and status labels remain within the enclosing panel

## Run

```sh
python3 tests/test_magma_evolution_ui.py

ASAN_OPTIONS=detect_leaks=0 \
LD_PRELOAD="$(cc -print-file-name=libasan.so)" \
MAGMA_EVOLUTION_SANITIZERS=address,undefined \
python3 tests/test_magma_evolution_ui.py

MAGMA_EVOLUTION_CAPTURE_DIR=build/magma-evolution-ui-host \
python3 tests/test_magma_evolution_ui.py
```

The capture option additionally needs Pillow. Ordinary checks have no Pillow
dependency. The bridge is `tests/magma_evolution_ui_host.c`; the test compiles
the real source directly into a temporary shared library and deletes it on exit.

## Host raster captures

Representative images and exact draw-call records are in
`docs/evidence/magma-evolution-ui/`:

- `branch-37-choice-0.png`: first Tuftpika branch selected
- `branch-46-choice-1.png`: second Ashkite branch selected
- `reserved-first-branch.png`: first branch selected with collection reservation

These are labeled host rasters, not native screenshots. They were visually
inspected at 240×160. The test can regenerate all eight branch-choice images and
the reserved-state image. `source-hashes.json` identifies the inspected source,
generated text/art files and Southern fixture; each capture JSON also records
the progression source hash.

Native modal/controller regression and event-time worst-case latency remain
separate integration acceptance work. Event-only validation is verified here;
it does not imply that its ARM execution fits within one hardware frame.
