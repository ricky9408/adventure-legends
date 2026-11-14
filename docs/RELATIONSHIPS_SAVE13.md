# Relationship persistence, content13

This slice adds storage, not playable romance scenes. The event core remains
unconnected to people/dialogue. Current normal adventures therefore retain empty
personal ledgers until the scene slice is implemented.

## Wire and memory contract

- Wire version5, both 6,144-byte banks, CRC range and commit-last protocol stay
  unchanged. Content13 appends four event bytes at5088..5091; used length is5092.
- All prior typed offsets stay unchanged. Revisions1–9 require used length5056;
  revisions10–12 require5088. Their newly used bytes still have to be zero.
- The full decoded state grows4976→4980. Metadata staging stays at5056; its
  original1088-byte extent must not move. A separate four-byte staging snapshot
  protects events while metadata is assembled.
- The ID scratch region and current padding start at5092, not5088, preventing
  the640-byte scratch clear from destroying the new wire payload.
- Blocking load, incremental load, streamed validation and transaction preflight
  all validate the event bytes. Earlier revisions decode to zero without awards.
  The economic schema for13 is explicitly mapped to12, not broadened.
- Economy/gear transactions retain events and their full-state preflight tokens
  detect a concurrent change in relationship state.

Historical fixtures, frozen policy inputs and pins remain unchanged. Test-only
ABI adapters zero-extend pre-economy states by36 bytes and pre-relationship states
by4; neither old codec nor old wire grammar is changed. Current writer assertions
advance to13/5092. Historical fake-bank tests retain their historical header
length instead of accidentally testing an invalid modern header.

## Local verification (not a full release certification)

- Relationship core: normal and UBSan tests.
- Relationship codec (normal and UBSan): all1,296 legal ledgers; every value at each of four bytes;
  old12 migration/forgery rejection; bounded loader budgets and newest-bank
  fallback; invalid writes; full-state preflight matching; every write-cut
  position while replacing one nonzero ledger with another.
- Save5 main41 tests; incremental loader7 tests comparing68 existing SRAM files;
  history policy7 tests; frozen Southern differential166,703 cases; Return
  differential247,438 cases; economic state18 and economic history7 tests;
  later reward codec10 tests; Southern save13, Horizons history6, Covenants
  history6, Underwater history6 tests; retained migration validator2 tests.
- Full-state snapshot:64,740 byte mutations across13 fixtures; strict and
  ASan/UBSan copy-canary tests cover the new five-word tail.
- ARM GBA build: ROM28,780,220 bytes; ELF text28,780,044/data176/BSS123,324.
- Real mGBA cold Continue/cancellation: six historical/prepared cases plus a
  synthetic relationship input. All loading frames fit280,896 cycles; observed
  maximum266,697. Source saves remain unchanged during the read job.
- Dedicated physical-input test: prepared [31,15,7,3] ledger, UP across the actual
  village road, verified new SRAM write, exported save and cold Continue;
 1,601 hardware frames, no game-RAM writes or machine-state imports.
  This proves persistence, not that the romance was earned through scenes.

Candidate ROM SHA-256:
`1147560da069117114b0aa463d709002d0536c61c979f9d8d145ff5d4a51f504`.
Native report/input traces/screenshots are generated under the chosen test output
folder; CI runs the same dedicated travel test and retains its artifacts.

Independent final review, exact-head hosted CI and postmerge verification remain
release gates. Physical GBA hardware and playable personal scenes are untested.
