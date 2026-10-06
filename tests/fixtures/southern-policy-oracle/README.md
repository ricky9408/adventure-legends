# Frozen Southern policy oracle

This minimal source closure is copied byte-for-byte from delivered Southern commit
`0d08f7dd1c232bfdff0a3b572ba8d1fdee07ba15`. It lets
`tests/test_save5_history_differential.py` run from a clean Magma source export
without any sibling checkout. No production Magma module includes these files.

`provenance.json` records every archived input's size and SHA-256. The runner pins
the entire provenance file as well as retaining its original seven C-source pins
and prior-SRAM pins. All 12 runtime C/header files were also checked against the
already archived delivered Southern runtime-source manifest. The helper and four
SRAM files were checked against the same local release commit.

The SRAM files are generated controller-test fixtures, not player saves. Their
original provenance remains in the normal `tests/fixtures/v5-revision1`,
`v5-revision2` and `v5-revision3` directories. The Southern helper constructs
additional synthetic host states; these are never native acquisition evidence.
`southern_n5_fixture.h` is generated in a temporary
compile directory from the pinned Northern revision3 SRAM. It is intentionally
not a pre-existing source file.

Run from the project root:

    python3 tests/test_save5_history_differential.py

An explicit `SAVE5_HISTORY_BASELINE=/path/to/frozen/southern` override remains
available. Every required input must retain the same frozen hashes. No source
from an expanded live catalog may replace or regenerate this oracle.
