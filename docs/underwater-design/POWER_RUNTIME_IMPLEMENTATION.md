# Underwater command runtime handoff

Implementation evidence only. This is not a release, an earned-roster claim, a controller-affordance acceptance run, a full-engine frame-budget result, or physical-hardware validation. All host targets, roster instances, collision scenes, projectile examples and isolated ARM timings are synthetic.

## Files and integration

- `src/underwater_powers.c/.h`: commands67–90, exactly one instance-bound cast
- `src/underwater_power_art.c/.h`, `src/underwater_tip_orbit.inc`: ROM-only original motifs and integer geometry
- `assets/generate_underwater_powers.py`: deterministic original code-native glyph generator, using the existing named RGB555 palette
- `src/northern_powers.c/.h`: narrow shared-lease extension, owner `NORTHERN_TILES_UNDERWATER`; historical focused linkers remain supported with a weak live-state reference
- `tests/underwater_powers_native.c`, `tests/test_underwater_powers.py`: strict host, ASan/UBSan, ARM objects and separate isolated timing cartridge
- `tests/underwater_power_preview.c`, `tests/preview_underwater_powers.py`: actual host-module native glyph pixels and explicitly sampled cumulative hit maps
- `tests/magma_powers_native.c`: existing lease regression updated to include the newly valid owner5; next owner is still rejected

The parent owns engine dispatch, gear locks, controller labels, body sprites, progression/selection hooks, world implementation, all native journeys and whole-frame acceptance. No game/core/save/equipment/world source is owned by this module.

Required calls:

1. Dispatch R to `underwater_power(command)` for67–90, including near field props. No feedback shortcut grants a field receipt
2. After modal, selector, dialogue, save, EVENT_PENDING and hit-stop early returns: pass cardinal key edges to `underwater_powers_input(pressed)` before player movement. Movement still proceeds. Input bits are GBA Right16/Left32/Up64/Down128
3. Tick once per active simulation update; draw is presentation only
4. Reset on room/death/load/new game. Never reset on a party/equipment/command edit. Reset deliberately does not clear global `ability_cd`; preserve ordinary-room cooldown to prevent a doorway refund
5. Call `underwater_powers_enemy_spawn(index)` for every new pool-slot identity, including bulk room spawning
6. Call `underwater_powers_geometry_changed()` immediately after any actual solid change, before subsequent hit/draw hooks. Dirty geometry cannot authorize a hit. The next active tick rebuilds it without changing ages, hit receipts or cooldown
7. Call `underwater_powers_selection_changed()` on selected-instance, party-map, form or equipped-command edits, even inside a frozen selector. This prevents away-and-back selection from restoring field rights between ticks. Combat age/cooldown continue; field rights and alternate aim are invalidated
8. Include `underwater_powers_busy()` in equipment locks
9. Body rendering can query `underwater_powers_companion_pose()`: -1 for ordinary movement,0 for startup anticipation,1 for the next4 updates,2 for the next6,then-1. Exact current selected identity/form/command is checked. Age never advances in this read

The once-only startup alternate accepts a single direction edge before age8. Horizontal edges mirror ordinary side choices; command69 accepts four cardinal starting corners;83/90 accept Up/Down for axes/inversion.67,71,77 and81 have no direction alternate. Mixed direction edges are ignored. Acceptance never changes cast origin, age, instance, phase, duration or cooldown. These API checks are not a substitute for native-controller proof that the parent routes those edges and teaches them.

## Field and boss bridge

At cast start, obtain `underwater_game_action_begin(3)`. During actual active geometry, inspect at most8 sequential `underwater_game_field_target(index,&x,&y,&radius)` targets. Field overlap uses the exact enclosed octagon drawn by the target ring: |dx|≤radius, |dy|≤radius, |dx|+|dy|≤radius+3, with radius bounded to0..10. A receipt requires an actual clipped active-shape pixel inside that octagon, plus a clear supercover from that pixel to the field center. Empty stencil windows remain empty; a field entirely inside one cannot trigger. Enemy and boss tests remain center-only. Only the same currently selected instance/form/equipped command can call `underwater_game_field_hit(index,command,caster_id,form_id,token)`. Per-cast target bits prevent repeats, while world code owns room-attempt/source/trial causality. Any nonzero field response consumes that index's cast receipt. A geometry mutation inside a field hit blocks later cached hits until rebuild.

Teaching signatures both reach f24,s0, with f forward and s lateral:67 on its returning18..30 range band;70 within its12×16 stroke. Other dependable default base targets are73 f12,s0;76 f12,s0 before scenery;79 f8,s0;82 f16,s0 on a rotating tip;85 f6,s0;88 f12,s-10. These are genuine active signatures, not phase permissions.

Boss targeting remains separate through `underwater_game_target` / `underwater_game_command_hit`. The world callback retains authored vulnerability. No boss is displaced, rooted, staggered, retimed or reflected.71 explicitly catches ordinary moving foes only;77 requires a real directional entry and opposite exit, so a stationary boss cannot trigger it. No hidden armor bypass or generic boss hit is added.

## Finite geometry and provenance

Every ordinary target slot has a generation receipt. Recycling a slot during a cast marks it unavailable to that cast, including16-bit serial wrap. At most one damage budget is paid per target: base16Q4 or terminal24Q4 before the existing five-phase resolver. The selected individual is validated once at cast admission; ticks/draws never validate a roster.

All paths use endpoint-inclusive integer scenery traversal and diagonal side-cell checks. Path lengths are validated and bounded. Clipped moving tips cannot restart when a wall is removed. The near-wall crawler preserves its origin/turn connectivity, stops at convex corners and has a24-step tangent cap. Remote frond and jaw pivots retain explicit anchor connectivity. Target nudges are bounded one-pixel steps with scenery-footprint checks.

No new command consumes, reflects, reallocates or impersonates any engine Shot. Moving tips are internal cast geometry, with their cast as provenance. Tests leave real hostile and friendly Shot identities untouched. No generic melee guard, root, slow, stagger, windup, invulnerability, projectile interception or weapon-followup hook exists.

Noteworthy exact raster interpretations:

-68 uses two approximately20px opposed diagonals pivoting into the f28 seam; mirroring changes the folding diagonal
-69 uses four separate8×8 cells, ordered in6-update intervals
-71 records the intersected entry edge, waits8 active updates, then nudges at most8 pixels toward that edge; it never traps a foe
-72 uses12 forward×14 lateral lobes, with the central8px corridor empty; lowered sides exchange in5-update intervals
-75 uses4 forward×12 lateral bars,8 updates each
-78 has two distinct6×10 apertures in its24 forward×28 lateral footprint
-80 grows a front quarter-arc and an opposite rear quarter-arc: each is a semicircle with a90-degree gap, never a complete annulus
-81 records4 positions over12 simulation updates, then warns12 more, then retraces at most36 pixels. Each segment is Manhattan-capped12; warps cannot author a trail; the player is never moved
-82 has five4×4 tips,15 active updates and exactly72 degrees of procedural rotation. Center/arms do not damage
-83 uses four4px arms and an exact central8×8 aperture; Up/Down swaps12/24 axis extents
-84 damages only the three2px joint/end cells; hollow dots show the harmless articulated ribbon body
-85 has two opposed pulses on one fixed bent path; only one is damaging at a time. The other is hollow
-87 shows both unequal loop outlines; the current priming loop has denser hollow dots. Only the shared8×8 crossing can damage in its two timed windows
-88 has four3px teeth and real3px gaps; all teeth stop together at the first scenery contact
-89 retains its diagonal safe stripe across both triangle phases
-90 requires all triangle vertices to stay scenery-connected and preserves its6×6 center aperture

## Shared tile and render budget

Permanent OBJ delta:0 bytes. Exclusively lease existing PIN at15616..15871 (256B) plus WATER_DROP at16192..16255 (64B). Do not overwrite heart, arrow or phase-icon regions. Startup streams the unique16×16 command emblem into PIN and hollow2-pixel particles into WATER_DROP. On release, PIN's first64B becomes the hollow particle and WATER_DROP becomes the solid2×2 active particle. No other claimant may write these bytes until expiry/reset releases the lease. All old/new lease claimants reject while any live claimant exists, including an older caller lacking a recorded lease.

Warnings, harmless priming/return/body outlines, and actual damaging pixels have distinct hollow/solid marks. Intended safe holes are not filled by large opaque decoration. Draw uses at most24 cached geometry sprites plus one startup emblem:25 OAM entries. Repeated unchanged draws make0 scenery probes and do not advance any simulation state. Total engine/scanline OAM remains a parent acceptance gate.

Mutable module state is456 bytes in the measured ARM objects, including observation globals; it is compile-time bounded to512. The power object and glyphs remain ROM-resident. The world-side exact supercover and row-interval helper use712 IWRAM bytes including section alignment within the parent-owned collision section; its placement does not reduce the4KiB stack reserve. No heap or large local draw buffer is used. See the regenerated object report for exact ROM/stack figures; individual-function stack size is not a measured whole-engine/IRQ high-water mark.

## Verification artifacts and limitations

Run:

- `python3 tests/test_underwater_powers.py`
- `python3 tests/test_underwater_geometry_equivalence.py`
- `python3 tests/test_underwater_field_overlap.py`
- `python3 tests/test_underwater_supercover.py`
- `python3 tests/preview_underwater_powers.py`
- `python3 tests/test_magma_powers.py` for the extended legacy lease regression

The host suite retains the original23034 damage assertions and adds147, for23181 total, including all24 commands against five phases plus neutral, four facings, startup/active/recovery bounds, all retained base commands, honest entry/exit catches, one-hit target budgets, slot reuse/serial wrap, selected-instance changes, away-and-back invalidation, inherited root/slow/stagger state, hostile-vs-friendly shot identity, scenery/corner clipping, intended apertures, delayed world/boss receipts, default/alternate controls, and read-only pause/pose behavior. Nine nonconvex/static signatures also use an independent51×49 integer-set oracle. Synthetic boss callbacks explicitly reject invulnerable targets. The engine has no separate ordinary-foe armor attribute in this runtime; an invented armor model is not claimed as tested.

`build/underwater-powers-host/report.json` records host/object measurements. `arm-timing.json` records a separate synthetic ARM7TDMI cartridge at WAITCNT0x4317; timer readings include six foes/eight mock field targets and scenery invalidation. Its ELF symbols are STT_FILE-scoped and ELF/ROM bytes are checked. `source-pins.json` verifies compiler inputs did not change during that run. The cartridge never replaces the game's ELF/ROM.

`build/underwater-powers-art/` contains original glyph sheets and actual host-drawn1×/2× command snapshots. Collision maps are explicitly2px sampled cumulative unions against stationary foes.71/77 correctly show no stationary union because they require movement receipts. Snapshots contain no world art or companion body art and are not player screenshots.

Still required from the parent: real native controller routing and alternate affordances; actual current world collision and field targets; all required rooms/boss states; cold/loaded menus and EVENT_PENDING freezing; earned89-history/50-instance collection and reboot; full update+save+draw+OAM frame cycles/VBlank/page-flip cadence; scanline OAM; max-roster stack; final source/ROM freeze. These isolated results do not establish59.7275Hz whole-engine operation.

## Exact geometry optimization and Gate Release correction

Candidate A's geometry is frozen at `tests/fixtures/underwater_powers_candidate_a.c`, SHA256 `e2ec1a0adcb188fe1e69c730d7bd02f17d22eed54484344dcf65e73792bfacd0`. The differential suite compares36,800 cast-frame records, each with1,386 exact pixel queries and rendered mark data, across24 commands, four facings and eight collision/mutation/startup-alternate scenes. Another15,135 directed supercover checks match. The same records also match frozen candidate D (`tests/fixtures/underwater_powers_candidate_d.c`, SHA256 `bef0ec007fbda6366e51b6566ab99a6012370dbfe62aa1a197f84ca0baee5d5a`). Only the original reference's command77 cadence is adapted; none of its geometry or collision algorithms are changed. A separate exhaustive intersection oracle matches13,824 octagonal field-area cases across every command/facing, holes, radius1/10 and wall invalidation.

The world provides `underwater_game_clear_box(x0,y0,x1,y1)`: true means every integer pixel in the inclusive rectangle is clear under current world solidity. It returns false outside Underwater, for invalid bounds, and whenever any row-band or dynamic obstacle intersects. If a distant obstacle defeats the full positive-forward certificate, the module tries an exact near-half rectangle, keeping near rays cheap while far rays still fall back. Command90 uses its actual side-dependent extent (forward34 or48), so unrelated far scenery does not defeat an otherwise clear triangle. The power caches a tight per-command empty-box proof for one collision epoch. A ray whose endpoints are both inside that convex proven-empty rectangle needs no pixel retrace. Longer rays outside the proof can request an exact smaller rectangle certificate, falling back to the original endpoint-inclusive supercover if it fails. This is a proof-based broad phase, not corner sampling or an assumption about tiles.

Solid endpoints are rejected before per-ray rectangle scans. A proved-clear whole-stroke rectangle can bypass duplicate raster collision probes, while the same Bresenham steps and clipping fallback remain. Mark creation reuses the exact pixel proof already supplied by its successful ray or stroke instead of probing that pixel again. Full mark buffers skip presentation-only rays.

A64-byte, two-bit-per-pixel16×16 central memo is used only for exact observed collision results. Moving hook/zig/wave tips remember how much of their authored prefix was already proved clear; collision changes discard both prefix and occupancy proofs. Once stopped, a tip stays stopped, including if the obstacle is later removed. Catch handlers reject impossible entry bounds before expensive line-of-sight checks. Field strokes test their actual raster and Manhattan brush directly, avoiding nested target-area-by-segment rescans; identical sequential field targets share one result only within the current tick, and any collision mutation invalidates it. A callback regression raises a wall after the first of eight identical targets and proves later targets cannot reuse that receipt or stale overlap.

Command77 keeps startup14, the18-pixel lane fromf15..33, genuine front entry, opposite exit,24Q4 once-only damage, and side/retreat escape. Its active window is now132 updates, lifetime154, cooldown180. The host suite also requires `creatures_catalog_validate()` before combat cases, catching reviewed-policy/generated-catalog/runtime cooldown misalignment. The independent natural-pursuit test starts atf38, advances one pixel per six updates, enters atage30, and exits atage144; this is114 updates after entry. Side escape or retreat still whiffs. The old36-update active window could not support that ordinary native walking speed.

Current isolated synthetic ARM maxima: cast26,491, tick61,999, draw4,002 cycles. Mutable state456B, largest individual function stack104B, power-object IWRAM0B, world-side supercover/interval helpers712B, and new OBJ VRAM0B. These are not native whole-engine cadence evidence; the parent must rerun real combat, trial4 natural targeting, and Gate Release pursuit on the frozen full ROM.

For blocked rectangles, the validated bounded ray dispatches to `underwater_game_supercover`, which runs the same endpoint-inclusive supercover and both diagonal side-cell checks in the parent-owned hot collision section. It rejects coordinates outside0..1023 and Manhattan distances greater than160, and returns-1 outside Underwater so old chapters keep the original generic fallback. The public helper compiles to326 code bytes and96 stack bytes; its private hot row-interval helper is384 code bytes and36 stack bytes. Section alignment brings their combined hot addition to712 bytes. The entire parent-owned collision hot section is1928 bytes. An independent Python pixel-grid oracle matches242,566 directed rays across15 actual room/puzzle/projection configurations, including all reported hostile scenery origins, all octants, ties, reversals, and extreme invalid inputs. The host module timing cartridge uses its generic synthetic fallback, so its cycle report does not measure this real-world hot path. Native whole-frame timing is still a separate acceptance gate.

Command87's two startup ring warnings do not depend on its side choice. Accepting its startup alternate now updates only the side/aim receipt; the active geometry key still rebuilds the correct damaging lobe on time. The extra differential scenes prove the warning marks and every point-hit result remain equal to both frozen predecessors, including a collision mutation after aiming.

### Measured blocked-scenery follow-up

A separate H instrumented ROM was paired with a byte-identical uninstrumented H control (`tests/build_underwater_power_profile.py`). At the real Commons origin(400,255), facing Up, cold inclusive counts attributed135,847 cycles to cast admission and124,074 to geometry. Seventeen clear calls used111,250 cycles, including13 rectangle proofs totaling26,446 and five pixel supercovers totaling67,144 (maximum21,406). Nested timer overhead is included, so these totals must not be added together or used as release cadence evidence. A separately paired one-predicate counterfactual that skipped command87's per-ray rectangle proofs made native cold admission worse,364,867 versus328,181 cycles, and was reverted.

The subsequent exact row-interval traversal keeps the rectangle proofs. For each visited row it computes the maximal empty horizontal interval containing the previous ray pixel from the original collision bands plus at most two current radius-five puzzle rectangles. A diagonal step checks newx against the old-row interval, then obtains the new-row interval at oldx and checks newx there: these are exactly the original two side cells and destination. Within this one bounded call, an identical immutable row-band pointer plus identical dynamic-row activity mask permits reuse only if currentx is inside the prior interval. The36-byte context is stack-only; no interval survives the ray, and no persistent generation/collision cache is trusted. All15 real world/projection configurations retain242,566 exact-oracle agreements. Native cadence still must be rechecked on the new frozen ROM.

The final box proof also keeps one stack-local previous collision-band pointer. Adjacent rows sharing that immutable pointer have identical results for the unchanged query x interval, so their repeated band scans are skipped. Dynamic rectangles are still checked once after all static rows. Sorted-band early termination is supported by the shared generator's documented sorted/disjoint merge contract and an additional test of all1,920 generated Underwater rows. The independent prefix-sum box suite passes1,183,690 checks, and all242,566 directed world rays plus36,800 frame geometry records remain equal. This adds only8 bytes to the combined hot section relative to the preceding row-span version.
