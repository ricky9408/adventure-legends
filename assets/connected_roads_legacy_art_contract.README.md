# Connected Roads C4: reviewed art successor

The historical Underwater and Return creature-prefix contracts are unchanged. They match accepted Experience Polish P2 exactly. Their ordinary validation mode still rejects this successor because its world background intentionally differs.

`make assets` explicitly selects `--world-successor connected-roads-c4` for only those two generators. The reviewed contract accepts exact C4 identities for one Underwater background chunk and 27 Return entries (26 repacked base-art chunks plus the background-authoring source). It does not refresh historical hashes, exempt whole directories, or bypass validation.

The guard independently checks all 16 complete base-art initializers across chunk boundaries. Exactly two differ from P2: the village background and the first two foreground-canopy masks. The other 14 arrays, including all creature/player frames, shadows, palette and other backgrounds, stay exact. The four non-village canopy masks stay exact. All 37 source definitions are checked; only `village` and `main` differ. Unchanged historical entries retain their original file hashes. Extra chunks, declarations, authoring changes and unreviewed successors are rejected.

Portable verification commands, from the source root:

```
make assets
python3 tools/check_connected_art_successor.py
python3 assets/generate_underwater_creatures.py --world-successor connected-roads-c4 --verify
python3 assets/generate_return_creatures.py --world-successor connected-roads-c4 --verify
```

The `--verify` commands use the existing ARM toolchain selection (`ARM_PREFIX`, `DEVKITARM`, extracted toolchain or system tools). No workspace-specific path is stored in this contract or the generators. Optional `--baseline PATH` on the guard checker additionally validates the original historical files in an accepted P2 checkout.

`tests/test_underwater_creature_art.py` and `tests/test_return_creature_art.py` still contain historical-mode assertions and invoke the generators without the successor argument. Those specific historical guards intentionally reject C4; do not report those entire old suites as unchanged passing successor tests. Current explicit-successor checks preserve the protected prefix and prove deterministic sprite generation, native ARM size/stack bounds and zero writable asset memory.

Regeneration also refreshes source-provenance/validation metadata and six derived scene-review composites to show the current road backgrounds. These are not runtime artwork changes. Every generated runtime source, original creature/palette image and native world bitmap remains byte-identical to frozen C4. Originals are preserved in the retained source archive `cfc280707fd6c82b3c24c3c0821bdaae2c3bb27e54ec5d64773509b6ff9845c8` and accepted P2.
