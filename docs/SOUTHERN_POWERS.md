# Southern combat commands: implementation and evidence

Development evidence, 5 October 2026. This is not a native cartridge/controller acceptance claim.

## Fixed scope and integration

Commands23–42 use the frozen41-form catalog, real learned/equipped-command validation, real Q4/phase damage and the real gear cooldown clamp. Ability12 and legendary/reserved forms remain disabled. No field capability is inferred from a damage phase or a command. Field dispatch remains the chapter controller's responsibility and happens before ordinary combat dispatch.

`src/southern_powers.h` is the integration contract. Call tick only after dialogue/menu/selector/hitstop early returns; hitstop is also defensively checked internally. Reset on room change, death, new game and load. Never reset merely for party selection. The shared global cooldown is set only by a successful new cast, not by party selection, feedback or a second aim.

- `southern_powers_melee_guard(index, attack_x, attack_y)` is called only for a confirmed eligible ordinary melee contact, never from generic damage. One interception grants12 active updates of grace against that same generation-bound enemy only. Other enemies, shots and bosses are unaffected. No second counter is produced
- `southern_powers_windup(index, base_updates)` is called only at an ordinary windup start. Command29 targets kind2 ranged actors: either an active ordinary windup, or a resting timer at most40. An active timer is extended through this same hook at cast, once; a resting timer is left untouched until its actual windup starts. A mark must leave room for its12-update pop. No boss timer is changed
- `southern_powers_approach(index, &x, &y)` returns a temporary walking destination for an ordinary actor. It never changes player coordinates or teleports an enemy
- `southern_powers_weapon_hit(index)` is notified only after confirmed sword/lance/ordinary-arrow damage. The normal weapon call site, not the generic damage resolver, owns this notification. A lethal hit can still trigger a surviving paired mark. Echo damage cannot recurse into this hook
- `southern_powers_intercept_shot(index, old_x, old_y, next_x, next_y, eligible)` consumes one explicitly tagged ordinary hostile shot. Boss/special eligibility must be false. Consumption kills that slot immediately and never modifies its owner/phase into a friendly projectile
- `southern_powers_enemy_spawn(index)` is required for every new enemy pool identity. It invalidates matching marks and grace even on serial wrap and prevents that recycled slot gaining another hit in the current cast
- `southern_powers_busy()` is included in the real gear mutation lock. All internal projectiles end no later than their owning effect
- `southern_powers_can_aim()`/`aim()` allow only the same selected instance ID, form and equipped command. Command32 permits one left-to-right replacement before update22, restarting only six-update startup. Command40 permits a second independently aimed target before update48. Neither refreshes lifetime, cooldown or hit budget. Hint enum values distinguish these two interactions
- `southern_powers_feedback()` captures form, instance ID, facing and position for a20-update cast animation without combat, tile ownership, damage, busy lock or cooldown changes. It cannot overwrite an active combat cast
- `southern_powers_cast_matches_selected()` protects the cast-animation identity. `southern_powers_companion_pose()` supplies Leafbound's render-only swept sidestep/recovery for the matching selected instance; use it for both body and shadow without assigning player/follower coordinates

## Distinct command behavior

| Command | Role and timing | Base Q4 budget |
|---|---|---|
|23 Leafbound|Companion moves8px left in four swept updates, cuts laterally at6, recovers9–12|16 once per target|
|24 Canopy Arc|Six-update preview; projectile follows the exact two Bresenham segments shown by the preview|24 once per target|
|25 Ridgekick|Widening forward wedge during6–18; ordinary target push capped6 swept pixels|20 once per target|
|26 Rampart Turn|One angled ridge; one ordinary approach redirected to a side lane for12 updates; crumble at30|20 once per target|
|27 Lens Dart|Straight bead splits into two outward rays only on its first actual impact|16 initial,8 secondary; shared ledger|
|28 Prism Wake|Crossing line opens at6; one incoming eligible ordinary shot becomes two harmless10-update droplets; endpoint burst|24 once per endpoint target|
|29 Ember Hush|One eligible ranged mark; current/next ordinary windup extended12 once; pop after12, without a flash-induced interruption|16 once|
|30 Bellows Ring|Expanding annulus starts at radius8, reaches36 and fades; safe center remains empty|24 once per edge target|
|31 Sideguard|Left flank only; four-update startup; one ordinary melee interception and swipe|16 once|
|32 Vault Step|One optional R-again replacement to the right; six-update startup; interception emits lateral wave|24 once per target|
|33 Pinch Window|Narrow frontal arc, active updates8–16; one eligible ordinary melee interception|24 once|
|34 Shear Gate|Two blades; crossing window6–30; stationary presence alone does not count as crossing|24 once per crossing target|
|35 Sapling Feint|One grounded decoy diverts one ordinary approach for up to12 updates, then folds|No damage|
|36 Canopy Exchange|Two linked decoys; one approach routed toward the endpoint farther from the current player|16 snap once, only after activation|
|37 Rill Fork|A12px stem becomes a Y fork; short slow limited to effect lifetime|12 once per target across all branches|
|38 Veil Curl|Four-segment crescent with an open rear lane, active6–26; short slow|24 once per target|
|39 Warm Echo|One visible target's next confirmed ordinary weapon hit causes an eight-update delayed Fire follow-up|16 once|
|40 Paired Echo|Second target separately aimed; striking either causes one LOS-checked eight-update follow-up on its surviving partner|24 total follow-up budget|
|41 Needle Bank|One swept spine with one wall ricochet|20 once per target, including return path|
|42 Quill Return|Three-spine fan returns after18 updates toward the current companion only along a clear lane|24 once per target across outbound/return|

Base/evolved cooldowns remain90/120, gear-clamped to at most8 updates shorter. Maximum owning lifetime is60 updates; spent short effects release early. Windup and weapon marks disappear before a new delayed follow-up could exceed that bound. There is no player teleport, universal invulnerability, boss displacement, boss retiming or echo recursion. The separate native boss actor is not targeted by these ordinary-enemy hooks; this module does not claim companion boss-damage coverage.

## Collision and bounded work

Every moving pixel, fixed segment and target connection uses wall checks, including the side-adjacent pixels at diagonal corners. Shared span traversal tests at most six targets in one sweep; a hit is applied only after its path is confirmed. Curved projectile movement uses the same discrete segments as its preview. The fixed crescent caches its exact84-point world-axis raster and the complete unobstructed prefix of its four segments. Mark rendering/echoes cache LOS keyed by exact endpoint positions and enemy generations. Moving-target proximity and short target LOS remain live; reverse-direction LOS is not assumed symmetric. Dynamic walls require the explicit invalidation contract below. No hit shape, active timing window or lifetime changed in this optimization.

At most one Southern effect, three internal missiles, six enemy ledger bits, two marked identities and24 drawn objects are allowed. The host drawing stress observed at most12. No malloc, save/roster stack copy, IWRAM code placement or new resident OBJ allocation is used. Ten original family motifs remain in ROM. Their only uploads are the existing PIN256B plus WATER_DROP64B lease. Owner3 is Southern; claims reject any prior owner atomically, even before an effect clock is assigned. Active release is rejected; render requires the owning generation.

## Collision-cache invalidation contract

`void southern_powers_geometry_changed(void)` invalidates crescent scenery and both mark sight proofs without changing damage ledgers, timer state, cooldown, generation or lease. A successful new cast, reset and room entry reset already invalidate internally. The controller must call this hook after EVERY other collision/topology mutation and before the next Southern tick OR draw. That includes bridge/door/torch/campaign flags, old trial parcel/puzzle states, regional crates/dry blocks, new island machinery and any collision-changing interaction. A conservative collision-state fingerprint checked before both tick and draw is preferred; do not assume old rooms are static. Ordinary enemy position changes are handled automatically by mark endpoint/generation comparisons, and crescent target queries never cache enemy locations.

The original native S0 stress exposed170 updates/flips in180 hardware frames and a289,493-cycle peak with five naturally gathered bodies and command38. A second-aim command40 trace also dropped a hardware frame. These failures motivated collision-work reduction, not an IWRAM allocation or a geometry/timing change. The optimized isolated module has408 BSS bytes (including214 bytes added for both caches), no new OBJ allocation and no IWRAM code. In the six-target synthetic fixture, command38's recurring draw uses zero solid calls; the exact320,96 to272,48 paired-mark host test also renders with zero solid calls after its second aim. Native candidate replay is still required before claiming the release blocker resolved.

## Reproducible evidence

Run `python3 tests/test_southern_powers.py` for strict host C, ASan/UBSan, isolated ARM object/stack inspection, and a separate minimal ARM7TDMI timing cartridge under mGBA. It never builds or rewrites `build/emberbond.*`. Run `python3 tests/test_northern_powers.py` for the legacy Northern regression suite plus owner3 overlap tests.

The host harness links actual core41 catalog validation, Q4 phase resolver, equipment validation/mutation, weapon actions, arrows and gear runtime. World collision, actor setup, input/update scheduling, sound/impact, and OBJ hardware are synthetic. It covers all20 role handlers; startup/delayed windows; wrong direction; thin walls and touching corners; dynamic render obstruction; actual two-segment arc versus an incorrect diagonal shortcut; one-hit and recycled-slot behavior; interception eligibility and spent state; lethal-source paired echoes; same-form/different-instance rendering; real sword/lance geometry and real arrow echo callbacks; actual gear-busy rejection/release; pause/reset/decay; field-only feedback; and4,800 bounded drawing calls. An additional2,380 differential cases compare the cached crescent to the original uncached endpoint-inclusive geometry across four facings, thin walls, invalidation, removal, moving targets and reset. Long paired-mark cases verify aim-proof reuse, endpoint movement, geometry changes during the delay, generation reuse and no stale render after reset.

`build/southern-powers-host/report.json` records object size, stack frames and source identity. `arm-timing.json` records per-command timer readings at WAITCNT0x4317, exact linked-source hashes, and the isolated cartridge hash. Evidence copies are under `docs/evidence/southern-powers/`. The conservative module-only call-chain bound is256 bytes, excluding external world/renderer/progression callbacks and interrupt context; individual function stack maxima are separately reported.

ARM timing callbacks are still synthetic. Neither host success nor the isolated cartridge proves full-room collision cost, renderer/cache/OAM pressure, scrolling cadence, controller discoverability, boss behavior, natural recruitment/evolution, or an acceptable full-game frame budget. Those remain the integration controller's native acceptance tasks.
