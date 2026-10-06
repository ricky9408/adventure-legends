# Adventure Legends: Emberbond — 灯の契約

An original, evolving Game Boy Advance action-adventure about a small light and the companions who travel beside you.

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

Keep the emulator's `.sav` file. Progress records automatically. A short saving state preserves your progress before reward dialogue continues; world actions pause during that state. Title-screen Select offers a new adventure; a separate A confirmation is required before replacing existing progress. B, Start or Select cancels. Published saves from formats 2–4 and format 5 revisions 1–4 continue into this version (format 5 content revision 5). Back up your `.sav` before upgrading or returning to an older ROM: older builds cannot understand the new equipment, quests and recruits.

[日本語の遊び方、ネタバレなし](docs/PLAY_JA.md)

## This update: the mountain beyond the islands

- Eight connected new places and a bright mountain community with its own stories
- Nine new companion families, including three-stage growth and genuinely different branch choices
- Eight quests, six equipment sidegrades and twenty-four new field/combat commands
- Movable-object puzzles, companion-powered paths and little discoveries to return for
- An explicit left/right evolution choice; B lets you wait without changing your companion
- Forward migration from the delivered Southern save, retaining each real individual

After finishing the Southern main journey, look for the lift in its opening town. In the mountain chapter, **A grabs a movable object, a fresh D-pad press slides it, and A or B releases it**. A favors nearby conversations and objects; step away from a resting place when you want to fight. Hints and requests remain in the journal.

The player teaser is a continuous 20-second opening-town stroll with a familiar companion. It contains no new recruitment, evolution, puzzle solutions, secret routes, boss or ending. Developer data and test reports contain progression spoilers. Audio is still the original PSG ambient phrase and sound effects; no new orchestral soundtrack is included.

## Development status

The Magma milestone implements **65 obtainable forms in 30 families**, **46 areas**, **31 equipment items** and **38 global quests**. Its completed controller collection route retains **34 actual individuals** to cover both branches without replacing old companions. Evolution changes an existing individual; a second branch requires another genuine encounter, not a copied creature.

The catalog reserves 128 stable identities and contains 66 authored designs. 65 are enabled; the authored legendary remains disabled. The underwater chapter, remaining return journeys and legendary progression are still in development. Reserved rows are not playable monsters, and evolved forms count within the 128-form goal. No final campaign length is claimed.

Wood, Fire, Earth, Metal and Water are separate from Yin/Yang polarity. Numerical battle rules are original game design. Full-screen world presentation, normalized diagonal movement, four-slot field switching and original pixel art remain central to the project.

The tested ROM is 7,495,920 bytes, SHA-256 `90ba47f30a0c94c28f073d26cc31ac5f5c736eb4d6e704d090892d2776f1ffb2`. Final same-ROM collection and regression checks are recorded in the verification guide. Native timing measures actual emulator hardware-frame updates and displayed pages, never host FPS. Cold-menu margins remain limited; future content/music changes must repeat pacing tests. Physical GBA hardware remains untested.

Developer links, with spoilers: [Roadmap](docs/ROADMAP.md) · [Architecture](docs/ARCHITECTURE.md) · [Verification](docs/VERIFICATION.md) · [Magma chapter](docs/magma-runtime/HANDOFF.md) · [Save format](docs/SAVE5.md)

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
make test-magma       # new chapter host and complete native acceptance
make gameplay-video  # ffmpeg; spoiler-free player teaser
```

`make test` retains native-controller journeys, full-screen pixel/OAM checks, older-save migration, fault-injected host persistence tests, earlier personal trials/evolutions, regional quests/collection, Northern and Southern acquisition/combat/control coverage, weapon/gear/phase effects and actual emulated display cadence. The new Magma acceptance is a separate target below. Synthetic host fixtures are labeled separately from normal controller gameplay. Raw traces are generated under ignored `build/`.

`make test-magma-host` runs the current core, admission, art, puzzle, evolution, save and power contracts. `make test-magma` runs those hosts plus a fresh collection route, minimal prerequisites, controls, retained-save lifecycle, all new combat commands, pacing and the teaching encounter. `make test-magma-native` selects only that native sequence and archives each producer before dependent checks. `make test-southern` retains the island host, journey, optics, selector, combat and rendering suites. `make test-northern` retains the Northern regression suites; [the QA guide](tests/NORTHERN_QA.md) documents individual commands and provenance. `make developer-video` produces a spoiler-bearing campaign recording for development review. `python3 tools/package_source.py` makes a deterministic source ZIP and file-integrity manifest. `tools/package_northern_evidence.py` validates and summarizes the archived, hash-pinned N5 reports into bounded public JSON; it is not a test runner and intentionally requires that exact evidence set. `tools/package_southern_evidence.py` and `tools/package_magma_evidence.py` accept passing exact-ROM native reports and pin their full bytes while producing bounded summaries; the release checklist separately verifies complete suite coverage.

## Credits and limits

Original world, characters, pixel art, story, music and code, under the repository's Apache license. Handheld top-down adventures inspire readability and movement; no Nintendo characters, maps, music or extracted game art are included. The standard cartridge boot-identification header is included for GBA compatibility.

Physical GBA hardware, flash cartridges, other emulator/compiler releases and the macOS native bridge-build path are not yet verified. Cold checkpoint decoding is a short blocking load transition, distinct from the measured steady gameplay and incremental-save cadence. There is no hosted CI configured yet.
