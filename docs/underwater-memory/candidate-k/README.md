# Final candidate K: memory and stack validation

## Result

K preserves the full **3,840-byte SYSTEM stack reserve**. Native diagnostic
runs on genuinely earned **34- and 50-individual** saves, including an actual
70→72 evolution at 50 and casts of all 16 retained Underwater evolved forms,
show the same **948-byte overwritten-canary extent** as earlier candidates.
The **2,892-byte lower prefix** and bottom **64-byte guard** remain unchanged.

**No memory blocker was found in the measured paths.** This is not a true
minimum-SP measurement, exhaustive stack-safety proof, physical-hardware test,
or exact production-K timing acceptance. No 160-individual native roster was
fabricated. Production sources and the 18 frozen shared helper files were not
edited.

## Exact candidate and diagnostic pairing

- K ROM: `df3733446cda3d41c2e78da134b25cd446846d6283e4ac5dc47b3fcaa3f98607`
- K symbols: `3839900cde0cbbfae5f3883bfda7e726f2f85ee92d736f60381e95cc3899a797`
- K source manifest: `458a276750c5f677123a5905d4214af585db5ad6787a07d5a5135f565eb03929`
- Frozen runtime inputs: **1,163**, read from K's archived runtime-source closure
- Separate diagnostic ROM: `a9e538a2446db905d72624e9303f57b5fc57b3f44a6333796d392a467f3bf718`

Only copied startup assembly differs. Before the first C call, it fills
`[0x03007000, 0x03007f00)` with `0xa55ac33c`, without touching game progress,
code, globals, or the SVC/IRQ/BIOS-reserved upper range. The native observer
only reads memory and provides controller inputs.

All C objects were built with release flags plus `-fstack-usage`. Relinking
those exact objects with authenticated, uninstrumented startup reproduces the
K ROM **byte for byte**. See `diagnostic-build-receipt.json`.

The canary ROM adds startup bytes and relocates ROM addresses, so its timing
remains diagnostic. No production ROM, map, source or protection setting was
changed.

## K-earned SRAM provenance

The source is K's fresh single controller producer at
`build/underwater-k-full01/underwater-journey.json`:

- Producer report SHA: `8e8c9f749f7f78aa043fd985a05c7d06c2ff6dec95effa1639f8f6520954cc6d`
- **10,940 assertions, zero failures**, actual retained roster and histories
- Final 50/89 save SHA: `41cf371618208e0097fe6ee10393e3185b4bffb2af9dad9e5f81e2663d6673a0`
- Trial15-complete 50/88 save SHA: `fc4488e9d94c61291bbcf74da8277cb3fd8acddcdd42473c54044ba69735b253`

These are authenticated against the K producer's snapshot records. The bytes
also match the prior deterministic F endpoints, but the source provenance here
is the fresh K producer, not an imported F machine state.

The observer cold-imports only SRAM into the separately hashed K diagnostic.
Save wire format 5 / content revision 6, the persisted schema, codec, catalog
and validation sources are unchanged. **No machine state crosses ROMs.** The
34-person run instead cold-imports the pinned delivered Magma revision5 SRAM
and exercises normal Continue migration. See `cold-sram-pairing.json`.

## Native observations

| Route | Hardware frames | Functional assertions | Result |
| --- | ---: | ---: | --- |
| Delivered Magma 34/65 Continue and revision5→6 migration | 202 | 4 | Passed |
| K 50/88 Continue, travel back to town, five tabs, checkpoint save, real cast, decline/reopen, actual 70→72 evolution to 50/89 | 2,768 | 202 | Passed |
| K 50/89 Continue, five tabs, checkpoint save and actual casts of all 16 retained Underwater evolved forms | 7,549 | 182 | Passed |

All three runs have zero harness failures. Each observation's lowest changed
word is `0x03007b4c`, giving a cumulative 948-byte extent below the startup SP.
There are 928 bytes' worth of changed words with untouched holes; this is not a
byte-exact count of writes. Unused allocated slots or writes equal to the canary
can remain invisible. The unchanged prefix therefore is not guaranteed free
stack, and the extent is not true minimum SP.

The all-16 cast windows each record 120 updates and 120 page flips in 120
frames, maximum **213,965 cycles**. The measured evolution waits also meet the
original cadence predicate on this diagnostic. Timing is recorded without
using it as a stack-test gate; these results **do not replace production-K
cadence acceptance**.

Exact source-report hashes, counts and observations are in `run-ledger.json`
and `native*-observations.json`. Full diagnostic timing traces are retained.
`observe_stack_used.py` is the exact observer source used (archival copy; run
the maintained driver in the parent directory).

## Actual memory accounting

- ROM: **9,777,176 / 33,554,432 bytes**, remaining **23,777,256 bytes**
- EWRAM `.data`: **96 bytes**; `.bss`: **49,760 bytes**
- EWRAM total: **49,856 / 262,144 bytes**, remaining **212,288 bytes**
- IWRAM code: **28,432 bytes**, ending at `0x03006f10`
- Gap before the protected stack floor at `0x03007000`: **240 bytes**
- SYSTEM stack reserve: **3,840 bytes**, ending at startup SP `0x03007f00`
- GCC records: **919**, all qualified `static`, none dynamically sized
- Largest individual C frame: **832 bytes**, `obj_init`
- Largest individual Underwater-power frame: **104 bytes**

Individual GCC frames exclude callees and do not constitute an exhaustive
call-graph bound. Assembly/library paths and unexercised conditions still matter.
Keep the stack reserve; the 240-byte code gap is not a reason to consume it.

The 160-slot roster is fixed capacity. Important transaction/evolution frames
remain fixed, with persistent state in EWRAM instead of full-save stack copies:
`adventure_save` 4,944 bytes, shared save scratch 6,144, scan state 1,092,
admission job 160, Underwater job 104, evolution job 72 and preflight 24.
Additional occupied slots increase iteration/validation work, not these frame
sizes. This does not claim native full-160 timing or full path coverage.

Startup sets `0xd3` before SP `0x03007fa0`, which is Supervisor/SVC, not IRQ;
then sets `0xdf` for SYSTEM. The probe does not measure interrupt-stack use.

## Enforced build limits

Three independent diagnostic links exercised the unchanged linker:

- Additional 512 bytes of IWRAM fail the explicit reserved-stack assertion
- Additional 256 KiB of BSS fail the EWRAM region limit
- Additional 32 MiB of ROM fail the ROM region limit

All three expected failures are recorded in `link-limit-probes.json` and the
corresponding logs. The actual candidate also passes the ROM/EWRAM/IWRAM bounds
in `memory-budget.json`. Production artifacts remain untouched.

## Explicit chapter-growth budget exception

The accepted Magma ROM is 7,495,920 bytes. K's chapter growth is **2,281,256 bytes**.

- Original **2 MiB** target: **failed by 184,104 bytes**
- Explicit proposed **2.5 MiB** ceiling: **340,184 bytes remain**
- Hardware **32 MiB** ROM limit: **23,777,256 bytes remain**

The adjusted proposal accounts for four 480×320 maps, four small rooms, 196,632
bytes of creature art, power art/geometry, Japanese UI masks and chapter logic.
It is an explicit budget change proposal, never a silent pass of the original
2 MiB target.

## Freeze verification and reproduction

`helper-freeze-before.json` and `helper-freeze-after.json` are byte-identical.
Both verify that all 18 live helper files match their frozen shared copies and
pinned hashes. The runtime closure and candidate hashes were checked again at
completion. All generated files live in separate diagnostic/evidence folders.

```
python3 docs/underwater-memory/build_diagnostic.py \
  --candidate build/underwater-candidate-k \
  --runtime-root build/underwater-candidate-k/runtime-source \
  --output build/new-memory-diagnostic-k
python3 docs/underwater-memory/observe_stack.py \
  --diagnostic-build build/new-memory-diagnostic-k/build \
  --source-rom-sha df3733446cda3d41c2e78da134b25cd446846d6283e4ac5dc47b3fcaa3f98607 \
  --source-report build/underwater-k-full01/underwater-journey.json \
  --snapshot trial-15-complete --scope evolve-earned \
  --evolve-source 70 --evolve-target 72 --output build/new-stack50-k
```

For all 16 retained-form casts, use `--snapshot 11-all89-earned-town --scope
all-powers`. Use `--scope boot` without a source report for delivered Magma
migration. A changed production ROM requires another paired repeat.

## Published cadence trace format

The all-16 cadence trace is published as `native50-all16-cadence-traces.json.gz`.
Its adjacent compression receipt records exact raw and compressed hashes. The
uncompressed build original remains unchanged. See the parent README for
reading and verification commands. Include this directory’s `stack-usage.tsv`
in the source package.
