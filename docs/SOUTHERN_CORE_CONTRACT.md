# Southern core/save implementation contract

Proposal supplement to `/tmp/southern-chapter-design.md`, 5 October 2026. Work only in the separately authorized Southern workspace; Northern is frozen. Core/save implementer must not edit `game.c`, UI generator, or UI generated assets owned by the integration lead. No GitHub or Library writes.

## Exact content revision 4 scope

- Preserve wire version5, 24-byte instance, 160 records, used5056, two6144-byte banks at0x0200/0x1A00, offsets, CRC and commit protocol
- Enabled forms: `[1,2,4,5,7,8,10,11,13,14,16,19,20,22,23,25,26,28,29,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94]`
- Southern forms exactly25,26,28,29,79–94. Forty-one enabled forms total. Ability12 and every legendary remain disabled
- Abilities: `[1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42]`
- Existing10 evolution edges unchanged. Add `[25,26],[28,29],[79,80],[81,82],[83,84],[85,86],[87,88],[89,90],[91,92],[93,94]`
- Quests22–29 masks `[3,3,15,7,3,3,3,3]`; Q24 prefixes only0,1,3,7,15
- New items `[4,12,36,52,66,84]`; source mapping19→4,20→12,21→36,22→52,23→66,24→84; corresponding quests22,29,25,27,26,28
- New region visits byte2; new anchors byte2 bits0/1; field claims byte8 bits0–7; discovery byte18 bits0/1. All other newly reserved bytes/bits zero
- New context bits SOUTH_READY=0x0040 from Q22 AND Q23 CLAIMED; SUNWELL_OPEN=0x0080 from Q24 CLAIMED. Never copy these into campaign chapter flags

| Family | Base/evolved | Phase/polarity | Base/evolved commands | Evolution minimum level/bond | Field actions |
|---|---|---|---|---|---|
| F009 |25/26|Wood/Yang|23/24|20/40|GROW_ROOTS; evolution adds GROW_BRIDGE|
| F010 |28/29|Earth/Yin|25/26|22/45|UNCAP_WELL|
| F028 |79/80|Water/Yang|27/28|20/40|REFRACT_BEAM|
| F029 |81/82|Fire/Yin|29/30|22/45|STORE_HEAT|
| F030 |83/84|Earth/Yang|31/32|22/45|PRESS_WEIGHT|
| F031 |85/86|Metal/Yang|33/34|20/40|TUNE_LATCH|
| F032 |87/88|Wood/Yin|35/36|24/45|REEL_LOAD|
| F033 |89/90|Water/Yin|37/38|22/45|REVEAL_CURRENT + FILL_BASIN|
| F034 |91/92|Fire/Yang|39/40|24/45|IGNITE|
| F035 |93/94|Metal/Yin|41/42|22/45|DRAW_ORE|

All evolved forms retain base actions/commands; base command unlock1, evolved command unlock at listed minimum. All10 edges require SOUTH_READY, owning-family local trial1, sanctuary and explicit confirmation. Exact immutable locked family/tier/ordinary rarity stays unchanged. Forms27/30 remain disabled. Initial baseline signature policy has31 learnset rows; these pairs add30 for61 total if no other new commands are introduced.

## Trial API: exact behavior

Keep public legacy `creatures_family_trial(unsigned form_id)` and `creatures_mark_trial(CreatureInstance *, unsigned mask)` signatures and original semantics. Separate the legacy policy from the new local registry.

Proposed new public signatures:

- `int creatures_mark_trial_qualified(CreatureInstance *instance, unsigned family_id, unsigned local_trial_id);`
- `int creatures_has_trial_qualified(const CreatureInstance *instance, unsigned family_id, unsigned local_trial_id);`
- `unsigned creatures_trial_mask_for_key(unsigned family_id, unsigned local_trial_id);` (returns0 if unknown/disabled; lookup only, not authorization)

Internal historical helpers should accept an explicit content revision and form ID, never ambient mutable “current revision” for old-bank checks.

Table key `(family_id, local_trial_id)` has one explicit u16 one-hot mask. Require full-width inputs to be within authored domains before conversion; no family shift. Different keys within one family cannot alias a mask. Different families may share a mask only through reviewed rows. Check resolved instance family equals requested family *before* looking up the mask. Reject unknown/disabled pair, zero key, overflow, malformed instance and unmet prerequisite trial; failure is byte-unchanged. Marking is idempotent for the same valid key.

Original legacy masks: F0011,F0022,F0034,F0048,F00516,F0060,F00732,F00864,F025128,F026256,F027512. Preserve their actual saved bits. Map their existing achievement to qualified key1 except F006 (no key). Southern F009,F010,F028–F035 qualified key1 maps to mask1 for each family.

Legacy mark rejects every Southern instance even with mask1; its meaning cannot become “first local trial.” Legacy family-trial query returns0 for new families, original scalar masks for old families, and0 for unknown/disabled. Old APIs never return a union. Future additional trials must use the qualified API.

Revision4 adds no masks to old families. Future third tiers may append qualified key2: use1024 for original trial-bearing families,2 for new families whose first bit is1. Future F006 may use1/2. These future rows remain disabled in revision4 and historical whitelist checks continue to reject them.

The chapter transaction, not this bit-setting API, proves environmental objectives, participant identity and prerequisites. It must set trial+minimum training on one same-family instance and commit atomically. Never combine evidence across copies, auto-complete a trial on load/evolve, or derive trial validity from the current global OR mask.

## Target-selected evolution API and legacy adapters

Retain existing structs' public wire-independent meaning; `CreatureEvolution.trial_flag` is the explicit required-mask union in the edge's own immutable family. It need not be a globally unique one-hot value. A registry binds every component bit to that family/revision/edge. For a future third edge requiring trial1 and trial2, the required mask is their OR. Current20 enabled edges all require a single trial.

Add:

- `unsigned creatures_evolution_count(unsigned from_form);`
- `const CreatureEvolution *creatures_evolution_at(unsigned from_form, unsigned ordinal);`
- `const CreatureEvolution *creatures_evolution_to(unsigned from_form, unsigned target_form);`
- `unsigned creatures_can_evolve_to(const CreatureInstance *, unsigned target_form, unsigned context, int sanctuary);`
- `unsigned creatures_evolve_to(CreatureRoster *, unsigned roster_slot, unsigned target_form, unsigned context, int sanctuary, int confirmed);`
- Append `CREATURE_EVOLVE_AMBIGUOUS=9` after existing DEFERRED=8. Do not renumber old result values

Exact legacy behavior:

- On every released single-edge form, old lookup/can/evolve outcomes, validation order, preserved fields and side effects remain identical
- `creatures_evolution(from)` returns its sole edge only when count==1; returnsNULL for count0 or a future branching source
- Old `creatures_can_evolve`/`creatures_evolve` validate the same input preconditions first; a valid future branching source returns AMBIGUOUS with zero mutation. They never pick the first row
- Target APIs reject invalid/disabled/out-of-range target as INVALID; valid enabled target with no exact from→target edge gives NO_EDGE. Validate source, target, qualifier/context and edge before mutation
- For an exact edge preserve requirement order LEVEL→BOND→STORY→TRIAL→SANCTUARY, followed by explicit confirmation for mutation; this keeps old UI reason precedence
- Deferral is byte-unchanged. Evolution stages one candidate instance, changes only form/polarity where explicitly authored, preserves instance ID, XP, bond, flags, cosmetic seed, trial evidence and valid equipped inherited commands, then sets seen/obtained for target. No clone or implicit command equip
- Edge enumeration order is explicit immutable policy order, never the UI's sole determinant of target. UI must show both named target choices and per-edge requirements before confirmation

Validator permits repeated source IDs only when exact locked branch edges exist in reviewed policy, preserves unique targets, validates same-family increasing tiers, inherited actions/commands, no cycles/merges, exact offsets/counts, and rejects any unlisted from/target pair. Do not simply delete the duplicate-source check without replacing its invariant. No branch family is enabled in revision4; synthetic branch fixtures test new APIs without enabling reserved content in the ROM.

Future branch acquisition: after choosing either first branch, expose a clearly marked **repeatable, deterministic base-family encounter**. It guarantees another ordinary base individual so both terminal choices remain collectible in one save. No real-time clock/random odds, no clone from history, no consuming the first evolved companion. First additional encounter may set the authored second-copy receipt bit; further voluntary repeats use grant0, respect160 capacity and cannot reissue one-time XP/bond/rewards. Full collection needs at least72 retained individuals, not exactly72 if the player chooses extra recruits.

## Extensible field capabilities without another global-bit ceiling

Keep every existing bit0–24 and all legacy32-bit functions exact. Southern's one new interaction may occupy bit25, but the architecture must allow capability IDs beyond32 without widening save instances or sacrificing old meanings.

Introduce a stable ROM capability-key registry (`CreatureCapabilityId`, suggested u16). Map IDs1–25 explicitly to existing bits0–24 in their current order; ID26=REFRACT_BEAM may map to bit25. IDs27–32 are reserved, not implicitly valid. IDs33+ can later exist with **no legacy mask projection**, through explicit authored `(form_id, capability_id)` rows or per-form bounded lists.

Add:

- `int creatures_supports_capability(unsigned form_id, unsigned capability_id);`
- `int creatures_party_supports_capability(const CreatureRoster *, unsigned capability_id);`
- `int creatures_party_set_requirements(CreatureRoster *, const CreatureU8 party[4], const CreatureCapabilityId *required, unsigned required_count);`

Reject unknown/disabled capability IDs; an invalid form does not satisfy even an empty capability. The party query checks only actual active members, not historical collection/storage. New party-set is atomic, checks duplicate/invalid refs, preserves selected identity, and validates every explicit required capability against the proposed active party. Bound per-route requirement count (propose8) and reject oversized/unregistered lists. Manual route alternatives are expressed in the route solver, not as fake creature capabilities.

Legacy `creatures_capabilities(form)` returns only its exact low32 projection; `creatures_has_capability(form,needed32)` retains existing zero-mask behavior for a valid form and false for invalid forms; old `creatures_party_set(...,required32)` is unchanged. Never shift by an ID>32, truncate a high capability into the mask, reinterpret a high action as an old phase or claim that a zero legacy projection means no extended capability. A dedicated query is authoritative for new routes. Polarity remains a separate field, not a capability bit.

Field dispatcher binds capability + tagged target kind + bounded geometry to a handler. Optional advanced methods can test a form/edge tier through explicit policy; they cannot require a combat signature to be equipped. No map pixel or item damage phase silently creates a capability. Evolution must preserve the full key set as well as legacy mask.

## Immutable historical validation snapshots

Use full per-revision snapshots or versioned immutable rows covering:

`forms, collection IDs, per-form learned-command/min-level pairs, per-family trial masks, minimum incoming-edge level, phase/polarity, gear IDs/source map, quest masks/allowed variables, region/discovery/anchor masks, room/spawn policy, reward-source relationships`.

A bank is validated against its exact declared revision BEFORE current-policy validation or migration. Accept only1,2,3,4; future values fail. The full brief section7 lists exact historical command levels and forms. Do not let today's expanded learnset/trial union authorize old-bank bytes. Do not add strict historical causal trial/bond requirements which the old released validator did not enforce.

Revision1 forms1,2,4,5,7,8,10,11 and commands1–8; quest/gear reservations zero, existing starter migration exception.
Revision2 adds forms13,14,16 and commands9–11; gear1,2,9,10,17,18,33,34,49,50,65,81,82; quests0–10; sources0–12.
Revision3 adds19,20,22,23,73,74,75,76,77,78 and commands13–22; adds gear3,11,19,35,51,83; quests11–21; sources13–18.
Revision4 adds the exact Southern rows above only. Ability12 never allowed. Old masks exact as above; revision1 excludes later families, revision2 excludes Northern, revision3 excludes Southern; no historical F006 trial. All new source/visit/discovery bytes remain zero in old inputs.

Preserve legal historical generic creature reward bytes5–128 and all event/lifetime-aid bytes. They were broad API namespaces; apparent unused bits cannot be repurposed into mandatory new ownership. New recruits use typed source transactions around grant(...,reward_id0). An old aid bit suppresses repeat XP only, never a future world encounter, source or explicit training reward.

## Exact Southern source and discovery checks

Entry: NorthQ21 CLAIMED plus inherited Northern gates. Southern historical visits require this gate even when current checkpoint is outside the region.
Q22 claimed requires retained F028 instance, obtained79 or80, gear source19 and seen item4. Q23 claimed requires retained F031, obtained85 or86. The two quests do not allocate new generic creature reward bits.
Field source byte8 mapping and minimum visited location:

- bit0→F009/base25, visit31
- bit1→F010/base28, visit31
- bit2→F029/base81, visit33
- bit3→F030/base83, visit31
- bit4→F032/base87, visit31 plus discovery byte18 bit0
- bit5→F033/base89, visit31
- bit6→F034/base91, visit32 plus discovery byte18 bit1
- bit7→F035/base93, visit33

All require town30 visit and entry gate. A claimed source retains its exact family and enabled obtained history, active or stored. Source bit never means merely seen.
Discovery18:0 requires visited32 and Q29 objectives complete (READY or CLAIMED); discovery18:1 requires visited32 and Q28 objectives complete (READY or CLAIMED). The environmental interaction that reveals each is checked at mutation time; save policy checks those durable prerequisites. Quest reward claim is not required to encounter the creature, so a full gear bag cannot conceal the creature forever.
For new Southern families, a persisted personal-trial bit requires SOUTH_READY, its matching retained-source contract and the stated level/bond floor on that same individual. New evolved Southern forms require the exact trial/floor/source contract. These newly authored causal checks must not be retroactively imposed on historical old-family records.
Room30 spawns0–4,31 spawns0–3,32–37 spawn0; current visit required; town bit required for other region visits. Rooms34–37 require Q22/Q23 CLAIMED;35 requires Q24 prefix1,36 prefix3,37 prefix7. New anchor bits imply30/31 visit respectively. Coordinates belong to integration lead's region contract and need collision checks.

## Non-grinding and polarity guardrails

No changes to old five-phase multipliers or generation/control relationships. No new Yin/Yang damage multiplier or “canon” claim.
For a mechanically readable optional polarity activity, use an explicitly invented two-receiver display: Yin-authored companion can *hold* a receptive lens state; Yang-authored companion can *pulse* its release. Labels/icons show actual independent polarity. Stations latch sequentially so four-party capacity and swaps are safe, and manual A controls offer the same town lesson. It is an optional discovery/trial variation, not a mandatory dual-polarity blocker (both guaranteed Southern recruits are Yang). Never equate shade with Yin/evil or sunlight with Yang/good. Actual family command timing/geometry remains independently authored.

## Must-pass before enabling content

Legacy API mutation snapshots byte-exact; all historical whitelist adversarial matrices; wrong-family local-mask collision cases; duplicate/overflow trial definitions; zero-write invalid save snapshots; old→4 byte preservation; generic-reward collision fixtures; all interrupted writes/retries; stable identity lock; branch target selection/defer/ambiguity tests with test-only catalogs; key-based capability IDs33+ tests with no projection overflow; full160 roster and48 bag bounded save timing; no game.c/UI ownership conflict. Source rows remain design-only until actual handlers/art/acquisition and native controller evidence pass separately.

## Required companion main-route correction

The integration lead requires one mandatory REFRACT_BEAM interaction in room34 (Q24 objective1) after guaranteed79, and one mandatory TUNE_LATCH interaction in room35 (Q24 objective2) after guaranteed85. Both use selected active form capabilities independently of equipped combat command. Base79+85 suffice; no evolution, old Earth, gear or optional recruit is required. Manual mirror/shutter positioning, RESET, emergency escape and safe journal reassignment remain available; manual controls cannot grant/bypass these two objectives. Stored ownership is preserved and can be reassigned at any safe approach. Keep this in the target/route contract; core does not edit game.c or UI integration.
