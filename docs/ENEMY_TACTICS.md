# Magma lane charger

One ordinary encounter changes: Magma area 39, slot 3 at (328,56) becomes a lane
charger. Its 5HP, Earth phase, position and ordinary 6G reward are unchanged.
Other authored enemies, controls, music and save formats keep their behavior.

The beetle locks a cardinal lane when the hero enters 64px Manhattan distance.
Its gold bracing pose and existing warning spark last 42 active updates. It then
rushes 3px per update for 18 updates and remains vulnerable for 90 updates.
Side-stepping avoids the locked lane; a hit, stagger or root cancels the attack.
Warning and recovery have no contact damage. Every movement pixel uses the
existing radius-five foot collision, including thin walls and bounds.

`enemy_tactics.c` owns the behavior and renderer frame selection in ROM. It reuses
the existing per-enemy clock, warning and aim storage. It allocates no new RAM,
projectile identities or resident OBJ tiles. One16px regional sprite cache entry
replaces the old body draw; shadow, warning spark and phase marker stay in their
existing object slots. The original procedural beetle uses the existing palette
and a shared 16px anchor across all poses/directions.

## Verification

- `make test-enemy-tactics-host`: production `update_enemies` integration in
  strict and ASan/UBSan builds. Checks warning damage gating, locked aim,
  recovery, thin-wall probes, interruptions, modal/dead/reset/slow behavior,
  and one sprite cache entry.
- `tools/measure_enemy_tactics.py --arm-prefix <ARM_PREFIX>`: exact comparison
  to cc5e88e. ROM grows 2656B overall; IWRAM decreases 8B to 28320B, leaving 352B
  before the reserved stack. Data/BSS remain 168B/92632B. The new module has
  616B ROM code, 2048B art, 0B data/BSS and 56B maximum individual function stack.
- `tests/enemy_tactics_native.py`: unmodified earned SRAM resumed through
  ordinary Continue, then real controller navigation, sidestep, sword
  interruption, three hitstop freeze frames, room re-entry, natural ordinary
  encounter death and A retry. No game-RAM writes or machine-state imports.

The native run at `build/enemy-tactics-native-04/regions/` completed 3179 hardware
frames with zero active update/flip misses, active overruns or emulator faults.
Its active-frame peak was 177463 cycles, below 280896. Larger cold-transition
frames are recorded separately and excluded from that active-frame claim.
Native 240×160 captures show the warning pose, sidestep recovery, hit, death and
retry. The controller sidestep preserved all 144q4 HP.

This is a focused cross-ROM integration follow-up from an authenticated earned
save, not a fresh candidate campaign or a subjective balance/fun assessment.
The combined changes still need the full fresh native campaign gate.
