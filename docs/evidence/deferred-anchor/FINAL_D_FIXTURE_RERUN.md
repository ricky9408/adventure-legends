# Final D fixture rerun

The original `REVIEW.md`, results, and logs describe the unchanged deferred-anchor
engine review using the controller-earned predecessor-C input. They have not
been relabeled or overwritten. Exact candidate-D originals, including that
runner, are additionally preserved under `historical-c/` with `SHA256.json`.

The current runner now always loads the packaged generated regression fixture
`tests/fixtures/v5-revision5/magma-all65-town.sav`, SHA-256
`a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858`.
This is the independently cold-booted final-D town SRAM, with34 actual retained
individuals and65 earned histories. It is not a player save. A missing fixture
now fails explicitly instead of silently omitting the large-roster case.

Both normal and UndefinedBehaviorSanitizer reruns passed all27 synthetic host
scenarios. Both variants also passed from a separately extracted source ZIP
with no `build/` directory. Results, logs, and the export-portability receipt are
under `tests/fixtures/v5-revision5/verification/`. The fixture's portable verifier
authenticates the exact acquisition/lifecycle reports, archived helper inputs,
four SRAM banks, and the893-entry runtime manifest.

These reruns deliberately modify host state after decoding the authentic input.
They remain synthetic integration evidence, not additional native gameplay or
hardware timing claims. Production sources were unchanged and reverified
against D manifest `a72fd93eddb0a39322b22e45caf0f4ac49496d962776ee616dfd83642342ef3f`.
