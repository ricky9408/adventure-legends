# Original regional soundtrack

All 78 rooms now have explicit assignments to 23 original project-specific
cues. Connected rooms in the same musical area preserve the current phrase;
a change of cue uses the existing bounded 512-sample fade out and fade in.
Unknown room IDs safely select HOME. Title and new-game confirmation use HOME.

Lanterns by the Footbridge remains the exact approved HOME master: 907,421
signed 8-bit mono samples at 16,384 Hz, SHA-256
`a9ada6ff0b3ef068dc8ab9bfabd02f69521c6ef252420157b9646636e98e4838`.
No resampling, gain change, appended silence or playable alignment bytes were
added. Every cue loops at its own exact sample count, including odd lengths.
There is no new compression or sequencer architecture.

## Cartridge and ownership

The immutable catalog is `assets/music/regional/catalog.json`; it records
actual titles, keys, meters, tempos, exact sizes, SHA-256s and room membership.
`room-plan.json` maps every room explicitly. RIVER uses the reviewed ROAD
render, and GROVE uses the reviewed GROVE_SHRINE render. Proposed planning
metadata is not substituted for the final scores.

The total PCM payload is 17,331,092 bytes. The two obsolete shared village and
dungeon cartridge arrays have been removed. Historical v2 source inputs and
old release evidence remain provenance only; they are not linked into music.

Direct Sound A retains DMA1 and timers 0/1, an 8 KiB EWRAM ring and 256-byte
repeated guard. Refills remain at most one 512-sample block per eligible frame.
PSG1 effects, PSG2's room-68 assembly chime, DMA3 graphics and timers 2/3 retain
their existing roles. Pause, dialogue, saves and death do not restart a cue.
The existing recovery, startup, IRQ and fade implementation is unchanged.

## Build and reproduction

Generated cartridge C is included. Build with an ARM7TDMI GCC toolchain:

    make ARM_PREFIX=/path/to/arm-none-eabi-

Regenerate the exact cartridge data and routing catalog using standard Python:

    python3 tools/generate_music.py

This validates every exact raw input hash, length and rate before generation.
The source packager includes only explicitly hash-pinned music binaries.
Each regional folder includes the original score/event sources, performance
manifest and synthesis palette. Recreate the
22 regional raw assets with standard Python (several minutes):

    python3 assets/music/regional/reproduce_raw.py --output-dir build/regional-reproduced

HOME's approved renderer and sources remain under `assets/music/lanterns`.
Its byte identity is independently checked against the approved source archive.

## Authorship and verification

These are original compositions created with OpenAI for Adventure Legends.
The synthesizer uses original additive instruments, with no third-party
recordings or samples. The ending roll now credits this regional soundtrack;
its row count, presentation and controls are unchanged.

The accepted cartridge is SHA-256
`f3731bad2290aa680edc6c2cb191e945dd24bc4dcb3fdc16dc6343e91959e913`.
It is 32,194,208 bytes, below the 32 MiB cartridge limit. Regional integration
was checked with actual-C tests, exact PCM readback and native emulator timing.
These checks do not establish subjective listening approval or physical GBA
compatibility. See [publication scope and verification](docs/PUBLICATION.md)
for the current GitHub tree and the distinction between included source and
separately retained historical evidence.
