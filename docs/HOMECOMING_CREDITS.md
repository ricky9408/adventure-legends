# Homecoming credits offer

After Q63 has committed and its final dialogue releases control, the village
homecoming offers two explicit choices: A shows the existing credits, B returns
to exploration. It waits for all A/B/Start buttons to release, then requires a
fresh press. It does not start automatically. B or Start during the roll also
returns to the same field scene, without reconstructing the village or writing
a save. A at the completed endroll replays the credits.

The offer and replay are presentation only. Quest completion, equipment,
invitations, optional companions, rewards and saved flags are unchanged by
viewing or skipping the credits. The original ending's automatic-start behavior
is preserved. The existing credits retain all names, including the GBJ author.
No soundtrack or music data is changed.

An existing completed Q63 save can see the offer again by speaking to the
village elder. The normal completed-quest dialogue plays first. A pending
event, dialogue or unverified save prevents the offer from taking control.
The original queued final story stages must also reach zero: verified claim
publication alone does not mean those closing dialogue pages have finished.

## Validation

`python3 tests/test_covenants_world.py` checks a synthetic Q63 READY checkpoint
derived through the real typed quest jobs, its final claim transaction, the
verified-save gate, one-time offer consumption and read-only replay through
the elder. This does not establish a fresh native campaign route.

`python3 tests/test_ending_credits_host.py` checks every held-button combination,
fresh-input entry, long idle without automatic start for homecoming, the
original automatic ending, full scroll, stable end, replay and B/Start exit.
The renderer is checked against 25,521 independent clipped full-frame/canary
comparisons, in both strict and AddressSanitizer/UBSan builds.

## Native acceptance route

Use a disposable save copy and temporary SRAM directory. Complete or load an
earned Q63 route, finish the elder dialogue while holding A, and verify the
offer waits for release. Idle, then choose B and confirm the same position,
health, companions and quest state. Speak to the elder again, release input,
choose A, inspect the full roll including the GBJ credit, and replay once.
Exit with B/Start; reload the copied save and confirm Q63 and optional invitation
state were not altered. Repeat with a simulated failed pending save: the offer
must wait until the final claim is verified.
