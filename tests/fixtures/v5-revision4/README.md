# Delivered Southern S3 migration fixtures

These are exact controller-generated SRAM bytes from the delivered Southern S3
ROM, not constructed host states and not user save data. Only copies in this
directory were written. Southern source artifacts were read and hash-checked.

## Inputs

| Fixture | Original snapshot | Obtained forms | Owned instances | Gear | Claimed quests |
| --- | --- | ---: | ---: | ---: | ---: |
| `southern-all41-town.sav` | `08-complete41-independent-reboot` | 41 | 21 | 25 | 30 |
| `southern-minimal8-town.sav` | `05-minimal-independent-reboot` | 8 | 8 | 2 | 6 |

Both are 32 KiB SRAM files with two CRC-valid format-5/content-revision4 banks.
Both resume in Southern town, room 30. The minimal route has only quest IDs
11, 13, 21, 22, 23, and 24 claimed; no Core/ending flags, optional Southern
recruits, optional Southern quest claims, or Southern evolution/trial completion.

The latest all41 bank has sequence 359, and the latest minimal8 bank has sequence
67. Both latest banks are at offset `0x200`. The fixtures preserve both original
banks, all other SRAM bytes, party order/selection, and every recorded identity.

## Immutable identities

- ROM: `87d16a0fc513d7e8a491e0b5ac5929f7951e1e44e18b7f534f1e5e0cc794d4de`
- Symbols: `ceedba1a6052fe450f17c91375eef6ddd5200d1a7bb01394c1eb95d2bc4f1305`
- All41 SRAM: `0bd83c19eb0dee81b3cd9e2b48462f6362b559786e38fa119312fe05787b0bd3`
- Minimal8 SRAM: `968066ed983bd48fc2af0d7ffeb79f635624037ef2099809fd00c97aaa04cc0c`
- Journey report: `780317f27cb2595ece2741a33edc085aa6646e0ab2687e98f2a62689056fd635`
- Minimal-route report: `b028d1aa5020b53fa9b17eed863921d39d66c6bff0e93c93b464546452045b09`

`provenance.json` and `southern-minimal8-town.provenance.json` retain source
locations, snapshot records, producer hashes, and independently decoded wire
counts. The originals' ROM, symbols, 707 runtime-source files, producer test
files, and every reported state/SRAM pair were checked before copying. No
machine state was loaded. The immutable source manifest is also archived.

## Exact report storage

The 3,112,391-byte journey report uses 104 parts under
`southern-journey-producer/report_parts/`; the 569,857-byte minimal report uses 20
parts under `southern-minimal-route-producer/report_parts/`. Every part is valid
UTF-8 and at most 30,000 bytes. Concatenate in each manifest's `parts` order to
recover the exact original bytes and SHA-256. Reports were not minified,
reformatted, regenerated, or re-pinned.

`producer-test-source/` retains the exact eight producer scripts. The minimal
report also pins its Northern ancestor fixture and producer archive, which are
already preserved under `tests/fixtures/v5-revision3/`.

## Verify

Run from the repository root:

```sh
python3 tests/test_southern_frozen_fixtures.py
```

This read-only host suite checks part hashes/order/size, reconstructed source
hashes, target ROM identity, producer sources, fixture hashes, both bank CRCs,
counts, and the minimal route's absent optional progress. Original source files
are additionally checked when available; the archived evidence is portable.
The SRAM files are inputs for separate forward-migration tests and do not by
themselves demonstrate Magma acquisition or gameplay correctness.
