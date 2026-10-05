# Adventure Legends: Emberbond — 灯の契約

An original native Game Boy Advance action-adventure in active development. This foundation contains a continuous scrolling grove,14 areas,4 field companions,3 dungeon arcs,3 bosses and a complete first story with a post-ending village. It has Japanese dialogue, bright original pixel art, directional animation, PSG audio and persistent SRAM checkpoints.

The requested larger game is still being built: monster evolution, a 128-form roster, five-phase/polarity systems, equipment, regional towns and side quests are planned in [ROADMAP.md](docs/ROADMAP.md). They are not claimed as implemented by this ROM.

## Play

Open `emberbond.gba` in [mGBA](https://mgba.io/) or another accurate GBA emulator. Configure keyboard/gamepad mappings there. No commercial-game ROM or extracted assets are required. [日本語の遊び方](docs/PLAY_JA.md)

| GBA button | Action |
| --- | --- |
| D-pad | Move/face; diagonal speed is normalized |
| A | Sword/interact/dialogue; successive attacks chain into a stronger third strike |
| B | Summon/recall selected companion; close journal |
| L | Cycle unlocked companions, including while paused |
| R | Summoned companion's power |
| Select, during play | Collision-safe dodge with cooldown |
| Start | Open/close journal |
| A, journal | Cycle objectives/controls, map, companion powers |
| R, completed-game journal | Replay the ending |
| Start, title | New game or continue checkpoint |
| Select, title | Fresh adventure, replacing prior progress |

### Companions and first story

Homura uses fire for projectiles, braziers and armor. Midori grows roots, pushes nearby foes and supplies slower cooldown-limited healing. After the grove guardian, Fuuri joins with wind-driven traversal, projectile clearing and stagger. After the sky guardian, Kohaku joins with stone mechanisms, a pulse and a short one-hit guard. Switching companions does not reset the shared power cooldown.

1. Leave the village north. Grow the grove's river bridge with Midori and find the northeast shrine. Homura lights both braziers and exposes the first guardian
2. Return to the village and interact with the eastern sign. Follow the sky route: wind vanes, a patrol, and two wind relays plus a fire source. Kazane becomes vulnerable to wind during recovery
3. After Kohaku joins, use the village's western stone marker. Open the arch, set weights, uncover the well, grow roots and burn thorns. Activate four power sockets in any order
4. The final core has stone, wind and fire phases. Watch its warnings, use the required power during recovery, then strike. Return to the elder for the story payoff; Start on the ending card returns to peaceful exploration

Optional grove camp/rest, an eight-heart relic and a ridge chime reward exploration. Current puzzles are companion-dependent mechanisms with persistent progress; richer movable-object/clue/quest dungeons and more hidden field discoveries are future milestones.

Progress records at transitions, puzzle completions, rests and rewards. Retrying restores health at a safe entrance or the recorded camp. Save format 4 uses two transactional CRC-protected banks. It loads published formats 2/3 without overwriting their original bytes; an old completed first chapter continues into the new sky route. Keep the emulator's `.sav` file.

## Build

Requires GNU Make, Python 3 and ARM bare-metal GCC. Checked-in generated data permits builds without art-generation dependencies.

- Official [devkitPro GBA toolchain](https://devkitpro.org/wiki/Getting_Started): set `DEVKITARM` and run `make`
- Or compatible `arm-none-eabi-gcc`/`arm-none-eabi-objcopy` on PATH
- Or `make ARM_PREFIX=/absolute/path/to/arm-none-eabi-`

Output: `build/emberbond.gba` plus matching ELF/map/symbols. [Tool setup](tools/README.md) documents the isolated official Debian packages used in verification.

`make assets` regenerates original art, geometry and Japanese text. It needs Pillow and Noto Sans CJK at the generator's documented path. Generated arrays stay in deterministic small includes in `src/asset_data`, `world_data`, `campaign_art_data` and `ui_data`; do not replace them with a giant monolith.

## Test and capture

With native mGBA development headers/library and Pillow:

```sh
make
./tools/build_mgba_bridge.sh
make test
make test-tools
```

The aggregate retains scrolling/combat regressions and adds host serialization tests, full minimal/optional campaign routes and real display-cadence measurements. Ordinary progress uses GBA controls and read-only symbol inspection, never injected game RAM. Save-corruption fixtures are explicitly labeled and separate.

```sh
make gameplay-video  # requires ffmpeg; continuous controller-only campaign + actual audio
```

[Verification](docs/VERIFICATION.md) records exact hashes, coverage and limitations. Frame-rate claims concern actual emulated GBA updates/page presentations, not host emulator throughput.

## Source layout

- `src/game.c`: input, gameplay, camera, compositor, audio and orchestration
- `src/campaign_rules.*`: generated room geometry, mechanisms and dialogue definitions
- `src/save4.*`: transactional save serialization and prior-version migration
- `src/assets.*`, `world.*`, `campaign_art.*`, `ui.*`: generated original graphics/text
- `src/startup.s`, `linker.ld`: cartridge entry and hardware memory budgets
- `assets/`: editable generators, data and visual proofs
- `tests/`: controller-only gameplay/performance, persistence, authentic prior-ROM fixtures
- `docs/`: player guide, architecture, evidence and expanded development roadmap

## Scope and credits

Original world, characters, artwork, story, tune and code under the repository's existing Apache license. Handheld top-down adventures inspire readability and motion; no Nintendo characters, maps, music or extracted assets are included. The standard cartridge boot-identification header is present for GBA compatibility.

This is a foundation release in a continuing project, not 128 finished monsters or commercial-game parity. Physical GBA hardware, flash cartridges, other emulators/compiler releases and the macOS bridge-build path remain untested. Remote hosted CI is not currently configured.
