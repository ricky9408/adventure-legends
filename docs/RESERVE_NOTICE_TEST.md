# Reserve recruit discovery regression

`tests/fresh_reserve_notice.py` starts a new StrictNative cartridge with blank
SRAM, beats Grove, walks through Grove's east road to Reedhaven, earns Water by
the real handle/Nature/reeds/Wind/report sequence, and then beats Sky. Fire,
Nature, Wind and Water fill the four active slots before Sky recruits Stone.
Stone must therefore remain in reserve.

The test browses that actual Stone in Party with Down, checks the exact native
NEW bitmap at the candidate row, and presses A once to inspect it. It compares
the complete before/after Save5 bytes against an expected state with only Stone's
acknowledgement bit added. Party assignments, selected companion, every instance,
position, HP and remaining cooldowns must stay unchanged. Closing the menu drains
the ordinary save; a fresh emulator then continues only this run's own SRAM.
The acknowledgement, full roster and reserve status must persist. Native
screenshots prove the tag appears before inspection and stays absent afterward.

The early regional adapter borrows the exact live original controller session,
logs and metrics. It initializes navigation geometry only and never invokes the
regional helper's finished-ending constructor. The historical Sky helper's
optional post-reward Stone selection is explicitly skipped because Stone is in
reserve. No party assignment or game state mutation replaces that selection.

This is a targeted fresh route through Grove and Sky, not a Core/ending or full
collection acceptance run. The report deliberately retains `route_complete`
false for the original full campaign. `summary.json` records acceptance only for
the named reserve scenario, blank-SRAM provenance, runtime/helper hashes, checks
and measured native frame behavior. ROM, symbols, ELF, source receipt and helper
source are copied into the new output directory. All receipt inputs must match
the selected checkout; later harness-only commits are allowed only when their
changed files do not intersect the runtime build receipt.

Example with a native mGBA bridge built for the local host:

```sh
python tests/fresh_reserve_notice.py \
  --source-root /absolute/path/to/pinned-checkout \
  --output /absolute/path/to/new-evidence-directory \
  --bridge /absolute/path/to/native-bridge.so \
  --expected-commit FULL_RUNTIME_COMMIT_HASH
```

`tests/test_recruit_reserve_notice.py` is the complementary host regression. Its
full-party fixture is prepared using public creature grants and is explicitly
synthetic. It builds the real menu, bitmap renderer, acknowledgement and codec;
checks browsing/B cancellation, first-A acknowledgement-only behavior, repeated
inspection, a Save5 round trip and the immutable preflight lease. Portraits are
host stand-ins. Strict warnings and AddressSanitizer/UndefinedBehaviorSanitizer
both run. The native screenshots carry the visual and controller-earned proof.

```sh
python tests/test_recruit_reserve_notice.py \
  --source-root /absolute/path/to/pinned-checkout \
  --capture-dir /absolute/path/to/host-raster-directory
```

Both scripts leave production files and personal saves untouched.
