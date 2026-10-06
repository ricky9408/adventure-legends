# Candidate G: paired memory and stack validation

## Result

The G-source canary diagnostic preserves the complete **3,840-byte SYSTEM stack
reserve**. Actual controller routes with **34** and **50** retained individuals,
including real evolution at 50 and all 16 retained Underwater evolved-form casts,
again show a **948-byte overwritten canary extent** and **2,892-byte unchanged
prefix**, with the bottom 64-byte guard intact in every sample.

No new memory blocker was found in the measured paths. **This is not a true
minimum-SP measurement, exhaustive stack safety, physical-hardware testing or
production-G timing acceptance.** There is no fabricated 160-individual native
fixture. The shared analysis of fixed-capacity storage and fixed GCC frames
remains applicable; actual full 160 timing/stack paths are not claimed.

## Exact pairing: F SRAM → G-source diagnostic

- G ROM: `8c216b7e36a241a713f2aae87d1c1e33cd7ff221c9279c305c150d9386f8ad9b`
- G symbols: `1cbe12124a1f1b2abb8ad350e53d25cc9cf811dc25b2bb6e15eb6e3b9d185597`
- G source manifest: `77d212ef0747a95e455521284eb7d176ffd3d3ae2733ab191f93025f499fc288`
- Source closure: `build/underwater-candidate-g/runtime-source`, **1,163 inputs**
- F SRAM producer ROM: `78ba51a7dd8160af681fb68e52e573f6de4140a70ea320d344d10d8fdd4d13c8`
- F producer report: `a0e9796a9023944582db44c89844b39b2fa91275c7adc0ac09b7db99a212568f`
- F single producer: **10,939 assertions, zero failures**
- F final 50/89 SRAM: `41cf371618208e0097fe6ee10393e3185b4bffb2af9dad9e5f81e2663d6673a0`
- F trial15-complete 50/88 SRAM: `fc4488e9d94c61291bbcf74da8277cb3fd8acddcdd42473c54044ba69735b253`

The diagnostic source changes **startup only**. Relinking its `-fstack-usage` C
objects with uninstrumented startup reproduces the G ROM **byte for byte**.
The canary ROM is a separate cartridge with relocated addresses, recorded in
`diagnostic-build-receipt.json`.

F→G changes only `game.c`, `underwater_game.c` and `underwater_powers.c`.
The observer verified **19 identical persisted schema, codec, catalog and
validation source files** between the producer and consumer manifests. Format 5 /
content-revision6 SRAM is cold-imported, then ordinary Continue runs on G's C
code. **No machine state crosses ROMs. No game progress is injected into RAM.**
This is intentionally distinct from a same-G-ROM acquisition run.

See `f-to-g-cold-sram-pairing.json` for the complete pairing and source checks.

## Observed controller routes

| Route | Hardware frames | Functional assertions | Outcome |
| --- | ---: | ---: | --- |
| Delivered Magma 34/65 cold Continue + revision5→6 migration | 202 | 4 | Passed |
| F final 50/89 cold Continue, five tabs, checkpoint save, form50 cast | 1,486 | 54 | Passed |
| F 50/88 cold Continue, travel 52→53→46, tabs/save/cast, decline/reopen, actual 70→72 evolution to 50/89 | 2,768 | 202 | Passed |
| F 50/89 cold Continue, tabs/save, actual casts of all 16 retained Underwater evolved forms | 7,549 | 182 | Passed |

Every route's deepest changed word is `0x03007b4c`. The 948-byte extent is a
cumulative overwritten-word measurement since startup. Untouched allocated
slots and writes equal to the canary can be invisible, so the unchanged prefix
is not a guaranteed minimum amount of free stack.

The all 16 cast windows each recorded 120 updates and 120 flips in 120 frames,
maximum 221,872 cycles. Evolution's measured preparation/commit waits also meet
the original timing predicate on this diagnostic. The predicate is recorded,
not used to gate the stack route. **Relocated diagnostic timing is not a
substitute for exact production-G timing acceptance.**

`run-ledger.json` and the `native*-observations.json` files retain exact report
hashes and measured values. The `*cadence-traces.json` / `*evolution-traces.json`
files retain the timing observations. Exact observer versions are archived as
`observe_stack_first_used.py` and `observe_stack_all16_used.py` (archival copies;
run the maintained driver in the parent directory).

## G memory accounting and hard-limit tests

- ROM: **9,777,000 / 33,554,432 bytes**
- EWRAM `.data`+`.bss`: **49,856 / 262,144 bytes**
- IWRAM code: **28,344 bytes**, ending at `0x03006eb8`
- Gap to the protected stack floor: **328 bytes**
- SYSTEM stack reserve: **3,840 bytes**, unchanged
- GCC stack records: **914**, all static, none dynamically sized
- Largest individual C frame: **832 bytes**, `obj_init`

The unchanged linker was exercised using separate +512-byte IWRAM,
+256 KiB EWRAM and +32 MiB ROM probes. All three links failed with the intended
stack-boundary/region diagnostics. See `link-limit-probes.json` and logs.

These checks support retaining the reserve and continuing to place appropriate
chapter code in ROM. They do not authorize using the reserve as extra code space.

## Explicit growth-budget exception

Compared with the accepted 7,495,920-byte Magma ROM, G adds **2,281,080 bytes**.

- Original 2 MiB target: **failed by 183,928 bytes**
- Explicit proposed 2.5 MiB ceiling: **340,360 bytes remain**
- Physical32 MiB cartridge limit: **23,777,432 bytes remain**

The proposal accounts for four large 480×320 maps, four small rooms, creature art,
power art/geometry, Japanese UI masks and chapter logic. It does not silently
turn the failed original budget into a pass. `memory-budget.json` records both.

## Reproduction

```
python3 docs/underwater-memory/build_diagnostic.py \
  --candidate build/underwater-candidate-g \
  --runtime-root build/underwater-candidate-g/runtime-source \
  --output build/new-memory-diagnostic-g
python3 docs/underwater-memory/observe_stack.py \
  --diagnostic-build build/new-memory-diagnostic-g/build \
  --source-rom-sha 8c216b7e36a241a713f2aae87d1c1e33cd7ff221c9279c305c150d9386f8ad9b \
  --sram-producer-rom-sha 78ba51a7dd8160af681fb68e52e573f6de4140a70ea320d344d10d8fdd4d13c8 \
  --source-report build/underwater-f-full01/underwater-journey.json \
  --snapshot trial-15-complete --scope evolve-earned \
  --evolve-source 70 --evolve-target 72 --output build/new-stack50-g
```

Use `--snapshot 11-all89-earned-town --scope all-powers` for the 16-form repeat.
A different release ROM requires a new paired build; these results are pinned
to G and must not be silently transferred to later runtime changes.

## Published cadence trace format

The all-16 cadence trace is published as `native50-all16-cadence-traces.json.gz`.
Its adjacent compression receipt records exact raw and compressed hashes. The
uncompressed build original remains unchanged. See the parent README for
reading and verification commands. Include this directory’s `stack-usage.tsv`
in the source package.
