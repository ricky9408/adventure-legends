# Relationships: people to return to

## Requested experience

Different women become familiar through the adventure, with individual hidden
felt affinity, personal scenes, optional dating, marriage and multiple spouses.
The reference is the warmth of returning to distinct people in Ocarina of Time,
not its characters, names, designs, dialogue, music or age settings.

The player and all romantic characters are adults. For this expansion the player
is 22. The following ages and personal arcs are new authored design, not a claim
that the existing game already establishes them.

| Person | Age | Existing anchor / proposed personality | Personal scene |
| --- | --- | --- | --- |
| Edda | 25 | Northern cargo reopening; direct, capable, quietly protective | Help restore a delivery route, then learn why she keeps an undelivered letter |
| Ressa | 27 | Magma brick kiln reopening; proud craftswoman with dry humor | Make something imperfect together instead of proving strength in another fight |
| Mina | 23 | Southern conservatory reopening; curious and enthusiastic, but afraid her seedlings will fail | Return for planting and stay to see the first growth with her |
| Lyra (new) | 22 | Home village; an old friend with her own plans to leave | Listen to her travel plans and help choose a first destination, without asking her to abandon them |

Names and profiles are original. Existing three chapter hints and rewards stay
intact; no required story task becomes a romance requirement to finish the game.
Each person's goals remain meaningful outside their relationship to the player.

## Small, verifiable delivery units

1. **Completed foundation: isolated relationship core.** Four independent event ledgers,
   hidden derived affinity, explicit dating/marriage milestones, deterministic
   validation and tests.
2. **Completed foundation: persistence and admission.** Content13 adds the ledger;
   see [storage and verification](RELATIONSHIPS_SAVE13.md). Preserve revision1–12 policy and every historical
   fixture/hash. Append a typed four-byte ledger without repurposing reserved
   bytes in a released schema. Update blocking/incremental load, streamed
   validation, writer/preflight, migration, metadata packing and source inventory
   together. Existing adventures start all four routes unrecorded; loading may
   not invent relationship events or repeat earned chapter rewards. Existing
   completed quests may unlock a new meeting scene, not count as having seen it.
3. **Current slice: one complete playable route first (Mina).** Meet during the existing chapter,
   invitation after the report, return to plant together, personal scene, explicit
   dating choice, then a separately paced proposal/marriage scene. Keep chapter
   clues and receipts available and prevent interaction priority from swallowing
   quests, shops or doors. Do not ship all four routes as shallow repeated text.
   The implemented route and its earned-play evidence are described in
   [Mina's route](MINA_ROUTE.md).
4. **Future: other routes, then multi-partner scene coverage.** Different activities,
   cadence, dialogue, visual identity and home/epilogue reactions. An additional
   relationship requires an explicit conversation about existing relationships,
   with agreement from the people involved. Multiple spouse bits are allowed;
   no single global spouse slot silently replaces the first person.

## Core contract

`RelationshipState` is four bytes; each byte records five unique ordered events:
shared task → return visit → personal story → accepted dating → accepted marriage.
The first three contribute 10, 20 and 30 to a hidden affinity score. The score is
not a bar, counter, currency or gift-grinding mechanic. Dating/marriage do not add
points. Dialogue, shared activities and changed greetings communicate closeness.

This initial linear ledger is deliberately small. Distinct scene conditions and
chapter gating belong to the authored scene adapter, not an implied claim by the
core that a chapter was played. The adapter must not call `relationships_record`
merely because a quest flag or score threshold is true. An acceptance event is
committed only after a completed mutual-consent scene and a fresh affirmative
player input. B/cancel, interruption and "not now" do not record it; friendship
and the main adventure remain available. A later retry uses the same event ID.

Repeated events are no-ops. Missing predecessors, invalid IDs or corrupt ledgers
are rejected without mutation. Relationship records never touch companion bonds,
quest rewards, currency or combat stats. A marriage on one route neither erases
nor prevents another route. The full-state validator does not reject multiplicity.
Future branching will require an explicitly versioned contract rather than a
silent change to legal event masks.

## Release gates for the playable slice

- Host tests for hidden scores, ordered/idempotent events, no automatic romance,
  cancellation, interruption, invalid states and independent concurrent spouses.
- Save tests for old-bank selection, all old revisions, zero manufactured events,
  round trip, interrupted writes, corrupt relationship payload and bounded loads.
- GBA build/header, ROM/RAM/stack budget checks and Japanese text width/glyph
  validation. No heap or unbounded relationship loops.
- Native mGBA controller test for meeting → cancel → reopen → accept → save → cold
  Continue and repeated reports. Include screenshot review of
  each meaningful state; synthetic host calls are not gameplay proof.
- Two independently earned marriages remain a gate for the later multi-partner
  slice, when a second playable route and consent conversation exist.
- Independent review and exact-head CI. Do not merge the playable slice on the
  strength of the core tests alone. Physical hardware remains separately untested.
