# Render-B diagnostic against A-earned Southern SRAM

This is an authorized **diagnostic cold-SRAM import**, not final same-ROM acquisition or acceptance. No A machine state was imported into B. The original acceptance scripts and their source-admission policies were not changed. The isolated adapter and raw reports are under `build/underwater-render-diagnostics/`.

B ROM: `e02c410824086957a9ee472185a384360e3f6c144b1693b875c05873d6603923`

All1161 runtime closure file hashes were authenticated under `build/underwater-render-b/runtime-source/`. Two already-changed Magma files were recovered from A's closure only because their bytes matched the exact B manifest hashes.

| Same controller workload | Candidate A | Render B | B peak cycles |
| --- | ---: | ---: | ---: |
| Southern42 | 179 /180 | **180 /180** |246,188|
| Southern30 |180 /180|180 /180|239,755|
| Earned21 storage candidates |115 /120|**120 /120**|181,040|
| Cold town journal |95 /95|95 /95|262,215|
| Cold field journal |95 /95|95 /95|255,873|
| Summoned rest/save |157 /160|**156 /160**|276,951|
| Unsummoned earned rest/save |180 /180|**178 /180**|275,338|

The numerator denotes both updates and displayed flips; the denominator is hardware frames. Rest/save remains a production pacing blocker. B summoned misses are indices1/37/81/117; unsummoned misses36/116. Strict checks remain unchanged. Renderer cycles exclude VBlank/OAM commit.

## Pixel preservation

Independent cold boots of the same authenticated A-earned SRAM produced30 matched observations on A and B: eight journal pages and22 storage-candidate views. All full240×160 indexed bitmaps are byte-identical, with matching roster bytes, modal state, selected tab and candidate identity. No pixel mismatch was hidden by cropping. These static modal checks do not cover the entire new chapter or every animated transition.

[Bounded evidence and report hashes](../evidence/underwater-legacy/render-b-diagnostic.json)
