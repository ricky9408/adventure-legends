# Isolated GBA build and test tools

The game targets ARM7TDMI directly, so the build uses GCC ARM bare-metal and does not require libgba. Tools were extracted from official Debian 13 packages into this directory, without root, system package changes, accounts, or purchases.

## Build tools

Compiler/binutils prefix: `tools/sysroot/usr/bin/arm-none-eabi-`

- GCC 14.2.1 (Debian package `14.2.rel1-1`)
- Binutils 2.44
- Freestanding compile options: `-mcpu=arm7tdmi -mthumb -ffreestanding`
- Link with the GCC driver and `-mcpu=arm7tdmi -mthumb -nostdlib ... -lgcc`
- GCC is relocatable and finds its local compiler support files automatically
- No target C standard library is installed; the game supplies any needed memory functions

Run `./tools/install_tools.sh` to reproduce extraction on Linux x86_64 with a Debian 13-compatible host. The script pins official package URLs and SHA-256 digests. GCC's digest was additionally checked against Debian's package-download page. Runtime dependencies for mGBA must already be available (as they are in the build computer); `ldd tools/sysroot/usr/lib/x86_64-linux-gnu/libmgba.so` diagnoses missing libraries.

Official sources:
- https://packages.debian.org/trixie/gcc-arm-none-eabi
- https://packages.debian.org/trixie/amd64/gcc-arm-none-eabi/download
- https://packages.debian.org/trixie/binutils-arm-none-eabi
- https://packages.debian.org/stable/libs/libmgba0.10t64
- https://deb.debian.org/debian/pool/main/m/mgba/

## True-ROM mGBA automation

`mgba_bridge.c` is a thin wrapper around mGBA 0.10.5's native core. It executes the ARM ROM and emulates GBA video and memory; it is not a browser recreation. The custom Python front end accepts held keys, frame counts, memory reads, screenshots, and emulator states. An external BIOS is not required because mGBA's own HLE BIOS is used.

Dependencies for the test runner: a native C compiler, mGBA 0.10.x development headers/library, Python 3, and Pillow. `pkg-config` is optional. On a Debian 13 system the corresponding packages are `build-essential libmgba-dev python3-pil pkg-config`. ARM compiler and mGBA runtime packages have different purposes: only the ARM tools are needed to produce the ROM.

Compile the bridge: `./tools/build_mgba_bridge.sh`

The script prefers this workspace's isolated mGBA library. Without it, the script checks system `pkg-config` names `mgba` then `libmgba`, and finally standard system include/library locations. `HOST_CC` can select a native compiler. The tested host is Linux x86_64; a Darwin shared-library flag is supplied but that path has not been tested here.

Capture a screenshot after boot:

```
python tools/mgba_runner.py build/emberbond.gba --frames 120 --shot title.png
```

Run commands from a file:

```
python tools/mgba_runner.py build/emberbond.gba --script test.txt
```

Example `test.txt`:

```
frames 120
shot title.png
tap A 2 2
frames 60
shot game.png
read 0x02000000 4 8
```

Commands:

- `frames COUNT [KEYS]`: run COUNT emulated frames with keys held (default released)
- `tap KEYS [HOLD] [RELEASE]`: hold keys then release; default 1 frame each
- `shot PATH`: save native 240×160 PNG, PPM, or another Pillow-supported format
- `read ADDRESS [WIDTH] [COUNT]`: print JSON values, byte width 1/2/4 (default 4)
- `dump ADDRESS LENGTH PATH`: dump bus memory to a binary file
- `write ADDRESS VALUE [WIDTH]`: write memory, for targeted diagnostics only
- `state PATH` / `loadstate PATH`: save/restore emulator state
- `reset`: reset core without unloading the ROM

Keys: `A B SELECT START RIGHT LEFT UP DOWN R L`; combine with `+`, or use an integer mask. Masks match GBA bit positions but use 1 for pressed; the emulated KEYINPUT register still uses GBA's active-low convention.

The same interface is importable:

```python
import sys
sys.path.insert(0, 'tools')
from mgba_runner import Emulator
with Emulator('build/emberbond.gba') as game:
    game.frames(120)
    game.tap('START', 2, 2)
    value = game.read(0x02000000, 4)
    game.screenshot('screen.png')
```

`game.bytes(address, count)` captures arbitrary memory. `game.load_save(path)` loads a private copy of cartridge save data without modifying the input file; reset afterward to test the game's boot-load behavior. Keep an appropriate SRAM identifier in the ROM if using SRAM. Emulator savestates and cartridge SRAM saves are different formats.

## Verification performed

- ARM7TDMI Thumb C compilation and disassembly
- Core initialization and execution of a real ARM branch-loop ROM
- Frame stepping and memory read/write
- 240×160 RGB output verified with red, green, and blue framebuffer regions
- A+LEFT input produced KEYINPUT `0x03DE`
- Emulator savestate RAM round-trip

The public mGBA core API and official frontend example were consulted:
- https://github.com/mgba-emu/mgba/blob/0.10.5/include/mgba/core/core.h
- https://github.com/mgba-emu/mgba/blob/0.10.5/include/mgba/core/interface.h
- https://github.com/mgba-emu/mgba/blob/master/src/platform/example/client-server/server.c

Do not include `downloads/` or `sysroot/` in the game's player release. Players only need the `.gba` ROM and a compatible emulator or flash cartridge. Source releases can include the small wrapper scripts and installer, rather than hundreds of megabytes of host compiler binaries.

## ROM build verification

`make -B -j4` rebuilt the complete game with zero warnings, producing a 227,452-byte ROM at the time of tool validation. The header logo/identification bytes match the official devkitPro gbafix reference, the complement checksum is valid, and `SRAM_V113` remains in the binary. The linker `.data` load/start/end and `.bss` start/end symbols are 4-byte aligned, matching startup's word copy/zero loops. `.bss` is 608 bytes at that revision, and `.data` is empty. The actual game ROM booted in mGBA to title state after 120 frames and produced a native screenshot. Sizes may change as gameplay is revised.

The custom startup is intentionally minimal: game code is copied to IWRAM, `.bss` is zeroed, and `.data` is copied, but arbitrary unused RAM is not cleared. IRQ/FIQ are disabled; gameplay polls VBlank rather than using an interrupt handler. This is sufficient for this game's globals and main loop.

## Audio capture

The wrapper can record the emulator's real mixed PCM output as stereo 16-bit WAV:

```
python tools/mgba_runner.py build/emberbond.gba --frames 600 --audio music.wav
```

Or call `game.audio_start('music.wav')`, run frames/inputs, and `game.audio_stop()`. Closing the session also finalizes the WAV header. Script commands are `audio PATH` and `stopaudio`. The current game's native output is 32,768 Hz; the captured audio includes raw GBA DC bias characteristics. The runner explicitly enables a normal 256 master volume, since a blank mGBA frontend configuration otherwise leaves volume at zero. A 300-frame capture was verified to contain 164,120 stereo frames with nonconstant samples.

Cartridge save loading was independently checked with a valid 32KiB SRAM file: after reset, the actual ROM set `has_save=1`; SRAM remained writable within the emulator and the input file's bytes were unchanged.


## Deferred-anchor synthetic host probe

The Linux-only host integration probe reserves inert memory at GBA hardware address
ranges with MAP_FIXED_NOREPLACE. A randomized Python heap can overlap those ranges.
The Magma source-export audit recorded one setup failure before game assertions;
a disposable diagnostic independently reproduced EEXIST from a heap overlap.
An unchanged fresh-process probe passed all 27 cases, and the full live host aggregate
passed. This is separate from mGBA native tests and does not affect the cartridge.

Do not use MAP_FIXED, overwrite a live mapping or disable memory protections to make
this test pass. Preserve the failure log. A fresh-process rerun can distinguish this
setup problem; an actual game assertion failure must still be investigated. The normal
Make target directs its generated report into build/ to preserve archived evidence.
See docs/magma/source-export-review.json and docs/VERIFICATION.md for exact scope.


The ongoing Underwater branch adds a narrowly bounded launcher for that host probe.
It captures errno, the requested range and only overlapping generic mapping tags.
Only EEXIST with an independently recorded overlapping Python heap, before any game
assertion, permits up to two fresh-process retries. Every attempt and original failure
is retained in a unique build directory. Permission failures, other setup failures,
malformed diagnostics and game assertion failures stop immediately. No fixed mapping
is overwritten and no ASLR/protection setting changes. Synthetic launcher tests cover
all of these refusal paths; they are not extra game-coverage evidence.
