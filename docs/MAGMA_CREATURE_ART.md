# Magma companion art module

Original native GBA art for the approved Magma design: 24 forms across nine families. This is an isolated art deliverable. It does not enable any catalog row, acquisition, evolution, field power, map, or playable content.

## Delivered

- Exact form IDs: 31–48 and 95–100
- Each form: four directions × four walk poses, four directions × two cast poses, and one independently composed 32×32 portrait
- 576 native 16×16 field/cast images and 24 native portraits, stored as row-major 8bpp indices into the unchanged Southern game palette
- Original hand-authored geometry, separate anatomy for both third tiers and all four alternate-branch pairs, no traced or extracted game art
- Living, articulated silhouettes: independently rocking snail shells; braced/stepping goat gaits; separate tapir trunk/ear/body shapes; three-pair moving crawler feet beneath an open lattice
- Selective material-colored upper/leading rims improve dark-scene readability. They change only existing ink pixels; they never change alpha, native bounds, or silhouette geometry
- `src/magma_creature_art.c`, its header, and 15 deterministic include fragments, each at most 30,000 bytes
- Native PNG sheets, motion GIFs, a manifest, 65-form silhouette comparison, per-pose terrain review, and host/ARM tests

## Review the actual native scale

Start with `assets/magma_creatures/roster_native.png`, `roster_walk_native.gif`, and the `fullscreen_*_native.png` files. The fullscreen images are 240×160 art composites using real existing scene pixels. They are not emulator screenshots or evidence of playable/acquirable forms.

Each `{name}_native.png` shows all 24 field poses on bright and dark review grounds beside its portrait. Each `{name}_terrain_native.png` checks those same pixels over six real existing scene crops: bright grass, water, plaster, wood, shaded foliage, and a dark doorway. Sprites are never scaled in these reviews. `roster_2x.png` is an optional exact nearest-neighbor inspection aid.

`released65_silhouettes_native.png` compares the released 41 forms and these 24 forms at native size. All 24 new front masks are distinct; none exactly matches a released front mask. All evolution and sibling-branch silhouette pairs differ by at least 18 native mask pixels in every facing.

Per-form GIF walk timing is derived from `WALK_TICKS` in 60Hz updates. These timings are art recommendations, with GIF display quantized to 10ms; they do not change an engine animation clock. Cast poses represent anticipation and recovery, not a simulated ability.

## Runtime interface

- `magma_creature_art_index(form_id)` returns the art row, or −1
- `magma_creature_art_frame(form_id, direction, frame)` returns a 256-byte walk frame, or NULL
- `magma_creature_art_ability_frame(form_id, direction, pose)` returns a 256-byte cast frame, or NULL
- `magma_creature_art_portrait(form_id)` returns a 1,024-byte portrait, or NULL

Directions are down/up/left/right (0/1/2/3). Walk frame range is 0–3; cast pose range is 0–1. Pixel zero is transparent; field anchor is (8,8). Unknown IDs and invalid unsigned values, including negative signed values converted to unsigned, are rejected before indexing.

The module has no coordinate, blit, DMA, tile-upload, OAM, or frame-buffer API. It therefore cannot write offscreen. The existing renderer must retain signed coordinate arithmetic, reject fully offscreen rectangles, and clip before consuming returned pixels. Renderer integration and its offscreen behavior remain a separate acceptance gate.

## Reproduce

From this directory, with the already-installed Python/Pillow and ARM7 toolchain:

    python3 -B assets/generate_magma_creatures.py --verify
    python3 -B -m unittest discover -s tests -p 'test_magma_creature_art.py' -v

The verifier can use `arm-none-eabi-gcc` on PATH or the existing sibling Southern toolchain. Tests also read the sibling Southern baseline to independently compare its actual game_palette and copied review sources. No package installation or external connection is used.

Generation writes only this module's own asset directory and C art module. `assets/magma_palette.py` contains only the existing palette and primitive drawing conventions extracted from Southern, without its output side effects. `src/assets.h` is an unchanged validation reference, not a replacement game header. `SOURCE_PROVENANCE.json` records the exact read-only input hashes.

## Verified budget and boundaries

- Raw const art arrays: 172,056 bytes
- ARM7TDMI Thumb object ROM: 172,308 bytes, under the 174,080-byte module budget
- Mutable data: 0 bytes; BSS: 0 bytes
- Maximum ARM stack frame: 8 bytes
- External runtime symbols: none; no heap, IWRAM, EWRAM, OBJ lease, or hardware tile allocation
- Largest generated include: 29,993 bytes

The terrain diagnostic checks 3,456 native pose/terrain combinations. Its minimum visible-pixel fraction is 0.475 and minimum visible-boundary fraction is 0.4286 using an RGB-distance threshold of 48 against the real underlying terrain. This is a reproducible visibility heuristic, not a perceptual guarantee; native visual review remains necessary. The dark-terrain check prompted the material-rim refinement.

The standalone art tests verify every PNG pixel against the C accessors, all 65,536 low-range unsupported IDs plus extreme unsigned inputs, clipped-authoring absence, pose articulation, alpha-preserving rims, branch differentiation, independent portraits, exact RGB555 palette preservation, source hashes, deterministic generation, native terrain/GIF composites, and ARM section/stack budgets.

No active Southern source, frozen S3 build, magma-core source, global palette, game.c, or UI file was changed. Runtime smoothness, frame pacing, obtaining companions, and playable integration are not claimed by this art-only module.
