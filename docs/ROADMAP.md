# Adventure Legends development roadmap

## Direction and current state

An original, bright native-GBA action adventure with readable full-screen worlds,
responsive sword/lance/bow combat, four-slot field companions, evolution, regional
puzzles, discoveries, equipment and side quests. The finite target is **128 forms**,
including evolved forms. “Mail” is the working interpretation of body armor.
Neither a reserved row nor a palette swap counts as a playable monster.

The Magma milestone implements **65 obtainable forms in 30 families, 46 areas,
38 quests and 31 equipment items**. A controller-earned complete collection keeps
34 real individuals: evolution changes an individual, while alternate branches
require another actual encounter. All 65 histories, 15 new evolution edges and
24 new commands have native acceptance gates. See [VERIFICATION.md](VERIFICATION.md)
for the exact cartridge, completed checks and remaining limitations.

The catalog has 66 authored designs, 65 enabled forms and no obtainable legendary.
Underwater design documents describe a later batch; those designs do not count as
implemented, obtainable or verified. Physical hardware remains untested.

## Delivered foundation

- Continuous 480×320 exploration, normalized diagonal motion, camera easing,
  companion following, directional animation and floating corner HUD
- Three-lantern campaign, ending and postgame exploration, retained as a foundation
  within the larger adventure rather than a claim that the expanded game is finished
- Sword, lance and bow; body, boots, belt and ring parameters; meaningful sidegrades
- Four actual-instance party slots; hold L plus a direction and release to switch,
  B to cancel, short L to cycle; assignment from the owned collection in the journal
- Explicit personal trials, learned commands, evolution choice and stable identities
- Wood, Fire, Earth, Metal and Water plus independent Yin/Yang; numerical combat
  multipliers are original game rules, not traditional doctrine
- River, Northern harbor, Southern island and Magma mountain chapters with distinct
  towns, field activities, recoverable puzzles and non-repeating quest rewards
- Save-format 2–4 migration and unchanged Save5 wire layout; frozen content revisions
  1–4, current revision 5, interrupted-write recovery and no fabricated acquisition

## Latest milestone: Magma mountain

Eight connected areas, two guaranteed pre-gate companions, three multiroom mechanism
stages and a regulator encounter. The optional route adds ecological invitations,
fifteen individual-bound trials, two third tiers and four alternate evolutions.
Six gear rewards and eight quests augment the existing adventure. Public clues,
reset controls, town return and starter-weapon completion remain available.

The art uses pale terraces, moss, ceramic channels, work canopies, a pottery workshop
and a spring grotto. The three industrial mechanism rooms share visual materials and
are intentionally sparse; greater narrative/environmental density remains worthwhile.
All eight native scenes are reviewed, not just the player-facing town preview.

Capacity admission reserves the full planned topology's 72 terminal opportunities
within 160 individual slots. Legal old over-budget rosters remain loadable/saveable;
this does not promise that every such roster can recover every future opportunity.
History never clones an individual. Per-form masks prevent impossible earlier-tier
trial evidence, and branch UI validates the actual roster before confirmation.

## Finite remaining milestones

1. **Underwater town and memory archive: 89 forms.** Eight planned families / 24 forms,
   24 commands, 16 personal trials, eight areas and eight quests. Acoustic and buoyancy
   companions teach the main route before gates. No oxygen-pressure punishment.
   Freeze revision-5 historical policy before enabling revision 6. Native acquisition,
   repeat encounters, all branch orders, save migration and cadence must pass.
2. **First return journey: 104 forms.** Revisit earlier regions with meaningful new
   routes, NPC consequences and discoveries. New rewards must integrate with existing
   powers, never require opaque pixel hunting or mandatory grinding.
3. **Second return journey: 120 forms.** Complete ordinary families and regional story
   threads, strengthen encounter/puzzle variety and test every obtainable terminal path.
4. **Eight legendary forms: 128.** Original rare, powerful companions with discoverable,
   finite acquisition conditions and narrative payoff. No impossible odds or paywalls.
5. **Integrated release.** Complete ending/return behavior, balance, onboarding, hint
   clarity, full collection graph, localization and comprehensive regression/hardware QA.

These are explicit planned counts, not current content or a measured playtime promise.
The full planned budget is 72 retained terminal individuals, 64 quest IDs and 48 item
slots. Namespace demand must be reviewed before each batch; never truncate trial bits,
shift beyond capability words or silently reinterpret a released family.

## Gates for every milestone

Report designed, implemented, normally obtainable and verified counts separately.
Each form needs original art, animation, a useful role, acquisition and tested powers.
Each region needs a coherent entrance-to-exit route, meaningful NPC/quest activity,
visual landmarks and recoverable multiroom puzzles. Required companions precede gates.

- Exact-ROM full and minimal routes, all new acquisitions/evolutions, optional rewards,
  repeated/reset interactions, death/retry, cold reboot and old-region return
- Save migrations from authenticated delivered fixtures; malformed and interrupted
  transactions; historical policy cannot be legalized by the expanded live catalog
- Native 240×160 pixel/OAM checks and actual emulated update/page-flip cadence, including
  crowded combat, full earned roster, cold menus and saving; host FPS is irrelevant
- ROM under 32 MiB and explicit EWRAM/IWRAM/OBJ/stack budgets; limited cold-menu and
  IWRAM headroom demand fresh measurement after new content or audio
- Deterministic editable source, clean rebuild, spoiler-free player teaser/guide and
  honest evidence distinguishing host models, emulator acceptance and physical hardware

Each meaningful milestone is reviewed against an exact source snapshot before delivery.
Repository publication/review/merge follows the owner's authorized workflow when access
is available. A local acceptance result does not imply a remote PR or merge exists.
