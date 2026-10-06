# Legacy-region acquisition admission integration

All17 pre-Magma forward gameplay acquisition routes now use the same global
72-terminal-opportunity reserve as new Magma sources:

- Regional quests2/3: Water and Metal recruits
- Northern quests11–15: all five recruits
- Southern quests22/23: both guaranteed recruits
- Southern field tokens16–23: all eight ordinary field recruits

The wrappers use creatures_grant_admitted. Southern teaching rewards additionally
preflight the candidate form before staging equipment, preserving the mixed Q22
transaction: failed admission cannot leave a gear reward, receipt, quest state,
ID increment or creature/history mutation. Standalone field claims avoid a
redundant preflight scan and commit source bits only after admitted success.

Existing result values remain unchanged. The three headers append RESERVED=6:

- FULL=5 remains a physically full160-record roster or actual equipment capacity
- RESERVED=6 means a redundant new copy would consume terminal-reserved space
- INVALID=-1 covers malformed state, exhausted instance identity and invalid data
- An already-claimed quest/source remains UNCHANGED=0 before admission, even in a
  full or over-budget collection

Missing-family captures increase occupied and viable coverage together. They
remain available at excess88 and, while space remains, in a grandfathered
excess89 collection. Redundant rewards at either boundary refuse byte-exactly.
No migration, save wire format, old source meaning or historical record is changed.
Existing legal over-budget states can still load/save; no full-completion recovery
is promised for those states.

## Focused evidence

Run python3 tests/test_magma_legacy_admission.py. The strict C99 and ASan/UBSan
executables each pass23,133 checks across all17 actual source wrappers. The harness
links the real creature, quest, equipment and Save5 implementations; Southern
setup loads the immutable Northern controller fixture before host-authored events.
These are integration-state tests, not new controller-native route evidence.

Each route is tested for:

1. Missing-family acquisition at safe excess88 and grandfathered excess89
2. Byte-exact duplicate refusal, including equipment, source/quest receipts,
   retained IDs, histories and selected party
3. Real FULL at160 records and distinct INVALID for ID exhaustion or bad IDs
4. Idempotent retry after the successful source has been followed by a full roster
5. Current and exact revision4 validity, plus real save/store/load roundtrips

Mixed Q22 is also checked on either side of the reserve threshold. Below it,
exactly one new companion and the authored gear commit together; at it, all bytes
remain unchanged and the quest is retryable.

## Regression updates

Current-only expectations now describe65 forms,35 edges and commands through66.
Synthetic branch/capability tests use the reviewed current F013 branch; the
synthetic future F001 extension uses the next unused command67. Historical binary
prefixes, migration hashes, frozen revisions1–4, u16 trial-width tests and every
malformed-graph case remain tested without weakening their assertions.

The isolated regional/northern/southern runtime harness UI dictionaries append
only MG_RESERVED/MG_RESERVEDB aliases. Production text ordering is untouched.
The parent integration owns the actual UI mapping, controller flow and cadence.

A separate authoritative current per-form policy now rejects premature trial key2
on base31/34, including forged records with sufficient level/bond. Qualified trial
APIs and current/revision5 readers agree;32/35 and33/36 preserve legal inherited
masks. The frozen historical policy is unchanged.
