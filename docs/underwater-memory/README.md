# Underwater memory and stack evidence

**Latest paired validation: [final candidate K](candidate-k/README.md).** K repeats
34-person migration, actual evolution at 50, and all 16 retained Underwater form
casts using K-earned SRAM. Its observed overwrite extent remains 948 bytes.
The sections below retain A as historical evidence; B and G have separate addenda.

## Result and scope

The frozen candidate A fits the GBA ROM/EWRAM limits and keeps its full 3,840-byte
SYSTEM stack reserve. The isolated native diagnostic observed a 948-byte
canary-overwrite extent on authenticated 34- and 42-individual rosters, including
an actually earned Underwater trial and evolution. The lower 2,892-byte prefix
remained unchanged. **This is neither a true minimum-SP measurement nor an
exhaustive/hardware stack-safety proof.**

The original 2 MiB chapter-growth target was **exceeded**. An explicit proposed
2.5 MiB adjustment accommodates the authored maps/art/localization while staying
far below the cartridge's 32 MiB limit. The original target is not retroactively
reported as passed.

The main sections below cover candidate A; the linked addendum covers B. Candidate A has independently observed
frame-cadence blockers; passing memory checks does not clear those blockers.
Any changed release candidate needs a separately paired final-source repeat.
A separate candidate-B 50-individual observation is now complete; see
[`candidate-b/README.md`](candidate-b/README.md). It includes an actual
70→72 evolution at 50 retained individuals. A and B evidence remain separately
paired. No native 160-individual roster was fabricated.

## Exact candidate accounting

- ROM SHA-256: `0d7fd78733405a6fc8ec6eeca68ad207dfb11b91dcfe44a8d67f312552b46675`
- Source manifest SHA-256: `f75b5b9924bda3e9118e64f80f12f5905d1d72cef166980c3d8a94d407484580`
- ROM: **9,770,108 bytes**, with 23,784,324 bytes left below 32 MiB
- EWRAM `.data`: 96 bytes; `.bss`: 49,600 bytes; total **49,696 / 262,144 bytes**
- IWRAM code: **28,304 bytes**, ending at `0x03006e90`
- Gap to reserved stack floor: **368 bytes**
- SYSTEM stack interval: `[0x03007000, 0x03007f00)`, **3,840 bytes**
- The remaining upper 256 bytes are outside this probe

Startup's `CPSR=0xd3; SP=0x03007fa0` configures **Supervisor/SVC**, not IRQ.
`CPSR=0xdf; SP=0x03007f00` configures SYSTEM. The canary never writes the
SVC/IRQ/BIOS-reserved upper range. The game sets IME to zero in `main` and uses
polled VBlank. This diagnostic does not measure interrupt-stack usage.

Keep the stack reserve. The small IWRAM code gap is a reason to keep new chapter
code in ROM, not a reason to shrink the reserve.

## Explicit ROM-growth budget change proposal

Accepted Magma ROM: 7,495,920 bytes. Candidate-A growth: **2,274,188 bytes**
(2.274 MB decimal, approximately 2.169 MiB).

- Original target: 2,097,152 bytes (2 MiB)
- Original-target overrun: **177,036 bytes**
- Proposed adjusted ceiling: 2,621,440 bytes (2.5 MiB)
- Remaining space under that proposed ceiling: **347,252 bytes**

The chapter contains four 480×320 maps and four 240×160 rooms, authored room
geometry/collision/actors, 196,632 bytes of creature art, power art, Japanese
15-pixel UI masks, and game/transaction logic. The linked Underwater room-art
object alone contributes 1,393,228 bytes of `.rodata`; creature art contributes
196,632 and power art 9,216. These are contributions, not a complete isolated
chapter-delta decomposition: common UI/catalog/logic changes also contribute.
The proposal preserves this authored content instead of silently reducing maps.

`memory-budget.json` records both the failed original target and the proposed
ceiling comparison. Treat approval of an adjusted product budget separately
from the technical 32 MiB cartridge limit.

## Reproducible static evidence

All 1,161 runtime inputs matched candidate A's frozen manifest before a separate
source snapshot was created at `build/underwater-memory-diagnostic/`.
All C translation units were compiled with the release flags plus
`-fstack-usage`. Only the copied startup assembly was instrumented.

A control link substituted the authenticated original startup into the same
`-fstack-usage` C objects. Its GBA ROM reproduced candidate A **byte for byte**.
See `control-rebuild.json`. Thus the flag did not silently change candidate-A
C code. The canary ROM adds 32 startup bytes; its addresses and timing are a
separate pairing, recorded in `diagnostic-pairing.json`.

`stack-usage.tsv` contains **895 GCC records**, all qualified `static`; no
record reports dynamic stack allocation. Largest individual frames:

| Function | Bytes |
| --- | ---: |
| `obj_init` | 832 |
| `magma_quest_claim` | 576 |
| `underwater_quest_claim` | 568 |
| `southern_quest_claim` | 568 |
| `equipment_claim_many` | 544 |
| `draw_floating_hud` | 360 |
| `admission_query_validated` | 232 |
| `render` | 208 |
| `creatures_collection_coverage` | 152 |
| `save5_validate_revision` | 128 |

These are individual frame sizes, not sums of callees or a call-graph proof.
Assembly/libgcc paths, indirect calls and unexercised branches still matter.

## Why growing to the 160-slot capacity does not allocate a larger stack frame

The roster has a compile-time 160-record capacity. Iteration count and validation
work can grow, but these relevant GCC frames are fixed:

- `creatures_roster_validate_revision`: 48 bytes
- `creatures_admission_job_step`: 56 bytes
- `creatures_admission_job_commit_evolution`: 72 bytes
- `save5_preflight_step`: 72 bytes
- `underwater_job_begin` / `underwater_job_step`: 56 bytes each
- `evolution_prepare_step`: 32 bytes

The candidate ELF confirms persistent EWRAM storage, rather than per-call full
roster/save copies: `adventure_save` 4,944 bytes, shared save scratch 6,144,
`scan` 1,092, admission job 160, Underwater job 104, evolution job 72, and
preflight 24. The preflight shares the save writer's scratch. Gear staging reuses
`scan.equipment`; the Underwater job stores one 24-byte individual. Evolution
owns the existing save/admission jobs rather than adding another full save.

Preflight examines at most eight roster records per call; admission steps have
an explicit capped record count; Underwater passes four. The evolution wrapper
has its own bounded slice count. Fixed stack frames do **not** establish that a
full 160-slot validation meets a frame budget: duplicate-ID checks and content
checks still take time. Native 160-slot performance and stack-path coverage are
not claimed here.

## Native canary method and observations

Diagnostic startup fills only `[0x03007000,0x03007f00)` with word `0xa55ac33c`,
before the first C call and without allocating a stack frame itself. It does
not touch live game state, code, globals or the upper reserved memory. The
observer only reads memory. Controller input earns any new progress.

Save wire format 5 is unchanged, with 6,144-byte banks at SRAM `0x200` and
`0x1a00`, content revisions 5/6, in a 32 KiB SRAM image. The delivered Magma
revision5 fixture goes through ordinary Continue migration. Candidate-A
revision6 SRAM can cold-import into the diagnostic because its persisted schema
and all C code are unchanged. **No cross-ROM machine state is loaded.**

1. `native34-observations.json`: exact delivered Magma save SHA
   `a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858`;
   ordinary Continue, migration, 34 retained individuals and 65 histories
2. `native42-observations.json`: actual candidate-A town SRAM from the full03
   producer, authenticated by its snapshot SHA and source ROM; 42 individuals
   and 73 histories at cold boot; five journal tabs, checkpoint save, real field
   cast, travel/rendering, actual trial0 proof, preparation decline/reopen,
   confirmation, and same-individual Inkbud evolution to form50 / 74 histories

The second run covers 4,084 hardware frames. Every sample has the same lowest
changed word at `0x03007b4c`, giving **948 bytes of observed overwrite extent**.
There are 928 bytes' worth of changed words, with untouched holes; that number
is not a byte-exact count of writes. The bottom 64-byte guard and 2,892-byte
prefix remain unchanged. All observations are cumulative since startup.

Unused allocated slots can keep their canary; a write equal to the canary can
be invisible. The overwrite extent therefore is not true minimum SP and must
not be labeled a proven maximum stack use or guaranteed remaining headroom.

`native42-evolution-traces.json` retains actual diagnostic frame traces without
applying the release timing gate. Functional preparation/commit/state/identity
checks still apply. Neither this modified gate nor diagnostic timing can clear
candidate A's production cadence failures.

## Link-limit enforcement was exercised, not merely inspected

`probe_link_limits.py` adds synthetic section sizes to **separate diagnostic
links**, without changing the linker script or candidate artifacts:

- +512 bytes IWRAM: fails with `IWRAM code overlaps reserved stack space`
- +262,144 bytes BSS: fails the EWRAM region limit
- +33,554,432 bytes ROM: fails the ROM region limit

All three expected failures are archived in `*-overflow-link.log` and
`link-limit-probes.json`. `verify_budget.py` also asserts the actual candidate
limits, and keeps the original chapter target failure explicit.

## Files and reproduction

The docs retain compact pairing, GCC stack and native-observation evidence.
The exact diagnostic source/ELF/map/ROM and full controller report artifacts
remain in the separate `build/underwater-memory-*` directories; they are not
production ROMs. The initial 34-person observer is archived as
`observe_stack_initial.py`; the exact 42-person observer is archived as
`observe_stack_candidate_a.py`. The current observer additionally accepts a
new diagnostic build and verifies its build receipt before importing SRAM.

`build_diagnostic.py` makes a new isolated source snapshot, verifies every
selected candidate manifest input, creates the startup-only canary, and checks
an uninstrumented control reproduces the candidate exactly. It refuses to reuse
an existing output directory. `diagnostic-tool-selftest.json` records a full
successful self-test against a separate authenticated candidate-A source copy.
For a later frozen candidate (whose runtime inputs still match the checkout):

```
python3 docs/underwater-memory/build_diagnostic.py \
  --candidate build/NEW-CANDIDATE --output build/NEW-MEMORY-DIAGNOSTIC
```

Pass its `build` subdirectory via `--diagnostic-build` and the exact candidate
hash via `--source-rom-sha` when observing a later candidate's earned SRAM. The
build receipt must match both; cross-candidate timing evidence remains separate.

Given the authenticated candidate-A diagnostic build and producer report:

```
python3 docs/underwater-memory/verify_budget.py
python3 docs/underwater-memory/probe_link_limits.py
python3 docs/underwater-memory/observe_stack.py --scope boot --output build/new-stack34
python3 docs/underwater-memory/observe_stack.py \
  --source-report build/underwater-a-full03/underwater-journey.json \
  --snapshot 10-all-eight-families-and-stories --scope evolve-first \
  --output build/new-stack42
```

Do not load a candidate-A machine state into the diagnostic or any later ROM.
Do not transfer these measurements to changed release sources without a repeat.

## Source-package compression and required TSV evidence

The large all-16-form cadence traces for candidates B, G and K are shipped as
`native50-all16-cadence-traces.json.gz` within each candidate's directory.
Each gzip uses compression level9, **mtime=0 and no embedded filename**. It
preserves the **exact original JSON bytes**; nothing is minified or reformatted.

The adjacent `native50-all16-cadence-traces.compression.json` receipt records
both compressed and uncompressed SHA-256 hashes and byte lengths. The raw
originals remain unchanged in their `build/underwater-memory-*` evidence folders.
Only the three redundant uncompressed docs JSON paths listed in
`packaging-notes.json` are omitted from the source publication. The shipped
checksum list verifies the `.json.gz` files and receipts; raw hashes remain
explicitly documented in those receipts.

All four compiler stack reports must be included in the published source:

- `docs/underwater-memory/stack-usage.tsv` (candidate A)
- `docs/underwater-memory/candidate-b/stack-usage.tsv`
- `docs/underwater-memory/candidate-g/stack-usage.tsv`
- `docs/underwater-memory/candidate-k/stack-usage.tsv`

Verify the complete shipped evidence, even when raw docs traces are omitted:

```
python3 docs/underwater-memory/verify_shipped_evidence.py
```

Read the original K JSON without creating a file:

```
python3 -c "import gzip; print(gzip.open('docs/underwater-memory/candidate-k/native50-all16-cadence-traces.json.gz','rt').read())"
```

To materialize the exact original JSON in an extracted source package:

```
python3 -m gzip -d docs/underwater-memory/candidate-k/native50-all16-cadence-traces.json.gz
```

Do not substitute pretty-printed or minified JSON when checking the recorded
uncompressed hash. Repeat the same commands for B or G by changing the directory.
