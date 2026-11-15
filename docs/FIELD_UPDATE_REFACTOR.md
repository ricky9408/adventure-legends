# Field update stages

The field update previously mixed timers, input ownership, movement, weapons,
every chapter's simulation and exits in one long function. `src/field_update.inc`
now gives those decisions five named stages: input, powers and timers, actions,
actors, and exits. `update()` still owns loading, opening, picker, event, save,
dialogue and menu states before it calls the field pipeline.

This is a behavior-preserving change. A contextual confirmation still consumes
its buttons while allowing the world to advance. A road crossing, new dialogue,
deferred rest or queued event stops the later stages at its existing boundary.
The movement/action stage has no `goto`. No save field, weapon timing, damage,
quest rule or controller assignment changes.

## Host verification

`python3 tests/test_field_update.py` executes the production include with real
weapon actions and controlled chapter/event outcomes. Both the strict C build
and ASan/UBSan pass 60 checks covering hit-stop and menu freezes, contextual B,
recall before aim, once-per-update timers, movement before attack, road and
dialogue barriers, deferred saves, claimed power input and every event boundary.
These fixtures stub collision, rendering and chapter effects; they establish
ownership/order, not a complete gameplay route.

The existing context cancellation, field Select and sword contact suites also
pass in strict and sanitized modes. The field-step checks pass; their garden
link additionally needs the documented Linux GNU linker for `--wrap`.

## Native baseline comparison

The 2026-11-15 comparison uses two immutable ROM/ELF/symbol sets built with
`/opt/devkitpro/devkitARM`. The baseline source is commit `81895ba`; the second
build includes the field refactor. It is a scoped intermediate candidate,
not the final art/story release build.

| Artifact | Baseline SHA-256 | Refactor SHA-256 |
| --- | --- | --- |
| ROM | `2cd10f4aa25029b07acbc26fbbabb336400513f760c97bf741721defbe9ed07d` | `0f0108b9f950a16e38f777d01e7beb11c9c1b9bfca86d5a52992449aa16cc25d` |
| ELF | `771237a60fdb5d4022a0f2b9806344bdca94e66e2374af74b759d0de69ed4ad0` | `f14d4306fa7100a364fea8803376a3bd40e680980feca880e0bfae03db662bdf` |
| Symbols | `fdf83f30fd440b43806946c13f1fbc80dd5b2d0a3ee2f4fc471922587bbf8d96` | `bff07f0911fbf336c6a52a7e0194752c57ea5297f9114c70df2cc3d55cbb87ff` |

```sh
build/redesign-venv/bin/python tests/field_update_native.py \
  --baseline build/redesign-baseline --candidate build/redesign-refactor \
  --bridge tools/mgba_bridge.so --output build/redesign-refactor-parity-full
```

Use a new output directory for a rerun. Both cartridges begin empty. Identical
physical button sequences advance all eight opening beats, complete the first
save, chain sword attacks, open/browse/close the menu, call and use a companion,
show the goal, step with L+direction, open the carousel, cross the village road,
and walk and attack in the scrolling forest.

All 1,127 measured hardware frames match on 31 named gameplay fields and all
20 bytes of `WeaponAttack`. Full `Save5State` and 32 KiB SRAM match at five
checkpoints. Each measured frame presents once, flips its bitmap page and stays
below 280,896 GBA cycles. The presentation serial supplies the cadence check
because New Adventure deliberately resets the gameplay `frame` counter.

Peak sampled cost is 258,392 cycles for the baseline and 258,396 for the
refactor. IWRAM code changes from 28,152 to 28,224 bytes, leaving 448 bytes below
the linker's code boundary and preserving the separate 4 KiB stack reserve.

The retained report is `build/redesign-refactor-parity-full/report.json`.
The compressed per-frame trace SHA-256 is
`b25976fde3ced903f344329480757e24c4c51776f11664dae99456d4d3f6f632`.
Inputs, candidate hashes and native screenshots are retained beside it.
The local bridge has no core-fault counter; the report records that limitation.
No game RAM writes, imported machine states, personal saves or physical GBA
testing are involved. This route does not establish all-chapter timing or an
exhaustive worst-case bound.
