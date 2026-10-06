# Southern authoring schema 2, content revision 4

Current authoring contains **42 designs**, including disabled legendary 121,
with **128 immutable reserved identities**. The separate reviewed ROM manifest
contains **41 enabled forms, 61 learned-command pairs, 20 evolution edges and
41 abilities**. Only forms **25, 26, 28, 29, 79–94** and commands **23–42** are
added here. Ability 12, legendary 121, third forms 27/30, all branching families
and all other unlisted rows remain disabled. These counts establish authored
core data only, not native gameplay, acquisition, sprite or combat acceptance.

## Stable identity, order and bounded generation

- `identity-lock.json` is unchanged (SHA-256
  `fe553a9d963de059e7d6c0f8647ab6a3fe736c5fdf7ca8d3b18c6dedd3292969`)
- Authored forms and abilities stay ID-sorted. `enabled.json` specifies stable
  ROM table order independently: the original 21 forms precede the 20 Southern
  forms, even though IDs 25–29 sort before Northern IDs 73–78
- Three generated const u8 ROM maps provide bounded form, command and incoming
  evolution lookup without scans. A stored value is the table row plus one;
  zero always means disabled/absent. IDs are checked before indexing and every
  index-backed table is capped at 255 rows. The maps retain explicit manifest
  order and do not enable any reserved identity
- Existing generated form, learnset, edge and ability prefixes are byte-exact.
  New pair `i` has base/evolved learn offsets `31+3*i` / `32+3*i`, and its edge
  starts at `10+i`. Zero-edge forms retain offset zero
- Schema 2 allows command IDs through **255**, matching the unchanged saved
  command byte. It does not enable any command implicitly. Every enabled ID
  remains in an exact content-revision whitelist in `catalog_policy.py`
- The original schema is preserved byte-for-byte as `catalog.v1.schema.json`.
  The validator automatically selects it for archived schema-1 catalogs,
  retaining their 63-command authoring ceiling and original capability order
- Multi-edge generation uses an explicit count and contiguous manifest offset,
  rejecting split source groups and overflow of u8 counts/u16 offsets. Actual
  branching rows remain disabled. The authoring validator accepts only the
  immutable reserved branch topology, with no cycles, merges, cross-family
  edges, lost field actions or delayed/lost inherited commands

## Qualified trial and capability authoring

`trial_bindings` names the family, local trial key, one-hot u16 wire mask,
introduction revision, source forms and prerequisite mask. Keys and wire bits
must be unique within their family; prerequisites are known, acyclic and no
newer than their dependent trial. Every executable edge references a trial
bound to that same source family. Current ROM mappings are separately checked
against explicit reviewed policy rather than inferred from family numbers.

Legacy trial bits remain 1, 2, 4, 8, 16, 32, 64, 128, 256 and 512 with their
original owners. F006 remains unassigned. Southern families F009, F010 and
F028–F035 each explicitly map **local key 1 to wire mask 1**. All ten new edges
require their own trial and **SOUTH_READY = 64**, plus their authored level/bond,
sanctuary and explicit player confirmation. New requirements do not reinterpret
legacy unqualified APIs or campaign chapter flags.

All old capability bits 0–24 retain their meaning. The sole appended capability
is **REFRACT_BEAM at bit 25 (`0x02000000`)** for forms 79/80. Existing abilities
and field actions remain independent; no generic phase grants an action.

Japanese name and command text is appended in `ui_additions.json`; this change
does not run or modify global UI generation. New command cooldown targets are
90 updates for base signatures and 120 for evolved signatures. Stat weights
are authored 180/240 totals, not evidence that every weight is a combat consumer.

## Reproducible authoring checks

```
python3 assets/creatures/validate_catalog.py
python3 assets/creatures/generate_data.py --check
python3 tests/test_southern_catalog.py
# Archived source, with its exact historical manifest:
python3 assets/creatures/validate_catalog.py OLD_CATALOG --enabled OLD_MANIFEST
# Standalone archived design validation, with no runtime enablement claim:
python3 assets/creatures/validate_catalog.py OLD_CATALOG --catalog-only
```

The focused tests pin old authored rows, original schema, identity lock and
legacy generated table bytes; exercise local-trial collisions/overflow, exact
enabled boundaries, command-byte limits, inheritance, branch topology,
prerequisite cycles, multi-edge layout and deterministic generation. Native C,
save migration, battle handlers, sprites, route safety and controller-based
obtainability are separate integration gates owned by their corresponding tests.

The notes below are preserved historical documentation. Their eleven-form,
revision-2 counts and masks describe that earlier release, not current totals.

---

# Historical river/core notes, content revision 2

This directory preserves the original authoring catalog and schema, with **12
fully described designs and 128 reserved identities**. Its historical
`DESIGN_ONLY_NOT_IN_ROM` scope describes that original proposal, not the current
runtime manifest. `enabled.json` separately enables eleven core definitions:
1, 2, 4, 5, 7, 8, 10, 11, **13 Dewspindle, 14 Tidewheel and 16 Chimeclasp**.
Abilities 1–11 and five evolution edges are enabled. Legendary 121, every other
placeholder, and ability 12 remain disabled. No reserved identity is an encounter
fallback and no count here claims 128 authored creatures.

This directory reports **data/core** acceptance separately from gameplay. The
river release also passes acquisition, original sprite, combat, quest and UI
integration tests; all eleven forms were obtained and reloaded in one normal
controller-driven collection. See `docs/reedhaven/summary.json` for that exact-ROM
evidence rather than treating enabled data rows alone as proof of obtainability. The
original proposal's repeatable acquisitions and gate descriptions remain design
history; the actual one-time regional reward contract is documented below.

Run `python3 assets/creatures/generate_data.py` to validate the source and rebuild
`src/creature_data.c`. `--check` checks the checked-in generated file without
writing. The generator's identity lock and schema validation reject field loss,
phase/polarity errors, cyclic evolutions and reserved endpoints. These data rows
contain authored combat weights, not evidence that new combat handlers are
implemented or balanced. Sprite offsets are deliberately zero; the separate
art subsystem resolves the selected enabled form. No artwork is included here.

## Runtime contract

`src/creatures.h` defines all public APIs. There is no malloc and no mutable
module-global state. Keep caller-owned `CreatureRoster` in EWRAM, not on the
stack. It is 4,140 bytes, including 160 exact 24-byte instances, four reference
indices and compact persistent ledgers. New ROM tables and functions remain
outside `game.o`, hence outside its IWRAM placement.

- Form IDs 1–128 are reserved identities; only `creatures_form(id) != NULL`
  means enabled content. ID 0 is empty; party index 255 is empty. Do not use a
  form ID as a roster index or a legacy companion index
- Use `creatures_legacy_spirit` as the compatibility adapter for both original
  and evolved forms. `creatures_capabilities` preserves every original field
  action independently of equipped combat commands. Wood Midori and Wood Fuuri
  have different capability sets
- `creatures_party_set` rejects duplicate/out-of-range references and missing
  caller-supplied required route capabilities. It preserves selected creature
  identity when sorting. Storage/release UI still requires the separate route
  safety and sanctuary-return integration. There is no release API. Regional
  recruits are retained ordinary owned instances, not story-locked instances;
  changing party composition does not delete stored companions
- `creatures_grant_story` checks story gates, gives the party's median level
  with chapter floors 1/1/8/14 and bond 20, and is idempotent even after evolution.
  Reward IDs 1–4 are reserved for those four story families. General rewards use
  IDs 5–128; ID 0 is explicitly repeatable. A full roster never overwrites a
  member or consumes a reward. With a full four-member party, new recruits stay
  in storage; no story companion or party reference is silently replaced.
  Callers remain responsible for authored recruit trials and encounter gating
- XP uses `4*(L-1)^3`, level 1–50 and a saturating 470,596 cap. Only eligible
  party members receive credited event XP. Storage receives none. Bond is
  capped at 100 and +10 per member per expedition
- Event IDs 0–383 are authored encounter/quest IDs; 384–511 are field-aid
  events mapping to lifetime field-aid IDs 0–127. One shared expedition bitmap
  prevents repeat credit or party-swap farming. Aid bond is awarded only for the
  lifetime first aid. `creatures_begin_expedition` clears expedition counters
  and event bits, never lifetime aid bits or personal trials. Reserve unique IDs
  in the gameplay authoring layer; don't derive IDs from hits or frame count
- Personal trials are external authored achievements. `creatures_mark_trial`
  accepts only the owning family's flag and does not fabricate completion,
  clear objectives or grant rewards. Caller must prove its distinct-object
  trial and award its event exactly once. Flags 1/2/4/8 keep their original
  families; flag 16 (`CREATURE_TRIAL_PAIRED_POOLS`) belongs exclusively to
  Dewspindle/Tidewheel. Metal has no personal trial bit in this revision. Zero,
  combined and wrong-family trial flags are rejected
- `creatures_can_evolve` returns visible requirement reasons. All requirements
  are ANDed: level, bond, evolution context, matching personal trial and sanctuary.
  `creatures_evolve` also needs explicit confirmation. Defer makes no changes.
  Evolution preserves XP, bond, ID, cosmetic seed and equipped old commands;
  the signature becomes learnable but is not silently equipped. Both forms
  remain in seen/obtained masks
- `creatures_roster_validate` is intended for grants, save/load, and mutation
  tests, not every frame. It performs bounded duplicate-ID checks. Per-command
  checks inspect only the selected form or four party references

### Regional integration contract

- Quest 2 CLAIMED recruits form 13 at level 10/bond 20 through reward ID 5
- Quest 3 CLAIMED recruits form 16 at level 10/bond 20 through reward ID 6
- Both grants use flags 0, giving `CREATURE_OCCUPIED` only. They never use
  `CREATURE_STORY_LOCKED`; protected legacy story families remain owned even
  when the active party changes
- Quest 4 is the Water personal trial and marks bit 16 after successful reward
  commit. It is distinct from quest 2's recruitment/restored-basin gate
- Evolution 13→14 requires level 15, bond 45, the restored-basin context gate,
  Water trial 16, sanctuary and explicit confirmation. Default ability 9 is
  preserved; signature 10 becomes available at level 15 but is not auto-equipped.
  Chimeclasp defaults to ability 11 and has no enabled evolution
- `CreatureEvolution.chapter_flags` keeps its old field name/layout but holds
  **evolution context**, not raw `CampaignSave.chapter_flags`. Use:

```c
unsigned context = (campaign.chapter_flags & CREATURE_EVOLUTION_CHAPTER_MASK) |
    (quest2_claimed ? CREATURE_REED_RESTORED : 0);
```

`CREATURE_EVOLUTION_CHAPTER_MASK` is 7; `CREATURE_REED_RESTORED` is 8;
`CREATURE_EVOLUTION_CONTEXT_MASK` is 15. Campaign bit 3 is **ENDING_SEEN** and
must be stripped before deriving this separate context. The core cannot tell
raw campaign value 15 from a correctly composed context value 15. Story grant,
legacy migration and story catch-up APIs continue to accept the original
campaign flag namespace. Unknown evolution-context bits reject without mutation.

The core grant API still supports general reward IDs 5–128 and does not enforce
quest completion or synthesize it. Save5 and the quest transaction own exact
quest/reward/collection consistency. Revision-2 Save5 now requires claimed quest 2
to retain at least one valid owned form 13/14 and claimed quest 3 to retain
form 16, whether active or stored. Both blocking and incremental validation
reject history/reward-only claims; revision-1 migration is unchanged. Current-party
capability checks inspect active members only; story ownership is not a substitute
for the actual route capabilities supplied to `creatures_party_set`.

### Explicit story catch-up compensation

The current integration adds these transparent design choices so imported
checkpoints need not replay early training. `creatures_apply_story_floors` never
reduces XP or bond and is idempotent:

| Cleared chapter | Homura / Midori | Fuuri | Kohaku |
|---|---|---|---|
| Grove | Level 12, bond 30 | No extra floor | No extra floor |
| Sky | Level 16, bond 40 | Level 16, bond 45 | No extra floor |
| Core | Level 20, bond 50 | Level 20, bond 55 | Level 20, bond 50 |

`creatures_migrate_legacy` first creates only unlocked companions at the ordinary
migration floors, then applies this compensation. Normal new joins do not
implicitly apply it. Gameplay may explicitly invoke it at chapter milestones.
The original proposal's migration bond 20 remains in the preserved design source;
this table documents the new implementation decision rather than rewriting it
as historical player progress. These floors never complete personal trials.

## Save integration and verification

The 24-byte instance layout matches the proposed wire offsets, but **never save
raw structs**. `save5.c` owns byte encoding, CRC, bank commit and legacy migration.
The 160 expedition counters + 64 event bytes + 16 lifetime aid bytes occupy the
shared quest/bond reservation after its 264 authored quest bytes. All reserves
and future item encoding belong to the save subsystem.

Run `python3 tests/test_creatures.py`. Tests compile and call the actual native C
code, test all 50 XP boundaries and 25 phase pairings, fill all 160 slots,
exercise rewards, corruption, collection, party safety, XP/bond event deduplication,
all five evolutions, deferred evolution, learned-command retention and every
migration chapter. Twenty-six deliberately damaged C data tables must fail
validation. Six SHA256-pinned full-roster snapshots from the preceding core
assert byte-exact legacy migration/evolution compatibility. Host API grants
are explicitly distinguished from controller-based native obtainability tests.
`core-verification.json` records object-level ARM sizes and a sanitizer smoke run;
these are not full-cartridge timing or playable-campaign acceptance claims.

The deterministic mixed-operation sanitizer harness is reproducible with:

```sh
cc -std=c99 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Isrc src/creatures.c src/creature_data.c tests/creatures_sanitizer.c \
  -o /tmp/creatures-sanitizer
ASAN_OPTIONS=detect_leaks=0:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
  /tmp/creatures-sanitizer
```

Leak checking is disabled only because this execution environment uses ptrace;
address and undefined-behavior checking remain enabled. No creature core function
allocates dynamic memory.

The current sanitizer covers 24,000 mixed operations including stored Water and
Metal recruits, 33,120 single-bit roster mutations, and 67,584 byte-value probes
across all eleven enabled instance types. The ARM core objects contain no libc
imports and no mutable `.data`/`.bss`; object sizes and compiler stack frames are
recorded in `core-verification.json`. These are not complete-engine timing or
whole-program stack-high-water measurements.


The complete Southern S3 cartridge is independently accepted in `docs/VERIFICATION.md` and the bounded `docs/southern/` reports. Catalog enablement alone remains insufficient evidence of native acquisition or combat. `format_catalog.py` stores one semantic record per line without changing values or order; `--check` verifies this bounded, deterministic publication format.
