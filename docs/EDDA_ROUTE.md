# Edda: playable harbor route

The player is 22 and Edda is 25. Both are original adult characters. Her
affinity remains hidden and uses the existing content13 relationship ledger;
no save format or old-bank rule changes.

After the original Northern beacon repair and quest21 reward, a dispatch
document appears on the quay beside Edda. Interacting with it lets the two
sort cargo labels and load the next boat. A later quay visit confirms the
delivery. Edda then tells the player about an undelivered apology to a friend;
she decides to send it herself. On separate later visits she asks whether the
player wants to date, and then whether they want to marry. Both choices require
a fresh final A. B leaves the offer open for a later visit. Each accepted scene
records one ordered event, so repeated talks cannot raise affinity.

Edda's original quest conversation, cargo handles, shop, ferry and doors retain
their interaction priority. The relationship document appears only after the
Northern main reward and does not grant or replace any quest reward.

If Mina or another person already has a dating or marriage event, Edda's dating
and marriage choices pause. Mina's route likewise pauses those choices when
Edda is a partner. Multiple relationships require authored conversations and
agreement from everyone involved; this slice does not implement them. Ressa
and Lyra still have no playable romance scenes. Physical GBA hardware was not
tested.

## Earned route evidence

The native `edda-earned-route` Gameplay CI stage runs
`tests/edda_route_native.py` from empty SRAM. The test finishes the original
and Northern main route with controller input, then checks B cancellation,
separate visits, event masks `0, 1, 3, 7, 15, 31`, repeated interaction, saved
SRAM and cold Continue. `edda-summary.json` is its bounded acceptance record;
`regions/edda-*.png` contains the scene screenshots. The full campaign driver
deliberately stops after North, so its generic `summary.json` does not claim a
completed nine-chapter run. Its snapshots and frame pacing still apply to this
route. Host tests cover the same event admission and existing partner guard
with synthetic setup; those tests do not prove that the scenes were earned.
