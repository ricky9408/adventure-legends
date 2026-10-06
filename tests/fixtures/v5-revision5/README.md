# Generated Magma revision5 regression fixtures

These are controller-generated test SRAM, not player saves. No ownership,
health, progression, or catalog receipts were injected into game RAM.

The primary `magma-all65-town.sav` is the exact independently cold-booted D
snapshot `03-full34-independent-reboot`: 34 distinct retained individuals,
65 actually earned histories, 38 claimed quests, town38 checkpoint3.
Its SHA-256 is
`a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858`.

`magma-all65-acquisition-town.sav` preserves its exact original D acquisition
input, SHA-256
`28a01170b27b9029546067e2866ee91cde1ee7f64ffd6564f37df836aa2c11eb`.
Both are unchanged 32KiB SRAM with two CRC-valid format5/content-revision5 banks.

## Authenticated production chain

- Exact D ROM: `90ba47f30a0c94c28f073d26cc31ac5f5c736eb4d6e704d090892d2776f1ffb2`
- Symbols: `add52be1a5d23d2e8df8fd616f4ef1c7fde8d3e1906e1d789925d68476cf50f6`
- Acquisition report: `055d1cf3c86f64cb9a5781731c252dc32b652e9b7d6f32b0cab104123ec9241b`, 26,884 passing controller assertions
- Independent lifecycle report: `8093ef37f4ae90174b24a3a12203c80c6bfaad94d5e087e5b65c4ede38c23bc6`, 647 passing assertions
- Runtime manifest: `a72fd93eddb0a39322b22e45caf0f4ac49496d962776ee616dfd83642342ef3f`, 893 verified inputs

The independent lifecycle loads only authenticated SRAM. It verifies exact
roster/quest/equipment preservation, actual same-family selection, native save,
independent reboot, real enemy death/retry, another reboot, and old-region return.
Its full34 native save presents180/180 hardware frames, with max219,356 cycles.
This is native emulator evidence, not physical-handheld testing.

## Portable evidence

`provenance.json` records exact endpoint metadata, both wire banks, acquisition
ancestry, source hashes, and original artifact verification. The two original
reports are archived as186 exact UTF-8 parts, each at most30,000 bytes. Their
manifests reconstruct the original bytes without reformatting or re-pinning.
The runtime manifest is similarly retained in four exact parts.

Each producer has its own archived exact test/helper sources. The acquisition
capture receipt also identifies imported observer scripts; lifecycle observers
were verified identical before archival. The differing acquisition and lifecycle
navigation scripts are intentionally retained separately. Original state/SRAM
pairs were hash-verified at capture; machine states are not shipped or loaded.

Run this read-only standard-library verifier from an exported source ZIP:

```sh
python3 tests/fixtures/v5-revision5/verify_fixture.py
```

To additionally verify a checkout still contains exact D runtime sources:

```sh
python3 tests/fixtures/v5-revision5/verify_fixture.py --runtime-root .
```

`CHECKSUMS.json` covers the complete archived folder except itself. The
deferred-anchor host probe always uses the pinned primary fixture, so the
authentic34 input case also runs when no local build artifacts exist. That probe
then deliberately changes host state for isolated assertions; its results remain
clearly labeled synthetic and do not replace the native controller provenance.
