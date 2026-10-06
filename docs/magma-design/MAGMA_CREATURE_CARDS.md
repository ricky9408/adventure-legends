# Magma creature and command cards

Developer-only proposal; no runtime rows are enabled. All timing values are 60Hz PLAY updates, not measured balance results. Commands preserve current equipment cooldown semantics and hit ledgers.

## 31 · Coalcoil (F011, tier 1)
- Identity: Fire / Yin, locked ordinary rarity; signature 43
- Silhouette: A low snail with a broad smiling muzzle, two blunt eyestalks and a sideways crescent shell; pale foot clearly separate from charcoal shell.
- Locomotion: Foot ripples in four readable waves; shell rocks after the head stops.
- Field: store_heat; tagged targets only
- Combat role: Delayed lane crossing
- Warm Thread: Draw a 40px ground thread after an 8-update warning; first crossing ends it. No through-wall segments.
- Timing: startup/active/recovery/cooldown 8/36/12/90; live objects≤1; total target budget≤16 Q4
- Stat weights: {'vitality': 30, 'power': 44, 'guard': 26, 'focus': 45, 'haste': 35} = 180; verify actual consumers before balancing
- Acquisition: Receive the rescued hatchling after manually moving an insulated jar to the marked cool shelf; no heat power is needed to earn it.
- Learned commands: 43@1

## 32 · Emberhelix (F011, tier 2)
- Identity: Fire / Yin, locked ordinary rarity; signature 44
- Silhouette: A raised snail on a narrow long foot; its open spiral shell sits upright with a large triangular window and expressive face below.
- Locomotion: Stretch, brace, pull the shell forward; spiral tips lag by one pose.
- Field: store_heat; tagged targets only
- Combat role: Two-point squeeze
- Coil Clamp: Two hooked arcs close on a 32px pocket; a target is hit once across both arcs. The player can walk through.
- Timing: startup/active/recovery/cooldown 12/16/16/120; live objects≤2; total target budget≤24 Q4
- Stat weights: {'vitality': 42, 'power': 56, 'guard': 38, 'focus': 57, 'haste': 47} = 240; verify actual consumers before balancing
- Acquisition: Explicit 31→32 choice after owning-family trial 1; defer is unchanged.
- Learned commands: 43@1, 44@26
- Evolution: 31→32, level26/bond45, MAGMA_READY, family-local key1 (required mask1), sanctuary and explicit target confirmation
- Trial ‘Three Cool Shelves’: Store heat from each of three numbered refractory jars, then park each at the matching safe shelf; never warm the seedling tray.

## 33 · Hearthcrown (F011, tier 3)
- Identity: Fire / Yin, locked ordinary rarity; signature 45
- Silhouette: A long muscular snail with a flat fan-shaped shell held above its face on three connected shell ribs; large open spaces replace the earlier spiral.
- Locomotion: Wide foot fans to anchor, then contracts into an unhurried glide.
- Field: store_heat, ignite; tagged targets only
- Combat role: Delayed directional denial
- Crown Interval: Show three short spokes, then activate them in order; share a 32Q4 target budget across the whole cast. Gap remains visibly safe.
- Timing: startup/active/recovery/cooldown 18/30/20/150; live objects≤3; total target budget≤32 Q4
- Stat weights: {'vitality': 51, 'power': 65, 'guard': 47, 'focus': 66, 'haste': 56} = 285; verify actual consumers before balancing
- Acquisition: Explicit 32→33 choice after owning-family trial 2; defer is unchanged.
- Learned commands: 43@1, 44@26, 45@32
- Evolution: 32→33, level32/bond60, CALDERA_OPEN, family-local key2 (required mask3), sanctuary and explicit target confirmation
- Trial ‘One Hearth, Three Uses’: As form32, reuse one charged brick to dry clay, temper a tool and warm seedlings in that order, cooling it at a marked sink between uses; prove all three different outputs.

## 34 · Shardibex (F012, tier 1)
- Identity: Earth / Yang, locked ordinary rarity; signature 46
- Silhouette: A small round-nosed mountain goat with short straight stone horns, wide cloven feet and a tilted rectangular shoulder patch.
- Locomotion: Quick paired hoof plants, head dip, rear-foot catch-up.
- Field: press_weight; tagged targets only
- Combat role: Short-range interrupt
- Heel Knock: A narrow 22px stomp cone interrupts eligible ordinary foes; no boss displacement or terrain mutation.
- Timing: startup/active/recovery/cooldown 6/8/16/90; live objects≤1; total target budget≤20 Q4
- Stat weights: {'vitality': 44, 'power': 33, 'guard': 43, 'focus': 30, 'haste': 30} = 180; verify actual consumers before balancing
- Acquisition: Raise the pedestrian brace with its public handwheel and guide the young ibex along the open terrace; no weight power is needed.
- Learned commands: 46@1

## 35 · Bracehorn (F012, tier 2)
- Identity: Earth / Yang, locked ordinary rarity; signature 47
- Silhouette: A low broad-shouldered goat with huge outward U-curved horns enclosing its face, short hindquarters and distinctly spread forehooves.
- Locomotion: Three-beat brace and short forward shuffle; head stays level.
- Field: press_weight, break_crack; tagged targets only
- Combat role: Commitment counter
- Brace Reply: Visible frontal bracing arc catches one eligible ordinary contact attack, then replies; expiry gives no damage and no invulnerability.
- Timing: startup/active/recovery/cooldown 12/24/18/120; live objects≤1; total target budget≤24 Q4
- Stat weights: {'vitality': 56, 'power': 45, 'guard': 55, 'focus': 42, 'haste': 42} = 240; verify actual consumers before balancing
- Acquisition: Explicit 34→35 choice after owning-family trial 1; defer is unchanged.
- Learned commands: 46@1, 47@26
- Evolution: 34→35, level26/bond45, MAGMA_READY, family-local key1 (required mask1), sanctuary and explicit target confirmation
- Trial ‘A Walkable Load’: Press three marked braces while each pedestrian side lane remains open; dragging a baffle into a walking lane invalidates only that attempt.

## 36 · Spanram (F012, tier 3)
- Identity: Earth / Yang, locked ordinary rarity; signature 48
- Silhouette: A tall long-legged ram with two high buttress horns joining above its brow, a narrow waist and two strong negative-space arches.
- Locomotion: High deliberate diagonal hoof steps; horns sway opposite hips.
- Field: press_weight, break_crack; tagged targets only
- Combat role: Wide frontal stagger
- Archfall: A visible overhead arch lands in a wide 44px frontal crescent after its warning. No temporary solid wall, crush or player push.
- Timing: startup/active/recovery/cooldown 20/10/22/150; live objects≤1; total target budget≤32 Q4
- Stat weights: {'vitality': 65, 'power': 54, 'guard': 64, 'focus': 51, 'haste': 51} = 285; verify actual consumers before balancing
- Acquisition: Explicit 35→36 choice after owning-family trial 2; defer is unchanged.
- Learned commands: 46@1, 47@26, 48@32
- Evolution: 35→36, level32/bond60, CALDERA_OPEN, family-local key2 (required mask3), sanctuary and explicit target confirmation
- Trial ‘The Unbroken Crossing’: As form35, brace the high and low supports from opposite landings and move the central slab between them without blocking the marked return loop.

## 37 · Tuftpika (F013, tier 1)
- Identity: Wood / Yin, locked ordinary rarity; signature 49
- Silhouette: A tiny pika with long swept-back grass whiskers, round ears, a square leafy tail tuft and two high-set dark eyes.
- Locomotion: Compact four-paw gallop, pause, whisker flick.
- Field: grow_roots; tagged targets only
- Combat role: Precision hindrance
- Burr Skip: One bouncing seed follows two 18px ground hops; first ordinary hit gets a short visible slow. Walls end the path.
- Timing: startup/active/recovery/cooldown 8/18/12/90; live objects≤1; total target budget≤16 Q4
- Stat weights: {'vitality': 33, 'power': 31, 'guard': 34, 'focus': 43, 'haste': 39} = 180; verify actual consumers before balancing
- Acquisition: Follow paired nibble marks to a sheltered plot; put its visibly displaced seed tray back without clearing the living hedge.
- Learned commands: 49@1

## 38 · Rootmuffle (F013, tier 2)
- Identity: Wood / Yin, locked ordinary rarity; signature 50
- Silhouette: A low long-bodied pika with a broad root beard and two separated leafy shoulder mounds; its ears and living muzzle remain exposed.
- Locomotion: Low belly-clear scamper; beard trails, then gathers beneath chin.
- Field: grow_roots; tagged targets only
- Combat role: Narrow area hold
- Root Hem: Two parallel 32px root lines leave a walkable central gap; crossing either gives one brief ordinary-root effect, never on a boss.
- Timing: startup/active/recovery/cooldown 14/36/14/120; live objects≤2; total target budget≤20 Q4
- Stat weights: {'vitality': 45, 'power': 43, 'guard': 46, 'focus': 55, 'haste': 51} = 240; verify actual consumers before balancing
- Acquisition: Explicit 37→38 choice after owning-family trial 1; defer is unchanged.
- Learned commands: 49@1, 50@26
- Evolution: 37→38, level26/bond45, MAGMA_READY, family-local key1 (required mask1), sanctuary and explicit target confirmation
- Trial ‘Shelter the Roots’: Grow roots into two dry hedge ties while a third living opening stays clear; choose the low sheltered plot, not every green target.

## 39 · Sporevault (F013, tier 2)
- Identity: Wood / Yang, locked ordinary rarity; signature 51
- Silhouette: An upright long-hindleg pika with a closed pinecone tail carried above its head and a tiny chest between large open arm spaces.
- Locomotion: Crouch, tall hop, two-foot settle; tail opens only during casting.
- Field: grow_roots; tagged targets only
- Combat role: Remote falling strike
- Cone Drop: Aimed visible 12px landing marker within48px; one falling cone hits after16 updates, with line of sight checked at aim and impact.
- Timing: startup/active/recovery/cooldown 16/6/18/120; live objects≤1; total target budget≤24 Q4
- Stat weights: {'vitality': 45, 'power': 43, 'guard': 46, 'focus': 55, 'haste': 51} = 240; verify actual consumers before balancing
- Acquisition: Explicit 37→39 choice after owning-family trial 2; defer is unchanged.
- Learned commands: 49@1, 51@26
- Evolution: 37→39, level26/bond45, MAGMA_READY, family-local key2 (required mask2), sanctuary and explicit target confirmation
- Trial ‘Scatter the Canopy’: Grow two elevated seed supports after manually opening the airflow hood; carry the marked seed tray by the open upper walkway.

## 40 · Chalklung (F014, tier 1)
- Identity: Water / Yang, locked ordinary rarity; signature 52
- Silhouette: A living porous sponge with three soft lobed feet, one angled chimney and a friendly face on its lower flexible skirt.
- Locomotion: Three-foot rocking walk; chimney compresses and rebounds as it breathes.
- Field: fill_basin, reveal_current; tagged targets only
- Combat role: Stopping a charge
- Mist Stop: A short square puff at28px arrests one eligible ordinary rush without pulling the player; one target hit per cast.
- Timing: startup/active/recovery/cooldown 8/12/14/90; live objects≤1; total target budget≤16 Q4
- Stat weights: {'vitality': 37, 'power': 28, 'guard': 37, 'focus': 46, 'haste': 32} = 180; verify actual consumers before balancing
- Acquisition: Read the three ripple marks and manually unclog the public catch bowl; a sponge walks out of the dry side niche.
- Learned commands: 52@1

## 41 · Bellcup (F014, tier 2)
- Identity: Water / Yang, locked ordinary rarity; signature 53
- Silhouette: A tall sponge with an inverted bell mouth, a long curved neck, broad two-lobed base and a face looking out beneath the rim.
- Locomotion: Leans forward on the base, straightens neck, then draws the base underneath.
- Field: fill_basin, reveal_current; tagged targets only
- Combat role: Vertical lane control
- Cup Shower: A stationary narrow three-drop column falls at a visible marker; all drops share24Q4 maximum per target.
- Timing: startup/active/recovery/cooldown 12/30/18/120; live objects≤3; total target budget≤24 Q4
- Stat weights: {'vitality': 49, 'power': 40, 'guard': 49, 'focus': 58, 'haste': 44} = 240; verify actual consumers before balancing
- Acquisition: Explicit 40→41 choice after owning-family trial 1; defer is unchanged.
- Learned commands: 52@1, 53@26
- Evolution: 40→41, level26/bond45, MAGMA_READY, family-local key1 (required mask1), sanctuary and explicit target confirmation
- Trial ‘Keep the Last Drop’: Reveal the feeding current, fill the catch bowl and close two leaks before draining the practice outlet; targets have distinct shapes.

## 42 · Runnelribbon (F014, tier 2)
- Identity: Water / Yang, locked ordinary rarity; signature 54
- Silhouette: A flat ribbon sponge with two raised breathing sails, four stub feet and a living face at one blunt leading corner.
- Locomotion: Sideways inchworm fold, unfold and soft skirt sweep.
- Field: fill_basin, reveal_current; tagged targets only
- Combat role: Lateral crossing interception
- Ribbon Sweep: A45px lateral water band travels along one wall-checked segment; widens only after its first12px. Single target budget24Q4.
- Timing: startup/active/recovery/cooldown 10/20/20/120; live objects≤1; total target budget≤24 Q4
- Stat weights: {'vitality': 49, 'power': 40, 'guard': 49, 'focus': 58, 'haste': 44} = 240; verify actual consumers before balancing
- Acquisition: Explicit 40→42 choice after owning-family trial 2; defer is unchanged.
- Learned commands: 52@1, 54@26
- Evolution: 40→42, level26/bond45, MAGMA_READY, family-local key2 (required mask2), sanctuary and explicit target confirmation
- Trial ‘Share the Runnel’: Reveal both branch arrows and fill alternating receiving bowls without feeding the already-full trough; no timer or random rain.

## 43 · Orelet (F015, tier 1)
- Identity: Metal / Yin, locked ordinary rarity; signature 55
- Silhouette: A round mole with a pale snout, narrow metallic digging nails and one smooth ore nodule at the tip of its very short tail.
- Locomotion: Alternating outward forepaw scoops with its feet visibly above the ground.
- Field: draw_ore; tagged targets only
- Combat role: Close approach interruption
- Pick Tap: Two short alternating nail jabs; second occurs only if first misses, so one enemy cannot take both.
- Timing: startup/active/recovery/cooldown 6/12/16/90; live objects≤2; total target budget≤20 Q4
- Stat weights: {'vitality': 32, 'power': 45, 'guard': 38, 'focus': 32, 'haste': 33} = 180; verify actual consumers before balancing
- Acquisition: Return two visibly labeled loose ore samples to their matching shelf shapes; the mole leaves its inspection basket.
- Learned commands: 55@1

## 44 · Augermole (F015, tier 2)
- Identity: Metal / Yin, locked ordinary rarity; signature 56
- Silhouette: A long wedge-bodied mole whose broad serrated forepaws frame a low face; its body tapers into a small straight tail.
- Locomotion: Wide shoulder crawl with nails swept behind during recovery.
- Field: draw_ore; tagged targets only
- Combat role: Armor-window punish
- Spiral Notch: A narrow28px corkscrew strike; deals ordinary Metal damage with bounded stagger on an already vulnerable target. No armor bypass.
- Timing: startup/active/recovery/cooldown 14/8/22/120; live objects≤1; total target budget≤28 Q4
- Stat weights: {'vitality': 44, 'power': 57, 'guard': 50, 'focus': 44, 'haste': 45} = 240; verify actual consumers before balancing
- Acquisition: Explicit 43→44 choice after owning-family trial 1; defer is unchanged.
- Learned commands: 55@1, 56@26
- Evolution: 43→44, level26/bond45, MAGMA_READY, family-local key1 (required mask1), sanctuary and explicit target confirmation
- Trial ‘True the Buried Seam’: Draw three sample pins out in the diagrammed direction while the protected pot is behind its baffle; each pin has an independent identity.

## 45 · Pendulumole (F015, tier 2)
- Identity: Metal / Yin, locked ordinary rarity; signature 57
- Silhouette: An upright mole with long forearms, broad planted hindfeet and an elongated heavy tail curved into a counterweight loop.
- Locomotion: Two hindfoot steps then tail counter-swing; face aims independently of arms.
- Field: draw_ore; tagged targets only
- Combat role: Delayed flanking shot
- Tail Pendulum: A short visible diagonal swing releases one18px lateral shard; swing and shard share24Q4, walls stop both.
- Timing: startup/active/recovery/cooldown 16/20/16/120; live objects≤2; total target budget≤24 Q4
- Stat weights: {'vitality': 44, 'power': 57, 'guard': 50, 'focus': 44, 'haste': 45} = 240; verify actual consumers before balancing
- Acquisition: Explicit 43→45 choice after owning-family trial 2; defer is unchanged.
- Learned commands: 55@1, 57@26
- Evolution: 43→45, level26/bond45, MAGMA_READY, family-local key2 (required mask2), sanctuary and explicit target confirmation
- Trial ‘Balance the Hanging Note’: Draw two counterweights to opposite marked rests until the hanging clapper clears both sides; the player can inspect its entire swing.

## 46 · Ashkite (F016, tier 1)
- Identity: Fire / Yang, locked ordinary rarity; signature 58
- Silhouette: A planthopper with a broad kite-shaped shell, very short antennae, tucked legs and a visible round face below a shallow hood.
- Locomotion: Tiny spring hop, side slip and four-foot landing.
- Field: turn_vane; tagged targets only
- Combat role: Angled opener
- Cinder Tilt: One26px diagonal dart from the chosen facing side, with a readable aiming blink; stops at first wall or enemy.
- Timing: startup/active/recovery/cooldown 8/10/12/90; live objects≤1; total target budget≤16 Q4
- Stat weights: {'vitality': 30, 'power': 44, 'guard': 26, 'focus': 45, 'haste': 35} = 180; verify actual consumers before balancing
- Acquisition: Set a public wind hood away from the seedling bed using its handle, then approach the hopper shelter.
- Learned commands: 58@1

## 47 · Plumehopper (F016, tier 2)
- Identity: Fire / Yang, locked ordinary rarity; signature 59
- Silhouette: A tall long-legged hopper with a narrow upright plume, a pear-shaped abdomen and an open diamond between its rear legs.
- Locomotion: High tucked-leg spring, upright hover beat and heel-first landing.
- Field: turn_vane; tagged targets only
- Combat role: Cross-lane follow-through
- Plume Cut: A narrow rising slash then a forward falling slash; shared24Q4 target cap, no auto-tracking after startup.
- Timing: startup/active/recovery/cooldown 12/18/18/120; live objects≤2; total target budget≤24 Q4
- Stat weights: {'vitality': 42, 'power': 56, 'guard': 38, 'focus': 57, 'haste': 47} = 240; verify actual consumers before balancing
- Acquisition: Explicit 46→47 choice after owning-family trial 1; defer is unchanged.
- Learned commands: 58@1, 59@26
- Evolution: 46→47, level26/bond45, MAGMA_READY, family-local key1 (required mask1), sanctuary and explicit target confirmation
- Trial ‘Lift the Warm Air’: Turn three hood vanes to lift a visible ribbon through upper outlets without blowing on the seedling bed.

## 48 · Huskdrifter (F016, tier 2)
- Identity: Fire / Yin, locked ordinary rarity; signature 60
- Silhouette: A broad leaf-shaped hopper held horizontally beneath translucent folded shell sails, with a small face extending beyond their front edge.
- Locomotion: Low skirt-like glide with visible occasional leg taps; not a permanent flight permission.
- Field: turn_vane; tagged targets only
- Combat role: Protective interruption
- Ash Screen: A stationary small screen consumes one ordinary hostile projectile, expires after40 updates, then makes a16Q4 outward puff. Boss beams unaffected.
- Timing: startup/active/recovery/cooldown 14/40/18/120; live objects≤1; total target budget≤16 Q4
- Stat weights: {'vitality': 42, 'power': 56, 'guard': 38, 'focus': 57, 'haste': 47} = 240; verify actual consumers before balancing
- Acquisition: Explicit 46→48 choice after owning-family trial 2; defer is unchanged.
- Learned commands: 58@1, 60@26
- Evolution: 46→48, level26/bond45, MAGMA_READY, family-local key2 (required mask2), sanctuary and explicit target confirmation
- Trial ‘Settle the Ash’: Turn the hood down into a settling basket, open its safe side bypass and return the hood to still; visible ash clears rather than becoming a damage cloud.

## 95 · Screepeek (F036, tier 1)
- Identity: Earth / Yin, locked ordinary rarity; signature 61
- Silhouette: A stocky tapir with a short mobile trunk, small round ears, heavy hindquarters and three pale pebble pads along its shoulder.
- Locomotion: Slow alternating four-foot stroll; trunk probes ahead on the idle beat.
- Field: uncap_well; tagged targets only
- Combat role: Close sweeping attack
- Gravel Sift: A short fan of three ground chips, sharing20Q4 per target; maximum travel30px and wall stops per chip.
- Timing: startup/active/recovery/cooldown 10/12/12/90; live objects≤3; total target budget≤20 Q4
- Stat weights: {'vitality': 44, 'power': 33, 'guard': 43, 'focus': 30, 'haste': 30} = 180; verify actual consumers before balancing
- Acquisition: Uncover a clearly marked shallow spring lip with its A-operated brush; broad tracks lead to the waiting tapir.
- Learned commands: 61@1

## 96 · Stairtrunk (F036, tier 2)
- Identity: Earth / Yin, locked ordinary rarity; signature 62
- Silhouette: A long-trunked tapir with stepped flaring ears, high shoulders and low hindquarters, leaving a clear diagonal back silhouette.
- Locomotion: Forefoot reach, trunk curl, broad rear step; ears fold on recovery.
- Field: uncap_well; tagged targets only
- Combat role: Reliable reach tradeoff
- Terrace Lift: A sequence of two rising28px wedges separated by a safe lateral gap; one hit per target across both, no forced boss movement.
- Timing: startup/active/recovery/cooldown 16/20/20/120; live objects≤2; total target budget≤24 Q4
- Stat weights: {'vitality': 56, 'power': 45, 'guard': 55, 'focus': 42, 'haste': 42} = 240; verify actual consumers before balancing
- Acquisition: Explicit 95→96 choice after owning-family trial 1; defer is unchanged.
- Learned commands: 61@1, 62@26
- Evolution: 95→96, level26/bond45, MAGMA_READY, family-local key1 (required mask1), sanctuary and explicit target confirmation
- Trial ‘Find the Cold Seam’: Uncap three signposted spring mouths in separate pockets after observing their distinct bubbles; one dry inspection socket must be left closed.

## 97 · Mossmarch (F037, tier 1)
- Identity: Wood / Yang, locked ordinary rarity; signature 63
- Silhouette: A short six-legged caterpillar-like animal with a square muzzle, four separated moss cushions and a bare expressive brow.
- Locomotion: Six legs ripple in three pairs while cushions squash in sequence.
- Field: reel_load; tagged targets only
- Combat role: Moving narrow pressure
- Sprig March: One slow ground bud advances36px with a visible toe-like motion; it ends on first enemy or wall rather than lingering.
- Timing: startup/active/recovery/cooldown 10/24/12/90; live objects≤1; total target budget≤16 Q4
- Stat weights: {'vitality': 33, 'power': 31, 'guard': 34, 'focus': 43, 'haste': 39} = 180; verify actual consumers before balancing
- Acquisition: Inspect the moving moss along a frayed drying-line guide; solve the manual two-hook return and invite the crawler.
- Learned commands: 63@1

## 98 · Trellislong (F037, tier 2)
- Identity: Wood / Yang, locked ordinary rarity; signature 64
- Silhouette: A long high-arched six-legged crawler with an open lattice of connected moss ribs above its smooth living underside and wide face.
- Locomotion: Three alternating leg pairs carry a traveling body arch, never a static stretched base sprite.
- Field: reel_load; tagged targets only
- Combat role: Bent approach control
- Trellis Bend: Two connected ground segments form one chosen L-shaped path, capped48px total; one hit per target and no wall penetration.
- Timing: startup/active/recovery/cooldown 14/30/16/120; live objects≤2; total target budget≤24 Q4
- Stat weights: {'vitality': 45, 'power': 43, 'guard': 46, 'focus': 55, 'haste': 51} = 240; verify actual consumers before balancing
- Acquisition: Explicit 97→98 choice after owning-family trial 1; defer is unchanged.
- Learned commands: 63@1, 64@26
- Evolution: 97→98, level26/bond45, MAGMA_READY, family-local key1 (required mask1), sanctuary and explicit target confirmation
- Trial ‘The Cloth Stays Clear’: Reel the drying line through three marked hooks from different safe approaches while a wide worker passage remains unobstructed.

## 99 · Dripurchin (F038, tier 1)
- Identity: Water / Yin, locked ordinary rarity; signature 65
- Silhouette: A low sea-urchin-like animal with a soft visible face, five blunt movable spines and three rounded tube feet.
- Locomotion: Rotates its feet without rotating its face, then bobs with gathered droplets.
- Field: tune_latch; tagged targets only
- Combat role: Radial safe-distance lesson
- Bead Step: Three small outward beads leave large gaps; one enemy can receive only16Q4 across the fan. No homing.
- Timing: startup/active/recovery/cooldown 10/14/12/90; live objects≤3; total target budget≤16 Q4
- Stat weights: {'vitality': 37, 'power': 28, 'guard': 37, 'focus': 46, 'haste': 32} = 180; verify actual consumers before balancing
- Acquisition: Finish the optional Listening Stones discovery commission, then open the indicated quiet catch. The urchin is visible behind the grille before release.
- Learned commands: 65@1

## 100 · Dewmedusa (F038, tier 2)
- Identity: Water / Yin, locked ordinary rarity; signature 66
- Silhouette: A tall soft-bodied urchin with its five spines opened into curved umbrella ribs and long joined tube-foot tassels; face hangs below the cap.
- Locomotion: Gentle pulse-lift then trailing-foot settle; a grounded shadow makes its location legible.
- Field: tune_latch; tagged targets only
- Combat role: Center-out reposition cue
- Dewfold: An expanding five-lobed ring shows safe gaps before moving; edge-only24Q4 once per target, never a full-screen burst.
- Timing: startup/active/recovery/cooldown 18/24/18/120; live objects≤1; total target budget≤24 Q4
- Stat weights: {'vitality': 49, 'power': 40, 'guard': 49, 'focus': 58, 'haste': 44} = 240; verify actual consumers before balancing
- Acquisition: Explicit 99→100 choice after owning-family trial 1; defer is unchanged.
- Learned commands: 65@1, 66@26
- Evolution: 99→100, level26/bond45, MAGMA_READY, family-local key1 (required mask1), sanctuary and explicit target confirmation
- Trial ‘The Quiet Chord’: Tune three mechanically distinct catches after placing sound baffles on their pictogram rests; the source is geometry and vibration cues, not hearing acuity.

