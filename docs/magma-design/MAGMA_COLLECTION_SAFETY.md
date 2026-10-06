# Collection admission: all-choice-order capacity contract

Design revision2,5 October2026. This is a newly identified integration gate. It is not implemented in a game runtime or historical save reader by this packet.

## Defect in the original design

Deterministic unlimited branch-base recruitment was not safe merely because each transaction checked160-record capacity. Without release or replacement, a player could repeatedly evolve those bases into an already-owned terminal branch, fill storage, and permanently block a missing branch or a later guaranteed companion. A FULL result followed by “retry” could not recover that legal play state. The original single constructive34-individual route did not prove safety under every allowed choice order.

This revision keeps real extra individuals, existing companions, optional duplicates and explicit evolution choice. It adds a prospective admission test before gameplay mutations. No generic release, silent replacement, erased history, synthesized companion or new wire field is introduced.

## Exact invariant

The approved final topology has60 families and72 terminal-instance opportunities:

- Twelve linear-three families:12 terminal opportunities
- Twelve two-choice branch families:24
- Twenty linear-two families:20
- Eight ordinary singles:8
- Eight legendary singles:8, retained in storage under the separate one-active-legendary rule

Let N be all occupied retained roster slots, active or stored. Let V be the maximum number of distinct final terminal opportunities that those actual individuals can still realize. Compute V separately within each immutable family, then sum it. Seen/obtained history, source receipt bits, quest completion and active-party references never substitute for an individual.

Define E=N−V, the number of extra copies beyond viable terminal coverage. A state is admission-safe exactly when:

    E <=160−72 =88

Equivalently:

    free slots160−N >= missing terminal opportunities72−V

Reserve the full future72 opportunities now, including later regions and legends. Reserving only Magma's34 expected individuals would reproduce the same problem when the next region arrives.

### Family coverage is maximum matching, not a count of distinct form IDs

Use the reviewed final planned topology, including disabled future targets. This is a capacity reservation only; it never enables those targets or authorizes their acquisition. Each live individual can cover at most one terminal outcome.

A linear family or single contributes1 if any valid individual of that family is retained, otherwise0. A two-target branch family with b flexible bases, a copies of terminal A and c copies of terminal B contributes:

    min(b+a+c, (b+a>0 ?1:0) + (b+c>0 ?1:0))

Examples:

| Retained branch family | V contribution |
|---|---:|
|No individual|0|
|One flexible base|1, never2|
|Two flexible bases|2|
|A + one flexible base|2|
|A + A|1|
|A + B|2|
|A + A + one flexible base|2|

This is maximum bipartite matching between distinct actual individuals and the family's two reachable targets. Counting all target bits in the union without also limiting by individual count would incorrectly count one base as two individuals.

A bounded implementation may use one capped count byte and one reachable-target mask byte per family, about120 scratch bytes, plus a global occupied count. Immutable per-form metadata records family and terminal mask1/2/3. The supplied JSON contains all128 explicit rows. Keep this in ROM/EWRAM under existing budgets, not new IWRAM. Do not run it every frame. For a candidate grant/evolution, scan at most160 records with a virtual appended form or single-slot override; do not copy an entire roster onto the stack.

## Prospective admission rule

Evaluate the fully staged candidate before any durable or visible success mutation. The exact source, required trial, context, learned command, party/storage, level/bond, gear and save-transaction rules still apply. Admission is an additional check, not authorization by itself.

From an admission-safe state:

1. Require N_after≤160
2. Require N_after−V_after≤88
3. On refusal, leave the companion, source receipt, next instance ID, trial bits, bond/XP, gear, quest state, obtained/seen history and save state unchanged
4. On acceptance, use the normal atomic source/evolution transaction and interrupted-save protocol

Apply this to every forward gameplay source that can add an individual, including repeatable grant0 wrappers and future regions, and every evolution transaction that can reduce reachable terminal coverage. A lower-level grant/evolve function used by historical API fixtures is not automatically permission for a gameplay caller to bypass the new guard. Inventory rearrangement, party selection and assigning storage do not change N or V. Trials and training floors alone do not consume coverage; completing either branch's trial remains possible even when a later choice would be refused.

### Captures

- A first missing-family base increases N and V by1, so E does not change
- A missing branch's extra base increases N and V by1, so it also remains admissible at E=88
- A duplicate capture that adds no viable coverage increases E by1. Refuse it at E=88 even when there are many physically empty slots, because those slots are reserved for missing opportunities
- First source claims are idempotent. If a one-time receipt is already claimed, return the existing ALREADY_CLAIMED result before admission; a retry must not be presented as a newly refused capture
- First-extra branch receipts still mean an actual second distinct retained individual. Repeated later branch encounters remain deterministic and available, subject to this invariant rather than an arbitrary fixed two-capture limit

### Branch choices

An evolution does not change N. It can preserve V or reduce it by1; it cannot increase maximum reachable coverage, because evolution narrows an individual's future outcomes.

- Choosing either first branch from a family's only base preserves V=1 and remains allowed
- With A plus a base, choosing B preserves V=2. Choosing A reduces it to1
- That second A choice remains allowed if E≤87. The new E≤88 still reserves a slot for a later real base, which the deterministic encounter supplies
- At E=88, refuse only a choice that would reduce V. The player may keep the base, complete the other trial and choose the missing target, or defer indefinitely. Do not consume the already completed first trial or choose another target automatically
- If another flexible base or the missing terminal remains, evolving this copy into a duplicate can preserve V and is allowed. The rule is about global completion opportunities, not a blanket ban on duplicate terminal forms

### Player-readable refusals

Show the reason before confirmation. Do not reveal undiscovered creature names or regional spoilers.

For an extra capture: “Another copy would use space needed for companions you haven’t met. You can still invite a missing family or evolution path.”

For the last flexible opportunity: “This choice would leave no space for the other evolution path. Keep this companion as it is, or complete the other path.”

If both target names are already discovered, the branch screen may name the missing target and its actual unmet trial. Journal/source hints point to the same deterministic encounter and sanctuary. A refusal is not a failed capture roll, consumed reward, permanent exclusive choice or request to delete another companion.

## Why every allowed choice order preserves a completion path

This is an inductive capacity argument, not merely one favorable playthrough.

1. A normal Southern collection has21 actual individuals in21 families, so N=V=21 and E=0. It is safe
2. Every accepted mutation preserves E≤88 by construction. Therefore every state reached by any allowed sequence retains at least72−V free slots
3. For every uncovered family/branch terminal opportunity, its deterministic base acquisition can increase V by1 with one new real individual. E stays unchanged, so that acquisition remains admissible. If V<72, the invariant guarantees at least one physical free slot
4. Repeat at most72−V times. Occupancy becomes N+(72−V)=72+E≤160
5. Within each family, assign a maximum matching: keep existing terminal representatives first, then evolve flexible bases toward missing targets. Such a realization preserves V at every choice. Required linear intermediate evolutions also preserve V. No identity is cloned or replaced
6. Once every target has a representative, surplus bases may choose either existing target without reducing V

Source and trial availability remains a separate gameplay obligation. Every locked terminal path must remain deterministic, non-missable and reachable with safe returns and reassignment. The capacity proof cannot prove an unimplemented future region's art, quest or trial behavior. It proves that storage and all admitted choice orders do not themselves close that authored completion path.

## Grandfathered historical states: honest limitation

Never add E≤88 to revision1–4 bank validation, migration or normalization. Existing valid records, command/trial semantics and companions stay exactly preserved. Do not retrofit it into a revision5 bank predicate either: a valid imported over-budget roster must still be saveable without losing data. The guard governs new gameplay mutations only.

A pre-existing valid collection with E>88 is already outside the capacity theorem. Captures can keep E unchanged or increase it; evolution can only keep E unchanged or increase it. Consequently admission alone cannot reduce that excess or promise all72 final opportunities. A160-record historical collection with only one viable family remains physically full; “try again” cannot fix it.

For such a collection:

- Load, inspect, play and re-save under unchanged declared-revision legality rules
- Permit physical-capacity-respecting forward mutations only when excess does not increase and coverage does not decrease. Missing-family/missing-branch captures can be useful while space exists; ordinary linear evolution remains available
- Refuse worsening duplicate captures and coverage-losing branch choices; do not fabricate a completion guarantee
- Clearly explain that the older collection already uses more duplicate space than the expanded journey can support and may not fit every future companion
- Do not silently delete, replace, compact away or invent a release feature. Restoring completion for an already-overbudget roster requires a separately approved recovery feature or a player-selected earlier save/new collection. This packet does not authorize one

A malformed save is still rejected by its historical/current semantic reader for its actual invalidity. The admission model is not a replacement integrity check and makes no cryptographic provenance claim.

## Exhaustive model evidence and required native gates

terminal_admission.py evaluates every6,497 abstract safe(N,V,E) capacity state,25,665 admitted global transition classes and145 refused classes. It enumerates129,764 possible safe two-target branch multisets up to90 individuals,380,924 local capture/evolution transitions and178 coverage-losing choices. It checks maximum-matching realizations and finite completion from each sufficient state. Together with invariant closure, these cover all allowed future choice orders, not a fixed number of favorable sampled runs.

The adversarial suite additionally checks matching against all target-assignment patterns through six individuals,200 randomized220-action sequences, stable instance IDs, both branch choice directions, duplicate-source retries, full bags, full rosters, unchanged refusals, trial/history retention, all future roots, misleading historical collection bits and grandfathered over-budget states.

These are pure design-model tests. The eventual implementation must independently test every actual source/evolution mutation path, save interruption, modal UI and native controller flow. In particular, prove there is no unguarded gameplay grant0 path; no branch confirmation path that bypasses the prospective override; no source receipt written before admission; and no exception that reserves only currently enabled families. Add exact old-bank differential fixtures proving the new gameplay guard did not leak into historical validation.
