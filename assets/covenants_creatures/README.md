# Original covenant native art

`source/generate_covenant_art.py` is an unchanged copy of the isolated original art kit generator. Its authored pixel functions are integrated through `../generate_covenants_creatures.py`, which validates and emits the existing shared-palette pixels without modifying the original kit or any older asset.

Run the wrapper from the repository root:

`python assets/generate_covenants_creatures.py`

It creates six bounded C includes, the immutable frame/portrait API, gait durations and `manifest.json`. It does not enable forms, alter saves, allocate OAM or grant companions. The source copy includes unused standalone-preview helpers; use the wrapper for this repository.

The original kit's credits and static pixel review are preserved in `source/`. Those notes describe asset review, not native game acceptance. Current component tests and remaining whole-game review gates are documented in `docs/COVENANTS_POWER_INTEGRATION.md`.
