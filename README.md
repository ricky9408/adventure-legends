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

Keep the emulator's `.sav` file. Progress records automatically. A short saving state preserves your progress before reward dialogue continues; world actions pause during that state. Title-screen Select starts a new adventure and replaces prior progress. Published saves from formats 2–4 and the earlier format 5 revision 1 continue into this version. Back up your `.sav` before upgrading or returning to an older ROM: older builds cannot understand the new equipment, quests and recruits.

[日本語の遊び方、ネタバレなし](docs/PLAY_JA.md)

## This update

- A bright, inhabited riverside town and six connected new areas
- Sword, lance and bow, with five equipment slots and 13 earnable items
- Eleven side quests, resettable puzzles and visually hinted discoveries
- New companions, an optional evolution and all five phases active in regional combat
- Continued full-screen exploration and hold-L party switching
- Forward save migration, retained traversal companions and one-time rewards

The player preview and default video show ordinary opening-town play with a starting companion. Source data, test traces and developer guides contain spoilers.

## Development status

The current ROM has **11 implemented, obtainable and controller-verified forms** in six companion families, four assignable quick slots, 22 areas, three original story dungeon arcs, optional personal trials, 13 equipment items and 11 regional quests. All 11 forms have also been obtained in one normally played and reloaded progress file. The larger requested game remains in development.

The catalog reserves 128 stable identities and contains 12 authored designs. Eleven are enabled; the designed legendary is not enabled or obtainable. The remaining regional cultures, full 128-form roster and legendary progression are still ahead. A reserved row is not a playable monster, and an evolved form is counted within the provisional 128-form target.

Wood, Fire, Earth, Metal and Water are separate from Yin/Yang polarity. The numerical battle rules are original game design; the legacy untyped encounters retain their prior balance. Regional enemies display phase markers, and all five controlling matchups are verified in the native ROM.

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

`make test` includes native-controller journeys, full-screen pixel/OAM checks, older-save migration, fault-injected host persistence tests, personal trials, all enabled evolutions, regional quests/collection, weapon/gear/phase effects and actual emulated display cadence. Synthetic host fixtures are labeled separately from normal controller gameplay. Raw traces are generated under ignored `build/`.

`make developer-video` produces a spoiler-bearing campaign recording for development review. `python3 tools/package_source.py` makes a deterministic source ZIP and file-integrity manifest.

## Credits and limits

Original world, characters, pixel art, story, music and code, under the repository's Apache license. Handheld top-down adventures inspire readability and movement; no Nintendo characters, maps, music or extracted game art are included. The standard cartridge boot-identification header is included for GBA compatibility.

Physical GBA hardware, flash cartridges, other emulator/compiler releases and the macOS native bridge-build path are not yet verified. Cold checkpoint decoding is a short blocking load transition, distinct from the measured steady gameplay and incremental-save cadence. There is no hosted CI configured yet.
