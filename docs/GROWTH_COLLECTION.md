# Growth goals and Collection journal

The Growth tab previously showed only the first unmet evolution gate. Level or
bond messages hid the personal-trial clue, and branching families never showed
that clue there. Opening Evolve now shows every gate together, with current and
required level/bond, EXP to the next level, story/rest status, and the exact
personal trial. Up/Down browses goals, authored trial clues and the new technique;
Left/Right changes a branch. The existing frozen transaction still owns fresh-A
confirmation, admission, irreversible commit and cancellation. Viewing does not
grant progress or select a technique.

Collection is appended to the hub, preserving category indices0–7. It counts
the existing cumulative obtained ledger, groups discovered forms by family, and
distinguishes current individuals from historical forms and missing targets.
Known, currently owned and incomplete-family filters narrow browsing. A on an
owned form opens its exact storage candidate in Party, without assigning it.
Missing forms with an owned predecessor offer read-only growth goals; completely
unseen families are concealed. History and the Save5 layout remain unchanged.

The new text has its own GBJ UiRun compiler/data, preserving shared UI IDs. To
regenerate on a host with fonts outside the Linux default paths:

```sh
python assets/generate_growth_journal.py --font /path/to/NotoSansCJK-Bold.ttc --latin-font /path/to/DejaVuSans.ttf
```

`GBA_NOTO_FONT` and `GBA_LATIN_FONT` provide the same optional overrides. All
labels fit214×15 pixels. Generated includes remain bounded. Rare query/render
functions stay in ROM; the collection snapshot uses300 menu-only EWRAM bytes
and no new OAM slots. It is rebuilt on entry while the world is paused.

Validation:

- `python tests/test_growth_collection.py` exercises all68 edges ×32 independent
  gate combinations ×3 pages (6,528 real raster cases), branch-specific clues,
  EXP/max-level, zero/seen-only/full128 histories,60 families,160 individuals,
  filters, nested Back, exact Party handoff and unchanged save/recovery/selection.
  It also retains fresh-A evolution and complete old/new SRAM commit checks.
- `python tests/growth_collection_native.py --rom build/emberbond.gba --symbols
  build/emberbond.sym --bridge /path/to/native-bridge.so --output /fresh/output
  --fixture tests/fixtures/v5-revision9/covenants-all128-72-cold.sav` captures
  controller-earned fresh-opening UI separately from historical full-collection
  inspection. The helper hard-disables RAM writes and machine-state imports,
  checks wholeSave5/SRAM/recovery purity and records actual menu frame costs.

Native fixture inspection is not proof of fresh128-form acquisition or every
personal trial. Physical GBA display/hardware behavior remains a separate gate.
