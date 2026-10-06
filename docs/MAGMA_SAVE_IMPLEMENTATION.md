# Magma typed progress, equipment and Save5

Implementation in the separate Magma workspace. This document describes ledger,
codec and isolated ARM evidence. It is not a release, controller-acquisition,
whole-engine cadence, or physical-cartridge claim.

## Public runtime surface

`src/magma_quests.h` defines the chapter's explicit event transactions:

- Quest offer, single-bit authored objective, claim, availability and mask
- Permanent visits38–45 and anchors38/39
- Source identities1/2 forQ30/Q31 and16–22 for the seven ecological sources
- Initial source invitation, source status and family/form/credit lookup
- Branch repeat status/invitation using original source tokens16–19
- Discovery steps1/2/4 and derived Listening Stones journal state
- Participant-bound trial status/completion(slot,instanceID,family,key,source)
- u16-compatible READY0x100 and CALDERA_OPEN0x200 context projection

The world layer must prove the actual tagged object, geometry, allowed scene,
selected participant and explicit choice. These APIs do not detect a puzzle,
grant expedition credit or write SRAM. Call them only at interactions or cold
menu transitions; source/trial queries perform bounded collection validation.
Trial proof must be cleared on death/load by the world layer.

Results0/1/2/3 are unchanged/changed/ready/rewarded. Refusals4/5/6/7 are
locked/full/reserved terminal space/identity exhaustion; invalid is-1. A claimed
one-time source is checked before admission so a retry remains unchanged.

## Atomic transactions and ownership

Q30 preflights admission, stages its512-byte equipment reward, and only then
calls `creatures_grant_admitted`. After the grant succeeds only infallible gear
copy and quest/reward-bit writes remain. No complete Save5State or roster is
copied onto the stack. Q31 and all ecological/repeat grants use admitted grants.
Personal completion stages only one24-byte individual, preserves higher XP/bond,
and binds the exact selected slot and ID, family, key and typed source.

Every repeat is a real new individual with a unique ID. First-extra receipts do
not cap later explicit encounters. No repeat modifies one-time credit, generic
reward, item or existing-companion XP/bond ledgers. Trial floors belong to the
participant, even if a prior generic lifetime-aid bit already suppresses credit.

The prospective72-opportunity/88-extra admission rule is not bank validation.
Legal old over-budget rosters remain loadable and saveable. Only nonworsening,
non-coverage-losing, physically fitting gameplay additions may proceed from such
states; this does not promise recovery or room for every future companion.

## Exact durable interpretation

Wire5 and all offsets remain unchanged:160×24-byte individuals,5056 used bytes,
two6144-byte banks at0x0200/0x1A00. Current writes declare content revision5.
The SHA-pinned revision1–4 schema and policy block remain byte-identical.
Separate revision5 quest/item/room rows keep prior mappings frozen.

Quests30–37 have masks3,3,15,7,3,3,3,7;Q32 permits prefixes0/1/3/7/15.
Q33 requires claimedQ30. Q37 requiresQ32 objective prefix3. Every new regional
step requires claimedQ24 and town38 visit. New room visits are byte3; ecological
sources byte9 bits0–6; branch receipts byte16 bits0–3; Listening Stones discovery
byte19 prefix0/1/3/7. Southern discovery byte18 and all generic prior ledgers
retain their original meaning. No new variable bytes are used.

Each new source requires exact-family retention and enabled obtained history.
Every retained new family requires its typed source. Trials and evolutions have
same-individual level/bond/key checks, teaching context and, for linear key2,
claimedQ32. A branch receipt requires its initial source, two distinct retained
IDs and at least one retained evolved branch plus branch history, including after
both copies evolve. History never substitutes for an individual.

Collision-backed static spawn policy: rooms38/39 allow indices0–3, and only3 is
an anchor return requiring byte3 anchor bit0/1. Rooms40–45 allow only0. Exact
coordinates and radius-five path checks are in `assets/magma_region/contract.json`
and `validation.json`; these are static geometry checks, not controller evidence.

Gear sources25–30 append IDs20,37,53,67,85,5. All eight stat components match
`magma_allocation.json`. Source order0–24,48 noncompacting records, protected
starter fallback, busy locks, HP clamps and cooldown/action snapshot behavior
are unchanged. No item grants a field ability.

## Source-pinned historical evidence

`tests/fixtures/v5-revision4/southern-all41-town.sav` is the delivered controller
41-form/21-individual/25-gear/all30-quest independent reboot. Its SHA256 is
0bd83c19eb0dee81b3cd9e2b48462f6362b559786e38fa119312fe05787b0bd3.
The minimal8 fixture SHA256 is
968066ed983bd48fc2af0d7ffeb79f635624037ef2099809fd00c97aaa04cc0c.

Their original multi-megabyte reports are stored as124 exact-byte parts, each
at most30,000 bytes. Reassembly matches the original report pins, never a
minified surrogate. Provenance verifies source ROM
87d16a0fc513d7e8a491e0b5ac5929f7951e1e44e18b7f534f1e5e0cc794d4de,
707 manifest entries and original snapshot state/SRAM pairs. Six fixture tests
check these pins and raw-wire completion counts.

## Checks and measurement scope

Commands:

    python3 tests/test_southern_frozen_fixtures.py
    python3 tests/test_save5_history.py
    python3 tests/test_save5_history_differential.py
    python3 tests/test_save5.py
    python3 tests/test_southern_save.py
    python3 tests/test_southern_save_limits.py
    python3 tests/test_equipment.py
    python3 tests/test_magma_save.py
    python3 tests/test_magma_save_limits.py
    python3 tests/profile_magma_save.py

Historical differential comparisons:166,703 CRC-valid banks/images,4,688 accepted
and162,015 rejected, using the separately compiled SHA-pinned Southern oracle.
It compares load/has-valid acceptance, all decoded bytes, output atomicity and
SRAM immutability. Both delivered S3 SRAMs are included. Revision5 is a new
supported policy and is tested separately, not asserted identical to an older
reader that correctly rejects an unknown revision.

Magma direct-API tests construct65 obtained forms from34 retained individuals,
31 gear and38 quests. They check both alternatives, same branch twice then a
third real base, source/trial/branch floors, every unassigned byte, full/duplicate
refusals, discovery with a full bag, atomic mixed rewards, grandfathered160,
synthetic48 and save interruption. These constructed states are not authentic
controller acquisitions. The C sanitizer harness checks1,200 randomized
snapshots under ASan/UBSan plus full160 trial queries.

`docs/evidence/magma-save-arm.json` records isolated ARM7TDMI results, source
hashes, source stability, all measured steps and compiler stack frames. The
1024-byte prior70,000-cycle limit initially exposed a73,893-cycle boundary cost.
Deferring causal validation to a fresh bounded update fixes it; measured maxima
are21,644 begin cycles,68,320 cycles at1024 and156,520 at3072/effective3072.
Budget0 performs no work;1-byte steps progress; the3072 cap remains enforced.

Blocking current validation measures114,190 cycles for authentic S3 retained21,
152,285 for synthetic Magma34,486,059 for synthetic160. The independent declared
policy checks measure138,267,189,818,523,718 respectively. These are cold
transition checks, not per-frame APIs or whole-engine cadence measurements.
The benchmark supports `--authentic34 PATH --authentic34-sha256 SHA` for the
later earned controller fixture. Authentic34 measurement is now recorded in
`docs/evidence/magma-save-arm-authentic34.json` with separately verified source
provenance. The input is the bringup09 controller-earned34 snapshot; final reboot
and release acceptance remain separate.

The save core's mutable BSS grows20 bytes over the historical-policy foundation
(7248→7268); magma_quests adds no static mutable RAM. Its largest own-function
frame is576 bytes for the512-byte mixed-gear stage. Compiler own-function frames
are not cumulative stack high-water or interrupt safety proof. Native world
acquisition, modal interactions, merged-engine cadence, runtime stack high-water
and independent final-ROM review remain separate acceptance gates.

## Independent audit fixes

The independent current-source audit found and reproduced an impossible state:
linear bases31/34 could retain key2 if their flags and training floors were
forged. The authoritative creature policy now gives those bases allowed mask1,
while32/35 and33/36 retain mask3. Qualified query/mark and every current/revision5
instance reader reject key2 on the base; frozen1–4 policy is unchanged. Regression
coverage includes direct instances, decoded state, CRC-valid wire banks,
zero-write pending snapshots and sanitizers. The original failed reproducer is
preserved under `build/magma-save-independent-review`.

Typed status queries now mirror identity exhaustion before confirmation, while
already-claimed sources remain unchanged. Q30's status additionally preflights
its mixed gear reward. Every failure leaves state unchanged. A first-extra
receipt's specified ownership minima remain enforced; no unrequested converse
restriction or blanket duplicate-family prohibition was added.

## Exact gear-menu HP rendering

The six Japanese names/descriptions are appended in `assets/magma_ui.json` and
wired through `gear_menu.c` without changing published text keys. HP bonus text
uses hearts0.5/0.25, matching8/4 Q4 points.

The prior single-decimal helper truncated6.25 to6.2 and placed a fixed decimal
point over two-digit integers. The new helper uses variable integer width and
exact terminating decimals. In the54px comparison column, labels use0–12,
before values13–29 right-aligned, arrows31–35, and after values37–53. All shipped
HP bonuses are quarter-aligned; every actual comparison therefore fits17px.
No numerical equipment statistic changed.

`tests/test_gear_hearts.py` passes strict and ASan/UBSan pixel checks over97 Q4
values at both pixel parities/backgrounds, plus2,500 quarter-heart before/after
canvases. Adjacent pixels are preserved. Native-size output is
`build/gear-heart-host/exact-heart-comparisons-240x160.png`; it was visually
inspected along with the4x nearest-neighbor copy. This is an isolated host canvas,
not a native game capture. Existing integer/speed pixel tests still pass.

ARM gear-menu object comparison against the delivered original: ROM+162 bytes,
BSS unchanged16 bytes, IWRAM text340 bytes smaller(0x4E4→0x390). The integrated
gear-menu native capture and cold-menu cadence remain part of parent acceptance.

## Authentic34 isolated measurement

The bringup09 all65-town SRAM SHA256 is
8287fb0c34b2cdd2a73408bd24bf290f640281ac3a8b7d98d0ad8a5f009ece28.
The source controller report records no game RAM writes and no failures; both
bank CRCs and raw retained/history/gear counts were independently checked. Its
named ROM SHA256 is8080b2fb1c82a99650da9837c5f5037a570dc3e5b17eb1a10ee7a9d7c31ffde4.

The exact earned34 payload passes isolated native current/declared validation
and all bounded save writes. Source files stayed unchanged during measurement.
Global maxima remain21,644 begin cycles,68,320 at1024 and156,520 at3072. Source
report/snapshot pins are in `magma-save-arm-authentic34-provenance.json`.
This closes the authentic34 isolated measurement gap, not final independent
reboot, whole-engine cadence, runtime stack or physical-cartridge acceptance.
