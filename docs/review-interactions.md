# Interaction reach and rail bearings

Underwater, Return, Horizons and Covenants now try the existing A targets first.
If none accepts A, they accept a target6–26px forward and at most10px to the
side, without the former `side <= forward/2` taper. Existing valid targets retain
their priority over newly reachable adjacent targets. Targets behind the player
and outside the bounds remain inactive. Invitation/reset confirmations use the
same facing reach, so a newly accepted off-axis approach can finish its second A;
turning away, leaving or cancelling still clears the prompt.

This only changes A target selection. Companion cast ownership, effect overlap,
ray/obstruction checks, cooldowns and directional power geometry are unchanged.
Old-town overlays retain their original target bounds. The temporary fallback
flag is cleared before every public interaction return and is never serialized.

The four `*_game_target_hint(int *x,int *y)` APIs provide read-only ordinary A
focus for the renderer. They share the exact reach predicate and strict-first
ordering; they do not invoke interaction, offer, claim, clear-prompt, or tick
functions. Hidden branch props, modal/pending-job states, and walking-door
targets do not acquire floating A icons. Work projections expose only their
visible controls. Original Underwater/Return active trial boards retain their
existing specialized markings rather than ordinary NPC hints.

The parent integration paints the existing8px `OBJ_HINT` at the returned world
coordinate during normal play, prioritizing shop hints and hiding prompts during
the quick picker and scene/modal presentation. This worktree provides/query-tests
the API; it intentionally leaves the shared `game.c` integration to its owner.

Northern junctions in room23 and rooms26–28 have a persistent signed arrow just
outside their existing16px actor. N/S and E/W now remain distinguishable after
the toast expires. The arrow follows camera translation. It uses existing
palette and line primitives, adds no OBJ tiles/actors, and leaves the binary
boss couplings and puzzle rules unchanged. All new production helpers are COLD.

## Host checks

Run from the repository root:

```sh
python3 tests/test_north_game.py
python3 tests/test_underwater_game.py
UNDERWATER_WORLD_POWERS=1 python3 tests/test_underwater_game.py
python3 tests/test_return_world.py
python3 tests/test_horizons_world.py
python3 tests/test_covenants_world.py
```

Passing first batch: Northern14, Underwater19, Return13, Horizons17, Covenants21,
plus the Underwater real-power mode19. The hint follow-up adds one passing test
per late region: Underwater21 (including disappearing claimed sources), Return14,
Horizons19, Covenants22. Horizons practice focus additionally shares the actual
command/qualified-trial eligibility predicate; wrong inherited commands and
missing qualification never advertise an inactive exhibit. New checks cover off-axis A success, outside/behind
rejection, reset/invitation retention and cancellation, all four stable rail
outputs, camera translation, and the room70 steward/manual precedence case.
Hint tests also assert repeated queries preserve save/quest data, settings,
confirmation/proof state and event queues, and suppress hidden/modal targets.
World fixtures are synthetic host positions and typed jobs; they are not earned
campaign acquisition evidence. Harness portability preserves transaction failure
injection on Apple ld, whose default shared-library link checks remain strict.

An additional Northern UBSan run stopped in unchanged `save5.c:1000` at
`scan.collection + p - 96`: the intermediate pointer is outside its array before
subtracting96. This pre-existing save-loader issue was reported to the save owner;
it is not fixed here. Two supplemental older power harnesses cannot link on macOS
because of absent weak-hook stubs; the changed world suites, real Underwater
power mode and native probes do run. Do not call those blocked checks passed.

## Native diagnostics and acceptance strategy

`tests/interaction_readability_native.py` cold Continues a copied, authenticated
controller-earned SRAM boundary, then issues ordinary controller inputs only.
It validates the producer report/save and current candidate source manifest;
the strict native bridge blocks RAM writes and machine-state imports. Each
changed-ROM import is explicitly a diagnostic, never fresh candidate acceptance.
Producer saves are verified unchanged at completion.

Example (use new output directories and the appropriate producer snapshot):

```sh
python3 tests/interaction_readability_native.py \
  --candidate build --bridge /path/to/review-player-bridge.so \
  --source-report /path/to/earned/regions/report.json \
  --source-snapshot north-north-main-after-continue \
  --case rails --output build/interaction-native-rails
```

Other cases are `underwater`, `return`, `horizons`, and `covenants`. Use their
corresponding earned main checkpoints; Covenants uses its chapter welcome.
For an integrated renderer build, add `--check-prompts`. It reads hardware OAM
to require exactly one existing A glyph at the actual target, checks dialogue
and quick-picker suppression, and verifies that the regional merchant retains
its single cue and opens the shop with A. Other recruitment notices use the same
glyph and are recorded separately rather than being counted as duplicate focus.
`--source-root` can authenticate an immutable source copy matching the candidate.

The implementation pass produced passing, visually inspected240×160 captures:

| Local output | Observed controller evidence |
|---|---|
| `build/interaction-native-rails-v4/regions` | Four signed bearings in room26 after180 quiet frames, no toast; real command turns;2,527frames |
| `build/interaction-native-underwater/regions` | Room46 hollow plaque: player136/118, forward14/side8, A dialogue;712frames |
| `build/interaction-native-return/regions` | Room54 sign: player263/253, forward13/side9, A dialogue;944frames |
| `build/interaction-native-horizons/regions` | Room62 handle: off-axis A changes actual setting;799frames |
| `build/interaction-native-covenants/regions` | Room70 steward: player121/259, forward13/side7, A dialogue;676frames |

Each approach is outside the former taper but inside the new bounds. Across
5,658diagnostic hardware frames: zero active update/flip misses, active overruns
or native faults. Cold-load cost is reported separately. Earlier rail-script
development attempts used the exterior with live enemies and failed from damage;
only the successful v4 interior record is the four-bearing diagnostic.

The parent renderer was inspected read-only at pinned commit `2049e1405ec09885a8cffdec6ac1067e3a725406`.
The ROM, ELF, symbols and source manifest were copied to `build/pinned-2049`;
all 2,954 runtime paths matched that commit's immutable Git blobs and the
manifest. Its ROM SHA-256 is
`8b64f8f9abc17e3419c55d0f579526ef175fe761306330f118ba3ea96c2b9228`.
The dispatch is COLD, queries one active late region, uses the existing 8px
glyph once, and yields to the shop, quick picker, scene and modal guards.
Integrated captures confirm the actual target cue, its disappearance during
dialogue/quick-picker overlays, shop priority, and all four stable rail bearings.
The separately visible Horizons source recruitment notice is not a second
ordinary target. Camera motion is allowed to settle before exact OAM-coordinate
checks because the publication pipeline displays the prior camera frame.

| Integrated diagnostic under `build/` | Hardware frames |
|---|---:|
| `integrated-2049-rails/regions` | 2,652 |
| `integrated-2049-underwater-complete/regions` | 1,145 |
| `integrated-2049-return-complete/regions` | 1,188 |
| `integrated-2049-horizons-complete/regions` | 1,023 |
| `integrated-2049-covenants-complete/regions` | 941 |

All five pass: 6,949 hardware frames, zero active update/flip misses, active
overruns or native faults. Producer SRAM hashes remain unchanged. Failed earlier
helper-development runs (missing bitmap tile base, counting unrelated recruit
notices, and checking before camera publication settled) are not acceptance
evidence and revealed no candidate runtime defect.

This integrated pin predates the disappearing-source and practice-eligibility
follow-up commits. Those corrections have passing focused host coverage; the
parent's newly pinned whole-build acceptance is still required. These captures
remain cross-ROM compatibility diagnostics from earned SRAM, with one explicitly
reported historical progress import per run and zero RAM writes or machine-state
imports. They must not be presented as fresh empty-SRAM acceptance.

Fresh integrated acceptance must still start with empty SRAM, run the full main
journey, and measure the whole merged build. Include Return trial ownership,
Horizons public assembly, Covenants last-watch/homecoming and cold Continue.
The focused probes do not cover every optional target/edge, full collection,
manual player feel, or physical GBA behavior. Room23 camera behavior is covered
by the host drawing test; the four-bearing native set is room26.

## Resource receipt

Official ARM14.2.Rel1 scoped build succeeds with linker assertions. First batch
ROM:32,194,920bytes, +712bytes versus `cc5e88e`. With read-only hint APIs it is
32,198,960bytes (+4,752bytes versus baseline), including claimed-source visibility
and exact practice eligibility.
IWRAM code stays0x6ea8:344bytes of
reserved code margin remain. Allocated BSS adds16bytes; initialized data is
unchanged. Existing OBJ allocation is unchanged, preserving its128byte margin.
No music, save-format, catalog, generated sprite or shared renderer change.
