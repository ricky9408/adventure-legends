# Underwater candidate A: independent minimal-player native review

Developer-only progression evidence. This is a failed strict timing acceptance
result, with the requested functional route and lifecycle checks completed.
It is native mGBA evidence, not physical-handheld validation.

## Results

- The unchanged, authenticated delivered Magma minimal-ten SRAM cold-boots into
  candidate A and completes the required Underwater route with only Inkbud49
  and Bobclam52 newly acquired: twelve individuals and twelve histories total
- The main route has 762 passing assertions and eight passing 120-frame native
  action windows; its worst measured render is 217,550 cycles
- The independent final review has 1,187 assertions: 1,177 pass and ten strict
  whole-action timing assertions fail. No final functional assertion fails
- All 21 directed ordinary transitions are exercised, including optional garden
  and archive shortcuts after the real story permits them. All destination
  rooms, reciprocal spawn slots, clear landing positions and retained identities
  are checked. The review performs 27 transition traversals
- Underwater46 south reaches Magma38/spawn4 at (416,240). The real shell-lift
  interaction returns to Underwater46/spawn0 with all new main progress intact
- Native rest and independent cold reboot preserve exact roster, quest and
  equipment bytes. Real Commons enemy contact causes death; normal A retry
  returns to the earned room47/spawn2 checkpoint. Retry and another cold reboot
  also preserve those exact bytes
- Repeated Keeper and Shellwright dialogs are durable no-ops. The unevolved,
  untrained Inkbud's two-branch preview correctly remains ineligible, and cancel
  preserves durable state. Eligible evolution preparation is outside this
  minimal save's state; no eligibility or personal trial was fabricated

## Timing failures retained

The strict predicate is one game update, one display-page flip, and fewer than
280,896 measured cycles per native hardware frame. Every frame of each tested
Continue, transition, rest, dialog and evolution-preview action is retained.

1. Underwater46 to Magma38 takes 197 hardware frames including ordinary approach
   and transition debounce, but presents and updates only 196 times. One frame
   measures 295,856 cycles. The earlier review independently measured the same
   path's hitch at 295,790 cycles. Re-entry to Underwater passes
2. Cold ineligible Inkbud49 evolution preview takes 30 hardware frames and has
   29 updates/page flips. Its first cold confirmation page measures 286,896
   cycles. This is not an eligible evolution preparation/commit case
3. Each of eight independent title Continue actions resets the game's frame
   counter, then has seven intervals without a page flip. A 52-frame window
   has 44 forward updates, 45 page flips and one observed counter reset. Worst
   measured loading cost is 2,226,970 cycles. These remain strict failures and
   are explicitly distinguished from the ordinary-gameplay return/UI hitches

The native town rest passes 85/85 frames at maximum 232,492 cycles; Commons
rest passes 85/85 at 242,150 cycles. Death retry passes 34/34 at 236,555 cycles.
Cold Keeper and Shellwright dialogs pass 189/189 and 194/194 frames.

## Authenticity and scope

Target ROM: `0d7fd78733405a6fc8ec6eeca68ad207dfb11b91dcfe44a8d67f312552b46675`

Target symbols: `da6615df0f932eb5f096442092962d2fa28fad684758640c65175bc535d8b176`

Target source manifest: `f75b5b9924bda3e9118e64f80f12f5905d1d72cef166980c3d8a94d407484580`

Source delivered Magma ROM: `90ba47f30a0c94c28f073d26cc31ac5f5c736eb4d6e704d090892d2776f1ffb2`

Source minimal SRAM: `f584de3b29cb77731148b31b99dc40e0c7e4ec05f1aac42e0d38dd5b44612eeb`

Both Magma fixture packages pass their portable authenticity verifiers. The
minimal producer's original report/artifacts and all 893 original Magma runtime
inputs were independently reverified against the existing original checkout.
The all65 package also passes original-runtime verification; this suite does not
claim an all65-derived target playthrough. The exact target ELF is paired against
the target ROM, and all 1,161 target runtime source inputs were verified and
archived unchanged before concurrent development could change the working tree.

The main helper and its imported project dependencies were copied before
execution. The independent review imports that frozen helper snapshot. Both
public and direct bridge RAM-write interfaces are blocked. The independent
review additionally blocks public and direct bridge machine-state imports.
No machine state is loaded anywhere in these routes: only the authenticated
source SRAM and subsequently hash-verified, same-candidate earned SRAM are used.

`summary.json` provides the compact results. Report folders retain the exact
original report bytes in ordered, hashed parts; concatenation reconstructs the
original JSON without reformatting. Failed attempts, their logs, and their exact
review drivers are retained. The first review launch failed in driver setup
before gameplay. The second review's two immediate reverse-exit failures came
from an eight-frame helper press during the existing twenty-frame transition
lock. The final review waits for that observed lock to clear naturally; no ROM,
state, predicate, or destination expectation was weakened.

The local complete native artifacts, including ROM/ELF copies, screenshots,
record-only machine states, SRAM and complete immutable helper/runtime trees,
are under `build/underwater-minimal-review-a`. The portable evidence below does
not rerun an emulator or claim that build artifacts are bundled here.

## Reproduction and evidence verification

Verify this evidence package with standard-library Python:

```
python3 docs/evidence/underwater-minimal-candidate-a/verify_evidence.py
```

The exact native run command is in `reproduce.sh`. It requires the local frozen
candidate, frozen helper/runtime tree and existing mGBA bridge dependencies. A
nonzero exit is expected for this candidate's retained timing failures.
