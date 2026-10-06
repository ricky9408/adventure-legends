# Southern runtime integration and verification

Implemented module scope: rooms30–37, quests22–29, eight typed field encounters, ten family-local personal trials and one mobile lens-machine encounter. This is the separately authorized Southern checkout. The supplied proposal/design documents retain their historical proposal status; this implementation report does not claim controller-native acquisition, release publication or end-to-end ROM acceptance.

## Public integration surface

`src/south_game.h` mirrors the Northern chapter interface: room recognition, validated entry, exact radius-five collision, explicit interaction, selected-companion field input, tick/reset, world actors/overlay, names, journal, weapon target and hit callback. `src/south_art.h` uses the same descriptor layout as NorthArtRoom, with room-index base30.

- Call `south_game_enter(area,spawn)` before camera/player fixed-point initialization. It validates the destination, records its visit against the still-valid previous checkpoint, sets new coordinates and resets local arrangements. Only afterward is the new checkpoint saved
- Shared native OBJ actor bridge: `south_actor(sprite,x,y)` uses keys4096+sprite and the existing20-slot regional cache. Creature actors use `region_form_actor`; no second cache, tile memory, heap or framebuffer is allocated
- `south_game_power(command)` returns0 for no tagged field target,1 for success,2 for a rejected tagged interaction. Return2 must consume the attempted field input without consuming a combat cooldown/resource. The numeric command is deliberately not consulted: the actual selected, occupied active instance must support the registered field capability and have a short unobstructed path to the exact tagged fixture
- Invoke the Southern field handler before combat-command dispatch. Room34 requires capability26/REFRACT_BEAM; room35 requires capability17/TUNE_LATCH. Base79 and85 suffice. Owning either in storage is not enough until the player explicitly puts/selects it in the active party
- The journal is tab7, with eight quests followed by ten trial descriptions. It has no independent global quest IDs for the personal trials
- `south_game_target` exposes only the currently vulnerable moving machine coupling. `south_game_weapon_hit` accepts the currently equipped mundane sword/lance/bow class1–3, a confirmed overlap and Q4 damage. Parent attack ledgers must deduplicate hits as for the Northern target
- Existing `game_north_hurt` is reused as the generic Q4 player-damage bridge
- `south_game_enemy_spawns` returns a const table: five field31 enemies and two hollow33 enemies. Whole-heart HP, explicit kind0 melee/kind2 ranged and phase0–4 are supplied. Parent creates them after its enemy reset and maps field slots to encounter IDs180–185, hollow slots to186–191. Unused entries remain unspawned

The parent must call `south_game_reset()` on death/load/new game. It clears transient participant proof as well as local arrangements. Ordinary `south_game_enter` resets only local arrangements and preserves identity-pinned trial evidence across normal room travel, allowing F009's three supports in rooms31/32. Menus, dialogue, save/reward confirmation and death must not run normal world tick/input. The module additionally rejects every interaction/power/tick outside PLAY.

## Ferry and room geometry

The Northern town ferry NPC belongs at(208,208), with interaction/return approach(208,224). Both points were checked against the original Northern solid rectangles with radius5; no existing NPC/control lies inside its normal interaction radius. An earlier candidate(384,224) was rejected because it intersects the expanded timber stack.

Southern return explicitly enters old room22 spawn0, then calls the existing `game_region_warp(208,224)` bridge. No old Northern spawn index is added. South town ferry entry is room30 spawn0=(240,284).

Exact room/spawn registries are in `assets/southern_region/contract.json`, fixture approaches in `scene.json`, and all generated collision descriptors in `layout.json`.

- Town30 spawns0 ferry(240,284),1 field(304,32),2 rest(112,224),3 loft(80,148),4 Crown return(400,224)
- Field31 spawns0 town(240,284),1 intake(400,72),2 rest(80,264),3 hollow(80,104)
- Interiors32–37 each have spawn0=(120,132), reachable RESET at(32,132), and southern escape through x108–132/y144. Main gates are at(208,56)
- Town north passage centers x304. Field south passage centers x240. Loft/hollow/intake entrances and all NPCs are explicit marked architectural targets, never arbitrary pixels
- Actors and mirror/shade arrangements do not change movement collision or move/crush the player. The Crown's outer water corners are solid, with safe side lanes(24,112)/(216,112)

Town30 is always a sanctuary. Field31's rest anchor center is(80,248), sanctuary spawn(80,264).

## Main route and optical proof

Q22: turn the visible town demonstration mirror; collect the misplaced hood at(192,240) and return it to(192,208); report to the guide. Q23: inspect public latch(304,192), then second hinge(352,192); report to the field caretaker. These produce base79 and85 through typed atomic transactions before room34 can be entered.

Each optical state has two binary mirror positions and one binary shade. Room34 uses only its first mirror. At most four cardinal segments and two fixed mirrors are traced. Rays query actual raw scene solids, without the movement foot expansion; the first blocker wins. Repeated mirror/direction states terminate, and the bounded loop cannot hang. Current beams and blocked endpoints are always previewed.

- Room34: eastward source(32,56), mirror(112,56), tagged water lens(112,104). A manually turns the mirror; only selected REFRACT_BEAM at the energized lens awards Q24 bit1
- Room35: source(32,56) crosses receiver A(80,56), turns at(112,56)/(112,104), then reaches tagged catch/receiver B(192,104). The closed shared screen interrupts the lower route; the player must open it and use both fixed pivots. Both receivers must be illuminated before selected TUNE_LATCH awards bit2
- Room36: source(32,104) turns north at(80,104), then east at(80,48), around the fixed living tree to receiver(192,48). Open the shade arm and use both opposite mirror diagonals. The spatial solution awards bit4
- Room37: the machine warns for60 PLAY updates, moves from x88 to152 over40 updates, pauses for100, and rests30 before repeating. The broad warning lane spans y76–100; side/bottom routes remain safe. Opening the right shade exposes the paused coupling to all three weapon classes. Defeat awards bit8; explicit reporting claims Q24, reopening the market and enabling direct town return

Q24 remains a prefix ledger0/1/3/7/15. Manual controls, resets, walking and emergency escape cannot synthesize bits1/2. Completed bits survive reset/re-entry/reload. Q29 opens the explicit loft market-return gate(208,64) to town30 spawn4, and room36 completion opens gate(208,112) to field31 spawn1; both remain available after re-entry. Incomplete arrangements reset safely without a mandatory timer.

## Facing-aware conversation targeting

A controller test found that the porter at(352,224) could intercept A from the third market stall's marked approach(344,224), even while the player faced up toward stall(344,208). The same interception occurred at the closer native position(343,216) because the old near test allowed a small backward tolerance.

Human NPC conversations now additionally require the target to lie in the facing cone: lateral distance must be at most forward distance plus four pixels. Manual fixture targeting and every scene coordinate/collision remain unchanged. Thus facing up at either recorded position operates the stall, while turning right from(344,224) deliberately talks to the porter. A focused regression first reproduced the failure, then verified both stall approaches and the porter's normal below/left/right/above approaches. The complete runtime suite passes14 tests with UBSan after this narrow change; no frozen controller fixture or art data was modified.

## Optional activity and identity policy

Eight field recruits use source tokens16–23 in the approved order25,28,81,83,87,89,91,93. Their marked actions are respectively two root ties; an open drain; warm shelf shutter; two connected shade panels; discovered loft handprints; ripple clue plus runnel gate; repaired awning plus quiet town clock; three returned inspection pins. Discovery0 follows simultaneous loft sightlines/Q29 READY; discovery1 follows Q28 READY plus the explicit quiet clock. Neither discovery requires accepting the equipment reward, so a full bag cannot conceal a creature.

A trial begins only when the player explicitly inspects a marked trial sign with the chosen, selected active individual. The trial holds its exact roster slot and instance_id, not a family OR-mask. Switching to another copy cannot contribute proof; choosing a new participant at a sign clears the previous proof. Three distinct drawn fixtures are required. Repeating one cannot count twice.

- F009: two field supports and one loft support
- F010: left/middle/right drainage caps, with overflow closed
- F028: three town receivers using right/left/right demonstration configurations
- F029: three cloths with the moisture gauge in its middle safe band
- F030: three pressure plates with left/both/right shade configurations; the walking loop stays open
- F031: three paired catches while the worker's shade lane is open
- F032: three loft cords with left/right/both sightlines open, approached from opposite ends
- F033: reveal each of three current sources with B, then remove the indicated leaf catch with A
- F034: three shielded beacons with left/both/right cloth-protection settings
- F035: three ore sockets with aligned dial states0/1/2

Only successful environmental proof calls `southern_trial_complete` with the same slot, instance ID, exact family, local key1 and typed source. The save worker stages the trial/training floors atomically and idempotently. No evolution is automatic, no base copy is cloned and no prior generic field-aid/reward bit suppresses these sources or training. All environmental controls and objectives remain available after the Crown.

## Evidence and limits

`tests/test_south_game.py` links the unchanged production runtime/art/creature/equipment/save/quest modules with synthetic input/render bridges and loads the authentic Northern revision3 fixture. It verifies actual runtime handlers rather than granting Southern completion flags directly. The fixtures are host-module tests, not controller-native acquisition evidence.

The suite covers all24 optical arrangements, manual reachability to a solution from every state, reset safety, source/quest idempotence, selected-capability checks independent of command arguments, mandatory base-only route, all eight field encounters, all ten personal trials and training floors, wrong order/duplicate target/wrong instance/reset, all side quests, modal freezing, every escape, boss vulnerability for all three weapons, exact pixel collision equivalence, enemy starts, save validation and roundtrip. Per-pixel outdoor camera scans include the extra ranged-enemy regional OBJ slots and active trial completion markers. A separate conservative superstate combines every possible conditional actor position, including mutually exclusive conditions: the town upper bound is20 and the field upper bound16 for every one-pixel camera alignment. Actual journey-state maxima are15 and13 respectively; the largest interior maximum is12.

The art suite independently checks unchanged palette, emitted pixels, odd-x camera rows, all144 critical radius-five BFS points, all24 beam arrangements against raw solids, source/archive caps and deterministic generation. Both suites are rerun with the final sources; UBSan is enabled for the runtime pass. Controller playthrough, native frame timing and actual ROM obtainability remain parent-owned acceptance gates.

Final isolated ARM runtime object: 12,500 code bytes,772 read-only data bytes and48 EWRAM bytes. It has no IWRAM section; the parent corrected the old *game.o linker wildcard to explicit historical hot-module names, so the current linker source routes all of south_game.o to ROM. Final linked-map and native timing evidence remain integration checks. Exact final source sizes and SHA-256 hashes are recorded in the accompanying chapter evidence after the final test pass. Art payload is859,332 bytes, including844,800 bitmap bytes,9,728 sprite bytes and3,962 collision lookup bytes.
