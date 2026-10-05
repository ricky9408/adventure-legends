# Adventure Legends — development roadmap

## Direction and explicit scope

The requested game is an original, bright, responsive GBA action-adventure with field companions, evolution, special abilities, equipment, culturally varied regional towns and side quests. The expanded target is **128 monster forms**, provisionally counting evolved forms within 128. The owner's wording about “males” is provisionally interpreted as mail/body armor. Both assumptions can be revised without renumbering released content.

The three-lantern story below is a playable foundation, **not completion of the expanded game**. No play-length promise is made without measured playthrough evidence. A handcrafted form needs a distinct design, animation, behavior/ability, acquisition and balanced gameplay role; a reserved database slot or palette swap does not count as a finished monster.

## Progress accounting

Every roster release will separately report:

1. Designed: approved original visual/gameplay specification
2. Implemented: ROM data, art, animations and abilities exist
3. Obtainable: a normal player can acquire the form in the shipped world
4. Verified: evolution/acquisition, field actions, combat, saves and performance are tested

At the current river-region milestone, **11 forms are implemented, obtainable and controller-verified**. There are six live companion families, five optional evolution paths, three player weapon classes, five equipment slots, 13 earnable items, 22 areas and 11 regional side quests. All 11 forms fit a single controller-earned/reloaded collection, without duplicated family instances or fabricated history.

The first three-lantern story remains a completed foundation. One Asian-inspired riverside town/field and four local activity rooms are now playable. Northern-European, southern-island, magma-mountain and underwater regions remain planned; the complete 128-form roster and legendary progression are not finished. Twelve forms are designed, eleven enabled, zero legendaries obtainable.

## Completed exploration foundation

- Continuous 480×320 grove, smooth constrained camera, useful landmarks and a map
- Camp checkpoint, permanent optional heart relic, collision-safe dodge and three-hit sword chain
- A ranged enemy with locked aim and visible warning
- Format-3 migration from published format-2 saves
- 113 gameplay/edge/exploration checks and 19 cadence scenes verified on that immutable milestone ROM

## Completed: three-lantern campaign foundation

- Sky route, wind vanes, patrol encounter, three-way relay and Kazane boss
- Stone route, weighted sockets, well/root/fire sequence, four-power chamber and three-phase final core
- Four field companions, contextual journal, expanded dialogue, optional chime, ending and postgame exploration
- Transactional dual-bank format-4 SRAM; preserve prior format-2/3 progress and reinterpret an old chapter ending as first-lantern completion
- Controller-only minimal and optional routes, all puzzle orderings, interrupted rewards, reentry/death/retry and frame-budget tests
- Cold-menu optimization and preserved earlier scrolling/combat regressions before release

This milestone establishes a coherent playable baseline while the larger systems are designed.

## Completed: representative monster systems

- Stable 1–128 catalog identifiers (0 means empty) with explicit unimplemented slots; data-driven family, phase, polarity, stats, learnsets and acquisition conditions
- Wood, Fire, Earth, Metal and Water phases, with Yin/Yang as a separate dimension; research cited in the system design and numerical battle rules identified as original game interpretation
- Party/storage, experience, learnable abilities and explicit evolution choices; preserve required traversal powers through evolution and party changes
- Eleven substantive representative forms across all five phases, including genuine evolutions; rare/legendary encounter progression is still a later milestone
- Journal/catalog, field selection and intelligible feedback at 240×160
- Save expansion with non-overwriting migration, bounded storage and old-save fixtures; no newly mandatory grinding in the existing story

Acceptance: each shipped representative is normally obtainable, its evolution and ability work in the real ROM, traversal cannot be stranded by party/equipment decisions, and the reported counts match the actual acquisition graph.

The quick-companion update adds a held-L directional selector and journal assignment/reordering from actually owned instances, with meaningful empty slots and safe immediate assignment saves. The story collection remains recoverable; historical evolved forms are not cloned into extra companions.

The first slice delivered eight story forms and the full-screen/quick-party foundation. The river milestone adds Water/Metal recruitment, Water evolution, actual regional five-phase damage, retained learned commands and collection reassignment. New recruits remain retained owned instances even when unequipped. Save5 content revision 2 migrates prior released saves and couples one-time quests, equipment and traversal-critical ownership.

## Completed: initial equipment and action roles

- Sword, lance and bow with distinct readable range/timing patterns under consistent controls
- Weapon, mail/body, boots, belt and ring slots; bounded integer parameters and clear equip comparison
- Useful drops/rewards and recoverable inventory management; prevent equip/heal/cooldown exploits
- A small fully tested item set before broad content expansion

Acceptance: each weapon has combat/traversal tests, each slot changes the documented parameter, and migrating or unequipping cannot corrupt a save or create an unwinnable required encounter.

Delivered: three native weapon state machines, attack snapshots, safe projectile ownership/tags, fractional-health armor, clear equipment comparisons, 13 meaningful rewards and controller-verified training/combat. Expansion should build on this tested set, not add inert catalog rows.

## Ongoing: regions, towns and side quests

- Connected original Asian-inspired, Northern-European-inspired, southern-island, magma-mountain and underwater regions, with researched visual reference and distinct original architecture/ecology
- Town services, named NPCs, legible routes, revisitable quest state and meaningful non-repeating rewards
- Regional mechanics integrated with companions and equipment, including a deliberate underwater movement/access design
- Multi-room dungeon quests combining contextual clues, switches, movable objects and companion powers; existing monotonic sockets/vanes are the starting point, not the full puzzle target
- Visually hinted hidden field paths, buried discoveries, rare encounters and ability-gated return areas, with worthwhile permanent or story rewards rather than random pixel hunting
- Side quests with explicit prerequisites, active/completed states, idempotent rewards and recovery after interruptions

Acceptance: each region has a playable entrance-to-exit route, distinct local activity, useful NPCs, at least one complete side quest and no inaccessible required companion or equipment dependency.

## Then: full roster and legendary progression

- Expand in reviewable regional families until all 128 forms meet implementation/acquisition/test criteria
- Original silhouettes and animation, differentiated battle/field niches and coherent evolution identities
- Powerful rare/legendary forms earned through discoverable, testable conditions; no opaque impossible odds or paywalls
- Balance acquisition rates, XP, stats, phase interactions, equipment and bosses as an integrated action game

Acceptance: a machine-checked acquisition/evolution graph reaches all 128 forms, representative manual visual/play review accompanies automation, every ability has a defined role, and progression has no forced palette-swap filler.

## Release gate

- Fresh full route, optional routes, collection completion, every supported save migration and corrupt/interrupted save recovery
- Worst representative combined camera/combat/ability/UI windows maintain actual emulated GBA update/presentation cadence, with documented headroom
- ROM remains within normal 32 MiB cartridge space; EWRAM/IWRAM/OBJ/stack budgets enforced
- Clean reproducible source build and deterministic asset generation; native `.gba`, player guide, credits and test evidence
- Known limitations stated, including untested physical hardware or emulator/platform combinations

Each meaningful milestone is a separate reviewable PR. The owner has authorized self-review and merge for this repository only; exact-head tests and an independent review still precede merge. Work can continue while review is pending; later commits must be reconciled with the actual main branch or clearly stacked on the earlier PR.
