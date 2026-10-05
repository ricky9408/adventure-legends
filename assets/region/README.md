# Reedhaven original region artwork

Generated with `python3 assets/generate_region.py`. Test with `python3 tests/test_region_art.py`.

- Running `make assets` also creates `region_preview_native.png`, a labeled native-pixel overview; `_2x` uses nearest-neighbor only. These redundant large contact sheets are generated locally rather than included in the source archive
- The locally generated `native_camera_sheet.png` shows real 240x160 crops, with actors staged separately. Individual room/camera images are included
- Six named backgrounds are opaque indexed PNGs; `_staged` files are previews, never ROM inputs
- `sprites/*.png` are original transparent native 16x16 assets, named by their public enum
- `layout.json` holds exact static geometry, dynamic rectangles, approaches, exits and sprite indices
- `validation.json` proves all exits, spawns and interaction approaches with 5px square feet in both mechanism states
- The fixed `contract.json` is read-only to this generator

## Engine integration

Compile `src/region_art.c`. Include `src/region_art.h`. Room index is `room - REGION_ART_FIRST_ROOM` (16).
`region_art_rooms[index]` supplies width/height, bitmap, bitmap_odd, solids and solid_count.
Exterior atlases are aligned to four bytes. For odd camera X use `bitmap_odd + row*width + camera_x-1`; even X uses `bitmap + row*width + camera_x`. Copy 240 bytes for all 160 rows. Interior cameras stay (0,0), so their odd pointer is null.
All collision rectangles are half-open and include world edges. Building/tree rectangles intentionally exclude their opaque projected roof/canopy silhouettes: without a foreground pass, these are impassable scenery islands. No required route passes behind a roof. Eaves may overhang the exclusion by a few decorative pixels, but all doors and 5px-foot approaches are proved clear. Add only the runtime dynamic rectangles recorded in `layout.json`; never duplicate them as permanent scenery walls. `region_sprites[REGION_SPR_*]` is row-major 16x16 for the existing obj_upload path, with index zero transparent. Dynamic bridge tiles can be repeated over the exact bridge rectangle.

The gate/latch art encodes no quest solution. The background supplies neutral sockets, inlays and local visual clues; runtime state owns all changing props. This is an artwork/navigation contract, not proof of implemented or completed quest logic.
