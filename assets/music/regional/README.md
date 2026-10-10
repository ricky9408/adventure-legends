# Original regional music sources

The 22 regional cues supplement the exact approved HOME cue in `../lanterns`.
Each folder contains a signed-8-bit 16,384 Hz raw loop, a performance manifest,
and original MIDI/MusicXML score sources. `render-inputs.json` retains the exact
additive synthesis palette and output hash required for reproduction.

From the repository root, run:

```sh
python3 assets/music/regional/reproduce_raw.py --output-dir build/regional-reproduced
```

This requires only Python's standard library and validates every rendered PCM
hash. The renderer's synthesis and quantizer are unchanged. Publication only
changes its default source path and uses portable source names in new reports.

`source/compose.py` scripts reproduce composition files where present. Optional
`source/engrave.py` scripts create PDF notation using ReportLab and the system
Noto Music font; these optional PDFs are not build or PCM reproduction inputs.
MIDI and MusicXML scores are supplied directly for notation software. Historical
internal review reports and execution traces are intentionally not distributed.
