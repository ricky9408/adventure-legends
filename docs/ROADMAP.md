# Finishing Adventure Legends: Emberbond

This is a finite completion plan for an original GBA adventure, not a promise of an unlimited commercial-scale game. The final play-length target remains open to the owner's preference; content should earn its length rather than add grind.

## Definition of the first complete game

- A connected overworld and village hub with clear routes, useful landmarks, optional discoveries, and a readable map
- Three distinct multi-room dungeon arcs, each with a companion-based traversal/puzzle idea, varied encounters, a boss, and a meaningful story payoff
- Four original companions with distinct field powers and combat roles, unlocked through the adventure
- A complete beginning, escalation and final ending, including village/NPC responses to major progress
- Responsive sword combat and dodge, readable enemy attack warnings, useful healing/checkpoints, and approachable retry behavior
- Persistent progression and upgrades; existing published save formats migrate safely; corrupt saves fail safely
- Consistent bright original pixel art, directional animation, effects and original audio
- Native `.gba` build, editable generators/source, controller-only end-to-end tests, representative frame-budget tests, and clear player/build documentation
- A release checklist with no known progression-blocking bug; physical-hardware limitations stated honestly

## Milestone 1: exploration and combat foundation (implemented, awaiting PR review)

- Expand the forest into one continuous 480×320 scrolling grove
- Connect the village, nature-grown river bridge and existing temple through clear paths
- Add a campfire checkpoint, one optional health discovery, and an in-game location map
- Add collision-safe dodge, a three-strike sword chain, and a telegraphed ranged enemy
- Introduce save format 3 with migration from the published format 2
- Preserve the existing chapter's ending and bright palette; measure scrolling plus combat at actual emulated GBA cadence

Verified: 113 gameplay/edge/exploration checks and 19 frame-pacing scenes pass on the milestone ROM.

Acceptance: new and migrated saves can reach the current ending, optional discoveries persist without duplication, no collision bypass or checkpoint trap, and scrolling/combat stress windows meet the one-update/one-presentation-per-display-frame target. Changes are reviewed in a new PR based on the verified merged main commit.

## Milestone 2: the second lantern

- Turn the first guardian clear into chapter progression and introduce the wind companion
- Add a new route/biome and a multi-room second dungeon with wind-driven traversal and a distinct boss
- Expand the hub's dialogue and journal objectives; add a small number of rewarding optional tasks
- Migrate earlier completed-chapter saves into the continuing adventure without discarding collected progress

## Milestone 3: the last lantern and ending

- Unlock the fourth companion and its stone/weight-based field interactions
- Add the third themed multi-room dungeon and final confrontation
- Complete the story, return-to-village payoff, ending, and optional completion records
- Ensure all four companion powers remain useful beyond their introduction

## Milestone 4: complete-game verification and release candidate

- Test a fresh complete playthrough, interrupted/reloaded playthrough, upgraded and minimal routes, deaths/retries and every save migration
- Check every required puzzle for softlocks, repeated interaction, out-of-order exploration and boundary collisions
- Balance health, checkpoints, warning times, attack recovery and navigation; remove filler and unclear objectives
- Measure representative worst-load scenes with scrolling, effects, projectiles and menus, with documented cycle headroom
- Rebuild from a clean checkout, regenerate assets deterministically, verify source/ROM hashes and prepare the player package

Each milestone is a tested reviewable PR. The owner merges PRs unless separately authorized otherwise. Later work may be prepared while an earlier PR is under review, but must be reconciled with the actual merged main branch before publication.
