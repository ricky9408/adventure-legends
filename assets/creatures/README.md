# Twenty-one-form creature core, content revision 3

Developer reference; contains companion, quest and progression spoilers.

This directory preserves the original authoring schema and 128 stable reserved
identities. The catalog now contains **22 authored designs**, including the
disabled legendary. Its historical `DESIGN_ONLY_NOT_IN_ROM` scope is proposal
metadata, not the current runtime manifest. `enabled.json` explicitly enables
**21 forms**: `1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 19, 20, 22, 23, 73, 74,
75, 76, 77, 78`. There are 31 learnset rows, 21 enabled commands (IDs 1–11 and
13–22), and ten enabled evolution edges. Ability 12, legendary 121, reserved
third-tier forms 21/24 and all other unlisted identities remain disabled.
A reserved identity is never an encounter fallback or proof of an authored form.

The five Northern families are Spoolbud/Loomcrown, Cindertray/Kilnbarrow,
Keelkip/Wakecradle, Cairncricket/Archspring and Rivetfoil/Gimbalcloak. The N5
controller journey obtains and independently reloads all 21 historical forms,
retaining eleven real family instances and the six previous instance identities.
That native proof, artwork, handlers, combat and UI acceptance are separate from
data/core validation. See [Northern verification](../../docs/NORTHERN_VERIFICATION.md)
and [the exact-ROM summary](../../docs/northern/summary.json). Header-enabled
rows or a host API grant alone do not establish obtainability. The full 128-form
roster and legendary progression remain unfinished.

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
  Dewspindle/Tidewheel. Chimeclasp (family 6) retains no personal trial bit.
  Northern masks 32/64/128/256/512 belong to families 7/8/25/26/27, respectively.
  Family IDs are sparse keys, never compact-array offsets or shift counts.
  `creatures_family_trial(form_id)` resolves the reviewed one-hot 16-bit mask;
  do not derive it with `1 << family`. Zero, combined and wrong-family trial
  flags are rejected
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
    (quest2_claimed ? CREATURE_REED_RESTORED : 0) |
    ((quest11_claimed && quest13_claimed) ? CREATURE_NORTH_HARBOR_READY : 0) |
    (quest21_claimed ? CREATURE_COUNTERWORKS_STABLE : 0);
```

`CREATURE_EVOLUTION_CHAPTER_MASK` is 7; `CREATURE_REED_RESTORED` is 8;
`CREATURE_NORTH_HARBOR_READY` is 16; `CREATURE_COUNTERWORKS_STABLE` is 32;
`CREATURE_EVOLUTION_CONTEXT_MASK` is **63**. Campaign bit 3 is **ENDING_SEEN** and
must be stripped before deriving this separate context. The core cannot tell
raw campaign value 15 from a correctly composed context value 15. Story grant,
legacy migration and story catch-up APIs continue to accept the original
campaign flag namespace. Unknown evolution-context bits reject without mutation.

The core grant API still supports general reward IDs 5–128 and does not enforce
quest completion or synthesize it. Save5 and the quest transaction own exact
quest/reward/collection consistency. Revision-2 and revision-3 Save5 require claimed quest 2
to retain at least one valid owned form 13/14 and claimed quest 3 to retain
form 16, whether active or stored. Both blocking and incremental validation
reject history/reward-only claims; revision-1 migration is unchanged. Current-party
capability checks inspect active members only; story ownership is not a substitute
for the actual route capabilities supplied to `creatures_party_set`.

### Northern integration and legacy compatibility

Northern forms keep the original instance wire layout, stable IDs and old
field capabilities. IDs are sparse in every lookup: form 73 is not table index
73, family 25 is not array index 25, and absent command 12 is not a fallback.
The catalog rejects duplicate IDs, cross-family trial collisions, missing policy
rows, invalid learnsets and unknown enabled endpoints.

| Recruit quest | Base/evolved forms | Family | One-time creature reward | Personal trial |
| ---: | --- | ---: | ---: | --- |
| 11 | 19/20 | 7 | 7 | Quest 16, mask 32, level 16/bond 40 |
| 12 | 22/23 | 8 | 8 | Quest 17, mask 64, level 17/bond 40 |
| 13 | 77/78 | 27 | 11 | Quest 20, mask 512, level 20/bond 50 |
| 14 | 73/74 | 25 | 9 | Quest 18, mask 128, level 18/bond 45 |
| 15 | 75/76 | 26 | 10 | Quest 19, mask 256, level 18/bond 45 |

Quest 13 requires quest 11 CLAIMED. All five new evolutions require the
Harbor-ready context from **both** recruit quests 11 and 13 CLAIMED, the
matching trial and level/bond floor, sanctuary and explicit confirmation.
The separate Counterworks context exists without making the machine clear a
hidden prerequisite for these five evolutions. New commands are learned through
the authored learnsets; evolving never silently equips a signature or deletes
the old command. Trials must belong to the same retained instance that meets
the training floor, not two different copies.

All Northern recruits are ordinary occupied instances with flags 0 at grant,
not new story-locked companions. A full active party leaves the recruit in
storage, and a full roster rejects atomically without consuming its reward.
Quest claims own their typed recruit, gear and trial consistency. General
creature reward IDs 5–128 keep the prior independent semantics: an old generic
reward bit does not fabricate a Northern quest or force a new recruit. Existing
story IDs 1–4, legacy migration, original trial bits, field commands, XP/bond
ledgers and reward history retain their historical meanings.

Save5 uses content revision 3 and explicit revision-1/revision-2 whitelists,
not the current enabled table as a permissive older-save reader. The authentic
R5 all-eleven save is preserved and migrates without new rewards. See
[SAVE5.md](../../docs/SAVE5.md) and [save verification](../../docs/NORTHERN_SAVE3_VERIFICATION.json).

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
all ten evolutions, deferred evolution, learned-command retention and every
migration chapter. Twenty-six deliberately damaged C data tables must fail
validation. Six SHA256-pinned full-roster snapshots from the preceding core
assert byte-exact legacy migration/evolution compatibility. Host API grants
are explicitly distinguished from controller-based native obtainability tests.
`core-verification.json` is preserved **historical revision-2** object-size and
sanitizer evidence, not current Northern acceptance. New sparse-key tests in
`tests/test_creature_sparse.py` also run through the normal creature test suite;
they cover shuffled form/family/ability tables, full-width synthetic trial masks,
colliding policies, unknown IDs and sanitizer safety. Synthetic tables are
host-only probes, not extra enabled or obtainable creatures.

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

The current sanitizer exercises 24,000 mixed operations across old and Northern
families, 33,120 single-bit roster mutations, and 129,024 byte-value probes
(21 forms × 24 instance bytes × 256 values). The ARM core objects contain no libc
imports and no mutable `.data`/`.bss`; object sizes and compiler stack frames are
historically recorded in `core-verification.json`; do not carry those old size
figures forward as N5 measurements. Native N5 memory and frame measurements are
in the Northern report, and whole-program stack high-water remains unmeasured.
