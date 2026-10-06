# Hearthwake: original Northern chapter world and runtime

This directory contains eight authored rooms, their immutable bitmap/collision data, thirty-two transparent 16×16 actors, Japanese UI additions, and the exact room/quest allocation contract. `src/north_game.c` implements the playable interactions; `src/northern_quests.c` owns the event/reward ledger. These files do not independently establish release obtainability or measured frame-time acceptance. Controller journeys and final same-ROM performance evidence remain separate gates.

## Build and inspect

- `python3 assets/generate_northern_region.py` regenerates the native indexed PNGs, camera crops, layout, geometry proofs, and bounded C includes
- `python3 tests/test_north_art.py` independently checks palette, C/PNG equality, every camera X parity, geometry, archive limits and deterministic regeneration
- `python3 tests/test_north_game.py` exercises actual production C, quest/reward code and Save5 through synthetic engine bridges
- `NORTH_SANITIZE=1 python3 tests/test_north_game.py` repeats that runtime suite under UndefinedBehaviorSanitizer
- `build/northern_preview_native.png` is an optional generated, labeled native-pixel collage. It is deliberately outside source assets. Individual PNGs are all below 70 KB

The original 178-entry shared RGB555 palette is unchanged. No raster artwork, existing-game sprite, external building facade, or traced layout is an input. All pixels are authored from the repository's primitive pixel-art generator. Exterior textures use the established bright sunlit material ramp; actors retain the original shared ramps.

## Spaces and route

| ID | Room | Native size | Purpose |
|---|---|---|---|
| 22 | Hearthwake Quay | 480×320 | Painted timber waterfront, ferry, two manual cargo lines, working harbor services |
| 23 | Headland Roads | 480×320 | Coastal load junction, tender rescue, mismatched route markers, sheltered rest |
| 24 | Boathouse Gallery | 240×160 | Overlapping hull ribs, visible gallery parcel, tether and fragile-cargo trials |
| 25 | Kiln and Chart Store | 240×160 | Draft channels, retained heat, three drying shelves |
| 26 | Loading Hall | 240×160 | Slatted freight rack, one-cart rail lesson, manual weight |
| 27 | Crossbeam Chamber | 240×160 | Braced high beam, separate load lanes, optional Earth trial |
| 28 | Relay Gallery | 240×160 | U-shaped gallery, service recess, routed carriage and compass trial |
| 29 | Beacon Crown | 240×160 | Open-air cliff platform, counterweight machinery and exposed coupling |

Ferry entry requires Sky-clear and having visited Reedhaven. It does not require the prior ending or completion of river quests. Wood 19 is guaranteed by quest 11 before its mandatory reel use. Metal 77 is guaranteed by quest 13 before mandatory rail alignment. Dungeon entry requires both quests claimed. The main dungeon can be finished without selecting Earth/Kohaku or any evolved command. Existing earned story companions remain untouched.

## Geometry, camera and state

All coordinates are world centers, all rectangles are half-open, and player collision includes a five-pixel foot. Both 480×320 exteriors include aligned row-local odd-X atlases. For even X, read `bitmap + y*width + camera_x`; for odd X, read `bitmap_odd + y*width + camera_x - 1`. Copy 240 bytes for each of all 160 rows. Interior cameras remain zero. HUD placement is parent-owned; no background reserves a UI strip.

Static collision is compiled deterministically into a per-room 16-bit y→band-offset table and a deduplicated stream of sorted, disjoint, half-open x intervals. Each authored rectangle is expanded by exactly the existing five-pixel foot; world-edge semantics are part of the same rows. The original rectangles remain in ROM for audit/testing, but are not scanned at runtime. Town rows have at most six intervals, field rows at most four, and most interiors at most two. Out-of-world coordinates return solid before table indexing, including signed integer extremes.

The lookup adds 4,014 bytes of ROM tables, 64 bytes of room pointers and ten alignment bytes, with no RAM allocation. The ARM collision function uses eight bytes of stack, down from twenty-four. Exhaustive production-C comparison to the independent original rectangle predicate checks all 537,600 room pixels, a 32-pixel surrounding border, extreme out-of-bounds pairs and non-Northern rooms: 827,778 comparisons. A separate Python raster reconstruction checks every generated interval row. All 62 source/staged/camera PNGs are byte-identical to the pre-optimization versions.

Every spawn, doorway approach, reset and interaction point is cardinally reachable. Actors are not solid blockers. Cargo checks a swept route against the player's foot before advancing and fails without consuming progress when occupied. There is no cargo crushing, arbitrary scenery pushing, freeform rope solver, timed main-path precision, or new framebuffer.

`NorthPuzzle` has four bytes: a two-bit rail orientation, two three-stop carts and a binary manual weight. Loading Hall has 24 reachable states, Crossbeam 72, and Relay 40. The host suite traverses each complete reachable graph and proves a solved state is reachable from every node; it also checks reset for all 72 Cartesian states in every room. Because transient machinery never changes movement collision, every state retains the independently proved reset and south-exit routes. Unfinished arrangements reset on room entry. Completed quest objective bits remain completed and reconstruct a solved room.

Quests 11–21 have exact masks `[3,7,3,7,7,3,7,7,3,7,15]`; all their variable bytes remain zero. Northern room visits use `region_flags[1]`, and rest anchors use `anchors[1]`. No Northern bit is added to the old campaign room flag shifts or chapter ending flags. Save5 revision 3 and the parent save validators own cross-ledger validation.

Recruit claims are atomic, one-time, family-preserving transactions. A full roster leaves READY and changes no byte. Personal trial claims stage one creature record locally; equipment FULL changes no creature, gear, quest or reward ledger. Trials raise experience/bond only to the authored floor, never lower progress, equip a command, evolve a creature or alter its identity automatically. Tests cover all five recruit/trial paths, retry/idempotence, objective order, save validation and round trips.

## Machine encounter bridge

The crown's left Wood coupling and right Metal coupling open the start handle. The machine cycles through a 60-update warning, 24-update sweep, 90-update exposed window and 30-update recovery. The warning is visible before damage; the south walkway stays safe. The weak point is `(120,68)`, radius 12, and has no static wall collider, so wall-first arrows can reach it. Every existing weapon class can finish it. Health is 128 Q4; damage and incoming sweep callbacks use Q4 units.

The parent reserves attack-ledger bit 8 and must call `north_game_weapon_hit` only after confirmed melee/arrow overlap, once per attack. The parent also supplies `game_north_hurt` and the distinct `north_actor` sprite-key namespace in the existing bounded twenty-slot OBJ cache. Reset and leaving restore an unfinished encounter; completed objectives are retained.

## Measured isolated objects

At the current ARM build:

- Background/actors/colliders/table: 857,808 ROM bytes
- World/puzzle runtime: 8,056 ROM bytes and 32 BSS bytes
- Quest event/reward module: 1,514 ROM bytes and zero BSS
- Every generated include is at most 32,000 bytes

These are isolated object measurements, not a claim about final linked ROM or 59.73 Hz native cadence. No new heap, roster, save scratch, framebuffer, or OBJ cache is allocated by this chapter module.

## Reference and cultural boundary

The fictional timber harbor borrows broad spatial/material ideas, not actual buildings or game art:

- [UNESCO: Bryggen](https://whc.unesco.org/en/list/59/): gabled harbor-facing timber frontage and working passages
- [Norsk Folkemuseum: Brottveit storehouse](https://norskfolkemuseum.no/en/storehousefrom-brottveit): a clearly identified storehouse-gallery reference, not a claim that its unusual three-storey form is universal
- [Viking Ship Museum: Gokstad boat reconstruction](https://www.vikingeskibsmuseet.dk/en/professions/boatyard/building-projects/the-gokstad-boat): overlapping shaped hull boards as a material/silhouette reference

All machines, names, residents, creatures, powers and phase assignments are invented. The game's separately documented five-phase/Yin–Yang inspiration is not presented as Nordic belief. No sacred symbols, pseudo-authentic runes, Indigenous motifs or purported authentic folklore are used.
