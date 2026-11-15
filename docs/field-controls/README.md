# Field controls and native frame pacing

B uses the selected companion's power and automatically calls a recalled companion. R calls or recalls without casting. Overlapping R and B requires a physical B release before another cast. Menus retain their own B cancellation and A confirmation.

A short neutral L press retains the existing next-occupied-party-slot switch, including its party order and empty-slot skipping. The original release rule is preserved: up to 12 held updates qualifies; a direction observed while L is held disqualifies the tap. B or Start cancellation takes priority over release. Holding L for 13 updates displays the all-owned carousel. Left/Right browses individual records, including reserves and identical forms; releasing L commits. A long hold does not also perform the short switch.

The hold interval prepares at most 13 physical roster records per update with the complete existing validator. The list remains hidden until all 160 positions have been checked. Input ownership pauses play immediately; a separate visibility flag controls panel drawing, opaque bitmap masks, actor occlusion and reward display. Existing reward and Horizons performance pause logic continues to use ownership. No validation cache, save decoder change or save schema change is introduced.

The native loop uses BIOS VBlankIntrWait with VBlank and Timer1 interrupts enabled. Approved PCM, cue routing and PSG arrangements are unchanged. Pixel-identical box, hint, save-badge and notice-strip optimizations reduce rendering work while preserving complete backing buffers and world/viewport guards.

## Verification

Run both current acceptance suites from fresh output directories:

```sh
python3 tools/run_gameplay_ci.py --suite host --output build/ci-host
python3 tools/run_gameplay_ci.py --suite native --output build/ci-native
```

| Requirement | Evidence and limits |
| --- | --- |
| Original short L switch | Actual-C strict/sanitizer tests cover the 12/13 boundary, party permutations and holes, release priority, cancellation, handoff and double-switch prevention. |
| All-owned long L selection | Actual-C tests cover 160 individual commits, duplicates and legendary replacement. Native capacity tests use six fresh cores with historical 72 and prepared 160-companion saves, including widely spaced IDs, immediate Continue and background saving. These fixtures do not prove acquisition. |
| B power and R presence | Actual input-boundary, context-cancellation and real power-module tests; controller-earned reserve and campaign routes. |
| Frame pacing and audio | Native routes require one update and presentation per active frame, the GBA cycle limit and zero core faults. The audio gate checks approved PCM across a loop seam, IRQ coexistence, reset and Continue. Physical Miyoo/RetroArch performance remains unverified. |
| Historical proofs | The additive contract restores every byte and mode of the exact 4005 parent tree before invoking unchanged inherited verifiers. Current runtime and helper inventories are authenticated separately. |

For a clean build with a chosen compiler, use the Makefile's `ARM_PREFIX` setting:

```sh
make clean
make ARM_PREFIX=/path/to/toolchain/bin/arm-none-eabi-
```

Two clean builds must reproduce the candidate. A source manifest alone does not prove that incremental object files came from the intended compiler. Hosted artifacts are built and verified independently; linker versions can produce different ROM hashes from identical source.

Fresh campaign routes, historical/synthetic fixtures, host oracles and visual inspection are distinct evidence. None establishes complete fresh acquisition of all 128 forms, every optional quest, subjective enjoyment or physical-device behavior.

## Reviewing a redesign boundary

The Lantern Trails redesign adds an exact path list at
`docs/redesign/production-scope.json`. The verifier pins its SHA-256 and the
current field contract binds the same identity. This extends the reviewed
production set without exempting an art directory or changing any inherited
proof. Current bytes and helper inventories still require exact hashes.

Finish deterministic asset generation and review all source/test changes before
authoring the boundary. First list the additional paths without changing it:

```sh
python3 -B tools/author_redesign_field_scope.py --list-candidates \
  > build/redesign-field-paths-review.json
```

Review that explicit list against the generator and runtime changes. Authoring
accepts only the complete sorted list of additional changed paths; wildcards,
extra paths, protected inputs and omitted changes are rejected. Then pin that
reviewed scope and inspect the prospective current contract/inverse hashes:

```sh
python3 -B tools/author_redesign_field_scope.py \
  --reviewed-paths build/redesign-field-paths-review.json
python3 -B tests/author_field_controls.py --repo . --check
```

After review, run `tests/author_field_controls.py --repo .` without `--check`
to freeze current production and helpers. It reads the original Git blobs,
checks the exact 4005 tree identity and modes, and adds only the original bytes
needed to reconstruct that parent from the changed checkout. Existing proof
contracts and archives remain byte-identical. Run the boundary negative tests
and the normal host/native suites after freezing. A later helper or production
edit invalidates the freeze and requires review again.

The authoring tools establish reviewed identities. They do not establish good
art, gameplay quality, successful regeneration or passing tests.
