# The Roads That Stay scenery contract

All eight runtime maps and 44 original 16×16 actors/props use the existing indexed RGB555 palette. Runtime bitmaps contain no people or creatures. Files with `_staged` and the developer sheet add sample actors for inspection only. `spoiler_free/` contains two first-town art previews, with no legendary or ending spoilers; these are not controller screenshots.

Run from the project root:

- `python3 assets/generate_covenants_region.py --check` checks byte-identical regeneration without rewriting files
- `python3 tests/test_covenants_art.py` checks exact full-foot collision, all intermediate dynamic positions, shortcut connectivity, palette/transparency, Japanese widths and ARM object resource use
- `python3 tests/check_covenants_field_feasibility.py` runs the actual Return/Horizons C support-power renderers against the actual art collision and proves nonzero native pixels reach every declared target, including the two heat beats from one cast

`geometry.json` is the authored runtime contract. Areas are indexed by area minus70. The C room struct has the same layout as `HorizonsArtRoom`. Static collision rows already include the radius-five square foot; adding another expansion would be wrong. Dynamic solid rectangles use the same half-open raw rectangle convention and still need a separate radius-five check. Targets are seven-pixel squares with radius3 and explicit expected facing and power age. They do not introduce solid collision.

Command108 uses a plate ten pixels to the right of the original foot center and a seam twelve pixels below it, facing RIGHT. Gather at age8, release at age10, and the same cast reaches the seam at age14. The seam cannot count for gathering. Command102 uses its real left-offset quiet line. The two area74 work targets are below the workshop's expanded wall, at(192,96) and(280,96). Form125 practice uses the clear crescent side at(204,100); form122's second corner socket is(64,84), outside the orchard bed.

`covenants_practice_shortcuts[8][4]` contains half-open allowed actor-CENTER strips, never raw object rectangles. Only a completed covenant plus an owned companion's explicit practice should activate them. The painted temporary surface must extend five pixels beyond each side of its center strip so every accepted full foot has visible support. Delay expiry while any actor occupies the closing strip. Each strip crosses an existing obstacle and joins two ordinary clear endpoints; the permanent outside route remains available. Orchard and seed-shelf crossings pass over empty irrigation gutters and never erase planted beds. Rooms72/74/77 have zero-width strips and use non-solid inspection, quiet-route and shelter overlays.

Human coordinates are foot centers. The normal16×16 placement is(x−8,y−15). The walker, seed keeper and passenger have a four-beat sequence: base, STEP_A, base, STEP_B. Frame names appear in `moving_resident_frames`; all original enum values remain fixed. The last-watch neighbor is at(104,112), safely inside the refuge, and the watcher is at(144,120).

The three porch pieces are nonblocking original overlay sprites. Their proposed village placement is a suggestion for integration; main must check the existing village's actors and exact homecoming frame. Draw them only after the informed shared-porch commitment and homecoming. No old village bitmap was changed.

`assets/covenants_ui_texts.json` is the merge-ready Japanese dictionary. `ui_english_developer.json` uses the same keys for English developer meanings. The porch dialog introduces the wish for private quiet, explains sharing the space and time, and presents the choice before committing. Story completion and optional invitations are explicitly separate, and declining keeps the invitation available at its named location. Form display spellings follow `assets/covenants_power_ui.json`.

The host proofs are deliberately narrower than final gameplay acceptance. They do not prove journal clipping after integration, native frame timing, controller-earned quest or invitation state, actor obstruction behavior during actual escort updates, or save/load reconstruction. Those remain part of the integrated native routes and independent review.
