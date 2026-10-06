# Magma Mountain runtime handoff

Developer-only implementation notes and puzzle spoilers. This is not player preview media. Work belongs only to the active `adventure-legends-magma` checkout; no delivered Southern/S3 workspace was edited by this module's author.

## Implemented surface

- Eight connected rooms38–45: two480×320 outdoors and six240×160 interiors
- Q30/Q31 guaranteed base31/34 before mandatory gates; manual public lessons do not require a companion power
- Q32 sequential heat, pressure, combined pin, regulator/report route
- Five optional gear quests33–37 plus the journal-visible Listening Stones commission
- Seven typed first invitations and four deterministic repeat branch encounters, routed through the real reviewed admission/quest APIs
- Fifteen instance-bound trials, including independent branch keys and exact form32/35 third-tier prerequisites
- Actual movable12×12 insulated bricks/baffles/shoes; engine-foot collision, every-pixel swept movement, push/pull/side-slide and live-enemy occupancy rejection
- Original pale stone/plaster town art, cool ceramic channels, moss and shallow-water pockets, work canopies, purpose-specific interiors, six NPC work poses and a courier who walks the repaired route

Definitions, instance/source policy, save codec, gear, global UI, command art and engine integration are owned by the other integration components. This runtime never writes SRAM directly or allocates a second save snapshot.

## Rebuild and evidence

Run:

- `python assets/generate_magma_region.py`
- `python tests/test_magma_art.py`
- `python tests/test_magma_game.py`

Both focused suites pass: 5 art tests and 16 production-linked runtime tests. The art suite includes deterministic regeneration, frozen178-entry palette, exact generated source bytes, camera odd/even alignment, every static spawn/exit/clue/reward/enemy approach, Southern lift placement and actual-pixel movable-state proof.

The runtime suite links real `magma_quests`, catalog, equipment and save modules. It imports the frozen Southern minimal8 fixture, performs authored interaction/field/push inputs, checks all first invitations, all quests/discovery, all15 trials and tier3 evolution, duplicate sources, branch repeat rewards, prospective admission at excess88, full160 grandfathered refusal, save round trips, modal pauses, actor rejection, independent combat tokens, and trial identity resets.

Host positions are deliberately warped to already-checked approaches. These are synthetic module tests, not a native-controller acquisition claim. Boss tests use explicit supplied Q4 damage to exercise windows/ledgers, not minimum-loadout balance evidence. Parent native controller/performance/stack-high-water acceptance remains authoritative.

### Exact geometry results

The C proof includes the production `magma_puzzle.inc` and real `magma_art.c`. It raster-floods240×160 engine-foot space for each legal arrangement, derives move edges from every reachable valid grab approach through the actual every-pixel simultaneous player/object sweep, then proves reachability to the goal without RESET. Every free player pixel in every reachable arrangement retains the ordinary walking exit.

| Room | Legal spatial arrangements | Swept move edges |
|---|---:|---:|
|40, workshop trial brick|29|92|
|42, heat brick|31|92|
|43, baffle + pressure shoe|1056|6448|
|44, brick + relief baffle|1056|6448|

An early test found isolated top-edge pixels in the original wall lip. The top of each internal divider now joins the fixed top wall. The proof passes with final geometry. No corner-phase, half-tile teleport, reduced foot radius or test-only collision exception is present.

### Measured isolated budgets

- Art payload860,026 bytes, including10,496 sprite bytes in ROM
- Generated data chunks≤29,998 bytes; every art JSON<30KB
- Permanent new OBJ allocation0; existing streamed regional slots only
- Isolated ARM7TDMI `magma_game.o`: `.text`3624, `.text.rom`15916, `.rodata`1344, `.data`5, `.bss`76 bytes
- Regional mutable state81 bytes, well below1KiB
- Largest individual ARM compiler stack frame120 bytes (`magma_puzzle_move`), next112 (`magma_game_input`)
- No heap, framebuffer, permanent IWRAM section or per-frame roster scan

Object section totals and individual compiler stack frames are not whole-frame timing or stack-high-water measurements. The final merged linker map must confirm ROM placement and total budgets.

## Entry, arrivals and parent bridges

Southern room30 requires Q24 CLAIMED. Its proposed lift actor is(288,248), with arrival(288,264),32+ Manhattan pixels from every existing Southern actor/fixture and clear under exact radius-five collision. The parent owns rendering and interaction at this old-world point. Return enters existing Southern spawn0, then warps to(288,264).

Final save spawn masks:

- Room38:0=(240,284),1=(304,32),2=(80,152),3=(112,264)
- Room39:0=(240,284),1=(80,104),2=(400,72),3=(80,280)
- Rooms40–45:0=(120,136) only
- Spawn3 is the rest anchor for38/39; spawn2 is an ordinary doorway return, not an anchor

`magma_game.h` is the callback contract. Room lookup, spawn lookup, visit/gate/entry, selected-active field dispatch, enemy descriptors, collision/fingerprint inputs, exclusive grab input, transient reset, actor/overlay/journal rendering and weapon/command hooks are exposed.

Parent responsibilities:

1. Route region38–45 before older regional fallbacks; use `magma_art_rooms` including odd-X bitmap copies
2. Add all three `magma_game_collision_inputs` words to exact collision invalidation; heat/brace/art animation does not alter solidity
3. Call `magma_game_input(pressed,held)` before ordinary movement/roll/weapon while PLAY; if it owns input, stop those paths. It already calls `game_region_warp` after a slide to synchronize fixed-point coordinates
4. Freeze world updates during dialogue, saving, picker/menu, reward/evolution UI, death and hitstop using the parent early returns
5. Call `magma_game_reset` after death/load/new game. Ordinary `magma_game_enter` resets the room arrangement while preserving pinned multiroom trial evidence
6. Provide `game_magma_actor_overlap(x,y,radius)` over live enemies. The runtime checks every point of prop/player sweeps, not only the destination
7. Use the existing streamed20 regional actor slots; no new permanent OBJ offsets
8. Add172 `MG_*` Japanese labels from `assets/magma_region/dialogue.json` to global UI and expose journal tab8

### Independent damage identities

`magma_game_action_begin(channel)` returns a nonzero serial for a new action in that channel:

-0: melee action
-1: arrow slot0
-2: arrow slot1
-3: companion cast

Store the serial with the action. Weapon bridge takes class,point,damage,channel,token; command bridge takes point,damage,token and uses channel3. A new weapon action cannot clear a companion's hit, one arrow cannot clear another, and aim/retarget must retain the cast token. Call the begin hook once on successful start, never once per hit or frame. Regulator damage is resolved neutral-phase Q4; pin44 rejects companion damage.

Enemy encounter credit namespace is exactly220–231:39 slots0–4→220–224;41 slots0–1→225–226;42 slot0→227;43 slot0→228;44 slots0–1→229–230;45 regulator outcome→231. There is no sixth field enemy. Reserved232–239 remain unused.

## Native input guide

A grabs a nearby physical prop; a fresh D-pad press slides it one24×18 resting cell. Player and object move together through a checked sweep. A or B releases. A rejected destination leaves the state and player unchanged. Props cannot enter x≤32/x≥208 side lanes or y≥128 entrance/reset lane. Opposite-side grabs allow pulling away from a wall. One press does one step; held arrows do not auto-repeat.

-38: Ressa(160,176), jar initially(144,232), cool shelf(192,232), hood(224,208), workshop entrance(80,136), lift(240,268), rest(112,248)
-39: handwheel(192,192), guiding footprint(240,192), invite(288,192), grotto(80,88), intake(400,56), rest(80,264)
-42: selected STORE_HEAT at brick(48,68), move below the cold wall at y104 and then right to receiver(192,68)
-43: baffle from(96,86) to(144,32), shoe from(168,86) to(144,68), selected PRESS_WEIGHT at brace(168,104)
-44: charge brick at(48,68), route to(192,68); baffle to(144,32); selected PRESS_WEIGHT at(168,104); strike exposed pin(192,104) with ordinary sword/lance/bow
-45: start(120,112), either diversion handle(32,80)/(208,80), exposed coupling(120,64)

Ordinary south exits are x108–132 at y143+, with DOWN. They never require a companion. RESET is(24,136). Forward gate controls are(216,56).44 shortcut(216,136) returns to39 once prefix7;45 exit(208,136) returns to38 after regulator completion.

The regulator cycle is60 warning→36 moving sweep→90 vented pause→30 recovery. Shape-marked lanes preview exactly the sweep region; side lanes and entry are safe. At half HP the next warned lane alternates without speeding up. A diversion persists through undamaged cycles, allowing ordinary walking and waiting. After any successful coupling-hit window it clears at the next warning; the next damage window needs another deliberate diversion. Parent native testing found and removed an earlier unhinted speed/roll gate.

## Optional stories and invitation clues

- Q33: workshop tag(48,64); shelf selector(88,64), hood(128,64), practice set(168,64). Low+closed, high+closed and wide+open are independent successful arrangements. Then return to Nemi to finish and claim
- Q34: grotto arrows(48,64), bypass(80,64), public bowl(112,64), report to Tavi(208,80). The refuge remains visibly supplied
- Q35: physically slide field screen128→176 at y264; open outside return door(104,112); report to Sen. The opened doorway really leads to40; its return-window control(208,136) goes back to39
- Q36: town vibration board(384,208), workshop hook(48,96), both clearances(80,96)/(112,96), report to Pell(384,176). Visual pulses provide a silent confirmation
- Q37: field ribbon(368,264) after Q32 prefix3; gallery hood(72,112); carry reusable seed tray through ordinary travel to field landing(336,240), report to Omi(304,232). Death/load clears the carried transient; hood remains retryable
- Listening Stones: Tavi conversation or illustrated sign(48,96) accepts the same request. Arrange left/right baffles(80,96)/(144,96), return clapper(176,96), invite at grille(192,112). READY does not depend on gear capacity

First invitations:

| Token/form | Two visible clues and manual proof |
|---|---|
|16/37|Paired nibble gaps and displaced tray; A tray(72,208), then shelter(104,208) in39|
|17/40|Three ripple arrows and chimney-like catch bowl; bypass/public basin, then catch bowl(144,64) in41|
|18/43|Two stamped samples and basket snout; inspect(144,96)/(176,96), then basket(192,112) in40|
|19/46|Split ribbon and sheltered hood shadow; hood(392,208) to open state, then shelter(424,208) in39|
|20/95|Broad tracks and bubble lip; inspect(272,96), brush spring(304,96), then invite at that lip|
|21/97|Moving moss and frayed line; two hooks(56,112)/(88,112), then moss(120,112) in40|
|22/99|Five droplet dents and visible grille eyes; complete Listening Stones, invite explicitly at grille|

Branch extra bases use second shelters/bowls/baskets/hoods:37 at(80,232) in39,40 at(176,64) in41,43 at(160,112) in40,46 at(424,240) in39. The first retained evolved branch reveals a blue second-source cue. One A prepares the marked place; another explicitly invites a real new individual. Each subsequent encounter must be prepared again. No repeat one-time source/event/gear/XP/bond credit. Missing-branch coverage remains admissible at excess88; a duplicate with no coverage gain is refused without durable changes. Historical full160 collections remain playable/saveable but cannot be promised new physical capacity.

## Trial evidence and design interpretation

Left sign chooses key1, right sign key2 for the actual selected active individual. Town signs(432,280)/(400,280); field(208,248)/(272,248); interiors(24,112)/(216,112). Their facing-aware approaches cannot accidentally press the nearby RESET plaque. Each step has a distinct tagged target and room; branch order/face/environment rules are in the production table in `magma_trials.inc`.

Only one trial is pinned, as slot+instance_id. Switching active copies prevents credit; switching back may resume. Choosing another participant/trial, explicit RESET/restart, death or reload clears incomplete proof. Ordinary room transitions preserve evidence but clear local props/heat. Completed trial bits/floors and source receipts remain durable.

For the form32 “one brick, three uses” trial, the same physical workshop brick performs all three outputs at96/168/192,y86, with the actual sink rest144,86 and manual cooling control144,112 between outputs. Return it to source48,86 for reheating. Final gallery inspection72,112 proves the multiroom endpoint. This is the explicit implementation interpretation of the proposal's40/44 trial: it avoids magically carrying room-local heat across doors while retaining one actual reusable brick and three independent outputs.

All trial completions call the reviewed exact family/key/source/slot/identity API. Source receipts, quests, gear and capacity rules are not duplicated here. The source policy still checks exact from-forms31/32,34/35 or branch bases, prerequisite key1 for each third tier, context and training floors before committing.

## Cached sweep rendering correction

Every actual stage2 clock decrement now increments only `magma_game_revision`, forcing the parent bitmap cache to redraw the newly damaging sweep position. The slower32-update ambient clock no longer controls hazard visibility. Cadence, collision geometry and stage transitions are unchanged. The focused regression seeds all36 damaging positions, observes actual production overlay rectangles, checks damage and revision advance together, and proves frozen non-PLAY states leave both timer and revision unchanged. Draw calls never mutate them.


## Final integration note

The final D runtime pins and controller evidence are in `../VERIFICATION.md` and
`../magma/`. Those results supersede this handoff's early native-acceptance status.
Deferred rest now queues exact anchor proof inside the frozen save presentation;
see `../SAVE5.md` and `../evidence/deferred-anchor/REVIEW.md`. It does not weaken
validation or bypass the ordinary transactional writer. The linked regulator
sweep is refreshed every damaging position, the diversion remains latched through
undamaged cycles, and the completed repair screen survives travel/death/load.
