# Current-r6 reciprocal return landing follow-up

This small follow-up supersedes only the room/spawn acceptance rows in the earlier Underwater save/progress receipts. It does not alter the wire layout, frozen revisions1–5, quest/source/trial semantics, transaction lifecycle, admission policy, writer algorithm, or gear staging. Native coordinates and walking/collision evidence belong to the matching world update.

## Exact production delta

Only `src/save5.c` and `src/save5_underwater_policy.h` changed. `codec.diff` is the complete delta against the prior reviewed frozen files.

- Room46 spawn3 is the ordinary east return
- Rooms48/51/52 spawn2 are ordinary authored returns, retaining each room's visit and main quest/prefix gates
- Room38 spawn4 is a current-r6 shell-lift return and additionally requires the Underwater town46 visit
- Only rooms46/47 spawn2 require their Underwater anchors
- Every previous spawn remains unchanged; other unsupported values remain rejected
- Revision1–5 still reject room38 spawn4. The frozen Save5 history header remains byte-identical, SHA256 `69dba67ea332f03bab26246b5739662aef7177ff1cabe43bed8b444940d40a13`
- Original native Magma34 SRAM remains SHA256 `a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858`

The r6-only Magma room override retains its original room-introduction revision5 so existing spawn3 anchor semantics remain exact; only the revision6 decoder selects the override.

## Focused verification

`python3 tests/test_underwater_return_spawns.py` passes seven methods:

- All256 spawn-byte values across20 room cases, including unsupported room/spawn holes
- Current validator, revision6 validator, bounded preflight and CRC-valid banks at both bank positions agree
- Positive ordinary returns do not borrow anchor permission; town/Commons anchor landings still require anchors
- Teaching, main prefix, source/history and permanent visit failure cases remain rejected
- Every spawn byte for all eight Magma rooms still agrees with the accepted revision5 oracle
- All five new landings save/read back; invalid new landings fail before any SRAM write
- All6146 interruption positions for two new return checkpoints, targeting both A and B, preserve the prior bank and load exactly the old or committed target state

`host.json` records19505 case groups, including12292 complete interruption cases, and hashes the unchanged23-file source/include closure used during testing.

Also rerun after the delta:

- Full historical differential:61216 banks, exactly441 accepted and60775 rejected, with no decoded-state or mutation differences
- Save/gear/sanitizer regression:10 methods, including6000 ASan/UBSan adversaries
- Bounded transaction regression:8 methods
- Isolated ARM transaction profiling at WAITCNT0x4317: maximum bounded stage56038 cycles, maximum begin24836 cycles; report `transactions-arm.json`

No unrelated long-cut suite was rerun. Earlier430220 transaction interruption checks remain evidence for the unchanged writer/transaction implementation on the pre-return source closure; the focused new-checkpoint interruption tests cover this delta.

Independent review and its separate bounds-sanitizer receipt are under `review/`.
