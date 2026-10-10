# Shared Horizons powers

Original code-native art and sixteen independently authored command shapes for
forms105–120. Existing RGB555 indices only. The code and generated art are const
ROM/orchestration; only one296-byte bounded cast state is mutable. No music, DMA,
resident OBJ, palette, catalog, save or world reward ownership lives here.

`python3 assets/generate_horizons_powers.py` deterministically generates the
sixteen16px command motifs, two8px particles per command, manifest and contact
sheet. The exact13 opaque pixels of each particle are the collision mask.
`python3 tests/preview_horizons_powers.py` also builds
`runtime_shapes_native.png` from actual host OBJ raster output.
`python3 tests/test_horizons_powers.py` checks generation, strict C99 compilation,
ASan/UBSan, actual catalog ownership, Q4 phase combat and ARM placement/resource
accounting. These host results are not evidence of controller-earned gameplay.

Current ARM power objects total15,196 ROM bytes and296 BSS, zero data/IWRAM
and zero additional resident OBJ tiles. Maximum individual function stack is
104 bytes, excluding callback/IRQ stack. The host observed17 OBJ submissions
and6088 solid probes in a deliberately hostile one-pixel-wall case; production
profiling must cover108/121 beside narrow solids with the room supercover
accelerator. Creature art adds131,212 ROM bytes and zero RAM.

|Command / form|Combat choice and actual shape|
|---|---|
|106 / Lintail|A48px straight strip goes out for1 damage, then retraces for2; each enemy is hit once, so the stronger return needs spacing|
|107 / Loomarten|One narrow ribbon travels a30px straight and32px perpendicular leg; one early perpendicular edge sets side; both legs independently require LOS|
|108 / Cindercup|A stationary short gathering bar, then fresh R makes a diamond pulse expand to radius12 at the immutable cast origin; damage2; no release by age30 dissipates|
|109 / Mantlewick|A stationary forward crescent catches one ordinary hostile shot; fresh R sends an ember to36px for3 if caught,1 otherwise; open rear|
|110 / Talusnip|A short wedge does2 and pushes an ordinary enemy up to8px along facing; full swept foot, actors and player block each step; boss-kind damage without movement|
|111 / Stratodillo|One near then one far offset pad, with a deliberate gap; side selected early; damage1 near or3 far, one hit maximum|
|112 / Gleamray|A moving blade with one of two6px lateral offsets; permanently stops on first obstruction in any occupied lane, no ricochet; damage2|
|113 / Foldcurrent|Short near blade then delayed far glint at a different lateral offset; damage1 near or3 far, one ledger|
|114 / Rivetusk|Long narrow straight metal tongue, damage3 and16-update settle; flanks remain open and player never dashes|
|115 / Furlace|Stationary split shelter arc leaves its center aperture visibly open, catches one ordinary shot and damages contacted enemies once for1|
|116 / Kilnspoke|A quarter arc moves from the side to behind; the forward lane remains empty; damage2|
|117 / Chalkox|Grounded frontal U does1 and gives ordinary enemies18 updates of stagger; no rear guard or armor|
|118 / Tinshear|Short first parallel stroke then longer second stroke, separated by a dry center; damage1 early or2 late, one ledger|
|119 / Rippleback|Unequal near/far diamond splashes in opposite offset lanes, damage1 near or2 far; center remains dry|
|120 / Tetherasp|A stationary root strip damages a genuine crossing ordinary enemy once for2 and adds18 updates of slow only when none already exists; no boss slow|
|121 / Cymbalop|An expanding forward fan is narrow near the caster and wider farther away; damage2 once per enemy, clipped by solids|

All damage above is in whole hearts before existing five-phase Q4 rules. Pulse/fan diamonds require direct origin LOS to all13 drawn pixels, so neither
a clear neighboring center nor a clear side route leaks a diamond edge behind
an occluder. No
new phase interaction, healing, invulnerability or enduring field capability is
introduced. Every target still needs the world's independent tagged-object,
identity, command, scene, attempt, party, approach and action-token checks.

## Integration

- Compile `src/horizons_powers.c` and `src/horizons_power_art.c`
- Dispatch learned commands106–121 to `horizons_power(command)`
- Add `NORTHERN_TILES_HORIZONS` to the existing mutually exclusive PIN/WATER_DROP
  lease; neither claim nor release may overwrite any other live power
- Call `horizons_powers_enemy_spawn(index)` after assigning each enemy pool slot,
  and `horizons_powers_shot_spawn(index)` after assigning each shot pool slot
- Before each projectile moves, call `horizons_powers_intercept_shot` with the exact
  current segment and explicit ordinary hostile provenance; skip consumed shots
- Tick only after PLAY modal/journal/held-L/hitstop early returns; the engine alone
  ticks shared ability cooldown. Pure draw may run repeatedly while paused
- Call `horizons_powers_input(pressed)` before R's cooldown rejection. Its result2
  consumes the fresh R for the existing cast; never start another cast that frame
- Real party/identity/form/command edits call `horizons_powers_selection_changed`;
  merely viewing a menu does not. Geometry changes call `geometry_changed`
- Room exit/load/death/new game reset the module. Reset never changes ability_cd
- Use `horizons_powers_companion_pose()` (-1,0,1,2), cast-matched identity and the
  snapshotted direction for the selected companion's cast pose
- The world's `action_begin(3)`, `field_target`, `field_hit` and `revoke_cast` match
  Return's structure. Targets receive the same immutable identity/form/command/
  token only after exact live visible-pixel/octagon overlap and supercover LOS
- `horizons_powers_beat()` returns1 for first/outward/gather and2 for second/return/
  release; target dispatch is once per target per beat. `release_phase()` identifies
  the explicit fresh-R release window. This permits a same-cast source→seam proof
- New powers never forward to Return rooms. Parent's legacy-power adapter must
  separately forward Hingelet102/Rillkite104 and older commands in Horizons rooms

Geometry changes revoke outstanding field authority permanently for that cast.
When an accepted moving-load action changes collision, world code must retain
its already accepted ordinary movement independently; the revoked token cannot
be used as another fresh contact. Multi-beat exhibits with no collision change
must avoid artificial geometry invalidation between their two proof beats.
