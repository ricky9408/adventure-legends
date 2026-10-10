# Adventure Legends development roadmap

## Direction and current state

An original, bright native-GBA action adventure with readable full-screen worlds,
responsive sword/lance/bow combat, four-slot field companions, evolution, regional
puzzles, hinted discoveries, equipment and side quests. The finite target is
**128 forms including evolutions**. A reserved row or a palette swap does not
count as a playable monster. Body armor is the interpretation of mail.

The expanded narrative also takes high-level story-structure inspiration from
The Lord of the Rings: an original fellowship journey with personal and
community stakes and a changed homecoming. [Narrative requirements](NARRATIVE_REQUIREMENTS.md)
separate the requested inspiration from concrete authoring choices and future
implementation. Delivered H remains unchanged.

**Prior delivered milestone: Return I plus original music, build H.** Its complete six-stage controller
recipe passes, as do companion/art/control, pixel, memory and Return host gates.
The complete retained-game gates pass; source-export verification is recorded
separately with the delivered archive.
H implements **104 obtainable forms in 40 families, 62 areas, 54 quests and
42 equipment items**. The full route retains 52 real individuals. Its 22,285
assertions include all 13 new personal trials/evolutions; both minimal arm
orders, lifecycle, repeat encounters and editing/viewing controls also pass.
The six stages sample 172,383 active hardware frames with zero missed updates
or displayed-page flips. See [the combined H verification](VERIFICATION-RETURN-H.md); original G results remain historical evidence.

Shared Horizons build C passes its clean four-stage native controller matrix:
120 enabled forms in 52 families, 70 areas, 60 quests and 46 equipment items.
The full route retains 64 individuals; twelve repeat encounters retain 76.
All 173,201 strict hardware frames meet the update, page-flip, OAM and audio
contract. The exported-source build, complete retained suites and generator roundtrip pass.
The catalog contains one additional disabled legendary draft. Reserved
identities and that draft are not obtainable. The Shared Horizons C Library delivery is confirmed; H remains its immutable
predecessor.
The expanded game and final collection remain unfinished. No final playtime or
commercial-game level of polish is claimed.

## Implemented foundation

- Scrolling 480×320 maps and smaller native rooms, normalized diagonal movement,
  eased camera, companion following, directional animation and floating corner
  controls within the full 240×160 viewport
- The original three-lantern campaign, ending and postgame, extended by River,
  Northern harbor, Southern island, Magma mountain, Underwater and Return content
- Sword, lance and bow; body, boots, belt and ring parameters and sidegrades
- Four real-instance party slots: hold L, choose a direction, release to switch;
  B cancels, a short L cycles, and journal assignment keeps every owned companion
- Personal trials, learned commands, optional explicit evolution and stable IDs
- Wood, Fire, Earth, Metal and Water plus separate Yin/Yang polarity; numerical
  combat multipliers are original game rules, not traditional doctrine
- Migration from save formats 2–4 and Save5 content revisions 1–8 into content9,
  without changing the wire layout or reinterpreting historical validation rules

## Return I: the roads we left open

Eight areas (54–61) connect familiar communities to new places and requests.
Fifteen enabled forms, fifteen commands (91–105), thirteen personal trials and
optional evolution edges, two new families, eight quests (46–53) and five gear
sources complete this chapter. Required companions precede their gates. The
minimal route uses guaranteed companions and starter gear without optional
training or evolution.

The new locations have orchard, loft, garden, harbor, terrace, landing, map-room
and causeway identities, with readable paths and reversible mechanisms. The
journal gives hints without exposing engine details. Viewing the journal or
selector freezes simulation and preserves a trial; real party/identity/command
changes can revoke the action without refunding its cooldown.

Player media contains familiar scenery and controls, not puzzle solutions,
rare encounters or endings. H includes the two original themes as a synthesized
GBA PCM arrangement with native audio captures and transport tests. It is not
a Mac orchestral/voice render; human listening and physical hardware remain untested.

## Finite remaining milestones

The final-eight implementation now passes the exact-E ten-report native matrix:
128 forms, 78 areas, 64 quests and 48 gear entries, including both minimal
endings and later optional invitations. The full collection route retains 72
individuals. Final packaging and external delivery/publication have separate
receipts. [Final verification](VERIFICATION-COVENANTS.md).

1. **Shared Horizons: 120 ordinary forms.** Add forms 105–120, completing four
   two-form families and eight single-form families. Finish their original art,
   distinct powers and actual encounter/evolution paths. Six quests (54–59) and
   four equipment choices (42–45) must support new narrative and interaction
   motifs rather than repeat the Return I room sequence. Planned full-route
   retention is 64 individuals across 52 families.
2. **Eight legendary covenants: 128 forms.** Forms121–128 are eight complete
   families with distinct finite, discoverable trials and narrative rewards.
   Quests 60–63 and gear 46–47 remain reserved. No impossible random odds,
   mandatory payment, trading service or external clock requirement. Planned
   full-route retention is 72 individuals across 60 families.
3. **Integrated release.** Finish narrative and return behavior, balance,
   onboarding, clue clarity, localization, collection graph, soundtrack and
   comprehensive regression/resource review. Physical-hardware testing remains
   a separate unperformed check; emulator evidence must not imply it happened.

Shared Horizons C is implemented and passes exact-ROM and exported-source
acceptance. Delivery and source publication have separate receipts. The eight
legendary covenants, homecoming and integrated native/host gates pass on E.
The exported archive and external delivery/publication remain separately verified. The original
capacity remains 160 individuals, 72 protected
terminal opportunities, 64 quest IDs and 48 gear slots. There are 88 possible extra
copies within that terminal reservation. Some legally accepted historical
rosters can already exceed the new opportunity budget; preserving their saves
is not a promise that every such roster can recover every future opportunity.

Ability 12 is implemented for form121. Ordinary Return II commands 106–121 and the
remaining legendary commands 122–128 must not collide or silently repurpose old
identities, trial bits, capability words or released policy rows.

## Resource and performance limits

The content-only G baseline is 11,820,208 bytes, within the 32 MiB cartridge window. Its increase over delivered
Underwater is 2,043,032 bytes, inside the original 2 MiB chapter target with 54,120
bytes remaining. EWRAM occupied span is 51,380 bytes, an increase of 1,524 within
its 4 KiB target. IWRAM code is 26,856 bytes, a reduction of 1,576; it ends 1,816 bytes
before the 0x03007000 stack floor. The 3,840-byte SYSTEM stack reserve is unchanged.

A startup-only paired diagnostic observes 936 bytes of overwritten SYSTEM extent
and 2,904 bytes of unchanged prefix across its exercised paths. This is not true
minimum SP, an exhaustive call-chain bound or physical-hardware safety proof.
H adds 1,499,468 ROM bytes, 8,504 EWRAM bytes and 592 IWRAM bytes. Its total is
13,319,676 ROM bytes, 59,884 EWRAM bytes and 27,448 IWRAM bytes, with 1,224 bytes
before the stack floor. Audio has separate native queue/IRQ/stack acceptance;
the original content-only budget does not cover this addition. H observations
include 936/3,840 SYSTEM bytes, 32/160 IRQ bytes and 0/64 SVC bytes. Future
content requires renewed accounting and native checks.

Cold Continue is a recorded blocking load transition. Every observed active
play, menu, dialogue, evolution and incremental-save frame must still update
and flip once. The render-cycle register alone can miss later presentation
cost; the update-and-flip gate is mandatory. Host FPS is not acceptance evidence.

## Gates for every milestone

Report designed, enabled, obtainable and actually verified counts separately.
Every form needs original art/animation, a useful role, an obtainable path and
real field/combat tests. Each region needs meaningful NPC activity, recognizable
landmarks and recoverable puzzles. Required companions precede their gates.

- Exact-ROM full/minimal routes, genuine acquisitions/evolutions, optional
  rewards, repeated/reset interactions, death/retry, cold reboot and old-region return
- Authenticated prior-save migrations; malformed and interrupted transactions;
  no legalization of historical data through a newer live catalog
- Native screen/OAM and actual hardware-frame cadence checks, including crowded
  combat, the full earned roster, cold menus and bounded saving
- ROM/EWRAM/IWRAM/OBJ/stack accounting, negative link probes and qualified canaries
- Deterministic editable source, generator roundtrip, clean rebuild, bounded
  source fragments and spoiler-free player media

Review an exact source snapshot before delivery. Artifact delivery and GitHub
publication have separate receipts; no local result alone proves a remote PR or
merge. Historical chapter documents and failed diagnostic evidence retain their
original scope. Source publication uses only the personal ricky9408 account.
