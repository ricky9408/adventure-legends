# Ressa: playable kiln route

The player is 22 and Ressa is 27. Both are original adult characters. Affinity
remains hidden in the existing content13 relationship ledger; no save wire or
historical-bank rule changes.

After the original Magma kiln reward and quest32 claim, a small imperfect dish
appears on Ressa's worktable in Kilnstep. A nearby, correctly faced A cue marks
the bowl after the reward, while Ressa keeps priority when addressed directly.
The player can help shape it. On a later visit the dish comes out of the kiln;
another visit lets Ressa explain
why she once hid flawed work and why she now keeps this dish. Separate later
visits offer explicit choices to date and to marry. A final A completes each
scene. B defers it without adding an event, and an interrupted dialogue is
discarded. The same visit cannot award the next event, and repeated talks do
not increase affinity. A married revisit has its own greeting.

The original quest32 reward, Ressa's quest NPC, kiln controls, other quests,
rest point and doors keep their interaction priority. The dish appears only
after the original reward. If Mina, Edda or another person is already dating
or married, Ressa's romantic offer pauses. Mutual consent conversations are
future work, so this route cannot silently create a second partner or spouse.
Lyra still has no playable relationship route. Physical GBA hardware remains
untested.

## Earned route evidence

The native `ressa-earned-route` Gameplay CI stage runs
`tests/ressa_route_native.py` from empty SRAM. It earns the original and Magma
chapter rewards with controller input, then checks B cancellation, separate
visits, masks `0, 1, 3, 7, 15, 31`, repeat talks, cold Continue and a married
revisit. It also checks the actual OAM A cue at the earned bowl and captures a
field screenshot. `ressa-summary.json` is the bounded acceptance record; scene PNGs and
input traces are retained under `ressa-route/`. The campaign driver stops after
Magma, so its generic `summary.json` does not claim all nine chapters. Host
tests use synthetic quest completion to check event admission, interruption,
save roundtrip and existing-partner blocking; that setup is not gameplay proof.
