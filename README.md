# Adventure Legends: Emberbond — 灯の契約

An original Game Boy Advance action-adventure about a small light and the companions who travel beside you.

The complete adventure has 78 areas, 128 companion forms across 60 families,
48 equipment items and 64 global quests. This release brings 23 original regional
music cues, individual companion collection browsing, equipment previews and
lasting boss treasures, connected roads, native GBJ text and ending credits.
See [music and reproduction](README_MUSIC.md) and [source publication](docs/PUBLICATION.md).

The world fills the native 240×160 screen with floating corner controls. No commercial-game ROM or extracted game assets are needed. [日本語の遊び方、ネタバレなし](docs/PLAY_JA.md)

## Start playing

Open `emberbond.gba` in [mGBA](https://mgba.io/) or another accurate GBA emulator and set your keyboard/controller mapping. At the title, Up/Down chooses and A confirms. Choose Continue for an existing save; Start also starts or continues directly. New Adventure opens with a short village story: release the title button, then use fresh A presses to advance or Start to skip. Continue resumes without replaying it. The first save starts after the opening finishes.

| Button | In the world |
| --- | --- |
| D-pad | Move and face; follow roads across map boundaries and walk through doors/stairs |
| A | Attack, talk or examine; hold and release to fire a bow |
| B | Call or recall your companion |
| Hold L + D-pad, release L | Choose a quick-slot companion; B cancels |
| Tap L | Cycle assigned companions with a short tap |
| R | Your summoned companion's selected power |
| Start | Open or close the menu |
| Select | Unused |

People and puzzles use A. Exterior roads connect at the north, south, east or west boundary of the map. On a scrolling map, the edge of the current camera view is not a map exit. Walk through building doors and stairs where the scenery leads into them. Closed routes show a visible barrier and a brief hint without opening a dialogue. Deliberately talking to people and examining objects still uses A. Area names appear on arrival; the corner companion bar shows power recovery.

## Choose a menu, then press A

Start opens Items & Money, Equipment, Party, Skills & Evolution, Map, Quests, Controls, and Return to Adventure. Use all four directions to browse the hub and A to enter. B goes back one level; Start closes. Directional browsing repeats while held; A confirms on a fresh press.

- Equipment: Left/Right chooses the body part; Up/Down previews its items; A equips. Choose the explicit removal entry and A to remove it. Removing a weapon returns to the protected starter sword
- Party: the `001/072` indicator means individual 1 of 72 owned companions; `No.001` is that individual’s stable storage number, retained through evolution. `枠1` means currently assigned to slot 1; `控え` means in reserve. Empty shows `000/072` and is not included in the owned count. Left/Right chooses a slot; Up/Down browses owned companions or Empty; A opens its description, then a second A assigns or swaps. Empty followed by A clears a slot. One companion must remain, and only one legendary may be active. No owned companion is released or duplicated
- Skills & Evolution: view the companion selected with L in the field. Up/Down chooses command or evolution. Left/Right previews learned commands; A opens an explanation, then a second A selects. Up/Down in the explanation switches combat/field help. Recovery is shown in active-play updates, which pause in menus. Choose Evolve with A at a resting place when ready, compare the new form’s phase, saved polarity and role, then confirm separately with a fresh A. B cancels; alternative forms use Left/Right
- Quests: choose a region with A, then a named request with A to open its clues. B returns through the request list, region list and hub. Map opens at the current place. Up/Down examines exits, A opens known places, Left/Right chooses a known region, and A inspects the chosen place. B returns one step. Undiscovered detours remain unnamed

Previewing changes nothing until A. Equipping never heals. Finish an attack, recovery or live arrow before changing equipment. Attack and defense use game stat points; health is in hearts; ordinary walking speed is indexed at 100.0. The arrows compare current and selected equipment after active treasure effects and caps. Companion recovery is approximate active-play seconds for the selected command; a smaller value is faster. Weapon reach is the ordinary opening attack in pixels, and stagger applies to ordinary enemies. Recovery gear affects future companion uses without restarting a timer already running.

Hold L for the familiar Up/Right/Down/Left four-slot picker and release L to switch. A summoned companion is replaced immediately; an uncalled one stays uncalled. A short tap cycles assigned companions. Looking for longer without choosing keeps the current companion. After B cancels, release L before reopening.

Menus and the picker pause the world and power recovery. Viewing preserves an ongoing attempt; actually changing an individual, command or party can require that companion's action to be started again. Evolution changes the same individual, preserves familiar field powers and may be deferred. Completed evolution cannot be reversed.

Swords link three cuts, lances make a narrow longer thrust and bows can be charged. Opening a menu or the field picker cancels an unfired bow draw.

## Money, supplies and treasures

Combat briefly shows the EXP actually awarded and the G actually earned. The notice waits while menus, dialogue or the held-L picker cover it, so opening a pause menu does not use up its display time. Check your wallet under Items & Money or at the first village's shop. The A symbol appears when the village shopkeeper is in talking range. Talk with A, browse with Up/Down (hold to repeat), and use A to review and confirm a purchase. B cancels. Prices, owned quantities and the selected effect are shown together; controls remain visible after a refusal.

Heart Tonic restores two hearts. Spirit Tonic clears the companion power's current wait. Iron Edge is a one-time permanent +4 attack-point upgrade. Select a supply in Items & Money and confirm with A. Full health or an already-ready power prevents needless consumption.

The three original-chapter bosses and four later main-boss reports award money and unique permanent treasures. The receipt explains the effect and shows the G actually credited; later reports also show any actual earned EXP. A continues, B closes. Owned treasures work automatically without equipment slots or bag space, and their effects can be checked in Items. Undiscovered names stay hidden. For an older completed adventure, the village shop highlights a missing-gift entry; review and confirm with A. The original report point can also deliver a missing gift. Each treasure and its money can be collected once. Loading alone claims nothing, and recovery does not replay quest EXP or refill health.

## Save and continue safely

Progress saves automatically. Routine travel and combat saves use a small indicator while play continues. Some purchases, equipment changes and important rewards wait for recording to finish. Let saving finish before closing the emulator.

On failure, the last successful record remains. Open Start → Controls → A Retry save and retry before quitting. The failure clears only after success. After defeat, A retries; completed progress and owned companions remain.

Before upgrading, copy the ordinary `.sav` as a backup. Match ROM/save basenames, such as `emberbond.gba` and `emberbond.sav`, choose Continue with A, and wait for loading. Transfer ordinary SRAM across versions, not emulator save states.

This update writes Save5 content revision 11. Ordinary saves from Village Morning G7, Connected Roads C4, Experience Polish P2 and Player Feedback R7 (content10) migrate forward without resetting progress. Supported formats2–4 and Save5 revisions1–9 also migrate. A cold Continue uses the retained safe checkpoint, which can differ from the transient position just after a road crossing. Never open a migrated content11 save in an older ROM; use the untouched pre-upgrade backup when returning to an earlier release.

To intentionally replace progress, select New Adventure with Up/Down and A, then confirm again with A. B or Start cancels the replacement prompt.

## Build

Requires GNU Make, Python 3 and ARM bare-metal GCC. Generated data ships with source, so a ROM build does not require art fonts/Pillow.

- With the official [devkitPro GBA toolchain](https://devkitpro.org/wiki/Getting_Started), set `DEVKITARM` and run `make`
- Or use compatible `arm-none-eabi-gcc` / `arm-none-eabi-objcopy` on PATH
- Or `make ARM_PREFIX=/absolute/path/to/arm-none-eabi-`

Output: `build/emberbond.gba`, plus ELF/map/symbols. [Tool setup](tools/README.md) describes the isolated official Debian packages used in verification.

`make assets` regenerates original graphics, text, creature tables and puzzle data. It explicitly selects the reviewed Connected Roads world successor for the two historical creature-prefix guards; see [the generation contract](assets/connected_roads_legacy_art_contract.README.md). It needs Pillow and the Noto Sans CJK font used by the generator. Generated C arrays remain in bounded include chunks; do not combine them into huge monolithic files.

## Test and capture

Install the documented Linux mGBA dependencies and build the native bridge with
`./tools/build_mgba_bridge.sh`; `make test-tools` checks that bridge. The pinned
isolated dependency layout is documented in [tools/README.md](tools/README.md).
Tests that use native mGBA require those local tools; they are not bundled binaries.

`make test` runs the equipment/treasure host aggregate and retained gameplay,
menu, economy, migration, geometry and save interruption checks. Specialized
current checks include:

    python3 tests/test_companion_browsing.py
    python3 tests/test_ending_credits_host.py
    python3 tests/test_gbj_font.py
    python3 tests/test_horizons_audio.py

Native scripts under tests execute the actual ROM in mGBA. Run their `--help`
for explicit ROM/symbol hashes, output and dependency options. Start every run
in a fresh output directory with the matching ROM, ELF and symbols. Synthetic
late-game preparation is distinct from controller-earned travel. Host passes
do not establish native timing, physical hardware behavior or a complete fresh
78-room campaign.

Older scripts target their historical releases and may require archived
producer evidence. See [publication scope](docs/PUBLICATION.md) before treating
those scripts or old reports as current release acceptance. A clean forced
build must reproduce the accepted ROM hash; source hashes alone cannot prove
that reused build objects were current.

`python3 tools/package_source.py` produces a deterministic source ZIP. Generated
C arrays stay in bounded include chunks. Build outputs, ordinary runtime saves
and compiled dependencies are excluded.

## Credits and limits

Project licensing is recorded in LICENSE. The original project world, characters, code-native pixel art and original regional music are credited in the ending roll. Third-party GBJ, Noto and DejaVu fonts retain their separate usage permissions and license notices; see assets/fonts. Handheld top-down adventures inspire readability and movement; no Nintendo characters, maps, music or extracted game art are included. The standard cartridge boot-identification header is included for GBA compatibility.

Physical GBA hardware, flash cartridges, other emulator/compiler releases and
the macOS native bridge-build path are unverified. Source/signal checks and
emulator capture do not establish subjective listening quality. There is no
hosted CI configured; local verification is required before merging.

## GBJ font successor

GBJ / GBJ-Slim by **GeeBee**: https://geebeegb.itch.io/gbj. Both official atlas/config pairs are included untouched. The GBA pipeline precompiles their native pixels into UiRuns; no GB Studio engine is required. All story, menu, map, companion, gear and treasure labels use GBJ where available. Kanji and unsupported symbols use Noto Sans CJK Bold at 10px; lowercase uses DejaVu Sans at 8px. Existing compact dynamic stat digits and the authored title wordmark are intentionally retained to preserve narrow numeric cells and performance. See [font provenance and usage](assets/fonts/gbj/README.md).

Regenerate font text only with `make font-assets` (Pillow, fonts-noto-cjk, fonts-dejavu-core required); `make assets` also includes it through the existing individual generators. Native GBJ glyphs are never rescaled. Existing text IDs and vertical layout boxes are retained. All contributor, asset and tool credits, including GeeBee and the official URL, appear only in the ending roll. Source legal notices remain bundled. The title has no author-credit footer.

After the ending card, the credits scroll automatically once controls are released; A starts them sooner. B or Start returns to the village. The final thanks screen waits for A to replay the roll or B/Start to return. With a completed save, open the journal, choose Quests, select the first/current-journey entry, then press A on its ending-replay prompt. Replay never resets progress or requests another save.
