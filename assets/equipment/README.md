# Native equipment/stat core

These assets author the thirty-one fixed equipment definitions and three weapon
parameter sets. They do not imply that an acquisition route, weapon action,
region, or UI has been integrated into the ROM.

## Source and generation

`catalog.json` preserves the proposed fixed IDs and all eight explicit bonuses.
Run `python3 assets/equipment/generate_data.py`, or pass `--check` to verify the
committed generated `src/equipment_data.c`. The generated C source remains below 32 KB; there are no generated include fragments. The 512-entry definition
table is 12,288 ROM bytes, including disabled zero-filled identities.

Only one unique instance of each authored item can exist. Bag records do not
compact. Record zero permanently contains protected item 1, the Wayfarer Sword.
Rank is zero, quantity is one for occupied records, and empty records are all
zero. A seen bit records acquisition history, not current ownership. Discarding
an item does not erase its history or allow its unique reward to repeat.

## Equipment save allocation

The public `EquipmentState` is exactly 512 bytes. `save5` is the single codec;
it must encode fields explicitly in little-endian order, not persist a C struct.

| Relative offset | Bytes | Field |
| --- | ---: | --- |
| 0 | 384 | 48 eight-byte `EquipmentRecord` entries |
| 384 | 5 | Weapon/body/boots/belt/ring bag references |
| 389 | 11 | Settings reservation, all zero |
| 400 | 64 | Item-seen bits, indexed by exact item ID |
| 464 | 16 | Wallet/key reservation, all zero |
| 480 | 8 | Equipment acquisition source claims |
| 488 | 24 | Reservation, all zero |

Starter seen bit is `seen[0] = 2`; starter source claim is `reward_claims[0] = 1`.
Equipment sources 0..12 map respectively to item IDs
1, 2, 9, 10, 17, 18, 33, 34, 49, 50, 65, 81, 82. Northern sources13..18 append
3, 11, 19, 35, 51, 83. Southern sources 19..24 append 4, 12, 36, 52, 66, 84.
Magma sources25..30 append20,37,53,67,85,5, with exact stats from
`docs/magma-design/magma_allocation.json`. Sources31..63 remain reserved.
This array is stable acquisition order, not sorted item order: inserting item3
must never shift any published claim. Catalog checks prove exact definition
coverage and uniqueness. The shared save codec applies revision-specific
whitelists, so enabling new data does not legalize new gear in old revisions. Claimed sources require matching item-seen history. Quest
completion is a separate ledger, with cross-ledger consistency owned by save5.
These checks establish consistent claims; CRC is not authentication against
intentional save editing.

`equipment_record_validate`, `equipment_refs_validate`, and the checked O(1)
definition lookup support bounded save work. `equipment_reserved_validate`
checks all seen/claim bits and padding. `equipment_validate` checks the complete
state, including duplicate ownership and slot compatibility.

## Calls and transaction behavior

- `equipment_init` creates only the protected starter sword
- `equipment_claim` accepts the explicit source/item mapping; FULL is byte-for-byte atomic
- `equipment_claim_many` accepts 1..4 distinct enabled source IDs and stages one
  512-byte temporary state. FULL or INVALID changes no inventory, seen, or claim
  byte, even when an earlier staged grant would have succeeded
- Claim results OK, DUPLICATE, and ALREADY_CLAIMED are successful source outcomes;
  DUPLICATE grants no second copy, and ALREADY_CLAIMED changes no source state
- `equipment_preview` exposes exact before/after stats and HP without mutation
- `equipment_equip`, `equipment_unequip`, and confirmed `equipment_discard`
  only change bag/slot state and clamp current HP downward
- Charging, attacking, recovery, rolling, and any player projectile lock gear
  mutation. Unknown busy bits are invalid
- Remaining cooldowns, attack snapshots, and action clocks are absent from these
  mutation APIs. Caller sets future cooldowns from effective stats
- Cache effective stats after init, load, successful gear mutation, or base-HP
  changes. Full validation/derivation is cold work, not per-active-frame work

Base HP stays independent. Effective caps are HP 96..192, speed 288..352 Q8,
attack 24 Q4, defense 8 Q4, roll reduction 6, power reduction 8, weapon reach 12 pixels,
and stagger 3. Diagonal is `(speed * 181 + 128) >> 8`. Healing's separate
360-update lock is never shortened by power gear.

## Damage and field events

`combat_damage_q4` validates inputs, uses a checked neutral sentinel 255 or calls
the existing creature phase multiplier, rounds with signed 32-bit arithmetic,
subtracts defense, then clamps 4..255. Immunity returns zero before minimum damage.
The maximum intermediate is 89,408, which exceeds 16-bit range. Neutral damage
is unchanged after the deliberate engine-wide hearts-to-Q4 rescale.

Field capabilities are independent explicit tags. `combat_field_allows(0,
FIELD_IGNITE)` is false. No owner or combat-phase argument can grant field powers;
mundane arrows have zero field capabilities. All twenty-five current gear items are
combat-neutral. Sword/lance/bow action integration is outside this data/core.

## Verification

`python3 tests/test_equipment.py` passes 34 tests of native C and deterministic
generation, including:

- All 25 authored IDs, disabled ID bounds, every item/slot combination and all 256 refs
- Frozen original 19-row catalog/weapon/source snapshot and byte-exact starter state
- Exact Southern sidegrade names/stats, true derived previews, and no-heal behavior
- Southern sources 19..24, source 23/24 byte-boundary bundles, full-bag rollback/retry
- Generator rejection of source remaps, reordered/extra/missing rows, and stat overflow
- Every busy bit combination, no hover mutation, explicit unequip/starter fallback
- Atomic two-item sources 3+12 grants, invalid source bundles, full-bag retries
- Duplicate and discarded item history, fixed-record references, source consistency
- 1,000 repeated equip/unequip cycles, no free healing, preserved adjacent cooldown bytes
- Synthetic future catalogs exercising all 48 slots, exact caps and signed extreme bonuses
- Malformed save-facing records, references, padding, history, and claim bits
- All 25 elemental pairs, neutral sentinels, immunity, minimum/maximum and exact rounding
- 20,000 malformed-state fuzz iterations under AddressSanitizer and UBSan

The synthetic larger/extreme catalogs are host-only fixtures and never enable
those definitions in the ROM. LeakSanitizer is disabled because the execution
environment uses ptrace; AddressSanitizer and UBSan remain enabled. These modules
perform no allocations.

C99 host and ARM7TDMI Thumb builds pass `-Wall -Wextra -Werror -pedantic`.
ARM compilation also uses `-ffreestanding -fno-builtin -O2 -fstack-usage`.
Measured object sections with all 25 Southern-era definitions:

| Object | ROM bytes | .data | .bss |
| --- | ---: | ---: | ---: |
| equipment.o | 3,372 | 0 | 0 |
| equipment_data.o | 15,525 | 0 | 0 |
| combat_rules.o | 164 | 0 | 0 |
| Total | 19,061 | 0 | 0 |

No IWRAM sections or allocator/libc imports are introduced. Persistent RAM is the
caller's existing 512-byte equipment allocation. The largest individual ARM
stack frame is 544 bytes for atomic multi-item claims; ordinary gear operations
have at most 96-byte individual frames. Whole-ROM size, timing, UI, and gameplay
verification belong to the engine integration pass.

## Northern sidegrade integration

Six new definitions trade different useful parameters rather than replacing all
older items. Their acquisition quests are tested separately; an enabled row is
not proof of obtainability. Reach bonus is bounded at12 pixels, with charged bow
range156 pixels fitting the existing16-bit fixed-point arrow travel field.
Attack snapshots retain the captured range and attack when a preview changes.
The original thirteen definitions, source IDs and starter wire bytes are unchanged.

## Southern sidegrade definitions

The six new rows append to the stable source order. All unlisted bonuses are
zero; all six items remain combat-neutral, unique, rank zero, and discardable.
No new item mechanic or field capability is introduced.

| Source | Item ID | Name | Explicit nonzero bonuses | Quest allocation |
| ---: | ---: | --- | --- | ---: |
| 19 | 4 | Shadecutter Sword | reach +1; stagger +1 | 22 |
| 20 | 12 | Sunlace Lance | reach +4 | 29 |
| 21 | 36 | Breezewall Mail | defense +3; speed -2 | 25 |
| 22 | 52 | Softsand Boots | roll reduction +4; speed -4 | 27 |
| 23 | 66 | Raincatch Belt | HP +4; power reduction +1 | 26 |
| 24 | 84 | Springpin Ring | stagger +2; speed -4 | 28 |

Attack, defense and HP use Q4; walking-speed deltas use Q8. Reach is in pixels;
roll and power reductions use the existing bounded cooldown semantics. The
Shadecutter Sword with the four Southern armor/accessory pieces at base HP 96
derives HP 100 Q4, speed 310 Q8, diagonal 219 Q8, attack 0, defense 3, roll
cooldown 38, power cooldown 74, reach 1 and stagger 3. Replacing it with the
Sunlace Lance yields reach 4 and stagger 2.
Neither loadout heals when equipped, and the existing aggregate clamps apply.

The original nineteen source mappings, catalog rows, weapon parameters, starter
wire bytes, and runtime module remain unchanged. All twenty-five unique items
fit in the existing forty-eight-record bag. Source claims use four of the
existing eight bytes; only bit 0 of claim byte 3 is enabled. Save5 owns historical
revision whitelists and quest/source relationships; these data/core tests do not
prove acquisition, localization, combat impact, or native controller gameplay.
