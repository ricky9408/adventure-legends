# Underwater Japanese localization

Development text and layout evidence only. The candidate's 89 creature data rows do not establish an earned native release, a completed controller route, emulator acceptance or hardware performance.

## Delivered files and ownership

- `assets/underwater_region/dialogue_ja.json`: all 188 English dialogue keys, in identical order
- `assets/underwater_ui.json`: 24 form names, 24 command names, 8 family wishes, 2 progression hints, 1 pending-transaction label, 3 startup-direction hints and 12 equipment name/description keys; 74 keys total
- `tests/test_underwater_localization.py`: 7 focused tests, plus an optional preview renderer
- `docs/underwater-localization/previews/`: six individually labelled 240×160 text mockups, a 720×320 contact sheet whose panels remain at native size, and measured per-key widths

This task changes none of the English source, game logic, generated UI, catalog fragments or delivered sibling projects. The integration owner must load the Japanese dialogue and UI files into `assets/generate_ui.py` and connect their keys in progression/equipment UI. Do not load the English dialogue into the shipped Japanese text table.

## Reproduce checks and previews

Run from the candidate's root:

    python tests/test_underwater_localization.py -v
    python tests/test_underwater_localization.py --previews

The exact text font is `/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc`, index 0, 12 px. Width is exactly `font.getbbox(text)[2] + 1`, matching `assets/generate_ui.py`. Preview glyphs use the same monochrome 15-pixel mask and `(0,-2)` draw offset; no antialiasing or font-size reduction is used.

Bounds checked:

- Every string: at most 214 px
- Form names: at most 96 px, matching each evolution-branch name slot
- Journal quest/trial title: at most 156 px, leaving six pixels before the status at x176
- Journal status: at most 50 px
- Pending-transaction message: at most 154 px inside the 166-pixel modal
- Glyphs: no clipping above or below the generated 15-pixel mask

The previews have a neutral background and explicitly say “LOCALIZATION PREVIEW / TEXT MOCKUP / NOT EMULATOR.” Their purpose is inspecting wording and mask density. The branch preview demonstrates the two exact name slots; the pending/aim and gear previews juxtapose independent contexts for review. They do not claim these combinations appear together in gameplay. No map, earned roster or real emulator capture is represented.

The test pins the final English source hash after the world author's agreed portal-wording correction. A later English change intentionally fails the pin so the corresponding Japanese meanings must be reviewed, even when the key set stays unchanged.

## Terminology and spoiler boundaries

- Nacreway: 真珠路; archive: 記録庫; keeper: 記録守; shellwright: 貝細工師
- Echo: 響き; ballast: 重し; fixed landing: 固定足場; acoustic baffle: 音よけ板
- Inkbud: スミツボミ; Bobclam: ウキガイ. Their named field-signature hints match the menu names exactly
- The portal is a 貝の昇降機. Its wait line refers to the existing Japanese Q32 title, 「山に息を通そう」, and says to report it. It deliberately does not name the separate Q36 lost-bell quest
- The guardian opening says 武器. No sword-only restriction is introduced
- “進化した仲間がいれば、また。” describes the retained terminal's availability for another visitor without requiring that terminal to occupy the active party
- The reset line preserves A to reset and B to keep this attempt
- No source coordinate, required switch-state number, forced branch choice, hidden receipt or exact solution sequence has been added to player text
- Status labels distinguish 未発見, 探索中, 報告可 and 記録済

### Direction and ordering audit

Checked against the final English dialogue, `docs/underwater-runtime/DEVELOPER_ROUTE.md`, `src/underwater_trials.inc` and the actual power/control contracts:

- Main overlay: echo, ballast, then rotate the other leaf
- Parade: bowls first, frames second, curling steps last
- Teaching return route: both pale shell landings, then the lower shell path
- Shoal screen: approach its handle from the far side
- Trial 0: rotate the positive outline, mirror the missing space, echo both matching outlines
- Trial 1: shade only the crescent; the live border still matters
- Trial 2: ballast this side, walk around, return the shelf from the far side
- Trial 3: opposite float depths and both observation stones
- Trial 4: trace the two side rails, leave the notch, unfold the cross-frond by hand
- Trial 5: both curled fronds, small doorway left open, both stones before joining the root
- Trial 6: turn both guides along the L-shaped wall, release the bead, then trace the rim
- Trial 7: unfold and slide the perforated screen; preserve both windows and close only the outer rim
- Trial 8: warm the outside, turn, then cool at the stone; leave the center unchanged
- Trial 9: upper left to lower right, four adjacent pads, avoid the crossed pad
- Trial 10: lower-left starting arm; all five distinct tips must fit
- Trial 11: three non-overlapping panels, both joints, refuge pads remain clear
- Trial 12: whole moving sweep stays clear of the frame; either safe angle remains valid
- Trial 13: genuine figure-eight lobes, once each, with the crossing between; no obsolete left-center-right shortcut is taught
- Trial 14: both sides lit, diagonal left unlit
- Trial 15: three corners chosen and echoed; the remaining fourth corner stays dim

The three aim hints say to press the relevant direction immediately after R. They describe a fresh one-direction press, not another R activation. The exact contract is one cardinal key edge during the first eight active simulation updates: horizontal for ordinary side alternates, four directions for command 69's starting corner, Up/Down for commands 83/90's axes/inversion. Commands 67/71/77/81 have no such startup-direction hint. Nothing claims that steering restarts a command, changes its origin, stops time or changes the cooldown.

## Authored creature names

Names follow the new living anatomy and visible branch shapes. They are authored for this chapter; no external franchise creature names or art were used. This is a creative naming record, not trademark clearance.

| IDs | English forms | Japanese forms | Shape vocabulary |
|---|---|---|---|
|49–51|Inkbud / Scriptcuttle / Fanfolio|スミツボミ / フデヒレ / フタオウギ|Ink bud, brush-like fin rails, two fan-shaped webbed arms|
|52–54|Bobclam / Keelcasket / Crownfloat|ウキガイ / フナゾコガイ / カンムリガイ|Buoyant clam, boat-keel lower valve, crown valves|
|55–57|Frondfoal / Trellisseer / Bowercoil|モコタツ / ハシゴタツ / マキモタツ|Small kelp seahorse, ladder fronds, coiled kelp bower|
|58–60|Rimlet / Gateshield / Stencilback|フチコ / モンフチ / マドフチ|Small continuous rim, gate rim, windowed shell rim|
|61–63|Ventplume / Haloworm / Trailwick|ヌクホサ / ワッカホサ / ヒキホサ|Warm feather tuft, incomplete crown ring, trailing wick tuft|
|64–66|Palmstar / Crossbloom / Foldrunner|コモテ / ヒラクロテ / オリノテ|Small kelp-edged hands, open cross arms, folded walking arms|
|67–69|Linkeel / Hingejaw / Claspcoil|ツナウナ / ツギアゴ / フタワウナ|Linked eel, articulated jaw, two-loop eel|
|70–72|Combgleam / Veilglass / Triadome|クシユラ / スジスケ / ミスミユラ|Waving comb bands, transparent diagonal veil, three soft corners|

Command labels describe their geometry without inventing shield, reflect, trapping, slow or boss-displacement effects. Base signatures retain their own names after evolution.

## Equipment numbers

Checked against `assets/equipment/catalog.json` and the progression/save worker's final vectors. Attack and defense numbers follow the game's displayed raw Q4-stat convention; HP bonuses are expressed as hearts (`hp_q4 / 16`). Speed changes are qualitative, avoiding an inaccurate integer promise after the speed display's rounding. Wait reductions preserve their actual update counts.

| ID | Japanese name | Description meaning |
|---|---|---|
|6|貝文字の剣|Attack +1, reach +3|
|13|真珠穂の槍|Defense +1, reach +4, slightly slower (−2 Q8)|
|38|真珠織りの鎧|Defense +2, health +0.25 heart|
|54|流れ歩きの靴|Lighter steps (+6 Q8), roll wait −1|
|68|地図折りの帯|Health +0.5 heart, power wait −2, slightly slower (−2 Q8)|
|86|静水の指輪|Defense +1, power wait −2|

No item description adds an oxygen system, breathing requirement, access permission or field ability. These are optional sidegrades.

## Integration re-review (2026-10-05)

The full188 English/Japanese pairs were re-read against the integrated world and
trial contracts after the source-pin check correctly rejected the regenerated
English reference. The current English reference is SHA256
`67a32a8e12bae0cfa451946c955663a8e0051259c026e7d68e04a240be8c2476`;
the previous translation-review pin was
`5be8ca52f9edd47fbb0ee3edac4cb0cad50bc680a3576ea8791f4df4535a8035`.
No Japanese text or generated game UI changed in this re-review. The portal's
mountain-safety report remains the existing Q32 Japanese title, and guardian
openings remain weapon-neutral. Added explicit semantic assertions for both
cases; key/order, every pixel-width/height, names, controls and gear checks
remain intact. The earlier failed pin check is preserved in the development
aggregate log; this is a reviewed new pin, not a disabled integrity test.
