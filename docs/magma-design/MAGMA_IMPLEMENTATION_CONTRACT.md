# Magma implementation contract

Developer-only design proposal, revision2. Source of truth: magma_allocation.json plus immutable identity-lock snapshot. No runtime enablement by these files. Review against the eventual accepted Southern revision4 checkout.

## Exact allocation and dependency gates

- Revision5 is proposed content revision, retaining wire version5,24-byte instance×160,5056 used bytes and two6144-byte banks at0x0200/0x1A00; no offset/CRC/commit changes
- Add forms31–48 and95–100 only; all locked(id,key,family,tier,rarity) tuples remain identical. Baseline41+24=65, ordinary families21+9=30
- Add signatures43–66 in form order31–48,95–100; command12 and all121–128 stay disabled
- Enabled evolution edges add31→32→33,34→35→36,37→38/39,40→41/42,43→44/45,46→47/48,95→96,97→98,99→100:15 edges,35 cumulative;41 new learn rows,102 cumulative
- Local trials1→1 and2→2. Linear key2 prerequisite1 and tier3 required-mask3; branch keys independent, edge required-mask1 or2. Three linear-two families key1 only
- Freeze old legacy trial query/mark scalar behavior before current unions/subsets. New families never become legacy HEARTH owners
- Freeze exact revision1–4 form/learnset/trial/incoming-minimum/phase/polarity/quest/gear/source/visit/anchor/discovery/room relationships. Validate each old bank under its declared policy before current migration. Preserve legal historical exception states and broad generic event/reward bytes
- Tier3 totals285, inherited capabilities and learnsets are exact. Branch target selection/decline/ambiguous legacy calls and second-copy acquisition need explicit proof
- No partial release is proposed. Both architectural gates plus tier/branch/source, terminal-opportunity admission and native acceptance precede the full24-form Magma release

## Context, room and quest namespaces

MAGMA_READY=0x0100 derives only from Q30 and Q31 CLAIMED. CALDERA_OPEN=0x0200 derives only from Q32 CLAIMED. These are u16 evolution context bits, never campaign chapter flags or new saved flag fields. Review mask/projection callers so0x100/0x200 cannot truncate to u8. Preserve old context API behavior and reject unregistered bits.

Areas38–45. region_flags[3] bits0–7 map exact area IDs minus38. Every visit implies Q24 CLAIMED and town38 visit, even after leaving. Rooms42–45 additionally require Q30/Q31 CLAIMED;43 requires Q32 bit1;44 prefix3;45 prefix7. Current area requires its visit. Anchors[3] bits0/1 imply38/39 respectively; no other new anchor bits. Exact spawn coordinates and allowed indices must be frozen after collision QA, not guessed into save policy from this brief.

Quests30–37: masks3,3,15,7,3,3,3,7. Q32 legal prefixes0/1/3/7/15 only. Existing quest variables remain unchanged; no new variable bytes. Main and teaching guards as described in the brief. READY/CLAIMED requires exact objective mask; reward/source causality is separate from objectives.

- Q30 CLAIMED implies retained F011/obtained31,32or33 plus gear source25/item20 history
- Q31 CLAIMED implies retained F012/obtained34,35or36
- Q33–37 source26–30 map items37,53,67,85,5 respectively
- All quest mutations are explicit authored-object events, never visits alone; old typed quest definitions remain frozen by revision

## Typed sources and discovery ledger

New field source byte9 bits0–6: F013/base37@39,F014/40@41,F015/43@40,F016/46@39,F036/95@39,F037/97@40,F038/99@41. Bit7 remains zero. Each implies region entry, town visit, encounter-room visit, exact retained family and enabled obtained history. Bit6 additionally requires discovery byte19==7. Do not repurpose generic creature rewards5–128. Typed transactions use grant0 only as their staged inner operation.

Branch first-extra receipts byte16 bits0–3: F013,F014,F015,F016. Each requires its initial typed source, at least one retained evolved branch, at least two valid distinct retained instance_ids of that family, and history for a valid branch. Enforce those minimums after both extra individuals evolve too. The first-extra receipt is not the only permission to encounter another base; subsequent explicit deterministic repeats remain available without extra one-time rewards, subject to the prospective terminal-opportunity admission rule. A physical FULL check alone is insufficient. A receipt alone cannot materialize a creature. Existing seen/history cannot clone a base.

Discovery byte19 legal prefixes0/1/3/7 only: request, both baffles/niche, returned clapper/reveal. Any bit implies entry, town and grotto visits. M_FIELD_6 requires7. Partial scenery remains transient; named durable steps set only after their object proof. This supports the sixth optional journal commission without allocating quest38. Byte18's old Southern bits are unchanged; do not merge the new mask into an old-revision reader. All other new unassigned bytes/bits remain zero in revision5.

New trials require exact acquired source, context, allowed from-form and same participant's authored level/bond floor. Cross-copy trial/floor aggregation fails. For F011/F012 key2 the same individual must already have key1; tier3 requires both. Branch trial2 is not a tier3 achievement. Old families acquire no new trials or rewritten causal requirements.

## Explicit credit registry

- Enemy encounter credit220–231: reserve explicit tuples39 slots0–4→220–224,41 slots0–1→225–226,42 one approach patrol→227,43 one approach patrol→228,44 two approach patrols→229–230,45 regulator outcome→231. Never credit a boss hit as an encounter
- Quest claim credit240–247 maps Q30–37. IDs232–239 and248–259 remain unused/reserved. Exactly20 assigned IDs,20 reserved; no area×6 arithmetic
- Lifetime aid indices40–54 map fifteen trial bindings in declared family/key order;55–61 map the seven first field sources;62–63 remain unused. Their actual event IDs are384+aid
- A prior historical lifetime aid bit suppresses duplicate credit only, not a future source, world interaction, explicit trial completion or authored floor. Generic reward/event ledgers are not new-source provenance
- Additional branch copies issue no repeated one-time event/bond/source/gear rewards. Shared expedition ledger continues to prevent party-swap farming

## Equipment map

Append source25→item20 Ventstring Bow;26→37 Kilnweave Mail;27→53 Pumice Boots;28→67 Bricklayer Belt;29→85 Quietnote Ring;30→5 Terrace Sword. Exact bounded vectors are in allocation JSON. Keep48 noncompacting bag records, five slot semantics, protected starter fallback, busy equip locks, snapshotted attacks, HP clamps and no cooldown/heal reset. All visible comparisons must show actual derived values, including clamp saturation. None grants a new field action.

## Required terminal-opportunity admission gate

The original repeat-base design could legally fill160 records with duplicate terminal branches and permanently block missing/future companions. This is a real newly identified integration defect; the constructive34-individual route did not cover arbitrary choice orders.

Before every new gameplay creature grant or potentially coverage-losing evolution, compute candidate occupied countN and maximum viable final-terminal coverageV. The reviewed final topology needs72 terminal opportunities. RequireN−V≤88 andN≤160, equivalently160−N≥72−V. Linear/single families contribute at most1; a branch contributes the maximum matching of its distinct retained bases/A/B to its two targets. One flexible base contributes1, two bases2, A+base2, A+A1, A+B2. History/source receipts are not ownership. Use the full final topology, never only currently enabled regions.

Every missing-family or missing-branch base increasesN andV together and remains admissible from a safe state. At88 excess copies, refuse only duplicate captures or branch choices that reduceV; keep all bytes unchanged and explain the retained alternative/defer path without spoilers. Lower-level grant0 is still an inner operation: every gameplay wrapper must check admission before committing receipt/instance/quest/gear/history. Already-claimed one-time sources remain idempotent before this check. Trial completion alone changes neitherN norV and remains possible.

Grandfather all legal historical saves. Never add this predicate to bank validation or normalize old records, including when re-saving an imported state in revision5. For pre-existingE>88, allow only physical-capacity-respecting nonworsening excess and nondecreasing coverage; disclose that admission cannot restore full completion capacity. No release, silent replacement or capacity-recovery promise is authorized.

MAGMA_COLLECTION_SAFETY.md gives the exact proof, UI feedback and legacy limitation. terminal_admission.py and test_terminal_admission.py provide pure design-model evidence over all safe sufficient states and choice orders. Runtime/native/save-path integration remains required.

## Runtime integration and budgets

- Separate magma_game, magma_quests, magma_powers and art modules in ROM. Check linker selectors; no broad *game.o IWRAM wildcard. New permanent IWRAM code/data0
- Target ROM increment≤2MiB, new mutable EWRAM≤8KiB, of which regional transient runtime state≤1KiB. These are ceilings to measure, not results. Normal cartridge remains≤32MiB
- Existing Mode4 OBJ near-capacity layout is not a new sprite budget. Stream selected companion frames into shared slots and use reviewed mutually exclusive regional prop/effect slots; permanent new OBJ allocation0
- Maximum five visible enemies and three live companion power objects; single-cast bounded target ledger. No malloc, no complete roster/save snapshot on stack, no per-frame all-form/all-roster scan
- Abstract puzzle state is bounded and per-room. Collision, facing, range, actor overlap, reset and exits use final native geometry. Reprove every prop arrangement against radius-five movement and weapon sweeps; visual affordances and solids agree
- Pause all new world ticks/input during menus, dialogue, save/reward confirmation and death. Clear incomplete scene/trial identity proof on death/load; preserve selected trial proof only across ordinary room travel
- Current policies already use indexed bounded tables. Check generated offsets/counts before narrowing.102 cumulative learn pairs remain below u8 offsets for this slice, but do not redefine the global8-command authoring limit as proof every future layout fits
- SAVE_PENDING remains authoritative. Benchmark authentic21- and34-individual collections plus full160/full48 synthetic valid state, both blocking/incremental validation, and worst supported write budgets. Isolated ARM measurements do not substitute for whole-frame native cadence or stack high-water

## Required tests before activation/release

1. Identity lock and exact revision whitelists; disabled rows fail through forms, collection, commands, source bits and current-room state
2. Frozen legacy scalar vs current union, wrong-family same-bit calls, key2 prerequisites, edge subsets, mask overflow and mutation-free failure
3. All historical fixtures and differential valid/invalid bank matrices; future values forged into revision1–4 still rejected; old generic reward/aid bytes preserved
4. Third-tier source→target chain and tier285 totals, complete inherited commands/capabilities, explicit branch choices, ambiguous wrappers, no mutation on defer
5. Thirteen actual new individuals produce all24 new histories; both alternatives retained for four families; same-branch-twice then deterministic third base still recovers the other alternative
6. Source/trial/gear/quest atomicity under every interruption, duplicate call, save retry, full160/full48 and mixed teaching reward failure. No fake success UI and no lost existing record
7. Base31+34/starter sword main route, full party storage and reassignment, empty-party retreat, every incomplete reset/reentry/death, power independent of battle equip, wrong phase/family/capability rejection
8. All three weapons at release pin and regulator, every24 new signature's geometry/timing/hit cap, modal/busy/picker/cooldown behavior, minimum-gear ordinary damage and unsafe through-wall actions
9. Every optional source/side story after main ending, two clue routes, READY discovery with full gear bag, repeated branch-copy capacity handling, no missable weather/time/RNG conditions
10. Native original silhouettes and animation at240×160 on both light/dark terrain; separate all24 from prior41, body-plan changes and living faces; grayscale/palette review, portraits, four directions×four locomotion and at least two cast poses
11. Exact ROM head: real updates/presented frames under combined five-enemy/three-power/camera/UI stress and cold expanded journals; map/OBJ/ROM/EWRAM/stack evidence. Publish no unmeasured physical-hardware claim
12. Independent review and clean reproducible build of the eventual merged source. Preserve the distinction between designed, implemented, obtainable and verified

13. All-choice-order admission: global72 opportunity reserve, exact maximum matching, duplicate-at88 and coverage-loss refusal, missing-base admission at the limit, stable identity/history/receipt on failure, repeat-source idempotence, real alternate encounter recovery, all actual gameplay grant/evolve callers guarded, and unchanged historical bank acceptance.
14. Explicit current per-form polarity overrides for39/48, if approved; no family-guard bypass or released-polarity changes.
