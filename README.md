# Adventure Legends: Emberbond — 灯の契約

An original, evolving Game Boy Advance action-adventure about a small light and the companions who travel beside you.

**Tested Underwater milestone, build K.** Full acquisition, minimal lifecycle, independent combat/control and whole-game regression checks pass on the exact ROM below. The game remains in development. Repository publication is paused; packaged delivery has a separate sealed source-export receipt.

The world now fills the native **240×160 screen**, with floating corner controls instead of a permanent menu strip. Explore, choose a sword, lance or bow, call a companion, and pay attention to the little things along the path. Companions can grow, learn new commands and change form through optional personal journeys. You can wait before evolving, and their familiar field powers remain yours.

## Start playing

Open `emberbond.gba` in [mGBA](https://mgba.io/) or another accurate GBA emulator. Set keyboard/controller mappings there and press **Start**. No commercial-game ROM or extracted assets are needed.

| Button | Action |
| --- | --- |
| D-pad | Move and face; diagonals have normalized speed |
| A | Attack, talk or examine; with a bow, hold to aim and release to shoot |
| B | Call/recall your companion; close the journal |
| Hold L + D-pad, release L | Choose a quick-slot companion; B cancels |
| Tap L | Cycle assigned companions (a short tap only) |
| R | Your summoned companion's selected power |
| Select | Dodge |
| Start | Open/close your journal |

Hold **L** for the temporary four-slot selector: **up, right, down, left** match its four slots. Choose a direction and release L to switch. The world and power recovery pause while selecting. A summoned companion is replaced immediately; an uncalled companion stays uncalled. A short L tap still cycles your assigned companions. Looking without choosing for longer leaves the current companion unchanged.

In the journal, **A changes pages**. On the party page, **left/right chooses a slot**, **up/down browses owned companions or an empty slot**, **R assigns/swaps**, and **Select clears a slot**. At least one companion stays assigned. This never releases or duplicates a companion: all owned companions remain available here, including powers you need along the route. Assignments save immediately; field selection is remembered at the next normal checkpoint. The growth page shows level, bond and the next step. **R changes a learned command; Select offers evolution** when its conditions are met at a resting place. Evolution has a separate confirmation and can be deferred. B returns to play.

On the equipment page, **up/down chooses a body slot**, **left/right previews owned gear**, **R equips**, and **Select removes it** (a removed weapon falls back to your starter sword). Attacks, recovery, rolling and your live projectiles must finish before equipment can change. Equipping never restores health. The quest page keeps requests and readable hints together.

Swords link three cuts, lances commit to a narrow longer thrust, and bows can be charged. Roll or open a menu/selector to cancel an un-fired bow draw. Attack/defense are game stat points; health is shown in hearts, and walking speed uses an index with the normal pace at 100. Power recovery depends on the contextual field action or combat command; recovery gear affects future uses without resetting an existing timer.

The corner icon shows B when a companion can be called and R while it is summoned. Its small bar shows power recovery. Area names appear briefly on entry and are available in the journal.

Keep the emulator's `.sav` file. Progress records automatically. A short saving state preserves your progress before reward dialogue continues; world actions pause during that state. Title-screen Select offers a new adventure; a separate A confirmation is required before replacing existing progress. B, Start or Select cancels. Published saves from formats 2–4 and format 5 revisions 1–5 can migrate forward into this version (format 5 content revision 6; unchanged wire layout). Back up your `.sav` before upgrading, and use the same basename for the ROM and save, for example `emberbond.gba` and `emberbond.sav`. Do not use an upgraded save with an older ROM; keep the untouched backup if you need to return to an older build. Cold Continue can take 52 emulated hardware frames before play resumes; wait for the loading transition to finish.

[日本語の遊び方、ネタバレなし](docs/PLAY_JA.md)

## This update: a town beneath the water

- Eight connected new places, with a bright underwater town and a memory archive
- Eight new companion families, 24 forms and 16 optional personal growth paths
- Eight quests, six equipment sidegrades and 24 new field/combat commands
- Sound, buoyancy and visible shapes to explore with your companions
- Reversible mechanisms, readable clues and places to rest or try again
- Forward migration from the delivered Magma save, retaining each real individual

After finishing and reporting the mountain's main request, look for the shell lift in its town. There is no oxygen meter or required breathing equipment. Existing sword, lance, bow, equipment, four-slot selection and optional evolution remain available. A favors nearby conversations and objects; step away from a resting place when you want to fight.

Some powers briefly show a direction hint after **R**. Make a fresh press of the indicated D-pad direction immediately after R; holding a direction beforehand does not choose it. These hints change a power's starting direction or pattern. The journal keeps requests, learned commands and personal-growth clues together.

The player teaser is a continuous 20-second stroll through the opening town with a familiar companion. It contains no new recruitment, evolution, puzzle solutions, rare encounters or ending. Developer data and test reports contain progression spoilers. Audio remains the original PSG ambient phrase and sound effects; no new orchestral soundtrack is included.

## Development status

The Underwater milestone implements **89 obtainable forms in 38 families**, **54 areas**, **37 equipment items** and **46 global quests**. Its completed controller collection route retains **50 actual individuals** and records all 89 forms encountered through growth. Evolution changes an existing individual; a second branch requires another genuine encounter, not a copied creature. This route passes 10,940 checks with no failures; the minimal route passes 761. Independent lifecycle, all 138 top-level combat/control/stress cases, the fresh eight-stage native recipe and full retained regression targets also pass.

The assembled catalog contains **90 authored designs** and reserves 128 stable identities. Of those authored designs, 89 are enabled and one legendary remains disabled. Reserved rows are not playable monsters, and evolved forms count within the 128-form goal. The remaining milestones are 104 forms, 120 ordinary forms, eight legendary forms for 128, then an integrated release. No final campaign length or measured playtime is claimed.

Wood, Fire, Earth, Metal and Water are separate from Yin/Yang polarity. Numerical battle rules are original game design. Full-screen world presentation, normalized diagonal movement, four-slot field switching and original pixel art remain central to the project.

Candidate K is **9,777,176 bytes**, SHA-256 `df3733446cda3d41c2e78da134b25cd446846d6283e4ac5dc47b3fcaa3f98607`. [Underwater verification](docs/VERIFICATION-UNDERWATER.md) records exact-ROM results, their limits and historical evidence. Native timing uses actual emulator hardware-frame updates and displayed pages, never host FPS. Cold Continue is a blocking load transition outside the active-play cadence gate; active play, menus and incremental saving still require one update and one page flip per hardware frame in the measured windows. Physical GBA hardware remains untested.

Developer links, with spoilers: [Roadmap](docs/ROADMAP.md) · [Architecture](docs/ARCHITECTURE.md) · [Underwater verification](docs/VERIFICATION-UNDERWATER.md) · [Underwater runtime](docs/underwater-runtime/ENGINE_HOOKS.md) · [Revision 6 persistence](docs/UNDERWATER_PROGRESS_SAVE6.md) · [Historical Magma verification](docs/VERIFICATION.md) · [Save format](docs/SAVE5.md)

## Build

Requires GNU Make, Python 3 and ARM bare-metal GCC. Generated data ships with source, so a ROM build does not require art fonts/Pillow.

- With the official [devkitPro GBA toolchain](https://devkitpro.org/wiki/Getting_Started), set `DEVKITARM` and run `make`
- Or use compatible `arm-none-eabi-gcc` / `arm-none-eabi-objcopy` on PATH
- Or `make ARM_PREFIX=/absolute/path/to/arm-none-eabi-`

Output: `build/emberbond.gba`, plus ELF/map/symbols. [Tool setup](tools/README.md) describes the isolated official Debian packages used in verification.

`make assets` regenerates original graphics, text, creature tables and puzzle data. It needs Pillow and the Noto Sans CJK font used by the generator. Generated C arrays remain in bounded include chunks; do not combine them into huge monolithic files.

## Test and capture

With mGBA development headers/library and Pillow installed:

```sh
make
./tools/build_mgba_bridge.sh
make test             # retained whole-game regression through Southern
make test-tools
make test-magma       # retained mountain host/native acceptance
make test-underwater  # new chapter hosts and sequenced native acceptance
make gameplay-video  # ffmpeg; spoiler-free Underwater town teaser
```

`make test` retains native-controller journeys, full-screen pixel/OAM checks, older-save migration, fault-injected host persistence tests, earlier personal trials/evolutions, regional quests/collection, Northern and Southern acquisition/combat/control coverage, weapon/gear/phase effects and actual emulated display cadence. Magma and Underwater checks are separate targets below. Synthetic host fixtures are labeled separately from normal controller gameplay. Raw traces are generated under ignored `build/`.

`make test-underwater-host` runs the new chapter's core, history, art, world, localization, save, transaction, power-loss, return and power contracts. `make test-underwater-native` freezes its observer sources, earns a fresh exact-ROM full collection and minimal route, then runs the minimal cold-SRAM lifecycle review, all precision/combat/control/art cases, dense-scenery, moving-power, phase-stress and alternate-aim checks. `make test-underwater` combines both. The exact eight-stage native recipe has passed; see [Underwater verification](docs/VERIFICATION-UNDERWATER.md) for exact results and the separate final-package verification contract. A host-only pass is not release acceptance.

`make test-magma-host` runs the retained mountain core, admission, art, puzzle, evolution, save and power contracts. `make test-magma` runs those hosts plus a fresh collection route, minimal prerequisites, controls, retained-save lifecycle, all new combat commands, pacing and the teaching encounter. `make test-magma-native` selects only that native sequence and archives each producer before dependent checks. `make test-southern` retains the island host, journey, optics, selector, combat and rendering suites. `make test-northern` retains the Northern regression suites; [the QA guide](tests/NORTHERN_QA.md) documents individual commands and provenance. `make gameplay-video` captures the spoiler-free Underwater town stroll with the game's real PSG audio. `make developer-video` produces a spoiler-bearing campaign recording for development review. `python3 tools/package_source.py` makes a deterministic source ZIP and file-integrity manifest. `tools/package_northern_evidence.py` validates and summarizes the archived, hash-pinned N5 reports into bounded public JSON; it is not a test runner and intentionally requires that exact evidence set. `tools/package_southern_evidence.py`, `tools/package_magma_evidence.py` and `tools/package_underwater_evidence.py` accept passing exact-ROM native reports and pin their full bytes while producing bounded summaries; the release checklist separately verifies complete suite coverage.

## Credits and limits

Original world, characters, pixel art, story, music and code, under the repository's Apache license. Handheld top-down adventures inspire readability and movement; no Nintendo characters, maps, music or extracted game art are included. The standard cartridge boot-identification header is included for GBA compatibility.

Physical GBA hardware, flash cartridges, other emulator/compiler releases and the macOS native bridge-build path are not yet verified. Cold checkpoint decoding is a blocking load transition, distinct from the measured steady gameplay and incremental-save cadence. The original 2 MiB chapter-growth target was exceeded; the revised engineering budget is 2.5 MiB, within the 32 MiB cartridge limit. Only 240 bytes separate IWRAM code from the reserved SYSTEM stack floor, so future content and audio changes must repeat resource and pacing tests. Canary observations are not an exhaustive maximum-stack or hardware-safety proof. There is no hosted CI configured yet. Underwater repository publication is paused; this candidate makes no PR or merge claim.
