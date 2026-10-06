# Magma Mountain: Kilnstep and the Breathing Kiln

Developer-only proposal, revision2, 5 October 2026. This document contains discovery and puzzle spoilers. Do not reuse it as a player preview.

## Decision and exact scope

Build a mountain community whose everyday work is keeping useful heat moving safely between pottery, gardens and public shelters. The chapter's verbs are move, shelter, charge, brace and release. Its visual identity is a bright terraced settlement with cool springs and moss pockets, not a succession of red fire arenas.

The agreed allocation in Southern chapter design section 10 is authoritative: F011–F012 (31–36), F013–F016 (37–48), F036–F038 (95–100). That is 24 forms in nine new families. The full chapter is one intended 24-form release after the required architecture proof, not a silently reduced 18-form release.

- Eight areas38–45; eight global quests30–37
- Two guaranteed teaching companions, seven typed ecological sources, four deterministic extra-base encounter sources
- Five optional global sidequests and one additional journal-visible optional discovery commission, six optional side stories in total
- Fifteen new evolution edges, fifteen family-qualified trials, signatures43–66,41 new inherited learnset pairs
- Six gear sidegrades, no new field capabilities, no newly enabled legacy third tiers, no legendary or command12
- After independent native acceptance:65 cumulative forms,30 families,46 areas,38 global quests,31 gear;34 retained individuals suffice for every branch alternative

This design implements zero runtime forms. The delivered Southern S3 cartridge is5,858,700 bytes. This proposal is not an enabled runtime chapter. Inspected IWRAM end0x03006D28 leaves728 bytes to the0x03007000 code boundary. New regional code gets zero additional IWRAM.

## Invented culture and ecological architecture

Kilnstep residents work in rotating public heat shifts: a potter, gardener, spring keeper and lift keeper share a plainly drawn schedule board. A “first warm cup” is an invented civic welcome, offered from the same public basin to residents and visitors. The narrative tension is a practical disagreement about a malfunctioning heat distributor, not a culture represented as secretive or primitive. Nobody is a caricatured “volcano tribe.”

Working NPCs:

- Ressa, lift and public-heat keeper: demonstrates portable insulated jars, then owns the main repair report
- Nemi, potter: needs different drying arrangements for thick and thin vessels and explains the marked shelf shapes
- Omi, terrace gardener: protects a seedbed from the misplaced exhaust and notices creature tracks
- Tavi, spring keeper: follows the cold-water route and teaches the visual vibration marks in the grotto
- Sen, walking courier: needs a continuous low path, not a speed challenge
- Pell, instrument repairer: maintains the public clapper and shows why a counterweight should clear both sides

Use broad pale-ochre roof terraces, indigo-purple stone edges, cream plaster recesses, teal ceramic water channels and restrained saffron heat indicators. A thin coral-red hot edge is a hazard accent. No lava-screen tint; bright sky and green pockets remain visible. Town roofs step with the slope, with large simple chimney cowls and working courtyards. Dark waist-high boundary walls make cultivated pockets legible; gates are wide and clearly marked. Cool tube interiors have pale ceiling openings and blue reflected pools, with dry walking ledges. Indoor and outdoor foreground silhouettes must differ at native240×160.

The architectural reference is the relationship between small cultivated plots and dry-stone boundaries documented by UNESCO for Pico's vineyard landscape. Its real cultural and agricultural history belongs to Pico; the game does not reproduce its buildings, names, costumes or claim authenticity. Use that planning relationship as one reference for an independently drawn fantasy mountain town. [UNESCO, Landscape of the Pico Island Vineyard Culture](https://whc.unesco.org/en/list/1117/), accessed5 October2026.

For natural space, use the contrasting tube walls, former-flow marks and openings described by the USGS as a way to avoid generic circular caves. The game's insulated bricks, heat transfer, safe marked ledges and regulator are explicitly invented. They are not representations of safe behavior around real lava tubes or active volcanoes. [USGS Hawaiian Volcano Observatory, Volcano Watch: Lava tubes,30 August1996](https://www.usgs.gov/news/volcano-watch-lava-tubes), accessed5 October2026.

No borrowed Nintendo assets, traced map arrangements, sacred diagrams, real scripts used as decorative texture, or “authentic” invented translations. Character names are working names pending Japanese UI review. Botanical and animal designs are fantasy; phase is a combat relationship and Yin/Yang is independently authored. Only forms39 and48 change polarity on their explicitly chosen branch; no morality, gender, day/night or region is inferred from that change.

## Connected eight-area chapter

| Room | Space | Activity and connection |
|---|---|---|
|38|Kilnstep Commons,480×320|Lower lift from Southern30, upper field road, Potters Walk door, rest and public heat lesson; Ressa/Nemi/Pell and a visible branch-encounter notice board|
|39|Pumice Terraces,480×320|Two interlinked garden loops, resting landing, Cloudwell door and clear main-kiln entrance; Omi/Sen, guaranteed brace lesson, ecological pockets|
|40|Potters Walk,240×160|Indoor workshop with real drying bays, sample shelves, clapper rig and a courtyard return window; connects directly back to town|
|41|Cloudwell Grotto,240×160|Cool spring ledges, manually accessible bowls and visible grille niche; returns to the field without a power check|
|42|Intake Ledger,240×160|First movable insulated brick plus cold dividing wall; heat companion action is required for the receiver; returns to field|
|43|Breathing Vault,240×160|Movable baffle and pressure shoe; weight companion action seats a brace; returns to42|
|44|Return-Flue Gallery,240×160|Heat brick, relief baffle, brace and visible weapon-release pin; opens the short field return; returns to43|
|45|Caldera Bell,240×160|Regulator encounter with a changing vulnerable coupling, useful room machinery and safe side lanes; returns to44, then town after completion|

### Main narrative steps and guarantees

Entry is Southern Q24 CLAIMED plus an explicit conversation at the reopened landing. It inherits earlier entry gates but requires no old Core ending, optional regional creature, optional gear or evolution. The lift always has a return conversation; it is not a new inventory ticket.

1. Q30 teaches hand movement of a cool insulated jar and an A-operated hood. Ressa grants31 Coalcoil plus source25/item20 as one staged transaction. Coalcoil supplies STORE_HEAT. Neither prerequisite requires that power
2. Q31 teaches a public handwheel and a clear pedestrian route in39. The player guides34 Shardibex along it, then explicitly invites it. Shardibex supplies PRESS_WEIGHT. No Earth phase inference, old Kohaku or evolved goat is required
3. Both CLAIMED establish MAGMA_READY and permit room42. The journal explains how to assign and select either retained companion even when the party was full. Main puzzle checks actual selected active capability, independent of equipped battle command
4. Q32 is the four-stage monotonic prefix0/1/3/7/15: heat receiver42, pressure brace43, combined routing and weapon pin44, regulator45 plus report. Each passed stage permanently opens the forward threshold; resets never erase that stage
5. Caldera completion diverts the useful heat to the public kiln, restores a garden exhaust and changes courtyard activity. A visible travel lead points toward the later Underwater chapter without enabling its rooms or content

Every mandatory interaction uses base31 and34 plus the protected starter sword. Lance or bow can substitute at the release pin and boss. The new bow is a sidegrade, not a unique key. Gearless/base-only acceptance must be tested. All other species, evolutions, late trials and side stories remain accessible after the ending.

## Finite movable-object rules

These are actual floor props with spatial consequences, not menu choices that merely move decoration. Move one insulated brick or baffle by a cardinal tile using a nearby grab/slide action. A clear short arrow previews the destination. Pulling away from a wall is supported. Reject occupied, solid, actor-overlapping, boundary-lane and invalid target positions; the player never gets pushed or crushed. Objects have a clear heavy-material base and separate blue grab affordance. No permanent weight, physics integration, inventory pickup or consumable is added.

- Room42: the heat source can charge the insulated brick only at its marked input resting place. The player routes that brick around the cold wall to the distant receiver. Simply walking to the receiver or placing a cold brick cannot progress
- Room43: baffle placement directs the relief outlet away from the pedestrian route. Only then can selected PRESS_WEIGHT seat the marked brace. A wrongly placed pressure shoe visibly opens the bypass and prevents the objective, not the exit
- Room44: first route and charge the brick, seat the relief baffle and use the base weight companion. Once both readouts show their shape-stamped ready state, a release pin extends. An ordinary sword/lance/bow hit on the exposed pin finishes the room. It can be approached for short-range sword use and shot from the safe lane
- Field actions test exact target kind, selected active form, facing/range and unobstructed geometry. A failed targeted attempt consumes the field input but no battle cooldown/resource. Do not fall through and attack the NPC or props
- A latched heat state belongs only to that room's insulated brick, not to the player's inventory or all Fire forms. The next room has its own source and starts with its own uncharged brick. No secret carried state crosses room transitions
- The bottom walkway and both side lanes remain permanently unoccupied. Proposed native room entrance(120,136), reset plaque(24,136), south exit(120,152); use radius-five and real swept-movement proof before accepting these coordinates. Interior furniture stays above y120, with side lanes atx≤40 andx≥200
- RESET clears incomplete prop/charge/brace arrangements to the taught start. Reentry/death/reload also restores a safe arrangement and entrance. Completed Q32 stages and committed sources/trials remain intact
- Free emergency return never grants a stage. Menus, conversation, saving, reward confirmation, death and paused state freeze room input/animation clocks

The supplied validator exhausts finite abstract7×5-cell micro-layouts for rooms42–44 with reversible prop moves, selected heat/weight actions and a release pin. It proves924/11,648/24,180 reachable abstract states respectively have a solution without reset, and every player/prop arrangement retains a walking-only exit. It does not validate final pixel solids, actual input timing, sprite overlap or the native ROM. The implementer must faithfully re-prove the final authored maps; the abstract micro-layout is a prototype contract rather than permission to claim complete route QA.

## Regulator encounter

The antagonist is an over-tightened public heat regulator with three articulating ceramic vanes and a plainly visible brass coupling, not an evil culture or a giant palette-swapped monster. Inactive outer kiln structures frame a real machinery space; do not place the same enemy in several empty chambers.

Proposed PLAY-update loop:60 warning →36 sweep →90 vented pause →30 recovery. A broad shape-marked lane previews the sweep; two side lanes and the entire entrance ledge remain safe. The player operates a reachable baffle handle to divert the pause's jet and expose the coupling. All three mundane weapon classes can hit it; existing phase rules affect efficiency but no companion/polarity/gear creates an immunity key. Companion commands can deal their normal damage only during that same vulnerability window. At half health the next sweep chooses the opposite visibly announced lane; no speed surprise or hidden timer.

Start from12 hearts/192Q4 HP for the prototype; tune against real minimum-loadout sword/lance/bow runs. One coupling ledger prevents repeat damage from one swing/projectile/command. Reset on death restores boss HP and unclaimed room progression, not completed quests or retained companions. Avoid screen shake that hides the warning. Design counts and damage values are balance proposals, not measured play length or difficulty.

## Six optional side stories

Five use existing global quest slots. The sixth uses its already-budgeted discovery/source contract; it must still have a normal journal card and clear objective feedback.

| Story | Steps and consequence | Reward |
|---|---|---|
|Q33 Pots Without Cracks|Nemi's thick, thin and decorated practice vessels need three different shelf/baffle arrangements; read shape tags, arrange each, report. Finished pots appear in the public court|source26/item37 Kilnweave Mail|
|Q34 The Last Cool Cup|Tavi's upper basin steals a creature refuge's seep. Follow visible arrows, open the side bypass, fill the public bowl without emptying the refuge. Both remain visibly supplied|source27/item53 Pumice Boots|
|Q35 A Clear Way Home|Sen's low route is blocked by a fallen screen. Move it to the marked storage bay and open the return door from outside. Sen later uses the route|source28/item67 Bricklayer Belt|
|Q36 The Missing Chime|Pell's public clapper hangs on the wrong counterweight. Follow vibration marks, use the public hook, clear both swing sides. A silent visual pulse also confirms the repaired chime|source29/item85 Quietnote Ring|
|Q37 A Seedbed Above the Smoke|Omi's wind ribbon points to the wrong hood. Read it, redirect the upper hood, carry a reusable seed tray through the clear route and report. Garden foliage appears without changing collision|source30/item5 Terrace Sword|
|Listening Stones|Accept Tavi's illustrated grotto request, arrange two sound baffles by shape, return the clapper and inspect the revealed grille. The face was visible from the start; invitation is explicit|typed source M_FIELD_6, form99 Dripurchin; no global quest ID or equipment reward|

Q33 mask7; Q34/Q35/Q36 masks3; Q37 mask7. Q37 becomes available after Q32 prefix3, when the upper gallery is accessible. No mandatory speed grade, random drops, real-time window or rare weather. Each READY activity stays retryable if a reward cannot be stored. Discovery READY never depends on accepting a gear reward.

Listening Stones lives in region_flags[19] bits0 request,1 baffles/niche,2 clapper/reveal, legal prefixes0/1/3/7. M_FIELD_6 can be claimed only at prefix7. Journal states derive as UNSEEN if0, ACTIVE if1/3, READY if7 and source unclaimed, CLAIMED if the source is claimed. Tavi and the illustrated sign provide the same request entry, so skipping dialogue cannot strand it. Reading the sign alone grants no later discovery or creature.

## Discoveries and creature roles

The complete24 form cards are in MAGMA_CREATURE_CARDS.md and the same machine-readable rows in magma_allocation.json. Every form has separate silhouette, locomotion, command geometry/timing, field utility, exact acquisition/evolution and level/bond/trial contract. These are requirements for original art and actual handlers, not proof those assets exist.

Every source has two native-visible clues plus an NPC/journal fallback:

- Tuftpika37: paired nibble marks + displaced seed tray; Omi points to the sheltered plot
- Chalklung40: three ripple arrows + a moving sponge chimney behind the dry niche; Tavi names the catch bowl
- Orelet43: two shape-stamped loose samples + a twitching snout under the basket; Nemi describes the inspection shelf
- Ashkite46: a fluttering split ribbon + a hood-shadow shaped like its shelter; Omi points out the secondary wind path
- Screepeek95: broad tracks + a bubbling shallow spring lip; the nearby illustrated brush sign explains the manual action
- Mossmarch97: moving moss cushions + a frayed line guide; Nemi gives the safe two-hook hint
- Dripurchin99: five droplet dents + the visible face/vibration marks at the grille; the Listening Stones card names the baffle rests

Initial field encounters are one-time typed invitations. Branch extras are separately encountered actual base individuals, never reconstructed from seen/obtained history. After the first branch is retained, the source visibly reveals a second shelter/bowl/basket/hood and its exact action. The first new receipt records two distinct retained individuals. The encounter remains deterministically repeatable for a player who evolves both into the same branch; further copies grant no repeat one-time XP/bond, item or source reward. They obey the terminal-opportunity admission rule below and never replace a party or stored instance. Physical capacity alone is insufficient.

### Trial and evolution behavior

All trials explicitly select one active participant at a nearby sign, pin its roster slot plus instance_id, and prove distinct environment objects. Changing to another copy cannot combine proof. Normal room travel preserves the selected participant's partial multiroom evidence; choosing a new participant, explicit trial restart, death or reload clears incomplete evidence. Menus freeze it. Each completion supplies the named level/bond floor only to that participant, atomically with its trial bit. Greater earned values are preserved. This removes arbitrary grinding; it never fabricates a trial during migration or evolution.

F011/F012 key1→mask1 and key2→mask2, key2 prerequisite1. Their tier2 edges require1; tier3 edges require3 and CALDERA_OPEN. Branch families have two independent keys1/2 with masks1/2 and no prerequisite. Each branch requires only its own key, level26/bond45 and MAGMA_READY. Both may be learned before choosing, but neither implies the other. F036–F038 use key1/mask1. Every evolution needs sanctuary plus explicit target confirmation. A branch-choice screen shows both named outcomes and unmet conditions; legacy single-target calls return AMBIGUOUS for valid branch bases and do not choose.

Tier2 trial floors26/45 and tier3 floors32/60 are starting design values. Initial recruits use active-party median clamped24–30 and bond20; a full party stores the new creature. Three-stage families inherit all commands and capabilities. Branches retain their base capability and signature; no alternate branch command leaks into the sibling's learnset. No new phase multiplier or polarity combat bonus is introduced.

## Equipment and honest capacity

All six items use existing parameters and are optional. Exact stats/source mappings are in magma_allocation.json. Sources25–30 append; every old ID/source relationship remains fixed. Item IDs20,37,53,67,85,5 were absent from the inspected catalog and are proposed reservations, not enabled definitions. Test actual derived clamps and tradeoffs rather than assuming every numeric change matters. Body, boots, belt and ring are represented; the bow and sword offer existing-weapon choices while the lance remains useful for narrow release-pin/boss approaches.

Normal full collection grows from21 individuals/25 gear to34 individuals/31 gear, comfortably within160/48. Main teaching reward Q30 is mixed gear+creature: stage both, then commit or leave everything READY unchanged. The original repeat-capture plan had a real softlock: enough same-branch duplicates could permanently consume slots needed by later companions. A FULL/retry response could not recover it without a release feature. The new required integration gate reserves all72 final terminal-instance opportunities, permits at most88 excess copies, and checks every candidate capture or coverage-losing evolution before commitment. Viable coverage is maximum matching of actual retained individuals to reachable terminal targets, never obtained history. Missing-family/missing-branch bases remain admissible from every safe state, while only choices that consume the last reserved opportunity are refused. See MAGMA_COLLECTION_SAFETY.md for the exact rule and all-choice-order proof. A pre-existing legal over-budget legacy collection remains valid and preserved, but admission alone cannot restore its lost completion capacity. Do not claim retry will fix it or invent release/replacement.

## Implementation and acceptance handoff

Start from the eventual accepted Southern source, not its lagging live build. First prove the two isolation gates, additional branch/tier handling and terminal-opportunity admission, then add a separate Magma module, explicit map/source/event registries, one guaranteed recruit and a movable-prop prototype. Continue with the complete chapter and24 forms. Do not enable six late targets in a partially validated catalog merely because their IDs were reserved.

MAGMA_IMPLEMENTATION_CONTRACT.md gives exact namespaces, persistence and test gates. validate_design.py checks this developer plan; it deliberately does not call catalog generation or edit enabled.json. A passing design validator is not a shipping ROM, a playable count or a migration proof. Release requires independent exact-ROM controller evidence, all65 form history with34 actual retained individuals, all three weapons, old-save fixtures and corruption/interruption matrices, native frames and visual review at240×160. Physical GBA testing remains a separate claim.

### Additional per-form polarity integration gate

The proposed polarity changes on forms39 and48 are explicit developer design choices. Current catalog validation still assumes one polarity per family, even though target mutation supports a per-form value. Before these branches can be implemented, review bounded per-form current polarity overrides while freezing every released polarity and the identity-lock tuple. Do not bypass the family guard or silently remove either design choice.
