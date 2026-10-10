# Return I companion art

Original code-native pixel geometry for RETURN_I_DESIGN_R2. Art-only deliverable.
No third-party imagery, image extraction, tracing, Nintendo assets or palette edits.

## Rebuild and verify

```
python3 -B assets/generate_return_creatures.py --verify
python3 -B tests/test_return_creature_art.py
```

Both commands run from the repository root. Python 3 and Pillow are required. ARM
verification uses the existing project toolchain resolver. No network is needed.
The generator fails if an existing companion-array/palette baseline changed.

## Runtime contract

- Exactly 15 sparse form IDs: 3, 6, 9, 12, 15, 17, 18, 21, 24, 27, 30, 101–104
- Four directions: down, up, left, right
- Four articulated 16×16 walk frames per direction, row-major 8bpp
- Three articulated cast frames per direction: anticipation, release, settle
- After settle, the caller returns to the walk cycle; no fourth cast frame exists
- 32×32 separately composed portrait per form
- Center anchor (8,8), transparency index zero, transparent one-pixel field rim
- Sprite shadows are external to the images, matching the established renderer
- All indices are existing actor colors 0–96 of the cartridge game_palette
- No catalog, save, command, framebuffer, OAM, palette upload or allocation logic
- All pixels and form IDs are const ROM, no .data/.bss/IWRAM/EWRAM dependencies
- Every invalid ID, direction and frame fails closed; arguments never wrap modulo

The generated accessor names are return_creature_art_index,
return_creature_art_frame, return_creature_art_ability_frame and
return_creature_art_portrait. Their signatures match the Underwater equivalents.
The caller must test this sparse dispatch independently of catalog row ordering,
select cast frames only during casting, and retain signed clipping at render time.

ROM payload is 122,895 bytes: 61,440 walking + 46,080 casting + 15,360 portraits +
15 form IDs. ARM7TDMI Thumb object is 123,187 bytes against a 131,072-byte budget.
The four accessors require at most 8 bytes of stack; .data and .bss are zero.
Generated source chunks are below 30,000 bytes (also below the 75 KB requirement).
Recommended individual walk beat timings are in manifest.json; they are review
suggestions and do not change runtime timing by themselves.

## Review files

- roster_native.png / roster_2x.png: all 15 portraits and directional idle views
- all_frames_native.png / all_frames_2x.png: all 420 field poses and 15 portraits
- lineage_native.png / lineage_2x.png: actual released predecessor images beside
  the Return evolutions; two new families also have their own two-stage rows
- released104_silhouettes_native.png / _2x.png: 89 released and 15 new masks
- Each form has indexed _walk.png, _ability.png and _portrait.png sources
- Each form has _native.png and exactly nearest-neighbor _3x.png light/dark review
- Each _walk_native.gif is exactly 64×16, four native 16px directional views
- Each _motion.gif demonstrates walk → anticipation → release → settle → walk
- Each _terrain_native.png compares every pose against six actual native crops
- greenwake_composite_native.png / _3x.png and roster_walk_native.gif are art
  composites over an actual new background; they are explicitly not game captures
- terrain_readability.json records a simple RGB555 color-distance heuristic
- manifest.json and validation.json carry source hashes and verification results

Old sources: Frondshore grass and Sunlace cream/teal. New sources: Greenwake grass,
Sunlace Shade Terraces cream and Overflow Gardens teal. Source paths, crop boxes
and exact hashes are recorded. If a world artist changes those backgrounds, run
the generator again before using the final review results.

## Visual identity

- Homura Wayhearth keeps one connected wick tail, a pointed fox face and visible
  stepping feet beneath an open ivory horseshoe mantle
- Midori Orchardkeeper retains the blue living seed and turquoise boughs; its two
  uneven boughs and stepping open root arch replace an enlarged umbrella
- Fuuri Skyhem keeps four silk surfaces and one continuous trailing ribbon loop;
  upper crescents bank while the short lower sails steer
- Kohaku Waystone keeps amber architectural anatomy, toe feet and a low face;
  two offset shoulder arches have transparent interiors
- Riverturn keeps the droplet face and reed feet while its two joined water loops
  run sideways rather than repeating Tidewheel's vertical wheel
- Bellstride has joined bronze spring anatomy, long rear prongs and cheek
  clappers; Pealwarden is taller with an open bell collar and three planted prongs
- Arbourloom keeps living vine/leaf anatomy with a long-legged open trellis and
  one tail threaded through it
- Hearthrover keeps a ceramic face and vented kiln shoulder over a real quadruped
- Crownleap keeps the gecko face and toes, a single dorsal fin, foreleg membranes
  and one counterbalancing tail
- Terrashaper keeps large listening ears, a hooked single tuft tail and wide split
  forepaws; its chest remains visibly above the ground
- Hingelet and Hushhinge are copper/silver plated shrews with soft pointed noses,
  delicate whiskers, small paws and a single curl tail; the evolved ears open
- Rillkite and Wakebraid have mudskipper eyes, smiling faces and bowed stepping
  pectoral fins; the evolved forefins widen and one continuous crest braids visually

## What is verified

15 automated tests cover all 435 native images independently round-tripped through
host C and PNG, synthetic tensor ordering, exhaustive byte-width sparse-ID misses
and wide invalid values, bad-emitter atomic rejection, palettes, geometry bounds,
transparent rims, articulated masks, source hashes, nearest-neighbor review scales,
walk GIF frame identity, cast recovery GIF order, frozen predecessor arrays,
determinism, target ARM ROM/data/BSS/stack/undefined-symbol/section contracts.

Every form has four distinct direction masks; every direction has four unique
normalized walking silhouettes and three unique normalized casting silhouettes.
No new front silhouette duplicates any of the 89 released fronts. New forms also
remain distinct from one another. The minimum front-mask distance to any other
released or Return form is 25 pixels.

All 2,520 field/terrain comparisons are measured. The lowest whole-body distinct
fraction is 0.811 and the lowest boundary distinct fraction is 0.750, using RGB555
Euclidean distance ≥48. These fractions are a heuristic, not a gameplay test or
proof that every edge is equally visible. Bright water highlights naturally have
less contrast on teal; the darker body structure remains visible in native review.

## Still required after integration

Native emulator checks must establish form-ID dispatch, portrait selection,
walk/cast/recovery state selection, facing, signed off-screen clipping, pause/save/
load/scene transitions, actual VRAM bounds and frame/memory budgets. This module
makes no claims that generated sheets prove native-game rendering or obtainability.
