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

At the current **Southern S3 candidate**, **41 forms are implemented, obtainable and controller-verified**. There are 21 retained companion families, 20 optional evolution edges, three player weapon classes, five equipment slots, 25 earnable items, 38 areas and 30 regional side quests. All 41 historical forms fit a single controller-earned/reloaded collection with 21 real individuals. They are not duplicated from collection history.

The three-lantern story remains a completed foundation. The river, Northern harbor/headland and Southern island chapters are playable. Magma-mountain and underwater regions, later return journeys and the complete 128-form/legendary progression are unfinished. Forty-two forms are designed, 41 enabled, zero legendaries obtainable. Native emulator acceptance is separate from physical-hardware testing, which remains outstanding.

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
- Forty-one substantive representative forms across all five phases, including genuine evolutions; rare/legendary encounter progression is still a later milestone
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

## Completed candidate: Northern harbor chapter

- Eight connected new areas with a harbor town, scrolling headland, working interiors and a multiroom movable-load/rail puzzle sequence
- Five genuinely distinct new base/evolution pairs, ten field/combat commands, eleven local quests and six gear sidegrades
- Guaranteed base companions precede mandatory gates; reset, re-entry, safe return and reassignment stay available
- Content revision 3 preserves earlier revision 1/2 data and uses exact historical whitelists, coupled retained ownership and atomic one-time rewards
- All 21 forms, 19 items and 22 regional quests obtained and independently reloaded through controller input; separate Sky-clear route proves no old ending or optional River quest prerequisite
- All ten commands, all three boss weapon classes, cooldown/equip/picker control paths and actual native frame presentation verified
- Five-visible-enemy combined stress: 420/420 hardware updates and flips; cold seven-tab journals: 80/80; no physical-GBA claim

See `docs/VERIFICATION.md` and the bounded `docs/northern/` reports for exact-candidate evidence and the status of the whole-game aggregate. This does not mean the expanded game is complete.

## Completed candidate: Southern islands

- Eight connected areas with a sunny harbor, distinct field/interior activities and a recoverable multi-room optical/companion puzzle chain
- Ten distinct new base/evolution families, 20 field/combat commands, eight local quests and six gear sidegrades
- Guaranteed base companions before mandatory gates; a separate minimal-prerequisite native route uses only the starter sword and preserves absent optional content
- Content revision 4 retains every prior owned individual and exact historical source semantics; mixed one-time rewards and personal trials remain instance-bound
- All 41 forms, 25 gear and 30 quests earned and independently reloaded, with storage/selector, dialogue, death, reset, return and real combat checks
- Native frame-pacing fixes for collision geometry, full-collection saving and large storage gaps, with full-screen pixel/OAM evidence

See `docs/VERIFICATION.md` and `docs/southern/` for source-pinned evidence and whole-game regression status. These are native emulator results, not physical-cartridge certification.

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
is a future architecture gate only; Northern N5's 16-bit trial field, 32-bit
capabilities and frozen runtime remain unchanged.

## Release gate

- Fresh full route, optional routes, collection completion, every supported save migration and corrupt/interrupted save recovery
- Worst representative combined camera/combat/ability/UI windows maintain actual emulated GBA update/presentation cadence, with documented headroom
- ROM remains within normal 32 MiB cartridge space; EWRAM/IWRAM/OBJ/stack budgets enforced
- Clean reproducible source build and deterministic asset generation; native `.gba`, player guide, credits and test evidence
- Known limitations stated, including untested physical hardware or emulator/platform combinations

Each meaningful milestone is a separate reviewable PR. The owner has authorized self-review and merge for this repository only; exact-head tests and an independent review still precede merge. Work can continue while review is pending; later commits must be reconciled with the actual main branch or clearly stacked on the earlier PR.


## Next implementation: Magma Mountain

The agreed next batch is 24 forms across nine families: F011–F016 (IDs31–48)
and F036–F038 (IDs95–100). It adds two third tiers and four alternate branches,
so both policy-isolation gates in `SOUTHERN_CORE_REVIEW.md` must be closed and
independently reviewed before activation. The separate development workspace
is preparing those changes; no new Magma form or save revision is enabled in
this Southern release.

Each alternate branch needs its own ordinarily acquired base individual;
collection history never manufactures a duplicate. The full planned collection
at that chapter boundary is 65 historical forms and 34 real retained individuals.
Global quest IDs 30–37 and eight area IDs 38–45 are reserved for the chapter.
Current cold-menu/save headroom is limited, so broader collection and new-world
costs require fresh whole-engine native tests before the next delivery.

The finite full roster remains 65 after Magma, 89 after underwater, 104/120 after
two return-content batches, then 128 including eight gated legends. These are
planned counts, not current playable content or a measured playtime promise.
