# Remaining rest/save hitch: isolated timestamp profile

Source: exact archived render-B plus timestamp-only hooks in copied `game.c`. Production source was not edited. Diagnostic ROM SHA-256: `255592c03fdc3f70eeb40c3f6bf4aec0695a351eb99af8565e25228535a1e807`.

All1058 matched production functions retain their original ROM/IWRAM memory region. The original28KiB linker guard was unchanged. IWRAM ends at0x03006ef0, versus production B0x03006f00. Counters are EWRAM; new sampling helpers are ROM. No cross-ROM machine states are used, only authenticated A-earned21 SRAM cold-imported into this altered ROM. These measurements include diagnostic overhead and **are not final cadence acceptance**.

## Measured breakdown, cycles

| Operation | Update | save_frame | Render | World | UI after world | Actors | OBJ commit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Summoned PLAY→SAVE |133,839|485|138,239|83,199|30,192|19,611|6,922|
| Summoned SAVE→DIALOG |100,212|276|176,942|83,199|68,725|19,751|9,455|
| Unsummoned SAVE→DIALOG |100,202|276|175,367|83,191|68,725|18,184|8,349|

World/UI/actor columns are components of render, not additional costs. `save_frame` is only scheduling; the expensive writer work occurs inside update.

Summoned dialogue render finishes at scanline163; unsummoned at161. Both have already missed the scanline160 entry the main loop expects. Its first wait exits the current VBlank, then waits for the following one, producing an additional276–279K-cycle wait. Merely comparing render_cycles to280,896 misses this condition, because the update begins after the previous frame's OAM commit.

Steady save updates can cost159,759 cycles but only require22,009 render cycles and fit. The failure arises when a heavier transition update shares a frame with an83K world copy and30–69K new UI.

## Source attribution

- A repeated Southern rest invokes `southern_anchor()`, which calls full `save5_validate()` before discovering the anchor is already set
- A completed writer calls `progression_save_step(SAVE5_RECOMMENDED_BUDGET*3)`, including final SRAM verification, then resumes dialogue in that same update
- Rest and dialogue transitions must preserve validation and persistence semantics. Candidate remedies need an explicit bounded/no-op-safe rest path, a light separate resume update, or an independently verified redraw optimization

[Bounded measurements and exact report hashes](../evidence/underwater-legacy/render-b-profile.json)
