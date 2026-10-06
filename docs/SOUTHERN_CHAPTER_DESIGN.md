# Southern chapter and full-roster expansion contract

Developer brief for Adventure Legends · 5 October 2026

Status: **proposal only**. Read-only inspection of `/workspace/scratch/33ed39a77941/adventure-legends-northern`. No runtime, catalog, GitHub, Library, or release changes are authorized by this document. Keep player-facing locations, creatures, solutions, and rewards as discoveries rather than announcing this spoiler-rich brief to the player.

## 1. Recommendation and decision gates

Build **Sunlace Anchorage**, a bright original island harbor, its **Frondshore Commons**, and the linked **Sunwell Conservatory**. The central activity is arranging *light, shade, and clear sightlines*: turn a bounded mirror, move a hinged shade screen, and split or interrupt an optical path. This is spatial planning with visible consequences, not Northern rail carts, Reedhaven's linked-pool sequence, or an empty combat arena repeated for each creature.

The bounded slice proposes **8 areas, 10 new families, 20 new forms, 8 typed quests, 6 gear sidegrades, and 1 new field capability bit**. Two families are guaranteed teaching recruits. Six are ordinary field recruits and two are visibly hinted uncommon field encounters. All ten retain their locked **ordinary** rarity; encounter presentation does not silently reclassify them as rare or legendary. No third tier, branching evolution, legendary form, or ability 12 is enabled in this slice.

Before implementation, approve three separate architecture changes:

1. A family-qualified local trial namespace with frozen legacy APIs and exact revision-specific validation; retain the 24-byte instance wire format
2. Explicit new-area/event/acquisition registries; do not extend `room*6` or borrow historical generic reward bits
3. A full-roster authoring-schema revision for more than 63 unique signature abilities, plus later explicit multi-edge evolution APIs. These are identified now, not silently “fixed” by weakening current checks

Suggested implementation order: historical codec fixtures and trial APIs → regional persistence/entry → one teaching recruit and two prototype optical rooms → remaining main loop → remaining creatures/side content → independent native acceptance. Work in a separate checkout based on the eventual exact Northern release candidate. Do not mutate the frozen Northern checkout or publish while approval is pending.

### Inspected baseline and honest counts

Read: `docs/NORTHERN_CHAPTER_DESIGN.md`, `docs/ROADMAP.md`, `docs/SAVE5.md`; creature catalog/schema/identity lock/enabled manifest/generator/validator; equipment catalog and headers; Northern regional contract; `creatures.c/h`, `save5.c/h`, `progression.c`, Northern quests and OBJ layout.

- Locked identities: 128 forms in 60 families
- Current catalog actually contains **22 designed rows**, including disabled legendary 121. Older prose saying “12 designed” or “11 enabled” is historical and must not be copied into current accounting
- Manifest revision 3: **21 enabled forms, 21 abilities, 10 evolution edges**
- Parent's N5 controller evidence: **21 obtained forms in 11 retained family instances, 30 areas, 22 regional quests, 19 gear items**. This brief did not rerun that controller suite and is not additional gameplay evidence
- Proposed addition: 20 specifications in 10 families. If approved, implemented, ordinarily acquired, reloaded and verified, this slice would yield **41 obtainable forms, 21 retained family instances, 38 areas, 30 quests and 25 gear items**. Until then it adds **zero** implemented/obtainable forms
- Legendary 121 and ability 12 remain disabled. Other 121–128 identities remain disabled until their own design and acceptance gates

Inspection pins:

| File | SHA-256 |
|---|---|
| `assets/creatures/identity-lock.json` | `fe553a9d963de059e7d6c0f8647ab6a3fe736c5fdf7ca8d3b18c6dedd3292969` |
| `assets/creatures/catalog.json` | `2482d59fb138788c359942cc09ce35eab4a0cfa06351ea2f2eb6c096c8e2dffe` |
| `src/creatures.c` | `c87806fec74b550ae6b6f3846c830c1415cd031862b49786d9028f802b16a6f9` |
| `src/save5.c` | `0e374df92371da179f608671bd534331fb26bb59110c65c41e66646affba158b` |
| inspected `build/emberbond.gba` | `302316c53d6fb9dafa0ecbf9f679c9c39af3a150af3aa78398c368312e50399e` |

The checkout already has substantial tracked/untracked Northern development changes. They are the supplied baseline, not changes made for this brief.

## 2. Researched reference boundary and invented visual language

Use climate-responsive coastal planning as reference, not a collage of supposedly interchangeable island cultures. The principal architectural lens is the secular street/courtyard/waterfront relationships documented for Lamu. The game town, people, ecology, technology, names, clothing, signs and supernatural rules are invented. It is not a reconstruction of Lamu or a representation of one real community.

### Primary references, accessed 5 October 2026

1. [UNESCO World Heritage Centre: Lamu Old Town](https://whc.unesco.org/en/list/1055/) — inscription 2001; page publication date not stated. It documents coral-stone/mangrove-timber buildings, courtyards, winding streets, verandas and a working seafront. Borrow the *relationship* of shaded narrow approaches, courtyard openings and a continuous waterfront edge. Do not copy carved doors, decorative niches, mosques, named institutions or sacred iconography. Lamu remains a living Swahili town with Islamic cultural significance
2. [UNESCO: Promoting climate change adaptation and mitigation in Lamu Old Town](https://whc.unesco.org/en/Lamu_AFR/) — credited UNESCO 2023; discusses a January 2022 workshop. It describes the gently rising dune/drainage, street orientation to breezes, close-spaced shade and thick construction. Translate that into a town that rises inland, with visible rain channels and gaps for wind. This is a documented case study, not a claim that these features eliminate storm or flood risk
3. [UNESCO: Historic Bridgetown and its Garrison](https://whc.unesco.org/en/list/1376/) — inscription 2011; page publication date not stated. Its irregular street network and maritime working spaces are a secondary planning comparison only. The source also explains colonial expansion and trade in enslaved people; do not romanticize imperial emblems, plantation imagery or the garrison as a decorative tropical kit. No direct façade or cultural ornament is proposed from this reference

### Original fantasy translation

- Cream and warm yellow mineral-plaster walls; turquoise shutters; orange-red shade cloth; cool violet-blue shadows; green trees and clear shallow water
- Low stepped rectangular roof masses, simple veranda posts, courtyard wells used as civic rain collectors, open repair terraces and a plainly visible ferry landing
- Fictional quarried inland stone. No gameplay rewards for coral extraction or mangrove clearance; keep the mangrove fringe visibly alive and traversable on an existing raised path
- Secular civic imagery invented for the game: painted creature-shaped shop signs, geometric rain-gauge marks, a mechanical public shade clock and a broad striped ferry bell
- No borrowed sacred diagrams, Indigenous patterns, ceremonial masks, real script used as meaningless texture, invented “authentic” translations or generic islander costume shorthand
- Light is not coded as Yang/good and shade is not coded as Yin/evil. Neither polarity determines a species' phase, morality, gender, day/night schedule or regional origin

At 240×160, communicate architecture with broad light walls, deep door recesses and useful courtyard openings. Distinguish it from Hearthwake's gabled timber frontage and Reedhaven's roof/bridge vocabulary without claiming either reference region has a single culture. The existing Northern chapter is itself bright, not uniformly dark; the contrast is material, roof mass, vegetation and street composition, not simply increased brightness.

## 3. Eight-area progression loop

Room IDs **30–37** are proposed exact additions after 22–29; allocate only after checking the final merged registry. Never mark them by shifting `CampaignSave.room_flags` by their absolute room ID. Southern visited state uses regional byte 2.

| ID | Working space | Size target | Activity and persistent change |
|---|---|---:|---|
| 30 | Sunlace Anchorage | 480×320 | Ferry, rest, market court, guide, manual optical demonstration, first guaranteed recruit, six returning side-quest NPCs |
| 31 | Frondshore Commons | 480×320 | Branching raised path, dune cut, visible sunlit/shaded habitat pockets, second guaranteed recruit, field discoveries, rest |
| 32 | Awning Loft | 240×160 | Open upstairs workplace; hinged screens and sightline puzzle; town shortcut opens visibly |
| 33 | Chalkspring Hollow | 240×160 | Dry ledges around a shallow spring; visible drainage clues and a cave window, optional ecology/trial encounters |
| 34 | Conservatory Light Intake | 240×160 | One source, one mirror, one receiver; learn optical collision and reachable reset |
| 35 | Split-Shade Walk | 240×160 | Two receivers, one shared shade screen; solve simultaneous illumination without closing the walking return route |
| 36 | Turning-Bough Gallery | 240×160 | Route light around a fixed living tree and across two ledges using two orientable mirrors; open a permanent short return |
| 37 | Sunwell Crown | 240×160 | Telegraphed mobile lens-machine encounter; shade creates readable attack windows, then the conservatory reopens and town changes |

### Entry and mandatory dependency graph

Entry is Northern quest 21 CLAIMED plus an explicit ferry conversation. Do not require Northern optional recruits/evolutions, the old Core ending, every river quest, a particular gear item, or completion of the collection. Town entry records only its own visit and checkpoint.

1. Ferry → room 30. Manual A-operated demonstration and two clearly marked repair actions complete quest 22; this grants **79 Skimkip** before any water-lens route use
2. An ordinary walking path reaches room 31 without any companion. A public inspection latch can be released with A. Two visible latch tasks complete quest 23 and grant **85 Clipmantis** before its optional shortcuts are offered
3. Quests 22 and 23 CLAIMED unlock room 34. Journal can assign these retained companions into a full party without deleting an old member. A local notice identifies the relevant creature/action and the assignment control
4. Quest 24 follows rooms 34 → 35 → 36 → 37. Each completed stage permanently opens the next threshold; return routes remain available
5. Crown completion offers a return to town. The market's previously shaded work area opens, a damaged lens is visibly repaired, and a new travel lead appears. Optional recruits and side quests remain available afterward

**Companion-puzzle and safety invariant:** the main route requires one tagged Water refraction in room 34 and one tagged Metal latch interaction in room 35, after guaranteed recruits 79 and 85. Mirror rotation, shutter positioning, resets and safe escape are manually operable on the player's reachable side; manual controls cannot award or bypass those two companion objectives. The player can always reassign a retained stored companion from the journal at a safe accessible position, and both field actions work independently of equipped combat commands. No companion release/deletion is introduced. A manual emergency exit returns to the prior safe space without granting progression. These recovery routes must be tested, not merely described in dialogue.

Base-form Skimkip and Clipmantis are sufficient for every mandatory companion solution. Room 34 objective 1 is awarded only after a valid active companion with REFRACT_BEAM energizes its marked lens receiver; room 35 objective 2 requires a valid active companion with TUNE_LATCH to release its marked catch. Normal walking, mirror rotation, reset and return do not fabricate either success. Clipmantis is the guaranteed provider; other explicitly compatible owned tuning companions may substitute only if the target policy supports them. No evolution, old Earth press, old Fire ignition, generic “all Water creatures,” or nonexistent underwater companion is silently assumed. Field helpers consult the actually selected active companion's form capabilities and explicit target rules, not the selected combat-command slot. Ownership alone is not a claim that a stored companion is already active; journal reassignment is always available before the required action. Never make `FIELD_REFRACT_BEAM` work through a wall or on every shiny object.

### Reversible optical rule set

This is invented fantasy machinery, not a real optics simulation.

- Four cardinal emitter directions; mirrors have two clearly drawn diagonal positions; hinged shutters have open/closed states
- Beam segments stop at the first blocking surface. A receiver requires an unobstructed segment and matching drawn shape; color alone is never a clue
- At most four segments and two mirrors per authored network. Detect repeated `(node, direction)` pairs and stop a loop without hanging; invalid arrangements are ordinary puzzle states
- Mirrors are fixed in marked pivot sockets, not free-moving carts. Screens turn around a hinge; they never push the player, move an NPC, or consume equipment
- One shutter may shade a walkway while exposing another beam route. A tree blocks light even when its canopy is foreground art; the collision/source drawing must agree
- A reachable RESET plaque returns the room's incomplete arrangement to its taught configuration. Completed stage bits remain complete. Re-entry/death/reload resets incomplete arrangements and places the player on a safe entrance ledge
- Freeze the puzzle during menus, dialogue, saving, reward confirmation and death. Do not infer sunlight from real-world time or wait for random weather
- A visible “inspect path” preview shows the entire current beam and blocked endpoint. The required water-lens receiver and Metal catch use a companion glyph and explanatory prompt, distinct from manual handles and emergency exits. Failed casts consume no field resource and do not set trial/objective bits
- No mandatory timer. Optional practice may record active-play time, but free retry and all content access remain available without a speed grade

Room 35 is genuinely spatial: illuminating receiver A by closing the shared screen interrupts receiver B, so the player must use the second fixed pivot and walk around the shade edge. Room 36 adds a fixed obstruction and a two-turn route, not a longer memorized switch order. Both are enumerable finite state spaces with mechanical reachability and reset proofs.

The final lens-machine shows its facing and a broad warning arc, moves into the lit lane, then pauses. A player-operated shutter exposes its coupling. Any mundane sword, lance or bow can damage that coupling; phases change efficiency only. No immunities require a particular recruit or advanced power. Design the room around sightlines and safe side lanes, not hidden boss-control coordinates.

### Discovery language

Every hidden route has at least two mutually reinforcing clues: e.g. a broken shade pattern plus a scuffed hinge; paired claw tracks plus a visible face in a branch; a warm draft plus a moving silhouette under an awning. A nearby NPC gives a plain-language fallback and the journal preserves it. The reward must be reachable without pressing A on an unmarked random pixel.

Rare-in-presentation encounters are deterministic once their openly discoverable state is set. They remain available after leaving, dying, or finishing the chapter. There are no low probability rolls, missable clock windows, limited consumables or mandatory repeated room loading.

## 4. Locked allocation: ten expressive families, twenty forms

All names are original working names, pending naming/Japanese UI review. IDs, keys, family ownership, tier and rarity come from the existing lock. No ID is renumbered, recycled or converted from a reserved legendary.

| Family | Proposed forms and IDs | Locked future topology | Phase | Polarity | Proposed command IDs |
|---|---|---|---|---|---|
| F009 | 25 Tangleaper → 26 Boughvault | 25→26→27; 27 remains disabled | Wood | Yang | 23, 24 |
| F010 | 28 Duneroll → 29 Dunescoop | 28→29→30; 30 remains disabled | Earth | Yin | 25, 26 |
| F028 | 79 Skimkip → 80 Sailskip | 79→80 | Water | Yang | 27, 28 |
| F029 | 81 Warmcroak → 82 Bellowswell | 81→82 | Fire | Yin | 29, 30 |
| F030 | 83 Shellwaddle → 84 Vaultback | 83→84 | Earth | Yang | 31, 32 |
| F031 | 85 Clipmantis → 86 Foilscythe | 85→86 | Metal | Yang | 33, 34 |
| F032 | 87 Swaylemur → 88 Canopetail | 87→88 | Wood | Yin | 35, 36 |
| F033 | 89 Rillnewt → 90 Veilcrest | 89→90 | Water | Yin | 37, 38 |
| F034 | 91 Glimmerbat → 92 Flarefan | 91→92 | Fire | Yang | 39, 40 |
| F035 | 93 Needletrot → 94 Quillstride | 93→94 | Metal | Yin | 41, 42 |

These are two families for each of the five phases, with both polarities represented within each phase. This is intentional coverage for this batch, not a general rule deriving polarity from phase or name. Both forms in each family keep their authored polarity and inherited field actions.

### Common art and implementation acceptance

Each base/evolution pair must differ in body plan, negative space, posture and locomotion, not scale or palette alone. Require a readable face, eyes that aim or react, a breathing/idle gesture, anticipation, cast expression and recovery at native size. Grayscale silhouette review must distinguish all 20 from one another and the prior 21. Avoid literal tools with anonymous eyes pasted on, small recolored foxes, or a portrait standing in for an unreadable field sprite.

Budget four directions × four locomotion poses plus two readable cast poses per form within a reviewed shared sprite plan. Cap live power objects and per-cast enemy hits; no unrestricted particle system. Battle numbers below are **design starting points**, not implemented or balanced measurements. Creature stat weights keep tier-1 total 180 and tier-2 total 240; tune after battle role prototypes, and never claim all weights affect native combat before tracing their consumers.

### F009 · Tangleaper / Boughvault

- **Shape and motion:** small wide-toed gecko, short rounded muzzle, lifted eyes and a long coiled vine tail; alternating splayed-foot scuttle. Evolution grows a lean chest and broad *connected* leaf-like side membranes between limbs, producing a triangular gliding silhouette and a crouch–hop–settle gait. Retain its living face and single continuous body
- **Battle:** 23 Leafbound is a brief collision-swept companion sidestep followed by a narrow lateral Wood cut (16 Q4; cooldown target 90). The player is never teleported or invulnerable. 24 Canopy Arc launches a clearly previewed two-segment curved seed arc (24 Q4 once per enemy; cooldown 120), giving angled attacks with walls respected rather than a stronger straight shot
- **Field:** base GROW_ROOTS at named garden anchors; evolution additionally GROW_BRIDGE at explicitly marked spans. No arbitrary wall climbing or free glide across gaps
- **Recruit:** normal field encounter in room 31. A gecko visibly tends one torn root mat beside the walking path. Restore two marked ties with manual stakes, then interact with the companion. Neither Midori nor Tangleaper itself is required to recruit it
- **Personal trial:** restore three separately drawn root supports from different ledges in rooms 31/32; each can be reached on foot. The final composition creates a visible canopy path. Persist the completed family trial, not every intermediate root arrangement

### F010 · Duneroll / Dunescoop

- **Shape and motion:** big-eared hopping dune mammal with long hind feet, compact forepaws and a thin tufted tail. Evolution shifts weight forward onto two broad digging forefeet, raises the ear arc and lengthens the body; it runs with a low scoop–bound rhythm. This is not Kohaku's armored mass or Cairncricket's jointed insect outline
- **Battle:** 25 Ridgekick sends a short widening Earth wedge (20 Q4, bounded push of ordinary targets; cooldown 90). 26 Rampart Turn creates one short angled ridge that redirects an ordinary walking enemy into a visible side lane, then crumbles for 20 Q4; at most one ridge, no boss displacement or player-trapping collision, cooldown 120
- **Field:** UNCAP_WELL on shallow marked silt caps; evolution retains it. It does not acquire every Earth capability
- **Recruit:** room 31 dune cut, visible pawprints leading to an animal unable to reach the shaded end of a drainage lip. Open the adjacent manual drain cover, providing a dry walking route. Free, deterministic interaction
- **Personal trial:** trace three drawn drainage branches in room 33 and clear their marked caps without opening the drawn overflow shortcut first. The order is inferred from visible slopes, and RESET drains the scene safely; no pixel search or real water hazard

### F028 · Skimkip / Sailskip — guaranteed recruit

- **Shape and motion:** expressive flying-fish-like body with broad paired pectoral fins, cheek spots, short beakless mouth and a forked tail; low skim–fin-plant movement on land. Evolution opens tall connected sail fins and bends through a longer banking arc, leaving a strong V-shaped negative space. Distinguish from Keelkip's seal muzzle/flipper waddle and both Reedhaven Water shapes
- **Battle:** 27 Lens Dart fires a narrow Water bead that splits into two weak outward rays *only at its first target impact* (initial 16 Q4, secondary 8 Q4; no repeat hit on the initial target; cooldown 90). 28 Prism Wake leaves a brief clearly drawn line that divides the next eligible ordinary hostile shot into two harmless outward droplets, then ends; its endpoint makes a 24 Q4 Water burst. Maximum one line and one consumed shot, cooldown 120; no repeated projectile recycling
- **Field:** new REFRACT_BEAM on marked water-lens pivots. Base turns one beam at one fixed socket; evolution can preserve one authored lens while activating a second. Both require unobstructed target checks. No free swimming, underwater movement or generic filling implied
- **Recruit:** quest 22 in town, after the manual optics lesson and returning a misplaced lens hood. Guaranteed before room 34
- **Personal trial:** route a single beam through three separately labeled demonstration receivers across two configurations. A teacher shows the first refraction. Base command alone suffices; no evolved-command prerequisite

### F029 · Warmcroak / Bellowswell

- **Shape and motion:** squat round frog with short webbed feet, heavy eyelids and one pale warm throat pouch; slow blink and deliberate hop. Evolution broadens its hind-leg stance, develops paired connected cheek/throat folds and rears slightly before a two-beat exhale. The head remains expressive and the body continuous
- **Battle:** 29 Ember Hush applies one visible warm mark: an ordinary enemy's next attack windup is lengthened, then a 16 Q4 Fire pop occurs (boss telegraphs are not silently retimed; cooldown 90). 30 Bellows Ring has a visible expanding annulus with an empty safe center, 24 Q4 once per target at its edge; cooldown 120. This is neither a lingering Homura floor line nor Cindertray's delayed patch
- **Field:** STORE_HEAT in tagged drying cloths; evolution retains the same tag with two explicitly previewed delivery positions. Existing heat-bearing creatures can substitute for ordinary utility targets
- **Recruit:** room 33 warm rock shelf; expose a sun patch with a manual shutter and leave the neighboring wet shelter available. The frog emerges in front of the player, rather than after repeated random encounters
- **Personal trial:** use three drying stations while keeping each cloth's drawn moisture indicator in its safe band. No real-time fail timer; a wrong setting dampens the cloth and can be reset freely

### F030 · Shellwaddle / Vaultback

- **Shape and motion:** sideways-walking sand crab with two unequal soft-tipped claws, stalk eyes and a low shell arch; its eye stalks follow the player. Evolution has long raised rear legs and a high open shell vault over a visible abdomen, changing into a broad sideways strut with clear under-body space. No living coral is worn or harvested
- **Battle:** 31 Sideguard braces a narrow flank for one ordinary melee hit and replies with a 16 Q4 Earth swipe; frontal/rear exposure remains. 32 Vault Step moves that guard to one of two explicitly selected side positions and produces a 24 Q4 lateral wave after interception. It does not duplicate Kohaku's stationary general defense or Archspring's placed projectile counterweight
- **Field:** PRESS_WEIGHT on floor plates. Main-path manual handles still work; new Earth ownership is optional
- **Recruit:** room 31, beside an obviously shaded boardwalk alcove. Rotate two public shade panels so both the entrance and resting spot are shaded; the crab walks out along the resulting continuous shade
- **Personal trial:** maintain a walkable loop while holding one pressure plate and rotating two linked shutters. The solution concerns the player's access graph and shade, not cart loads. Every incorrect arrangement has a reachable return handle

### F031 · Clipmantis / Foilscythe — guaranteed recruit

- **Shape and motion:** upright thin mantis with triangular head, large aimed eyes, long forearms and four fine walking legs. Evolution unfurls broad crescent forearm foils and a longer folded abdomen, using a measured high-knee stalk. Wings are subordinate; it must not become Rivetfoil's bird silhouette
- **Battle:** 33 Pinch Window catches one marked ordinary melee strike in a narrow frontal arc, replying with a Metal pin (24 Q4; cooldown 90); clear startup prevents instant universal parry. 34 Shear Gate places two visible facing blades for one short crossing window; a target crossing between them is hit once for 24 Q4, maximum one gate, cooldown 120. Boss behavior follows existing vulnerable windows
- **Field:** TUNE_LATCH, with tagged two-jaw shutter catches. Evolution retains it. Manual levers are never removed when this helper becomes available
- **Recruit:** quest 23, room 31 public shutter inspection. Use a manual latch, inspect its second hinge and give the companion room to climb down; no Metal command is required to earn Metal
- **Personal trial:** release three visibly paired catches without closing the worker's access lane. Reset handles lie outside every catch. No requirement to win a parry timing challenge

### F032 · Swaylemur / Canopetail — hinted uncommon encounter

- **Shape and motion:** long-tailed tree mammal with round forward-facing eyes, large plain ears, small hands and a flexible tail with two large leaf-like tufts. Evolution hangs its taller body below a raised tail loop, with long forearms and a pronounced counterbalancing step. Original anatomy, no claim of a specific country's folklore
- **Battle:** 35 Sapling Feint leaves one brief grounded decoy that diverts one eligible ordinary enemy's approach, then folds (no boss taunt; cooldown 90). 36 Canopy Exchange places two short-lived decoys whose visible connecting line can redirect one approach toward the safer endpoint; no player teleport or invulnerability, a 16 Q4 Wood snap only after activation, cooldown 120
- **Field:** REEL_LOAD, narrowly applied to tagged awning cords rather than arbitrary objects. The same old capability keeps its authored target rules; it does not become a universal “move thing” bit
- **Recruit:** solve the openly shown loft shade pattern, then follow fresh handprints and a visibly moving tail to room 31's branch niche. An NPC explicitly mentions the same pattern. It stays there once revealed, with a normal interaction prompt
- **Personal trial:** reopen a three-part canopy shade route from opposite ends without obscuring the caretaker's exit. The third tie is visible from the first screen; no hidden interaction coordinate

### F033 · Rillnewt / Veilcrest

- **Shape and motion:** low newt with a broad smiling mouth, four widely planted toes and a long flat tail; swaying knuckle crawl. Evolution raises a transparent continuous dorsal veil, develops foreleg frills and walks with lifted elbows, contrasting with the frog's crouching hops and fish's skimming fins
- **Battle:** 37 Rill Fork sends a short Y-shaped Water fork, 12 Q4 per branch with one hit cap per target and a small slowing effect; cooldown 90. 38 Veil Curl wraps that fork into a clearly drawn crescent with a gap, catching targets approaching from a side while preserving an escape lane; 24 Q4 once, cooldown 120. Neither command pulls the player or ignores walls
- **Field:** REVEAL_CURRENT and FILL_BASIN at tagged civic water displays. These are existing capabilities, not a reason to duplicate Reedhaven's mandatory pool-link puzzle
- **Recruit:** trace an already visible ripple/leaf trail through room 31's shallow runnel and manually open its jammed shade gate. The creature is seen before recruitment and can be revisited
- **Personal trial:** identify the three sources feeding a cloudy runnel using current previews, then clear their visible leaf catches. An incorrect catch is harmless and reversible; no underwater access required

### F034 · Glimmerbat / Flarefan — hinted uncommon encounter

- **Shape and motion:** fruit-bat-like mammal with large ears, short bright muzzle, linked wing fingers and a tucked tail; quick flap–hang pauses. Evolution fans its broad wing fingers in a shallow W silhouette and lands on long hind toes before a slow wingfold. Distinguish it from Fuuri's insect wings and metal birds
- **Battle:** 39 Warm Echo marks one visible target for the next ordinary weapon hit, causing a delayed 16 Q4 Fire follow-up once; short expiry and one mark prevent stockpiling. 40 Paired Echo links two separately aimed target marks; striking one triggers a weak follow-up on the other only with line of sight, total budget 24 Q4, cooldown 120. No infinite chains, friendly fire or through-wall targeting
- **Field:** IGNITE on shielded signal braziers. Its roost and encounter do not depend on real night or Yin/Yang
- **Recruit:** a torn awning casts a conspicuously wing-shaped moving shadow near room 32. Complete the visible awning repair, then select “quiet shade” on the town's manual shade clock; the bat hangs at a clear interaction point. Quest 28's NPC offers the clue but its claim is not required
- **Personal trial:** light three shielded line-of-sight beacons while keeping the cloth screens between them protected. Fixtures are marked, RESET restores a wrong arrangement, and the game does not model or reward burning the town

### F035 · Needletrot / Quillstride

- **Shape and motion:** long-snouted tenrec-like mammal with small focused eyes, rounded ears, short legs and a low quill crest; quick nosing trot. Evolution grows long rear legs and an open fan of separately readable metallic quills above a slim living body; it rises, pivots and settles with a different center of gravity
- **Battle:** 41 Needle Bank fires one Metal spine with one wall ricochet, 20 Q4 maximum once per target; collision-swept segments and visible reflection, cooldown 90. 42 Quill Return fires a three-spine fan that retracts to the creature's current unobstructed lane; outbound/return share a per-target hit budget of 24 Q4, at most three bounded objects, cooldown 120
- **Field:** DRAW_ORE from tagged shallow inspection sockets. Never extracts coral or invents magnetic effects from an item's damage phase
- **Recruit:** room 33, a plainly visible metallic footprint trail leads to three loose inspection pins. Return them to their matching drawn tray slots manually; the animal noses out of its hiding ledge to help
- **Personal trial:** use three differently aligned ore sockets to reveal a route diagram while leaving its central walking gap open. No rail carriage, randomized buried item or permanent inventory consumption

### Acquisition and evolution accounting

- Guaranteed typed quest recruits: 79 via Q22; 85 via Q23
- Deterministic ordinary field recruits: 25, 28, 81, 83, 89, 93
- Visibly hinted uncommon field recruits, still ordinary rarity: 87, 91
- Ten enabled proposed edges: 25→26, 28→29, 79→80, 81→82, 83→84, 85→86, 87→88, 89→90, 91→92, 93→94
- Recruit at active-party median, clamped to level 18–24, bond 20; no automatic party replacement
- Personal trial completion explicitly grants the *participating, same-family retained instance* a level/bond floor sufficient for its listed evolution, preserving any greater earned values. Floors are design compensation, not fabricated historical XP or proof the trial was done
- Evolution targets: F009/F028/F031 level 20, bond 40; F010/F029/F030/F033/F035 level 22, bond 45; F032/F034 level 24, bond 45. All require their own completed trial, Southern-ready context, sanctuary and explicit player confirmation
- Trials are open after recruitment and the two teaching quests; none requires its evolved form. Their bounded completion gives sufficient floors, so normal collection is not stalled by repeated combat or resting
- The player explicitly chooses the participating roster instance before a personal trial. Persist the trial and training floor on that same instance, whether active or stored afterward. No union of one copy's trial and another copy's level/bond
- Base abilities remain learned and may remain equipped through evolution. The new signature becomes learnable; do not silently replace equipped commands. Both forms remain in collection history; do not clone the base into storage

## 5. Eight quests and six equipment sidegrades

Proposed quests 22–29 use existing two-bit states and 16-bit objectives. All require the Southern entry gate and town visit. INACTIVE has no objectives; ACTIVE is incomplete; READY/CLAIMED exactly match the authored mask. Rewards become authoritative only after a durable successful save.

| Quest | Purpose | Mask | Claim/reward and visible change |
|---|---|---:|---|
| 22 | A Window for the Harbor | 3 | Manual optics lesson + returned lens hood; recruit 79; source 19/item 4; demonstration window opens |
| 23 | The Quiet Hinge | 3 | Two public latch tasks in field; recruit 85; inspection walkway opens |
| 24 | Open the Sunwell | 15 | Four dungeon stages, monotonic prefixes 0/1/3/7/15; Crown opens and return route becomes visible |
| 25 | Cool Market | 7 | Arrange shade at three staffed stalls; source 21/item 36; stalls remain open |
| 26 | Rain at Two Doors | 3 | Repair two clearly drawn rain-catch connections; source 23/item 66; courtyard rain indicators work |
| 27 | Clear Delivery | 3 | Find and open two safe, signed walking approaches for a delivery; source 22/item 52; porter uses the route |
| 28 | The Missing Awning | 3 | Find a torn-panel clue and install its visible replacement; source 24/item 84; exposes a useful creature hint |
| 29 | A Welcome Upstairs | 3 | Clear two independent sightlines into the loft store; source 20/item 12; usable town/loft shortcut |

Personal evolution trials are small authored environmental activities recorded on the participating creature, not ten additional quest IDs and not ten copied arenas. Journal can show their names, prerequisites and missing objectives without giving each one a global typed quest slot. Partial progress resets safely and is explained; completed trials persist. Field recruits use their own typed source ledger below.

### Proposed items

Only existing bounded stat dimensions and sword/lance/bow mechanics are used. No new inventory keys, consumables, currencies, underwater kit or hidden gear abilities are implied.

| Item ID | Name/type | Stats relative to empty/base gear | Reason to choose / cost | Source |
|---:|---|---|---|---:|
| 4 | Shadecutter Sword | attack +0, reach +1, stagger +1 | Interruption with a little reach; gives up Reedguard attack and Ropeguard reach | 19/Q22 |
| 12 | Sunlace Lance | attack +0, reach +4 | Safer narrow spacing; gives up Copperleaf attack/stagger and Quay defense | 20/Q29 |
| 36 | Breezewall Mail | defense +3, HP +0, speed −2 | Guard with lighter movement penalty than Hearthscale; no HP bonus | 21/Q25 |
| 52 | Softsand Boots | roll reduction +4, speed −4 | Shorter roll recovery/cooldown parameter within current semantics, at walking-speed cost; not a free upgrade to Surestep | 22/Q27 |
| 66 | Raincatch Belt | HP +4, power reduction +1 | Small mixed reserve/cooldown option; less HP than Woven Belt | 23/Q26 |
| 84 | Springpin Ring | stagger +2, speed −4 | More stagger at a real movement cost; gives up Steady defense and Resonance cooldown | 24/Q28 |

All unlisted stats zero. These IDs are unused in the inspected equipment table; recheck after merging. Keep all old ID/source pairs byte-identical. Every proposal is within existing per-item bounds. Review *derived clamps and combinations*, not just the table: a speed penalty can disappear at an existing clamp, and added stagger must actually affect eligible enemies. Equip comparison must show true derived numbers. Equipment cannot be required to solve a chapter puzzle or damage its boss. Existing attack snapshots, busy-state equip locks, no-heal-on-equip and protected starter fallback remain intact.

Current 19 + six = 25 bag records if all collected, well below 48. No forced discard. Q22's creature and gear are a single staged transaction: full inventory/roster leaves it READY with no claimed bit, no success dialogue and no duplicate companion. Main-path progression must allow the user to resolve a genuinely full custom roster/bag using existing supported management; do not overwrite a member or claim that a nonexistent release API is available.

## 6. Trial architecture: explicit family-local identities

### Why the current global model must stop here

`CreatureInstance.trial_flags` is a 16-bit wire field at instance offset 14. Current flags are 1,2,4,8,16,32,64,128,256,512. The validator enforces a single one-hot mask per family, global uniqueness and aggregate mask 1023. Six global positions remain, while this proposal needs ten new family trials and the locked catalog has 60 families and 68 evolution edges. Consuming the final six then improvising is not a plan.

**Recommendation: retain the same 16-bit field, interpret future flags through an explicit family-qualified, revisioned registry, and freeze the old unqualified API.** A family is already unambiguously determined by the immutable form identity. No new instance bytes or remapping of old masks is needed.

### Data policy and proposed APIs

Introduce a reviewed ROM policy table conceptually containing:

`{family_id, local_trial_id, wire_mask, introduced_content_revision, allowed_source_ids, allowed_from_forms, prerequisite_trial_mask}`

- `family_id` is the immutable locked family, never an enabled-table index
- `local_trial_id` is a stable authored key within that family; 0 is invalid. Treat `(family_id, local_trial_id)` as the trial identity, not the numeric mask alone
- `wire_mask` is exactly one nonzero bit ≤32768. Reject the full-width input before narrowing or shifting. Never derive it with `1 << family_id`
- Distinct trial keys within the *same* family must map to distinct bits. Same numeric masks across *different* families are permitted only by explicit registry rows
- Evolution edges refer to their owning family and an explicit required mask/list of qualified trial keys. The exact same family must own source, target, trial and acquisition/training evidence
- Each family has an exact revision-specific allowed mask. Unknown bits, unknown trial keys, unknown families, disabled forms and unreviewed source/edge associations fail closed

Proposed new functions, names illustrative:

- `creatures_mark_trial_qualified(instance, family_id, local_trial_id)` — validate the instance, resolve its exact immutable family, require qualifier equality, look up an enabled exact pair, validate prerequisites and set only the mapped one-hot bit. Return failure with no mutation otherwise
- `creatures_has_trial_qualified(instance, family_id, local_trial_id)` — same family check; no raw-mask boolean shortcut
- `creatures_trial_allowed_mask(form_id, content_revision)` — internal explicit lookup for validators, not authorization for callers to award all bits

The mutation function does **not** prove an environmental trial, synthesize objective completion, choose a different roster copy, set floors or issue rewards. A typed chapter transaction proves the authored source, participant ID, prerequisites and actual object outcomes, then stages trial+floor+source state and commits once. A caller can never present F009's trial key as F010's evidence, even though both happen to map to bit 1.

### Preserve exact old API semantics

Freeze a separate **legacy trial map**:

| Legacy family | Accepted unqualified flag and preserved wire mask |
|---|---:|
| F001 | 1 |
| F002 | 2 |
| F003 | 4 |
| F004 | 8 |
| F005 | 16 |
| F006 | none/0 |
| F007 | 32 |
| F008 | 64 |
| F025 | 128 |
| F026 | 256 |
| F027 | 512 |

- Existing `creatures_mark_trial(instance, flag)` remains a legacy-only wrapper. On old families it accepts only the exact original one-hot value, including after a later evolution in that family. It still rejects zero, combinations, overflows and all wrong-family values
- On a new family it always fails, even if raw bit 1 is that family's local trial. Old code accidentally passing HEARTH to F009 cannot award the F009 trial
- Existing `creatures_family_trial(form_id)` keeps its scalar legacy meaning: original mask for the above owners, 0 for F006/new families/unknown forms. Do not quietly repurpose it into a union or return a reused new-family mask
- Add explicit APIs for multi-trial queries. Migrate new chapter callers to those APIs rather than changing what old callers mean
- Keep `CREATURE_TRIAL_MASK=1023` as a named legacy mask or provide a source-compatible alias. It is not a global validity mask for new families

### Exact revision-4 trial allocation

The ten Southern families F009,F010,F028,F029,F030,F031,F032,F033,F034,F035 each receive local trial **1 → wire bit 0x0001**. Their distinct semantic names are the ten personal trials described above. This is legal only through the new family-qualified table; a raw value of 1 is insufficient context.

Existing families acquire **no new allowed trial bits in revision 4**. Their recorded bytes remain unchanged. F006 stays zero. Third forms 27/30 remain disabled and do not receive an automatic second trial.

For later, separately approved third tiers:

- New linear-three families may use local trial 2 → wire bit 0x0002, requiring the first trial too, so the reviewed tier-3 edge requires mask 0x0003
- Existing F001–F005/F007/F008 may use a newly approved second local key → wire bit **0x0400** (1024), while preserving their original first mask. The tier-3 edge requires original-mask OR 0x0400. Reuse of 1024 across these families is deliberately family-qualified
- F006's eventual first/second trial can use 1/2 only in its future revision; it must remain mask 0 in historical revisions and revision 4
- Branch families need two separately named trial keys/options, not a tier-3 mask or a global flag. Each branch edge binds its own key; selecting one edge does not consume or falsely prove the other. Detailed branch API is below
- At most 16 persistent trial achievements per family is the explicit limit; this roster needs at most two for its fixed topology. Reject a seventeenth trial or duplicate same-family bit at generation time

### Do not confuse contextual identity with tamper resistance

A valid CRC save is not proof of historical play. The goal is strict semantic consistency and corruption/implementation-error detection. A 16-bit value cannot encode its external causal source by itself; the family mapping and typed source transaction are what prevent accidental cross-family grants. Do not advertise cryptographic provenance or relax malformed old-bank rejection because the current catalog now knows a reused bit.

## 7. Content revision 4 migration and exact historical whitelists

Keep **wire version 5**, bank A 0x0200, bank B 0x1A00, bank size 6144, used allocation 5056, every offset, 24×160 records, CRC and last-byte commit semantics unchanged. Write content revision **4** only after acceptance. Header reader must accept exact revisions `{1,2,3,4}`, not `revision <= current`, `revision >= 3` or a general current-catalog fallback.

Every input bank is first validated under its **own immutable revision policy**, then decoded/migrated into current runtime state. Only thereafter may current policy validate it. A newer catalog's expanded learnset or local-trial masks must not retroactively make an old bank valid. Blocking, startup scanning and incremental old-bank scanning must use the same policy data and equivalent checks.

### Form and command whitelists

| Revision | Exact enabled form set |
|---|---|
| 1 | 1,2,4,5,7,8,10,11 |
| 2 | revision 1 plus 13,14,16 |
| 3 | revision 2 plus 19,20,22,23,73,74,75,76,77,78 |
| 4 proposed | revision 3 plus 25,26,28,29,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94 |

Use exact lists for instances, seen and obtained. All other forms, notably 3,6,9,12,15,17,18,21,24,27,30,95–128 where not otherwise listed, remain rejected. Zero still means an entirely empty record.

Historical per-form learnsets and their unlock levels are frozen:

| Forms | Permitted nonzero command IDs and minimum levels |
|---|---|
| 1 | 1@1 |
| 2 | 1@1, 5@12 |
| 4 | 2@1 |
| 5 | 2@1, 6@12 |
| 7 | 3@1 |
| 8 | 3@1, 7@16 |
| 10 | 4@1 |
| 11 | 4@1, 8@20 |
| 13 | 9@1 |
| 14 | 9@1, 10@15 |
| 16 | 11@1 |
| 19 / 20 | 13@1 / 13@1,14@16 |
| 22 / 23 | 15@1 / 15@1,16@17 |
| 73 / 74 | 17@1 / 17@1,18@18 |
| 75 / 76 | 19@1 / 19@1,20@18 |
| 77 / 78 | 21@1 / 21@1,22@20 |

Revision 1 commands are 1–8 only; revision 2 is 1–11; revision 3 is 1–11 and 13–22. Revision 4 is 1–11 and 13–42, still subject to the exact form/level table. Ability 12 is invalid in every one of these revisions. An allowed global command ID does not make it learned by another form. Selected-command validity, no duplicate equipped command, optional empty unselected slot and all old equip semantics remain unchanged.

For the new pairs, base signature is available at level 1; the evolution retains that base command and adds its listed new signature at the listed evolution minimum (20/22/24). These exact rows must be immutable revision-4 policy, not inferred from neighboring IDs. Old forms receive no new commands in revision 4.

### Historical trial policies

- Revision 1: F001=1,F002=2,F003=4,F004=8; reject every other bit or family
- Revision 2: above plus F005=16,F006=0
- Revision 3: above plus F007=32,F008=64,F025=128,F026=256,F027=512
- Revision 4: all preceding masks unchanged; exact ten Southern families each allow local wire bit 1 only

Allow zero or a subset of that form/family's authored mask under the historical rules; do not impose new “evolved forms must prove every historical trial/bond” conditions on old records which the released validator did not require. The old validator checks evolved minimum level, learned commands and family mask, while some causal trial/floor evidence is enforced by typed Northern quest claims. Preserve this distinction. For new Southern trial/recruit claims, specify their exact evidence separately and enforce it for the same retained instance.

A CRC-valid revision-1 Homura with mask 0x0401 remains invalid, even if a future third tier uses 0x0400. A revision-3 form 25 or old form equipped with ability 23 remains invalid. Revision-3 bit 1 on F008 remains wrong-family evidence, even though revision-4 F009 legitimately uses bit 1.

### Equipment and quest whitelist contract

- Revision 1 wire equipment allocation is all zero under its historical reservation reader; migration installs only protected starter sword/source 0. It is not a normal revision-2 item reader
- Revision 2 item IDs: **1,2,9,10,17,18,33,34,49,50,65,81,82**, sources 0–12 with their existing exact mapping
- Revision 3 adds IDs **3,11,19,35,51,83**, sources 13–18, exactly as current
- Revision 4 adds IDs **4,12,36,52,66,84**, sources 19–24 with mapping 19→4,20→12,21→36,22→52,23→66,24→84
- Validate seen bits as well as live records and source bits against revision. Zero rank, quantity one, unique IDs, flags, bag references, protected bag 0 and all padding remain exact
- Revision 1 quest reservation remains all zero
- Revision 2 allows quests 0–10 and only its existing variables/region/anchor bits
- Revision 3 allows quests 0–21 and exactly current Northern contracts
- Revision 4 allows quests 0–29; all variables remain as before (only 3 and 9 may be 0–3). Southern incomplete mechanisms are transient, not extra quest variables
- Keep Q0–21 masks/source links/retained-family requirements exactly unchanged. Add Q22–29 masks and source links explicitly; do not use an “all new IDs allowed” range without row definitions

### New typed acquisition ledger; preserve old generic rewards

Important inspected behavior: creature reward IDs 5–128 are historically valid general one-time API rewards, and saved generic reward bytes are not restricted to the currently used 5–11. Therefore “unused” bit 12 is not safely free historical storage. A legal old save may contain it. Do not reinterpret it as a Southern recruit claim, reject it retroactively, clear it, or let it consume a newly assigned source.

Use new, revision-gated regional source bits instead:

- Q22/Q23 CLAIMED are the authoritative one-time sources for guaranteed recruits 79/85
- Region flags byte **8**, bits 0–7 are typed field-recruit claims for forms **25,28,81,83,87,89,91,93**, respectively. Bits mean exact source transactions, not generic species seen
- Each transaction stages `creatures_grant(..., reward_id=0)` into the snapshot plus its new typed source claim. The existing API's repeatable-zero route is only the inner mutation; the new typed source transaction makes this world acquisition one-time
- Check the typed source before granting, require its authored gate/visited location, reject a duplicate source claim, and keep claim+owned instance+obtained history together through save failure/retry
- Do not alter or newly depend on the old generic reward ledger for any Southern source. Preserve all its bytes on old-save migration, including legal unusual historical bit patterns
- A claimed source requires one retained valid instance of its exact family and obtained history for an enabled form in that family. Storage is valid; active party membership is not required. No release API is introduced
- A source can be unclaimed while a creature is observed. Seen is discovery, not recruitment. Do not infer a claim from seen/obtained bits alone
- Partial clue state may use separately assigned discovery bits below; never reuse a claim bit for “noticed tracks”

### Rooms, region bytes, anchors and contexts

- Revision 4 enables exact rooms/spawns only: town 30 spawns 0 ferry,1 field,2 rest,3 loft,4 return; field 31 spawns 0 town,1 conservatory,2 rest,3 hollow; interiors 32–37 spawn 0. Coordinates must be authored and collision-verified before acceptance
- Region byte 2 bits 0–7 correspond exactly to rooms 30–37; bit 0 required for every other Southern visit
- Anchor byte 2 bits 0/1 correspond to room 30/31 rest; each implies its visit. No other new anchor bits in revision 4
- Every Southern visit requires North Q21 CLAIMED, Sky-clear and the inherited prerequisites; historic visits remain gated after returning elsewhere
- Rooms 34–37 and historical visits there require Q22/Q23 CLAIMED. Room 35 requires Q24 objective 1; 36 requires prefix 3; 37 requires prefix 7. The current room requires its visit bit. Room 32/33 remain optional and reachable without evolved companions
- Proposed discovery byte **18** bits 0/1 store the two durable uncommon-encounter reveals. Each has an exact source/location prerequisite; bit 0 requires loft pattern completion and bit 1 requires the awning setting. Partial arrangement is not saved
- Bytes 3–7,9–17,19–31 remain zero in revision 4. Regional byte 8 and byte 18 are validated as explicitly typed source/discovery data, not generic visit bytes
- Derived creature context adds SOUTH_READY=0x0040 from Q22 AND Q23 CLAIMED and SUNWELL_OPEN=0x0080 from Q24 CLAIMED. Existing bits 0x0001..0x0020 retain exact meaning. These values never enter `CampaignSave.chapter_flags`; its 0x08 remains ENDING_SEEN

### Preservation and rejection tests

Required immutable inputs: published revision-1 controller SRAM, revision-2 all-eleven controller SRAM, and the final controller-earned/rebooted Northern revision-3 all-21 save, each pinned to exact source ROM/hash. Record the final N5 fixture only after its release candidate is confirmed; this brief does not invent a fixture hash.

For revision 2→4 and 3→4 normal fixtures, the complete payload at offset 32 onward must remain byte-identical after re-save; only header revision/generation/CRC/commit changes. Revision 1 retains its existing starter-equipment and resume-normalization migration exception. No load grants a Southern creature, XP, trial, item, source bit, visit, quest, anchor or discovery. No implicit migration write. Legacy v2/v3/v4 SRAM decode retains existing policy and does not overwrite old banks.

New adversarial coverage must include: every historical form with every new command/trial bit; forged revision numbers with valid CRC; unknown content revisions; wrong qualified family even with the same numeric local mask; combined/zero/overflow trial inputs; same-family duplicate key/mask; legacy mark on new families; evolved/base records with historical exceptional valid states; independently mismatched retained trial/floor across two copies; new quest/source history without ownership; wrong typed-source family; source/reward collision fixtures with historical generic bits 12–128 set; new discovery without prerequisite; room32+ shift errors; visits after moving back to town; bogus item seen/source bits; all invalid snapshots rejected before any durable write.

Preserve interruption/readback coverage at every durable write position for old→4 migration, one field recruit, Q22's mixed creature/gear bundle, each trial and evolution, and a final Crown reward. Retry must commit the same staged state, never a second companion. Test both banks corrupt, one corrupt, generations wrapping and exact-half-range tie behavior. Complete host, ASan/UBSan, incremental-budget and native controller validation are required; a schema pass alone is insufficient.

## 8. Comparison: wider globally unique persisted trials

A wider representation is viable only as an explicit new wire version. Widening the C member alone is forbidden.

| Model | Capacity and costs | Assessment |
|---|---|---|
| Keep global u16 | 16 bits total; only 6 remain | Cannot support even this 10-family proposal; reject |
| Global u64 | +6 wire bytes ×160 =960; 64 global bits | Still insufficient for 68 distinct evolution-edge trials plus legendary/other trials; not the long-term answer if global uniqueness is kept |
| Global 128-bit | +14 wire bytes ×160 =2240; 128 global trial IDs | Enough for 68 evolution-edge trials +8 legendary trials with headroom, but new serializer/layout and additional RAM/scratch required |
| Family-local u16 | 16 per family; existing record/bank unchanged | Recommended for fixed 60-family roster, with qualified API and frozen per-revision policies |

Concrete wider-wire fallback: wire **6**, explicit **38-byte** instance record replacing the old 2-byte field with 16 bytes, 160 records =6080 bytes. Keeping other logical blocks at their current total would use **7296 bytes** (5056+2240), so choose two **8192-byte** banks at **0x4000 and 0x6000**, ending exactly at 0x8000 and preserving all existing v5/legacy bytes below 0x3200. This is a proposed layout, not permission to start writing it.

A naturally aligned C instance would likely become 40 bytes, not 38; confirm with static assertions/compiler reports. Runtime roster growth could be 2560 bytes while wire growth is 2240. The 8192 bank's remaining 896 padding bytes are *smaller* than the current 1088-byte temporary packed staging area; the current in-place streaming algorithm cannot simply be copied. Re-prove scratch overlap, backwards encoding and old-bank instance-ID indexing, and measure every save step again. A second whole-bank stack allocation is not acceptable.

Migration under wire 6 must decode every old version/revision with the exact policies above, translate each old family/mask to its immutable global trial ID without fabricating unset achievements, and preserve all old SRAM banks. Append new global IDs only after the original ten; never reinterpret an old mask as another trial. A malformed old family/mask must fail *before* translation. New readers select valid v6 first, then fall back to exact v5/older decoders; old ROM downgrade synchronization remains unsupported and must be explained if exposed.

Global 128-bit trials may be preferable if future gameplay needs many cross-family achievements on a single individual. No such requirement exists in this fixed topology. Family-local u16 is smaller and preserves exact old bytes, provided its API and revision contract are treated as the architecture rather than an informal bit reuse trick.

## 9. Other full-roster blockers found during inspection

### Unique signatures versus max ability ID 63

The authoring validator simultaneously requires a distinct signature ability for every designed form and `max_ability_id=63`. Thus 128 forms cannot satisfy the current schema even if trials are solved. Revision 4's proposed 20 abilities (23–42) fit, but do not defer the architecture decision until ID 64 fails.

Propose **authoring schema 2**, retaining every old stable identity and command ID, raising the authoring command ceiling to **255**, which fits the existing saved command byte. Plan exactly **128 distinct signature IDs** for the final roster: existing 1–22 including disabled 12, Southern 23–42, future signatures 43–128. IDs 129–255 stay unassigned unless later deliberately reviewed. This is an explicit schema/policy change, not a wire-width change or permission to enable any ID.

Retain separate immutable schema-1 validation for archived catalogs and all old revision-specific command whitelists. Audit generator bounds, ROM count constants, signed casts, UI name tables, dispatch switches and learned-command checks. Do not replace IDs with array indices. Every enabled signature still requires a real handler, animation and role; shared low-level primitives are fine, blank handler aliases are not.

The ROM `CreatureForm.learnset_offset` is u16, but the separate reviewed `CreatureFormPolicy.learn_offset` is u8. The bare fixed topology with inherited signatures needs about **209 learnset pairs** (including 121's existing extra Water command), which currently fits u8 offsets; the advertised 128×8 upper bound is 1024 and does not. Expand policy offsets to u16 before any table offset exceeds255, or impose a reviewed stronger bound; never truncate silently.

### Branches and third tiers

Locked topology: **12 linear-three families, 12 branch-three families, 20 linear-two families, 8 ordinary singles, 8 legendary singles**, totaling 128 forms and **68** directed evolution edges. Runtime `creatures_evolution(from)` returns only the first edge and catalog validation currently rejects duplicate `from` values. This is correct for the enabled linear slice but does not implement the locked branch graph.

Before the first branch family is enabled, add explicit bounded enumeration and target choice, e.g. `creatures_evolution_count(form)`, `creatures_evolution_at(form,index)`, and `creatures_can_evolve_to(instance,target,context,sanctuary)` / `creatures_evolve_to(...)`. The legacy single-target APIs must retain behavior for all released forms and return an explicit ambiguous/no-single-edge result for a future branching base rather than silently choosing the first branch. Never repoint an old edge or permit cross-family/merging/cyclic graphs. Target, qualified trial, inherited learnset and capability superset must match an exact reviewed edge.

Third-tier enablement must add exact tier-3 stat totals (285) rather than the current `tier==1 ?180:240` rule, per-tier capability policy rather than indiscriminate `tier>1` assumptions, and explicit legacy companion mappings for forms3/6/9/12 so story ownership/traversal survive. Legendary enablement must review the current ordinary-only rarity check, use exact legendary IDs and stat total330, and preserve the one-active-legendary rule. These are later gated changes, not justification to relax ordinary current validation.

### Capability budget

Current field bits0–24 remain byte-for-byte unchanged. Proposed Southern bit25: **REFRACT_BEAM**. This is a genuinely new interaction, with a bounded optical handler and tagged target semantics. Result:26 of32 bits used, six remain.

Reserve, do not enable, candidate categories for future review: bit26 deliberate submerged traversal/pressure interface, bit27 lava-safe *tagged* conduit interaction. Bits28–31 stay unassigned. Water phase is not swimming permission; Fire phase is not lava immunity. Reuse existing tags only for the same action on explicit supported targets. Every higher-stage form must retain base field capabilities. Do not collapse old tags or derive tags from phase/polarity to recover capacity.

Full-roster capability groups need not match number of species. Distinct creature silhouettes, command timing, geometry, movement and battle decisions provide variety while several companions can honestly uncap the same marked well. Shared utility must not make their whole combat/animation design identical.

## 10. Bounded route to exactly 128 obtainable forms

This is an allocation and acquisition-topology plan, not 128 completed designs. Every listed future family still needs its own specification, art and acceptance. Do not enable the whole table at once.

| Milestone | New forms | Exact allocation | New families | Cumulative forms/families |
|---|---:|---|---:|---:|
| Current N5 candidate | 21 | F001–F008 partial; F025–F027 complete | 11 | 21 /11 |
| Southern slice | 20 | 25,26,28,29; F028–F035 complete (79–94) | 10 | 41 /21 |
| Magma chapter | 24 | F011–F012 all six forms31–36; F013–F016 all12 forms37–48; F036–F038 six forms95–100 | 9 | 65 /30 |
| Underwater chapter | 24 | F017–F020 twelve forms49–60; F039–F042 eight forms101–108; F045–F048 singles113–116 | 12 | 89 /42 |
| Regional return A | 15 | Dormant3,6,9,12,15,17,18,21,24,27,30; F043–F044 forms109–112 | 2 | 104 /44 |
| Regional return B | 16 | F021–F024 twelve forms61–72; F049–F052 singles117–120 | 8 | 120 /52 |
| Legendary gates | 8 | F053–F060/forms121–128 | 8 | 128 /60 |

All 128 form IDs appear exactly once in the resulting obtainable set. Return A deliberately completes existing lineages after new regions, instead of packing all late evolution requirements into the Southern onboarding. Return B adds branches/singles to previously visited towns and visible return paths; it is not sixteen recycled arena missions.

### Acquisition graph shape and finite collection

- Each of 60 families has one discoverable initial acquisition root. Existing four story roots and seven released regional roots retain their exact routes
- Every one of the 68 locked evolution edges has an explicit from/to, qualified trial, minimums, context, sanctuary and confirmation gate. No evolved form is a zero-effort generic fallback spawn
- Twelve branch families need both branches reachable in one save. Supply **two separately encountered base individuals per branch family**, with the second visible bounded encounter unlocked by choosing the first branch. No cloning a historical base, irreversible exclusive choice, random breeding grind or unlimited capture farm
- Additional branch-copy sources use 12 typed bits, with exact family/source gates and clear journal directions. A player may defer either evolution; acquiring the second does not reset the first
- Full final collection therefore needs **72 retained individuals** if all twelve branch alternatives are retained (60 initial family individuals +12 second branch individuals), within160. Collection history records all128 forms as these individuals evolve; it does not require128 simultaneous live instances
- Each root is a guaranteed story/quest interaction, visible ecological encounter, or clearly hinted deterministic rare encounter. Rarity is discoverability/presentation unless its immutable lock says legendary
- Allocate two main teaching quest recruits per new major region; remaining ordinary families use typed ecological encounter sources and reusable journal tracking. This prevents128 forms from becoming128 global quests
- All evolution trials give authored sufficient training floors after actual completion. No mandatory random battle farming or repeated resting to meet bond thresholds
- A reachability checker must model party size4, owned storage, available field/manual actions, context gates, both branch copies, sanctuary access and resource/reward capacity. A flat check that every ID appears in a table is not an acquisition proof

### Legendary gates remain separate

Reserve Q54–61, one explicit gate per form121–128. Do not enable ability12 or any legendary from this allocation alone. Existing designed 121's covenant remains a design to review, not a promised complete encounter. Do not silently replace its existing identity/phase/polarity with a Southern animal design.

Five-phase relay prerequisites must be **sequential or use explicit latched stations**, because the active party holds four members. Never require five simultaneous active phases. Opposite-polarity tasks check the independent authored polarity and provide clear stations; they cannot infer polarity from element. No mandatory legendary is required to acquire another ordinary family or to reach a region's safe return.

Each legendary receives a distinct environment/problem, clear world clues, free failure retry and an exact one-time retained-source contract. One-active-legendary restriction stays enforced. Neither a high stat total nor the word “legendary” substitutes for animated behavior and a combat role. All eight need independent art/design review; a repeated90-second empty survival arena is not an acceptable template.

## 11. Final namespace and capacity budgets

### Areas and typed quests

| Allocation | Proposed areas | Typed quests |
|---|---|---|
| Existing | 0–29, with existing checkpoint holes/rules preserved | 0–21 (22) |
| Southern | 30–37 (8) | 22–29 (8) |
| Magma | 38–45 (8) | 30–37 (8) |
| Underwater | 46–53 (8) | 38–45 (8) |
| Return A | 54–59 (6) | 46–49 (4) |
| Return B | 60–65 (6) | 50–53 (4) |
| Legendary locations | 66–73 (8) | 54–61 (8) |
| Reserve | unassigned | 62–63 (2) |

Final planning ceiling:74 areas,62 of64 quests. A revised scope must rebudget instead of silently adding quest64. Indoor counters/source lists do not become quests by default. Quest reward and gear source namespaces remain separate.

Visited bytes0–7 of `region_flags` cover the eight region groups: masks0x3F,0xFF,0xFF,0xFF,0xFF,0x3F,0x3F,0xFF. Anchor bytes0–7 use at most two safe rest anchors each; bytes8–15 remain reserve. Absolute room IDs never index a32-bit campaign mask.

Region flags bytes8–15 reserve64 typed ordinary field-acquisition bits; the plan needs **35** (Southern8, Magma7, Underwater10, Return A2, Return B8). Bytes16–17 reserve12 second-branch-copy bits, leaving4 spare. Bytes18–21 reserve32 persistent discovery hints/doors; the remaining bytes22–31 stay unassigned. Exact per-revision masks/source gates are mandatory; reservations do not make bytes valid in an earlier revision. Quest objectives handle main chapter stages; do not duplicate them as unexplained free flags.

### Creature event credit namespace

The current `progression_encounter` computes `area*6+enemy` only through room29; it occupies/reserves0–179. At room64 that arithmetic reaches384 and collides with the field-event namespace. Replace future allocation with an explicit `EncounterDef.credit_event_id`, retaining all old numeric event IDs exactly.

| Event category | IDs below384 | Budget |
|---|---|---:|
| Legacy/Northern unchanged | 0–179 | 180 |
| Southern encounter/quest credit | 180–219 | 40 |
| Magma | 220–259 | 40 |
| Underwater | 260–299 | 40 |
| Return A | 300–323 | 24 |
| Return B | 324–347 | 24 |
| Legendary activity | 348–371 | 24 |
| Reserve | 372–383 | 12 |

Give IDs to authored creditable encounters/outcomes, not every room slot or cast/hit. Do not award repeat XP by swapping the party. An explicit registry test rejects collisions, wrong credit kind and out-of-range IDs. Enemies can exist without issuing a new permanent quest ID.

Field events stay384–511, mapping to128 lifetime aid bits. Plan local aid indices0–15 legacy reserve (currently only0–7 actively used),16–39 Southern24,40–63 Magma24,64–87 Underwater24,88–103 combined returns16,104–119 legendary16,120–127 reserve8. Southern's24 can cover ten trial completions, eight field recruitment aids and six civic scene aids; internal object touches do not each need lifetime bits.

Historical event and generic reward APIs accepted broad valid IDs; preserve their old bytes and semantics. A future field-aid bit is XP/bond credit bookkeeping, **not proof** a new typed world trial or acquisition happened. If an unusual old save already has that bit, its new source must remain discoverable and its explicit trial floor must still work; only duplicate event XP/bond is suppressed. Starting an expedition may clear the shared expedition bitmap per existing rules, but migration itself must not clear it as a convenient namespace reset.

### Gear, rewards and records

Plan final unique gear budget: current19 +Southern6 +Magma6 +Underwater6 +Return A3 +Return B2 = **42**, within48 non-compacting records. Legendary trials reward creatures/access rather than eight more compulsory items. This leaves6 bag slots and22 of64 source IDs unassigned. Sources0–41 would be allocated once, appended in stable acquisition order. No mandatory consumable economy is added; wallet/key reserve stays zero.

Retain128 seen/obtained form bits and128 generic creature reward bits. Do not repurpose the latter. Sources for future quest/field/branch recruits use typed state, with transactional grant-zero inner operations as described. Inventory capacity tests still cover160 occupied creature records and48 gear records, including synthetic supported extremes, even though a normal full planned collection needs72/42.

## 12. Hardware and integration budgets

Inspected cartridge: **4,351,688 bytes**, under32MiB; do not reuse the ancient catalog baseline1.58MiB to claim current headroom. Map reports IWRAM code0x6DD8 =28,120 bytes against0x7000 =28,672, leaving only **552 bytes before the code boundary**. Keep new chapter logic, policies and optical handlers outside the hot `game.o` IWRAM placement. This is a hard review concern even with abundant ROM.

Mode4 OBJ static layout currently uses16256/16384 bytes, only128 bytes unused. Twenty creatures cannot each receive permanently reserved OBJ slots. Stream the selected companion's frames into reviewed shared slots; region-specific props must use existing mutually exclusive regional ranges. Prove no overlap with arrows, glyphs, partial hearts, phase icons or prior effects. Increased ROM sprite count does not itself increase available OBJ VRAM.

Provisional Southern ceilings, to be measured rather than asserted:

- ROM increment≤2MiB including eight backgrounds,20 forms/casts, portraits, UI, code and tables
- Mutable EWRAM increment≤8KiB; save/roster wire sizes unchanged under the recommended trial approach
- New IWRAM code allocation0; any claimed need requires an explicit relocation/headroom review
- Bounded optical network≤4 segments/2 mirrors per network and at most2 small networks in a room; cap VFX objects/target ledgers explicitly
- No malloc, no full roster/save snapshot on the GBA stack, no unbounded scans in per-frame drawing
- Preserve dedicated SAVE_PENDING behavior. Existing revision-3 maximum3072-budget step is192,790 cycles in its benchmark, already68.6% of a280,896-cycle frame. Expanded policy lookups and source validation require new measured timing, not a promise of unchanged cadence

Use explicit direct/sparse ROM lookup tables or bounded indexed policy maps where they reduce repeated roster×catalog scanning, preserving exact validation behavior. Current linear scans that are acceptable at21 forms/31 learn entries can become expensive at128 forms/209+ entries. Measure full160-instance validation and save, not only the normal21-family roster. Every optimization must retain historical malformed-bank tests.

## 13. Acceptance and stop conditions

A slice is complete only after all of these agree on the exact ROM/source head:

1. Schema/identity diff: all128 locked `(id,key,family,tier,rarity)` tuples unchanged; approved20 forms only; ability12 and legendaries disabled; no undefined signature/learnset/evolution/capability
2. API/codec: legacy trial semantics exact; wrong-family qualifiers rejected; per-revision form/command/trial/item/source policies pinned; old fixtures preserved; source transactions atomic; all corrupt/interruption tests and bounded incremental budgets pass
3. Visual review:20 native-size black silhouettes, readable faces and directional locomotion/casts; paired evolutions change anatomy/posture, not merely hue; secular reference boundaries respected
4. Fresh controller route: North→Southern entry, both guaranteed recruits, required base-79 refraction and base-85 latch interactions, manual positioning/reset/escape, all three weapons at boss, town return and post-clear revisits
5. Optional controller route: six field and two hinted uncommon recruits; ten distinct personal trials and evolutions; all8 quest claims and6 gear rewards; obtained41 in one save with21 retained families and no injected collection/XP/flags
6. Adversarial route: full party, all new recruits stored, unequipped signatures, wrong/empty command, no optional old companion selected, minimum weapon/gear, wrong mirror states, reset from every reachable state, death/re-entry/save reload, source READY/full inventory, failed save and retry, deferred evolution, different participating copies
7. Puzzles: exhaustive finite-state reachability/reset proof for rooms34–36 plus manual walk-through; no trapped player, no mirror beam through collision walls, no timer/menu exploit and no pixel-sized hidden interaction
8. Performance: actual emulated gameplay/update/presentation cadence in combined scrolling+20-family-art-switch+power+gear/UI/save windows, plus stack/OBJ/EWRAM/IWRAM reports. Physical-hardware verification is separate and must not be claimed if absent
9. Progress accounting: designed/implemented/obtainable/verified counted separately; every acquisition source linked to a normal controller artifact; no “128 complete” claim until the final graph and all content have passed

If the trial/revision-policy review fails, stop Southern enablement and finish the architecture review rather than consume remaining global bits. If a family fails expressive silhouette or unique gameplay-role review, redesign or reduce the batch; a numerical target does not authorize filler. If a migration fixture changes unexpectedly, isolate the difference before adding more content. Publication remains paused until the parent confirms approval and exact-head release conditions.

## 14. Immediate next developer actions

1. Review/approve the family-qualified trial and revision4 contracts independently of chapter art
2. Freeze the final Northern controller save as a revision3 fixture and preserve its exact ROM provenance
3. In a separate authorized checkout, implement and test policy/API scaffolding with all Southern rows still disabled
4. Prototype one town demonstration and rooms34/35 using placeholder *original* geometry; prove the required base-companion solutions plus manual arrangement/reset/escape without evolved-command, gear, or old-companion dependencies
5. Only then commit to the20-form production batch and measured resource budget

This document supplies the next bounded design and a finite128-form acquisition plan. It does not claim new code, new obtainable creatures, new release artifacts or permission to publish.

## 15. Implementation-ready supplement and clarifications

`/tmp/southern-core-contract.md` supplies exact public API signatures, legacy branching return semantics (append AMBIGUOUS=9), old/new whitelist snapshots, complete Southern source/discovery rules, key-based capability extension preserving32-bit wrappers, and integration file ownership. These are proposals for the separately authorized Southern workspace; do not edit Northern, `game.c`, or the UI generator as part of core/save work.

Use the supplement's repeatable deterministic branch-family encounter policy in place of the bounded two-individual-only wording in section10: two distinct individuals are the minimum needed to retain both branches, and further optional recruits may be allowed under ordinary capacity checks without repeated one-time rewards. This preserves irreversible evolution choice without cloning history or forcing random grinding. The full collection count72 is a minimum for all retained branches, not a cap.

The supplement also fixes exact discovery prerequisites: byte18 bit0 requires room32 visited and Q29 READY/CLAIMED; bit1 requires room32 visited and Q28 READY/CLAIMED. Thus the related gear reward need not be claimed to reveal a creature. Field source ownership and historical visits use the exact mapping in that contract.

Capability masks are a legacy projection, not the final architecture ceiling: preserve old low32 wrappers and add explicit form/capability-key queries before future needs exceed those bits. Southern uses one justified new interaction; future unrelated actions never alias old bits. Polarity has optional explicitly invented hold/pulse reception, with sequential latches/manual alternatives, no added canonical damage multiplier, and no mandatory requirement for an unowned Yin recruit.

### Main-route correction accepted by the integration lead

The two guaranteed companions are meaningful progression tools: a Water refraction and a Metal latch are mandatory. Manual geometry controls, reset, escape and journal access guarantee recoverability, but cannot replace these two actions. Evolution, optional Earth, special gear and an equipped signature are never required. Test wrong active family, companion stored, four full party slots, unequipped signature, reset before/after action, interrupted objective save and safe return/reassignment. This supersedes any residual suggestion of an entirely manual main-route completion.
