# Archived Underwater design handoff

This directory preserves the pre-implementation proposal and its historical checks.
It is **not the current release acceptance suite**. The implemented chapter and
same-ROM verification are documented in `../VERIFICATION-UNDERWATER.md` and
`../underwater-runtime/`.

The original README is preserved byte-for-byte in `README.original.md.gz`; its
SHA-256 is `e57665a5c8425ae72123908c6f7f495ee8edeeb109b1fa1777263250c9734275`.
`artifact_manifest.json`, `validation_report.json`, and `unittest_report.txt`
remain the historical design-stage receipts, not results for the final cartridge.

## Reproduction boundary

`validate_design.py` and `test_design.py` deliberately require the exact sibling
Magma development baseline pinned in `underwater_allocation.json`. That proposal
predates the accepted Magma D release. Against the later accepted Magma checkout,
15 model tests still pass but the source-pin/schema test correctly rejects the
changed baseline. A source ZIP alone does not contain that external historical
build. These commands must not be advertised as a current green test target.

Do not silently update the baseline hashes or rerun `build_design.py` over this
archive. That generator rewrites the proposed source pins and estimates. Current
catalog/schema/history, transaction and native tests exercise the implemented
revision6 instead. Some proposal values were intentionally revised after actual
native measurement, including command77 timing and the incremental ROM estimate.
See the runtime handoffs and memory evidence for the reviewed final values.

## Documents

The chapter brief, creature cards, acquisition/trial contracts and compact JSON
are developer-only design material with progression spoilers. They do not prove
implemented acquisition, image quality, save migration or native pacing.
The current finite roadmap is `../ROADMAP.md`; the archived finer-grained plan
remains available as historical context.

`accepted-magma-baseline.json` identifies the later accepted source baseline.
Its original final-export smoke claim linked an unsuccessful bridge-setup log;
`accepted-magma-smoke-correction.json` records the subsequent clean ZIP extraction,
bridge build and successful smoke rerun. The older failed log was retained.
