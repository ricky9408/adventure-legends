# Lanterns by the Footbridge

The original 24-bar HOME theme uses 300 MIDI notes in three voices. The bundled
MIDI, MusicXML, and performance manifest preserve the approved composition.
The renderer uses only Python standard-library additive synthesis, with no
third-party recordings or soundbanks.

The game input is `lanterns-gba-16384-s8.raw`: signed 8-bit mono at 16,384 Hz,
907,421 samples, SHA-256
`a9ada6ff0b3ef068dc8ab9bfabd02f69521c6ef252420157b9646636e98e4838`.
Its period is exact; alignment bytes must not be played as added silence.

Reproduce the raw asset and optional WAV audition files from the repository root:

```sh
python3 assets/music/lanterns/render_lanterns_gba.py --rates 16384 --output-dir build/lanterns-reproduced
```

The default input is the bundled `source` directory. Output reports use relative
source names, so no local user paths are embedded in published provenance.
The waveform, MIDI and MusicXML are unchanged by publication preparation.
Numerical reproduction is not subjective listening or physical-hardware testing.
