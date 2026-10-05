# Engine architecture

## Native execution and budgets

The cartridge is a freestanding ARM7TDMI program. `startup.s` enters ARM System mode, copies hot Thumb gameplay code to IWRAM, initializes EWRAM and calls `main`. Cold setup/save/dialogue functions stay in ROM using `.text.rom`. No target libc or libgba is required. The linker reserves at least 4 KiB of IWRAM for the stack and limits cartridge ROM to 32 MiB.

The GBA display cadence is approximately 59.7275 Hz (16,777,216 /280,896 cycles). Hardware timers measure input/update/render execution independently of VBlank wait. Tests also count actual bitmap page changes after each emulated frame; host execution speed is not used as a frame-rate claim.

## Rendering and original assets

Mode 4 uses two 240×160 indexed VRAM pages and a shared RGB555 palette. Moving actors use 8 bpp hardware OBJ tiles beginning at bitmap-mode tile index 512. Assets upload on pose/room/progress changes. Software y-sorting, shadow priority and foreground canopy masks provide depth; modal panels hide intersecting actors. OAM and the bitmap page commit at VBlank.

Static page caching compares exact fields, including room, state, companion, dialogue text/speaker, progression and camera; it does not pack growing identifiers into overlapping bit ranges. HUD/toast pixels use independent EWRAM caches. Long aligned rectangle spans use fixed-source DMA fills. Japanese text is generated into nonzero paired-pixel spans for both halfword alignments, with pixel-exact reconstruction assertions. This avoids decoding thousands of blank glyph bits on a cold menu opening. Generated data stays in deterministic text chunks below 32 KiB rather than giant C blobs.

The grove is a 480×320 continuous world. The 240×136 world viewport leaves a 24-pixel HUD; camera clamps to x 0..240/y 0..184. Even/odd immutable source atlases permit aligned row DMA16 transfers at every camera-x parity. This consumes extra ROM but avoids costly per-frame shifts. Tests compare all four modulo 4 viewport alignments against source pixels.

## Movement, combat and content

Player movement uses Q8 positions: cardinal 320/256 pixels/update and diagonal 226/256 per component. Camera and companion follow ease at subpixel precision. Collision checks all four foot corners and sweeps dodge/lunge movement. Sword combat includes three strikes, bounded buffering, three intentional hit-stop updates on impact and visible particles. Enemy warnings lock aim before firing.

`campaign_rules.*` is generated from editable JSON: 10 new fixed rooms with blocks, gated exits, monotonic puzzle objects, enemies and dialogue; original rooms 0..3 remain separately implemented. Combined requirement masks use room bits 0..15 and chapter bits 16..19. Room transitions clear transient attacks/projectiles and use an entrance lock to prevent bouncing.

Four current powers have distinct roles: fire projectiles/lighting/armor, nature roots/push/cooldown healing, wind vanes/projectile removal/stagger, and stone weights/one-hit guard/pulse. Power cooldown is shared across selection changes. Bosses expose only during explicitly timed recovery, cannot have vulnerability extended indefinitely, and reset living encounters on retreat. The final core clamps damage at each of its three phase boundaries. Cleared bosses do not respawn.

All content, sprites, dialogue and PSG music are original. Audio uses an ambient square-wave phrase and event effects, not streamed samples.

## Persistence

`save4.*` owns the serialized cartridge contract. Two 32-byte banks at SRAM 0x40 and 0x80 contain a version, sequence, progression, safe spawn, companion selection and CRC16-CCITT-FALSE. Writes commit an inactive bank and mark it valid last. The newest valid sequence wins using wrap-safe comparison; corruption falls back to the other bank. Legacy bytes 0..12 remain untouched.

Formats 2/3 are read and normalized without changing their source record. A former completed chapter becomes the first lantern plus the wind companion, not completion of the expanded campaign. Reward saves point to a safe village checkpoint before multi-page dialogue finishes. Ending completion and prior unlocks persist independently. Retry/load restores full health at a safe entrance or recorded camp, not an exact mid-combat snapshot.

Host serialization tests cover interrupted writes, every stored-bit corruption, invalid progression and sequence wrap. Real-ROM tests cover the gameplay timing of saves and migration from authenticated prior-ROM fixtures. Emulator save states are a different mechanism; test branches explicitly pair them with matching SRAM.

## Expansion boundaries

The current 14-area/four-companion campaign is a foundation. Creature evolution/catalog/party, equipment, regional quests and 128 forms are not silently implied by this architecture. The next milestone introduces stable data-driven IDs and a larger non-overwriting save schema before expanding those systems. Required traversal powers must survive evolution and party management. ROM/RAM/OBJ limits and cold as well as steady frame cadence remain release gates.
