# Design review: first pass

This pass read the play guide, the live Japanese script, the field/combat
update, and the current host contracts, then built the ROM and ran the host
weapon and equipment-reward suites. It is a play and code review, not a full
78-room controller campaign and not a physical GBA session.

## How the game plays

Emberbond is a top-down action adventure on a 240×160 screen. You walk, cut
with a three-hit sword (or a lance or bow once you find them), and solve rooms
with a companion's power. B uses that power. R calls the companion out or sends
them home. A short L press cycles the party; holding L and pressing Left or
Right browses every companion you own. Start opens the journal. Select does
nothing in the field.

The opening in the lantern village is the warmest writing in the game. Homura
is saving bread, Midori is watering the flowers, and you promise to share the
bread when the forest light is safe. Ryuma says the soup will be waiting.
After that, the adventure becomes a long chain of clear jobs: cross the river
with Midori, light the shrine with Homura, wake Fuuri, then a new region with
its own companions, gear, and puzzles. Death sends you back to the entrance at
full health and keeps your companions. Progress saves on its own.

The combat rules are readable once you know them. Ordinary enemies walk in
when you are close. Rangers and the lane charger show a warning before they
commit. A hit flashes, stops the action for three updates, and can be landed
only once per swing. The sword's authored arc is wide. The lance is narrow and
long. Companion powers are the keys to doors, bridges, and boss armor.

## What is already strong

- The first hour tells you where to go. Quest lines name the next verb
  ("grow a bridge with Midori", "light both pedestals with Homura").
- Closed roads show a barrier and a one-line hint. You keep walking.
- The journal, map, equipment comparison, and collection counts are careful
  about what they reveal. Unfound names stay hidden.
- Saves survive interrupted writes, and a failed save leaves the last good
  record with an on-screen retry.
- Frame time is treated as a GBA budget. Hot code stays in IWRAM, and the
  linker refuses to eat the stack. Weapon data lives in ROM, so a combat
  timing change does not spend that budget.

## Player-facing gaps

These are the changes worth making next. Each one is filed as its own issue.

**Sword contact is a single update.** The opening and middle cuts wind up for
two updates, hit for one, then recover for fourteen. The slash stays on screen
through that recovery, and the lance already hits for three updates. A swing
that looks true often misses because the enemy stepped on the next update.
Damage and swing length can stay the same; the hit window should occupy part
of the recovery that is already playing. This pass makes that change.

**The Japanese play guide teaches retired controls.** `docs/PLAY_JA.md` says B
calls the companion and R uses their power, and that holding L picks one of
four directions. The ROM and the in-game lines do the opposite: B is the
power, R calls or dismisses, and a held L browses left and right. A player who
follows the linked guide will fail the first river puzzle.

**The current job is buried in the journal.** `journey_goal_read` already
knows the next place and the next sentence, for every chapter. On the field
you only see an area name. In a 78-room journey, Select is free and could show
that sentence without pausing the world.

**There is no committed defense.** Select used to roll. The roll was removed,
live strings no longer ask for it, and garden stones are walked. What remains
is walking out of the way, then about 1.3 seconds of mercy after you are hit.
A short step that still respects walls, and that does not grant the old
invulnerable roll, would make ranged rooms feel like action instead of
attrition.

**The opening promise never comes back.** Soup and shared bread appear in the
opening and in Ryuma's first line. Later chapters, including the homecoming
quests, talk about work, signs, and the right power. The people at the start
do not get a scene where the bread, the soup, or the changed village is real.

**Later regions talk like instruction labels.** Horizons and Covenants lines
are accurate puzzle orders ("left and right down, middle up"). They rarely say
who wants the work done or what it costs them. The clues can stay. One human
sentence in front of the instruction would make the places feel inhabited.

**The first forest fights before it teaches.** Room 1 spawns five enemies,
including two rangers, on the way to the bridge that introduces Midori. The
bridge hint is good. The fight in front of it is a difficulty step the opening
did not practice.

**A failed power often says only "try another aim."** Cooldown, a blocked
line, and the wrong place share a short toast. Players repeat the button
instead of learning the rule.

**Getting hit during your own swing, and getting hit at all, is uneven.**
Contact range is checked while your sword is active, so a correct spacing
mistake and a correct swing can trade. After the trade, invulnerability lasts
80 updates, and a defeat heals you completely. Early fights are tense for one
hit and then loose. Later bosses that depend on a specific power stay strict.
The curve should tighten mercy only after a defensive step exists.

## Code health that will block the next passes

- `update` in `src/game.c` owns input, menus, saving, movement, every chapter
  tick, and room exits. A feel change has to be threaded through that function.
- Equipment weapon timings are frozen by released catalog hashes. A live feel
  adjustment belongs in `weapon_actions.c`, which is what the sword window does,
  so the historical item definitions stay byte-stable.
- Authoring JSON still describes the removed dodge (`campaign_dialogue.json`,
  the garden source lines, shop comparison copy, English item blurbs). The
  generated player text was corrected by hand. The next `make assets` can put
  the lie back on screen.
- `docs/READABLE_AIMING.md` still says to hold R and that B summons. The live
  aim hints say to hold B.

## Roadmap

Filed issues use `[priority][area]` in the title. This token can open issues
and cannot create or apply labels.

1. **P1, this pass.** [#23](https://github.com/ricky9408/adventure-legends/issues/23).
   Sword contact lasts four updates. Swing length, damage, reach, and the
   one-hit-per-swing ledger stay authored. Lance and bow timings stay authored.
2. **P1.** [#24](https://github.com/ricky9408/adventure-legends/issues/24).
   Correct `docs/PLAY_JA.md` so B, R, and held L match the ROM.
3. **P1.** [#25](https://github.com/ricky9408/adventure-legends/issues/25).
   Select shows the current journey-goal sentence on the field.
4. **P1.** [#26](https://github.com/ricky9408/adventure-legends/issues/26).
   Add a short, wall-checked step on Select. No invulnerability tunnel.
5. **P1.** [#27](https://github.com/ricky9408/adventure-legends/issues/27)
   and [#28](https://github.com/ricky9408/adventure-legends/issues/28).
   Write the village return that pays off the bread and the soup, then put
   one personal stake ahead of each later region's puzzle order.
6. **P1.** [#30](https://github.com/ricky9408/adventure-legends/issues/30).
   Split power-failure toasts into cooldown, blocked aim, and wrong place.
7. **P2.** [#29](https://github.com/ricky9408/adventure-legends/issues/29),
   [#33](https://github.com/ricky9408/adventure-legends/issues/33),
   and [#34](https://github.com/ricky9408/adventure-legends/issues/34).
   Thin the first forest until the bridge lesson has happened. After a step
   exists, shorten post-hit mercy, and stop a connecting swing from trading
   a heart with the enemy it just hit.
8. **P2.** [#31](https://github.com/ricky9408/adventure-legends/issues/31)
   and [#32](https://github.com/ricky9408/adventure-legends/issues/32).
   Make authoring generation fail if player text mentions a dodge, and split
   `update` only as far as the next feel change needs.

## Verification this pass

- Host weapon-action suite, strict and ASan/UBSan, including the new sword
  window and the unchanged lance window.
- `make` produced `build/emberbond.gba` (valid header) and stayed inside the
  IWRAM stack reserve.
- `make test` passed: the equipment-reward host aggregate, 50 checks, exit 0.
  That includes the weapon-action suite, the field-controls parent archive, and
  the southern, magma, and covenants host gates.
- Headless mGBA booted the ROM, skipped the opening with Start, and reached
  the village in play. A single A press then showed sword phase active on
  ages 2, 3, 4, and 5, recovery through age 16, and idle at age 17. The
  bundled mGBA 0.10.5 library needs Debian 13 codec libraries
  (`libavcodec.so.61` and its libva stack); those were loaded from a private
  directory for this trace. A full 78-room campaign and physical hardware
  were not run.
