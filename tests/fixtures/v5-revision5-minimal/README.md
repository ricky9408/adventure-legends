# Authentic final-D Magma minimal prerequisite

`magma-minimal10-town.sav` is an unchanged 32,768-byte, controller-generated
Magma save. It is the original `09-minimal-independent-reboot` snapshot, after
the required Magma main route and before the old-region return. This is archived
historical native-emulator evidence, not a new acquisition run or a player save.

- SRAM SHA-256: `f584de3b29cb77731148b31b99dc40e0c7e4ec05f1aac42e0d38dd5b44612eeb`
- Delivered D ROM: `90ba47f30a0c94c28f073d26cc31ac5f5c736eb4d6e704d090892d2776f1ffb2`
- Original report: `c650e0982ff84ecda77faf4cc75270d2eff6ac73f05596ed8ffedd3f39715632`
- ELF: `0b56a0a525ef59d36b14a89a2786e5811f29fd9a54c386093fa06528f3afcc99`
- Symbols: `add52be1a5d23d2e8df8fd616f4ef1c7fde8d3e1906e1d789925d68476cf50f6`

## Decoded state, independently checked against the producer

Both CRC-valid format5/content-revision5 banks contain:

- Ten retained base individuals with stable IDs 1 through 10. Owned forms, in
  roster order: 1, 4, 7, 10, 19, 77, 79, 85, 31, 34
- Exactly ten obtained histories, matching those owned forms
- Nine claimed quests: 11, 13, 21, 22, 23, 24, 30, 31, 32
- Gear items 1, 4, 20; only starter sword item 1 equipped
- Room 38, checkpoint 3, chapter flags 3; bank sequences 95 and 94
- No personal trial flags, evolved forms, optional quest progress, optional
  recruits, or unearned earlier Core/ending flags

The eight prior identities are byte-identical at import. Their final records
preserve form, stable identity, commands, seed and trial fields; only ordinary
level/bond/XP may increase. All thirty earlier quest states, objectives,
variables and reward receipts are unchanged. The mandatory field route uses
only teaching base 31/individual 9 and base 34/individual 10.

The original run has 1,837 passing controller assertions, zero reported game-RAM
writes, zero machine-state loads, and an independent cold SRAM reboot. Its
archived controller subclass rejects writes and machine-state loads. Historical
emulator evidence does not establish physical-handheld behavior, nor does it
establish that the new Underwater ROM awards or preserves this state correctly.

## Portable evidence and verification

Run with Python3, from any working directory, with no emulator or dependencies:

```sh
python3 tests/fixtures/v5-revision5-minimal/verify_fixture.py
```

The verifier checks the fixture SHA, both CRCs, canonical wire fields, exact
retained records, minimal semantics, original report assertions, SRAM-only
ancestry, every report/helper part, and the complete file ledger. It performs no
emulation, save mutation or machine-state load. It remains fail-closed with
Python's `-O` flag.

Run the seven portable export/corruption/CRC/semantic regression tests with:

```sh
python3 tests/fixtures/v5-revision5-minimal/test_verifier.py
```

Optional local authentication of the still-present original artifacts:

```sh
python3 tests/fixtures/v5-revision5-minimal/verify_fixture.py \
  --runtime-root ../adventure-legends-magma-candidate-d \
  --original-run ../adventure-legends-magma-candidate-d/build/magma-independent-minimal-d1
```

`producer/report_parts` preserves the exact original Magma report in 15 UTF-8
parts of at most 30,000 bytes. `ancestry/report_parts` preserves its authenticated
Southern minimal-eight predecessor report in 19 such parts.
`ancestry/southern-minimal8-input.bin` is an exact byte copy of the earlier SRAM,
retained solely as an ancestry input. Its `.bin` suffix does not represent a
conversion; its original SRAM SHA is
`968066ed983bd48fc2af0d7ffeb79f635624037ef2099809fd00c97aaa04cc0c`.

The exact runtime source manifest is preserved in four parts. All 893 runtime
entries were verified against the immutable candidate-D source tree at capture;
the save wire-schema source subset is archived too. All 13 Magma and 15 Southern
original SRAM/state pairs were read and hash-verified. Machine states, ROM, ELF,
and symbols are not shipped or loaded by this package; their verified original
identities are recorded in `capture-verified-originals.json`.

## Source-authentication boundary

The seven helpers individually pinned in the Magma minimal report are copied
from its original `test-source` archive. In particular, the minimal run's
`magma_journey.py` SHA is
`bc0dd73960c23816c1d5bd53b7dff6ebbde015e5da8181f397249c3ec87e51e5`.
It is intentionally different from the later all65 helper and was not re-pinned.

The original report did not hash every imported observer module or the bridge C
source. Six available supplemental source files are preserved separately with
capture-time hashes, clearly marked as capture-only. Their exact historical use
cannot be independently authenticated from this report. The emulator bridge
binary itself matches the original report's hash. This distinction is retained
in `producer/source-capture.json` and `provenance.json`; no missing provenance is
invented or retroactively inserted into the original report.

All text files are smaller than 90,000 bytes. `CHECKSUMS.json` covers every
archived file except itself. The existing `v5-revision5` all65 fixtures and all
source-run files remain unchanged. Only this folder's primary `.sav` has a new,
exact-path `.gitignore` exception.

For a new chapter test, copy the primary `.sav` to a fresh output location and
cold-import SRAM into the new ROM. Keep the archived fixture read-only and
record new native evidence separately; never load the old machine state.
