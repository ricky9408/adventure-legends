# Independent game review

Reviewed production logic, the build/include graph, generated content, and the
verification pipeline. Prior instructions and PASS reports were not acceptance
oracles. The executable acceptance map is `.trust/policy.json`; `make test` runs it.

| Finding | Change | Independent evidence |
| --- | --- | --- |
| Diagonal movement checked Y using the previous X and could enter a solid corner | Publish accepted X before checking Y | Production-linked movement cases across 78 room states; restoring the old operation order fails |
| Invalid room IDs could index outside collision arrays | Reject invalid rooms before dispatch | Negative IDs and IDs beyond the region range under UBSan |
| Stat composition allowed attack values rejected by the weapon API | Clamp with the shared equipment limit | All valid attack values across bonus and weapon configurations; current authored loadouts were below the conflicting limit |
| Compiler warnings could pass | Enable `-Werror`; fix ambiguous statement layout and redundant address checks | Native ARM compilation and host behavioral properties |
| Source freshness could miss added files and nested helpers | Compare exact file sets and contents, including verification inputs | Added/removed/changed-input negative controls |
| Persistence tests wrote generated reports into reviewed documentation | Put transient reports under `build/` | Input freshness rejects new documentation reports during validation |
| Active checks pinned obsolete production bytes | Keep historical fixtures intact; replace active historical-identity rows with current behavior checks | Explicit retired-command inventory, source graph, geometry and regeneration checks |
| Optional generators were not covered by reproducible builds | Regenerate in a disposable copy; include selected PCM generation | Compare production source bytes and existing asset semantics |
| Cached bytecode and sibling modules could bypass source pins | Reject unpinned vendor files and disable bytecode writing | Malicious-cache and sibling-import negative controls |
| Nested timeouts could leave generators running | Forward interruption through a dedicated exception and terminate child groups | Descendant-process timeout tests |

New behavior checks exercise actual production C. They cover movement, collision
enumeration, input ownership, modal clocks, weapon bounds, projectile occlusion,
save interruption/corruption, replay-safe rewards, invalid roster records,
transaction publication, and starter-save migration for revisions 1–13. Deliberate
source faults must fail their behavior assertions. The native observer exposes
controller input, observation and same-run earned SRAM loading; it exposes no
game-RAM-write or machine-state-import API.

Existing full campaign routes remain supplemental. Their exact inputs and results
are recorded independently; fixture preparation is distinct from controller-earned
progress. Inventory classification alone is not execution or branch coverage.

Native emulator checks do not prove physical cartridge behavior. Synthetic room
states do not prove every authored puzzle state or optional route. Starter-save
migrations do not prove every populated historical collection. Unsigned local
receipts do not establish hostile-process isolation or release authorization.
