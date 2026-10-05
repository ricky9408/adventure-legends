# Adventure Legends: Emberbond — 灯の契約

An original, evolving Game Boy Advance action-adventure about a small light and the companions who travel beside you.

The world now fills the native **240×160 screen**, with floating corner controls instead of a permanent menu strip. Explore, fight with your sword, call a companion, and pay attention to the little things along the path. Companions can grow, learn new commands and change form through optional personal journeys. You can wait before evolving, and their familiar field powers remain yours.

## Start playing

Open `emberbond.gba` in [mGBA](https://mgba.io/) or another accurate GBA emulator. Set keyboard/controller mappings there and press **Start**. No commercial-game ROM or extracted assets are needed.

| Button | Action |
| --- | --- |
| D-pad | Move and face; diagonals have normalized speed |
| A | Sword, talk, examine, advance dialogue; successive strikes form a three-hit chain |
| B | Call/recall your companion; close the journal |
| Hold L + D-pad, release L | Choose a quick-slot companion; B cancels |
| Tap L | Cycle assigned companions (a short tap only) |
| R | Your summoned companion's selected power |
| Select | Dodge |
| Start | Open/close your journal |

Hold **L** for the temporary four-slot selector: **up, right, down, left** match its four slots. Choose a direction and release L to switch. The world and power recovery pause while selecting. A summoned companion is replaced immediately; an uncalled companion stays uncalled. A short L tap still cycles your assigned companions. Looking without choosing for longer leaves the current companion unchanged.

In the journal, **A changes pages**. On the party page, **left/right chooses a slot**, **up/down browses owned companions or an empty slot**, **R assigns/swaps**, and **Select clears a slot**. At least one companion stays assigned. This never releases or duplicates a companion: all owned companions remain available here, including powers you need along the route. Assignments save immediately; field selection is remembered at the next normal checkpoint. The growth page shows level, bond and the next step. **R changes a learned command; Select offers evolution** when its conditions are met at a resting place. Evolution has a separate confirmation and can be deferred. B returns to play.

The corner icon shows B when a companion can be called and R while it is summoned. Its small bar shows power recovery. Area names appear briefly on entry and are available in the journal.

Keep the emulator's `.sav` file. Progress records automatically. A short saving state preserves your progress before reward dialogue continues; world actions pause during that state. Title-screen Select starts a new adventure and replaces prior progress. Published saves from formats 2–4 continue into this version; keep a backup before returning to an older ROM, which cannot see new format-5 progress.

[日本語の遊び方、ネタバレなし](docs/PLAY_JA.md)

## This update

- Hold-L cross selector with direct summoned-companion replacement
- Journal party assignments from actual owned companions, including swaps and empty slots

- Full-screen exploration with a compact floating HUD
- Optional companion growth, explicit evolution choices and retained familiar commands
- New personal discoveries and resettable environmental puzzles
- More distinctive field/combat powers and readable movement tradeoffs
- Transactional save upgrades, older-save migration, interruption recovery and repeat-reward protection

The player preview and default video show only opening areas. Technical tests, source data and developer guides contain spoilers.

## Development status

The current ROM has **8 implemented, obtainable and controller-verified forms**, four assignable quick-companion slots, 16 areas, three story dungeon arcs and optional personal trials. The broader requested game is still in development: the 128-form roster, equipment/weapon variety, regional towns and a larger quest campaign are not claimed as finished.

The catalog reserves 128 stable identities and has 12 authored designs. Only eight are enabled. Five-phase/polarity definitions and matchup reference rules exist; numerical phase battle modifiers are not yet applied to the legacy combat encounters. There is no claim that 128 reserved rows are 128 playable monsters.

[Roadmap](docs/ROADMAP.md) · [Architecture](docs/ARCHITECTURE.md) · [Verification](docs/VERIFICATION.md) · [Save format](docs/SAVE5.md)

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
make test
make test-tools
make gameplay-video  # ffmpeg; spoiler-free player teaser
```

`make test` includes native-controller journeys, full-screen pixel/OAM checks, older-save migration, fault-injected host persistence tests, personal trials, all enabled evolutions, command effects and actual emulated display cadence. Synthetic host fixtures are labeled separately from normal controller gameplay. Raw traces are generated under ignored `build/`.

`make developer-video` produces a spoiler-bearing campaign recording for development review. `python3 tools/package_source.py` makes a deterministic source ZIP and file-integrity manifest.

## Credits and limits

Original world, characters, pixel art, story, music and code, under the repository's Apache license. Handheld top-down adventures inspire readability and movement; no Nintendo characters, maps, music or extracted game art are included. The standard cartridge boot-identification header is included for GBA compatibility.

Physical GBA hardware, flash cartridges, other emulator/compiler releases and the macOS native bridge-build path are not yet verified. Cold checkpoint decoding is a short blocking load transition, distinct from the measured steady gameplay and incremental-save cadence. There is no hosted CI configured yet.
