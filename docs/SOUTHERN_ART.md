# Southern chapter art and geometry

This is original code-native pixel art for areas 30–37. Run:

    python3 assets/generate_southern_region.py
    python3 tests/test_south_art.py

The generator reads `assets/southern_region/contract.json` and `scene.json`; it does not write either input. It uses the original shared 178-color RGB555-compatible palette without changing its slots. No outside raster, Nintendo imagery, copied cultural ornament, traced facade, sacred symbol, external font, or generated image is an input. The climate-responsive inspiration boundary remains in `SOUTHERN_CHAPTER_DESIGN.md`.

## Authored spaces

- Sunlace Anchorage, 480×320: three stepped mineral-plaster masses, inset turquoise shutters, deep door recesses, orange cloth canopies, a shaded civic rain collector, two visible drainage channels, little court benches, living shade trees, waterfront terrace and ferry pier. The ferry vessel and creature shop board are original civic scenery
- Frondshore Commons, 480×320: branching light walking paths, shallow winding runnels, three raised plank crossings, white dune hollow, plaster intake entrance, shaded inspection/rest stands, distinct dune and bough habitats, live mangroves with stilt roots and foliage
- Awning Loft, 240×160: long timber planks, side cloth storage, overhead shade rails, hanging civic cloth and a broad diagonal sun patch. Its rear wall ends at y24, leaving all three y32 beacons reachable from y48; a clearly inset eastern market shortcut at (208,64) opens after quest 29 is READY/CLAIMED
- Chalkspring Hollow, 240×160: pale uneven chalk roof, three dry display ledges, separate shallow water branches, broad sunlight from a high cave opening, pin/drain/cloth arrays and a readable southern escape
- Conservatory Light Intake, 240×160: inset western water trough, large emitter, a single-bend measuring lane, an upper service basin and the companion water-lens dock
- Split-Shade Walk, 240×160: upper planted ledge, two visibly different light/shade terraces, broad central steps, two-pivot lane and a shared screen mounting with both arm sockets visible
- Turning-Bough Gallery, 240×160: raised rear gallery, side piers, a rooted living tree island, and an optical route around its western/northern sides. The exact living-tree solid is (112,72,24,28); a second inset return at (208,112) leads to the field intake after quest 24 objective bit 4
- Sunwell Crown, 240×160: an open pale stepped conservatory roof over turquoise sea, an original circular lens chassis, side walking lanes and a central animated coupling supplied by runtime

The original small-sprite source lives in `assets/southern_region/sprite_art.py`, keeping both source modules under 30,000 bytes.

The small palm-like trees, spreading shade crowns, stepped buildings, lens structures and all scene composition are newly authored here. Generic raster/verification/byte-emission helpers are reused from the existing generator pipeline; Northern authored scenery is not imported.

## Runtime drawing contract

`src/south_art.h` exposes `SouthArtRoom`, `SouthArtRect`, `south_art_rooms`, `south_sprites`, native bitmaps and the complete `SOUTH_SPR_*` enum. The room structure matches the Northern renderer's layout. Sprite pixels are row-major native 16×16 with index zero transparent. Scenery contains no index-zero pixels.

Every layout object preserves its scene key, kind, center, approach, trial/source metadata and interaction radius. `static_baked` identifies objects already present in scenery. These can receive runtime completion markers without spending an OBJ slot for their base.

Base actors that remain dynamic:

- GUIDE, TAILOR, MARKET, RAIN, PORTER, CURATOR
- REST, FERRY, HOOD
- MIRROR_SLASH, MIRROR_BACK, CLOCK, SHADE_CLOSED, SHADE_OPEN
- GATE, WATER_LENS, MACHINE_IDLE, MACHINE_WARN, MACHINE_OPEN

Only neutral supports are baked underneath changing mirror/screen/gate/hood fixtures. No immutable slash, closed panel or collectible hood remains under its changed actor. The main optical receivers may have static sockets with the runtime CATCH/RECEIVER/DONE actor on top. RESET and TRIAL markers and ordinary trial fixtures are baked; unchanged duplicate actors are unnecessary.

HOOD is deliberately not baked because collecting it hides the actor. TORN is a static torn patch; after repairing it, runtime can draw AWNING at the same center (48,48) to cover that patch and show the repair. This is separate from the replacement-panel completion marker at (176,48).

The shared runtime cap is 20 visible region actors, not an allocation of one actor for every object in the entire map. Creature sprites come from the companion source and do not add a CREATURE enum here. Staged previews use the authored Southern walk frame once available; until then, a small footprint-only marker is explicitly recorded as unauthored in `validation.json`. Such staging marks are never exported into a runtime background or sprite array. The final generated previews now use authored Southern frames for all eight scene CREATURE placements (25, 28, 83, 87, 89, 91, 81, 93), with no fallback markers remaining.

## Coordinates, reachability and collision

The generator never moves contract spawns or scene fixtures. Rectangles are half-open. Player collision is the existing exact square-foot radius of five pixels. `collision_rows[y]` indexes a deduplicated u16 stream of records `[count,lo0,hi0,...]` containing sorted, merged, half-open x intervals. World-foot limits are included; the runtime must bounds-check x/y first. There is no RAM unpacking, IWRAM code, extra radius expansion or stateful room collider.

The movement-proof graph includes every spawn, every critical object approach, every authored exit and all seven field/hollow enemy positions supplied by the runtime owner. It currently contains 144 required points. Verification flood-fills one-pixel cardinal moves in both open/closed sets. There are no dynamic movement rectangles, so every mirror/shade state shares the same walking reset and escape routes. Fixtures and actors themselves are not movement collision.

Shallow runnels, chalkspring water and raised paths are visibly traversable. The deep west mangrove fringe and harbor water have static blockers. Stepped collision strips protect the crown’s outer sea corners while explicitly preserving safe side-lane centers (24,112)/(216,112) and the bottom escape. Field enemy positions are (208,264), (320,272), (432,128), (208,64), (336,64); hollow positions are (80,120), (184,136).

Town's north passage remains x304; loft approach is (80,148), with its doorway centered at (80,132); ferry is at (240,264). Field's southern passage remains x240, with hollow/intake approaches (80,104)/(400,72). Every interior has the same (108,144,24,16) southern escape and spawn (120,132). The permanent loft shortcut returns to town spawn 4 and the gallery shortcut returns to field spawn 1; both are additional, nonblocking exits and preserve all prior doorways.

## Generated evidence and storage

- `assets/southern_region/*.png`: indexed native scenery and RGB staged previews
- `assets/southern_region/sprites/*.png`: all 38 native sprite states
- `assets/southern_region/camera/*.png`: exact 240×160 staged crops, including odd camera offsets
- `assets/southern_region/layout.json`: geometry, object/static-actor contract and byte budget
- `assets/southern_region/validation.json`: individual reachability targets and source/staging accounting
- `src/south_art_data/part_*.inc`: generated source chunks at most 30,000 bytes each
- `build/southern_preview_native.png`: large labeled contact sheet; build-only, not a source-archive input

The current total is 859,332 bytes, with 3,962 bytes of exact collision lookup data. The native bitmap payload is 844,800 bytes, including independently emitted odd-x rows for both outdoor maps. Those odd rows allow the existing aligned renderer to select any camera x without changing native pixels. The 38 actor states add 9,728 bytes. Total generated art data, collision, alignment and 32-bit room-table allowance stays below 1.35 MiB; exact current figures are in layout/validation.

All generated JSON and C include files are capped at 30,000 bytes. Individual PNGs stay below 70,000 bytes. Regeneration is deterministic for the same contract, scene and available companion preview inputs.

## Independent test coverage

The ten art tests verify:

1. Native sizes, exact palette, nontransparent scenery and byte-identical PNG/C arrays
2. Every camera x from 0 through 240, six representative y offsets, exact odd-row alignment and native crop sizes
3. Unchanged fixtures/spawns plus all required foot-radius-five BFS targets and enemy starts
4. No baked changing mirror, screen, gate, machine or hood; exact live-tree collision and loft beacon-wall clearance
5. Independent reconstructed collision occupancy matching every emitted row-band record pixel for pixel
6. Sprite C bytes, enum-backed PNG ordering, ROM/data/archive caps and absence of IWRAM code
7. Deterministic regeneration
8. Strict host-C syntax check for the generated translation unit
9. All 24 finite optical room/state combinations traced through the unchanged production ray functions, with no segment interior crossing a raw scene solid and every wall endpoint landing on a material
10. Both permanent shortcut gate fixtures, clear center/approach geometry, exact unlock conditions and existing destination spawn indices

These checks establish art/data/geometry correctness. They do not claim controller playthrough, target hardware frame timing, actor ordering under every gameplay state, or durable progression acceptance; those belong to the runtime/native acceptance work.
