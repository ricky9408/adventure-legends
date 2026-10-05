# Eight-form creature core

This directory preserves the original **design-only** authoring catalog and
schema, with 12 proposed designs and 128 reserved identities. `enabled.json`
separately selects the eight runtime forms: 1, 2, 4, 5, 7, 8, 10, and 11. It is
not evidence of 128 implemented creatures. Water, Metal and legendary forms
remain disabled; no reserved form is an encounter fallback.

Run `python3 assets/creatures/generate_data.py` to validate the source and rebuild
`src/creature_data.c`. `--check` checks the checked-in generated file without
writing. The generator's identity lock and schema validation reject field loss,
phase/polarity errors, cyclic evolutions and reserved endpoints. These data rows
contain proposed combat weights, not evidence that new combat handlers are
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
  safety and sanctuary-return integration. There is no release API
- `creatures_grant_story` checks story gates, gives the party's median level
  with chapter floors 1/1/8/14 and bond 20, and is idempotent even after evolution.
  Reward IDs 1–4 are reserved for those four story families. General rewards use
  IDs 5–128; ID 0 is explicitly repeatable. A full roster never overwrites a
  member or consumes a reward. Callers remain responsible for authored recruit
  trials and repeatable encounter gating
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
  trial and award its event exactly once
- `creatures_can_evolve` returns visible requirement reasons. All requirements
  are ANDed: level, bond, chapter, matching personal trial and sanctuary.
  `creatures_evolve` also needs explicit confirmation. Defer makes no changes.
  Evolution preserves XP, bond, ID, cosmetic seed and equipped old commands;
  the signature becomes learnable but is not silently equipped. Both forms
  remain in seen/obtained masks
- `creatures_roster_validate` is intended for grants, save/load, and mutation
  tests, not every frame. It performs bounded duplicate-ID checks. Per-command
  checks inspect only the selected form or four party references

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
all four evolutions, deferred evolution, learned-command retention and every
migration chapter. Eight deliberately damaged C data tables must fail validation.
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
