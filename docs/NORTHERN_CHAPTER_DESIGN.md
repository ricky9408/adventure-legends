# Northern coastal chapter design proposal

Internal developer brief for Adventure Legends

Prepared 2026-10-05 against the frozen river-region R5 build

## Recommendation and status

Design direction approved for the separate `feat/northern-beacon` checkout on 2026-10-05. The live river-region R5 source remains frozen. Equipment IDs/sidegrade balance still require their own audit; this approval is not catalog enablement or shipped-content evidence.

Build a bright, original coastal chapter around **Hearthwake Quay**, **the Headland Roads**, and **the Beacon Counterworks**. The player helps a working harbor restore its cargo routes, learns to redirect loads and stored energy in the field, then repairs a cliffside counterweight machine. This makes the region about observing and arranging movement rather than repeating Reedhaven's paired pools, valve sequence, crate puzzle, or garden roll course.

Propose **ten new forms in five families**, covering all five phases with independent Yin/Yang assignments. Use existing locked identities: 19/20, 22/23, 73/74, 75/76, and 77/78. This document neither enables those IDs nor changes the catalog, saved content, code, assets, or release. It proposes specifications for approval, not ten already-finished monsters. Names are original working names, subject to naming and Japanese UI review.

If all ten eventually pass implementation, acquisition, visual, save and native acceptance, the release would have **21 enabled/obtainable forms and eleven retained family instances in a complete collection**. It would still not have 128 finished forms. The presently designed-but-disabled legendary 121 remains outside this chapter.

### Baseline inspected

- `assets/creatures/catalog.json`, its schema, `identity-lock.json`, and `enabled.json`: twelve existing authored designs, eleven enabled forms, five active evolution edges; ability 12 belongs to the disabled legendary proposal
- `docs/ROADMAP.md`: regions must add distinct activities, explicit acquisition, useful side quests, visible clues and recoverable traversal; forms require original silhouettes, motion and functional roles
- `src/creatures.h/c`, `save5.h/c`, and `obj_layout.h`: fixed IDs and save allocations; current validators include several deliberate reviewed-content assumptions that must be expanded, not bypassed
- Frozen R5 cartridge `0ba77d82ce15619784c35a67be83950f924265b604a47495a8987afb21963e90`: 3,085,056 bytes; matching ELF/symbols used for the budget below

Some older architecture and verification paragraphs still describe the eight-form/revision-1 foundation. Use the frozen cartridge and current typed contracts as the implementation baseline; do not copy those historical counts into the next release.

## Reference boundary and visual direction

The primary reference lens is Norwegian coastal timber construction, with a clearly identified Nordic boatbuilding reference. This is an invented world, not a reconstruction of a particular historical town or a claim that Northern Europe has one culture.

- **Harbor frontage and passageways.** UNESCO describes Bryggen's harbor-facing gabled timber buildings, narrow passages, and stone storage structures behind them. Borrow the readable relationship between waterfront frontage, working passages and protected rear storage. Do not reproduce the real site plan, merchant institutions or building façades. [UNESCO World Heritage Centre on Bryggen](https://whc.unesco.org/en/list/59/)
- **An upper storage gallery.** Norsk Folkemuseum's Brottveit article explains the loft storehouse and surrounding galleries; it identifies the surviving three-storey example as unusual. Use a modest fictional two-level store with a visible exterior gallery for one clue route. Do not describe three-storey storehouses as a universal Norwegian feature or place an inland building unchanged into a coastal reconstruction. [Norsk Folkemuseum on the Brottveit storehouse](https://norskfolkemuseum.no/en/storehousefrom-brottveit)
- **Overlapping hull boards.** The Viking Ship Museum's Gokstad reconstruction documents fitted overlapping strakes, shaped timber and side-rudder work. Use overlapping curved planes as an abstract silhouette reference for the Water family and the working boathouse. This is an original creature and fictional craft, not a historical vessel copied into the game. [Viking Ship Museum on the Gokstad boat reconstruction](https://www.vikingeskibsmuseet.dk/en/professions/boatyard/building-projects/the-gokstad-boat)

All supernatural devices, monster names, phase assignments, polarities, puzzles and social relationships below are invented game design. The established five-phase/Yin-Yang system remains the game's independently documented inspiration; it is not presented as Nordic belief. Avoid invented translations, pseudo-authentic runes, horned-helmet shorthand, borrowed sacred iconography, or unresearched Indigenous motifs. No new mythical creature is labeled authentic folklore.

Use warm painted timber, pale stone, gold grass, clear water, green sheltered gardens and bright cloth markers. Favor stepped roof masses, long plank shadows, curved hull ribs and open sightlines. Keep the light, colorful established game identity; snow, darkness and violent-raider imagery are not required to communicate the region. Weather is conveyed through bounded pennants, cloud shadows and existing palette ramps, not a permanently dark screen or a new full-screen particle layer.

## Town field and dungeon loop

### Eight area scope

Room IDs 22–29 are **proposed**, not allocated by this document. Verify the room registry before implementation; preserve trial-room holes and all existing checkpoint rules.

| Proposed room | Space | Size | Player activity |
|---|---|---:|---|
| 22 | Hearthwake Quay | 480×320 | Meet workers, handle a real cargo demonstration, choose jobs, rest, inspect the forecast board |
| 23 | Headland Roads | 480×320 | Read load routes, adjust rail junctions, find sheltered crossings, rescue a stranded tender |
| 24 | Boathouse and upper gallery | 240×160 | Match hull supports to cargo shape; follow a visible clue into the gallery |
| 25 | Kiln and chart store | 240×160 | Carry a bounded heat charge, dry a damaged chart, learn why the route markers disagree |
| 26 | Counterworks loading hall | 240×160 | Learn the dungeon's load symbols with a reversible one-cart arrangement |
| 27 | Crossbeam chamber | 240×160 | Separate two conflicting cart routes and hold a counterweight at a safe stop |
| 28 | Relay gallery | 240×160 | Combine a rail turn and stored load without trapping the player or consuming an item |
| 29 | Beacon crown | 240×160 | Resolve a telegraphed machine encounter, reconnect the working harbor and reveal a future route |

The main path is town → field demonstration → two linked counterworks rooms → beacon → changed town. Its required dependency set is the two guaranteed base recruits plus manual mechanisms, not the three optional families. Side jobs take the player through a different field route or a new use of the same apparatus and return to a specific person. A completed service changes its local scene: a cart starts moving, a store opens its upper gallery, a tender is tied safely at the quay, or the chart board gains a useful route drawing.

Proposed entrance gate: Sky-clear plus a visited Reedhaven and an explicit ferry conversation. Do not require all eleven river quests, the prior ending, a legendary, or optional evolved commands. The old three-lantern ending remains earned; Northern completion gets its own quest/context flags.

### The reusable local mechanic

Use **authored rail carts, marked stops and two-state counterweights**. The player reads a load glyph, turns one junction, positions one or two loads, then observes which beam clears. A three-position mechanical forecast board labels which route is sheltered; the board is player-operated and deterministic. It does not change with real time, silent random rolls, or elapsed time in menus.

- Cart sockets and destinations have matching shape symbols as well as color
- A companion can reel a tagged load or align a tagged junction; no ability moves arbitrary scenery
- Basic A-operated handles demonstrate the mechanism in town, and an always-reachable reset lever restores unsolved transient arrangements
- Critical loops accept base-form commands. Evolved commands create optional alternate routes or safer/faster arrangements, not surprise requirements late in the mandatory dungeon
- Completed puzzle stages stay completed. Unfinished cart arrangements reset safely on room re-entry unless a later persistence design explicitly supports them
- Cargo never crushes or permanently displaces an NPC or the player. A blocked move fails without consuming a charge or objective
- No compulsory timing precision is required for the main route. A voluntary delivery challenge can measure active-play updates, with free reset and no lost reward

Wood 19 and Metal 77 are the two guaranteed recruits on the chapter's main teaching route. Their acquisition happens before any mandatory use of their capabilities. **The normal Sky-clear story grants Kohaku before his conversation; retain that ownership and the existing resume normalization. The entire mandatory dungeon must be completable without selecting or using Earth, with Wood 19, Metal 77 and local A-operated manual weights.** Earth pressing by Kohaku or the new Earth family is an optional alternative, never an unstated prerequisite or a hidden side-quest requirement. Every required return also has a local manual reset/exit. The other three new families have clearly offered side routes. All owned members remain assignable from the journal, so a four-member active party cannot strand a player who owns the needed companion.

The final encounter is a malfunctioning ballast carrier that exposes an obvious coupling after its telegraphed sweep. The mechanism, not raw grinding, creates damage windows. Any mundane weapon can finish it. The four earlier story powers stay useful without being individually required for its damage loop; phase advantage is an option, not an immunity puzzle.

## Ten proposed original forms

### Locked identity allocation

The following family IDs, form IDs, rarity and tiers exactly match the current identity lock. F007 and F008 remain three-stage reserved families, but only their first two forms are proposed here. Slots 21 and 24 are left reserved and undesigned. The three two-stage families are used without renumbering. Slots 3/6/9/12/15/17/18 and 121–128 are not repurposed.

| Family | Forms proposed | Locked topology | Phase | Polarity | Signature ability IDs proposed |
|---|---|---|---|---|---|
| F007 | 19 Spoolbud → 20 Loomcrown | 19→20→21; 21 stays reserved | Wood | Yin | 13, 14 |
| F008 | 22 Cindertray → 23 Kilnbarrow | 22→23→24; 24 stays reserved | Fire | Yin | 15, 16 |
| F025 | 73 Keelkip → 74 Wakecradle | 73→74 | Water | Yang | 17, 18 |
| F026 | 75 Cairncricket → 76 Archspring | 75→76 | Earth | Yang | 19, 20 |
| F027 | 77 Rivetfoil → 78 Gimbalcloak | 77→78 | Metal | Yin | 21, 22 |

All are ordinary rarity. Polarity is a separate authored axis, not a sixth/seventh phase, gender, moral ranking or a universal damage bonus. No family differs only by hue. A release review must identify each base and evolution from a black silhouette at native scale and explain how its motion and command change the decisions a player makes.

**Living-creature art gate:** every family needs a readable face, animal-like weight and posture, an intentional idle/breath or head/ear/antenna motion, a focused cast expression and a readable recovery. The workshop references shape anatomy and materials; they are not a substitute for living creatures. Review all ten grayscale native-size silhouettes against one another and the existing eleven forms, then inspect facial readability in front, profile and moving views. Portraits cannot be used to excuse a blank or unreadable in-game face. The two cast poses and locomotion frames should carry those expressions within the art budget; extra frames require a revised measured budget.

Stat vectors below are tentative authored weights in the existing vitality/power/guard/focus/haste order. Base totals are 180 and evolved totals 240. These are not a claim that currently unused creature stats already scale native damage.

| Form | Proposed vector | Total |
|---|---|---:|
| 19 | 36 / 24 / 30 / 54 / 36 | 180 |
| 20 | 48 / 30 / 42 / 72 / 48 | 240 |
| 22 | 36 / 28 / 44 / 52 / 20 | 180 |
| 23 | 52 / 40 / 56 / 68 / 24 | 240 |
| 73 | 34 / 38 / 26 / 34 / 48 | 180 |
| 74 | 48 / 52 / 34 / 46 / 60 | 240 |
| 75 | 30 / 50 / 26 / 24 / 50 | 180 |
| 76 | 44 / 62 / 40 / 32 / 62 | 240 |
| 77 | 32 / 28 / 38 / 50 / 32 | 180 |
| 78 | 44 / 38 / 52 / 64 / 42 | 240 |

### Spoolbud and Loomcrown

**19 Spoolbud** is a living, low thicket creature with a bobbin-like seed body, a vine-loop tail and four short root paws. An expressive face peers from the central knot: bright eyes, a tiny mouth and two leaf ears that tilt with curiosity. Its paws gather beneath it before the body rocks forward; it sniffs a rope end instead of moving like a motorized spool. **20 Loomcrown** becomes a taller, long-legged thicket animal whose arched shoulder branches frame an open trellis above its living body. Its vine tail threads through that negative space, while its face, ears and chest remain clearly readable. It must not read as a larger Spoolbud, an empty workshop loom or Midori with different leaves.

- Base command **Threadhold**, proposed ability 13: one narrow Wood tether, 16 Q4 base damage, pulling one ordinary enemy at most eight collision-swept pixels; bosses cannot be pulled. Cooldown target 90 updates
- Evolution command **Shuttle Span**, ability 14: a visible short thread between two authored endpoints, 24 Q4 when crossed, once per enemy per cast; maximum six enemy-ledger bits. Cooldown 120, effect at most 60 updates
- Field role: reel a marked light load onto the next rail stop. The evolved command can hold an existing tether while setting a second marked endpoint, enabling an optional upper-gallery route; neither command creates an unmarked bridge
- Acquisition: the introductory harbor job repairs two separated cargo lines and lets the worker show the player a normal cart reset before recruitment. Guaranteed once, no random encounter requirement
- Evolution target: level 16, bond 40, its roof-line personal trial, harbor-ready context and sanctuary confirmation. It retains the base command and capability

### Cindertray and Kilnbarrow

**22 Cindertray** is a warm ceramic quadruped with a squat rounded belly, four soft-looking paws, handle-shaped ears and a triangular back plate. Amber eyes, cheek vents and a small muzzle make it read as a living companion before its kiln-like material reads as equipment. It breathes, crouches and pads toward warmth. **23 Kilnbarrow** has a longer low body, broad forelegs and two separating kiln-like shoulder plates; its gait changes to a deliberate animal lope, with an expressive head above the front plate. Its side plates open for a cast and settle with a relieved exhale. Neither form is merely an ash pan on legs, and neither reuses Homura's fox outline or flame poses.

- **Heat Pocket**, ability 15: set one telegraphed stationary heat patch that bursts after 18 updates, 24 Q4 Fire damage once per enemy. Cooldown 90, lifetime at most 48
- **Firing Drawer**, ability 16: move a stored heat patch between two short, visible positions before its arrival burst. Damage remains 24 Q4; placement and timing change rather than merely multiplying damage. Cooldown 120, lifetime at most 60
- Field role: retain heat in a tagged receptacle so the player can move an otherwise cold load. Evolved routing transfers it across a second marked stop. This is an invented puzzle charge, not a simulation of real kiln practice
- Acquisition: repair a kiln's draft path without burning its wooden surrounding props; the ordinary Fire companion can provide the initial ignition, while the new family's retention role remains distinct
- Evolution: level 17, bond 40, the dry-chart personal trial and sanctuary confirmation. Neither base nor evolution is automatically tagged with every Fire field action

### Keelkip and Wakecradle

**73 Keelkip** is a seal-like living companion with a rounded muzzle, bright attentive eyes, broad front flippers and a forked hind flipper. Three overlapping translucent body plates suggest fitted hull boards without becoming a literal boat. It lifts its chest, flipper-waddles and settles into a buoyant glide. **74 Wakecradle** grows long outward-curving front flippers and a raised back crest framing a suspended water sling below its continuous body; open spaces around the flippers change both the silhouette and swimming posture. Its face remains visible during its wide turning cast. Both contrast with Dewspindle's reed legs and Tidewheel's upright ring; the evolution must not look like two disconnected hull props.

- **Washback**, ability 17: a short frontal Water surge, 24 Q4, pushing ordinary targets up to ten swept pixels; no boss displacement. Cooldown 90
- **Wake Turn**, ability 18: a bounded L-shaped surge following two orthogonal segments, at most 48 pixels total, 24 Q4 once per enemy. The corner is visible before travel; every segment and endpoint uses wall checks. Cooldown 120
- Field role: buoy a tagged dock load, temporarily changing its displayed weight from three to one. Evolution can pivot the floating load at a specifically marked junction. No diving, free swimming, gap teleportation or underwater system is implied
- Acquisition: locate a missing work tender from two visible mooring clues and guide it to a sheltered landing. No animals need to be harmed, and leaving the rescue does not delete the tender
- Evolution: level 18, bond 45, the fragile-cargo personal trial and sanctuary confirmation. Existing Dewspindle filling and Tidewheel pool links retain their separate niches

### Cairncricket and Archspring

**75 Cairncricket** is an expressive cricket-like animal with three offset stone plates, two long jointed hind legs, short forefeet and flexible antennae. Eyes beneath the upper pebble brow and a tiny chirping mouth establish a living face. Its crouch, spring and antenna recoil are more important than a mechanical hinge. **76 Archspring** has a high arched thorax, longer paired hind legs and a hanging tail stone, with large negative spaces between body and legs. Its face leans into a deliberate springing gait instead of simply enlarging the original hop. It must remain recognizable apart from Kohaku's body and armor mass, and never read only as a walking masonry arch.

- **Counterdrop**, ability 19: place a clearly marked Earth impact that lands after 18 updates, 24 Q4 in a small radius, once per enemy. Cooldown 90
- **Counterpoise**, ability 20: place one short-lived weight that intercepts one hostile projectile and then emits a 32 Q4 Earth pulse. No player invulnerability or healing; bosses still require their normal damage window. Cooldown 120, maximum lifetime 48
- Field role: the existing explicit PRESS_WEIGHT capability, applied to marked counterweight pans. Evolved timing permits an optional two-load solution, but an already-owned Kohaku can still perform the ordinary press
- Acquisition: follow three misplaced route markers, discover why they moved, and settle each on a correctly drawn plinth. The lesson is matching support/load shape, not a hidden click sequence
- Evolution: level 18, bond 45, the balanced-reach personal trial and sanctuary confirmation

### Rivetfoil and Gimbalcloak

**77 Rivetfoil** is a small folded bird-like companion with fan-shaped metal wings, two forked feet, a pointed beak and an off-center rivet marking. Its bright eye, quick head tilt, feather-like folds and short balancing tail communicate an alert animal. **78 Gimbalcloak** becomes a crested, longer-necked bird whose broad cloak-like wings surround a visible gimbal-shaped breast structure. It opens those wings into a directional screen, steps sideways and tucks them back with a living recovery pose. Its face cannot disappear behind the mechanism. Neither form uses Chimeclasp's three-prong clasp body or returning-pin animation.

- **Quarterturn**, ability 21: redirect one approaching hostile projectile by 90 degrees into a displayed side lane, changing it to friendly Metal combat damage. It does not reverse it like Fuuri's reflection, and grants no field/fire tags. Cooldown 90
- **Gimbal Screen**, ability 22: place a short fixed directional gate that redirects up to two later hostile projectiles by 90 degrees. One gate only; a per-cast projectile ledger prevents a projectile being redirected repeatedly. Cooldown 120, lifetime at most 48
- Field role: align a marked rail junction to one of four authored orientations. The evolution can set a conditional second stop for an optional carriage return. This is different from Chimeclasp's tuned latch
- Acquisition: the main field job recovers a borrowed bearing using a manual junction first, then lets the companion demonstrate the same action. Recruitment is complete before the dungeon expects this capability
- Evolution: level 20, bond 50, the compass-round personal trial and sanctuary confirmation

### Recruitment and training policy

Propose base recruit level `clamp(current valid party median, 14, 20)` and bond 20. The five personal trials explicitly provide a one-time training floor at their family's evolution threshold and required bond, following the already transparent catch-up precedent. They never lower existing progress, auto-evolve, auto-equip a new command, or change a selected party member silently. This avoids a new mandatory kill grind while keeping progression visible.

Each evolution keeps level-one access to the base ability and learns its new signature at the evolution's minimum level. Deferral changes no instance, collection or quest byte. One family remains one live instance through evolution; history counts both forms. All new companions are ordinary occupied records, not legacy STORY_LOCKED records.

## Quests clues and rewards

The IDs below are proposed authoring assignments within the existing 64-quest allocation. Do not reserve them in a live table until the chapter contract is approved. Creature rewards 7–11 are likewise proposed after existing story rewards 1–4 and Reedhaven 5–6; equipment reward sources use their own namespace.

| Proposed quest | Person and purpose | Concrete activity and visible clue | Permanent result |
|---|---|---|---|
| 11 Lines for Tomorrow | Edda, a fictional harbor rigger | Repair two cargo lines with different support diagrams; hanging loose ends show where each line belongs | Spoolbud 19, creature reward 7; the harbor teaching route opens |
| 12 A Cold Kiln | Tove, a fictional kiln worker | Reopen a draft route using a vent diagram on the working kiln; soot ends abruptly at the blocked section | Cindertray 22, reward 8; kiln room becomes a useful service |
| 13 The Borrowed Bearing | Neri, a fictional track keeper | Compare a missing bearing's outline to two open housings and turn the manual field junction correctly | Rivetfoil 77, reward 11; dungeon entry context becomes available |
| 14 One Tender Missing | Pell, a fictional boat repairer | Follow a broken mooring line and a second visible hull reflection; guide the tender between fixed safe stops | Keelkip 73, reward 9; a shorter field return is marked on the chart |
| 15 Markers That Walk | Iven, a fictional route surveyor | Find three moved sign stones; differently shaped clean marks identify their original plinths | Cairncricket 75, reward 10; crossroads signage stays corrected |
| 16 A Roof without Nails | Edda | Use two taught tether positions to reach a visible roof-gallery load without blocking the stairs | Wood personal trial and an optional roof shortcut; a useful sword sidegrade |
| 17 The Dry Ledger | Tove | Carry heat to three chart-drying stations in a player-chosen order; damp patches visibly recede | Fire personal trial; the chart reveals two specific future return clues |
| 18 Carry the Fragile Cargo | Pell | Float, pivot and unload a marked crate without dropping it; free local reset and no real-time deadline | Water personal trial; a range-oriented bow sidegrade |
| 19 Balance without Breaking | Iven | Balance two unequal loads while keeping the exit stair clear; each pan displays its current weight | Earth personal trial; movement/armor sidegrade and a repaired lookout |
| 20 The Honest Compass | Neri | Trace a carriage from three drawn bearings and prove the return path works in both directions | Metal personal trial; a cooldown/defense ring sidegrade |
| 21 Beacon Counterworks | The harbor's small working group | Complete the linked dungeon route and its readable machine encounter | Chapter completion, reliable ferry return, changed town activity and a spoiler-controlled hint toward the next region |

Reward items should add choices within the three existing weapon classes and five equipment slots. A six-item candidate pool is sword 3, lance 11, bow 19, mail 35, boots 51 and ring 83, **pending an equipment-ID audit**. Examples: a small reach gain with less attack; lighter mail with less bonus health; or a ring trading half the cooldown reduction for defense. Do not add inert stats or strictly superior replacements for all thirteen existing items. No new weapon class, random affix system, price economy or bag expansion is needed for this chapter.

### Discovery rules

Every optional discovery needs two independent cues and an explicit payoff:

1. **Upper gallery:** a visible parcel above an open wall gap plus a loose rope end below it. The player can see the destination before gaining the evolved tether. Reward is a short return and a signed route sketch, not an unexplained invisible chest
2. **Sheltered tender:** a broken line on the field bank plus the hull visible from the overlook. Wind pennants indicate the safe side; the clue does not require recognizing a real-world nautical tradition
3. **Warm chart shelf:** a strip of damp paper and a condensation mark on a nearby window point to the same heater socket. Failed placement returns the load; it never destroys a quest item
4. **Counterweight recess:** scrape marks and a missing section of a painted load diagram reveal a shallow side niche. Its reward is announced by a distinct object and a journal entry; no wall-pixel search
5. **Return after evolution:** a narrow route is visible behind a short rail gap, with a two-stop pictogram. The journal names the missing maneuver rather than merely saying “come back later”

Never place an essential recruit behind its own ability or evolved form. No permanent missables, timed calendar availability, blind hidden-button sequences, or rare RNG drop are needed.

## Implementation contract and boundaries

### Catalog and progression work that must precede enabling content

1. **Sparse forms and families.** The current reviewed family policy indexes a compact six-family table. F025–F027 require a keyed family-policy lookup. Preserve IDs/tier/rarity/topology byte-for-byte in the identity lock; do not renumber them into a contiguous family block
2. **Ability 12 stays disabled.** Proposed signatures 13–22 create a gap after currently enabled 1–11. Replace the contiguous `id-1` enabled-ability assumption with an explicit enabled lookup or checked sparse table. Enabled count would be 21 abilities, maximum enabled ID 22; those are different quantities
3. **Trial bits.** Keep existing bits 1/2/4/8/16. Proposed new family bits are 32/64/128/256/512. The instance wire field is already 16-bit, but the current family-policy trial member is only 8-bit and must be widened in ROM metadata before 256/512 can work. Family-specific validation remains mandatory. A read-only `creatures_family_trial(form_id)` API can expose the explicitly mapped mask or zero for an enabled form with no trial. Proposed symbolic names are TENSION_ROOF, DRY_LEDGER, FRAGILE_CARGO, BALANCED_REACH and COMPASS_ROUND, respectively
4. **Evolution context.** Do not write new gates into `CampaignSave.chapter_flags`. Propose separate context bit 16 for harbor-ready and bit 32 for Counterworks completion, derived from claimed quests. Existing chapter mask 7 and Reed-restored context bit 8 remain unchanged; campaign bit 3 remains ENDING_SEEN
5. **Field caps.** Reserve only four new reusable tags, provisionally bits 21–24: REEL_LOAD, STORE_HEAT, FLOAT_LOAD and ALIGN_RAIL. Earth reuses PRESS_WEIGHT. Evolved modes use the same inherited tag plus an authored command/target rule. This leaves seven 32-bit capability positions for later regions; update the known-capability mask deliberately. A phase or friendly projectile owner never grants a field tag
6. **Selected identity.** Keep roster instance and form as the authority. Broaden the old six-family display/dispatch adapter explicitly; do not let family 25 fall through to a legacy companion or use a form ID as a quick-party position. Four active references and 160 stored records remain unchanged
7. **Handlers before claims.** Each new command needs a real bounded handler, animation, acquisition path and contextual feedback. No enablement solely to satisfy collection counts. Publish designed/implemented/obtainable/verified counts separately

### Persistence proposal

Use **save format 5, proposed content revision 3**, preserving bank offsets, 6,144-byte banks, 24-byte creature records and the existing SRAM safety range. No wire-size expansion is necessary for ten forms or eleven quests.

- Revision 1 must keep its exact eight-form whitelist and zero typed quest/equipment allocations
- Revision 2 must gain its own explicit eleven-form whitelist. The current “anything other than revision 1 uses the current catalog” shortcut must not permit new Northern forms to appear in a CRC-valid revision-2 bank
- Revision 3 may permit the reviewed 21 forms and new authored quests. Unknown/future revision IDs still reject rather than normalize
- Allocate new quest IDs 11–21, with exact objective masks and allowed variable ranges. Existing quests 0–10, reward bits, expedition credits and all prior variables remain byte-identical
- Keep Reedhaven visits in `region_flags[0]`. Use a separate byte for the eight proposed Northern room visits, and a separate anchor byte for northern rests; do not overflow the old room-minus-16 bit mapping
- Validate exact room/spawn entries for 22–29. Do not turn rooms 14/15 into save checkpoints or accept holes merely by increasing a maximum room number
- Use regional visit/objective arrays for new areas. In particular, room IDs 32 and above must never feed an old campaign `1u << room` expression; a 32-bit shift is not a growing room registry. Keep original campaign puzzle bits in their original namespace
- The current encounter-credit expression `room * 6 + enemy` stays below the reserved field-aid range 384–511 only for room IDs below 64. The proposed field room 23 is within that bound. Add an explicit checked event registry before any area 64 or above, preserve existing credit IDs, and keep encounter/quest/field-aid allocations disjoint
- Require claimed guaranteed-recruit quests to retain a valid owned member of the relevant family, regardless of active party or evolution, just as the traversal-critical river recruits are protected now. No release API is introduced
- Failed one-time grants leave the quest READY and all authoritative state unchanged. At capacity, show a clear failure and preserve the pending reward; do not invent a release feature or overwrite a companion. The normal proposed roster and gear counts cannot fill the existing capacities, but synthetic capacity tests remain required. Publish recruitment/reward dialogue only after durable commit
- Generic creature reward IDs and equipment acquisition sources remain separate. Audit new reward-ID reservations against prior published authoring, and explicitly author their new cross-ledger relationships instead of interpreting every high reward bit as a quest
- No migration invents Northern visits, discoveries, training floors, item sources or companions
- Re-run power cuts at all write positions, valid-CRC malformed content, newest-bank fallback, immutable snapshot and budget tests. The unchanged maximum-budget rule is still 3,072 work units

### Finite trial and capability namespaces: required next-batch gate

The Northern candidate uses **10 distinct personal-trial bits in a 16-bit
instance field** (values 1 through 512) and **25 of 32 field-capability bits**.
Six unique trial positions remain (1024, 2048, 4096, 8192, 16384, 32768), and seven
capability positions remain (bits 25–31). The locked catalog allocates 60
families, so one globally unique trial bit per family cannot scale to the full
roster. Never allocate a trial value beyond 32768, truncate it to 16 bits, or
shift beyond the capability word.

Before approving the next family batch, review its namespace demand and choose
an explicit long-term trial model. The decision is required **before** a batch
would exceed either remaining capacity; using the last positions is not a
substitute for the design review. Two possible directions need separate review:

- A family-scoped trial namespace may reuse numeric bits for different families,
  with explicit family/form lookup and a versioned policy. It must preserve the
  exact meanings and saved bytes of all released families, distinguish multiple
  trials within one family, preserve evolution ownership, and reject accidental
  cross-family evidence. Today's validator requires globally distinct nonzero
  family trials, so reuse is not implicitly enabled by the existing API
- A wider persisted trial representation needs a new wire-layout/version plan,
  explicit migration from every released format/content revision, new SRAM/ROM/
  RAM/stack budgets, and complete interrupted-write and malformed-record tests.
  Widening a C field alone must never change the established 24-byte wire record

Prefer existing reusable capability tags plus explicit command/target rules
when they express the same action. A genuinely new capability must justify its
bit, bounded runtime handler, target semantics and regression coverage. Do not
collapse unrelated old abilities just to reclaim a bit, or derive capabilities
from phase, polarity, family number or an item's damage type.

The reviewed decision must specify stable IDs, old/new revision whitelists,
translation or identity-preserving migration, no fabricated trial rewards,
collision/overflow rejection and exact-save fixtures before activation. This
is a future architecture gate only; Northern N0's 16-bit trial field, 32-bit
capabilities and frozen runtime remain unchanged.

### New behavior deliberately excluded

No legendary enablement; no underwater movement or oxygen; no freeform physics/rope solver; no continuous seasonal clock; no crafting-material economy; no creature release, breeding or duplicate-family collection workaround; no new combat stat layer or automatic weapon-element inheritance. Full 128-form completion, the remaining third tiers and other planned regions remain later work.

## Measured baseline and provisional budgets

These figures are against the frozen R5 cartridge, not the older catalog budget proposal:

| Resource | R5 evidence | Implication for this chapter |
|---|---:|---|
| ROM | 3,085,056 bytes | Normal cartridge limit remains 33,554,432; require a separate chapter delta budget |
| IWRAM code span | 27,664 bytes, `0x03000000..0x03006c10` | Only 1,008 bytes remain under the 28,672-byte code cap; put new logic in ROM and count added veneers |
| Initialized data plus BSS | 47,320 bytes, from 80 + 47,240 | Roster allocation is already paid; propose at most 4 KiB additional transient chapter state, not another full save snapshot |
| Mode 4 OBJ cache | 16,256 of 16,384 bytes used | Only 128 bytes are unassigned; adding resident effects per form is not viable |
| Persistent roster | 160×24-byte records; four active refs | Five additional live families need no layout expansion |
| Save bank | 6,144 bytes; used allocation 5,056 | Existing 64 quest/objective slots and 48 gear records can carry this proposal with explicit content revisioning |

### ROM estimate

An uncompressed first estimate for two scrolling areas and six fixed rooms is:

- Two 480×320 areas with even/odd source atlases: **614,400 bytes**
- Six 240×160 backgrounds: **230,400 bytes**
- Ten forms × four directions × four 16×16 frames: **40,960 bytes**
- Ten 32×32 portraits: **10,240 bytes**
- Two 16×16 cast poses in four directions for ten forms: **20,480 bytes**
- Fifty 16×16 actor/prop frames: **12,800 bytes**
- Provisional text/code/enemy/boss/collision/effect reserve: **160 KiB**

This is about **1.04 MiB**, before any additional variations; set a proposed hard review budget of **1.25 MiB added ROM**. Projected total at that cap is 4,395,776 bytes. These are estimates, not measurements or an assurance that extra atlas variants are free. The historical catalog's 1-MiB incremental allowance described an earlier subsystem proposal and is not a fresh allowance for every chapter.

### Runtime and art limits

- Reuse the selected-companion tile and portrait paths; do not keep every owned form's frames resident in OBJ
- Reuse the bounded region actor cache, respecting its split around shared hint/spark/armor tiles. Keep a documented maximum of 20 simultaneously cached regional actor slots and retain the OAM insertion guard
- Budget new effects to reuse existing effect regions when their ownership is provably exclusive, or fit two new 8×8 glyphs into the remaining 128 bytes. A header assertion on final end address is insufficient: validate all simultaneously live intervals for overlap
- Returning pins, both arrows, HUD partial hearts, all phase icons and a new companion effect must be exercised together. Invalidate pose caches when tile ownership changes
- Keep maximum enemy count six, player arrows two, hostile/friendly shot pool twelve. Bounded new effect descriptors and per-cast masks are preferable to unbounded object lists
- No full framebuffer, bank, roster, pathfinding grid or freeform rope simulation goes on the GBA stack. Inspect compiler frames and the complete call-chain high-water separately
- Render simple weather markers from cached sprites. Do not add a full-screen snow/rain pass, per-pixel alpha or a second scrolling layer without a separate measured budget
- The 280,896-cycle hardware-frame budget is unchanged. R5's 118,095-cycle sampled two-arrow/fractional-health window was not a maximal stress guarantee: it had five live enemies, at most two visible and no hostile shots. Build a new representative worst window including hostile shots, cart animation, camera parity changes, new effects and cold UI/save transitions

## Work packages and acceptance

1. **Approve the design and allocation contract.** Resolve names, recruitment gates, quest IDs, item sidegrades and the exact ten-form scope. Add no live entries until that review is complete
2. **Generalize content validation in isolation.** Sparse families/abilities, wider trial metadata, explicit revision-2→3 migration and revision-specific whitelists, checked room/event registries, and selected-form dispatch. Preserve byte-exact original migrations, current river saves and every legacy field capability; run sanitizer mutation suites before art integration
3. **Greybox one complete loop.** Town cargo demonstration, guaranteed Spoolbud, field bearing lesson, guaranteed Rivetfoil, one reversible dungeon chamber, rest and return. Use marked placeholders for geometry only; count zero new forms as implemented/obtainable release content at this stage
4. **Author five families completely.** Sparse family/ability lookup, preserved disabled ability 12, and a verified reusable OBJ ownership map are required acceptance gates before any form is enabled. Approve silhouette sheets before animation; produce all directional locomotion/cast frames and portraits, readable phase/polarity labels, learnsets and contextual error feedback. Each evolution changes silhouette, motion and tactical/field decisions
5. **Finish linked dungeon and side jobs.** First prove a complete mandatory route from a legitimate Sky-clear save without selecting or using Kohaku/Earth, using only guaranteed Wood 19/Metal 77 and manual weights. Then test Earth-powered optional alternatives separately. Exhaustively enumerate finite cart/junction states; prove reset and exit reachability from each. Test wrong commands, every objective order, moving away during a cast, leaving/re-entering, death, declined evolution and failed reward commits
6. **Run exact-ROM player evidence.** Begin with a newly started route and authenticated prior-cartridge SRAM routes. Use only controller input for acquisition/collection/combat evidence; label synthetic fault tests separately. Reboot a complete history with all 21 enabled form bits and eleven live family instances, including unreleased forms absent
7. **Re-run the whole game.** Old campaign routes, five-phase damage, all weapons, no-heal/cooldown behavior, projectile gear locks, scrolling parity, cold menu/save cadence, return trips and every supported save migration. Publish the exact ROM hash with reports and limits

### Approved direction and remaining decisions

Approved: eight areas 22–29; ten forms and abilities at the listed stable allocations; Sky-clear plus visited-Reedhaven ferry entry; two guaranteed recruits and three optional families; four reusable new field tags; content revision 3; and non-dominating item sidegrades after an ID audit.

Required dependency clarification: retain the normal Sky-clear story ownership and resume normalization; never require selecting or using Kohaku/Earth. Manual weights plus Wood 19 and Metal 77 must complete the mandatory dungeon. Earth commands are optional alternatives.

Required art clarification: every family is a living, expressive companion with animal-like posture and motion. Keep the inventive thicket/bobbin, warm ceramic quadruped, seal-like, cricket-like and folded bird-like silhouettes; do not deliver animated workshop props with token eyes.

Still to settle before individual content is enabled:

- Final names and Japanese UI wording
- Equipment ID audit and exact non-dominating sidegrade numbers
- Final cart/junction layout and finite-state proof, including a main-route proof with no Earth actions
- Explicit reusable effect-tile ownership and simultaneous-effect tests
- Measured art/code/cycle deltas and final balance values

### Spoiler-free player-facing direction

A later update can say: “Next is a bright northern-coast region with a working harbor, new companion shapes, and field puzzles built around moving and balancing cargo.” Keep names, acquisition steps, hidden paths, evolution conditions and the dungeon resolution inside developer material until the player-facing reveal is requested.
