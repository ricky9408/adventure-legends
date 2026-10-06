# Candidate B: real 50-individual stack observation

## Result

A separately paired B canary ROM cold-imported an authenticated, actually earned
50-individual / 88-history SRAM snapshot and completed a controller-confirmed
70→72 evolution, ending at 50 individuals / 89 histories. Across **2,758 hardware
frames**, all stack samples retained the same **948-byte overwritten extent**,
lowest changed word `0x03007b4c`, **2,892-byte unchanged prefix**, and intact bottom
64-byte guard.

This is an overwritten-canary observation, **not true minimum SP, exhaustive
stack safety, physical-hardware testing, or final release evidence**. Candidate B
has known cadence blockers. The acquisition chain is diagnostic and retains its
earlier failing navigation/usability branches. A later release candidate needs
its own repeat.

## Exact pairing and input

- B ROM SHA-256: `e02c410824086957a9ee472185a384360e3f6c144b1693b875c05873d6603923`
- B source closure: `build/underwater-render-b/runtime-source`
- Build receipt: `diagnostic-build-receipt.json`
- Input: `trial-15-complete` from `build/underwater-b-debug03/underwater-journey.json`
- Source report SHA: `765b3da7fafdcb373a705a55e646de9de38d8a17ae5799d1af98b6e2ec29604f`
- Both input snapshot hashes and the verified Bfull01 → debug02 → debug03 chain:
  `acquisition-chain.json`

The build independently authenticated all 1,161 runtime inputs. Its canary changes
startup only; a control using original startup and the same `-fstack-usage` C
objects reproduces B byte-for-byte. The canary ROM therefore has a distinct hash
and relocated addresses. The persisted Save5 schema remains unchanged.

The producer chain uses **same-ROM** state resumptions. This observer imports
only the resulting SRAM into the separate canary ROM and cold boots it. **No
machine state crosses ROMs and no game progress is written into RAM.**

## What ran

- Cold Continue from the actual 50-person / 88-history save in room52
- Ordinary controller travel to town, rendering rooms52/53/46
- All five journal tabs
- Checkpoint save/transaction
- Real form50 cast
- Evolution preparation, decline, reopen and target choice
- Bounded preparation/commit of the already-earned form70→72 route
- Same-individual identity preserved, actual animation/autosave, then 50/89

The successful run has 202 functional assertions and zero harness failures.
See `run-ledger.json` for the exact count and hashes; the ledger also retains the
first cadence-gated run and the separate observer navigation mistake, rather
than erasing them. `observe_stack_used.py` is the exact successful observer.

`native50-cadence-traces.json` and `native50-evolution-traces.json` record timing
predicates without using them as a stack-test gate. Failing timing predicates
remain failures in the recorded fields. The real-cast window records 119 updates
and 119 flips in 120 frames, max 288,737 cycles, so its original timing
predicate is false. The measured evolution waits satisfy that predicate on
this diagnostic only. This deliberately narrowed gate does
not count as a production timing pass.

## Static memory and build boundaries

- ROM: **9,770,620 bytes**
- EWRAM data+BSS: **49,696 bytes**, unchanged from A
- IWRAM code: **28,416 bytes**, ending at `0x03006f00`
- IWRAM gap before reserved stack: **256 bytes**, down from A's 368
- SYSTEM stack reserve remains **3,840 bytes**
- **896 GCC stack records**, all static; largest individual frame remains
  `obj_init` at **832 bytes**

The three isolated overflow links were repeated on B and all failed as intended:
IWRAM stack-boundary assertion, EWRAM region limit and ROM region limit. See
`link-limit-probes.json` and the corresponding logs.

Chapter growth over Magma is **2,274,700 bytes**, exceeding the original 2 MiB
proposal by **177,548 bytes**. The explicit proposed **2.5 MiB** ceiling leaves
**346,740 bytes**. This is not a retroactive pass of the original target.

## Reproduction

```
python3 docs/underwater-memory/build_diagnostic.py \
  --candidate build/underwater-render-b \
  --runtime-root build/underwater-render-b/runtime-source \
  --output build/new-memory-diagnostic-b
python3 docs/underwater-memory/observe_stack.py \
  --diagnostic-build build/new-memory-diagnostic-b/build \
  --source-rom-sha e02c410824086957a9ee472185a384360e3f6c144b1693b875c05873d6603923 \
  --source-report build/underwater-b-debug03/underwater-journey.json \
  --snapshot trial-15-complete --scope evolve-earned \
  --evolve-source 70 --evolve-target 72 --output build/new-stack50-b
```

## Additional all16-form coverage

A separate cold-booted 50/89 run controller-selected and actually cast every one
of the 16 retained Underwater evolved forms (50/51, 53/54, …, 71/72) in town.
It covered 6772 hardware frames and 175 functional assertions, with no
harness failures. Every observation still had a 948-byte overwritten extent
and the intact 2,892-byte prefix. The forms were already genuinely earned; no
base forms or 160-slot state were fabricated. This broadens native stack-path
coverage but does not claim every geometry/target arrangement was exercised.

See `native50-all16-observations.json` and `native50-all16-cadence-traces.json`.
Known B timing failures remain recorded. The controller driver is
`../observe_power_stack.py`; the run hash is in `run-ledger.json`.

## Published cadence trace format

The all-16 cadence trace is published as `native50-all16-cadence-traces.json.gz`.
Its adjacent compression receipt records exact raw and compressed hashes. The
uncompressed build original remains unchanged. See the parent README for
reading and verification commands. Include this directory’s `stack-usage.tsv`
in the source package.
