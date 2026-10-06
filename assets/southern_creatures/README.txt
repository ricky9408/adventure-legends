SOUTHERN COMPANIONS: ORIGINAL NATIVE ANIMAL ART

Scope
Twenty original forms for fixed IDs25,26,28,29,79–94. Art only. This bundle does
not grant companions, prove acquisition, enable powers or modify save state.
Source: assets/generate_southern_creatures.py. No Nintendo or other extracted
art, raster tracing, downloaded creature image or raster-generated input.

Native runtime contract
-16×16 field images, anchor(8,8), row-major8bpp existing game palette indices
-Direction order: down, up, left, right
-Four authored locomotion beats and two cast poses per direction and form
-Anticipation narrows upper lids without covering pupils; recovery opens them
-Separately authored32×32 portrait per form
-Palette178 entries preserved; only original actor slots0–96 are used
-Transparent index0; cast/field drawings remain inside one16×16 footprint
-Immutable ROM tables. No heap, mutable globals, persistent OBJ reservation,
 palette changes, scene state or background buffers
-Unknown IDs and invalid unsigned direction/pose values return NULL/-1
-Accessors mirror the Northern interface, prefixed southern_creature_art_

Generation and verification
python3 assets/generate_southern_creatures.py --verify
python3 tests/test_southern_creature_art.py

Measured ARM7TDMI Thumb/O2 object
143,380 pixel/table bytes;143,632 total ROM bytes;0 data;0 BSS;8B max stack.
Source include chunks are at most29,999B. The ceiling is170KiB, not a claim
about full-game link size or emulated presentation cadence.

Review outputs
{name}_walk.png:64×64; frame columns, direction rows
{name}_ability.png:32×64; anticipation/recovery columns, direction rows
{name}_portrait.png:32×32 original portrait
{name}_native.png:240×166 contact sheet, all poses at1:1 on dark/light ground
{name}_terrain_native.png:576×112, all poses at1:1 on four actual chapter crops
{name}_motion.gif:128×48, four walk beats then anticipation/recovery
silhouette_native.png:20 forms in color and black, native field resolution
prior21_silhouettes_native.png:all41 forms, all four directions in black

Review notes
Ten living families use different silhouettes, anatomy and locomotion. The
gecko evolution connects its gliding skin to the body; the dune evolution
bears weight on broad digging forefeet; the fish banks tall sail fins; the
frog has broad paired throat folds; the crab preserves an open shell vault;
the mantis grows crescent forearms; the mammal hangs below a tail loop; the
newt raises a continuous dorsal veil; the bat spreads linked W-shaped wing
fingers; the tenrec rises on longer rear legs below separate quills.

At native scale, all20 front silhouettes are different and none duplicates
the prior21. Minimum front-mask difference against another Southern form is
18 pixels (the related frogs); minimum against a prior form is27 pixels.
Front/back colors and anatomy are independently drawn. Bilateral profiles
mirror exactly; symmetric front/back outlines for some mammals are normal,
while their directional faces/back markings differ. Eye anchors remain clear
through all six poses. Gaits change feet/fins/wings as well as breathing lift.

The four actual Southern background crops and SHA256 provenance are stored in
manifest.json. Visual review covers green grass, blue water, warm light plaster
and striped timber. There are no terrain-color sprite substitutions. Dark
outlines and eye whites are consistent across scenes. Only runtime integration
and actual emulator captures can prove native rendering in gameplay.
