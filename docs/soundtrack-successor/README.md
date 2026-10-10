# Current soundtrack release acceptance

`make test` runs current runtime/behavior checks plus explicitly labeled historical compatibility proofs. Native gameplay, audio output, and performance remain separate gates; host source proofs do not establish hardware behavior.

## Three distinct layers

1. `verify_soundtrack_successor.py` authenticates the complete current runtime file set and all bytes, soundtrack source inputs, and a finite reviewed delta against the pristine companion-browsing parent. The allowed change is music transport/catalog/PCM and three generated ending-credit fragments. Gameplay, save, geometry, and renderer implementation are unchanged. Unexpected files, missing files, unapproved runtime edits, changed authoring/PCM, and altered contracts or inverse payloads are rejected.
2. Historical proofs run on authenticated historical inputs only. The exact parent runtime is reconstructed in a temporary directory and passed through the unchanged companion/endroll/GBJ/I4 chain. The old renderer comparison and its 28 negative tests remain unchanged. The recovered G5 UI corpus matches the immutable original 431-file corpus digest; all 26 story and 24 parent tests, including their original negative controls, run unchanged. These inputs are never compiled into the release ROM, and historical pixels are never described as current pixels.
3. Current behavior runs against actual current sources: the complete retained engine/save/equipment/transaction suite, current geometry and authored directions, GBJ glyph and six-span-family checks, ending clipping/state checks, current ending full-frame/mutation checks, and actual C music transport sanitizers plus importer rejection tests. The current geometry adapter preserves unchanged geometry methods; its deliberately excluded old-font pixel methods are represented by the historical proofs and separate current font tests.

## Reproducible commands

Build the ROM with the normal ARM toolchain and prepare the documented mGBA bridge before the host aggregate, because several host suites also execute small ARM benchmark ROMs:

```
make
sh tools/build_mgba_bridge.sh
make test
```

Focused checks:

```
python3 tests/verify_soundtrack_successor.py
python3 tests/verify_soundtrack_successor.py --renderer-negatives
python3 tests/test_soundtrack_historical_ui.py
python3 tests/test_soundtrack_historical_ui.py --parent
python3 tests/test_soundtrack_geometry.py
python3 tests/test_soundtrack_runtime.py
```

The historical parent archive SHA-256 is recorded in `contract.json`; only the necessary exact inverse source bytes are included in `parent-inverse.json.gz`. The historical UI fixture contains source/metadata only, bound to the unchanged old corpus and contract hashes. Existing contracts are preserved verbatim. No old hash is repinned to accept new runtime bytes.

The original obsolete aggregate failures are superseded, not relabeled as passes. Inherited cold-Continue stalls and startup repeats remain separate limitations in native reports. Passing measured play cadence does not erase those diagnostics.
