# Emberbond: Lantern Trails

Emberbond is a walking adventure about a young lantern keeper and companions
who reconnect places that have forgotten how to welcome one another. A light
kept behind a locked door cannot guide anyone home. The player's work makes
that idea tangible: grow a crossing, reopen a harbor, warm a kiln, and return
to someone whose day has changed.

This redesign builds on the existing nine-chapter adventure. The 78 areas,
companion families, equipment, earned relationships, and revision-13 saves
remain part of the game. The design changes their presentation and the clarity
of their purpose, rather than adding another chapter to explain the theme.

## References and interpretation

- [Shigeru Miyamoto's 1998 interview](https://shmuplations.com/miyamotodesign/)
  informs the emphasis on enjoyable movement, curiosity, generous rules, and
  expressive representation. The hiking analogy becomes paths, landmarks,
  small discoveries, and a reason to return home.
- [Sprite Fusion's effect workflow](https://www.spritefusion.com/blog/how-to-make-good-pixel-art-effects-with-claude)
  informs code-authored variants, visible iteration, and deliberate motion
  timing. Art is reviewed at the actual handheld resolution as well as enlarged.
- [Game Design Principles](https://github.com/agent-skills-hub/agent-skills-hub/blob/main/skills/game-development/game-design/SKILL.md)
  informs the short action/feedback/reward loop, early successes, and rest
  between difficult encounters. This document records concrete choices for
  Emberbond; the reference is not a substitute for playtesting.

All characters, maps, graphics, story, and music remain original. Inspiration
comes from design principles and the feeling of exploration.

## The playable loop

Within roughly thirty seconds, notice an inviting path or an interrupted
everyday activity, try movement or a companion's power, see a clear response,
and gain a crossing, a shortcut, a useful item, or a changed conversation.
Combat interrupts and varies that loop. It does not replace exploration as
the reason to travel.

The first village establishes the promise of shared food and a journey worth
returning from. The first forest teaches the bridge before restoring its full
enemy pressure. The sword's visible contact frames, directional step, readable
enemy warnings, and post-hit mercy give mistakes a recoverable cost. A failed
power explains whether to wait, change aim, or find the right place.

Later rooms develop familiar verbs through their own materials and people.
The field goal remains available on Select, while optional discoveries stay
unnamed until found. Menus and the companion carousel pause the world. The
main route should remain understandable without completing the collection.

## Visual language

The hero reads as a traveler through scarf, satchel, boots, and a lantern
accent. Homura's warm wick-tail, Midori's leaf-and-seed silhouette, and Fuuri's
airy shape communicate their identities before a help screen is opened.
Residents have work, posture, and tools: a gardener, sailor, and kiln worker
should remain distinguishable when shown in one color.

Actors use a strong outer contour, a restrained shadow plane, and small
highlights. Faces and hands receive detail before clothing texture. Walk
frames show planted feet and a controlled body rhythm. Effects have a clear
strong moment and a short decay; they must leave enemies and puzzle targets
readable. Scenery provides calmer planes around moving actors and emphasizes
paths and useful objects over decorative noise.

Native 240×160 captures are the final layout reference. Enlarged nearest-neighbor
atlases help inspect individual clusters, but do not establish in-game clarity.
The title needs a quiet wordmark area and an unmistakable selection highlight.

## Story and return

The opening's bread, herbs, and waiting table establish small personal stakes.
Each regional ending names someone and what they can do again, followed by a
concrete clue to the next destination. The underwater guardian admits that its
protection has closed the way home. The return chapters carry the repaired
routes back to the village, and the final gathering pays off the shared table.

Mina, Edda, and Ressa retain their individual relationship routes and choices.
Progress comes from completed events and separate visits; loading an older
save does not invent a history with them. Story presentation must preserve
reward ownership, once-only receipts, cancellation, and successful saving.

## Hardware budget

Art is authored and packed before the ROM is built. Existing actor dimensions,
frame indices, palette slots, collision anchors, and streamed OBJ allocations
are retained. The existing OBJ layout uses 16,256 of 16,384 bytes, so additional
resident effects are not an acceptable route to polish. Background presentation
must not change the geometry used for movement and power targeting.

The field update separates input ownership, actions, movement, chapter ticks,
and exits while retaining their order and early-return behavior. Rendering,
audio service, and save publication remain subject to the existing GBA frame
budget. The linker continues to enforce the IWRAM stack reserve. Native tests
measure actual emulated frame cadence; host test speed is not a performance
measurement of the cartridge.

## Release acceptance

The release requires reproducible clean ROM builds, the current host and native
gameplay suites, a field-refactor comparison against the pre-redesign ROM, and
visual review of the title, opening, core animations, and regional residents.
The main campaign and relationship routes must complete with physical button
inputs through the emulator. Save migration, interrupted writes, pause
ownership, and audio cadence remain acceptance gates.

Historical pixel/source contracts retain their original meaning. A separate
explicit Lantern Trails art contract admits the reviewed new pixels while
protecting palette layout and the other released companion assets. Current
tests run against the new ROM; restored historical source is used only for
historical assertions.

Issues #32 and #48 close only after their behavioral requirements pass. Branch
cleanup follows completed development and checks merged pull-request records
as well as ancestry, since squash merges do not retain branch ancestry. Any
uncommitted files must be preserved. Emulator evidence does not establish
physical GBA or Miyoo Mini Plus performance, and automated completion does
not establish subjective enjoyment or full optional collection coverage.
