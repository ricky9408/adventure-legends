# Emulated frame pacing

This test measures **game updates per emulated GBA display frame**, not the speed
of the host computer running mGBA. The display rate used is
16,777,216 / 280,896 = **59.7275006 Hz**. “60 Hz” below means one update per
hardware display frame.

## Reproduce

Do not rebuild a ROM while another process is capturing it. Prefer an immutable
copy of the ROM and the matching `.sym` file.

```sh
python3 tests/performance_tests.py \
  --rom build/emberbond.gba --symbols build/emberbond.sym \
  --output build/perf-final --strict
```

To recapture the original baseline preserved during development:

```sh
python3 tests/performance_tests.py \
  --rom build/perf-baseline/emberbond.gba \
  --symbols build/perf-baseline/emberbond.sym \
  --output build/perf-baseline/captures
```

The script does not run `make`, modify the game, or write game RAM. It boots the
real ROM in `tools/mgba_runner.Emulator`, follows controller-only traversal,
opens the bridge, lights both braziers, and reaches the guardian. The traversal
is derived from `tests/playthrough.py`. Every scene is a 360-hardware-frame
window by default. `--frames` changes that window.

At a scene waypoint, an mGBA savestate is saved after 12 warmup frames. The
measurement runs, then that exact controller-reached state is restored so that
the stress window does not change subsequent traversal. The snapshots are not
hand-authored saves. Initial/final screenshots and the state files remain in the
selected output directory.

## What is recorded

After every `Emulator.frames(1)` call, the script reads the retained `frame`
symbol, which increments at `update()` entry. It independently reads the
DISPCNT bitmap page bit to count presentation flips. The renderer commits OAM
at that same VBlank in the optimized build. Reading a symbol does not alter game
state.

`metrics.json` records ROM SHA-256/size, symbol-file SHA-256, per-scene emulated
frames and seconds, update count, update-interval histogram, longest unchanged
run, presentation count/intervals, initial/final game state, projectile peak,
and the number of frames with a companion, toast, cooldown, or exposed boss.
It retains event offsets so isolated misses can be traced to state changes.

Targets:

- Gameplay: one update per hardware frame, with no missed update frames
- Static title/dialog/pause: at least one update every two hardware frames,
  with no longer gaps; steady 60 Hz is preferred
- Cold menu transitions: recognize the input within two hardware frames, with
  no update gap longer than two hardware frames
- Motion: 24-frame unobstructed cardinal and diagonal movement probes;
  diagonal/cardinal distance ratio within 5%, and diagonal axes within one pixel

The cold-transition probes intentionally have no cache warmup. They catch the
one-off stall that an idle-menu average would hide. Motion probes use controller
input and readback in an unobstructed village patch.

This is representative, reproducible emulation coverage. The baseline has no
cycle instrumentation; the final engine also provides hardware-timer region
measurements. This is not an exhaustive worst-case proof or a physical-cartridge
hardware test. An update interval says when updates occurred; it does not imply
that every cycle between them was busy. A displayed bitmap page flip does not
prove that its pixels differ from the previous page.

## Original baseline

ROM: `a5957540687e3889b81eba3f0f04a131a8d089797898d45220f541d7045b6304`,
228,152 bytes. Full scene summaries are in `baseline.json`.

| Scene | Updates / 360 display frames | Cadence |
|---|---:|---|
| Title / intro dialogue | 180 | Fixed 2-frame intervals (29.864 Hz) |
| Village idle / motion | 360 | Fixed 1-frame intervals |
| Forest combat, no summon | 360 | Fixed 1-frame intervals |
| Forest summon + toast | 266 | Mixed 1/2-frame intervals (44.132 Hz) |
| Forest companion + nature cooldown | 302 | Mixed 1/2-frame intervals (50.105 Hz) |
| Temple combat | 360 | Fixed 1-frame intervals |
| Bridge / temple / gate / boss dialogues | 120 | Fixed 3-frame intervals (19.909 Hz) |
| Pause | 90 | Fixed 4-frame intervals (14.932 Hz) |
| Guardian armored / exposed | 180 | Fixed 2-frame intervals (29.864 Hz) |

The armored guardian window includes eight simultaneous live projectiles.
The companion windows include actual toast/cooldown activity. None of these
windows left its intended game state or room.

Original diagonal movement moved 12 horizontal and 24 vertical pixels in
24 updates, versus 24 pixels for cardinal input. That was both 11.8% faster in
Euclidean distance and an unequal-axis heading.

## Bottleneck evidence

`baseline-renderer-disassembly.txt` contains the preserved ELF disassembly of
`pix`, `text`, and `sprite`. `text` and `sprite` issue a function call to `pix`
for each opaque pixel. Each pixel call repeats clipping, row/column address
calculation, a VRAM halfword read/modify/write, and function prologue/epilogue.
The renderer also copies the complete background each frame.

Font work read directly from the baseline ROM's `ui_texts` table:

| Text group | Bitmap bit tests | Opaque-pixel `pix` calls |
|---|---:|---:|
| Village location label | 915 | 259 |
| Title text | 5,605 | 1,388 |
| First intro overlay alone | 6,735 | 1,563 |
| Pause overlay alone | 12,000 | 2,989 |
| Guardian HUD text | 2,910 | 844 |

These are raster-operation counts, not measured CPU cycle totals. Individual
font dimensions and counts are in `baseline-font-work.json`. They explain why
text-heavy scenes regress much more than the village.

## Optimization strategy and remaining checks

The engine's optimization uses hardware OBJ sprites for moving actors, caches
static background/UI pixels independently for both bitmap pages, and uses Q8
fixed-point movement. This removes repeated transparent sprite rasterization
and redundant text drawing without changing the hardware frame target.

The first optimized measurement made all village/forest/temple, summon/toast,
and cooldown windows exactly one update per display frame. Steady title and
pause also reached that rate. It exposed a second issue: full static redraws
on HP changes still caused paired one-frame misses in the guardian, and cold
pause entry still had a four-frame gap. A toast expiring during a dialogue also
unnecessarily invalidated both cached pages.

A cache is only effective when its invalidation key contains state that is
actually visible. Frequently changing HUD elements should update small regions
or hardware objects instead of invalidating the entire scene. Cold text drawing
also needs to fit the transition budget; caching alone hides the cost after the
first frame but does not remove it.

The final immutable ROM results below verify the resolved hot-path and
cold-transition budgets.

## Current result: scrolling milestone strict pass

The current native ROM is 571,408 bytes, SHA-256 `a0c68c5ecde39b75b7bbafff4e19467d1e6cc901bb1c99b92af60492d3de375c`. All 15 existing steady-scene windows pass, plus four new scrolling/companion/attack/projectile/dodge windows. The new windows produce 1,440 updates and 1,440 presentations in 1,440 hardware frames. Maximum sampled scrolling update/render cost is 125,325 cycles, or 44.6% of a frame before OAM commit.

Scrolling uses two precomputed even/odd pixel atlases with aligned DMA16 row transfers, rather than CPU byte shifts. Forest HUD/toast caches have independent invalidation keys, and sword tiles precompute at boot. Every camera alignment is checked against original atlas pixels: 28,560 pixels per alignment, no mismatches.

The original baseline above remains historical evidence of earlier optimization; the current primary report is `final.json`, and the additional moving-camera coverage is [milestone1/exploration-results.json](../milestone1/exploration-results.json), summarized in [milestone1/summary.json](../milestone1/summary.json).

Use `make test` to run the full journey, edge cases, performance suite and exploration checks. Representative measurements do not establish an exhaustive worst-case bound or physical-GBA validation. Intentional sword hit-stop remains distinct from missed rendering frames.
