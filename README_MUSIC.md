# Selected game soundtrack

The owner approved replacing all 23 BGMs and the room-68 makers' assembly
jingle after the final old/new listening comparison on 2026-10-12.
`assets/music/selected/catalog.json` is the current cartridge input catalog.
It records exact PCM hashes, lengths, keys, meters, tempos and room membership.
The previous `regional` and `lanterns` catalogs remain historical sources.

The score has 19 independent BGM melodies. The original main theme is arranged
only in HOME, CORE, HORIZONS, COVENANTS and MAKERS_ASSEMBLY. The reference brief
was the adventure and instrumental colors of Pokemon Ruby/Sapphire/Emerald,
A Link to the Past, and selective theme arrangements as in Undertale; these
are original melodies, without audio or melodies extracted from those games.
CORE, covering rooms 10-13 including the main-story final boss, uses the heavy
orchestral arrangement and its accepted noise-clean cartridge conversion.

## Cartridge and playback

All 78 room assignments and the existing title/HOME selection remain intact.
Connected rooms using the same cue preserve its phrase; changing cues uses
existing bounded 512-sample fades. Each cue loops at its exact unpadded sample
count. Pause, dialogue, saves and death preserve the ongoing room BGM.

The payload is 15,097,961 bytes of signed 8-bit mono PCM at 16,384 Hz.
CORE is 702,172 samples, SHA-256
`dc26f90664b8a1f23edbc9e767b706677caf10dacb9cc9fdd5e4b4f157e30731`.
Its final quantization adds no random dither, reducing the previously heard
noise without changing the arrangement, gain or period. The other 22 cues are
the exact accepted game-format bytes from the orchestral review edition.

Direct Sound A retains DMA1, timers 0/1, the 8 KiB EWRAM ring and 256-byte
guard. PSG1 effects and PSG2's assembly jingle retain their existing roles.
The jingle is D4-F#4-A4-F#4 repeated three times, with the existing 12-note,
180-active-tick timing, trigger, pause and exit behavior.

## Build and exact reproduction

Generated cartridge C is included. Build with an ARM7TDMI GCC toolchain:

    make ARM_PREFIX=/path/to/arm-none-eabi-

Regenerate exact cartridge data with Python's standard library:

    python3 tools/generate_music.py

The importer validates all 23 hashes, lengths, rates, previous per-cue size
budgets and the complete 78-room mapping before changing generated output.
It copies approved PCM; it does not rerender or requantize music.
The source packager includes selected PCM and 24 canonical MIDIs through
explicit binary hash pins. Note-level scores accompany those files; only
historical provenance path labels were made portable, with original source
hashes retained in `assets/music/selected/provenance.json`. Stereo masters and
historical trials remain in the local production archive.

## Credits and checks

Original game music credit: **GarlicDot**, as supplied by the owner.
Current music is original score work created with OpenAI and rendered with
FluidSynth 2.3.4 / FluidR3 GM 3.1; primary audio was not generated with Suno or
ACE-Step. The FluidR3 sample-library notice is included in
`assets/music/selected/FLUIDR3-LICENSE.txt`; the soundfont itself is not bundled.
Earlier repository authorship records remain unchanged.

Run current host transport/import checks and the PSG sequence contract:

    python3 tests/test_soundtrack_runtime.py
    python3 tests/test_horizons_audio.py
    python3 tests/test_ending_credits_host.py

For actual mGBA audio, build first and run:

    python3 tests/selected_music_native.py --expected-rom-sha SHA256 --output build/selected-native

This checks controller playback, all room transitions, two exact loops per
BGM, PSG coexistence, frame cadence and sample/inter-sample headroom. Room and
long-loop fixtures are labeled synthetic. Emulator checks do not establish
physical GBA compatibility or a full campaign replay. Historical proof suites
run separately on their authenticated prior source tree.
