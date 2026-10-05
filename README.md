# Adventure Legends: Emberbond — 灯の契約

An original native Game Boy Advance action-adventure in active development. This milestone adds a continuous scrolling grove, optional discoveries and richer combat to the first playable chapter. It includes Japanese dialogue, original bright pixel art, hardware sprite animation, PSG audio and persistent SRAM checkpoints.

The build is a real `.gba` ROM, not a browser recreation. The finite completion plan is in [ROADMAP.md](docs/ROADMAP.md); additional dungeon/companion arcs and the final campaign ending are still ahead.

## Play

Open `emberbond.gba` in [mGBA](https://mgba.io/) or another accurate GBA emulator. Configure the emulator's keyboard/gamepad mappings as needed. No commercial-game ROM or extracted assets are required. [日本語の遊び方](docs/PLAY_JA.md)

| GBA button | Action |
| --- | --- |
| D-pad | Move / face; diagonal speed is normalized |
| A | Sword / interact / advance dialogue; successive attacks chain into a stronger third strike |
| B | Summon or recall the selected companion; close the journal |
| L | Switch Homura (fire fox) / Midori (nature spirit) |
| R | Use the summoned companion's power |
| Select, while playing | Collision-safe dodge roll with a cooldown |
| Start | Open / close the quest and controls journal |
| A, in journal | Switch map / controls; the map is available in the grove |
| Start, title | New game or continue checkpoint |
| Select, title | Fresh adventure, replacing previous progress |

Fire lights braziers, attacks enemies and exposes the guardian's armored core. Nature grows the river bridge, pushes nearby foes and heals a heart when its longer healing cooldown is ready. Powers share a short cooldown, including after companion changes.

### First-chapter route and discoveries

1. Read the elder's introduction, then leave the village to the north
2. Explore the 480×320 grove. The campfire west of the southern path heals and records a checkpoint when you press A nearby
3. Follow the center path to the river. Summon Midori and use R from the bank to grow the crossing
4. Across the river, the west path leads to an optional chest that permanently adds two hearts. The northeast path leads to the temple
5. Use Homura near both temple braziers, allowing the ability cooldown to recover. Sword attacks and dodge help handle nearby enemies
6. Enter the north gate. Break the guardian's armor with Homura, then strike its exposed core with the sword. Keep outside contact range, and repeat after the armor reforms
7. If defeated, press A to retry with full health. Grove retries/continues use an activated campfire; ordinary area transitions keep their physical entrances

Ranged seed-spitters visibly charge for 30 updates before firing toward your earlier position. Their aim locks during the warning, so movement and dodge are useful. The third sword strike has extra range/damage; holding one button is not an automatic combo.

Progress saves at area transitions, puzzle completion, the campfire and the optional chest. Keep the emulator's `.sav` file beside the ROM. Save format 3 loads the published format 2 and migrates it on continue. An already completed old chapter still opens its ending; a later campaign milestone will migrate chapter completion into continuing story progress.

## Build

Requires GNU Make, Python 3 and ARM bare-metal GCC. The checked-in generated C data allows ROM builds without art-generation dependencies.

- Use the official [devkitPro GBA toolchain](https://devkitpro.org/wiki/Getting_Started), set `DEVKITARM`, and run `make`
- Or use compatible `arm-none-eabi-gcc` / `arm-none-eabi-objcopy` on PATH
- Or run `make ARM_PREFIX=/absolute/path/to/arm-none-eabi-`

Output: `build/emberbond.gba`, plus matching ELF/map/symbol files. `make clean` removes build products only. [Tool setup](tools/README.md) documents the isolated official Debian compiler/mGBA packages used for verification.

`make assets` regenerates original art, text and world data. It needs Pillow and Noto Sans CJK at the font path in `assets/generate_ui.py`. Generated pixel data remains in deterministic small `src/asset_data/` and `src/world_data/` includes; do not replace them with a large monolithic source file.

## Test

Install native mGBA development headers/library and Pillow, then:

```sh
make
./tools/build_mgba_bridge.sh
make test
make test-tools
```

`make test` covers the full journey, independent edge cases, frame pacing and exploration. Normal gameplay checks use actual GBA buttons and read-only symbol inspection, not injected game progress. Optional video recording needs ffmpeg:

```sh
make gameplay-video
python3 tests/capture_milestone_video.py
```

## Verified milestone

- 20 full-journey checks, 19 independent edge checks and 74 exploration checks pass
- All 19 measured cadence scenes pass, including four moving-camera/companion/sword/projectile/roll windows
- The four scrolling stress windows produced 1,440 updates and 1,440 presentations in 1,440 GBA frames (~59.73 Hz)
- Worst sampled scrolling update/render cost is 44.6% of one hardware frame, before OAM commit
- All four viewport alignments match the source atlas exactly; authentic older SRAM saves migrate correctly

[Verification](docs/VERIFICATION.md) gives hashes, scope and reproduction. These are representative mGBA measurements, not an exhaustive timing proof or physical-hardware certification.

## Project layout

- `src/game.c`: gameplay, camera, cached bitmap renderer, hardware objects, audio, input and save handling
- `src/startup.s`, `linker.ld`: ARM7TDMI startup and cartridge memory layout
- `src/assets.*`, `src/asset_data/`: original room/sprite/palette data
- `src/world.*`, `src/world_data/`: continuous grove, collision data, props and even/odd viewport atlases
- `src/ui.*`: Japanese text masks
- `assets/`: editable generators, manifests, art previews and route proofs
- `tools/`: cartridge header utility and actual mGBA-core automation
- `tests/`: controller-only gameplay, exploration, migration and performance checks
- `docs/`: architecture, player guide, measured evidence and completion roadmap

## Scope and credits

Original world, story, characters, artwork, tune and code, under the repository's existing Apache license. The high-level visual/motion reference is handheld top-down adventures; no Nintendo characters, maps, music or extracted game assets are included. The standard boot-identification header is used for GBA cartridge compatibility.

This remains the first chapter: four areas including one scrolling grove, two companions and one dungeon boss. Physical GBA hardware, flash cartridges, other emulators, alternate compiler releases and the macOS bridge-build path have not been tested. More campaign content is in development through separate reviewable milestones.
