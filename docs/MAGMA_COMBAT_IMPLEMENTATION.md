# Magma combat implementation and parent-hook contract

This describes the implemented command module, not cartridge/controller acceptance. The source contract remains `docs/magma-design/magma_allocation.json` and the creature cards. Commands43–66 are implemented; their real catalog rows are validated on cast. No released Southern checkout was edited.

## Module and ownership

- `src/magma_powers.c/.h`: one immutable caster snapshot, at most three projectile-like components, six target ledger bits, and twelve bounded geometry paths
- `src/magma_power_art.c/.h`:24 original signature motifs, each a16×16 mark and8×8 particle, entirely ROM-resident
- `src/northern_powers.c/.h`: appends lease owner4 for exactly the existing PIN256B/WATER_DROP64B overlap; old owners1–3 retain their guards. The optional weak `magma_power_time` reference preserves independently linked historical harnesses
- No heap, player displacement, player immunity, terrain mutation, IWRAM placement, new resident OBJ allocation, roster copy, or save copy
- Gear must stay locked for the complete startup/active/recovery lifetime. Projectile motion ends within that lifetime. Early consumed effects may leave only recovery; they do not shorten/reset the cooldown

## Engine hooks required before native acceptance

1. Dispatch a learned selected command43–66 to `magma_power`. Validate normal gameplay/busy/modal state in the same place as other command handlers. `magma_power_side(command,-1/+1)` permits an explicit side for58/64; default is left relative to cast-facing
2. Offer `MAGMA_HINT_LANDING` from `magma_powers_hint`, then `magma_powers_aim` only when requested. Command51 allows exactly one retarget during its first12 startup updates. It preserves the original clock, cooldown, hit ledger and lease. A same-form different individual cannot retarget the earlier individual's cast
3. Tick once after every dialogue/menu/selector/save/death/hitstop early return. `tick` also defensively freezes on hitstop. Draw never changes age or cooldown
4. Add `magma_powers_busy()` to the actual gear busy mask. No separate projectile pool survives cast expiry
5. On room/death/new/load reset, call `magma_powers_reset`. Do not reset on selection/party changes. Reset releases only its own lease and clears only bounded statuses it supplied
6. Every assignment of a new enemy pool-slot identity, including bulk room initialization, calls `magma_powers_enemy_spawn`. Six slot ledger bits prevent recycled targets from receiving a second hit; explicit slot invalidation survives serial wrap
7. Only ordinary melee contact may call `magma_powers_melee_guard` before applying contact damage. Bosses, ranged attacks and generic player damage never call it. The8-update grace belongs only to that same enemy identity and consumed contact
8. Before moving an ordinary hostile projectile, call `magma_powers_intercept_shot(index,current_x,current_y,next_x,next_y,eligible)`. Eligibility must be exactly1 only for the game's ordinary hostile-shot provenance bit; boss/special beams are0. The module also verifies owner, positive lifetime, pool bounds, exact shot delta, bounded sweep, wall and diagonal-corner collision. Return1 means consumed
9. Fingerprint actual solid inputs, including moved bricks/baffles, manual/field mechanisms, doors and bridges, before damage, hooks or rendering. Call `magma_powers_geometry_changed()` after any change. Room/reset/cast/retarget also invalidate internally
10. Successful field actions call only `magma_powers_feedback`, with that companion's learned command. It supplies a16-update companion pose signal via `magma_power_cast_time`; it uploads nothing, claims no lease, damages nobody and changes neither cooldown nor gear lock. The main companion renderer must honor `magma_powers_cast_matches_selected`
11. An exposed regulator coupling is an explicit damage-only exception. On each successful new combat cast, the module retains `magma_game_action_begin(3)` and its own chapter-hit bit. Exact active damage geometry calls `magma_game_command_hit` with phase-resolved Q4 against the neutral coupling. The bridge confirms exposure and room45; room44 weapon-only pins reject companion damage. No retarget, selection change or other weapon channel resets either local cast identity or local hit rights. Cone/Shower aim can see the exposed coupling. No control/guard/slow/root reaches the boss
12. There is no Magma weapon-hit callback: none of the24 authored commands has a weapon-triggered follow-up. Preserve the Southern confirmed sword/lance/real-arrow callbacks, including lethal sources; never call them recursively from Magma damage

## Exact action mapping

All startup/active/recovery/cooldown values are copied exactly from the cards. Every target receives at most one nominal authored Q4 budget, through the real `game_enemy_hurt` and five-phase resolver. Elemental advantage/resistance changes final HP loss; the card budget is the base damage allocation, consistent with existing combat. No gear attack bonus or armor bypass is injected.

|Command|Distinct action and checked geometry|
|---|---|
|43 Warm Thread|40px transverse ground thread; first swept ordinary crossing consumes the whole effect|
|44 Coil Clamp|Two separately grouped hooked arms close inward in three steps across a32px pocket; shared target bit|
|45 Crown Interval|Three separated spokes activate in successive10-update intervals|
|46 Heel Knock|Narrow22px forward three-spoke cone; ordinary windup interruption and8-update stagger|
|47 Brace Reply|Stationary frontal bracing arc; one eligible contact triggers its reply; expiry alone deals zero|
|48 Archfall|44px-wide four-span frontal arch/crescent with20-update warning and12-update ordinary stagger|
|49 Burr Skip|One36px seed path, two18px hops with visible lifted body and checked ground footprint; first target slow18|
|50 Root Hem|Parallel32px lines at lateral±12; central gap safe; one brief12-update ordinary root per target|
|51 Cone Drop|12px landing footprint, aim≤48px,16-update warning, falling body; cached origin LOS invalidated by real topology changes|
|52 Mist Stop|Short square puff centered28px forward; first ordinary target gets12-update movement arrest|
|53 Cup Shower|Three stationary small landing points in a narrow column; drops land at active updates6/16/26 and share one24Q4 target bit|
|54 Ribbon Sweep|45px lateral path; traveling band broadens only after its first12px|
|55 Pick Tap|Two lateral nail jabs six updates apart; any first-jab hit suppresses the second|
|56 Spiral Notch|Narrow28px metal strike; bounded stagger extends only an already-staggered ordinary target|
|57 Tail Pendulum|Diagonal swing, then one18px lateral shard on the connected wall-checked segment; one shared target bit|
|58 Cinder Tilt|Facing-relative chosen-side dart with26px diagonal maximum and first enemy/wall stop|
|59 Plume Cut|Two distinct rising/falling diagonal slash intervals with fixed startup aim and shared target bit|
|60 Ash Screen|Stationary16px screen consumes one ordinary shot; at its40-update active expiry, one outward three-ray puff|
|61 Gravel Sift|Three nonhoming ground chips, each travel≤30px, independent wall/first-target stop, shared20Q4 target bit|
|62 Terrace Lift|Two28px-reach rising lanes, active in sequence, with wide safe lateral gap and one target bit|
|63 Sprig March|Slow36px ground bud, alternating one/two-pixel advance, first enemy/wall termination|
|64 Trellis Bend|Two connected24px segments, chosen L turn,48px total; second segment requires intact first|
|65 Bead Step|Three small nonhoming outward beads with large angular gaps and one16Q4 target budget|
|66 Dewfold|Five separate expanding edge lobes; center and angular gaps remain safe, once-per-target24Q4|

## Collision and rendering contract

Paths cache their exact endpoint-inclusive raster visibility with side-cell tests on every diagonal step. This includes the origin-to-first-segment connection and any connected-parent span. A wall clips a segment; no child can restart beyond its blocked parent. Endpoint changes invalidate downstream cache entries. Topology invalidation clears all cached proofs without changing lifetime, damage ledger, cooldown or ownership.

Only scenery proofs are cached. Enemy coordinates, ordinary classification, positive health, target ledger and short footprint-to-target LOS are live. Swept crossing is bounded to24px of actual enemy travel; larger discontinuities cannot create retroactive hits. Projectile-like effects use the exact checked path's moving raster interval. Rendering uses those same clipped paths and intervals, with a24-object hard cap. Airborne body decoration for seed/cone/drop retains its checked ground footprint and cannot deal independent damage.

Boss/special enemy kinds are excluded explicitly from the ordinary pool. The regulator coupling is reached only through the dedicated exposed-scene damage/token bridge described above. Ash Screen additionally requires caller-provided ordinary projectile provenance. Neither guards nor slows/roots retime a boss.

## Evidence and remaining acceptance

Run `python tests/test_magma_powers.py`. It builds strict C99 and ASan/UBSan harnesses using the actual creature, equipment, Q4 damage, gear and weapon runtime. Only the world, selected-instance bridge, pools, feedback and OBJ hardware callbacks are synthetic. The harness covers all24 commands×all five phases plus neutral, all four facings, startup/recovery boundaries,401 ordinary damage assertions, all24 explicit scene-coupling cases, independent cast/weapon tokens, one-hit/reused/wrapped identities, wall/corner/dynamic geometry, one-shot aim, field feedback, freeze/reset, all four lease owners, guards, projectile exclusions, and actual sword/lance/arrow paths.

It then compiles ARM objects with stack-usage reports and creates a separate minimal cartridge under `build/magma-powers-host/arm-bench/`. It never replaces `build/emberbond.*`. Timers use the game's WAITCNT0x4317. Observation reads size-checked ELF32 STT_FILE-scoped locals from `main.c` and `magma_powers.c`; repaired-header-excluded ROM pairing is verified. Repeated unchanged draw must cause zero scenery probes.

`build/magma-powers-host/report.json` contains ARM ROM/EWRAM/IWRAM/individual-stack data. `arm-timing.json` contains each command's cast/tick/draw/busy cycles and collision/OBJ counts. The module-only conservative call-chain bound is384bytes; external engine/solid/renderer/IRQ stack is not included.

At the lease-only integration stage, before the parent added new chapter bridges to shared gear code, the historical Southern strict harness was separately relinked without Magma and passed its20-command suite,2,380 cached-raster differential cases, and4,800 draw stress calls. Parent integration must still establish actual-room controller behavior, native combined-frame cadence, full-engine stack high-water, visual acceptance, gear lock, modal routing and publication readiness. Isolated timing is not evidence of a full-game frame budget or physical-hardware performance.
