# Regional suppliers

Each regional town has a traveling supplier beside its arrival road. Walk close
and press A. Up/down selects stock, A opens the price/effect confirmation, a
fresh A purchases, and B backs out. Gear joins the existing equipment bag;
select it explicitly from Equipment. Purchases never equip or heal the player.

The three original village products remain Heart Tonic (18), Spirit Tonic (24),
and Iron Edge (120). Regional suppliers also sell those products and add one
existing equipment option per chapter. Later towns retain earlier stock.
Existing quest acquisition remains available; buying the same unique item
does not create a second copy or claim its quest reward.

| Town room | Supplier center | New equipment | Price | Nominal equipment bonuses |
| ---: | --- | --- | ---: | --- |
| 16, Reedhaven | 208,284 | 2, Reedguard Sword | 96 | Attack +4 Q4; defense +1 Q4 |
| 22, Hearthwake Quay | 240,272 | 49, Trail Boots | 144 | Walking speed +8 Q8 |
| 30, Sunlace Anchorage | 160,272 | 67, Bricklayer Belt | 180 | Defense +1 Q4; stagger +1; walking speed -2 Q8 |
| 38, Kilnstep Commons | 304,284 | 85, Quietnote Ring | 216 | Walking speed +2 Q8; power recovery -3 updates |
| 46, Nacreway | 304,284 | 54, Driftstep Boots | 252 | Walking speed +6 Q8; dodge recovery -1 update |
| 54, Greenwake Common | 208,284 | 68, Mapfold Belt | 288 | Maximum health +8 Q4; walking speed -2 Q8; power recovery -2 updates |
| 62, Shared Horizons town | 208,284 | 86, Quietwater Ring | 324 | Defense +1 Q4; power recovery -2 updates |
| 70, Covenants town | 208,284 | 6, Shellscribe Sword | 360 | Attack +1 Q4; sword reach +3 pixels |

The menu shows the selected item's price, owned count and effect before the
confirmation. The existing Equipment preview provides the exact comparison
against the current loadout, including aggregate clamps. The speed percentage
and recovery seconds in the shop text are approximate at the base walking
speed and normal 60 Hz play rate. All eight optional gear purchases total 1,860
gold. A seen or discarded unique item cannot be bought again.

## Persistence and limits

Content revision 12 adds honest paid-gear receipt bits in `EconomyState.reserved[0]`.
`reserved[1]` is reserved for the two inspected story-companion flags. Both use
already allocated bytes. The 6,144-byte bank, 5,088 used bytes, record offsets,
48 equipment slots and all existing item/source IDs remain unchanged.
Revisions 1–11 retain their existing accepted semantics; revision 11 requires
all newly used wallet bytes to remain zero. A purchase writes the gold debit,
receipt and unique equipment record together. Live ownership changes only
after the committed bank has verified successfully.

## Validation

`python3 tests/test_economy.py` covers regional location and stock gates,
unchanged supply history, unique gear ownership, changed-owner rejection,
sampled interruption points, old-or-complete purchase recovery, later quest
duplicate handling and revision 12 receipts on an existing completed history.
The completed history and interruption probes are host fixtures, not native
controller acquisition evidence.

`python3 tests/test_shop_experience.py` checks all eight stocks, range boundaries,
confirmation and failure input, price/effect rows and 240×160 text bounds under
strict compilation plus AddressSanitizer/UBSan.
`python3 tests/test_regional_shop_positions.py` checks the actual authored town
solid tables with the five-pixel foot predicate and a bounded four-pixel BFS.
Every supplier is reachable from the standard arrival and has at least two
safe approach centers. This is static geometry evidence; the combined game
must still be checked with native controller input.

## Native acceptance route

Use a disposable copy of the save, or a clean temporary SRAM directory.
Do not run these checks against a personal save.

1. Fresh game: buy a tonic and Iron Edge in the village, then earn access to
   Reedhaven. Approach the new merchant and inspect Sword price/effect. Cancel
   once; buy with a fresh A; confirm one item, 96 fewer gold, no automatic
   equip and no health gain. Equip through the existing comparison menu.
2. Reload a copy of an existing revision 11 regional checkpoint. Visit each
   town with normal movement; inspect its newly added row and inherited stock.
   Buy an unowned option, save/reload, and confirm debit plus ownership. An
   already seen item must show an owned message without spending gold.
3. Check the neighboring authored interactions: Southern ferry at 240,280;
   Magma lift at 240,284 and notice near 208,288; Underwater Q45 notice near
   240,288 and archive copy near 200,288. A must still reach the intended actor.
4. With a copied save, interrupt a pending purchase at sampled frame boundaries
   and reload. Observe either the original balance/bag or the complete purchase,
   never a debit without the item. Retain the host interruption suite as the
   wider byte-boundary evidence.
5. Inspect merchant sprites, A hints, selected rows and feedback at native
   240×160 in all eight towns. Check for authored actor/hint overlap and verify
   normal frame timing on the final combined ROM.

`tests/regional_suppliers_credits_native.py` automates these controller branches
from authenticated snapshots of this review's accepted main campaign. It blocks
game-RAM writes and machine-state imports, records the producer and candidate
hashes, labels cross-ROM SRAM use, copies input saves into a fresh evidence
directory, and records every hardware frame. This diagnostic checks all eight
regional Heart Tonic and newly introduced gear purchases, exact debits, unique
ownership, unchanged equipment selection/health, cold Continue and refusal to
charge for already owned gear. Its completed-Q63 replay covers A/B offer,
full credits, GBJ author, replay and read-only field return. Fresh first-Q63
acquisition and the queued narrative gate require the full campaign route.
