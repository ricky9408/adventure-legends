# Underwater world integration

Developer-only integration/solution notes. These are not player-facing media.

## Files and ownership

- `src/underwater_game.c/.h`, `underwater_trials.inc`, `underwater_events.inc`, `underwater_game_draw.inc`: ROM-only world and bounded transient proof
- `assets/underwater_region/dialogue.json`: 188 `UW_` UI text fragments; append to the global raster text generator
- `src/underwater_art.c/.h`, `underwater_art_data`: eight original indexed backgrounds and 20 glyphs; four large rooms include odd-column copies
- `tests/test_underwater_game.py`: real world/transaction code behind synthetic host warps and synthetic field-hit callbacks, never native acquisition evidence
- `tests/test_underwater_art.py`: exact original pixels, static collision, safe approaches and reproducibility

## Engine dispatch

Use `underwater_game_is_room`, not an unbounded `room >= 46` test.
Room sizes are 480×320 at 46/47/48/51, 240×160 otherwise. Copy every row of the full 240×160 viewport. The small floating HUD stays separate.

Add the following paths alongside prior region hooks:

- room name/quest HUD text, art bitmap and odd-column scrolling, geometry fingerprint, `solid`, actor pass, overlay pass
- room spawn count and positions, enemy spawn rows, actor glyph streamer `underwater_actor(sprite,x,y)` using existing regional slots
- journal tab 9 with `underwater_game_draw_journal` and menu input
- A → `underwater_game_interact`; R must always start the actual command runtime, never substitute `underwater_game_power` feedback for a cast
- active PLAY tick only → `underwater_game_tick`; no tick in pause/dialogue/hitstop/saving
- melee class 1/2/3 (sword/lance/bow) callback → guardian `underwater_game_weapon_hit`; the three successful exposed openings are independent action-token receipts
- exact native field-shape hit → `underwater_game_field_hit`; powers iterates at most eight `field_target` entries and tests the target center with real clipping/LOS
- every explicit selected individual, party map or equipped/selected-command mutation → `underwater_game_selection_changed` AND the powers selection hook, including away/back within a menu
- death/load/new game → world reset and powers reset

The world itself calls `underwater_powers_geometry_changed()` immediately when physical geometry changes. The next engine geometry fingerprint check may call it again harmlessly. The proof never treats a capability, a phase, a global aid or an owned copy as a cast.

## Frozen transaction handshake

`underwater_game_event_pending()` is an immediate simulation stop. An interaction or field hit may set it mid-update; return before more hostile simulation or input. Show the same honest frozen working notice on both display pages before stepping, as with the existing deferred save notice. Do not skip simulation frames silently and do not render a new geometry state without updating its cache key.

Call `underwater_game_prepare_event()` once per frozen cached update. It uses `underwater_job_step(handle,1024,room_generation)` and returns `SAVE5_BUSY`, `SAVE5_DONE`, or `SAVE5_FAILED`. It does not run synchronous validation. Four 12-byte intents are the bounded maximum. The job owns the existing save scratch. Only successful job completion can award XP, refresh the roster, consume an invitation, or schedule SRAM saving. Failure leaves invitations and durable progress unchanged. Loading, death or explicit cancellation clears unfinished jobs/proof.

A pending transition is not the same as a pending save:

1. At the beginning of `enter_room`, before changing the engine room, player coordinates, campaign room/spawn, enemies or attack state, call `underwater_game_request_enter(area,spawn)`
2. Return 0 means denied; return 1 means the existing visited destination is ready; return 2 means freeze the old scene and process the event queue
3. On completed events, call `underwater_game_take_transition(&area,&spawn)` and then the normal `enter_room` path. A queued new visit was committed against the valid old checkpoint. Its second `request_enter` returns 1
4. Only now call `underwater_game_enter`, which is a cheap gate/visit check plus canonical scene setup. It does not validate/mutate the visit synchronously
5. Scene entry can itself queue the main quest offer. Drain that event before starting any pending SRAM snapshot

A door used by an interaction that also records a return-arch objective waits for that objective queue to complete before exposing the transition. Do not discard it by changing the room first.

Rest uses the same ANCHOR job. Until success, health and campaign/checkpoint spawn are unchanged. Only success fills health, stamps spawn 2 and requests SRAM saving. Legacy `save_prepare_pending/prepare_save` exports return 0 for compatibility and are not the Underwater path. A later SRAM write failure may leave valid earned live progress in RAM; a transaction failure must not fabricate a checkpoint.

## Scene safety

All manual controls use a strict facing cone: forward 6–26 px and lateral at most 10 px/half the forward distance. This prevents nearby RESET/talk/rest targets from stealing ordinary A presses. RESET is a separate shell pedestal; two A presses from the same approach confirm, B or walking away declines. It never costs health/resources or erases earned records.

The explicit trial lectern unfolds one projected practice fixture. Main movable geometry is suspended for the attempt; static architecture and all exits remain. Trial completion or selection cancellation restores the main solid arrangement only after the player stands clear. While temporarily inside its future footprint, field/A targets pause and movement remains free to the outer ring. There is no involuntary shove through scenery.

## Resource envelope

Art payload: 1,393,216 ROM bytes; no new resident OBJ bytes; exactly 20 glyphs streamed through existing regional slots. At most eight field targets and one trial are live. World mutable state is below 256 bytes including the compact queue; trial proof is far below its separate 192-byte ceiling. Check final ARM symbols for authoritative totals. No world code belongs in IWRAM. Dynamic line drawings use no extra OAM.

This document and the host tests do not claim native controller acquisition, power-shape acceptance, final frame cadence, OAM scanline limits, maximum160 roster behavior or stack high-water. Those remain whole-cartridge acceptance gates.

## Magma town portal

Engine-owned portal at room38 center(416,224), `UNDERWATER_SPR_GATE`, with a small pale-water ring/shaft as a visible landmark. Strict A approach(416,240), facing up. This position and approach are clear of both static collision and every old town A target. Gate is Magma quest32 CLAIMED, then request destination46 spawn0. Waiting lines: `TX_UW_PORTAL_WAIT_A/B`. Room46 south exit returns to38 spawn4 at(416,240), the actual shell-lift approach. This appended current-r6 landing requires Nacreway visited; historical revisions1–5 still allow only their exact old Magma rows0–3. No old pixels or old-policy rows change.

## Reciprocal return landings (current revision6)

Old rows remain exact. New explicit rows are46:3=(448,160),48:2=(448,160),51:2=(32,160),52:2=(32,112). Anchor spawn2 remains anchor-only at46/47; it is an ordinary explicit entrance at48/51/52. Routes47→46 now land at46:3;48→51 at51:2;51→48 at48:2;49→52 at52:2. Other pair directions retain their existing reciprocal0/1 landings. The one-way Court return arch remains53→46:1. Generator exit records include actual target_spawn rather than a default0.

Focused verification: `python3 tests/test_underwater_landings.py`. It executes all nine reciprocal door pairs, every legal spawn and codec reload, the new optional-entry gates, the shell-lift append and old A-target separation, and rejection of a false south-door transition elsewhere on Nacreway's bottom edge. These are synthetic host checks; final native route/reboot acceptance belongs to the exact newly built cartridge.
