# Adventure Legends: Emberbond — 灯の契約

An original, playable Game Boy Advance action-adventure vertical slice. Explore a lantern village, cross a forest river with a summoned nature spirit, light an ancient temple with a fire fox, and free the grove guardian through sword combat.

The game is a **native `.gba` ROM**, not a browser imitation. It runs at the GBA's 240 × 160 resolution with cached indexed-palette backgrounds, hardware OBJ sprites, original pixel art, Japanese dialogue, PSG music/sound effects, and SRAM checkpoints.

## Play

Open `emberbond.gba` in [mGBA](https://mgba.io/) or another accurate Game Boy Advance emulator. No commercial game ROM or extracted assets are required. Use your emulator's controller settings to map the GBA buttons to your keyboard or gamepad. [日本語の遊び方](docs/PLAY_JA.md)

| GBA button | Action |
| --- | --- |
| D-pad | Move / face a direction |
| A | Swing sword / talk / advance dialogue |
| B | Summon or recall selected companion |
| L | Switch companion: Homura (fire fox) / Midori (nature spirit) |
| R | Use summoned companion's power |
| Start / Select | Open quest and control guide |
| Start, title screen | New game or continue checkpoint |
| Select, title screen | Start a fresh adventure |

Fire opens braziers and breaks the guardian's armor. Nature grows a bridge and heals one heart when its longer healing cooldown is ready. Companion power has a short shared cooldown. The first dialogue teaches the route; the pause screen always lists the current objective.

### Walkthrough / accessibility

1. Press Start and read the elder's four short dialogue pages with A
2. Walk north from the village
3. At the river, press L to select Midori, B to summon, and R near the central south bank
4. Cross the grown bridge and go north into the temple
5. Press L to select Homura; approach each of the two braziers and press R, allowing the cooldown to recover between uses
6. Enter the opened north gate
7. Use Homura's R power near the guardian to expose its core, then face it and strike with A. Keep a little distance; the sword reaches beyond contact range. Repeat after the armor reforms. Midori can help recover hearts
8. If defeated, press A to retry the current area from a checkpoint with full health

Progress is saved automatically at area transitions and puzzle completion. Keep the emulator's SRAM `.sav` file beside the ROM. This first chapter is intended to be a short, self-contained vertical slice rather than a complete commercial-length adventure.

## Build

A portable freestanding C implementation, requiring GNU Make, Python 3, and an ARM bare-metal GCC toolchain. The checked-in generated art/text C files let you build without installing art-generation dependencies.

- Official [devkitPro GBA toolchain](https://devkitpro.org/wiki/Getting_Started): install `gba-dev`, set `DEVKITARM`, and run `make`
- Or use a compatible `arm-none-eabi-gcc` and `arm-none-eabi-objcopy` on PATH
- Or `make ARM_PREFIX=/absolute/path/to/arm-none-eabi-`

The result is `build/emberbond.gba`; the ELF and map are useful for debugging. `make clean` removes build products only. See `tools/README.md` for the isolated Debian toolchain and real-emulator test setup used in cloud development.

Art is defined in `assets/generate_assets.py`. Japanese text is defined in `assets/generate_ui.py`. Regeneration requires Pillow; text regeneration also uses the SIL Open Font License Noto Sans CJK font installed at the path shown in that script. The ROM contains rasterized text masks, not a redistributed font file.

## Project layout

- `src/game.c`: gameplay, rendering, audio, input, SRAM checkpointing
- `src/startup.s`, `linker.ld`: ARM7TDMI startup and cartridge memory map
- `src/assets.*`: generated original palette, backgrounds and sprites
- `src/ui.*`: generated Japanese UI masks
- `assets/`: editable generators, placement manifest and art previews
- `tools/fix_header.py`: required cartridge header and checksum
- `tools/mgba_runner.py`, `tools/mgba_bridge.c`: actual mGBA-core automation, screenshots and input playback
- `tests/`: repeatable gameplay tests
- `docs/`: build and verification notes

## Scope and credits

Original world, story, characters, artwork, tune and code. The requested inspirations are top-down handheld adventures and field-summoned companions; no Nintendo characters, maps, music or commercial-game assets are included. The standard GBA boot-identification header is included only for cartridge compatibility.

Known scope: four compact areas; two companions; sword; one boss; no inventory economy, multi-dungeon campaign, scrolling overworld, or controller remapping inside the ROM. Emulator verification does not establish physical-cartridge compatibility; that should be tested separately on real hardware.

## Visual and motion polish

The revised renderer uses real GBA hardware sprites, y-sorted depth and shadows, cached background/UI pages, and aligned text writes. Four-frame directional walks, companion-facing poses, normalized Q8 diagonal movement, a small sword lunge, animated sword arcs, hit-stop and impact sparks improve motion without changing the original adventure. Sculpted foliage, roof/eave shadows and foreground canopies add native-pixel depth. A brighter scenery palette gives grass, paths and temple stone a sunnier look while retaining character/UI colors.

In 15 repeatable mGBA scene windows, every hardware frame had one simulation update and one presentation at the GBA's ~59.73 Hz refresh, including boss projectiles and companions. Cold menu rasterization takes at most two frames in the tested transitions. See [performance evidence](docs/perf/README.md) and [design notes](docs/POLISH.md); this is measured test coverage, not a universal physical-hardware guarantee.

Original SRAM checkpoints remain compatible.

## Test

After building the ROM and mGBA bridge:

```sh
make test
python3 tests/review_tests.py
python3 tests/performance_tests.py --strict
make gameplay-video  # optional, also needs ffmpeg
```

The gameplay tests use real emulated button input and read-only inspection of named game symbols. They do not inject game progress into RAM. Results and screenshots are written under `build/qa` and `build/review`; see [verified results](docs/VERIFICATION.md).

Generated pixel data is split into `src/asset_data/part_*.inc` and included by `src/assets.c`. `assets/generate_assets.py` regenerates this layout deterministically. This source packaging does not change ROM data.
