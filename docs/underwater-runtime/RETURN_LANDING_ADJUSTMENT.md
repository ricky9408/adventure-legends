# Reciprocal landing correction before the revision6 freeze

Developer-only navigation contract. This records a native usability correction;
it does not alter the original revisions1–5 save acceptance sets.

The first main-route native run exposed mismatched door landings: returning from
Siltglass arrived at Nacreway's north door (the Promenade route), while both
optional Archive loops arrived at unrelated doors. The current revision6 world
therefore appends four explicit side-door landings, preserving all existing
coordinates and every story/visit predicate.

| Area | Appended spawn | Position | Purpose |
|---|---:|---|---|
|46 Nacreway|3|448,160|Return from47 at the east Commons door|
|48 Kelp Promenade|2|448,160|Return from51 at the east Archive passage|
|51 Countercurrent Stacks|2|32,160|Arrival from48 at the west Promenade passage|
|52 Listening Chamber|2|32,112|Arrival from49 at the west Garden passage|
|38 Kilnstep Commons|4|416,240|Return from46 at the actual shell lift|

This supersedes the design proposal's original “spawn2 only at46/47” wording
for current-r6 explicit return entrances. Only46/47 spawn2 is an anchor and
requires its matching anchor bit. The appended48/51/52 spawn2 rows are ordinary
explicit landings; they retain each room's existing main-story requirements.
Room38 spawn4 requires Nacreway visited in revision6. Revisions1–5 still reject
it, and their original slots0–3 remain byte-for-byte the same coordinates and
acceptance policy.

The nine bidirectional doorway pairs are:
46↔47,46↔48,47↔50,48↔49,48↔51,49↔52,50↔51,51↔52,52↔53.
The Court's53→46 arch remains an intentional one-way return shortcut.
All generator exit records now store their actual destination spawn explicitly.
Nacreway's south transition also checks the visible door's horizontal span;
walking elsewhere along its lower boundary does not trigger the lift.

No original PNG, indexed pixel/C-art bytes, collision rectangles, story gates,
trial predicate or old spawn coordinate changed. The shell-lift landing and its
A approach are the same point(416,240), facing up at the portal(416,224), and no
old Magma town interaction claims that approach.

Verification is recorded in `return-landings-acceptance.json`. The focused tests
are synthetic host traversal and codec-reload checks. Native return travel,
reboot and cadence must be checked on the new final cartridge, not inferred
from the earlier main-route run.
