# Southern revision4 core and save review

Developer review, 5 October2026. This is separate from native Southern gameplay
and frame-pacing acceptance. No revision4 release-blocking core/save defect was
found in the reviewed sources.

Reviewed source SHA-256:
- creatures.c:40cf1dc6b2aac7f19abda7895b42fc20445bfa002a2a622a592344ccce7b1986
- save5.c:a43263f694a57c895b6deb20871975d1ae5393375f0121c7499897daaa078306

## Independent checks

-28 targeted tests passed:8 core,4 branch/capability,12 Southern persistence,
 4 capacity/sanitizer tests
- Four historical fixtures loaded identically under Northern N5 and Southern;
 158,400 old-instance comparisons found no semantic difference
- Historical command/trial legality, evolved zero-trial/zero-bond states,
 generic reward bits5–128 and event/lifetime-aid bytes remain preserved
- Sparse indexes fail closed; qualified same-bit trials reject wrong families;
 explicit target selection, ambiguity, decline and synthetic capability33 pass
- New source claims require retained exact-family ownership; trial floors are
 checked on the same individual
- Mixed Q22 stages gear before grant. Full160/full48 failures leave state
 unchanged and retryable. Reviewed southern_quests.c:104–127 and151–166
-147,504 interrupted-write/success positions pass, including migration,
 recruitment, mixed claims, personal trials and evolution

The source-pinned ARM evidence reports maximum save-step costs66,628 cycles at
budget1024 and196,321 at budget3072. Those are isolated measurements, not a
whole-engine guarantee. Reviewed static C call-chain sums are252 bytes for save
stepping and788 bytes for the mixed claim; runtime stack high-water remains
unmeasured.

## Required before later third-tier or historical-policy changes

These are expansion gates, not active revision4 failures. Revision4 enables
only one trial per family and preserves every old authored row.

1. Separate immutable legacy trial scalars from current family trial unions.
   creatures.c:202–204 currently exposes the current family mask through the
   legacy query; line684 still requires a one-hot family mask, and line758
   requires each edge to equal that whole mask. A synthetic F001 mask1|1024
   plus qualified key2→1024/prerequisite1 fails catalog validation, changes
   the legacy query to1025 and rejects legacy mark1. Before enabling third
   tiers, retain the old scalar separately, allow reviewed current unions and
   bind each edge's required subset to qualified keys. Do not renumber old bits.

2. Finish historical policy isolation before changing any released semantics.
   creatures.c:815 still passes historical instances through current checks
   at786–801. save5.c:288–297 uses current quest masks; revision gates at500–510
   mainly restrict identities/fields, and equipment relations at517–522 use
   current mappings. Synthetic replacement of current command1 with23 rejects
   a previously legal revision1 command1 instance; broadening Q0 mask7→15
   admits a CRC-valid old revision2 ACTIVE/objectives8 case. No such change is
   present in revision4. Future changes need immutable per-revision command,
   quest and equipment snapshots rather than broader current-policy fallback.

Retain all existing historical fixtures and differential tests when resolving
these gates. Never relax old-bank validation or fabricate trial/reward history
as a migration shortcut.


## Subsequent source-preserving validation work

The source hashes above identify the initial review, not the later optimized
release candidate. The final validation implementation is pinned by
`docs/evidence/southern-validation-second.json`. It uses adjacent XP thresholds,
a fully validated single roster traversal (standalone party validation remains
complete), lazy legacy-story lookup, and bytewise collection subset checks with
all set identities still resolved. The public XP API is unchanged.

Differential checks cover 23,531,642 XP/level pairs, 301,510 party/reference
cases, 1,048,576 collection-byte pairs and 36,720 active/stored corruptions.
Historical validation still matches across 158,400 comparisons. The real
controller-earned 21-individual anchor fixture drops from 127,256 to 105,891
isolated ARM cycles. This is not a whole-engine frame-budget claim; native
controller and presented-frame evidence remains a separate release gate.
