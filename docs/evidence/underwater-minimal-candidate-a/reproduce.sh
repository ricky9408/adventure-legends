#!/bin/sh
# Run from the repository root; requires this exact frozen candidate and snapshot.
set -eu
export PYTHONDONTWRITEBYTECODE=1
# Set LD_LIBRARY_PATH to the directory containing the existing libmgba.so.0.10.
python3 tests/underwater_minimal_review.py \
 --rom build/underwater-candidate-a/emberbond.gba \
 --symbols build/underwater-candidate-a/emberbond.sym \
 --source-manifest build/underwater-minimal-review-a/frozen-runtime/source-hashes.json \
 --helper-snapshot build/underwater-minimal-review-a/test-source \
 --source-sram tests/fixtures/v5-revision5-minimal/magma-minimal10-town.sav \
 --source-report build/underwater-minimal-review-a/main/underwater-journey.json \
 --output build/underwater-minimal-review-a/reproduction
