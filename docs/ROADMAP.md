# Adventure Legends development roadmap

## Direction and current state

An original, bright native-GBA action adventure with readable full-screen worlds,
responsive sword/lance/bow combat, four-slot field companions, evolution, regional
puzzles, discoveries, equipment and side quests. The finite target is **128 forms**,
including evolved forms. “Mail” is the working interpretation of body armor.
Neither a reserved row nor a palette swap counts as a playable monster.

**Current tested milestone: Underwater, build K.**
It implements **89 obtainable forms in 38 families, 54 areas, 46 quests and
37 equipment items**. A completed controller-earned collection route retains
50 real individuals and 89 historical forms. Evolution changes an individual;
an alternate branch requires another genuine encounter. The full route passes
10,940 checks, including all 16 new trial/evolution paths and eight repeat
encounters. The minimal main route passes 761 checks. Independent minimal cold lifecycle (1,187 checks), synthetic engine integration
(147 checks and 14,832 mutation rejections), final-source stack observations and
the player teaser also pass within their stated scopes. All eight native scenes
have been visually reviewed, and a source-export preflight clean-builds exactly.
All 138 top-level combat/control/stress cases also pass. Host, same-K Magma native, full retained whole-game regression and all eight stages
of the shipped Underwater native recipe pass. A separately accompanying sealed
export receipt records the final delivered source archive and its verification. See
[VERIFICATION-UNDERWATER.md](VERIFICATION-UNDERWATER.md).

The assembled catalog has **90 authored designs**, 89 enabled forms, 128 stable
identity slots and no obtainable legendary. This distinguishes designed content,
runtime content and normally earned route evidence. Physical hardware remains
untested; the project and final campaign are not complete.

## Delivered foundation and current extension

- Continuous exploration on scrolling 480×320 maps and smaller native rooms,
  normalized diagonal movement, camera easing, companion following, directional
  animation and a floating corner HUD within the full 240×160 viewport
- Three-lantern campaign, ending and postgame exploration retained as a foundation
  within the larger adventure, rather than a claim that the expanded game is finished
- Sword, lance and bow; body, boots, belt and ring parameters; meaningful sidegrades
- Four actual-instance party slots; hold L plus a direction and release to switch,
  B to cancel, short L to cycle; owned collection assignments in the journal
- Personal trials, learned commands, explicit evolution choices and stable identities
- Wood, Fire, Earth, Metal and Water plus independent Yin/Yang; numerical battle
  multipliers are original game rules, not traditional doctrine
- River, Northern harbor, Southern island and Magma mountain chapters, now extended
  by the Underwater milestone with distinct towns, recoverable puzzles and side quests
- Save-format 2–4 migration and unchanged Save5 wire layout; frozen content revisions
  1–5, current revision 6, interrupted-write recovery and no fabricated acquisition

## Latest tested milestone: Underwater town and memory archive

Eight connected areas (46–53), eight families (24 forms), 24 commands (67–90),
16 individual-bound branch trials, eight quests (38–45) and six gear sidegrades.
The main route supplies its acoustic and buoyancy companions before their gates.
It does not require evolution, optional training, armor or an oxygen system.
Eight repeat encounters create new individuals for alternate branches; history
never clones an individual or replaces a retained companion.

The region uses pearl, coral, jade and warm brass, with a lived-in town, listening
places, kelp passages and a memory archive. Four 480×320 maps and four 240×160
rooms support distinct exploration, reversible mechanisms and return routes.
Player-facing material stays clear of puzzle solutions, rare encounters and endings.
The soundtrack remains original PSG; orchestral or voice integration is not delivered.

The unchanged roster capacity is 160 individuals. Admission reserves the planned
72 terminal opportunities. Legally accepted older over-budget rosters remain
loadable/saveable; that does not promise that every such roster can recover every
future opportunity. Frozen historical policies are not reinterpreted by the live catalog.

## Finite remaining milestones

1. **First return journey: 104 forms.** Revisit earlier regions with meaningful new
   routes, NPC consequences and discoveries. Rewards must integrate with existing
   powers, without opaque pixel hunting or mandatory grinding.
2. **Second return journey: 120 forms.** Complete ordinary families and regional story
   threads, strengthen encounter/puzzle variety and test every obtainable terminal path.
3. **Eight legendary forms: 128.** Original rare, powerful companions with discoverable,
   finite acquisition conditions and narrative payoff. No impossible odds or paywalls.
4. **Integrated release.** Complete ending/return behavior, balance, onboarding, hint
   clarity, full collection graph, localization and comprehensive regression/hardware QA.

These are explicit planned counts, not current content or measured playtime promises.
This current sequence supersedes earlier draft batching in archived design documents.
The full planned capacity budget remains 72 retained terminal individuals, 64 quest IDs
and 48 item slots. Review namespace demand before every batch; never truncate trial bits,
shift beyond capability words or silently reinterpret a released family.

## Resource and performance limits

Candidate K is 9,777,176 bytes, within the 32 MiB cartridge window. Its growth over
Magma is 2,281,256 bytes: the original 2 MiB chapter target was exceeded by 184,104
bytes. The revised engineering budget is explicitly **2.5 MiB**, leaving 340,184
bytes for this chapter. This is a budget change, not an original-target pass.

IWRAM code ends at `0x03006f10`, only 240 bytes before the reserved SYSTEM stack
floor at `0x03007000`; retain the 3,840-byte stack reserve. EWRAM data plus BSS is
49,856 bytes. Stack canary observations measure only the overwrite extent of
exercised paths, not true minimum SP or exhaustive physical-hardware safety.
Future regions or music must repeat final-source memory and cadence checks.

Cold Continue can take 52 emulated hardware frames and is explicitly a blocking
load transition outside active cadence. Every measured active-play, menu, dialogue,
evolution and incremental-save window must still update and flip once per hardware
frame. A host FPS number or a successful load alone cannot establish this.

## Gates for every milestone

Report designed, implemented, normally obtainable and verified counts separately.
Each form needs original art, animation, a useful role, acquisition and tested powers.
Each region needs a coherent entrance-to-exit route, meaningful NPC/quest activity,
visual landmarks and recoverable multiroom puzzles. Required companions precede gates.

- Exact-ROM full/minimal routes, all acquisitions/evolutions, optional rewards,
  repeated/reset interactions, death/retry, cold reboot and old-region return
- Save migrations from authenticated delivered fixtures; malformed and interrupted
  transactions; historical policy cannot be legalized by the expanded live catalog
- Native 240×160 pixel/OAM checks and actual update/page-flip cadence, including
  crowded combat, the full earned roster, cold menus and incremental saving
- Explicit ROM/EWRAM/IWRAM/OBJ/stack budgets, link-limit probes and qualified canaries
- Deterministic editable source, generator roundtrip, clean rebuild, bounded text
  files below 90,000 bytes, spoiler-free player media and honest evidence that
  distinguishes host models, emulator acceptance and physical hardware

Each meaningful milestone is reviewed against an exact source snapshot before delivery.
Underwater repository publication is paused. No remote PR, push or merge is claimed.
Local acceptance and artifact delivery are distinct from repository publication.
Historical chapter documents and failed diagnostic evidence retain their original scope.
