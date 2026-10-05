# Transient weapon controller

`src/weapon_actions.c` is a freestanding, allocation-free state machine using
`equipment_weapons` as its sole timing/damage/reach source. It is a core module,
not evidence that the equipment or three actions have been integrated into the
playable engine yet.

- Sword: three directional cuts, 2/2/3-update windups, one active update,
  14/14/20 recovery, 44-update combo window, eight-update input buffer
- Lance: six-update windup, three active updates, twenty recovery, six-update
  input buffer; narrow forward hitbox and a per-swing sixteen-target ledger
- Bow: hold to aim, release to fire. A quick tap completes its four-update draw
  first. Holding24 updates charges; charge display saturates45. Release then has
  twenty-three updates of recovery. At most two live arrows; a capped release
  consumes recovery without overwriting a projectile

The caller invokes `weapon_action_tick` exactly once per active PLAY update,
not in pause, dialogue, selector, save, or hit-stop. Before a modal/roll/transition,
`weapon_action_suspend` clears buffered inputs, cancels an un-fired bow draw,
and requires A release before another press. It preserves committed melee and
recovery clocks. The caller still preserves cooldowns when gear changes.

Stats are snapshotted on attack start. Direction is locked for melee and tracks
aiming only while bow charge is held. The ARROW event carries a one-update,
single-consumption spawn ticket; repeated calls cannot duplicate the arrow.
Spawning checks the chosen projectile slot is empty. The live-arrow count must
include all player arrows and is bounded0..2.

Before marking a melee hit, the engine must check both geometry and scenery line
of sight. It can then mark one target ID0..15; a three-update lance cannot hit the
same target three times. Wall-blocked targets do not consume their target bit.
Arrows traverse every crossed pixel, checking world bounds and walls before
calling target collision. Thus a fast arrow cannot skip a thin wall or target,
and a target behind the first wall receives no callback. Target callback consumes
one arrow and applies its snapshotted q4 damage. Arrows carry zero field tags;
combat phase or friendly ownership never lights a brazier.

Host evidence:202,117 assertions per strict/sanitized run, including200,000 random
valid input/state-machine steps. AddressSanitizer and UBSan are enabled; leak
checking is disabled for the ptrace environment. ARM7TDMI Thumb-O2 object1472ROM
bytes, zero global data/BSS/IWRAM, largest individual stack56bytes. Native gameplay
cadence and action feel must still be verified after engine integration.
