# Save format 5, content revision 5

## Compatibility and wire contract

New saves declare content revision **5**. Wire version, offsets and record sizes are
unchanged: two 6,144-byte banks at SRAM `0x0200` / `0x1A00`, 5,056 allocated bytes,
160 explicit 24-byte individuals and 48 noncompacting 8-byte item records. The writer
commits the inactive bank last. All legacy bytes below `0x0200` remain untouched.

| Bank offset | Bytes | Meaning |
|---:|---:|---|
| 0 | 32 | Magic, wire version, bank/used size, generation, content revision, CRC, commit |
| 32 | 64 | Campaign and safe checkpoint |
| 96 | 64 | Seen, obtained, creature reward history, reserve |
| 160 | 3,840 | 160 explicit creature instances |
| 4,000 | 32 | Four party references, selected slot, next identity, reserve |
| 4,032 | 512 | Typed quests 264, expedition/event credits 240, reserve 8 |
| 4,544 | 512 | Typed equipment |
| 5,056 | 1,088 | Zero padding included in CRC |

Multibyte values are little endian. CRC32 uses polynomial `EDB88320` with initial/final
XOR `FFFFFFFF`; bank bytes 16–20 are treated as zero during CRC. Commit marker is `A5`.
Struct padding, pointers and derived combat statistics are never serialized.

The complete original field tables and revision 1–4 allocations are retained in
[SAVE5-REVISION4.md](SAVE5-REVISION4.md). That document's content counts, benchmark
numbers and release status are historical. [MAGMA_SAVE_IMPLEMENTATION.md](MAGMA_SAVE_IMPLEMENTATION.md)
and the generated revision-5 schema define the append-only current allocations.

## Frozen prior semantics and migration

Every revision is validated against its own immutable form/command/trial/polarity,
quest/item and room policy before migration. Revisions 1, 2, 3 and 4 contain exactly
8, 11, 21 and 41 enabled forms respectively. The live 65-form catalog cannot legalize
an invalid old record. Historical evolved records with legal zero trial/bond remain
legal; new causal rules are never retroactively imposed. Unknown revisions reject a
bank rather than normalizing unknown IDs into placeholders.

Revision 2–4 loading preserves all campaign, individual identities, XP/bond, commands,
party, collection, credit, quest and equipment payload bytes. It grants no new Magma
form, trial, gear, visit or quest. Revision 1 retains its original starter-sword and
safe-resume migration exception. When neither Save5 bank validates, the unchanged
format 4/3/2 decoder preserves its supported campaign and synthesizes only the already
unlocked original story families. Loading itself is read-only; the ordinary engine
Continue/arrival autosave is a separate later transaction.

Back up a player's `.sav` and retain the emulator's matching ROM/save basename before
upgrading. Older cartridges reject unknown newer banks and may show an untouched old
checkpoint. Downgrade synchronization is unsupported. Test fixtures are generated QA
saves, never player data; provenance pins the actual producer ROM, scripts and reports.

## Revision-5 additions

- Forms 31–48 and 95–100, commands 43–66; 65 enabled forms total
- Quests 30–37 with masks `3,3,15,7,3,3,3,7`; Q32 accepts only prefixes 0/1/3/7/15
- Visit byte 3 for rooms 38–45; anchor byte 3 bits 0/1 for rests 38/39
- Source byte 9 bits 0–6, repeat-branch receipts byte 16 bits 0–3,
  discovery byte 19 prefixes 0/1/3/7; no additional quest-variable bytes
- Gear sources 25–30 append items 20,37,53,67,85,5; prior sources 0–24 stay frozen
- Rooms 38/39 support spawns 0–3; only spawn 3 needs its anchor; rooms 40–45 use spawn 0

All new progress requires Q24 CLAIMED and town 38 visited. Room visits retain their
main-route gates even after returning to town. Every source requires exact-family
retention and enabled obtained history. Personal trials/evolutions require the same
individual's identity, source, form, trial key and training; linear key 2 is impossible
on bases 31/34, and requires Q32 completion on the proper later tier. Branch receipts
require two distinct retained identities, the initial source and evolved-branch history.

The full-roster admission rule is prospective gameplay policy, not stricter bank
validation. Previously legal over-budget collections remain loadable and saveable.
No source, repeated encounter or reward overwrites a companion. Full/reserved/invalid
refusals leave complete state unchanged; already-claimed rewards remain idempotent.

## Incremental transaction and anchor presentation

Save5 still uses an immutable snapshot, bounded validation/CRC/write/readback steps,
then the final commit byte. Snapshot and active state are separate; no full bank or
roster is copied onto the GBA stack. Failed writes preserve the last committed bank
and a persistent visible failure notice. Retrying uses the supported transaction path.

For ordinary saves, the engine enters frozen saving mode before beginning the snapshot.
Magma rest additionally queues its exact anchor and prior checkpoint, freezes before
hostile simulation, warms the two bitmap pages, then performs the exact full semantic
anchor validation once while frozen. Only successful proof sets campaign spawn 3.
The following update begins the existing snapshot/writer. Rendering does not perform
validation, and no weakened checksum/causality check replaces the real proof.

Cancellation or preparation failure restores the old checkpoint. Once the anchor is
valid, a later SRAM-write failure may retain that valid unsaved live checkpoint while
preserving the old committed bank. New/load/death clear pending requests. A+R, stale
requests, invalid rosters and failures at begin/mid-write/final commit are tested.

This scheduling change removes an authentic 34-individual save presentation overrun.
The exact final cartridge passes 180/180 hardware updates/page flips during the full
roster save, peak 219,356 measured cycles. Cycle timing excludes final VBlank/OAM commit,
so the update/flip checks are the actual presentation evidence. Cold load decoding is
separately blocking, not part of steady gameplay cadence.

## Evidence and limits

- 166,703 differential historical images/banks against the frozen Southern oracle
- 344,176 interruption/success positions over 56 current typed transitions
- Separate direct-API/sanitizer capacity and per-individual causal tests
- Full-engine deferred-anchor probes, including the exact earned 34-individual fixture
- Authenticated Southern → Magma controller acquisition and independent SRAM-only reboot

See [VERIFICATION.md](VERIFICATION.md), [MAGMA_POLICY_REVIEW.md](MAGMA_POLICY_REVIEW.md),
[MAGMA_LEGACY_ADMISSION.md](MAGMA_LEGACY_ADMISSION.md) and `evidence/deferred-anchor/`.
Synthetic 160-instance capacity and isolated ARM timing are not claims that 160 forms
are obtainable or that every worst-case engine load maintains cadence. Physical GBA
and whole-engine runtime stack high-water remain untested.
