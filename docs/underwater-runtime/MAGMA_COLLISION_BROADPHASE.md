# Exact legacy Magma path broadphase

This is a narrowly scoped performance correction for the current Underwater build. It does not modify the released Magma source snapshot, command timing, damage, path geometry, target policy, save state, or sprite output.

## Measured cause

The retained native command66 counterexample is in Magma room38 at hero(239,221). The exact-I diagnostic measured update16,515, save238, and render279,190 cycles. World rendering used82,565; actors used192,411, including163,367 in `magma_powers_draw`. Five radial paths were refreshed: four whole and one clipped. Each original refresh retraced every raster pixel through the general ROM collision dispatcher. The strict hardware-update/page-flip failure is retained as counterfactual evidence, rather than relaxing its threshold.

## Change

- `magma_game_clear_box(x0,y0,x1,y1)` certifies an inclusive empty rectangle only in large rooms38/39. It uses the exact generated collision-row bands and current22×22 `prop_hit` rectangle around the lesson jar or screen
- Identical adjacent immutable band pointers are scanned once; the shared generator's sorted/disjoint interval contract permits early termination to the right of the query
- The new world API returns0 for invalid bounds and every other room. Existing small-room/trial/puzzle behavior therefore remains on the original collision path
- The engine-owned `game_clear_box` dispatcher supplies the appropriate world proof. Magma powers hold no dependency on a future chapter
- `refresh_one` retains all existing origin/parent, bounds, length, and start-solidity checks. Only a certified empty rectangle stamps the exact authored endpoint as `ex/ey` and sets `whole`. Otherwise the unchanged endpoint-inclusive Bresenham/corner-cell loop clips the path as before
- The hook is weak and optional for old focused linkers. An absent proof provider takes the original exact fallback
- Damage brushes, path masks, from/to windows, parent chains, spawn receipts, collision invalidation, and rendering are unchanged

The empty rectangle is a proof about every pixel, not a corner sample or inflated hitbox. A monotone raster and both diagonal side cells are wholly inside its endpoint bounding rectangle.

## Cost

ARM object measurements add92 ROM bytes in `magma_powers.c` and284 ROM bytes for the world query. The query uses36 stack bytes; the power object's largest individual frame remains120 bytes. Mutable power state remains360 bytes, with no new IWRAM or OBJ VRAM. The parent owns the small cold engine dispatcher and final link budget.

## Verification

Run:

- `python3 tests/test_magma_powers.py`
- `python3 tests/test_magma_clear_box.py`
- `python3 tests/test_magma_geometry_equivalence.py`
- `python3 tests/test_magma_geometry_equivalence.py --sanitize`

The existing401 damage assertions are retained, and both strict and ASan/UBSan Magma integration runs pass. The actual-world box oracle passes951,647 checks across both large rooms and all three authored positions of each movable prop, including all individual pixels, independent prefix-sum rectangle checks, invalid bounds, and conservative fallback rooms.

The frozen candidate-J source is byte-identical at `tests/fixtures/magma_powers_candidate_j.c`, SHA256 `65764bcc3c056e6b55a8b69559637109dd47927e76a38e78e677603d0e3ca3a5`. No reference code is adapted. Both strict and complete ASan/UBSan differentials match:

- 104,352 cast-frame records across24 commands, four facings, both sides, and11 scenes
- 112,190,152 exact pixel hit masks
- 240,640 complete path records, including32,544 clipped paths
- 164,050 directed clear-ray checks
- All sprite attributes, mutation and repeated-draw checks, and5,544 command66 five-ray frames
- 6,992 successful empty-box certificates and1,510 fallback cases

Exact compared streams and reports are under `build/magma-geometry-equivalence`; box evidence is under `build/magma-clear-box`. These host results establish equivalence, not native cadence. The retained command66 failure was replayed on immutable candidate K using authenticated I-earned SRAM and an ordinary cold boot, without importing cross-ROM machine state or writing gameplay RAM. It passes all93 unchanged controller assertions,64/64 hardware updates/page flips, and a196,343-cycle peak versus the296,098-cycle I failure. Evidence is `build/underwater-k-magma66-cold-sram-diagnostic/replay/diagnostic-report.json`. This is explicitly cross-candidate diagnostic evidence; the fresh same-K final acquisition/combat aggregate remains the parent's release gate.

All12 wider Magma host suites pass: architecture, art, catalog policy, creature art, creature core, evidence, evolution UI, runtime game, historical core, legacy admission, exhaustive save interruption, and save limits. The save interruption suite completed its full241-second run. Logs and exits are in `build/magma-broadphase-host-regression/summary.json`. The complete Underwater23,181 strict/ASan damage suite also passes after the shared Magma link change.
