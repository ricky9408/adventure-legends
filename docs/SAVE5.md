# Save format 5: eight-form creature milestone

## Compatibility and limits

The only enabled forms in content revision 1 are **1, 2, 4, 5, 7, 8, 10, 11**.
Other identities remain reserved. A valid checksum does not make an unknown
form, ability, content revision, or malformed creature acceptable.

The serializer never writes below SRAM `0x0200`. All original v2/v3 bytes and
both v4 banks at `0x40`/`0x80` remain untouched. Neither v5 save bank is mirrored
back to v4. Loading this SRAM in an older ROM can therefore resume only its last
old-format checkpoint; it cannot see later v5 progress or creature changes.

Two 6,144-byte banks start at `0x0200` and `0x1A00`; the end is `0x3200`, below the
conservative 32-KiB SRAM limit. All numbers below are little endian. Runtime
struct layout, padding, pointers and derived caches are never the wire format.

## Wire layout

Offsets are relative to each bank.

| Offset | Bytes | Meaning |
|---:|---:|---|
| 0 | 2 | `45 42` magic |
| 2 | 1 | Version 5 |
| 3 | 1 | Header length 32 |
| 4 | 2 | Full bank length 6,144 |
| 6 | 2 | Used allocation 5,056 |
| 8 | 4 | Unsigned generation counter |
| 12 | 2 | Content revision 1 |
| 14 | 2 | Zero reserved flags |
| 16 | 4 | IEEE CRC32 of all 6,144 canonical bytes |
| 20 | 1 | Commit marker `A5`; zero during construction |
| 21 | 11 | Zero reserved |
| 32 | 64 | Campaign block |
| 96 | 64 | Seen 16, obtained 16, one-time rewards 16, zero reserved 16 |
| 160 | 3,840 | 160 explicit 24-byte creature records |
| 4,000 | 32 | Party indices/settings |
| 4,032 | 512 | Shared quest/bond allocation |
| 4,544 | 512 | Equipment allocation, entirely zero in revision 1 |
| 5,056 | 1,088 | Zero padding/reservation, covered by CRC |

The CRC uses polynomial `0xEDB88320`, initial state `FFFFFFFF` and final XOR
`FFFFFFFF`; `123456789` is `CBF43926`. CRC bytes 16–19 and commit byte 20 are
**treated as zero** during CRC calculation, including after the bank commits.
A 1-KiB constant CRC lookup table lives in ROM.

### Campaign block

Relative offsets: room 0, spawn 1, chapter flags 2, bridge 3, torches 4, relic 5,
camp 6, optional flags 7, 32-bit room flags 8, 16-bit story-seen flags 12,
legacy companion selection 14; bytes 15–63 are zero. Every v4 progression bit
is retained. `save5_campaign_validate` preserves the original v4 checks and
safe-resume rules. Pending story rewards and all Core-clear resumes use the
village/elder without revoking completion bits.

### Instance records

Relative offsets: form ID 0, flags 1, level 2, bond 3, XP32 at 4, instance ID32
at 8, preset nickname ID16 at 12, personal trial flags16 at 14, equipped ability
IDs at 16/17, polarity mirror 18, selected command slot 19, cosmetic seed32 at
20. Empty records are entirely zero. `creatures_instance_validate` controls
content constraints, including XP-derived level, learned commands, family trial
bits, evolved minimum level and polarity. No random combat stat is persisted.

Roster validation also enforces unique nonzero instance IDs below the next-ID
counter, ownership represented in the collection log, obtained as a subset of
seen, unique occupied party references, selected-party validity, and an exact
match between the first four story-reward ledger bits and story-locked families.
Only enabled forms may appear in seen/obtained. Other reward-ledger bits are a
bounded 128-bit authored transaction reservation.

### Party/settings block

Relative bytes 0–3 hold four roster indices, with 255 empty. Byte 4 selects a
party position, with 255 only for an empty party. Bytes 5–7 are zero. The 32-bit
next-instance ID is at 8; bytes 12–31 are zero. The counter never wraps/reuses an
existing identity; `FFFFFFFF` is the exhausted sentinel.

### Quest/bond and equipment allocations

Quest-block bytes 0–263 are explicitly zero-reserved for quest states (16),
objectives (128), reward ledger (8), variables (64), region flags (32), and safe
anchor discovery (16). They are not read as arbitrary inferred quest data.

- Bytes 264–423: 160 per-instance expedition bond counters, each 0–10; empty slots must be zero
- Bytes 424–487: shared 512-event expedition credit bitmap
- Bytes 488–503: permanent 128-event first-field-aid bitmap
- Bytes 504–511: zero reserved

The equipment allocation remains entirely zero. Its planned subdivisions stay
reserved: 384 item-instance bytes, 16 reference/settings bytes, 64 ownership
bytes, 16 wallet/key-flag bytes, and 32 reserved bytes. Enabling either extension
requires an explicit content revision and validator/migration update, using the
same v5 bank transaction. There is no independent equipment commit.

## Asynchronous transaction and engine contract

`save5_begin(state)` takes an immutable **4,944-byte runtime snapshot**. It checks
basic campaign/reservation bounds, does no SRAM access and no CRC, and does not
retain caller pointers. The caller may mutate its state immediately afterward.
A busy begin is refused without replacing the pending transaction.

Roster validation is asynchronous: begin can succeed and later report FAILED
for an invalid roster. No SRAM writes occur before the whole snapshot validates.
The in-place conversion explicitly encodes records backwards, retaining small
metadata in unused scratch space. Old-bank scans temporarily use unused padding
for an instance-ID index; that space is zeroed before CRC or writing.

Call `save5_step(budget)` once per display update. Zero does no work. The writer
caps the request at **3,072 byte/work units**, including conservative validation
charges. `1,024` is the recommended active-game budget; **3,072 is appropriate
for the engine's dedicated SAVE_PENDING mode with cached/light rendering**.
Avoid combining begin and a large step in one already-heavy update.

The phases are:

1. Encode and validate the immutable snapshot incrementally
2. Read/CRC/semantically validate both existing banks incrementally
3. Select the older/inactive bank; generation is current + 1, or 1 if none exists
4. Zero canonical padding and calculate the full snapshot CRC incrementally
5. Invalidate only the destination commit byte and verify that invalidation
6. Write the other 6,143 bytes, bounded per update
7. Read back every byte against the canonical snapshot, before committing
8. Write the single commit marker last
9. Read back all 6,144 bytes again; report DONE only when this succeeds

There are exactly **6,145 durable byte writes**: one invalidation, 6,143 content
writes, and one final commit. The prior valid bank remains untouched throughout.
A power cut before commit selects the old bank; after commit it can select the
complete new bank even if the final readback/update has not happened yet.
FAILED never means the old valid bank was erased. For first migration, the old
v4/v3/v2 checkpoint remains the fallback at every pre-commit interruption.

Report success/show the first earned reward page only after DONE when a durable
reward boundary is required. Continue the display loop during SAVE_PENDING.
The progress count is a conservative byte-work indication; invalid old banks
can short-circuit scans, so status rather than percentage determines completion.
The caller's generation/version metadata is not mutated; reload if needed.

`save5_store` is a blocking adapter for host tests or explicitly paused tools,
not the ordinary engine save path. `save5_load`, `save5_has_valid` and the full
`save5_validate` are also blocking startup/transition operations. Load/has-valid
refuse while the writer owns the shared scratch buffer.

## Migration

The newest fully valid v5 bank wins. Unsigned wrap is deterministic:
`FFFFFFFF -> 00000000` is newer; equal generations or an exactly half-range gap
choose bank A. If neither v5 bank validates, the unchanged `save4_load` decoder
is used. Migration preserves all decoded campaign fields/metadata and selected
legacy companion, adds only unlocked story families, and initializes all other
reserved content to zero. The creature module applies the authored migration
levels/bond and monotonic story-training compensation for this milestone; no
historical player XP is inferred. Loading alone never writes a converted save.
The host harness mirrors only the first 256 read bytes into save4's existing
host SRAM shim; cartridge builds read the same real SRAM directly.

## Verification and budgets

Run the exhaustive host suite:

    python3 tests/test_save5.py

It covers all 6,145 write interruptions for first migration and both bank
replacement directions; all 6,145 individual corrupted writes; every byte
corrupted in either 6-KiB bank; CRC-valid malformed headers/content/records;
unknown forms/abilities, duplicate IDs, XP disagreement, party references,
sequence wrap, exact v2/v3 payload combinations, pinned controller-produced
v2/v3/v4 fixtures, immutable snapshots, budget caps, commit visibility, full
160-instance saves and capacity-blocked idempotent story rewards. Failed loads
leave the output untouched; failed validation and migration reads write no SRAM.

Run the reproducible hardware-cycle microbenchmark after building the mGBA
bridge (or supply `--mgba-tools` with the existing bridge directory):

    python3 tests/test_save5.py --arm-timing --output build/save5-timing

It compiles the modules as ARM7TDMI Thumb with warnings as errors, matches the
engine's WAITCNT `0x4317`, and measures GBA cascaded timers. Twelve scenarios
cover 2/4 creatures, all 160 slots, mixed/evolved forms and both old-bank states.
This is an isolated SRAM subsystem test, **not a controller playthrough or proof
of the whole game's frame budget**. Integration must retain its own cadence test.

Measured on 2026-10-05:

| Operation | Maximum cycles | Fraction of 280,896-cycle frame |
|---|---:|---:|
| begin, any tested roster size | 35,649 | 12.7% |
| step requested 1,024 | 66,888 | 23.8% |
| step requested 3,072 | 187,587 | 66.8% |
| step requested 4,096, clamped to 3,072 | 187,583 | 66.8% |

With two valid banks, the tested four-creature transaction takes 18 display
updates at 3,072, and the full 160-instance transaction 35 updates. At 1,024
they take 54 and 102 updates. This is distributed work, not skipped game frames.

Module budget from the same warning-free ARM build: **7,568 bytes ROM**
(code plus constant table), **6,368 bytes EWRAM**, **0 bytes IWRAM**. The EWRAM
includes the single 6,144-byte scratch/snapshot union and 224 bytes of streaming
state; it does not include the caller's 4,944-byte live Save5State. Combined,
those are 11,312 bytes before unrelated UI/art buffers. The largest individual
compiler-reported stack frame is 104 bytes; no full bank or roster is on stack.
The unchanged legacy decoder contributes its pre-existing small allocation.

The final 16-test host suite passed, as did the unchanged 26-test save4 suite.
A separate native ASan/UBSan run completed 1,000 full-roster asynchronous
save/load cycles across budgets 1–1,000 without a memory or undefined-behavior
finding (leak detection disabled in the sandbox). The optional timing command
writes compiler stack usage, source/ROM hashes and per-step cycles to its JSON
report so later integration changes can be measured against the exact source.
