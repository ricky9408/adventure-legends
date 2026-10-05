# Original handheld-adventure visual and motion direction

The user's reference is The Legend of Zelda: The Minish Cap. Its role here is a quality reference for readable, lively top-down pixel art and responsive motion. This game keeps its own characters, landscapes, palettes, story and soundtrack; no commercial-game sprites, maps, music or textures were imported or traced.

Official reference material consulted:
- [Nintendo's Japanese game feature and screenshots](https://www.nintendo.com/jp/games/feature/nintendo-classics/a-8665_j/index.html)
- [Nintendo UK trailer](https://www.youtube.com/watch?v=cSIDghMWVMA)

## Visual changes at native 240×160 resolution

- Sculpted leaf clusters with multiple lighting planes, visible roots and contact shadows
- Deeper eaves and roof highlights, attic/window details, quieter floor textures
- Clear warm/cool separation: warm lanterns and characters against cooler forest and temple depth
- Four distinct walk poses in each hero direction, and directional companion poses with animated tails, feet and leaf limbs
- Ground shadows, y-sorted characters and small foreground canopy layers
- Original sword crescents, brief impact stop, sparks and a small collision-checked lunge
- Moss-like guardian armor markers instead of placeholder companion-shaped indicators

The art remains deliberately small and original. It does not claim the breadth or commercial polish of the reference game.

## Motion changes

The first playable version spent CPU time re-rasterizing every moving sprite and text label. Hardware OBJ and static-page caching remove that scene-dependent load. The measured guardian rate improved from ~29.86 updates/s to one update per GBA frame (~59.73/s); the old pause screen updated at ~14.93/s. All 15 sampled steady windows now meet the one-frame cadence target.

Q8 movement makes both diagonal axes equal and keeps diagonal distance close to cardinal distance. The test's 24-frame diagonal/cardinal ratio is 1.0254 due to rounding final integer coordinates, within its 5% tolerance. The underlying component ratio is normalized rather than the previous alternating-axis shortcut.

Opening an uncached menu recognizes input within one hardware frame, then may need two frames for the new static page. Three-frame sword hit-stop is intentional feedback; it is separate from a missed rendering frame. Rooms still use fixed framing with a brief transition fade. A larger scrolling world would be a separate extension.

See [performance evidence](perf/README.md), including before/after screenshots, exact hashes, frame intervals and hardware-cycle measurements. The comparison video uses original and revised native ROM execution at real GBA cadence, without interpolated frames or RAM-injected progress.

## Brighter background palette

A subsequent scenery-only pass lifts the village/forest/grove toward sunny greens and cream paths, lightens temple stone with cool highlights, and warms the title's twilight. New background-only palette entries preserve the original character/UI colors. Foreground canopy colors are remapped with their matching scene so layered depth remains coherent. Geometry, collisions, sprite pixels and gameplay machine code are unchanged. The full gameplay/save and strict frame suites passed again on the revised ROM.
