# Underwater creature art

Original, code-native 16×16 companion sprites and independently composed 32×32 portraits for canonical forms49–72. No game extraction, tracing, downloaded raster reference, or palette additions. The catalogue is read through `assets/creatures/catalog_source.py` and must agree with all24 identities.

## Reproduce and inspect

- `python3 -B assets/generate_underwater_creatures.py --verify`
- `python3 -B tests/test_underwater_creature_art.py`
- `roster_native.png` and `roster_2x.png`: all24 portraits with four native directional sprites
- `all_frames_native.png` and `all_frames_2x.png`: all24×4 directions×7 motion poses
- `<name>_walk.png`: editable indexed64×64 four-direction/four-beat atlas
- `<name>_ability.png`: editable indexed48×64 four-direction/three-pose atlas
- `<name>_portrait.png`: independent indexed32×32 portrait
- `<name>_native.png` / `<name>_3x.png`: all poses against light/dark grounds
- `<name>_terrain_native.png`: all28 field poses against five real Underwater terrain crops
- `<name>_motion.gif` and `roster_walk_native.gif`: timing/motion reviews
- `released89_silhouettes_native.png` / `_2x.png`: all89 released-plus-proposed masks
- `nacreway_composite_native.png` / `_3x.png`: native scene-and-shadow art composite

These are sprite sheets and art-review composites, never emulator captures, collection proof, or final native-performance evidence. Edit the code-native source then regenerate; editing a generated PNG alone does not alter cartridge art.

## Stable C contract

`src/underwater_creature_art.h` exports:

- `int underwater_creature_art_index(unsigned int form_id)`
- `const unsigned char *underwater_creature_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame)`
- `const unsigned char *underwater_creature_art_ability_frame(unsigned int form_id, unsigned int direction, unsigned int pose)`
- `const unsigned char *underwater_creature_art_portrait(unsigned int form_id)`

Direction0=down,1=up,2=left,3=right, matching regional/Magma convention. Walk frames0–3; frame0 is the calm held stance. Ability poses0=anticipation,1=release,2=settle. Playback should follow the actual cast startup/active/recovery intervals and freeze with gameplay pauses. Suggested per-form walk durations are in `manifest.json:walk_ticks_by_form`; they are recommendations, not a second clock or gameplay authority.

Pixels are row-major8bpp indices into the unchanged existing game palette. Zero is transparent. All16px sprites retain a fully transparent one-pixel outside boundary; no art crosses the16×16 footprint. Side views are paired horizontal reflections; up views show the dorsal surface without frontal pupils. Field anchor(8,8), external ground-shadow center(8,13). Art contains no baked shadow; retain the renderer's existing shadow and existing streaming OBJ slots. Palette, VRAM ownership, signed screen clipping, follower position, animation ages, and OAM admission remain caller responsibilities.

All four functions reject unsupported full-width unsigned IDs/indices, including wrapped negatives. Pointers have immutable static ROM lifetime. No heap, mutable storage, writable tables, IWRAM code, persistent OBJ allocation, renderer writes, or palette upload is introduced.

## Measured art-module budget

-196,632 immutable pixel/ID bytes:24 IDs +98,304 walk +73,728 cast +24,576 portrait
-196,756 total compiled ARM/Thumb ROM bytes, including124 bytes of lookup code
-0 data,0 BSS,0 EWRAM,0 IWRAM,0 function stack bytes in the isolated ARM build
-194KiB isolated ROM budget; maximum generated include29,996 bytes, strictly below30KB
-696 images independently reconstructed from compiled C and their saved indexed PNG atlases
-48 immutable old art/palette files match accepted Magma commit0a8b05c3e24d02bd350a11c32289fb5686641535

`validation.json` records exact current hashes and target-object evidence. Whole-ROM resource, live companion streaming, OAM/scanline, frame-cadence and gameplay verification are separate parent integration gates.

## Anatomy and animation review

Eight families retain stable material and body identity. Their branches are structural:

-F017: short teardrop mantle with six short arm tips and two bracket feelers; tall narrow scalloped mantle with long bracket arms; broad paired offset web fans with a deep center split
-F018: rounded unequal shell valves over a muscular foot; long low split keel; tall open crown and rounded ballast foot
-F019: upright hooked seahorse; high open ladder fronds and long tail; low sideways kelp loop with head outside
-F020: low U-shaped horseshoe; narrow upright open gate; broad rectangular shell with asymmetric true windows
-F021: short forked feather crown and root toes; high two-part crescent crown and coiled foot; low traveling mantle-fold worm
-F022: five-arm star; high unequal cross; low non-radial three-bend accordion walker
-F023: slender three-collar eel; angular elbow and open jaw; unequal double loop with crossing face and free tail
-F024: axial-banded oval comb jelly and short lobes; tall diagonal veil with two trailers; three soft corner lobes around a real center opening

For front and back views, some tiny appendages overlap in projection; the large portrait resolves their structure. Native walking patterns independently flex fins, valves, leaf tails, planted feet, crowns, star arms, eel loops, and comb bands rather than translating an unchanging bitmap. Casting compresses the live body before opening and settling. All directions have four translation-invariant walk masks and three translation-invariant cast masks.

All24 front silhouettes are unique and none exactly copies any of65 earlier front silhouettes. Every terminal pair differs by at least54 occupied pixels in all four views. These are geometric diagnostics, not a blinded species-recognition test.

## Remaining readability risks

-At16px, the thin double-loop eel, crab shell windows and shell/foot overlaps have only one- or two-pixel separations. Check them under scrolling and follower overlap, especially Claspcoil69 and Stencilback60
-The pale clam highlights approach light Nacreway chalk values. The minimum terrain sample visibility is56.3% opaque /60.98% boundary pixels for Keelcasket53 under a coarse RGB-distance heuristic; retain its dark edge and inspect it during real play
-Dark ink contours recede on dark ground. Native light/dark review sheets are provided, but only actual room motion can settle readability
-This review is by the author, not a blinded independent taxonomy test. True direction clarity, final follower rhythm, all24 obtained forms, casting timings, and budget acceptance need integrated emulator/controller evidence
