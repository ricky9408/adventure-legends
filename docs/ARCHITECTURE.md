# Engine notes

The cartridge is a freestanding ARM7TDMI program. `startup.s` enters ARM System mode with interrupts disabled, copies Thumb gameplay functions into fast IWRAM, copies initialized data into EWRAM, zeroes BSS, then calls `main`. The linker leaves the palette, backgrounds, sprites and text masks in ROM. No target C runtime or libgba is required.

Rendering uses GBA video Mode 4: two 240×160 indexed-color pages in VRAM, a shared RGB555 palette and VBlank page flips. Static backgrounds and UI are cached independently per page. Frequently changing hearts use hardware OBJ; boss bars and status text update small regions. Text uses aligned paired-pixel writes instead of a function call for every opaque pixel. Panels fill their interior once, then draw border strips.

Moving actors use 8bpp hardware OBJ tiles beginning at bitmap-mode tile index 512. Legacy graphics upload once; current directional hero/companion frames upload only when their pose changes. The software converts row-major art into the GBA's 8×8 tile ordering. Actors are y-sorted, shadows use a lower object priority, and two small foreground canopy masks frame each natural area. Modal panels hide intersecting actors/foreground masks. Sprite positions and OAM are committed with the page flip at VBlank.

Movement uses Q8 subpixel positions: cardinal speed is 320/256 pixels per update and diagonal components are 226/256 each, avoiding diagonal acceleration. Companion follow positions ease toward a trailing target. Sword strikes add a short collision-checked lunge, a changing crescent, three intentional hit-stop updates on impact and particle sparks. Area entry uses a short brightness fade. Rooms remain single-screen rather than a new scrolling overworld.

The nominal update follows the GBA display cadence (~59.7275 Hz). Hardware timers 2 and 3 measure update+render execution cycles, separate from VBlank waiting. All 15 representative steady scene windows passed one-update/one-presentation-per-frame checks; cold intro/pause builds had at most a two-frame interval. See `docs/perf` for exact tested scope and cycle budget. This does not establish all-frame worst-case or physical-cartridge timing.

Static environment collision comes from the artwork's generated `asset_collisions.h`. Dynamic rules enforce the river gap, unlit temple gate and brazier pedestals. Movement is collision-tested on both axes. The room's clear center corridor connects transitions. The quest screen derives its objective from room and persistent puzzle flags.

The selected companion follows the player when summoned. Fire lights nearby pedestals or breaks armor; otherwise it emits a facing-directed projectile. Nature creates the river crossing and supplies cooldown-limited healing plus a short-range push. Sword hits use directional range tests; enemies and the boss have hit flash/invulnerability windows. Contact and enemy projectiles damage the player with a separate invulnerability window.

SRAM uses a small versioned record with magic bytes, room, bridge/torch completion, ending flag and checksum. Areas/puzzles update checkpoints. Resume and retry restore a full-health entrance, not an exact mid-combat snapshot. Emulator save states are independent of this cartridge SRAM format.

Sound uses GBA PSG square channels: an original ambient phrase and event effects. It does not stream sampled music.

For expansion, separate room-specific scripting from `game.c`, introduce a scrolling tile-background renderer, add data-driven dialogue/enemy definitions, and expand the SRAM schema with version migration before adding inventory or additional chapters.
