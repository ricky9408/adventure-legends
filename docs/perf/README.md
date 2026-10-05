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

## Final result: strict pass

Final ROM SHA-256:
`91da6f939d18037a0f4c164d9c2c4b0b9f41782e6f2f4a9b253212b5fec0dddf`
(254,576 bytes). The immutable measured copy is
`build/perf-optimized-v3/emberbond.gba`; its matching symbols are beside it.
`final.json` contains the final measurements. Two separate complete final runs
produced identical JSON, including every recorded event offset and cycle value.

**All 15 scene windows had exactly 360 updates and 360 presentation flips in
360 hardware display frames. Every observed interval was one hardware frame.**
That includes both guardian windows, eight simultaneous projectiles, fire and
nature companions, summon toasts, ability cooldowns, sword animation, title,
all sampled dialogues, and idle pause.

Cold overlay behavior is separately bounded:

| Transition | Input recognized | Longest update gap | Maximum timed work |
|---|---:|---:|---:|
| Open introduction | 1 display frame | 2 display frames | 378,315 cycles |
| Open pause | 1 display frame | 2 display frames | 512,165 cycles |
| Close pause | 1 display frame | 1 display frame | 126,973 cycles |

One hardware frame is approximately 16.743 ms; a two-frame interval is
approximately 33.485 ms. The input-latency number records the internal state
change, not the completion time of the first visible new panel. Steady overlays
then run at one update per display frame.

The final engine instruments the input/update/render region with cascaded GBA
hardware timers. These counts **exclude VBlank waiting and the subsequent OAM
commit**. They are workload-region measurements, not whole-frame utilization.
The independent presentation cadence test verifies that the full observed hot
path, including presentation, still fits each hardware frame.

| Gameplay window | Largest sampled timed work | Fraction of 280,896-cycle frame |
|---|---:|---:|
| Village motion | 12,180 | 4.3% |
| Forest sword/combat | 89,440 | 31.8% |
| Summon + toast | 206,060 | 73.4% |
| Nature companion/cooldown | 92,683 | 33.0% |
| Temple sword/combat | 87,251 | 31.1% |
| Armored guardian/projectiles | 28,272 | 10.1% |
| Exposed guardian | 191,975 | 68.3% |

The largest sampled hot workload is 206,060 cycles. Cold pause work is larger
than one frame but below two, and the measured transition obeys the two-frame
budget. The final implementation removes redundant panel overdraw, uses paired
font writes, prevents hidden toast expiry from invalidating a dialogue, draws
hearts as hardware objects, and updates the guardian banner regionally.

Final motion probes move 30 pixels cardinally over 24 updates. Diagonal axes
remain within one pixel of each other and their average Euclidean distance is
1.0254 times the cardinal distance, within the 5% integer-readback tolerance.
The underlying movement uses Q8 state and a normalized diagonal step. The
engine's deliberate three-update sword hit-stop is a gameplay effect; the
`frame` counter measures update invocation even during that effect.

Selected native-resolution before/after captures:

- [Original pause](baseline-pause.png), [final pause](final-pause.png)
- [Original guardian](baseline-boss_armored.png), [final guardian](final-boss_armored.png)
- [Original summon](baseline-forest_summon_toast.png), [final summon](final-forest_summon_toast.png)

These are screenshots of real emulation at input-reached waypoints. Static
images do not demonstrate frame rate; the JSON and reproducible test do.
