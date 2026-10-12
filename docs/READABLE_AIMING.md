# Readable aiming and action notices

Return and Horizons commands, aimable Underwater commands, and Magma Cone Drop
(command51) now offer an optional aiming stage. Hold R after starting the ability,
use a single cardinal direction to revise the preview, then release R to cast.
The existing fast tap, startup, live effect, recovery, later R release actions,
and cooldown remain available. Japanese action hints and the companion field
guide explain the hold and release input.

The stage lasts at most90 active gameplay updates (about1.5seconds). The hero and
walking animation stay still while aiming. Enemies and the cooldown continue;
this is a deliberate choice window in a live world. Pause, hitstop, dialogue,
saving and the companion picker do not spend the aiming budget. B retains its
summon/dismiss meaning. A still confirms, L plus direction still switches
companions, and Select has no dodge action.

Only anticipation is extended. Damage, guard, field-contact, cast-pose and
startup ages stay at zero until release or timeout. The original origin,
instance, action token and total live effect duration remain unchanged. A cast
cannot reenter aiming after its first active update; changing the selected
instance or command invalidates field rights as before. Magma shows its existing
checked landing glyph during the stage and uses its original landing/LOS
validation when committing the cast. No new sprite, music, save field, enemy
damage or general projectile authority is added.

An action hint exclusively owns the bottom notice area. A pending ordinary toast
is hidden with its remaining timer paused until the hint closes. The existing
single pending-toast slot keeps its latest message; this does not introduce an
unbounded message queue. Cached and uncached notice drawing share the same owner
and must produce identical pixels.

## Verification

`make test-readable-aim-input` runs real C module fixtures in strict and
ASan/UBSan builds. It exercises all79 commands in the four affected modules,
including commands that retain their original non-aimable timeline. Cases cover
late and revised input, the90update cap, cooldown progress, identity changes,
no anticipation damage or field progress, unchanged cast tokens and tap
lifetimes, plus the retained geometry/damage/release suites. Notice checks
compare full frames against uncached drawing and independently assert exclusive
hint ownership and deferred timer semantics.

For controller and native rendering evidence, run:

```sh
python tests/readable_aim_native.py --rom build/emberbond.gba \
  --symbols build/emberbond.sym --bridge PATH_TO_NATIVE_BRIDGE \
  --producer-report PATH_TO_EARNED_JOURNEY_REPORT \
  --output build/readable-aim-native
```

The diagnostic loads an ordinary SRAM snapshot whose producer and hashes are
recorded in the report. It uses only controller inputs and readback, forbids
game-RAM writes and machine-state imports, and verifies the source save is
unchanged. If the source save was earned with a different ROM, it explicitly
labels the run as a cross-ROM compatibility diagnostic. Such a run demonstrates
the held controls, notice ownership, menu copy and native cadence; it does not
prove fresh candidate acquisition or full campaign completion. Keep the full
fresh campaign, font width, ROM size and IWRAM linker gates in integration CI.
